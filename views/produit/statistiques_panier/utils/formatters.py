"""
Utilitaires de formatage pour le module statistiques.
Responsabilité : Fonctions de formatage et conversion.
Pattern : Utility Functions.
"""


class Formatters:
    """Classe contenant les fonctions de formatage."""
    
    @staticmethod
    def formater_montant(montant: float) -> str:
        """
        Formate un montant en GNF avec séparateurs de milliers.
        
        Args:
            montant: Montant à formater
        
        Returns:
            str: Montant formaté (ex: "1 250 000 GNF")
        
        Examples:
            >>> Formatters.formater_montant(1250000)
            '1 250 000 GNF'
            >>> Formatters.formater_montant(0)
            '0 GNF'
        """
        try:
            montant_int = int(montant)
            montant_str = f"{montant_int:,}".replace(",", " ")
            return f"{montant_str} GNF"
        except (ValueError, TypeError):
            return "0 GNF"
    
    @staticmethod
    def formater_quantite(quantite: int, unite: str = "unités") -> str:
        """
        Formate une quantité avec son unité.
        
        Args:
            quantite: Quantité à formater
            unite: Unité (par défaut "unités")
        
        Returns:
            str: Quantité formatée (ex: "100 unités")
        
        Examples:
            >>> Formatters.formater_quantite(100)
            '100 unités'
            >>> Formatters.formater_quantite(1, "unité")
            '1 unité'
        """
        try:
            return f"{int(quantite)} {unite}"
        except (ValueError, TypeError):
            return f"0 {unite}"
    
    @staticmethod
    def formater_pourcentage(pourcentage: int) -> str:
        """
        Formate un pourcentage.
        
        Args:
            pourcentage: Pourcentage à formater
        
        Returns:
            str: Pourcentage formaté (ex: "50%")
        
        Examples:
            >>> Formatters.formater_pourcentage(50)
            '50%'
            >>> Formatters.formater_pourcentage(0)
            '0%'
        """
        try:
            return f"{int(pourcentage)}%"
        except (ValueError, TypeError):
            return "0%"
    
    @staticmethod
    def normaliser_type_produit(type_produit: str) -> str:
        """
        Normalise le type de produit (première lettre en majuscule).
        
        Args:
            type_produit: Type de produit
        
        Returns:
            str: Type normalisé
        
        Examples:
            >>> Formatters.normaliser_type_produit("liquide")
            'Liquide'
            >>> Formatters.normaliser_type_produit("POMMADE")
            'Pommade'
        """
        try:
            return type_produit.strip().capitalize()
        except AttributeError:
            return "Inconnu"
    
    @staticmethod
    def tronquer_texte(texte: str, longueur_max: int = 50) -> str:
        """
        Tronque un texte s'il dépasse une longueur maximale.
        
        Args:
            texte: Texte à tronquer
            longueur_max: Longueur maximale
        
        Returns:
            str: Texte tronqué avec "..." si nécessaire
        
        Examples:
            >>> Formatters.tronquer_texte("Paracétamol 500mg", 10)
            'Paracéta...'
            >>> Formatters.tronquer_texte("Court", 10)
            'Court'
        """
        try:
            if len(texte) <= longueur_max:
                return texte
            return texte[:longueur_max - 3] + "..."
        except (TypeError, AttributeError):
            return ""
