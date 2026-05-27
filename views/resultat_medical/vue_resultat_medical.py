"""
vue_resultat_medical.py
------------------------
Vue principale — Gestion des résultats médicaux.
Design inspiré du module consultation (QTabWidget, KPI cards, tableaux,
formulaire avec wrapper-badge, quick actions).
"""

import logging
import os

import urllib.request

import qtawesome as qta
from PySide6.QtCore import Qt, QSize, QRect, QPoint
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QLineEdit, QComboBox, QTextEdit, QPushButton,
    QTabWidget, QScrollArea, QLayout, QDialog,
    QSizePolicy, QFileDialog,
)

from views.shared.theme_manager import theme_manager
from views.shared.message_box import CustomMessageBox

_TYPES_SOURCE  = ["consultation", "examen", "chirurgie"]
_TYPES_FICHIER = ["image", "video", "pdf"]
_NIVEAUX_CONF  = ["faible", "moyen", "eleve"]


def _fmt_date(d) -> str:
    if d is None:
        return "—"
    try:
        return d.strftime("%d/%m/%Y %H:%M") if hasattr(d, "strftime") else str(d)[:16]
    except Exception:
        return str(d)


class FlowLayout(QLayout):
    """Layout qui dispose les widgets en lignes et revient à la ligne automatiquement."""

    def __init__(self, parent=None, h_spacing=16, v_spacing=16):
        super().__init__(parent)
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self._items = []

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect, test_only):
        m = self.contentsMargins()
        eff = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x, y = eff.x(), eff.y()
        line_height = 0
        for item in self._items:
            if item.widget() and item.widget().isHidden():
                continue
            w = item.sizeHint().width()
            h = item.sizeHint().height()
            next_x = x + w + self._h_spacing
            if next_x - self._h_spacing > eff.right() and line_height > 0:
                x = eff.x()
                y += line_height + self._v_spacing
                next_x = x + w + self._h_spacing
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x = next_x
            line_height = max(line_height, h)
        return y + line_height - rect.y() + m.bottom()


