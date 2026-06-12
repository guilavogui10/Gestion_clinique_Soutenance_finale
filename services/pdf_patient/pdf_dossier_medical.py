"""
pdf_dossier_medical.py
─────────────────────────────────────────────────────────────────────────────
Génère un dossier médical complet multi-pages pour un patient.

Structure :
  Page 1  — Couverture (page de garde)
  Page 2  — Historique des visites
  Page 3  — Consultations réalisées
  Page 4  — Examens médicaux
  Page 5  — Chirurgies
  Page 6  — Prescriptions médicales
  Page 7  — Commandes de lunettes
  Page 8  — Rendez-vous
  Dernière — Synthèse médicale
"""
import os
import tempfile
from collections import defaultdict
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether,
)

# ══════════════════════════════════════════════════════════════════════════════
# PALETTE
# ══════════════════════════════════════════════════════════════════════════════
_B   = colors.Color(0.10, 0.25, 0.63)   # bleu principal
_BL  = colors.Color(0.90, 0.93, 1.00)   # bleu très clair
_BM  = colors.Color(0.55, 0.70, 0.95)   # bleu moyen
_V   = colors.Color(0.06, 0.50, 0.30)   # vert (examens)
_VL  = colors.Color(0.87, 0.97, 0.91)   # vert clair
_O   = colors.Color(0.80, 0.42, 0.05)   # orange (chirurgies)
_OL  = colors.Color(1.00, 0.94, 0.86)   # orange clair
_P   = colors.Color(0.42, 0.18, 0.68)   # violet (prescriptions)
_PL  = colors.Color(0.95, 0.90, 1.00)   # violet clair
_T   = colors.Color(0.05, 0.50, 0.60)   # teal (lunettes)
_TL  = colors.Color(0.88, 0.97, 1.00)   # teal clair
_RD  = colors.Color(0.65, 0.10, 0.10)   # rouge (rendez-vous)
_RL  = colors.Color(1.00, 0.91, 0.91)   # rouge clair
_GR  = colors.Color(0.45, 0.45, 0.45)   # gris texte
_GRL = colors.Color(0.96, 0.96, 0.97)   # gris clair
_W   = colors.white
_K   = colors.black


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _s(obj, *keys, d='-'):
    """Lit un champ depuis dict ou objet-modèle, essaie plusieurs clés."""
    for k in keys:
        if obj is None:
            continue
        if isinstance(obj, dict):
            v = obj.get(k)
        else:
            v = getattr(obj, k, None)
            if v is None:
                fn = getattr(obj, f'get_{k}', None)
                if fn:
                    try:
                        v = fn()
                    except Exception:
                        v = None
        if v is not None and str(v).strip() not in ('', 'None'):
            return str(v).strip()
    return d


def _f(obj, key, d=0.0):
    v = obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)
    if v is None:
        return d
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def _date(obj, *keys, d='-'):
    for k in keys:
        if obj is None:
            continue
        v = obj.get(k) if isinstance(obj, dict) else getattr(obj, k, None)
        if v is None:
            continue
        if hasattr(v, 'strftime'):
            return v.strftime('%d/%m/%Y')
        s = str(v).strip()
        if len(s) >= 10:
            return f"{s[8:10]}/{s[5:7]}/{s[:4]}" if s[4] == '-' else s[:10]
    return d


def _gnf(v):
    try:
        return f"{float(v):,.0f} GNF".replace(',', ' ')
    except Exception:
        return '0 GNF'


def _medecin(obj):
    pr = _s(obj, 'personnel_prenom', d='')
    nm = _s(obj, 'personnel_nom',    d='')
    full = f"{pr} {nm}".strip()
    return f"Dr. {full}" if full else '-'


# ══════════════════════════════════════════════════════════════════════════════
# STYLES
# ══════════════════════════════════════════════════════════════════════════════
def _mk_styles():
    base = getSampleStyleSheet()

    def p(name, parent='Normal', **kw):
        return ParagraphStyle(name, parent=base[parent], **kw)

    return {
        'sec_title':  p('DmST', fontSize=11, textColor=_W, fontName='Helvetica-Bold',
                         spaceAfter=0, spaceBefore=0, leftIndent=8),
        'card_title': p('DmCT', fontSize=10, fontName='Helvetica-Bold', textColor=_B, spaceAfter=2),
        'label':      p('DmLB', fontSize=8,  fontName='Helvetica-Bold', textColor=_GR),
        'value':      p('DmVL', fontSize=9,  fontName='Helvetica',      textColor=_K),
        'tbl_hdr':    p('DmTH', fontSize=8,  fontName='Helvetica-Bold', textColor=_W),
        'tbl_cell':   p('DmTC', fontSize=8,  leading=10),
        'tbl_total':  p('DmTT', fontSize=8,  fontName='Helvetica-Bold', textColor=_B),
        'empty':      p('DmEM', fontSize=10, textColor=_GR, alignment=TA_CENTER, spaceAfter=12),
        'syn_label':  p('DmSL', fontSize=9,  fontName='Helvetica-Bold', textColor=_B),
        'syn_value':  p('DmSV', fontSize=9,  fontName='Helvetica',      textColor=_K),
    }


