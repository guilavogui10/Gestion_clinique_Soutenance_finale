"""
Composant PrescriptionForm.
Responsabilité : Formulaire de saisie d'une ligne de prescription.

Pattern identique à CommandeLunetteFormDialog :
  - combo_consultation → liste les consultations 'Attente pharmacie'
  - edit_code_visite   → readonly, auto-rempli à la sélection
  - carte patient      → auto-remplie (nom, prénom) à la sélection
  - Pas de date_expiration → FEFO automatique (DAO)
  - input_prix readonly    → auto-rempli depuis produits.prix_vente_unitaire
  - input_designation readonly → auto-rempli depuis produits.libelle
"""

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QFrame, QLabel, QComboBox, QScrollArea
)
from ..styles.prescription_style import PrescriptionStyles
from .modern_quantity_spinner import ModernQuantitySpinner
from .modern_price_input import ModernPriceInput
from views.shared.theme_manager import theme_manager


class PrescriptionForm:
    """
    Gère le formulaire de saisie d'une ligne de prescription.
    Pattern : Facade — même disposition que CommandeLunetteFormDialog.
    """

    def __init__(self):

        # ── Widgets exposés au widget principal ──────────────────────────────
        self.combo_consultation = None   # sélection consultation 'Attente pharmacie'
        self.edit_code_visite   = None   # readonly — auto-rempli depuis combo
        self.combo_produit      = None
        self.input_designation  = None
        self.input_quantite     = None
        self.input_prix         = None
        self.btn_prescrire      = None
        self.container_panier   = None
        self.layout_lignes      = None

        # Labels carte patient
        self.lbl_patient_nom    = None
        self.lbl_patient_code   = None
        self.err_consultation   = None

    # =========================================================================
    # CRÉATION DU FORMULAIRE
    # =========================================================================

    def create(self, parent_layout, appliquer_style_scrollbar_callback, afficher_panier_interne=True):
        """
        Crée le formulaire complet dans un QScrollArea.

        Args:
            afficher_panier_interne: Si False, ne crée pas la section "Produits prescrits" dans le formulaire

        Returns:
            tuple: (container_panier, layout_lignes)
        """
        body_scroll = QScrollArea()
        body_scroll.setWidgetResizable(True)
        body_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body_scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {theme_manager.colors()['bg_main']}; }}")
        appliquer_style_scrollbar_callback(body_scroll)

        body = QWidget()
        body.setStyleSheet(f"background: {theme_manager.colors()['bg_main']};")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(14, 12, 14, 12)
        body_layout.setSpacing(10)

        # 1. Combo consultation
        self._create_combo_consultation_section(body_layout)

        # 2. Code visite readonly
        self._create_code_visite_section(body_layout)

        # 3. Carte patient
        self._create_patient_card(body_layout)

        # 4. Séparateur
        self._ajouter_separateur(body_layout, "Détail du produit à prescrire")

        # 5. Combo produit
        self._create_produit_section(body_layout)

        # 6. Désignation readonly
        self._create_designation_section(body_layout)

        # 7. Quantité + Prix
        self._create_quantite_prix_section(body_layout)

        # 8. Note FEFO
        self._create_fefo_note(body_layout)

        # 9. Bouton prescrire
        self._create_bouton_prescrire(body_layout)

        # 10. Séparateur + container lignes (seulement si afficher_panier_interne=True)
        if afficher_panier_interne:
            self._ajouter_separateur(body_layout, "Produits prescrits")

            self.container_panier = QWidget()
            self.container_panier.setStyleSheet("background: transparent;")
            self.layout_lignes = QVBoxLayout(self.container_panier)
            self.layout_lignes.setContentsMargins(0, 0, 0, 0)
            self.layout_lignes.setSpacing(6)
            self.layout_lignes.addStretch()
            body_layout.addWidget(self.container_panier)
        else:
            # Créer des containers vides pour éviter les erreurs
            self.container_panier = None
            self.layout_lignes = None

        body_scroll.setWidget(body)
        parent_layout.addWidget(body_scroll, stretch=1)

        return self.container_panier, self.layout_lignes

    # =========================================================================
    # SECTIONS PRIVÉES
    # =========================================================================

    def _create_combo_consultation_section(self, layout):
        """
        Combo listant les actes médicaux 'Attente pharmacie'.
        userData = dict complet retourné par patients_en_attente_prescription :
          {'code_acte', 'nom', 'prenom', ...}
        """
        vbox = QVBoxLayout()
        vbox.setSpacing(4)

        lbl = QLabel("Acte médical (patient en attente pharmacie)")
        lbl.setStyleSheet(
            f"font-size: 10px; font-weight: bold; color: {theme_manager.colors()['text_muted']};"
            "text-transform: uppercase; border: none; background: transparent;"
        )
        vbox.addWidget(lbl)

        self.combo_consultation = QComboBox()
        self.combo_consultation.setFixedHeight(40)
        self.combo_consultation.addItem(
            qta.icon("fa5s.file-medical", color=theme_manager.colors()['primary']),
            "  — Sélectionner un acte médical —",
            None
        )
        self.combo_consultation.setStyleSheet(
            PrescriptionStyles.combo_produit()
        )
        self.combo_consultation.setToolTip(
            "Actes médicaux avec statut 'Attente pharmacie' sans prescription enregistrée"
        )
        vbox.addWidget(self.combo_consultation)

        self.err_consultation = QLabel("")
        self.err_consultation.setStyleSheet(
            f"color: {theme_manager.colors()['danger']}; font-size: 10px; font-style: italic;"
            "border: none; background: transparent;"
        )
        self.err_consultation.setVisible(False)
        vbox.addWidget(self.err_consultation)

        layout.addLayout(vbox)

    def _create_code_visite_section(self, layout):
        """
        Champ code_acte readonly — auto-rempli à la sélection de la consultation.
        """
        vbox = QVBoxLayout()
        vbox.setSpacing(4)

        lbl = QLabel("Code Acte (auto)")
        lbl.setStyleSheet(
            f"font-size: 10px; font-weight: bold; color: {theme_manager.colors()['text_muted']};"
            "border: none; background: transparent;"
        )
        vbox.addWidget(lbl)

        self.edit_code_visite = QLineEdit()
        self.edit_code_visite.setPlaceholderText("Auto-rempli à la sélection...")
        self.edit_code_visite.setFixedHeight(38)
        self.edit_code_visite.setReadOnly(True)
        self.edit_code_visite.setStyleSheet(PrescriptionStyles.input_readonly())
        vbox.addWidget(self.edit_code_visite)

        layout.addLayout(vbox)

    def _create_patient_card(self, layout):
        """Carte patient readonly — auto-remplie depuis le combo."""
        card = QFrame()
        card.setStyleSheet(PrescriptionStyles.patient_card())
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(4)

        titre_row = QHBoxLayout()
        icon_patient = QLabel()
        icon_patient.setPixmap(
            qta.icon("fa5s.user-injured", color=theme_manager.colors()['primary']).pixmap(14, 14)
        )
        icon_patient.setStyleSheet("border: none; background: transparent;")

        lbl_titre = QLabel("Patient")
        lbl_titre.setStyleSheet(
            f"font-size: 10px; font-weight: bold; color: {theme_manager.colors()['primary']};"
            "text-transform: uppercase; border: none; background: transparent;"
        )
        titre_row.addWidget(icon_patient)
        titre_row.addWidget(lbl_titre)
        titre_row.addStretch()
        card_layout.addLayout(titre_row)

        self.lbl_patient_nom = QLabel("— Sélectionnez une consultation —")
        self.lbl_patient_nom.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {theme_manager.colors()['text_primary']};"
            "border: none; background: transparent;"
        )
        card_layout.addWidget(self.lbl_patient_nom)

        self.lbl_patient_code = QLabel("")
        self.lbl_patient_code.setStyleSheet(
            f"font-size: 10px; color: {theme_manager.colors()['text_muted']}; border: none; background: transparent;"
        )
        card_layout.addWidget(self.lbl_patient_code)

        layout.addWidget(card)

    def _create_produit_section(self, layout):
        """Combo de sélection du produit."""
        vbox = QVBoxLayout()
        vbox.setSpacing(4)

        lbl = QLabel("Produit")
        lbl.setStyleSheet(
            f"font-size: 10px; font-weight: bold; color: {theme_manager.colors()['text_muted']};"
            "border: none; background: transparent;"
        )
        self.combo_produit = QComboBox()
        self.combo_produit.addItem(
            qta.icon("fa5s.pills", color=theme_manager.colors()['primary']),
            "  Choisir un produit..."
        )
        self.combo_produit.setFixedHeight(38)
        self.combo_produit.setStyleSheet(
            PrescriptionStyles.combo_produit()
        )
        vbox.addWidget(lbl)
        vbox.addWidget(self.combo_produit)
        layout.addLayout(vbox)

    def _create_designation_section(self, layout):
        """Désignation readonly."""
        vbox = QVBoxLayout()
        vbox.setSpacing(4)

        lbl = QLabel("Désignation")
        lbl.setStyleSheet(
            f"font-size: 10px; font-weight: bold; color: {theme_manager.colors()['text_muted']};"
            "border: none; background: transparent;"
        )
        self.input_designation = QLineEdit()
        self.input_designation.setPlaceholderText("Rempli automatiquement...")
        self.input_designation.setFixedHeight(36)
        self.input_designation.setReadOnly(True)
        self.input_designation.setStyleSheet(PrescriptionStyles.input_readonly())
        vbox.addWidget(lbl)
        vbox.addWidget(self.input_designation)
        layout.addLayout(vbox)

    def _create_quantite_prix_section(self, layout):
        """Quantité (spinner) + Prix (readonly)."""
        row = QHBoxLayout()
        row.setSpacing(10)

        col_qte = QVBoxLayout()
        col_qte.setSpacing(4)
        lbl_qte = QLabel("Quantité")
        lbl_qte.setStyleSheet(
            f"font-size: 10px; font-weight: bold; color: {theme_manager.colors()['text_muted']};"
            "border: none; background: transparent;"
        )
        self.input_quantite = ModernQuantitySpinner()
        self.input_quantite.setMinimum(1)
        self.input_quantite.setMaximum(9999)
        col_qte.addWidget(lbl_qte)
        col_qte.addWidget(self.input_quantite)

        col_prix = QVBoxLayout()
        col_prix.setSpacing(4)
        lbl_prix = QLabel("Prix unitaire (auto)")
        lbl_prix.setStyleSheet(
            f"font-size: 10px; font-weight: bold; color: {theme_manager.colors()['text_muted']};"
            "border: none; background: transparent;"
        )
        self.input_prix = ModernPriceInput()
        self.input_prix.setPlaceholderText("0")
        self.input_prix.setEnabled(False)
        col_prix.addWidget(lbl_prix)
        col_prix.addWidget(self.input_prix)

        row.addLayout(col_qte)
        row.addLayout(col_prix)
        layout.addLayout(row)

    def _create_fefo_note(self, layout):
        """Note FEFO informative."""
        row = QHBoxLayout()
        row.setSpacing(6)

        icon_info = QLabel()
        icon_info.setPixmap(
            qta.icon("fa5s.info-circle", color=theme_manager.colors()['info']).pixmap(12, 12)
        )
        icon_info.setStyleSheet("border: none; background: transparent;")

        lbl = QLabel("Date d'expiration attribuée automatiquement (méthode FEFO).")
        lbl.setStyleSheet(
            f"font-size: 10px; color: {theme_manager.colors()['info']}; font-style: italic;"
            "border: none; background: transparent;"
        )
        lbl.setWordWrap(True)

        row.addWidget(icon_info)
        row.addWidget(lbl, 1)
        layout.addLayout(row)

    def _create_bouton_prescrire(self, layout):
        """Bouton principal d'ajout."""
        self.btn_prescrire = QPushButton(
            qta.icon("fa5s.prescription", color="white"),
            "  Prescrire ce produit"
        )
        self.btn_prescrire.setFixedHeight(48)
        self.btn_prescrire.setCursor(Qt.PointingHandCursor)
        self.btn_prescrire.setStyleSheet(
            PrescriptionStyles.btn_prescrire_modern()
        )
        self.btn_prescrire.setEnabled(False)
        layout.addWidget(self.btn_prescrire)

    def _ajouter_separateur(self, layout, texte: str):
        """Séparateur horizontal avec label."""
        sep_row = QHBoxLayout()
        sep_row.setSpacing(8)

        line1 = QFrame()
        line1.setFixedHeight(1)
        line1.setStyleSheet(f"background: {theme_manager.colors()['border_light']}; border: none;")

        lbl = QLabel(texte.upper())
        lbl.setStyleSheet(
            f"font-size: 9px; font-weight: bold; color: {theme_manager.colors()['text_muted']};"
            "border: none; background: transparent;"
        )
        lbl.setFixedHeight(16)

        line2 = QFrame()
        line2.setFixedHeight(1)
        line2.setStyleSheet(f"background: {theme_manager.colors()['border_light']}; border: none;")

        sep_row.addWidget(line1, 1)
        sep_row.addWidget(lbl)
        sep_row.addWidget(line2, 1)
        layout.addLayout(sep_row)

    # =========================================================================
    # API PUBLIQUE
    # =========================================================================

    def charger_patient(self, nom: str, prenom: str, code_acte: str) -> None:
        """
        Auto-remplit la carte patient.
        Appelé depuis _on_consultation_change() dans le widget principal.
        """
        self.lbl_patient_nom.setText(f"{prenom} {nom}".strip())
        self.lbl_patient_code.setText(f"Acte médical : {code_acte}")
        self.edit_code_visite.setText(code_acte)
        self.btn_prescrire.setEnabled(True)

    def vider_patient(self) -> None:
        """Réinitialise l'affichage patient."""
        self.lbl_patient_nom.setText("— Sélectionnez une consultation —")
        self.lbl_patient_code.setText("")
        self.edit_code_visite.clear()
        self.btn_prescrire.setEnabled(False)

    def vider_formulaire(self) -> None:
        """Vide les champs produit après un ajout."""
        self.combo_produit.setCurrentIndex(0)
        self.input_designation.clear()
        self.input_designation.setStyleSheet(PrescriptionStyles.input_readonly())
        self.input_quantite.clear()
        self.input_prix.clear()

    def activer_formulaire(self) -> None:
        """Active les champs produit."""
        self.combo_produit.setEnabled(True)
        self.input_quantite.setEnabled(True)
        self.btn_prescrire.setEnabled(True)

    def desactiver_formulaire(self) -> None:
        """Désactive les champs produit."""
        self.combo_produit.setEnabled(False)
        self.input_quantite.setEnabled(False)
        self.btn_prescrire.setEnabled(False)