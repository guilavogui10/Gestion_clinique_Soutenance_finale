from services.pdf_actes._base import (
    dessiner_entete_et_fond, obtenir_valeur,
    A4, cm, colors, SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, PageBreak, getSampleStyleSheet, ParagraphStyle,
    datetime, os
)


class RapportFactureFournisseurPDF:

    @staticmethod
    def generer_pdf_par_date(factures, info_cabinet, chemin_pdf=None):
        """Génère un PDF des factures fournisseur groupées par date."""
        import tempfile
        from collections import defaultdict

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="rapport_factures_fourni_")
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
            'RptFfTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu
        )
        date_gen_style = ParagraphStyle(
            'RptFfDateGen', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        date_section_style = ParagraphStyle(
            'RptFfSection', parent=styles['Normal'],
            fontSize=11, fontName='Helvetica-Bold',
            textColor=bleu, spaceBefore=10, spaceAfter=4
        )
        cell_style = ParagraphStyle(
            'RptFfCell', parent=styles['Normal'],
            fontSize=8, leading=10
        )
        header_cell_style = ParagraphStyle(
            'RptFfHdr', parent=styles['Normal'],
            fontSize=9, textColor=colors.white, fontName='Helvetica-Bold'
        )
        total_label_style = ParagraphStyle(
            'RptFfTotLbl', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold', textColor=bleu
        )
        total_val_style = ParagraphStyle(
            'RptFfTotVal', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold', textColor=bleu, alignment=2
        )

        def _v(obj, key, default=''):
            return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

        def _get_date_key(f):
            d = _v(f, 'date_facture_four')
            if not d:
                return '9999-99-99'
            if hasattr(d, 'date'):
                return d.date().strftime('%Y-%m-%d')
            if hasattr(d, 'strftime'):
                return d.strftime('%Y-%m-%d')
            s = str(d)
            return s[:10] if len(s) >= 10 else s

        def _fmt_date(d):
            if not d:
                return 'Date inconnue'
            if hasattr(d, 'strftime'):
                return d.strftime('%d/%m/%Y')
            s = str(d)
            if len(s) >= 10 and s[4] == '-':
                return f"{s[8:10]}/{s[5:7]}/{s[:4]}"
            return s

        elements.append(Paragraph("RAPPORT FINANCIER — FACTURES FOURNISSEURS", titre_style))
        elements.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            date_gen_style
        ))
        elements.append(Spacer(1, 0.3*cm))

        if not factures:
            elements.append(Paragraph("Aucune facture à afficher.", styles['Normal']))
        else:
            groupes = defaultdict(list)
            for f in factures:
                groupes[_get_date_key(f)].append(f)

            for date_key in sorted(groupes.keys()):
                groupe = groupes[date_key]
                date_label = _fmt_date(_v(groupe[0], 'date_facture_four'))
                elements.append(Paragraph(f"Date : {date_label}", date_section_style))

                header_row = [
                    Paragraph("<b>Code Facture</b>", header_cell_style),
                    Paragraph("<b>Fournisseur</b>", header_cell_style),
                    Paragraph("<b>Montant (GNF)</b>", header_cell_style),
                    Paragraph("<b>Mode Paiement</b>", header_cell_style),
                    Paragraph("<b>Statut</b>", header_cell_style),
                ]
                data = [header_row]
                total_montant = 0.0

                for f in groupe:
                    code = str(_v(f, 'code_facture_four', 'N/A'))
                    fournisseur = str(_v(f, 'fournisseur_nom', '-') or '-')
                    montant_val = _v(f, 'montant_total', 0)
                    try:
                        total_montant += float(montant_val or 0)
                        montant_fmt = f"{float(montant_val or 0):,.0f}".replace(',', ' ')
                    except Exception:
                        montant_fmt = '0'
                    mode = str(_v(f, 'mode_payement', '-') or '-')
                    statut = str(_v(f, 'statut', '-') or _v(f, 'statut_facture', '-') or '-')

                    data.append([
                        Paragraph(code, cell_style),
                        Paragraph(fournisseur, cell_style),
                        Paragraph(montant_fmt, cell_style),
                        Paragraph(mode, cell_style),
                        Paragraph(statut, cell_style),
                    ])

                total_fmt = f"{total_montant:,.0f}".replace(',', ' ') + " GNF"
                data.append([
                    Paragraph(f"Total : {len(groupe)} facture(s)", total_label_style),
                    '', '',
                    Paragraph(total_fmt, total_val_style),
                    '',
                ])

                col_widths = [3.0*cm, 4.5*cm, 3.2*cm, 3.5*cm, 3.8*cm]
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
                    ('SPAN', (0, -1), (2, -1)),
                    ('SPAN', (3, -1), (4, -1)),
                    ('ALIGN', (3, -1), (3, -1), 'RIGHT'),
                    ('BOX', (0, 0), (-1, -1), 1.5, colors.Color(0.90, 0.91, 0.93)),
                ]))
                elements.append(tbl)
                elements.append(Spacer(1, 0.5*cm))

        def ajouter_entete(c, doc):
            dessiner_entete_et_fond(c, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf

    @staticmethod
    def generer_pdf_date_precise(factures, date_cible, info_cabinet, chemin_pdf=None):
        """Génère un PDF des factures fournisseur pour une date précise."""
        import tempfile

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="rapport_ff_date_")
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

        def _get_date_key(f):
            d = f.get('date_facture_four') if isinstance(f, dict) else getattr(f, 'date_facture_four', None)
            return _normalize_key(d)

        cible_key = _normalize_key(date_cible)
        filtrees = [f for f in (factures or []) if _get_date_key(f) == cible_key]

        if hasattr(date_cible, 'strftime'):
            date_affichee = date_cible.strftime('%d/%m/%Y')
        else:
            s = str(date_cible).strip()
            date_affichee = f"{s[8:10]}/{s[5:7]}/{s[:4]}" if len(s) >= 10 and s[4] == '-' else s

        doc = SimpleDocTemplate(
            chemin_pdf, pagesize=A4,
            leftMargin=1.5*cm, rightMargin=1.5*cm,
            topMargin=3*cm, bottomMargin=1.5*cm
        )
        styles = getSampleStyleSheet()
        elements = []

        bleu = colors.Color(0.15, 0.38, 0.93)

        titre_style = ParagraphStyle(
            'RptFfDTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=12, alignment=1, textColor=bleu
        )
        sous_titre_style = ParagraphStyle(
            'RptFfDSub', parent=styles['Normal'],
            fontSize=12, spaceAfter=16, alignment=1, textColor=bleu
        )
        date_gen_style = ParagraphStyle(
            'RptFfDDateGen', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        cell_style = ParagraphStyle(
            'RptFfDCell', parent=styles['Normal'],
            fontSize=8, leading=10
        )
        header_cell_style = ParagraphStyle(
            'RptFfDHdr', parent=styles['Normal'],
            fontSize=9, textColor=colors.white, fontName='Helvetica-Bold'
        )
        total_label_style = ParagraphStyle(
            'RptFfDTotLbl', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold', textColor=bleu
        )
        total_val_style = ParagraphStyle(
            'RptFfDTotVal', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold', textColor=bleu, alignment=2
        )

        def _v(obj, key, default=''):
            return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

        elements.append(Paragraph("RAPPORT FINANCIER — FACTURES FOURNISSEURS", titre_style))
        elements.append(Paragraph(f"Du {date_affichee}", sous_titre_style))
        elements.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            date_gen_style
        ))
        elements.append(Spacer(1, 0.4*cm))

        if not filtrees:
            elements.append(Paragraph(
                f"Aucune facture fournisseur pour le {date_affichee}.", styles['Normal']
            ))
        else:
            header_row = [
                Paragraph("<b>Code Facture</b>", header_cell_style),
                Paragraph("<b>Fournisseur</b>", header_cell_style),
                Paragraph("<b>Montant (GNF)</b>", header_cell_style),
                Paragraph("<b>Mode Paiement</b>", header_cell_style),
                Paragraph("<b>Statut</b>", header_cell_style),
            ]
            data = [header_row]
            total_montant = 0.0

            for f in filtrees:
                code = str(_v(f, 'code_facture_four', 'N/A'))
                fournisseur = str(_v(f, 'fournisseur_nom', '-') or '-')
                montant_val = _v(f, 'montant_total', 0)
                try:
                    total_montant += float(montant_val or 0)
                    montant_fmt = f"{float(montant_val or 0):,.0f}".replace(',', ' ')
                except Exception:
                    montant_fmt = '0'
                mode = str(_v(f, 'mode_payement', '-') or '-')
                statut = str(_v(f, 'statut', '-') or _v(f, 'statut_facture', '-') or '-')

                data.append([
                    Paragraph(code, cell_style),
                    Paragraph(fournisseur, cell_style),
                    Paragraph(montant_fmt, cell_style),
                    Paragraph(mode, cell_style),
                    Paragraph(statut, cell_style),
                ])

            total_fmt = f"{total_montant:,.0f}".replace(',', ' ') + " GNF"
            data.append([
                Paragraph(f"Total : {len(filtrees)} facture(s)", total_label_style),
                '', '',
                Paragraph(total_fmt, total_val_style),
                '',
            ])

            col_widths = [3.0*cm, 4.5*cm, 3.2*cm, 3.5*cm, 3.8*cm]
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
                ('SPAN', (0, -1), (2, -1)),
                ('SPAN', (3, -1), (4, -1)),
                ('ALIGN', (3, -1), (3, -1), 'RIGHT'),
                ('BOX', (0, 0), (-1, -1), 1.5, colors.Color(0.90, 0.91, 0.93)),
            ]))
            elements.append(tbl)

        def ajouter_entete(c, doc):
            dessiner_entete_et_fond(c, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf
