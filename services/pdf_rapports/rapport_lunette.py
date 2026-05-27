from services.pdf_actes._base import (
    dessiner_entete_et_fond, obtenir_valeur,
    A4, cm, colors, SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, PageBreak, getSampleStyleSheet, ParagraphStyle,
    datetime, os
)


class RapportLunettePDF:

    @staticmethod
    def generer_pdf_commandes_par_date(commandes_details, info_cabinet, chemin_pdf=None):
        """Génère un PDF groupant toutes les commandes de lunettes par date."""
        import tempfile
        from collections import defaultdict

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="rapport_lunettes_")
            os.close(fd)

        def _normalize_key(d):
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

        def _get_date_key(c):
            d = c.get('date_commande') if isinstance(c, dict) else getattr(c, 'date_commande', None)
            return _normalize_key(d)

        def _key_to_display(k):
            if len(k) == 10 and k[4] == '-':
                return f"{k[8:10]}/{k[5:7]}/{k[:4]}"
            return k

        groupes = defaultdict(list)
        for c in (commandes_details or []):
            groupes[_get_date_key(c)].append(c)
        dates_triees = sorted(groupes.keys())

        doc = SimpleDocTemplate(
            chemin_pdf, pagesize=A4,
            leftMargin=1.5*cm, rightMargin=1.5*cm,
            topMargin=3*cm, bottomMargin=1.5*cm
        )
        styles = getSampleStyleSheet()
        elements = []

        bleu = colors.Color(0.15, 0.38, 0.93)

        titre_style = ParagraphStyle(
            'RptLnTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu
        )
        date_gen_style = ParagraphStyle(
            'RptLnDateGen', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        date_groupe_style = ParagraphStyle(
            'RptLnDateGroupe', parent=styles['Normal'],
            fontSize=11, fontName='Helvetica-Bold', textColor=bleu, spaceAfter=4
        )
        cell_style = ParagraphStyle(
            'RptLnCell', parent=styles['Normal'],
            fontSize=8, leading=10
        )
        header_cell_style = ParagraphStyle(
            'RptLnHdr', parent=styles['Normal'],
            fontSize=9, textColor=colors.white, fontName='Helvetica-Bold'
        )
        total_label_style = ParagraphStyle(
            'RptLnTotLbl', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold', textColor=bleu
        )
        total_val_style = ParagraphStyle(
            'RptLnTotVal', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold', textColor=bleu, alignment=2
        )

        def _v(obj, key, default=''):
            return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

        elements.append(Paragraph("RAPPORT DES COMMANDES DE LUNETTES", titre_style))
        elements.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            date_gen_style
        ))
        elements.append(Spacer(1, 0.4*cm))

        if not dates_triees:
            elements.append(Paragraph("Aucune commande trouvée.", styles['Normal']))
        else:
            header_row = [
                Paragraph("<b>Code</b>", header_cell_style),
                Paragraph("<b>Patient</b>", header_cell_style),
                Paragraph("<b>N° verre</b>", header_cell_style),
                Paragraph("<b>Médecin</b>", header_cell_style),
                Paragraph("<b>Prix (GNF)</b>", header_cell_style),
                Paragraph("<b>Statut</b>", header_cell_style),
            ]
            col_widths = [2.2*cm, 3.5*cm, 3.8*cm, 3.2*cm, 2.6*cm, 2.7*cm]

            for i, date_key in enumerate(dates_triees):
                groupe = groupes[date_key]
                date_affichee = _key_to_display(date_key) if date_key else "Date inconnue"

                elements.append(Paragraph(f"Date : {date_affichee}", date_groupe_style))

                data = [header_row[:]]
                total_prix = 0.0

                for c in groupe:
                    code = str(_v(c, 'code', 'N/A'))
                    patient = f"{_v(c, 'patient_nom', '')} {_v(c, 'patient_prenom', '')}".strip() or 'N/A'
                    numero_verre = str(_v(c, 'numero_verre', '-'))
                    if len(numero_verre) > 35:
                        numero_verre = numero_verre[:35] + '…'
                    medecin = f"Dr. {_v(c, 'personnel_nom', '')} {_v(c, 'personnel_prenom', '')}".strip()
                    if medecin == 'Dr. ':
                        medecin = '-'
                    prix_val = _v(c, 'prix', 0)
                    try:
                        total_prix += float(prix_val or 0)
                        prix_fmt = f"{float(prix_val or 0):,.0f}".replace(',', ' ')
                    except Exception:
                        prix_fmt = '0'
                    statut = str(_v(c, 'statut_facture', '-'))

                    data.append([
                        Paragraph(code, cell_style),
                        Paragraph(patient, cell_style),
                        Paragraph(numero_verre, cell_style),
                        Paragraph(medecin, cell_style),
                        Paragraph(prix_fmt, cell_style),
                        Paragraph(statut, cell_style),
                    ])

                total_prix_fmt = f"{total_prix:,.0f}".replace(',', ' ') + " GNF"
                data.append([
                    Paragraph(f"Total : {len(groupe)} commande(s)", total_label_style),
                    '', '', '',
                    Paragraph(total_prix_fmt, total_val_style),
                    '',
                ])

                nb = len(data)
                tbl = Table(data, colWidths=col_widths, repeatRows=1)
                tbl.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), bleu),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('BACKGROUND', (0, 1), (-1, nb - 2), colors.Color(0.98, 0.98, 0.99)),
                    ('LINEBELOW', (0, 0), (-1, 0), 1, bleu),
                    ('LINEBELOW', (0, 1), (-1, nb - 2), 0.5, colors.Color(0.90, 0.91, 0.93)),
                    ('BACKGROUND', (0, -1), (-1, -1), colors.Color(0.92, 0.95, 1.0)),
                    ('SPAN', (0, -1), (3, -1)),
                    ('SPAN', (4, -1), (5, -1)),
                    ('ALIGN', (4, -1), (4, -1), 'RIGHT'),
                    ('BOX', (0, 0), (-1, -1), 1.5, colors.Color(0.90, 0.91, 0.93)),
                ]))
                elements.append(tbl)

                if i < len(dates_triees) - 1:
                    elements.append(Spacer(1, 0.6*cm))

        def ajouter_entete(c, doc):
            dessiner_entete_et_fond(c, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf

    @staticmethod
    def generer_pdf_commandes_date_precise(commandes_details, date_cible, info_cabinet, chemin_pdf=None):
        """Génère un PDF pour les commandes de lunettes d'une date précise."""
        import tempfile

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="rapport_lunettes_date_")
            os.close(fd)

        def _normalize_key(d):
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

        def _get_date_key(c):
            d = c.get('date_commande') if isinstance(c, dict) else getattr(c, 'date_commande', None)
            return _normalize_key(d)

        cible_key = _normalize_key(date_cible)
        filtrees = [c for c in (commandes_details or []) if _get_date_key(c) == cible_key]

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
            'RptLnDpTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu
        )
        date_gen_style = ParagraphStyle(
            'RptLnDpDateGen', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        cell_style = ParagraphStyle(
            'RptLnDpCell', parent=styles['Normal'],
            fontSize=8, leading=10
        )
        header_cell_style = ParagraphStyle(
            'RptLnDpHdr', parent=styles['Normal'],
            fontSize=9, textColor=colors.white, fontName='Helvetica-Bold'
        )
        total_label_style = ParagraphStyle(
            'RptLnDpTotLbl', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold', textColor=bleu
        )
        total_val_style = ParagraphStyle(
            'RptLnDpTotVal', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold', textColor=bleu, alignment=2
        )

        def _v(obj, key, default=''):
            return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

        elements.append(Paragraph(
            f"RAPPORT DES LUNETTES DU {date_affichee}", titre_style
        ))
        elements.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            date_gen_style
        ))
        elements.append(Spacer(1, 0.4*cm))

        if not filtrees:
            elements.append(Paragraph(
                f"Aucune commande trouvée pour le {date_affichee}.",
                styles['Normal']
            ))
        else:
            header_row = [
                Paragraph("<b>Code</b>", header_cell_style),
                Paragraph("<b>Patient</b>", header_cell_style),
                Paragraph("<b>N° verre</b>", header_cell_style),
                Paragraph("<b>Médecin</b>", header_cell_style),
                Paragraph("<b>Prix (GNF)</b>", header_cell_style),
                Paragraph("<b>Statut</b>", header_cell_style),
            ]
            data = [header_row]
            total_prix = 0.0

            for c in filtrees:
                code = str(_v(c, 'code', 'N/A'))
                patient = f"{_v(c, 'patient_nom', '')} {_v(c, 'patient_prenom', '')}".strip() or 'N/A'
                numero_verre = str(_v(c, 'numero_verre', '-'))
                if len(numero_verre) > 35:
                    numero_verre = numero_verre[:35] + '…'
                medecin = f"Dr. {_v(c, 'personnel_nom', '')} {_v(c, 'personnel_prenom', '')}".strip()
                if medecin == 'Dr. ':
                    medecin = '-'
                prix_val = _v(c, 'prix', 0)
                try:
                    total_prix += float(prix_val or 0)
                    prix_fmt = f"{float(prix_val or 0):,.0f}".replace(',', ' ')
                except Exception:
                    prix_fmt = '0'
                statut = str(_v(c, 'statut_facture', '-'))

                data.append([
                    Paragraph(code, cell_style),
                    Paragraph(patient, cell_style),
                    Paragraph(numero_verre, cell_style),
                    Paragraph(medecin, cell_style),
                    Paragraph(prix_fmt, cell_style),
                    Paragraph(statut, cell_style),
                ])

            total_prix_fmt = f"{total_prix:,.0f}".replace(',', ' ') + " GNF"
            data.append([
                Paragraph(f"Total : {len(filtrees)} commande(s)", total_label_style),
                '', '', '',
                Paragraph(total_prix_fmt, total_val_style),
                '',
            ])

            col_widths = [2.2*cm, 3.5*cm, 3.8*cm, 3.2*cm, 2.6*cm, 2.7*cm]
            tbl = Table(data, colWidths=col_widths, repeatRows=1)
            nb = len(data)
            tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), bleu),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (0, 1), (-1, nb - 2), colors.Color(0.98, 0.98, 0.99)),
                ('LINEBELOW', (0, 0), (-1, 0), 1, bleu),
                ('LINEBELOW', (0, 1), (-1, nb - 2), 0.5, colors.Color(0.90, 0.91, 0.93)),
                ('BACKGROUND', (0, -1), (-1, -1), colors.Color(0.92, 0.95, 1.0)),
                ('SPAN', (0, -1), (3, -1)),
                ('SPAN', (4, -1), (5, -1)),
                ('ALIGN', (4, -1), (4, -1), 'RIGHT'),
                ('BOX', (0, 0), (-1, -1), 1.5, colors.Color(0.90, 0.91, 0.93)),
            ]))
            elements.append(tbl)

        elements.append(Spacer(1, 1*cm))

        def ajouter_entete(c, doc):
            dessiner_entete_et_fond(c, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf
