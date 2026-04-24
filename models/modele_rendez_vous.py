from datetime import datetime

class RendezVous:
    def __init__(self, code_rendez_vous=None, code_visite=None, code_personnel=None,
                 code_session=None, date_rendez_vous=None, statut_rendez_vous="En attente"):
        
        self._code_rendez_vous   = code_rendez_vous
        self._code_visite        = code_visite
        self._code_personnel     = code_personnel
        self._code_session       = code_session
        self._date_rendez_vous   = date_rendez_vous or datetime.now()
        self._statut_rendez_vous = statut_rendez_vous

    # -------------------------------------------------------------------------
    # code_rendez_vous
    # -------------------------------------------------------------------------
    @property
    def code_rendez_vous(self):
        return self._code_rendez_vous

    @code_rendez_vous.setter
    def code_rendez_vous(self, value):
        self._code_rendez_vous = value

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
    # code_personnel
    # -------------------------------------------------------------------------
    @property
    def code_personnel(self):
        return self._code_personnel

    @code_personnel.setter
    def code_personnel(self, value):
        self._code_personnel = value

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
    # date_rendez_vous
    # -------------------------------------------------------------------------
    @property
    def date_rendez_vous(self):
        return self._date_rendez_vous

    @date_rendez_vous.setter
    def date_rendez_vous(self, value):
        self._date_rendez_vous = value

    # -------------------------------------------------------------------------
    # statut_rendez_vous
    # -------------------------------------------------------------------------
    @property
    def statut_rendez_vous(self):
        return self._statut_rendez_vous

    @statut_rendez_vous.setter
    def statut_rendez_vous(self, value):
        self._statut_rendez_vous = value