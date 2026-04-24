class Patient:
    def __init__(self,code_patient: str,nom:str,prenom:str,telephone:str,
                 naissance,genre:str,profession:str,adresse:str
    ):
       # encapsultion des attributs 
        self._code_patient = code_patient
        self._nom = nom
        self._prenom = prenom
        self._telephone = telephone
        self._naissance = naissance
        self._genre = genre
        self._profession = profession
        self._adresse = adresse

    # Getters
    def get_code_patient(self):
        return self._code_patient

    def get_nom(self):
        return self._nom

    def get_prenom(self):
        return self._prenom

    def get_telephone(self):
        return self._telephone

    def get_naissance(self):
        return self._naissance

    def get_genre(self):
        return self._genre

    def get_profession(self):
        return self._profession

    def get_adresse(self):
        return self._adresse

    # Setters

    def set_code_patient(self, code_patient):
        self._code_patient = code_patient

    def set_nom(self, nom):
        self._nom = nom

    def set_prenom(self, prenom):
        self._prenom = prenom

    def set_telephone(self, telephone):
        self._telephone = telephone

    def set_naissance(self, naissance):
        self._naissance = naissance

    def set_genre(self, genre):
        self._genre = genre

    def set_profession(self, profession):
        self._profession = profession

    def set_adresse(self, adresse):
        self._adresse = adresse
    
    # --- Méthode utilitaire ---
    def __str__(self):
        return (f"Nom: {self._nom}, prenom: {self._prenom}, "
                f"Tél: {self._telephone},naissance: {self._naissance},"
                f"genre:{self._genre}, profession:{self._profession},"
                f"adresse: {self._adresse}"
                )

    # def to_dict(self):
    #     return {
    #         "nom": self._nom,
    #         "prenom": self._prenom,
    #         "telephone": self._telephone,
    #         "naissance": self._naissance,
    #         "genre": self._genre,
    #         "profession": self._profession,
    #         "adresse": self._adresse
    # }
