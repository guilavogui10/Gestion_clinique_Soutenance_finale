from datetime import datetime

class Consultation:
    def __init__(self, code=None, diagnostique=None,
                 frais_consultation=0.0, statut_facture="attente payement",
                 date_consultation=None, code_visite=None, code_session=None, code_personne=None):
        self._code                = code
        self._diagnostique        = diagnostique
        self._frais_consultation  = frais_consultation
        self._statut_facture      = statut_facture
        self._date_consultation   = date_consultation or datetime.now()
        self._code_visite         = code_visite
        self._code_session        = code_session
        self._code_personne       = code_personne

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, value):
        self._code = value

    @property
    def diagnostique(self):
        return self._diagnostique

    @diagnostique.setter
    def diagnostique(self, value):
        self._diagnostique = value

    @property
    def frais_consultation(self):
        return self._frais_consultation

    @frais_consultation.setter
    def frais_consultation(self, value):
        self._frais_consultation = value

    @property
    def statut_facture(self):
        return self._statut_facture

    @statut_facture.setter
    def statut_facture(self, value):
        self._statut_facture = value

    @property
    def date_consultation(self):
        return self._date_consultation

    @date_consultation.setter
    def date_consultation(self, value):
        self._date_consultation = value

    @property
    def code_visite(self):
        return self._code_visite

    @code_visite.setter
    def code_visite(self, value):
        self._code_visite = value

    @property
    def code_session(self):
        return self._code_session

    @code_session.setter
    def code_session(self, value):
        self._code_session = value

    @property
    def code_personne(self):
        return self._code_personne

    @code_personne.setter
    def code_personne(self, value):
        self._code_personne = value
    
    def to_dict(self):
        """Convertit l'objet Consultation en dictionnaire"""
        return {
            'code': self._code,
            'diagnostique': self._diagnostique,
            'frais_consultation': self._frais_consultation,
            'statut_facture': self._statut_facture,
            'date_consultation': self._date_consultation,
            'code_visite': self._code_visite,
            'code_session': self._code_session,
            'code_personnel': self._code_personne
        }
