# /modele/Cabinet.py

class Parametre:
    def __init__(self, nom_cabinet= None, logo= None, adresse=None):
        # Le Cabinet n'aura probablement qu'une seule instance (ID non nécessaire)
        self._nom_cabinet = nom_cabinet
        self._logo = logo         # Stocke le nom du fichier (ex: 'oeil.png')
        self._adresse = adresse

    # --- Getters ---
    def get_nom_cabinet(self):
        return self._nom_cabinet

    def get_logo(self):
        return self._logo

    def get_adresse(self):
        return self._adresse

    # --- Setters (Optionnels, si l'on permet la modification) ---
    def set_nom_cabinet(self, nom):
        self._nom_cabinet = nom

    def set_logo(self, logo_filename):
        self._logo = logo_filename
        
    def set_adresse(self, adresse):
        self._adresse = adresse

    def __str__(self):
        return f"Cabinet: {self._nom_cabinet}, Adresse: {self._adresse}, Logo: {self._logo}"