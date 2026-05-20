# /parametre/config_cabinet.py

from parametre.dao_param import CabinetDAO

class ConfigCabinet:
    """
    Singleton pour accéder aux paramètres du cabinet partout dans l'application.
    Évite d'avoir des valeurs en dur dans le code.
    
    Usage:
        from parametre.config_cabinet import config_cabinet
        
        devise = config_cabinet.get_devise()
        format_date = config_cabinet.get_format_date()
    """
    
    _instance = None
    _cache = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigCabinet, cls).__new__(cls)
            cls._instance.dao = CabinetDAO()
        return cls._instance
    
    def _charger_config(self):
        """Charge la configuration depuis la base de données."""
        if self._cache is None:
            info = self.dao.get_info_cabinet()
            if info:
                self._cache = {
                    'nom_cabinet': info.get('nom_cabinet', 'Cabinet Ophtalmologique'),
                    'logo': info.get('logo', ''),
                    'adresse': info.get('adresse', ''),
                    'devise': info.get('devise', 'GNF'),
                    'fuseau_horaire': info.get('fuseau_horaire', '(GMT) Afrique/Conakry'),
                    'format_date': info.get('format_date', 'DD/MM/YYYY')
                }
            else:
                # Valeurs par défaut si rien en base
                self._cache = {
                    'nom_cabinet': 'Cabinet Ophtalmologique',
                    'logo': '',
                    'adresse': '',
                    'devise': 'GNF',
                    'fuseau_horaire': '(GMT) Afrique/Conakry',
                    'format_date': 'DD/MM/YYYY'
                }
        return self._cache
    
    def rafraichir(self):
        """Force le rechargement de la configuration depuis la base."""
        self._cache = None
        return self._charger_config()
    
    def get_nom_cabinet(self):
        """Retourne le nom du cabinet."""
        config = self._charger_config()
        return config['nom_cabinet']
    
    def get_logo(self):
        """Retourne le nom du fichier logo."""
        config = self._charger_config()
        return config['logo']
    
    def get_adresse(self):
        """Retourne l'adresse du cabinet."""
        config = self._charger_config()
        return config['adresse']
    
    def get_devise(self):
        """
        Retourne la devise configurée (ex: 'GNF', 'EUR', 'USD').
        À utiliser partout au lieu d'écrire 'GNF' en dur.
        """
        config = self._charger_config()
        devise_complete = config['devise']
        # Extrait juste le code (ex: "GNF - Franc guinéen (GNF)" -> "GNF")
        if ' - ' in devise_complete:
            return devise_complete.split(' - ')[0]
        return devise_complete
    
    def get_devise_complete(self):
        """Retourne la devise avec son libellé complet."""
        config = self._charger_config()
        return config['devise']
    
    def get_symbole_devise(self):
        """
        Retourne le symbole de la devise (GNF, €, $).
        """
        devise = self.get_devise()
        symboles = {
            'GNF': 'GNF',
            'EUR': '€',
            'USD': '$',
            'XOF': 'GNF',
            'XAF': 'GNF'
        }
        return symboles.get(devise, devise)
    
    def get_fuseau_horaire(self):
        """Retourne le fuseau horaire configuré."""
        config = self._charger_config()
        return config['fuseau_horaire']
    
    def get_format_date(self):
        """
        Retourne le format de date configuré (ex: 'DD/MM/YYYY').
        À utiliser pour formater les dates partout dans l'application.
        """
        config = self._charger_config()
        return config['format_date']
    
    def formater_montant(self, montant):
        """
        Formate un montant avec la devise configurée.
        
        Args:
            montant: Le montant à formater (float ou int)
        
        Returns:
            str: Le montant formaté (ex: "10 000 GNF")
        """
        try:
            montant_float = float(montant)
            symbole = self.get_symbole_devise()
            
            # Format avec espaces pour les milliers
            montant_str = f"{montant_float:,.0f}".replace(",", " ")
            
            return f"{montant_str} {symbole}"
        except (ValueError, TypeError):
            return f"0 {self.get_symbole_devise()}"
    
    def formater_date(self, date_obj):
        """
        Formate une date selon le format configuré.
        
        Args:
            date_obj: Un objet date/datetime
        
        Returns:
            str: La date formatée selon le format configuré
        """
        if not date_obj:
            return ""
        
        format_config = self.get_format_date()
        
        try:
            if format_config == "DD/MM/YYYY":
                return date_obj.strftime("%d/%m/%Y")
            elif format_config == "MM/DD/YYYY":
                return date_obj.strftime("%m/%d/%Y")
            elif format_config == "YYYY-MM-DD":
                return date_obj.strftime("%Y-%m-%d")
            else:
                return date_obj.strftime("%d/%m/%Y")
        except Exception:
            return str(date_obj)
    
    def get_toutes_config(self):
        """Retourne toutes les configurations sous forme de dictionnaire."""
        return self._charger_config()


# Instance singleton globale à importer partout
config_cabinet = ConfigCabinet()
