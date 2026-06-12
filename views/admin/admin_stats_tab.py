"""
Onglet Statistiques — Vue globale admin.
Layout compact sans scroll : tout visible en une page.
"""
import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGraphicsDropShadowEffect, QPushButton, QSizePolicy
)
from views.shared.theme_manager import theme_manager


# ─────────────────────────────────────────────────────────────────────────────
# Carte KPI compacte
# ─────────────────────────────────────────────────────────────────────────────

class KpiCard(QFrame):

    def __init__(self, title: str, icon: str, color: str, parent=None):
        super().__init__(parent)
        self._title = title
        self._icon  = icon
        self._color = color
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(55)
        self._build()
        theme_manager.theme_changed.connect(self.apply_theme)

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(10, 6, 10, 6)
        root.setSpacing(8)

        # Icône
        self._ico = QLabel()
        self._ico.setFixedSize(28, 28)
        self._ico.setAlignment(Qt.AlignCenter)

        # Textes
        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(1)

        self._title_lbl = QLabel(self._title)
        self._title_lbl.setWordWrap(True)
        self._val_lbl   = QLabel("—")
        self._sub_lbl   = QLabel("")
        self._sub_lbl.hide()

        col.addWidget(self._title_lbl)
        col.addWidget(self._val_lbl)
        col.addWidget(self._sub_lbl)

        root.addWidget(self._ico, 0, Qt.AlignTop)
        root.addLayout(col, 1)

        self.apply_theme()

    def set_value(self, value: str, subtitle: str = ""):
        self._val_lbl.setText(str(value))
        if subtitle:
            self._sub_lbl.setText(subtitle)
            self._sub_lbl.show()
        else:
            self._sub_lbl.hide()

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"""
            QFrame {{
                background:{c['bg_card']};
                border:1px solid {c['border']};
                border-radius:10px;
            }}
            QFrame:hover {{ border-color:{self._color}; }}
        """)
        self._ico.setStyleSheet(
            f"background:{self._color}18; border:none; border-radius:14px;"
        )
        self._ico.setPixmap(
            qta.icon(self._icon, color=self._color).pixmap(QSize(14, 14))
        )
        self._title_lbl.setStyleSheet(
            f"color:{c['text_secondary']}; font-size:9px; font-weight:600; border:none;"
        )
        self._val_lbl.setStyleSheet(
            f"color:{self._color}; font-size:17px; font-weight:800; border:none;"
        )
        self._sub_lbl.setStyleSheet(
            f"color:{c['text_muted']}; font-size:8px; font-weight:500; border:none;"
        )


# ─────────────────────────────────────────────────────────────────────────────
# En-tête de section (minimaliste)
# ─────────────────────────────────────────────────────────────────────────────

class _SectionHeader(QWidget):

    def __init__(self, title: str, icon: str, parent=None):
        super().__init__(parent)
        self._title = title
        self._icon  = icon
        self.setFixedHeight(20)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(2, 0, 0, 0)
        lay.setSpacing(5)
        self._ico = QLabel()
        self._ico.setFixedSize(14, 14)
        self._lbl = QLabel(title)
        self._sep = QFrame()
        self._sep.setFrameShape(QFrame.HLine)
        self._sep.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        lay.addWidget(self._ico)
        lay.addWidget(self._lbl)
        lay.addWidget(self._sep, 1)
        theme_manager.theme_changed.connect(self._style)
        self._style()

    def _style(self):
        c = theme_manager.colors()
        self._ico.setPixmap(
            qta.icon(self._icon, color=c['primary']).pixmap(QSize(10, 10))
        )
        self._lbl.setStyleSheet(
            f"color:{c['text_secondary']}; font-size:10px; font-weight:700; border:none;"
        )
        self._sep.setStyleSheet(f"background:{c['border_light']}; border:none;")


# ─────────────────────────────────────────────────────────────────────────────
# Widget principal
# ─────────────────────────────────────────────────────────────────────────────

