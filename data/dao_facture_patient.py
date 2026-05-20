"""
facture_patient_dao.py
----------------------
DAO pour la gestion de la table facture_patient.
Architecture MVC : accès aux données uniquement.

Rôle : en-tête de la facture patient.
       Gère la génération automatique de la facture + panier,
       l'enregistrement du paiement et les statistiques financières.

Colonnes table facture_patient :
    code_facture   PK  VARCHAR    généré FCT001+
    code_visite    FK  → visite
    Montant_total  DECIMAL
    Mode_payement  VARCHAR
    telephone      VARCHAR
    statut_facture VARCHAR        'Attente payement' | 'Payé' | 'Annulé'
    date_facture   DATETIME
    code_session   FK  → annee

Flux métier :
    Visite → ... → statut_patient = 'Attente payement'
    → generer_facture()       crée FCT + lignes PAN atomiquement
    → enregistrer_paiement()  solde la facture et libère le patient
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
from datetime import datetime
from core.connexion_db import DBConnection
from models.modele_facture_patient import FacturePatient
from models.modele_panier_facture import PanierFacture
from data.dao_panier_facture_patient import PanierFactureDAO

DictCursor = pymysql.cursors.DictCursor


class FacturePatientDAO:
    """
    Classe DAO pour la gestion de la table facture_patient.
    Architecture MVC : accès aux données uniquement.
    """

    def __init__(self):
        self.db              = DBConnection()
        self.panier_dao      = PanierFactureDAO()

    # =========================================================================
    # GÉNÉRATION AUTOMATIQUE DE FACTURE
    # =========================================================================

    def generer_facture(self, code_visite: str,
                        telephone: str = "",
                        creer_panier: bool = True) -> tuple:
        """
        Crée automatiquement la facture_patient et, si demandé,
        toutes les lignes panier_facture en agrégeant les frais de chaque service rendu.

        Toute l'opération est atomique (une seule transaction SQL).

        Règles métier :
          - Une visite ne peut avoir qu'UNE seule facture active.
          - Si la facture existe déjà, retourne son code sans erreur.
          - Seuls les services avec montant > 0 génèrent une ligne panier.
          - La pharmacie est agrégée en UNE seule ligne (SUM).
          - Si creer_panier=False : seules l'entête est créée (montant_total=0).

        Args:
            code_visite (str): Code de la visite à facturer.
            telephone   (str): Contact optionnel (Mobile Money).
            creer_panier (bool): Si True, crée les lignes panier automatiquement.

        Returns:
            tuple(bool, str, str|None): (succès, message, code_facture)
        """
        conn = self.db.connect()
        if not conn:
            return False, "Erreur de connexion à la base de données.", None

        try:
            with conn.cursor(DictCursor) as cursor:

                # 0. Vérifier doublon ─────────────────────────────────────────
                cursor.execute(
                    "SELECT code_facture FROM facture_patient WHERE code_visite = %s LIMIT 1",
                    (code_visite,)
                )
                existante = cursor.fetchone()
                if existante:
                    return True, "Facture déjà existante.", existante["code_facture"]

                # 1. Récupérer session + téléphone patient ─────────────────────
                cursor.execute("""
                    SELECT v.code_session, p.telephone
                    FROM visite v
                    LEFT JOIN patients p ON v.code_patient = p.code_patient
                    WHERE v.code_visite = %s
                """, (code_visite,))
                row_visite = cursor.fetchone()
                if not row_visite:
                    return False, f"Visite '{code_visite}' introuvable.", None

                code_session = row_visite["code_session"]
                tel          = telephone or row_visite.get("telephone") or ""

                # 2. Collecter les lignes de chaque service ────────────────────
                lignes_data = self._collecter_lignes_panier(cursor, code_visite)
                if not lignes_data:
                    return False, "Aucun service facturable trouvé pour cette visite.", None

                # 3. Calculer le montant total (si panier auto) ───────────────
                montant_total = 0.0
                if creer_panier:
                    montant_total = round(
                        sum(l["prix_applique"] * l["quantite_facture"] for l in lignes_data), 2
                    )

                # 4. Insérer l'en-tête facture_patient ────────────────────────
                code_facture = self._generer_code(cursor)
                cursor.execute("""
                    INSERT INTO facture_patient (
                        code_facture, code_visite, Montant_total,
                        Mode_payement, telephone, statut_facture,
                        date_facture, code_session
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    code_facture,
                    code_visite,
                    montant_total,
                    "",
                    tel,
                    "Attente payement",
                    datetime.now(),
                    code_session,
                ))

                # 5. Insérer les lignes panier_facture ─────────────────────────
                if creer_panier:
                    lignes_obj = [
                        PanierFacture(
                            code_paniere      = "",          # généré dans ajouter_plusieurs
                            designation       = data["designation"],
                            numero_reference  = data["numero_reference"],
                            quantite_facture  = data["quantite_facture"],
                            prix_applique     = data["prix_applique"],
                            code_facture      = code_facture,
                        )
                        for data in lignes_data
                    ]
                    self.panier_dao.ajouter_plusieurs(lignes_obj, conn=conn)

                conn.commit()
                return True, "Facture générée avec succès.", code_facture

        except pymysql.MySQLError as e:
            conn.rollback()
            return False, f"Erreur SQL lors de la génération : {e}", None
        except Exception as e:
            conn.rollback()
            return False, f"Erreur inattendue : {e}", None
        finally:
            conn.close()

    # =========================================================================
    # ENREGISTREMENT DU PAIEMENT
    # =========================================================================

    def enregistrer_paiement(self, code_facture: str,
                              mode_payement: str,
                              telephone: str = "") -> tuple:
        """
        Enregistre le règlement d'une facture et synchronise tout le dossier.

        Actions atomiques :
          1. Met à jour facture_patient → statut 'Payé' + mode + téléphone
          2. Met à jour statut_facture de chaque service lié (consultation,
             examen, chururgie, commandeslunettes)
          3. Met à jour statut_patient → 'Libéré' dans visite
          4. Met à jour statut_visite  → 'terminée' dans visite

        Args:
            code_facture  (str): Code de la facture à solder.
            mode_payement (str): 'Espèces' | 'Mobile Money' | 'Carte bancaire'.
            telephone     (str): Numéro pour confirmation (Mobile Money).

        Returns:
            tuple(bool, str): (succès, message)
        """
        conn = self.db.connect()
        if not conn:
            return False, "Erreur de connexion à la base de données."

        try:
            with conn.cursor(DictCursor) as cursor:

                # 0. Vérifier existence + statut ──────────────────────────────
                cursor.execute(
                    "SELECT code_visite, statut_facture FROM facture_patient WHERE code_facture = %s",
                    (code_facture,)
                )
                facture = cursor.fetchone()
                if not facture:
                    return False, f"Facture '{code_facture}' introuvable."
                if facture["statut_facture"].lower() == "payé":
                    return False, "Cette facture est déjà soldée."

                code_visite = facture["code_visite"]

                # 1. Solder la facture_patient ─────────────────────────────────
                cursor.execute("""
                    UPDATE facture_patient
                    SET statut_facture = 'Payé',
                        Mode_payement  = %s,
                        telephone      = COALESCE(NULLIF(%s, ''), telephone)
                    WHERE code_facture = %s
                """, (mode_payement, telephone, code_facture))

                # 2. Synchroniser les statuts de chaque service ────────────────
                self._synchroniser_statuts_services(cursor, code_visite)

                # 3. Déterminer le statut patient après paiement ──────────
                # Si le patient a un RDV en attente (statut_rendez_vous = 'attente'),
                # il doit rester en "Attente rendez-vous [type_acte]"
                # Sinon, la visite est terminée
                cursor.execute("""
                    SELECT am.type_acte
                    FROM rendez_vous rdv
                    JOIN acte_medical am ON rdv.code_acte = am.code_acte
                    WHERE rdv.code_visite = %s
                      AND LOWER(rdv.statut_rendez_vous) IN ('attente', 'en attente')
                    LIMIT 1
                """, (code_visite,))
                rdv_en_attente = cursor.fetchone()
                
                if rdv_en_attente:
                    # Patient a un RDV en attente → garder statut "Attente rendez-vous [type]"
                    type_acte = (rdv_en_attente.get('type_acte') or '').lower()
                    statut_map = {
                        'examen': 'Attente rendez-vous examen',
                        'chirurgie': 'Attente rendez-vous chirurgie',
                        'lunette': 'Attente rendez-vous lunette',
                        'prescription': 'Attente rendez-vous pharmacie'
                    }
                    nouveau_statut = statut_map.get(type_acte, 'Attente rendez-vous')
                else:
                    # Pas de RDV en attente → visite terminée
                    nouveau_statut = 'Terminée'
                
                cursor.execute("""
                    UPDATE visite
                    SET statut_patient = %s,
                        statut_visite  = 'terminée'
                    WHERE code_visite = %s
                """, (nouveau_statut, code_visite))

                conn.commit()
                return True, "Paiement enregistré avec succès. Patient libéré."

        except pymysql.MySQLError as e:
            conn.rollback()
            return False, f"Erreur SQL lors du paiement : {e}"
        except Exception as e:
            conn.rollback()
            return False, f"Erreur inattendue : {e}"
        finally:
            conn.close()

    def annuler_facture(self, code_facture: str) -> tuple:
        """
        Annule une facture en attente de paiement.
        Une facture déjà payée NE PEUT PAS être annulée.

        Args:
            code_facture (str): Code de la facture à annuler.

        Returns:
            tuple(bool, str): (succès, message)
        """
        conn = self.db.connect()
        if not conn:
            return False, "Erreur de connexion à la base de données."

        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute(
                    "SELECT statut_facture FROM facture_patient WHERE code_facture = %s",
                    (code_facture,)
                )
                facture = cursor.fetchone()
                if not facture:
                    return False, f"Facture '{code_facture}' introuvable."
                if facture["statut_facture"].lower() == "payé":
                    return False, "Impossible d'annuler une facture déjà payée."

                cursor.execute("""
                    UPDATE facture_patient
                    SET statut_facture = 'Annulé'
                    WHERE code_facture = %s
                """, (code_facture,))

                conn.commit()
                return True, "Facture annulée avec succès."

        except pymysql.MySQLError as e:
            conn.rollback()
            return False, f"Erreur SQL : {e}"
        except Exception as e:
            conn.rollback()
            return False, f"Erreur inattendue : {e}"
        finally:
            conn.close()

    # =========================================================================
    # MÉTHODES DE RÉCUPÉRATION
    # =========================================================================

    def obtenir_par_code(self, code_facture: str):
        """
        Retourne un objet FacturePatient par son code.

        Args:
            code_facture (str): Code de la facture.

        Returns:
            FacturePatient | None
        """
        conn = self.db.connect()
        if not conn:
            return None
        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM facture_patient WHERE code_facture = %s",
                    (code_facture,)
                )
                row = cursor.fetchone()
                return self._row_to_object(row) if row else None
        except Exception as e:
            print(f"[FacturePatientDAO] Erreur obtenir_par_code: {e}")
            return None
        finally:
            conn.close()

    def obtenir_par_visite(self, code_visite: str):
        """
        Retourne la facture active d'une visite.
        Utilisé au moment de l'affichage de la caisse.

        Args:
            code_visite (str): Code de la visite.

        Returns:
            FacturePatient | None
        """
        conn = self.db.connect()
        if not conn:
            return None
        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM facture_patient
                    WHERE code_visite = %s
                    ORDER BY date_facture DESC
                    LIMIT 1
                """, (code_visite,))
                row = cursor.fetchone()
                return self._row_to_object(row) if row else None
        except Exception as e:
            print(f"[FacturePatientDAO] Erreur obtenir_par_visite: {e}")
            return None
        finally:
            conn.close()

    def lister_par_session(self, code_session: str) -> list:
        """
        Retourne toutes les factures d'une session avec infos patient (JOIN).
        Triées par date décroissante.

        Args:
            code_session (str): Code de la session.

        Returns:
            list[FacturePatient]
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        f.*,
                        p.nom    AS patient_nom,
                        p.prenom AS patient_prenom
                    FROM facture_patient f
                    LEFT JOIN visite   v ON f.code_visite  = v.code_visite
                    LEFT JOIN patients p ON v.code_patient = p.code_patient
                    WHERE f.code_session = %s
                    ORDER BY f.date_facture DESC
                """, (code_session,))
                rows = cursor.fetchall()
                factures = []
                for row in rows:
                    obj = self._row_to_object(row)
                    obj.nom_patient    = row.get("patient_nom",    "")
                    obj.prenom_patient = row.get("patient_prenom", "")
                    factures.append(obj)
                return factures
        except Exception as e:
            print(f"[FacturePatientDAO] Erreur lister_par_session: {e}")
            return []
        finally:
            conn.close()

    def lister_en_attente(self, code_session: str) -> list:
        """
        Retourne les factures non soldées de la session.
        Utilisé pour la file d'attente caisse.

        Args:
            code_session (str): Code de la session.

        Returns:
            list[FacturePatient]
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        f.*,
                        p.nom    AS patient_nom,
                        p.prenom AS patient_prenom
                    FROM facture_patient f
                    LEFT JOIN visite   v ON f.code_visite  = v.code_visite
                    LEFT JOIN patients p ON v.code_patient = p.code_patient
                    WHERE f.code_session   = %s
                      AND f.statut_facture = 'Attente payement'
                    ORDER BY f.date_facture ASC
                """, (code_session,))
                rows = cursor.fetchall()
                factures = []
                for row in rows:
                    obj = self._row_to_object(row)
                    obj.nom_patient    = row.get("patient_nom",    "")
                    obj.prenom_patient = row.get("patient_prenom", "")
                    factures.append(obj)
                return factures
        except Exception as e:
            print(f"[FacturePatientDAO] Erreur lister_en_attente: {e}")
            return []
        finally:
            conn.close()

    def rechercher_par_critere(self, critere: str, code_session: str) -> list:
        """
        Recherche sur code_facture, nom, prénom ou téléphone patient.

        Args:
            critere      (str): Mot-clé de recherche.
            code_session (str): Code de la session.

        Returns:
            list[FacturePatient]
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            with conn.cursor(DictCursor) as cursor:
                like = f"%{critere}%"
                cursor.execute("""
                    SELECT
                        f.*,
                        p.nom    AS patient_nom,
                        p.prenom AS patient_prenom
                    FROM facture_patient f
                    LEFT JOIN visite   v ON f.code_visite  = v.code_visite
                    LEFT JOIN patients p ON v.code_patient = p.code_patient
                    WHERE f.code_session = %s
                      AND (
                          f.code_facture LIKE %s OR
                          f.telephone    LIKE %s OR
                          p.nom          LIKE %s OR
                          p.prenom       LIKE %s
                      )
                    ORDER BY f.date_facture DESC
                """, (code_session, like, like, like, like))
                rows = cursor.fetchall()
                factures = []
                for row in rows:
                    obj = self._row_to_object(row)
                    obj.nom_patient    = row.get("patient_nom",    "")
                    obj.prenom_patient = row.get("patient_prenom", "")
                    factures.append(obj)
                return factures
        except Exception as e:
            print(f"[FacturePatientDAO] Erreur rechercher_par_critere: {e}")
            return []
        finally:
            conn.close()

    def patients_en_attente_paiement(self, code_session: str) -> list:
        """
        Retourne les patients avec statut_patient = 'Attente payement'
        sans encore de facture générée.
        Utilisé pour déclencher la génération depuis la vue caisse.

        Args:
            code_session (str): Code de la session.

        Returns:
            list[dict]: [{code_visite, date_visite, urgent, code_patient,
                          nom, prenom, telephone}, ...]
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        v.code_visite,
                        v.date_visite,
                        v.urgent,
                        p.code_patient,
                        p.nom,
                        p.prenom,
                        p.telephone
                    FROM visite v
                    INNER JOIN patients       p ON v.code_patient = p.code_patient
                    LEFT  JOIN facture_patient f ON v.code_visite  = f.code_visite
                    WHERE v.code_session   = %s
                      AND v.statut_patient = 'Attente payement'
                      AND f.code_facture   IS NULL
                    ORDER BY v.urgent DESC, v.date_visite ASC
                """, (code_session,))
                return cursor.fetchall()
        except Exception as e:
            print(f"[FacturePatientDAO] Erreur patients_en_attente_paiement: {e}")
            return []
        finally:
            conn.close()

    def reinitialiser_facture(self, code_facture: str) -> tuple:
        """
        Reinitialise une facture non payee :
        - conserve le statut 'Attente payement'
        - supprime toutes les lignes panier
        - remet le montant a 0 et le mode de paiement vide

        Args:
            code_facture (str): Code de la facture a reinitialiser.

        Returns:
            tuple(bool, str): (succes, message)
        """
        conn = self.db.connect()
        if not conn:
            return False, "Erreur de connexion à la base de données."

        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute(
                    "SELECT statut_facture FROM facture_patient WHERE code_facture = %s",
                    (code_facture,)
                )
                facture = cursor.fetchone()
                if not facture:
                    return False, f"Facture '{code_facture}' introuvable."
                if str(facture.get("statut_facture", "")).lower() == "payé":
                    return False, "Impossible de reinitialiser une facture déjà payée."

                # Supprimer lignes panier
                cursor.execute(
                    "DELETE FROM panier_facture WHERE code_facture = %s",
                    (code_facture,)
                )

                # Remettre l'entete en attente
                cursor.execute("""
                    UPDATE facture_patient
                    SET Montant_total = 0,
                        Mode_payement = '',
                        statut_facture = 'Attente payement'
                    WHERE code_facture = %s
                """, (code_facture,))

                conn.commit()
                return True, "Facture reinitialisee."

        except pymysql.MySQLError as e:
            conn.rollback()
            return False, f"Erreur SQL : {e}"
        except Exception as e:
            conn.rollback()
            return False, f"Erreur inattendue : {e}"
        finally:
            conn.close()

    def supprimer_facture(self, code_facture: str) -> tuple:
        """
        Supprime une facture non payee et toutes ses lignes panier.
        Utilise pour abandonner une facture et remettre la visite en attente.

        Args:
            code_facture (str): Code de la facture a supprimer.

        Returns:
            tuple(bool, str): (succes, message)
        """
        conn = self.db.connect()
        if not conn:
            return False, "Erreur de connexion à la base de données."

        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute(
                    "SELECT code_visite, statut_facture FROM facture_patient WHERE code_facture = %s",
                    (code_facture,)
                )
                facture = cursor.fetchone()
                if not facture:
                    return False, f"Facture '{code_facture}' introuvable."
                if str(facture.get("statut_facture", "")).lower() == "payé":
                    return False, "Impossible de supprimer une facture déjà payée."

                code_visite = facture.get("code_visite")

                # Supprimer lignes panier puis entete
                cursor.execute(
                    "DELETE FROM panier_facture WHERE code_facture = %s",
                    (code_facture,)
                )
                cursor.execute(
                    "DELETE FROM facture_patient WHERE code_facture = %s",
                    (code_facture,)
                )

                # Remettre la visite en attente de paiement (si besoin)
                if code_visite:
                    cursor.execute("""
                        UPDATE visite
                        SET statut_patient = 'Attente payement'
                        WHERE code_visite = %s
                    """, (code_visite,))

                conn.commit()
                return True, "Facture supprimée."

        except pymysql.MySQLError as e:
            conn.rollback()
            return False, f"Erreur SQL : {e}"
        except Exception as e:
            conn.rollback()
            return False, f"Erreur inattendue : {e}"
        finally:
            conn.close()

    def recalculer_montant_facture(self, code_facture: str) -> bool:
        """
        Recalcule et met a jour Montant_total a partir des lignes panier.
        Utilise la colonne `prix_appliqué` de panier_facture.

        Args:
            code_facture (str): Code facture.

        Returns:
            bool
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute("""
                    SELECT COALESCE(SUM(quantite_facture * `prix_appliqué`), 0) AS total
                    FROM panier_facture
                    WHERE code_facture = %s
                """, (code_facture,))
                row = cursor.fetchone()
                total = float(row["total"] or 0) if row else 0.0
                cursor.execute("""
                    UPDATE facture_patient
                    SET Montant_total = %s
                    WHERE code_facture = %s
                """, (total, code_facture))
                conn.commit()
                return True
        except Exception as e:
            conn.rollback()
            print(f"[FacturePatientDAO] Erreur recalculer_montant_facture: {e}")
            return False
        finally:
            conn.close()

    def lister_services_visite(self, code_visite: str) -> list:
        """
        Retourne la liste des services liés à une visite
        (consultation, examen, chirurgie, lunettes, pharmacie).

        Args:
            code_visite (str): Code de la visite.

        Returns:
            list[dict]
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            with conn.cursor(DictCursor) as cursor:
                return self._collecter_lignes_panier(cursor, code_visite)
        except Exception as e:
            print(f"[FacturePatientDAO] Erreur lister_services_visite: {e}")
            return []
        finally:
            conn.close()

    def details_facture_pdf(self, code_facture: str) -> dict:
        """
        Retourne toutes les données nécessaires à la génération du PDF facture patient.

        Args:
            code_facture (str): Code facture.

        Returns:
            dict: {facture, patient, consultations, examens, chirurgies, lunettes, prescriptions, resume}
        """
        conn = self.db.connect()
        if not conn:
            return {}
        try:
            with conn.cursor(DictCursor) as cursor:
                # Facture + patient + visite
                cursor.execute("""
                    SELECT
                        f.*,
                        v.code_patient,
                        v.code_visite,
                        v.date_visite,
                        p.nom       AS patient_nom,
                        p.prenom    AS patient_prenom,
                        p.telephone AS patient_telephone,
                        p.adresse   AS patient_adresse,
                        p.naissance AS patient_naissance
                    FROM facture_patient f
                    LEFT JOIN visite   v ON f.code_visite  = v.code_visite
                    LEFT JOIN patients p ON v.code_patient = p.code_patient
                    WHERE f.code_facture = %s
                """, (code_facture,))
                facture = cursor.fetchone()
                if not facture:
                    return {}

                code_visite = facture.get("code_visite")
                patient = {
                    "code_patient": facture.get("code_patient", ""),
                    "code_visite": code_visite,
                    "nom": facture.get("patient_nom", ""),
                    "prenom": facture.get("patient_prenom", ""),
                    "telephone": facture.get("patient_telephone", ""),
                    "adresse": facture.get("patient_adresse", ""),
                    "naissance": facture.get("patient_naissance", None),
                }

                # Consultations
                cursor.execute("""
                    SELECT
                        c.diagnostique,
                        c.frais_consultation,
                        c.date_consultation,
                        per.nom   AS medecin_nom,
                        per.prenom AS medecin_prenom
                    FROM consultation c
                    LEFT JOIN personnel per ON c.code_personnel = per.code
                    WHERE c.code_visite = %s
                    ORDER BY c.date_consultation DESC
                """, (code_visite,))
                consultations = cursor.fetchall()

                # Examens
                cursor.execute("""
                    SELECT
                        e.libelle_examen,
                        e.frais_examen,
                        e.date_examen,
                        per.nom   AS medecin_nom,
                        per.prenom AS medecin_prenom
                    FROM examen e
                    INNER JOIN acte_medical am ON e.code_acte        = am.code_acte
                    INNER JOIN consultation  c  ON am.code_consultation = c.code
                    LEFT JOIN personnel per ON e.code_personnel = per.code
                    WHERE c.code_visite = %s
                    ORDER BY e.date_examen DESC
                """, (code_visite,))
                examens = cursor.fetchall()

                # Chirurgies
                cursor.execute("""
                    SELECT
                        ch.libelle_chururgie,
                        ch.frais_chururgie,
                        ch.date_chururgie,
                        per.nom   AS medecin_nom,
                        per.prenom AS medecin_prenom
                    FROM chururgie ch
                    INNER JOIN acte_medical am ON ch.code_acte        = am.code_acte
                    INNER JOIN consultation  c  ON am.code_consultation = c.code
                    LEFT JOIN personnel per ON ch.code_personnel = per.code
                    WHERE c.code_visite = %s
                    ORDER BY ch.date_chururgie DESC
                """, (code_visite,))
                chirurgies = cursor.fetchall()

                # Lunettes
                cursor.execute("""
                    SELECT
                        cl.numero_verre,
                        cl.prix,
                        cl.date_commande,
                        per.nom   AS medecin_nom,
                        per.prenom AS medecin_prenom
                    FROM commandeslunettes cl
                    INNER JOIN acte_medical am ON cl.code_acte        = am.code_acte
                    INNER JOIN consultation  c  ON am.code_consultation = c.code
                    LEFT JOIN personnel per ON cl.code_personnel = per.code
                    WHERE c.code_visite = %s
                    ORDER BY cl.date_commande DESC
                """, (code_visite,))
                lunettes = cursor.fetchall()

                # Prescriptions
                cursor.execute("""
                    SELECT
                        pp.designation,
                        pp.quantite_prescript,
                        pp.prix_applique,
                        per.nom   AS medecin_nom,
                        per.prenom AS medecin_prenom
                    FROM prescription_produit pp
                    INNER JOIN acte_medical am ON pp.code_acte        = am.code_acte
                    INNER JOIN consultation  c  ON am.code_consultation = c.code
                    LEFT JOIN personnel per ON c.code_personnel = per.code
                    WHERE c.code_visite = %s
                    ORDER BY pp.code_prescription ASC
                """, (code_visite,))
                prescriptions = cursor.fetchall()

                # Resume des totaux
                total_consultation = sum(float(c.get("frais_consultation", 0) or 0) for c in consultations)
                total_examens = sum(float(e.get("frais_examen", 0) or 0) for e in examens)
                total_chirurgie = sum(float(c.get("frais_chururgie", 0) or 0) for c in chirurgies)
                total_lunettes = sum(float(l.get("prix", 0) or 0) for l in lunettes)
                total_prescriptions = sum(
                    float(p.get("quantite_prescript", 0) or 0) * float(p.get("prix_applique", 0) or 0)
                    for p in prescriptions
                )
                total_facture = total_consultation + total_examens + total_chirurgie + total_lunettes + total_prescriptions

                resume = {
                    "total_consultation": total_consultation,
                    "total_examens": total_examens,
                    "total_chirurgie": total_chirurgie,
                    "total_lunettes": total_lunettes,
                    "total_prescriptions": total_prescriptions,
                    "total_facture": total_facture,
                }

                return {
                    "facture": facture,
                    "patient": patient,
                    "consultations": consultations,
                    "examens": examens,
                    "chirurgies": chirurgies,
                    "lunettes": lunettes,
                    "prescriptions": prescriptions,
                    "resume": resume,
                }
        except Exception as e:
            print(f"[FacturePatientDAO] Erreur details_facture_pdf: {e}")
            return {}
        finally:
            conn.close()

    # =========================================================================
    # MÉTHODES STATISTIQUES — CARDS
    # =========================================================================

    def nombre_factures_aujourd_hui(self, code_session: str) -> int:
        """Card 'Factures du Jour' : factures créées aujourd'hui."""
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute("""
                    SELECT COUNT(*) AS total
                    FROM facture_patient
                    WHERE code_session = %s
                      AND DATE(date_facture) = CURDATE()
                """, (code_session,))
                result = cursor.fetchone()
                return int(result["total"]) if result else 0
        except Exception as e:
            print(f"[FacturePatientDAO] Erreur nombre_factures_aujourd_hui: {e}")
            return 0
        finally:
            conn.close()

    def nombre_en_attente(self, code_session: str) -> int:
        """Card 'En Attente' : factures non soldées de la session."""
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute("""
                    SELECT COUNT(*) AS total
                    FROM facture_patient
                    WHERE code_session   = %s
                      AND statut_facture = 'Attente payement'
                """, (code_session,))
                result = cursor.fetchone()
                return int(result["total"]) if result else 0
        except Exception as e:
            print(f"[FacturePatientDAO] Erreur nombre_en_attente: {e}")
            return 0
        finally:
            conn.close()

    def nombre_total_par_session(self, code_session: str) -> int:
        """Card 'Total Session' : toutes les factures de la session."""
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute("""
                    SELECT COUNT(*) AS total
                    FROM facture_patient
                    WHERE code_session = %s
                """, (code_session,))
                result = cursor.fetchone()
                return int(result["total"]) if result else 0
        except Exception as e:
            print(f"[FacturePatientDAO] Erreur nombre_total_par_session: {e}")
            return 0
        finally:
            conn.close()

    # =========================================================================
    # MÉTHODES STATISTIQUES — REVENUS
    # =========================================================================

    def revenu_total(self, code_session: str,
                     date_debut: str = None,
                     date_fin:   str = None) -> float:
        """
        Chiffre d'affaires total des factures PAYÉES.
        Filtre date optionnel au format 'YYYY-MM-DD'.

        Args:
            code_session (str): Code de la session.
            date_debut   (str): Date de début (optionnel).
            date_fin     (str): Date de fin (optionnel).

        Returns:
            float: Montant total encaissé.
        """
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            with conn.cursor(DictCursor) as cursor:
                if date_debut and date_fin:
                    cursor.execute("""
                        SELECT COALESCE(SUM(Montant_total), 0) AS total
                        FROM facture_patient
                        WHERE code_session   = %s
                          AND statut_facture = 'Payé'
                          AND DATE(date_facture) BETWEEN %s AND %s
                    """, (code_session, date_debut, date_fin))
                else:
                    cursor.execute("""
                        SELECT COALESCE(SUM(Montant_total), 0) AS total
                        FROM facture_patient
                        WHERE code_session   = %s
                          AND statut_facture = 'Payé'
                    """, (code_session,))
                row = cursor.fetchone()
                return float(row["total"]) if row else 0.0
        except Exception as e:
            print(f"[FacturePatientDAO] Erreur revenu_total: {e}")
            return 0.0
        finally:
            conn.close()

    def resume_financier(self, code_session: str) -> dict:
        """
        Synthèse financière complète pour le dashboard paiement.

        Retourne :
            total_encaisse    (float) : Montant total des factures payées.
            total_en_attente  (float) : Créances en cours.
            nombre_payees     (int)   : Nombre de factures soldées.
            nombre_en_attente (int)   : Nombre de factures non soldées.
            taux_recouvrement (float) : % factures payées / total.

        Args:
            code_session (str): Code de la session.

        Returns:
            dict
        """
        conn = self.db.connect()
        if not conn:
            return self._resume_vide()
        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        COALESCE(SUM(CASE WHEN statut_facture = 'Payé'
                                         THEN Montant_total ELSE 0 END), 0) AS encaisse,
                        COALESCE(SUM(CASE WHEN statut_facture = 'Attente payement'
                                         THEN Montant_total ELSE 0 END), 0) AS en_attente,
                        COUNT(CASE WHEN statut_facture = 'Payé'
                                   THEN 1 END)                               AS nb_payees,
                        COUNT(CASE WHEN statut_facture = 'Attente payement'
                                   THEN 1 END)                               AS nb_attente,
                        COUNT(*)                                              AS nb_total
                    FROM facture_patient
                    WHERE code_session = %s
                """, (code_session,))
                row = cursor.fetchone()
                if not row:
                    return self._resume_vide()

                nb_total  = int(row["nb_total"]  or 0)
                nb_payees = int(row["nb_payees"] or 0)
                taux      = round((nb_payees / nb_total) * 100, 1) if nb_total > 0 else 0.0

                return {
                    "total_encaisse":    float(row["encaisse"]   or 0),
                    "total_en_attente":  float(row["en_attente"] or 0),
                    "nombre_payees":     nb_payees,
                    "nombre_en_attente": int(row["nb_attente"]   or 0),
                    "taux_recouvrement": taux,
                }
        except Exception as e:
            print(f"[FacturePatientDAO] Erreur resume_financier: {e}")
            return self._resume_vide()
        finally:
            conn.close()

    def revenu_par_mois(self, code_session: str) -> dict:
        """
        Revenus mensuels (factures payées uniquement).
        Format : {'Jan': 0.0, 'Fév': 0.0, ..., 'Déc': 0.0}

        Args:
            code_session (str): Code de la session.

        Returns:
            dict
        """
        stats = {
            'Jan': 0.0, 'Fév': 0.0, 'Mar': 0.0, 'Avr': 0.0,
            'Mai': 0.0, 'Juin': 0.0, 'Juil': 0.0, 'Août': 0.0,
            'Sep': 0.0, 'Oct': 0.0, 'Nov': 0.0, 'Déc': 0.0
        }
        mois_map = {
            1: 'Jan', 2: 'Fév', 3: 'Mar',  4: 'Avr',
            5: 'Mai', 6: 'Juin', 7: 'Juil', 8: 'Août',
            9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Déc'
        }
        conn = self.db.connect()
        if not conn:
            return stats
        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        MONTH(date_facture)        AS num_mois,
                        SUM(Montant_total)          AS total
                    FROM facture_patient
                    WHERE code_session   = %s
                      AND statut_facture = 'Payé'
                    GROUP BY MONTH(date_facture)
                """, (code_session,))
                for row in cursor.fetchall():
                    m = row["num_mois"]
                    if m in mois_map:
                        stats[mois_map[m]] = float(row["total"] or 0)
            return stats
        except Exception as e:
            print(f"[FacturePatientDAO] Erreur revenu_par_mois: {e}")
            return stats
        finally:
            conn.close()

    def repartition_par_mode_paiement(self, code_session: str) -> list:
        """
        Répartition des paiements par mode.
        Utilisé pour graphique en secteurs (camembert).

        Args:
            code_session (str): Code de la session.

        Returns:
            list[dict]: [{'Mode_payement', 'nombre', 'total'}, ...]
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        Mode_payement,
                        COUNT(*)           AS nombre,
                        SUM(Montant_total)  AS total
                    FROM facture_patient
                    WHERE code_session   = %s
                      AND statut_facture = 'Payé'
                      AND Mode_payement  IS NOT NULL
                    GROUP BY Mode_payement
                    ORDER BY nombre DESC
                """, (code_session,))
                return cursor.fetchall()
        except Exception as e:
            print(f"[FacturePatientDAO] Erreur repartition_par_mode_paiement: {e}")
            return []
        finally:
            conn.close()

    # =========================================================================
    # MÉTHODES PRIVÉES — COLLECTE DES LIGNES PANIER
    # =========================================================================

    def _collecter_lignes_panier(self, cursor, code_visite: str) -> list:
        """
        Agrège les frais de chaque service rendu lors de la visite
        en une liste de dictionnaires prêts à construire des PanierFacture.

        Règle : une ligne par type de service, seulement si montant > 0.
        Les services (examen, chirurgie, lunettes, pharmacie) sont liés via :
          acte_medical.code_acte  ←→  service
          acte_medical.code_consultation  →  consultation.code  →  code_visite

        Args:
            cursor    : Curseur actif dans la transaction courante.
            code_visite (str): Code de la visite.

        Returns:
            list[dict]: [{'designation', 'numero_reference',
                          'quantite_facture', 'prix_applique'}, ...]
        """
        lignes = []

        # 1. Consultation ──────────────────────────────────────────────────────
        cursor.execute("""
            SELECT code, frais_consultation
            FROM consultation
            WHERE code_visite = %s
            LIMIT 1
        """, (code_visite,))
        row = cursor.fetchone()
        if row and row.get("frais_consultation") and float(row["frais_consultation"]) > 0:
            lignes.append({
                "designation":      "Consultation",
                "numero_reference": row["code"],
                "quantite_facture": 1,
                "prix_applique":    float(row["frais_consultation"]),
            })

        # 2. Examen — lié via code_acte → acte_visite (role='execution') OU consultation
        cursor.execute("""
            SELECT MIN(e.code)                           AS ref_examen,
                   COALESCE(SUM(e.frais_examen), 0)     AS total_examen
            FROM examen e
            INNER JOIN acte_medical am ON e.code_acte = am.code_acte
            LEFT JOIN acte_visite av ON am.code_acte = av.code_acte AND av.role_visite = 'execution'
            LEFT JOIN consultation c ON am.code_consultation = c.code
            WHERE av.code_visite = %s OR c.code_visite = %s
        """, (code_visite, code_visite))
        row = cursor.fetchone()
        if row and row.get("total_examen") and float(row["total_examen"]) > 0:
            lignes.append({
                "designation":      "Examen",
                "numero_reference": row["ref_examen"] or "EXM",
                "quantite_facture": 1,
                "prix_applique":    float(row["total_examen"]),
            })

        # 3. Chirurgie — lié via code_acte → acte_visite (role='execution') OU consultation
        cursor.execute("""
            SELECT MIN(ch.code)                              AS ref_chururgie,
                   COALESCE(SUM(ch.frais_chururgie), 0)     AS total_chururgie
            FROM chururgie ch
            INNER JOIN acte_medical am ON ch.code_acte = am.code_acte
            LEFT JOIN acte_visite av ON am.code_acte = av.code_acte AND av.role_visite = 'execution'
            LEFT JOIN consultation c ON am.code_consultation = c.code
            WHERE av.code_visite = %s OR c.code_visite = %s
        """, (code_visite, code_visite))
        row = cursor.fetchone()
        if row and row.get("total_chururgie") and float(row["total_chururgie"]) > 0:
            lignes.append({
                "designation":      "Chirurgie",
                "numero_reference": row["ref_chururgie"] or "CHR",
                "quantite_facture": 1,
                "prix_applique":    float(row["total_chururgie"]),
            })

        # 4. Lunettes — lié via code_acte → acte_visite (role='execution') OU consultation
        cursor.execute("""
            SELECT MIN(cl.code)                       AS ref_lunette,
                   COALESCE(SUM(cl.prix), 0)          AS total_lunette
            FROM commandeslunettes cl
            INNER JOIN acte_medical am ON cl.code_acte = am.code_acte
            LEFT JOIN acte_visite av ON am.code_acte = av.code_acte AND av.role_visite = 'execution'
            LEFT JOIN consultation c ON am.code_consultation = c.code
            WHERE av.code_visite = %s OR c.code_visite = %s
        """, (code_visite, code_visite))
        row = cursor.fetchone()
        if row and row.get("total_lunette") and float(row["total_lunette"]) > 0:
            lignes.append({
                "designation":      "Lunettes",
                "numero_reference": row["ref_lunette"] or "LUN",
                "quantite_facture": 1,
                "prix_applique":    float(row["total_lunette"]),
            })

        # 5. Pharmacie (SUM) — lié via code_acte → acte_visite (role='execution') OU consultation
        cursor.execute("""
            SELECT MIN(pp.code_prescription)                              AS ref_pharmacie,
                   COALESCE(SUM(pp.prix_applique * pp.quantite_prescript), 0) AS total_pharmacie
            FROM prescription_produit pp
            INNER JOIN acte_medical am ON pp.code_acte = am.code_acte
            LEFT JOIN acte_visite av ON am.code_acte = av.code_acte AND av.role_visite = 'execution'
            LEFT JOIN consultation c ON am.code_consultation = c.code
            WHERE av.code_visite = %s OR c.code_visite = %s
        """, (code_visite, code_visite))
        row = cursor.fetchone()
        if row and row.get("total_pharmacie") and float(row["total_pharmacie"]) > 0:
            lignes.append({
                "designation":      "Pharmacie",
                "numero_reference": row["ref_pharmacie"] or "PRS",
                "quantite_facture": 1,
                "prix_applique":    float(row["total_pharmacie"]),
            })

        return lignes

    def _synchroniser_statuts_services(self, cursor, code_visite: str) -> None:
        """
        Met à jour statut_facture = 'Payé' dans chaque table de service
        liée à la visite, après validation du paiement.

        - consultation  : liée directement via code_visite
        - examen, chururgie, commandeslunettes : liées via
          code_acte → acte_medical → consultation → visite
        Note : prescription_produit n'a pas de statut_facture.

        Args:
            cursor      : Curseur actif dans la transaction courante.
            code_visite (str): Code de la visite.
        """
        # Consultation — lien direct
        try:
            cursor.execute(
                "UPDATE consultation SET statut_facture = 'Payé' WHERE code_visite = %s",
                (code_visite,)
            )
        except pymysql.MySQLError as e:
            print(f"[FacturePatientDAO] Warning sync statut consultation: {e}")

        # Services liés via acte_medical → consultation → visite
        for table in ["examen", "chururgie", "commandeslunettes"]:
            try:
                cursor.execute(f"""
                    UPDATE {table} t
                    INNER JOIN acte_medical am ON t.code_acte        = am.code_acte
                    INNER JOIN consultation  c  ON am.code_consultation = c.code
                    SET t.statut_facture = 'Payé'
                    WHERE c.code_visite = %s
                """, (code_visite,))
            except pymysql.MySQLError as e:
                print(f"[FacturePatientDAO] Warning sync statut {table}: {e}")

    # =========================================================================
    # MÉTHODES PRIVÉES — GÉNÉRATION DE CODES ET CONVERSION
    # =========================================================================

    def _generer_code(self, cursor) -> str:
        """Génère le prochain code FCT : FCT001, FCT002, ..."""
        try:
            cursor.execute(
                "SELECT code_facture FROM facture_patient ORDER BY code_facture DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                last_code = row["code_facture"] if isinstance(row, dict) else row[0]
                last_num  = int(last_code[3:])
                return f"FCT{last_num + 1:03d}"
            return "FCT001"
        except Exception as e:
            print(f"[FacturePatientDAO] Erreur _generer_code: {e}")
            return "FCT" + datetime.now().strftime("%H%M%S")

    def _row_to_object(self, row) -> FacturePatient:
        """Convertit une ligne DictCursor en objet FacturePatient."""
        return FacturePatient(
            code_facture   = row["code_facture"],
            code_visite    = row["code_visite"],
            montant_total  = float(row["Montant_total"] or 0),
            mode_payement  = row.get("Mode_payement")  or "",
            telephone      = row.get("telephone")       or "",
            statut_facture = row.get("statut_facture")  or "Attente payement",
            date_facture   = row.get("date_facture"),
            code_session   = row["code_session"],
        )

    @staticmethod
    def _resume_vide() -> dict:
        """Retourne un dictionnaire résumé vide (cas d'erreur ou session vide)."""
        return {
            "total_encaisse":    0.0,
            "total_en_attente":  0.0,
            "nombre_payees":     0,
            "nombre_en_attente": 0,
            "taux_recouvrement": 0.0,
        }
