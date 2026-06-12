"""
export_import_acte.py
----------------------
Module autonome gérant l'export et l'import des 4 types d'actes médicaux.

Contient :
  - ExportImportActeMenu  : menu popup (vers le haut) depuis le bouton "Exporter"
  - ApercuActeModal       : aperçu des données avant export ou import
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QFrame
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont
import qtawesome as qta

from views.shared.theme_manager import theme_manager
from views.shared.message_box import CustomMessageBox
from service_metier.acte_import_export_service import COLONNES_EXPORT


# ============================================================================
# MENU POPUP
# ============================================================================

_TYPES = {
    "examen":       ("Examens",       "#0070c0"),
    "chirurgie":    ("Chirurgies",    "#7b2cbf"),
    "lunette":      ("Lunettes",      "#217346"),
    "prescription": ("Prescriptions", "#e67e22"),
}


class ExportImportActeMenu:
    """
    Menu popup vers le haut depuis le bouton "Exporter".
    Structure : Export (4 types) / Import (4 types).
    """

    @staticmethod
    def afficher(parent_widget, bouton, controleur):
        from PySide6.QtWidgets import QMenu
        c = theme_manager.colors()

        menu = QMenu(parent_widget)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 6px 4px;
            }}
            QMenu::item {{
                padding: 8px 20px 8px 12px;
                border-radius: 6px;
                font-size: 13px;
                color: {c['text_primary']};
                min-width: 240px;
            }}
            QMenu::item:selected {{
                background: {c.get('primary_light', '#e8f0fe')};
                color: {c['primary']};
            }}
            QMenu::separator {{
                height: 1px;
                background: {c['border']};
                margin: 4px 10px;
            }}
        """)

        # ── Export ──
        export_menu = menu.addMenu(
            qta.icon("fa5s.download", color=c['success']), "  Exporter"
        )
        for type_acte, (label, color) in _TYPES.items():
            sub = export_menu.addMenu(
                qta.icon("fa5s.folder-open", color=color), f"  {label}"
            )
            act_xl = sub.addAction(
                qta.icon("fa5s.file-excel", color="#217346"), "  Excel (.xlsx)"
            )
            act_cs = sub.addAction(
                qta.icon("fa5s.file-csv",   color="#0070c0"), "  CSV (.csv)"
            )
            act_xl.triggered.connect(
                lambda checked=False, t=type_acte: ApercuActeModal.ouvrir_export(
                    parent_widget, controleur, t, "excel"
                )
            )
            act_cs.triggered.connect(
                lambda checked=False, t=type_acte: ApercuActeModal.ouvrir_export(
                    parent_widget, controleur, t, "csv"
                )
            )

        menu.addSeparator()

        # ── Import ──
        import_menu = menu.addMenu(
            qta.icon("fa5s.upload", color=c['primary']), "  Importer"
        )
        for type_acte, (label, color) in _TYPES.items():
            sub = import_menu.addMenu(
                qta.icon("fa5s.folder-open", color=color), f"  {label}"
            )
            act_xl = sub.addAction(
                qta.icon("fa5s.file-excel", color="#217346"), "  Depuis Excel (.xlsx)"
            )
            act_cs = sub.addAction(
                qta.icon("fa5s.file-csv",   color="#0070c0"), "  Depuis CSV (.csv)"
            )
            act_xl.triggered.connect(
                lambda checked=False, t=type_acte: ApercuActeModal.ouvrir_import(
                    parent_widget, controleur, t, "excel"
                )
            )
            act_cs.triggered.connect(
                lambda checked=False, t=type_acte: ApercuActeModal.ouvrir_import(
                    parent_widget, controleur, t, "csv"
                )
            )

        # Positionner au-dessus du bouton
        menu.adjustSize()
        menu_h = menu.sizeHint().height()
        pos_global = bouton.mapToGlobal(QPoint(0, 0))
        target = QPoint(pos_global.x(), pos_global.y() - menu_h - 6)
        menu.exec(target)


# ============================================================================
# MODAL APERÇU
# ============================================================================

