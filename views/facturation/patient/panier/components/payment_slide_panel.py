"""
Composant PaymentSlidePanel - Interface de paiement fournisseur glissante.
Responsabilité : Affichage des produits et formulaire de paiement avec animation.
Design fluide, compact et fidèle aux spécifications de la Guinée (GNF, MTN, Orange).
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QComboBox, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea, QButtonGroup, QRadioButton, QSizePolicy
)
from views.shared.theme_manager import theme_manager
from .modern_message_box import ModernMessageBox


class NetworkCard(QFrame):
    """
    Carte réseau mobile : Nouveau design horizontal, compact et fluide.
    Empêche le texte de se chevaucher et réduit drastiquement la hauteur.
    """

    def __init__(self, name: str, bg_color: str, text_color: str = "white", parent=None):
        super().__init__(parent)
        self.name = name
        self._bg_color = bg_color
        self._text_color = text_color
        self._selected = False
        
        # ── MODIF : Design horizontal beaucoup plus compact (40px de haut)
        self.setFixedHeight(40)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self._build()
        self._apply_style(False)

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 8, 4)
        layout.setSpacing(8)

        # Radio button
        self.radio = QRadioButton()
        self.radio.setFixedSize(14, 14)
        c = theme_manager.colors()
        self.radio.setStyleSheet(f"""
            QRadioButton::indicator {{
                width: 12px; height: 12px;
                border-radius: 6px;
                border: 2px solid {c['border']};
                background: {c['bg_card']};
            }}
            QRadioButton::indicator:checked {{
                border: 2px solid {self._bg_color};
                background: {self._bg_color};
            }}
        """)
        layout.addWidget(self.radio)

        # Logo compact
        self.logo_frame = QFrame()
        self.logo_frame.setFixedSize(28, 28)
        self.logo_frame.setStyleSheet(
            f"background: {self._bg_color}; border-radius: 6px; border: none;"
        )
        logo_layout = QVBoxLayout(self.logo_frame)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        
        # On prend juste le premier mot pour le logo (Orange ou MTN)
        short_name = self.name.split()[0]
        lbl_logo = QLabel(short_name)
        lbl_logo.setAlignment(Qt.AlignCenter)
        lbl_logo.setStyleSheet(
            f"color: {self._text_color}; font-size: 8px; font-weight: 800;"
            " background: transparent; border: none;"
        )
        logo_layout.addWidget(lbl_logo)
        layout.addWidget(self.logo_frame)

        # Nom complet du réseau
        lbl_name = QLabel(self.name)
        lbl_name.setStyleSheet(
            f"color: {c['text_primary']}; font-size: 11px; font-weight: 600;"
            " background: transparent; border: none;"
        )
        layout.addWidget(lbl_name)
        layout.addStretch()

    def _apply_style(self, selected: bool):
        c = theme_manager.colors()
        if selected:
            self.setStyleSheet(f"""
                NetworkCard {{
                    background: {c['bg_main']};
                    border: 2px solid {self._bg_color};
                    border-radius: 8px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                NetworkCard {{
                    background: {c['bg_card']};
                    border: 1px solid {c['border']};
                    border-radius: 8px;
                }}
            """)

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_style(selected)
        self.radio.setChecked(selected)

    def mousePressEvent(self, event):
        self.radio.setChecked(True)
        super().mousePressEvent(event)


class PaymentSlidePanel(QFrame):
    """
    Panneau glissant pour le paiement de facture fournisseur.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.facture_data = None
        self.produits_data =[]
        self.fournisseur_data = None
        self._visible = False
        self._animation = None

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("QFrame { background: transparent; border: none; }")
        self._init_ui()
        self.hide()

    # =========================================================================
    # CONSTRUCTION UI
    # =========================================================================

    def _init_ui(self):
        layout = QVBoxLayout(self)
        # ── MODIF : Marges globales réduites pour maximiser l'espace
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self._create_header(layout)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(8)

        body.addWidget(self._create_left_section(), 7)
        body.addWidget(self._create_right_section(), 3)

        layout.addLayout(body, 1)

    # ─── En-tête ─────────────────────────────────────────────────────────────

    def _create_header(self, layout):
        c = theme_manager.colors()

        header = QFrame()
        # ── MODIF : Hauteur réduite pour l'en-tête
        header.setFixedHeight(36)
        header.setAttribute(Qt.WA_StyledBackground, True)
        header.setStyleSheet(f"""
            QFrame {{
                background: {c['bg_card']};
                border-radius: 8px;
                border: 1px solid {c['border']};
            }}
        """)

        hl = QHBoxLayout(header)
        hl.setContentsMargins(6, 0, 8, 0)
        hl.setSpacing(8)

        btn_back = QPushButton(qta.icon("fa5s.arrow-left", color=c['primary']), "")
        btn_back.setFixedSize(26, 26)
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background: {c['bg_main']};
                border: 1px solid {c['border']};
                border-radius: 6px;
            }}
            QPushButton:hover {{ background: {c['primary']}18; border: 1px solid {c['primary']}; }}
        """)
        btn_back.clicked.connect(self.close_panel)
        hl.addWidget(btn_back)

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        title_col.setContentsMargins(0, 4, 0, 4)

        title = QLabel("Paiement Fournisseur")
        title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {c['text_primary']}; background: transparent; border: none;")
        subtitle = QLabel("Régler la facture d'un fournisseur")
        subtitle.setStyleSheet(f"font-size: 8px; color: {c['text_muted']}; background: transparent; border: none;")
        
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        hl.addLayout(title_col)
        hl.addStretch()

        self.lbl_reference = self._badge_label("fa5s.file-invoice", "", c)
        hl.addWidget(self.lbl_reference)

        self.lbl_date = self._badge_label("fa5s.calendar-alt", "", c)
        hl.addWidget(self.lbl_date)

        layout.addWidget(header)

    def _badge_label(self, icon_name: str, text: str, c: dict) -> QWidget:
        frame = QFrame()
        frame.setAttribute(Qt.WA_StyledBackground, True)
        frame.setStyleSheet(f"QFrame {{ background: {c['bg_main']}; border: none; border-radius: 6px; }}")
        fl = QHBoxLayout(frame)
        fl.setContentsMargins(6, 2, 6, 2)
        fl.setSpacing(4)

        ico = QLabel()
        ico.setPixmap(qta.icon(icon_name, color=c['text_muted']).pixmap(10, 10))
        ico.setStyleSheet("background: transparent; border: none;")
        fl.addWidget(ico)

        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 9px; font-weight: 600; color: {c['text_primary']}; background: transparent; border: none;")
        fl.addWidget(lbl)

        frame.setVisible(False)
        frame._text_lbl = lbl
        return frame

    def _update_badge(self, badge_frame: QFrame, text: str):
        badge_frame._text_lbl.setText(text)
        badge_frame.setVisible(bool(text))

    # ─── Section gauche ───────────────────────────────────────────────────────

    def _create_left_section(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.verticalScrollBar().setStyleSheet(self._scrollbar_style())

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        vl = QVBoxLayout(container)
        vl.setContentsMargins(0, 0, 4, 0)
        vl.setSpacing(6)

        vl.addWidget(self._create_fournisseur_card())
        vl.addWidget(self._create_products_table(), 1)
        vl.addWidget(self._create_note())

        scroll.setWidget(container)
        return scroll

    def _create_fournisseur_card(self):
        c = theme_manager.colors()
        card = QFrame()
        card.setAttribute(Qt.WA_StyledBackground, True)
        card.setStyleSheet(f"QFrame {{ background: {c['bg_card']}; border: 1px solid {c['border']}; border-radius: 8px; }}")

        hl = QHBoxLayout(card)
        # ── MODIF : Marges réduites considérablement
        hl.setContentsMargins(8, 6, 8, 6)
        hl.setSpacing(8)

        # Icône store réduite
        icon_frame = QFrame()
        icon_frame.setFixedSize(32, 32)
        icon_frame.setStyleSheet(f"background: {c['primary']}18; border-radius: 8px; border: none;")
        ifl = QVBoxLayout(icon_frame)
        ifl.setContentsMargins(0, 0, 0, 0)
        ico = QLabel()
        ico.setPixmap(qta.icon("fa5s.store", color=c['primary']).pixmap(16, 16))
        ico.setAlignment(Qt.AlignCenter)
        ico.setStyleSheet("background: transparent; border: none;")
        ifl.addWidget(ico)
        hl.addWidget(icon_frame)

        info_vl = QVBoxLayout()
        info_vl.setSpacing(1)
        info_vl.setContentsMargins(0, 0, 0, 0)

        lbl_hint = QLabel("Nom du fournisseur")
        lbl_hint.setStyleSheet(f"font-size: 8px; color: {c['text_muted']}; background: transparent; border: none;")
        
        self.lbl_fournisseur_nom = QLabel("")
        self.lbl_fournisseur_nom.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {c['primary']}; background: transparent; border: none;")

        info_vl.addWidget(lbl_hint)
        info_vl.addWidget(self.lbl_fournisseur_nom)
        hl.addLayout(info_vl)
        hl.addStretch()

        contact_vl = QVBoxLayout()
        contact_vl.setSpacing(2)
        contact_vl.setContentsMargins(0, 0, 0, 0)

        self.lbl_tel     = self._contact_row("fa5s.phone", "")
        self.lbl_email   = self._contact_row("fa5s.envelope", "")
        contact_vl.addWidget(self.lbl_tel)
        contact_vl.addWidget(self.lbl_email)
        hl.addLayout(contact_vl)

        return card

    def _contact_row(self, icon_name: str, text: str) -> QWidget:
        c = theme_manager.colors()
        row = QWidget()
        row.setStyleSheet("background: transparent; border: none;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(4)

        ico = QLabel()
        ico.setPixmap(qta.icon(icon_name, color=c['text_muted']).pixmap(10, 10))
        ico.setStyleSheet("background: transparent; border: none;")

        lbl = QLabel(text)
        # ✅ CORRECTION: Augmentation de la police et suppression totale des bordures
        lbl.setStyleSheet(f"font-size: 11px; color: {c['text_secondary']}; background: transparent; border: none; padding: 0; margin: 0;")
        lbl.setFrameStyle(0)  # Supprime complètement le cadre
        
        rl.addWidget(ico)
        rl.addWidget(lbl)
        rl.addStretch()
        row._lbl = lbl
        return row

    def _create_products_table(self):
        c = theme_manager.colors()
        frame = QFrame()
        frame.setAttribute(Qt.WA_StyledBackground, True)
        frame.setStyleSheet(f"QFrame {{ background: {c['bg_card']}; border: 1px solid {c['border']}; border-radius: 8px; }}")

        vl = QVBoxLayout(frame)
        vl.setContentsMargins(8, 6, 8, 6)
        vl.setSpacing(4)

        title = QLabel("Produits de la facture")
        title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {c['text_primary']}; background: transparent; border: none;")
        vl.addWidget(title)

        self.table_produits = QTableWidget(0, 5)
        self.table_produits.setHorizontalHeaderLabels(["#", "Produit", "Qté", "Prix U.", "Montant"])
        h = self.table_produits.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_produits.verticalHeader().setVisible(False)
        self.table_produits.setAlternatingRowColors(True)
        self.table_produits.setSelectionMode(QTableWidget.NoSelection)
        self.table_produits.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_produits.verticalScrollBar().setStyleSheet(self._scrollbar_style())
        
        # Style table optimisé
        self.table_produits.setStyleSheet(f"""
            QTableWidget {{
                background: {c['bg_main']};
                border: 1px solid {c['border']}; border-radius: 6px;
                gridline-color: {c['border']}; font-size: 10px;
            }}
            QTableWidget::item {{ padding: 2px 4px; color: {c['text_primary']}; }}
            QTableWidget::item:alternate {{ background: {c['bg_card']}; }}
            QHeaderView::section {{
                background: {c['bg_card']}; color: {c['text_muted']};
                font-weight: 700; font-size: 8px; text-transform: uppercase;
                padding: 4px; border: none; border-bottom: 1px solid {c['border']};
            }}
        """)
        vl.addWidget(self.table_produits, 1)

        tl = QHBoxLayout()
        tl.setContentsMargins(2, 2, 2, 0)
        lbl_t = QLabel("Total produits")
        lbl_t.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {c['text_primary']}; background: transparent; border: none;")
        self.lbl_total_produits = QLabel("")
        self.lbl_total_produits.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {c['primary']}; background: transparent; border: none;")
        
        tl.addWidget(lbl_t)
        tl.addStretch()
        tl.addWidget(self.lbl_total_produits)
        vl.addLayout(tl)

        return frame

    def _create_note(self):
        c = theme_manager.colors()
        note = QFrame()
        note.setAttribute(Qt.WA_StyledBackground, True)
        note.setStyleSheet(f"QFrame {{ background: {c['info']}12; border: 1px solid {c['info']}60; border-radius: 6px; }}")
        nl = QHBoxLayout(note)
        nl.setContentsMargins(6, 4, 6, 4)
        nl.setSpacing(6)

        ico = QLabel()
        ico.setPixmap(qta.icon("fa5s.info-circle", color=c['info']).pixmap(12, 12))
        ico.setStyleSheet("background: transparent; border: none;")

        txt = QLabel("Note : Veuillez vérifier les informations avant confirmation.")
        txt.setStyleSheet(f"font-size: 9px; color: {c['info']}; font-weight: 500; background: transparent; border: none;")
        txt.setWordWrap(True)

        nl.addWidget(ico)
        nl.addWidget(txt, 1)
        return note

    # ─── Section droite (Formulaire) ──────────────────────────────────────────

    def _create_right_section(self):
        c = theme_manager.colors()
        widget = QFrame()
        widget.setAttribute(Qt.WA_StyledBackground, True)
        widget.setStyleSheet(f"QFrame {{ background: {c['bg_card']}; border: 1px solid {c['border']}; border-radius: 8px; }}")

        vl = QVBoxLayout(widget)
        vl.setContentsMargins(10, 10, 10, 10)
        vl.setSpacing(8)

        title = QLabel("Détails du paiement")
        title.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {c['text_primary']}; background: transparent; border: none;")
        vl.addWidget(title)

        self._create_devise_section(vl)
        self._create_montant_section(vl)
        
        # ── MODIF : Suppression onglet bancaire, on affiche directement les cartes réseaux
        self._create_network_cards_section(vl)
        
        self._create_phone_input_section(vl)
        self._create_reference_section(vl)

        vl.addStretch()
        self._create_pay_button(vl)
        return widget

    def _field_label(self, text: str) -> QLabel:
        c = theme_manager.colors()
        lbl = QLabel(text)
        # ── MODIF : Assurance totale qu'aucun label n'a de bordure
        lbl.setStyleSheet(f"font-size: 10px; font-weight: 600; color: {c['text_muted']}; background: transparent; border: none;")
        return lbl

    def _input_style(self):
        c = theme_manager.colors()
        return f"""
            border: 1px solid {c['border']}; border-radius: 6px;
            padding-left: 8px; background: {c['bg_main']};
            font-size: 11px; color: {c['text_primary']};
        """

    def _create_devise_section(self, layout):
        layout.addWidget(self._field_label("Devise"))
        self.combo_devise = QComboBox()
        # ── MODIF : Devise Guinéenne
        self.combo_devise.addItems(["GNF – Franc Guinéen", "EUR – Euro", "USD – Dollar"])
        self.combo_devise.setFixedHeight(28) # Plus compact
        c = theme_manager.colors()
        self.combo_devise.setStyleSheet(f"""
            QComboBox {{ {self._input_style()} }}
            QComboBox:focus {{ border: 1px solid {c['primary']}; }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox QAbstractItemView {{ background: {c['bg_card']}; color: {c['text_primary']}; border: 1px solid {c['border']}; border-radius: 5px; }}
        """)
        layout.addWidget(self.combo_devise)

    def _create_montant_section(self, layout):
        layout.addWidget(self._field_label("Montant total à payer"))
        self.lbl_montant_total = QLabel("")
        c = theme_manager.colors()
        self.lbl_montant_total.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {c['primary']}; background: transparent; border: none;")
        layout.addWidget(self.lbl_montant_total)

    def _create_network_cards_section(self, layout):
        layout.addWidget(self._field_label("Mode de paiement"))

        # ── MODIF : Cartes de paiement horizontales (Espèces + Orange + MTN)
        networks_layout = QHBoxLayout()
        networks_layout.setSpacing(8)
        networks_layout.setContentsMargins(0, 0, 0, 0)

        self.network_group = QButtonGroup(self)
        self._network_cards = []

        networks =[
            ("Espèces",       "#2ecc71", "white"),   # Vert pour espèces
            ("Orange Money", "#FF7900", "white"),
            ("MTN Mobile",   "#FFC300", "black"),
        ]

        for i, (name, bg, fg) in enumerate(networks):
            card = NetworkCard(name, bg, fg, self)
            if i == 0:  # Espèces sélectionné par défaut
                card.set_selected(True)
            card.radio.toggled.connect(lambda checked, c_ref=card: self._on_network_selected(c_ref, checked))
            self.network_group.addButton(card.radio, i)
            self._network_cards.append(card)
            networks_layout.addWidget(card)

        layout.addLayout(networks_layout)

    def _on_network_selected(self, selected_card, checked):
        for card in self._network_cards:
            card.set_selected(card is selected_card and checked)

    def _create_phone_input_section(self, layout):
        c = theme_manager.colors()
        layout.addWidget(self._field_label("Numéro de paiement"))

        row = QHBoxLayout()
        row.setSpacing(6)

        self.combo_indicatif = QComboBox()
        # ── MODIF : +224 par défaut pour la Guinée
        self.combo_indicatif.addItems(["+224", "+225", "+33", "+1"])
        self.combo_indicatif.setFixedWidth(60)
        self.combo_indicatif.setFixedHeight(28)
        self.combo_indicatif.setStyleSheet(f"""
            QComboBox {{ {self._input_style()} padding-left: 4px; }}
            QComboBox::drop-down {{ border: none; width: 14px; }}
            QComboBox QAbstractItemView {{ background: {c['bg_card']}; color: {c['text_primary']}; border: 1px solid {c['border']}; }}
        """)

        self.input_phone = QLineEdit()
        self.input_phone.setPlaceholderText("6XX XX XX XX")
        self.input_phone.setFixedHeight(28)
        self.input_phone.setStyleSheet(self._input_style())

        row.addWidget(self.combo_indicatif)
        row.addWidget(self.input_phone)
        layout.addLayout(row)

    def _create_reference_section(self, layout):
        layout.addWidget(self._field_label("Référence (optionnel)"))
        self.input_reference = QLineEdit()
        self.input_reference.setPlaceholderText("Motif...")
        self.input_reference.setFixedHeight(28)
        self.input_reference.setStyleSheet(self._input_style())
        layout.addWidget(self.input_reference)

    def _create_pay_button(self, layout):
        c = theme_manager.colors()
        self.btn_pay = QPushButton(qta.icon("fa5s.lock", color="white"), "  Payer")
        self.btn_pay.setFixedHeight(36) # Compact mais cliquable
        self.btn_pay.setCursor(Qt.PointingHandCursor)
        self.btn_pay.setStyleSheet(f"""
            QPushButton {{
                background: {c['primary']}; color: white;
                border-radius: 6px; font-size: 12px; font-weight: 700; border: none;
            }}
            QPushButton:hover {{ background: {c['primary_light']}; }}
        """)
        self.btn_pay.clicked.connect(self.process_payment)
        layout.addWidget(self.btn_pay)

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def _scrollbar_style(self):
        c = theme_manager.colors()
        return f"""
            QScrollBar:vertical {{ border: none; background: transparent; width: 4px; border-radius: 2px; }}
            QScrollBar::handle:vertical {{ background: {c['border']}; min-height: 20px; border-radius: 2px; }}
            QScrollBar::handle:vertical:hover {{ background: {c['text_muted']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """

    # =========================================================================
    # CHARGEMENT DES DONNÉES
    # =========================================================================

    def load_data(self, facture_data, produits_data, fournisseur_data):
        self.facture_data = facture_data
        self.produits_data = produits_data
        self.fournisseur_data = fournisseur_data
        self._update_ui()

    def _update_ui(self):
        if not self.facture_data: return

        if hasattr(self.facture_data, 'code_facture_four'):
            self._update_badge(self.lbl_reference, f"Réf : {self.facture_data.code_facture_four}")

        if hasattr(self.facture_data, 'date_facture_four') and self.facture_data.date_facture_four:
            d = self.facture_data.date_facture_four
            date_str = d.strftime('%d/%m/%Y') if hasattr(d, 'strftime') else str(d)
            self._update_badge(self.lbl_date, f"Date : {date_str}")

        if self.fournisseur_data:
            # ✅ CORRECTION: Adapter aux vrais noms de colonnes de la table fournisseurs
            # La table a: email_fournisseur, nom_entreprise, telephone, adresse
            
            # Récupérer le nom (peut être dict ou objet)
            if isinstance(self.fournisseur_data, dict):
                nom_entreprise = self.fournisseur_data.get('nom_entreprise', '')
                telephone = self.fournisseur_data.get('telephone', '')
                email = self.fournisseur_data.get('email_fournisseur', '')
                adresse = self.fournisseur_data.get('adresse', '')
            else:
                nom_entreprise = getattr(self.fournisseur_data, 'nom_entreprise', '') or getattr(self.fournisseur_data, 'nom', '')
                telephone = getattr(self.fournisseur_data, 'telephone', '')
                email = getattr(self.fournisseur_data, 'email_fournisseur', '') or getattr(self.fournisseur_data, 'email', '')
                adresse = getattr(self.fournisseur_data, 'adresse', '')
            
            self.lbl_fournisseur_nom.setText(nom_entreprise or "—")
            self.lbl_tel._lbl.setText(telephone or "—")
            self.lbl_email._lbl.setText(email or "—")

        self.table_produits.setRowCount(0)
        total = 0.0

        for i, produit in enumerate(self.produits_data or[], 1):
            row = self.table_produits.rowCount()
            self.table_produits.insertRow(row)

            c = theme_manager.colors()
            item_num = QTableWidgetItem(str(i))
            item_num.setTextAlignment(Qt.AlignCenter)
            self.table_produits.setItem(row, 0, item_num)

            designation = getattr(produit, 'libelle', None) or getattr(produit, 'designation', 'Produit')
            self.table_produits.setItem(row, 1, QTableWidgetItem(designation))

            qte = getattr(produit, 'quantite_four', 0)
            item_qte = QTableWidgetItem(str(qte))
            item_qte.setTextAlignment(Qt.AlignCenter)
            self.table_produits.setItem(row, 2, item_qte)

            pu = getattr(produit, 'prix_unitaire', 0.0)
            # ── MODIF : GNF au lieu de XOF
            self.table_produits.setItem(row, 3, QTableWidgetItem(f"{int(pu):,} GNF".replace(',', ' ')))

            montant = qte * pu
            total += montant
            item_mt = QTableWidgetItem(f"{int(montant):,} GNF".replace(',', ' '))
            item_mt.setForeground(__import__('PySide6.QtGui', fromlist=['QColor']).QColor(c['primary']))
            item_mt.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_produits.setItem(row, 4, item_mt)

        self.table_produits.resizeRowsToContents()

        # ── MODIF : GNF au lieu de XOF
        total_str = f"{int(total):,} GNF".replace(',', ' ')
        self.lbl_total_produits.setText(total_str)
        self.lbl_montant_total.setText(total_str)
        self.btn_pay.setText(f"  Payer {total_str}")

    # =========================================================================
    # ANIMATIONS
    # =========================================================================

    def show_panel(self):
        if self._visible: return
        self.raise_()
        self.show()
        self._visible = True

    def close_panel(self):
        # Remonter la hiérarchie pour trouver la vraie vue
        p = self.parent()
        while p and not hasattr(p, '_fermer_payment_overlay'):
            p = p.parent()
        
        if p:
            p._fermer_payment_overlay()
        else:
            self.hide()
        self._visible = False

    # =========================================================================
    # TRAITEMENT DU PAIEMENT
    # =========================================================================

    def process_payment(self):
        if not self.facture_data:
            ModernMessageBox.error(self, "Erreur", "Aucune facture à finaliser.", theme_manager.colors()['primary'])
            return

        telephone = self.input_phone.text().strip()
        if not telephone or len(telephone) < 8 or not telephone.isdigit():
            ModernMessageBox.warning(self, "Attention", "Le numéro de téléphone est invalide.", theme_manager.colors()['primary'])
            return

        # ── MODIF : Mapping propre pour Espèces, MTN et Orange Money
        selected_id = self.network_group.checkedId()
        modes = ["especes", "orange money", "mtn mobile money"]
        mode_paiement = modes[selected_id] if 0 <= selected_id < len(modes) else "especes"

        confirmed = ModernMessageBox.question(
            self, "Confirmation",
            f"Confirmer le paiement de {self.lbl_montant_total.text()} ?\n\nMode : {mode_paiement.title()}\nTéléphone : {self.combo_indicatif.currentText()} {telephone}"
        )
        if not confirmed: return

        from controllers.controleur_factureFournisseur import FactureFournisseurControleur
        from models.modele_factureFournisseur import FactureFournisseur
        from datetime import datetime

        facture_ctrl = FactureFournisseurControleur()
        facture = FactureFournisseur(
            code_facture_four=self.facture_data.code_facture_four,
            code_fournisseur=self.facture_data.code_fournisseur,
            code_session=self.facture_data.code_session,
            date_facture_four=datetime.now(),
            montant_total=0,
            mode_payement=mode_paiement,
            telephone=telephone
        )

        ok, msg = facture_ctrl.finaliser_facture(facture)

        if ok:
            ModernMessageBox.success(self, "Succès", "Facture finalisée avec succès !", theme_manager.colors()['primary'])
            # ✅ CORRECTION: Fermer le panneau et actualiser l'interface parente
            self.close_panel()
            # # Forcer l'actualisation de la vue parente
            # if self.parent() and hasattr(self.parent(), 'charger_donnees'):
            #     print("[PaymentSlidePanel] Actualisation de la vue parente")
            #     parent = self.parent()
            #     if hasattr(parent, 'code_session') and parent.code_session:
            #         parent.charger_donnees(parent.code_session)
        else:
            ModernMessageBox.error(self, "Erreur", f"Erreur lors de la finalisation : {msg}", theme_manager.colors()['primary'])