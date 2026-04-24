"""
Modèle de données pour la table panier_facture.
Représente une ligne de détail dans le corps d'une facture patient.
"""


class PanierFacture:
    """
    Représente une ligne de la table panier_facture.

    Colonnes :
        code_paniere      PK  VARCHAR   généré PAN001+
        designation       VARCHAR       libellé du service (ex: 'Consultation')
        numero_reference  VARCHAR       code source du service (ex: CLS001)
        quantite_facture  INT           toujours 1 sauf cas particulier
        prix_applique     DECIMAL       montant de la ligne
        code_facture      FK → facture_patient
    """

    def __init__(
        self,
        code_paniere:     str,
        designation:      str,
        numero_reference: str,
        quantite_facture: int,
        prix_applique:    float,
        code_facture:     str,
    ):
        self.__code_paniere     = code_paniere
        self.__designation      = designation
        self.__numero_reference = numero_reference
        self.__quantite_facture = quantite_facture
        self.__prix_applique    = prix_applique
        self.__code_facture     = code_facture

    # ── Getters ───────────────────────────────────────────────────────────────

    def get_code_paniere(self)     -> str:   return self.__code_paniere
    def get_designation(self)      -> str:   return self.__designation
    def get_numero_reference(self) -> str:   return self.__numero_reference
    def get_quantite_facture(self) -> int:   return self.__quantite_facture
    def get_prix_applique(self)    -> float: return self.__prix_applique
    def get_code_facture(self)     -> str:   return self.__code_facture

    # ── Setters ───────────────────────────────────────────────────────────────

    def set_code_paniere(self,     v: str):   self.__code_paniere     = v
    def set_designation(self,      v: str):   self.__designation      = v
    def set_numero_reference(self, v: str):   self.__numero_reference = v
    def set_quantite_facture(self, v: int):   self.__quantite_facture = v
    def set_prix_applique(self,    v: float): self.__prix_applique    = v
    def set_code_facture(self,     v: str):   self.__code_facture     = v

    # ── Calcul ────────────────────────────────────────────────────────────────

    def get_sous_total(self) -> float:
        """Retourne le montant réel de la ligne (quantite × prix)."""
        return round(self.__quantite_facture * self.__prix_applique, 2)

    # ── Représentation ────────────────────────────────────────────────────────

    def __str__(self) -> str:
        return (
            f"PanierFacture(code={self.__code_paniere}, "
            f"designation={self.__designation}, "
            f"ref={self.__numero_reference}, "
            f"qte={self.__quantite_facture}, "
            f"prix={self.__prix_applique}, "
            f"facture={self.__code_facture})"
        )