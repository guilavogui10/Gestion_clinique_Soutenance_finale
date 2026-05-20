import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymysql
import logging
import re
from typing import Optional
from core.connexion_db import DBConnection
from models.modele_produits import Produit
from datetime import datetime

DictCursor = pymysql.cursors.DictCursor


class ProduitDAO:
    """
    Classe DAO pour la gestion des produits.
    Architecture MVC : acces aux donnees uniquement.
    Table produits = registre catalogue des produits de la pharmacie.
    """

    def __init__(self):
        self.db = DBConnection()
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # METHODES CRUD
    # =========================================================================

    def ajouter(self, produit: Produit) -> bool:
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            produit.set_code_produit(self._generer_code(cursor, produit.get_type()))
            query = """
                INSERT INTO produits (
                    code_produit, libelle, type,
                    prix_achat_unitaire, prix_vente_unitaire
                ) VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                produit.get_code_produit(),
                produit.get_libelle(),
                produit.get_type(),
                produit.get_prix_achat_unitaire(),
                produit.get_prix_vente_unitaire()
            ))
            conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"[ProduitDAO] Erreur ajouter: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            self.db.close()

    def modifier(self, produit: Produit) -> bool:
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            query = """
                UPDATE produits SET
                    libelle=%s, type=%s,
                    prix_achat_unitaire=%s, prix_vente_unitaire=%s
                WHERE code_produit=%s
            """
            cursor.execute(query, (
                produit.get_libelle(),
                produit.get_type(),
                produit.get_prix_achat_unitaire(),
                produit.get_prix_vente_unitaire(),
                produit.get_code_produit()
            ))
            conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"[ProduitDAO] Erreur modifier: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            self.db.close()

    def supprimer(self, code_produit: str) -> bool:
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM produits WHERE code_produit=%s", (code_produit,))
            conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"[ProduitDAO] Erreur supprimer: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            self.db.close()

    # =========================================================================
    # METHODES DE RECUPERATION
    # =========================================================================

    def obtenir_par_code(self, code_produit: str):
        """Retourne un produit par son code."""
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM produits WHERE code_produit=%s", (code_produit,)
            )
            row = cursor.fetchone()
            return self._row_to_object(row) if row else None
        except Exception as e:
            self.logger.error(f"[ProduitDAO] Erreur obtenir_par_code: {e}", exc_info=True)
            return None
        finally:
            self.db.close()

    def lister_tous(self) -> list:
        """Retourne tous les produits du catalogue."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM produits ORDER BY libelle ASC")
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            self.logger.error(f"[ProduitDAO] Erreur lister_tous: {e}", exc_info=True)
            return []
        finally:
            self.db.close()

    def lister_par_type(self, type_produit: str) -> list:
        """Retourne les produits d'un type spécifique."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM produits WHERE type=%s ORDER BY libelle ASC",
                (type_produit,)
            )
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            self.logger.error(f"[ProduitDAO] Erreur lister_par_type: {e}", exc_info=True)
            return []
        finally:
            self.db.close()

    def rechercher_par_critere(self, critere: str) -> list:
        """Recherche des produits par code, libellé ou type."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            critere_like = f"%{critere}%"
            query = """
                SELECT * FROM produits
                WHERE code_produit LIKE %s
                   OR libelle LIKE %s
                   OR type LIKE %s
                ORDER BY libelle ASC
            """
            cursor.execute(query, (critere_like, critere_like, critere_like))
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Erreur rechercher_par_critere: {e}", exc_info=True)
            return []
        finally:
            self.db.close()
    
    def obtenir_prix_achat(self, code_produit: str) -> Optional[float]:
        """
        Retourne le prix d'achat unitaire d'un produit.
        Utilise pour auto-remplir le champ prix dans le panier.
        
        Args:
            code_produit: Code du produit
        
        Returns:
            float: Prix d'achat unitaire ou None si produit introuvable
        """
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT prix_achat_unitaire FROM produits WHERE code_produit=%s",
                (code_produit,)
            )
            row = cursor.fetchone()
            if row:
                return float(row['prix_achat_unitaire']) if isinstance(row, dict) else float(row[0])
            return None
        except Exception as e:
            self.logger.error(f"Erreur obtenir_prix_achat: {e}", exc_info=True)
            return None
        finally:
            self.db.close()
    
    def mettre_a_jour_prix_achat(self, code_produit: str, nouveau_prix: float) -> bool:
        """
        Met a jour le prix d'achat unitaire d'un produit.
        Appele apres validation du panier si le prix fournisseur est different.
        
        Args:
            code_produit: Code du produit
            nouveau_prix: Nouveau prix d'achat unitaire
        
        Returns:
            bool: True si mise a jour reussie, False sinon
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE produits SET prix_achat_unitaire=%s WHERE code_produit=%s",
                (nouveau_prix, code_produit)
            )
            conn.commit()
            self.logger.info(f"Prix achat produit {code_produit} mis a jour: {nouveau_prix}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur mettre_a_jour_prix_achat: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            self.db.close()

    # =========================================================================
    # METHODES PRIVEES
    # =========================================================================

    def _generer_code(self, cursor, type_produit: str) -> str:
        """Génère un code unique selon le type (ex: L0001, P0001, C0001)."""
        prefix_map = {
            'liquide':  'L',
            'pommade':  'P',
            'comprime': 'C',
        }
        prefix = prefix_map.get(type_produit, 'X')
        try:
            cursor.execute(
                "SELECT code_produit FROM produits WHERE code_produit LIKE %s ORDER BY code_produit DESC LIMIT 1",
                (f"{prefix}%",)
            )
            row = cursor.fetchone()
            if row:
                last_code = row['code_produit'] if isinstance(row, dict) else row[0]
                match = re.match(r'[A-Z](\d+)', last_code)
                if match:
                    return f"{prefix}{int(match.group(1)) + 1:04d}"
            return f"{prefix}0001"
        except Exception as e:
            print(f"Erreur génération code produit: {e}")
            return f"{prefix}" + datetime.now().strftime("%H%M%S")

    def _row_to_object(self, row) -> Produit:
        """Convertit une ligne de BDD en objet Produit."""
        return Produit(
            code_produit        = row['code_produit'],
            libelle             = row['libelle'],
            type_produit        = row['type'],
            prix_achat_unitaire = row['prix_achat_unitaire'],
            prix_vente_unitaire = row['prix_vente_unitaire']
        )