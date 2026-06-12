"""
Formulaire de prescription optimisé - disposition en lignes claires sans scroll.
Inspiré de l'interface CliniKGest.
"""

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QFrame, QLabel, QComboBox
)
from ..styles.prescription_style import PrescriptionStyles
from .modern_quantity_spinner import ModernQuantitySpinner
from .modern_price_input import ModernPriceInput
from views.shared.theme_manager import theme_manager


class PrescriptionFormOptimized:
    """
    Formulaire de prescription optimisé - lignes de champs bien espacées,
    dans une seule carte, sans scroll.
    """

    def __init__(self):

        # Widgets exposés
        self.combo_acte = None
        self.edit_code_session = None
        self.combo_produit = None
        self.input_designation = None
        self.input_quantite = None
        self.input_prix = None
        self.btn_ajouter = None

        # Labels carte patient
        self.lbl_patient_nom = None
        self.lbl_patient_code = None

        # Refs pour apply_theme
        self._form_card = None
        self._form_sep = None
        self._icon_box = None
        self._icon_ic = None
        self._title_lbl = None
        self._sub_lbl = None
        self._patient_band = None
        self._patient_band_ic = None

    def create(self, parent_layout):
        """Crée le formulaire optimisé sans scroll."""
        c = theme_manager.colors()

        # Container extérieur
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        outer = QVBoxLayout(container)
        outer.setContentsMargins(16, 4, 16, 14)
        outer.setSpacing(8)  # Espacement réduit entre header et carte

        # ── En-tête ──────────────────────────────────────────────
        self._create_header(outer)

        # ── Carte unique avec tous les champs ────────────────────
        card = QFrame()
        card.setObjectName("formCard")
        card.setStyleSheet(f"""
            QFrame#formCard {{
                background: {c['bg_card']};
                border: 1.5px solid {c['border_light']};
                border-radius: 14px;
            }}
        """)
        self._form_card = card
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)  # Marges réduites
        card_layout.setSpacing(12)  # Espacement réduit entre les lignes

        # Ligne 1 : Code Session | Acte médical
        row1_w = QWidget(); row1_w.setStyleSheet("background: transparent;")
        row1_w.setFixedHeight(64)  # Hauteur fixe pour la ligne
        row1 = QHBoxLayout(row1_w)
        row1.setContentsMargins(0, 0, 0, 0)
        row1.setSpacing(16)

        vb_session, wr_session = self._make_field("fa5s.calendar-check", "Code Session")
        self.edit_code_session = self._create_readonly_input("Code session")
        vb_session.addWidget(self.edit_code_session)

        vb_acte, wr_acte = self._make_field("fa5s.file-medical", "Acte médical *")
        self.combo_acte = self._create_combo("Sélectionner un acte", "fa5s.file-medical")
        vb_acte.addWidget(self.combo_acte)

        row1.addWidget(wr_session)
        row1.addWidget(wr_acte)
        card_layout.addWidget(row1_w)

        # Bandeau patient (pleine largeur)
        self._create_patient_card(card_layout)

        # Séparateur
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {c['border_light']}; border: none;")
        self._form_sep = sep
        card_layout.addWidget(sep)

        # Ligne 2 : Produit | Désignation
        row2_w = QWidget(); row2_w.setStyleSheet("background: transparent;")
        row2_w.setFixedHeight(64)  # Hauteur fixe pour la ligne
        row2 = QHBoxLayout(row2_w)
        row2.setContentsMargins(0, 0, 0, 0)
        row2.setSpacing(16)

        vb_produit, wr_produit = self._make_field("fa5s.pills", "Produit *")
        self.combo_produit = self._create_combo("Choisir un produit", "fa5s.pills")
        vb_produit.addWidget(self.combo_produit)

        vb_desig, wr_desig = self._make_field("fa5s.file-alt", "Désignation")
        self.input_designation = self._create_readonly_input("Auto-rempli")
        vb_desig.addWidget(self.input_designation)

        row2.addWidget(wr_produit)
        row2.addWidget(wr_desig)
        card_layout.addWidget(row2_w)

        # Ligne 3 : Quantité | Prix
        row3_w = QWidget(); row3_w.setStyleSheet("background: transparent;")
        row3_w.setFixedHeight(64)  # Hauteur fixe pour la ligne
        row3 = QHBoxLayout(row3_w)
        row3.setContentsMargins(0, 0, 0, 0)
        row3.setSpacing(16)

        vb_qte, wr_qte = self._make_field("fa5s.sort-numeric-up", "Quantité prescrite *")
        self.input_quantite = ModernQuantitySpinner()
        self.input_quantite.setMinimum(1)
        self.input_quantite.setMaximum(9999)
        self.input_quantite.setFixedHeight(42)
        vb_qte.addWidget(self.input_quantite)

        vb_prix, wr_prix = self._make_field("fa5s.dollar-sign", "Prix appliqué *")
        self.input_prix = ModernPriceInput()
        self.input_prix.setPlaceholderText("0")
        self.input_prix.setEnabled(False)
        self.input_prix.setFixedHeight(42)
        vb_prix.addWidget(self.input_prix)

        row3.addWidget(wr_qte)
        row3.addWidget(wr_prix)
        card_layout.addWidget(row3_w)

        outer.addWidget(card, 1)

        # ── Bouton Ajouter ────────────────────────────────────────
        self._create_bouton_ajouter(outer)

        parent_layout.addWidget(container, 1)
        return None, None

    # ─────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────

    def _make_field(self, icon_name: str, label_text: str) -> tuple:
        """
        Retourne (QVBoxLayout, QWidget) — le QWidget est le conteneur à ajouter
        au layout parent via addWidget(). Le QVBoxLayout sert à y ajouter l'input.
        """
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        wrapper.setFixedHeight(64)  # Hauteur réduite pour éviter chevauchement
        vbox = QVBoxLayout(wrapper)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(4)  # Espacement réduit entre label et input

        # Ligne label + icône
        lbl_row = QHBoxLayout()
        lbl_row.setSpacing(5)
        lbl_row.setContentsMargins(0, 0, 0, 0)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(
            qta.icon(icon_name, color=theme_manager.colors()['text_muted']).pixmap(13, 13)
        )
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        icon_lbl.setFixedSize(13, 13)  # Taille fixe pour l'icône

        text_lbl = QLabel(label_text)
        text_lbl.setFixedHeight(16)  # Hauteur fixe pour le label
        text_lbl.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 600;
            color: {theme_manager.colors()['text_muted']};
            border: none;
            background: transparent;
        """)

        lbl_row.addWidget(icon_lbl)
        lbl_row.addWidget(text_lbl)
        lbl_row.addStretch()
        vbox.addLayout(lbl_row)

        return vbox, wrapper

    def _create_header(self, layout):
        """En-tête compact avec icône, titre et sous-titre."""
        c = theme_manager.colors()
        hdr = QHBoxLayout()
        hdr.setSpacing(12)

        # Cercle icône
        icon_box = QFrame()
        icon_box.setFixedSize(46, 46)
        icon_box.setStyleSheet(f"""
            QFrame {{
                background: {c['primary']};
                border-radius: 12px;
            }}
        """)
        self._icon_box = icon_box
        ib_lay = QVBoxLayout(icon_box)
        ib_lay.setContentsMargins(0, 0, 0, 0)
        ib_lay.setAlignment(Qt.AlignCenter)
        ic = QLabel()
        ic.setPixmap(qta.icon("fa5s.clipboard-list", color=c['text_inverse']).pixmap(22, 22))
        ic.setStyleSheet("border: none; background: transparent;")
        self._icon_ic = ic
        ib_lay.addWidget(ic)

        # Texte
        col = QVBoxLayout()
        col.setSpacing(2)
        title = QLabel("Nouvelle prescription")
        title.setStyleSheet(f"""
            font-size: 15px; font-weight: bold;
            color: {c['text_primary']}; border: none; background: transparent;
        """)
        self._title_lbl = title
        sub = QLabel("Sélectionnez un acte puis renseignez le produit")
        sub.setStyleSheet(f"""
            font-size: 11px; color: {c['text_muted']};
            border: none; background: transparent;
        """)
        self._sub_lbl = sub
        col.addWidget(title)
        col.addWidget(sub)

        hdr.addWidget(icon_box)
        hdr.addLayout(col)
        hdr.addStretch()
        layout.addLayout(hdr)

    def _create_readonly_input(self, placeholder: str) -> QLineEdit:
        """Input en lecture seule."""
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setFixedHeight(42)
        field.setReadOnly(True)
        field.setStyleSheet(PrescriptionStyles.input_readonly())
        return field

    def _create_combo(self, placeholder: str, icon_name: str) -> QComboBox:
        """Combobox stylisé."""
        c = theme_manager.colors()
        combo = QComboBox()
        combo.setFixedHeight(42)
        combo.addItem(
            qta.icon(icon_name, color=c['primary']),
            f"  — {placeholder} —",
            None
        )
        combo.setStyleSheet(PrescriptionStyles.combo_produit())
        return combo

    def _create_patient_card(self, layout):
        """Bandeau patient compact (pleine largeur)."""
        c = theme_manager.colors()
        card = QFrame()
        card.setObjectName("patientBand")
        card.setFixedHeight(46)
        card.setStyleSheet(f"""
            QFrame#patientBand {{
                background: {c['bg_input']};
                border: 1px solid {c['border_light']};
                border-radius: 8px;
            }}
        """)
        self._patient_band = card
        row = QHBoxLayout(card)
        row.setContentsMargins(12, 0, 12, 0)
        row.setSpacing(10)

        ic = QLabel()
        ic.setPixmap(qta.icon("fa5s.user-injured", color=c['primary']).pixmap(15, 15))
        ic.setStyleSheet("border: none; background: transparent;")
        self._patient_band_ic = ic

        self.lbl_patient_nom = QLabel("— Sélectionnez un acte médical —")
        self.lbl_patient_nom.setStyleSheet(f"""
            font-size: 12px; font-weight: bold;
            color: {c['text_primary']}; border: none; background: transparent;
        """)

        self.lbl_patient_code = QLabel("")
        self.lbl_patient_code.setStyleSheet(f"""
            font-size: 10px; color: {c['text_muted']};
            border: none; background: transparent;
        """)

        row.addWidget(ic)
        row.addWidget(self.lbl_patient_nom)
        row.addSpacing(8)
        row.addWidget(self.lbl_patient_code)
        row.addStretch()

        layout.addWidget(card)

    def _create_bouton_ajouter(self, layout):
        """Bouton Ajouter au Panier pleine largeur."""
        c = theme_manager.colors()
        self.btn_ajouter = QPushButton(
            qta.icon("fa5s.plus", color=c['text_inverse']),
            "  Ajouter au panier"
        )
        self.btn_ajouter.setFixedHeight(46)
        self.btn_ajouter.setCursor(Qt.PointingHandCursor)
        self.btn_ajouter.setStyleSheet(f"""
            QPushButton {{
                background: {c['primary']};
                color: {c['text_inverse']};
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background: {c['primary_hover']};
            }}
            QPushButton:disabled {{
                background: {c['border']};
                color: {c['text_muted']};
            }}
        """)
        self.btn_ajouter.setEnabled(False)
        layout.addWidget(self.btn_ajouter)

    def _create_note_info(self, layout):
        """Note informative en bas"""
        note_frame = QFrame()
        note_frame.setStyleSheet(f"""
            QFrame {{
                background: {theme_manager.colors()['info_bg']};
                border: 1px solid {theme_manager.colors()['info']};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        note_layout = QHBoxLayout(note_frame)
        note_layout.setContentsMargins(12, 8, 12, 8)
        note_layout.setSpacing(8)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon("fa5s.info-circle", color=theme_manager.colors()['info']).pixmap(16, 16))
        icon_lbl.setStyleSheet("border: none; background: transparent;")

        text_lbl = QLabel("Tous les champs marqués d'un * sont obligatoires.\nVeuillez vérifier tous les produits avant de valider la prescription.")
        text_lbl.setStyleSheet(f"""
            font-size: 11px;
            color: {theme_manager.colors()['info']};
            border: none;
            background: transparent;
        """)
        text_lbl.setWordWrap(True)

        note_layout.addWidget(icon_lbl)
        note_layout.addWidget(text_lbl, 1)

        layout.addWidget(note_frame)

    # ─────────────────────────────────────────────────────────────
    # Thème dynamique
    # ─────────────────────────────────────────────────────────────

    def apply_theme(self):
        """Met à jour tous les styles avec le thème courant."""
        if not self._form_card:
            return
        c = theme_manager.colors()

        self._form_card.setStyleSheet(f"""
            QFrame#formCard {{
                background: {c['bg_card']};
                border: 1.5px solid {c['border_light']};
                border-radius: 14px;
            }}
        """)
        if self._form_sep:
            self._form_sep.setStyleSheet(f"background: {c['border_light']}; border: none;")
        if self._icon_box:
            self._icon_box.setStyleSheet(f"QFrame {{ background: {c['primary']}; border-radius: 12px; }}")
        if self._icon_ic:
            self._icon_ic.setPixmap(qta.icon("fa5s.clipboard-list", color=c['text_inverse']).pixmap(22, 22))
        if self._title_lbl:
            self._title_lbl.setStyleSheet(
                f"font-size: 15px; font-weight: bold; color: {c['text_primary']}; border: none; background: transparent;"
            )
        if self._sub_lbl:
            self._sub_lbl.setStyleSheet(
                f"font-size: 11px; color: {c['text_muted']}; border: none; background: transparent;"
            )
        if self._patient_band:
            self._patient_band.setStyleSheet(f"""
                QFrame#patientBand {{
                    background: {c['bg_input']};
                    border: 1px solid {c['border_light']};
                    border-radius: 8px;
                }}
            """)
        if self._patient_band_ic:
            self._patient_band_ic.setPixmap(qta.icon("fa5s.user-injured", color=c['primary']).pixmap(15, 15))
        if self.lbl_patient_nom:
            self.lbl_patient_nom.setStyleSheet(
                f"font-size: 12px; font-weight: bold; color: {c['text_primary']}; border: none; background: transparent;"
            )
        if self.lbl_patient_code:
            self.lbl_patient_code.setStyleSheet(
                f"font-size: 10px; color: {c['text_muted']}; border: none; background: transparent;"
            )
        if self.btn_ajouter:
            self.btn_ajouter.setIcon(qta.icon("fa5s.plus", color=c['text_inverse']))
            self.btn_ajouter.setStyleSheet(f"""
                QPushButton {{
                    background: {c['primary']};
                    color: {c['text_inverse']};
                    border: none;
                    border-radius: 10px;
                    font-size: 13px;
                    font-weight: bold;
                    padding: 0 20px;
                }}
                QPushButton:hover {{ background: {c['primary_hover']}; }}
                QPushButton:disabled {{ background: {c['border']}; color: {c['text_muted']}; }}
            """)
        if self.combo_acte:
            self.combo_acte.setStyleSheet(PrescriptionStyles.combo_produit())
        if self.combo_produit:
            self.combo_produit.setStyleSheet(PrescriptionStyles.combo_produit())
        if self.edit_code_session:
            self.edit_code_session.setStyleSheet(PrescriptionStyles.input_readonly())
        if self.input_designation:
            self.input_designation.setStyleSheet(PrescriptionStyles.input_readonly())

    # API publique
    def charger_patient(self, nom: str, prenom: str, code_acte: str) -> None:
        """Auto-remplit la carte patient"""
        self.lbl_patient_nom.setText(f"{prenom} {nom}".strip())
        self.lbl_patient_code.setText(f"Acte: {code_acte}")
        self.btn_ajouter.setEnabled(True)

    def vider_patient(self) -> None:
        """Réinitialise l'affichage patient"""
        self.lbl_patient_nom.setText("— Sélectionnez un acte médical —")
        self.lbl_patient_code.setText("")
        self.btn_ajouter.setEnabled(False)

    def vider_formulaire(self) -> None:
        """Vide les champs produit"""
        self.combo_produit.setCurrentIndex(0)
        self.input_designation.clear()
        self.input_quantite.clear()
        self.input_prix.clear()

    def activer_formulaire(self) -> None:
        """Active les champs produit"""
        self.combo_produit.setEnabled(True)
        self.input_quantite.setEnabled(True)
        self.btn_ajouter.setEnabled(True)

    def desactiver_formulaire(self) -> None:
        """Désactive les champs produit"""
        self.combo_produit.setEnabled(False)
        self.input_quantite.setEnabled(False)
        self.btn_ajouter.setEnabled(False)
