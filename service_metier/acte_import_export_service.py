"""
acte_import_export_service.py
------------------------------
Service centralisé gérant l'export et l'import des 4 types d'actes médicaux :
  - Examens, Chirurgies, Lunettes (commandes), Prescriptions

Logique d'import (données historiques, statut termine direct) :
  Pour chaque ligne CSV/Excel, en UNE SEULE transaction :
    1. Récupère code_visite + code_session depuis la consultation  → ConsultationDAO
    2. INSERT acte_medical  (statut="termine", choix="maintenant") → ActeMedicalDAO
    3. INSERT acte_visite   (role="execution")                     → ActeVisiteDAO
    4. INSERT table spécifique                                     → DAO spécifique
    5. UPDATE visite.statut_patient → statut terminal             → Visitedao
"""

import logging
from datetime import datetime
from typing import List, Dict, Tuple

import pymysql

from core.connexion_db import DBConnection
from data.dao_acte_medicale import ActeMedicalDAO
from data.dao_acte_visite import ActeVisiteDAO
from data.dao_visite import Visitedao
from data.dao_consultation import ConsultationDAO
from data.dao_examen import ExamenDAO
from data.dao_chirurgie import ChirurgieDAO
from data.dao_commande_lunette import CommandeLunetteDAO
from data.dao_panier_prescription_produit import PrescriptionProduitDAO

logger = logging.getLogger(__name__)
DictCursor = pymysql.cursors.DictCursor


# ============================================================================
# HELPERS PURS (aucun SQL)
# ============================================================================

def _get_col(row, *cles) -> str:
    for k in cles:
        val = row.get(k, '')
        if val is not None and str(val).strip() not in ('', 'nan', 'None'):
            return str(val).strip()
    return ''


def _parse_date(val) -> datetime:
    if isinstance(val, datetime):
        return val
    if val is None or str(val).strip() in ('', 'nan', 'None'):
        return datetime.now()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(val), fmt)
        except ValueError:
            continue
    return datetime.now()


def _parse_float(val, default=0.0) -> float:
    try:
        return float(val) if val not in ('', None) else default
    except (ValueError, TypeError):
        return default


# ============================================================================
# STATUTS TERMINAUX PAR TYPE
# ============================================================================

_STATUT_TERMINAL = {
    "examen":       "Examen terminé",
    "chirurgie":    "Chirurgie terminée",
    "lunette":      "Lunette terminée",
    "prescription": "Pharmacie terminée",
}

# ============================================================================
# COLONNES D'EXPORT PAR TYPE
# ============================================================================

COLONNES_EXPORT = {
    "examen": [
        "code_examen", "code_consultation", "code_personnel",
        "libelle_examen", "frais_examen", "conclusion_medicale",
        "statut_facture", "date_examen"
    ],
    "chirurgie": [
        "code_chirurgie", "code_consultation", "code_personnel",
        "libelle_chirurgie", "frais_chirurgie", "compte_rendu",
        "statut_facture", "date_chirurgie"
    ],
    "lunette": [
        "code_lunette", "code_consultation", "code_personnel",
        "numero_cadre", "numero_verre", "prix",
        "statut_facture", "date_commande", "date_livraison"
    ],
    "prescription": [
        "code_prescription", "code_consultation", "code_produit",
        "designation", "quantite", "prix_applique", "date_expiration"
    ],
}


# ============================================================================
# EXPORT — délégation totale aux DAOs
# ============================================================================

_DAO_EXPORT = {
    "examen":       ExamenDAO,
    "chirurgie":    ChirurgieDAO,
    "lunette":      CommandeLunetteDAO,
    "prescription": PrescriptionProduitDAO,
}


def _lire_donnees_export(type_acte: str) -> List[Dict]:
    """Retourne toutes les données d'un type d'acte pour export/aperçu."""
    dao_cls = _DAO_EXPORT.get(type_acte)
    if not dao_cls:
        return []
    try:
        return dao_cls().lister_pour_export()
    except Exception as e:
        logger.error("Erreur _lire_donnees_export %s : %s", type_acte, e)
        return []


def obtenir_donnees_export(type_acte: str) -> List[Dict]:
    return _lire_donnees_export(type_acte)


