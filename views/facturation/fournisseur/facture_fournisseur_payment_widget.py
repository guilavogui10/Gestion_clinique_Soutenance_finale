"""
Widget de paiement facture fournisseur - Style consultation avec icônes encadrées
"""

import logging
from datetime import datetime
import qtawesome as qta
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QComboBox, QLineEdit
)

from views.shared.theme_manager import theme_manager
from views.shared.message_box import CustomMessageBox
from models.modele_factureFournisseur import FactureFournisseur


class FactureFournisseurPaymentWidget(QWidget):
    paiement_valide = Signal(str)
    
    def __init__(self, facture_ctrl=None, fournisseur_ctrl=None, parent=None):
        super().__init__(parent)
        self.facture_ctrl = facture_ctrl
        self.fournisseur_ctrl = fournisseur_ctrl
        self.logger = logging.getLogger(__name__)
        
        self.code_facture_four = None
        self.code_fournisseur = None
        self.montant_total = 0.0
        
        self._init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Titre sans fond
        titre = QLabel("Informations de paiement")
        titre.setObjectName("MainTitle")
        layout.addWidget(titre)
        
        # Formulaire pleine largeur
        self._create_form_section(layout)
        
        layout.addStretch()
        
        # Boutons
        self._create_buttons(layout)
        
        self.apply_theme()
    
    def _create_form_section(self, parent_layout):
        # Card formulaire
        card = QFrame()
        card.setObjectName("FormCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(16)
        
        # Ligne 1
        row1 = QHBoxLayout()
        row1.setSpacing(16)
        self._add_field(row1, "Code facture", "code_facture", "fa5s.file-invoice", "#9b59b6", readonly=True)
        self._add_field(row1, "Montant total (GNF)", "montant", "fa5s.dollar-sign", "#27ae60", readonly=True)
        card_layout.addLayout(row1)
        
        # Ligne 2
        row2 = QHBoxLayout()
        row2.setSpacing(16)
        self._add_combo_field(row2, "Mode de paiement", "mode_paiement", "fa5s.credit-card", "#e67e22")
        self._add_field(row2, "Téléphone", "telephone", "fa5s.phone", "#3498db")
        card_layout.addLayout(row2)
        
        # Ligne 3
        row3 = QHBoxLayout()
        row3.setSpacing(16)
        self._add_field(row3, "Date facture", "date", "fa5s.calendar", "#1abc9c", readonly=True)
        self._add_field(row3, "Code session", "session", "fa5s.shield-alt", "#9b59b6", readonly=True)
        card_layout.addLayout(row3)
        
        parent_layout.addWidget(card)
    
    def _add_field(self, parent_layout, label_text, field_name, icon_name, icon_color, readonly=False):
        vbox = QVBoxLayout()
        vbox.setSpacing(6)
        
        label = QLabel(label_text)
        label.setObjectName("FieldLabel")
        vbox.addWidget(label)
        
        wrapper = QFrame()
        wrapper.setObjectName("FieldWrapper")
        wrapper.setFixedHeight(44)
        
        h_layout = QHBoxLayout(wrapper)
        h_layout.setContentsMargins(10, 0, 10, 0)
        h_layout.setSpacing(10)
        
        # Badge icône
        badge = QFrame()
        badge.setFixedSize(28, 28)
        badge.setStyleSheet(f"background-color: {icon_color}20; border-radius: 7px; border: none;")
        badge_layout = QHBoxLayout(badge)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(14, 14))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("border: none; background: transparent;")
        badge_layout.addWidget(icon_label)
        
        h_layout.addWidget(badge)
        
        # Input
        if readonly:
            value_label = QLabel("—")
            value_label.setObjectName("ReadonlyValue")
            h_layout.addWidget(value_label)
            setattr(self, f"lbl_{field_name}", value_label)
        else:
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"Entrez {label_text.lower()}")
            input_field.setStyleSheet("border: none; background: transparent; font-size: 13px;")
            h_layout.addWidget(input_field)
            setattr(self, f"input_{field_name}", input_field)
        
        h_layout.addStretch()
        vbox.addWidget(wrapper)
        parent_layout.addLayout(vbox, 1)
    
    def _add_combo_field(self, parent_layout, label_text, field_name, icon_name, icon_color):
        vbox = QVBoxLayout()
        vbox.setSpacing(6)
        
        label = QLabel(label_text)
        label.setObjectName("FieldLabel")
        vbox.addWidget(label)
        
        wrapper = QFrame()
        wrapper.setObjectName("FieldWrapper")
        wrapper.setFixedHeight(44)
        
        h_layout = QHBoxLayout(wrapper)
        h_layout.setContentsMargins(10, 0, 10, 0)
        h_layout.setSpacing(10)
        
        # Badge icône
        badge = QFrame()
        badge.setFixedSize(28, 28)
        badge.setStyleSheet(f"background-color: {icon_color}20; border-radius: 7px; border: none;")
        badge_layout = QHBoxLayout(badge)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(14, 14))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("border: none; background: transparent;")
        badge_layout.addWidget(icon_label)
        
        h_layout.addWidget(badge)
        
        # Combo
        combo = QComboBox()
        combo.addItem("Sélectionnez...", None)
        combo.addItem("Espèces", "especes")
        combo.addItem("Chèque", "cheque")
        combo.addItem("Virement", "virement")
        combo.addItem("Mobile Money", "mobile money")
        combo.setStyleSheet("border: none; background: transparent; font-size: 13px;")
        h_layout.addWidget(combo, 1)
        
        vbox.addWidget(wrapper)
        parent_layout.addLayout(vbox, 1)
        setattr(self, f"combo_{field_name}", combo)
    
    def _create_buttons(self, parent_layout):
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.btn_annuler = QPushButton("Annuler")
        self.btn_annuler.setFixedHeight(44)
        self.btn_annuler.setObjectName("BtnAnnuler")
        self.btn_annuler.setCursor(Qt.PointingHandCursor)
        self.btn_annuler.clicked.connect(self._annuler)
        
        self.btn_valider = QPushButton(qta.icon("fa5s.lock", color=theme_manager.colors()['text_inverse']), "  Valider le paiement")
        self.btn_valider.setFixedHeight(44)
        self.btn_valider.setObjectName("BtnValider")
        self.btn_valider.setCursor(Qt.PointingHandCursor)
        self.btn_valider.clicked.connect(self._valider_paiement)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_annuler)
        btn_layout.addWidget(self.btn_valider)
        
        parent_layout.addLayout(btn_layout)
    
    def charger_facture(self, code_facture_four: str):
        if not self.facture_ctrl:
            return
        
        try:
            facture = self.facture_ctrl.obtenir_par_code(code_facture_four)
            if not facture:
                CustomMessageBox.error(self, "Erreur", "Facture introuvable")
                return
            
            self.code_facture_four = code_facture_four
            self.code_fournisseur = facture.code_fournisseur
            self.montant_total = facture.montant_total or 0.0
            
            # Afficher
            self.lbl_code_facture.setText(code_facture_four)
            self.lbl_montant.setText(f"{self.montant_total:,.0f} GNF".replace(",", " "))
            
            # Date
            if facture.date_facture_four:
                date_str = facture.date_facture_four.strftime("%d/%m/%Y") if isinstance(facture.date_facture_four, datetime) else str(facture.date_facture_four)[:10]
                self.lbl_date.setText(date_str)
            
            # Session
            self.lbl_session.setText(facture.code_session or "—")
            
            # Reset
            self.combo_mode_paiement.setCurrentIndex(0)
            self.input_telephone.clear()
            
        except Exception as e:
            self.logger.error(f"Erreur: {e}", exc_info=True)
            CustomMessageBox.error(self, "Erreur", str(e))
    
    def _valider_paiement(self):
        if not self.code_facture_four:
            CustomMessageBox.warning(self, "Attention", "Aucune facture chargée")
            return
        
        mode_paiement = self.combo_mode_paiement.currentData()
        if not mode_paiement:
            CustomMessageBox.warning(self, "Attention", "Sélectionnez un mode de paiement")
            return
        
        telephone = self.input_telephone.text().strip()
        if not telephone:
            CustomMessageBox.warning(self, "Attention", "Saisissez un téléphone")
            return
        
        valide, msg = self.facture_ctrl.valider_telephone(telephone)
        if not valide:
            CustomMessageBox.warning(self, "Attention", msg)
            return
        
        facture = FactureFournisseur(
            code_facture_four=self.code_facture_four,
            mode_payement=mode_paiement,
            telephone=telephone
        )
        
        ok, msg = self.facture_ctrl.finaliser_facture(facture)
        
        if ok:
            CustomMessageBox.success(self, "Succès", f"Paiement validé!\n\nFacture: {self.code_facture_four}\nMontant: {self.montant_total:,.0f} GNF")
            self.paiement_valide.emit(self.code_facture_four)
            self._reinitialiser()
        else:
            CustomMessageBox.error(self, "Erreur", msg)
    
    def _annuler(self):
        self._reinitialiser()
    
    def _reinitialiser(self):
        self.code_facture_four = None
        self.lbl_code_facture.setText("—")
        self.lbl_montant.setText("—")
        self.lbl_date.setText("—")
        self.lbl_session.setText("—")
        self.combo_mode_paiement.setCurrentIndex(0)
        self.input_telephone.clear()
    
    def apply_theme(self):
        c = theme_manager.colors()
        
        self.setStyleSheet(f"""
            FactureFournisseurPaymentWidget {{
                background: {c['bg_main']};
                color: {c['text_primary']};
            }}
            
            QLabel#MainTitle {{
                font-size: 18px;
                font-weight: 700;
                color: {c['text_primary']};
                background: transparent;
            }}
            
            QLabel#FieldLabel {{
                font-size: 11px;
                font-weight: 600;
                color: {c['text_secondary']};
                background: transparent;
            }}
            
            QFrame#FormCard {{
                background: {c['bg_card']};
                border: 1.5px solid {c['border_light']};
                border-radius: 14px;
            }}
            
            QFrame#FieldWrapper {{
                background: {c['bg_input']};
                border: 1.5px solid {c['border']};
                border-radius: 10px;
            }}
            
            QLabel#ReadonlyValue {{
                font-size: 13px;
                color: {c['text_primary']};
                background: transparent;
            }}
            
            QLabel#SummaryLabel {{
                font-size: 13px;
                font-weight: 600;
                color: {c['text_secondary']};
            }}
            
            QLabel#SummaryValue {{
                font-size: 14px;
                font-weight: 600;
                color: {c['text_primary']};
                margin-bottom: 8px;
            }}
            
            QPushButton#BtnValider {{
                background: {c['primary']};
                color: {c['text_inverse']};
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 700;
            }}
            
            QPushButton#BtnValider:hover {{
                background: {c['primary_hover']};
            }}
            
            QPushButton#BtnAnnuler {{
                background: {c['bg_card']};
                color: {c['text_secondary']};
                border: 1.5px solid {c['border']};
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
            }}
            
            QPushButton#BtnAnnuler:hover {{
                background: {c['hover']};
            }}
        """)
