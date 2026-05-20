
class Visite():
    def __init__(self, code_visite:str, code_patient:str, code_session:str, type_visite:str,
                  urgent:str,date_visite,statut_visite:str=None, statut_patient:str= None,
                  date_debut_consultation=None ):
        
        self._code_visite = code_visite
        self._code_patient= code_patient
        self._code_session = code_session
        self._type_visite= type_visite
        self._urgent= urgent
        self._date_visite= date_visite
        self._date_debut_consultation = date_debut_consultation
        
        # Statut de la visite : Toujours "en cours" à la création
        self._statut_visite = statut_visite if statut_visite else "en cours"
        
        # Statut du patient : Défini par le DAO selon la logique métier
        # Le modèle ne doit PAS contenir de logique métier
        self._statut_patient = statut_patient if statut_patient else "En attente"

    
    def get_code_visite(self):
        return self._code_visite
    def get_code_patient(self):
        return self._code_patient
    def get_code_session(self):
        return self._code_session
    def get_type_visite(self):
        return self._type_visite
    def get_statut_visite(self):
        return self._statut_visite
    def get_statut_patient(self):
        return self._statut_patient
    def get_urgent(self):
        return self._urgent
    def get_date_visite(self):
        return self._date_visite
    def get_date_debut_consultation(self):
        return self._date_debut_consultation
    
    # setters
    def set_code_visite(self, code_visite):
        self._code_visite = code_visite

    def set_code_patient(self, code_patient):
        self._code_patient = code_patient
        
    def set_code_session(self, code_session):
        self._code_session = code_session

    def set_type_visite(self, type_visite):
        self._type_visite= type_visite

    # Correction suggérée
    def set_statut_visite(self, statut_visite): # Ajout du 't'
        self._statut_visite = statut_visite

    def set_statut_patient(self, statut_patient): # Ajout du 't'
        self._statut_patient = statut_patient

    def set_urgent(self, urgent):
        self._urgent= urgent
    def set_date_visite(self, date_visite):
        self._date_visite= date_visite
    def set_date_debut_consultation(self, date_debut_consultation):
        self._date_debut_consultation = date_debut_consultation
    
    def to_dict(self):
        """Convertit l'objet Visite en dictionnaire"""
        return {
            'code_visite': self._code_visite,
            'code_patient': self._code_patient,
            'code_session': self._code_session,
            'type_visite': self._type_visite,
            'statut_visite': self._statut_visite,
            'statut_patient': self._statut_patient,
            'urgent': self._urgent,
            'date_visite': self._date_visite,
            'date_debut_consultation': self._date_debut_consultation,
            # Alias pour compatibilité
            'date': self._date_visite,
            'statut': self._statut_visite,
            'motif': self._type_visite
        }
        