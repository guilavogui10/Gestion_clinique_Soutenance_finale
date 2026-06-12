"""
Onglet Historique Patient — intégré dans la vue Chirurgie.

Architecture :
  • Gauche  : timeline scrollable des chirurgies du patient sélectionné
  • Droite  : détail de la chirurgie sélectionnée, composé de cartes blanches
"""
import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QScrollArea, QFrame, QGridLayout, QSplitter,
)
from views.shared.theme_manager import theme_manager


class HistoriquePatientChirurgieView(QWidget):
    """Vue onglet — historique des chirurgies d'un patient."""

    def __init__(self, ctrl, code_session: str, parent=None):
        super().__init__(parent)
        self.ctrl = ctrl
        self.code_session = code_session
        self._selected_card = None

        self._init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    # ──────────────────────────────────────────────────────────────────────
    # Session
    # ──────────────────────────────────────────────────────────────────────

    def set_session(self, code_session: str):
        self.code_session = code_session
        self._charger_patients()

    # ──────────────────────────────────────────────────────────────────────
    # Construction UI
    # ──────────────────────────────────────────────────────────────────────

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # ── Barre supérieure ──────────────────────────────────────────────
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        ico = QLabel()
        ico.setPixmap(qta.icon("fa5s.history", color=theme_manager.colors()['danger']).pixmap(20, 20))
        title = QLabel("Historique des chirurgies")
        title.setObjectName("HistTitre")
        top_bar.addWidget(ico)
        top_bar.addWidget(title)
        top_bar.addStretch()

        lbl_combo = QLabel("Patient :")
        lbl_combo.setObjectName("HistCmbLabel")
        self.cmb_patient = QComboBox()
        self.cmb_patient.setObjectName("HistPatientCombo")
        self.cmb_patient.setMinimumWidth(300)
        self.cmb_patient.setFixedHeight(38)
        self.cmb_patient.addItem("  Sélectionner un patient...", None)
        self.cmb_patient.currentIndexChanged.connect(self._on_patient_changed)

        top_bar.addWidget(lbl_combo)
        top_bar.addWidget(self.cmb_patient)
        layout.addLayout(top_bar)

        # ── Séparateur ────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("HistHSep")
        layout.addWidget(sep)

        # ── Corps : splitter gauche / droite ──────────────────────────────
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.setChildrenCollapsible(False)

        self.splitter.addWidget(self._build_left_panel())
        self.splitter.addWidget(self._build_right_panel())
        self.splitter.setSizes([290, 800])
        layout.addWidget(self.splitter, 1)

    # ── Panneau gauche ────────────────────────────────────────────────────

    def _build_left_panel(self):
        frame = QFrame()
        frame.setObjectName("HistLeftPanel")
        frame.setFixedWidth(290)
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._timeline_container = QWidget()
        self._timeline_container.setObjectName("HistTimelineBg")
        self._timeline_layout = QVBoxLayout(self._timeline_container)
        self._timeline_layout.setContentsMargins(10, 10, 10, 10)
        self._timeline_layout.setSpacing(8)
        self._timeline_layout.addStretch()

        scroll.setWidget(self._timeline_container)
        vl.addWidget(scroll)
        return frame

    # ── Panneau droit ─────────────────────────────────────────────────────

    def _build_right_panel(self):
        frame = QFrame()
        frame.setObjectName("HistRightPanel")
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._detail_container = QWidget()
        self._detail_container.setObjectName("HistDetailBg")
        self._detail_layout = QVBoxLayout(self._detail_container)
        self._detail_layout.setContentsMargins(16, 12, 16, 16)
        self._detail_layout.setSpacing(12)
        self._detail_layout.setAlignment(Qt.AlignTop)

        self._show_empty_state("fa5s.search", "Sélectionnez un patient pour voir son historique")

        scroll.setWidget(self._detail_container)
        vl.addWidget(scroll)
        return frame

    # ──────────────────────────────────────────────────────────────────────
    # Chargement des données
    # ──────────────────────────────────────────────────────────────────────

    def _charger_patients(self):
        self.cmb_patient.blockSignals(True)
        self.cmb_patient.clear()
        self.cmb_patient.addItem("  Sélectionner un patient...", None)

        try:
            patients = self.ctrl.codes_patients_session(self.code_session) or []
        except Exception:
            patients = []

        for p in patients:
            code      = p.get("code_patient", "") if isinstance(p, dict) else str(p)
            nom       = p.get("nom", "")          if isinstance(p, dict) else ""
            prenom    = p.get("prenom", "")        if isinstance(p, dict) else ""
            a_consulte = p.get("a_consulte", 0)   if isinstance(p, dict) else 0
            label = f"  {nom} {prenom}".strip()
            if a_consulte:
                label += "  ✓"
            self.cmb_patient.addItem(label, code)

        self.cmb_patient.blockSignals(False)
        self._clear_timeline()
        self._show_empty_state("fa5s.search", "Sélectionnez un patient pour voir son historique")

    def _on_patient_changed(self):
        code_patient = self.cmb_patient.currentData()
        if not code_patient:
            self._clear_timeline()
            self._show_empty_state("fa5s.search", "Sélectionnez un patient pour voir son historique")
            return
        self._charger_historique(code_patient)

    def _charger_historique(self, code_patient: str):
        self._clear_timeline()

        try:
            rows = self.ctrl.obtenir_historique_patient(code_patient) or []
        except Exception:
            rows = []

        if not rows:
            self._show_empty_state("fa5s.folder-open", "Aucune chirurgie trouvée pour ce patient")
            return

        for i, row in enumerate(rows):
            card = self._build_timeline_card(row, is_first=(i == 0))
            # Insérer avant le stretch
            self.timeline_layout.insertWidget(self._timeline_layout.count() - 1, card)

        # Sélection automatique du premier
        self._select_timeline_card(rows[0])

    # ──────────────────────────────────────────────────────────────────────
    # Timeline — cartes gauche
    # ──────────────────────────────────────────────────────────────────────

    def _build_timeline_card(self, row, is_first=False):
        c = theme_manager.colors()

        code     = self._g(row, "code", "-")
        date     = self._g(row, "date_chururgie")
        libelle  = self._g(row, "libelle_chururgie", "-")
        p_nom    = self._g(row, "personnel_nom", "")
        p_prenom = self._g(row, "personnel_prenom", "")

        date_str = date.strftime("%d/%m/%Y") if hasattr(date, "strftime") else str(date or "-")
        dr_name  = f"Dr. {p_nom} {p_prenom}".strip() if p_nom else "Personnel non défini"

        card = QFrame()
        card.setObjectName("HistTimelineCard")
        card.setCursor(Qt.PointingHandCursor)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(12, 10, 12, 10)
        cl.setSpacing(5)

        # Ligne date + badge
        date_row = QHBoxLayout()
        date_row.setSpacing(6)

        ico_cal = QLabel()
        ico_cal.setPixmap(qta.icon("fa5s.calendar-alt", color=c['danger']).pixmap(13, 13))
        date_lbl = QLabel(date_str)
        date_lbl.setObjectName("HistTimelineDate")
        date_row.addWidget(ico_cal)
        date_row.addWidget(date_lbl)
        date_row.addStretch()

        if is_first:
            badge = QLabel("  Récent  ")
            badge.setObjectName("HistRecentBadge")
            date_row.addWidget(badge)
        cl.addLayout(date_row)

        # Médecin
        dr_row = QHBoxLayout()
        dr_row.setSpacing(6)
        ico_dr = QLabel()
        ico_dr.setPixmap(qta.icon("fa5s.user-md", color=c['text_secondary']).pixmap(12, 12))
        dr_lbl = QLabel(dr_name)
        dr_lbl.setObjectName("HistTimelineDr")
        dr_row.addWidget(ico_dr)
        dr_row.addWidget(dr_lbl, 1)
        cl.addLayout(dr_row)

        # Libellé
        lib_row = QHBoxLayout()
        lib_row.setSpacing(6)
        ico_lib = QLabel()
        ico_lib.setPixmap(qta.icon("fa5s.procedures", color=c['text_muted']).pixmap(11, 11))
        lib_lbl = QLabel(libelle or "-")
        lib_lbl.setObjectName("HistTimelineLib")
        lib_lbl.setWordWrap(True)
        lib_row.addWidget(ico_lib)
        lib_row.addWidget(lib_lbl, 1)
        cl.addLayout(lib_row)

        card.mousePressEvent = lambda e, r=row, wc=card: self._on_card_click(r, wc)
        return card

    def _on_card_click(self, row, card):
        if self._selected_card and self._selected_card is not card:
            self._selected_card.setProperty("selected", False)
            self._selected_card.style().unpolish(self._selected_card)
            self._selected_card.style().polish(self._selected_card)
        self._selected_card = card
        card.setProperty("selected", True)
        card.style().unpolish(card)
        card.style().polish(card)
        self._show_detail(row)

    def _select_timeline_card(self, row):
        """Sélectionne et affiche la première chirurgie automatiquement."""
        self._show_detail(row)
        if self._timeline_layout.count() > 1:
            first = self._timeline_layout.itemAt(0)
            if first and first.widget():
                wc = first.widget()
                self._selected_card = wc
                wc.setProperty("selected", True)
                wc.style().unpolish(wc)
                wc.style().polish(wc)

    # ──────────────────────────────────────────────────────────────────────
    # Panneau droit — détail
    # ──────────────────────────────────────────────────────────────────────

    def _clear_detail(self):
        while self._detail_layout.count():
            item = self._detail_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _clear_timeline(self):
        self._selected_card = None
        while self._timeline_layout.count() > 1:
            item = self._timeline_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _show_empty_state(self, icon_name, message):
        self._clear_detail()
        c = theme_manager.colors()

        wrapper = QWidget()
        wl = QVBoxLayout(wrapper)
        wl.setAlignment(Qt.AlignCenter)

        ico = QLabel()
        ico.setPixmap(qta.icon(icon_name, color=c['border']).pixmap(56, 56))
        ico.setAlignment(Qt.AlignCenter)

        msg = QLabel(message)
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet(f"color: {c['text_muted']}; font-size: 14px;")
        msg.setWordWrap(True)

        wl.addStretch()
        wl.addWidget(ico)
        wl.addSpacing(14)
        wl.addWidget(msg)
        wl.addStretch()

        self._detail_layout.addWidget(wrapper, 1)

    def _show_detail(self, row):
        """Charge et affiche le détail complet d'une chirurgie."""
        self._clear_detail()
        c = theme_manager.colors()

        code = self._g(row, "code", "")
        try:
            detail = self.ctrl.obtenir_chururgie_complete(code) or {}
        except Exception:
            detail = {}

        def g(key, fallback=""):
            v = detail.get(key) if detail else None
            if v is not None and v != "":
                return v
            if isinstance(row, dict):
                return row.get(key) or fallback
            return getattr(row, key, fallback) or fallback

        # Champs chirurgie
        date      = g("date_chururgie")
        libelle   = g("libelle_chururgie", "-")
        frais     = g("frais_chururgie", 0)
        statut    = g("statut_facture", "-")
        compte_rendu = g("compte_rendu_operatoire", "")
        code_acte = g("code_acte", "-")
        # Champs patient
        p_nom     = g("patient_nom", "")
        p_prenom  = g("patient_prenom", "")
        p_tel     = g("patient_telephone", "")
        p_adr     = g("patient_adresse", "")
        p_dob     = g("patient_date_naissance", "")
        # Champs personnel
        per_nom   = g("personnel_nom", "")
        per_prenom = g("personnel_prenom", "")
        per_fonc  = g("personnel_fonction", "")

        date_str  = date.strftime("%d/%m/%Y") if hasattr(date, "strftime") else str(date or "-")
        frais_str = f"{float(frais or 0):,.0f} GNF".replace(",", " ")
        dr_name   = f"Dr. {per_nom} {per_prenom}".strip() if per_nom else "Non défini"

        # ── Ligne 1 : patient (gauche) + personnel (droite) ───────────────
        row_top = QWidget()
        row_top_l = QHBoxLayout(row_top)
        row_top_l.setContentsMargins(0, 0, 0, 0)
        row_top_l.setSpacing(12)
        row_top_l.addWidget(
            self._card_patient_header(p_nom, p_prenom, p_tel, p_adr, p_dob, c)
        )
        row_top_l.addWidget(
            self._card_personnel_header(per_nom, per_prenom, per_fonc, dr_name, libelle, date_str, c)
        )
        self._detail_layout.addWidget(row_top)

        # ── Ligne 2 : grille d'informations chirurgie ─────────────────────
        infos = [
            ("fa5s.barcode",            "Code chirurgie",     code),
            ("fa5s.calendar-alt",       "Date",               date_str),
            ("fa5s.money-bill-wave",    "Frais",              frais_str),
            ("fa5s.file-invoice-dollar","Statut facture",     statut),
            ("fa5s.link",               "Code acte",          code_acte),
            ("fa5s.procedures",         "Libellé",            libelle),
        ]
        self._detail_layout.addWidget(self._card_info_grid(infos, c))

        # ── Ligne 3 : compte rendu opératoire ─────────────────────────────
        if compte_rendu:
            self._detail_layout.addWidget(self._card_compte_rendu(compte_rendu, c))

    # ──────────────────────────────────────────────────────────────────────
    # Builders de cartes
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _white_card():
        f = QFrame()
        f.setObjectName("HistDetailCard")
        return f

    def _card_patient_header(self, nom, prenom, tel, adresse, dob, c):
        card = self._white_card()
        cl = QHBoxLayout(card)
        cl.setContentsMargins(18, 16, 18, 16)
        cl.setSpacing(16)

        initiales = ((nom[:1] if nom else "") + (prenom[:1] if prenom else "")).upper() or "?"
        avatar = QLabel(initiales)
        avatar.setFixedSize(56, 56)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setObjectName("HistAvatar")

        info_w = QWidget()
        info_l = QVBoxLayout(info_w)
        info_l.setContentsMargins(0, 0, 0, 0)
        info_l.setSpacing(6)

        name_lbl = QLabel(f"{nom} {prenom}".strip())
        name_lbl.setObjectName("HistPatientName")
        info_l.addWidget(name_lbl)

        sub_row = QHBoxLayout()
        sub_row.setSpacing(18)
        if tel:
            sub_row.addWidget(self._icon_text("fa5s.phone-alt", tel, c))
        if dob:
            dob_str = dob.strftime("%d/%m/%Y") if hasattr(dob, "strftime") else str(dob)
            sub_row.addWidget(self._icon_text("fa5s.birthday-cake", dob_str, c))
        if adresse:
            sub_row.addWidget(self._icon_text("fa5s.map-marker-alt", str(adresse)[:40], c))
        sub_row.addStretch()
        info_l.addLayout(sub_row)

        cl.addWidget(avatar)
        cl.addWidget(info_w, 1)
        return card

    def _card_personnel_header(self, nom, prenom, fonction, dr_name, libelle, date_str, c):
        card = self._white_card()
        cl = QHBoxLayout(card)
        cl.setContentsMargins(18, 16, 18, 16)
        cl.setSpacing(16)

        initiales = ((nom[:1] if nom else "") + (prenom[:1] if prenom else "")).upper() or "Dr"
        avatar = QLabel(initiales)
        avatar.setFixedSize(56, 56)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setObjectName("HistPersonnelAvatar")

        info_w = QWidget()
        info_l = QVBoxLayout(info_w)
        info_l.setContentsMargins(0, 0, 0, 0)
        info_l.setSpacing(6)

        name_lbl = QLabel(dr_name or "Personnel non défini")
        name_lbl.setObjectName("HistPatientName")
        info_l.addWidget(name_lbl)

        sub_row = QHBoxLayout()
        sub_row.setSpacing(18)
        if fonction:
            sub_row.addWidget(self._icon_text("fa5s.briefcase-medical", fonction, c))
        if libelle and libelle != "-":
            sub_row.addWidget(self._icon_text("fa5s.procedures", libelle, c))
        if date_str:
            sub_row.addWidget(self._icon_text("fa5s.calendar-check", f"Chirurgie du {date_str}", c))
        sub_row.addStretch()
        info_l.addLayout(sub_row)

        cl.addWidget(avatar)
        cl.addWidget(info_w, 1)
        return card

    def _card_info_grid(self, infos, c):
        card = self._white_card()
        outer = QVBoxLayout(card)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(10)

        # Titre section
        title_row = QHBoxLayout()
        title_ico = QLabel()
        title_ico.setPixmap(qta.icon("fa5s.info-circle", color=c['danger']).pixmap(14, 14))
        title_lbl = QLabel("Informations de la chirurgie")
        title_lbl.setObjectName("HistCardSectionTitle")
        title_row.addWidget(title_ico)
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        outer.addLayout(title_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("HistCardSep")
        outer.addWidget(sep)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        for i, (icon_name, label, value) in enumerate(infos):
            row_i = i // 2
            col_i = i % 2

            item_f = QFrame()
            item_f.setObjectName("HistInfoItem")
            item_l = QVBoxLayout(item_f)
            item_l.setContentsMargins(12, 10, 12, 10)
            item_l.setSpacing(4)

            top = QHBoxLayout()
            top.setSpacing(6)
            ico = QLabel()
            ico.setPixmap(qta.icon(icon_name, color=c['danger']).pixmap(12, 12))
            lbl = QLabel(label)
            lbl.setObjectName("HistInfoLabel")
            top.addWidget(ico)
            top.addWidget(lbl)
            top.addStretch()

            val = QLabel(str(value) if value else "-")
            val.setObjectName("HistInfoValue")
            val.setWordWrap(True)

            item_l.addLayout(top)
            item_l.addWidget(val)
            grid.addWidget(item_f, row_i, col_i)

        outer.addLayout(grid)
        return card

    def _card_compte_rendu(self, texte, c):
        card = self._white_card()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(18, 14, 18, 14)
        cl.setSpacing(8)

        title_row = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(qta.icon("fa5s.notes-medical", color=c['danger']).pixmap(16, 16))
        title_lbl = QLabel("Compte rendu opératoire")
        title_lbl.setObjectName("HistCardSectionTitle")
        title_row.addWidget(ico)
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        cl.addLayout(title_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("HistCardSep")
        cl.addWidget(sep)

        txt = QLabel(texte)
        txt.setObjectName("HistConclusionText")
        txt.setWordWrap(True)
        cl.addWidget(txt)
        return card

    # ──────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _g(row, key, fallback=""):
        """Lecture robuste dict ou objet."""
        if isinstance(row, dict):
            v = row.get(key)
        else:
            v = getattr(row, key, None)
        return v if (v is not None and v != "") else fallback

    @staticmethod
    def _icon_text(icon_name, text, c, color=None):
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(5)
        ico = QLabel()
        ico.setPixmap(qta.icon(icon_name, color=color or c['text_secondary']).pixmap(12, 12))
        txt = QLabel(str(text))
        txt.setObjectName("HistIconText")
        l.addWidget(ico)
        l.addWidget(txt)
        return w

    # ──────────────────────────────────────────────────────────────────────
    # Thème
    # ──────────────────────────────────────────────────────────────────────

    def apply_theme(self):
        c = theme_manager.colors()
        danger = c['danger']
        danger_bg = c['danger_bg']
        self.setStyleSheet(f"""
            /* ── Fond général ── */
            QWidget {{
                background: {c['bg_main']};
                font-family: 'Segoe UI', sans-serif;
            }}

            /* ── Barre supérieure ── */
            QLabel#HistTitre {{
                font-size: 16px; font-weight: 700;
                color: {c['text_primary']};
            }}
            QLabel#HistCmbLabel {{
                font-size: 13px; color: {c['text_secondary']};
            }}
            QComboBox#HistPatientCombo {{
                background: {c['bg_input']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 0 14px;
                color: {c['text_primary']};
                font-size: 13px;
            }}
            QComboBox#HistPatientCombo:focus {{ border-color: {danger}; }}
            QComboBox#HistPatientCombo::drop-down {{ border: none; width: 28px; }}
            QComboBox#HistPatientCombo QAbstractItemView {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                selection-background-color: {danger_bg};
                color: {c['text_primary']};
            }}
            QFrame#HistHSep {{ color: {c['border']}; }}

            /* ── Panneau gauche ── */
            QFrame#HistLeftPanel {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 14px;
            }}
            QWidget#HistTimelineBg {{ background: transparent; }}

            /* ── Cards timeline ── */
            QFrame#HistTimelineCard {{
                background: {c['bg_card']};
                border: 1px solid {c['border_light']};
                border-radius: 10px;
            }}
            QFrame#HistTimelineCard:hover {{
                background: {danger_bg};
                border-color: {danger};
            }}
            QFrame#HistTimelineCard[selected="true"] {{
                background: {danger_bg};
                border: 2px solid {danger};
            }}
            QLabel#HistTimelineDate {{
                font-size: 13px; font-weight: 700; color: {danger};
            }}
            QLabel#HistTimelineDr {{
                font-size: 12px; font-weight: 600; color: {c['text_primary']};
            }}
            QLabel#HistTimelineLib {{
                font-size: 11px; color: {c['text_secondary']};
            }}
            QLabel#HistRecentBadge {{
                background: {danger_bg};
                color: {danger};
                border: 1px solid {danger}55;
                border-radius: 6px;
                font-size: 10px; font-weight: 700;
                padding: 2px 8px;
            }}

            /* ── Panneau droit ── */
            QFrame#HistRightPanel {{ background: {c['bg_main']}; }}
            QWidget#HistDetailBg  {{ background: {c['bg_main']}; }}

            /* ── Cartes blanches ── */
            QFrame#HistDetailCard {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 12px;
            }}

            /* ── Header patient ── */
            QLabel#HistAvatar {{
                background: {danger};
                color: {c['text_inverse']};
                border-radius: 28px;
                font-size: 20px; font-weight: 700;
            }}
            QLabel#HistPersonnelAvatar {{
                background: {c['warning']};
                color: {c['text_inverse']};
                border-radius: 28px;
                font-size: 20px; font-weight: 700;
            }}
            QLabel#HistPatientName {{
                font-size: 16px; font-weight: 700; color: {c['text_primary']};
            }}
            QLabel#HistIconText {{
                font-size: 12px; color: {c['text_secondary']};
            }}

            /* ── Grille infos ── */
            QFrame#HistInfoItem {{
                background: {c['bg_card']};
                border: 1px solid {c['border_light']};
                border-radius: 8px;
            }}
            QLabel#HistInfoLabel {{
                font-size: 11px; font-weight: 600; color: {c['text_secondary']};
            }}
            QLabel#HistInfoValue {{
                font-size: 13px; font-weight: 700; color: {c['text_primary']};
            }}

            /* ── Titre section + séparateur ── */
            QLabel#HistCardSectionTitle {{
                font-size: 13px; font-weight: 700; color: {c['text_primary']};
            }}
            QFrame#HistCardSep {{ color: {c['border_light']}; }}

            /* ── Compte rendu ── */
            QLabel#HistConclusionText {{
                font-size: 13px; color: {c['text_primary']};
                padding: 4px 0;
            }}

            /* ── Scrollbars fines ── */
            QScrollBar:vertical {{
                background: transparent; width: 6px; margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {c['border']}; border-radius: 3px; min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

    # ──────────────────────────────────────────────────────────────────────
    # Propriété pour accéder au layout timeline
    # ──────────────────────────────────────────────────────────────────────

    @property
    def timeline_layout(self):
        return self._timeline_layout
