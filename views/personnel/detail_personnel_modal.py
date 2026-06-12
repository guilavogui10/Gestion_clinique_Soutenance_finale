import os
import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap, QGuiApplication
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QFrame, QPushButton, QGraphicsDropShadowEffect
)
from views.shared.modal_theme import MC
from views.shared.theme_manager import theme_manager


class DetailsPersonnelModal(QDialog):
    def __init__(self, parent, personnel: dict, ctrl):
        super().__init__(parent)
        self.ctrl = ctrl
        self.data = personnel or {}
        self.info_cabinet = (
            self.ctrl.get_cabinet_info()
            if hasattr(self.ctrl, "get_cabinet_info") else {}
        )

        self.setWindowTitle("Details Personnel")
        self._apply_dialog_size()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._init_ui()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self):
        """Reconstruit l'UI quand le thème change."""
        # Vider le container et reconstruire
        old_layout = self.container.layout()
        if old_layout:
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        c = theme_manager.colors()
        self.container.setStyleSheet(f"""
            QFrame#RootCard {{
                background-color: {c['bg_card']};
                border-radius: 24px;
                border: 1px solid {c['border_light']};
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        main = old_layout
        self._setup_badge_face(main)
        self._setup_info_zone(main)
        self._setup_footer(main)

    def _apply_dialog_size(self):
        width, height = 720, 460
        screen = QGuiApplication.primaryScreen()
        if screen:
            available = screen.availableGeometry()
            width = min(width, max(640, available.width() - 80))
            height = min(height, max(420, available.height() - 110))
        self.setFixedSize(width, height)

    def _photo_absolue(self):
        photo_name = self.data.get("photo_path")
        if not photo_name:
            return None
        script_dir = os.path.dirname(__file__)
        photo_path = os.path.normpath(
            os.path.join(script_dir, "..", "..", "connexion", "image", photo_name)
        )
        return photo_path if os.path.exists(photo_path) else None

    def _logo_label(self, width=72, height=72):
        logo_path = self.info_cabinet.get("logo_url")
        label = QLabel()
        label.setAlignment(Qt.AlignCenter)
        if logo_path and os.path.exists(logo_path):
            label.setPixmap(QPixmap(logo_path).scaled(
                width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        else:
            label.setPixmap(qta.icon("fa5s.id-badge", color=MC.PRIMARY).pixmap(56, 56))
        return label

    def _init_ui(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(34)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 85))

        self.container = QFrame(self)
        self.container.setGraphicsEffect(shadow)
        self.container.setStyleSheet(f"""
            QFrame#RootCard {{
                background-color: {MC.BG_CARD};
                border-radius: 24px;
                border: 1px solid {MC.BORDER_LIGHT};
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        self.container.setObjectName("RootCard")

        main = QVBoxLayout(self.container)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        self._setup_badge_face(main)
        self._setup_info_zone(main)
        self._setup_footer(main)

        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(14, 14, 14, 14)
        wrapper.addWidget(self.container)

    def _setup_badge_face(self, layout):
        face = QFrame()
        face.setMinimumHeight(210)
        face.setStyleSheet(f"""
            QFrame {{
                border-top-left-radius: 24px;
                border-top-right-radius: 24px;
                border: none;
                background: {MC.BG_CARD};
            }}
        """)
        root = QVBoxLayout(face)
        root.setContentsMargins(22, 6, 22, 0)
        root.setSpacing(0)

        nom_cabinet = (self.info_cabinet.get("nom_cabinet", "Cabinet Medical") or "").upper()

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(10)

        brand_col = QVBoxLayout()
        brand_col.setContentsMargins(0, 0, 0, 0)
        brand_col.setSpacing(0)

        lbl_cabinet = QLabel(nom_cabinet)
        lbl_cabinet.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        lbl_cabinet.setStyleSheet(
            f"color: {MC.DANGER}; font-size: 12px; font-weight: 900; letter-spacing: 0.4px;"
        )
        brand_col.addWidget(lbl_cabinet)

        lbl_sub = QLabel("ASSOCIATION / ETABLISSEMENT")
        lbl_sub.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        lbl_sub.setStyleSheet(f"color: {MC.TEXT_SECONDARY}; font-size: 8px; font-weight: 600;")
        brand_col.addWidget(lbl_sub)

        header.addLayout(brand_col, 1)
        header.addWidget(self._logo_label(52, 52), 0, Qt.AlignTop | Qt.AlignRight)
        root.addLayout(header)

        root.addSpacing(1)

        lbl_title = QLabel("CARTE DE MEMBRE")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet(
            f"color: {MC.PRIMARY}; font-size: 20px; font-weight: 900; letter-spacing: 0.6px;"
        )
        root.addWidget(lbl_title)

        code = self.data.get("code", "")
        lbl_code = QLabel(code)
        lbl_code.setAlignment(Qt.AlignCenter)
        lbl_code.setStyleSheet(
            f"color: {MC.INFO}; font-size: 11px; font-weight: 800; margin-top: 2px;"
        )
        root.addWidget(lbl_code)

        root.addSpacing(3)

        infos = QHBoxLayout()
        infos.setContentsMargins(0, 0, 0, 0)
        infos.setSpacing(12)

        photo_box = QFrame()
        photo_box.setFixedSize(92, 112)
        photo_box.setStyleSheet(f"""
            QFrame {{
                background: {MC.BG_CARD};
                border: 2px solid {MC.PRIMARY};
                border-radius: 14px;
            }}
        """)
        photo_layout = QVBoxLayout(photo_box)
        photo_layout.setContentsMargins(6, 6, 6, 6)

        photo_lbl = QLabel()
        photo_lbl.setAlignment(Qt.AlignCenter)
        photo_lbl.setStyleSheet("border: none; background: transparent;")
        photo_lbl.setFixedSize(78, 98)
        photo_path = self._photo_absolue()
        if photo_path:
            photo_lbl.setPixmap(QPixmap(photo_path).scaled(
                78, 98, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        else:
            photo_lbl.setPixmap(qta.icon("fa5s.user-circle", color=MC.TEXT_MUTED).pixmap(46, 46))
        photo_layout.addWidget(photo_lbl)

        infos.addWidget(photo_box, 0, Qt.AlignTop)

        identite_box = QFrame()
        identite_box.setMinimumHeight(96)
        identite_box.setStyleSheet(f"""
            QFrame {{
                background: {MC.BG_CARD};
                border: 1px solid {MC.BORDER_LIGHT};
                border-radius: 16px;
            }}
        """)
        identite_layout = QVBoxLayout(identite_box)
        identite_layout.setContentsMargins(12, 8, 12, 8)
        identite_layout.setSpacing(4)

        nom_complet = f"{self.data.get('nom', '')} {self.data.get('prenom', '')}".strip().upper()
        lbl_nom = QLabel(nom_complet or "INCONNU")
        lbl_nom.setWordWrap(True)
        lbl_nom.setStyleSheet(f"color: {MC.TEXT_PRIMARY}; font-size: 12px; font-weight: 900;")
        identite_layout.addWidget(lbl_nom)

        lbl_fonction = QLabel(self.data.get("fonction", ""))
        lbl_fonction.setWordWrap(True)
        lbl_fonction.setStyleSheet(f"color: {MC.PRIMARY}; font-size: 9px; font-weight: 800;")
        identite_layout.addWidget(lbl_fonction)

        lbl_contact = QLabel(f"Contact : {self.data.get('contact', '')}")
        lbl_contact.setWordWrap(True)
        lbl_contact.setStyleSheet(f"color: {MC.TEXT_SECONDARY}; font-size: 8px; font-weight: 600;")
        identite_layout.addWidget(lbl_contact)

        lbl_mail = QLabel(self.data.get("mail", ""))
        lbl_mail.setWordWrap(True)
        lbl_mail.setStyleSheet(f"color: {MC.TEXT_MUTED}; font-size: 8px;")
        identite_layout.addWidget(lbl_mail)

        infos.addWidget(identite_box, 1, Qt.AlignTop)
        root.addLayout(infos)

        strip = QFrame()
        strip.setFixedHeight(10)
        strip.setStyleSheet(f"background: {MC.PRIMARY}; border: none;")
        root.addWidget(strip)

        layout.addWidget(face)

    def _setup_info_zone(self, layout):
        body = QFrame()
        body.setStyleSheet(f"background: {MC.BG_MAIN}; border: none;")
        root = QVBoxLayout(body)
        root.setContentsMargins(18, 10, 18, 10)
        root.setSpacing(6)

        title = QLabel("Informations du personnel")
        title.setStyleSheet(f"color: {MC.TEXT_PRIMARY}; font-size: 11px; font-weight: 900;")
        root.addWidget(title)

        grid_card = QFrame()
        grid_card.setStyleSheet(f"""
            QFrame {{
                background: {MC.BG_CARD};
                border: 1px solid {MC.BORDER_LIGHT};
                border-radius: 18px;
            }}
        """)
        grid_layout = QGridLayout(grid_card)
        grid_layout.setContentsMargins(12, 10, 12, 10)
        grid_layout.setHorizontalSpacing(12)
        grid_layout.setVerticalSpacing(6)

        items = [
            ("Code", self.data.get("code", ""), "fa5s.id-card"),
            ("Nom", self.data.get("nom", ""), "fa5s.user"),
            ("Prenom", self.data.get("prenom", ""), "fa5s.user"),
            ("Fonction", self.data.get("fonction", ""), "fa5s.briefcase"),
            ("Contact", self.data.get("contact", ""), "fa5s.phone"),
            ("Email", self.data.get("mail", ""), "fa5s.envelope"),
            ("Naissance", self.data.get("date_naissance", ""), "fa5s.calendar-alt"),
            ("Adresse", self.data.get("adresse", ""), "fa5s.map-marker-alt"),
        ]

        row = 0
        col = 0
        for label, value, icon_name in items:
            cell = self._info_cell(label, value, icon_name)
            grid_layout.addWidget(cell, row, col)
            if col == 0:
                col = 1
            else:
                col = 0
                row += 1

        root.addWidget(grid_card)
        layout.addWidget(body)

    def _info_cell(self, label, value, icon_name):
        cell = QFrame()
        cell.setStyleSheet(f"""
            QFrame {{
                background: {MC.BG_INPUT};
                border: 1px solid {MC.BORDER_LIGHT};
                border-radius: 12px;
            }}
        """)
        layout = QHBoxLayout(cell)
        layout.setContentsMargins(7, 5, 7, 5)
        layout.setSpacing(7)

        icon = QLabel()
        icon.setPixmap(qta.icon(icon_name, color=MC.PRIMARY).pixmap(14, 14))
        layout.addWidget(icon, 0, Qt.AlignTop)

        texts = QVBoxLayout()
        texts.setSpacing(1)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {MC.TEXT_SECONDARY}; font-size: 8px; font-weight: 700;")
        texts.addWidget(lbl)

        val = QLabel(str(value or ""))
        val.setWordWrap(True)
        val.setStyleSheet(f"color: {MC.TEXT_PRIMARY}; font-size: 9px; font-weight: 800;")
        texts.addWidget(val)

        layout.addLayout(texts, 1)
        return cell

    def _setup_footer(self, layout):
        footer = QFrame()
        footer.setFixedHeight(50)
        footer.setStyleSheet(f"""
            QFrame {{
                background: {MC.BG_CARD};
                border-bottom-left-radius: 24px;
                border-bottom-right-radius: 24px;
                border-top: 1px solid {MC.BORDER_LIGHT};
            }}
        """)
        f = QHBoxLayout(footer)
        f.setContentsMargins(20, 0, 20, 0)

        footer_left = QLabel("CARTE DE MEMBRE / VUE DETAILLEE")
        footer_left.setStyleSheet(f"color: {MC.DANGER}; font-size: 8px; font-weight: 900;")
        f.addWidget(footer_left)
        f.addStretch()

        btn_imprimer = QPushButton(qta.icon("fa5s.print", color=MC.TEXT_INVERSE), " Imprimer la carte")
        btn_imprimer.setFixedHeight(30)
        btn_imprimer.setStyleSheet(f"""
            QPushButton {{
                background-color: {MC.INFO};
                color: {MC.TEXT_INVERSE};
                border-radius: 10px;
                font-weight: bold;
                padding: 0 14px;
            }}
            QPushButton:hover {{ background-color: {MC.PRIMARY_HOVER}; }}
        """)
        btn_imprimer.clicked.connect(self._imprimer)
        f.addWidget(btn_imprimer)
        f.addSpacing(10)

        btn_close = QPushButton(qta.icon("fa5s.times", color=MC.TEXT_INVERSE), " Fermer")
        btn_close.setFixedHeight(30)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {MC.PRIMARY};
                color: {MC.TEXT_INVERSE};
                border-radius: 10px;
                font-weight: bold;
                padding: 0 14px;
            }}
            QPushButton:hover {{ background-color: {MC.PRIMARY_HOVER}; }}
        """)
        btn_close.clicked.connect(self.accept)
        f.addWidget(btn_close)

        layout.addWidget(footer)

    def _imprimer(self):
        from views.shared.message_box import CustomMessageBox
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        from services.pdf_personnel.personnel_pdf import PersonnelPDFService
        try:
            pdf_path = PersonnelPDFService.generer_carte_membre(
                personnel_data = self.data,
                cabinet_info   = self.info_cabinet,
                photo_path     = self._photo_absolue(),
            )
            code = self.data.get("code", "")
            ApercuPDFDialog(pdf_path, f"Carte Membre — {code}", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Impossible de générer la carte :\n{e}",
                             is_success=False, parent=self).exec()
