# /modele/Cabinet.py

class Parametre:
    def __init__(self, nom_cabinet=None, logo=None, adresse=None, email=None, telephone=None, 
                 devise=None, fuseau_horaire=None, format_date=None, format_heure=None, notes=None, date_creation=None):
        self._nom_cabinet = nom_cabinet
        self._logo = logo
        self._adresse = adresse
        self._email = email
        self._telephone = telephone
        self._devise = devise
        self._fuseau_horaire = fuseau_horaire
        self._format_date = format_date
        self._format_heure = format_heure
        self._notes = notes
        self._date_creation = date_creation

    # --- Getters ---
    def get_nom_cabinet(self):
        return self._nom_cabinet

    def get_logo(self):
        return self._logo

    def get_adresse(self):
        return self._adresse
    
    def get_email(self):
        return self._email
    
    def get_telephone(self):
        return self._telephone
    
    def get_devise(self):
        return self._devise
    
    def get_fuseau_horaire(self):
        return self._fuseau_horaire
    
    def get_format_date(self):
        return self._format_date
    
    def get_format_heure(self):
        return self._format_heure
    
    def get_notes(self):
        return self._notes
    
    def get_date_creation(self):
        return self._date_creation

    # --- Setters ---
    def set_nom_cabinet(self, nom):
        self._nom_cabinet = nom

    def set_logo(self, logo_filename):
        self._logo = logo_filename
        
    def set_adresse(self, adresse):
        self._adresse = adresse
    
    def set_email(self, email):
        self._email = email
    
    def set_telephone(self, telephone):
        self._telephone = telephone
    
    def set_devise(self, devise):
        self._devise = devise
    
    def set_fuseau_horaire(self, fuseau_horaire):
        self._fuseau_horaire = fuseau_horaire
    
    def set_format_date(self, format_date):
        self._format_date = format_date
    
    def set_format_heure(self, format_heure):
        self._format_heure = format_heure
    
    def set_notes(self, notes):
        self._notes = notes
    
    def set_date_creation(self, date_creation):
        self._date_creation = date_creation

    def __str__(self):
        return (f"Cabinet: {self._nom_cabinet}, Email: {self._email}, Tel: {self._telephone}, "
                f"Adresse: {self._adresse}, Logo: {self._logo}, Devise: {self._devise}, "
                f"Fuseau: {self._fuseau_horaire}, Format date: {self._format_date}, "
                f"Format heure: {self._format_heure}")