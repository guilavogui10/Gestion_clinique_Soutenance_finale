# Standard library imports
from enum import Enum
from typing import Dict, Optional

# Third-party imports
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QColor

# Local imports
from views.shared.vue_monitor import PerformanceMonitor
from views.shared.theme_manager import theme_manager
from PySide6.QtWidgets import QGraphicsDropShadowEffect
import qtawesome as qta


class _TC:
    """Descripteur renvoyant la couleur du thème courant."""
    def __init__(self, key):
        self._key = key
    def __set_name__(self, owner, name):
        self._name = name
    def __get__(self, obj, objtype=None):
        return theme_manager.colors()[self._key]


class WorkflowColors:
    """Constantes de couleurs pour le workflow (dynamique via thème)."""
    WAITING = _TC('warning')
    COMPLETED = _TC('success')
    INACTIVE = _TC('border')
    TEXT_ACTIVE = _TC('text_primary')
    TEXT_INACTIVE = _TC('text_muted')
    BORDER_HOVER = _TC('border')
    BACKGROUND_HOVER = _TC('hover')
    SURFACE = _TC('bg_card')
    BORDER = _TC('border')



class ModernTooltip(QFrame):
    """Popup professionnel stylisé avec QtAwesome et ombres portées."""
    def __init__(self, parent=None):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint)
        self.setFixedWidth(240)
        
        # --- Style de la bordure et du fond ---
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {WorkflowColors.SURFACE};
                border: 1px solid {WorkflowColors.BORDER};
                border-radius: 12px;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)

        # --- Effet d'ombre (Shadow) ---
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 50)) # Ombre légère noire
        self.setGraphicsEffect(shadow)

        # --- Layout Principal ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(10)

        # --- En-tête : Icône dynamique + Titre ---
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Label pour l'icône QtAwesome (On l'initialise vide, mise à jour dans enterEvent)
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(20, 20)
        
        self.title_lbl = QLabel("STATUT PATIENT")
        self.title_lbl.setStyleSheet(f"""
            font-weight: 800; 
            color: {WorkflowColors.TEXT_ACTIVE}; 
            font-size: 11px; 
            letter-spacing: 0.5px;
        """)
        
        header_layout.addWidget(self.icon_lbl)
        header_layout.addWidget(self.title_lbl)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # --- Séparateur élégant ---
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color: {WorkflowColors.BORDER};")
        layout.addWidget(line)

        # --- Section Détails : Service ---
        service_container = QHBoxLayout()
        self.service_icon = QLabel() # Petite icône de localisation
        self.service_icon.setPixmap(qta.icon('fa5s.map-marker-alt', color=WorkflowColors.TEXT_INACTIVE).pixmap(12, 12))
        
        self.service_info = QLabel("Service: --")
        self.service_info.setStyleSheet(f"color: {WorkflowColors.TEXT_INACTIVE}; font-size: 11px; font-weight: 500;")
        
        service_container.addWidget(self.service_icon)
        service_container.addWidget(self.service_info)
        service_container.addStretch()
        layout.addLayout(service_container)

        # --- Section Détails : Temps (Mise en avant) ---
        time_container = QHBoxLayout()
        self.time_icon = QLabel() # Petite icône d'horloge
        self.time_icon.setPixmap(qta.icon('fa5s.history', color=WorkflowColors.TEXT_INACTIVE).pixmap(12, 12))
        
        self.time_info = QLabel("Durée: --")
        self.time_info.setStyleSheet(f"color: {WorkflowColors.TEXT_ACTIVE}; font-weight: 700; font-size: 13px;")
        
        time_container.addWidget(self.time_icon)
        time_container.addWidget(self.time_info)
        time_container.addStretch()
        layout.addLayout(time_container)

        # Empêche le tooltip de masquer le curseur
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

