"""
Sidebar Stats - Colonne droite
1. Répartition par statut patient (barres horizontales)
2. Alertes & Attentes (cards d'alertes)
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QPushButton, QProgressBar)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import qtawesome as qta
from views.shared.theme_manager import theme_manager


class StatusBar(QWidget):
    """Barre horizontale pour un statut"""
    
    def __init__(self, label, count, percentage, color, parent=None):
        super().__init__(parent)
        self.color = color
        self.init_ui(label, count, percentage)
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def init_ui(self, label, count, percentage):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(10)
        
        # Label du statut
        self.label = QLabel(label)
        self.label.setObjectName("StatusLabel")
        self.label.setFixedWidth(150)
        
        # Barre de progression
        self.progress = QProgressBar()
        self.progress.setObjectName("StatusProgress")
        self.progress.setFixedHeight(10)
        self.progress.setTextVisible(False)
        self.progress.setMaximum(100)
        self.progress.setValue(percentage)
        self.progress.setProperty("color", self.color)
        
        # Count + Percentage
        self.count_label = QLabel(f"{count} ({percentage}%)")
        self.count_label.setObjectName("CountLabel")
        self.count_label.setFixedWidth(80)
        self.count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        layout.addWidget(self.label)
        layout.addWidget(self.progress, 1)
        layout.addWidget(self.count_label)
    
    def apply_theme(self):
        c = theme_manager.colors()
        
        self.setStyleSheet(f"""
            QLabel {{
                background: transparent;
                border: none;
            }}
            QLabel#StatusLabel {{
                color: {c['text_secondary']};
                font-size: 11px;
                font-weight: 500;
            }}
            QLabel#CountLabel {{
                color: {self.color};
                font-size: 11px;
                font-weight: 800;
            }}
            QProgressBar#StatusProgress {{
                background: {c['border_light']};
                border: none;
                border-radius: 5px;
            }}
            QProgressBar#StatusProgress::chunk {{
                background: {self.color};
                border-radius: 5px;
            }}
        """)


class AlertCard(QFrame):
    """Card d'alerte individuelle"""
    
    def __init__(self, alert_type, patient_name, code_visite, message, time_exceeded, parent=None):
        super().__init__(parent)
        self.alert_type = alert_type  # "critical", "warning", "info"
        self.init_ui(patient_name, code_visite, message, time_exceeded)
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def init_ui(self, patient_name, code_visite, message, time_exceeded):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        
        # Icône d'alerte
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(20, 20)
        
        # Textes
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        # Nom + Code
        header = QLabel(f"{patient_name} ({code_visite})")
        header.setObjectName("AlertHeader")
        font_header = QFont()
        font_header.setBold(True)
        font_header.setPointSize(11)
        header.setFont(font_header)
        
        # Message
        msg_label = QLabel(message)
        msg_label.setObjectName("AlertMessage")
        msg_label.setWordWrap(True)
        
        text_layout.addWidget(header)
        text_layout.addWidget(msg_label)
        
        # Badge temps dépassé
        self.time_badge = QLabel(time_exceeded)
        self.time_badge.setObjectName("TimeBadge")
        self.time_badge.setAlignment(Qt.AlignCenter)
        self.time_badge.setFixedWidth(90)
        
        layout.addWidget(self.icon_label)
        layout.addLayout(text_layout, 1)
        layout.addWidget(self.time_badge)
    
    def apply_theme(self):
        c = theme_manager.colors()
        
        # Couleurs selon le type d'alerte
        colors_map = {
            "critical": c['danger'],
            "warning": c['warning'],
            "info": c['info']
        }
        icon_map = {
            "critical": "fa5s.exclamation-circle",
            "warning": "fa5s.exclamation-triangle",
            "info": "fa5s.info-circle"
        }
        
        color = colors_map.get(self.alert_type, c['text_secondary'])
        icon_name = icon_map.get(self.alert_type, "fa5s.info-circle")
        
        self.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid {c['border']};
                border-radius: 10px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
            QLabel#AlertHeader {{
                color: {c['text_primary']};
            }}
            QLabel#AlertMessage {{
                color: {c['text_secondary']};
                font-size: 10px;
            }}
            QLabel#TimeBadge {{
                background: {c['border']};
                color: {c['text_primary']};
                border-radius: 8px;
                padding: 4px 8px;
                font-size: 10px;
                font-weight: 800;
            }}
        """)
        
        self.icon_label.setPixmap(qta.icon(icon_name, color=color).pixmap(20, 20))


class SidebarStats(QWidget):
    """Sidebar avec répartition et alertes"""
    
    view_all_alerts = Signal()  # Signal pour voir toutes les alertes
    
    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Section 1 : Répartition par statut
        self.repartition_frame = self._create_section_frame("Répartition par statut patient")
        self.repartition_layout = QVBoxLayout()
        self.repartition_layout.setSpacing(8)
        self.repartition_frame.layout().addLayout(self.repartition_layout)
        
        # Section 2 : Alertes & Attentes
        self.alerts_frame = self._create_section_frame("Alertes & Attentes")
        self.alerts_layout = QVBoxLayout()
        self.alerts_layout.setSpacing(10)
        self.alerts_frame.layout().addLayout(self.alerts_layout)
        
        # Bouton "Voir toutes"
        self.btn_view_all = QPushButton("Voir toutes")
        self.btn_view_all.setObjectName("ViewAllButton")
        self.btn_view_all.setCursor(Qt.PointingHandCursor)
        self.btn_view_all.clicked.connect(self.view_all_alerts.emit)
        self.alerts_frame.layout().addWidget(self.btn_view_all, alignment=Qt.AlignRight)
        
        layout.addWidget(self.repartition_frame)
        layout.addWidget(self.alerts_frame)
        layout.addStretch()
    
    def _create_section_frame(self, title):
        """Crée un cadre de section"""
        frame = QFrame()
        frame.setObjectName("SectionFrame")
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(10)
        
        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")
        font_title = QFont()
        font_title.setPointSize(12)
        font_title.setBold(True)
        title_label.setFont(font_title)
        
        layout.addWidget(title_label)
        
        return frame
    
    def update_repartition(self, stats):
        """Met à jour la répartition par statut"""
        # Nettoyer
        while self.repartition_layout.count():
            item = self.repartition_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        c = theme_manager.colors()
        
        # Utiliser les vraies données du DAO
        details_par_statut = stats.get('details_par_statut', [])
        
        # Calculer le total pour les pourcentages
        total = sum(item['nombre'] for item in details_par_statut)
        
        # Mapping des couleurs par statut
        couleurs_statut = {
            'Attente consultation': c['warning'],
            'Attente rendez-vous': c['warning'],
            'En consultation': c['info'],
            'Examen en cours': c['accent'],
            'Attente examen': c['accent'],
            'Attente chirurgie': c['danger'],
            'Attente commande lunette': c['info'],
            'Attente prescription': c['info'],
            'Attente paiement': c['warning'],
            'Accueil': c['success'],
            'Libéré': c['success']
        }
        
        # Créer les barres pour chaque statut
        for item in details_par_statut:
            statut = item['statut']
            count = item['nombre']
            pct = round((count / total * 100)) if total > 0 else 0
            color = couleurs_statut.get(statut, c['text_secondary'])
            
            bar = StatusBar(statut, count, pct, color)
            self.repartition_layout.addWidget(bar)
    
    def update_alerts(self, alertes):
        """Met à jour les alertes"""
        # Nettoyer
        while self.alerts_layout.count():
            item = self.alerts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Utiliser les vraies alertes
        if not alertes or len(alertes) == 0:
            # Aucune alerte
            info_label = QLabel("✅ Aucune alerte en cours")
            info_label.setStyleSheet(f"color: {theme_manager.colors()['success']}; font-size: 12px; padding: 10px;")
            self.alerts_layout.addWidget(info_label)
            return
        
        # Afficher les alertes (max 3)
        for alerte in alertes[:3]:
            code_visite = alerte.get('code_visite', '')
            temps_attente = alerte.get('temps_attente', 0)
            statut = alerte.get('statut', '')
            severite = alerte.get('severite', 'faible')
            
            # Déterminer le type d'alerte
            if severite == 'critique':
                alert_type = 'critical'
            elif severite in ['elevee', 'moyenne']:
                alert_type = 'warning'
            else:
                alert_type = 'info'
            
            # Formater le temps
            heures = temps_attente // 60
            minutes = temps_attente % 60
            temps_str = f"{heures}h {minutes}min" if heures > 0 else f"{minutes}min"
            
            # Message
            message = f"{statut} depuis {temps_str}"
            
            # Badge temps dépassé
            seuil = 20
            depassement = temps_attente - seuil
            time_badge = f"Dépasse {depassement}min"
            
            # Récupérer le nom du patient (si disponible)
            patient_name = f"Patient {code_visite}"
            
            card = AlertCard(alert_type, patient_name, code_visite, message, time_badge)
            self.alerts_layout.addWidget(card)
        
        # Info urgences totales
        if len(alertes) > 3:
            info_card = QFrame()
            info_card.setObjectName("InfoCard")
            info_layout = QHBoxLayout(info_card)
            info_layout.setContentsMargins(12, 10, 12, 10)
            
            icon = QLabel()
            icon.setPixmap(qta.icon("fa5s.bell", color=theme_manager.colors()['info']).pixmap(18, 18))
            
            text = QLabel(f"{len(alertes)} alertes au total\nAction prioritaire requise")
            text.setObjectName("InfoText")
            
            info_layout.addWidget(icon)
            info_layout.addWidget(text, 1)
            
            self.alerts_layout.addWidget(info_card)
    
    def apply_theme(self):
        c = theme_manager.colors()
        
        self.setStyleSheet(f"""
            QWidget {{
                background: white;
            }}
            QFrame#SectionFrame {{
                background: white;
                border: none;
            }}
            QLabel#SectionTitle {{
                color: {c['text_primary']};
                background: transparent;
                border: none;
            }}
            QPushButton#ViewAllButton {{
                background: transparent;
                border: none;
                color: {c['info']};
                font-size: 11px;
                font-weight: 600;
                padding: 5px 10px;
            }}
            QPushButton#ViewAllButton:hover {{
                color: {c['primary']};
                text-decoration: underline;
            }}
            QFrame#InfoCard {{
                background: white;
                border: 1px solid {c['border']};
                border-radius: 8px;
            }}
            QLabel#InfoText {{
                color: {c['text_primary']};
                font-size: 11px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