# ══════════════════════════════════════════════════════════════════════════════
# CANVAS — PAGE DE GARDE  (fond blanc, texte bleu, bordure décorative)
# ══════════════════════════════════════════════════════════════════════════════
def _dessiner_couverture(c, W, H, patient, info_cabinet, stats):
    nom_cab   = info_cabinet.get('nom_cabinet', 'CABINET OPHTALMOLOGIQUE').upper()
    adr_cab   = info_cabinet.get('adresse_cabinet', '')
    logo_path = info_cabinet.get('logo')

    # ── Fond blanc ─────────────────────────────────────────────────────────
    c.setFillColor(_W)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # ── Bordure décorative double (cadre de page) ──────────────────────────
    marge = 0.7*cm
    c.setStrokeColor(_B)
    c.setLineWidth(2.0)
    c.rect(marge, marge, W - 2*marge, H - 2*marge, fill=0, stroke=1)

    c.setStrokeColor(_BM)
    c.setLineWidth(0.6)
    inner = marge + 0.2*cm
    c.rect(inner, inner, W - 2*inner, H - 2*inner, fill=0, stroke=1)

    # ── Logo (haut gauche dans le cadre) ──────────────────────────────────
    if logo_path and os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, marge + 0.5*cm, H - marge - 3.2*cm,
                        width=2.5*cm, height=2.5*cm, mask='auto')
        except Exception:
            pass

    # ── Nom du cabinet (en-tête centré) ───────────────────────────────────
    c.setFillColor(_B)
    c.setFont('Helvetica-Bold', 16)
    c.drawCentredString(W / 2, H - marge - 1.4*cm, nom_cab)

    if adr_cab:
        c.setFillColor(_GR)
        c.setFont('Helvetica', 8.5)
        c.drawCentredString(W / 2, H - marge - 2.0*cm, adr_cab)

    # Ligne déco sous l'en-tête
    c.setStrokeColor(_BM)
    c.setLineWidth(0.8)
    c.line(marge + 0.5*cm, H - marge - 2.5*cm, W - marge - 0.5*cm, H - marge - 2.5*cm)

    # ── Titre principal ────────────────────────────────────────────────────
    c.setFillColor(_B)
    c.setFont('Helvetica-Bold', 20)
    c.drawCentredString(W / 2, H - marge - 4.0*cm, 'DOSSIER MÉDICAL DU PATIENT')

    # Ligne déco sous le titre
    title_line_y = H - marge - 4.5*cm
    c.setStrokeColor(_B)
    c.setLineWidth(1.2)
    c.line(W / 2 - 5*cm, title_line_y, W / 2 + 5*cm, title_line_y)

    # ── Avatar initiales (cercle avec contour bleu) ────────────────────────
    cx, cy = W / 2, H - marge - 7.0*cm
    c.setFillColor(_BL)
    c.setStrokeColor(_B)
    c.setLineWidth(1.5)
    c.circle(cx, cy, 1.5*cm, fill=1, stroke=1)
    c.setFillColor(_B)
    c.setFont('Helvetica-Bold', 22)
    init = (_s(patient, 'prenom', d='?')[0] + _s(patient, 'nom', d='?')[0]).upper()
    c.drawCentredString(cx, cy - 8, init)

    # Nom complet patient sous l'avatar
    nom_complet = f"{_s(patient, 'prenom', d='')} {_s(patient, 'nom', d='')}".strip() or '-'
    c.setFillColor(_B)
    c.setFont('Helvetica-Bold', 14)
    c.drawCentredString(W / 2, H - marge - 9.2*cm, nom_complet)

    # ── Séparateur ─────────────────────────────────────────────────────────
    sep_y = H - marge - 9.8*cm
    c.setStrokeColor(_BM)
    c.setLineWidth(0.5)
    c.line(marge + 1*cm, sep_y, W - marge - 1*cm, sep_y)

    # ── Carte infos patient (fond très léger, bordure bleue) ───────────────
    card_top  = sep_y - 0.3*cm
    cw        = W - 2*marge - 1.2*cm
    ch        = 5.6*cm
    cx_card   = marge + 0.6*cm

    c.setFillColor(colors.Color(0.97, 0.98, 1.0))
    c.setStrokeColor(_BM)
    c.setLineWidth(0.7)
    c.roundRect(cx_card, card_top - ch, cw, ch, 6, fill=1, stroke=1)

    # Titre section
    c.setFillColor(_B)
    c.setFont('Helvetica-Bold', 8.5)
    c.drawString(cx_card + 0.4*cm, card_top - 0.60*cm, 'INFORMATIONS DU PATIENT')
    c.setStrokeColor(_BL)
    c.setLineWidth(0.4)
    c.line(cx_card + 0.3*cm, card_top - 0.80*cm,
           cx_card + cw - 0.3*cm, card_top - 0.80*cm)

    champs = [
        ('Code patient',   _s(patient, 'code_patient', 'code', d='-')),
        ('Nom',            _s(patient, 'nom',           d='-')),
        ('Prénom',         _s(patient, 'prenom',        d='-')),
        ('Sexe / Genre',   _s(patient, 'genre', 'sexe', d='-')),
        ('Date naissance', _date(patient, 'naissance', 'date_naissance', d='-')),
        ('Téléphone',      _s(patient, 'telephone', 'contact', d='-')),
        ('Adresse',        _s(patient, 'adresse',       d='-')),
        ('Profession',     _s(patient, 'profession',    d='-')),
    ]

    half    = (cw - 1.0*cm) / 2
    x1      = cx_card + 0.5*cm
    x2      = x1 + half + 0.2*cm
    y_start = card_top - 1.20*cm
    row_h   = 0.68*cm

    for i, (lbl, val) in enumerate(champs):
        x = x1 if i % 2 == 0 else x2
        y = y_start - (i // 2) * row_h
        c.setFillColor(_GR)
        c.setFont('Helvetica-Bold', 6.5)
        c.drawString(x, y, lbl.upper())
        c.setFillColor(_K)
        c.setFont('Helvetica', 8.5)
        val_s = (val[:30] + '…') if len(val) > 30 else val
        c.drawString(x, y - 0.26*cm, val_s)

    # ── Statistiques (fond blanc, bordure colorée) ─────────────────────────
    stats_top  = card_top - ch - 0.5*cm
    stat_items = [
        ('Visites',       stats.get('nb_visites', 0),       _B),
        ('Consultations', stats.get('nb_consultations', 0), _V),
        ('Examens',       stats.get('nb_examens', 0),       _O),
        ('Chirurgies',    stats.get('nb_chirurgies', 0),    _P),
        ('Prescriptions', stats.get('nb_prescriptions', 0), _T),
        ('Lunettes',      stats.get('nb_lunettes', 0),      _RD),
    ]
    n  = len(stat_items)
    bw = (W - 2*marge - 1.2*cm) / n
    bh = 1.8*cm

    for i, (lbl, cnt, col) in enumerate(stat_items):
        bx = cx_card + i * bw
        by = stats_top - bh

        light = colors.Color(col.red * 0.10 + 0.90,
                              col.green * 0.10 + 0.90,
                              col.blue * 0.10 + 0.90)
        c.setFillColor(light)
        c.setStrokeColor(col)
        c.setLineWidth(0.8)
        c.roundRect(bx + 0.1*cm, by, bw - 0.2*cm, bh, 5, fill=1, stroke=1)

        c.setFillColor(col)
        c.setFont('Helvetica-Bold', 16)
        c.drawCentredString(bx + bw / 2, by + bh - 0.85*cm, str(cnt))

        c.setFillColor(_GR)
        c.setFont('Helvetica', 6.5)
        c.drawCentredString(bx + bw / 2, by + 0.22*cm, lbl)

    # ── Date d'impression ──────────────────────────────────────────────────
    c.setFillColor(_GR)
    c.setFont('Helvetica-Oblique', 7.5)
    c.drawCentredString(W / 2, marge + 0.9*cm,
                        f"Dossier imprimé le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")

    c.setFillColor(_B)
    c.setFont('Helvetica-Bold', 6.5)
    c.drawCentredString(W / 2, marge + 0.3*cm,
                        '— DOCUMENT CONFIDENTIEL — USAGE MÉDICAL UNIQUEMENT —')


# ══════════════════════════════════════════════════════════════════════════════
# CANVAS — EN-TÊTE PAGES INTÉRIEURES
# ══════════════════════════════════════════════════════════════════════════════
def _dessiner_entete(c, W, H, info_cabinet):
    nom_cab   = info_cabinet.get('nom_cabinet', 'CABINET').upper()
    adr_cab   = info_cabinet.get('adresse_cabinet', '')
    logo_path = info_cabinet.get('logo')

    c.setFillColor(_B)
    c.setFont('Helvetica-Bold', 10)
    c.drawString(0.6*cm, H - 1.1*cm, nom_cab)

    if adr_cab:
        c.setFillColor(_GR)
        c.setFont('Helvetica', 7)
        c.drawString(0.6*cm, H - 1.6*cm, adr_cab)

    c.setFillColor(_B)
    c.setFont('Helvetica-Bold', 8)
    c.drawRightString(W - 0.6*cm, H - 1.1*cm, 'DOSSIER MÉDICAL')

    c.setFillColor(_GR)
    c.setFont('Helvetica', 7)
    c.drawRightString(W - 0.6*cm, H - 1.6*cm, f"Page {c.getPageNumber()}")

    if logo_path and os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, W - 2.5*cm, H - 2.3*cm,
                        width=1.5*cm, height=1.5*cm, mask='auto')
        except Exception:
            pass

    c.setStrokeColor(_B)
    c.setLineWidth(1.5)
    c.line(0.6*cm, H - 2.2*cm, W - 0.6*cm, H - 2.2*cm)


