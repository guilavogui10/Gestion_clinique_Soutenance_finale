"""
Composant PrescriptionLigneItem.
Responsabilité : Affichage d'une ligne produit prescrit avec bouton suppression.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from views.shared.theme_manager import theme_manager


class PrescriptionLigneItem:
    """Crée une ligne visuelle pour un produit dans le panier prescription."""

    def __init__(self):
        pass

    def create(self, designation: str, quantite: int, prix: float,
               date_expiration, code_prescription: str,
               on_delete_callback) -> QFrame:
        c = theme_manager.colors()

        ligne = QFrame()
        ligne.setFixedHeight(70)
        ligne.setStyleSheet(f"""
            QFrame {{
                background: {c['bg_card']};
                border-radius: 12px;
                border: 2px solid {c['border']};
            }}
            QFrame:hover {{
                border: 2px solid {c['primary']};
                background: {c['hover']};
            }}
        """)

        ligne.code_prescription = code_prescription
        ligne.quantite          = quantite
        ligne.prix              = prix

        layout = QHBoxLayout(ligne)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Icône médicale
        icon_container = QFrame()
        icon_container.setFixedSize(50, 50)
        icon_container.setStyleSheet(f"""
            QFrame {{
                background: {c['primary']};
                border-radius: 10px;
                border: none;
            }}
        """)
        icon_layout = QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(
            qta.icon("fa5s.pills", color=c['text_inverse']).pixmap(QSize(24, 24))
        )
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(icon_lbl)

        # Informations produit
        info = QVBoxLayout()
        info.setSpacing(4)

        nom_lbl = QLabel(designation)
        nom_lbl.setStyleSheet(
            f"font-weight: bold; color: {c['text_primary']}; font-size: 13px;"
            "border: none; background: transparent;"
        )

        date_str = (
            date_expiration.strftime("%d/%m/%Y")
            if hasattr(date_expiration, "strftime")
            else str(date_expiration) if date_expiration else "N/A"
        )

        detail_lbl = QLabel(
            f"<span style='color: {c['text_secondary']};'>Qté:</span> "
            f"<span style='color: {c['primary']}; font-weight: bold;'>{quantite}</span> "
            f"<span style='color: {c['border']};'>•</span> "
            f"<span style='color: {c['text_secondary']};'>{prix:,.0f} GNF</span> "
            f"<span style='color: {c['border']};'>•</span> "
            f"<span style='color: {c['text_secondary']};'>Exp:</span> "
            f"<span style='color: {c['warning']}; font-weight: bold;'>{date_str}</span>"
            .replace(",", " ")
        )
        detail_lbl.setStyleSheet(
            f"color: {c['text_secondary']}; font-size: 11px; border: none; background: transparent;"
        )

        info.addWidget(nom_lbl)
        info.addWidget(detail_lbl)

        # Sous-total
        total_container = QVBoxLayout()
        total_container.setSpacing(2)

        lbl_sous_total_titre = QLabel("Sous-total")
        lbl_sous_total_titre.setStyleSheet(
            f"font-size: 9px; color: {c['text_muted']}; font-weight: bold;"
            "border: none; background: transparent;"
        )
        lbl_sous_total_titre.setAlignment(Qt.AlignRight)

        sous_total = quantite * prix
        lbl_sous_total_valeur = QLabel(f"{sous_total:,.0f} GNF".replace(",", " "))
        lbl_sous_total_valeur.setStyleSheet(
            f"font-size: 14px; color: {c['primary']}; font-weight: bold;"
            "border: none; background: transparent;"
        )
        lbl_sous_total_valeur.setAlignment(Qt.AlignRight)

        total_container.addWidget(lbl_sous_total_titre)
        total_container.addWidget(lbl_sous_total_valeur)

        # Bouton supprimer
        btn_del = QPushButton(qta.icon("fa5s.trash-alt", color=c['text_inverse']), "")
        btn_del.setFixedSize(40, 40)
        btn_del.setStyleSheet(f"""
            QPushButton {{
                background: {c['danger']};
                border: none;
                border-radius: 10px;
            }}
            QPushButton:hover {{ background: {c['danger']}cc; }}
            QPushButton:pressed {{ background: {c['danger']}; }}
        """)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setToolTip("Supprimer ce produit de la prescription")
        btn_del.clicked.connect(lambda: on_delete_callback(ligne))

        layout.addWidget(icon_container)
        layout.addLayout(info, 1)
        layout.addLayout(total_container)
        layout.addWidget(btn_del)

        return ligne
