"""
Modal de détail d'un acte médical.
Affiche : info acte, passages (acte_visite), durées calculées, résultats médicaux.
"""
import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QWidget, QPushButton, QGraphicsDropShadowEffect,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from views.shared.theme_manager import theme_manager

STATUT_COLORS = {
    "en_attente": ("#F59E0B", "#FFFBEB"),
    "planifie":   ("#3B82F6", "#EFF6FF"),
    "en_cours":   ("#8B5CF6", "#F5F3FF"),
    "termine":    ("#10B981", "#ECFDF5"),
    "refuse":     ("#EF4444", "#FEF2F2"),
}


def _badge(text: str, fg: str, bg: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setFixedHeight(22)
    lbl.setStyleSheet(
        f"background:{bg};color:{fg};border-radius:8px;padding:0 8px;font-size:11px;font-weight:600;"
    )
    return lbl


def _row(label: str, value: str, c: dict) -> QWidget:
    w = QWidget()
    layout = QHBoxLayout(w)
    layout.setContentsMargins(0, 2, 0, 2)
    layout.setSpacing(8)
    lbl = QLabel(label)
    lbl.setStyleSheet(f"color:{c['text_secondary']};font-size:12px;font-weight:600;min-width:150px;")
    val = QLabel(value or "—")
    val.setStyleSheet(f"color:{c['text_primary']};font-size:13px;")
    val.setWordWrap(True)
    layout.addWidget(lbl)
    layout.addWidget(val, 1)
    return w


class DetailActeModal(QDialog):
    def __init__(self, parent, acte_row: dict, ctrl):
        super().__init__(parent)
        self.ctrl = ctrl
        self.acte_row = acte_row
        id_acte = acte_row.get("id_acte")

        # Données enrichies depuis le contrôleur
        self.passages = []
        self.durees   = {}
        if id_acte and hasattr(ctrl, "obtenir_durees_acte"):
            self.durees = ctrl.obtenir_durees_acte(id_acte) or {}
        if id_acte and hasattr(ctrl, "obtenir_passages"):
            self.passages = ctrl.obtenir_passages(id_acte) or []

        self.setWindowTitle(f"Détail Acte #{id_acte}")
        self.setFixedSize(640, 680)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._init_ui()

    # =========================================================================
    def _init_ui(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 70))

        self.container = QFrame(self)
        self.container.setGraphicsEffect(shadow)
        self.container.setObjectName("DetailContainer")

        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._build_header(main_layout)
        self._build_body(main_layout)
        self._build_footer(main_layout)

        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(20, 20, 20, 20)
        wrapper.addWidget(self.container)

        theme_manager.theme_changed.connect(self._apply_theme)
        self._apply_theme()

    def _build_header(self, main_layout):
        c = theme_manager.colors()
        header = QFrame()
        header.setFixedHeight(68)
        header.setObjectName("DetailHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 16, 0)

        self._icon_lbl = QLabel()
        self._icon_lbl.setFixedSize(32, 32)

        id_acte = self.acte_row.get("id_acte", "")
        type_acte = self.acte_row.get("type_acte", "")
        title = QLabel(f"Détail de l'acte médical")
        title.setObjectName("DetailHeaderTitle")
        sub = QLabel(f"#{id_acte}  •  {type_acte.capitalize()}")
        sub.setObjectName("DetailHeaderSub")

        vbox = QVBoxLayout()
        vbox.setSpacing(1)
        vbox.addWidget(title)
        vbox.addWidget(sub)

        layout.addWidget(self._icon_lbl)
        layout.addSpacing(10)
        layout.addLayout(vbox, 1)

        self._btn_close = QPushButton()
        self._btn_close.setFixedSize(32, 32)
        self._btn_close.setObjectName("BtnClose")
        self._btn_close.setCursor(Qt.PointingHandCursor)
        self._btn_close.clicked.connect(self.reject)
        layout.addWidget(self._btn_close)
        main_layout.addWidget(header)

    def _build_body(self, main_layout):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 16, 24, 16)
        content_layout.setSpacing(16)

        c = theme_manager.colors()

        # ── Section info acte ─────────────────────────────────────────────────
        content_layout.addWidget(self._section_title("Informations de l'acte"))
        a = self.acte_row

        statut = a.get("statut_acte", "")
        fc, bc = STATUT_COLORS.get(statut, ("#6B7280", "#F9FAFB"))
        status_row = QWidget()
        sl = QHBoxLayout(status_row)
        sl.setContentsMargins(0, 2, 0, 2)
        lbl_s = QLabel("Statut")
        lbl_s.setStyleSheet(f"color:{c['text_secondary']};font-size:12px;font-weight:600;min-width:150px;")
        sl.addWidget(lbl_s)
        sl.addWidget(_badge(statut, fc, bc))
        sl.addStretch()
        content_layout.addWidget(status_row)

        choix = a.get("choix_patient") or "—"
        choix_colors = {
            "maintenant": ("#10B981", "#ECFDF5"),
            "plus_tard":  ("#3B82F6", "#EFF6FF"),
            "ailleurs":   ("#EF4444", "#FEF2F2"),
        }
        choix_row = QWidget()
        cl = QHBoxLayout(choix_row)
        cl.setContentsMargins(0, 2, 0, 2)
        lbl_c = QLabel("Choix patient")
        lbl_c.setStyleSheet(f"color:{c['text_secondary']};font-size:12px;font-weight:600;min-width:150px;")
        cl.addWidget(lbl_c)
        fc2, bc2 = choix_colors.get(choix, ("#6B7280", "#F9FAFB"))
        cl.addWidget(_badge(choix, fc2, bc2))
        cl.addStretch()
        content_layout.addWidget(choix_row)

        for label, key in [
            ("Code consultation",  "code_consultation"),
            ("Type d'acte",        "type_acte"),
            ("Mode réalisation",   "mode_realisation"),
            ("Décision médicale",  "decision_medicale"),
            ("Raison refus",       "raison_refus"),
            ("Date création",      "date_creation"),
        ]:
            val = a.get(key, "")
            if hasattr(val, "strftime"):
                val = val.strftime("%d/%m/%Y %H:%M")
            content_layout.addWidget(_row(label, str(val) if val else "—", c))

        # Séparateur
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color:{c['border']};")
        content_layout.addWidget(sep)

        # ── Durées calculées ──────────────────────────────────────────────────
        content_layout.addWidget(self._section_title("Durées (calculées dynamiquement)"))

        durees_widget = QWidget()
        dl = QHBoxLayout(durees_widget)
        dl.setSpacing(12)
        dl.setContentsMargins(0, 0, 0, 0)
        for label, key, color in [
            ("Attente",    "attente_min",   c.get("warning", "#F59E0B")),
            ("Exécution",  "execution_min", c.get("info",    "#3B82F6")),
            ("Totale",     "totale_min",    c.get("primary", "#0F7B6C")),
        ]:
            val = self.durees.get(key)
            text = f"{val:.0f} min" if val is not None else "—"
            card = QFrame()
            card.setStyleSheet(f"background:{color}22;border-radius:10px;border:1px solid {color}44;")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 8, 12, 8)
            v_lbl = QLabel(text)
            v_lbl.setAlignment(Qt.AlignCenter)
            v_lbl.setStyleSheet(f"font-size:18px;font-weight:bold;color:{color};background:transparent;")
            t_lbl = QLabel(label)
            t_lbl.setAlignment(Qt.AlignCenter)
            t_lbl.setStyleSheet(f"font-size:11px;color:{c['text_secondary']};background:transparent;")
            card_layout.addWidget(v_lbl)
            card_layout.addWidget(t_lbl)
            dl.addWidget(card, 1)
        content_layout.addWidget(durees_widget)

        # Séparateur
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"color:{c['border']};")
        content_layout.addWidget(sep2)

        # ── Passages (acte_visite) ─────────────────────────────────────────────
        content_layout.addWidget(self._section_title("Passages & file d'attente"))
        if self.passages:
            tbl = QTableWidget(len(self.passages), 5)
            tbl.setHorizontalHeaderLabels(["Rôle", "Entrée file", "Début exec.", "Sortie", "Statut"])
            tbl.verticalHeader().setVisible(False)
            tbl.setEditTriggers(QTableWidget.NoEditTriggers)
            tbl.setAlternatingRowColors(True)
            tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            tbl.setShowGrid(False)
            tbl.setFixedHeight(min(200, 40 + len(self.passages) * 36))
            for row, p in enumerate(self.passages):
                def fmt(v):
                    if v is None:
                        return "—"
                    if hasattr(v, "strftime"):
                        return v.strftime("%d/%m %H:%M")
                    return str(v)
                tbl.setItem(row, 0, QTableWidgetItem(str(getattr(p, "role_visite", "") or "—")))
                tbl.setItem(row, 1, QTableWidgetItem(fmt(getattr(p, "date_entree", None))))
                tbl.setItem(row, 2, QTableWidgetItem(fmt(getattr(p, "date_debut_execution", None))))
                tbl.setItem(row, 3, QTableWidgetItem(fmt(getattr(p, "date_sortie", None))))
                stat_p = str(getattr(p, "statut_passage", "") or "—")
                tbl.setItem(row, 4, QTableWidgetItem(stat_p))
            tbl.setStyleSheet(f"""
                QTableWidget {{ background:{c['bg_table']};border:none;
                    alternate-background-color:{c['bg_table_alt']};
                    color:{c['text_primary']};font-size:12px; }}
                QHeaderView::section {{ background:{c['table_header_bg']};
                    color:{c['text_secondary']};font-size:11px;font-weight:600;
                    padding:6px;border:none;
                    border-bottom:2px solid {c['table_header_border']}; }}
            """)
            content_layout.addWidget(tbl)
        else:
            no_pass = QLabel("Aucun passage enregistré pour cet acte.")
            no_pass.setStyleSheet(f"color:{c['text_muted']};font-size:13px;font-style:italic;")
            content_layout.addWidget(no_pass)

        content_layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll, 1)

    def _build_footer(self, main_layout):
        footer = QFrame()
        footer.setObjectName("DetailFooter")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.addStretch()
        btn = QPushButton("Fermer")
        btn.setObjectName("BtnClose2")
        btn.setFixedHeight(40)
        btn.setFixedWidth(120)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.reject)
        self._btn_close2 = btn
        layout.addWidget(btn)
        main_layout.addWidget(footer)

    def _section_title(self, text: str) -> QLabel:
        c = theme_manager.colors()
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size:13px;font-weight:bold;color:{c['primary']};"
            f"border-bottom:1px solid {c['border']};padding-bottom:4px;"
            f"background:transparent;"
        )
        return lbl

    # =========================================================================
    def _apply_theme(self):
        c = theme_manager.colors()
        self.container.setStyleSheet(f"""
            QFrame#DetailContainer {{
                background:{c['bg_card']};
                border-radius:20px;
                border:1px solid {c['border']};
            }}
            QFrame#DetailHeader {{
                background:qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {c['bg_card']}, stop:1 {c['bg_main']});
                border-top-left-radius:20px;
                border-top-right-radius:20px;
            }}
            QLabel#DetailHeaderTitle {{
                font-size:16px;font-weight:bold;color:{c['text_primary']};
                background:transparent;
            }}
            QLabel#DetailHeaderSub {{
                font-size:12px;color:{c['text_secondary']};
                background:transparent;
            }}
            QFrame#DetailFooter {{
                background:{c['bg_main']};
                border-bottom-left-radius:20px;
                border-bottom-right-radius:20px;
                border-top:1px solid {c['border']};
            }}
            QPushButton#BtnClose2 {{
                background:{c['primary']};color:white;
                border-radius:8px;font-weight:bold;font-size:13px;border:none;
            }}
            QPushButton#BtnClose2:hover {{ background:{c['primary_hover']}; }}
            QPushButton#BtnClose {{
                background:transparent;border:none;border-radius:6px;
            }}
            QPushButton#BtnClose:hover {{ background:{c['danger_bg']}; }}
        """)
        self._btn_close.setIcon(qta.icon("fa5s.times", color=c["danger"]))
        self._icon_lbl.setPixmap(qta.icon("fa5s.file-medical", color=c["primary"]).pixmap(28, 28))
