from services.pdf_actes._base import (
    dessiner_entete_et_fond, obtenir_valeur,
    A4, cm, colors, SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, PageBreak, getSampleStyleSheet, ParagraphStyle,
    datetime, os
)


class RapportPatientPDF:

    @staticmethod
    def generer_pdf_liste_patients(liste_patients, info_cabinet, chemin_pdf=None):
        """
        Génère un PDF liste complète des patients.
        Structure identique à RapportConsultationPDF.
        Retourne le chemin du PDF généré.
        """
        import tempfile
        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="rapport_patients_")
            os.close(fd)

        doc = SimpleDocTemplate(
            chemin_pdf, pagesize=A4,
            leftMargin=1.5*cm, rightMargin=1.5*cm,
            topMargin=3*cm, bottomMargin=1.5*cm
        )
        styles = getSampleStyleSheet()
        elements = []

        bleu = colors.Color(0.15, 0.38, 0.93)

        titre_style = ParagraphStyle(
            'RptPatTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu
        )
        date_gen_style = ParagraphStyle(
            'RptPatDateGen', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        stats_style = ParagraphStyle(
            'RptPatStats', parent=styles['Normal'],
            fontSize=11, fontName='Helvetica-Bold', textColor=bleu,
            spaceBefore=6, spaceAfter=10
        )
        cell_style = ParagraphStyle(
            'RptPatCell', parent=styles['Normal'],
            fontSize=8, leading=10
        )
        header_cell_style = ParagraphStyle(
            'RptPatHdr', parent=styles['Normal'],
            fontSize=9, textColor=colors.white, fontName='Helvetica-Bold'
        )
        total_label_style = ParagraphStyle(
            'RptPatTotLbl', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold', textColor=bleu
        )

        def _v(obj, key, default=''):
            if isinstance(obj, dict):
                return obj.get(key, default)
            getter = getattr(obj, f'get_{key}', None)
            if getter:
                try:
                    return getter() or default
                except Exception:
                    return default
            return getattr(obj, key, default) or default

        elements.append(Paragraph("RAPPORT — LISTE DES PATIENTS", titre_style))
        elements.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            date_gen_style
        ))
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph(
            f"Nombre total de patients : {len(liste_patients)}",
            stats_style
        ))

        if liste_patients:
            header_row = [
                Paragraph("<b>ID</b>",           header_cell_style),
                Paragraph("<b>Nom</b>",           header_cell_style),
                Paragraph("<b>Prénom</b>",        header_cell_style),
                Paragraph("<b>Téléphone</b>",     header_cell_style),
                Paragraph("<b>Naissance</b>",     header_cell_style),
                Paragraph("<b>Genre</b>",         header_cell_style),
                Paragraph("<b>Profession</b>",    header_cell_style),
                Paragraph("<b>Adresse</b>",       header_cell_style),
            ]
            data = [header_row]

            for p in liste_patients:
                code      = str(_v(p, 'code_patient') or "")
                nom       = str(_v(p, 'nom')          or "")
                prenom    = str(_v(p, 'prenom')       or "")
                tel       = str(_v(p, 'telephone')    or "")
                naissance = str(_v(p, 'naissance')    or "")
                genre     = str(_v(p, 'genre')        or "")
                profession= str(_v(p, 'profession')   or "")
                adresse   = str(_v(p, 'adresse')      or "")

                data.append([
                    Paragraph(code,       cell_style),
                    Paragraph(nom,        cell_style),
                    Paragraph(prenom,     cell_style),
                    Paragraph(tel,        cell_style),
                    Paragraph(naissance,  cell_style),
                    Paragraph(genre,      cell_style),
                    Paragraph(profession, cell_style),
                    Paragraph(adresse,    cell_style),
                ])

            nb = len(data)
            data.append([
                Paragraph(f"Total : {len(liste_patients)} patient(s)", total_label_style),
                '', '', '', '', '', '', '',
            ])

            col_widths = [1.6*cm, 2.3*cm, 2.3*cm, 2.2*cm, 2.0*cm, 1.4*cm, 2.5*cm, 3.2*cm]
            tbl = Table(data, colWidths=col_widths, repeatRows=1)
            tbl.setStyle(TableStyle([
                ('BACKGROUND',    (0, 0), (-1, 0),      bleu),
                ('TEXTCOLOR',     (0, 0), (-1, 0),      colors.white),
                ('FONTNAME',      (0, 0), (-1, 0),      'Helvetica-Bold'),
                ('FONTSIZE',      (0, 0), (-1, 0),      9),
                ('ALIGN',         (0, 0), (-1, 0),      'CENTER'),
                ('VALIGN',        (0, 0), (-1, -1),     'TOP'),
                ('LEFTPADDING',   (0, 0), (-1, -1),     6),
                ('RIGHTPADDING',  (0, 0), (-1, -1),     6),
                ('TOPPADDING',    (0, 0), (-1, -1),     5),
                ('BOTTOMPADDING', (0, 0), (-1, -1),     5),
                ('BACKGROUND',    (0, 1), (-1, nb - 1), colors.Color(0.98, 0.98, 0.99)),
                ('LINEBELOW',     (0, 0), (-1, 0),      1,   bleu),
                ('LINEBELOW',     (0, 1), (-1, nb - 1), 0.5, colors.Color(0.90, 0.91, 0.93)),
                ('BACKGROUND',    (0, -1), (-1, -1),    colors.Color(0.92, 0.95, 1.0)),
                ('SPAN',          (0, -1), (7, -1)),
                ('BOX',           (0, 0), (-1, -1),     1.5, colors.Color(0.90, 0.91, 0.93)),
            ]))
            elements.append(tbl)

        elements.append(Spacer(1, 0.5*cm))

        def ajouter_entete(c, doc):
            dessiner_entete_et_fond(c, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf
