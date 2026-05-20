"""
Widget de paiement pour les factures fournisseurs.
Responsabilité : Finaliser le paiement d'une facture fournisseur.
"""

import logging
from typing import Optional
from datetime import datetime

import qtawesome as qta
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QComboBox, QLineEdit, QGroupBox, QTextEdit
)

from views.shared.theme_manager import theme_manager
from views.shared.message_box import CustomMessageBox
from models.modele_factureFournisseur import FactureFournisseur


class FactureFournisseurPaymentWidget(QWidget):
    """
    Widget de paiement pour finaliser une facture fournisseur.
    
    Workflow :
    1. Afficher les infos de la facture (fournisseur, montant)
    2. Saisir le mode de paiement et le téléphone
    3. Valider le paiement
    """
    
    # Signal émis quand le paiement est validé
    paiement_valide = Signal(str)  # code_facture_four
    
    def __init__(self, facture_ctrl=None, fournisseur_ctrl=None, parent=None):
        super().__init__(parent)
        self.facture_ctrl = facture_ctrl
        self.fournisseur_ctrl = fournisseur_ctrl
        self.logger = logging.getLogger(__name__)
        
        self.code_facture_four = None
        self.code_fournisseur = None
        self.montant_total = 0.0
        
        self._init_ui()
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)
    
    def _init_ui(self):
        """Initialise l'interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(30)
        
        # Colonne gauche : Formulaire
        left_column = QVBoxLayout()
        left_column.setSpacing(20)
        
        # Titre
        titre = QLabel("Informations de paiement")
        titre.setObjectName("SectionTitle")
        left_column.addWidget(titre)
        
        # Formulaire en grille 2x3
        form_container = QWidget()
        form_container.setStyleSheet("background: transparent;")
        grid_layout = QVBoxLayout(form_container)
        grid_layout.setSpacing(16)
        
        # Ligne 1 : Code facture + Code fournisseur
        row1 = QHBoxLayout()
        row1.setSpacing(16)
        row1_left = QVBoxLayout()
        self._add_readonly_field(row1_left, "Code facture fournisseur", "code_facture")
        row1_right = QVBoxLayout()
        self._add_combo_field(row1_right, "Code fournisseur", "fournisseur")
        row1.addLayout(row1_left, 1)
        row1.addLayout(row1_right, 1)
        grid_layout.addLayout(row1)
        
        # Ligne 2 : Montant total + Mode de paiement
        row2 = QHBoxLayout()
        row2.setSpacing(16)
        row2_left = QVBoxLayout()
        self._add_readonly_field(row2_left, "Montant total (FCFA)", "montant")
        row2_right = QVBoxLayout()
        self._add_combo_field(row2_right, "Mode de paiement", "mode_paiement")
        row2.addLayout(row2_left, 1)
        row2.addLayout(row2_right, 1)
        grid_layout.addLayout(row2)
        
        # Ligne 3 : Téléphone + Date facture
        row3 = QHBoxLayout()
        row3.setSpacing(16)
        row3_left = QVBoxLayout()
        self._add_input_field(row3_left, "Téléphone", "telephone", "fa5s.phone", "Entrez le numéro de téléphone")
        row3_right = QVBoxLayout()
        self._add_readonly_field(row3_right, "Date facture fournisseur", "date")
        row3.addLayout(row3_left, 1)
        row3.addLayout(row3_right, 1)
        grid_layout.addLayout(row3)
        
        # Ligne 4 : Code session (pleine largeur)
        row4 = QVBoxLayout()
        self._add_readonly_field(row4, "Code session", "session")
        grid_layout.addLayout(row4)
        
        left_column.addWidget(form_container)
        left_column.addStretch()
        
        # Boutons d'action
        self._create_action_buttons(left_column)
        
        # Colonne droite : Récapitulatif
        right_column = self._create_summary_panel()
        
        # Ajouter les colonnes au layout principal
        layout.addLayout(left_column, 6)
        layout.addLayout(right_column, 4)
    
    def _add_readonly_field(self, parent_layout, label_text, field_name):
        """Ajoute un champ en lecture seule."""
        field_layout = QVBoxLayout()
        field_layout.setSpacing(8)
        
        label = QLabel(label_text)
        label.setObjectName("FieldLabel")
        field_layout.addWidget(label)
        
        input_container = QFrame()
        input_container.setObjectName("ReadonlyField")
        input_container.setFixedHeight(48)
        
        container_layout = QHBoxLayout(input_container)
        container_layout.setContentsMargins(16, 0, 16, 0)
        container_layout.setSpacing(10)
        
        # Icône
        icon_map = {
            "code_facture": "fa5s.file-invoice",
            "montant": "fa5s.dollar-sign",
            "date": "fa5s.calendar",
            "session": "fa5s.shield-alt"
        }
        
        if field_name in icon_map:
            icon_label = QLabel()
            icon_label.setPixmap(qta.icon(icon_map[field_name], color="#9CA3AF").pixmap(QSize(18, 18)))
            container_layout.addWidget(icon_label)
        
        value_label = QLabel("—")
        value_label.setObjectName("ReadonlyValue")
        container_layout.addWidget(value_label)
        container_layout.addStretch()
        
        field_layout.addWidget(input_container)
        parent_layout.addLayout(field_layout)
        
        # Stocker la référence
        setattr(self, f"lbl_{field_name}", value_label)
    
    def _add_combo_field(self, parent_layout, label_text, field_name):
        """Ajoute un champ combo."""
        field_layout = QVBoxLayout()
        field_layout.setSpacing(8)
        
        label = QLabel(label_text)
        label.setObjectName("FieldLabel")
        field_layout.addWidget(label)
        
        combo = QComboBox()
        combo.setFixedHeight(48)
        combo.setObjectName("ComboField")
        
        if field_name == "fournisseur":
            combo.addItem("Sélectionnez un fournisseur", None)
            self.combo_fournisseur = combo
        elif field_name == "mode_paiement":
            combo.addItem("Sélectionnez le mode de paiement", None)
            combo.addItem("Espèces", "especes")
            combo.addItem("Chèque", "cheque")
            combo.addItem("Virement", "virement")
            combo.addItem("Mobile Money", "mobile money")
            self.combo_mode_paiement = combo
        
        field_layout.addWidget(combo)
        parent_layout.addLayout(field_layout)
    
    def _add_input_field(self, parent_layout, label_text, field_name, icon_name, placeholder):
        """Ajoute un champ de saisie."""
        field_layout = QVBoxLayout()
        field_layout.setSpacing(8)
        
        label = QLabel(label_text)
        label.setObjectName("FieldLabel")
        field_layout.addWidget(label)
        
        input_container = QFrame()
        input_container.setObjectName("InputField")
        input_container.setFixedHeight(48)
        
        container_layout = QHBoxLayout(input_container)
        container_layout.setContentsMargins(16, 0, 16, 0)
        container_layout.setSpacing(10)
        
        # Icône
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color="#9CA3AF").pixmap(QSize(18, 18)))
        container_layout.addWidget(icon_label)
        
        # Input
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setStyleSheet("border: none; background: transparent; font-size: 14px;")
        container_layout.addWidget(input_field)
        
        field_layout.addWidget(input_container)
        parent_layout.addLayout(field_layout)
        
        # Stocker la référence
        if field_name == "telephone":
            self.input_telephone = input_field
    
    def _create_summary_panel(self):
        """Crée le panneau récapitulatif à droite."""
        right_layout = QVBoxLayout()
        right_layout.setSpacing(20)
        
        # Titre avec icône
        header_layout = QHBoxLayout()
        titre = QLabel("Récapitulatif du paiement")
        titre.setObjectName("SectionTitle")
        
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon("fa5s.receipt", color="#3B82F6").pixmap(QSize(20, 20)))
        
        header_layout.addWidget(titre)
        header_layout.addStretch()
        header_layout.addWidget(icon_label)
        right_layout.addLayout(header_layout)
        
        # Carte récapitulatif
        summary_card = QFrame()
        summary_card.setObjectName("SummaryCard")
        card_layout = QVBoxLayout(summary_card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(20)
        
        # Fournisseur
        fournisseur_label = QLabel("Fournisseur")
        fournisseur_label.setObjectName("SummaryLabel")
        card_layout.addWidget(fournisseur_label)
        
        self.lbl_summary_fournisseur = QLabel("—")
        self.lbl_summary_fournisseur.setObjectName("SummaryValue")
        card_layout.addWidget(self.lbl_summary_fournisseur)
        
        # Code facture
        code_label = QLabel("Code facture")
        code_label.setObjectName("SummaryLabel")
        card_layout.addWidget(code_label)
        
        self.lbl_summary_code = QLabel("—")
        self.lbl_summary_code.setObjectName("SummaryValue")
        card_layout.addWidget(self.lbl_summary_code)
        
        # Montant total (mis en évidence)
        montant_label = QLabel("Montant total")
        montant_label.setObjectName("SummaryLabel")
        card_layout.addWidget(montant_label)
        
        self.lbl_summary_montant = QLabel("0 FCFA")
        self.lbl_summary_montant.setObjectName("SummaryMontant")
        card_layout.addWidget(self.lbl_summary_montant)
        
        # Mode de paiement
        mode_label = QLabel("Mode de paiement")
        mode_label.setObjectName("SummaryLabel")
        card_layout.addWidget(mode_label)
        
        self.lbl_summary_mode = QLabel("—")
        self.lbl_summary_mode.setObjectName("SummaryValue")
        card_layout.addWidget(self.lbl_summary_mode)
        
        card_layout.addStretch()
        
        right_layout.addWidget(summary_card)
        right_layout.addStretch()
        
        return right_layout
    

    
    def _create_action_buttons(self, parent_layout):
        """Crée les boutons d'action."""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.btn_annuler = QPushButton("Annuler")
        self.btn_annuler.setFixedHeight(48)
        self.btn_annuler.setObjectName("BtnAnnuler")
        self.btn_annuler.setCursor(Qt.PointingHandCursor)
        self.btn_annuler.clicked.connect(self._annuler)
        
        self.btn_valider = QPushButton("  Valider le paiement")
        self.btn_valider.setIcon(qta.icon("fa5s.lock", color="#ffffff"))
        self.btn_valider.setFixedHeight(48)
        self.btn_valider.setObjectName("BtnValider")
        self.btn_valider.setCursor(Qt.PointingHandCursor)
        self.btn_valider.clicked.connect(self._valider_paiement)
        
        btn_layout.addWidget(self.btn_annuler, 1)
        btn_layout.addWidget(self.btn_valider, 2)
        
        parent_layout.addLayout(btn_layout)
    
    def charger_facture(self, code_facture_four: str):
        """Charge les données d'une facture pour paiement."""
        if not self.facture_ctrl:
            self.logger.error("Contrôleur facture non initialisé")
            return
        
        try:
            facture = self.facture_ctrl.obtenir_par_code(code_facture_four)
            
            if not facture:
                CustomMessageBox.error(self, "Erreur", "Facture introuvable")
                return
            
            self.code_facture_four = code_facture_four
            self.code_fournisseur = facture.code_fournisseur
            self.montant_total = facture.montant_total or 0.0
            
            # Afficher les infos
            self.lbl_code_facture.setText(code_facture_four)
            self.lbl_montant.setText(f"{self.montant_total:,.0f} GNF".replace(",", " "))
            
            # Récapitulatif
            self.lbl_summary_code.setText(code_facture_four)
            self.lbl_summary_montant.setText(f"{self.montant_total:,.0f} GNF".replace(",", " "))
            self.lbl_summary_mode.setText("—")
            
            # Charger le nom du fournisseur
            if self.fournisseur_ctrl:
                fournisseur = self.fournisseur_ctrl.obtenir_par_code(self.code_fournisseur)
                if fournisseur:
                    # Le contrôleur peut retourner un dict ou un objet
                    if isinstance(fournisseur, dict):
                        nom = fournisseur.get('nom_entreprise', self.code_fournisseur)
                        self.lbl_summary_fournisseur.setText(nom)
                    else:
                        self.lbl_summary_fournisseur.setText(fournisseur.nom_entreprise)
                else:
                    self.lbl_summary_fournisseur.setText(self.code_fournisseur)
            else:
                self.lbl_summary_fournisseur.setText(self.code_fournisseur)
            
            # Date
            if facture.date_facture_four:
                if isinstance(facture.date_facture_four, datetime):
                    self.lbl_date.setText(facture.date_facture_four.strftime("%d/%m/%Y"))
                else:
                    self.lbl_date.setText(str(facture.date_facture_four)[:10])
            
            # Session
            self.lbl_session.setText(facture.code_session or "—")
            
            # Réinitialiser le formulaire
            self.combo_mode_paiement.setCurrentIndex(0)
            self.input_telephone.clear()
            
        except Exception as e:
            self.logger.error(f"Erreur chargement facture: {e}", exc_info=True)
            CustomMessageBox.error(self, "Erreur", f"Erreur lors du chargement:\n{str(e)}")
    
    def _valider_paiement(self):
        """Valide le paiement de la facture."""
        if not self.code_facture_four:
            CustomMessageBox.warning(self, "Attention", "Aucune facture chargée")
            return
        
        # Validation des champs
        mode_paiement = self.combo_mode_paiement.currentData()
        if not mode_paiement:
            CustomMessageBox.warning(self, "Attention", "Veuillez sélectionner un mode de paiement")
            self.combo_mode_paiement.setFocus()
            return
        
        telephone = self.input_telephone.text().strip()
        if not telephone:
            CustomMessageBox.warning(self, "Attention", "Veuillez saisir un numéro de téléphone")
            self.input_telephone.setFocus()
            return
        
        # Validation du téléphone
        valide, msg = self.facture_ctrl.valider_telephone(telephone)
        if not valide:
            CustomMessageBox.warning(self, "Attention", msg)
            self.input_telephone.setFocus()
            return
        
        # Créer l'objet facture pour finalisation
        facture = FactureFournisseur(
            code_facture_four=self.code_facture_four,
            mode_payement=mode_paiement,
            telephone=telephone
        )
        
        # Finaliser la facture
        ok, msg = self.facture_ctrl.finaliser_facture(facture)
        
        if ok:
            CustomMessageBox.success(
                self, 
                "Succès", 
                f"Paiement validé avec succès!\n\nFacture: {self.code_facture_four}\nMontant: {self.montant_total:,.0f} GNF"
            )
            self.paiement_valide.emit(self.code_facture_four)
            self._reinitialiser()
        else:
            CustomMessageBox.error(self, "Erreur", msg)
    
    def _annuler(self):
        """Annule le paiement."""
        self._reinitialiser()
    
    def _reinitialiser(self):
        """Réinitialise le formulaire."""
        self.code_facture_four = None
        self.code_fournisseur = None
        self.montant_total = 0.0
        
        self.lbl_code_facture.setText("—")
        self.lbl_montant.setText("—")
        self.lbl_date.setText("—")
        self.lbl_session.setText("—")
        
        self.lbl_summary_code.setText("—")
        self.lbl_summary_fournisseur.setText("—")
        self.lbl_summary_montant.setText("0 GNF")
        self.lbl_summary_mode.setText("—")
        
        self.combo_mode_paiement.setCurrentIndex(0)
        self.input_telephone.clear()
    
    def apply_theme(self):
        """Applique le thème actif."""
        c = theme_manager.colors()
        
        self.setStyleSheet(f"""
            QWidget {{
                background: {c['bg_main']};
                color: {c['text_primary']};
            }}
            
            QLabel#SectionTitle {{
                font-size: 16px;
                font-weight: 700;
                color: {c['text_primary']};
                margin-bottom: 4px;
            }}
            
            QLabel#FieldLabel {{
                font-size: 13px;
                font-weight: 600;
                color: {c['text_secondary']};
            }}
            
            QFrame#ReadonlyField {{
                background: transparent;
                border: 1px solid {c['border']};
                border-radius: 10px;
            }}
            
            QLabel#ReadonlyValue {{
                font-size: 14px;
                color: {c['text_primary']};
                background: transparent;
            }}
            
            QFrame#InputField {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
            }}
            
            QFrame#InputField:focus-within {{
                border: 2px solid {c['primary']};
            }}
            
            QComboBox#ComboField {{
                background: transparent;
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 0 16px;
                color: {c['text_primary']};
                font-size: 14px;
            }}
            
            QComboBox#ComboField:focus {{
                border: 2px solid {c['primary']};
            }}
            
            QComboBox#ComboField::drop-down {{
                border: none;
                width: 30px;
            }}
            
            QComboBox#ComboField::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {c['text_secondary']};
                margin-right: 10px;
            }}
            
            QComboBox#ComboField QAbstractItemView {{
                background: white;
                color: {c['text_primary']};
                selection-background-color: {c['primary']};
                selection-color: white;
                border: 1px solid {c['border']};
            }}
            
            QFrame#SummaryCard {{
                background: {c['bg_card']};
                border: 1px solid {c['border_light']};
                border-radius: 16px;
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
                margin-bottom: 12px;
            }}
            
            QLabel#SummaryMontant {{
                font-size: 28px;
                font-weight: 700;
                color: {c['primary']};
                margin-bottom: 12px;
            }}
            
            QLabel#SecurityTitle {{
                font-size: 13px;
                font-weight: 700;
                color: {c['text_primary']};
            }}
            
            QLabel#SecurityText {{
                font-size: 11px;
                color: {c['text_muted']};
                line-height: 1.4;
            }}
            
            QPushButton#BtnValider {{
                background: {c['primary']};
                color: {c['text_inverse']};
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 700;
                padding: 0 24px;
            }}
            
            QPushButton#BtnValider:hover {{
                background: {c['primary_hover']};
            }}
            
            QPushButton#BtnAnnuler {{
                background: {c['bg_card']};
                color: {c['text_secondary']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
                padding: 0 24px;
            }}
            
            QPushButton#BtnAnnuler:hover {{
                background: {c['hover']};
                border-color: {c['danger']};
                color: {c['danger']};
            }}
        """)
