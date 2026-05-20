import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymysql
import logging
from typing import Optional, List, Dict, Tuple
from core.connexion_db import DBConnection
from datetime import datetime
from models.modele_panier_fourni import PanierFactureFourni
DictCursor = pymysql.cursors.DictCursor

logger = logging.getLogger(__name__)


class PanierFactureFourniDAO:
    """
    Classe DAO pour la gestion du panier d approvisionnement.
    Architecture MVC : acces aux donnees uniquement.

    Logique :
        facture_fournisseur   = entete  (cree avant par FactureFournisseurDAO)
        panier_facture_four = contenu (lignes rattachees a la facture)

    Chaque ajout / modification / suppression :
        â†’ recalcule automatiquement le montant_total de la facture
        â†’ met a jour le stock global du produit
    """

    def __init__(self):
        self.db = DBConnection()
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # METHODES CRUD
    # =========================================================================

    def ajouter(self, panier: PanierFactureFourni) -> bool:
        """
        Ajoute une ligne produit dans le panier d une facture existante.
        Recalcule le montant_total de la facture.
        Met a jour le stock global du produit.
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()

            # Generer le code de la ligne panier
            panier.code_panier_four = self._generer_code(cursor)

            # Inserer la ligne dans le panier
            query = """
                INSERT INTO panier_facture_four (
                    code_panier_four, designation, quantite_four,
                    prix_unitaire, date_expiration,
                    code_produit, code_facture_four, code_session
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                panier.code_panier_four,
                panier.designation,
                panier.quantite_four,
                panier.prix_unitaire,
                panier.date_expiration,
                panier.code_produit,
                panier.code_facture_four,
                panier.code_session
            ))

            # Recalculer le montant_total de la facture
            self._recalculer_montant_facture(cursor, panier.code_facture_four)

            # Mettre a jour le stock global
            self._update_stock(cursor, panier.code_produit, panier.quantite_four, panier.code_session)

            conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Erreur ajouter panier: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            self.db.close()

    def modifier(self, panier: PanierFactureFourni) -> bool:
        """
        Modifie une ligne du panier.
        Ajuste le stock selon la difference entre ancienne et nouvelle quantite.
        Recalcule le montant_total de la facture.
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()

            # Recuperer l ancienne quantite pour calculer la difference de stock
            cursor.execute(
                "SELECT quantite_four FROM panier_facture_four WHERE code_panier_four=%s",
                (panier.code_panier_four,)
            )
            ancienne_ligne = cursor.fetchone()
            ancienne_quantite = ancienne_ligne['quantite_four'] if ancienne_ligne else 0

            # Modifier la ligne
            query = """
                UPDATE panier_facture_four SET
                    designation=%s, quantite_four=%s,
                    prix_unitaire=%s, date_expiration=%s,
                    code_produit=%s
                WHERE code_panier_four=%s
            """
            cursor.execute(query, (
                panier.designation,
                panier.quantite_four,
                panier.prix_unitaire,
                panier.date_expiration,
                panier.code_produit,
                panier.code_panier_four
            ))

            # Recalculer le montant_total de la facture
            self._recalculer_montant_facture(cursor, panier.code_facture_four)

            # Ajuster le stock : appliquer uniquement la difference
            difference = panier.quantite_four - ancienne_quantite
            if difference != 0:
                self._update_stock(cursor, panier.code_produit, difference, panier.code_session)

            conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Erreur modifier panier: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            self.db.close()

    def supprimer(self, code_panier_four: str) -> bool:
        """
        Supprime une ligne du panier.
        Recalcule le montant_total de la facture apres suppression.
        Decremente le stock global du produit.
        Note : la facture_fournisseur n est jamais supprimee ici,
               c est le role de FactureFournisseurDAO.
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()

            # Recuperer la ligne avant suppression
            cursor.execute("""
                SELECT code_facture_four, code_produit, quantite_four, code_session
                FROM panier_facture_four
                WHERE code_panier_four=%s
            """, (code_panier_four,))
            ligne = cursor.fetchone()
            if not ligne:
                return False

            code_facture_four = ligne['code_facture_four']
            code_produit      = ligne['code_produit']
            quantite_four     = ligne['quantite_four']
            code_session      = ligne['code_session']

            # Supprimer la ligne
            cursor.execute(
                "DELETE FROM panier_facture_four WHERE code_panier_four=%s",
                (code_panier_four,)
            )

            # Recalculer le montant_total de la facture
            self._recalculer_montant_facture(cursor, code_facture_four)

            # Decrementer le stock global
            self._update_stock(cursor, code_produit, -quantite_four, code_session)

            conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Erreur supprimer panier: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            self.db.close()

    # =========================================================================
    # METHODES DE RECUPERATION
    # =========================================================================

    def obtenir_par_code(self, code_panier_four: str) -> Optional[PanierFactureFourni]:
        """Retourne une ligne panier par son code."""
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM panier_facture_four WHERE code_panier_four=%s",
                (code_panier_four,)
            )
            row = cursor.fetchone()
            return self._row_to_object(row) if row else None
        except Exception as e:
            self.logger.error(f"Erreur obtenir_par_code: {e}", exc_info=True)
            return None
        finally:
            self.db.close()

    def lister_par_facture(self, code_facture_four: str) -> List[PanierFactureFourni]:
        """
        Retourne toutes les lignes du panier pour une facture donnee.
        Jointure avec produits pour avoir libelle et type.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pf.*, p.libelle, p.type, p.prix_vente_unitaire
                FROM panier_facture_four pf
                INNER JOIN produits p ON pf.code_produit = p.code_produit
                WHERE pf.code_facture_four = %s
                ORDER BY pf.date_expiration ASC
            """, (code_facture_four,))
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Erreur lister_par_facture: {e}", exc_info=True)
            return []
        finally:
            self.db.close()

    def lister_par_session(self, code_session: str) -> List[PanierFactureFourni]:
        """Retourne toutes les lignes d approvisionnement d une session."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pf.*, p.libelle, p.type,
                       ff.code_fournisseur, ff.date_facture_four
                FROM panier_facture_four pf
                INNER JOIN produits p ON pf.code_produit = p.code_produit
                INNER JOIN facture_fournisseur ff ON pf.code_facture_four = ff.code_facture_four
                WHERE pf.code_session = %s
                ORDER BY ff.date_facture_four DESC
            """, (code_session,))
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Erreur lister_par_session: {e}", exc_info=True)
            return []
        finally:
            self.db.close()

    def lister_lots_par_produit(self, code_produit: str, code_session: str) -> List[Dict]:
        """
        Retourne tous les lots d un produit avec stock restant et statut par lot.
        stock_lot = entrees - sorties (prescriptions validées).
        Trie par date_expiration ASC pour visualiser les lots prioritaires.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    pf.code_produit,
                    pf.date_expiration,
                    p.libelle,
                    p.type,
                    SUM(pf.quantite_four) - COALESCE((
                        SELECT SUM(pp.quantite_prescript)
                        FROM prescription_produit pp
                        WHERE pp.code_produit = pf.code_produit
                          AND pp.date_expiration = pf.date_expiration
                          AND pp.code_session = pf.code_session
                    ), 0) AS stock_lot,
                    DATEDIFF(pf.date_expiration, CURDATE()) AS jours_restants,
                    CASE
                        WHEN pf.date_expiration < CURDATE()
                            THEN 'Expiré'
                        WHEN DATEDIFF(pf.date_expiration, CURDATE()) <= 30
                            THEN 'À Expirer'
                        ELSE 'Valide'
                    END AS statut_lot
                FROM panier_facture_four pf
                INNER JOIN produits p ON pf.code_produit = p.code_produit
                WHERE pf.code_produit = %s
                  AND pf.code_session = %s
                GROUP BY pf.date_expiration, pf.code_produit, p.libelle, p.type
                HAVING stock_lot > 0
                ORDER BY pf.date_expiration ASC
            """, (code_produit, code_session))
            return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Erreur lister_lots_par_produit: {e}", exc_info=True)
            return []
        finally:
            self.db.close()

    def rechercher_par_critere(self, critere: str, code_session: str) -> List[PanierFactureFourni]:
        """Recherche des lignes panier par designation ou code produit."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            critere_like = f"%{critere}%"
            cursor.execute("""
                SELECT pf.*, p.libelle, p.type
                FROM panier_facture_four pf
                INNER JOIN produits p ON pf.code_produit = p.code_produit
                WHERE pf.code_session = %s
                  AND (
                      pf.designation LIKE %s OR
                      pf.code_produit LIKE %s OR
                      p.libelle LIKE %s
                  )
                ORDER BY pf.date_expiration ASC
            """, (code_session, critere_like, critere_like, critere_like))
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Erreur rechercher_par_critere: {e}", exc_info=True)
            return []
        finally:
            self.db.close()

    # =========================================================================
    # METHODES STOCK & EXPIRATION
    # =========================================================================

    def get_stock(self, code_produit: str, code_session: str) -> Optional[Dict]:
        """Retourne la ligne de stock global d un produit pour la session."""
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.code_stock, s.code_produit, s.quantite_actuelle,
                       s.date_derniere_maj, s.code_session,
                       p.libelle, p.type, p.prix_vente_unitaire
                FROM stocks s
                INNER JOIN produits p ON s.code_produit = p.code_produit
                WHERE s.code_produit = %s
                  AND s.code_session = %s
            """, (code_produit, code_session))
            return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"Erreur get_stock: {e}", exc_info=True)
            return None
        finally:
            self.db.close()

    def produits_en_rupture_stock(self, code_session: str) -> List[Dict]:
        """Retourne les produits avec quantite_actuelle <= 5 pour la session."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.code_produit, s.quantite_actuelle, s.date_derniere_maj,
                       p.libelle, p.type, p.prix_vente_unitaire
                FROM stocks s
                INNER JOIN produits p ON s.code_produit = p.code_produit
                WHERE s.code_session = %s
                  AND s.quantite_actuelle <= 5
                ORDER BY s.quantite_actuelle ASC, p.libelle ASC
            """, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Erreur produits_en_rupture_stock: {e}", exc_info=True)
            return []
        finally:
            self.db.close()

    def produits_stock_faible(self, code_session: str, seuil: int = 10) -> List[Dict]:
        """Retourne les produits avec stock > 0 mais sous le seuil."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.code_produit, s.quantite_actuelle, s.date_derniere_maj,
                       p.libelle, p.type, p.prix_vente_unitaire
                FROM stocks s
                INNER JOIN produits p ON s.code_produit = p.code_produit
                WHERE s.code_session = %s
                  AND s.quantite_actuelle > 0
                  AND s.quantite_actuelle < %s
                ORDER BY s.quantite_actuelle ASC
            """, (code_session, seuil))
            return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Erreur produits_stock_faible: {e}", exc_info=True)
            return []
        finally:
            self.db.close()

    def lots_a_expirer(self, code_session: str, jours: int = 30) -> List[Dict]:
        """
        Retourne les lots dont l expiration est dans moins de jours
        avec leur stock restant > 0.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pf.code_produit, pf.date_expiration,
                       p.libelle, p.type,
                       DATEDIFF(pf.date_expiration, CURDATE()) AS jours_restants,
                       SUM(pf.quantite_four) -
                           COALESCE((
                               {sorties_validees}
                           ), 0) AS stock_lot
                FROM panier_facture_four pf
                INNER JOIN produits p ON pf.code_produit = p.code_produit
                WHERE pf.code_session = %s
                  AND DATEDIFF(pf.date_expiration, CURDATE()) BETWEEN 0 AND %s
                GROUP BY pf.code_produit, pf.date_expiration
                HAVING stock_lot > 0
                ORDER BY pf.date_expiration ASC
            """.format(
                sorties_validees=self._sous_requete_sorties_lot_validees()
            ), (code_session, code_session, jours))
            return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Erreur lots_a_expirer: {e}", exc_info=True)
            return []
        finally:
            self.db.close()

    def lots_expires(self, code_session: str) -> List[Dict]:
        """Retourne les lots dont la date expiration est depassee avec stock > 0."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pf.code_produit, pf.date_expiration,
                       p.libelle, p.type,
                       DATEDIFF(pf.date_expiration, CURDATE()) AS jours_restants,
                       SUM(pf.quantite_four) -
                           COALESCE((
                               {sorties_validees}
                           ), 0) AS stock_lot
                FROM panier_facture_four pf
                INNER JOIN produits p ON pf.code_produit = p.code_produit
                WHERE pf.code_session = %s
                  AND pf.date_expiration < CURDATE()
                GROUP BY pf.code_produit, pf.date_expiration
                HAVING stock_lot > 0
                ORDER BY pf.date_expiration ASC
            """.format(
                sorties_validees=self._sous_requete_sorties_lot_validees()
            ), (code_session, code_session))
            return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Erreur lots_expires: {e}", exc_info=True)
            return []
        finally:
            self.db.close()

    # =========================================================================
    # METHODES STATISTIQUES CARDS
    # =========================================================================

    def nombre_ruptures(self, code_session: str) -> int:
        """Card Rupture de Stock : COUNT produits avec quantite <= 5 (seuil critique)."""
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) AS total FROM stocks
                WHERE code_session = %s
                  AND quantite_actuelle <= 5
            """, (code_session,))
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            self.logger.error(f"Erreur nombre_ruptures: {e}", exc_info=True)
            return 0
        finally:
            self.db.close()

    def nombre_lots_a_expirer(self, code_session: str, jours: int = 30) -> int:
        """Card Ã€ Expirer : COUNT lots dont expiration est dans moins de jours."""
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(DISTINCT code_produit, date_expiration) AS total
                FROM panier_facture_four
                WHERE code_session = %s
                  AND DATEDIFF(date_expiration, CURDATE()) BETWEEN 0 AND %s
            """, (code_session, jours))
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            self.logger.error(f"Erreur nombre_lots_a_expirer: {e}", exc_info=True)
            return 0
        finally:
            self.db.close()

    def nombre_lots_expires(self, code_session: str) -> int:
        """Card ExpirÃ©s : COUNT lots dont la date est depassee."""
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(DISTINCT code_produit, date_expiration) AS total
                FROM panier_facture_four
                WHERE code_session = %s
                  AND date_expiration < CURDATE()
            """, (code_session,))
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            self.logger.error(f"Erreur nombre_lots_expires: {e}", exc_info=True)
            return 0
        finally:
            self.db.close()

    def valeur_stock_total(self, code_session: str) -> float:
        """Card Valeur Stock : SUM(quantite_actuelle * prix_achat_unitaire)."""
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(s.quantite_actuelle * p.prix_achat_unitaire), 0) AS total
                FROM stocks s
                INNER JOIN produits p ON s.code_produit = p.code_produit
                WHERE s.code_session = %s
            """, (code_session,))
            result = cursor.fetchone()
            return float(result['total']) if result else 0.0
        except Exception as e:
            self.logger.error(f"Erreur valeur_stock_total: {e}", exc_info=True)
            return 0.0
        finally:
            self.db.close()

    # =========================================================================
    # METHODE FEFO
    # =========================================================================

    def get_date_expiration_fefo(self, code_produit: str, code_session: str, quantite: int) -> Optional[datetime]:
        """
        Retourne la date_expiration du lot prioritaire selon le principe FEFO
        (First Expired First Out).
        Appelee par PrescriptionDAO lors de la validation d une prescription.
        Garantit que le lot selectionne a suffisamment de stock.
        Le pharmacien ne voit rien â€” le systeme choisit automatiquement.
        """
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pf.date_expiration,
                       SUM(pf.quantite_four) -
                           COALESCE((
                               {sorties_validees}
                           ), 0) AS stock_lot
                FROM panier_facture_four pf
                WHERE pf.code_produit = %s
                  AND pf.code_session = %s
                GROUP BY pf.date_expiration
                HAVING stock_lot >= %s
                ORDER BY pf.date_expiration ASC
                LIMIT 1
            """.format(
                sorties_validees=self._sous_requete_sorties_lot_validees()
            ), (code_produit, code_session, code_session, quantite))
            row = cursor.fetchone()
            return row['date_expiration'] if row else None
        except Exception as e:
            self.logger.error(f"Erreur get_date_expiration_fefo: {e}", exc_info=True)
            return None
        finally:
            self.db.close()

    # =========================================================================
    # METHODES PRIVEES
    # =========================================================================

    def _sous_requete_sorties_lot_validees(self) -> str:
        """
        Ne compte que les prescriptions dont le stock global a deja ete decremente.
        Simplifie : compte toutes les prescriptions validees.
        """
        return """
            SELECT SUM(pp.quantite_prescript)
            FROM prescription_produit pp
            WHERE pp.code_produit = pf.code_produit
              AND pp.date_expiration = pf.date_expiration
              AND pp.code_session = %s
        """

    def _recalculer_montant_facture(self, cursor, code_facture_four: str) -> None:
        """
        Recalcule et met a jour le montant_total dans facture_fournisseur.
        montant_total = SUM(quantite_four * prix_unitaire) de toutes les lignes.
        """
        cursor.execute("""
            SELECT COALESCE(SUM(quantite_four * prix_unitaire), 0) AS total
            FROM panier_facture_four
            WHERE code_facture_four = %s
        """, (code_facture_four,))
        result = cursor.fetchone()
        total = float(result['total']) if result else 0.0

        cursor.execute("""
            UPDATE facture_fournisseur
            SET montant_total = %s
            WHERE code_facture_four = %s
        """, (total, code_facture_four))

    def _update_stock(self, cursor, code_produit: str, quantite: int, code_session: str) -> None:
        """
        Met a jour la quantite dans la table stock.
        quantite positive â†’ entree (approvisionnement)
        quantite negative â†’ sortie (suppression de ligne panier)
        INSERT si premiere entree pour ce produit/session, UPDATE sinon.
        """
        # VÃ©rifier si le produit existe dÃ©jÃ  dans le stock pour cette session
        cursor.execute("""
            SELECT code_stock, quantite_actuelle 
            FROM stocks 
            WHERE code_produit = %s AND code_session = %s
        """, (code_produit, code_session))
        
        stock_existant = cursor.fetchone()
        
        if stock_existant:
            # UPDATE : Le produit existe dÃ©jÃ 
            cursor.execute("""
                UPDATE stocks 
                SET quantite_actuelle = quantite_actuelle + %s,
                    date_derniere_maj = NOW()
                WHERE code_produit = %s AND code_session = %s
            """, (quantite, code_produit, code_session))
        else:
            # INSERT : PremiÃ¨re entrÃ©e pour ce produit/session
            # GÃ©nÃ©rer un code_stock unique
            nouveau_code = self._generer_code_stock(cursor)
            
            cursor.execute("""
                INSERT INTO stocks (code_stock, code_produit, quantite_actuelle, date_derniere_maj, code_session)
                VALUES (%s, %s, %s, NOW(), %s)
            """, (nouveau_code, code_produit, quantite, code_session))
    
    def _generer_code_stock(self, cursor) -> str:
        """Génère un code unique pour la table stocks (ex: STK001)."""
        try:
            # Utiliser MAX(CAST(...)) pour un tri numérique fiable
            cursor.execute("""
                SELECT COALESCE(MAX(CAST(SUBSTRING(code_stock, 4) AS UNSIGNED)), 0) AS max_num
                FROM stocks
                WHERE code_stock REGEXP '^STK[0-9]+$'
            """)
            row = cursor.fetchone()
            max_num = int(row['max_num']) if row and row['max_num'] else 0
            return f"STK{max_num + 1:03d}"
        except Exception as e:
            self.logger.error(f"Erreur génération code stock: {e}", exc_info=True)
            from datetime import datetime
            return "STK" + datetime.now().strftime("%H%M%S")
        
    def nombre_lots_valides_par_produit(self, code_produit: str, code_session: str) -> int:
        """Nombre de lots valides (expiration loin) pour un produit specifique."""
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM (
                    SELECT
                        pf.date_expiration,
                        GREATEST(
                            SUM(pf.quantite_four) - COALESCE((
                                {sorties_validees}
                            ), 0),
                            0
                        ) AS stock_lot
                    FROM panier_facture_four pf
                    WHERE pf.code_produit = %s
                      AND pf.code_session = %s
                      AND DATEDIFF(pf.date_expiration, CURDATE()) > 30
                    GROUP BY pf.date_expiration
                ) AS lots
                WHERE lots.stock_lot > 0
            """.format(
                sorties_validees=self._sous_requete_sorties_lot_validees()
            ), (code_produit, code_session, code_session))
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            self.logger.error(f"Erreur nombre_lots_valides_par_produit: {e}", exc_info=True)
            return 0
        finally:
            self.db.close()

    def nombre_lots_a_expirer_par_produit(self, code_produit: str, code_session: str, jours: int = 30) -> int:
        """Nombre de lots bientot en expiration pour un produit specifique."""
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM (
                    SELECT
                        pf.date_expiration,
                        GREATEST(
                            SUM(pf.quantite_four) - COALESCE((
                                {sorties_validees}
                            ), 0),
                            0
                        ) AS stock_lot
                    FROM panier_facture_four pf
                    WHERE pf.code_produit = %s
                      AND pf.code_session = %s
                      AND DATEDIFF(pf.date_expiration, CURDATE()) BETWEEN 0 AND %s
                    GROUP BY pf.date_expiration
                ) AS lots
                WHERE lots.stock_lot > 0
            """.format(
                sorties_validees=self._sous_requete_sorties_lot_validees()
            ), (code_produit, code_session, code_session, jours))
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            self.logger.error(f"Erreur nombre_lots_a_expirer_par_produit: {e}", exc_info=True)
            return 0
        finally:
            self.db.close()

    def nombre_lots_expires_par_produit(self, code_produit: str, code_session: str) -> int:
        """Nombre de lots expires pour un produit specifique."""
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM (
                    SELECT
                        pf.date_expiration,
                        GREATEST(
                            SUM(pf.quantite_four) - COALESCE((
                                {sorties_validees}
                            ), 0),
                            0
                        ) AS stock_lot
                    FROM panier_facture_four pf
                    WHERE pf.code_produit = %s
                      AND pf.code_session = %s
                      AND pf.date_expiration < CURDATE()
                    GROUP BY pf.date_expiration
                ) AS lots
                WHERE lots.stock_lot > 0
            """.format(
                sorties_validees=self._sous_requete_sorties_lot_validees()
            ), (code_produit, code_session, code_session))
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            self.logger.error(f"Erreur nombre_lots_expires_par_produit: {e}", exc_info=True)
            return 0
        finally:
            self.db.close()
            
    def valeur_lots_a_expirer(self, code_session: str, jours: int = 30) -> float:
        """
        Retourne la valeur financiere des lots bientot expires.
        Repond a la question du jury : 'Combien va-t-on perdre si ces lots expirent ?'
        Calcul : SUM(stock_lot * prix_achat_unitaire) pour les lots a expirer.
        """
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(lots.stock_lot * lots.prix_achat_unitaire), 0) AS valeur_a_perdre
                FROM (
                    SELECT
                        pf.code_produit,
                        pf.date_expiration,
                        p.prix_achat_unitaire,
                        GREATEST(
                            SUM(pf.quantite_four) - COALESCE((
                                {sorties_validees}
                            ), 0),
                            0
                        ) AS stock_lot
                    FROM panier_facture_four pf
                    INNER JOIN produits p ON pf.code_produit = p.code_produit
                    WHERE pf.code_session = %s
                      AND DATEDIFF(pf.date_expiration, CURDATE()) BETWEEN 0 AND %s
                    GROUP BY pf.code_produit, pf.date_expiration, p.prix_achat_unitaire
                ) AS lots
                WHERE lots.stock_lot > 0
            """.format(
                sorties_validees=self._sous_requete_sorties_lot_validees()
            ), (code_session, code_session, jours))
            row = cursor.fetchone()
            return float(row['valeur_a_perdre']) if row and row['valeur_a_perdre'] is not None else 0.0
        except Exception as e:
            self.logger.error(f"Erreur valeur_lots_a_expirer: {e}", exc_info=True)
            return 0.0
        finally:
            self.db.close()

    def top_produits_consommes(self, code_session: str, limite: int = 10) -> List[Dict]:
        """
        Retourne les produits les plus prescrits pour une session.
        Repond a la question du jury : 'Comment savez-vous quels produits commander en priorite ?'
        Utile pour anticiper les reapprovisionnements.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pp.code_produit,
                    p.libelle,
                    p.type,
                    SUM(pp.quantite_prescript) AS total_consomme,
                    s.quantite_actuelle        AS stock_restant
                FROM prescription_produit pp
                INNER JOIN visite v ON pp.code_visite = v.code_visite
                INNER JOIN produits p ON pp.code_produit = p.code_produit
                LEFT JOIN stocks s ON pp.code_produit = s.code_produit
                                AND s.code_session  = pp.code_session
                WHERE pp.code_session = %s
                  AND v.statut_patient IN ('Attente payement', 'Libéré')
                GROUP BY pp.code_produit, p.libelle, p.type, s.quantite_actuelle
                ORDER BY total_consomme DESC
                LIMIT %s
            """, (code_session, limite))
            return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Erreur top_produits_consommes: {e}", exc_info=True)
            return []
        finally:
            self.db.close()
    
    def obtenir_quantites_par_statut(self, code_session: str) -> Dict[str, int]:
        """Retourne les quantitÃ©s par statut d'expiration (expirÃ©, bientÃ´t, valide)."""
        conn = self.db.connect()
        if not conn:
            return {'qte_expire': 0, 'qte_bientot': 0, 'qte_valide': 0}
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    SUM(CASE 
                        WHEN lots.date_expiration < CURDATE() THEN lots.stock_lot
                        ELSE 0
                    END) AS qte_expire,
                    SUM(CASE 
                        WHEN DATEDIFF(lots.date_expiration, CURDATE()) BETWEEN 0 AND 30 THEN lots.stock_lot
                        ELSE 0
                    END) AS qte_bientot,
                    SUM(CASE 
                        WHEN DATEDIFF(lots.date_expiration, CURDATE()) > 30 THEN lots.stock_lot
                        ELSE 0
                    END) AS qte_valide
                FROM (
                    SELECT
                        pf.code_produit,
                        pf.date_expiration,
                        GREATEST(
                            SUM(pf.quantite_four) - COALESCE((
                                {sorties_validees}
                            ), 0),
                            0
                        ) AS stock_lot
                    FROM panier_facture_four pf
                    INNER JOIN stocks s
                        ON s.code_produit = pf.code_produit
                       AND s.code_session = pf.code_session
                       AND s.quantite_actuelle > 0
                    WHERE pf.code_session = %s
                    GROUP BY pf.code_produit, pf.date_expiration
                ) AS lots
                WHERE lots.stock_lot > 0
            """.format(
                sorties_validees=self._sous_requete_sorties_lot_validees()
            ), (code_session, code_session))
            row = cursor.fetchone()
            if row:
                return {
                    'qte_expire': int(row.get('qte_expire') or 0),
                    'qte_bientot': int(row.get('qte_bientot') or 0),
                    'qte_valide': int(row.get('qte_valide') or 0)
                }
            return {'qte_expire': 0, 'qte_bientot': 0, 'qte_valide': 0}
        except Exception as e:
            self.logger.error(f"Erreur obtenir_quantites_par_statut: {e}", exc_info=True)
            return {'qte_expire': 0, 'qte_bientot': 0, 'qte_valide': 0}
        finally:
            self.db.close()
    
    def obtenir_quantites_par_type(self, code_session: str) -> Dict[str, int]:
        """Retourne les quantitÃ©s par type de produit (Liquide, Pommade, ComprimÃ©)."""
        conn = self.db.connect()
        if not conn:
            return {'Liquide': 0, 'Pommade': 0, 'Comprimé': 0}
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.type, SUM(s.quantite_actuelle) as total_quantite
                FROM stocks s
                INNER JOIN produits p ON s.code_produit = p.code_produit
                WHERE s.code_session = %s
                GROUP BY p.type
            """, (code_session,))
            resultats = cursor.fetchall()
            
            stock_par_type = {'Liquide': 0, 'Pommade': 0, 'Comprimé': 0}
            for row in resultats:
                type_produit = (row.get('type') or row.get('Type') or '').strip().capitalize()
                quantite = int(row.get('total_quantite') or 0)
                
                if type_produit in stock_par_type:
                    stock_par_type[type_produit] = quantite
                else:
                    type_lower = type_produit.lower()
                    if 'liquide' in type_lower:
                        stock_par_type['Liquide'] += quantite
                    elif 'pommade' in type_lower:
                        stock_par_type['Pommade'] += quantite
                    elif 'comprim' in type_lower:
                        stock_par_type['Comprimé'] += quantite
            
            return stock_par_type
        except Exception as e:
            self.logger.error(f"Erreur obtenir_quantites_par_type: {e}", exc_info=True)
            return {'Liquide': 0, 'Pommade': 0, 'ComprimÃ©': 0}
        finally:
            self.db.close()
    
    def obtenir_stock_detaille_par_produit(self, code_session: str, limite: int = 20) -> List[Dict]:
        """Retourne le stock dÃ©taillÃ© par produit avec dÃ©signation, type et quantitÃ©."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    p.libelle as designation,
                    p.type,
                    s.quantite_actuelle as quantite_totale
                FROM stocks s
                INNER JOIN produits p ON s.code_produit = p.code_produit
                WHERE s.code_session = %s
                ORDER BY s.quantite_actuelle DESC
                LIMIT %s
            """, (code_session, limite))
            resultats = cursor.fetchall()
            
            stock_detaille = []
            for row in resultats:
                designation = row.get('designation') or row.get('Designation') or 'Produit inconnu'
                type_produit = (row.get('type') or row.get('Type') or 'ComprimÃ©').strip().capitalize()
                quantite = int(row.get('quantite_totale') or 0)
                
                stock_detaille.append({
                    'designation': designation,
                    'type': type_produit,
                    'quantite': quantite
                })
            
            return stock_detaille
        except Exception as e:
            self.logger.error(f"Erreur obtenir_stock_detaille_par_produit: {e}", exc_info=True)
            return []
        finally:
            self.db.close()

    def _generer_code(self, cursor) -> str:
        """Genere un code unique pour panier_facture_four (ex: PFF001)."""
        try:
            cursor.execute(
                "SELECT code_panier_four FROM panier_facture_four ORDER BY code_panier_four DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                last_code = row['code_panier_four'] if isinstance(row, dict) else row[0]
                last_num  = int(last_code[3:])
                return f"PFF{last_num + 1:03d}"
            return "PFF001"
        except Exception as e:
            self.logger.error(f"Erreur generation code panier: {e}", exc_info=True)
            return "PFF" + datetime.now().strftime("%H%M%S")

    def _row_to_object(self, row) -> PanierFactureFourni:
        """Convertit une ligne de BDD en objet PanierFactureFourni."""
        designation_value = (
            row.get('designation') or
            row.get('Designation') or
            row.get('libelle') or
            row.get('Libelle') or
            ''
        )

        obj = PanierFactureFourni(
            code_panier_four  = row.get('code_panier_four', ''),
            designation       = designation_value,
            quantite_four     = row.get('quantite_four', 0),
            prix_unitaire     = row.get('prix_unitaire', 0.0),
            date_expiration   = row.get('date_expiration'),
            code_produit      = row.get('code_produit', ''),
            code_facture_four = row.get('code_facture_four', ''),
            code_session      = row.get('code_session', '')
        )

        # Attributs dynamiques issus des JOINs
        # PrÃ©sents quand la requÃªte fait un JOIN avec produits
        obj.type    = row.get('type') or row.get('Type') or 'â€”'
        obj.libelle = row.get('libelle') or row.get('Libelle') or ''

        return obj
        
    def verifier_stock_suffisant(self, code_produit: str, code_session: str, quantite_demandee: int) -> Tuple[bool, str]:
        """
        Verifie avant toute prescription si le stock est suffisant.
        Appelee par PrescriptionControleur avant de valider.
        Retourne (True, stock_dispo) ou (False, message d erreur).
        Repond a la question du jury : 'Que se passe-t-il si le stock est a 0 ?'
        """
        conn = self.db.connect()
        if not conn:
            return False, "Connexion impossible"
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.quantite_actuelle, p.libelle
                FROM stocks s
                INNER JOIN produits p ON s.code_produit = p.code_produit
                WHERE s.code_produit = %s
                AND s.code_session = %s
            """, (code_produit, code_session))
            row = cursor.fetchone()
            if not row:
                return False, "Produit introuvable en stock"
            dispo = row['quantite_actuelle']
            if dispo <= 0:
                return False, f"Rupture de stock : {row['libelle']} est epuise"
            if dispo < quantite_demandee:
                return False, f"Stock insuffisant : seulement {dispo} unite(s) disponible(s) pour {row['libelle']}"
            return True, dispo
        except Exception as e:
            self.logger.error(f"Erreur verifier_stock_suffisant: {e}", exc_info=True)
            return False, "Erreur verification stock"
        finally:
            self.db.close()

    def historique_approvisionnements_par_fournisseur(self, code_fournisseur: str, code_session: str) -> List[Dict]:
        """
        Retourne l historique complet des approvisionnements d un fournisseur.
        Repond a la question du jury : 'Comment tracez-vous vos achats par fournisseur ?'
        Retourne : par facture â†’ les lignes produits avec quantites et montants.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    ff.code_facture_four,
                    ff.date_facture_four,
                    ff.montant_total,
                    ff.mode_payement,
                    f.nom              AS fournisseur_nom,
                    f.prenom           AS fournisseur_prenom,
                    pf.code_produit,
                    pf.designation,
                    pf.quantite_four,
                    pf.prix_unitaire,
                    pf.date_expiration,
                    (pf.quantite_four * pf.prix_unitaire) AS sous_total,
                    p.type
                FROM facture_fournisseur ff
                INNER JOIN fournisseur f             ON ff.code_fournisseur = f.code_fournisseur
                INNER JOIN panier_facture_four pf  ON ff.code_facture_four = pf.code_facture_four
                INNER JOIN produits p                ON pf.code_produit = p.code_produit
                WHERE ff.code_fournisseur = %s
                AND ff.code_session     = %s
                ORDER BY ff.date_facture_four DESC, pf.designation ASC
            """, (code_fournisseur, code_session))
            return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Erreur historique_approvisionnements_par_fournisseur: {e}", exc_info=True)
            return []
        finally:
            self.db.close()

    def comparaison_entrees_sorties_par_mois(self, code_session: str) -> Dict[str, Dict[str, int]]:
        """
        Compare les quantites entrees (approvisionnements) et sorties (prescriptions) par mois.
        Repond a la question du jury : 'Comment prouvez-vous la coherence de votre systeme ?'
        Format retourne :
        {
            'Jan':  {'entrees': 150, 'sorties': 80},
            'Fev':  {'entrees': 200, 'sorties': 120},
            ...
        }
        """
        stats = {
            'Jan':  {'entrees': 0, 'sorties': 0},
            'Fev':  {'entrees': 0, 'sorties': 0},
            'Mar':  {'entrees': 0, 'sorties': 0},
            'Avr':  {'entrees': 0, 'sorties': 0},
            'Mai':  {'entrees': 0, 'sorties': 0},
            'Juin': {'entrees': 0, 'sorties': 0},
            'Juil': {'entrees': 0, 'sorties': 0},
            'Aout': {'entrees': 0, 'sorties': 0},
            'Sep':  {'entrees': 0, 'sorties': 0},
            'Oct':  {'entrees': 0, 'sorties': 0},
            'Nov':  {'entrees': 0, 'sorties': 0},
            'Dec':  {'entrees': 0, 'sorties': 0}
        }
        mois_mapping = {
            1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Avr',  5: 'Mai',  6: 'Juin',
            7: 'Juil', 8: 'Aout', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }
        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()

            # Entrees : quantites approvisionnees par mois
            cursor.execute("""
                SELECT MONTH(ff.date_facture_four) AS num_mois,
                    SUM(pf.quantite_four)       AS total_entrees
                FROM panier_facture_four pf
                INNER JOIN facture_fournisseur ff ON pf.code_facture_four = ff.code_facture_four
                WHERE pf.code_session = %s
                GROUP BY MONTH(ff.date_facture_four)
            """, (code_session,))
            for row in cursor.fetchall():
                m = row['num_mois']
                if m in mois_mapping:
                    stats[mois_mapping[m]]['entrees'] = row['total_entrees']

            # Sorties : quantites prescrites par mois
            # La table prescription_produit ne porte pas date_prescription.
            # On s'appuie sur la date_consultation via le lien code_consultation.
            cursor.execute("""
                SELECT MONTH(c.date_consultation) AS num_mois,
                    SUM(pp.quantite_prescript) AS total_sorties
                FROM prescription_produit pp
                INNER JOIN consultation c
                    ON pp.code_consultation = c.code
                INNER JOIN visite v
                    ON pp.code_visite = v.code_visite
                WHERE pp.code_session = %s
                  AND c.date_consultation IS NOT NULL
                  AND v.statut_patient IN ('Attente payement', 'Libéré')
                GROUP BY MONTH(c.date_consultation)
            """, (code_session,))
            for row in cursor.fetchall():
                m = row['num_mois']
                if m in mois_mapping:
                    stats[mois_mapping[m]]['sorties'] = row['total_sorties']

            return stats
        except Exception as e:
            self.logger.error(f"Erreur comparaison_entrees_sorties_par_mois: {e}", exc_info=True)
            return stats
        finally:
            self.db.close()

