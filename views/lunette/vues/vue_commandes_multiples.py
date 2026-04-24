import qtawesome as qta
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from views.shared.theme_manager import theme_manager


def _c():
    return theme_manager.colors()


def _sep(couleur=None):
    c = _c()
    if couleur is None:
        couleur = c['border']
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background:{couleur}; border:none;")
    return f


def _lbl_vide(texte):
    from PySide6.QtCore import Qt
    c = _c()
    lbl = QLabel(texte)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(
        f"color:{c['text_secondary']}; font-size:11px; background:transparent;"
    )
    return lbl


def _row_ic_val(icone_name, valeur, couleur_ic=None, couleur_val=None, gras=False):
    c = _c()
    if couleur_ic is None:
        couleur_ic = c['text_secondary']
    if couleur_val is None:
        couleur_val = c['text_secondary']
    w = QWidget()
    w.setStyleSheet("background:transparent;")
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(5)
    ic = QLabel()
    ic.setPixmap(qta.icon(icone_name, color=couleur_ic).pixmap(QSize(11, 11)))
    ic.setStyleSheet("background:transparent; border:none;")
    lbl = QLabel(str(valeur) if valeur else "—")
    poids = "700" if gras else "400"
    lbl.setStyleSheet(
        f"color:{couleur_val}; font-size:11px; font-weight:{poids};"
        f"background:transparent; border:none;"
    )
    lbl.setWordWrap(True)
    lay.addWidget(ic)
    lay.addWidget(lbl)
    lay.addStretch()
    return w


class VueCommandesMultiples(QWidget):
    """Liste des patients ayant plus d'une commande sur la session."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 12, 16, 16)
        self._layout.setSpacing(10)

    def charger(self, patients: list):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not patients:
            self._layout.addWidget(
                _lbl_vide("Aucun patient avec plusieurs commandes"))
            self._layout.addStretch()
            return

        # En-tête informatif
        c = _c()
        info = QLabel(
            f"{len(patients)} patient(s) avec commandes multiples détectés")
        info.setStyleSheet(
            f"color:{c['danger']}; font-size:11px; font-weight:700;"
            f"background:{c['danger_bg']}; border-radius:8px; padding:6px 10px;"
            f"border:1px solid {c['danger']};"
        )
        info.setWordWrap(True)
        self._layout.addWidget(info)

        for p in patients:
            self._layout.addWidget(self._carte_patient(p))

        self._layout.addStretch()

    def _carte_patient(self, p: dict) -> QFrame:
        c = _c()
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame{{background:{c['bg_card']}; border-radius:12px;"
            f"border:1px solid {c['border']};}}"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)

        # Ligne 1 : nom + badge nombre
        l1 = QHBoxLayout()
        nom = p.get("patient_nom", "")
        prenom = p.get("patient_prenom", "")
        nom_lbl = QLabel(f"{nom} {prenom}".strip() or "—")
        nom_lbl.setStyleSheet(
            f"color:{c['text_primary']}; font-size:12px; font-weight:700;"
            f"background:transparent; border:none;"
        )
        nb = p.get("nombre_commandes", 0)
        badge = QLabel(f"{nb} commandes")
        badge.setStyleSheet(
            f"background:{c['danger_bg']}; color:{c['danger']};"
            f"border-radius:8px; font-size:10px; font-weight:700;"
            f"padding:2px 8px; border:1px solid {c['danger']};"
        )
        ic = QLabel()
        ic.setPixmap(
            qta.icon("fa5s.user", color=c['danger']).pixmap(QSize(12, 12)))
        ic.setStyleSheet("background:transparent; border:none;")
        l1.addWidget(ic)
        l1.addSpacing(6)
        l1.addWidget(nom_lbl)
        l1.addStretch()
        l1.addWidget(badge)
        lay.addLayout(l1)
        lay.addWidget(_sep())

        # Ligne 2 : avertissement
        lay.addWidget(_row_ic_val(
            "fa5s.exclamation-triangle",
            "Vérifier doublons ou remplacement urgent",
            c['warning'], c['warning']))

        return frame
