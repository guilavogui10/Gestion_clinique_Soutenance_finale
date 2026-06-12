"""
export_import_personnel.py
------------------------
Module autonome gérant l'export et l'import du personnel avec aperçu visuel.

Contient :
  - ApercuPersonnelModal : modal d'aperçu des données avant export ou import
  - Fonctions statiques ouvrir_export() et ouvrir_import() appelées depuis la vue
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import qtawesome as qta

from views.shared.theme_manager import theme_manager
from views.shared.message_box import CustomMessageBox


class ApercuPersonnelModal(QDialog):
    """
    Modal d'aperçu des données personnel avant export ou import.
    - Export : affiche le personnel existant, puis demande où sauvegarder.
    - Import : affiche le contenu du fichier choisi, puis lance l'import.
    """

    COLONNES_EXPORT = [
        "Code", "Nom", "Prénom", "Fonction", "Contact", "Email", "Adresse"
    ]

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

    # ------------------------------------------------------------------
    # Construction UI
    # ------------------------------------------------------------------

    def _build_ui(self, titre, sous_titre, colonnes, donnees):
        c = theme_manager.colors()
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(14)

        # --- En-tête ---
        lbl_titre = QLabel(titre)
        font_titre = QFont()
        font_titre.setPointSize(15)
        font_titre.setBold(True)
        lbl_titre.setFont(font_titre)
        lbl_titre.setStyleSheet(f"color: {c['primary']};")
        root.addWidget(lbl_titre)

        lbl_sous = QLabel(sous_titre)
        lbl_sous.setStyleSheet(f"color: {c['text_muted']}; font-size: 12px;")
        root.addWidget(lbl_sous)

        # --- Séparateur ---
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {c['border']};")
        root.addWidget(sep)

        # --- Tableau ---
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

        # --- Barre de boutons ---
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
        """Contraint le modal à 90 % de l'écran disponible et le centre."""
        from PySide6.QtWidgets import QApplication
        ecran = QApplication.primaryScreen().availableGeometry()
        max_w = int(ecran.width()  * 0.90)
        max_h = int(ecran.height() * 0.88)
        self.setMinimumSize(min(820, max_w), min(400, max_h))
        self.resize(min(900, max_w), min(560, max_h))
        self.move(
            ecran.x() + (ecran.width()  - self.width())  // 2,
            ecran.y() + (ecran.height() - self.height()) // 2
        )

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------

    def _apply_styles(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"background: {c['bg_card']}; color: {c['text_primary']};")

        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                gridline-color: {c.get('border_light', c['border'])};
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
                background: {c.get('primary_light', c['bg_main'])};
                color: {c['primary']};
            }}
        """)

        self.btn_annuler.setStyleSheet(f"""
            QPushButton {{
                background: {c['bg_card']}; color: {c['text_primary']};
                border: 1px solid {c['border']}; border-radius: 8px;
                font-weight: 600; padding: 0 20px; font-size: 13px;
            }}
            QPushButton:hover {{ background: {c['hover']}; border-color: {c['primary']}; }}
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
    def ouvrir_export(parent, controleur, format_fichier: str):
        """
        1. Charge les données via le contrôleur
        2. Affiche l'aperçu
        3. Si confirmé → file dialog pour sauvegarder → export
        """
        donnees_dicts = controleur.get_all_personnels()

        if not donnees_dicts:
            CustomMessageBox(
                "Export", "Aucun personnel à exporter.",
                msg_type="info", parent=parent
            ).exec()
            return

        colonnes = ApercuPersonnelModal.COLONNES_EXPORT
        donnees = [
            [
                d.get("code", ""), d.get("nom", ""), d.get("prenom", ""), d.get("fonction", ""),
                d.get("contact", ""), d.get("mail", ""), d.get("adresse", "")
            ]
            for d in donnees_dicts
        ]

        ext   = "xlsx" if format_fichier == "excel" else "csv"
        titre = f"Aperçu export {ext.upper()} — Personnel"
        sous  = f"{len(donnees)} personnel(s) prêt(s) à exporter"

        modal = ApercuPersonnelModal(parent, titre, sous, colonnes, donnees, mode="export")
        if not (modal.exec() and modal._confirme):
            return

        filtre = "Excel Files (*.xlsx)" if format_fichier == "excel" else "CSV Files (*.csv)"
        chemin, _ = QFileDialog.getSaveFileName(
            parent, f"Enregistrer — {ext.upper()}", f"personnel_export.{ext}", filtre
        )
        if not chemin:
            return

        if format_fichier == "excel":
            ok, msg = controleur.export_to_excel(chemin)
        else:
            ok, msg = controleur.export_to_csv(chemin)

        CustomMessageBox(
            "Export réussi" if ok else "Erreur export",
            msg,
            is_success=ok,
            parent=parent
        ).exec()

    @staticmethod
    def ouvrir_import(parent, controleur, format_fichier: str):
        """
        1. File dialog pour choisir le fichier
        2. Lit le fichier et affiche l'aperçu
        3. Si confirmé → import avec validation complète
        4. Rafraîchit la vue parente
        """
        ext    = "xlsx" if format_fichier == "excel" else "csv"
        filtre = "Excel Files (*.xlsx)" if format_fichier == "excel" else "CSV Files (*.csv)"

        chemin, _ = QFileDialog.getOpenFileName(
            parent, f"Sélectionner le fichier {ext.upper()}", "", filtre
        )
        if not chemin:
            return

        # Lecture du fichier pour l'aperçu
        try:
            import pandas as pd
            df = pd.read_excel(chemin) if format_fichier == "excel" \
                 else pd.read_csv(chemin, encoding="utf-8-sig")

            if df.empty:
                CustomMessageBox(
                    "Import", "Le fichier ne contient aucune donnée.",
                    is_success=False, parent=parent
                ).exec()
                return

            colonnes = list(df.columns)
            donnees  = [list(row) for _, row in df.iterrows()]

        except Exception as e:
            CustomMessageBox(
                "Erreur de lecture",
                f"Impossible de lire le fichier :\n{e}",
                is_success=False, parent=parent
            ).exec()
            return

        titre = f"Aperçu import {ext.upper()} — Personnel"
        sous  = f"{len(donnees)} ligne(s) détectée(s) dans le fichier"

        modal = ApercuPersonnelModal(parent, titre, sous, colonnes, donnees, mode="import")
        if not (modal.exec() and modal._confirme):
            return

        # Lancer l'import
        if format_fichier == "excel":
            ok, msg = controleur.import_from_excel(chemin)
        else:
            ok, msg = controleur.import_from_csv(chemin)

        CustomMessageBox(
            "Import réussi" if ok else "Import — résultat",
            msg,
            is_success=ok,
            parent=parent
        ).exec()

        # Rafraîchir le tableau
        try:
            if hasattr(parent, 'charger_donnees'):
                parent.charger_donnees()
        except Exception:
            pass
