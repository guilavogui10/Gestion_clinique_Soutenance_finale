import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service_metier.resultat_medical_service import ResultatMedicalService
from models.model_resultat_medical import (
    TypeSource, TypeFichier, NiveauConfidentialite
)


class ResultatMedicalControleur:
    """
    Contrôleur MVC pour la gestion des résultats médicaux.

    Fait le lien entre la vue et le service métier.
    Délègue toute la logique (upload MinIO, validation, BD) au service.
    """

    def __init__(self):
        self.service = ResultatMedicalService()
        self.logger  = logging.getLogger(__name__)

    # =========================================================================
    # SECTION 1 — VALIDATION
    # =========================================================================

    def valider_type_source(self, type_source: str) -> tuple:
        if not type_source or type_source not in TypeSource.VALEURS:
            return False, f"type_source invalide. Valeurs acceptées : {TypeSource.VALEURS}"
        return True, ""

    def valider_type_fichier(self, type_fichier: str) -> tuple:
        if not type_fichier or type_fichier not in TypeFichier.VALEURS:
            return False, f"type_fichier invalide. Valeurs acceptées : {TypeFichier.VALEURS}"
        return True, ""

    def valider_chemin_fichier(self, chemin: str) -> tuple:
        if not chemin or not chemin.strip():
            return False, "Le chemin du fichier est obligatoire"
        if not os.path.isfile(chemin.strip()):
            return False, f"Fichier introuvable : {chemin.strip()}"
        return True, ""

    def valider_source_reference(self, code_acte_medical: str = None,
                                  code_consultation: str = None) -> tuple:
        if not code_acte_medical and not code_consultation:
            return False, "Fournir code_acte_medical ou code_consultation"
        return True, ""

    # =========================================================================
    # SECTION 2 — UPLOAD / ENREGISTREMENT
    # =========================================================================

    def ajouter_resultat(self,
                          type_source: str,
                          type_fichier: str,
                          chemin_local: str,
                          code_acte_medical: str = None,
                          code_consultation: str = None,
                          description: str = None,
                          niveau_confidentialite: str = NiveauConfidentialite.MOYEN
                          ) -> tuple:
        """
        Valide les champs puis délègue l'upload MinIO + enregistrement BD au service.

        Returns:
            (ResultatMedical, message)  si succès
            (None, message_erreur)       si échec
        """
        ok, msg = self.valider_type_source(type_source)
        if not ok:
            return None, msg

        ok, msg = self.valider_type_fichier(type_fichier)
        if not ok:
            return None, msg

        ok, msg = self.valider_chemin_fichier(chemin_local)
        if not ok:
            return None, msg

        ok, msg = self.valider_source_reference(code_acte_medical, code_consultation)
        if not ok:
            return None, msg

        return self.service.enregistrer_resultat(
            type_source            = type_source,
            type_fichier           = type_fichier,
            chemin_local           = chemin_local,
            code_acte_medical      = code_acte_medical,
            code_consultation      = code_consultation,
            description            = description,
            niveau_confidentialite = niveau_confidentialite,
        )

    def ajouter_resultat_bytes(self,
                                type_source: str,
                                type_fichier: str,
                                data: bytes,
                                nom_fichier: str,
                                code_acte_medical: str = None,
                                code_consultation: str = None,
                                description: str = None,
                                niveau_confidentialite: str = NiveauConfidentialite.MOYEN
                                ) -> tuple:
        """Upload depuis des données binaires en mémoire (ex : PDF généré)."""
        ok, msg = self.valider_type_source(type_source)
        if not ok:
            return None, msg

        ok, msg = self.valider_type_fichier(type_fichier)
        if not ok:
            return None, msg

        if not data:
            return None, "Données binaires vides"

        ok, msg = self.valider_source_reference(code_acte_medical, code_consultation)
        if not ok:
            return None, msg

        return self.service.enregistrer_bytes(
            type_source            = type_source,
            type_fichier           = type_fichier,
            data                   = data,
            nom_fichier            = nom_fichier,
            code_acte_medical      = code_acte_medical,
            code_consultation      = code_consultation,
            description            = description,
            niveau_confidentialite = niveau_confidentialite,
        )

    # =========================================================================
    # SECTION 3 — MODIFICATION / SUPPRESSION
    # =========================================================================

    def modifier_resultat(self, id_resultat: str,
                           description: str = None,
                           niveau_confidentialite: str = None) -> tuple:
        """Met à jour description et/ou niveau de confidentialité."""
        if not id_resultat or not id_resultat.strip():
            return False, "L'identifiant du résultat est obligatoire"
        return self.service.modifier_resultat(
            id_resultat            = id_resultat.strip(),
            description            = description,
            niveau_confidentialite = niveau_confidentialite,
        )

    def modifier_resultat_complet(self,
                                  id_resultat: str,
                                  type_source: str,
                                  type_fichier: str,
                                  chemin_local: str = None,
                                  code_acte_medical: str = None,
                                  code_consultation: str = None,
                                  description: str = None,
                                  niveau_confidentialite: str = "moyen"
                                  ) -> tuple:
        ok, msg = self.valider_type_source(type_source)
        if not ok:
            return False, msg

        ok, msg = self.valider_type_fichier(type_fichier)
        if not ok:
            return False, msg

        if chemin_local and chemin_local.strip():
            ok, msg = self.valider_chemin_fichier(chemin_local)
            if not ok:
                return False, msg

        ok, msg = self.valider_source_reference(code_acte_medical, code_consultation)
        if not ok:
            return False, msg

        return self.service.modifier_resultat_complet(
            id_resultat=id_resultat,
            type_source=type_source,
            type_fichier=type_fichier,
            chemin_local=chemin_local,
            code_acte_medical=code_acte_medical,
            code_consultation=code_consultation,
            description=description,
            niveau_confidentialite=niveau_confidentialite,
        )

    def supprimer_resultat(self, id_resultat: str) -> tuple:
        """Supprime le fichier sur MinIO et la ligne en base de données."""
        if not id_resultat or not id_resultat.strip():
            return False, "L'identifiant du résultat est obligatoire"
        return self.service.supprimer_resultat(id_resultat.strip())

    # =========================================================================
    # SECTION 4 — RÉCUPÉRATION
    # =========================================================================

    def obtenir_resultat(self, id_resultat: str):
        """Retourne un résultat par son identifiant."""
        if not id_resultat or not id_resultat.strip():
            return None
        return self.service.obtenir_resultat(id_resultat.strip())

    def lister_par_acte(self, code_acte_medical: str) -> list:
        """Retourne tous les résultats d'un acte médical."""
        if not code_acte_medical:
            return []
        return self.service.lister_par_acte(code_acte_medical)

    def lister_par_consultation(self, code_consultation: str) -> list:
        """Retourne tous les résultats d'une consultation."""
        if not code_consultation:
            return []
        return self.service.lister_par_consultation(code_consultation)

    def lister_images_acte(self, code_acte_medical: str) -> list:
        """Retourne uniquement les images d'un acte médical."""
        return self.service.lister_images_acte(code_acte_medical)

    def lister_pdfs_acte(self, code_acte_medical: str) -> list:
        """Retourne uniquement les PDFs d'un acte médical."""
        return self.service.lister_pdfs_acte(code_acte_medical)

    def resume_par_acte(self, code_acte_medical: str) -> dict:
        """Résumé groupé par type de fichier pour un acte médical."""
        return self.service.resume_par_acte(code_acte_medical)

    def resume_par_consultation(self, code_consultation: str) -> dict:
        """Résumé groupé par type de fichier pour une consultation."""
        return self.service.resume_par_consultation(code_consultation)

    # =========================================================================
    # SECTION 5 — ACCÈS MINIO
    # =========================================================================

    def get_url_temporaire(self, id_resultat: str, duree_minutes: int = 60) -> str | None:
        """
        Retourne une URL présignée pour accéder au fichier depuis le navigateur.

        Args:
            id_resultat:   Code du résultat (ex: RES-00000001).
            duree_minutes: Durée de validité (défaut 60 min).
        """
        if not id_resultat or not id_resultat.strip():
            return None
        return self.service.get_url_temporaire(id_resultat.strip(), duree_minutes)

    def lire_fichier_bytes(self, id_resultat: str) -> bytes | None:
        """Lit le contenu binaire du fichier (pour affichage ou traitement)."""
        if not id_resultat or not id_resultat.strip():
            return None
        return self.service.lire_fichier_bytes(id_resultat.strip())

    def verifier_integrite_resultat(self, id_resultat: str) -> tuple[bool, str]:
        """Verifie l'integrite Vault d'un fichier avant ouverture."""
        if not id_resultat or not id_resultat.strip():
            return False, "L'identifiant du resultat est obligatoire."
        return self.service.verifier_integrite_resultat(id_resultat.strip())

    # =========================================================================
    # SECTION 6 — LISTING PAR TYPE SOURCE / PATIENT
    # =========================================================================

    def lister_par_type_source(self, type_source: str) -> list:
        """Retourne tous les résultats d'un type de source (consultation/examen/chirurgie)."""
        if not type_source:
            return []
        return self.service.lister_par_type_source(type_source)

    def compter_par_type_source(self) -> dict:
        """Retourne un dict {type_source: count} pour les statistiques."""
        return self.service.compter_par_type_source()

    def lister_par_patient(self, code_patient: str) -> list:
        """Retourne tous les résultats liés à un patient (dossier patient)."""
        if not code_patient or not code_patient.strip():
            return []
        return self.service.lister_par_patient(code_patient.strip())

    def get_detail_resultat(self, id_resultat: str) -> dict:
        """Retourne toutes les infos jointes d'un résultat (patient, personnel, service)."""
        return self.service.get_detail_complet(id_resultat)

    # =========================================================================
    # SECTION 7 — AIDE FORMULAIRE (chargement des combos)
    # =========================================================================

    def lister_codes_consultations(self) -> list:
        """
        Retourne la liste des consultations pour peupler le combo 'code source'.
        Chaque élément est un tuple (code, label_affiche).
        """
        try:
            from controllers.controleur_consultation import ConsultationControleur
            consultations = ConsultationControleur().lister_toutes()
            result = []
            for c in consultations:
                code = c.code if hasattr(c, 'code') else c.get('code', '')
                diag = c.diagnostique if hasattr(c, 'diagnostique') else c.get('diagnostique', '')
                label = f"{code}"
                if diag:
                    label += f" — {str(diag)[:40]}"
                result.append((code, label))
            return result
        except Exception as e:
            self.logger.warning("Erreur lister_codes_consultations: %s", e)
            return []

    def lister_codes_actes_par_type(self, type_acte: str) -> list:
        """
        Retourne la liste des actes médicaux d'un type donné pour peupler le combo.
        Chaque élément est un tuple (code_acte, label_affiche).
        type_acte : 'examen' | 'chirurgie'
        """
        return self.service.lister_codes_actes_par_type(type_acte)