class WorkflowStep(QWidget):
    """Widget représentant une étape du workflow médical."""
    def __init__(self, nom: str):
        super().__init__()
        self.setup_ui(nom)
        self.setup_animation()
        
    def setup_ui(self, nom: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        self.dot = QFrame()
        self.dot.setFixedSize(14, 14)
        self.dot.setStyleSheet(
            f"background-color: {WorkflowColors.INACTIVE}; "
            "border-radius: 7px; "
            f"border: 2px solid {WorkflowColors.SURFACE};"
        )
        
        self.opacity_effect = QGraphicsOpacityEffect(self.dot)
        self.dot.setGraphicsEffect(self.opacity_effect)
        
        self.label = QLabel(nom)
        self.label.setStyleSheet(
            f"font-size: 9px; color: {WorkflowColors.TEXT_INACTIVE}; font-weight: 500;"
        )
        self.label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.dot, alignment=Qt.AlignCenter)
        layout.addWidget(self.label, alignment=Qt.AlignCenter)
    
    def setup_animation(self):
        self.pulse_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.pulse_anim.setDuration(800)
        self.pulse_anim.setStartValue(1.0)
        self.pulse_anim.setEndValue(0.1)
        self.pulse_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.pulse_anim.setLoopCount(-1)
    
    def set_status(self, active: bool, waiting: bool = False):
        self.pulse_anim.stop()
        self.opacity_effect.setOpacity(1.0)

        if active:
            color = WorkflowColors.WAITING if waiting else WorkflowColors.COMPLETED
            font_weight = "bold" if waiting else "500"
            if waiting: self.pulse_anim.start()
            
            self.dot.setStyleSheet(f"background-color: {color}; border-radius: 7px; border: 2px solid {WorkflowColors.SURFACE};")
            self.label.setStyleSheet(f"font-size: 9px; color: {color}; font-weight: {font_weight};")
        else:
            self.dot.setStyleSheet(f"background-color: {WorkflowColors.INACTIVE}; border-radius: 7px; border: 2px solid {WorkflowColors.SURFACE};")
            self.label.setStyleSheet(f"font-size: 9px; color: {WorkflowColors.TEXT_INACTIVE}; font-weight: 500;")
    
    def cleanup(self):
        if self.pulse_anim.state() == QPropertyAnimation.Running:
            self.pulse_anim.stop()

