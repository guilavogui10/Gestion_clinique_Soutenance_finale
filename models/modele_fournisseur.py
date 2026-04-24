class Fournisseur:
    """
    Modèle représentant un fournisseur.
    Utilise mail_fournisseur comme identifiant unique.
    Les accès aux attributs se font via les méthodes get_ et set_.
    """
    
    def __init__(self, mail_fournisseur, nom, telephone, adresse):
        # Attributs encapsulés
        self._mail_fournisseur = mail_fournisseur  
        self._nom = nom
        self._telephone = telephone
        self._adresse = adresse

    # --- Getters (Accesseurs) ---

    def get_mail_fournisseur(self):
        return self._mail_fournisseur

    def get_nom(self):
        return self._nom

    def get_telephone(self):
        return self._telephone

    def get_adresse(self):
        return self._adresse

    # --- Setters (Mutateurs) ---

    def set_mail_fournisseur(self, nouveau_mail):
        if nouveau_mail:
            self._mail_fournisseur = nouveau_mail
        else:
            raise ValueError("L'email du fournisseur ne peut pas être vide.")

    def set_nom(self, nouveau_nom):
        self._nom = nouveau_nom

    def set_telephone(self, nouveau_telephone):
        self._telephone = nouveau_telephone

    def set_adresse(self, nouvelle_adresse):
        self._adresse = nouvelle_adresse

    # --- Méthode utilitaire ---
    def __str__(self):
        return (f"Fournisseur: {self._nom}, Email: {self._mail_fournisseur}, "
                f"Tél: {self._telephone}, Adresse: {self._adresse}")

    def to_dict(self):
        return {
            "mail_fournisseur": self._mail_fournisseur,
            "nom": self._nom,
            "telephone": self._telephone,
            "adresse": self._adresse
    }