# ══════════════════════════════════════════════════════════════════════════════
# BUILDERS DE SECTION
# ══════════════════════════════════════════════════════════════════════════════
_CW = 17.5 * cm   # largeur totale des tableaux


def _bandeau(titre, couleur, st):
    tbl = Table([[Paragraph(titre, st['sec_title'])]], colWidths=[_CW])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), couleur),
        ('TOPPADDING',    (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
    ]))
    return tbl


def _card_table(pairs, bg_lbl, bg_val, border_col, st):
    """Tableau 2 colonnes Label | Valeur pour une card."""
    rows = []
    for lbl, val in pairs:
        rows.append([
            Paragraph(lbl, st['label']),
            Paragraph(str(val) if val else '-', st['value']),
        ])
    tbl = Table(rows, colWidths=[4.5*cm, 13.0*cm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (0, -1),  bg_lbl),
        ('BACKGROUND',    (1, 0), (1, -1),  bg_val),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW',     (0, 0), (-1, -2), 0.4, border_col),
        ('BOX',           (0, 0), (-1, -1), 0.8, border_col),
    ]))
    return tbl


# ─────────────────────────────────────────────────────────────────────────────
def _section_visites(visites, st):
    elts = [_bandeau('HISTORIQUE DES VISITES', _B, st), Spacer(1, 0.3*cm)]

    if not visites:
        elts.append(Paragraph("Aucune visite enregistrée.", st['empty']))
        return elts

    hdr = [Paragraph(f'<b>{h}</b>', st['tbl_hdr'])
           for h in ('Code', 'Date', 'Type', 'Motif', 'Urgent', 'Statut')]
    cw  = [2.5*cm, 2.5*cm, 2.8*cm, 5.2*cm, 1.8*cm, 2.7*cm]
    rows = [hdr]

    for v in visites:
        rows.append([
            Paragraph(_s(v, 'code_visite', 'code',       d='-'), st['tbl_cell']),
            Paragraph(_date(v, 'date_visite',             d='-'), st['tbl_cell']),
            Paragraph(_s(v, 'type_visite',                d='-'), st['tbl_cell']),
            Paragraph(_s(v, 'motif_visite', 'motif',      d='-'), st['tbl_cell']),
            Paragraph(_s(v, 'urgent',                     d='-'), st['tbl_cell']),
            Paragraph(_s(v, 'statut_visite', 'statut',   d='-'), st['tbl_cell']),
        ])

    tbl = Table(rows, colWidths=cw, repeatRows=1)
    _style_tableau(tbl, _B, len(rows))
    elts.append(tbl)
    elts.append(Spacer(1, 0.4*cm))
    return elts


