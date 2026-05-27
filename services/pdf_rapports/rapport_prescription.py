from services.pdf_actes._base import (
    dessiner_entete_et_fond,
    A4, cm, colors, SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, getSampleStyleSheet, ParagraphStyle,
    datetime, os
)


def _get_str(row, key, default='-'):
    """Extrait une valeur d'un dict PyMySQL et la convertit en str proprement."""
    val = row.get(key) if isinstance(row, dict) else getattr(row, key, None)
    if val is None:
        return default
    return str(val)


def _get_float(row, key):
    """Extrait une valeur numérique (int/Decimal/float) depuis un dict PyMySQL."""
    val = row.get(key) if isinstance(row, dict) else getattr(row, key, None)
    if val is None:
        return 0.0
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _normalize_date(d):
    """Normalise une date en clé YYYY-MM-DD."""
    if not d:
        return ''
    if hasattr(d, 'date'):
        return d.date().strftime('%Y-%m-%d')
    if hasattr(d, 'strftime'):
        return d.strftime('%Y-%m-%d')
    s = str(d).strip()
    if len(s) >= 10:
        if s[2] == '/':
            return f"{s[6:10]}-{s[3:5]}-{s[:2]}"
        return s[:10]
    return s


def _key_to_display(k):
    if len(k) == 10 and k[4] == '-':
        return f"{k[8:10]}/{k[5:7]}/{k[:4]}"
    return k


