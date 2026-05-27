"""
Service de génération PDF pour les résultats médicaux.
Format A5 · cadre global coloré · 2 colonnes · aperçu image intégré.
"""
from __future__ import annotations

import os
import tempfile
from datetime import datetime, date
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdf_canvas

# ── Palette ──────────────────────────────────────────────────────────────────
_VERT   = colors.Color(0.059, 0.482, 0.424)
_BLEU   = colors.Color(0.145, 0.388, 0.922)
_VIOLET = colors.Color(0.486, 0.227, 0.929)
_ROUGE  = colors.Color(0.937, 0.267, 0.267)
_DARK   = colors.Color(0.067, 0.094, 0.153)
_GREY   = colors.Color(0.420, 0.447, 0.502)
_BORD   = colors.Color(0.898, 0.906, 0.918)
_WHITE  = colors.white

# ── Géométrie page A5 ─────────────────────────────────────────────────────────
_W, _H  = A5
_FRAME  = 8
_MX     = 0.45 * cm
_MY_BOT = 1.0  * cm
_LGAP   = 0.25 * cm
_COL_W  = (_W - 2 * (_FRAME + _MX) - _LGAP) / 2
_LBL_W  = 2.60 * cm
_LHGT   = 13
_CPAD   = 0.32 * cm
_FSM    = 7.5
_FTT    = 8.5


def _v(d: dict, k: str) -> str:
    v = d.get(k)
    return "—" if (v is None or str(v).strip() == "") else str(v).strip()


def _fd(val) -> str:
    if val is None:
        return "—"
    if isinstance(val, (datetime, date)):
        return val.strftime("%d/%m/%Y")
    return str(val)


def _ff(val) -> str:
    if val is None:
        return "—"
    try:
        return f"{float(val):,.0f} GNF".replace(",", " ")
    except (TypeError, ValueError):
        return str(val)


