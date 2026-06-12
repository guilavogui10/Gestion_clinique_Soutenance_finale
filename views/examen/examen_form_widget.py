"""
Widget formulaire examen — même pattern que consultation_form_widget.
- Header avec boutons Annuler / Enregistrer en haut à droite
- Une seule carte, 3 rangées, pas de scroll
- Labels sans bordure ni fond
"""
import qtawesome as qta
from PySide6.QtCore    import Qt, QDateTime, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QDateTimeEdit, QFrame, QTextEdit,
)
from models.modeles_examen import Examen
from views.shared.message_box import CustomMessageBox
from views.shared.theme_manager import theme_manager


class ExamenFormWidget(QWidget):
    """
    Formulaire examen — structure identique à ConsultationFormWidget.
    Header en haut avec boutons, une seule carte section, 3 rangées, pas de scroll.
    """

    examen_saved = Signal()

    def __init__(self, controleur, code_session: str, code_acte: str = "",
                 code_personnel: str = "", examen_obj=None, parent=None):
        super().__init__(parent)
        self.controleur          = controleur
        self.code_session        = code_session
        self.code_acte_init      = code_acte
        self.code_personnel_init = code_personnel
        self.examen_obj          = examen_obj
        self.code_acte_passage   = None  # Pour terminer le passage après enregistrement

        self._actes_attente = []
        self._personnels    = []

        self._charger_donnees_combos()
        self._init_ui()
        self._connecter_validations()

        if self.examen_obj:
            self._remplir_champs()
        else:
            if self.code_acte_init:
                self._preselectionner_acte(self.code_acte_init)
            if self.code_personnel_init:
                self._preselectionner_personnel(self.code_personnel_init)

        theme_manager.theme_changed.connect(self.apply_theme)

    # =========================================================================
    # DONNÉES COMBOS
    # =========================================================================

    def _charger_donnees_combos(self):
        try:
            self._actes_attente = (
                self.controleur.obtenir_patients_attente_examen(self.code_session) or []
            )
        except Exception:
            self._actes_attente = []
        try:
            if hasattr(self.controleur, 'lister_personnel_par_roles'):
                self._personnels = self.controleur.lister_personnel_par_roles(
                    ['Laborantin']
                ) or []
            elif hasattr(self.controleur, 'lister_personnel'):
                self._personnels = self.controleur.lister_personnel() or []
        except Exception:
            self._personnels = []
        # Personnels pour "Interprété par" — même filtre de rôle que code_personnel
        try:
            if hasattr(self.controleur, 'lister_personnel_par_roles'):
                self._tous_personnels = self.controleur.lister_personnel_par_roles(
                    ['Laborantin']
                ) or []
            elif hasattr(self.controleur, 'lister_personnel'):
                self._tous_personnels = self.controleur.lister_personnel() or []
            else:
                self._tous_personnels = []
        except Exception:
            self._tous_personnels = []

    # =========================================================================
    # UI PRINCIPALE
    # =========================================================================

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 4, 20, 12)
        outer.setSpacing(10)

        self._setup_header(outer)
        self._section_infos(outer)
        self._section_info_bas(outer)
        outer.addStretch()

        self.apply_theme()

    # =========================================================================
    # HEADER — titre + boutons Annuler / Enregistrer
    # =========================================================================

    def _setup_header(self, parent_layout):
        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(72)
        c = theme_manager.colors()
        self.header_frame.setStyleSheet(f"""
            background-color: {c['bg_card']};
            border-radius: 14px;
            border: none;
        """)

        layout = QHBoxLayout(self.header_frame)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(14)

        self._icon_box = QFrame()
        icon_box = self._icon_box
        icon_box.setFixedSize(46, 46)
        icon_box.setStyleSheet(f"""
            background-color: {c['bg_main']};
            border-radius: 10px;
            border: 1px solid {c['border_light']};
        """)
        ib_layout = QHBoxLayout(icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        self._ico_header = QLabel()
        self._ico_header.setPixmap(qta.icon("fa5s.microscope", color=c['primary']).pixmap(22, 22))
        self._ico_header.setAlignment(Qt.AlignCenter)
        ib_layout.addWidget(self._ico_header, alignment=Qt.AlignCenter)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self._lbl_main = QLabel("Enregistrement d'un Examen")
        self._lbl_main.setStyleSheet(
            f"font-size: 17px; font-weight: bold; color: {c['text_primary']};"
            " background: transparent; border: none;"
        )
        self._lbl_sub = QLabel("Veuillez remplir les informations de l'examen")
        self._lbl_sub.setStyleSheet(
            f"font-size: 12px; color: {c['text_muted']};"
            " background: transparent; border: none;"
        )
        title_col.addWidget(self._lbl_main)
        title_col.addWidget(self._lbl_sub)

        layout.addWidget(icon_box)
        layout.addLayout(title_col)
        layout.addStretch()

        self.btn_cancel = QPushButton(
            qta.icon("fa5s.times", color=c['text_secondary']), " Annuler"
        )
        self.btn_cancel.setFixedSize(110, 40)
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['bg_main']};
                color: {c['text_secondary']};
                border: 1.5px solid {c['border']};
                border-radius: 10px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background-color: {c['hover']}; }}
        """)
        self.btn_cancel.clicked.connect(self._on_cancel)

        label_save = " Enregistrer" if not self.examen_obj else " Mettre à jour"
        self.btn_save = QPushButton(
            qta.icon("fa5s.save", color=c['text_inverse']), label_save
        )
        self.btn_save.setFixedSize(150, 40)
        self.btn_save.setEnabled(False)
        self._apply_save_btn_style()
        self.btn_save.clicked.connect(self._soumettre)

        layout.addWidget(self.btn_cancel)
        layout.addWidget(self.btn_save)
        parent_layout.addWidget(self.header_frame)

    def _apply_save_btn_style(self):
        c = theme_manager.colors()
        self.btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['border']};
                color: {c['text_muted']};
                border-radius: 10px;
                font-weight: bold;
                font-size: 13px;
                border: none;
            }}
            QPushButton:enabled {{
                background-color: {c['primary']};
                color: {c['text_inverse']};
            }}
            QPushButton:enabled:hover {{ background-color: {c['primary_hover']}; }}
        """)

    # =========================================================================
    # HELPERS — champ badge-icône (même API que consultation)
    # =========================================================================

    def _make_field(self, label_text: str, widget, icon_name: str, color_key: str,
                    height: int = 42, align_top: bool = False):
        """Retourne (QVBoxLayout, wrapper_QFrame). Enregistre dans _field_registry."""
        c = theme_manager.colors()
        vbox = QVBoxLayout()
        vbox.setSpacing(4)

        lbl = QLabel(label_text)
        vbox.addWidget(lbl)

        wrapper = QFrame()
        wrapper.setObjectName("inputWrapper")
        if align_top:
            wrapper.setMinimumHeight(height)
        else:
            wrapper.setFixedHeight(height)
        self._apply_wrapper_style(wrapper)

        hbox = QHBoxLayout(wrapper)
        hbox.setContentsMargins(8, 5, 8, 5)
        hbox.setSpacing(8)
        v_align = Qt.AlignTop if align_top else Qt.AlignVCenter

        badge = QFrame()
        badge.setFixedSize(28, 28)
        bl = QHBoxLayout(badge)
        bl.setContentsMargins(0, 0, 0, 0)
        ico_lbl = QLabel()
        ico_lbl.setAlignment(Qt.AlignCenter)
        ico_lbl.setStyleSheet("border: none; background: transparent;")
        bl.addWidget(ico_lbl, alignment=Qt.AlignCenter)

        self._clear_widget_style(widget, c)
        hbox.addWidget(badge, 0, v_align)
        hbox.addWidget(widget, 1)
        vbox.addWidget(wrapper)

        if not hasattr(self, '_field_registry'):
            self._field_registry = []
        self._field_registry.append({
            'wrapper':   wrapper,
            'badge':     badge,
            'ico_lbl':   ico_lbl,
            'lbl':       lbl,
            'icon_name': icon_name,
            'color_key': color_key,
        })
        self._refresh_field(self._field_registry[-1], c)

        return vbox, wrapper

    def _refresh_field(self, entry: dict, c: dict):
        icon_color = c[entry['color_key']]
        entry['badge'].setStyleSheet(
            f"background-color: {icon_color}20; border-radius: 7px; border: none;"
        )
        entry['ico_lbl'].setPixmap(
            qta.icon(entry['icon_name'], color=icon_color).pixmap(14, 14)
        )
        entry['lbl'].setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {c['text_secondary']};"
            " background: transparent; border: none;"
        )
        self._apply_wrapper_style(entry['wrapper'])

    def _apply_wrapper_style(self, wrapper: QFrame, border_color: str = None):
        c = theme_manager.colors()
        bc = border_color or c['border']
        wrapper.setStyleSheet(f"""
            QFrame#inputWrapper {{
                background-color: {c['bg_input']};
                border: 1.5px solid {bc};
                border-radius: 10px;
            }}
        """)

    def _clear_widget_style(self, widget, c):
        base = (
            f"border: none; background: transparent;"
            f" font-size: 12px; color: {c['text_primary']};"
        )
        if isinstance(widget, QComboBox):
            widget.setStyleSheet(f"""
                QComboBox {{ {base} padding: 0; min-height: 28px; }}
                QComboBox::drop-down {{ border: none; width: 20px; }}
                QComboBox QAbstractItemView {{
                    background-color: {c['bg_card']};
                    border: 1px solid {c['border']};
                    border-radius: 8px;
                    color: {c['text_primary']};
                    selection-background-color: {c['primary_light']};
                    outline: none;
                }}
                QComboBox QAbstractItemView::item {{ padding: 6px 10px; min-height: 26px; }}
                QComboBox QAbstractItemView::item:hover {{ background-color: {c['hover']}; }}
                QComboBox QAbstractItemView::item:selected {{
                    background-color: {c['primary_light']}; color: {c['primary']};
                }}
            """)
        elif isinstance(widget, QDateTimeEdit):
            widget.setStyleSheet(f"QDateTimeEdit {{ {base} padding: 0; }}")
        elif isinstance(widget, QTextEdit):
            widget.setStyleSheet(f"QTextEdit {{ {base} padding: 4px 0; }}")
        else:
            widget.setStyleSheet(f"QLineEdit {{ {base} padding: 0; }}")

    def _field_widget(self, vbox: QVBoxLayout) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent; border: none;")
        w.setLayout(vbox)
        return w

    def _err_label(self) -> QLabel:
        c = theme_manager.colors()
        lbl = QLabel("")
        lbl.setStyleSheet(
            f"color: {c['danger']}; font-size: 10px; font-style: italic;"
            " background: transparent;"
        )
        lbl.setVisible(False)
        return lbl

    # =========================================================================
    # SECTION UNIQUE — 3 rangées dans une seule carte
    # =========================================================================

    def _section_infos(self, parent_layout):
        c = theme_manager.colors()
        self._section_card = QFrame()
        card = self._section_card
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {c['bg_card']};
                border: 1.5px solid {c['border_light']};
                border-radius: 14px;
            }}
        """)
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(18, 14, 18, 14)
        vbox.setSpacing(12)

        # Titre de section
        hdr = QHBoxLayout()
        self._ico_section = QLabel()
        ico = self._ico_section
        ico.setPixmap(
            qta.icon("fa5s.clipboard-list", color=c['primary']).pixmap(16, 16)
        )
        ico.setStyleSheet("border: none; background: transparent;")
        self._section_card_lbl = QLabel("Informations de l'examen")
        lbl_t = self._section_card_lbl
        lbl_t.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {c['primary']};"
            " background: transparent; border: none;"
        )
        hdr.addWidget(ico)
        hdr.addSpacing(8)
        hdr.addWidget(lbl_t)
        hdr.addStretch()
        vbox.addLayout(hdr)

        # ── Rangée 1 : Code | Libellé | Frais | Statut Facture ──
        row1 = QHBoxLayout()
        row1.setSpacing(14)
        row1.setAlignment(Qt.AlignTop)

        self.edit_code = QLineEdit()
        self.edit_code.setPlaceholderText("Ex: EXA001")
        self.edit_code.setEnabled(False)
        vb, _ = self._make_field("Code", self.edit_code, "fa5s.hashtag", "accent")
        row1.addWidget(self._field_widget(vb), 1, Qt.AlignTop)

        self.edit_libelle = QTextEdit()
        self.edit_libelle.setPlaceholderText("Ex: Fond d'œil, Tonométrie, Champ visuel...")
        self.edit_libelle.setFixedHeight(72)
        vb_lib, self._wrap_libelle = self._make_field(
            "Libellé de l'examen *", self.edit_libelle,
            "fa5s.align-left", "accent", height=76, align_top=True
        )
        self._err_libelle = self._err_label()
        vb_lib.addWidget(self._err_libelle)
        row1.addWidget(self._field_widget(vb_lib), 2, Qt.AlignTop)

        self.edit_frais = QLineEdit()
        self.edit_frais.setPlaceholderText("Ex: 80000")
        vb_frais, self._wrap_frais = self._make_field(
            "Frais de l'examen *", self.edit_frais, "fa5s.dollar-sign", "success"
        )
        self._err_frais = self._err_label()
        vb_frais.addWidget(self._err_frais)
        row1.addWidget(self._field_widget(vb_frais), 1, Qt.AlignTop)

        self.combo_statut = QComboBox()
        self.combo_statut.setEnabled(False)
        self.combo_statut.addItem("Sélectionner le statut")
        vb_stat, _ = self._make_field(
            "Statut Facture", self.combo_statut, "fa5s.file-invoice", "warning"
        )
        row1.addWidget(self._field_widget(vb_stat), 1, Qt.AlignTop)

        vbox.addLayout(row1)

        # ── Rangée 2 : Date | Code Session | Code Personnel | Code Acte ──
        row2 = QHBoxLayout()
        row2.setSpacing(14)

        self.edit_date = QDateTimeEdit()
        self.edit_date.setCalendarPopup(True)
        self.edit_date.setDateTime(QDateTime.currentDateTime())
        self.edit_date.setDisplayFormat("dd/MM/yyyy")
        vb_date, _ = self._make_field(
            "Date de l'examen *", self.edit_date, "fa5s.calendar-alt", "info"
        )
        row2.addWidget(self._field_widget(vb_date), 1, Qt.AlignTop)

        self.edit_session = QLineEdit(self.code_session or "")
        self.edit_session.setPlaceholderText("Ex: SES001")
        self.edit_session.setEnabled(False)
        vb_sess, _ = self._make_field(
            "Code Session", self.edit_session, "fa5s.graduation-cap", "accent"
        )
        row2.addWidget(self._field_widget(vb_sess), 1, Qt.AlignTop)

        self.combo_personnel = QComboBox()
        self.combo_personnel.addItem("— Sélectionner un médecin —", "")
        for p in self._personnels:
            code   = p.get('code', "")
            nom    = p.get('nom', "")
            prenom = p.get('prenom', "")
            self.combo_personnel.addItem(f"{code} — {nom} {prenom}", code)
        vb_perso, self._wrap_personnel = self._make_field(
            "Code Personnel *", self.combo_personnel, "fa5s.user-md", "primary"
        )
        self._err_personnel = self._err_label()
        vb_perso.addWidget(self._err_personnel)
        row2.addWidget(self._field_widget(vb_perso), 1, Qt.AlignTop)

        self.combo_acte = QComboBox()
        self.combo_acte.addItem("— Sélectionner un acte —", "")
        for a in self._actes_attente:
            code_acte = a.get('code_acte', "")
            nom       = a.get('nom', "")
            prenom    = a.get('prenom', "")
            code_c    = a.get('code_consultation', "")
            self.combo_acte.addItem(
                f"{code_acte} — {nom} {prenom} [{code_c}]", code_acte
            )
        vb_acte, self._wrap_acte = self._make_field(
            "Code Acte *", self.combo_acte, "fa5s.file-medical", "danger"
        )
        self._err_acte = self._err_label()
        vb_acte.addWidget(self._err_acte)
        row2.addWidget(self._field_widget(vb_acte), 1, Qt.AlignTop)

        vbox.addLayout(row2)

        # ── Rangée 3 : Interprété par | Date interprétation | Conclusion ──
        row3 = QHBoxLayout()
        row3.setSpacing(14)
        row3.setAlignment(Qt.AlignTop)

        self.combo_interpreter_par = QComboBox()
        self.combo_interpreter_par.addItem("— Sélectionner un praticien —", "")
        for p in self._tous_personnels:
            code   = p.get('code', "")
            nom    = p.get('nom', "")
            prenom = p.get('prenom', "")
            self.combo_interpreter_par.addItem(f"{code} — {nom} {prenom}", code)
        vb_int, _ = self._make_field(
            "Interprété par", self.combo_interpreter_par, "fa5s.user", "warning"
        )
        row3.addWidget(self._field_widget(vb_int), 1, Qt.AlignTop)

        self.edit_date_interpretation = QDateTimeEdit()
        self.edit_date_interpretation.setCalendarPopup(True)
        self.edit_date_interpretation.setDateTime(QDateTime.currentDateTime())
        self.edit_date_interpretation.setDisplayFormat("dd/MM/yyyy")
        vb_dint, _ = self._make_field(
            "Date d'interprétation", self.edit_date_interpretation,
            "fa5s.calendar-check", "info"
        )
        row3.addWidget(self._field_widget(vb_dint), 1, Qt.AlignTop)

        self.edit_conclusion = QTextEdit()
        self.edit_conclusion.setPlaceholderText("Saisissez la conclusion médicale...")
        self.edit_conclusion.setFixedHeight(72)
        vb_con, self._wrap_conclusion = self._make_field(
            "Conclusion médicale", self.edit_conclusion,
            "fa5s.notes-medical", "success", height=76, align_top=True
        )
        row3.addWidget(self._field_widget(vb_con), 2, Qt.AlignTop)

        vbox.addLayout(row3)
        parent_layout.addWidget(card)

    # =========================================================================
    # SECTION INFO BAS
    # =========================================================================

    def _section_info_bas(self, parent_layout):
        c = theme_manager.colors()
        self._info_bas_card = QFrame()
        card = self._info_bas_card
        card.setFixedHeight(70)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {c['primary_light']};
                border: 1.5px solid {c['border_light']};
                border-radius: 14px;
            }}
        """)
        hbox = QHBoxLayout(card)
        hbox.setContentsMargins(20, 0, 20, 0)
        hbox.setSpacing(14)

        self._ico_bas_frame = QFrame()
        ico_frame = self._ico_bas_frame
        ico_frame.setFixedSize(36, 36)
        ico_frame.setStyleSheet(
            f"background-color: {c['primary']}; border-radius: 18px;"
        )
        ifi = QHBoxLayout(ico_frame)
        ifi.setContentsMargins(0, 0, 0, 0)
        self._ico_bas_lbl = QLabel()
        il = self._ico_bas_lbl
        il.setPixmap(qta.icon("fa5s.info", color=c['text_inverse']).pixmap(14, 14))
        il.setAlignment(Qt.AlignCenter)
        ifi.addWidget(il, alignment=Qt.AlignCenter)

        txt = QVBoxLayout()
        txt.setSpacing(2)
        self._info_bas_t1 = QLabel("Informations")
        t1 = self._info_bas_t1
        t1.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {c['primary']};"
            " background: transparent;"
        )
        self._info_bas_t2 = QLabel(
            "Veuillez remplir tous les champs obligatoires avant d'enregistrer l'examen."
        )
        t2 = self._info_bas_t2
        t2.setStyleSheet(
            f"font-size: 11px; color: {c['text_secondary']}; background: transparent;"
        )
        txt.addWidget(t1)
        txt.addWidget(t2)

        hbox.addWidget(ico_frame)
        hbox.addLayout(txt)
        hbox.addStretch()
        parent_layout.addWidget(card)

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def _connecter_validations(self):
        self.edit_libelle.textChanged.connect(self._valider_formulaire)
        self.edit_frais.textChanged.connect(self._valider_formulaire)
        self.combo_acte.currentIndexChanged.connect(self._valider_formulaire)
        self.combo_personnel.currentIndexChanged.connect(self._valider_formulaire)

    def _valider_formulaire(self):
        tout_valide = True

        lib = self.edit_libelle.toPlainText().strip()
        ok, msg = self.controleur.valider_texte(lib, "libellé examen")
        self._set_field_state(self._wrap_libelle, self._err_libelle, ok, msg, bool(lib))
        if not ok:
            tout_valide = False

        frais = self.edit_frais.text().strip()
        ok, msg = self.controleur.valider_frais(frais if frais else "-1")
        self._set_field_state(self._wrap_frais, self._err_frais, ok, msg, bool(frais))
        if not ok:
            tout_valide = False

        if not self.combo_acte.currentData():
            self._set_field_state(
                self._wrap_acte, self._err_acte,
                False, "Veuillez sélectionner un acte", True
            )
            tout_valide = False
        else:
            self._set_field_state(self._wrap_acte, self._err_acte, True, "", False)

        if not self.combo_personnel.currentData():
            self._set_field_state(
                self._wrap_personnel, self._err_personnel,
                False, "Veuillez sélectionner un médecin", True
            )
            tout_valide = False
        else:
            self._set_field_state(self._wrap_personnel, self._err_personnel, True, "", False)

        self.combo_statut.clear()
        self.combo_statut.addItem(
            "attente payement" if tout_valide else "Sélectionner le statut"
        )

        self.btn_save.setEnabled(tout_valide)
        self._apply_save_btn_style()

    def _set_field_state(self, wrapper: QFrame, err_lbl: QLabel,
                         valide: bool, msg: str, has_text: bool):
        c = theme_manager.colors()
        if not valide and has_text:
            self._apply_wrapper_style(wrapper, c['danger'])
            err_lbl.setText(msg)
            err_lbl.setVisible(True)
        else:
            bc = c['border_focus'] if (valide and has_text) else c['border']
            self._apply_wrapper_style(wrapper, bc)
            err_lbl.setVisible(False)

    # =========================================================================
    # PRÉSÉLECTION
    # =========================================================================

    def pre_remplir_code_acte(self, code_acte: str):
        """Pré-remplit le formulaire avec un code_acte spécifique."""
        print(f"[ExamenFormWidget] pre_remplir_code_acte appelé avec code_acte: {code_acte}")
        
        # Recharger les données des combos pour s'assurer que le code_acte est dans la liste
        self._charger_donnees_combos()
        print(f"[ExamenFormWidget] Nombre d'actes en attente: {len(self._actes_attente)}")
        
        # Vérifier si le code_acte est dans la liste
        acte_trouve = False
        for a in self._actes_attente:
            if a.get('code_acte') == code_acte:
                acte_trouve = True
                break
        
        # Si l'acte n'est pas dans la liste (car il est en_cours), le récupérer depuis la base
        if not acte_trouve:
            print(f"[ExamenFormWidget] Acte {code_acte} non trouvé dans les actes en attente, récupération depuis la base...")
            try:
                from core.connexion_db import DBConnection
                import pymysql
                db = DBConnection()
                conn = db.connect()
                if conn:
                    cursor = conn.cursor(pymysql.cursors.DictCursor)
                    cursor.execute("""
                        SELECT 
                            am.code_acte,
                            p.nom,
                            p.prenom,
                            am.code_consultation
                        FROM acte_medical am
                        JOIN consultation c ON c.code = am.code_consultation
                        JOIN visite v ON v.code_visite = c.code_visite
                        JOIN patients p ON p.code_patient = v.code_patient
                        WHERE am.code_acte = %s
                    """, (code_acte,))
                    acte_data = cursor.fetchone()
                    db.close()
                    
                    if acte_data:
                        self._actes_attente.append(acte_data)
                        print(f"[ExamenFormWidget] Acte récupéré: {acte_data}")
            except Exception as e:
                print(f"[ExamenFormWidget] Erreur récupération acte: {e}")
        
        print(f"[ExamenFormWidget] Nombre d'actes après récupération: {len(self._actes_attente)}")
        
        # Reconstruire le combo acte avec les nouvelles données
        self.combo_acte.blockSignals(True)
        self.combo_acte.clear()
        self.combo_acte.addItem("— Sélectionner un acte —", "")
        for a in self._actes_attente:
            code_a = a.get('code_acte', "")
            nom    = a.get('nom', "")
            prenom = a.get('prenom', "")
            code_c = a.get('code_consultation', "")
            self.combo_acte.addItem(
                f"{code_a} — {nom} {prenom} [{code_c}]", code_a
            )
            if code_a == code_acte:
                print(f"[ExamenFormWidget] Code acte trouvé dans la liste: {code_a}")
        self.combo_acte.blockSignals(False)
        
        print(f"[ExamenFormWidget] Nombre d'items dans combo_acte: {self.combo_acte.count()}")
        
        # Pré-sélectionner le code_acte
        self._preselectionner_acte(code_acte)
        self._valider_formulaire()
        
        print(f"[ExamenFormWidget] Index sélectionné: {self.combo_acte.currentIndex()}")
        print(f"[ExamenFormWidget] Code acte sélectionné: {self.combo_acte.currentData()}")
    
    def _preselectionner_acte(self, code_acte: str):
        print(f"[ExamenFormWidget] _preselectionner_acte appelé avec: {code_acte}")
        for i in range(self.combo_acte.count()):
            data = self.combo_acte.itemData(i)
            print(f"[ExamenFormWidget] Item {i}: data={data}")
            if data == code_acte:
                print(f"[ExamenFormWidget] Correspondance trouvée à l'index {i}")
                self.combo_acte.setCurrentIndex(i)
                break
        self.combo_acte.setEnabled(False)

    def _preselectionner_personnel(self, code_personnel: str):
        for i in range(self.combo_personnel.count()):
            if self.combo_personnel.itemData(i) == code_personnel:
                self.combo_personnel.setCurrentIndex(i)
                break

    # =========================================================================
    # REMPLISSAGE MODE MODIFICATION
    # =========================================================================

    def _remplir_champs(self):
        obj = self.examen_obj
        if obj.code:
            self.edit_code.setText(obj.code)
        self._preselectionner_acte(obj.code_acte or "")
        self._preselectionner_personnel(obj.code_personnel or "")
        if obj.date_examen and hasattr(obj.date_examen, 'year'):
            d = obj.date_examen
            self.edit_date.setDateTime(QDateTime(d.year, d.month, d.day, 0, 0))
        self.edit_libelle.setPlainText(obj.libelle_examen or "")
        self.edit_frais.setText(str(obj.frais_examen or ""))
        self.combo_statut.clear()
        self.combo_statut.addItem(obj.statut_facture or "attente payement")
        self._preselectionner_interpreter(obj.interpreter_par or "")
        if obj.date_interpretation and hasattr(obj.date_interpretation, 'year'):
            d = obj.date_interpretation
            self.edit_date_interpretation.setDateTime(QDateTime(d.year, d.month, d.day, 0, 0))
        self.edit_conclusion.setPlainText(obj.conclusion_medicale or "")

    # =========================================================================
    # RECHARGER POUR PATIENT
    # =========================================================================

    def recharger_pour_patient(self, code_consultation: str, code_session: str = None):
        if code_session:
            self.code_session = code_session
            self.edit_session.setText(code_session)

        self._charger_donnees_combos()
        self._on_cancel()

        self.combo_acte.blockSignals(True)
        self.combo_acte.clear()
        self.combo_acte.addItem("— Sélectionner un acte —", "")
        code_acte_trouve = ""
        for a in self._actes_attente:
            code_acte = a.get('code_acte', "")
            nom       = a.get('nom', "")
            prenom    = a.get('prenom', "")
            code_c    = a.get('code_consultation', "")
            self.combo_acte.addItem(
                f"{code_acte} — {nom} {prenom} [{code_c}]", code_acte
            )
            if code_c == code_consultation:
                code_acte_trouve = code_acte
        self.combo_acte.blockSignals(False)

        if code_acte_trouve:
            self._preselectionner_acte(code_acte_trouve)

    # =========================================================================
    # ACTIONS BOUTONS
    # =========================================================================

    def _preselectionner_interpreter(self, code_personnel: str):
        """Présélectionne le praticien interprétant dans le combo."""
        for i in range(self.combo_interpreter_par.count()):
            if self.combo_interpreter_par.itemData(i) == code_personnel:
                self.combo_interpreter_par.setCurrentIndex(i)
                return
        self.combo_interpreter_par.setCurrentIndex(0)

    def _on_cancel(self):
        self.edit_libelle.clear()
        self.edit_frais.clear()
        self.combo_interpreter_par.setCurrentIndex(0)
        self.edit_conclusion.clear()
        self.combo_acte.setEnabled(True)
        self.combo_acte.setCurrentIndex(0)
        self.combo_personnel.setCurrentIndex(0)
        self.edit_date.setDateTime(QDateTime.currentDateTime())
        self.edit_date_interpretation.setDateTime(QDateTime.currentDateTime())
        self.btn_save.setEnabled(False)
        self._apply_save_btn_style()

    def _soumettre(self):
        try:
            code_acte      = self.combo_acte.currentData()
            code_personnel = self.combo_personnel.currentData()

            examen = Examen(
                code                = self.examen_obj.code if self.examen_obj else None,
                libelle_examen      = self.edit_libelle.toPlainText().strip(),
                frais_examen        = float(self.edit_frais.text().strip() or 0),
                statut_facture      = self.combo_statut.currentText(),
                date_examen         = self.edit_date.dateTime().toPython(),
                code_session        = self.code_session,
                code_personnel      = code_personnel,
                code_acte           = code_acte,
                interpreter_par     = self.combo_interpreter_par.currentData() or None,
                date_interpretation = self.edit_date_interpretation.dateTime().toPython(),
                conclusion_medicale = self.edit_conclusion.toPlainText().strip() or None,
            )

            if self.examen_obj:
                ok, msg = self.controleur.modifier_examen(examen)
            else:
                ok, msg = self.controleur.creer_examen(examen)

            if ok:
                # Si c'est un passage depuis la file d'attente, terminer le passage
                if self.code_acte_passage:
                    self._terminer_passage_automatique(self.code_acte_passage)
                
                CustomMessageBox("Succès", msg, True, self).exec()
                self._on_cancel()
                self.examen_saved.emit()
            else:
                CustomMessageBox("Erreur", msg, False, self).exec()

        except Exception as e:
            CustomMessageBox("Erreur Système", str(e), False, self).exec()
    
    def _terminer_passage_automatique(self, code_acte: str):
        """Termine automatiquement le passage après l'enregistrement de l'examen,
        puis redirige vers acte_médical pour la décision du médecin."""
        try:
            from controllers.controleur_acte_medicale import ActeMedicalControleur
            ctrl_acte = ActeMedicalControleur()
            ok, msg = ctrl_acte.terminer_passage_par_code_acte(code_acte)
            if ok:
                print(f"Passage terminé automatiquement pour acte {code_acte}")
                code_consultation = ctrl_acte.obtenir_code_consultation_par_acte(code_acte)
                self._rediriger_vers_acte_medical(code_consultation)
            else:
                print(f"Erreur lors de la terminaison automatique: {msg}")
        except Exception as e:
            print(f"Erreur _terminer_passage_automatique: {e}")

    def _rediriger_vers_acte_medical(self, code_consultation: str = None):
        """Redirige vers la vue acte_médical (Index 15) après enregistrement de l'examen."""
        try:
            parent = self.parent()
            while parent:
                if parent.__class__.__name__ == 'DashboardView':
                    parent.workspace_stack.setCurrentIndex(15)
                    if hasattr(parent, 'lbl_page_title'):
                        parent.lbl_page_title.setText("Gestion des Actes Médicaux")
                    
                    # Rafraîchir la file d'attente immédiatement
                    if hasattr(parent, 'page_actes'):
                        from PySide6.QtCore import QTimer
                        QTimer.singleShot(100, lambda: parent.page_actes._update_file_attente())
                        if code_consultation:
                            QTimer.singleShot(200, lambda c=code_consultation: parent.page_actes._filtrer_par_consultation(c))
                    break
                parent = parent.parent()
        except Exception as e:
            print(f"Erreur redirection acte_médical: {e}")

    # =========================================================================
    # THÈME
    # =========================================================================

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"QWidget {{ background: {c['bg_main']}; color: {c['text_primary']}; }}")

        # ── Header ──────────────────────────────────────────────────────────
        if hasattr(self, 'header_frame'):
            self.header_frame.setStyleSheet(f"""
                background-color: {c['bg_card']};
                border-radius: 14px; border: none;
            """)
        if hasattr(self, '_icon_box'):
            self._icon_box.setStyleSheet(f"""
                background-color: {c['bg_main']};
                border-radius: 10px;
                border: 1px solid {c['border_light']};
            """)
        if hasattr(self, '_ico_header'):
            self._ico_header.setPixmap(
                qta.icon("fa5s.microscope", color=c['primary']).pixmap(22, 22)
            )
        if hasattr(self, '_lbl_main'):
            self._lbl_main.setStyleSheet(
                f"font-size: 17px; font-weight: bold; color: {c['text_primary']};"
                " background: transparent; border: none;"
            )
        if hasattr(self, '_lbl_sub'):
            self._lbl_sub.setStyleSheet(
                f"font-size: 12px; color: {c['text_muted']}; background: transparent; border: none;"
            )

        # ── Card infos section ───────────────────────────────────────────────
        if hasattr(self, '_section_card'):
            self._section_card.setStyleSheet(f"""
                QFrame {{
                    background-color: {c['bg_card']};
                    border: 1.5px solid {c['border_light']};
                    border-radius: 14px;
                }}
            """)
        if hasattr(self, '_ico_section'):
            self._ico_section.setPixmap(
                qta.icon("fa5s.clipboard-list", color=c['primary']).pixmap(16, 16)
            )
        if hasattr(self, '_section_card_lbl'):
            self._section_card_lbl.setStyleSheet(
                f"font-size: 14px; font-weight: bold; color: {c['primary']};"
                " background: transparent; border: none;"
            )

        # ── Card bas ─────────────────────────────────────────────────────────
        if hasattr(self, '_info_bas_card'):
            self._info_bas_card.setStyleSheet(f"""
                QFrame {{
                    background-color: {c['primary_light']};
                    border: 1.5px solid {c['border_light']};
                    border-radius: 14px;
                }}
            """)
        if hasattr(self, '_ico_bas_frame'):
            self._ico_bas_frame.setStyleSheet(
                f"background-color: {c['primary']}; border-radius: 18px;"
            )
        if hasattr(self, '_ico_bas_lbl'):
            self._ico_bas_lbl.setPixmap(
                qta.icon("fa5s.info", color=c['text_inverse']).pixmap(14, 14)
            )
        if hasattr(self, '_info_bas_t1'):
            self._info_bas_t1.setStyleSheet(
                f"font-size: 13px; font-weight: bold; color: {c['primary']}; background: transparent;"
            )
        if hasattr(self, '_info_bas_t2'):
            self._info_bas_t2.setStyleSheet(
                f"font-size: 11px; color: {c['text_secondary']}; background: transparent;"
            )

        # ── Registre champs (badge + icône + label + wrapper) ────────────────
        if hasattr(self, '_field_registry'):
            for entry in self._field_registry:
                self._refresh_field(entry, c)

        # ── Widgets internes ─────────────────────────────────────────────────
        if hasattr(self, 'edit_libelle'):
            for w in (self.edit_libelle, self.edit_frais, self.combo_acte,
                      self.combo_personnel, self.edit_code, self.edit_session,
                      self.edit_date, self.combo_statut, self.combo_interpreter_par,
                      self.edit_date_interpretation, self.edit_conclusion):
                self._clear_widget_style(w, c)

        # ── Boutons ──────────────────────────────────────────────────────────
        self._apply_save_btn_style()
        if hasattr(self, 'btn_cancel'):
            self.btn_cancel.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c['bg_main']};
                    color: {c['text_secondary']};
                    border: 1.5px solid {c['border']};
                    border-radius: 10px;
                    font-size: 13px;
                    font-weight: 500;
                }}
                QPushButton:hover {{ background-color: {c['hover']}; }}
            """)
