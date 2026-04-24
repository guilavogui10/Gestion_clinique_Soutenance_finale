"""
Composant PrescriptionLigneItem.
Responsabilité : Affichage d'une ligne produit prescrit avec bouton suppression.
Fidèle au pattern PanierLigneItem — palette médicale bleue.

Différences vs PanierLigneItem :
  - Attribut stocké : code_prescription (pas code_panier)
  - date_expiration affichée en lecture seule (remplie par FEFO, non saisie)
  - Icône médicale : fa5s.prescription-bottle-alt
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
)


class PrescriptionLigneItem:
    """Crée une ligne visuelle pour un produit dans le panier prescription."""

    def __init__(self, bleu_principal: str, rouge: str):
        self.bleu_principal = bleu_principal
        self.rouge          = rouge

    def create(self, designation: str, quantite: int, prix: float,
               date_expiration, code_prescription: str,
               on_delete_callback) -> QFrame:
        """
        Crée une ligne prescription avec toutes les informations.

        Args:
            designation      : Libellé du produit prescrit
            quantite         : Quantité prescrite
            prix             : Prix unitaire appliqué
            date_expiration  : Date du lot FEFO (auto-remplie)
            code_prescription: Code PRS généré par le DAO
            on_delete_callback: Callable(ligne_widget) pour suppression

        Returns:
            QFrame: Widget de la ligne prêt à être inséré dans le layout
        """
        ligne = QFrame()
        ligne.setFixedHeight(70)
        ligne.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ffffff,
                    stop:1 #f8fafc
                );
                border-radius: 12px;
                border: 2px solid #e2e8f0;
            }
            QFrame:hover {
                border: 2px solid #bfdbfe;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f8fafc,
                    stop:1 #eff6ff
                );
            }
        """)

        # Données stockées sur le widget pour calcul du total et suppression BDD
        ligne.code_prescription = code_prescription
        ligne.quantite          = quantite
        ligne.prix              = prix

        layout = QHBoxLayout(ligne)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Icône médicale avec background bleu dégradé
        icon_container = QFrame()
        icon_container.setFixedSize(50, 50)
        icon_container.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {self.bleu_principal},
                    stop:1 #2c5282
                );
                border-radius: 10px;
                border: none;
            }}
        """)
        icon_layout = QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(
            qta.icon("fa5s.pills", color="white").pixmap(QSize(24, 24))
        )
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(icon_lbl)

        # Informations produit
        info = QVBoxLayout()
        info.setSpacing(4)

        nom_lbl = QLabel(designation)
        nom_lbl.setStyleSheet(
            "font-weight: bold; color: #1e293b; font-size: 13px;"
            "border: none; background: transparent;"
        )

        # Formatage date expiration
        date_str = (
            date_expiration.strftime("%d/%m/%Y")
            if hasattr(date_expiration, "strftime")
            else str(date_expiration) if date_expiration else "N/A"
        )

        sous_total = quantite * prix

        detail_lbl = QLabel(
            f"<span style='color: #64748b;'>Qté:</span> "
            f"<span style='color: {self.bleu_principal}; font-weight: bold;'>{quantite}</span> "
            f"<span style='color: #cbd5e1;'>•</span> "
            f"<span style='color: #64748b;'>{prix:,.0f} GNF</span> "
            f"<span style='color: #cbd5e1;'>•</span> "
            f"<span style='color: #64748b;'>Exp:</span> "
            f"<span style='color: #f59e0b; font-weight: bold;'>{date_str}</span>"
            .replace(",", " ")
        )
        detail_lbl.setStyleSheet(
            "color: #64748b; font-size: 11px; border: none; background: transparent;"
        )

        info.addWidget(nom_lbl)
        info.addWidget(detail_lbl)

        # Sous-total mis en valeur
        total_container = QVBoxLayout()
        total_container.setSpacing(2)

        lbl_sous_total_titre = QLabel("Sous-total")
        lbl_sous_total_titre.setStyleSheet(
            "font-size: 9px; color: #94a3b8; font-weight: bold;"
            "border: none; background: transparent; text-transform: uppercase;"
        )
        lbl_sous_total_titre.setAlignment(Qt.AlignRight)

        lbl_sous_total_valeur = QLabel(f"{sous_total:,.0f} GNF".replace(",", " "))
        lbl_sous_total_valeur.setStyleSheet(
            f"font-size: 14px; color: {self.bleu_principal}; font-weight: bold;"
            "border: none; background: transparent;"
        )
        lbl_sous_total_valeur.setAlignment(Qt.AlignRight)

        total_container.addWidget(lbl_sous_total_titre)
        total_container.addWidget(lbl_sous_total_valeur)

        # Bouton supprimer
        btn_del = QPushButton(qta.icon("fa5s.trash-alt", color="white"), "")
        btn_del.setFixedSize(40, 40)
        btn_del.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.rouge},
                    stop:1 #c0392b
                );
                border: none;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c0392b,
                    stop:1 {self.rouge}
                );
            }}
            QPushButton:pressed {{ background: #922b21; }}
        """)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setToolTip("Supprimer ce produit de la prescription")
        btn_del.clicked.connect(lambda: on_delete_callback(ligne))

        layout.addWidget(icon_container)
        layout.addLayout(info, 1)
        layout.addLayout(total_container)
        layout.addWidget(btn_del)

        return ligne