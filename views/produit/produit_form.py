from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QFrame, 
                             QGraphicsDropShadowEffect, QDoubleSpinBox)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QColor, QPixmap
import qtawesome as qta
import os
from models.modele_produits import Produit
from views.shared.message_box import CustomMessageBox
from views.shared.theme_manager import theme_manager


class ProduitFormDialog(QDialog):
    """
    Formulaire moderne pour la gestion des produits pharmaceutiques.
    Design ultra-optimisé avec validation en temps réel.
    Pattern MVC : Utilise le contrôleur pour toutes les validations.
    """
    
    def __init__(self, controleur, produit_obj=None, parent=None):
        super().__init__(parent)
        self.controleur = controleur
        self.produit_obj = produit_obj
        self.info_cabinet = self.controleur.get_cabinet_info()
        
        # Configuration fenêtre moderne
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(600, 580)
        
        self.init_ui()
        
        # ═══════════════════════════════════════════════════════════════
        # CONNEXION DES VALIDATIONS EN TEMPS RÉEL
        # ═══════════════════════════════════════════════════════════════
        self.edit_libelle.textChanged.connect(self.valider_libelle)
        self.edit_prix_achat.valueChanged.connect(self.valider_prix_achat)
        self.edit_prix_vente.valueChanged.connect(self.valider_prix_vente)
        
        if self.produit_obj:
            self.remplir_champs()
        theme_manager.theme_changed.connect(self.apply_theme)
    
    def init_ui(self):
        """Construction de l'interface ultra-moderne."""
        self.main_layout = QVBoxLayout(self)
        self.container = QFrame()
        self.container.setObjectName("MainContainer")
        
        self._apply_container_style()
        
        # Ombre portée élégante
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.container.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 30)
        layout.setSpacing(0)
        
        # ═══════════════════════════════════════════════════════════════
        # HEADER ÉLÉGANT
        # ═══════════════════════════════════════════════════════════════
        self._setup_header(layout)
        
        # Séparateur design
        self._add_separator(layout)

        body = QVBoxLayout()
        body.setContentsMargins(35, 12, 35, 0)
        body.setSpacing(8)
        
        # ═══════════════════════════════════════════════════════════════
        # FORMULAIRE AVEC SECTIONS
        # ═══════════════════════════════════════════════════════════════
        
        # Section 1 : Informations générales
        section1 = QLabel("📋 Informations Générales")
        section1.setObjectName("SectionTitle")
        body.addWidget(section1)
        
        # Libellé du produit
        self.edit_libelle = self._add_field_with_icon(
            body, "Libellé du produit", "fa5s.pills", 
            "Ex: Paracétamol 500mg, Collyre..."
        )
        
        # Type de produit avec icônes personnalisées
        c = theme_manager.colors()
        type_layout = QVBoxLayout()
        type_layout.setSpacing(6)
        
        lbl_type = QLabel("Type de produit")
        lbl_type.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']};")
        type_layout.addWidget(lbl_type)
        
        self.combo_type = QComboBox()
        self.combo_type.addItem(qta.icon("fa5s.tint", color=c['info']), "Liquide", "liquide")
        self.combo_type.addItem(qta.icon("fa5s.hand-holding-medical", color=c['warning']), "Pommade", "pommade")
        self.combo_type.addItem(qta.icon("fa5s.tablets", color=c['accent']), "Comprimé", "comprime")
        self.combo_type.setFixedHeight(48)
        self.combo_type.currentIndexChanged.connect(self.valider_type_produit)
        type_layout.addWidget(self.combo_type)
        
        # Label erreur type
        self.err_type = QLabel("")
        self.err_type.setStyleSheet(f"color: {c['danger']}; font-size: 10px; font-style: italic;")
        self.err_type.setVisible(False)
        type_layout.addWidget(self.err_type)
        
        body.addLayout(type_layout)
        body.addSpacing(8)
        
        # Section 2 : Tarification
        section2 = QLabel("💰 Tarification")
        section2.setObjectName("SectionTitle")
        body.addWidget(section2)
        
        # Prix en ligne (côte à côte)
        prix_row = QHBoxLayout()
        prix_row.setSpacing(15)
        
        # Prix d'achat
        self.edit_prix_achat = self._add_price_field(
            prix_row, "Prix d'achat unitaire (GNF)", "fa5s.shopping-cart"
        )
        
        # Prix de vente
        self.edit_prix_vente = self._add_price_field(
            prix_row, "Prix de vente unitaire (GNF)", "fa5s.cash-register"
        )
        
        body.addLayout(prix_row)
        
        # Indicateur de marge bénéficiaire (design moderne)
        self.lbl_marge = QLabel("")
        self.lbl_marge.setStyleSheet(f"""
            background-color: {c['info_bg']};
            color: {c['info']};
            padding: 10px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 12px;
        """)
        self.lbl_marge.setVisible(False)
        body.addWidget(self.lbl_marge)
        
        body.addSpacing(15)
        
        # ═══════════════════════════════════════════════════════════════
        # BOUTONS D'ACTION
        # ═══════════════════════════════════════════════════════════════
        actions = QHBoxLayout()
        actions.setSpacing(12)
        
        self.btn_cancel = QPushButton(qta.icon("fa5s.times", color=theme_manager.colors()['text_secondary']), " Annuler")
        self.btn_cancel.setObjectName("CancelBtn")
        self.btn_cancel.setFixedHeight(48)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton(
            qta.icon("fa5s.check-circle", color="white"), 
            " Enregistrer le produit"
        )
        self.btn_save.setObjectName("SaveBtn")
        self.btn_save.setFixedHeight(48)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setEnabled(False if not self.produit_obj else True)
        self.btn_save.clicked.connect(self.soumettre)
        
        actions.addWidget(self.btn_cancel, 1)
        actions.addWidget(self.btn_save, 2)
        body.addLayout(actions)

        layout.addLayout(body)
        self.main_layout.addWidget(self.container)

    def _apply_container_style(self):
        c = theme_manager.colors()
        self.container.setStyleSheet(f"""
            QFrame#MainContainer {{
                background-color: {c['bg_card']}; border-radius: 22px; border: 2px solid {c['border']};
            }}
            QLabel {{ color: {c['text_primary']}; font-size: 13px; background-color: transparent; }}
            QLabel#CabinetName {{ font-size: 22px; font-weight: bold; color: {c['danger']}; background-color: transparent; }}
            QLabel#SectionTitle {{ font-size: 16px; font-weight: bold; color: {c['primary']}; background-color: transparent; padding: 8px 0px; }}
            QLineEdit, QComboBox, QDoubleSpinBox {{
                padding: 12px 12px 12px 42px; border: 2px solid {c['border']}; border-radius: 10px;
                background-color: {c['bg_input']}; font-size: 14px; color: {c['text_primary']};
            }}
            QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {{
                border: 2px solid {c['border_focus']}; background-color: {c['bg_card']};
            }}
            QComboBox::drop-down {{ border: none; width: 35px; background: transparent; }}
            QComboBox::down-arrow {{ image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid {c['primary']}; }}
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ width: 0px; }}
            QPushButton#SaveBtn {{
                background-color: {c['primary']}; color: {c['text_inverse']}; border-radius: 12px;
                font-weight: bold; font-size: 15px; padding: 5px;
            }}
            QPushButton#SaveBtn:hover {{ background-color: {c['hover']}; }}
            QPushButton#SaveBtn:disabled {{ background-color: {c['border_light']}; color: {c['text_muted']}; }}
            QPushButton#CancelBtn {{
                background-color: {c['bg_main']}; color: {c['text_secondary']}; border-radius: 12px;
                font-weight: bold; font-size: 14px; border: 1px solid {c['border']};
            }}
            QPushButton#CancelBtn:hover {{ background-color: {c['bg_input']}; }}
        """)

    def apply_theme(self):
        c = theme_manager.colors()
        self._apply_container_style()
        if hasattr(self, '_header_card'):
            self._header_card.setStyleSheet(f"QFrame {{ border: none; border-top-left-radius: 20px; border-top-right-radius: 20px; background: {c['bg_card']}; }}")
        if hasattr(self, '_title_form'):
            self._title_form.setStyleSheet(f"color: {c['primary']}; font-size: 21px; font-weight: 900; letter-spacing: 0.8px;")
        if hasattr(self, '_accent'):
            self._accent.setStyleSheet(f"background: {c['border_focus']}; border: none;")
        # Icônes combo type
        if hasattr(self, 'combo_type'):
            self.combo_type.setItemIcon(0, qta.icon("fa5s.tint", color=c['info']))
            self.combo_type.setItemIcon(1, qta.icon("fa5s.hand-holding-medical", color=c['warning']))
            self.combo_type.setItemIcon(2, qta.icon("fa5s.tablets", color=c['accent']))
        # Bouton annuler
        if hasattr(self, 'btn_cancel'):
            self.btn_cancel.setIcon(qta.icon("fa5s.times", color=c['text_secondary']))
        # Marge
        if hasattr(self, 'lbl_marge') and self.lbl_marge.isVisible():
            self.calculer_marge()
    
    def _setup_header(self, layout):
        """Header avec logo et nom du cabinet."""
        header_card = QFrame()
        self._header_card = header_card
        c = theme_manager.colors()
        header_card.setStyleSheet(f"""
            QFrame {{
                border: none;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                background: {c['bg_card']};
            }}
        """)
        header_container = QVBoxLayout(header_card)
        header_container.setContentsMargins(24, 16, 24, 10)
        header_container.setSpacing(8)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        
        # Infos cabinet
        cabinet_layout = QVBoxLayout()
        cabinet_layout.setSpacing(2)
        
        name_cab = QLabel(self.info_cabinet.get("nom_cabinet", "Cabinet Médical"))
        name_cab.setObjectName("CabinetName")
        name_cab.setWordWrap(True)
        
        addr_cab = QLabel(self.info_cabinet.get("adresse_cabinet", ""))
        addr_cab.setStyleSheet(f"color: {c['text_muted']}; font-size: 12px; background: transparent;")
        
        cabinet_layout.addWidget(name_cab)
        cabinet_layout.addWidget(addr_cab)
        
        header.addLayout(cabinet_layout, 4)
        header.addStretch(1)
        
        # Logo
        logo_path = self.info_cabinet.get('logo_url')
        if logo_path and os.path.exists(logo_path):
            logo_lbl = QLabel()
            logo_lbl.setStyleSheet("background: transparent;")
            pix = QPixmap(logo_path).scaled(75, 75, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            logo_lbl.setAlignment(Qt.AlignCenter)
            header.addWidget(logo_lbl)

        header_container.addLayout(header)

        title_form = QLabel("FORMULAIRE PRODUIT")
        self._title_form = title_form
        title_form.setAlignment(Qt.AlignCenter)
        title_form.setStyleSheet(
            f"color: {c['primary']}; font-size: 21px; font-weight: 900; letter-spacing: 0.8px;"
        )
        header_container.addWidget(title_form)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {c['border_light']};")
        header_container.addWidget(line)

        accent = QFrame()
        self._accent = accent
        accent.setFixedHeight(6)
        accent.setStyleSheet(f"background: {c['border_focus']}; border: none;")
        header_container.addWidget(accent)

        layout.addWidget(header_card)
    
    def _add_separator(self, layout):
        """Ajoute un séparateur élégant."""
        return
    
    def _add_field_with_icon(self, layout, label_text, icon_name, placeholder):
        """Crée un champ avec icône, label et validation."""
        vbox = QVBoxLayout()
        vbox.setSpacing(6)
        c = theme_manager.colors()
        
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']};")
        vbox.addWidget(lbl)
        
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setFixedHeight(48)
        
        icon = qta.icon(icon_name, color=c['primary'])
        icon_label = QLabel(edit)
        icon_label.setPixmap(icon.pixmap(20, 20))
        icon_label.move(12, 14)
        icon_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        icon_label.setStyleSheet("background: transparent;")
        
        vbox.addWidget(edit)
        
        err_lbl = QLabel("")
        err_lbl.setStyleSheet(f"color: {c['danger']}; font-size: 10px; font-style: italic;")
        err_lbl.setVisible(False)
        vbox.addWidget(err_lbl)
        
        edit.error_label = err_lbl
        layout.addLayout(vbox)
        
        return edit
    
    def _add_price_field(self, layout, label_text, icon_name):
        """Crée un champ de prix avec validation."""
        vbox = QVBoxLayout()
        vbox.setSpacing(6)
        c = theme_manager.colors()
        
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"font-weight: bold; color: {c['text_secondary']}; font-size: 12px;")
        vbox.addWidget(lbl)
        
        spin = QDoubleSpinBox()
        spin.setRange(0.01, 999999999.99)
        spin.setDecimals(2)
        spin.setSingleStep(100)
        spin.setFixedHeight(48)
        spin.setAlignment(Qt.AlignRight)
        
        icon = qta.icon(icon_name, color=c['primary'])
        icon_label = QLabel(spin)
        icon_label.setPixmap(icon.pixmap(18, 18))
        icon_label.move(12, 15)
        icon_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        icon_label.setStyleSheet("background: transparent;")
        
        vbox.addWidget(spin)
        
        err_lbl = QLabel("")
        err_lbl.setStyleSheet(f"color: {c['danger']}; font-size: 10px; font-style: italic;")
        err_lbl.setVisible(False)
        vbox.addWidget(err_lbl)
        
        spin.error_label = err_lbl
        layout.addLayout(vbox)
        
        return spin
    
    def remplir_champs(self):
        """Remplit le formulaire en mode modification."""
        self.btn_save.setText(" Mettre à jour le produit")
        self.edit_libelle.setText(self.produit_obj.get_libelle())
        
        # Type
        type_map = {"liquide": 0, "pommade": 1, "comprime": 2}
        idx = type_map.get(self.produit_obj.get_type().lower(), 0)
        self.combo_type.setCurrentIndex(idx)
        
        # Prix
        self.edit_prix_achat.setValue(float(self.produit_obj.get_prix_achat_unitaire()))
        self.edit_prix_vente.setValue(float(self.produit_obj.get_prix_vente_unitaire()))
        
        # Calcul marge initiale
        self.calculer_marge()
    
    def soumettre(self):
        """Enregistrement avec validation finale."""
        nouveau_produit = Produit(
            code_produit=self.produit_obj.get_code_produit() if self.produit_obj else "",
            libelle=self.edit_libelle.text().strip(),
            type_produit=self.combo_type.currentData(),
            prix_achat_unitaire=self.edit_prix_achat.value(),
            prix_vente_unitaire=self.edit_prix_vente.value()
        )
        
        if self.produit_obj:
            ok, msg = self.controleur.modifier_produit(nouveau_produit)
        else:
            ok, msg = self.controleur.creer_produit(nouveau_produit)
        
        if ok:
            self.show_message(True, "Le produit a été enregistré avec succès !")
            self.accept()
        else:
            self.show_message(False, f"Erreur : {msg}")
    
    # ═══════════════════════════════════════════════════════════════════
    # VALIDATIONS EN TEMPS RÉEL
    # ═══════════════════════════════════════════════════════════════════
    
    def valider_libelle(self):
        """Validation du libellé en temps réel."""
        texte = self.edit_libelle.text()
        valide, msg = self.controleur.valider_texte(texte, "libellé", 3)
        cv = theme_manager.colors()
        
        if not valide and texte != "":
            self.edit_libelle.setStyleSheet(f"""
                border: 2px solid {cv['danger']}; 
                background-color: {cv['danger_bg']};
                padding: 12px 12px 12px 42px;
                border-radius: 10px;
            """)
            self.edit_libelle.error_label.setText(msg)
            self.edit_libelle.error_label.setVisible(True)
        elif not valide and texte == "":
            self.edit_libelle.setStyleSheet(f"""
                border: 2px solid {cv['border']};
                background-color: {cv['bg_card']};
                padding: 12px 12px 12px 42px;
                border-radius: 10px;
            """)
            self.edit_libelle.error_label.setVisible(False)
        else:
            self.edit_libelle.setStyleSheet(f"""
                border: 2px solid {cv['border_focus']};
                background-color: {cv['bg_card']};
                padding: 12px 12px 12px 42px;
                border-radius: 10px;
            """)
            self.edit_libelle.error_label.setVisible(False)
        
        self.verifier_formulaire_complet()
    
    def valider_type_produit(self):
        """Validation du type."""
        type_val = self.combo_type.currentData()
        valide, msg = self.controleur.valider_type(type_val)
        
        if not valide:
            self.err_type.setText(msg)
            self.err_type.setVisible(True)
        else:
            self.err_type.setVisible(False)
        
        self.verifier_formulaire_complet()
    
    def valider_prix_achat(self):
        """Validation du prix d'achat."""
        prix = self.edit_prix_achat.value()
        valide, msg = self.controleur.valider_prix(prix, "prix d'achat")
        cv = theme_manager.colors()
        
        if not valide:
            self.edit_prix_achat.setStyleSheet(f"""
                border: 2px solid {cv['danger']};
                background-color: {cv['danger_bg']};
                padding: 12px 12px 12px 42px;
                border-radius: 10px;
            """)
            self.edit_prix_achat.error_label.setText(msg)
            self.edit_prix_achat.error_label.setVisible(True)
        else:
            self.edit_prix_achat.setStyleSheet(f"""
                border: 2px solid {cv['border_focus']};
                background-color: {cv['bg_card']};
                padding: 12px 12px 12px 42px;
                border-radius: 10px;
            """)
            self.edit_prix_achat.error_label.setVisible(False)
        
        self.calculer_marge()
        self.verifier_formulaire_complet()
    
    def valider_prix_vente(self):
        """Validation du prix de vente."""
        prix = self.edit_prix_vente.value()
        valide, msg = self.controleur.valider_prix(prix, "prix de vente")
        cv = theme_manager.colors()
        
        if not valide:
            self.edit_prix_vente.setStyleSheet(f"""
                border: 2px solid {cv['danger']};
                background-color: {cv['danger_bg']};
                padding: 12px 12px 12px 42px;
                border-radius: 10px;
            """)
            self.edit_prix_vente.error_label.setText(msg)
            self.edit_prix_vente.error_label.setVisible(True)
        else:
            if self.edit_prix_vente.value() < self.edit_prix_achat.value():
                self.edit_prix_vente.setStyleSheet(f"""
                    border: 2px solid {cv['danger']};
                    background-color: {cv['danger_bg']};
                    padding: 12px 12px 12px 42px;
                    border-radius: 10px;
                """)
                self.edit_prix_vente.error_label.setText("Le prix de vente doit être ≥ au prix d'achat")
                self.edit_prix_vente.error_label.setVisible(True)
            else:
                self.edit_prix_vente.setStyleSheet(f"""
                    border: 2px solid {cv['border_focus']};
                    background-color: {cv['bg_card']};
                    padding: 12px 12px 12px 42px;
                    border-radius: 10px;
                """)
                self.edit_prix_vente.error_label.setVisible(False)
        
        self.calculer_marge()
        self.verifier_formulaire_complet()
    
    def calculer_marge(self):
        """Calcule et affiche la marge bénéficiaire."""
        achat = self.edit_prix_achat.value()
        vente = self.edit_prix_vente.value()
        
        if achat > 0 and vente >= achat:
            marge = vente - achat
            pourcentage = (marge / achat) * 100
            
            self.lbl_marge.setText(
                f"💹 Marge bénéficiaire : {marge:,.0f} GNF ({pourcentage:.1f}%)"
            )
            self.lbl_marge.setVisible(True)
            
            # Couleur selon la marge
            if pourcentage < 10:
                color = theme_manager.colors()['danger']
                bg = theme_manager.colors()['danger_bg']
            elif pourcentage < 30:
                color = theme_manager.colors()['warning']
                bg = theme_manager.colors()['warning_bg']
            else:
                color = theme_manager.colors()['primary']
                bg = theme_manager.colors()['primary_light']
            
            self.lbl_marge.setStyleSheet(f"""
                background-color: {bg};
                color: {color};
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
            """)
        else:
            self.lbl_marge.setVisible(False)
    
    def verifier_formulaire_complet(self):
        """Active le bouton uniquement si tout est valide."""
        v_lib, _ = self.controleur.valider_texte(self.edit_libelle.text(), "libellé", 3)
        v_type, _ = self.controleur.valider_type(self.combo_type.currentData())
        v_achat, _ = self.controleur.valider_prix(self.edit_prix_achat.value(), "prix achat")
        v_vente, _ = self.controleur.valider_prix(self.edit_prix_vente.value(), "prix vente")
        
        # Vérification prix vente >= prix achat
        prix_coherent = self.edit_prix_vente.value() >= self.edit_prix_achat.value()
        
        tous_valides = all([v_lib, v_type, v_achat, v_vente, prix_coherent])
        self.btn_save.setEnabled(tous_valides)
    
    def show_message(self, reussite, message):
        """Affiche un message de succès ou d'erreur."""
        titre = "Succès" if reussite else "Erreur"
        dialog = CustomMessageBox(titre, message, is_success=reussite, parent=self)
        dialog.exec()