class ApercuActeModal(QDialog):
    """
    Modal d'aperçu des données actes médicaux avant export ou import.
    Fond blanc, titre bleu, adapté à l'écran.
    """

    def __init__(self, parent, titre, sous_titre, colonnes, donnees, mode):
        super().__init__(parent)
        self.mode = mode
        self._confirme = False

        self.setWindowTitle(titre)
        self.setModal(True)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self._build_ui(titre, sous_titre, colonnes, donnees)
        self._apply_styles()
        self._ajuster_taille_ecran()
        theme_manager.theme_changed.connect(self._apply_styles)

    def _build_ui(self, titre, sous_titre, colonnes, donnees):
        c = theme_manager.colors()
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(14)

        lbl_titre = QLabel(titre)
        font = QFont()
        font.setPointSize(15)
        font.setBold(True)
        lbl_titre.setFont(font)
        lbl_titre.setStyleSheet(f"color: {c['primary']};")
        root.addWidget(lbl_titre)

        lbl_sous = QLabel(sous_titre)
        lbl_sous.setStyleSheet(f"color: {c['text_muted']}; font-size: 12px;")
        root.addWidget(lbl_sous)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {c['border']};")
        root.addWidget(sep)

        self.table = QTableWidget(len(donnees), len(colonnes))
        self.table.setHorizontalHeaderLabels(colonnes)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSortingEnabled(False)

        for r, row_data in enumerate(donnees):
            for col, cell in enumerate(row_data):
                item = QTableWidgetItem(str(cell) if cell is not None else "")
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, col, item)

        self.table.setSortingEnabled(True)
        root.addWidget(self.table)

        bar = QHBoxLayout()
        bar.setSpacing(10)
        bar.addStretch()

        self.btn_annuler = QPushButton("  Annuler")
        self.btn_annuler.setIcon(qta.icon("fa5s.times", color=c['text_secondary']))
        self.btn_annuler.setFixedHeight(40)
        self.btn_annuler.setCursor(Qt.PointingHandCursor)
        self.btn_annuler.clicked.connect(self.reject)

        label_ok = "  Exporter" if self.mode == "export" else "  Importer"
        icon_ok  = "fa5s.download" if self.mode == "export" else "fa5s.upload"
        self.btn_ok = QPushButton(label_ok)
        self.btn_ok.setIcon(qta.icon(icon_ok, color=c['text_inverse']))
        self.btn_ok.setFixedHeight(40)
        self.btn_ok.setCursor(Qt.PointingHandCursor)
        self.btn_ok.clicked.connect(self._on_ok)

        bar.addWidget(self.btn_annuler)
        bar.addWidget(self.btn_ok)
        root.addLayout(bar)

    def _on_ok(self):
        self._confirme = True
        self.accept()

    def _ajuster_taille_ecran(self):
        from PySide6.QtWidgets import QApplication
        ecran = QApplication.primaryScreen().availableGeometry()
        max_w = int(ecran.width()  * 0.92)
        max_h = int(ecran.height() * 0.88)
        self.setMinimumSize(min(860, max_w), min(420, max_h))
        self.resize(min(960, max_w), min(580, max_h))
        self.move(
            ecran.x() + (ecran.width()  - self.width())  // 2,
            ecran.y() + (ecran.height() - self.height()) // 2
        )

    def _apply_styles(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"background: {c['bg_card']};")
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                gridline-color: {c.get('border_light', '#e0e0e0')};
                font-size: 12px;
            }}
            QHeaderView::section {{
                background: {c.get('table_header_bg', c['bg_card'])};
                color: {c['text_primary']};
                padding: 8px 6px;
                border: none;
                font-weight: 600;
                font-size: 12px;
            }}
            QTableWidget::item {{ padding: 6px 8px; }}
            QTableWidget::item:alternate {{ background: {c['bg_main']}; }}
            QTableWidget::item:selected {{
                background: {c.get('primary_light', '#e8f0fe')};
                color: {c['primary']};
            }}
        """)
        self.btn_annuler.setStyleSheet(f"""
            QPushButton {{
                background: {c['bg_card']}; color: {c['text_primary']};
                border: 1px solid {c['border']}; border-radius: 8px;
                font-weight: 600; padding: 0 20px; font-size: 13px;
            }}
            QPushButton:hover {{ background: {c['border']}; }}
        """)
        self.btn_ok.setStyleSheet(f"""
            QPushButton {{
                background: {c['primary']}; color: {c['text_inverse']};
                border: none; border-radius: 8px;
                font-weight: 600; padding: 0 28px; font-size: 13px;
            }}
            QPushButton:hover {{ background: {c['primary_hover']}; }}
        """)

    # ------------------------------------------------------------------
    # Méthodes statiques d'ouverture
    # ------------------------------------------------------------------

    @staticmethod
    def _appeler_export(controleur, type_acte: str, format_fichier: str, chemin: str):
        """
        Appelle la bonne méthode d'export selon le contrôleur reçu.
        Compatible avec ActeMedicalControleur ET les contrôleurs spécifiques.
        """
        # Contrôleurs spécifiques ont export_to_excel / export_to_csv
        if hasattr(controleur, 'export_to_excel') and format_fichier == "excel":
            return controleur.export_to_excel(chemin)
        if hasattr(controleur, 'export_to_csv') and format_fichier == "csv":
            return controleur.export_to_csv(chemin)
        # ActeMedicalControleur a des méthodes nommées par type
        fn_map = {
            ("examen",       "excel"): getattr(controleur, 'export_examens_excel',    None),
            ("examen",       "csv"):   getattr(controleur, 'export_examens_csv',      None),
            ("chirurgie",    "excel"): getattr(controleur, 'export_chirurgies_excel', None),
            ("chirurgie",    "csv"):   getattr(controleur, 'export_chirurgies_csv',   None),
            ("lunette",      "excel"): getattr(controleur, 'export_lunettes_excel',   None),
            ("lunette",      "csv"):   getattr(controleur, 'export_lunettes_csv',     None),
            ("prescription", "excel"): getattr(controleur, 'export_prescriptions_excel', None),
            ("prescription", "csv"):   getattr(controleur, 'export_prescriptions_csv',   None),
        }
        fn = fn_map.get((type_acte, format_fichier))
        return fn(chemin) if fn else (False, "Méthode d'export introuvable")

    @staticmethod
    def ouvrir_export(parent, controleur, type_acte: str, format_fichier: str):
        label = _TYPES[type_acte][0]

        # Compatible : contrôleurs spécifiques (sans arg) et ActeMedicalControleur (avec arg)
        try:
            donnees_dicts = controleur.obtenir_donnees_export()
        except TypeError:
            donnees_dicts = controleur.obtenir_donnees_export(type_acte)

        if not donnees_dicts:
            CustomMessageBox(f"Export {label}",
                             f"Aucun(e) {label.lower()} à exporter.",
                             msg_type="info", parent=parent).exec()
            return

        colonnes = COLONNES_EXPORT[type_acte]
        donnees = [[str(d.get(col, "")) for col in colonnes] for d in donnees_dicts]

        ext   = "xlsx" if format_fichier == "excel" else "csv"
        titre = f"Aperçu export {ext.upper()} — {label}"
        sous  = f"{len(donnees)} enregistrement(s) prêt(s) à exporter"

        modal = ApercuActeModal(parent, titre, sous, colonnes, donnees, mode="export")
        if not (modal.exec() and modal._confirme):
            return

        filtre = "Excel Files (*.xlsx)" if format_fichier == "excel" else "CSV Files (*.csv)"
        chemin, _ = QFileDialog.getSaveFileName(
            parent, f"Enregistrer — {ext.upper()}",
            f"{type_acte}s_export.{ext}", filtre
        )
        if not chemin:
            return

        ok, msg = ApercuActeModal._appeler_export(controleur, type_acte, format_fichier, chemin)
        CustomMessageBox(
            f"Export {label} réussi" if ok else f"Erreur export {label}",
            msg, msg_type="success" if ok else "error", parent=parent
        ).exec()

    @staticmethod
    def ouvrir_import(parent, controleur, type_acte: str, format_fichier: str):
        label = _TYPES[type_acte][0]
        ext    = "xlsx" if format_fichier == "excel" else "csv"
        filtre = "Excel Files (*.xlsx)" if format_fichier == "excel" else "CSV Files (*.csv)"

        chemin, _ = QFileDialog.getOpenFileName(
            parent, f"Sélectionner le fichier {ext.upper()} — {label}", "", filtre
        )
        if not chemin:
            return

        try:
            import pandas as pd
            df = pd.read_excel(chemin) if format_fichier == "excel" \
                 else pd.read_csv(chemin, encoding="utf-8-sig")
            if df.empty:
                CustomMessageBox("Import", "Le fichier ne contient aucune donnée.",
                                 msg_type="warning", parent=parent).exec()
                return
            colonnes = list(df.columns)
            donnees  = [list(row) for _, row in df.iterrows()]
        except Exception as e:
            CustomMessageBox("Erreur de lecture", f"Impossible de lire le fichier :\n{e}",
                             msg_type="error", parent=parent).exec()
            return

        titre = f"Aperçu import {ext.upper()} — {label}"
        sous  = f"{len(donnees)} ligne(s) détectée(s) dans le fichier"

        modal = ApercuActeModal(parent, titre, sous, colonnes, donnees, mode="import")
        if not (modal.exec() and modal._confirme):
            return

        # Tous les contrôleurs (spécifiques et ActeMedical) ont la méthode nommée par type
        fn = getattr(controleur, f"import_{type_acte}s", None)
        if fn is None:
            CustomMessageBox("Erreur", f"Méthode import_{type_acte}s introuvable.",
                             msg_type="error", parent=parent).exec()
            return
        ok, msg = fn(chemin, format_fichier)
        CustomMessageBox(
            f"Import {label} réussi" if ok else f"Import {label} — résultat",
            msg, msg_type="success" if ok else "warning", parent=parent
        ).exec()

        try:
            parent.load_data()
        except Exception:
            pass
