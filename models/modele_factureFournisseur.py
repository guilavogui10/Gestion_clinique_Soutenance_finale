from datetime import datetime


class FactureFournisseur:
    def __init__(self, code_facture_four=None, montant_total=0.0,
                 mode_payement=None, telephone=None,
                 date_facture_four=None, code_fournisseur=None,
                 code_session=None):
        self._code_facture_four  = code_facture_four
        self._montant_total      = montant_total
        self._mode_payement      = mode_payement
        self._telephone          = telephone
        self._date_facture_four  = date_facture_four or datetime.now()
        self._code_fournisseur   = code_fournisseur
        self._code_session       = code_session

    # -------------------------------------------------------------------------
    # code_facture_four
    # -------------------------------------------------------------------------
    @property
    def code_facture_four(self):
        return self._code_facture_four

    @code_facture_four.setter
    def code_facture_four(self, value):
        self._code_facture_four = value

    # -------------------------------------------------------------------------
    # montant_total
    # -------------------------------------------------------------------------
    @property
    def montant_total(self):
        return self._montant_total

    @montant_total.setter
    def montant_total(self, value):
        self._montant_total = value

    # -------------------------------------------------------------------------
    # mode_payement
    # -------------------------------------------------------------------------
    @property
    def mode_payement(self):
        return self._mode_payement

    @mode_payement.setter
    def mode_payement(self, value):
        self._mode_payement = value

    # -------------------------------------------------------------------------
    # telephone
    # -------------------------------------------------------------------------
    @property
    def telephone(self):
        return self._telephone

    @telephone.setter
    def telephone(self, value):
        self._telephone = value

    # -------------------------------------------------------------------------
    # date_facture_four
    # -------------------------------------------------------------------------
    @property
    def date_facture_four(self):
        return self._date_facture_four

    @date_facture_four.setter
    def date_facture_four(self, value):
        self._date_facture_four = value

    # -------------------------------------------------------------------------
    # code_fournisseur
    # -------------------------------------------------------------------------
    @property
    def code_fournisseur(self):
        return self._code_fournisseur

    @code_fournisseur.setter
    def code_fournisseur(self, value):
        self._code_fournisseur = value

    # -------------------------------------------------------------------------
    # code_session
    # -------------------------------------------------------------------------
    @property
    def code_session(self):
        return self._code_session

    @code_session.setter
    def code_session(self, value):
        self._code_session = value