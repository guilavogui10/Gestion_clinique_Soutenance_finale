"""
personnel_pdf.py  —  Carte membre du personnel
Format : portrait compact (275 × 255 pt ≈ 97 × 90 mm)
Fond blanc, sans bordure externe, thème bleu.
"""
import os
import io
import tempfile
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader


# ── Cache module-niveau pour images (évite de ré-encoder à chaque appel) ─────
_OEIL_READER  = None   # ImageReader pré-chargé et redimensionné
_LOGO_READERS = {}     # {chemin: ImageReader}  (un par logo de cabinet)


def _oeil_path():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for p in [
        os.path.join(root, "assets", "images", "oeil.png"),
        os.path.join(root, "assets", "image",  "oeil.png"),
        os.path.join(root, "images", "oeil.png"),
    ]:
        if os.path.exists(p):
            return p
    return None


def _get_oeil_reader(display_w=62, display_h=46):
    """Retourne un ImageReader de oeil.png redimensionné à 2× la taille d'affichage."""
    global _OEIL_READER
    if _OEIL_READER is None:
        path = _oeil_path()
        if path:
            try:
                from PIL import Image
                img = Image.open(path).convert("RGBA")
                img = img.resize((display_w * 2, display_h * 2), Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                _OEIL_READER = ImageReader(buf)
            except Exception:
                _OEIL_READER = False   # marqueur "échec, ne pas réessayer"
    return _OEIL_READER if _OEIL_READER else None


def _get_logo_reader(logo_path, display_w=38, display_h=38):
    """Retourne un ImageReader du logo redimensionné (cache par chemin)."""
    if logo_path not in _LOGO_READERS:
        try:
            from PIL import Image
            img = Image.open(logo_path).convert("RGBA")
            img = img.resize((display_w * 2, display_h * 2), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            _LOGO_READERS[logo_path] = ImageReader(buf)
        except Exception:
            _LOGO_READERS[logo_path] = None
    return _LOGO_READERS[logo_path]


# ── Palette ──────────────────────────────────────────────────────────────────
PAT_HDR = colors.Color(0.10, 0.20, 0.33)
VIS_HDR = colors.Color(0.22, 0.59, 0.59)
BLEU    = colors.Color(0.15, 0.38, 0.93)
ICON_BG = colors.Color(0.84, 0.91, 0.97)
BLANC   = colors.white
GRIS_LN = colors.Color(0.72, 0.82, 0.90)
TEXT_DK = colors.Color(0.10, 0.20, 0.33)


# ── Primitives ────────────────────────────────────────────────────────────────

def _icon_sq(c, x, y, sz=13):
    c.setFillColor(ICON_BG)
    c.roundRect(x, y, sz, sz, 2, fill=1, stroke=0)


def _dotline(c, x1, x2, y):
    c.setStrokeColor(GRIS_LN)
    c.setLineWidth(0.4)
    c.setDash([1, 2])
    c.line(x1, y, x2, y)
    c.setDash()


def _section_box(c, x, y, w, h, hdr_color, r=6, hdr_h=26):
    """Boîte blanche + bandeau haut coloré, sans bordure externe."""
    c.setFillColor(BLANC)
    c.roundRect(x, y, w, h, r, fill=1, stroke=0)
    c.setFillColor(hdr_color)
    c.roundRect(x, y + h - hdr_h, w, hdr_h, r, fill=1, stroke=0)
    c.rect(x, y + h - hdr_h, w, r, fill=1, stroke=0)
    return y + h - hdr_h   # y_bas_du_bandeau


def _field(c, x, y, w, label, value=""):
    """Ligne : [ico] LABEL : ...... valeur   (hauteur ~14pt)"""
    SZ = 13
    _icon_sq(c, x, y - SZ + 1, SZ)
    LX = x + SZ + 4
    c.setFillColor(TEXT_DK)
    c.setFont("Helvetica-Bold", 6.5)
    c.drawString(LX, y - 8, f"{label} :")
    lw = len(label) * 3.9 + 11
    vx = LX + lw
    if value:
        c.setFont("Helvetica", 6.5)
        c.setFillColor(BLEU)
        c.drawString(vx, y - 8, str(value))
        vx += len(str(value)) * 3.9 + 3
    _dotline(c, vx, x + w - 3, y - 9)


def _draw_eye(c, cx, cy, color=BLEU):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(1.5)
    c.ellipse(cx-7, cy-3, cx+7, cy+3, fill=0, stroke=1)
    c.circle(cx, cy, 2.5, fill=1, stroke=0)
    c.setFillColor(BLANC)
    c.circle(cx, cy, 1.2, fill=1, stroke=0)


def _person_icon(c, x, y, sz, col):
    c.setFillColor(col)
    c.setStrokeColor(col)
    c.circle(x + sz/2, y + sz*0.63, sz*0.26, fill=1, stroke=0)
    c.setLineWidth(1.4)
    c.arc(x+sz*0.1, y+sz*0.15, x+sz*0.9, y+sz*0.55, 0, 180)


# ── Service ───────────────────────────────────────────────────────────────────

class PersonnelPDFService:

    @staticmethod
    def generer_carte_membre(personnel_data, cabinet_info=None, photo_path=None, chemin_pdf=None):
        """Génère la carte membre du personnel — portrait compact, fond blanc."""
        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="carte_membre_")
            os.close(fd)

        cabinet_info = cabinet_info or {}
        personnel_data = personnel_data or {}

        # ── Dimensions portrait compact : 275 × 255 pt (≈97 × 90 mm) ──────────
        PAGE_W, PAGE_H = 275, 255
        c = pdfcanvas.Canvas(chemin_pdf, pagesize=(PAGE_W, PAGE_H))

        M      = 8    # marge
        HDR_H  = 48   # entête cabinet
        FTR_H  = 16   # pied de page
        GAP    = 7    # espace entre colonnes
        HDR_BND= 26   # hauteur bandeau section (doit correspondre à _section_box hdr_h)

        BODY_TOP = PAGE_H - HDR_H - 4
        BODY_BOT = FTR_H + 3
        SEC_H    = BODY_TOP - BODY_BOT
        COL_W    = (PAGE_W - 2*M - GAP) / 2  # ≈ 126 pt

        FIELD_H  = 18   # hauteur fixe par champ (compact)

        # ── Helpers modèle ────────────────────────────────────────────────────
        def _get(attr, default=""):
            v = personnel_data.get(attr)
            return str(v) if v else default

        code       = _get('code')
        nom        = _get('nom')
        prenom     = _get('prenom')
        fonction   = _get('fonction')
        contact    = _get('contact')
        mail       = _get('mail')
        adresse    = _get('adresse')

        # ─────────────────────────────────────────────────────────────────────
        # FOND BLANC
        # ─────────────────────────────────────────────────────────────────────
        c.setFillColor(BLANC)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

        # ─────────────────────────────────────────────────────────────────────
        # EN-TÊTE CABINET
        # ─────────────────────────────────────────────────────────────────────
        hdr_y = PAGE_H - HDR_H

        # Logo (reader redimensionné mis en cache pour éviter le ré-encodage)
        logo_path = cabinet_info.get('logo_url') or cabinet_info.get('logo')
        logo_ok = False
        if logo_path and os.path.exists(logo_path):
            logo_reader = _get_logo_reader(logo_path, display_w=38, display_h=38)
            if logo_reader:
                try:
                    c.drawImage(logo_reader, M, hdr_y + 6,
                                width=38, height=38, mask='auto',
                                preserveAspectRatio=True)
                    logo_ok = True
                except Exception:
                    pass
        if not logo_ok:
            _draw_eye(c, M + 18, hdr_y + 24)
            c.setStrokeColor(BLEU)
            c.setLineWidth(1.6)
            c.ellipse(M+2, hdr_y+16, M+34, hdr_y+32, fill=0, stroke=1)

        txt_x = M + 44
        nom_cab = cabinet_info.get("nom_cabinet", "CABINET OPHTALMOLOGIQUE").upper()
        adr_cab = cabinet_info.get("adresse_cabinet", "")

        c.setFillColor(TEXT_DK)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(txt_x, hdr_y + 34, nom_cab)
        c.setFillColor(BLEU)
        c.setFont("Helvetica", 6)
        c.drawString(txt_x, hdr_y + 24, "VOTRE VISION, NOTRE PRIORITÉ")
        if adr_cab:
            c.setFillColor(colors.Color(0.45, 0.50, 0.55))
            c.setFont("Helvetica", 5.5)
            c.drawString(txt_x, hdr_y + 14, adr_cab)

        # Image oeil.png (coin haut droit) — reader redimensionné mis en cache
        OW, OH = 62, 46
        oeil_reader = _get_oeil_reader(display_w=OW, display_h=OH)
        if oeil_reader:
            try:
                c.drawImage(oeil_reader, PAGE_W - M - OW, hdr_y + 1,
                            width=OW, height=OH, mask='auto',
                            preserveAspectRatio=True)
            except Exception:
                pass

        # Ligne bleue séparatrice
        c.setStrokeColor(BLEU)
        c.setLineWidth(1.0)
        c.line(M, hdr_y, PAGE_W - M, hdr_y)

        # ─────────────────────────────────────────────────────────────────────
        # SECTION PERSONNEL (gauche)
        # ─────────────────────────────────────────────────────────────────────
        LEFT_X = M
        hdr_bot = _section_box(c, LEFT_X, BODY_BOT, COL_W, SEC_H, PAT_HDR, hdr_h=HDR_BND)

        _person_icon(c, LEFT_X + 6, hdr_bot + 6, 14, BLANC)
        c.setFillColor(BLANC)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(LEFT_X + 24, hdr_bot + 9, "PERSONNEL")

        personnel_fields = [
            ("CODE",       code),
            ("NOM",        nom),
            ("PRÉNOM",     prenom),
            ("FONCTION",   fonction),
            ("CONTACT",    contact),
            ("EMAIL",      mail),
            ("ADRESSE",    adresse),
        ]
        PAD   = 7
        FW    = COL_W - 12

        for i, (lbl, val) in enumerate(personnel_fields):
            # Distribue depuis le bas du bandeau vers le bas de la section
            fy = hdr_bot - PAD - (i + 0.5) * FIELD_H
            _field(c, LEFT_X + 6, fy, FW, lbl, val)

        # ─────────────────────────────────────────────────────────────────────
        # SECTION PHOTO (droite)
        # ─────────────────────────────────────────────────────────────────────
        RIGHT_X = M + COL_W + GAP
        hdr_bot2 = _section_box(c, RIGHT_X, BODY_BOT, COL_W, SEC_H, VIS_HDR, hdr_h=HDR_BND)

        _person_icon(c, RIGHT_X + 6, hdr_bot2 + 6, 14, BLANC)
        c.setFillColor(BLANC)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(RIGHT_X + 24, hdr_bot2 + 9, "PHOTO")

        # Cadre photo
        photo_x = RIGHT_X + (COL_W - 80) / 2
        photo_y = BODY_BOT + 18
        photo_w = 80
        photo_h = 100

        c.setStrokeColor(BLEU)
        c.setLineWidth(1.5)
        c.rect(photo_x, photo_y, photo_w, photo_h, fill=0, stroke=1)

        photo_ok = False
        if photo_path and os.path.exists(photo_path):
            try:
                c.drawImage(photo_path, photo_x + 2, photo_y + 2,
                            width=photo_w - 4, height=photo_h - 4, mask='auto',
                            preserveAspectRatio=True)
                photo_ok = True
            except Exception:
                pass
        
        if not photo_ok:
            c.setFillColor(colors.Color(0.85, 0.85, 0.85))
            c.setStrokeColor(colors.Color(0.85, 0.85, 0.85))
            _person_icon(c, photo_x + 20, photo_y + 30, 40, colors.Color(0.75, 0.75, 0.75))

        # ─────────────────────────────────────────────────────────────────────
        # PIED DE PAGE
        # ─────────────────────────────────────────────────────────────────────
        c.setStrokeColor(GRIS_LN)
        c.setLineWidth(0.4)
        c.line(M, FTR_H, PAGE_W - M, FTR_H)
        _draw_eye(c, PAGE_W / 2, FTR_H - 6)
        c.setFillColor(TEXT_DK)
        c.setFont("Helvetica", 5)
        c.drawCentredString(PAGE_W / 2, FTR_H - 14,
                            "CARTE MEMBRE STRICTEMENT CONFIDENTIELLE.")

        c.save()
        return chemin_pdf
