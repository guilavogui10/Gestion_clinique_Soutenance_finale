"""
Widget Popover pour afficher les factures des visites d'un patient
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QScrollArea, QWidget, QFrame,
                               QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
import qtawesome as qta
from views.shared.theme_manager import theme_manager

class FacturesVisitesPopover(QDialog):
    """Dialogue style popover pour lister les visites et imprimer leurs factures"""
    
    def __init__(self, patient, controleur_historique, parent=None):
        super().__init__(parent)
        self.patient = patient
        self.controleur = controleur_historique
        
        # Style frameless comme un menu
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._init_ui()
        self.charger_visites()
        
    def _init_ui(self):
        c = theme_manager.colors()
        
        # Layout principal transparent
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Container principal stylé
        self.container = QFrame()
        self.container.setObjectName("PopoverContainer")
        self.container.setStyleSheet(f"""
            QFrame#PopoverContainer {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 8px;
            }}
        """)
        
        # Ajouter une ombre
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # En-tête
        header = QWidget()
        header.setStyleSheet(f"background-color: {c['primary_light']}; border-top-left-radius: 8px; border-top-right-radius: 8px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 12, 15, 12)
        
        lbl_titre = QLabel(f"Factures des visites - {self.patient.get_nom()} {self.patient.get_prenom()}")
        lbl_titre.setStyleSheet(f"color: {c['primary']}; font-weight: bold; font-size: 13px;")
        header_layout.addWidget(lbl_titre)
        
        container_layout.addWidget(header)
        
        # Zone de défilement
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        scroll.setWidget(self.content_widget)
        container_layout.addWidget(scroll)
        
        main_layout.addWidget(self.container)
        
        # Taille fixe / max
        self.setFixedWidth(450)
        self.setMaximumHeight(400)
        
    def charger_visites(self):
        code_patient = self.patient.get_code_patient()
        visites = self.controleur.lister_visites_patient(code_patient)
        
        c = theme_manager.colors()
        
        if not visites:
            lbl_vide = QLabel("Aucune visite trouvée pour ce patient.")
            lbl_vide.setAlignment(Qt.AlignCenter)
            lbl_vide.setStyleSheet(f"color: {c['text_secondary']}; padding: 20px;")
            self.content_layout.addWidget(lbl_vide)
            return
            
        for visite in visites:
            code_visite = visite.get('code_visite', '')
            date_visite = visite.get('date_visite', '')
            if hasattr(date_visite, 'strftime'):
                date_visite = date_visite.strftime('%d/%m/%Y')
                
            # Récupérer la facture pour cette visite
            facture = self.controleur.get_facture_par_visite(code_visite)
            
            row_widget = QWidget()
            row_widget.setStyleSheet(f"""
                QWidget {{
                    border-bottom: 1px solid {c['border_light']};
                }}
                QWidget:hover {{
                    background-color: {c['bg_main']};
                }}
            """)
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(15, 10, 15, 10)
            
            # Infos visite
            lbl_info = QLabel(f"<b>{date_visite}</b> - {code_visite}")
            lbl_info.setStyleSheet(f"color: {c['text_primary']}; border: none; background: transparent;")
            row_layout.addWidget(lbl_info, 1)
            
            # Statut facture
            statut = "Aucune"
            color_statut = c['text_secondary']
            code_facture = None
            
            if facture:
                # Récupération du statut et code facture
                if isinstance(facture, dict):
                    statut_val = facture.get('statut_facture', '')
                    code_facture = facture.get('code_facture')
                else:
                    statut_val = facture.get_statut_facture() if hasattr(facture, 'get_statut_facture') else getattr(facture, 'statut_facture', '')
                    code_facture = facture.get_code_facture() if hasattr(facture, 'get_code_facture') else getattr(facture, 'code_facture', None)
                
                # Normalisation et vérification du statut
                statut_normalise = (statut_val or '').strip().lower()
                
                # Liste complète des statuts "terminé"
                statuts_termines = [
                    'payée', 'payee', 'payé', 'paye',
                    'terminée', 'terminee', 'terminé', 'termine',
                    'terminer', 'complète', 'complete', 'validée', 'validee'
                ]
                
                if statut_normalise in statuts_termines:
                    statut = "Terminée"
                    color_statut = c['success']
                elif statut_normalise in ['en attente', 'attente', 'en cours', 'encours', 'à payer', 'a payer']:
                    statut = "En attente"
                    color_statut = c['warning']
                else:
                    # Afficher le statut tel quel s'il n'est pas reconnu
                    statut = statut_val.capitalize() if statut_val else "En attente"
                    color_statut = c['warning']
            
            lbl_statut = QLabel(statut)
            lbl_statut.setStyleSheet(f"color: {color_statut}; font-weight: bold; border: none; background: transparent; padding-right: 10px;")
            row_layout.addWidget(lbl_statut)
            
            # Bouton Imprimer
            btn_imprimer = QPushButton(" Imprimer")
            btn_imprimer.setIcon(qta.icon("fa5s.print", color="white"))
            
            if facture:
                btn_imprimer.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {c['danger']};
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 5px 10px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: {c['danger']}dd;
                    }}
                """)
                btn_imprimer.setCursor(Qt.PointingHandCursor)
                btn_imprimer.clicked.connect(lambda checked=False, cf=code_facture, cv=code_visite: self.imprimer_facture(cf, cv))
            else:
                btn_imprimer.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {c['border_light']};
                        color: {c['text_secondary']};
                        border: none;
                        border-radius: 4px;
                        padding: 5px 10px;
                        font-weight: bold;
                    }}
                """)
                btn_imprimer.setEnabled(False)
                
            row_layout.addWidget(btn_imprimer)
            
            self.content_layout.addWidget(row_widget)
            
        self.content_layout.addStretch()
        
    def imprimer_facture(self, code_facture, code_visite):
        """Imprime la facture et affiche l'aperçu PDF"""
        from views.shared.message_box import CustomMessageBox
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        from services.pdf_patient.facture_pdf import FacturePatientPDFService
        
        try:
            # Récupérer les détails complets (panier, patient, etc.)
            details_facture = self.controleur.service.facture_service.dao.details_facture_pdf(code_facture)
            info_cabinet = self.controleur.get_cabinet_info()
            
            if not details_facture:
                CustomMessageBox("Erreur", "Impossible de récupérer les détails de la facture.", is_success=False, parent=self).exec()
                return
                
            import tempfile
            import os
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix=f"facture_{code_facture}_")
            os.close(fd)
            
            # Utilisation du nouveau service PDF
            info_cabinet = self.controleur.get_cabinet_info()
            chemin = FacturePatientPDFService.generer_facture_pdf(details_facture, info_cabinet, chemin_pdf)
            
            if chemin and os.path.exists(chemin):
                # Fermer le popover
                self.accept()
                
                # Ouvrir l'aperçu PDF
                dialog = ApercuPDFDialog(chemin, f"Aperçu - Facture {code_facture}", self.parent())
                dialog.exec()
            else:
                CustomMessageBox("Erreur", "La génération du PDF a échoué.", is_success=False, parent=self).exec()
                
        except Exception as e:
            CustomMessageBox("Erreur", f"Erreur inattendue :\n{str(e)}", is_success=False, parent=self).exec()