def _exporter(type_acte: str, chemin: str, separateur: str = "excel") -> Tuple[bool, str]:
    import pandas as pd
    donnees = _lire_donnees_export(type_acte)
    if not donnees:
        return False, f"Aucun(e) {type_acte} à exporter."
    df = pd.DataFrame(donnees)
    if separateur == "excel":
        df.to_excel(chemin, index=False)
    else:
        df.to_csv(chemin, index=False, encoding="utf-8-sig")
    return True, f"{len(donnees)} {type_acte}(s) exporté(s) avec succès."


def export_examens_excel(chemin: str)        -> Tuple[bool, str]: return _exporter("examen",       chemin, "excel")
def export_examens_csv(chemin: str)          -> Tuple[bool, str]: return _exporter("examen",       chemin, "csv")
def export_chirurgies_excel(chemin: str)     -> Tuple[bool, str]: return _exporter("chirurgie",    chemin, "excel")
def export_chirurgies_csv(chemin: str)       -> Tuple[bool, str]: return _exporter("chirurgie",    chemin, "csv")
def export_lunettes_excel(chemin: str)       -> Tuple[bool, str]: return _exporter("lunette",      chemin, "excel")
def export_lunettes_csv(chemin: str)         -> Tuple[bool, str]: return _exporter("lunette",      chemin, "csv")
def export_prescriptions_excel(chemin: str)  -> Tuple[bool, str]: return _exporter("prescription", chemin, "excel")
def export_prescriptions_csv(chemin: str)    -> Tuple[bool, str]: return _exporter("prescription", chemin, "csv")


# ============================================================================
# VALIDATION DE DATE PAR RAPPORT À LA SESSION
# ============================================================================

# Colonnes CSV qui portent la date principale de l'acte, par type
_CLE_DATE_CSV: Dict[str, tuple] = {
    "examen":    ("date_examen",    "date"),
    "chirurgie": ("date_chirurgie", "date_chururgie", "date"),
    "lunette":   ("date_commande",  "date"),
    # prescription : pas de date propre dans le CSV → pas de validation de plage
    "prescription": None,
}


def _valider_date_acte(
    date_acte: datetime,
    date_debut: datetime,
    date_fin: datetime,
    nom_session: str,
) -> str | None:
    """
    Retourne un message d'erreur si la date est invalide, None si OK.
    Règles :
      - La date ne peut PAS être dans le futur (> aujourd'hui)
      - La date doit être >= date_debut de la session
      - La date doit être <= date_fin de la session
    """
    aujourd_hui = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)

    if date_acte > aujourd_hui:
        return (
            f"Date {date_acte.date()} dans le futur — importation refusée "
            f"(aujourd'hui : {aujourd_hui.date()})."
        )

    if isinstance(date_debut, datetime) and date_acte < date_debut:
        return (
            f"Date {date_acte.date()} antérieure au début de la session "
            f"'{nom_session}' ({date_debut.date()})."
        )

    if isinstance(date_fin, datetime) and date_acte > date_fin:
        return (
            f"Date {date_acte.date()} postérieure à la fin de la session "
            f"'{nom_session}' ({date_fin.date()})."
        )

    return None


# ============================================================================
# IMPORT — extraction et nettoyage des champs CSV (logique métier pure)
# ============================================================================

