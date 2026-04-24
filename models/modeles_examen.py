from datetime import datetime


class Examen:
    def __init__(self, code=None, libelle_examen=None, resultat_examen=None,
                 frais_examen=0.0, statut_facture="attente payement",
                 date_examen=None, code_consultation=None,code_visite=None,
                 code_session=None, code_personnel=None):
        self._code             = code
        self._libelle_examen   = libelle_examen
        self._resultat_examen  = resultat_examen
        self._frais_examen     = frais_examen
        self._statut_facture   = statut_facture
        self._date_examen      = date_examen or datetime.now()
        self._code_consultation = code_consultation
        self._code_visite = code_visite
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
    # libelle_examen
    # -------------------------------------------------------------------------
    @property
    def libelle_examen(self):
        return self._libelle_examen

    @libelle_examen.setter
    def libelle_examen(self, value):
        self._libelle_examen = value

    # -------------------------------------------------------------------------
    # resultat_examen
    # -------------------------------------------------------------------------
    @property
    def resultat_examen(self):
        return self._resultat_examen

    @resultat_examen.setter
    def resultat_examen(self, value):
        self._resultat_examen = value

    # -------------------------------------------------------------------------
    # frais_examen
    # -------------------------------------------------------------------------
    @property
    def frais_examen(self):
        return self._frais_examen

    @frais_examen.setter
    def frais_examen(self, value):
        self._frais_examen = value

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
    # date_examen
    # -------------------------------------------------------------------------
    @property
    def date_examen(self):
        return self._date_examen

    @date_examen.setter
    def date_examen(self, value):
        self._date_examen = value

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