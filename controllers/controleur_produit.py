import sys
import os
import logging
import re
from typing import Dict, Optional, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.doa_produits import ProduitDAO
from models.modele_produits import Produit
from parametre.dao_param import CabinetDAO


class ProduitControleur:
    """
    Controleur MVC pour la gestion des produits.
    Fait le lien entre la vue et le DAO.
    Contient toute la logique metier et la validation des donnees.
    """

    TYPES_VALIDES = ['liquide', 'pommade', 'comprime']

    def __init__(self):
        self.dao        = ProduitDAO()
        self.cabinetdao = CabinetDAO()
        self.logger     = logging.getLogger(__name__)

    # =========================================================================
    # METHODES DE VALIDATION (LOGIQUE METIER)
    # =========================================================================

    def valider_texte(self, texte: str, nom_champ: str, min_longueur: int = 3) -> tuple:
        """
        Valide qu un champ texte est non vide et sans caracteres interdits.
        Accepte les accents et caracteres francais (é, è, ê, à, ù, ç, etc.).
        """
        if not texte or texte.strip() == "":
            return False, f"Le champ {nom_champ} est obligatoire"

        if len(texte.strip()) < min_longueur:
            return False, f"Le {nom_champ} doit contenir au moins {min_longueur} caracteres"

        # Autorise lettres (y compris accentuees), chiffres, espaces, tirets, points
        # Refuse uniquement les caracteres vraiment dangereux ou non medicaux
        if re.search(r'[<>{}[\]\\|`~@#$%^*+=]', texte):
            return False, f"Le {nom_champ} contient des caracteres speciaux interdits"

        return True, ""

    def valider_prix(self, prix, nom_champ: str) -> tuple:
        """Valide qu un prix est un nombre positif strictement superieur a 0."""
        try:
            prix_float = float(prix)
            if prix_float <= 0:
                return False, f"Le {nom_champ} doit etre superieur a 0"
            return True, ""
        except Exception:
            return False, f"Le {nom_champ} doit etre un nombre valide"

    def valider_type(self, type_produit: str) -> tuple:
        """Valide que le type est parmi les valeurs autorisees."""
        if not type_produit or type_produit.strip() == "":
            return False, "Le type de produit est obligatoire"
        if type_produit.lower() not in self.TYPES_VALIDES:
            return False, f"Le type doit etre : {', '.join(self.TYPES_VALIDES)}"
        return True, ""

    def valider_produit(self, produit: Produit) -> tuple:
        """
        Regroupe toutes les validations communes a la creation et a la modification.
        Evite la duplication de code entre creer et modifier.
        """
        valide, msg = self.valider_texte(produit.get_libelle(), "libelle")
        if not valide:
            return False, msg

        valide, msg = self.valider_type(produit.get_type())
        if not valide:
            return False, msg

        valide, msg = self.valider_prix(produit.get_prix_achat_unitaire(), "prix achat unitaire")
        if not valide:
            return False, msg

        valide, msg = self.valider_prix(produit.get_prix_vente_unitaire(), "prix vente unitaire")
        if not valide:
            return False, msg

        # Prix vente doit etre superieur ou egal au prix achat
        try:
            if float(produit.get_prix_vente_unitaire()) < float(produit.get_prix_achat_unitaire()):
                return False, "Le prix de vente ne peut pas etre inferieur au prix d achat"
        except Exception:
            pass

        return True, ""

    def _nettoyer_produit(self, produit: Produit) -> None:
        """Nettoie les champs texte et normalise le type en minuscules."""
        produit.set_libelle(produit.get_libelle().strip())
        produit.set_type(produit.get_type().strip().lower())

    # =========================================================================
    # METHODES CRUD
    # =========================================================================

    def creer_produit(self, produit: Produit) -> tuple:
        """Valide et cree un nouveau produit dans le catalogue."""
        valide, msg = self.valider_produit(produit)
        if not valide:
            return False, msg

        self._nettoyer_produit(produit)

        if self.dao.ajouter(produit):
            self.logger.info(f"Produit {produit.get_code_produit()} cree : {produit.get_libelle()}")
            return True, "Produit cree avec succes"

        return False, "Erreur lors de la creation du produit"

    def modifier_produit(self, produit: Produit) -> tuple:
        """Valide et met a jour un produit existant."""
        if not produit.get_code_produit():
            return False, "Code produit invalide"

        valide, msg = self.valider_produit(produit)
        if not valide:
            return False, msg

        self._nettoyer_produit(produit)

        if self.dao.modifier(produit):
            self.logger.info(f"Produit {produit.get_code_produit()} modifie")
            return True, "Produit modifie avec succes"

        return False, "Erreur lors de la modification du produit"

    def supprimer_produit(self, code_produit: str) -> tuple:
        """Supprime un produit du catalogue par son code."""
        if not code_produit:
            return False, "Code produit invalide"

        if self.dao.supprimer(code_produit):
            self.logger.info(f"Produit {code_produit} supprime")
            return True, "Produit supprime avec succes"

        return False, "Erreur lors de la suppression du produit"

    # =========================================================================
    # METHODES DE RECUPERATION
    # =========================================================================

    def obtenir_par_code(self, code_produit: str):
        """Retourne un produit par son code."""
        return self.dao.obtenir_par_code(code_produit)

    def lister_produits(self) -> list:
        """Retourne tous les produits du catalogue."""
        return self.dao.lister_tous()

    def lister_par_type(self, type_produit: str) -> list:
        """Retourne les produits d un type specifique."""
        return self.dao.lister_par_type(type_produit)

    def rechercher_produit(self, critere: str) -> list:
        """Recherche des produits par code, libelle ou type."""
        return self.dao.rechercher_par_critere(critere)
    
    def obtenir_libelle_par_code(self, code_produit: str) -> str:
        """
        Retourne le libelle d un produit par son code.
        Utilise pour remplir automatiquement le champ designation
        dans le panier des qu un code_produit est selectionne.
        Retourne une chaine vide si le produit n existe pas.
        """
        produit = self.dao.obtenir_par_code(code_produit)
        return produit.get_libelle() if produit else ""
    
    def obtenir_prix_achat_par_code(self, code_produit: str) -> float:
        """
        Retourne le prix d'achat unitaire d'un produit par son code.
        Utilise pour auto-remplir le champ prix dans le panier.
        Retourne 0.0 si le produit n'existe pas.
        
        Args:
            code_produit: Code du produit
        
        Returns:
            float: Prix d'achat unitaire ou 0.0
        """
        prix = self.dao.obtenir_prix_achat(code_produit)
        return prix if prix is not None else 0.0
    
    def actualiser_prix_achat(self, code_produit: str, nouveau_prix: float) -> Tuple[bool, str]:
        """
        Valide et met a jour le prix d'achat d'un produit.
        Appele apres validation du panier si le prix fournisseur est different.
        
        Args:
            code_produit: Code du produit
            nouveau_prix: Nouveau prix d'achat unitaire
        
        Returns:
            Tuple[bool, str]: (succes, message)
        """
        # Validation du prix
        valide, msg = self.valider_prix(nouveau_prix, "prix achat unitaire")
        if not valide:
            return False, msg
        
        # Mise a jour
        if self.dao.mettre_a_jour_prix_achat(code_produit, nouveau_prix):
            self.logger.info(f"Prix achat produit {code_produit} actualise: {nouveau_prix}")
            return True, "Prix d'achat mis a jour avec succes"
        
        return False, "Erreur lors de la mise a jour du prix d'achat"

    # =========================================================================
    # INFORMATIONS CABINET
    # =========================================================================

    def get_cabinet_info(self) -> Dict[str, Optional[str]]:
        """Recupere les informations du cabinet medical."""
        try:
            info            = self.cabinetdao.get_info_cabinet() or {}
            nom_cabinet     = info.get("nom_cabinet", "Cabinet ophtalmologique")
            adresse_cabinet = info.get("adresse", "")
            logo_cabinet    = info.get("logo", None)

            final_logo = None
            if logo_cabinet:
                try:
                    base_dir  = os.path.dirname(os.path.dirname(__file__))
                    logo_path = os.path.join(base_dir, "connexion", "image", logo_cabinet)
                    if os.path.exists(logo_path) and os.path.isfile(logo_path):
                        final_logo = os.path.abspath(logo_path)
                except Exception as e:
                    self.logger.warning(f"Erreur chemin logo: {e}")

            return {
                "nom_cabinet":     nom_cabinet,
                "adresse_cabinet": adresse_cabinet,
                "logo_url":        final_logo
            }

        except Exception as e:
            self.logger.error(f"Erreur get_cabinet_info: {e}")
            return {
                "nom_cabinet":     "Cabinet ophtalmologique",
                "adresse_cabinet": "",
                "logo_url":        None
            }