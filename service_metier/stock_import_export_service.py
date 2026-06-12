"""
stock_import_export_service.py
-------------------------------
Service centralisé pour l'import/export des données stock :
  - Produits (catalogue)
  - Lots de stock / panier_facture_four (avec date_expiration pour FEFO)
  - Factures fournisseur (export uniquement)

Ordre d'import obligatoire avant de pouvoir prescrire :
  1. produits          (catalogue — aucune dépendance)
  2. fournisseurs      (via fournisseur_service — aucune dépendance)
  3. facture_fournisseur (dépend de fournisseurs)
  4. lots de stock     (dépend de produits + facture_fournisseur, alimente FEFO)
  5. prescriptions     (dépend des lots via FEFO — géré par acte_import_export_service)
"""

import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from data.doa_produits import ProduitDAO
from data.dao_fournisseur import FournisseurDAO
from data.dao_factureFournisseur import FactureFournisseurDAO
from data.dao_panier_facture_fourni import PanierFactureFourniDAO
from models.modele_produits import Produit
from models.modele_factureFournisseur import FactureFournisseur
from models.modele_panier_fourni import PanierFactureFourni

logger = logging.getLogger(__name__)


# ============================================================================
# HELPERS PRIVÉS
# ============================================================================

def _str(val, default: str = '') -> str:
    if val is None or str(val).strip() in ('', 'nan', 'None'):
        return default
    return str(val).strip()


def _float(val, default: float = 0.0) -> float:
    try:
        return float(val) if val not in ('', None) else default
    except (ValueError, TypeError):
        return default


def _int(val, default: int = 0) -> int:
    try:
        return int(float(val)) if val not in ('', None) else default
    except (ValueError, TypeError):
        return default


def _parse_date(val) -> Optional[datetime]:
    if isinstance(val, datetime):
        return val
    s = str(val).strip() if val is not None else ''
    if s in ('', 'nan', 'None'):
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _lire_fichier(chemin: str, format_fichier: str) -> 'pd.DataFrame':
    if format_fichier == "excel":
        return pd.read_excel(chemin)
    return pd.read_csv(chemin, sep=None, engine='python', encoding="utf-8-sig")


def _date_str(val) -> str:
    if val is None:
        return ''
    if hasattr(val, 'strftime'):
        return val.strftime('%Y-%m-%d')
    return str(val)


def _resultat(succes: int, entite: str, erreurs: List[str]) -> Tuple[bool, str]:
    """Formate le résultat d'un import avec compteur et liste d'erreurs."""
    if succes == 0:
        msg = f"Aucun(e) {entite} importé(e)."
        if erreurs:
            msg += "\nErreurs :\n" + "\n".join(erreurs[:5])
        return False, msg
    msg = f"{succes} {entite}(s) importé(s) avec succès."
    if erreurs:
        msg += f"\n{len(erreurs)} ligne(s) ignorée(s) :\n"
        msg += "\n".join(e[:120] for e in erreurs[:3])
        if len(erreurs) > 3:
            msg += f"\n... et {len(erreurs) - 3} autre(s)."
        return True, msg   # succès partiel → True pour que la vue recharge
    return True, msg


# ============================================================================
# SERVICE
# ============================================================================

