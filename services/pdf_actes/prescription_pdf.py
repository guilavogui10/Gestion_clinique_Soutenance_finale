from ._base import (
    dessiner_entete_et_fond, obtenir_valeur,
    A4, cm, colors, SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, PageBreak, getSampleStyleSheet, ParagraphStyle,
    datetime, os
)


class PrescriptionPDF:

    @staticmethod
    def generer_pdf_prescription(prescription_group, lignes, info_cabinet, chemin_pdf=None):
        """Génère un PDF ordonnance (liste des produits prescrits pour un acte médical)."""
        import tempfile

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="ordonnance_")
            os.close(fd)

        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        bleu = colors.Color(0.15, 0.38, 0.93)

        titre_style = ParagraphStyle(
            'OrdTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu
        )
        date_style = ParagraphStyle(
            'OrdDate', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        section_style = ParagraphStyle(
            'OrdSection', parent=styles['Heading2'],
            fontSize=13, spaceAfter=8, textColor=bleu, fontName='Helvetica-Bold'
        )
        info_style = ParagraphStyle(
            'OrdInfo', parent=styles['Normal'],
            fontSize=10, spaceAfter=4, leading=12
        )
        label_style = ParagraphStyle(
            'OrdLabel', parent=styles['Normal'],
            fontSize=9, textColor=colors.Color(0.42, 0.45, 0.50), spaceAfter=2
        )

        def _v(obj, key, default='N/A'):
            return obtenir_valeur(obj, key, default)

        elements.append(Paragraph("ORDONNANCE MÉDICALE", titre_style))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Générée le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style))
        elements.append(Spacer(1, 0.5*cm))

        patient_nom = _v(prescription_group, 'patient_prenom', '') + ' ' + _v(prescription_group, 'patient_nom', '')
        code_acte   = _v(prescription_group, 'code_acte', 'N/A')
        date_cons   = _v(prescription_group, 'date_consultation', 'N/A')

        info_pat = Table([
            [Paragraph("<b>Patient</b>", label_style),    Paragraph(patient_nom.strip() or 'N/A', info_style),
             Paragraph("<b>Code Acte</b>", label_style),  Paragraph(str(code_acte), info_style)],
            [Paragraph("<b>Date</b>", label_style),       Paragraph(str(date_cons), info_style), '', ''],
        ], colWidths=[3*cm, 5.5*cm, 3*cm, 5.5*cm])
        info_pat.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.97, 0.97, 0.99)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 1, colors.Color(0.88, 0.88, 0.90)),
        ]))
        elements.append(info_pat)
        elements.append(Spacer(1, 0.8*cm))

        elements.append(Paragraph("PRODUITS PRESCRITS", section_style))
        elements.append(Spacer(1, 0.3*cm))

        header_row = [
            Paragraph("<b>Désignation</b>", label_style),
            Paragraph("<b>Quantité</b>", label_style),
            Paragraph("<b>Prix unitaire (GNF)</b>", label_style),
            Paragraph("<b>Montant (GNF)</b>", label_style),
        ]
        data_rows = [header_row]

        for ligne in (lignes or []):
            designation = _v(ligne, 'designation', 'N/A')
            quantite    = _v(ligne, 'quantite_prescript', 0)
            prix        = _v(ligne, 'prix_applique', 0)
            try:
                montant = float(quantite or 0) * float(prix or 0)
                montant_fmt = f"{montant:,.0f}".replace(',', ' ')
            except Exception:
                montant_fmt = 'N/A'
            try:
                prix_fmt = f"{float(prix or 0):,.0f}".replace(',', ' ')
            except Exception:
                prix_fmt = str(prix)
            data_rows.append([
                Paragraph(str(designation), info_style),
                Paragraph(str(quantite), info_style),
                Paragraph(prix_fmt, info_style),
                Paragraph(montant_fmt, info_style),
            ])

        if len(data_rows) == 1:
            data_rows.append([Paragraph("Aucun produit prescrit.", info_style), '', '', ''])

        prod_table = Table(data_rows, colWidths=[6*cm, 3*cm, 4.5*cm, 4*cm])
        prod_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), bleu),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BACKGROUND', (0, 1), (-1, -1), colors.Color(0.98, 0.98, 0.99)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.Color(0.90, 0.91, 0.93)),
            ('LINEBELOW', (0, 0), (-1, 0), 1, bleu),
            ('LINEBELOW', (0, 1), (-1, -2), 0.5, colors.Color(0.90, 0.91, 0.93)),
        ]))
        elements.append(prod_table)
        elements.append(Spacer(1, 1*cm))

        def ajouter_entete(canvas, doc):
            dessiner_entete_et_fond(canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf

    @staticmethod
    def generer_pdf_prescription_avec_resultat(prescription_group, lignes, resultat, info_cabinet,
                                                chemin_pdf=None, fichier_bytes=None, type_fichier_res=None):
        """Génère un PDF ordonnance + résultat médical."""
        import tempfile

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="ordonnance_resultat_")
            os.close(fd)

        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        bleu = colors.Color(0.15, 0.38, 0.93)

        titre_style = ParagraphStyle(
            'OrdResTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu
        )
        date_style = ParagraphStyle(
            'OrdResDate', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        section_style = ParagraphStyle(
            'OrdResSection', parent=styles['Heading2'],
            fontSize=13, spaceAfter=8, textColor=bleu, fontName='Helvetica-Bold'
        )
        info_style = ParagraphStyle(
            'OrdResInfo', parent=styles['Normal'],
            fontSize=10, spaceAfter=4, leading=12
        )
        label_style = ParagraphStyle(
            'OrdResLabel', parent=styles['Normal'],
            fontSize=9, textColor=colors.Color(0.42, 0.45, 0.50), spaceAfter=2
        )

        def _v(obj, key, default='N/A'):
            return obtenir_valeur(obj, key, default)

        elements.append(Paragraph("ORDONNANCE MÉDICALE AVEC RÉSULTAT", titre_style))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Générée le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style))
        elements.append(Spacer(1, 0.5*cm))

        patient_nom = _v(prescription_group, 'patient_prenom', '') + ' ' + _v(prescription_group, 'patient_nom', '')
        code_acte   = _v(prescription_group, 'code_acte', 'N/A')
        date_cons   = _v(prescription_group, 'date_consultation', 'N/A')

        info_pat = Table([
            [Paragraph("<b>Patient</b>", label_style),   Paragraph(patient_nom.strip() or 'N/A', info_style),
             Paragraph("<b>Code Acte</b>", label_style), Paragraph(str(code_acte), info_style)],
            [Paragraph("<b>Date</b>", label_style),      Paragraph(str(date_cons), info_style), '', ''],
        ], colWidths=[3*cm, 5.5*cm, 3*cm, 5.5*cm])
        info_pat.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.97, 0.97, 0.99)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 1, colors.Color(0.88, 0.88, 0.90)),
        ]))
        elements.append(info_pat)
        elements.append(Spacer(1, 0.8*cm))

        elements.append(Paragraph("PRODUITS PRESCRITS", section_style))
        elements.append(Spacer(1, 0.3*cm))

        header_row = [
            Paragraph("<b>Désignation</b>", label_style),
            Paragraph("<b>Quantité</b>", label_style),
            Paragraph("<b>Prix unitaire (GNF)</b>", label_style),
            Paragraph("<b>Montant (GNF)</b>", label_style),
        ]
        data_rows = [header_row]
        for ligne in (lignes or []):
            designation = _v(ligne, 'designation', 'N/A')
            quantite    = _v(ligne, 'quantite_prescript', 0)
            prix        = _v(ligne, 'prix_applique', 0)
            try:
                montant_fmt = f"{float(quantite or 0) * float(prix or 0):,.0f}".replace(',', ' ')
                prix_fmt    = f"{float(prix or 0):,.0f}".replace(',', ' ')
            except Exception:
                montant_fmt = prix_fmt = 'N/A'
            data_rows.append([
                Paragraph(str(designation), info_style),
                Paragraph(str(quantite), info_style),
                Paragraph(prix_fmt, info_style),
                Paragraph(montant_fmt, info_style),
            ])

        if len(data_rows) == 1:
            data_rows.append([Paragraph("Aucun produit prescrit.", info_style), '', '', ''])

        prod_table = Table(data_rows, colWidths=[6*cm, 3*cm, 4.5*cm, 4*cm])
        prod_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), bleu),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BACKGROUND', (0, 1), (-1, -1), colors.Color(0.98, 0.98, 0.99)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.Color(0.90, 0.91, 0.93)),
            ('LINEBELOW', (0, 0), (-1, 0), 1, bleu),
            ('LINEBELOW', (0, 1), (-1, -2), 0.5, colors.Color(0.90, 0.91, 0.93)),
        ]))
        elements.append(prod_table)
        elements.append(Spacer(1, 0.8*cm))

        if resultat:
            id_res      = _v(resultat, 'id_resultat', 'N/A')
            date_upload = _v(resultat, 'date_upload', 'N/A')
            type_fich   = _v(resultat, 'type_fichier', 'N/A')
            niveau      = _v(resultat, 'niveau_confidentialite', 'N/A')
            description = _v(resultat, 'description', 'N/A')

            inner_res = Table([
                [Paragraph("<b>Référence</b>", label_style), Paragraph(str(id_res), info_style),
                 Paragraph("<b>Date</b>", label_style),      Paragraph(str(date_upload), info_style)],
                [Paragraph("<b>Type de fichier</b>", label_style), Paragraph(str(type_fich), info_style),
                 Paragraph("<b>Confidentialité</b>", label_style), Paragraph(str(niveau), info_style)],
                [Paragraph("<b>Description</b>", label_style), Paragraph(str(description), info_style), '', ''],
            ], colWidths=[4*cm, 5.5*cm, 3*cm, 5*cm])
            inner_res.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            frame_res = Table([
                [Paragraph("RÉSULTAT MÉDICAL", section_style)],
                [inner_res]
            ], colWidths=[17.5*cm])
            frame_res.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, 0), 0),
                ('RIGHTPADDING', (0, 0), (-1, 0), 0),
                ('TOPPADDING', (0, 0), (-1, 0), 0),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BOX', (0, 1), (0, 1), 1.5, colors.Color(0.85, 0.85, 0.85)),
                ('ROUNDEDCORNERS', [10, 10, 10, 10]),
                ('LEFTPADDING', (0, 1), (0, 1), 15),
                ('RIGHTPADDING', (0, 1), (0, 1), 15),
                ('TOPPADDING', (0, 1), (0, 1), 15),
                ('BOTTOMPADDING', (0, 1), (0, 1), 15),
            ]))
            elements.append(frame_res)

        if fichier_bytes and type_fichier_res == 'image':
            import io
            from reportlab.platypus import Image as RLImage
            try:
                elements.append(Spacer(1, 0.6*cm))
                img_io = io.BytesIO(fichier_bytes)
                img = RLImage(img_io, width=14*cm, height=10*cm, kind='proportional')
                frame_img = Table([
                    [Paragraph("FICHIER RÉSULTAT", section_style)],
                    [img]
                ], colWidths=[17.5*cm])
                frame_img.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 1), (0, 1), 'CENTER'),
                    ('LEFTPADDING', (0, 0), (-1, 0), 0),
                    ('RIGHTPADDING', (0, 0), (-1, 0), 0),
                    ('TOPPADDING', (0, 0), (-1, 0), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BOX', (0, 1), (0, 1), 1.5, colors.Color(0.85, 0.85, 0.85)),
                    ('ROUNDEDCORNERS', [10, 10, 10, 10]),
                    ('LEFTPADDING', (0, 1), (0, 1), 15),
                    ('RIGHTPADDING', (0, 1), (0, 1), 15),
                    ('TOPPADDING', (0, 1), (0, 1), 15),
                    ('BOTTOMPADDING', (0, 1), (0, 1), 15),
                ]))
                elements.append(frame_img)
            except Exception:
                pass

        elements.append(Spacer(1, 1*cm))

        def ajouter_entete(canvas, doc):
            dessiner_entete_et_fond(canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf
