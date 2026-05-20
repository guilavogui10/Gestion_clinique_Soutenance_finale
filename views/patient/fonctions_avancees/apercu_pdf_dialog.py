"""
Dialogue d'aperçu PDF pour l'historique patient
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                                QLabel, QFrame, QFileDialog)
from PySide6.QtCore import Qt
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
import qtawesome as qta
from views.shared.theme_manager import theme_manager
from views.shared.message_box import CustomMessageBox
import tempfile
import os


class ApercuPDFDialog(QDialog):
    """Dialogue modal pour afficher l'aperçu d'un PDF avec bouton d'impression"""
    
    def __init__(self, pdf_path, titre="Aperçu du document", parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.setWindowTitle(titre)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._init_ui()
        self._load_pdf()
        
        # Centrer et dimensionner comme resultat_medical
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.setMinimumHeight(int(screen.height() * 0.75))
        self.setMaximumHeight(int(screen.height() * 0.95))
        self.setFixedWidth(min(900, int(screen.width() * 0.95)))
        self.adjustSize()
        self.move(
            screen.x() + (screen.width() - self.width()) // 2,
            screen.y() + (screen.height() - self.height()) // 2,
        )
    
    def _init_ui(self):
        """Initialise l'interface"""
        c = theme_manager.colors()
        
        # Layout principal avec marges pour l'ombre
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(16, 16, 16, 16)
        outer_layout.setSpacing(0)
        
        # Carte principale
        card = QFrame()
        card.setObjectName("ModalCard")
        card.setStyleSheet(f"""
            QFrame#ModalCard {{
                background: white;
                border-radius: 18px;
                border: 1px solid {c['border']};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 14, 20, 12)
        layout.setSpacing(8)
        
        outer_layout.addWidget(card)
        
        # En-tête
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Badge icône
        badge_hdr = QFrame()
        badge_hdr.setFixedSize(34, 34)
        badge_hdr.setStyleSheet(f"background: {c['danger']}18; border-radius: 9px; border: none;")
        badge_layout = QHBoxLayout(badge_hdr)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon("fa5s.file-pdf", color=c['danger']).pixmap(16, 16))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("border: none; background: transparent;")
        badge_layout.addWidget(icon_label, alignment=Qt.AlignCenter)
        
        # Titre
        titre_col = QVBoxLayout()
        titre_col.setSpacing(1)
        title_label = QLabel("Aperçu du document")
        title_label.setObjectName("TitleLabel")
        title_label.setStyleSheet(f"font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px; font-weight: 700; color: #111827; border: none; background: transparent;")
        titre_col.addWidget(title_label)
        
        # Bouton fermer
        close_btn = QPushButton()
        close_btn.setIcon(qta.icon("fa5s.times", color="#9CA3AF"))
        close_btn.setFixedSize(26, 26)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(
            "QPushButton { border: none; background: transparent; border-radius: 6px; }"
            "QPushButton:hover { background: #F3F4F6; }"
        )
        close_btn.clicked.connect(self.reject)
        
        header_layout.addWidget(badge_hdr)
        header_layout.addLayout(titre_col)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Séparateur
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {c['border_light']};")
        layout.addWidget(sep)
        
        # Visionneuse PDF
        self.pdf_view = QPdfView()
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
        layout.addWidget(self.pdf_view, 1)
        
        # Séparateur
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"color: {c['border_light']};")
        layout.addWidget(sep2)
        
        # Footer avec boutons
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(8)
        footer_layout.addStretch()
        
        # Bouton Imprimer
        btn_imprimer = QPushButton("  Imprimer")
        btn_imprimer.setIcon(qta.icon("fa5s.print", color="white"))
        btn_imprimer.setFixedHeight(32)
        btn_imprimer.setMinimumWidth(105)
        btn_imprimer.setCursor(Qt.PointingHandCursor)
        btn_imprimer.setStyleSheet(f"""
            QPushButton {{
                background: #059669;
                color: white;
                border: none;
                border-radius: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
                font-weight: 600;
                padding: 0 14px;
            }}
            QPushButton:hover {{
                background: #047857;
            }}
        """)
        btn_imprimer.clicked.connect(self._imprimer)
        
        # Bouton Fermer
        btn_fermer = QPushButton("  Fermer")
        btn_fermer.setIcon(qta.icon("fa5s.times", color="#6B7280"))
        btn_fermer.setFixedHeight(32)
        btn_fermer.setMinimumWidth(88)
        btn_fermer.setCursor(Qt.PointingHandCursor)
        btn_fermer.setStyleSheet(f"""
            QPushButton {{
                background: #F9FAFB;
                color: #374151;
                border: 1.5px solid {c['border']};
                border-radius: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
                font-weight: 600;
                padding: 0 14px;
            }}
            QPushButton:hover {{
                background: #F3F4F6;
            }}
        """)
        btn_fermer.clicked.connect(self.reject)
        
        footer_layout.addWidget(btn_imprimer)
        footer_layout.addWidget(btn_fermer)
        
        layout.addLayout(footer_layout)
    
    def _load_pdf(self):
        """Charge le PDF dans la visionneuse"""
        try:
            self.pdf_document = QPdfDocument(self)
            self.pdf_document.load(self.pdf_path)
            self.pdf_view.setDocument(self.pdf_document)
        except Exception as e:
            CustomMessageBox(
                "Erreur",
                f"Impossible de charger le PDF:\n{str(e)}",
                is_success=False,
                parent=self
            ).exec()
    
    def _imprimer(self):
        """Demande où sauvegarder le PDF"""
        chemin, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le PDF",
            os.path.expanduser("~/Documents/consultation.pdf"),
            "Fichiers PDF (*.pdf)"
        )
        
        if chemin:
            try:
                # Copier le fichier temporaire vers le chemin choisi
                import shutil
                shutil.copy2(self.pdf_path, chemin)
                
                CustomMessageBox(
                    "Succès",
                    f"Le document a été enregistré avec succès:\n{chemin}",
                    is_success=True,
                    parent=self
                ).exec()
                
                self.accept()
            except Exception as e:
                CustomMessageBox(
                    "Erreur",
                    f"Erreur lors de l'enregistrement:\n{str(e)}",
                    is_success=False,
                    parent=self
                ).exec()

