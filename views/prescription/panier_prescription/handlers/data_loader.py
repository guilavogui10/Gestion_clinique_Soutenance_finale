"""
Handler PrescriptionDataLoader.
Responsabilité : Chargement des données (produits, patients, panier existant).
Pattern : Single Responsibility Principle (SRP).

Différences vs DataLoader panier :
  - charger_fournisseurs() → remplacé par charger_patients_en_attente()
  - charger_produits()     → adapté pour dicts (DictCursor) depuis PrescriptionControleur
  - charger_panier_existant() → recharge visuellement les lignes d'une consultation
"""

import qtawesome as qta
from typing import Callable, Any


class PrescriptionDataLoader:
    """Gère le chargement des données depuis le contrôleur prescription."""

    def __init__(self, bleu_principal: str):
        self.bleu_principal = bleu_principal

    # =========================================================================
    # PATIENTS
    # =========================================================================

    def charger_patients_en_attente(self, prescription_ctrl,
                                    combo_consultation, code_session: str) -> None:
        """
        Charge les consultations 'Attente pharmacie' dans le combo.

        Format label identique à CommandeLunetteFormDialog :
            code_consultation | nom prénom | date_visite

        userData = dict complet retourné par patients_en_attente_prescription :
            {'code_consultation', 'code_visite', 'nom', 'prenom',
             'date_visite', 'telephone', 'code_patient', 'statut_patient'}

        Args:
            prescription_ctrl  : PrescriptionControleur
            combo_consultation : QComboBox à remplir
            code_session       : Code de la session active
        """
        print(f"[PrescriptionDataLoader] Chargement consultations session={code_session}")

        if not prescription_ctrl:
            print("[PrescriptionDataLoader] ERREUR: prescription_ctrl est None")
            return

        try:
            patients = prescription_ctrl.obtenir_patients_en_attente(code_session)
            print(f"[PrescriptionDataLoader] {len(patients)} patients récupérés")

            combo_consultation.clear()
            combo_consultation.addItem(
                qta.icon("fa5s.file-medical", color=self.bleu_principal),
                "  — Sélectionner une consultation —",
                None
            )

            for p in patients:
                # Format identique à CommandeLunetteFormDialog
                label = (
                    f"  {p.get('code_consultation', '')}  |  "
                    f"{p.get('nom', '')} {p.get('prenom', '')}  |  "
                    f"{p.get('date_visite', '')}"
                )
                combo_consultation.addItem(
                    qta.icon("fa5s.user-injured", color=self.bleu_principal),
                    label,
                    p   # dict complet comme userData
                )

            print(f"[PrescriptionDataLoader] Combo rempli: {combo_consultation.count()} items")

        except Exception as e:
            print(f"[PrescriptionDataLoader] EXCEPTION charger_patients: {e}")
            import traceback
            traceback.print_exc()

    # =========================================================================
    # PRODUITS
    # =========================================================================

    def charger_produits(self, prescription_ctrl, combo_produit) -> None:
        """
        Charge la liste des produits actifs dans le combo.

        Retour du contrôleur : [{'code_produit', 'libelle', 'type',
                                  'prix_vente_unitaire'}, ...]

        Args:
            prescription_ctrl : PrescriptionControleur
            combo_produit     : QComboBox à remplir
        """
        print("[PrescriptionDataLoader] Chargement produits")

        if not prescription_ctrl:
            print("[PrescriptionDataLoader] ERREUR: prescription_ctrl est None")
            return

        try:
            produits = prescription_ctrl.lister_produits()

            combo_produit.clear()
            combo_produit.addItem(
                qta.icon("fa5s.pills", color=self.bleu_principal),
                "  Choisir un produit...",
                None
            )

            for p in produits:
                libelle = p.get('libelle', str(p))
                type_p  = p.get('type', '')
                code    = p.get('code_produit', None)

                combo_produit.addItem(
                    qta.icon("fa5s.capsules", color=self.bleu_principal),
                    f"  {libelle}  ({type_p})",
                    p   # ✅ dict complet comme userData (libelle + prix_vente_unitaire)
                )

            print(f"[PrescriptionDataLoader] {combo_produit.count()} produits chargés")

        except Exception as e:
            print(f"[PrescriptionDataLoader] Erreur charger_produits: {e}")
            import traceback
            traceback.print_exc()

    # =========================================================================
    # RECHARGEMENT PANIER EXISTANT
    # =========================================================================

    def charger_panier_existant(self, prescription_ctrl,
                                code_acte: str,
                                ajouter_ligne_visuelle_callback: Callable) -> None:
        """
        Recharge visuellement les lignes de prescription déjà enregistrées
        pour un acte médical donné.

        Utilisé quand on reprend une prescription en cours.

        Args:
            prescription_ctrl             : PrescriptionControleur
            code_acte                     : Code de l'acte médical en cours
            ajouter_ligne_visuelle_callback: Callable(dict) → ajoute la ligne dans le layout
        """
        if not prescription_ctrl or not code_acte:
            return

        try:
            lignes = prescription_ctrl.lister_par_acte(code_acte)
            print(f"[PrescriptionDataLoader] {len(lignes)} lignes existantes rechargées")

            for ligne in lignes:
                # ✅ Utiliser code_panier_prescription (nom réel dans le modèle)
                # Le DAO stocke la PK dans code_panier_prescription via __init__
                data = {
                    'code_prescription': ligne.code_prescription,
                    'designation':       ligne.designation,
                    'quantite':          ligne.quantite_prescript,
                    'prix':              ligne.prix_applique,
                    'date_expiration':   ligne.date_expiration,
                    'code_produit':      ligne.code_produit,
                }
                ajouter_ligne_visuelle_callback(data)

        except Exception as e:
            print(f"[PrescriptionDataLoader] Erreur charger_panier_existant: {e}")