class PatientRowWidget(QFrame):
    """Widget représentant une ligne de patient avec Tooltip dynamique."""
    
    STATUS_MAPPING = {
        # Consultation
        "consultation": 0, "consult": 0,
        # Examen
        "examen": 1, "labo": 1, "laboratoire": 1,
        # Chirurgie
        "chirurgie": 2, "operation": 2, "chir": 2,
        # Lunette
        "lunette": 3, "lunettes": 3, "optique": 3,
        # Pharmacie
        "pharmacie": 4, "pharma": 4, "prescription": 4,
        # Paiement
        "paiement": 5, "caisse": 5, "payment": 5, "payement": 5,
        # Rendez-vous (statut spécial - avant consultation)
        "rendez-vous": -1, "rendez vous": -1, "rdv": -1
    }
    
    def __init__(self, patient_name: str, statut_db: str, controleur=None, code_visite=None):
        super().__init__()
        self.patient_name = patient_name
        self.statut_db = statut_db
        self.controleur = controleur
        self.code_visite = code_visite
        
        # Initialisation du tooltip personnalisé (invisible au départ)
        self.custom_tooltip = ModernTooltip()
        self.setMouseTracking(True) # Autorise le suivi du mouvement de souris
        
        self.setup_ui()
        self.apply_workflow_logic(statut_db)
        
        # Monitoring invisible pour récupérer les données
        if self.controleur and self.code_visite:
            self.monitor = PerformanceMonitor(self.controleur)
            self.monitor.start_monitoring(self.code_visite)
            # On n'ajoute PAS self.monitor au layout pour le garder invisible
            
            # Récupérer les services actifs pour ce patient
            self._load_active_services()
        
    def setup_ui(self):
        self.setFixedHeight(60)
        self.setStyleSheet(f"""
            PatientRowWidget {{
                background: {WorkflowColors.SURFACE}; 
                border-radius: 10px; 
                border: 1px solid {WorkflowColors.INACTIVE};
            }}
            PatientRowWidget:hover {{
                border: 1px solid {WorkflowColors.BORDER_HOVER};
                background: {WorkflowColors.BACKGROUND_HOVER};
            }}
        """)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 5, 15, 5)
        
        self.name_lbl = QLabel(self.patient_name)
        self.name_lbl.setMinimumWidth(120)
        self.name_lbl.setMaximumWidth(160)
        self.name_lbl.setWordWrap(True)
        self.name_lbl.setStyleSheet(f"font-weight: bold; color: {WorkflowColors.TEXT_ACTIVE}; font-size: 12px; border: none; background: transparent;")
        main_layout.addWidget(self.name_lbl)

        # Container pour les étapes
        self.steps_container = QWidget()
        self.steps_container.setStyleSheet("background: transparent; border: none;")
        self.steps_layout = QHBoxLayout(self.steps_container)
        self.steps_layout.setContentsMargins(0, 0, 0, 0)
        
        self.steps = {
            "Consultation": WorkflowStep("CONSULTATION"),
            "Examen": WorkflowStep("EXAMEN"),
            "Chirurgie": WorkflowStep("CHIRURGIE"),
            "Lunette": WorkflowStep("LUNETTE"),
            "Pharmacie": WorkflowStep("PHARMACIE"),
            "Paiement": WorkflowStep("PAIEMENT")
        }

        for step in self.steps.values():
            self.steps_layout.addWidget(step)
        
        main_layout.addWidget(self.steps_container)

    def enterEvent(self, event):
        """Met à jour les labels avec QtAwesome uniquement (zéro emoji)."""
        if hasattr(self, 'monitor') and self.controleur:
            # 1. Récupération des données
            info_complete = self.controleur.obtenir_temps_ecoule(self.code_visite)
            alerte, temps, service_brut = self.controleur.verifier_temps_attente_critique(self.code_visite, 15)
            
            # Couleurs de base
            c = theme_manager.colors()
            color_alert = c['danger']
            color_info = c['info']
            color_text_sec = c['text_secondary']
            
            # 2. Logique visuelle selon l'état
            if alerte:
                main_icon = qta.icon('fa5s.exclamation-triangle', color=color_alert)
                self.custom_tooltip.title_lbl.setText("ALERTE RETARD")
                self.custom_tooltip.title_lbl.setStyleSheet(f"font-weight: 800; color: {color_alert}; font-size: 11px; border: none;")
                self.custom_tooltip.setStyleSheet(f"QFrame {{ background-color: {c['danger_bg']}; border: 1px solid {c['danger']}; border-radius: 12px; }}")
                # Mise à jour des icônes de section en rouge pour l'alerte
                self.custom_tooltip.service_icon.setPixmap(qta.icon('fa5s.map-marker-alt', color=color_alert).pixmap(12, 12))
                self.custom_tooltip.time_icon.setPixmap(qta.icon('fa5s.history', color=color_alert).pixmap(12, 12))
            else:
                main_icon = qta.icon('fa5s.clock', color=color_info)
                self.custom_tooltip.title_lbl.setText("STATUT PATIENT")
                self.custom_tooltip.title_lbl.setStyleSheet(f"font-weight: 800; color: {c['text_primary']}; font-size: 11px; border: none;")
                self.custom_tooltip.setStyleSheet(f"QFrame {{ background-color: {c['bg_card']}; border: 1px solid {c['border']}; border-radius: 12px; }}")
                # Icônes de section en gris standard
                self.custom_tooltip.service_icon.setPixmap(qta.icon('fa5s.map-marker-alt', color=color_text_sec).pixmap(12, 12))
                self.custom_tooltip.time_icon.setPixmap(qta.icon('fa5s.history', color=color_text_sec).pixmap(12, 12))

            # Application de l'icône principale
            self.custom_tooltip.icon_lbl.setPixmap(main_icon.pixmap(18, 18))

            # 3. Mise à jour des textes (Nettoyage des emojis texte)
            nom_service = service_brut if service_brut else "Accueil"
            duree_seule = info_complete.split(':')[-1].strip() if ":" in info_complete else info_complete
            
            # On remplace le texte qui contenait des emojis par du texte pur
            self.custom_tooltip.service_info.setText(f"Service: {nom_service}")
            self.custom_tooltip.time_info.setText(f"Durée: {duree_seule}")
            
            # Style spécifique pour le texte de la durée
            time_color = color_alert if alerte else c['text_primary']
            self.custom_tooltip.time_info.setStyleSheet(f"color: {time_color}; font-weight: 700; font-size: 13px; border: none;")

            # 4. Affichage et positionnement
            self.custom_tooltip.adjustSize()
            self._update_tooltip_pos(event.globalPos())
            self.custom_tooltip.show()
            
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Cache le tooltip quand la souris sort."""
        self.custom_tooltip.hide()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        """Fait suivre le tooltip avec la souris."""
        if self.custom_tooltip.isVisible():
            self._update_tooltip_pos(event.globalPos())
        super().mouseMoveEvent(event)

    def _update_tooltip_pos(self, global_pos):
        """Calcule la position du popup au-dessus du curseur."""
        self.custom_tooltip.move(global_pos.x() + 15, global_pos.y() - self.custom_tooltip.height() - 10)

    def apply_workflow_logic(self, statut: str):
        statut_lower = statut.lower().strip()
        ordre_etapes = ["Consultation", "Examen", "Chirurgie", "Lunette", "Pharmacie", "Paiement"]
        index_actuel = self._get_current_step_index(statut_lower)
        is_waiting = "attente" in statut_lower or "waiting" in statut_lower
        
        # Cas spécial : Rendez-vous (avant consultation)
        if index_actuel == -1:
            # Toutes les étapes sont inactives, patient en attente de rendez-vous
            for step_name in ordre_etapes:
                self.steps[step_name].set_status(active=False)
            return

        for i, step_name in enumerate(ordre_etapes):
            if i < index_actuel:
                self.steps[step_name].set_status(active=True, waiting=False)
            elif i == index_actuel:
                self.steps[step_name].set_status(active=True, waiting=is_waiting)
            else:
                self.steps[step_name].set_status(active=False)
    
    def _load_active_services(self):
        """Charge les services actifs pour ce patient et masque les étapes non utilisées."""
        try:
            # Récupérer la consultation pour ce code_visite
            from data.dao_consultation import ConsultationDAO
            dao_consult = ConsultationDAO()
            consultation = dao_consult.obtenir_par_visite(self.code_visite)
            
            if consultation:
                # Vérifier quels services sont demandés
                services_demandes = {
                    "Consultation": True,  # Toujours actif
                    "Examen": consultation.examen == "Oui",
                    "Chirurgie": consultation.chirurgie == "Oui",
                    "Lunette": consultation.commandelunette == "Oui",
                    "Pharmacie": consultation.prescription_produit == "Oui",
                    "Paiement": True  # Toujours actif
                }
                
                # Masquer les étapes non demandées
                for step_name, is_demande in services_demandes.items():
                    if not is_demande and step_name in self.steps:
                        self.steps[step_name].setVisible(False)
            else:
                # Pas de consultation encore, afficher toutes les étapes
                pass
                    
        except Exception as e:
            # En cas d'erreur, afficher toutes les étapes
            print(f"Erreur chargement services actifs: {e}")
            import traceback
            traceback.print_exc()
            pass
    
    def _get_current_step_index(self, statut_lower: str) -> int:
        for keyword, index in self.STATUS_MAPPING.items():
            if keyword in statut_lower:
                return index
        return -1
    
    def cleanup(self):
        if hasattr(self, 'monitor'):
            self.monitor.timer.stop()
        if hasattr(self, 'custom_tooltip'):
            self.custom_tooltip.deleteLater()
        for step in self.steps.values():
            step.cleanup()