# ─────────────────────────────────────────────────────────────────────────────
def _section_consultations(consultations, st):
    elts = [_bandeau('CONSULTATIONS RÉALISÉES', _B, st), Spacer(1, 0.3*cm)]

    if not consultations:
        elts.append(Paragraph("Aucune consultation enregistrée.", st['empty']))
        return elts

    for c in consultations:
        code  = _s(c, 'code', 'code_consultation',              d='-')
        date  = _date(c, 'date_consultation',                    d='-')
        med   = _medecin(c)
        typ   = _s(c, 'type_consultation',                       d='-')
        frais = _gnf(_f(c, 'frais_consultation'))
        diag  = _s(c, 'diagnostique', 'diagnostic',             d='-')
        obs   = _s(c, 'observation', 'notes_medical',           d='')

        pairs = [
            ('Code',         code),
            ('Date',         date),
            ('Médecin',      med),
            ('Type',         typ),
            ('Frais',        frais),
            ('Diagnostic',   diag),
        ]
        if obs and obs != '-':
            pairs.append(('Observation', obs))

        title = Paragraph(f"Consultation <b>{code}</b> — {date}", st['card_title'])
        tbl   = _card_table(pairs, _BL, _W, _BM, st)
        elts.append(KeepTogether([title, Spacer(1, 0.1*cm), tbl, Spacer(1, 0.35*cm)]))

    return elts


