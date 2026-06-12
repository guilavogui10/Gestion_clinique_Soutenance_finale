"""
dao_resultat_medical.py
------------------------
DAO pour la table resultat_medical.
Gère le stockage et la récupération des fichiers résultats
(images, vidéos, PDFs) liés à un acte médical ou une consultation.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.connexion_db import DBConnection
from models.model_resultat_medical import (
    ResultatMedical, TypeSource, TypeFichier, NiveauConfidentialite
)


class ResultatMedicalDAO:

    def __init__(self):
        self.db = DBConnection()

    # =========================================================================
    # GÉNÉRATION DE CODE
    # =========================================================================

    def generate_code_resultat(self) -> str:
        """Génère un code unique de type RES-XXXXXXXX."""
        conn = self.db.connect()
        if not conn:
            import uuid
            return "RES-" + uuid.uuid4().hex[:8].upper()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id_resultat FROM resultat_medical ORDER BY id_resultat DESC LIMIT 1"
            )
            row = cursor.fetchone() or {}
            dernier = row.get("id_resultat", "RES-00000000")
            try:
                numero = int(dernier.split("-")[-1]) + 1
            except (ValueError, IndexError):
                numero = 1
            return f"RES-{numero:08d}"
        except Exception:
            import uuid
            return "RES-" + uuid.uuid4().hex[:8].upper()
        finally:
            self.db.close()

    # =========================================================================
    # ÉCRITURE
    # =========================================================================

    def ajouter(self, resultat: ResultatMedical) -> bool:
        """Enregistre un nouveau résultat médical en base."""
        if not resultat.type_source or resultat.type_source not in TypeSource.VALEURS:
            return False
        if not resultat.chemin_fichier:
            return False
        if resultat.type_fichier not in TypeFichier.VALEURS:
            return False
        if resultat.niveau_confidentialite not in NiveauConfidentialite.VALEURS:
            resultat.niveau_confidentialite = NiveauConfidentialite.MOYEN

        if not resultat.id_resultat:
            resultat.id_resultat = self.generate_code_resultat()

        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """INSERT INTO resultat_medical
                       (id_resultat, type_source, code_acte_medical, code_consultation,
                        type_fichier, chemin_fichier, empreinte_sha256, hmac_integrite,
                        description, date_upload, niveau_confidentialite)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        resultat.id_resultat,
                        resultat.type_source,
                        resultat.code_acte_medical,
                        resultat.code_consultation,
                        resultat.type_fichier,
                        resultat.chemin_fichier,
                        resultat.empreinte_sha256,
                        resultat.hmac_integrite,
                        resultat.description,
                        resultat.date_upload,
                        resultat.niveau_confidentialite,
                    )
                )
            except Exception as e:
                if "Unknown column" not in str(e):
                    raise

                cursor.execute(
                    """INSERT INTO resultat_medical
                       (id_resultat, type_source, code_acte_medical, code_consultation,
                        type_fichier, chemin_fichier, description,
                        date_upload, niveau_confidentialite)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        resultat.id_resultat,
                        resultat.type_source,
                        resultat.code_acte_medical,
                        resultat.code_consultation,
                        resultat.type_fichier,
                        resultat.chemin_fichier,
                        resultat.description,
                        resultat.date_upload,
                        resultat.niveau_confidentialite,
                    )
                )
            conn.commit()
            return True
        except Exception as e:
            print(f"[ResultatMedicalDAO] Erreur ajouter: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    def modifier(self, resultat: ResultatMedical) -> bool:
        """Met à jour description et niveau de confidentialité d'un résultat."""
        if not resultat.id_resultat:
            return False
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE resultat_medical
                   SET description = %s, niveau_confidentialite = %s
                   WHERE id_resultat = %s""",
                (resultat.description, resultat.niveau_confidentialite, resultat.id_resultat)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ResultatMedicalDAO] Erreur modifier: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    def modifier_complet(self, resultat: ResultatMedical) -> bool:
        """Met à jour toutes les propriétés modifiables du résultat."""
        if not resultat.id_resultat:
            return False
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE resultat_medical
                   SET type_source = %s, code_acte_medical = %s, code_consultation = %s,
                       type_fichier = %s, chemin_fichier = %s, empreinte_sha256 = %s, 
                       hmac_integrite = %s, description = %s, niveau_confidentialite = %s
                   WHERE id_resultat = %s""",
                (
                    resultat.type_source,
                    resultat.code_acte_medical,
                    resultat.code_consultation,
                    resultat.type_fichier,
                    resultat.chemin_fichier,
                    resultat.empreinte_sha256,
                    resultat.hmac_integrite,
                    resultat.description,
                    resultat.niveau_confidentialite,
                    resultat.id_resultat
                )
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            if "Unknown column" not in str(e):
                print(f"[ResultatMedicalDAO] Erreur modifier_complet: {e}")
                conn.rollback()
                return False
            # Fallback
            try:
                cursor.execute(
                    """UPDATE resultat_medical
                       SET type_source = %s, code_acte_medical = %s, code_consultation = %s,
                           type_fichier = %s, chemin_fichier = %s, 
                           description = %s, niveau_confidentialite = %s
                       WHERE id_resultat = %s""",
                    (
                        resultat.type_source,
                        resultat.code_acte_medical,
                        resultat.code_consultation,
                        resultat.type_fichier,
                        resultat.chemin_fichier,
                        resultat.description,
                        resultat.niveau_confidentialite,
                        resultat.id_resultat
                    )
                )
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e2:
                print(f"[ResultatMedicalDAO] Erreur modifier_complet fallback: {e2}")
                conn.rollback()
                return False
        finally:
            self.db.close()


    def supprimer(self, id_resultat: int) -> bool:
        """Supprime un résultat par son id (suppression du fichier physique côté service)."""
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM resultat_medical WHERE id_resultat = %s",
                (id_resultat,)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ResultatMedicalDAO] Erreur supprimer: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    # =========================================================================
    # LECTURE
    # =========================================================================

    def obtenir_par_id(self, id_resultat: int) -> ResultatMedical | None:
        """Retourne un résultat par son id."""
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM resultat_medical WHERE id_resultat = %s",
                (id_resultat,)
            )
            row = cursor.fetchone()
            return self._row_to_object(row) if row else None
        except Exception as e:
            print(f"[ResultatMedicalDAO] Erreur obtenir_par_id: {e}")
            return None
        finally:
            self.db.close()

    def lister_par_acte(self, code_acte_medical: str) -> list:
        """Retourne tous les résultats liés à un acte médical."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM resultat_medical
                   WHERE code_acte_medical = %s
                   ORDER BY date_upload ASC""",
                (code_acte_medical,)
            )
            return [self._row_to_object(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"[ResultatMedicalDAO] Erreur lister_par_acte: {e}")
            return []
        finally:
            self.db.close()

    def lister_par_consultation(self, code_consultation: str) -> list:
        """Retourne tous les résultats liés à une consultation."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM resultat_medical
                   WHERE code_consultation = %s
                   ORDER BY date_upload ASC""",
                (code_consultation,)
            )
            return [self._row_to_object(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"[ResultatMedicalDAO] Erreur lister_par_consultation: {e}")
            return []
        finally:
            self.db.close()

    def lister_par_type_fichier(self, code_acte_medical: str, type_fichier: str) -> list:
        """Retourne les résultats d'un acte filtrés par type de fichier."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM resultat_medical
                   WHERE code_acte_medical = %s AND type_fichier = %s
                   ORDER BY date_upload ASC""",
                (code_acte_medical, type_fichier)
            )
            return [self._row_to_object(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"[ResultatMedicalDAO] Erreur lister_par_type_fichier: {e}")
            return []
        finally:
            self.db.close()

    def source_a_des_resultats(self, code_acte_medical: str = None, code_consultation: str = None) -> bool:
        """Vérifie si un acte ou une consultation a au moins un résultat."""
        if not code_acte_medical and not code_consultation:
            return False
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            if code_acte_medical:
                cursor.execute(
                    "SELECT COUNT(*) AS total FROM resultat_medical WHERE code_acte_medical = %s",
                    (code_acte_medical,)
                )
            else:
                cursor.execute(
                    "SELECT COUNT(*) AS total FROM resultat_medical WHERE code_consultation = %s",
                    (code_consultation,)
                )
            row = cursor.fetchone() or {}
            return row.get("total", 0) > 0
        except Exception as e:
            print(f"[ResultatMedicalDAO] Erreur source_a_des_resultats: {e}")
            return False
        finally:
            self.db.close()

    def lister_par_type_source(self, type_source: str) -> list:
        """Retourne tous les résultats d'un type de source donné, avec infos patient."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT rm.*,
                          COALESCE(p1.nom,    p2.nom)    AS patient_nom,
                          COALESCE(p1.prenom, p2.prenom) AS patient_prenom
                   FROM resultat_medical rm
                   -- Via consultation directe
                   LEFT JOIN consultation c   ON rm.code_consultation = c.code
                   LEFT JOIN visite v1        ON c.code_visite = v1.code_visite
                   LEFT JOIN patients p1      ON v1.code_patient = p1.code_patient
                   -- Via acte_medical
                   LEFT JOIN acte_medical am  ON rm.code_acte_medical = am.code_acte
                   LEFT JOIN consultation c2  ON am.code_consultation = c2.code
                   LEFT JOIN visite v2        ON c2.code_visite = v2.code_visite
                   LEFT JOIN patients p2      ON v2.code_patient = p2.code_patient
                   WHERE rm.type_source = %s
                   ORDER BY rm.date_upload DESC""",
                (type_source,)
            )
            return [self._row_to_object(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"[ResultatMedicalDAO] Erreur lister_par_type_source: {e}")
            return []
        finally:
            self.db.close()

    def compter_par_type_source(self) -> dict:
        """Retourne le nombre de résultats groupés par type de source."""
        conn = self.db.connect()
        if not conn:
            return {}
        try:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT type_source, COUNT(*) AS total
                   FROM resultat_medical
                   GROUP BY type_source"""
            )
            return {row.get("type_source", ""): row.get("total", 0)
                    for row in cursor.fetchall()}
        except Exception as e:
            print(f"[ResultatMedicalDAO] Erreur compter_par_type_source: {e}")
            return {}
        finally:
            self.db.close()

    def lister_par_patient(self, code_patient: str) -> list:
        """Retourne tous les résultats liés à un patient (via JOINs consultation + acte)."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT rm.*,
                          COALESCE(p1.nom,    p2.nom)    AS patient_nom,
                          COALESCE(p1.prenom, p2.prenom) AS patient_prenom
                   FROM resultat_medical rm
                   LEFT JOIN consultation c   ON rm.code_consultation = c.code
                   LEFT JOIN visite v1        ON c.code_visite = v1.code_visite
                   LEFT JOIN patients p1      ON v1.code_patient = p1.code_patient
                   LEFT JOIN acte_medical am  ON rm.code_acte_medical = am.code_acte
                   LEFT JOIN consultation c2  ON am.code_consultation = c2.code
                   LEFT JOIN visite v2        ON c2.code_visite = v2.code_visite
                   LEFT JOIN patients p2      ON v2.code_patient = p2.code_patient
                   WHERE v1.code_patient = %s OR v2.code_patient = %s
                   ORDER BY rm.date_upload DESC""",
                (code_patient, code_patient)
            )
            return [self._row_to_object(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"[ResultatMedicalDAO] Erreur lister_par_patient: {e}")
            return []
        finally:
            self.db.close()

    # =========================================================================
    # CONVERSION
    # =========================================================================

    def _row_to_object(self, row: dict) -> ResultatMedical:
        obj = ResultatMedical(
            id_resultat            = row.get("id_resultat"),
            type_source            = row.get("type_source"),
            code_acte_medical      = row.get("code_acte_medical"),
            code_consultation      = row.get("code_consultation"),
            type_fichier           = row.get("type_fichier"),
            chemin_fichier         = row.get("chemin_fichier"),
            empreinte_sha256       = row.get("empreinte_sha256"),
            hmac_integrite         = row.get("hmac_integrite"),
            description            = row.get("description"),
            date_upload            = row.get("date_upload"),
            niveau_confidentialite = row.get("niveau_confidentialite", NiveauConfidentialite.MOYEN),
        )
        obj.patient_nom    = row.get("patient_nom",    "") or ""
        obj.patient_prenom = row.get("patient_prenom", "") or ""
        return obj

    def get_detail_complet(self, id_resultat: str) -> dict:
        """Retourne toutes les infos jointes d’un résultat (patient, personnel, service)."""
        conn = self.db.connect()
        if not conn:
            return {}
        try:
            cursor = conn.cursor()
            # 1. Fiche de base
            cursor.execute("SELECT * FROM resultat_medical WHERE id_resultat = %s", (id_resultat,))
            rm = cursor.fetchone()
            if not rm:
                return {}
            data = dict(rm)
            type_source = data.get("type_source", "")

            if type_source == "consultation":
                cursor.execute("""
                    SELECT
                        p.code_patient, p.nom AS p_nom, p.prenom AS p_prenom,
                        p.telephone AS p_tel, p.naissance AS p_naissance,
                        p.genre AS p_genre, p.adresse AS p_adresse, p.profession AS p_profession,
                        per.nom AS per_nom, per.prenom AS per_prenom,
                        per.fonction AS per_fonction, per.contact AS per_contact,
                        c.diagnostique, c.frais_consultation, c.date_consultation, c.statut_facture,
                        a.nom_session
                    FROM consultation c
                    LEFT JOIN visite v      ON c.code_visite   = v.code_visite
                    LEFT JOIN patients p    ON v.code_patient  = p.code_patient
                    LEFT JOIN personnel per ON c.code_personnel = per.code
                    LEFT JOIN annee a       ON c.code_session   = a.code_session
                    WHERE c.code = %s
                """, (data.get("code_consultation"),))
                row = cursor.fetchone()
                if row:
                    data.update(dict(row))

            elif type_source == "examen":
                cursor.execute("""
                    SELECT
                        p.code_patient, p.nom AS p_nom, p.prenom AS p_prenom,
                        p.telephone AS p_tel, p.naissance AS p_naissance,
                        p.genre AS p_genre, p.adresse AS p_adresse, p.profession AS p_profession,
                        per.nom AS per_nom, per.prenom AS per_prenom,
                        per.fonction AS per_fonction, per.contact AS per_contact,
                        am.type_acte, am.decision_medicale, am.statut_acte,
                        e.libelle_examen, e.frais_examen, e.date_examen, e.conclusion_medicale,
                        a.nom_session
                    FROM acte_medical am
                    LEFT JOIN examen e      ON e.code_acte       = am.code_acte
                    LEFT JOIN consultation c ON am.code_consultation = c.code
                    LEFT JOIN visite v      ON c.code_visite    = v.code_visite
                    LEFT JOIN patients p    ON v.code_patient   = p.code_patient
                    LEFT JOIN personnel per ON e.code_personnel = per.code
                    LEFT JOIN annee a       ON e.code_session   = a.code_session
                    WHERE am.code_acte = %s
                """, (data.get("code_acte_medical"),))
                row = cursor.fetchone()
                if row:
                    data.update(dict(row))

            elif type_source == "chirurgie":
                cursor.execute("""
                    SELECT
                        p.code_patient, p.nom AS p_nom, p.prenom AS p_prenom,
                        p.telephone AS p_tel, p.naissance AS p_naissance,
                        p.genre AS p_genre, p.adresse AS p_adresse, p.profession AS p_profession,
                        per.nom AS per_nom, per.prenom AS per_prenom,
                        per.fonction AS per_fonction, per.contact AS per_contact,
                        am.type_acte, am.decision_medicale, am.statut_acte,
                        ch.libelle_chururgie, ch.frais_chururgie, ch.date_chururgie,
                        ch.compte_rendu_operatoire,
                        a.nom_session
                    FROM acte_medical am
                    LEFT JOIN chururgie ch  ON ch.code_acte      = am.code_acte
                    LEFT JOIN consultation c ON am.code_consultation = c.code
                    LEFT JOIN visite v      ON c.code_visite    = v.code_visite
                    LEFT JOIN patients p    ON v.code_patient   = p.code_patient
                    LEFT JOIN personnel per ON ch.code_personnel = per.code
                    LEFT JOIN annee a       ON ch.code_session   = a.code_session
                    WHERE am.code_acte = %s
                """, (data.get("code_acte_medical"),))
                row = cursor.fetchone()
                if row:
                    data.update(dict(row))

            return data
        except Exception as e:
            print(f"[ResultatMedicalDAO] Erreur get_detail_complet: {e}")
            return {}
        finally:
            self.db.close()