class DialogResultatDetail(QDialog):
    """Modal centré sur l'écran, hauteur adaptative, icônes FA devant chaque champ."""

    _FONT = "font-family:'Segoe UI',Arial,sans-serif;"

    def __init__(self, id_resultat: str, ctrl, parent=None):
        super().__init__(parent)
        self._id   = id_resultat
        self._ctrl = ctrl
        self._data = {}
        self.logger = logging.getLogger(__name__)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        try:
            self._data = ctrl.get_detail_resultat(id_resultat)
        except Exception as e:
            self.logger.error(f"[DialogResultatDetail] Erreur chargement détail: {e}")
        self._build_ui()
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.setMaximumHeight(int(screen.height() * 0.88))
        self.setFixedWidth(min(860, int(screen.width() * 0.92)))
        self.adjustSize()
        self.move(
            screen.x() + (screen.width()  - self.width())  // 2,
            screen.y() + (screen.height() - self.height()) // 2,
        )

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _ico(self, name, color, size=11):
        lbl = QLabel()
        lbl.setPixmap(qta.icon(name, color=color).pixmap(size, size))
        lbl.setFixedSize(size + 2, size + 2)
        lbl.setStyleSheet("border:none;background:transparent;")
        return lbl

    def _field_row(self, ico_name, ico_color, label, value, c):
        """Ligne : [icône 10px] label : valeur"""
        h = QHBoxLayout()
        h.setSpacing(5)
        h.setContentsMargins(0, 1, 0, 1)
        h.addWidget(self._ico(ico_name, ico_color, 10))
        key_lbl = QLabel(f"{label}\u00a0:")
        key_lbl.setStyleSheet(
            f"{self._FONT}font-size:10px;font-weight:600;color:#6B7280;"
            "border:none;background:transparent;min-width:105px;"
        )
        val_lbl = QLabel(str(value) if value else "\u2014")
        val_lbl.setWordWrap(True)
        val_lbl.setStyleSheet(
            f"{self._FONT}font-size:10px;color:#111827;border:none;background:transparent;"
        )
        h.addWidget(key_lbl, 0, Qt.AlignTop)
        h.addWidget(val_lbl, 1)
        return h

    def _sub_card(self, title, hdr_icon, hdr_color, rows_fn, c):
        """Carte subdivision avec badge coloré + séparateur + champs."""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background:white;
                border-radius:10px;
                border:1.5px solid {c['border_light']};
            }}
        """)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(4)
        th = QHBoxLayout()
        th.setSpacing(6)
        badge = QFrame()
        badge.setFixedSize(22, 22)
        badge.setStyleSheet(f"background:{hdr_color}18;border-radius:6px;border:none;")
        bl = QHBoxLayout(badge)
        bl.setContentsMargins(0, 0, 0, 0)
        bi = QLabel()
        bi.setPixmap(qta.icon(hdr_icon, color=hdr_color).pixmap(11, 11))
        bi.setAlignment(Qt.AlignCenter)
        bi.setStyleSheet("border:none;background:transparent;")
        bl.addWidget(bi, alignment=Qt.AlignCenter)
        ttl = QLabel(title)
        ttl.setStyleSheet(
            f"{self._FONT}font-size:11px;font-weight:700;"
            f"color:{hdr_color};border:none;background:transparent;"
        )
        th.addWidget(badge)
        th.addWidget(ttl)
        th.addStretch()
        lay.addLayout(th)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color:{c['border_light']};")
        lay.addWidget(sep)
        rows_fn(lay, c)
        return frame

    # ── Build UI ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        c = theme_manager.colors()
        d = self._data
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(0)

        card = QFrame()
        card.setObjectName("ModalCard")
        card.setStyleSheet(f"""
            QFrame#ModalCard {{
                background:white;
                border-radius:18px;
                border:1px solid {c['border']};
            }}
        """)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(20, 14, 20, 12)
        card_lay.setSpacing(8)
        outer.addWidget(card)

        # Header
        type_source = d.get("type_source", "")
        _src = {
            "consultation": ("fa5s.stethoscope", "#2563EB"),
            "examen":       ("fa5s.microscope",  "#7C3AED"),
            "chirurgie":    ("fa5s.cut",          "#EF4444"),
        }
        ico_name, ico_color = _src.get(type_source, ("fa5s.file-medical", "#0F7B6C"))
        nom_patient = (
            f"{d.get('p_nom') or ''} {d.get('p_prenom') or ''}".strip() or
            d.get("code_consultation") or d.get("code_acte_medical") or ""
        )
        hdr = QHBoxLayout()
        hdr.setSpacing(10)
        badge_hdr = QFrame()
        badge_hdr.setFixedSize(34, 34)
        badge_hdr.setStyleSheet(
            f"background:{ico_color}18;border-radius:9px;border:none;"
        )
        bhl = QHBoxLayout(badge_hdr)
        bhl.setContentsMargins(0, 0, 0, 0)
        bhi = QLabel()
        bhi.setPixmap(qta.icon(ico_name, color=ico_color).pixmap(16, 16))
        bhi.setAlignment(Qt.AlignCenter)
        bhi.setStyleSheet("border:none;background:transparent;")
        bhl.addWidget(bhi, alignment=Qt.AlignCenter)
        titre_col = QVBoxLayout()
        titre_col.setSpacing(1)
        titre_main = QLabel(f"R\u00e9sultat \u2014 {type_source.capitalize()}")
        titre_main.setStyleSheet(
            f"{self._FONT}font-size:14px;font-weight:700;color:#111827;"
            "border:none;background:transparent;"
        )
        titre_sub = QLabel(nom_patient)
        titre_sub.setStyleSheet(
            f"{self._FONT}font-size:10px;color:#6B7280;border:none;background:transparent;"
        )
        titre_col.addWidget(titre_main)
        titre_col.addWidget(titre_sub)
        close_btn = QPushButton()
        close_btn.setIcon(qta.icon("fa5s.times", color="#9CA3AF"))
        close_btn.setFixedSize(26, 26)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(
            "QPushButton{border:none;background:transparent;border-radius:6px;}"
            "QPushButton:hover{background:#F3F4F6;}"
        )
        close_btn.clicked.connect(self.reject)
        hdr.addWidget(badge_hdr)
        hdr.addLayout(titre_col)
        hdr.addStretch()
        hdr.addWidget(close_btn)
        card_lay.addLayout(hdr)

        sep0 = QFrame()
        sep0.setFrameShape(QFrame.HLine)
        sep0.setStyleSheet(f"color:{c['border_light']};")
        card_lay.addWidget(sep0)

        # Zone scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sc_w = QWidget()
        sc_w.setStyleSheet("background:transparent;")
        sc_lay = QVBoxLayout(sc_w)
        sc_lay.setContentsMargins(0, 4, 0, 4)
        sc_lay.setSpacing(8)
        scroll.setWidget(sc_w)
        card_lay.addWidget(scroll, 1)

        row1 = QHBoxLayout()
        row1.setSpacing(8)
        row1.addWidget(self._section_patient(d, c), 1)
        row1.addWidget(self._section_personnel(d, c), 1)
        sc_lay.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        row2.addWidget(self._section_service(d, c), 1)
        row2.addWidget(self._section_resultat(d, c), 1)
        sc_lay.addLayout(row2)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"color:{c['border_light']};")
        card_lay.addWidget(sep2)

        footer = QHBoxLayout()
        footer.setSpacing(8)
        footer.addStretch()
        btn_print = QPushButton("  Imprimer")
        btn_print.setIcon(qta.icon("fa5s.print", color="white"))
        btn_print.setFixedHeight(32)
        btn_print.setMinimumWidth(105)
        btn_print.setCursor(Qt.PointingHandCursor)
        btn_print.setStyleSheet(f"""
            QPushButton{{background:#059669;color:white;border:none;border-radius:8px;
                        {self._FONT}font-size:11px;font-weight:600;padding:0 14px;}}
            QPushButton:hover{{background:#047857;}}
        """)
        btn_print.clicked.connect(self._print_pdf)
        btn_open = QPushButton("  Ouvrir le fichier")
        btn_open.setIcon(qta.icon("fa5s.external-link-alt", color="white"))
        btn_open.setFixedHeight(32)
        btn_open.setMinimumWidth(140)
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.setStyleSheet(f"""
            QPushButton{{background:{ico_color};color:white;border:none;border-radius:8px;
                        {self._FONT}font-size:11px;font-weight:600;padding:0 14px;}}
            QPushButton:hover{{opacity:0.85;}}
        """)
        btn_open.clicked.connect(self._open_file)
        btn_close = QPushButton("  Fermer")
        btn_close.setIcon(qta.icon("fa5s.times", color="#6B7280"))
        btn_close.setFixedHeight(32)
        btn_close.setMinimumWidth(88)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet(f"""
            QPushButton{{background:#F9FAFB;color:#374151;
                        border:1.5px solid {c['border']};border-radius:8px;
                        {self._FONT}font-size:11px;font-weight:600;padding:0 14px;}}
            QPushButton:hover{{background:#F3F4F6;}}
        """)
        btn_close.clicked.connect(self.reject)
        footer.addWidget(btn_print)
        footer.addWidget(btn_open)
        footer.addWidget(btn_close)
        card_lay.addLayout(footer)

    # ── Sections ─────────────────────────────────────────────────────────────

    def _section_patient(self, d, c):
        nom = f"{d.get('p_nom') or ''} {d.get('p_prenom') or ''}".strip() or "\u2014"

        def rows(lay, c):
            for ico, lbl, val in [
                ("fa5s.user",           "Nom complet",  nom),
                ("fa5s.phone",          "T\u00e9l\u00e9phone",    d.get("p_tel")),
                ("fa5s.birthday-cake",  "Naissance",    _fmt_date(d["p_naissance"]) if d.get("p_naissance") else None),
                ("fa5s.venus-mars",     "Genre",        d.get("p_genre")),
                ("fa5s.briefcase",      "Profession",   d.get("p_profession")),
                ("fa5s.map-marker-alt", "Adresse",      d.get("p_adresse")),
            ]:
                lay.addLayout(self._field_row(ico, "#2563EB", lbl, val, c))

        return self._sub_card("Patient", "fa5s.user", "#2563EB", rows, c)

    def _section_personnel(self, d, c):
        nom = f"{d.get('per_nom') or ''} {d.get('per_prenom') or ''}".strip() or "\u2014"

        def rows(lay, c):
            for ico, lbl, val in [
                ("fa5s.user-md",   "Nom complet", nom),
                ("fa5s.id-badge",  "Fonction",    d.get("per_fonction")),
                ("fa5s.phone-alt", "Contact",     d.get("per_contact")),
            ]:
                lay.addLayout(self._field_row(ico, "#059669", lbl, val, c))

        return self._sub_card("Personnel soignant", "fa5s.user-md", "#059669", rows, c)

    def _section_service(self, d, c):
        ts = d.get("type_source", "")
        if ts == "consultation":
            frais = d.get("frais_consultation")
            frais_str = f"{frais:,.0f} GNF".replace(",", " ") if frais else None

            def rows(lay, c):
                for ico, lbl, val in [
                    ("fa5s.hashtag",      "Code",          d.get("code_consultation")),
                    ("fa5s.notes-medical","Diagnostique",  d.get("diagnostique")),
                    ("fa5s.coins",        "Frais",         frais_str),
                    ("fa5s.calendar-alt", "Date",          _fmt_date(d["date_consultation"]) if d.get("date_consultation") else None),
                    ("fa5s.layer-group",  "Session",       d.get("nom_session")),
                ]:
                    lay.addLayout(self._field_row(ico, "#2563EB", lbl, val, c))

            return self._sub_card("Consultation", "fa5s.stethoscope", "#2563EB", rows, c)
        elif ts == "examen":
            frais = d.get("frais_examen")
            frais_str = f"{frais:,.0f} GNF".replace(",", " ") if frais else None

            def rows(lay, c):
                for ico, lbl, val in [
                    ("fa5s.hashtag",        "Code acte",   d.get("code_acte_medical")),
                    ("fa5s.flask",          "Libell\u00e9",    d.get("libelle_examen")),
                    ("fa5s.comment-medical","D\u00e9cision",   d.get("decision_medicale")),
                    ("fa5s.coins",          "Frais",       frais_str),
                    ("fa5s.calendar-alt",   "Date",        _fmt_date(d["date_examen"]) if d.get("date_examen") else None),
                    ("fa5s.check-circle",   "Conclusion",  d.get("conclusion_medicale")),
                    ("fa5s.layer-group",    "Session",     d.get("nom_session")),
                ]:
                    lay.addLayout(self._field_row(ico, "#7C3AED", lbl, val, c))

            return self._sub_card("Examen", "fa5s.microscope", "#7C3AED", rows, c)
        else:
            frais = d.get("frais_chururgie")
            frais_str = f"{frais:,.0f} GNF".replace(",", " ") if frais else None

            def rows(lay, c):
                for ico, lbl, val in [
                    ("fa5s.hashtag",        "Code acte",     d.get("code_acte_medical")),
                    ("fa5s.procedures",     "Libell\u00e9",      d.get("libelle_chururgie")),
                    ("fa5s.comment-medical","D\u00e9cision",     d.get("decision_medicale")),
                    ("fa5s.coins",          "Frais",         frais_str),
                    ("fa5s.calendar-alt",   "Date",          _fmt_date(d["date_chururgie"]) if d.get("date_chururgie") else None),
                    ("fa5s.file-alt",       "Compte rendu",  d.get("compte_rendu_operatoire")),
                    ("fa5s.layer-group",    "Session",       d.get("nom_session")),
                ]:
                    lay.addLayout(self._field_row(ico, "#EF4444", lbl, val, c))

            return self._sub_card("Chirurgie", "fa5s.cut", "#EF4444", rows, c)

    def _section_resultat(self, d, c):
        def rows(lay, c):
            for ico, lbl, val in [
                ("fa5s.barcode",    "ID R\u00e9sultat",     d.get("id_resultat")),
                ("fa5s.tag",        "Type source",     d.get("type_source")),
                ("fa5s.file",       "Type fichier",    d.get("type_fichier")),
                ("fa5s.shield-alt", "Confidentialit\u00e9", d.get("niveau_confidentialite")),
                ("fa5s.clock",      "Date upload",     _fmt_date(d["date_upload"]) if d.get("date_upload") else None),
                ("fa5s.align-left", "Description",     d.get("description")),
            ]:
                lay.addLayout(self._field_row(ico, "#0F7B6C", lbl, val, c))
            if d.get("type_fichier") == "image":
                self._add_image_preview(lay, d, c)
            else:
                lbl_type = {"pdf": "PDF", "video": "vid\u00e9o"}.get(d.get("type_fichier", ""), d.get("type_fichier", ""))
                hint = QLabel(f"  Fichier {lbl_type} \u2014 cliquez sur \u00ab\u00a0Ouvrir le fichier\u00a0\u00bb")
                hint.setStyleSheet(
                    "font-size:10px;font-style:italic;color:#9CA3AF;border:none;background:transparent;"
                )
                lay.addWidget(hint)

        return self._sub_card("R\u00e9sultat m\u00e9dical", "fa5s.file-medical-alt", "#0F7B6C", rows, c)

    def _add_image_preview(self, lay, d, c):
        # Vérifier l'intégrité avant d'afficher l'image
        id_resultat = d.get("id_resultat", "")
        if not id_resultat:
            hint = QLabel("Aperçu non disponible")
            hint.setStyleSheet(
                "font-size:10px;font-style:italic;color:#9CA3AF;border:none;background:transparent;"
            )
            lay.addWidget(hint)
            return
        
        try:
            integrite_ok, message_integrite = self._ctrl.verifier_integrite_resultat(id_resultat)
            
            if not integrite_ok:
                # Afficher un message d'avertissement au lieu de l'image
                warning_lbl = QLabel(f"⚠️ {message_integrite}")
                warning_lbl.setStyleSheet(
                    "font-size:10px;font-weight:600;color:#EF4444;border:1.5px solid #FEE2E2;"
                    "border-radius:8px;background:#FEF2F2;padding:8px;"
                )
                warning_lbl.setWordWrap(True)
                lay.addWidget(warning_lbl)
                return
            
            url = self._ctrl.get_url_temporaire(id_resultat, 30)
            if not url:
                raise ValueError("URL vide - vérification intégrité échouée")
            
            with urllib.request.urlopen(url, timeout=6) as resp:
                img_bytes = resp.read()
            pix = QPixmap()
            pix.loadFromData(img_bytes)
            if not pix.isNull():
                pix = pix.scaled(200, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_lbl = QLabel()
                img_lbl.setPixmap(pix)
                img_lbl.setAlignment(Qt.AlignCenter)
                img_lbl.setStyleSheet(
                    "border:1.5px solid #E5E7EB;border-radius:8px;background:transparent;padding:4px;"
                )
                lay.addWidget(img_lbl)
                return
        except Exception as e:
            self.logger.warning(f"Erreur aperçu image {id_resultat}: {e}")
        
        hint = QLabel("Aperçu non disponible")
        hint.setStyleSheet(
            "font-size:10px;font-style:italic;color:#9CA3AF;border:none;background:transparent;"
        )
        lay.addWidget(hint)

    def _open_file(self):
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        from views.shared.message_box import CustomMessageBox
        
        if not self._id:
            CustomMessageBox.warning(self, "Erreur", "Identifiant du résultat manquant.")
            return
        
        # Vérifier l'intégrité avant d'ouvrir
        try:
            integrite_ok, message_integrite = self._ctrl.verifier_integrite_resultat(self._id)
            
            if not integrite_ok:
                CustomMessageBox.warning(self, "Fichier bloqué", message_integrite)
                return
            
            url = self._ctrl.get_url_temporaire(self._id, 60)
            if url:
                QDesktopServices.openUrl(QUrl(url))
            else:
                CustomMessageBox.warning(self, "Erreur", "Impossible de générer l'URL. Le fichier a peut-être été modifié.")
        except Exception as e:
            CustomMessageBox.warning(self, "Erreur", f"Erreur lors de l'ouverture du fichier: {str(e)}")

    def _print_pdf(self):
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        from services.pdf_admin.resultat_pdf import ResultatPDFService
        
        try:
            info_cabinet = {}
            if hasattr(self._ctrl, "service") and hasattr(self._ctrl.service, "info_cabinet"):
                try:
                    info_cabinet = self._ctrl.service.info_cabinet() or {}
                except Exception:
                    info_cabinet = {}
            
            pdf_path = ResultatPDFService.generer_temp(self._data or {}, info_cabinet)
            QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_path))
        except Exception as e:
            from views.shared.message_box import CustomMessageBox
            CustomMessageBox.warning(self, "Erreur impression", str(e))
 
 
class VueResultatMedical(QWidget):

    def __init__(self, controleur, permission_ctrl=None, user_info=None, parent=None):
        super().__init__(parent)
        self.ctrl   = controleur
        self.permission_ctrl = permission_ctrl
        self.user_info = user_info or {}
        self.logger = logging.getLogger(__name__)
        
        # Extraire les infos utilisateur pour les permissions
        self.code_utilisateur = self.user_info.get("code", "")
        self.role = self.user_info.get("role", "")
        self.est_responsable = bool(self.user_info.get("est_responsable", 0))
        
        # Créer le helper de permissions si disponible
        self.permission_helper = None
        if self.permission_ctrl and self.user_info:
            from views.shared.permission_helper import PermissionHelper
            self.permission_helper = PermissionHelper(self, self.permission_ctrl, self.user_info)
        
        self._init_ui()
        self._connect_signals()
        self._load_data()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(0)
        self.main_frame = QFrame()
        self.main_frame.setObjectName("MainWhiteFrame")
        mfl = QVBoxLayout(self.main_frame)
        mfl.setContentsMargins(0, 0, 0, 0)
        mfl.setSpacing(0)
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setIconSize(QSize(18, 18))
        mfl.addWidget(self.tabs, 1)
        self.quick_actions = self._build_quick_actions()
        mfl.addWidget(self.quick_actions)
        self.tab_stats         = self._create_stats_tab()
        self.tab_consultations = self._create_liste_tab("consultation")
        self.tab_examens       = self._create_liste_tab("examen")
        self.tab_chirurgies    = self._create_liste_tab("chirurgie")
        self.tab_dossier       = self._create_dossier_tab()
        self.tab_nouveau       = self._create_nouveau_tab()
        c = theme_manager.colors()
        self.tabs.addTab(self.tab_stats,         qta.icon("fa5s.chart-bar",   color=c.get("primary","#0F7B6C")), "Statistiques")
        self.tabs.addTab(self.tab_consultations, qta.icon("fa5s.stethoscope", color=c.get("info","#2563EB")),    "Consultations")
        self.tabs.addTab(self.tab_examens,       qta.icon("fa5s.microscope",  color=c.get("accent","#7C3AED")),  "Examens")
        self.tabs.addTab(self.tab_chirurgies,    qta.icon("fa5s.cut",         color=c.get("warning","#D97706")), "Chirurgies")
        self.tabs.addTab(self.tab_dossier,       qta.icon("fa5s.folder-open", color=c.get("warning","#D97706")), "Dossier patient")
        self.tabs.addTab(self.tab_nouveau,       qta.icon("fa5s.plus-circle", color=c.get("success","#059669")), "Enregistrer")
        
        # Connecter le signal de changement d'onglet pour vérifier les permissions
        self.tabs.currentChanged.connect(self._verifier_acces_onglet)
        
        root.addWidget(self.main_frame)

    def _build_quick_actions(self):
        bar = QWidget()
        bar.setObjectName("QuickActionsBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(8)
        self._qa_buttons = []
        actions = [
            ("fa5s.plus-circle", "Nouveau résultat", "primary", lambda: self.tabs.setCurrentIndex(5)),
            ("fa5s.sync-alt",    "Actualiser tout",  "info",    self._load_data),
            ("fa5s.folder-open", "Dossier patient",  "warning", lambda: self.tabs.setCurrentIndex(4)),
            ("fa5s.chart-bar",   "Statistiques",     "success", lambda: self.tabs.setCurrentIndex(0)),
        ]
        for icon_name, label, color_key, handler in actions:
            btn = QPushButton(f"  {label}")
            btn.setObjectName("QuickActionButton")
            btn.setProperty("icon_name", icon_name)
            btn.setProperty("color_key", color_key)
            btn.setFixedHeight(40)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(handler)
            layout.addWidget(btn)
            self._qa_buttons.append(btn)
        layout.addStretch()
        return bar

    def _create_stats_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)
        h = QHBoxLayout()
        tl = QLabel("Aperçu des résultats médicaux")
        tl.setObjectName("StatsTitle")
        btn_refresh = QPushButton()
        btn_refresh.setIcon(qta.icon("fa5s.sync-alt", color=theme_manager.colors().get("primary","#0F7B6C")))
        btn_refresh.setObjectName("BtnRefreshStats")
        btn_refresh.setFixedSize(36, 36)
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setToolTip("Actualiser")
        btn_refresh.clicked.connect(self._load_data)
        h.addWidget(tl)
        h.addStretch()
        h.addWidget(btn_refresh)
        layout.addLayout(h)
        lbl_s1 = QLabel("Résultats par source")
        lbl_s1.setObjectName("SectionLabel")
        layout.addWidget(lbl_s1)
        row1 = QHBoxLayout()
        row1.setSpacing(16)
        self._kpi_total   = self._kpi_card("Total résultats",  "fa5s.database",    "#0F7B6C", "0")
        self._kpi_consult = self._kpi_card("Consultations",    "fa5s.stethoscope", "#2563EB", "0")
        self._kpi_examen  = self._kpi_card("Examens",          "fa5s.microscope",  "#7C3AED", "0")
        self._kpi_chir    = self._kpi_card("Chirurgies",       "fa5s.cut",         "#EF4444", "0")
        for card, _ in [self._kpi_total, self._kpi_consult, self._kpi_examen, self._kpi_chir]:
            row1.addWidget(card)
        row1.addStretch()
        layout.addLayout(row1)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("StatsSep")
        layout.addWidget(sep)
        lbl_s2 = QLabel("Répartition par type de fichier")
        lbl_s2.setObjectName("SectionLabel")
        layout.addWidget(lbl_s2)
        row2 = QHBoxLayout()
        row2.setSpacing(16)
        self._kpi_image = self._kpi_card("Images",  "fa5s.image",    "#F59E0B", "0")
        self._kpi_pdf   = self._kpi_card("PDFs",    "fa5s.file-pdf", "#EF4444", "0")
        self._kpi_video = self._kpi_card("Vidéos",  "fa5s.film",     "#8B5CF6", "0")
        for card, _ in [self._kpi_image, self._kpi_pdf, self._kpi_video]:
            row2.addWidget(card)
        row2.addStretch()
        layout.addLayout(row2)
        layout.addStretch()
        return tab

    def _kpi_card(self, title, icon_name, color, value):
        card = QFrame()
        card.setObjectName("KpiCard")
        card.setFixedHeight(82)
        card.setMinimumWidth(190)
        cl = QHBoxLayout(card)
        cl.setContentsMargins(16, 0, 16, 0)
        cl.setSpacing(14)
        circle = QFrame()
        circle.setFixedSize(42, 42)
        circle.setStyleSheet(f"background-color: {color}; border-radius: 21px; border: none;")
        circ_lay = QHBoxLayout(circle)
        circ_lay.setContentsMargins(0, 0, 0, 0)
        ic_lbl = QLabel()
        ic_lbl.setPixmap(qta.icon(icon_name, color="white").pixmap(20, 20))
        ic_lbl.setAlignment(Qt.AlignCenter)
        ic_lbl.setStyleSheet("border: none; background: transparent;")
        circ_lay.addWidget(ic_lbl, alignment=Qt.AlignCenter)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("KpiTitle")
        val_lbl = QLabel(value)
        val_lbl.setObjectName("KpiValue")
        val_lbl.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: 700; background: transparent; border: none;")
        text_col.addStretch()
        text_col.addWidget(title_lbl)
        text_col.addWidget(val_lbl)
        text_col.addStretch()
        cl.addWidget(circle)
        cl.addLayout(text_col)
        cl.addStretch()
        return card, val_lbl

    def _create_liste_tab(self, source_type):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Barre d'outils : recherche + bouton nouveau
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)
        search = QLineEdit()
        search.setObjectName("SearchInput")
        search.setPlaceholderText(f"Rechercher un résultat — {source_type}s…")
        search.setFixedHeight(40)
        search.addAction(
            qta.icon("fa5s.search", color=theme_manager.colors()["text_muted"]),
            QLineEdit.LeadingPosition,
        )
        btn_new = QPushButton("  Nouveau résultat")
        btn_new.setObjectName("PrimaryButton")
        btn_new.setFixedHeight(40)
        btn_new.setMinimumWidth(155)
        btn_new.setCursor(Qt.PointingHandCursor)
        btn_new.setIcon(qta.icon("fa5s.plus", color="white"))
        btn_new.clicked.connect(lambda: self.tabs.setCurrentIndex(5))
        toolbar.addWidget(search, 1)
        toolbar.addWidget(btn_new)
        layout.addLayout(toolbar)

        # Zone défilante avec FlowLayout pour les cartes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("CardsScrollArea")
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        container.setObjectName("CardsContainer")
        flow = FlowLayout(container, h_spacing=16, v_spacing=16)
        container.setLayout(flow)
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        setattr(self, f"_flow_{source_type}",      flow)
        setattr(self, f"_container_{source_type}", container)
        setattr(self, f"_data_{source_type}",      [])
        setattr(self, f"_search_{source_type}",    search)

        search.textChanged.connect(lambda txt, st=source_type: self._filter_cards(st, txt))
        return tab

    def _create_dossier_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)
        self._dossier_input = QLineEdit()
        self._dossier_input.setObjectName("SearchInput")
        self._dossier_input.setPlaceholderText("Code patient — ex: PAT-00000001")
        self._dossier_input.setFixedHeight(40)
        self._dossier_input.addAction(qta.icon("fa5s.user", color=theme_manager.colors()["text_muted"]), QLineEdit.LeadingPosition)
        btn_search = QPushButton("  Rechercher")
        btn_search.setObjectName("PrimaryButton")
        btn_search.setFixedHeight(40)
        btn_search.setMinimumWidth(130)
        btn_search.setCursor(Qt.PointingHandCursor)
        btn_search.setIcon(qta.icon("fa5s.search", color="white"))
        toolbar.addWidget(self._dossier_input, 1)
        toolbar.addWidget(btn_search)
        layout.addLayout(toolbar)
        self._dossier_info = QLabel("Entrez un code patient pour afficher ses résultats médicaux.")
        self._dossier_info.setObjectName("DossierInfo")
        layout.addWidget(self._dossier_info)
        # Zone défilante avec FlowLayout
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("CardsScrollArea")
        scroll.setFrameShape(QFrame.NoFrame)
        self._dossier_container = QWidget()
        self._dossier_container.setObjectName("CardsContainer")
        self._dossier_flow = FlowLayout(self._dossier_container, h_spacing=16, v_spacing=16)
        self._dossier_container.setLayout(self._dossier_flow)
        scroll.setWidget(self._dossier_container)
        layout.addWidget(scroll, 1)

        btn_search.clicked.connect(self._search_dossier)
        self._dossier_input.returnPressed.connect(self._search_dossier)
        return tab

    def _create_nouveau_tab(self):
        tab = QWidget()
        tab.setObjectName("NouveauTab")
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(16)
        c = theme_manager.colors()

        # En-tête style consultation
        self.header_frame = QFrame()
        self.header_frame.setObjectName("FormHeader")
        self.header_frame.setFixedHeight(72)
        hl = QHBoxLayout(self.header_frame)
        hl.setContentsMargins(20, 12, 16, 12)
        hl.setSpacing(14)
        icon_box = QFrame()
        icon_box.setObjectName("FormIconBox")
        icon_box.setFixedSize(46, 46)
        ib_lay = QHBoxLayout(icon_box)
        ib_lay.setContentsMargins(0, 0, 0, 0)
        ico_lbl = QLabel()
        ico_lbl.setPixmap(qta.icon("fa5s.file-medical", color=c["primary"]).pixmap(22, 22))
        ico_lbl.setAlignment(Qt.AlignCenter)
        ico_lbl.setStyleSheet("border: none; background: transparent;")
        ib_lay.addWidget(ico_lbl, alignment=Qt.AlignCenter)
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self._form_title = QLabel("Enregistrement d'un Résultat Médical")
        self._form_title.setObjectName("FormTitle")
        self._form_sub = QLabel("Fichier lié à une consultation, un examen ou une chirurgie")
        self._form_sub.setObjectName("FormSub")
        title_col.addWidget(self._form_title)
        title_col.addWidget(self._form_sub)
        hl.addWidget(icon_box)
        hl.addLayout(title_col)
        hl.addStretch()
        self.n_btn_cancel = QPushButton("  Annuler")
        self.n_btn_cancel.setObjectName("BtnCancel")
        self.n_btn_cancel.setFixedSize(110, 40)
        self.n_btn_cancel.setCursor(Qt.PointingHandCursor)
        self.n_btn_cancel.setIcon(qta.icon("fa5s.times", color=c["text_secondary"]))
        self.n_btn_save = QPushButton("  Enregistrer")
        self.n_btn_save.setObjectName("BtnSave")
        self.n_btn_save.setFixedSize(140, 40)
        self.n_btn_save.setCursor(Qt.PointingHandCursor)
        self.n_btn_save.setIcon(qta.icon("fa5s.upload", color="white"))
        hl.addWidget(self.n_btn_cancel)
        hl.addWidget(self.n_btn_save)
        outer.addWidget(self.header_frame)

        # Section carte
        section = QFrame()
        section.setObjectName("FormSection")
        sl = QVBoxLayout(section)
        sl.setContentsMargins(22, 18, 22, 18)
        sl.setSpacing(20)
        shdr = QHBoxLayout()
        s_ico = QLabel()
        s_ico.setPixmap(qta.icon("fa5s.clipboard-list", color=c["primary"]).pixmap(16, 16))
        s_ico.setStyleSheet("border: none; background: transparent;")
        s_lbl = QLabel("Informations du résultat")
        s_lbl.setObjectName("SectionTitle")
        shdr.addWidget(s_ico)
        shdr.addSpacing(8)
        shdr.addWidget(s_lbl)
        shdr.addStretch()
        sl.addLayout(shdr)

        # Rangée 1
        row1 = QHBoxLayout()
        row1.setSpacing(16)
        self.n_type_source = QComboBox()
        self.n_type_source.addItems(_TYPES_SOURCE)
        vl1, _ = self._make_field("Type de source *", self.n_type_source, "fa5s.tag", c["info"])
        self.n_code_source = QComboBox()
        self.n_code_source.setPlaceholderText("Sélectionner un code…")
        vl2, _ = self._make_field("Code source *", self.n_code_source, "fa5s.hashtag", c["success"])
        self.n_type_fichier = QComboBox()
        self.n_type_fichier.addItems(_TYPES_FICHIER)
        vl3, _ = self._make_field("Type de fichier *", self.n_type_fichier, "fa5s.file-alt", c["warning"])
        row1.addLayout(vl1, 1)
        row1.addLayout(vl2, 1)
        row1.addLayout(vl3, 1)
        sl.addLayout(row1)

        # Rangée 2 : chemin + confidentialité
        row2 = QHBoxLayout()
        row2.setSpacing(16)
        file_outer = QVBoxLayout()
        file_outer.setSpacing(4)
        fl_label = QLabel("Chemin du fichier *")
        fl_label.setObjectName("FieldLabel")
        file_outer.addWidget(fl_label)
        file_wrapper = QFrame()
        file_wrapper.setObjectName("inputWrapper")
        file_wrapper.setFixedHeight(42)
        fw_lay = QHBoxLayout(file_wrapper)
        fw_lay.setContentsMargins(8, 5, 8, 5)
        fw_lay.setSpacing(6)
        file_badge = QFrame()
        file_badge.setFixedSize(28, 28)
        file_badge.setStyleSheet(f"background-color: {c['warning']}20; border-radius: 7px; border: none;")
        fb_lay = QHBoxLayout(file_badge)
        fb_lay.setContentsMargins(0, 0, 0, 0)
        fb_ico = QLabel()
        fb_ico.setPixmap(qta.icon("fa5s.folder-open", color=c["warning"]).pixmap(14, 14))
        fb_ico.setAlignment(Qt.AlignCenter)
        fb_ico.setStyleSheet("border: none; background: transparent;")
        fb_lay.addWidget(fb_ico, alignment=Qt.AlignCenter)
        self.n_chemin = QLineEdit()
        self.n_chemin.setPlaceholderText("Chemin du fichier à uploader…")
        self.n_chemin.setStyleSheet(f"border: none; background: transparent; font-size: 12px; color: {c['text_primary']}; padding: 0;")
        self._btn_browse = QPushButton()
        self._btn_browse.setObjectName("BtnBrowse")
        self._btn_browse.setIcon(qta.icon("fa5s.folder-open", color=c["warning"]))
        self._btn_browse.setFixedSize(28, 28)
        self._btn_browse.setCursor(Qt.PointingHandCursor)
        self._btn_browse.setToolTip("Parcourir…")
        self._btn_browse.setStyleSheet(f"QPushButton#BtnBrowse {{ border: none; background: transparent; }} QPushButton#BtnBrowse:hover {{ background: {c['hover']}; border-radius: 6px; }}")
        fw_lay.addWidget(file_badge)
        fw_lay.addWidget(self.n_chemin, 1)
        fw_lay.addWidget(self._btn_browse)
        file_outer.addWidget(file_wrapper)
        self.n_confidentialite = QComboBox()
        self.n_confidentialite.addItems(_NIVEAUX_CONF)
        self.n_confidentialite.setCurrentIndex(1)
        vl5, _ = self._make_field("Confidentialité", self.n_confidentialite, "fa5s.shield-alt", c.get("accent","#7C3AED"))
        row2.addLayout(file_outer, 2)
        row2.addLayout(vl5, 1)
        sl.addLayout(row2)

        # Description
        self.n_description = QTextEdit()
        self.n_description.setPlaceholderText("Description du résultat (optionnel)")
        self.n_description.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vl_desc, _ = self._make_field("Description", self.n_description, "fa5s.align-left", c["text_secondary"], height=90, align_top=True)
        sl.addLayout(vl_desc)

        outer.addWidget(section, 1)
        return tab

    def _make_field(self, label_text, widget, icon_name, icon_color, height=42, align_top=False):
        c = theme_manager.colors()
        vbox = QVBoxLayout()
        vbox.setSpacing(4)
        lbl = QLabel(label_text)
        lbl.setObjectName("FieldLabel")
        vbox.addWidget(lbl)
        wrapper = QFrame()
        wrapper.setObjectName("inputWrapper")
        if align_top:
            wrapper.setMinimumHeight(height)
        else:
            wrapper.setFixedHeight(height)
        wrapper.setStyleSheet(f"""
            QFrame#inputWrapper {{
                background-color: {c.get('bg_input', c['bg_main'])};
                border: 1.5px solid {c['border']};
                border-radius: 10px;
            }}
        """)
        hbox = QHBoxLayout(wrapper)
        hbox.setContentsMargins(8, 5, 8, 5)
        hbox.setSpacing(8)
        v_align = Qt.AlignTop if align_top else Qt.AlignVCenter
        badge = QFrame()
        badge.setFixedSize(28, 28)
        badge.setStyleSheet(f"background-color: {icon_color}20; border-radius: 7px; border: none;")
        bl = QHBoxLayout(badge)
        bl.setContentsMargins(0, 0, 0, 0)
        ico_lbl = QLabel()
        ico_lbl.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(14, 14))
        ico_lbl.setAlignment(Qt.AlignCenter)
        ico_lbl.setStyleSheet("border: none; background: transparent;")
        bl.addWidget(ico_lbl, alignment=Qt.AlignCenter)
        base = f"border: none; background: transparent; font-size: 12px; color: {c['text_primary']};"
        if isinstance(widget, QComboBox):
            widget.setStyleSheet(f"""
                QComboBox {{ {base} padding: 0; min-height: 28px; }}
                QComboBox::drop-down {{ border: none; width: 20px; }}
                QComboBox QAbstractItemView {{
                    background-color: {c['bg_card']};
                    border: 1px solid {c['border']};
                    border-radius: 8px;
                    color: {c['text_primary']};
                    outline: none;
                }}
                QComboBox QAbstractItemView::item {{ padding: 6px 10px; min-height: 26px; }}
                QComboBox QAbstractItemView::item:hover {{ background-color: {c['hover']}; }}
            """)
        elif isinstance(widget, QTextEdit):
            widget.setStyleSheet(f"QTextEdit {{ {base} padding: 4px 0; }}")
        else:
            widget.setStyleSheet(f"QLineEdit {{ {base} padding: 0; }}")
        hbox.addWidget(badge, 0, v_align)
        hbox.addWidget(widget, 1)
        vbox.addWidget(wrapper)
        return vbox, wrapper

    def _connect_signals(self):
        self.n_btn_cancel.clicked.connect(self._reset_form)
        self.n_btn_save.clicked.connect(self._save_resultat)
        self._btn_browse.clicked.connect(self._browse_file)
        self.n_type_source.currentTextChanged.connect(self._on_type_source_changed)
    
    def _verifier_acces_onglet(self, index):
        """
        Vérifie si l'utilisateur peut accéder à l'onglet sélectionné.
        Si refusé, revient à l'onglet précédent.
        """
        # Mapping des index d'onglets vers les types de source
        onglet_map = {
            0: "Statistiques",
            1: "Consultations",
            2: "Examens",
            3: "Chirurgies",
            4: "Dossier patient",
            5: "Enregistrer"
        }
        
        nom_onglet = onglet_map.get(index, "")
        
        # Pas de contrôle pour Statistiques, Dossier patient et Enregistrer
        if index in [0, 4, 5]:
            self._on_tab_changed(index)
            return
        
        # Vérifier les permissions pour Consultations, Examens, Chirurgies
        if not self.permission_ctrl:
            self._on_tab_changed(index)
            return  # Mode dégradé
        
        # DG et Admin ont accès à tout
        if self.role in ["Directeur Général", "Administrateur"]:
            self._on_tab_changed(index)
            return
        
        # Chirurgien : accès uniquement à Chirurgies
        if self.role.lower() == "chirurgien":
            if index != 3:  # Index 3 = Chirurgies
                CustomMessageBox.warning(
                    self,
                    "Accès refusé",
                    f"Votre rôle 'Chirurgien' ne vous permet pas d'accéder à l'onglet '{nom_onglet}'.\n\nVous avez uniquement accès aux résultats de chirurgie."
                )
                # Revenir à l'onglet Chirurgies
                self.tabs.blockSignals(True)
                self.tabs.setCurrentIndex(3)
                self.tabs.blockSignals(False)
                return
        
        # Accès autorisé, charger les données
        self._on_tab_changed(index)

    def _load_data(self):
        self._load_stats()
        for src in _TYPES_SOURCE:
            self._load_source_tab(src)

    def _load_stats(self):
        try:
            stats = self.ctrl.compter_par_type_source()
            total = sum(stats.values())
            self._kpi_total[1].setText(str(total))
            self._kpi_consult[1].setText(str(stats.get("consultation", 0)))
            self._kpi_examen[1].setText(str(stats.get("examen", 0)))
            self._kpi_chir[1].setText(str(stats.get("chirurgie", 0)))
            all_r = []
            for src in _TYPES_SOURCE:
                all_r.extend(self.ctrl.lister_par_type_source(src))
            self._kpi_image[1].setText(str(sum(1 for r in all_r if getattr(r,"type_fichier","")=="image")))
            self._kpi_pdf[1].setText(str(sum(1 for r in all_r if getattr(r,"type_fichier","")=="pdf")))
            self._kpi_video[1].setText(str(sum(1 for r in all_r if getattr(r,"type_fichier","")=="video")))
        except Exception as e:
            self.logger.warning("Erreur chargement stats: %s", e)

    def _load_source_tab(self, source_type):
        try:
            resultats = self.ctrl.lister_par_type_source(source_type)
            self._populate_cards(source_type, resultats)
        except Exception as e:
            self.logger.warning("Erreur chargement %s: %s", source_type, e)

    # ── Cartes FlowLayout ─────────────────────────────────────────────────────

    def _populate_cards(self, source_type, resultats):
        """Vide et remplit le FlowLayout de l'onglet source_type."""
        flow = getattr(self, f"_flow_{source_type}", None)
        if flow is None:
            return
        while flow.count():
            item = flow.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        setattr(self, f"_data_{source_type}", resultats)
        _colors = {"consultation": "#2563EB", "examen": "#7C3AED", "chirurgie": "#EF4444"}
        color = _colors.get(source_type, "#0F7B6C")
        for r in resultats:
            flow.addWidget(self._make_result_card(r, color))
        container = getattr(self, f"_container_{source_type}", None)
        if container:
            container.adjustSize()

    def _populate_cards_dossier(self, resultats):
        """Vide et remplit le FlowLayout du dossier patient."""
        while self._dossier_flow.count():
            item = self._dossier_flow.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        _colors = {"consultation": "#2563EB", "examen": "#7C3AED", "chirurgie": "#EF4444"}
        for r in resultats:
            color = _colors.get(getattr(r, "type_source", ""), "#0F7B6C")
            self._dossier_flow.addWidget(self._make_result_card(r, color))
        self._dossier_container.adjustSize()

    def _make_result_card(self, r, color):
        """Crée une carte : grande icône + bouton œil avec nom patient."""
        id_r           = getattr(r, "id_resultat",    "") or ""
        patient_nom    = getattr(r, "patient_nom",    "") or ""
        patient_prenom = getattr(r, "patient_prenom", "") or ""
        if patient_nom or patient_prenom:
            nom_display = f"{patient_nom} {patient_prenom}".strip()
        else:
            nom_display = (
                getattr(r, "code_consultation", "") or
                getattr(r, "code_acte_medical",  "") or
                id_r
            )

        card = QWidget()
        card.setFixedWidth(210)
        card.setStyleSheet("background: transparent;")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(8, 8, 8, 8)
        cl.setSpacing(10)
        cl.setAlignment(Qt.AlignCenter)

        # Grande icône book-medical
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon("fa5s.book-medical", color=color).pixmap(72, 72))
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        cl.addWidget(icon_lbl)

        # Bouton : œil + Résultat — nom patient
        btn_voir = QPushButton(f"  Résultat — {nom_display}")
        btn_voir.setObjectName("CardViewBtn")
        btn_voir.setFixedHeight(34)
        btn_voir.setCursor(Qt.PointingHandCursor)
        btn_voir.setIcon(qta.icon("fa5s.eye", color="white"))
        btn_voir.setStyleSheet(f"""
            QPushButton#CardViewBtn {{
                background: {color};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 11px;
                font-weight: 600;
                text-align: left;
                padding-left: 6px;
            }}
            QPushButton#CardViewBtn:hover {{
                background: {color}cc;
            }}
        """)
        btn_voir.clicked.connect(lambda _, rid=id_r: self._show_detail(rid))
        cl.addWidget(btn_voir)
        return card

    def _filter_cards(self, source_type, text):
        """Filtre les cartes selon le texte de recherche (nom patient / code)."""
        all_data = getattr(self, f"_data_{source_type}", [])
        text = text.lower().strip()
        if not text:
            self._populate_cards(source_type, all_data)
        else:
            filtered = [
                r for r in all_data
                if text in (
                    (getattr(r, "patient_nom",       "") or "") + " " +
                    (getattr(r, "patient_prenom",    "") or "") + " " +
                    (getattr(r, "code_consultation", "") or "") + " " +
                    (getattr(r, "code_acte_medical",  "") or "") + " " +
                    (getattr(r, "id_resultat",        "") or "")
                ).lower()
            ]
            self._populate_cards(source_type, filtered)

    def _on_tab_changed(self, index):
        mapping = {1: "consultation", 2: "examen", 3: "chirurgie"}
        if index in mapping:
            self._load_source_tab(mapping[index])
        elif index == 5:
            self._on_type_source_changed(self.n_type_source.currentText())

    def _on_type_source_changed(self, type_source):
        self.n_code_source.clear()
        try:
            if type_source == "consultation":
                codes = self.ctrl.lister_codes_consultations()
            elif type_source in ("examen", "chirurgie"):
                codes = self.ctrl.lister_codes_actes_par_type(type_source)
            else:
                codes = []
            for code, label in codes:
                self.n_code_source.addItem(label, code)
            if not codes:
                self.n_code_source.addItem("Aucun enregistrement trouvé", "")
        except Exception as e:
            self.logger.warning("Erreur chargement codes: %s", e)

    def _search_dossier(self):
        code = self._dossier_input.text().strip()
        if not code:
            CustomMessageBox.warning(self, "Recherche", "Veuillez entrer un code patient.")
            return
        try:
            resultats = self.ctrl.lister_par_patient(code)
            if resultats:
                self._dossier_info.setText(
                    f"<b>{len(resultats)}</b> résultat(s) trouvé(s) pour le patient <b>{code}</b>"
                )
                self._populate_cards_dossier(resultats)
            else:
                self._dossier_info.setText(
                    f"Aucun résultat trouvé pour le patient <b>{code}</b>."
                )
                self._populate_cards_dossier([])
        except Exception as e:
            CustomMessageBox.warning(self, "Erreur", str(e))

    def _show_detail(self, id_resultat):
        if not id_resultat:
            return
        
        # Vérifier les permissions pour consulter les résultats
        if not self.permission_helper:
            # Mode dégradé sans permissions
            dlg = DialogResultatDetail(id_resultat, self.ctrl, self)
            dlg.exec()
            return
        
        # Vérifier et exécuter avec gestion OTP
        def afficher_detail():
            dlg = DialogResultatDetail(id_resultat, self.ctrl, self)
            dlg.exec()
        
        self.permission_helper.verifier_et_executer(
            action=self.permission_ctrl.ACTION_CONSULTATION,
            contexte=f"Résultat médical {id_resultat}",
            callback_success=afficher_detail
        )

    def _open_url(self, id_resultat):
        if not id_resultat:
            return
        try:
            integrite_ok, message_integrite = self.ctrl.verifier_integrite_resultat(id_resultat)
            if not integrite_ok:
                CustomMessageBox.warning(self, "Fichier bloqué", message_integrite)
                return
            
            url = self.ctrl.get_url_temporaire(id_resultat, 60)
            if url:
                from PySide6.QtGui import QDesktopServices
                from PySide6.QtCore import QUrl
                QDesktopServices.openUrl(QUrl(url))
            else:
                CustomMessageBox.warning(self, "URL introuvable", "Impossible de générer l'URL.\nLe fichier a peut-être été modifié ou le serveur MinIO est arrêté.")
        except Exception as e:
            self.logger.error(f"Erreur ouverture URL {id_resultat}: {e}")
            CustomMessageBox.warning(self, "Erreur", str(e))

    def _delete_resultat(self, id_resultat):
        if not id_resultat:
            return
        rep = CustomMessageBox.question(self, "Confirmation", f"Supprimer le résultat <b>{id_resultat}</b> ?<br>Le fichier MinIO sera également supprimé.")
        if not rep:
            return
        ok, msg = self.ctrl.supprimer_resultat(id_resultat)
        if ok:
            CustomMessageBox.info(self, "Succès", msg)
            self._load_data()
        else:
            CustomMessageBox.warning(self, "Erreur", msg)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier", os.path.expanduser("~"),
            "Tous les fichiers (*.*);; Images (*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp);; PDF (*.pdf);; Vidéos (*.mp4 *.avi *.mov *.mkv *.wmv)")
        if not path:
            return
        self.n_chemin.setText(path)
        ext = os.path.splitext(path)[1].lower()
        if ext in (".jpg",".jpeg",".png",".gif",".bmp",".tiff",".webp"):
            self.n_type_fichier.setCurrentIndex(_TYPES_FICHIER.index("image"))
        elif ext == ".pdf":
            self.n_type_fichier.setCurrentIndex(_TYPES_FICHIER.index("pdf"))
        elif ext in (".mp4",".avi",".mov",".mkv",".wmv"):
            self.n_type_fichier.setCurrentIndex(_TYPES_FICHIER.index("video"))

    def _save_resultat(self):
        type_source  = self.n_type_source.currentText().strip()
        code_source  = (self.n_code_source.currentData() or self.n_code_source.currentText().split(" — ")[0]).strip()
        type_fichier = self.n_type_fichier.currentText().strip()
        chemin       = self.n_chemin.text().strip()
        conf         = self.n_confidentialite.currentText().strip()
        desc         = self.n_description.toPlainText().strip() or None
        code_consultation = code_source if type_source == "consultation" else None
        code_acte_medical = code_source if type_source in ("examen","chirurgie") else None
        resultat, msg = self.ctrl.ajouter_resultat(
            type_source=type_source, type_fichier=type_fichier, chemin_local=chemin,
            code_acte_medical=code_acte_medical, code_consultation=code_consultation,
            description=desc, niveau_confidentialite=conf,
        )
        if resultat:
            CustomMessageBox.info(self, "Succès", msg)
            self._reset_form()
            self._load_data()
            tab_map = {"consultation": 1, "examen": 2, "chirurgie": 3}
            if type_source in tab_map:
                self.tabs.setCurrentIndex(tab_map[type_source])
        else:
            CustomMessageBox.warning(self, "Erreur d'enregistrement", msg)

    def _reset_form(self):
        self.n_type_source.setCurrentIndex(0)
        self._on_type_source_changed("consultation")
        self.n_type_fichier.setCurrentIndex(0)
        self.n_chemin.clear()
        self.n_confidentialite.setCurrentIndex(1)
        self.n_description.clear()

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"""
            QFrame#MainWhiteFrame {{
                background: white;
                border-radius: 16px;
                border: 1px solid {c['border']};
            }}
            QTabWidget::pane {{
                border: none;
                background: white;
                padding: 0px;
                margin-top: 0px;
            }}
            QTabBar {{ background: white; border: none; }}
            QTabBar::tab {{
                background: white;
                color: {c['text_secondary']};
                border: none;
                border-bottom: 3px solid transparent;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
                min-width: 120px;
            }}
            QTabBar::tab:selected {{
                background: white;
                color: {c['primary']};
                border-bottom: 3px solid {c['primary']};
            }}
            QTabBar::tab:hover {{ background: white; color: {c['text_primary']}; }}
            QFrame#KpiCard {{
                background: {c['bg_card']};
                border: 1.5px solid {c['border_light']};
                border-radius: 14px;
            }}
            QLabel#KpiTitle {{
                font-size: 11px; font-weight: 500;
                color: {c['text_secondary']};
                background: transparent; border: none;
            }}
            QLabel#SectionLabel {{
                font-size: 13px; font-weight: 600;
                color: {c['text_secondary']};
                background: transparent; border: none;
            }}
            QLabel#StatsTitle {{
                font-size: 16px; font-weight: 700;
                color: {c['text_primary']};
                background: transparent;
            }}
            QFrame#StatsSep {{ color: {c['border']}; margin: 4px 0; }}
            QLineEdit#SearchInput {{
                background: {c['bg_card']};
                border: 1.5px solid {c['border']};
                border-radius: 10px;
                padding: 0 12px;
                font-size: 12px;
                color: {c['text_primary']};
            }}
            QLineEdit#SearchInput:focus {{ border-color: {c['primary']}; }}
            QComboBox#StatusFilter {{
                background: {c['bg_card']};
                border: 1.5px solid {c['border']};
                border-radius: 10px;
                padding: 0 10px;
                font-size: 12px;
                color: {c['text_primary']};
            }}
            QPushButton#PrimaryButton {{
                background: {c['primary']}; color: white;
                border: none; border-radius: 10px;
                font-size: 13px; font-weight: 600;
            }}
            QPushButton#PrimaryButton:hover {{ background: {c['primary_hover']}; }}
            QPushButton#BtnRefreshStats {{
                background: transparent;
                border: 1.5px solid {c['border']};
                border-radius: 8px;
            }}
            QPushButton#BtnRefreshStats:hover {{ background: {c['hover']}; }}
            QScrollArea#CardsScrollArea {{
                background: transparent;
                border: none;
            }}
            QWidget#CardsContainer {{
                background: transparent;
            }}
            QLabel#DossierInfo {{
                font-size: 12px; color: {c['text_secondary']};
                background: transparent; padding: 2px 0;
            }}
            QWidget#NouveauTab {{ background: white; }}
            QFrame#FormHeader {{
                background: {c['bg_card']};
                border-radius: 14px;
                border: 1px solid {c['border_light']};
            }}
            QFrame#FormIconBox {{
                background: {c['bg_main']};
                border-radius: 10px;
                border: 1px solid {c['border_light']};
            }}
            QLabel#FormTitle {{
                font-size: 17px; font-weight: bold;
                color: {c['text_primary']};
                background: transparent; border: none;
            }}
            QLabel#FormSub {{
                font-size: 12px; color: {c['text_muted']};
                background: transparent; border: none;
            }}
            QPushButton#BtnCancel {{
                background-color: {c['bg_main']};
                color: {c['text_secondary']};
                border: 1.5px solid {c['border']};
                border-radius: 10px;
                font-size: 13px; font-weight: 500;
            }}
            QPushButton#BtnCancel:hover {{ background-color: {c['hover']}; }}
            QPushButton#BtnSave {{
                background-color: {c['primary']}; color: white;
                border-radius: 10px; font-size: 13px; font-weight: bold; border: none;
            }}
            QPushButton#BtnSave:hover {{ background-color: {c['primary_hover']}; }}
            QFrame#FormSection {{
                background: {c['bg_card']};
                border: 1.5px solid {c['border_light']};
                border-radius: 14px;
            }}
            QLabel#SectionTitle {{
                font-size: 14px; font-weight: bold;
                color: {c['primary']};
                background: transparent; border: none;
            }}
            QLabel#FieldLabel {{
                font-size: 11px; font-weight: 600;
                color: {c['text_secondary']};
                background: transparent; border: none;
            }}
            QFrame#inputWrapper {{
                background-color: {c.get('bg_input', c['bg_main'])};
                border: 1.5px solid {c['border']};
                border-radius: 10px;
            }}
            QWidget#QuickActionsBar {{
                background: white;
                border-top: 1px solid {c['border_light']};
            }}
            QPushButton#QuickActionButton {{
                background: white; border: none; border-radius: 8px;
                padding-left: 15px; text-align: left;
                font-size: 12px; font-weight: 600;
                color: {c['text_primary']};
            }}
            QPushButton#QuickActionButton:hover {{ background: {c['bg_card']}; }}
        """)
        for btn in self._qa_buttons:
            color_key = btn.property("color_key") or "primary"
            color = c.get(color_key, c["primary"])
            btn.setIcon(qta.icon(btn.property("icon_name") or "fa5s.circle", color=color))
