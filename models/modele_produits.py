# /modeles/produit.py
from datetime import datetime

class Produit:
    def __init__(self, code_produit: str, libelle: str, type_produit: str, prix_achat_unitaire: float, prix_vente_unitaire: float):
        self._code_produit = code_produit
        self._libelle = libelle
        self._type = type_produit
        self._prix_achat_unitaire = prix_achat_unitaire
        self._prix_vente_unitaire = prix_vente_unitaire

    # --- Getters ---
    def get_code_produit(self):
        return self._code_produit

    def get_libelle(self):
        return self._libelle

    def get_type(self):
        return self._type

    def get_prix_achat_unitaire(self):
        return self._prix_achat_unitaire

    def get_prix_vente_unitaire(self):
        return self._prix_vente_unitaire


    # --- Setters ---
    def set_code_produit(self, code_produit):
        self._code_produit = code_produit

    def set_libelle(self, libelle):
        self._libelle = libelle

    def set_type(self, type_produit):
        self._type = type_produit

    def set_prix_achat_unitaire(self, prix):
        self._prix_achat_unitaire = prix

    def set_prix_vente_unitaire(self, prix):
        self._prix_vente_unitaire = prix
