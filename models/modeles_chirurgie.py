from datetime import datetime


class Chirurgie:
    def __init__(self, code=None, libelle_chururgie=None, frais_chururgie=0.0,
                 statut_facture="attente payement", date_chururgie=None,
                 code_session=None, code_personnel=None,
                 code_acte=None, compte_rendu_operatoire=None):

        self._code                   = code
        self._libelle_chururgie      = libelle_chururgie
        self._frais_chururgie        = frais_chururgie
        self._statut_facture         = statut_facture
        self._date_chururgie         = date_chururgie or datetime.now()
        self._code_session           = code_session
        self._code_personnel         = code_personnel
        self._code_acte              = code_acte
        self._compte_rendu_operatoire = compte_rendu_operatoire

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
    # libelle_chururgie
    # -------------------------------------------------------------------------
    @property
    def libelle_chururgie(self):
        return self._libelle_chururgie

    @libelle_chururgie.setter
    def libelle_chururgie(self, value):
        self._libelle_chururgie = value

    # -------------------------------------------------------------------------
    # frais_chururgie
    # -------------------------------------------------------------------------
    @property
    def frais_chururgie(self):
        return self._frais_chururgie

    @frais_chururgie.setter
    def frais_chururgie(self, value):
        self._frais_chururgie = value

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
    # date_chururgie
    # -------------------------------------------------------------------------
    @property
    def date_chururgie(self):
        return self._date_chururgie

    @date_chururgie.setter
    def date_chururgie(self, value):
        self._date_chururgie = value

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

    # -------------------------------------------------------------------------
    # code_acte
    # -------------------------------------------------------------------------
    @property
    def code_acte(self):
        return self._code_acte

    @code_acte.setter
    def code_acte(self, value):
        self._code_acte = value

    # -------------------------------------------------------------------------
    # compte_rendu_operatoire
    # -------------------------------------------------------------------------
    @property
    def compte_rendu_operatoire(self):
        return self._compte_rendu_operatoire

    @compte_rendu_operatoire.setter
    def compte_rendu_operatoire(self, value):
        self._compte_rendu_operatoire = value