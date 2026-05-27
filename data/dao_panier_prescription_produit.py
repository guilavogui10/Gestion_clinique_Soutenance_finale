"""
prescription_dao.py
--------------------
DAO pour la table prescription_produit.

Rôle : lignes de prescription liées à une consultation (pattern panier).
       Chaque ajout DÉCRÉMENTE le stock via la logique FEFO —
       date_expiration est remplie AUTOMATIQUEMENT, jamais saisie manuellement.
       designation et prix_applique sont aussi auto-complétés depuis produits.

Colonnes table prescription_produit :
    code_prescription   PK  VARCHAR   généré PRS001+
    designation         VARCHAR       auto-complété depuis produits.libelle
    code_produit        FK  → produits
    quantite_prescript  INT
    prix_applique       DECIMAL       auto-complété depuis produits.prix_vente_unitaire
    code_visite         FK  → visite
    code_consultation   FK  → consultation
    code_session        FK  → session
    date_expiration     DATE          rempli auto par FEFO

Note : statut_facture retiré — le paiement est atomique sur la facture patient,
       pas ligne par ligne. Le statut appartient à facture_patient.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
import logging
from typing import Optional
from datetime import datetime
from core.connexion_db import DBConnection
from models.modele_panier_prescription_produit import PanierPrescriptionProduit

DictCursor = pymysql.cursors.DictCursor


class PrescriptionProduitDAO:
    """
    DAO pour la gestion des prescriptions produits (service pharmacie).
    Architecture MVC : accès aux données uniquement.
    """

    def __init__(self):
        self.db = DBConnection()
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # CRUD
    # =========================================================================

    def ajouter(self, prescription: PanierPrescriptionProduit) -> bool:
        """
        Ajoute une ligne de prescription.

        Étapes internes automatiques :
          1. Auto-compléter designation + prix_applique depuis produits
          2. Récupérer la date_expiration du lot FEFO
          3. Générer le code PRS
          4. Insérer la ligne
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor(DictCursor)

            # 1. Auto-compléter designation et prix si absents
            self._completer_infos_produit(cursor, prescription)

            # 2. FEFO — allocation sur un ou plusieurs lots
            if prescription.date_expiration:
                allocations = [{
                    'date_expiration': prescription.date_expiration,
                    'quantite': int(prescription.quantite_prescript)
                }]
            else:
                allocations = self._calculer_allocations_fefo(
                    cursor,
                    prescription.code_produit,
                    prescription.code_session,
                    int(prescription.quantite_prescript)
                )
                if not allocations:
                    raise ValueError(
                        "Aucun lot FEFO disponible ou stock insuffisant pour ce produit."
                    )

            # 3. Insérer une ligne par lot alloué
            allocations_out = []
            quantite_initiale = int(prescription.quantite_prescript)
            for alloc in allocations:
                prescription.code_prescription = self._generer_code(cursor)
                prescription.quantite_prescript = int(alloc['quantite'])
                prescription.date_expiration = alloc['date_expiration']

                cursor.execute("""
                    INSERT INTO prescription_produit (
                        code_prescription, designation, code_produit,
                        quantite_prescript, prix_applique,
                        code_session, date_expiration, code_acte
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    prescription.code_prescription,
                    prescription.designation,
                    prescription.code_produit,
                    prescription.quantite_prescript,
                    prescription.prix_applique,
                    prescription.code_session,
                    prescription.date_expiration,
                    prescription.code_acte
                ))

                allocations_out.append({
                    'code_prescription': prescription.code_prescription,
                    'date_expiration': prescription.date_expiration,
                    'quantite': prescription.quantite_prescript
                })

            # Restaurer quantite d'origine pour la suite
            prescription.quantite_prescript = quantite_initiale
            if allocations_out:
                prescription.code_prescription = allocations_out[0]['code_prescription']
                prescription.date_expiration = allocations_out[0]['date_expiration']
                # Attacher les allocations pour la couche UI
                prescription.allocations = allocations_out

            conn.commit()
            return True

        except ValueError as ve:
            self.logger.warning(f"[PrescriptionProduitDAO] Erreur FEFO: {ve}")
            conn.rollback()
            raise ve
        except Exception as e:
            self.logger.error(f"[PrescriptionProduitDAO] Erreur ajouter: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            self.db.close()

    def modifier(self, prescription: PanierPrescriptionProduit) -> bool:
        """
        Modifie une ligne de prescription existante.
        Recalcule le FEFO si date_expiration absente.
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor(DictCursor)

            self._completer_infos_produit(cursor, prescription)

            if not prescription.date_expiration:
                # Reutiliser la meme connexion/cursor (evite fermeture involontaire)
                prescription.date_expiration = self.get_date_expiration_fefo(
                    prescription.code_produit,
                    prescription.code_session,
                    prescription.quantite_prescript,
                    cursor=cursor
                )
                if not prescription.date_expiration:
                    raise ValueError("Aucun lot FEFO disponible pour ce produit.")

            cursor.execute("""
                UPDATE prescription_produit SET
                    designation        = %s,
                    code_produit       = %s,
                    quantite_prescript = %s,
                    prix_applique      = %s,
                    code_session       = %s,
                    date_expiration    = %s,
                    code_acte          = %s
                WHERE code_prescription = %s
            """, (
                prescription.designation,
                prescription.code_produit,
                prescription.quantite_prescript,
                prescription.prix_applique,
                prescription.code_session,
                prescription.date_expiration,
                prescription.code_acte,
                prescription.code_prescription
            ))
            conn.commit()
            return True

        except ValueError as ve:
            self.logger.warning(f"[PanierPrescriptionProduitDAO] Erreur FEFO (modifier): {ve}")
            conn.rollback()
            raise ve
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur modifier: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    def supprimer(self, code_prescription: str) -> bool:
        """Supprime une ligne de prescription."""
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute(
                "DELETE FROM prescription_produit WHERE code_prescription = %s",
                (code_prescription,)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur supprimer: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    def valider_prescription_visite(self, code_acte: str) -> bool:
        """
        Valide la prescription d'un acte médical.
        Récupère code_visite via acte_medical → consultation.
        Met à jour statut_patient vers 'Attente payement'.
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor(DictCursor)

            # Récupérer code_visite + code_consultation via acte_medical
            cursor.execute("""
                SELECT c.code AS code_consultation, c.code_visite
                FROM acte_medical am
                INNER JOIN consultation c ON am.code_consultation = c.code
                WHERE am.code_acte = %s
            """, (code_acte,))
            row = cursor.fetchone()
            if not row:
                return False
            code_consultation = row['code_consultation']
            code_visite = row['code_visite']

            # Éviter double décrément si déjà validé
            cursor.execute(
                "SELECT statut_patient FROM visite WHERE code_visite = %s",
                (code_visite,)
            )
            row_statut = cursor.fetchone()
            if row_statut and str(row_statut.get('statut_patient', '')).strip() == "Attente payement":
                return True

            # Décrémenter le stock global pour chaque produit de l'acte
            cursor.execute("""
                SELECT code_produit, code_session, SUM(quantite_prescript) AS total_qte
                FROM prescription_produit
                WHERE code_acte = %s
                GROUP BY code_produit, code_session
            """, (code_acte,))
            for row in cursor.fetchall():
                code_produit = row.get('code_produit')
                code_session = row.get('code_session')
                total_qte = int(row.get('total_qte') or 0)
                if code_produit and code_session and total_qte > 0:
                    self._decrementer_stock(cursor, code_produit, total_qte, code_session)

            nouveau_statut = self._determiner_prochain_statut_apres_prescription(
                cursor, code_acte
            )
            cursor.execute(
                "UPDATE visite SET statut_patient = %s WHERE code_visite = %s",
                (nouveau_statut, code_visite)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur valider_prescription_visite: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    # =========================================================================
    # RÉCUPÉRATION
    # =========================================================================

    def obtenir_par_code(self, code_prescription: str):
        """Retourne un objet PanierPrescriptionProduit enrichi (JOIN patient)."""
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT pp.*,
                       p.nom    AS patient_nom,
                       p.prenom AS patient_prenom
                FROM prescription_produit pp
                LEFT JOIN acte_medical am ON pp.code_acte = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite = v.code_visite
                LEFT JOIN patients p      ON v.code_patient = p.code_patient
                WHERE pp.code_prescription = %s
            """, (code_prescription,))
            row = cursor.fetchone()
            return self._row_to_object(row) if row else None
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur obtenir_par_code: {e}")
            return None
        finally:
            self.db.close()

    def obtenir_par_acte(self, code_acte: str) -> list:
        """
        Retourne toutes les lignes de prescription d un acte medical.
        Utilisé pour afficher le panier prescription en cours dans la vue.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT *
                FROM prescription_produit
                WHERE code_acte = %s
                ORDER BY code_prescription ASC
            """, (code_acte,))
            return [self._row_to_object(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur obtenir_par_acte: {e}")
            return []
        finally:
            self.db.close()

    def lister_par_session(self, code_session: str) -> list:
        """Toutes les prescriptions de la session enrichies (JOIN patient)."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT pp.*,
                       p.nom    AS patient_nom,
                       p.prenom AS patient_prenom
                FROM prescription_produit pp
                LEFT JOIN acte_medical am ON pp.code_acte = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite = v.code_visite
                LEFT JOIN patients p      ON v.code_patient = p.code_patient
                WHERE pp.code_session = %s
                ORDER BY pp.code_prescription DESC
            """, (code_session,))
            return [self._row_to_object(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur lister_par_session: {e}")
            return []
        finally:
            self.db.close()

    def lister_groupes_par_acte(self, code_session: str) -> list:
        """
        Regroupe les prescriptions par code_acte (1 ligne par acte medical).
        Retourne : code_acte, code_visite, patient_nom, patient_prenom,
                   date_consultation, nb_produits, total_quantite, total_montant.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT
                    pp.code_acte,
                    v.code_visite,
                    p.nom    AS patient_nom,
                    p.prenom AS patient_prenom,
                    c.date_consultation,
                    COUNT(*) AS nb_produits,
                    SUM(pp.quantite_prescript)                    AS total_quantite,
                    SUM(pp.prix_applique * pp.quantite_prescript) AS total_montant
                FROM prescription_produit pp
                LEFT JOIN acte_medical am ON pp.code_acte       = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite       = v.code_visite
                LEFT JOIN patients p      ON v.code_patient      = p.code_patient
                WHERE pp.code_session = %s
                GROUP BY
                    pp.code_acte, v.code_visite,
                    p.nom, p.prenom, c.date_consultation
                ORDER BY c.date_consultation DESC, pp.code_acte DESC
            """, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur lister_groupes_par_acte: {e}")
            return []
        finally:
            self.db.close()

    def lister_par_visite(self, code_visite: str) -> list:
        """Toutes les prescriptions liées à une visite (via acte_medical → consultation)."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT pp.*
                FROM prescription_produit pp
                INNER JOIN acte_medical am ON pp.code_acte = am.code_acte
                INNER JOIN consultation c  ON am.code_consultation = c.code
                WHERE c.code_visite = %s
                ORDER BY pp.code_prescription ASC
            """, (code_visite,))
            return [self._row_to_object(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur lister_par_visite: {e}")
            return []
        finally:
            self.db.close()

    def rechercher_par_critere(self, critere: str, code_session: str) -> list:
        """Recherche sur code_prescription, designation, nom et prénom patient."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            like = f"%{critere}%"
            cursor.execute("""
                SELECT pp.*,
                       p.nom    AS patient_nom,
                       p.prenom AS patient_prenom
                FROM prescription_produit pp
                LEFT JOIN acte_medical am ON pp.code_acte = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite = v.code_visite
                LEFT JOIN patients p      ON v.code_patient = p.code_patient
                WHERE pp.code_session = %s
                  AND (
                      pp.code_prescription LIKE %s OR
                      pp.designation       LIKE %s OR
                      p.nom                LIKE %s OR
                      p.prenom             LIKE %s
                  )
                ORDER BY pp.code_prescription DESC
            """, (code_session, like, like, like, like))
            return [self._row_to_object(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur rechercher_par_critere: {e}")
            return []
        finally:
            self.db.close()

    def prescription_complete(self, code_prescription: str):
        """
        Retourne une ligne brute (dict) avec toutes les infos JOIN :
        patient, produit, consultation.
        Utilisé pour l impression d ordonnance.
        """
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT
                    pp.*,
                    p.nom                  AS patient_nom,
                    p.prenom               AS patient_prenom,
                    p.telephone            AS patient_telephone,
                    p.adresse              AS patient_adresse,
                    p.naissance            AS patient_date_naissance,
                    pr.libelle             AS produit_libelle,
                    pr.type                AS produit_type,
                    pr.prix_vente_unitaire AS produit_prix_vente_unitaire
                FROM prescription_produit pp
                LEFT JOIN acte_medical am ON pp.code_acte = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite = v.code_visite
                LEFT JOIN patients  p     ON v.code_patient  = p.code_patient
                LEFT JOIN produits  pr    ON pp.code_produit = pr.code_produit
                WHERE pp.code_prescription = %s
            """, (code_prescription,))
            return cursor.fetchone()
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur prescription_complete: {e}")
            return None
        finally:
            self.db.close()

    # =========================================================================
    # PATIENTS
    # =========================================================================

    def patients_en_attente_prescription(self, code_session: str) -> list:
        """
        Liste les patients avec statut_patient = 'Attente pharmacie'
        sans encore de prescription. Triés urgence → heure.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT DISTINCT
                    v.code_visite,
                    v.date_visite,
                    v.statut_patient,
                    am.code_acte        AS code_acte,
                    c.code              AS code_consultation,
                    c.date_consultation,
                    p.code_patient,
                    p.nom,
                    p.prenom,
                    p.telephone
                FROM visite v
                INNER JOIN patients     p   ON v.code_patient  = p.code_patient
                INNER JOIN acte_visite  av  ON av.code_visite  = v.code_visite
                INNER JOIN acte_medical am  ON am.code_acte    = av.code_acte
                                           AND am.type_acte    = 'prescription'
                LEFT  JOIN consultation c   ON c.code          = am.code_consultation
                WHERE v.code_session   = %s
                  AND v.statut_patient IN ('Attente pharmacie', 'En pharmacie')
                ORDER BY v.urgent DESC, v.date_visite ASC
            """, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur patients_en_attente_prescription: {e}")
            return []
        finally:
            self.db.close()

    def historique_patient(self, code_patient: str) -> list:
        """Historique complet des prescriptions d un patient."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT pp.*,
                       pr.libelle AS produit_libelle,
                       pr.type    AS produit_type
                FROM prescription_produit pp
                INNER JOIN acte_medical am ON pp.code_acte = am.code_acte
                INNER JOIN consultation c  ON am.code_consultation = c.code
                INNER JOIN visite v        ON c.code_visite = v.code_visite
                LEFT  JOIN produits pr     ON pp.code_produit = pr.code_produit
                WHERE v.code_patient = %s
                ORDER BY pp.code_prescription DESC
            """, (code_patient,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur historique_patient: {e}")
            return []
        finally:
            self.db.close()

    def lister_produits(self) -> list:
        """
        Retourne tous les produits actifs.
        Utilisé pour peupler le combo_produit dans la vue prescription.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT code_produit, libelle, type, prix_vente_unitaire
                FROM produits
                ORDER BY libelle ASC
            """)
            return cursor.fetchall()
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur lister_produits: {e}")
            return []
        finally:
            self.db.close()

    # =========================================================================
    # CALCULS PAR CONSULTATION (panier en cours)
    # =========================================================================

    def montant_total_acte(self, code_acte: str) -> float:
        """
        Total du panier prescription en cours pour un acte médical.
        Affiché en temps réel dans le footer de la vue (lbl_total).
        """
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT COALESCE(SUM(prix_applique * quantite_prescript), 0) AS total
                FROM prescription_produit
                WHERE code_acte = %s
            """, (code_acte,))
            row = cursor.fetchone()
            return float(row['total']) if row else 0.0
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur montant_total_acte: {e}")
            return 0.0
        finally:
            self.db.close()

    def nombre_lignes_acte(self, code_acte: str) -> int:
        """Nombre de lignes dans le panier en cours (badge_panier)."""
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM prescription_produit
                WHERE code_acte = %s
            """, (code_acte,))
            row = cursor.fetchone()
            return int(row['total']) if row else 0
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur nombre_lignes_acte: {e}")
            return 0
        finally:
            self.db.close()

    # =========================================================================
    # PONT VERS FACTURE PATIENT (agrégation par visite)
    # =========================================================================

    def get_montant_pharmacie_par_visite(self, code_visite: str) -> float:
        """
        Agrège TOUTES les lignes d une visite en UN seul montant pharmacie.
        C est ce montant qui est injecté comme ligne 'Pharmacie'
        dans facture_patient.

        Calcul : SUM(prix_applique * quantite_prescript)
                 pour toutes les lignes WHERE code_visite = %s
        """
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT COALESCE(
                    SUM(pp.prix_applique * pp.quantite_prescript), 0
                ) AS montant_pharmacie
                FROM prescription_produit pp
                INNER JOIN acte_medical am ON pp.code_acte = am.code_acte
                INNER JOIN consultation c  ON am.code_consultation = c.code
                WHERE c.code_visite = %s
            """, (code_visite,))
            row = cursor.fetchone()
            return float(row['montant_pharmacie']) if row else 0.0
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur get_montant_pharmacie_par_visite: {e}")
            return 0.0
        finally:
            self.db.close()

    def get_detail_lignes_par_visite(self, code_visite: str) -> list:
        """
        Retourne le détail de toutes les lignes d une visite.
        Utilisé pour le sous-détail pharmacie dans la facture patient
        (section dépliable 'Voir les produits prescrits').

        Retourne : [{'code_prescription', 'designation',
                     'quantite_prescript', 'prix_applique',
                     'sous_total', 'type_produit'}, ...]
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT
                    pp.code_prescription,
                    pp.designation,
                    pp.quantite_prescript,
                    pp.prix_applique,
                    (pp.quantite_prescript * pp.prix_applique) AS sous_total,
                    p.type AS type_produit
                FROM prescription_produit pp
                INNER JOIN acte_medical am ON pp.code_acte = am.code_acte
                INNER JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN produits p       ON pp.code_produit = p.code_produit
                WHERE c.code_visite = %s
                ORDER BY pp.code_prescription ASC
            """, (code_visite,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur get_detail_lignes_par_visite: {e}")
            return []
        finally:
            self.db.close()

    # =========================================================================
    # CARDS STATISTIQUES
    # =========================================================================

    def nombre_prescriptions_aujourd_hui(self, code_session: str) -> int:
        """
        Card 'Prescriptions du Jour'.
        Compte le nombre de VISITES distinctes servies aujourd hui,
        pas le nombre de lignes produits.
        """
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT COUNT(DISTINCT pp.code_acte) AS total
                FROM prescription_produit pp
                LEFT JOIN acte_medical am ON pp.code_acte = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                WHERE pp.code_session = %s
                  AND DATE(c.date_consultation) = CURDATE()
            """, (code_session,))
            row = cursor.fetchone()
            return int(row['total']) if row else 0
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur nombre_prescriptions_aujourd_hui: {e}")
            return 0
        finally:
            self.db.close()

    def nombre_total_par_session(self, code_session: str) -> int:
        """
        Card 'Total Session'.
        Compte le nombre de VISITES distinctes servies dans la session,
        pas le nombre de lignes produits.
        """
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT COUNT(DISTINCT code_acte) AS total
                FROM prescription_produit
                WHERE code_session = %s
            """, (code_session,))
            row = cursor.fetchone()
            return int(row['total']) if row else 0
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur nombre_total_par_session: {e}")
            return 0
        finally:
            self.db.close()

    def nombre_prescriptions_en_attente(self, code_session: str) -> int:
        """
        Card 'En Attente' : patients avec 'Attente pharmacie'
        sans encore de prescription enregistrée.
        """
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT COUNT(DISTINCT v.code_visite) AS total
                FROM visite v
                INNER JOIN acte_visite  av  ON av.code_visite = v.code_visite
                INNER JOIN acte_medical am  ON am.code_acte   = av.code_acte
                                           AND am.type_acte   = 'prescription'
                WHERE v.code_session   = %s
                  AND v.statut_patient IN ('Attente pharmacie', 'En pharmacie')
            """, (code_session,))
            row = cursor.fetchone()
            return int(row['total']) if row else 0
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur nombre_prescriptions_en_attente: {e}")
            return 0
        finally:
            self.db.close()

    def montant_total_session(self, code_session: str) -> float:
        """Chiffre d affaire pharmacie sur la session."""
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT COALESCE(SUM(prix_applique * quantite_prescript), 0) AS total
                FROM prescription_produit
                WHERE code_session = %s
            """, (code_session,))
            row = cursor.fetchone()
            return float(row['total']) if row else 0.0
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur montant_total_session: {e}")
            return 0.0
        finally:
            self.db.close()

    # =========================================================================
    # STATISTIQUES & GRAPHES
    # =========================================================================

    def revenu_total(self, code_session: str,
                     date_debut=None, date_fin=None) -> float:
        """
        Total des prix appliqués pour une session.
        Filtre date optionnel (format 'YYYY-MM-DD').
        """
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor(DictCursor)
            if date_debut and date_fin:
                cursor.execute("""
                    SELECT COALESCE(SUM(pp.prix_applique * pp.quantite_prescript), 0) AS total
                    FROM prescription_produit pp
                    LEFT JOIN acte_medical am ON pp.code_acte = am.code_acte
                    LEFT JOIN consultation c  ON am.code_consultation = c.code
                    WHERE pp.code_session = %s
                      AND DATE(c.date_consultation) BETWEEN %s AND %s
                """, (code_session, date_debut, date_fin))
            else:
                cursor.execute("""
                    SELECT COALESCE(SUM(prix_applique * quantite_prescript), 0) AS total
                    FROM prescription_produit
                    WHERE code_session = %s
                """, (code_session,))
            row = cursor.fetchone()
            return float(row['total']) if row else 0.0
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur revenu_total: {e}")
            return 0.0
        finally:
            self.db.close()

    def nombre_par_mois(self, code_session: str) -> dict:
        """
        Agrégation par mois pour graphique en barres.
        Retourne : {'Jan': N, 'Fev': N, ..., 'Dec': N}
        """
        stats = {
            'Jan': 0, 'Fev': 0, 'Mar': 0, 'Avr': 0, 'Mai': 0, 'Juin': 0,
            'Juil': 0, 'Aout': 0, 'Sep': 0, 'Oct': 0, 'Nov': 0, 'Dec': 0
        }
        mois_mapping = {
            1: 'Jan',  2: 'Fev',  3: 'Mar',  4: 'Avr',
            5: 'Mai',  6: 'Juin', 7: 'Juil', 8: 'Aout',
            9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }
        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT MONTH(c.date_consultation) AS num_mois, COUNT(*) AS total
                FROM prescription_produit pp
                LEFT JOIN acte_medical am ON pp.code_acte = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                WHERE pp.code_session = %s
                  AND c.date_consultation IS NOT NULL
                GROUP BY MONTH(c.date_consultation)
            """, (code_session,))
            for row in cursor.fetchall():
                m = row['num_mois']
                if m in mois_mapping:
                    stats[mois_mapping[m]] = row['total']
            return stats
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur nombre_par_mois: {e}")
            return stats
        finally:
            self.db.close()

    def top_designations(self, code_session: str, limite: int = 10) -> list:
        """Top N désignations les plus fréquentes dans la session."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT designation, COUNT(*) AS nombre
                FROM prescription_produit
                WHERE code_session = %s
                  AND designation IS NOT NULL
                GROUP BY designation
                ORDER BY nombre DESC
                LIMIT %s
            """, (code_session, limite))
            return cursor.fetchall()
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur top_designations: {e}")
            return []
        finally:
            self.db.close()

    def prescriptions_par_produit(self, code_session: str) -> list:
        """Nombre de prescriptions groupées par produit avec montants."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT
                    code_produit,
                    designation,
                    COUNT(*)                                AS nombre,
                    SUM(quantite_prescript)                 AS total_quantite,
                    SUM(prix_applique * quantite_prescript) AS total_prix
                FROM prescription_produit
                WHERE code_session = %s
                GROUP BY code_produit, designation
                ORDER BY nombre DESC
            """, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur prescriptions_par_produit: {e}")
            return []
        finally:
            self.db.close()

    def top_produits_prescrits(self, code_session: str, limite: int = 5) -> list:
        """Top N produits par quantité prescrite."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT
                    code_produit,
                    designation,
                    SUM(quantite_prescript)                 AS total_quantite,
                    SUM(prix_applique * quantite_prescript) AS total_montant
                FROM prescription_produit
                WHERE code_session = %s
                GROUP BY code_produit, designation
                ORDER BY total_quantite DESC
                LIMIT %s
            """, (code_session, limite))
            return cursor.fetchall()
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur top_produits_prescrits: {e}")
            return []
        finally:
            self.db.close()

    # =========================================================================
    # FEFO
    # =========================================================================

    def _calculer_allocations_fefo(self, cursor,
                                   code_produit: str,
                                   code_session: str,
                                   quantite: int) -> list:
        """
        Calcule la rÃ©partition FEFO sur plusieurs lots si nÃ©cessaire.
        Retourne une liste [{'date_expiration': date, 'quantite': qte}, ...]
        """
        if not code_produit or not code_session or quantite <= 0:
            return []
        try:
            cursor.execute("""
                SELECT
                    pf.date_expiration,
                    SUM(pf.quantite_four) -
                        COALESCE((
                            {sorties_validees}
                        ), 0) AS stock_lot
                FROM panier_facture_four pf
                WHERE pf.code_produit = %s
                  AND pf.code_session = %s
                GROUP BY pf.date_expiration
                HAVING stock_lot > 0
                ORDER BY pf.date_expiration ASC
            """.format(
                sorties_validees=self._sous_requete_sorties_lot_validees()
            ), (code_session, code_produit, code_session))
            lots = cursor.fetchall()
            if not lots:
                return []

            allocations = []
            restant = int(quantite)
            for lot in lots:
                stock_lot = (
                    lot.get('stock_lot', 0) if isinstance(lot, dict) else lot[1]
                )
                date_exp = (
                    lot.get('date_expiration') if isinstance(lot, dict) else lot[0]
                )
                if not stock_lot or stock_lot <= 0:
                    continue
                prendre = stock_lot if stock_lot <= restant else restant
                allocations.append({
                    'date_expiration': date_exp,
                    'quantite': int(prendre)
                })
                restant -= int(prendre)
                if restant <= 0:
                    break

            if restant > 0:
                return []
            return allocations
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur _calculer_allocations_fefo: {e}")
            return []

    def get_date_expiration_fefo(self, code_produit: str,
                                  code_session: str,
                                  quantite: int,
                                  cursor=None) -> Optional[datetime]:
        """
        Retourne la date_expiration du lot prioritaire selon FEFO.
        stock_lot = SUM(entrées) - SUM(prescriptions sorties)
        Sélectionne le lot qui expire le plus tôt avec stock suffisant.
        """
        owns_connection = False
        if cursor is None:
            conn = self.db.connect()
            if not conn:
                return None
            cursor = conn.cursor(DictCursor)
            owns_connection = True
        try:
            cursor.execute("""
                SELECT
                    pf.date_expiration,
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
            ), (code_session, code_produit, code_session, quantite))
            row = cursor.fetchone()
            if not row:
                return None
            return row['date_expiration'] if isinstance(row, dict) else row[0]
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur get_date_expiration_fefo: {e}")
            return None
        finally:
            if owns_connection:
                self.db.close()

    # =========================================================================
    # MÉTHODES PRIVÉES
    # =========================================================================

    def _sous_requete_sorties_lot_validees(self) -> str:
        """
        Ne compte que les prescriptions dont le stock global a deja ete decremente.
        """
        return """
            SELECT SUM(pp.quantite_prescript)
            FROM prescription_produit pp
            INNER JOIN acte_medical am ON pp.code_acte = am.code_acte
            INNER JOIN consultation c  ON am.code_consultation = c.code
            INNER JOIN visite v        ON c.code_visite = v.code_visite
            WHERE pp.code_produit    = pf.code_produit
              AND pp.date_expiration = pf.date_expiration
              AND pp.code_session    = %s
              AND v.statut_patient IN ('Attente payement', 'Libéré')
        """

    def _decrementer_stock(self, cursor,
                           code_produit: str,
                           quantite: int,
                           code_session: str) -> None:
        """Décrémente la quantité en stock global lors de la validation."""
        if not code_produit or not code_session or not quantite:
            return
        # Vérifier si une ligne stock existe
        cursor.execute("""
            SELECT code_stock
            FROM stocks
            WHERE code_produit = %s AND code_session = %s
        """, (code_produit, code_session))
        row = cursor.fetchone()
        if row:
            code_stock = row['code_stock'] if isinstance(row, dict) else row[0]
            cursor.execute("""
                UPDATE stocks
                SET quantite_actuelle = quantite_actuelle - %s,
                    date_derniere_maj = NOW()
                WHERE code_stock = %s
            """, (quantite, code_stock))
            return

        # Si stock absent, créer une ligne (quantité négative)
        code_stock = self._generer_code_stock(cursor)
        cursor.execute("""
            INSERT INTO stocks (code_stock, code_produit, quantite_actuelle, date_derniere_maj, code_session)
            VALUES (%s, %s, %s, %s, %s)
        """, (code_stock, code_produit, -int(quantite), datetime.now(), code_session))

    def _generer_code_stock(self, cursor) -> str:
        """Génère un code unique pour la table stocks (ex: STK001)."""
        try:
            cursor.execute(
                "SELECT code_stock FROM stocks ORDER BY code_stock DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                last_code = row['code_stock'] if isinstance(row, dict) else row[0]
                last_num = int(last_code[3:])
                return f"STK{last_num + 1:03d}"
            return "STK001"
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur _generer_code_stock: {e}")
            return "STK" + datetime.now().strftime("%H%M%S")

    def _generer_code(self, cursor) -> str:
        """Génère le prochain code PRS : PRS001, PRS002, ..."""
        try:
            cursor.execute("""
                SELECT code_prescription
                FROM prescription_produit
                ORDER BY code_prescription DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                last_code = row['code_prescription'] if isinstance(row, dict) else row[0]
                return f"PRS{int(last_code[3:]) + 1:03d}"
            return "PRS001"
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur _generer_code: {e}")
            return "PRS" + datetime.now().strftime("%H%M%S")

    def _completer_infos_produit(self, cursor,
                                  prescription: PanierPrescriptionProduit) -> None:
        """
        Auto-complète designation et prix_applique depuis produits
        si ces champs sont absents ou à 0.
        """
        if not prescription or not prescription.code_produit:
            return

        designation_manquante = (
            not prescription.designation or
            str(prescription.designation).strip() == ""
        )
        prix_manquant = (
            prescription.prix_applique is None or
            prescription.prix_applique == 0
        )

        if not designation_manquante and not prix_manquant:
            return

        try:
            cursor.execute("""
                SELECT libelle, prix_vente_unitaire
                FROM produits
                WHERE code_produit = %s
            """, (prescription.code_produit,))
            row = cursor.fetchone()
            if not row:
                return
            if designation_manquante:
                prescription.designation = (
                    row['libelle'] if isinstance(row, dict) else row[0]
                )
            if prix_manquant:
                prix = (
                    row['prix_vente_unitaire'] if isinstance(row, dict) else row[1]
                )
                prescription.prix_applique = float(prix) if prix is not None else 0.0
        except Exception as e:
            print(f"[PanierPrescriptionProduitDAO] Erreur _completer_infos_produit: {e}")

    def _determiner_prochain_statut_apres_prescription(
            self, cursor, code_acte: str) -> str:
        """
        Détermine le prochain statut_patient après validation de prescription.
        Règle métier : → 'Attente payement'
        """
        return "Attente payement"

    def _row_to_object(self, row) -> PanierPrescriptionProduit:
        """
        Convertit une ligne DictCursor en objet PanierPrescriptionProduit.
        Ajoute patient_nom et patient_prenom si présents dans le JOIN.
        """
        obj = PanierPrescriptionProduit(
            code_prescription  = row['code_prescription'],
            designation        = row['designation'],
            code_produit       = row['code_produit'],
            quantite_prescript = row['quantite_prescript'],
            prix_applique      = float(row['prix_applique']) if row['prix_applique'] else 0.0,
            code_session       = row['code_session'],
            date_expiration    = row['date_expiration'],
            code_acte          = row.get('code_acte')
        )
        obj.patient_nom    = row.get('patient_nom',    "") if isinstance(row, dict) else ""
        obj.patient_prenom = row.get('patient_prenom', "") if isinstance(row, dict) else ""
        return obj

