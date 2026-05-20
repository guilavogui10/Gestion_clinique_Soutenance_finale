class ModelePersonnel:
    def __init__(self, code, nom, prenom, adresse, date_naissance, contact, mail, fonction, photo_path=None, est_responsable=0):
        self.code = code
        self.nom = nom
        self.prenom = prenom
        self.adresse = adresse
        self.date_naissance = date_naissance
        self.contact = contact
        self.mail = mail
        self.fonction = fonction
        self.photo_path = photo_path
        self.est_responsable = est_responsable

    # Getters
    def get_code(self):
        return self.code
    
    def get_nom(self):
        return self.nom
    
    def get_prenom(self):
        return self.prenom
        
    def get_adresse(self):
        return self.adresse
    
    def get_date_naissance(self):
        return self.date_naissance
    
    def get_contact(self):
        return self.contact
        
    def get_mail(self):
        return self.mail
        
    def get_fonction(self):
        return self.fonction
        
    def get_photo_path(self):
        return self.photo_path

    def get_est_responsable(self):
        return self.est_responsable

    def set_est_responsable(self, val):
        self.est_responsable = val
        
    # Setters (si nécessaire, mais souvent on gère les attibuts directement dans le contrôleur)
    def set_code(self, code):
        self.code = code
        
    # Les autres setters peuvent être ajoutés si besoin.

    def to_dict(self):
        return {
            "code": self.code,
            "nom": self.nom,
            "prenom": self.prenom,
            "adresse": self.adresse,
            "date_naissance": self.date_naissance,
            "contact": self.contact,
            "mail": self.mail,
            "fonction": self.fonction,
            "photo_path": self.photo_path,
            "est_responsable": self.est_responsable,
        }
