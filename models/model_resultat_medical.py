"""
model_resultat_medical.py
-------------------------
Modele de la table resultat_medical.
Stocke les fichiers produits apres un acte medical ou une consultation
(images, videos, PDFs) avec leur source, leur niveau de confidentialite
et leur preuve d'integrite Vault.
"""

from datetime import datetime


class TypeSource:
    CONSULTATION = "consultation"
    EXAMEN = "examen"
    CHIRURGIE = "chirurgie"

    VALEURS = [CONSULTATION, EXAMEN, CHIRURGIE]


class TypeFichier:
    IMAGE = "image"
    VIDEO = "video"
    PDF = "pdf"

    VALEURS = [IMAGE, VIDEO, PDF]


class NiveauConfidentialite:
    FAIBLE = "faible"
    MOYEN = "moyen"
    ELEVE = "eleve"

    VALEURS = [FAIBLE, MOYEN, ELEVE]


class ResultatMedical:
    """
    Represente un fichier resultat lie a un acte medical ou une consultation.
    """

    def __init__(
        self,
        id_resultat: str = None,
        type_source: str = None,
        code_acte_medical: str = None,
        code_consultation: str = None,
        type_fichier: str = None,
        chemin_fichier: str = None,
        empreinte_sha256: str = None,
        hmac_integrite: str = None,
        description: str = None,
        date_upload: datetime = None,
        niveau_confidentialite: str = NiveauConfidentialite.MOYEN,
    ):
        self.id_resultat = id_resultat
        self.type_source = type_source
        self.code_acte_medical = code_acte_medical
        self.code_consultation = code_consultation
        self.type_fichier = type_fichier
        self.chemin_fichier = chemin_fichier
        self.empreinte_sha256 = empreinte_sha256
        self.hmac_integrite = hmac_integrite
        self.description = description
        self.date_upload = date_upload or datetime.now()
        self.niveau_confidentialite = niveau_confidentialite

    def est_image(self) -> bool:
        return self.type_fichier == TypeFichier.IMAGE

    def est_confidentiel(self) -> bool:
        return self.niveau_confidentialite == NiveauConfidentialite.ELEVE

    def to_dict(self) -> dict:
        return {
            "id_resultat": self.id_resultat,
            "type_source": self.type_source,
            "code_acte_medical": self.code_acte_medical,
            "code_consultation": self.code_consultation,
            "type_fichier": self.type_fichier,
            "chemin_fichier": self.chemin_fichier,
            "empreinte_sha256": self.empreinte_sha256,
            "hmac_integrite": self.hmac_integrite,
            "description": self.description,
            "date_upload": self.date_upload.isoformat() if self.date_upload else None,
            "niveau_confidentialite": self.niveau_confidentialite,
        }

    def __repr__(self) -> str:
        return (
            f"ResultatMedical(id={self.id_resultat}, source={self.type_source}, "
            f"acte={self.code_acte_medical}, consultation={self.code_consultation}, "
            f"fichier={self.type_fichier})"
        )
