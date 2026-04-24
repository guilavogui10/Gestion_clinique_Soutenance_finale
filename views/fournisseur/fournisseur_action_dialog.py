import os
import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton
)
from views.shared.modal_theme import MC


class FournisseurActionDialog(QDialog):
    """
    Dialog moderne pour afficher les activites d'un fournisseur.
    """

    def __init__(self, controleur, fournisseur_data: dict, code_session: str = None, parent=None):
        super().__init__(parent)
        self.controleur = controleur
        self.fournisseur = fournisseur_data or {}
        self.mail = self.fournisseur.get("email_fournisseur", "")
        self.code_session = code_session
        self.info_cabinet = self.controleur.get_cabinet_info()
        self.stats = self.controleur.get_stats_fournisseur_detail(self.mail, self.code_session)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(820, 620)

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        container = QFrame()
        container.setObjectName("MainContainer")
        container.setStyleSheet(f"""
            QFrame#MainContainer {{
                background-color: {MC.BG_MAIN};
                border-radius: 18px;
                border: 1px solid {MC.BORDER};
            }}
            QLabel {{ color: {MC.TEXT_PRIMARY}; border: none; background: transparent; }}
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(22)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 70))
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 18, 24, 20)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        header_left = QVBoxLayout()
        header_left.setSpacing(2)

        title = QLabel("Activites du fournisseur")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {MC.PRIMARY};")
        header_left.addWidget(title)

        cab_name = QLabel(self.info_cabinet.get("nom_cabinet", "Cabinet Medical"))
        cab_name.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {MC.TEXT_PRIMARY}; border: none; background: transparent;"
        )
        cab_addr = QLabel(self.info_cabinet.get("adresse_cabinet", ""))
        cab_addr.setStyleSheet(
            f"font-size: 11px; color: {MC.TEXT_SECONDARY}; border: none; background: transparent;"
        )
        header_left.addWidget(cab_name)
        header_left.addWidget(cab_addr)
        header.addLayout(header_left, 5)

        logo_path = self.info_cabinet.get("logo_url")
        if logo_path and os.path.exists(logo_path):
            logo_lbl = QLabel()
            pix = QPixmap(logo_path).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            logo_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            header.addWidget(logo_lbl, 1)

        layout.addLayout(header)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {MC.BORDER_LIGHT};")
        layout.addWidget(sep)

        # Fournisseur info
        info_row = QHBoxLayout()
        name_icon = QLabel()
        name_icon.setPixmap(qta.icon("fa5s.user-tie", color=MC.PRIMARY).pixmap(QSize(18, 18)))
        info_row.addWidget(name_icon)
        info_row.addWidget(QLabel(f"Nom: {self.fournisseur.get('nom_entreprise', '')}"))
        info_row.addSpacing(20)
        mail_icon = QLabel()
        mail_icon.setPixmap(qta.icon("fa5s.envelope", color=MC.PRIMARY).pixmap(QSize(18, 18)))
        info_row.addWidget(mail_icon)
        info_row.addWidget(QLabel(f"Email: {self.fournisseur.get('email_fournisseur', '')}"))
        info_row.addStretch()
        layout.addLayout(info_row)

        # Derniere quantite (corrige si valeur zero mais mouvement present)
        dernier = self.stats.get("dernier_mouvement")
        last_qty = self.stats.get("dernier_quantite", 0)
        if dernier and (last_qty is None or last_qty == 0):
            last_qty = dernier.get("quantite_four", last_qty)

        # Stats cards
        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)
        stats_row.addWidget(self._stat_card("Produits", str(self.stats.get("nb_produits", 0)), "fa5s.boxes"))
        stats_row.addWidget(self._stat_card("Quantite totale", str(self.stats.get("quantite_totale", 0)), "fa5s.balance-scale"))
        stats_row.addWidget(self._stat_card("Derniere quantite", str(last_qty), "fa5s.history"))
        layout.addLayout(stats_row)

        # Table produits
        table_frame = QFrame()
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Produit", "Quantite"])
        prod_icon = qta.icon("fa5s.box", color="#0f5132")
        qty_icon = qta.icon("fa5s.hashtag", color="#0f5132")
        self.table.horizontalHeaderItem(0).setIcon(prod_icon)
        self.table.horizontalHeaderItem(1).setIcon(qty_icon)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: none;
                background-color: {MC.BG_CARD};
            }}
            QHeaderView::section {{
                background-color: {MC.PRIMARY_LIGHT}; padding: 6px; border: none;
                font-weight: bold; color: {MC.PRIMARY}; font-size: 11px;
            }}
            QTableWidget::item {{ padding: 4px; border: none; }}
            QTableWidget::item:selected {{ background: {MC.BG_MAIN}; color: {MC.TEXT_PRIMARY}; }}
            QTableWidget::item:focus {{ outline: none; }}
        """)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._apply_scrollbar_style(self.table)

        table_layout.addWidget(self.table)
        layout.addWidget(table_frame, 1)

        # Remplir table
        produits = self.stats.get("produits", [])
        for prod in produits:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(prod.get("nom", prod.get("code_produit", "")))))
            self.table.setItem(row, 1, QTableWidgetItem(str(prod.get("quantite", 0))))

        # Dernier mouvement
        last_box = QFrame()
        last_box.setStyleSheet(f"background: {MC.SUCCESS_BG}; border: 1px solid {MC.SUCCESS_BG}; border-radius: 10px;")
        last_layout = QHBoxLayout(last_box)
        last_layout.setContentsMargins(12, 8, 12, 8)
        last_layout.setSpacing(8)
        last_icon = QLabel()
        last_icon.setPixmap(qta.icon("fa5s.info-circle", color=MC.PRIMARY).pixmap(QSize(16, 16)))
        last_layout.addWidget(last_icon)
        if dernier:
            text = (
                f"Dernier produit: {dernier.get('code_produit', '')}  |  "
                f"Quantite: {dernier.get('quantite_four', last_qty)}  |  "
                f"Date: {dernier.get('date_facture_four', '')}"
            )
        else:
            text = "Aucun mouvement enregistre pour ce fournisseur."
        last_label = QLabel(text)
        last_label.setStyleSheet(f"color: {MC.PRIMARY}; font-weight: bold;")
        last_layout.addWidget(last_label)
        last_layout.addStretch()
        layout.addWidget(last_box)

        # Actions
        actions = QHBoxLayout()
        actions.addStretch()
        btn_close = QPushButton(qta.icon("fa5s.times", color="white"), " Fermer")
        btn_close.setFixedHeight(36)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {MC.PRIMARY};
                color: {MC.TEXT_INVERSE};
                border-radius: 8px;
                font-weight: bold;
                padding: 0 14px;
            }}
            QPushButton:hover {{ background-color: {MC.PRIMARY_HOVER}; }}
        """)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        actions.addWidget(btn_close)
        layout.addLayout(actions)

        main_layout.addWidget(container)

    def _stat_card(self, title, value, icon_name):
        card = QFrame()
        card.setStyleSheet(
            f"background: {MC.BG_CARD}; border: 1px solid {MC.BORDER}; border-radius: 12px;"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(4)

        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(icon_name, color=MC.PRIMARY).pixmap(QSize(16, 16)))
        header.addWidget(icon_lbl)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 11px; color: {MC.TEXT_SECONDARY}; border: none; background: transparent;")
        header.addWidget(title_lbl)
        header.addStretch()
        lay.addLayout(header)

        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {MC.PRIMARY}; border: none; background: transparent;")
        lay.addWidget(val_lbl)
        return card

    def _apply_scrollbar_style(self, widget):
        widget.verticalScrollBar().setStyleSheet(f"""
            QScrollBar:vertical {{
                border: none; background: {MC.BORDER_LIGHT};
                width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {MC.BORDER}; min-height: 20px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {MC.TEXT_MUTED}; }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)
