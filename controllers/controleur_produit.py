import sys
import os
import logging
from typing import Dict, Optional, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service_metier.produit_service import ProduitService
from models.modele_produits import Produit


class ProduitControleur:

    def __init__(self):
        self.service = ProduitService()
        self.logger  = logging.getLogger(__name__)

    def valider_texte(self, texte, nom_champ, min_longueur=3):
        return self.service.valider_texte(texte, nom_champ, min_longueur)

    def valider_prix(self, prix, nom_champ):
        return self.service.valider_prix(prix, nom_champ)

    def valider_type(self, type_produit):
        return self.service.valider_type(type_produit)

    def valider_produit(self, produit):
        return self.service.valider_produit(produit)

    def creer_produit(self, produit):
        return self.service.creer_produit(produit)

    def modifier_produit(self, produit):
        return self.service.modifier_produit(produit)

    def supprimer_produit(self, code_produit):
        return self.service.supprimer_produit(code_produit)

    def obtenir_par_code(self, code_produit):
        return self.service.obtenir_par_code(code_produit)

    def lister_produits(self):
        return self.service.lister_produits()

    def lister_par_type(self, type_produit):
        return self.service.lister_par_type(type_produit)

    def rechercher_produit(self, critere):
        return self.service.rechercher_produit(critere)

    def obtenir_libelle_par_code(self, code_produit):
        return self.service.obtenir_libelle_par_code(code_produit)

    def obtenir_prix_achat_par_code(self, code_produit):
        return self.service.obtenir_prix_achat_par_code(code_produit)

    def actualiser_prix_achat(self, code_produit, nouveau_prix):
        return self.service.actualiser_prix_achat(code_produit, nouveau_prix)

    def get_cabinet_info(self):
        return self.service.get_cabinet_info()