class ResultatPDFService:

    @staticmethod
    def generer(data: dict, info_cabinet: dict, chemin_pdf: str) -> str:
        """Génère la fiche PDF au chemin indiqué et renvoie ce chemin."""
        dname = os.path.dirname(chemin_pdf)
        if dname:
            os.makedirs(dname, exist_ok=True)

        c = pdf_canvas.Canvas(chemin_pdf, pagesize=A5)
        d = data
        ts    = d.get("type_source", "")
        accent = {"consultation": _BLEU, "examen": _VIOLET, "chirurgie": _ROUGE}.get(ts, _VERT)
        nom_cab    = info_cabinet.get("nom_cabinet", "CLINIQUE")
        adresse    = info_cabinet.get("adresse", info_cabinet.get("adresse_cabinet", ""))
        logo_path  = info_cabinet.get("logo", info_cabinet.get("logo_url", ""))

        r, g, b = accent.red, accent.green, accent.blue
        c.setFillColor(colors.Color(r * 0.04 + 0.96, g * 0.04 + 0.96, b * 0.04 + 0.96))
        c.rect(0, 0, _W, _H, fill=1, stroke=0)

        c.setStrokeColor(accent)
        c.setLineWidth(1.8)
        c.roundRect(_FRAME, _FRAME, _W - 2*_FRAME, _H - 2*_FRAME, 9, fill=0, stroke=1)
        c.setStrokeColor(_BORD)
        c.setLineWidth(0.5)
        c.roundRect(_FRAME + 3.5, _FRAME + 3.5,
                    _W - 2*(_FRAME + 3.5), _H - 2*(_FRAME + 3.5), 7, fill=0, stroke=1)

        c.setFillColor(_WHITE)
        c.roundRect(_FRAME + 5, _FRAME + 5,
                    _W - 2*(_FRAME + 5), _H - 2*(_FRAME + 5), 6, fill=1, stroke=0)

        if logo_path and os.path.exists(logo_path):
            c.saveState()
            c.setFillAlpha(0.06)
            ts_logo = 5.5 * cm
            c.drawImage(logo_path, (_W - ts_logo)/2, (_H - ts_logo)/2,
                        width=ts_logo, height=ts_logo, mask="auto")
            c.restoreState()

        lx  = _FRAME + _MX
        top = _H - _FRAME - 0.30 * cm

        if logo_path and os.path.exists(logo_path):
            c.drawImage(logo_path, lx, top - 0.95*cm,
                        width=0.90*cm, height=0.90*cm, mask="auto")
            tx = lx + 1.00 * cm
        else:
            tx = lx

        c.setFillColor(accent)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(tx, top - 0.32*cm, nom_cab.upper())
        c.setFillColor(_GREY)
        c.setFont("Helvetica", 7)
        c.drawString(tx, top - 0.58*cm, adresse)
        c.setFont("Helvetica", 6.5)
        c.drawRightString(_W - _FRAME - _MX, top - 0.32*cm,
                          f"Imprimé le {datetime.now().strftime('%d/%m/%Y %H:%M')}")

        sep_hdr = top - 1.15 * cm
        c.setStrokeColor(accent)
        c.setLineWidth(1.0)
        c.line(lx, sep_hdr, _W - _FRAME - _MX, sep_hdr)

        y = sep_hdr - 0.20 * cm
        c.setFillColor(colors.Color(r * 0.14 + 0.86, g * 0.14 + 0.86, b * 0.14 + 0.86))
        c.roundRect(lx, y - 18, _W - 2*(_FRAME + _MX), 20, 3, fill=1, stroke=0)
        c.setFillColor(accent)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(_W / 2, y - 12,
                            f"FICHE RÉSULTAT MÉDICAL  ·  {ts.upper()}")
        y -= 26

        def _sec_bar(xi, yi, title, col):
            bar = 3
            c.setFillColor(col)
            c.setStrokeColor(col)
            c.roundRect(xi, yi, bar, _FTT + 3, 1, fill=1, stroke=0)
            c.setFont("Helvetica-Bold", _FTT)
            c.drawString(xi + bar + 5, yi + 1, title.upper())
            c.setStrokeColor(_BORD)
            c.setLineWidth(0.5)
            c.line(xi, yi - 4, xi + _COL_W - 2*_CPAD - 4, yi - 4)
            return yi - 4

        def _frow(xi, yi, label, val):
            c.setFillColor(_GREY)
            c.setFont("Helvetica-Bold", _FSM)
            c.drawString(xi, yi, f"{label} :")
            c.setFillColor(_DARK)
            c.setFont("Helvetica", _FSM)
            max_c = max(10, int((_COL_W - _LBL_W - _CPAD - 4) / (_FSM * 0.50)))
            v = val if len(val) <= max_c else val[:max_c-1] + "…"
            c.drawString(xi + _LBL_W, yi, v)
            return yi - _LHGT

        def _draw_card(cx, cy, draw_fn, nb_rows):
            h = nb_rows * _LHGT + _FTT + 12 + int(2 * _CPAD) + 6
            h = max(h, 48)
            c.saveState()
            c.setFillColor(colors.Color(0.75, 0.75, 0.75, alpha=0.25))
            c.roundRect(cx + 2, cy - h - 1.5, _COL_W, h, 4, fill=1, stroke=0)
            c.setFillColor(_WHITE)
            c.setStrokeColor(_BORD)
            c.setLineWidth(0.5)
            c.roundRect(cx, cy - h, _COL_W, h, 4, fill=1, stroke=1)
            c.restoreState()
            draw_fn(cx + int(_CPAD) + 2, cy - int(_CPAD) - 4)
            return h

        x_l = lx
        x_r = lx + _COL_W + _LGAP
        nom_p   = (f"{_v(d,'p_nom')} {_v(d,'p_prenom')}").replace("— —", "—").strip() or "—"
        nom_per = (f"{_v(d,'per_nom')} {_v(d,'per_prenom')}").replace("— —", "—").strip() or "—"

        def _patient(xi, yi):
            yy = _sec_bar(xi, yi, "Patient", _BLEU)
            yy -= 2
            for lbl, val in [
                ("Nom",        nom_p),
                ("Tél",        _v(d, "p_tel")),
                ("Naissance",  _fd(d.get("p_naissance"))),
                ("Genre",      _v(d, "p_genre")),
                ("Profession", _v(d, "p_profession")),
                ("Adresse",    _v(d, "p_adresse")),
            ]:
                yy = _frow(xi, yy, lbl, val)

        def _personnel(xi, yi):
            yy = _sec_bar(xi, yi, "Personnel soignant", _VERT)
            yy -= 2
            for lbl, val in [
                ("Nom",      nom_per),
                ("Fonction", _v(d, "per_fonction")),
                ("Contact",  _v(d, "per_contact")),
            ]:
                yy = _frow(xi, yy, lbl, val)

        h1_l = _draw_card(x_l, y, _patient,   6)
        h1_r = _draw_card(x_r, y, _personnel,  3)
        y -= max(h1_l, h1_r) + 0.28 * cm

        if ts == "consultation":
            def _service(xi, yi):
                yy = _sec_bar(xi, yi, "Consultation", _BLEU)
                yy -= 2
                for lbl, val in [
                    ("Code",         _v(d, "code_consultation")),
                    ("Diagnostique", _v(d, "diagnostique")),
                    ("Frais",        _ff(d.get("frais_consultation"))),
                    ("Date",         _fd(d.get("date_consultation"))),
                    ("Session",      _v(d, "nom_session")),
                ]:
                    yy = _frow(xi, yy, lbl, val)
            nb_svc = 5
        elif ts == "examen":
            def _service(xi, yi):
                yy = _sec_bar(xi, yi, "Examen", _VIOLET)
                yy -= 2
                for lbl, val in [
                    ("Code acte",  _v(d, "code_acte_medical")),
                    ("Libellé",    _v(d, "libelle_examen")),
                    ("Décision",   _v(d, "decision_medicale")),
                    ("Frais",      _ff(d.get("frais_examen"))),
                    ("Date",       _fd(d.get("date_examen"))),
                    ("Conclusion", _v(d, "conclusion_medicale")),
                    ("Session",    _v(d, "nom_session")),
                ]:
                    yy = _frow(xi, yy, lbl, val)
            nb_svc = 7
        else:
            def _service(xi, yi):
                yy = _sec_bar(xi, yi, "Chirurgie", _ROUGE)
                yy -= 2
                for lbl, val in [
                    ("Code acte",   _v(d, "code_acte_medical")),
                    ("Libellé",     _v(d, "libelle_chururgie")),
                    ("Décision",    _v(d, "decision_medicale")),
                    ("Frais",       _ff(d.get("frais_chururgie"))),
                    ("Date",        _fd(d.get("date_chururgie"))),
                    ("Cpt. rendu",  _v(d, "compte_rendu_operatoire")),
                    ("Session",     _v(d, "nom_session")),
                ]:
                    yy = _frow(xi, yy, lbl, val)
            nb_svc = 7

        def _resultat(xi, yi):
            yy = _sec_bar(xi, yi, "Résultat médical", _VERT)
            yy -= 2
            for lbl, val in [
                ("ID Résultat",  _v(d, "id_resultat")),
                ("Type source",  _v(d, "type_source")),
                ("Fichier",      _v(d, "type_fichier")),
                ("Confident.",   _v(d, "niveau_confidentialite")),
                ("Date upload",  _fd(d.get("date_upload"))),
                ("Description",  _v(d, "description")),
            ]:
                yy = _frow(xi, yy, lbl, val)

        h2_l = _draw_card(x_l, y, _service,  nb_svc)
        h2_r = _draw_card(x_r, y, _resultat, 6)
        y -= max(h2_l, h2_r) + 0.28 * cm

        img_bytes = d.get("_img_bytes")
        if img_bytes:
            try:
                reader    = ImageReader(BytesIO(img_bytes))
                iw, ih    = reader.getSize()
                avail_w   = _W - 2 * (_FRAME + _MX)
                max_h     = min(3.5 * cm, y - _FRAME - _MY_BOT - 0.5 * cm)
                if max_h > 0.8 * cm:
                    ratio = min(avail_w / iw, max_h / ih)
                    dw, dh = iw * ratio, ih * ratio
                    ix = _FRAME + _MX + (avail_w - dw) / 2
                    iy = y - dh
                    c.setFillColor(colors.Color(0.97, 0.97, 0.97))
                    c.roundRect(ix - 4, iy - 4, dw + 8, dh + 8, 4, fill=1, stroke=0)
                    c.setStrokeColor(_BORD)
                    c.setLineWidth(0.7)
                    c.roundRect(ix - 4, iy - 4, dw + 8, dh + 8, 4, fill=0, stroke=1)
                    c.drawImage(reader, ix, iy, width=dw, height=dh,
                                mask="auto", preserveAspectRatio=True)
                    y -= dh + 0.25 * cm
            except Exception as e:
                print(f"[PDF image] {e}")

        fy = _FRAME + _MY_BOT - 0.05 * cm
        c.setStrokeColor(accent)
        c.setLineWidth(0.6)
        c.line(lx, fy, _W - _FRAME - _MX, fy)
        c.setFillColor(_GREY)
        c.setFont("Helvetica", 6.5)
        c.drawString(lx, fy - 8, f"Document généré par {nom_cab} — usage interne")
        c.drawRightString(_W - _FRAME - _MX, fy - 8, "Page 1 / 1")

        c.save()
        return chemin_pdf

    @staticmethod
    def generer_temp(data: dict, info_cabinet: dict) -> str:
        """Génère dans un fichier temporaire et renvoie son chemin."""
        id_res = data.get("id_resultat", "resultat").replace("/", "_")
        fd, path = tempfile.mkstemp(prefix=f"res_{id_res}_", suffix=".pdf")
        os.close(fd)
        return ResultatPDFService.generer(data, info_cabinet, path)