# ─────────────────────────────────────────────────────────────────────────────
def _section_examens(examens, st):
    elts = [_bandeau('EXAMENS MÉDICAUX', _V, st), Spacer(1, 0.3*cm)]

    if not examens:
        elts.append(Paragraph("Aucun examen enregistré.", st['empty']))
        return elts

    for ex in examens:
        code    = _s(ex, 'code', 'code_examen',              d='-')
        date    = _date(ex, 'date_examen',                    d='-')
        libelle = _s(ex, 'libelle_examen', 'libelle',        d='-')
        med     = _medecin(ex)
        frais   = _gnf(_f(ex, 'frais_examen'))
        conclu  = _s(ex, 'conclusion_medicale', 'conclusion', d='')
        statut  = _s(ex, 'statut_facture',                   d='-')

        pairs = [
            ('Code',        code),
            ('Date',        date),
            ('Type',        libelle),
            ('Médecin',     med),
            ('Frais',       frais),
            ('Statut fact.', statut),
        ]
        if conclu and conclu != '-':
            pairs.append(('Conclusion', conclu))

        title = Paragraph(f"Examen <b>{code}</b> — {libelle} — {date}", st['card_title'])
        tbl   = _card_table(pairs, _VL, _W, _V, st)
        elts.append(KeepTogether([title, Spacer(1, 0.1*cm), tbl, Spacer(1, 0.35*cm)]))

    return elts


# ─────────────────────────────────────────────────────────────────────────────
def _section_chirurgies(chirurgies, st):
    elts = [_bandeau('CHIRURGIES', _O, st), Spacer(1, 0.3*cm)]

    if not chirurgies:
        elts.append(Paragraph("Aucune chirurgie enregistrée.", st['empty']))
        return elts

    for ch in chirurgies:
        code    = _s(ch, 'code', 'code_chururgie', 'code_chirurgie', d='-')
        date    = _date(ch, 'date_chururgie', 'date_chirurgie',      d='-')
        libelle = _s(ch, 'libelle_chururgie', 'libelle_chirurgie', 'libelle', d='-')
        chir    = _medecin(ch)
        frais   = _gnf(_f(ch, 'frais_chururgie', d=0.0))
        cr      = _s(ch, 'compte_rendu_operatoire', 'compte_rendu',  d='')
        suivi   = _s(ch, 'suivi_postoperatoire', 'suivi',            d='')
        statut  = _s(ch, 'statut_facture',                           d='-')

        pairs = [
            ('Code',      code),
            ('Date',      date),
            ('Type',      libelle),
            ('Chirurgien', chir),
            ('Frais',     frais),
            ('Statut',    statut),
        ]
        if cr and cr != '-':
            pairs.append(('Compte rendu', cr))
        if suivi and suivi != '-':
            pairs.append(('Suivi post-op', suivi))

        title = Paragraph(f"Chirurgie <b>{code}</b> — {libelle} — {date}", st['card_title'])
        tbl   = _card_table(pairs, _OL, _W, _O, st)
        elts.append(KeepTogether([title, Spacer(1, 0.1*cm), tbl, Spacer(1, 0.35*cm)]))

    return elts


# ─────────────────────────────────────────────────────────────────────────────
def _section_prescriptions(prescriptions, st):
    """Groupe les lignes par code_acte (1 acte = 1 ordonnance)."""
    elts = [_bandeau('PRESCRIPTIONS MÉDICALES', _P, st), Spacer(1, 0.3*cm)]

    if not prescriptions:
        elts.append(Paragraph("Aucune prescription enregistrée.", st['empty']))
        return elts

    groupes = defaultdict(list)
    for p in prescriptions:
        key = _s(p, 'code_acte', d='—')
        groupes[key].append(p)

    for code_acte, lignes in groupes.items():
        premiere = lignes[0]
        date     = _date(premiere, 'date_creation', 'date_commande', d='-')

        hdr_row = [Paragraph(f'<b>{h}</b>', st['tbl_hdr'])
                   for h in ('Produit / Désignation', 'Quantité', 'Prix unitaire', 'Total')]
        cw_p    = [8.0*cm, 2.5*cm, 3.0*cm, 4.0*cm]
        rows    = [hdr_row]
        total   = 0.0

        for ligne in lignes:
            desig = _s(ligne, 'designation', 'nom_produit', d='-')
            qte   = _s(ligne, 'quantite_prescript', 'quantite', d='1')
            prix  = _f(ligne, 'prix_applique', 0.0)
            try:
                mont = float(qte) * prix
            except Exception:
                mont = 0.0
            total += mont
            rows.append([
                Paragraph(desig,       st['tbl_cell']),
                Paragraph(qte,         st['tbl_cell']),
                Paragraph(_gnf(prix),  st['tbl_cell']),
                Paragraph(_gnf(mont),  st['tbl_cell']),
            ])

        nb   = len(rows)
        tot_row = ['', '', '', Paragraph(f"<b>{_gnf(total)}</b>", st['tbl_total'])]
        rows.append(tot_row)

        tbl = Table(rows, colWidths=cw_p, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0),  (-1, 0),      _P),
            ('TEXTCOLOR',     (0, 0),  (-1, 0),      _W),
            ('ALIGN',         (0, 0),  (-1, -1),     'LEFT'),
            ('VALIGN',        (0, 0),  (-1, -1),     'TOP'),
            ('TOPPADDING',    (0, 0),  (-1, -1),     4),
            ('BOTTOMPADDING', (0, 0),  (-1, -1),     4),
            ('LEFTPADDING',   (0, 0),  (-1, -1),     6),
            ('RIGHTPADDING',  (0, 0),  (-1, -1),     6),
            ('BACKGROUND',    (0, 1),  (-1, nb - 1), _PL),
            ('LINEBELOW',     (0, 0),  (-1, 0),      1,   _P),
            ('LINEBELOW',     (0, 1),  (-1, nb - 1), 0.4, colors.Color(0.85, 0.80, 0.95)),
            ('BACKGROUND',    (0, -1), (-1, -1),     colors.Color(0.92, 0.88, 0.98)),
            ('ALIGN',         (3, -1), (3, -1),      'RIGHT'),
            ('BOX',           (0, 0),  (-1, -1),     0.8, colors.Color(0.85, 0.80, 0.95)),
        ]))

        title = Paragraph(
            f"Ordonnance — Acte <b>{code_acte}</b> — {date} "
            f"({len(lignes)} produit{'s' if len(lignes) > 1 else ''})",
            st['card_title']
        )
        elts.append(KeepTogether([title, Spacer(1, 0.1*cm), tbl, Spacer(1, 0.35*cm)]))

    return elts


