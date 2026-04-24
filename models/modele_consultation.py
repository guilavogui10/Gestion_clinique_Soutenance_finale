from datetime import datetime

class Consultation:
    def __init__(self, code=None, diagnostique=None, resultat_consultation=None,
                 examen="Non", chirurgie="Non", commandelunette="Non", prescription_produit="Non",
                 frais_consultation=0.0, statut_facture="attente payement", 
                 date_consultation=None, code_visite=None, code_session=None, code_personnel=None):
        self._code = code
        self._diagnostique = diagnostique
        self._resultat_consultation = resultat_consultation
        self._examen = examen
        self._chirurgie = chirurgie
        self._commandelunette = commandelunette
        self._prescription_produit = prescription_produit
        self._frais_consultation = frais_consultation
        self._statut_facture = statut_facture
        self._date_consultation = date_consultation or datetime.now()
        self._code_visite = code_visite
        self._code_session = code_session
        self._code_personnel = code_personnel

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
    def resultat_consultation(self):
        return self._resultat_consultation

    @resultat_consultation.setter
    def resultat_consultation(self, value):
        self._resultat_consultation = value

    @property
    def examen(self):
        return self._examen

    @examen.setter
    def examen(self, value):
        self._examen = value

    @property
    def chirurgie(self):
        return self._chirurgie

    @chirurgie.setter
    def chirurgie(self, value):
        self._chirurgie = value

    @property
    def commandelunette(self):
        return self._commandelunette

    @commandelunette.setter
    def commandelunette(self, value):
        self._commandelunette = value

    @property
    def prescription_produit(self):
        return self._prescription_produit

    @prescription_produit.setter
    def prescription_produit(self, value):
        self._prescription_produit = value

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
    def code_personnel(self):
        return self._code_personnel

    @code_personnel.setter
    def code_personnel(self, value):
        self._code_personnel = value
