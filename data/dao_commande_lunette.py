import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymysql
from core.connexion_db import DBConnection
from models.modeles_lunette import CommandeLunette
from datetime import datetime
DictCursor = pymysql.cursors.DictCursor
import calendar


class CommandeLunetteDAO:
    """
    Classe DAO pour la gestion des commandes de lunettes.
    Architecture MVC : acces aux donnees uniquement.
    """

    def __init__(self):
        self.db = DBConnection()

    # =========================================================================
    # METHODES CRUD
    # =========================================================================

    def ajouter(self, commande: CommandeLunette) -> bool:
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            commande.code = self._generer_code(cursor)
            query = """
                INSERT INTO commandeslunettes (
                    code, numero_cadre, numero_verre,
                    date_commande, date_livraison, prix,
                    statut, statut_facture,
                    code_session, code_personnel, code_acte
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                commande.code,
                commande.numero_cadre,
                commande.numero_verre,
                commande.date_commande,
                commande.date_livraison,
                commande.prix,
                commande.statut,
                commande.statut_facture,
                commande.code_session,
                commande.code_personnel,
                commande.code_acte
            ))

            # Mise à jour du statut_patient dans visite
            nouveau_statut, code_visite = self._determiner_statut_et_visite(cursor, commande.code_acte)
            if code_visite:
                cursor.execute(
                    "UPDATE visite SET statut_patient=%s WHERE code_visite=%s",
                    (nouveau_statut, code_visite)
                )

            conn.commit()
            return True
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur ajouter: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    def modifier(self, commande: CommandeLunette) -> bool:
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            query = """
                UPDATE commandeslunettes SET
                    numero_cadre=%s, numero_verre=%s,
                    date_commande=%s, date_livraison=%s, prix=%s,
                    statut=%s, statut_facture=%s,
                    code_session=%s, code_personnel=%s, code_acte=%s
                WHERE code=%s
            """
            cursor.execute(query, (
                commande.numero_cadre,
                commande.numero_verre,
                commande.date_commande,
                commande.date_livraison,
                commande.prix,
                commande.statut,
                commande.statut_facture,
                commande.code_session,
                commande.code_personnel,
                commande.code_acte,
                commande.code
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur modifier: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    def supprimer(self, code: str) -> bool:
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM commandeslunettes WHERE code=%s", (code,))
            conn.commit()
            return True
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur supprimer: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    # =========================================================================
    # METHODES DE RECUPERATION
    # =========================================================================

    def obtenir_par_code(self, code: str):
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor(DictCursor)
            query = """
                SELECT cl.*, p.nom AS patient_nom, p.prenom AS patient_prenom
                FROM commandeslunettes cl
                LEFT JOIN acte_medical am ON cl.code_acte = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite = v.code_visite
                LEFT JOIN patients p      ON v.code_patient = p.code_patient
                WHERE cl.code=%s
            """
            cursor.execute(query, (code,))
            row = cursor.fetchone()
            return self._row_to_object(row) if row else None
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur obtenir_par_code: {e}")
            return None
        finally:
            self.db.close()

    def obtenir_par_acte(self, code_acte: str):
        """Retourne la commande de lunette liée à un acte médical."""
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute(
                "SELECT * FROM commandeslunettes WHERE code_acte=%s", (code_acte,))
            row = cursor.fetchone()
            return self._row_to_object(row) if row else None
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur obtenir_par_acte: {e}")
            return None
        finally:
            self.db.close()

    def lister_par_session(self, code_session: str) -> list:
        conn = self.db.connect()
        if not conn: return []
        try:
            cursor = conn.cursor(DictCursor)
            query = """
                SELECT cl.*, p.nom AS patient_nom, p.prenom AS patient_prenom
                FROM commandeslunettes cl
                LEFT JOIN acte_medical am ON cl.code_acte = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite = v.code_visite
                LEFT JOIN patients p      ON v.code_patient = p.code_patient
                WHERE cl.code_session=%s
                ORDER BY cl.date_commande DESC
            """
            cursor.execute(query, (code_session,))
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur lister_par_session: {e}")
            return []
        finally:
            self.db.close()

    def lister_par_session_complet(self, code_session: str) -> list:
        """Retourne toutes les commandes d'une session avec informations complètes."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT
                    cl.code                 AS commande_code,
                    cl.numero_cadre,
                    cl.numero_verre,
                    cl.date_commande,
                    cl.date_livraison,
                    cl.prix,
                    cl.statut,
                    cl.statut_facture,
                    cl.code_acte,
                    cl.code_session,

                    p.code_patient,
                    p.nom                   AS patient_nom,
                    p.prenom                AS patient_prenom,
                    p.telephone             AS patient_telephone,
                    p.adresse               AS patient_adresse,
                    p.naissance             AS patient_date_naissance,

                    per.code                AS personnel_code,
                    per.nom                 AS personnel_nom,
                    per.prenom              AS personnel_prenom,
                    per.fonction            AS personnel_fonction
                FROM commandeslunettes cl
                LEFT JOIN acte_medical am ON cl.code_acte    = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite   = v.code_visite
                LEFT JOIN patients p      ON v.code_patient  = p.code_patient
                LEFT JOIN personnel per   ON cl.code_personnel = per.code
                WHERE cl.code_session = %s
                ORDER BY cl.date_commande DESC
            """
            cursor.execute(query, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur lister_par_session_complet: {e}")
            return []
        finally:
            self.db.close()

    def rechercher_par_critere(self, critere: str, code_session: str) -> list:
        conn = self.db.connect()
        if not conn: return []
        try:
            cursor = conn.cursor(DictCursor)
            critere_like = f"%{critere}%"
            query = """
                SELECT cl.*, p.nom AS patient_nom, p.prenom AS patient_prenom
                FROM commandeslunettes cl
                LEFT JOIN acte_medical am ON cl.code_acte = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite = v.code_visite
                LEFT JOIN patients p      ON v.code_patient = p.code_patient
                WHERE cl.code_session=%s
                AND (
                    cl.code LIKE %s OR
                    cl.numero_verre LIKE %s OR
                    p.nom LIKE %s OR
                    p.prenom LIKE %s
                )
                ORDER BY cl.date_commande DESC
            """
            cursor.execute(query, (code_session, critere_like, critere_like, critere_like, critere_like))
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur rechercher_par_critere: {e}")
            return []
        finally:
            self.db.close()

    def commande_complete(self, code_commande: str):
        """Retourne une commande avec infos patient et personnel (JOIN)."""
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor(DictCursor)
            query = """
                SELECT
                    cl.*,
                    p.nom           AS patient_nom,
                    p.prenom        AS patient_prenom,
                    p.telephone     AS patient_telephone,
                    p.adresse       AS patient_adresse,
                    p.naissance     AS patient_date_naissance,
                    per.nom         AS personnel_nom,
                    per.prenom      AS personnel_prenom,
                    per.fonction    AS personnel_fonction
                FROM commandeslunettes cl
                LEFT JOIN acte_medical am ON cl.code_acte    = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite   = v.code_visite
                LEFT JOIN patients p      ON v.code_patient  = p.code_patient
                LEFT JOIN personnel per   ON cl.code_personnel = per.code
                WHERE cl.code = %s
            """
            cursor.execute(query, (code_commande,))
            return cursor.fetchone()
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur commande_complete: {e}")
            return None
        finally:
            self.db.close()

    # =========================================================================
    # METHODES STATISTIQUES CARDS (COUNT SQL)
    # =========================================================================

    def nombre_commandes_en_attente_livraison(self, code_session: str) -> int:
        """Card 'Attente de Livraisons' : COUNT des commandes avec statut 'attente'."""
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM commandeslunettes
                WHERE code_session = %s
                  AND statut = 'attente'
            """, (code_session,))
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur nombre_commandes_en_attente_livraison: {e}")
            return 0
        finally:
            self.db.close()

    def nombre_total_par_session(self, code_session: str) -> int:
        """Card 'Commandes Lunettes Total Session' : COUNT de toutes les commandes de la session."""
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM commandeslunettes
                WHERE code_session = %s
            """, (code_session,))
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur nombre_total_par_session: {e}")
            return 0
        finally:
            self.db.close()

    def nombre_commandes_en_attente(self, code_session: str) -> int:
        """
        Card 'Patients en Attente' :
        Compte les visites distinctes avec un acte de type 'lunette'
        et statut_patient IN ('Attente lunette', 'En lunette').
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
                                           AND am.type_acte   = 'lunette'
                WHERE v.code_session   = %s
                  AND v.statut_patient IN ('Attente lunette', 'En lunette')
            """, (code_session,))
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur nombre_commandes_en_attente: {e}")
            return 0
        finally:
            self.db.close()

    # =========================================================================
    # METHODES STATISTIQUES & GRAPHES
    # =========================================================================

    def revenu_total(self, code_session: str, date_debut=None, date_fin=None) -> float:
        """Total des prix des commandes pour une session, avec filtre date optionnel."""
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            if date_debut and date_fin:
                cursor.execute("""
                    SELECT SUM(prix) AS total FROM commandeslunettes
                    WHERE code_session=%s AND DATE(date_commande) BETWEEN %s AND %s
                """, (code_session, date_debut, date_fin))
            else:
                cursor.execute("""
                    SELECT SUM(prix) AS total FROM commandeslunettes
                    WHERE code_session=%s
                """, (code_session,))
            result = cursor.fetchone()
            return float(result['total']) if result and result['total'] else 0.0
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur revenu_total: {e}")
            return 0.0
        finally:
            self.db.close()

    def top_numeros_verre(self, code_session: str, limite: int = 10) -> list:
        """Retourne les numéros de verre prescrits les plus fréquents pour une session."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT numero_verre, COUNT(*) AS nombre
                FROM commandeslunettes
                WHERE code_session=%s AND numero_verre IS NOT NULL
                GROUP BY numero_verre
                ORDER BY nombre DESC LIMIT %s
            """, (code_session, limite))
            return cursor.fetchall()
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur top_numeros_verre: {e}")
            return []
        finally:
            self.db.close()

    def commandes_par_personnel(self, code_session: str) -> list:
        """Nombre de commandes groupées par personnel."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT per.nom, per.prenom, COUNT(*) AS nombre,
                       SUM(cl.prix) AS total_prix
                FROM commandeslunettes cl
                INNER JOIN personnel per ON cl.code_personnel = per.code
                WHERE cl.code_session=%s
                GROUP BY per.code, per.nom, per.prenom
                ORDER BY nombre DESC
            """, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur commandes_par_personnel: {e}")
            return []
        finally:
            self.db.close()

    # =========================================================================
    # METHODES PATIENTS
    # =========================================================================

    def patients_en_attente_lunette(self, code_session: str) -> list:
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT
                    v.code_visite,
                    v.date_visite,
                    v.statut_patient,
                    MIN(am.code_acte)        AS code_acte,
                    MIN(c.code)              AS code_consultation,
                    MIN(c.date_consultation) AS date_consultation,
                    p.code_patient,
                    p.nom,
                    p.prenom,
                    p.telephone
                FROM visite v
                INNER JOIN patients     p   ON v.code_patient  = p.code_patient
                INNER JOIN acte_visite  av  ON av.code_visite  = v.code_visite
                INNER JOIN acte_medical am  ON am.code_acte    = av.code_acte
                                           AND am.type_acte    = 'lunette'
                LEFT  JOIN consultation c   ON c.code          = am.code_consultation
                WHERE v.code_session   = %s
                  AND v.statut_patient IN ('Attente lunette', 'En lunette')
                GROUP BY v.code_visite, v.date_visite, v.statut_patient, v.urgent,
                         p.code_patient, p.nom, p.prenom, p.telephone
                ORDER BY v.urgent DESC, v.date_visite ASC
            """, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur patients_en_attente_lunette: {e}")
            return []
        finally:
            self.db.close()

    def historique_patient(self, code_patient: str) -> list:
        """Retourne l'historique complet des commandes de lunettes d'un patient."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            query = """
                SELECT cl.*, per.nom AS personnel_nom, per.prenom AS personnel_prenom
                FROM commandeslunettes cl
                LEFT JOIN acte_medical am ON cl.code_acte    = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite   = v.code_visite
                LEFT JOIN personnel per   ON cl.code_personnel = per.code
                WHERE v.code_patient = %s
                ORDER BY cl.date_commande DESC
            """
            cursor.execute(query, (code_patient,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur historique_patient: {e}")
            return []
        finally:
            self.db.close()

    def lister_personnel(self) -> list:
        """Retourne la liste de tout le personnel médical."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT code, nom, prenom, fonction
                FROM personnel
                ORDER BY nom ASC
            """)
            return cursor.fetchall()
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur lister_personnel: {e}")
            return []
        finally:
            self.db.close()

    # =========================================================================
    # EXPORT / IMPORT
    # =========================================================================

    def lister_pour_export(self) -> list:
        """Retourne toutes les commandes de lunettes avec code_consultation pour export CSV/Excel."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT cl.code        AS code_lunette,
                       am.code_consultation,
                       cl.code_personnel,
                       cl.numero_cadre,
                       cl.numero_verre,
                       cl.prix,
                       cl.statut_facture,
                       cl.date_commande,
                       cl.date_livraison
                FROM commandeslunettes cl
                JOIN acte_medical am ON cl.code_acte = am.code_acte
                ORDER BY cl.code DESC
            """)
            return cursor.fetchall() or []
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur lister_pour_export: {e}")
            return []
        finally:
            self.db.close()

    def _inserer_import(self, cursor, code_acte: str, code_session: str, data: dict) -> bool:
        """
        INSERT commande lunette en mode import — reçoit curseur externe.
        Ne met PAS à jour visite.statut_patient (géré par le service).
        """
        code = self._generer_code(cursor)
        cursor.execute("""
            INSERT INTO commandeslunettes (
                code, numero_cadre, numero_verre, date_commande, date_livraison,
                prix, statut, statut_facture, code_session, code_personnel, code_acte
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            code,
            data.get('numero_cadre'),
            data.get('numero_verre'),
            data.get('date_commande'),
            data.get('date_livraison') or None,
            data.get('prix', 0.0),
            data.get('statut') or 'livree',
            data.get('statut_facture') or 'attente payement',
            code_session,
            data.get('code_personnel') or None,
            code_acte,
        ))
        return cursor.rowcount > 0

    # =========================================================================
    # METHODES PRIVEES
    # =========================================================================

    def _generer_code(self, cursor) -> str:
        """Génère un code unique (ex: CLT001)."""
        try:
            cursor.execute("SELECT code FROM commandeslunettes ORDER BY code DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                last_code = row['code'] if isinstance(row, dict) else row[0]
                last_num  = int(last_code[3:])
                return f"CLT{last_num + 1:03d}"
            else:
                return "CLT001"
        except Exception as e:
            print(f"Erreur generation code commande lunette: {e}")
            return "CLT" + datetime.now().strftime("%H%M%S")

    def _row_to_object(self, row) -> CommandeLunette:
        obj = CommandeLunette(
            code              = row['code'],
            numero_cadre      = row['numero_cadre'],
            numero_verre      = row['numero_verre'],
            date_commande     = row['date_commande'],
            date_livraison    = row['date_livraison'],
            prix              = row['prix'],
            statut            = row['statut'],
            statut_facture    = row['statut_facture'],
            code_session      = row['code_session'],
            code_personnel    = row['code_personnel'],
            code_acte         = row.get('code_acte')
        )
        obj.patient_nom    = row.get('patient_nom', "")
        obj.patient_prenom = row.get('patient_prenom', "")
        return obj

    def _determiner_statut_et_visite(self, cursor, code_acte: str) -> tuple:
        """Détermine le prochain statut après une commande de lunette et retourne (statut, code_visite).
        
        IMPORTANT : On met à jour UNIQUEMENT la visite d'exécution (role='execution'),
        PAS la visite d'origine (role='origine') pour éviter la duplication dans la file d'attente.
        """
        try:
            # Récupérer le code_visite d'exécution depuis acte_visite avec role='execution'
            conn = cursor.connection
            dcursor = conn.cursor(DictCursor)
            dcursor.execute(
                "SELECT code_visite FROM acte_visite WHERE code_acte=%s AND role_visite='execution' LIMIT 1",
                (code_acte,)
            )
            row_exec = dcursor.fetchone()
            
            if not row_exec:
                # Si pas de visite d'exécution, récupérer depuis la consultation (cas acte "maintenant")
                dcursor.execute("""
                    SELECT c.chiurgie, c.prescription_produit, c.code_visite
                    FROM acte_medical am
                    INNER JOIN consultation c ON am.code_consultation = c.code
                    WHERE am.code_acte = %s
                """, (code_acte,))
                row = dcursor.fetchone()
                if not row:
                    return "Attente payement", None
                code_visite = row['code_visite']
                if row['chiurgie'] == "Oui":
                    return "Attente chirurgie", code_visite
                elif row['prescription_produit'] == "Oui":
                    return "Attente pharmacie", code_visite
                else:
                    return "Attente payement", code_visite
            
            # Visite d'exécution trouvée
            code_visite = row_exec['code_visite']
            # Vérifier si chirurgie ou prescription
            dcursor.execute("""
                SELECT c.chiurgie, c.prescription_produit
                FROM acte_medical am
                INNER JOIN consultation c ON am.code_consultation = c.code
                WHERE am.code_acte = %s
            """, (code_acte,))
            row = dcursor.fetchone()
            if not row:
                return "Attente payement", code_visite
            
            if row['chiurgie'] == "Oui":
                return "Attente chirurgie", code_visite
            elif row['prescription_produit'] == "Oui":
                return "Attente pharmacie", code_visite
            else:
                return "Attente payement", code_visite
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur _determiner_statut_et_visite: {e}")
            return "Attente payement", None
        
    def commande_en_attente_complete(self, code_commande: str):
        """
        Retourne les informations complètes d'une seule commande en attente de livraison :
        données de la lunette + patient + personnel.
        """
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor(DictCursor)
            query = """
                SELECT
                    cl.code                  AS commande_code,
                    cl.numero_cadre,
                    cl.numero_verre,
                    cl.date_commande,
                    cl.date_livraison,
                    cl.prix,
                    cl.statut,
                    cl.statut_facture,
                    cl.code_acte,
                    cl.code_session,

                    p.code_patient,
                    p.nom                    AS patient_nom,
                    p.prenom                 AS patient_prenom,
                    p.telephone              AS patient_telephone,
                    p.adresse                AS patient_adresse,
                    p.naissance              AS patient_date_naissance,

                    per.code                 AS personnel_code,
                    per.nom                  AS personnel_nom,
                    per.prenom               AS personnel_prenom,
                    per.fonction             AS personnel_fonction
                FROM commandeslunettes cl
                LEFT JOIN acte_medical am ON cl.code_acte    = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite   = v.code_visite
                LEFT JOIN patients p      ON v.code_patient  = p.code_patient
                LEFT JOIN personnel per   ON cl.code_personnel = per.code
                WHERE cl.code = %s
                  AND cl.statut = 'attente'
            """
            cursor.execute(query, (code_commande,))
            return cursor.fetchone()
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur commande_en_attente_complete: {e}")
            return None
        finally:
            self.db.close()

    def lister_commandes_en_attente_livraison_completes(self, code_session: str) -> list:
        """
        Retourne la liste complète de toutes les commandes en attente de livraison
        pour une session donnée :
        données de la lunette + patient + personnel, triées par date de commande.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT
                    cl.code                  AS commande_code,
                    cl.numero_cadre,
                    cl.numero_verre,
                    cl.date_commande,
                    cl.date_livraison,
                    cl.prix,
                    cl.statut,
                    cl.statut_facture,
                    cl.code_acte,
                    cl.code_session,

                    p.code_patient,
                    p.nom                    AS patient_nom,
                    p.prenom                 AS patient_prenom,
                    p.telephone              AS patient_telephone,
                    p.adresse                AS patient_adresse,
                    p.naissance              AS patient_date_naissance,

                    per.code                 AS personnel_code,
                    per.nom                  AS personnel_nom,
                    per.prenom               AS personnel_prenom,
                    per.fonction             AS personnel_fonction
                FROM commandeslunettes cl
                LEFT JOIN acte_medical am ON cl.code_acte    = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite   = v.code_visite
                LEFT JOIN patients p      ON v.code_patient  = p.code_patient
                LEFT JOIN personnel per   ON cl.code_personnel = per.code
                WHERE cl.code_session = %s
                  AND cl.statut = 'attente'
                ORDER BY cl.date_commande ASC
            """
            cursor.execute(query, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur lister_commandes_en_attente_livraison_completes: {e}")
            return []
        finally:
            self.db.close()
            
    def marquer_comme_livree(self, code: str) -> bool:
        """
        Met à jour le statut d'une commande à 'livree' et enregistre
        automatiquement la date de livraison réelle à la date du jour.
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE commandeslunettes
                SET statut = 'livree',
                    date_livraison = CURDATE()
                WHERE code = %s
                  AND statut = 'attente'
            """, (code,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur marquer_comme_livree: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    def commandes_en_retard(self, code_session: str) -> list:
        """
        Retourne la liste complète des commandes dont la date de livraison prévue
        est dépassée et dont le statut est encore 'attente'.
        Jointures complètes : lunette + patient + personnel.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT
                    cl.code                 AS commande_code,
                    cl.numero_cadre,
                    cl.numero_verre,
                    cl.date_commande,
                    cl.date_livraison,
                    cl.prix,
                    cl.statut,
                    cl.statut_facture,
                    cl.code_acte,
                    cl.code_session,
                    DATEDIFF(CURDATE(), cl.date_livraison) AS jours_retard,

                    p.code_patient,
                    p.nom                   AS patient_nom,
                    p.prenom                AS patient_prenom,
                    p.telephone             AS patient_telephone,
                    p.adresse               AS patient_adresse,
                    p.naissance             AS patient_date_naissance,

                    per.code                AS personnel_code,
                    per.nom                 AS personnel_nom,
                    per.prenom              AS personnel_prenom,
                    per.fonction            AS personnel_fonction
                FROM commandeslunettes cl
                LEFT JOIN acte_medical am ON cl.code_acte    = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite   = v.code_visite
                LEFT JOIN patients p      ON v.code_patient  = p.code_patient
                LEFT JOIN personnel per   ON cl.code_personnel = per.code
                WHERE cl.code_session = %s
                  AND cl.statut       = 'attente'
                  AND cl.date_livraison IS NOT NULL
                  AND cl.date_livraison < CURDATE()
                ORDER BY cl.date_livraison ASC
            """
            cursor.execute(query, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur commandes_en_retard: {e}")
            return []
        finally:
            self.db.close()

    def commandes_a_livrer_dans_deux_jours(self, code_session: str) -> list:
        """
        Retourne la liste complète des commandes dont la date de livraison prévue
        tombe exactement dans les deux prochains jours (J+1 ou J+2),
        avec statut encore 'attente' — permet d'anticiper et d'alerter le personnel.
        Jointures complètes : lunette + patient + personnel.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT
                    cl.code                 AS commande_code,
                    cl.numero_cadre,
                    cl.numero_verre,
                    cl.date_commande,
                    cl.date_livraison,
                    cl.prix,
                    cl.statut,
                    cl.statut_facture,
                    cl.code_acte,
                    cl.code_session,
                    DATEDIFF(cl.date_livraison, CURDATE()) AS jours_restants,

                    p.code_patient,
                    p.nom                   AS patient_nom,
                    p.prenom                AS patient_prenom,
                    p.telephone             AS patient_telephone,
                    p.adresse               AS patient_adresse,
                    p.naissance             AS patient_date_naissance,

                    per.code                AS personnel_code,
                    per.nom                 AS personnel_nom,
                    per.prenom              AS personnel_prenom,
                    per.fonction            AS personnel_fonction
                FROM commandeslunettes cl
                LEFT JOIN acte_medical am ON cl.code_acte    = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite   = v.code_visite
                LEFT JOIN patients p      ON v.code_patient  = p.code_patient
                LEFT JOIN personnel per   ON cl.code_personnel = per.code
                WHERE cl.code_session = %s
                  AND cl.statut       = 'attente'
                  AND cl.date_livraison IS NOT NULL
                  AND cl.date_livraison BETWEEN CURDATE() + INTERVAL 1 DAY
                                            AND CURDATE() + INTERVAL 2 DAY
                ORDER BY cl.date_livraison ASC
            """
            cursor.execute(query, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur commandes_a_livrer_dans_deux_jours: {e}")
            return []
        finally:
            self.db.close()
            
    def revenu_recouvre_vs_en_attente(self, code_session: str) -> dict:
        """
        Retourne en une seule requête le montant total déjà encaissé
        et le montant total encore en attente de paiement pour une session.
        Résultat : {'recouvre': float, 'en_attente': float, 'total': float}
        """
        conn = self.db.connect()
        if not conn:
            return {'recouvre': 0.0, 'en_attente': 0.0, 'total': 0.0}
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN statut_facture != 'Attente payement'
                             THEN prix ELSE 0 END)  AS recouvre,
                    SUM(CASE WHEN statut_facture  = 'Attente payement'
                             THEN prix ELSE 0 END)  AS en_attente,
                    SUM(prix)                        AS total
                FROM commandeslunettes
                WHERE code_session = %s
            """, (code_session,))
            row = cursor.fetchone()
            if not row:
                return {'recouvre': 0.0, 'en_attente': 0.0, 'total': 0.0}
            return {
                'recouvre':   float(row['recouvre']   or 0.0),
                'en_attente': float(row['en_attente'] or 0.0),
                'total':      float(row['total']      or 0.0)
            }
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur revenu_recouvre_vs_en_attente: {e}")
            return {'recouvre': 0.0, 'en_attente': 0.0, 'total': 0.0}
        finally:
            self.db.close()

    def commandes_par_statut_facture(self, code_session: str) -> list:
        """
        Retourne pour chaque statut de facturation :
        le nombre de commandes et le montant total correspondant.
        Résultat exploitable directement pour un graphique (secteurs ou barres).
        Exemple de ligne : {'statut_facture': 'Attente payement', 'nombre': 5, 'total_prix': 1500000.0}
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    statut_facture,
                    COUNT(*)   AS nombre,
                    SUM(prix)  AS total_prix
                FROM commandeslunettes
                WHERE code_session = %s
                GROUP BY statut_facture
                ORDER BY nombre DESC
            """, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur commandes_par_statut_facture: {e}")
            return []
        finally:
            self.db.close()
            
    def derniere_commande_patient(self, code_visite: str):
        """
        Retourne la dernière commande de lunettes passée pour un patient
        identifié par son code_visite, avec toutes les informations complètes.
        """
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor(DictCursor)
            query = """
                SELECT
                    cl.code                 AS commande_code,
                    cl.numero_cadre,
                    cl.numero_verre,
                    cl.date_commande,
                    cl.date_livraison,
                    cl.prix,
                    cl.statut,
                    cl.statut_facture,
                    cl.code_acte,
                    cl.code_session,

                    p.code_patient,
                    p.nom                   AS patient_nom,
                    p.prenom                AS patient_prenom,
                    p.telephone             AS patient_telephone,
                    p.adresse               AS patient_adresse,
                    p.naissance             AS patient_date_naissance,

                    per.code                AS personnel_code,
                    per.nom                 AS personnel_nom,
                    per.prenom              AS personnel_prenom,
                    per.fonction            AS personnel_fonction
                FROM commandeslunettes cl
                LEFT JOIN acte_medical am ON cl.code_acte    = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite   = v.code_visite
                LEFT JOIN patients p      ON v.code_patient  = p.code_patient
                LEFT JOIN personnel per   ON cl.code_personnel = per.code
                WHERE v.code_visite = %s
                ORDER BY cl.date_commande DESC
                LIMIT 1
            """
            cursor.execute(query, (code_visite,))
            return cursor.fetchone()
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur derniere_commande_patient: {e}")
            return None
        finally:
            self.db.close()

    def patients_avec_commandes_multiples(self, code_session: str) -> list:
        """
        Retourne la liste des patients ayant passé plus d'une commande de lunettes
        sur une même session, avec le nombre de commandes et le total payé.
        Permet de détecter les doublons, remplacements urgents ou suivis rapprochés.
        Résultat trié par nombre de commandes décroissant.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT
                    p.code_patient,
                    p.nom                   AS patient_nom,
                    p.prenom                AS patient_prenom,
                    p.telephone             AS patient_telephone,
                    COUNT(cl.code)          AS nombre_commandes,
                    SUM(cl.prix)            AS total_prix
                FROM commandeslunettes cl
                LEFT JOIN acte_medical am ON cl.code_acte   = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite  = v.code_visite
                LEFT JOIN patients p      ON v.code_patient = p.code_patient
                WHERE cl.code_session = %s
                GROUP BY p.code_patient, p.nom, p.prenom, p.telephone
                HAVING COUNT(cl.code) > 1
                ORDER BY nombre_commandes DESC
            """
            cursor.execute(query, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur patients_avec_commandes_multiples: {e}")
            return []
        finally:
            self.db.close()

    def delai_moyen_livraison(self, code_session: str) -> dict:
        """
        Calcule le délai moyen de livraison en jours sur les commandes
        effectivement livrées (statut = 'livree') d'une session.
        Retourne aussi le délai minimum et maximum observés.
        Résultat : {'moyen': float, 'minimum': int, 'maximum': int, 'nombre_livrees': int}
        Indicateur qualité de service exploitable directement devant le jury.
        """
        conn = self.db.connect()
        if not conn:
            return {'moyen': 0.0, 'minimum': 0, 'maximum': 0, 'nombre_livrees': 0}
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    ROUND(AVG(DATEDIFF(date_livraison, date_commande)), 1) AS moyen,
                    MIN(DATEDIFF(date_livraison, date_commande))            AS minimum,
                    MAX(DATEDIFF(date_livraison, date_commande))            AS maximum,
                    COUNT(*)                                                AS nombre_livrees
                FROM commandeslunettes
                WHERE code_session    = %s
                  AND statut          = 'livree'
                  AND date_livraison  IS NOT NULL
                  AND date_commande   IS NOT NULL
            """, (code_session,))
            row = cursor.fetchone()
            if not row or not row['nombre_livrees']:
                return {'moyen': 0.0, 'minimum': 0, 'maximum': 0, 'nombre_livrees': 0}
            return {
                'moyen':          float(row['moyen']        or 0.0),
                'minimum':        int(row['minimum']        or 0),
                'maximum':        int(row['maximum']        or 0),
                'nombre_livrees': int(row['nombre_livrees'] or 0)
            }
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur delai_moyen_livraison: {e}")
            return {'moyen': 0.0, 'minimum': 0, 'maximum': 0, 'nombre_livrees': 0}
        finally:
            self.db.close()
            
    # methodes pour afficher le montant total des commandes d'aujourd'hui
    def montant_total_commandes_aujourdhui(self, code_session: str) -> float:
        """
        Calcule le montant total des commandes de lunettes passées aujourd'hui
        pour une session donnée. Permet d'afficher un indicateur de performance
        en temps réel sur le dashboard.
        """
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(prix) AS total
                FROM commandeslunettes
                WHERE code_session = %s
                  AND DATE(date_commande) = CURDATE()
            """, (code_session,))
            result = cursor.fetchone()
            return float(result['total']) if result and result['total'] else 0.0
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur montant_total_commandes_aujourdhui: {e}")
            return 0.0
        finally:
            self.db.close()
            
    # montant total des commandes par session
    def montant_total_commandes_par_session(self, code_session: str) -> float:
        """
        Calcule le montant total de toutes les commandes de lunettes passées
        pour une session donnée, sans filtre de date. Permet d'afficher un
        indicateur global de performance financière sur le dashboard.
        """
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(prix) AS total
                FROM commandeslunettes
                WHERE code_session = %s
            """, (code_session,))
            result = cursor.fetchone()
            return float(result['total']) if result and result['total'] else 0.0
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur montant_total_commandes_par_session: {e}")
            return 0.0
        finally:
            self.db.close()
            
    # les methodes statistiques et graphiques
    @staticmethod
    def _stats_mensuels_int() -> dict:
        return {
            'Jan': 0, 'Fév': 0, 'Mar': 0, 'Avr': 0, 'Mai': 0, 'Juin': 0,
            'Juil': 0, 'Août': 0, 'Sep': 0, 'Oct': 0, 'Nov': 0, 'Déc': 0
        }

    @staticmethod
    def _stats_mensuels_float() -> dict:
        return {
            'Jan': 0.0, 'Fév': 0.0, 'Mar': 0.0, 'Avr': 0.0, 'Mai': 0.0, 'Juin': 0.0,
            'Juil': 0.0, 'Août': 0.0, 'Sep': 0.0, 'Oct': 0.0, 'Nov': 0.0, 'Déc': 0.0
        }

    @staticmethod
    def _mois_mapping() -> dict:
        return {
            1: 'Jan', 2: 'Fév', 3: 'Mar', 4: 'Avr', 5: 'Mai', 6: 'Juin',
            7: 'Juil', 8: 'Août', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Déc'
        }

    @staticmethod
    def _jours_a_considerer_pour_moyenne(annee: int, mois: int, today) -> int:
        """
        Règle métier:
        - mois courant: du 1er jusqu'à aujourd'hui (inclus)
        - mois passés / futurs: nombre total de jours du mois
        """
        if annee == today.year and mois == today.month:
            return today.day
        return calendar.monthrange(annee, mois)[1]
    
    # nombre de commandes lunettes par jour pour une session donnée, sur les 30 derniers jours
    def nombre_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        """
        Retourne le nombre de consultations par jour pour un mois donné.
        Les jours sans activité sont inclus avec 0.
        - Si annee/mois non fournis: mois courant.
        - Pour le mois courant: jours 1..aujourd'hui.
        - Pour un autre mois: jours 1..fin du mois.
        """
        today = datetime.now().date()
        annee = annee or today.year
        mois = mois or today.month

        nb_jours_mois = calendar.monthrange(annee, mois)[1]
        dernier_jour = today.day if (annee == today.year and mois == today.month) else nb_jours_mois
        stats = {f"{j:02d}": 0 for j in range(1, dernier_jour + 1)}

        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DAY(date_commande) AS num_jour, COUNT(*) AS total
                FROM commandeslunettes
                WHERE code_session=%s
                  AND YEAR(date_commande)=%s
                  AND MONTH(date_commande)=%s
                GROUP BY DAY(date_commande)
            """, (code_session, annee, mois))
            for row in cursor.fetchall():
                j = int(row['num_jour'])
                if 1 <= j <= dernier_jour:
                    stats[f"{j:02d}"] = int(row['total']) if row['total'] else 0
            return stats
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur nombre_par_jour: {e}")
            return stats
        finally:
            self.db.close()
            
    # montant total des commandes de lunettes par jour dans le mois courant, pour une session donnée
    def montant_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        """
        Retourne le montant des consultations par jour pour un mois donné.
        Les jours sans activité sont inclus avec 0.
        - Si annee/mois non fournis: mois courant.
        - Pour le mois courant: jours 1..aujourd'hui.
        - Pour un autre mois: jours 1..fin du mois.
        """
        today = datetime.now().date()
        annee = annee or today.year
        mois = mois or today.month

        nb_jours_mois = calendar.monthrange(annee, mois)[1]
        dernier_jour = today.day if (annee == today.year and mois == today.month) else nb_jours_mois
        stats = {f"{j:02d}": 0.0 for j in range(1, dernier_jour + 1)}

        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DAY(date_commande) AS num_jour, SUM(prix) AS total
                FROM commandeslunettes
                WHERE code_session=%s
                  AND YEAR(date_commande)=%s
                  AND MONTH(date_commande)=%s
                GROUP BY DAY(date_commande)
            """, (code_session, annee, mois))
            for row in cursor.fetchall():
                j = int(row['num_jour'])
                if 1 <= j <= dernier_jour:
                    stats[f"{j:02d}"] = float(row['total']) if row['total'] else 0.0
            return stats
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur montant_par_jour: {e}")
            return stats
        finally:
            self.db.close()
            
    # nombre de commandes de lunettes par mois pour une session donnée
    def nombre_par_mois(self, code_session: str) -> dict:

        """
        Graphe 'Nombre de commandes de lunettes par mois' :
        Retourne le nombre de commandes de lunettes pour chaque mois de l'année.
        """
        stats = self._stats_mensuels_int()
        mois_mapping = self._mois_mapping()
        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MONTH(date_commande) AS num_mois, COUNT(*) AS total
                FROM commandeslunettes WHERE code_session=%s
                GROUP BY MONTH(date_commande)
            """, (code_session,))
            for row in cursor.fetchall():
                m = row['num_mois']
                if m in mois_mapping:
                    stats[mois_mapping[m]] = row['total']
            return stats
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur nombre_par_mois: {e}")
            return stats
        finally:
            self.db.close()
            
    # montant total des commandes de lunettes par mois pour une session donnée
    def montant_par_mois(self, code_session: str) -> dict:
        """
        Graphe 'Montant des commandes de lunettes par mois' :
        Retourne le montant total des commandes de lunettes pour chaque mois.
        """
        stats = self._stats_mensuels_float()
        mois_mapping = self._mois_mapping()
        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MONTH(date_commande) AS num_mois, 
                       SUM(prix) AS total
                FROM commandeslunettes 
                WHERE code_session=%s
                GROUP BY MONTH(date_commande)
            """, (code_session,))
            for row in cursor.fetchall():
                m = row['num_mois']
                if m in mois_mapping:
                    stats[mois_mapping[m]] = float(row['total']) if row['total'] else 0.0
            return stats
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur montant_par_mois: {e}")
            return stats
        finally:
            self.db.close()
            
    # revenue moyenne par mois pour une session donnée
    def revenu_moyen_par_mois(self, code_session: str) -> dict:
        """
        Moyenne journalière des montants de commandes de lunettes par mois.
        Important: on divise par le nombre de jours du mois en incluant
        les jours sans activité.
        - Mois courant: division par le nombre de jours écoulés (1..aujourd'hui)
        - Mois passés: division par le nombre total de jours du mois
        """
        return self.moyenne_montant_journalier_mois(code_session)
    
    # montant moyen journalier des commandes de lunettes pour chaque mois d'une session donnée
    def moyenne_montant_journalier_mois(self, code_session: str) -> dict:
        """
        Retourne la moyenne journalière des montants par mois (jours sans activité inclus).
        """
        stats = self._stats_mensuels_float()
        mois_mapping = self._mois_mapping()
        today = datetime.now().date()

        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT YEAR(date_commande) AS annee,
                       MONTH(date_commande) AS num_mois,
                       SUM(prix) AS total_mois
                FROM commandeslunettes
                WHERE code_session=%s
                GROUP BY YEAR(date_commande), MONTH(date_commande)
            """, (code_session,))

            for row in cursor.fetchall():
                num_mois = int(row['num_mois'])
                annee = int(row['annee'])
                if num_mois not in mois_mapping:
                    continue

                jours = self._jours_a_considerer_pour_moyenne(annee, num_mois, today)
                total_mois = float(row['total_mois']) if row['total_mois'] else 0.0
                stats[mois_mapping[num_mois]] = (total_mois / jours) if jours > 0 else 0.0

            return stats
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur moyenne_montant_journalier_mois: {e}")
            return stats
        finally:
            self.db.close()
            
    # moyenne des commandes lunettes journalières pour un mois donné d'une session donnée
    def moyenne_commandes_journalieres_mois(self, code_session: str) -> dict:
        """
        Retourne la moyenne journalière du nombre de commandes de lunettes par mois
        (jours sans activité inclus).
        """
        stats = self._stats_mensuels_float()
        mois_mapping = self._mois_mapping()
        today = datetime.now().date()

        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT YEAR(date_commande) AS annee,
                       MONTH(date_commande) AS num_mois,
                       COUNT(*) AS total_mois
                FROM commandeslunettes
                WHERE code_session=%s
                GROUP BY YEAR(date_commande), MONTH(date_commande)
            """, (code_session,))

            for row in cursor.fetchall():
                num_mois = int(row['num_mois'])
                annee = int(row['annee'])
                if num_mois not in mois_mapping:
                    continue

                jours = self._jours_a_considerer_pour_moyenne(annee, num_mois, today)
                total_mois = int(row['total_mois']) if row['total_mois'] else 0
                stats[mois_mapping[num_mois]] = (float(total_mois) / jours) if jours > 0 else 0.0

            return stats
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur moyenne_commandes_journalieres_mois: {e}")
            return stats
        finally:
            self.db.close()
            
    # moyenne des commandes lunettes par mois pour une session donnée
    def moyenne_commandes_par_mois(self, code_session: str) -> dict:
        """
        Alias conservé pour compatibilité.
        Retourne la moyenne journalière du nombre de commandes de lunettes par mois.
        """
        return self.moyenne_commandes_journalieres_mois(code_session)
    
    # methodes de recherche avancee et filtrage
    def rechercher_entre_dates(self, code_session: str, date_debut, date_fin) -> list:
        """
        Recherche les commandes de lunettes entre deux dates (incluses).
        date_debut et date_fin : objet datetime.date ou str au format YYYY-MM-DD
        Retourne une liste d'objets CommandeLunette.
        """
        if not code_session:
            return []
        
        # Convertir en string si nécessaire
        if hasattr(date_debut, 'strftime'):
            date_debut = date_debut.strftime('%Y-%m-%d')
        if hasattr(date_fin, 'strftime'):
            date_fin = date_fin.strftime('%Y-%m-%d')

        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            query = """
                SELECT c.*, v.code_patient, p.nom AS patient_nom, p.prenom AS patient_prenom
                FROM commandeslunettes c
                LEFT JOIN acte_medical am ON c.code_acte    = am.code_acte
                LEFT JOIN consultation con ON am.code_consultation = con.code
                LEFT JOIN visite v         ON con.code_visite = v.code_visite
                INNER JOIN patients p      ON v.code_patient = p.code_patient
                WHERE c.code_session=%s AND DATE(c.date_commande) BETWEEN %s AND %s
                ORDER BY c.date_commande DESC
            """
            cursor.execute(query, (code_session, date_debut, date_fin))
            result = cursor.fetchall()
            return [self._row_to_object(row) for row in result]
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur rechercher_entre_dates: {e}")
            return []
        finally:
            self.db.close()
            
    # methodes de commande de lunettes par patient par mois
    def commandes_par_patient_par_mois(self, code_session: str, code_patient: str = None) -> dict:
        """
        Retourne le nombre de commandes de lunettes par mois pour chaque patient (ou un patient spécifique).
        Format : { "Jan": { "P001": 2, "P002": 1 }, "Fév": { ... }, ... }
        ou si code_patient est spécifié : { "Jan": 2, "Fév": 1, ... }
        """
        stats = self._stats_mensuels_int()
        mois_mapping = self._mois_mapping()
        
        conn = self.db.connect()
        if not conn:
            return stats

        try:
            cursor = conn.cursor(DictCursor)
            
            if code_patient:
                # Un patient spécifique
                query = """
                    SELECT MONTH(c.date_commande) AS num_mois, COUNT(*) AS total
                    FROM commandeslunettes c
                    LEFT JOIN acte_medical am ON c.code_acte    = am.code_acte
                    LEFT JOIN consultation con ON am.code_consultation = con.code
                    LEFT JOIN visite v         ON con.code_visite = v.code_visite
                    WHERE c.code_session=%s AND v.code_patient=%s
                    GROUP BY MONTH(c.date_commande)
                """
                cursor.execute(query, (code_session, code_patient))
                for row in cursor.fetchall():
                    m = row['num_mois']
                    if m in mois_mapping:
                        stats[mois_mapping[m]] = row['total']
            else:
                # Tous les patients
                query = """
                    SELECT MONTH(c.date_commande) AS num_mois,
                           v.code_patient,
                           COUNT(*) AS total
                    FROM commandeslunettes c
                    LEFT JOIN acte_medical am ON c.code_acte    = am.code_acte
                    LEFT JOIN consultation con ON am.code_consultation = con.code
                    LEFT JOIN visite v         ON con.code_visite = v.code_visite
                    WHERE c.code_session=%s
                    GROUP BY MONTH(c.date_commande), v.code_patient
                """
                cursor.execute(query, (code_session,))
                
                # Réorganiser en dict { mois: { patient: count } }
                stats_by_patient = {}
                for row in cursor.fetchall():
                    m = row['num_mois']
                    if m in mois_mapping:
                        mois_label = mois_mapping[m]
                        if mois_label not in stats_by_patient:
                            stats_by_patient[mois_label] = {}
                        stats_by_patient[mois_label][row['code_patient']] = row['total']
                
                stats = stats_by_patient if stats_by_patient else stats
            
            return stats
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur commandes_par_patient_par_mois: {e}")
            return {}
        finally:
            self.db.close()
    
    # methodes code_patient par session
    def codes_patients_session(self, code_session: str) -> list:
        """
        Retourne la liste de tous les patients dans la table patients.
        Le champ a_consulte indique s'ils ont déjà une commande dans la session donnée.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            query = """
                SELECT p.code_patient, p.nom, p.prenom,
                       CASE WHEN EXISTS(
                           SELECT 1
                           FROM commandeslunettes cl2
                           LEFT JOIN acte_medical am2 ON cl2.code_acte    = am2.code_acte
                           LEFT JOIN consultation c2  ON am2.code_consultation = c2.code
                           LEFT JOIN visite v2        ON c2.code_visite   = v2.code_visite
                           WHERE v2.code_patient = p.code_patient AND v2.code_session = %s
                       ) THEN 1 ELSE 0 END AS a_consulte
                FROM patients p
                ORDER BY p.nom ASC, p.prenom ASC
            """
            cursor.execute(query, (code_session,))
            result = cursor.fetchall()
            return result
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur codes_patients_session: {e}")
            return []
        finally:
            self.db.close()
            
    # methodes privées
    def _patients_par_service(self, code_session: str, condition: str) -> list:
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            query = f"""
                SELECT cl.code, cl.date_commande, p.nom, p.prenom, p.telephone
                FROM commandeslunettes cl
                LEFT JOIN acte_medical am ON cl.code_acte    = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite   = v.code_visite
                LEFT JOIN patients p      ON v.code_patient  = p.code_patient
                WHERE cl.code_session=%s AND {condition}
                ORDER BY cl.date_commande DESC
            """
            cursor.execute(query, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[CommandeLunetteDAO] Erreur _patients_par_service ({condition}): {e}")
            return []
        finally:
            self.db.close()