class AdminStatsTab(QWidget):

    def __init__(self, consultation_ctrl, examen_ctrl, chirurgie_ctrl,
                 lunette_ctrl, rendez_vous_ctrl, visite_ctrl, parent=None):
        super().__init__(parent)
        self.ctrl_consultation = consultation_ctrl
        self.ctrl_examen       = examen_ctrl
        self.ctrl_chirurgie    = chirurgie_ctrl
        self.ctrl_lunette      = lunette_ctrl
        self.ctrl_rdv          = rendez_vous_ctrl
        self.ctrl_visite       = visite_ctrl
        self.code_session      = None

        try:
            from controllers.controleur_patient import ControleurPatient
            self.ctrl_patient = ControleurPatient()
        except Exception as e:
            print(f"[AdminStatsTab] ctrl_patient: {e}")
            self.ctrl_patient = None

        try:
            from controllers.controleur_personnel import ControllerPersonnel
            self.ctrl_personnel = ControllerPersonnel()
        except Exception as e:
            print(f"[AdminStatsTab] ctrl_personnel: {e}")
            self.ctrl_personnel = None

        try:
            from controllers.controleur_fournisseur import FournisseurControleur
            self.ctrl_fournisseur = FournisseurControleur()
        except Exception as e:
            print(f"[AdminStatsTab] ctrl_fournisseur: {e}")
            self.ctrl_fournisseur = None

        try:
            from controllers.controleur_statistiques_financieres import StatistiquesFinancieresControleur
            self.ctrl_fin = StatistiquesFinancieresControleur()
        except Exception as e:
            print(f"[AdminStatsTab] ctrl_fin: {e}")
            self.ctrl_fin = None

        self._build_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    # ─────────────────────────────────────────────────────────────────
    # Construction UI
    # ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 4, 10, 6)
        root.setSpacing(4)

        # ── Bouton Actualiser (compact, aligné à droite) ──────────────
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        self._btn_refresh = QPushButton("  Actualiser")
        self._btn_refresh.setFixedHeight(24)
        self._btn_refresh.setCursor(Qt.PointingHandCursor)
        self._btn_refresh.setObjectName("AdminRefreshBtn")
        self._btn_refresh.clicked.connect(self.charger_donnees)
        top.addStretch()
        top.addWidget(self._btn_refresh)
        root.addLayout(top)

        def _row(*cards):
            lay = QHBoxLayout()
            lay.setSpacing(6)
            for card in cards:
                lay.addWidget(card)
            return lay

        # ── Section 1 : Activité du jour ─────────────────────────────
        root.addWidget(_SectionHeader("Activité du jour", "fa5s.calendar-day"))
        self.kpi_visites_jour   = KpiCard("Visites aujourd'hui",   "fa5s.door-open",      "#3B82F6")
        self.kpi_consult_jour   = KpiCard("Consultations du jour", "fa5s.stethoscope",    "#10B981")
        self.kpi_examens_jour   = KpiCard("Examens du jour",       "fa5s.vials",          "#F59E0B")
        self.kpi_chirurgie_jour = KpiCard("Chirurgies du jour",    "fa5s.procedures",     "#EF4444")
        self.kpi_lunettes_jour  = KpiCard("Lunettes du jour",      "fa5s.glasses",        "#8B5CF6")
        self.kpi_rdv_jour       = KpiCard("Rendez-vous du jour",   "fa5s.calendar-check", "#06B6D4")
        root.addLayout(_row(self.kpi_visites_jour, self.kpi_consult_jour,
                            self.kpi_examens_jour, self.kpi_chirurgie_jour,
                            self.kpi_lunettes_jour, self.kpi_rdv_jour), 1)

        # ── Section 2 : Session en cours ─────────────────────────────
        root.addWidget(_SectionHeader("Session en cours", "fa5s.layer-group"))
        self.kpi_consult_session  = KpiCard("Total consultations", "fa5s.notes-medical",  "#3B82F6")
        self.kpi_examens_session  = KpiCard("Total examens",       "fa5s.microscope",     "#10B981")
        self.kpi_chir_session     = KpiCard("Total chirurgies",    "fa5s.user-md",        "#EF4444")
        self.kpi_lunettes_session = KpiCard("Total lunettes",      "fa5s.eye",            "#8B5CF6")
        self.kpi_rdv_session      = KpiCard("Total rendez-vous",   "fa5s.calendar-alt",   "#06B6D4")
        self.kpi_en_attente       = KpiCard("Patients en attente", "fa5s.hourglass-half", "#F59E0B")
        root.addLayout(_row(self.kpi_consult_session, self.kpi_examens_session,
                            self.kpi_chir_session, self.kpi_lunettes_session,
                            self.kpi_rdv_session, self.kpi_en_attente), 1)

        # ── Section 3 : Finances (session) ───────────────────────────
        root.addWidget(_SectionHeader("Finances — Session", "fa5s.coins"))
        self.kpi_encaissements   = KpiCard("Encaissements (GNF)",     "fa5s.hand-holding-usd", "#10B981")
        self.kpi_decaissements   = KpiCard("Décaissements (GNF)",     "fa5s.money-bill-wave",  "#EF4444")
        self.kpi_solde_net       = KpiCard("Solde net (GNF)",         "fa5s.balance-scale",    "#3B82F6")
        self.kpi_montant_consult = KpiCard("Montant consultations",   "fa5s.stethoscope",      "#F59E0B")
        root.addLayout(_row(self.kpi_encaissements, self.kpi_decaissements,
                            self.kpi_solde_net, self.kpi_montant_consult), 1)

        # ── Section 4 : Répartition financière ───────────────────────
        root.addWidget(_SectionHeader("Répartition financière", "fa5s.chart-pie"))
        self.kpi_montant_examen   = KpiCard("Montant examens",      "fa5s.vials",      "#10B981")
        self.kpi_montant_chir     = KpiCard("Montant chirurgies",   "fa5s.procedures", "#EF4444")
        self.kpi_montant_lunettes = KpiCard("Montant lunettes",     "fa5s.glasses",    "#8B5CF6")
        self.kpi_montant_presc    = KpiCard("Montant prescriptions","fa5s.pills",      "#F97316")
        root.addLayout(_row(self.kpi_montant_examen, self.kpi_montant_chir,
                            self.kpi_montant_lunettes, self.kpi_montant_presc), 1)

        # ── Section 5 : Patients, Personnel & Fournisseurs ───────────
        root.addWidget(_SectionHeader("Patients, Personnel & Fournisseurs", "fa5s.users"))
        self.kpi_total_patients    = KpiCard("Total patients",        "fa5s.user-injured",   "#3B82F6")
        self.kpi_total_personnel   = KpiCard("Total personnel",       "fa5s.user-nurse",     "#10B981")
        self.kpi_total_fournisseurs= KpiCard("Total fournisseurs",    "fa5s.truck",          "#F97316")
        self.kpi_fournisseurs_actifs=KpiCard("Fournisseurs actifs",   "fa5s.check-circle",   "#10B981")
        self.kpi_urgences          = KpiCard("Urgences actives",      "fa5s.ambulance",      "#EF4444")
        self.kpi_visites_terminees = KpiCard("Visites terminées",     "fa5s.door-open",      "#06B6D4")
        root.addLayout(_row(self.kpi_total_patients, self.kpi_total_personnel,
                            self.kpi_total_fournisseurs, self.kpi_fournisseurs_actifs,
                            self.kpi_urgences, self.kpi_visites_terminees), 1)

    # ─────────────────────────────────────────────────────────────────
    # Chargement synchrone (compatible barre de progression)
    # ─────────────────────────────────────────────────────────────────

    def charger_donnees(self, code_session: str = None):
        if code_session:
            self.code_session = code_session
        if not self.code_session:
            return
        try:
            self._appliquer_donnees(self._collecter_donnees())
        except Exception as e:
            print(f"[AdminStatsTab] Erreur: {e}")

    def _collecter_donnees(self) -> dict:
        s = self.code_session
        d = {}

        def _safe(fn, *args, default=0):
            try:
                return fn(*args)
            except Exception:
                return default

        d['visites_jour']    = _safe(self.ctrl_visite.obtenir_nombre_visites_aujourdhui)
        d['consult_jour']    = _safe(self.ctrl_consultation.obtenir_consultations_aujourd_hui, s)
        d['examens_jour']    = _safe(self.ctrl_examen.obtenir_examens_aujourd_hui, s)
        d['chir_jour']       = _safe(self.ctrl_chirurgie.obtenir_chururgies_aujourd_hui, s)
        d['lunettes_jour']   = _safe(self.ctrl_lunette.obtenir_total_commandes_session, s)
        try:
            rdv_j = self.ctrl_rdv.obtenir_rendez_vous_du_jour(s)
            d['rdv_jour'] = len(rdv_j) if isinstance(rdv_j, list) else int(rdv_j or 0)
        except Exception:
            d['rdv_jour'] = 0

        d['consult_session']  = _safe(self.ctrl_consultation.obtenir_nombre_total, s)
        d['examens_session']  = _safe(self.ctrl_examen.obtenir_total_examens_session, s)
        d['chir_session']     = _safe(self.ctrl_chirurgie.obtenir_total_chururgies_session, s)
        d['lunettes_session'] = _safe(self.ctrl_lunette.obtenir_total_commandes_session, s)
        try:
            rdv_l = self.ctrl_rdv.lister_rendez_vous(s)
            d['rdv_session'] = len(rdv_l) if isinstance(rdv_l, list) else int(rdv_l or 0)
        except Exception:
            d['rdv_session'] = 0
        d['en_attente'] = _safe(self.ctrl_consultation.obtenir_nombre_patients_en_attente, s)

        if self.ctrl_fin:
            d['encaissements'] = _safe(self.ctrl_fin.obtenir_total_encaissements, s, default=0.0)
            d['decaissements'] = _safe(self.ctrl_fin.obtenir_total_decaissements, s, default=0.0)
            d['solde_net']     = _safe(self.ctrl_fin.obtenir_solde_net, s, default=0.0)
            d['mnt_consult']   = _safe(self.ctrl_fin.obtenir_montant_consultations, s, default=0.0)
            d['mnt_examen']    = _safe(self.ctrl_fin.obtenir_montant_examens, s, default=0.0)
            d['mnt_chir']      = _safe(self.ctrl_fin.obtenir_montant_chirurgies, s, default=0.0)
            d['mnt_lunettes']  = _safe(self.ctrl_fin.obtenir_montant_lunettes, s, default=0.0)
            d['mnt_presc']     = _safe(self.ctrl_fin.obtenir_montant_prescriptions, s, default=0.0)
        else:
            d['encaissements'] = _safe(self.ctrl_consultation.obtenir_montant_session, s, default=0.0)
            d['decaissements'] = 0.0
            d['solde_net']     = d['encaissements']
            d['mnt_consult']   = d['encaissements']
            d['mnt_examen']    = _safe(self.ctrl_examen.obtenir_montant_session, s, default=0.0)
            d['mnt_chir']      = _safe(self.ctrl_chirurgie.obtenir_montant_total_par_session, s, default=0.0)
            d['mnt_lunettes']  = _safe(self.ctrl_lunette.obtenir_montant_total_par_session, s, default=0.0)
            d['mnt_presc']     = 0.0

        # Total patients — statistique() → {'total': X, 'filles': Y, ...}
        if self.ctrl_patient:
            try:
                sp = self.ctrl_patient.statistique()
                if isinstance(sp, dict):
                    d['total_patients'] = int(sp.get('total', 0) or 0)
                else:
                    d['total_patients'] = int(sp or 0)
            except Exception as e:
                print(f"[AdminStatsTab] total_patients: {e}")
                d['total_patients'] = 0
        else:
            d['total_patients'] = 0

        # Total personnel — nombre_total() → int
        if self.ctrl_personnel:
            try:
                d['total_personnel'] = int(self.ctrl_personnel.nombre_total() or 0)
            except Exception as e:
                print(f"[AdminStatsTab] total_personnel: {e}")
                d['total_personnel'] = 0
        else:
            d['total_personnel'] = 0

        # Fournisseurs — get_fournisseur_stats() → {'total': X, 'actifs': Y, 'inactifs': Z}
        if self.ctrl_fournisseur:
            try:
                sf = self.ctrl_fournisseur.get_fournisseur_stats()
                if isinstance(sf, dict):
                    d['total_fournisseurs']    = int(sf.get('total', 0) or 0)
                    d['fournisseurs_actifs']   = int(sf.get('actifs', 0) or 0)
                else:
                    d['total_fournisseurs']    = 0
                    d['fournisseurs_actifs']   = 0
            except Exception as e:
                print(f"[AdminStatsTab] fournisseurs: {e}")
                d['total_fournisseurs']  = 0
                d['fournisseurs_actifs'] = 0
        else:
            d['total_fournisseurs']  = 0
            d['fournisseurs_actifs'] = 0

        d['urgences']          = _safe(self.ctrl_visite.obtenir_nombre_urgences)
        d['visites_terminees'] = _safe(self.ctrl_visite.obtenir_nombre_visites_terminees)
        return d

    def _appliquer_donnees(self, d: dict):
        def _fmt(v) -> str:
            try:
                return f"{float(v):,.0f}".replace(",", " ")
            except Exception:
                return "0"

        self.kpi_visites_jour.set_value(str(d.get('visites_jour', 0)))
        self.kpi_consult_jour.set_value(str(d.get('consult_jour', 0)))
        self.kpi_examens_jour.set_value(str(d.get('examens_jour', 0)))
        self.kpi_chirurgie_jour.set_value(str(d.get('chir_jour', 0)))
        self.kpi_lunettes_jour.set_value(str(d.get('lunettes_jour', 0)))
        self.kpi_rdv_jour.set_value(str(d.get('rdv_jour', 0)))

        self.kpi_consult_session.set_value(str(d.get('consult_session', 0)))
        self.kpi_examens_session.set_value(str(d.get('examens_session', 0)))
        self.kpi_chir_session.set_value(str(d.get('chir_session', 0)))
        self.kpi_lunettes_session.set_value(str(d.get('lunettes_session', 0)))
        self.kpi_rdv_session.set_value(str(d.get('rdv_session', 0)))
        self.kpi_en_attente.set_value(str(d.get('en_attente', 0)))

        self.kpi_encaissements.set_value(_fmt(d.get('encaissements', 0)))
        self.kpi_decaissements.set_value(_fmt(d.get('decaissements', 0)))
        self.kpi_solde_net.set_value(_fmt(d.get('solde_net', 0)))
        self.kpi_montant_consult.set_value(_fmt(d.get('mnt_consult', 0)))

        self.kpi_montant_examen.set_value(_fmt(d.get('mnt_examen', 0)))
        self.kpi_montant_chir.set_value(_fmt(d.get('mnt_chir', 0)))
        self.kpi_montant_lunettes.set_value(_fmt(d.get('mnt_lunettes', 0)))
        self.kpi_montant_presc.set_value(_fmt(d.get('mnt_presc', 0)))

        self.kpi_total_patients.set_value(str(d.get('total_patients', 0)))
        self.kpi_total_personnel.set_value(str(d.get('total_personnel', 0)))
        self.kpi_total_fournisseurs.set_value(str(d.get('total_fournisseurs', 0)))
        self.kpi_fournisseurs_actifs.set_value(str(d.get('fournisseurs_actifs', 0)))
        self.kpi_urgences.set_value(str(d.get('urgences', 0)))
        self.kpi_visites_terminees.set_value(str(d.get('visites_terminees', 0)))

    # ─────────────────────────────────────────────────────────────────
    # Thème
    # ─────────────────────────────────────────────────────────────────

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"background:{c['bg_main']};")
        self._btn_refresh.setIcon(qta.icon("fa5s.sync-alt", color=c['primary']))
        self._btn_refresh.setStyleSheet(f"""
            QPushButton#AdminRefreshBtn {{
                background:{c['primary_light']};
                color:{c['primary']};
                border:1px solid {c['primary']};
                border-radius:6px;
                padding:0 10px;
                font-size:11px;
                font-weight:700;
            }}
            QPushButton#AdminRefreshBtn:hover {{
                background:{c['primary']};
                color:{c['text_inverse']};
            }}
        """)
