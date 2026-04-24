
class RendezVous:
    def __init__(self, code_rendez_vous: str, code_visite: str, code_personnel: str,
                 code_session: str, date_rendez_vous, statut_rendez_vous: str = None):
        
        self._code_rendez_vous = code_rendez_vous
        self._code_visite = code_visite
        self._code_personnel = code_personnel
        self._code_session = code_session
        self._date_rendez_vous = date_rendez_vous
        
        # Statut du rendez-vous : "en cours" par défaut à la création
        # Valeurs possibles : "en cours", "effectué", "annulé", "reporté"
        self._statut_rendez_vous = statut_rendez_vous if statut_rendez_vous else "en cours"
    
    # =========================================================================
    # GETTERS
    # =========================================================================
    
    def get_code_rendez_vous(self):
        return self._code_rendez_vous
    
    def get_code_visite(self):
        return self._code_visite
    
    def get_code_personnel(self):
        return self._code_personnel
    
    def get_code_session(self):
        return self._code_session
    
    def get_date_rendez_vous(self):
        return self._date_rendez_vous
    
    def get_statut_rendez_vous(self):
        return self._statut_rendez_vous
    
    # =========================================================================
    # SETTERS
    # =========================================================================
    
    def set_code_rendez_vous(self, code_rendez_vous):
        self._code_rendez_vous = code_rendez_vous
    
    def set_code_visite(self, code_visite):
        self._code_visite = code_visite
    
    def set_code_personnel(self, code_personnel):
        self._code_personnel = code_personnel
    
    def set_code_session(self, code_session):
        self._code_session = code_session
    
    def set_date_rendez_vous(self, date_rendez_vous):
        self._date_rendez_vous = date_rendez_vous
    
    def set_statut_rendez_vous(self, statut_rendez_vous):
        self._statut_rendez_vous = statut_rendez_vous
