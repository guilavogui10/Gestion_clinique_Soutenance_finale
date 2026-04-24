import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymysql
import logging
from typing import Optional, List, Dict
from core.connexion_db import DBConnection
from models.modele_factureFournisseur import FactureFournisseur
from datetime import datetime

DictCursor = pymysql.cursors.DictCursor


class FactureFournisseurDAO:
    """
    Classe DAO pour la gestion des factures fournisseurs.
    Architecture MVC : accès aux données uniquement.

    Logique :
        FactureFournisseur = entête de la facture d'approvisionnement.
        Créée au moment où l'utilisateur sélectionne le fournisseur.
        Le Montant_total est recalculé automatiquement par PanierFactureFourniDAO
        à chaque ajout / modification / suppression de ligne panier.
        Finalisée (mode_payement, telephone) à la validation.

    Table fournisseurs :
        - email_fournisseur  (clé primaire)
        - nom_entreprise
        - telephone
        - adresse
    """

    def __init__(self):
        self.db = DBConnection()
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # METHODES CRUD
    # =========================================================================

    def creer(self, facture: FactureFournisseur) -> bool:
        """
        Crée une nouvelle entête de facture fournisseur.
        Appelée une seule fois quand l'utilisateur sélectionne le fournisseur.
        Montant_total démarre à 0 et sera recalculé par PanierFactureFourniDAO.
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            facture.code_facture_four = self._generer_code(cursor)
            cursor.execute("""
                INSERT INTO facture_fournisseur (
                    code_facture_four, Montant_total, mode_payement,
                    telephone, date_facture_four,
                    code_fournisseur, code_session
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                facture.code_facture_four,
                0.0,
                facture.mode_payement,
                facture.telephone,
                facture.date_facture_four,
                facture.code_fournisseur,
                facture.code_session
            ))
            conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Erreur creer facture fournisseur: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            self.db.close()

    def finaliser(self, facture: FactureFournisseur) -> bool:
        """
        Finalise la facture en renseignant le mode de paiement et le téléphone.
        Appelée quand l'utilisateur valide la livraison.
        Ne touche pas au Montant_total : il est géré par PanierFactureFourniDAO.
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE facture_fournisseur SET
                    mode_payement = %s,
                    telephone     = %s
                WHERE code_facture_four = %s
            """, (
                facture.mode_payement,
                facture.telephone,
                facture.code_facture_four
            ))
            conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Erreur finaliser facture fournisseur: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            self.db.close()

    def modifier(self, facture: FactureFournisseur) -> bool:
        """
        Modifie les informations de la facture (fournisseur, mode paiement, téléphone).
        Ne touche pas au Montant_total : il est géré par PanierFactureFourniDAO.
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE facture_fournisseur SET
                    mode_payement    = %s,
                    telephone        = %s,
                    code_fournisseur = %s
                WHERE code_facture_four = %s
            """, (
                facture.mode_payement,
                facture.telephone,
                facture.code_fournisseur,
                facture.code_facture_four
            ))
            conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Erreur modifier facture fournisseur: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            self.db.close()

    def supprimer(self, code_facture_four: str) -> bool:
        """
        Supprime une facture fournisseur et toutes ses lignes panier en cascade.
        Le stock est décrémenté pour chaque ligne supprimée.
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()

            # Récupérer toutes les lignes panier avant suppression
            cursor.execute("""
                SELECT code_produit, quantite_four, code_session
                FROM panier_facture_four
                WHERE code_facture_four = %s
            """, (code_facture_four,))
            lignes = cursor.fetchall()

            # Décrémenter le stock pour chaque ligne
            for ligne in lignes:
                cursor.execute("""
                    UPDATE stocks SET
                        quantite_actuelle = quantite_actuelle - %s,
                        date_derniere_maj = NOW()
                    WHERE code_produit = %s
                      AND code_session  = %s
                """, (ligne['quantite_four'], ligne['code_produit'], ligne['code_session']))

            # Supprimer les lignes panier
            cursor.execute(
                "DELETE FROM panier_facture_four WHERE code_facture_four = %s",
                (code_facture_four,)
            )

            # Supprimer la facture
            cursor.execute(
                "DELETE FROM facture_fournisseur WHERE code_facture_four = %s",
                (code_facture_four,)
            )

            conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Erreur supprimer facture fournisseur: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            self.db.close()

    # =========================================================================
    # METHODES DE RECUPERATION
    # =========================================================================

    def obtenir_par_code(self, code_facture_four: str) -> Optional[FactureFournisseur]:
        """Retourne une facture fournisseur par son code."""
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM facture_fournisseur WHERE code_facture_four = %s",
                (code_facture_four,)
            )
            row = cursor.fetchone()
            return self._row_to_object(row) if row else None
        except Exception as e:
            self.logger.error(f"Erreur obtenir_par_code facture fournisseur: {e}", exc_info=True)
            return None
        finally:
            self.db.close()

    def lister_par_session(self, code_session: str) -> List[FactureFournisseur]:
        """
        Retourne toutes les factures fournisseurs d'une session.
        Jointure avec fournisseurs sur email_fournisseur (clé primaire).
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ff.*,
                       f.nom_entreprise AS fournisseur_nom,
                       f.telephone      AS fournisseur_telephone
                FROM facture_fournisseur ff
                LEFT JOIN fournisseurs f ON ff.code_fournisseur = f.email_fournisseur
                WHERE ff.code_session = %s
                ORDER BY ff.date_facture_four DESC
            """, (code_session,))
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Erreur lister_par_session facture fournisseur: {e}", exc_info=True)
            return []
        finally:
            self.db.close()

    def lister_par_fournisseur(self, code_fournisseur: str, code_session: str) -> List[FactureFournisseur]:
        """Retourne toutes les factures d'un fournisseur pour une session."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM facture_fournisseur
                WHERE code_fournisseur = %s
                  AND code_session     = %s
                ORDER BY date_facture_four DESC
            """, (code_fournisseur, code_session))
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Erreur lister_par_fournisseur: {e}", exc_info=True)
            return []
        finally:
            self.db.close()

    def facture_complete(self, code_facture_four: str) -> Optional[Dict]:
        """
        Retourne la facture avec toutes ses lignes panier et infos fournisseur.
        Utilisée pour l'affichage du détail et l'impression.
        """
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()

            # En-tête avec infos fournisseur
            cursor.execute("""
                SELECT ff.*,
                       f.nom_entreprise AS fournisseur_nom,
                       f.telephone      AS fournisseur_telephone,
                       f.adresse        AS fournisseur_adresse
                FROM facture_fournisseur ff
                LEFT JOIN fournisseurs f ON ff.code_fournisseur = f.email_fournisseur
                WHERE ff.code_facture_four = %s
            """, (code_facture_four,))
            entete = cursor.fetchone()

            if not entete:
                return None

            # Lignes du panier avec désignation et type produit
            cursor.execute("""
                SELECT pf.*,
                       p.libelle AS designation,
                       p.type    AS type_produit
                FROM panier_facture_four pf
                INNER JOIN produits p ON pf.code_produit = p.code_produit
                WHERE pf.code_facture_four = %s
                ORDER BY pf.date_expiration ASC
            """, (code_facture_four,))
            lignes = cursor.fetchall()

            return {
                'entete': dict(entete),
                'lignes': [dict(l) for l in lignes]
            }
        except Exception as e:
            self.logger.error(f"Erreur facture_complete: {e}", exc_info=True)
            return None
        finally:
            self.db.close()

    def rechercher_par_critere(self, critere: str, code_session: str) -> List[FactureFournisseur]:
        """Recherche des factures par code facture ou nom d'entreprise fournisseur."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            critere_like = f"%{critere}%"
            cursor.execute("""
                SELECT ff.*,
                       f.nom_entreprise AS fournisseur_nom
                FROM facture_fournisseur ff
                LEFT JOIN fournisseurs f ON ff.code_fournisseur = f.email_fournisseur
                WHERE ff.code_session = %s
                  AND (
                      ff.code_facture_four LIKE %s OR
                      f.nom_entreprise     LIKE %s
                  )
                ORDER BY ff.date_facture_four DESC
            """, (code_session, critere_like, critere_like))
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Erreur rechercher_par_critere facture fournisseur: {e}", exc_info=True)
            return []
        finally:
            self.db.close()

    # =========================================================================
    # METHODES STATISTIQUES CARDS
    # =========================================================================

    def nombre_factures_aujourd_hui(self, code_session: str) -> int:
        """Card Factures du Jour : COUNT factures créées aujourd'hui."""
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM facture_fournisseur
                WHERE code_session = %s
                  AND DATE(date_facture_four) = CURDATE()
            """, (code_session,))
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            self.logger.error(f"Erreur nombre_factures_aujourd_hui: {e}", exc_info=True)
            return 0
        finally:
            self.db.close()

    def nombre_total_par_session(self, code_session: str) -> int:
        """Card Total Factures : COUNT toutes les factures de la session."""
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM facture_fournisseur
                WHERE code_session = %s
            """, (code_session,))
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            self.logger.error(f"Erreur nombre_total_par_session: {e}", exc_info=True)
            return 0
        finally:
            self.db.close()

    def montant_total_par_session(self, code_session: str) -> float:
        """Card Dépenses Totales : SUM des montants de toutes les factures."""
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(Montant_total), 0) AS total
                FROM facture_fournisseur
                WHERE code_session = %s
            """, (code_session,))
            result = cursor.fetchone()
            return float(result['total']) if result else 0.0
        except Exception as e:
            self.logger.error(f"Erreur montant_total_par_session: {e}", exc_info=True)
            return 0.0
        finally:
            self.db.close()

    def montant_total_aujourd_hui(self, code_session: str) -> float:
        """Card Dépenses du Jour : SUM des montants des factures créées aujourd'hui."""
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(Montant_total), 0) AS total
                FROM facture_fournisseur
                WHERE code_session = %s
                  AND DATE(date_facture_four) = CURDATE()
            """, (code_session,))
            result = cursor.fetchone()
            return float(result['total']) if result else 0.0
        except Exception as e:
            self.logger.error(f"Erreur montant_total_aujourd_hui: {e}", exc_info=True)
            return 0.0
        finally:
            self.db.close()

    def nombre_par_mois(self, code_session: str) -> Dict[str, int]:
        """Nombre de factures fournisseurs par mois pour la session."""
        stats = {
            'Jan': 0, 'Fev': 0, 'Mar': 0, 'Avr': 0, 'Mai': 0, 'Juin': 0,
            'Juil': 0, 'Aout': 0, 'Sep': 0, 'Oct': 0, 'Nov': 0, 'Dec': 0
        }
        mois_mapping = {
            1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Avr', 5: 'Mai', 6: 'Juin',
            7: 'Juil', 8: 'Aout', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }
        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MONTH(date_facture_four) AS num_mois, COUNT(*) AS total
                FROM facture_fournisseur
                WHERE code_session = %s
                GROUP BY MONTH(date_facture_four)
            """, (code_session,))
            for row in cursor.fetchall():
                m = row['num_mois']
                if m in mois_mapping:
                    stats[mois_mapping[m]] = row['total']
            return stats
        except Exception as e:
            self.logger.error(f"Erreur nombre_par_mois: {e}", exc_info=True)
            return stats
        finally:
            self.db.close()

    # =========================================================================
    # METHODES PRIVEES
    # =========================================================================

    def _generer_code(self, cursor) -> str:
        """Génère un code unique pour facture_fournisseur (ex: FCF001)."""
        try:
            cursor.execute(
                "SELECT code_facture_four FROM facture_fournisseur ORDER BY code_facture_four DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                last_code = row['code_facture_four'] if isinstance(row, dict) else row[0]
                last_num  = int(last_code[3:])
                return f"FCF{last_num + 1:03d}"
            return "FCF001"
        except Exception as e:
            self.logger.error(f"Erreur génération code facture fournisseur: {e}", exc_info=True)
            return "FCF" + datetime.now().strftime("%H%M%S")

    
    def lister_dernieres_factures(self, code_session: str, limite: int = 10) -> List[Dict]:
        """
        Retourne les N dernières factures d'une session avec infos fournisseur.
        Utilisée pour l'onglet Historique du panneau factures.

        Args:
            code_session: Code de la session en cours
            limite: Nombre maximum de factures à retourner (défaut: 10)

        Returns:
            Liste de dictionnaires prêts à l'affichage
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ff.code_facture_four,
                    ff.Montant_total,
                    ff.mode_payement,
                    ff.telephone,
                    ff.date_facture_four,
                    ff.code_fournisseur,
                    ff.code_session,
                    f.nom_entreprise AS fournisseur_nom,
                    f.telephone      AS fournisseur_telephone,
                    f.adresse        AS fournisseur_adresse
                FROM facture_fournisseur ff
                LEFT JOIN fournisseurs f ON ff.code_fournisseur = f.email_fournisseur
                WHERE ff.code_session = %s
                ORDER BY ff.date_facture_four DESC
                LIMIT %s
            """, (code_session, limite))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Erreur lister_dernieres_factures: {e}", exc_info=True)
            return []
        finally:
            self.db.close()
    
    def _row_to_object(self, row) -> FactureFournisseur:
        """Convertit une ligne de BDD en objet FactureFournisseur."""
        obj = FactureFournisseur(
            code_facture_four = row['code_facture_four'],
            montant_total     = row['Montant_total'],
            mode_payement     = row['mode_payement'],
            telephone         = row['telephone'],
            date_facture_four = row['date_facture_four'],
            code_fournisseur  = row['code_fournisseur'],
            code_session      = row['code_session']
        )
        # Infos fournisseur ajoutées dynamiquement si présentes (JOIN)
        obj.fournisseur_nom = row.get('fournisseur_nom', '')
        return obj