# ─────────────────────────────────────────────────────────────────────────────
def _section_lunettes(lunettes, st):
    elts = [_bandeau('COMMANDES DE LUNETTES', _T, st), Spacer(1, 0.3*cm)]

    if not lunettes:
        elts.append(Paragraph("Aucune commande de lunettes enregistrée.", st['empty']))
        return elts

    for lun in lunettes:
        code     = _s(lun, 'code', 'code_commande',                d='-')
        date_cmd = _date(lun, 'date_commande',                      d='-')
        date_liv = _date(lun, 'date_livraison',                     d='-')
        cadre    = _s(lun, 'numero_cadre', 'cadre',                d='-')
        verre    = _s(lun, 'numero_verre', 'verre',                d='-')
        prix     = _gnf(_f(lun, 'prix', 0.0))
        statut   = _s(lun, 'statut_facture', 'statut',             d='-')
        med      = _medecin(lun)

        pairs = [
            ('Code',           code),
            ('Date commande',  date_cmd),
            ('N° cadre',       cadre),
            ('N° verre',       verre),
            ('Prix',           prix),
            ('Date livraison', date_liv),
            ('Médecin',        med),
            ('Statut',         statut),
        ]

        title = Paragraph(f"Commande <b>{code}</b> — {date_cmd}", st['card_title'])
        tbl   = _card_table(pairs, _TL, _W, _T, st)
        elts.append(KeepTogether([title, Spacer(1, 0.1*cm), tbl, Spacer(1, 0.35*cm)]))

    return elts


# ─────────────────────────────────────────────────────────────────────────────
def _section_rendez_vous(rdvs, st):
    elts = [_bandeau('RENDEZ-VOUS', _RD, st), Spacer(1, 0.3*cm)]

    if not rdvs:
        elts.append(Paragraph("Aucun rendez-vous enregistré.", st['empty']))
        return elts

    hdr = [Paragraph(f'<b>{h}</b>', st['tbl_hdr'])
           for h in ('Code', 'Date', 'Motif', 'Personnel', 'Statut')]
    cw  = [2.5*cm, 2.8*cm, 5.5*cm, 4.5*cm, 2.2*cm]
    rows = [hdr]

    for r in rdvs:
        rows.append([
            Paragraph(_s(r, 'code_rendez_vous', 'code',         d='-'), st['tbl_cell']),
            Paragraph(_date(r, 'date_rendez_vous',               d='-'), st['tbl_cell']),
            Paragraph(_s(r, 'motif_rendez_vous', 'motif',       d='-'), st['tbl_cell']),
            Paragraph(_medecin(r),                                        st['tbl_cell']),
            Paragraph(_s(r, 'statut_rendez_vous', 'statut',     d='-'), st['tbl_cell']),
        ])

    tbl = Table(rows, colWidths=cw, repeatRows=1)
    _style_tableau(tbl, _RD, len(rows))
    elts.append(tbl)
    elts.append(Spacer(1, 0.4*cm))
    return elts


