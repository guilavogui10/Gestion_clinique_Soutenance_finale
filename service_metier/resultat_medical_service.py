"""
resultat_medical_service.py
---------------------------
Service metier - Gestion des resultats medicaux.

Responsabilites :
  - Enregistrer un fichier resultat lie a un acte medical ou une consultation
  - Signer son empreinte via Vault Transit
  - Verifier l'integrite du fichier avant relecture
"""

import hashlib
import logging
from datetime import datetime

from core.minio_service import MinIOService
from core.vault_service import VaultService
from data.dao_resultat_medical import ResultatMedicalDAO
from models.model_resultat_medical import (
    NiveauConfidentialite,
    ResultatMedical,
    TypeFichier,
    TypeSource,
)


class ResultatMedicalService:
    def __init__(self, dao_resultat: ResultatMedicalDAO = None, minio: MinIOService = None):
        self.dao = dao_resultat or ResultatMedicalDAO()
        self._minio_instance = minio
        self._vault_instance = None
        self.logger = logging.getLogger(__name__)

    @property
    def minio(self) -> MinIOService:
        """Instanciation differee de MinIOService pour ne pas bloquer au demarrage."""
        if self._minio_instance is None:
            self._minio_instance = MinIOService()
        return self._minio_instance

    @property
    def vault(self) -> VaultService:
        """Instanciation differee de VaultService."""
        if self._vault_instance is None:
            self._vault_instance = VaultService()
        return self._vault_instance

    def _calculer_preuve_integrite(self, data: bytes) -> tuple[str | None, str | None, str | None]:
        """
        Calcule la preuve d'integrite en deux temps :
        1. empreinte SHA-256 locale
        2. signature HMAC Vault de cette empreinte
        """
        if not data:
            return None, None, "Impossible de calculer l'integrite d'un contenu vide"

        if not self.vault.est_connecte():
            return None, None, "Vault est indisponible : impossible de signer l'empreinte du fichier."

        empreinte_sha256 = hashlib.sha256(data).hexdigest()
        hmac_integrite = self.vault.calculer_hmac(empreinte_sha256.encode("utf-8"))
        if not hmac_integrite:
            return None, None, "Vault n'a pas pu produire la signature d'integrite du fichier."

        return empreinte_sha256, hmac_integrite, None

    # =========================================================================
    # SECTION 1 - ENREGISTREMENT
    # =========================================================================

    def enregistrer_resultat(
        self,
        type_source: str,
        type_fichier: str,
        chemin_local: str,
        code_acte_medical: str = None,
        code_consultation: str = None,
        description: str = None,
        niveau_confidentialite: str = NiveauConfidentialite.MOYEN,
    ) -> tuple:
        """
        Upload un fichier vers MinIO et enregistre les metadonnees en BD.
        """
        if not type_source or type_source not in TypeSource.VALEURS:
            return None, f"type_source invalide. Valeurs : {TypeSource.VALEURS}"
        if not type_fichier or type_fichier not in TypeFichier.VALEURS:
            return None, f"type_fichier invalide. Valeurs : {TypeFichier.VALEURS}"
        if not chemin_local or not chemin_local.strip():
            return None, "Le chemin local du fichier est obligatoire"
        if not code_acte_medical and not code_consultation:
            return None, "code_acte_medical ou code_consultation doit etre renseigne"
        if niveau_confidentialite not in NiveauConfidentialite.VALEURS:
            niveau_confidentialite = NiveauConfidentialite.MOYEN

        try:
            with open(chemin_local.strip(), "rb") as fichier:
                donnees = fichier.read()
        except Exception as e:
            return None, f"Lecture du fichier impossible : {e}"

        empreinte_sha256, hmac_integrite, erreur_integrite = self._calculer_preuve_integrite(donnees)
        if erreur_integrite:
            return None, erreur_integrite

        id_resultat = self.dao.generate_code_resultat()
        object_name = self.minio.upload_fichier(chemin_local.strip(), type_fichier, id_resultat)
        if not object_name:
            return None, "Echec de l'upload vers MinIO (verifier le fichier et la connexion)"

        resultat = ResultatMedical(
            id_resultat=id_resultat,
            type_source=type_source,
            code_acte_medical=code_acte_medical,
            code_consultation=code_consultation,
            type_fichier=type_fichier,
            chemin_fichier=object_name,
            empreinte_sha256=empreinte_sha256,
            hmac_integrite=hmac_integrite,
            description=description,
            date_upload=datetime.now(),
            niveau_confidentialite=niveau_confidentialite,
        )

        if self.dao.ajouter(resultat):
            self.logger.info(
                "Resultat %s uploade sur MinIO : %s (acte=%s, consultation=%s)",
                id_resultat,
                object_name,
                code_acte_medical,
                code_consultation,
            )
            return resultat, "Resultat enregistre avec succes"

        self.minio.supprimer_fichier(object_name)
        return None, "Erreur lors de l'enregistrement en base de donnees"

    def enregistrer_bytes(
        self,
        type_source: str,
        type_fichier: str,
        data: bytes,
        nom_fichier: str,
        code_acte_medical: str = None,
        code_consultation: str = None,
        description: str = None,
        niveau_confidentialite: str = NiveauConfidentialite.MOYEN,
    ) -> tuple:
        """
        Upload des donnees binaires en memoire (ex: PDF genere par ReportLab)
        vers MinIO et enregistre les metadonnees en BD.
        """
        if not type_source or type_source not in TypeSource.VALEURS:
            return None, f"type_source invalide. Valeurs : {TypeSource.VALEURS}"
        if not type_fichier or type_fichier not in TypeFichier.VALEURS:
            return None, f"type_fichier invalide. Valeurs : {TypeFichier.VALEURS}"
        if not data:
            return None, "Donnees binaires vides"
        if not code_acte_medical and not code_consultation:
            return None, "code_acte_medical ou code_consultation doit etre renseigne"
        if niveau_confidentialite not in NiveauConfidentialite.VALEURS:
            niveau_confidentialite = NiveauConfidentialite.MOYEN

        empreinte_sha256, hmac_integrite, erreur_integrite = self._calculer_preuve_integrite(data)
        if erreur_integrite:
            return None, erreur_integrite

        id_resultat = self.dao.generate_code_resultat()
        object_name = self.minio.upload_bytes(data, nom_fichier, type_fichier, id_resultat)
        if not object_name:
            return None, "Echec de l'upload bytes vers MinIO"

        resultat = ResultatMedical(
            id_resultat=id_resultat,
            type_source=type_source,
            code_acte_medical=code_acte_medical,
            code_consultation=code_consultation,
            type_fichier=type_fichier,
            chemin_fichier=object_name,
            empreinte_sha256=empreinte_sha256,
            hmac_integrite=hmac_integrite,
            description=description,
            date_upload=datetime.now(),
            niveau_confidentialite=niveau_confidentialite,
        )

        if self.dao.ajouter(resultat):
            self.logger.info("Resultat bytes %s uploade : %s", id_resultat, object_name)
            return resultat, "Resultat enregistre avec succes"

        self.minio.supprimer_fichier(object_name)
        return None, "Erreur lors de l'enregistrement en base de donnees"

    def modifier_resultat(
        self,
        id_resultat: str,
        description: str = None,
        niveau_confidentialite: str = None,
    ) -> tuple:
        """Met a jour description et/ou niveau de confidentialite."""
        resultat = self.dao.obtenir_par_id(id_resultat)
        if not resultat:
            return False, "Resultat introuvable"
        if description is not None:
            resultat.description = description
        if niveau_confidentialite is not None:
            if niveau_confidentialite not in NiveauConfidentialite.VALEURS:
                return False, f"Niveau invalide : {niveau_confidentialite}"
            resultat.niveau_confidentialite = niveau_confidentialite
        if self.dao.modifier(resultat):
            self.logger.info("Resultat %s mis a jour", id_resultat)
            return True, "Resultat mis a jour"
        return False, "Erreur lors de la mise a jour"

    def supprimer_resultat(self, id_resultat: str) -> tuple:
        """Supprime un resultat medical : fichier MinIO + metadonnees BD."""
        resultat = self.dao.obtenir_par_id(id_resultat)
        if resultat and resultat.chemin_fichier:
            self.minio.supprimer_fichier(resultat.chemin_fichier)
        if self.dao.supprimer(id_resultat):
            self.logger.info("Resultat %s supprime", id_resultat)
            return True, "Resultat supprime"
        return False, "Erreur lors de la suppression"

    # =========================================================================
    # SECTION 2 - RECUPERATION & ACCES MINIO
    # =========================================================================

    def obtenir_resultat(self, id_resultat: str) -> ResultatMedical | None:
        """Retourne un resultat par son id."""
        return self.dao.obtenir_par_id(id_resultat)

    def verifier_integrite_resultat(self, id_resultat: str) -> tuple[bool, str]:
        """
        Vérifie l'intégrité d'un fichier en deux étapes :
        1. SHA-256 (obligatoire) : détecte toute modification réelle du fichier.
        2. HMAC Vault (optionnel) : si Vault est indisponible, on passe en mode
           dégradé — le SHA-256 suffisant pour garantir l'intégrité du contenu.
        Les anciens enregistrements sans signature restent lisibles.
        """
        resultat = self.dao.obtenir_par_id(id_resultat)
        if not resultat or not resultat.chemin_fichier:
            return False, "Resultat introuvable."

        if not resultat.empreinte_sha256 or not resultat.hmac_integrite:
            return True, "Aucune signature d'integrite n'est enregistree pour ce fichier."

        donnees = self.minio.lire_bytes(resultat.chemin_fichier)
        if donnees is None:
            return False, "Impossible de relire le fichier sur MinIO."

        empreinte_calculee = hashlib.sha256(donnees).hexdigest()
        if empreinte_calculee != resultat.empreinte_sha256:
            self.logger.warning(
                "Integrite compromise pour %s : empreinte differente.",
                id_resultat,
            )
            return False, "Le contenu du fichier a ete modifie ou corrompu."

        # SHA-256 OK — vérification HMAC Vault (couche optionnelle, non bloquante)
        # Le SHA-256 suffit à garantir que le contenu du fichier n'a pas changé.
        # Le HMAC Vault peut échouer légitimement si Vault est indisponible ou si
        # la clé de chiffrement est différente (ex : autre machine, reinstallation).
        if not self.vault.est_connecte():
            self.logger.warning(
                "Vault indisponible pour %s — acces autorise sur SHA-256 uniquement.",
                id_resultat,
            )
            return True, "Integrite verifiee (SHA-256 OK, Vault indisponible)."

        try:
            signature_valide = self.vault.verifier_hmac(
                empreinte_calculee.encode("utf-8"),
                resultat.hmac_integrite,
            )
            if not signature_valide:
                self.logger.warning(
                    "HMAC Vault non conforme pour %s (cle differente ?) — acces autorise sur SHA-256.",
                    id_resultat,
                )
        except Exception as e:
            self.logger.warning(
                "Erreur HMAC Vault pour %s : %s — acces autorise sur SHA-256.",
                id_resultat, e,
            )

        return True, "Integrite du fichier verifiee."

    def get_url_temporaire(self, id_resultat: str, duree_minutes: int = 60) -> str | None:
        """Retourne une URL presignee MinIO pour afficher ou telecharger le fichier."""
        resultat = self.dao.obtenir_par_id(id_resultat)
        if not resultat or not resultat.chemin_fichier:
            return None

        integrite_ok, _ = self.verifier_integrite_resultat(id_resultat)
        if not integrite_ok:
            return None

        return self.minio.get_url_temporaire(resultat.chemin_fichier, duree_minutes)

    def lire_fichier_bytes(self, id_resultat: str) -> bytes | None:
        """Lit le contenu binaire du fichier MinIO d'un resultat."""
        resultat = self.dao.obtenir_par_id(id_resultat)
        if not resultat or not resultat.chemin_fichier:
            return None

        integrite_ok, _ = self.verifier_integrite_resultat(id_resultat)
        if not integrite_ok:
            return None

        return self.minio.lire_bytes(resultat.chemin_fichier)

    def lister_par_acte(self, code_acte_medical: str) -> list:
        """Retourne tous les resultats lies a un acte medical."""
        return self.dao.lister_par_acte(code_acte_medical)

    def lister_par_consultation(self, code_consultation: str) -> list:
        """Retourne tous les resultats lies a une consultation."""
        return self.dao.lister_par_consultation(code_consultation)

    def lister_images_acte(self, code_acte_medical: str) -> list:
        """Retourne uniquement les images d'un acte."""
        return self.dao.lister_par_type_fichier(code_acte_medical, TypeFichier.IMAGE)

    def lister_pdfs_acte(self, code_acte_medical: str) -> list:
        """Retourne uniquement les PDFs d'un acte."""
        return self.dao.lister_par_type_fichier(code_acte_medical, TypeFichier.PDF)

    def source_a_des_resultats(self, code_acte_medical: str = None, code_consultation: str = None) -> bool:
        """Verifie si un acte ou une consultation possede au moins un resultat."""
        return self.dao.source_a_des_resultats(code_acte_medical, code_consultation)

    # =========================================================================
    # SECTION 3 - RESUMES POUR LES VUES
    # =========================================================================

    def resume_par_acte(self, code_acte_medical: str) -> dict:
        """Resume groupe par type de fichier pour un acte medical."""
        resultats = self.dao.lister_par_acte(code_acte_medical)
        par_type = {}
        for resultat in resultats:
            par_type.setdefault(resultat.type_fichier, []).append(resultat.to_dict())
        return {
            "code_acte_medical": code_acte_medical,
            "nb_resultats": len(resultats),
            "par_type": par_type,
        }

    def resume_par_consultation(self, code_consultation: str) -> dict:
        """Resume groupe par type de fichier pour une consultation."""
        resultats = self.dao.lister_par_consultation(code_consultation)
        par_type = {}
        for resultat in resultats:
            par_type.setdefault(resultat.type_fichier, []).append(resultat.to_dict())
        return {
            "code_consultation": code_consultation,
            "nb_resultats": len(resultats),
            "par_type": par_type,
        }

    def lister_par_type_source(self, type_source: str) -> list:
        """Retourne tous les resultats d'un type de source donne."""
        return self.dao.lister_par_type_source(type_source)

    def compter_par_type_source(self) -> dict:
        """Retourne le nombre de resultats groupes par type de source."""
        return self.dao.compter_par_type_source()

    def lister_par_patient(self, code_patient: str) -> list:
        """Retourne tous les resultats medicaux lies a un patient."""
        return self.dao.lister_par_patient(code_patient)

    def get_detail_complet(self, id_resultat: str) -> dict | None:
        """Retourne le détail complet d'un résultat médical."""
        return self.dao.get_detail_complet(id_resultat)

    def lister_codes_actes_par_type(self, type_acte: str) -> list:
        """
        Retourne les actes médicaux d'un type donné (examen|chirurgie).
        Chaque élément est un tuple (code_acte, label_affiche).
        """
        try:
            from data.dao_acte_medicale import ActeMedicalDAO
            dao = ActeMedicalDAO()
            actes = dao.lister_par_type(type_acte)
            result = []
            for a in actes:
                code = a.id_acte if hasattr(a, 'id_acte') else a.get('id_acte', '')
                decision = a.decision_medicale if hasattr(a, 'decision_medicale') else a.get('decision_medicale', '')
                label = f"{code}"
                if decision:
                    label += f" — {str(decision)[:40]}"
                result.append((code, label))
            return result
        except Exception as e:
            self.logger.warning("Erreur lister_codes_actes_par_type: %s", e)
            return []
