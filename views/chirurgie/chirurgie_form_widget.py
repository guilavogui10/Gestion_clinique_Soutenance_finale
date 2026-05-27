"""
Widget formulaire chirurgie — pattern consultation_form_widget.
- Header avec boutons Annuler / Enregistrer en haut à droite
- Une seule carte, 2 rangées de champs, pas de scroll
- Labels sans bordure ni fond
"""
import qtawesome as qta
from PySide6.QtCore    import Qt, QDate, QSize, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QDateEdit, QFrame, QTextEdit,
)
from models.modeles_chirurgie import Chirurgie
from views.shared.message_box import CustomMessageBox
from views.shared.theme_manager import theme_manager


class ChirurgieFormWidget(QWidget):
    """
    Formulaire chirurgie — même structure que ConsultationFormWidget.
    Header en haut avec boutons, une carte section, 2 rangées, pas de scroll.
    """

    chirurgie_saved = Signal()

    def __init__(self, controleur, code_session: str,
                 code_consultation: str = "", code_personnel: str = "",
                 chirurgie_obj=None, parent=None):
        super().__init__(parent)
        self.controleur    = controleur
        self.code_session  = code_session
        self.chirurgie_obj = chirurgie_obj
        self._code_personnel_init = code_personnel

        self._init_ui()

        if chirurgie_obj:
            self._remplir_champs()
        else:
            if code_session:
                self.edit_session.setText(code_session)
            if code_personnel:
                self.edit_personnel.setText(code_personnel)

        theme_manager.theme_changed.connect(self.apply_theme)

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

        # Icône
        icon_box = QFrame()
        icon_box.setFixedSize(46, 46)
        icon_box.setStyleSheet(f"""
            background-color: {c['bg_main']};
            border-radius: 10px;
            border: 1px solid {c['border_light']};
        """)
        ib_layout = QHBoxLayout(icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        ico_lbl = QLabel()
        ico_lbl.setPixmap(
            qta.icon("fa5s.clipboard-list", color=c['primary']).pixmap(22, 22)
        )
        ico_lbl.setAlignment(Qt.AlignCenter)
        ib_layout.addWidget(ico_lbl, alignment=Qt.AlignCenter)

        # Titre + sous-titre
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        lbl_main = QLabel("Enregistrement d'une Chirurgie")
        lbl_main.setStyleSheet(
            f"font-size: 17px; font-weight: bold; color: {c['text_primary']};"
            " background: transparent; border: none;"
        )
        lbl_sub = QLabel("Veuillez remplir les informations de la chirurgie")
        lbl_sub.setStyleSheet(
            f"font-size: 12px; color: {c['text_muted']};"
            " background: transparent; border: none;"
        )
        title_col.addWidget(lbl_main)
        title_col.addWidget(lbl_sub)

        layout.addWidget(icon_box)
        layout.addLayout(title_col)
        layout.addStretch()

        # Bouton Annuler
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

        # Bouton Enregistrer
        label_save = " Enregistrer" if not self.chirurgie_obj else " Mettre à jour"
        self.btn_save = QPushButton(
            qta.icon("fa5s.save", color="#ffffff"), label_save
        )
        self.btn_save.setFixedSize(170, 40)
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
                color: #ffffff;
            }}
            QPushButton:enabled:hover {{ background-color: {c['primary_hover']}; }}
        """)

    # =========================================================================
    # HELPERS — champ badge-icône (même API que consultation)
    # =========================================================================

    def _make_field(self, label_text: str, widget, icon_name: str, icon_color: str,
                    height: int = 42, align_top: bool = False):
        """Retourne (QVBoxLayout, wrapper_QFrame)."""
        c = theme_manager.colors()
        vbox = QVBoxLayout()
        vbox.setSpacing(4)

        lbl = QLabel(label_text)
        lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {c['text_secondary']};"
            " background: transparent; border: none;"
        )
        vbox.addWidget(lbl)

        wrapper = QFrame()
        wrapper.setObjectName("inputWrapper")
        wrapper.setFixedHeight(height)
        self._apply_wrapper_style(wrapper)

        hbox = QHBoxLayout(wrapper)
        hbox.setContentsMargins(8, 5, 8, 5)
        hbox.setSpacing(8)
        v_align = Qt.AlignTop if align_top else Qt.AlignVCenter

        badge = QFrame()
        badge.setFixedSize(28, 28)
        badge.setStyleSheet(
            f"background-color: {icon_color}20; border-radius: 7px; border: none;"
        )
        bl = QHBoxLayout(badge)
        bl.setContentsMargins(0, 0, 0, 0)
        ico_lbl = QLabel()
        ico_lbl.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(14, 14))
        ico_lbl.setAlignment(Qt.AlignCenter)
        ico_lbl.setStyleSheet("border: none; background: transparent;")
        bl.addWidget(ico_lbl, alignment=Qt.AlignCenter)

        self._clear_widget_style(widget, c)
        hbox.addWidget(badge, 0, v_align)
        hbox.addWidget(widget, 1)
        vbox.addWidget(wrapper)
        return vbox, wrapper

    def _make_field_suffix(self, label_text: str, widget, icon_name: str,
                           icon_color: str, suffix: str, height: int = 42):
        """Champ avec label suffix à droite (ex: GNF)."""
        c = theme_manager.colors()
        vbox = QVBoxLayout()
        vbox.setSpacing(4)

        lbl = QLabel(label_text)
        lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {c['text_secondary']};"
            " background: transparent; border: none;"
        )
        vbox.addWidget(lbl)

        wrapper = QFrame()
        wrapper.setObjectName("inputWrapper")
        wrapper.setFixedHeight(height)
        self._apply_wrapper_style(wrapper)

        hbox = QHBoxLayout(wrapper)
        hbox.setContentsMargins(8, 5, 8, 5)
        hbox.setSpacing(8)

        badge = QFrame()
        badge.setFixedSize(28, 28)
        badge.setStyleSheet(
            f"background-color: {icon_color}20; border-radius: 7px; border: none;"
        )
        bl = QHBoxLayout(badge)
        bl.setContentsMargins(0, 0, 0, 0)
        ico_lbl = QLabel()
        ico_lbl.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(14, 14))
        ico_lbl.setAlignment(Qt.AlignCenter)
        ico_lbl.setStyleSheet("border: none; background: transparent;")
        bl.addWidget(ico_lbl, alignment=Qt.AlignCenter)

        self._clear_widget_style(widget, c)
        sfx = QLabel(suffix)
        sfx.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {c['text_secondary']};"
            " background: transparent; border: none;"
        )

        hbox.addWidget(badge, 0, Qt.AlignVCenter)
        hbox.addWidget(widget, 1)
        hbox.addWidget(sfx, 0, Qt.AlignVCenter)
        vbox.addWidget(wrapper)
        return vbox, wrapper

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
        elif isinstance(widget, QDateEdit):
            widget.setStyleSheet(f"QDateEdit {{ {base} padding: 0; }}")
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
    # SECTION INFORMATIONS — 1 carte, 2 rangées
    # =========================================================================

    def _section_infos(self, parent_layout):
        c = theme_manager.colors()
        card = QFrame()
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

        # Titre de la section
        hdr = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(
            qta.icon("fa5s.file-medical-alt", color=c['primary']).pixmap(16, 16)
        )
        ico.setStyleSheet("border: none; background: transparent;")
        lbl_t = QLabel("Informations de la chirurgie")
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

        # Code (auto, readonly)
        self.edit_code = QLineEdit()
        self.edit_code.setPlaceholderText("Entrez le code de la chirurgie")
        self.edit_code.setEnabled(False)
        vb, _ = self._make_field("Code *", self.edit_code, "fa5s.code", "#3498db")
        row1.addWidget(self._field_widget(vb), 1, Qt.AlignTop)

        # Libellé (textarea)
        self.edit_libelle = QTextEdit()
        self.edit_libelle.setPlaceholderText("Entrez le libellé de la chirurgie")
        self.edit_libelle.setFixedHeight(60)
        vb_lib, self._wrap_libelle = self._make_field(
            "Libellé de la chirurgie *", self.edit_libelle,
            "fa5s.align-left", "#6c757d", height=60
        )
        self._err_libelle = self._err_label()
        vb_lib.addWidget(self._err_libelle)
        row1.addWidget(self._field_widget(vb_lib), 2, Qt.AlignTop)

        # Frais + suffix GNF
        self.edit_frais = QLineEdit()
        self.edit_frais.setPlaceholderText("Entrez les frais de la chirurgie")
        vb_frais, self._wrap_frais = self._make_field_suffix(
            "Frais de la chirurgie *", self.edit_frais,
            "fa5s.dollar-sign", "#27ae60", "GNF"
        )
        self._err_frais = self._err_label()
        vb_frais.addWidget(self._err_frais)
        row1.addWidget(self._field_widget(vb_frais), 1, Qt.AlignTop)

        # Statut Facture
        self.combo_statut = QComboBox()
        self.combo_statut.setEnabled(False)
        self.combo_statut.addItem("Sélectionner le statut")
        vb_stat, _ = self._make_field(
            "Statut Facture", self.combo_statut,
            "fa5s.file-invoice", "#f39c12"
        )
        row1.addWidget(self._field_widget(vb_stat), 1, Qt.AlignTop)

        vbox.addLayout(row1)
        vbox.addSpacing(6)

        # ── Rangée 2 : Date | Code Session | Code Personnel | Code Acte ──
        row2 = QHBoxLayout()
        row2.setSpacing(14)

        self.edit_date = QDateEdit()
        self.edit_date.setCalendarPopup(True)
        self.edit_date.setDate(QDate.currentDate())
        self.edit_date.setDisplayFormat("dd/MM/yyyy")
        vb_date, _ = self._make_field(
            "Date de la chirurgie *", self.edit_date,
            "fa5s.calendar-alt", "#3498db"
        )
        row2.addWidget(self._field_widget(vb_date), 1, Qt.AlignTop)

        self.edit_session = QLineEdit(self.code_session or "")
        self.edit_session.setPlaceholderText("Entrez le code de la session")
        self.edit_session.setEnabled(False)
        vb_sess, _ = self._make_field(
            "Code Session *", self.edit_session,
            "fa5s.graduation-cap", "#9b59b6"
        )
        row2.addWidget(self._field_widget(vb_sess), 1, Qt.AlignTop)

        # Code Personnel (combo)
        self.combo_personnel = QComboBox()
        self.combo_personnel.addItem("-- Sélectionner le personnel --", "")
        # Charger la liste du personnel
        try:
            personnels = self.controleur.lister_personnel() or []
            for personnel in personnels:
                nom = personnel.get('nom', '') if isinstance(personnel, dict) else getattr(personnel, 'nom', '')
                prenom = personnel.get('prenom', '') if isinstance(personnel, dict) else getattr(personnel, 'prenom', '')
                fonction = personnel.get('fonction', '') if isinstance(personnel, dict) else getattr(personnel, 'fonction', '')
                code = personnel.get('code', '') if isinstance(personnel, dict) else getattr(personnel, 'code', '')
                label = f"{nom} {prenom}  |  {fonction}"
                self.combo_personnel.addItem(label, code)
            # Pré-sélectionner si code_personnel_init fourni
            if self._code_personnel_init:
                for i in range(self.combo_personnel.count()):
                    if self.combo_personnel.itemData(i) == self._code_personnel_init:
                        self.combo_personnel.setCurrentIndex(i)
                        break
        except Exception as e:
            print(f"Erreur chargement personnel: {e}")
        vb_perso, self._wrap_personnel = self._make_field(
            "Personnel *", self.combo_personnel,
            "fa5s.user-md", "#1abc9c"
        )
        self._err_personnel = self._err_label()
        vb_perso.addWidget(self._err_personnel)
        row2.addWidget(self._field_widget(vb_perso), 1, Qt.AlignTop)

        self.edit_acte = QLineEdit()
        self.edit_acte.setPlaceholderText("Entrez le code de l'acte")
        vb_acte, self._wrap_acte = self._make_field(
            "Code Acte *", self.edit_acte,
            "fa5s.file-medical", "#e74c3c"
        )
        self._err_acte = self._err_label()
        vb_acte.addWidget(self._err_acte)
        row2.addWidget(self._field_widget(vb_acte), 1, Qt.AlignTop)

        vbox.addLayout(row2)
        vbox.addSpacing(6)

        # ── Rangée 3 : Compte Rendu Opératoire ──
        row3 = QHBoxLayout()
        row3.setSpacing(14)

        self.edit_compte_rendu = QTextEdit()
        self.edit_compte_rendu.setPlaceholderText("Entrez le compte rendu opératoire")
        self.edit_compte_rendu.setFixedHeight(60)
        vb_cr, _ = self._make_field(
            "Compte Rendu Opératoire", self.edit_compte_rendu,
            "fa5s.notes-medical", "#8e44ad", height=60
        )
        row3.addWidget(self._field_widget(vb_cr), 1, Qt.AlignTop)

        vbox.addLayout(row3)

        parent_layout.addWidget(card)

        # Connexion des validations
        self.edit_libelle.textChanged.connect(self._valider_formulaire)
        self.edit_frais.textChanged.connect(self._valider_formulaire)
        self.combo_personnel.currentIndexChanged.connect(self._valider_formulaire)
        self.edit_acte.textChanged.connect(self._valider_formulaire)

    # =========================================================================
    # SECTION INFO BAS
    # =========================================================================

    def _section_info_bas(self, parent_layout):
        c = theme_manager.colors()
        card = QFrame()
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

        ico_frame = QFrame()
        ico_frame.setFixedSize(36, 36)
        ico_frame.setStyleSheet(
            f"background-color: {c['primary']}; border-radius: 18px;"
        )
        ifi = QHBoxLayout(ico_frame)
        ifi.setContentsMargins(0, 0, 0, 0)
        il = QLabel()
        il.setPixmap(qta.icon("fa5s.info", color="#ffffff").pixmap(14, 14))
        il.setAlignment(Qt.AlignCenter)
        ifi.addWidget(il, alignment=Qt.AlignCenter)

        txt = QVBoxLayout()
        txt.setSpacing(2)
        t1 = QLabel("Informations")
        t1.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {c['primary']};"
            " background: transparent;"
        )
        t2 = QLabel(
            "Veuillez remplir tous les champs obligatoires avant d'enregistrer la chirurgie."
        )
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

    def _valider_formulaire(self):
        tout_valide = True

        lib = self.edit_libelle.toPlainText().strip()
        if not lib:
            self._apply_wrapper_style(self._wrap_libelle, theme_manager.colors()['border'])
            self._err_libelle.setVisible(False)
            tout_valide = False
        else:
            self._apply_wrapper_style(
                self._wrap_libelle, theme_manager.colors()['border_focus']
            )
            self._err_libelle.setVisible(False)

        frais = self.edit_frais.text().strip()
        if not frais:
            self._apply_wrapper_style(self._wrap_frais, theme_manager.colors()['border'])
            self._err_frais.setVisible(False)
            tout_valide = False
        else:
            try:
                float(frais)
                self._apply_wrapper_style(
                    self._wrap_frais, theme_manager.colors()['border_focus']
                )
                self._err_frais.setVisible(False)
            except ValueError:
                self._apply_wrapper_style(
                    self._wrap_frais, theme_manager.colors()['danger']
                )
                self._err_frais.setText("Montant invalide")
                self._err_frais.setVisible(True)
                tout_valide = False

        if not self.combo_personnel.currentData():
            tout_valide = False

        if not self.edit_acte.text().strip():
            tout_valide = False

        # Statut auto
        self.combo_statut.clear()
        self.combo_statut.addItem(
            "attente payement" if tout_valide else "Sélectionner le statut"
        )

        self.btn_save.setEnabled(tout_valide)
        self._apply_save_btn_style()

    # =========================================================================
    # ACTIONS
    # =========================================================================

    def _on_cancel(self):
        self.edit_libelle.clear()
        self.edit_frais.clear()
        self.combo_personnel.setCurrentIndex(0)
        self.edit_acte.clear()
        self.edit_compte_rendu.clear()
        self.edit_date.setDate(QDate.currentDate())
        self.combo_statut.clear()
        self.combo_statut.addItem("Sélectionner le statut")
        self.chirurgie_obj = None
        self.btn_save.setEnabled(False)
        self._apply_save_btn_style()

    def _soumettre(self):
        try:
            libelle   = self.edit_libelle.toPlainText().strip()
            frais_str = self.edit_frais.text().strip()
            personnel = self.combo_personnel.currentData()
            acte      = self.edit_acte.text().strip()
            statut    = self.combo_statut.currentText()
            compte_rendu = self.edit_compte_rendu.toPlainText().strip()
            date_py   = self.edit_date.date().toPython()
            from datetime import datetime
            date_dt = datetime(date_py.year, date_py.month, date_py.day)

            chirurgie = Chirurgie(
                code              = self.chirurgie_obj.code if self.chirurgie_obj else None,
                libelle_chururgie = libelle,
                frais_chururgie   = float(frais_str),
                statut_facture    = statut,
                date_chururgie    = date_dt,
                code_session      = self.code_session or self.edit_session.text().strip(),
                code_personnel    = personnel,
                code_acte         = acte,
                compte_rendu_operatoire = compte_rendu or "",
            )

            if self.chirurgie_obj:
                ok, msg = self.controleur.modifier_chururgie(chirurgie)
            else:
                ok, msg = self.controleur.creer_chururgie(chirurgie)

            if ok:
                CustomMessageBox("Succès", msg, True, self).exec()
                self._on_cancel()
                self.chirurgie_saved.emit()
            else:
                CustomMessageBox("Erreur", msg, False, self).exec()

        except Exception as e:
            CustomMessageBox("Erreur Système", str(e), False, self).exec()

    # =========================================================================
    # PRÉ-REMPLISSAGE (mode modification)
    # =========================================================================

    def _remplir_champs(self):
        ch = self.chirurgie_obj
        if ch.code:
            self.edit_code.setText(str(ch.code))
        self.edit_libelle.setPlainText(ch.libelle_chururgie or "")
        self.edit_frais.setText(str(ch.frais_chururgie or ""))
        # Pré-sélectionner le personnel dans le combo
        if ch.code_personnel:
            for i in range(self.combo_personnel.count()):
                if self.combo_personnel.itemData(i) == ch.code_personnel:
                    self.combo_personnel.setCurrentIndex(i)
                    break
        self.edit_acte.setText(ch.code_acte or "")
        self.edit_compte_rendu.setPlainText(ch.compte_rendu_operatoire or "")
        if ch.statut_facture:
            self.combo_statut.clear()
            self.combo_statut.addItem(ch.statut_facture)
        if ch.date_chururgie and hasattr(ch.date_chururgie, 'year'):
            d = ch.date_chururgie
            self.edit_date.setDate(QDate(d.year, d.month, d.day))

    def recharger_pour_patient(self, code_consultation: str, code_session: str, code_acte: str = ""):
        """Appelé depuis l'onglet patients en attente."""
        self.code_session = code_session
        self.edit_session.setText(code_session or "")
        self._on_cancel()
        if code_acte:
            self.edit_acte.setText(code_acte)

    # =========================================================================
    # THÈME
    # =========================================================================

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"QWidget {{ background: {c['bg_main']}; }}")
        self.header_frame.setStyleSheet(f"""
            background-color: {c['bg_card']};
            border-radius: 14px;
            border: none;
        """)
        self._apply_save_btn_style()
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