# ─────────────────────────────────────────────────────────────────────────────
def _section_synthese(patient, consultations, examens, chirurgies,
                       prescriptions, lunettes, rendez_vous, st):
    elts = [_bandeau('SYNTHÈSE MÉDICALE', _B, st), Spacer(1, 0.4*cm)]

    def _last(lst, date_key, *fields):
        if not lst:
            return None
        try:
            return sorted(lst, key=lambda x: _date(x, date_key, d='01/01/1900'), reverse=True)[0]
        except Exception:
            return lst[-1]

    dern_c   = _last(consultations, 'date_consultation')
    dern_ex  = _last(examens,       'date_examen')
    dern_ch  = _last(chirurgies,    'date_chururgie', 'date_chirurgie')
    dern_p   = _last(prescriptions, 'date_creation', 'date_commande')
    dern_lun = _last(lunettes,      'date_commande')
    dern_rdv = _last(rendez_vous,   'date_rendez_vous')

    # Médecin référent = le plus fréquent dans consultations
    med_ref = '-'
    if consultations:
        cnt = defaultdict(int)
        for c in consultations:
            m = _medecin(c)
            if m != '-':
                cnt[m] += 1
        if cnt:
            med_ref = max(cnt, key=cnt.get)

    rows_syn = [
        ('Dernière consultation',
         f"{_date(dern_c, 'date_consultation', d='-')} — "
         f"{_s(dern_c, 'diagnostique', 'diagnostic', d='-')}" if dern_c else '-'),

        ('Médecin traitant', _medecin(dern_c) if dern_c else '-'),

        ('Dernier examen',
         f"{_date(dern_ex, 'date_examen', d='-')} — "
         f"{_s(dern_ex, 'libelle_examen', d='-')}" if dern_ex else '-'),

        ('Conclusion examen',
         _s(dern_ex, 'conclusion_medicale', 'conclusion', d='-') if dern_ex else '-'),

        ('Dernière chirurgie',
         f"{_date(dern_ch, 'date_chururgie', 'date_chirurgie', d='-')} — "
         f"{_s(dern_ch, 'libelle_chururgie', 'libelle', d='-')}" if dern_ch else '-'),

        ('Dernière prescription',
         f"{_date(dern_p, 'date_creation', 'date_commande', d='-')} — "
         f"{_s(dern_p, 'designation', d='-')}" if dern_p else '-'),

        ('Dernière commande lunettes',
         f"{_date(dern_lun, 'date_commande', d='-')} — "
         f"Statut : {_s(dern_lun, 'statut_facture', 'statut', d='-')}" if dern_lun else '-'),

        ('Prochain rendez-vous',
         f"{_date(dern_rdv, 'date_rendez_vous', d='-')} — "
         f"{_s(dern_rdv, 'statut_rendez_vous', 'statut', d='-')}" if dern_rdv else '-'),

        ('Médecin référent', med_ref),
    ]

    tbl_rows = []
    for lbl, val in rows_syn:
        tbl_rows.append([
            Paragraph(lbl, st['syn_label']),
            Paragraph(str(val), st['syn_value']),
        ])

    tbl = Table(tbl_rows, colWidths=[5.0*cm, 12.5*cm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (0, -1), _BL),
        ('BACKGROUND',    (1, 0), (1, -1), _W),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW',     (0, 0), (-1, -1), 0.5, _BM),
        ('BOX',           (0, 0), (-1, -1), 0.8, _BM),
    ]))
    elts.append(tbl)
    elts.append(Spacer(1, 1.2*cm))

    # Zone de signature
    sig_rows = [
        [Paragraph('<b>Médecin traitant</b>', st['syn_label']),
         Paragraph('<b>Cachet du cabinet</b>', st['syn_label'])],
        [Paragraph('Signature : ________________________________', st['syn_value']),
         Paragraph('Cachet : __________________________________', st['syn_value'])],
        [Spacer(1, 1.5*cm), Spacer(1, 1.5*cm)],
    ]
    sig_tbl = Table(sig_rows, colWidths=[8.75*cm, 8.75*cm])
    sig_tbl.setStyle(TableStyle([
        ('BOX',           (0, 0), (0, -1), 0.6, _GR),
        ('BOX',           (1, 0), (1, -1), 0.6, _GR),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING',   (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    elts.append(sig_tbl)
    return elts


# ══════════════════════════════════════════════════════════════════════════════
# UTILITAIRE STYLE TABLEAU STANDARD
# ══════════════════════════════════════════════════════════════════════════════
def _style_tableau(tbl, couleur_hdr, nb_rows):
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0),  (-1, 0),         couleur_hdr),
        ('TEXTCOLOR',     (0, 0),  (-1, 0),         _W),
        ('FONTNAME',      (0, 0),  (-1, 0),         'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0),  (-1, 0),         8),
        ('ALIGN',         (0, 0),  (-1, -1),        'LEFT'),
        ('VALIGN',        (0, 0),  (-1, -1),        'TOP'),
        ('TOPPADDING',    (0, 0),  (-1, -1),        5),
        ('BOTTOMPADDING', (0, 0),  (-1, -1),        5),
        ('LEFTPADDING',   (0, 0),  (-1, -1),        6),
        ('RIGHTPADDING',  (0, 0),  (-1, -1),        6),
        ('BACKGROUND',    (0, 1),  (-1, -1),        _GRL),
        ('LINEBELOW',     (0, 0),  (-1, 0),         1,   couleur_hdr),
        ('LINEBELOW',     (0, 1),  (-1, -1),        0.4, colors.Color(0.88, 0.88, 0.90)),
        ('BOX',           (0, 0),  (-1, -1),        0.8, colors.Color(0.88, 0.88, 0.90)),
    ]))