def _preparer_data_import(row, type_acte: str) -> dict:
    """
    Extrait et nettoie les champs du CSV selon le type d'acte.
    Retourne un dict propre prêt pour le DAO — aucun SQL ici.
    """
    if type_acte == "examen":
        return {
            'libelle_examen':      _get_col(row, "libelle_examen", "libelle"),
            'frais_examen':        _parse_float(_get_col(row, "frais_examen", "frais")),
            'statut_facture':      _get_col(row, "statut_facture") or "attente payement",
            'date_examen':         _parse_date(_get_col(row, "date_examen", "date")),
            'code_personnel':      _get_col(row, "code_personnel", "personnel") or None,
            'interpreter_par':     _get_col(row, "interpreter_par") or None,
            'date_interpretation': (
                _parse_date(_get_col(row, "date_interpretation"))
                if _get_col(row, "date_interpretation") else None
            ),
            'conclusion_medicale': _get_col(row, "conclusion_medicale", "conclusion") or None,
        }

    if type_acte == "chirurgie":
        return {
            'libelle_chirurgie': _get_col(row, "libelle_chirurgie", "libelle_chururgie", "libelle"),
            'frais_chirurgie':   _parse_float(_get_col(row, "frais_chirurgie", "frais_chururgie", "frais")),
            'statut_facture':    _get_col(row, "statut_facture") or "attente payement",
            'date_chirurgie':    _parse_date(_get_col(row, "date_chirurgie", "date_chururgie", "date")),
            'code_personnel':    _get_col(row, "code_personnel", "personnel") or None,
            'compte_rendu':      _get_col(row, "compte_rendu", "compte_rendu_operatoire") or "",
        }

    if type_acte == "lunette":
        return {
            'numero_cadre':   _get_col(row, "numero_cadre"),
            'numero_verre':   _get_col(row, "numero_verre"),
            'date_commande':  _parse_date(_get_col(row, "date_commande", "date")),
            'date_livraison': (
                _parse_date(_get_col(row, "date_livraison"))
                if _get_col(row, "date_livraison") else None
            ),
            'prix':           _parse_float(_get_col(row, "prix")),
            'statut':         _get_col(row, "statut") or "livree",
            'statut_facture': _get_col(row, "statut_facture") or "attente payement",
            'code_personnel': _get_col(row, "code_personnel", "personnel") or None,
        }

    if type_acte == "prescription":
        return {
            'code_produit':  _get_col(row, "code_produit") or None,
            'quantite':      _parse_float(_get_col(row, "quantite", "quantite_prescript"), default=1.0),
            'prix_applique': _parse_float(_get_col(row, "prix_applique", "prix")) or None,
            'designation':   _get_col(row, "designation") or None,
        }

    return {}


# ============================================================================
# IMPORT — orchestration transactionnelle
# ============================================================================

