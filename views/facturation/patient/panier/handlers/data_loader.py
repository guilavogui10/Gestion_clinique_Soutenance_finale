"""
Handler pour le chargement des données.
Responsabilité : Chargement des fournisseurs et produits depuis les contrôleurs.
Pattern : Single Responsibility Principle (SRP).
"""

import qtawesome as qta


class DataLoader:
    """Gère le chargement des données depuis les contrôleurs."""
    
    def __init__(self, vert_principal: str):
        self.vert_principal = vert_principal
    
    def charger_fournisseurs(self, fournisseur_ctrl, combo_fournisseur, code_session):
        """
        Charge la liste des fournisseurs dans le combo.
        
        Args:
            fournisseur_ctrl: Contrôleur fournisseur
            combo_fournisseur: Widget QComboBox à remplir
            code_session: Code de la session active
        """
        print(f"[DataLoader] Chargement fournisseurs pour session={code_session}")
        
        if not fournisseur_ctrl:
            print("[DataLoader] ERREUR: fournisseur_ctrl est None")
            return
            
        try:
            fournisseurs = fournisseur_ctrl.lister_fournisseurs(code_session)
            print(f"[DataLoader] {len(fournisseurs)} fournisseurs récupérés")
            
            combo_fournisseur.clear()
            combo_fournisseur.addItem(
                qta.icon("fa5s.truck", color=self.vert_principal),
                "  Sélectionner un fournisseur...",
                None
            )
            
            for f in fournisseurs:
                nom_entreprise = f.get('nom_entreprise', 'Entreprise inconnue')
                combo_fournisseur.addItem(
                    qta.icon("fa5s.user-tie", color=self.vert_principal),
                    f"  {nom_entreprise}",
                    f.get('email_fournisseur')
                )
            
            print(f"[DataLoader] Combo rempli avec {combo_fournisseur.count()} items")
            
        except Exception as e:
            print(f"[DataLoader] EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
    
    def charger_produits(self, produit_ctrl, combo_produit):
        """
        Charge la liste des produits dans le combo.
        
        Args:
            produit_ctrl: Contrôleur produit
            combo_produit: Widget QComboBox à remplir
        """
        print("[DataLoader] Chargement produits")
        
        if not produit_ctrl:
            print("[DataLoader] ERREUR: produit_ctrl est None")
            return
            
        try:
            produits = produit_ctrl.lister_produits()
            combo_produit.clear()
            combo_produit.addItem(
                qta.icon("fa5s.pills", color=self.vert_principal),
                "  Choisir un produit...",
                None
            )
            
            for produit in produits:
                libelle = produit.get_libelle() if hasattr(produit, 'get_libelle') else str(produit)
                type_prod = produit.get_type() if hasattr(produit, 'get_type') else ''
                code = produit.get_code_produit() if hasattr(produit, 'get_code_produit') else None
                
                combo_produit.addItem(
                    qta.icon("fa5s.capsules", color=self.vert_principal),
                    f"  {libelle} ({type_prod})",
                    code
                )
            
            print(f"[DataLoader] {combo_produit.count()} produits chargés")
            
        except Exception as e:
            print(f"[DataLoader] Erreur chargement produits: {e}")