class StockImportExportService:
    """
    Service métier pour l'import/export des produits et des lots de stock.
    Utilise les DAOs existants — pas de SQL direct.
    """

    def __init__(self):
        self.produit_dao  = ProduitDAO()
        self.fournisseur_dao = FournisseurDAO()
        self.facture_dao  = FactureFournisseurDAO()
        self.panier_dao   = PanierFactureFourniDAO()

    # =========================================================================
    # PRODUITS — export
    # =========================================================================

    def export_produits(self, chemin: str, format_fichier: str) -> Tuple[bool, str]:
        """Exporte tout le catalogue produits en Excel ou CSV."""
        try:
            produits = self.produit_dao.lister_tous()
            if not produits:
                return False, "Aucun produit à exporter."
            data = [
                {
                    'code_produit':         p.get_code_produit(),
                    'libelle':              p.get_libelle(),
                    'type':                 p.get_type(),
                    'prix_achat_unitaire':  p.get_prix_achat_unitaire(),
                    'prix_vente_unitaire':  p.get_prix_vente_unitaire(),
                }
                for p in produits
            ]
            df = pd.DataFrame(data)
            if format_fichier == "excel":
                df.to_excel(chemin, index=False)
            else:
                df.to_csv(chemin, index=False, encoding="utf-8-sig")
            return True, f"{len(data)} produit(s) exporté(s) → {chemin}"
        except Exception as e:
            logger.error("Erreur export produits: %s", e, exc_info=True)
            return False, f"Erreur export produits : {e}"

    # =========================================================================
    # PRODUITS — import
    # =========================================================================

    def import_produits(self, chemin: str, format_fichier: str) -> Tuple[bool, str]:
        """
        Importe des produits depuis CSV/Excel.

        Colonnes attendues :
          libelle              (obligatoire)
          type                 (obligatoire : liquide / pommade / comprime)
          prix_achat_unitaire  (obligatoire, > 0)
          prix_vente_unitaire  (obligatoire, >= prix_achat)

        code_produit est auto-généré (L0001, P0001, C0001…).
        Les lignes déjà présentes ne sont pas dupliquées (libelle + type = clé logique).
        """
        try:
            df = _lire_fichier(chemin, format_fichier)
            if df.empty:
                return False, "Fichier vide."
            df.columns = [c.strip().lower() for c in df.columns]
            df = df.fillna("")
        except Exception as e:
            return False, f"Erreur lecture fichier : {e}"

        succes  = 0
        erreurs = []
        TYPES_VALIDES = ('liquide', 'pommade', 'comprime')

        for idx, row in df.iterrows():
            ligne = idx + 2
            try:
                libelle      = _str(row.get('libelle'))
                type_p       = _str(row.get('type')).lower()
                prix_achat   = _float(row.get('prix_achat_unitaire'))
                prix_vente   = _float(row.get('prix_vente_unitaire'))

                if not libelle:
                    erreurs.append(f"Ligne {ligne} : colonne 'libelle' vide")
                    continue
                if type_p not in TYPES_VALIDES:
                    erreurs.append(
                        f"Ligne {ligne} : type '{type_p}' invalide "
                        f"(attendu : {'/'.join(TYPES_VALIDES)})"
                    )
                    continue
                if prix_achat <= 0:
                    erreurs.append(f"Ligne {ligne} : prix_achat_unitaire invalide ({prix_achat})")
                    continue
                if prix_vente <= 0:
                    erreurs.append(f"Ligne {ligne} : prix_vente_unitaire invalide ({prix_vente})")
                    continue
                if prix_vente < prix_achat:
                    erreurs.append(
                        f"Ligne {ligne} : prix_vente ({prix_vente}) < prix_achat ({prix_achat})"
                    )
                    continue

                produit = Produit(
                    code_produit        = None,
                    libelle             = libelle,
                    type_produit        = type_p,
                    prix_achat_unitaire = prix_achat,
                    prix_vente_unitaire = prix_vente,
                )
                if self.produit_dao.ajouter(produit):
                    succes += 1
                else:
                    erreurs.append(f"Ligne {ligne} : échec insertion (produit existant ?)")
            except Exception as e:
                erreurs.append(f"Ligne {ligne} : {str(e)[:80]}")

        return _resultat(succes, "produit", erreurs)

    # =========================================================================
    # LOTS DE STOCK — export
    # =========================================================================

    def export_lots_stock(self, chemin: str, format_fichier: str,
                          code_session: str) -> Tuple[bool, str]:
        """Exporte tous les lots de stock de la session (panier_facture_four)."""
        try:
            lots = self.panier_dao.lister_par_session(code_session)
            if not lots:
                return False, "Aucun lot de stock à exporter pour cette session."
            data = [
                {
                    'code_facture_four': lot.code_facture_four,
                    'code_produit':      lot.code_produit,
                    'designation':       lot.designation,
                    'quantite_four':     lot.quantite_four,
                    'prix_unitaire':     lot.prix_unitaire,
                    'date_expiration':   _date_str(lot.date_expiration),
                }
                for lot in lots
            ]
            df = pd.DataFrame(data)
            if format_fichier == "excel":
                df.to_excel(chemin, index=False)
            else:
                df.to_csv(chemin, index=False, encoding="utf-8-sig")
            return True, f"{len(data)} lot(s) exporté(s) → {chemin}"
        except Exception as e:
            logger.error("Erreur export lots: %s", e, exc_info=True)
            return False, f"Erreur export lots : {e}"

    # =========================================================================
    # LOTS DE STOCK — import
    # =========================================================================

    def import_lots_stock(self, chemin: str, format_fichier: str,
                          code_session: str) -> Tuple[bool, str]:
        """
        Importe des lots de stock depuis CSV/Excel.

        Colonnes obligatoires :
          code_produit      → doit exister dans la table produits
          quantite_four     → quantité reçue du lot (> 0)
          prix_unitaire     → prix d'achat unitaire du lot
          date_expiration   → DATE OBLIGATOIRE pour le FEFO (format AAAA-MM-JJ)

        Colonnes optionnelles :
          designation       → libellé du lot (auto-rempli depuis produits si absent)
          code_facture_four → si fourni, le lot est rattaché à cette facture existante
          code_fournisseur  → si fourni (sans code_facture_four), une facture est
                              auto-créée pour ce fournisseur (une par import par fournisseur)

        Si ni code_facture_four ni code_fournisseur → erreur sur la ligne.
        """
        try:
            df = _lire_fichier(chemin, format_fichier)
            if df.empty:
                return False, "Fichier vide."
            df.columns = [c.strip().lower() for c in df.columns]
            df = df.fillna("")
        except Exception as e:
            return False, f"Erreur lecture fichier : {e}"

        # Cache factures auto-créées par fournisseur (une par fournisseur unique)
        factures_auto: Dict[str, str] = {}

        succes  = 0
        erreurs = []

        for idx, row in df.iterrows():
            ligne = idx + 2
            try:
                code_produit     = _str(row.get('code_produit'))
                quantite         = _int(row.get('quantite_four', row.get('quantite', 0)))
                prix_unitaire    = _float(row.get('prix_unitaire', row.get('prix', 0)))
                date_exp         = _parse_date(_str(row.get('date_expiration')))
                designation      = _str(row.get('designation'))
                code_facture     = _str(row.get('code_facture_four'))
                code_fournisseur = _str(row.get('code_fournisseur'))

                # --- Validations ---
                if not code_produit:
                    erreurs.append(f"Ligne {ligne} : 'code_produit' vide")
                    continue
                if quantite <= 0:
                    erreurs.append(f"Ligne {ligne} : 'quantite_four' invalide ({quantite})")
                    continue
                if date_exp is None:
                    erreurs.append(
                        f"Ligne {ligne} : 'date_expiration' invalide ou vide "
                        f"(obligatoire pour le FEFO)"
                    )
                    continue

                # --- Résoudre code_facture_four ---
                if not code_facture:
                    if not code_fournisseur:
                        erreurs.append(
                            f"Ligne {ligne} : 'code_facture_four' ou 'code_fournisseur' "
                            f"requis pour rattacher le lot"
                        )
                        continue
                    # Auto-créer une facture pour ce fournisseur (une seule par import)
                    if code_fournisseur not in factures_auto:
                        fc = FactureFournisseur(
                            code_facture_four = None,
                            montant_total     = 0.0,
                            mode_payement     = 'especes',
                            telephone         = '000000000',
                            date_facture_four = datetime.now(),
                            code_fournisseur  = code_fournisseur,
                            code_session      = code_session,
                        )
                        if self.facture_dao.creer(fc):
                            factures_auto[code_fournisseur] = fc.code_facture_four
                        else:
                            erreurs.append(
                                f"Ligne {ligne} : impossible de créer la facture "
                                f"pour le fournisseur '{code_fournisseur}'"
                            )
                            continue
                    code_facture = factures_auto[code_fournisseur]

                # --- Auto-remplir désignation depuis produits si absente ---
                if not designation:
                    p = self.produit_dao.obtenir_par_code(code_produit)
                    if p:
                        designation = p.get_libelle()
                    else:
                        erreurs.append(
                            f"Ligne {ligne} : produit '{code_produit}' introuvable dans le catalogue"
                        )
                        continue

                # --- Auto-remplir prix_unitaire depuis produits si absent ---
                if prix_unitaire <= 0:
                    prix_unitaire = self.produit_dao.obtenir_prix_achat(code_produit) or 0.0

                # --- Insérer le lot via PanierFactureFourniDAO ---
                panier = PanierFactureFourni(
                    code_panier_four  = None,
                    designation       = designation,
                    quantite_four     = quantite,
                    prix_unitaire     = prix_unitaire,
                    date_expiration   = date_exp,
                    code_produit      = code_produit,
                    code_facture_four = code_facture,
                    code_session      = code_session,
                )
                if self.panier_dao.ajouter(panier):
                    succes += 1
                else:
                    erreurs.append(
                        f"Ligne {ligne} : échec insertion lot "
                        f"(produit '{code_produit}', facture '{code_facture}')"
                    )
            except Exception as e:
                erreurs.append(f"Ligne {ligne} : {str(e)[:80]}")

        return _resultat(succes, "lot de stock", erreurs)

    # =========================================================================
    # FACTURES FOURNISSEUR — export (lecture seule)
    # =========================================================================

    def export_factures_fournisseur(self, chemin: str, format_fichier: str,
                                    code_session: str) -> Tuple[bool, str]:
        """Exporte les factures fournisseur de la session courante."""
        try:
            factures = self.facture_dao.lister_par_session(code_session)
            if not factures:
                return False, "Aucune facture fournisseur à exporter."
            data = [
                {
                    'code_facture_four':  f.code_facture_four,
                    'code_fournisseur':   f.code_fournisseur,
                    'montant_total':      f.montant_total,
                    'mode_payement':      f.mode_payement,
                    'telephone':          f.telephone,
                    'date_facture_four':  _date_str(f.date_facture_four),
                }
                for f in factures
            ]
            df = pd.DataFrame(data)
            if format_fichier == "excel":
                df.to_excel(chemin, index=False)
            else:
                df.to_csv(chemin, index=False, encoding="utf-8-sig")
            return True, f"{len(data)} facture(s) exportée(s) → {chemin}"
        except Exception as e:
            logger.error("Erreur export factures fournisseur: %s", e, exc_info=True)
            return False, f"Erreur export factures : {e}"
