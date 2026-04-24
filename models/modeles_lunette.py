from datetime import datetime


class CommandeLunette:
    def __init__(self, code=None, numero_cadre=None, numero_verre=None,
                 date_commande=None, date_livraison=None, prix=0.0,
                 statut="attente", statut_facture="Attente payement",
                 code_consultation=None, code_visite=None,
                 code_session=None, code_personnel=None):

        self._code             = code
        self._numero_cadre     = numero_cadre
        self._numero_verre     = numero_verre
        self._date_commande    = date_commande or datetime.now()
        self._date_livraison   = date_livraison
        self._prix             = prix
        self._statut           = statut
        self._statut_facture   = statut_facture
        self._code_consultation = code_consultation
        self._code_visite      = code_visite
        self._code_session     = code_session
        self._code_personnel   = code_personnel

    # -------------------------------------------------------------------------
    # code
    # -------------------------------------------------------------------------
    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, value):
        self._code = value

    # -------------------------------------------------------------------------
    # numero_cadre
    # -------------------------------------------------------------------------
    @property
    def numero_cadre(self):
        return self._numero_cadre

    @numero_cadre.setter
    def numero_cadre(self, value):
        self._numero_cadre = value

    # -------------------------------------------------------------------------
    # numero_verre
    # -------------------------------------------------------------------------
    @property
    def numero_verre(self):
        return self._numero_verre

    @numero_verre.setter
    def numero_verre(self, value):
        self._numero_verre = value

    # -------------------------------------------------------------------------
    # date_commande
    # -------------------------------------------------------------------------
    @property
    def date_commande(self):
        return self._date_commande

    @date_commande.setter
    def date_commande(self, value):
        self._date_commande = value

    # -------------------------------------------------------------------------
    # date_livraison
    # -------------------------------------------------------------------------
    @property
    def date_livraison(self):
        return self._date_livraison

    @date_livraison.setter
    def date_livraison(self, value):
        self._date_livraison = value

    # -------------------------------------------------------------------------
    # prix
    # -------------------------------------------------------------------------
    @property
    def prix(self):
        return self._prix

    @prix.setter
    def prix(self, value):
        self._prix = value

    # -------------------------------------------------------------------------
    # statut
    # -------------------------------------------------------------------------
    @property
    def statut(self):
        return self._statut

    @statut.setter
    def statut(self, value):
        self._statut = value

    # -------------------------------------------------------------------------
    # statut_facture
    # -------------------------------------------------------------------------
    @property
    def statut_facture(self):
        return self._statut_facture

    @statut_facture.setter
    def statut_facture(self, value):
        self._statut_facture = value

    # -------------------------------------------------------------------------
    # code_consultation
    # -------------------------------------------------------------------------
    @property
    def code_consultation(self):
        return self._code_consultation

    @code_consultation.setter
    def code_consultation(self, value):
        self._code_consultation = value

    # -------------------------------------------------------------------------
    # code_visite
    # -------------------------------------------------------------------------
    @property
    def code_visite(self):
        return self._code_visite

    @code_visite.setter
    def code_visite(self, value):
        self._code_visite = value

    # -------------------------------------------------------------------------
    # code_session
    # -------------------------------------------------------------------------
    @property
    def code_session(self):
        return self._code_session

    @code_session.setter
    def code_session(self, value):
        self._code_session = value

    # -------------------------------------------------------------------------
    # code_personnel
    # -------------------------------------------------------------------------
    @property
    def code_personnel(self):
        return self._code_personnel

    @code_personnel.setter
    def code_personnel(self, value):
        self._code_personnel = value