# ══════════════════════════════════════════════════════════════════════════════
# CLASSE PRINCIPALE
# ══════════════════════════════════════════════════════════════════════════════
class DossierMedicalPDF:
    """Génère le dossier médical complet d'un patient (PDF multi-pages)."""

    @staticmethod
    def generer(patient, visites, consultations, examens, chirurgies,
                prescriptions, lunettes, rendez_vous, info_cabinet,
                chemin_pdf=None):
        """
        Args:
            patient:       objet Patient ou dict
            visites:       list de dicts (lister_visites_patient)
            consultations: list de dicts/objets (obtenir_historique_patient)
            examens:       list de dicts/objets (obtenir_historique_patient)
            chirurgies:    list de dicts/objets (obtenir_historique_patient)
            prescriptions: list de dicts/objets PanierPrescriptionProduit
            lunettes:      list d'objets CommandeLunette (obtenir_historique_patient)
            rendez_vous:   list de dicts/objets RendezVous (obtenir_historique_patient)
            info_cabinet:  dict {'nom_cabinet', 'adresse_cabinet', 'logo'}
            chemin_pdf:    chemin de sortie (None = fichier temporaire)
        Returns:
            str: chemin du fichier PDF généré
        """
        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix='.pdf', prefix='dossier_medical_')
            os.close(fd)

        W, H = A4
        st   = _mk_styles()

        # Nombre d'ordonnances = nombre de code_acte distincts
        codes_actes_presc = {
            _s(p, 'code_acte', d='') for p in (prescriptions or [])
            if _s(p, 'code_acte', d='')
        }
        stats = {
            'nb_visites':       len(visites       or []),
            'nb_consultations': len(consultations or []),
            'nb_examens':       len(examens       or []),
            'nb_chirurgies':    len(chirurgies     or []),
            'nb_prescriptions': len(codes_actes_presc) or len(prescriptions or []),
            'nb_lunettes':      len(lunettes       or []),
        }

        doc = SimpleDocTemplate(
            chemin_pdf, pagesize=A4,
            leftMargin=1.5*cm, rightMargin=1.5*cm,
            topMargin=3.0*cm,  bottomMargin=1.5*cm,
        )

        # ── Assemblage ────────────────────────────────────────────────────
        elts = []

        # Page 1 : couverture (Spacer vide + PageBreak,
        #          tout est dessiné par onFirstPage sur le canvas)
        elts.append(Spacer(1, 0.001))
        elts.append(PageBreak())

        # Page 2 : Visites
        elts += _section_visites(visites or [], st)
        elts.append(PageBreak())

        # Page 3 : Consultations
        elts += _section_consultations(consultations or [], st)
        elts.append(PageBreak())

        # Page 4 : Examens
        elts += _section_examens(examens or [], st)
        elts.append(PageBreak())

        # Page 5 : Chirurgies
        elts += _section_chirurgies(chirurgies or [], st)
        elts.append(PageBreak())

        # Page 6 : Prescriptions
        elts += _section_prescriptions(prescriptions or [], st)
        elts.append(PageBreak())

        # Page 7 : Lunettes
        elts += _section_lunettes(lunettes or [], st)
        elts.append(PageBreak())

        # Page 8 : Rendez-vous
        elts += _section_rendez_vous(rendez_vous or [], st)
        elts.append(PageBreak())

        # Dernière page : Synthèse
        elts += _section_synthese(
            patient,
            consultations or [], examens    or [],
            chirurgies    or [], prescriptions or [],
            lunettes      or [], rendez_vous  or [],
            st
        )

        # ── Callbacks canvas ──────────────────────────────────────────────
        _pat, _cab, _st = patient, info_cabinet, stats

        def on_cover(c, doc):
            _dessiner_couverture(c, W, H, _pat, _cab, _st)

        def on_page(c, doc):
            _dessiner_entete(c, W, H, _cab)

        doc.build(elts, onFirstPage=on_cover, onLaterPages=on_page)
        return chemin_pdf