class RapportPrescriptionPDF:

    @staticmethod
    def generer_pdf_prescriptions_par_date(groupes, info_cabinet, chemin_pdf=None):
        """Génère un PDF groupant toutes les prescriptions par date de consultation."""
        import tempfile
        from collections import defaultdict

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="rapport_prescriptions_")
            os.close(fd)

        grouped = defaultdict(list)
        for g in (groupes or []):
            key = _normalize_date(_get_str(g, 'date_consultation', ''))
            grouped[key].append(g)
        dates_triees = sorted(grouped.keys())

        doc = SimpleDocTemplate(
            chemin_pdf, pagesize=A4,
            leftMargin=1.5*cm, rightMargin=1.5*cm,
            topMargin=3*cm, bottomMargin=1.5*cm
        )
        styles = getSampleStyleSheet()
        elements = []

        bleu = colors.Color(0.15, 0.38, 0.93)

        titre_style = ParagraphStyle(
            'RptPrTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu
        )
        date_gen_style = ParagraphStyle(
            'RptPrDateGen', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        date_groupe_style = ParagraphStyle(
            'RptPrDateGroupe', parent=styles['Normal'],
            fontSize=11, fontName='Helvetica-Bold', textColor=bleu, spaceAfter=4
        )
        cell_style = ParagraphStyle(
            'RptPrCell', parent=styles['Normal'],
            fontSize=8, leading=10
        )
        header_cell_style = ParagraphStyle(
            'RptPrHdr', parent=styles['Normal'],
            fontSize=9, textColor=colors.white, fontName='Helvetica-Bold'
        )
        total_label_style = ParagraphStyle(
            'RptPrTotLbl', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold', textColor=bleu
        )
        total_val_style = ParagraphStyle(
            'RptPrTotVal', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold', textColor=bleu, alignment=2
        )

        elements.append(Paragraph("RAPPORT DES PRESCRIPTIONS", titre_style))
        elements.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            date_gen_style
        ))
        elements.append(Spacer(1, 0.4*cm))

        if not dates_triees:
            elements.append(Paragraph("Aucune prescription trouvée.", styles['Normal']))
        else:
            header_row = [
                Paragraph("<b>Code acte</b>",    header_cell_style),
                Paragraph("<b>Patient</b>",       header_cell_style),
                Paragraph("<b>Nb produits</b>",  header_cell_style),
                Paragraph("<b>Qté totale</b>",   header_cell_style),
                Paragraph("<b>Montant (GNF)</b>", header_cell_style),
            ]
            col_widths = [3.0*cm, 4.5*cm, 3.0*cm, 3.0*cm, 4.0*cm]

            for i, date_key in enumerate(dates_triees):
                groupe = grouped[date_key]
                date_affichee = _key_to_display(date_key) if date_key else "Date inconnue"
                elements.append(Paragraph(f"Date : {date_affichee}", date_groupe_style))

                data = [header_row[:]]
                cumul_montant = 0.0

                for g in groupe:
                    code_acte   = _get_str(g, 'code_acte', 'N/A')
                    nom         = _get_str(g, 'patient_nom', '')
                    prenom      = _get_str(g, 'patient_prenom', '')
                    patient     = f"{prenom} {nom}".strip() or 'N/A'
                    nb_produits = _get_str(g, 'nb_produits', '0')
                    qte_totale  = _get_str(g, 'total_quantite', '0')
                    montant     = _get_float(g, 'total_montant')
                    cumul_montant += montant
                    montant_fmt = f"{montant:,.0f}".replace(',', ' ')

                    data.append([
                        Paragraph(code_acte,    cell_style),
                        Paragraph(patient,      cell_style),
                        Paragraph(nb_produits,  cell_style),
                        Paragraph(qte_totale,   cell_style),
                        Paragraph(montant_fmt,  cell_style),
                    ])

                cumul_fmt = f"{cumul_montant:,.0f}".replace(',', ' ') + " GNF"
                data.append([
                    Paragraph(f"Total : {len(groupe)} ordonnance(s)", total_label_style),
                    '', '', '',
                    Paragraph(cumul_fmt, total_val_style),
                ])

                nb = len(data)
                tbl = Table(data, colWidths=col_widths, repeatRows=1)
                tbl.setStyle(TableStyle([
                    ('BACKGROUND',   (0, 0),  (-1, 0),      bleu),
                    ('TEXTCOLOR',    (0, 0),  (-1, 0),      colors.white),
                    ('FONTNAME',     (0, 0),  (-1, 0),      'Helvetica-Bold'),
                    ('FONTSIZE',     (0, 0),  (-1, 0),      9),
                    ('ALIGN',        (0, 0),  (-1, 0),      'CENTER'),
                    ('VALIGN',       (0, 0),  (-1, -1),     'TOP'),
                    ('LEFTPADDING',  (0, 0),  (-1, -1),     8),
                    ('RIGHTPADDING', (0, 0),  (-1, -1),     8),
                    ('TOPPADDING',   (0, 0),  (-1, -1),     6),
                    ('BOTTOMPADDING',(0, 0),  (-1, -1),     6),
                    ('BACKGROUND',   (0, 1),  (-1, nb - 2), colors.Color(0.98, 0.98, 0.99)),
                    ('LINEBELOW',    (0, 0),  (-1, 0),      1, bleu),
                    ('LINEBELOW',    (0, 1),  (-1, nb - 2), 0.5, colors.Color(0.90, 0.91, 0.93)),
                    ('BACKGROUND',   (0, -1), (-1, -1),     colors.Color(0.92, 0.95, 1.0)),
                    ('SPAN',         (0, -1), (3, -1)),
                    ('ALIGN',        (4, -1), (4, -1),      'RIGHT'),
                    ('BOX',          (0, 0),  (-1, -1),     1.5, colors.Color(0.90, 0.91, 0.93)),
                ]))
                elements.append(tbl)

                if i < len(dates_triees) - 1:
                    elements.append(Spacer(1, 0.6*cm))

        def ajouter_entete(c, doc):
            dessiner_entete_et_fond(c, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf

    @staticmethod
    def generer_pdf_prescriptions_date_precise(groupes, date_cible, info_cabinet, chemin_pdf=None):
        """Génère un PDF pour les prescriptions d'une date de consultation précise."""
        import tempfile

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="rapport_prescriptions_date_")
            os.close(fd)

        cible_key = _normalize_date(date_cible)
        filtrees = [
            g for g in (groupes or [])
            if _normalize_date(_get_str(g, 'date_consultation', '')) == cible_key
        ]

        if hasattr(date_cible, 'strftime'):
            date_affichee = date_cible.strftime('%d/%m/%Y')
        else:
            s = str(date_cible).strip()
            if len(s) >= 10 and s[4] == '-':
                date_affichee = f"{s[8:10]}/{s[5:7]}/{s[:4]}"
            else:
                date_affichee = s

        doc = SimpleDocTemplate(
            chemin_pdf, pagesize=A4,
            leftMargin=1.5*cm, rightMargin=1.5*cm,
            topMargin=3*cm, bottomMargin=1.5*cm
        )
        styles = getSampleStyleSheet()
        elements = []

        bleu = colors.Color(0.15, 0.38, 0.93)

        titre_style = ParagraphStyle(
            'RptPrDpTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu
        )
        date_gen_style = ParagraphStyle(
            'RptPrDpDateGen', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        cell_style = ParagraphStyle(
            'RptPrDpCell', parent=styles['Normal'],
            fontSize=8, leading=10
        )
        header_cell_style = ParagraphStyle(
            'RptPrDpHdr', parent=styles['Normal'],
            fontSize=9, textColor=colors.white, fontName='Helvetica-Bold'
        )
        total_label_style = ParagraphStyle(
            'RptPrDpTotLbl', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold', textColor=bleu
        )
        total_val_style = ParagraphStyle(
            'RptPrDpTotVal', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold', textColor=bleu, alignment=2
        )

        elements.append(Paragraph(
            f"RAPPORT DES PRESCRIPTIONS DU {date_affichee}", titre_style
        ))
        elements.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            date_gen_style
        ))
        elements.append(Spacer(1, 0.4*cm))

        if not filtrees:
            elements.append(Paragraph(
                f"Aucune prescription trouvée pour le {date_affichee}.",
                styles['Normal']
            ))
        else:
            header_row = [
                Paragraph("<b>Code acte</b>",    header_cell_style),
                Paragraph("<b>Patient</b>",       header_cell_style),
                Paragraph("<b>Nb produits</b>",  header_cell_style),
                Paragraph("<b>Qté totale</b>",   header_cell_style),
                Paragraph("<b>Montant (GNF)</b>", header_cell_style),
            ]
            data = [header_row]
            cumul_montant = 0.0

            for g in filtrees:
                code_acte   = _get_str(g, 'code_acte', 'N/A')
                nom         = _get_str(g, 'patient_nom', '')
                prenom      = _get_str(g, 'patient_prenom', '')
                patient     = f"{prenom} {nom}".strip() or 'N/A'
                nb_produits = _get_str(g, 'nb_produits', '0')
                qte_totale  = _get_str(g, 'total_quantite', '0')
                montant     = _get_float(g, 'total_montant')
                cumul_montant += montant
                montant_fmt = f"{montant:,.0f}".replace(',', ' ')

                data.append([
                    Paragraph(code_acte,    cell_style),
                    Paragraph(patient,      cell_style),
                    Paragraph(nb_produits,  cell_style),
                    Paragraph(qte_totale,   cell_style),
                    Paragraph(montant_fmt,  cell_style),
                ])

            cumul_fmt = f"{cumul_montant:,.0f}".replace(',', ' ') + " GNF"
            data.append([
                Paragraph(f"Total : {len(filtrees)} ordonnance(s)", total_label_style),
                '', '', '',
                Paragraph(cumul_fmt, total_val_style),
            ])

            col_widths = [3.0*cm, 4.5*cm, 3.0*cm, 3.0*cm, 4.0*cm]
            tbl = Table(data, colWidths=col_widths, repeatRows=1)
            nb = len(data)
            tbl.setStyle(TableStyle([
                ('BACKGROUND',   (0, 0),  (-1, 0),      bleu),
                ('TEXTCOLOR',    (0, 0),  (-1, 0),      colors.white),
                ('FONTNAME',     (0, 0),  (-1, 0),      'Helvetica-Bold'),
                ('FONTSIZE',     (0, 0),  (-1, 0),      9),
                ('ALIGN',        (0, 0),  (-1, 0),      'CENTER'),
                ('VALIGN',       (0, 0),  (-1, -1),     'TOP'),
                ('LEFTPADDING',  (0, 0),  (-1, -1),     8),
                ('RIGHTPADDING', (0, 0),  (-1, -1),     8),
                ('TOPPADDING',   (0, 0),  (-1, -1),     6),
                ('BOTTOMPADDING',(0, 0),  (-1, -1),     6),
                ('BACKGROUND',   (0, 1),  (-1, nb - 2), colors.Color(0.98, 0.98, 0.99)),
                ('LINEBELOW',    (0, 0),  (-1, 0),      1, bleu),
                ('LINEBELOW',    (0, 1),  (-1, nb - 2), 0.5, colors.Color(0.90, 0.91, 0.93)),
                ('BACKGROUND',   (0, -1), (-1, -1),     colors.Color(0.92, 0.95, 1.0)),
                ('SPAN',         (0, -1), (3, -1)),
                ('ALIGN',        (4, -1), (4, -1),      'RIGHT'),
                ('BOX',          (0, 0),  (-1, -1),     1.5, colors.Color(0.90, 0.91, 0.93)),
            ]))
            elements.append(tbl)

        elements.append(Spacer(1, 1*cm))

        def ajouter_entete(c, doc):
            dessiner_entete_et_fond(c, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf
