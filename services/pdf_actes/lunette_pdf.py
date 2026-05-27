from ._base import (
    dessiner_entete_et_fond, obtenir_valeur,
    A4, cm, colors, SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, PageBreak, getSampleStyleSheet, ParagraphStyle,
    datetime, os
)


class LunettePDF:

    @staticmethod
    def generer_pdf_lunette(commande, info_cabinet, chemin_pdf=None):
        """Génère un PDF bon de commande lunettes."""
        import tempfile

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="lunette_")
            os.close(fd)

        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        bleu = colors.Color(0.15, 0.38, 0.93)

        titre_style = ParagraphStyle(
            'LunTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu
        )
        date_style = ParagraphStyle(
            'LunDate', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        section_style = ParagraphStyle(
            'LunSection', parent=styles['Heading2'],
            fontSize=13, spaceAfter=8, textColor=bleu, fontName='Helvetica-Bold'
        )
        info_style = ParagraphStyle(
            'LunInfo', parent=styles['Normal'],
            fontSize=10, spaceAfter=4, leading=12
        )
        label_style = ParagraphStyle(
            'LunLabel', parent=styles['Normal'],
            fontSize=9, textColor=colors.Color(0.42, 0.45, 0.50), spaceAfter=2
        )

        def _v(obj, key, default='N/A'):
            return obtenir_valeur(obj, key, default)

        elements.append(Paragraph("BON DE COMMANDE LUNETTES", titre_style))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style))
        elements.append(Spacer(1, 0.5*cm))

        patient_nom   = f"{_v(commande, 'patient_prenom', '')} {_v(commande, 'patient_nom', '')}".strip()
        code_commande = _v(commande, 'code', 'N/A')
        code_acte     = _v(commande, 'code_acte', 'N/A')
        date_commande = _v(commande, 'date_commande', 'N/A')
        date_livraison = _v(commande, 'date_livraison', 'N/A')
        personnel_nom = f"{_v(commande, 'personnel_prenom', '')} {_v(commande, 'personnel_nom', '')}".strip()

        info_data = [
            [Paragraph("<b>Patient</b>", label_style),   Paragraph(patient_nom or 'N/A', info_style),
             Paragraph("<b>Code commande</b>", label_style), Paragraph(str(code_commande), info_style)],
            [Paragraph("<b>Code acte</b>", label_style), Paragraph(str(code_acte), info_style),
             Paragraph("<b>Date commande</b>", label_style), Paragraph(str(date_commande), info_style)],
            [Paragraph("<b>Opticien</b>", label_style),  Paragraph(personnel_nom or 'N/A', info_style),
             Paragraph("<b>Livraison prévue</b>", label_style), Paragraph(str(date_livraison), info_style)],
        ]
        info_table = Table(info_data, colWidths=[3*cm, 5.5*cm, 3.5*cm, 5*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.97, 0.97, 0.99)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 1, colors.Color(0.88, 0.88, 0.90)),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.8*cm))

        elements.append(Paragraph("DÉTAILS DE LA COMMANDE", section_style))
        elements.append(Spacer(1, 0.3*cm))

        numero_verre   = _v(commande, 'numero_verre', 'N/A')
        numero_cadre   = _v(commande, 'numero_cadre', 'N/A')
        prix           = _v(commande, 'prix', 0)
        statut         = _v(commande, 'statut', 'N/A')
        statut_facture = _v(commande, 'statut_facture', 'N/A')
        try:
            prix_fmt = f"{float(prix or 0):,.0f}".replace(',', ' ') + " GNF"
        except Exception:
            prix_fmt = str(prix)

        detail_data = [
            [Paragraph("<b>Numéro de verre</b>", label_style), Paragraph(str(numero_verre), info_style),
             Paragraph("<b>Numéro de cadre</b>", label_style), Paragraph(str(numero_cadre), info_style)],
            [Paragraph("<b>Prix</b>", label_style), Paragraph(prix_fmt, info_style),
             Paragraph("<b>Statut livraison</b>", label_style), Paragraph(str(statut), info_style)],
            [Paragraph("<b>Statut facture</b>", label_style), Paragraph(str(statut_facture), info_style),
             '', ''],
        ]
        detail_table = Table(detail_data, colWidths=[3.5*cm, 5*cm, 3.5*cm, 5*cm])
        detail_table.setStyle(TableStyle([
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
        elements.append(detail_table)
        elements.append(Spacer(1, 1*cm))

        def ajouter_entete(canvas, doc):
            dessiner_entete_et_fond(canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf

    @staticmethod
    def generer_pdf_lunette_avec_resultat(commande, resultat, info_cabinet,
                                           chemin_pdf=None, fichier_bytes=None, type_fichier_res=None):
        """Génère un PDF bon de commande lunettes + résultat médical."""
        import tempfile

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="lunette_resultat_")
            os.close(fd)

        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        bleu = colors.Color(0.15, 0.38, 0.93)

        titre_style = ParagraphStyle(
            'LunResTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu
        )
        date_style = ParagraphStyle(
            'LunResDate', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        section_style = ParagraphStyle(
            'LunResSection', parent=styles['Heading2'],
            fontSize=13, spaceAfter=8, textColor=bleu, fontName='Helvetica-Bold'
        )
        info_style = ParagraphStyle(
            'LunResInfo', parent=styles['Normal'],
            fontSize=10, spaceAfter=4, leading=12
        )
        label_style = ParagraphStyle(
            'LunResLabel', parent=styles['Normal'],
            fontSize=9, textColor=colors.Color(0.42, 0.45, 0.50), spaceAfter=2
        )

        def _v(obj, key, default='N/A'):
            return obtenir_valeur(obj, key, default)

        elements.append(Paragraph("BON DE COMMANDE LUNETTES AVEC RÉSULTAT", titre_style))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style))
        elements.append(Spacer(1, 0.5*cm))

        patient_nom   = f"{_v(commande, 'patient_prenom', '')} {_v(commande, 'patient_nom', '')}".strip()
        code_commande = _v(commande, 'code', 'N/A')
        code_acte     = _v(commande, 'code_acte', 'N/A')
        date_commande = _v(commande, 'date_commande', 'N/A')
        date_livraison = _v(commande, 'date_livraison', 'N/A')
        personnel_nom = f"{_v(commande, 'personnel_prenom', '')} {_v(commande, 'personnel_nom', '')}".strip()

        info_data = [
            [Paragraph("<b>Patient</b>", label_style),   Paragraph(patient_nom or 'N/A', info_style),
             Paragraph("<b>Code commande</b>", label_style), Paragraph(str(code_commande), info_style)],
            [Paragraph("<b>Code acte</b>", label_style), Paragraph(str(code_acte), info_style),
             Paragraph("<b>Date commande</b>", label_style), Paragraph(str(date_commande), info_style)],
            [Paragraph("<b>Opticien</b>", label_style),  Paragraph(personnel_nom or 'N/A', info_style),
             Paragraph("<b>Livraison prévue</b>", label_style), Paragraph(str(date_livraison), info_style)],
        ]
        info_table = Table(info_data, colWidths=[3*cm, 5.5*cm, 3.5*cm, 5*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.97, 0.97, 0.99)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 1, colors.Color(0.88, 0.88, 0.90)),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.8*cm))

        elements.append(Paragraph("DÉTAILS DE LA COMMANDE", section_style))
        elements.append(Spacer(1, 0.3*cm))

        numero_verre   = _v(commande, 'numero_verre', 'N/A')
        numero_cadre   = _v(commande, 'numero_cadre', 'N/A')
        prix           = _v(commande, 'prix', 0)
        statut         = _v(commande, 'statut', 'N/A')
        statut_facture = _v(commande, 'statut_facture', 'N/A')
        try:
            prix_fmt = f"{float(prix or 0):,.0f}".replace(',', ' ') + " GNF"
        except Exception:
            prix_fmt = str(prix)

        detail_data = [
            [Paragraph("<b>Numéro de verre</b>", label_style), Paragraph(str(numero_verre), info_style),
             Paragraph("<b>Numéro de cadre</b>", label_style), Paragraph(str(numero_cadre), info_style)],
            [Paragraph("<b>Prix</b>", label_style), Paragraph(prix_fmt, info_style),
             Paragraph("<b>Statut livraison</b>", label_style), Paragraph(str(statut), info_style)],
            [Paragraph("<b>Statut facture</b>", label_style), Paragraph(str(statut_facture), info_style),
             '', ''],
        ]
        detail_table = Table(detail_data, colWidths=[3.5*cm, 5*cm, 3.5*cm, 5*cm])
        detail_table.setStyle(TableStyle([
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
        elements.append(detail_table)
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