def _traiter_import_df(df, type_acte: str) -> Tuple[bool, str]:
    """
    Traite un DataFrame déjà lu pour un type d'acte donné.
    Une connexion DB / transaction par ligne CSV — atomicité garantie.
    """
    df.columns = [c.strip().lower() for c in df.columns]
    df = df.fillna("")

    # DAOs instanciés une fois pour toute la boucle
    consultation_dao  = ConsultationDAO()
    acte_dao          = ActeMedicalDAO()
    acte_visite_dao   = ActeVisiteDAO()
    visite_dao        = Visitedao()
    specifique_dao    = {
        "examen":       ExamenDAO(),
        "chirurgie":    ChirurgieDAO(),
        "lunette":      CommandeLunetteDAO(),
        "prescription": PrescriptionProduitDAO(),
    }.get(type_acte)

    succes_count = 0
    erreurs: list = []
    _cache_sessions: Dict[str, dict] = {}  # code_session → {nom_session, date_debut, date_fin}

    for index, row in df.iterrows():
        ligne = index + 2
        try:
            code_consultation = _get_col(row, "code_consultation")
            if not code_consultation:
                erreurs.append(f"Ligne {ligne} : code_consultation vide")
                continue

            # Lecture préalable (hors transaction) — propre connexion DAO
            v_info = consultation_dao.get_visite_et_session(code_consultation)
            if not v_info:
                erreurs.append(f"Ligne {ligne} : consultation '{code_consultation}' introuvable")
                continue
            code_visite  = v_info["code_visite"]
            code_session = v_info["code_session"]

            # ── Validation de la plage de session ──────────────────────────
            if code_session not in _cache_sessions:
                plage = visite_dao.get_plage_session(code_session)
                if not plage:
                    erreurs.append(
                        f"Ligne {ligne} : session '{code_session}' introuvable "
                        "dans la table annee — impossible de valider les dates."
                    )
                    continue
                _cache_sessions[code_session] = plage

            plage = _cache_sessions[code_session]
            cles_date = _CLE_DATE_CSV.get(type_acte)
            if cles_date:
                val_date = _get_col(row, *cles_date)
                date_acte = _parse_date(val_date)
                err_date = _valider_date_acte(
                    date_acte,
                    plage["date_debut"],
                    plage["date_fin"],
                    plage.get("nom_session", code_session),
                )
                if err_date:
                    erreurs.append(f"Ligne {ligne} : {err_date}")
                    continue
            # ───────────────────────────────────────────────────────────────

            # Une connexion = une transaction pour les 4 INSERTs + 1 UPDATE
            conn = DBConnection().connect()
            if not conn:
                erreurs.append(f"Ligne {ligne} : connexion DB échouée")
                continue

            try:
                with conn.cursor(DictCursor) as cur:
                    # Décision médicale = libellé principal selon le type
                    decision = _get_col(
                        row, "libelle_examen", "libelle_chirurgie",
                        "designation", "numero_cadre"
                    ) or type_acte

                    # Étape 1 — acte_medical statut=termine via ActeMedicalDAO
                    code_acte = acte_dao._inserer_import(
                        cur, code_consultation, type_acte, decision
                    )

                    # Étape 2 — acte_visite role=execution via ActeVisiteDAO
                    acte_visite_dao._inserer_liaison_import(cur, code_acte, code_visite)

                    # Étape 3 — table spécifique via DAO dédié
                    data = _preparer_data_import(row, type_acte)
                    specifique_dao._inserer_import(cur, code_acte, code_session, data)

                    # Étape 4 — statut terminal visite via Visitedao
                    statut_terminal = _STATUT_TERMINAL.get(type_acte, "Consultation terminée")
                    visite_dao._update_statut_visite_import(cur, code_visite, statut_terminal)

                conn.commit()
                succes_count += 1

            except Exception as e:
                conn.rollback()
                err = str(e)
                if "1452" in err or "foreign key" in err.lower():
                    erreurs.append(f"Ligne {ligne} : code visite ou personnel introuvable.")
                elif any(k in err.lower() for k in ("fefo", "lot fefo", "stock insuffisant", "aucun lot")):
                    erreurs.append(
                        f"Ligne {ligne} : stock insuffisant ou aucun lot disponible "
                        "pour ce produit (FEFO)."
                    )
                else:
                    erreurs.append(f"Ligne {ligne} : {err[:100]}")
            finally:
                conn.close()

        except Exception as e:
            erreurs.append(f"Ligne {ligne} : erreur inattendue — {str(e)[:80]}")

    if succes_count == 0:
        msg = f"Aucun(e) {type_acte} importé(e)."
        if erreurs:
            msg += "\nErreurs :\n" + "\n".join(erreurs[:3])
        return False, msg

    msg = f"{succes_count} {type_acte}(s) importé(s) avec succès."
    if erreurs:
        msg += f"\nDétail ({len(erreurs)} erreur(s)) :\n"
        msg += "\n".join([e[:120] for e in erreurs[:3]])
        if len(erreurs) > 3:
            msg += f"\n... et {len(erreurs) - 3} autre(s)."
        return False, msg
    return True, msg


def _lire_fichier(chemin: str, format_fichier: str):
    import pandas as pd
    if format_fichier == "excel":
        return pd.read_excel(chemin)
    return pd.read_csv(chemin, sep=None, engine='python', encoding="utf-8-sig")


def _importer(type_acte: str, chemin: str, format_fichier: str) -> Tuple[bool, str]:
    try:
        df = _lire_fichier(chemin, format_fichier)
        if df.empty:
            return False, "Le fichier est vide."
        return _traiter_import_df(df, type_acte)
    except Exception as e:
        return False, f"Erreur lecture fichier : {e}"


def import_examens(chemin: str, format_fichier: str)        -> Tuple[bool, str]: return _importer("examen",       chemin, format_fichier)
def import_chirurgies(chemin: str, format_fichier: str)     -> Tuple[bool, str]: return _importer("chirurgie",    chemin, format_fichier)
def import_lunettes(chemin: str, format_fichier: str)       -> Tuple[bool, str]: return _importer("lunette",      chemin, format_fichier)
def import_prescriptions(chemin: str, format_fichier: str)  -> Tuple[bool, str]: return _importer("prescription", chemin, format_fichier)
