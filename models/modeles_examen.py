from datetime import datetime


class Examen:
    def __init__(self, code=None, libelle_examen=None,
                 frais_examen=0.0, statut_facture="attente payement",
                 date_examen=None, code_session=None,
                 code_personnel=None, code_acte=None,
                 interpreter_par=None, date_interpretation=None,
                 conclusion_medicale=None):
        self._code                = code
        self._libelle_examen      = libelle_examen
        self._frais_examen        = frais_examen
        self._statut_facture      = statut_facture
        self._date_examen         = date_examen or datetime.now()
        self._code_session        = code_session
        self._code_personnel      = code_personnel
        self._code_acte           = code_acte
        self._interpreter_par     = interpreter_par
        self._date_interpretation = date_interpretation
        self._conclusion_medicale = conclusion_medicale

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
    # interpreter_par
    # -------------------------------------------------------------------------
    @property
    def interpreter_par(self):
        return self._interpreter_par

    @interpreter_par.setter
    def interpreter_par(self, value):
        self._interpreter_par = value

    # -------------------------------------------------------------------------
    # date_interpretation
    # -------------------------------------------------------------------------
    @property
    def date_interpretation(self):
        return self._date_interpretation

    @date_interpretation.setter
    def date_interpretation(self, value):
        self._date_interpretation = value

    # -------------------------------------------------------------------------
    # conclusion_medicale
    # -------------------------------------------------------------------------
    @property
    def conclusion_medicale(self):
        return self._conclusion_medicale

    @conclusion_medicale.setter
    def conclusion_medicale(self, value):
        self._conclusion_medicale = value