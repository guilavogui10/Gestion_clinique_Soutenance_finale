from datetime import datetime


class PanierFactureFourni:
    def __init__(self, code_panier_four=None, designation=None,
                 quantite_four=0, prix_unitaire=0.0,
                 date_expiration=None, code_produit=None,
                 code_facture_four=None,code_session=None):
        self._code_panier_four  = code_panier_four
        self._designation       = designation
        self._quantite_four     = quantite_four
        self._prix_unitaire     = prix_unitaire
        self._date_expiration   = date_expiration
        self._code_produit      = code_produit
        self._code_facture_four = code_facture_four
        self._code_session = code_session

    # -------------------------------------------------------------------------
    # code_panier_four
    # -------------------------------------------------------------------------
    @property
    def code_panier_four(self):
        return self._code_panier_four

    @code_panier_four.setter
    def code_panier_four(self, value):
        self._code_panier_four = value

    # -------------------------------------------------------------------------
    # designation
    # -------------------------------------------------------------------------
    @property
    def designation(self):
        return self._designation

    @designation.setter
    def designation(self, value):
        self._designation = value

    # -------------------------------------------------------------------------
    # quantite_four
    # -------------------------------------------------------------------------
    @property
    def quantite_four(self):
        return self._quantite_four

    @quantite_four.setter
    def quantite_four(self, value):
        self._quantite_four = value

    # -------------------------------------------------------------------------
    # prix_unitaire
    # -------------------------------------------------------------------------
    @property
    def prix_unitaire(self):
        return self._prix_unitaire

    @prix_unitaire.setter
    def prix_unitaire(self, value):
        self._prix_unitaire = value

    # -------------------------------------------------------------------------
    # date_expiration
    # -------------------------------------------------------------------------
    @property
    def date_expiration(self):
        return self._date_expiration

    @date_expiration.setter
    def date_expiration(self, value):
        self._date_expiration = value

    # -------------------------------------------------------------------------
    # code_produit
    # -------------------------------------------------------------------------
    @property
    def code_produit(self):
        return self._code_produit

    @code_produit.setter
    def code_produit(self, value):
        self._code_produit = value

    # -------------------------------------------------------------------------
    # code_facture_four
    # -------------------------------------------------------------------------
    @property
    def code_facture_four(self):
        return self._code_facture_four

    @code_facture_four.setter
    def code_facture_four(self, value):
        self._code_facture_four = value
        
    
    @property
    def code_session(self):
        return self._code_session

    @code_session.setter
    def code_session(self, value):
        self._code_session = value