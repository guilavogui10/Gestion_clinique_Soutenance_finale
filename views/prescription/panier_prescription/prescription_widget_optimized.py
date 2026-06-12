"""
Widget Prescription Optimisé - sans scroll, formulaire en grille.
"""

from typing import Dict, Any, List, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout

from views.shared.theme_manager import theme_manager

# Composants UI
from .components.prescription_form_optimized import PrescriptionFormOptimized
from .components.prescription_footer import PrescriptionFooter
from views.shared.message_box import CustomMessageBox

# Handlers métier
from .handlers.data_loader import PrescriptionDataLoader
from .handlers.validation_handler import PrescriptionValidationHandler
from .handlers.prescription_operation import PrescriptionOperations

# Styles
from .styles.prescription_style import PrescriptionStyles


class PrescriptionWidgetOptimized(QWidget):
    """
    Widget de prescription optimisé - formulaire en grille sans scroll.
    """

    # Signaux
    prescription_validee = Signal()
    ligne_ajoutee = Signal(dict)
    ligne_supprimee = Signal()
    panier_reinitialise = Signal()

    def __init__(self, prescription_ctrl=None, parent=None):
        super().__init__(parent)

        self.prescription_ctrl = prescription_ctrl
        self.code_session = None
        self.code_acte = None
        self.lignes_panier = []

        # Composants
        self.form_component = PrescriptionFormOptimized()
        self.footer_component = PrescriptionFooter()

        # Handlers
        self.data_loader = PrescriptionDataLoader()
        self.validation_handler = PrescriptionValidationHandler(prescription_ctrl)
        self.operations = PrescriptionOperations(prescription_ctrl)

        self._init_ui()
        self._connecter_signaux()
        theme_manager.theme_changed.connect(self.apply_theme)

    def apply_theme(self) -> None:
        """Met à jour le thème du widget et de ses composants."""
        c = theme_manager.colors()
        self.setStyleSheet(f"QWidget#PrescriptionOptimized {{ background: {c['bg_card']}; border-radius: 12px; }}")
        self.form_component.apply_theme()
        self.footer_component.apply_theme()

    def _init_ui(self) -> None:
        """Initialise l'interface"""
        self.setObjectName("PrescriptionOptimized")
        self.setStyleSheet(f"QWidget#PrescriptionOptimized {{ background: {theme_manager.colors()['bg_card']}; border-radius: 12px; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Formulaire optimisé
        self.form_component.create(layout)

        # Exposition des widgets
        self.combo_acte = self.form_component.combo_acte
        self.edit_code_session = self.form_component.edit_code_session
        self.combo_produit = self.form_component.combo_produit
        self.input_designation = self.form_component.input_designation
        self.input_quantite = self.form_component.input_quantite
        self.input_prix = self.form_component.input_prix
        self.btn_ajouter = self.form_component.btn_ajouter

        # Footer
        self.lbl_total, self.btn_valider, self.btn_annuler = \
            self.footer_component.create(layout)

    def _connecter_signaux(self) -> None:
        """Connecte les signaux"""
        self.combo_acte.currentIndexChanged.connect(self._on_acte_change)
        self.combo_produit.currentIndexChanged.connect(self._on_produit_change)
        self.input_quantite.valueChanged.connect(
            lambda value: self.validation_handler.valider_quantite(
                self.input_quantite, str(value)
            )
        )
        self.btn_ajouter.clicked.connect(self._prescrire)
        self.btn_valider.clicked.connect(self._valider_prescription)
        self.btn_annuler.clicked.connect(self._annuler_prescription)

    def selectionner_acte(self, code_acte: str) -> None:
        """Sélectionne un acte médical dans le combo par son code."""
        if not code_acte:
            return
        for i in range(self.combo_acte.count()):
            data = self.combo_acte.itemData(i)
            if data and data.get('code_acte') == code_acte:
                self.combo_acte.setCurrentIndex(i)
                return
        # Si l'acte n'est pas encore dans le combo, recharger et réessayer
        if self.prescription_ctrl and self.code_session:
            self.data_loader.charger_patients_en_attente(
                self.prescription_ctrl,
                self.combo_acte,
                self.code_session
            )
            for i in range(self.combo_acte.count()):
                data = self.combo_acte.itemData(i)
                if data and data.get('code_acte') == code_acte:
                    self.combo_acte.setCurrentIndex(i)
                    return

    def charger_donnees(self, code_session: str) -> None:
        """Charge les données de la session"""
        self.code_session = code_session
        self.edit_code_session.setText(code_session)

        if not self.prescription_ctrl:
            return

        # Charger produits
        self.data_loader.charger_produits(
            self.prescription_ctrl,
            self.combo_produit
        )

        # Charger actes en attente
        self.data_loader.charger_patients_en_attente(
            self.prescription_ctrl,
            self.combo_acte,
            code_session
        )

    def _on_acte_change(self, index: int) -> None:
        """Sélection d'un acte médical"""
        patient_data = self.combo_acte.currentData()

        if not patient_data:
            self.code_acte = None
            self.form_component.vider_patient()
            self.form_component.desactiver_formulaire()
            self._reinitialiser_lignes()
            return

        self.code_acte = patient_data.get('code_acte', '')

        self.form_component.charger_patient(
            nom=patient_data.get('nom', ''),
            prenom=patient_data.get('prenom', ''),
            code_acte=self.code_acte
        )

        self.form_component.activer_formulaire()
        self._reinitialiser_lignes()

        if self.code_acte:
            self.data_loader.charger_panier_existant(
                self.prescription_ctrl,
                self.code_acte,
                lambda data: self.ligne_ajoutee.emit(data)
            )

        self._recalculer_total()

    def _on_produit_change(self, index: int) -> None:
        """Auto-remplissage désignation + prix"""
        produit_data = self.combo_produit.currentData()

        if not produit_data:
            self.input_designation.clear()
            self.input_prix.clear()
            return

        designation = produit_data.get('libelle', '')
        prix = float(produit_data.get('prix_vente_unitaire', 0) or 0)

        self.input_designation.setText(designation)

        if prix > 0:
            self.input_prix.blockSignals(True)
            self.input_prix.clear()
            self.input_prix.setText(
                str(int(prix)) if prix == int(prix) else str(prix)
            )
            self.input_prix.blockSignals(False)

    def _prescrire(self) -> None:
        """Ajoute un produit au panier"""
        if not self.code_acte:
            self._afficher_message(
                "Attention", "Veuillez sélectionner un acte médical d'abord.", False
            )
            return

        produit_data = self.combo_produit.currentData()
        form_data = {
            'code_produit': produit_data.get('code_produit') if produit_data else None,
            'code_session': self.code_session,
            'code_acte': self.code_acte,
            'designation': self.input_designation.text().strip(),
            'quantite': self.input_quantite.text(),
            'prix': self.input_prix.text(),
        }

        ok, msg = self.operations.ajouter_ligne_prescription(form_data)

        if ok:
            allocations = form_data.get('allocations')
            if allocations:
                for alloc in allocations:
                    self.ligne_ajoutee.emit(alloc)
            else:
                self.ligne_ajoutee.emit(form_data)
            
            self.form_component.vider_formulaire()
            self._recalculer_total()
            self._afficher_message("Succès", msg, True)
        else:
            self._afficher_message("Erreur", msg, False)

    def _valider_prescription(self) -> None:
        """Valide la prescription"""
        if not self.code_acte:
            self._afficher_message(
                "Attention", "La prescription est vide.", False
            )
            return

        ok, msg = self.operations.valider_prescription(
            self.code_acte, self
        )

        if ok:
            self._afficher_message("Succès", msg, True)
            self._reinitialiser_complet()
            self.prescription_validee.emit()
        else:
            if msg != "Validation annulée":
                self._afficher_message("Erreur", msg, False)

    def _annuler_prescription(self) -> None:
        """Annule la prescription"""
        if not self.code_acte:
            return

        ok, msg = self.operations.annuler_prescription([], self)

        if ok:
            self._reinitialiser_complet()
            self._afficher_message("Succès", msg, True)
        else:
            if msg != "Annulation annulée":
                self._afficher_message("Erreur", msg, False)

    def _recalculer_total(self) -> None:
        """Recalcule le total"""
        if self.prescription_ctrl and self.code_acte:
            total = self.prescription_ctrl.obtenir_montant_total_acte(
                self.code_acte
            )
        else:
            total = 0

        self.footer_component.update_total(total)

    def _reinitialiser_lignes(self) -> None:
        """Réinitialise les lignes"""
        self.lignes_panier.clear()
        self.footer_component.update_total(0)
        self.panier_reinitialise.emit()

    def _reinitialiser_complet(self) -> None:
        """Réinitialisation complète"""
        self._reinitialiser_lignes()
        self.code_acte = None
        self.form_component.vider_formulaire()
        self.form_component.vider_patient()
        self.form_component.desactiver_formulaire()

        if self.prescription_ctrl and self.code_session:
            self.data_loader.charger_patients_en_attente(
                self.prescription_ctrl,
                self.combo_acte,
                self.code_session
            )

    def _afficher_message(self, titre: str, message: str, succes: bool) -> None:
        """Affiche un message"""
        if succes:
            CustomMessageBox.success(self, titre, message)
        else:
            CustomMessageBox.error(self, titre, message)
