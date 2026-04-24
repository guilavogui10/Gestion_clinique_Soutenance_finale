class PanierPrescriptionProduit:
    def __init__(self, code_prescription=None, designation=None, code_produit=None,
                 quantite_prescript=0, prix_applique=0.0, date_expiration=None,
                 code_consultation=None, code_visite=None, code_session=None):
        self._code_prescription = code_prescription
        self._designation = designation
        self._code_produit = code_produit
        self._quantite_prescript = quantite_prescript
        self._prix_applique = prix_applique
        self._date_expiration = date_expiration
        self._code_consultation = code_consultation
        self._code_visite = code_visite
        self._code_session = code_session

    # ---------------------------------------------------------------------
    # code_prescription
    # ---------------------------------------------------------------------
    @property
    def code_prescription(self):
        return self._code_prescription

    @code_prescription.setter
    def code_prescription(self, value):
        self._code_prescription = value

    # ---------------------------------------------------------------------
    # designation
    # ---------------------------------------------------------------------
    @property
    def designation(self):
        return self._designation

    @designation.setter
    def designation(self, value):
        self._designation = value

    # ---------------------------------------------------------------------
    # code_produit
    # ---------------------------------------------------------------------
    @property
    def code_produit(self):
        return self._code_produit

    @code_produit.setter
    def code_produit(self, value):
        self._code_produit = value

    # ---------------------------------------------------------------------
    # quantite_prescript
    # ---------------------------------------------------------------------
    @property
    def quantite_prescript(self):
        return self._quantite_prescript

    @quantite_prescript.setter
    def quantite_prescript(self, value):
        self._quantite_prescript = value

    # ---------------------------------------------------------------------
    # prix_applique
    # ---------------------------------------------------------------------
    @property
    def prix_applique(self):
        return self._prix_applique

    @prix_applique.setter
    def prix_applique(self, value):
        self._prix_applique = value

    # ---------------------------------------------------------------------
    # date_expiration
    # ---------------------------------------------------------------------
    @property
    def date_expiration(self):
        return self._date_expiration

    @date_expiration.setter
    def date_expiration(self, value):
        self._date_expiration = value

    # ---------------------------------------------------------------------
    # code_consultation
    # ---------------------------------------------------------------------
    @property
    def code_consultation(self):
        return self._code_consultation

    @code_consultation.setter
    def code_consultation(self, value):
        self._code_consultation = value

    # ---------------------------------------------------------------------
    # code_visite
    # ---------------------------------------------------------------------
    @property
    def code_visite(self):
        return self._code_visite

    @code_visite.setter
    def code_visite(self, value):
        self._code_visite = value

    # ---------------------------------------------------------------------
    # code_session
    # ---------------------------------------------------------------------
    @property
    def code_session(self):
        return self._code_session

    @code_session.setter
    def code_session(self, value):
        self._code_session = value
