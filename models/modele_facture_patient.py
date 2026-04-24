"""
Modèle de données pour la table facture_patient.
Représente l'en-tête d'une facture liée à une visite médicale.
"""


class FacturePatient:
    """
    Représente une ligne de la table facture_patient.

    Colonnes :
        code_facture   PK  VARCHAR    généré FCT001+
        code_visite    FK  → visite
        Montant_total  DECIMAL        somme de toutes les lignes panier
        Mode_payement  VARCHAR        'Espèces' | 'Mobile Money' | 'Carte bancaire'
        telephone      VARCHAR        contact patient (utile pour Mobile Money)
        statut_facture VARCHAR        'Attente payement' | 'Payé' | 'Annulé'
        date_facture   DATETIME       date de création de la facture
        code_session   FK  → annee
    """

    def __init__(
        self,
        code_facture:   str,
        code_visite:    str,
        montant_total:  float,
        mode_payement:  str,
        telephone:      str,
        statut_facture: str,
        date_facture,
        code_session:   str,
    ):
        self.__code_facture   = code_facture
        self.__code_visite    = code_visite
        self.__montant_total  = montant_total
        self.__mode_payement  = mode_payement
        self.__telephone      = telephone
        self.__statut_facture = statut_facture
        self.__date_facture   = date_facture
        self.__code_session   = code_session

    # ── Getters ───────────────────────────────────────────────────────────────

    def get_code_facture(self)   -> str:   return self.__code_facture
    def get_code_visite(self)    -> str:   return self.__code_visite
    def get_montant_total(self)  -> float: return self.__montant_total
    def get_mode_payement(self)  -> str:   return self.__mode_payement
    def get_telephone(self)      -> str:   return self.__telephone
    def get_statut_facture(self) -> str:   return self.__statut_facture
    def get_date_facture(self):            return self.__date_facture
    def get_code_session(self)   -> str:   return self.__code_session

    # ── Setters ───────────────────────────────────────────────────────────────

    def set_code_facture(self,   v: str):   self.__code_facture   = v
    def set_code_visite(self,    v: str):   self.__code_visite    = v
    def set_montant_total(self,  v: float): self.__montant_total  = v
    def set_mode_payement(self,  v: str):   self.__mode_payement  = v
    def set_telephone(self,      v: str):   self.__telephone      = v
    def set_statut_facture(self, v: str):   self.__statut_facture = v
    def set_date_facture(self,   v):        self.__date_facture   = v
    def set_code_session(self,   v: str):   self.__code_session   = v

    # ── Représentation ────────────────────────────────────────────────────────

    def __str__(self) -> str:
        return (
            f"FacturePatient(code={self.__code_facture}, "
            f"visite={self.__code_visite}, "
            f"montant={self.__montant_total}, "
            f"statut={self.__statut_facture}, "
            f"session={self.__code_session})"
        )