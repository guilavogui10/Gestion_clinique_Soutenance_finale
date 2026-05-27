"""
PDF pour les chirurgies (fiche info, compte rendu opératoire, avec résultat).
"""
from ._base import (
    dessiner_entete_et_fond, obtenir_valeur,
    A4, cm, colors, SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, PageBreak, getSampleStyleSheet, ParagraphStyle,
    datetime, os
)


class ChirurgiePDF:

    @staticmethod
    def generer_pdf_chirurgie(chirurgie, info_cabinet, chemin_pdf=None):
        import tempfile
        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="chirurgie_")
            os.close(fd)

        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        bleu = colors.Color(0.15, 0.38, 0.93)

        titre_style   = ParagraphStyle('ChirTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu)
        date_style    = ParagraphStyle('ChirDate', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray)
        section_style = ParagraphStyle('ChirSection', parent=styles['Heading2'],
            fontSize=13, spaceAfter=8, textColor=bleu, fontName='Helvetica-Bold')
        info_style    = ParagraphStyle('ChirInfo', parent=styles['Normal'],
            fontSize=10, spaceAfter=4, leading=12)
        label_style   = ParagraphStyle('ChirLabel', parent=styles['Normal'],
            fontSize=9, textColor=colors.Color(0.42, 0.45, 0.50), spaceAfter=2)

        def _v(obj, key, default='N/A'):
            return obtenir_valeur(obj, key, default)

        def _make_frame(titre_txt, rows, col_widths):
            inner = Table(rows, colWidths=col_widths)
            inner.setStyle(TableStyle([
                ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('LEFTPADDING',(0,0),(-1,-1),8), ('RIGHTPADDING',(0,0),(-1,-1),8),
                ('TOPPADDING',(0,0),(-1,-1),6),  ('BOTTOMPADDING',(0,0),(-1,-1),6),
            ]))
            frame = Table([[Paragraph(titre_txt, section_style)], [inner]], colWidths=[8.5*cm])
            frame.setStyle(TableStyle([
                ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('LEFTPADDING',(0,0),(-1,0),0), ('RIGHTPADDING',(0,0),(-1,0),0),
                ('TOPPADDING',(0,0),(-1,0),0),  ('BOTTOMPADDING',(0,0),(-1,0),8),
                ('BOX',(0,1),(0,1),1.5,colors.Color(0.85,0.85,0.85)),
                ('ROUNDEDCORNERS',[10,10,10,10]),
                ('LEFTPADDING',(0,1),(0,1),15), ('RIGHTPADDING',(0,1),(0,1),15),
                ('TOPPADDING',(0,1),(0,1),15),  ('BOTTOMPADDING',(0,1),(0,1),15),
            ]))
            return frame

        elements.append(Paragraph("RAPPORT DE CHIRURGIE", titre_style))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style))
        elements.append(Spacer(1, 0.5*cm))

        frame_patient = _make_frame("INFORMATIONS PATIENT", [
            [Paragraph("<b>Nom</b>", label_style),       Paragraph(str(_v(chirurgie,'patient_nom')), info_style)],
            [Paragraph("<b>Prénom</b>", label_style),    Paragraph(str(_v(chirurgie,'patient_prenom')), info_style)],
            [Paragraph("<b>Téléphone</b>", label_style), Paragraph(str(_v(chirurgie,'patient_telephone')), info_style)],
            [Paragraph("<b>Adresse</b>", label_style),   Paragraph(str(_v(chirurgie,'patient_adresse')), info_style)],
        ], [3*cm, 5.5*cm])
        frame_personnel = _make_frame("CHIRURGIEN", [
            [Paragraph("<b>Nom</b>", label_style),      Paragraph(str(_v(chirurgie,'personnel_nom')), info_style)],
            [Paragraph("<b>Prénom</b>", label_style),   Paragraph(str(_v(chirurgie,'personnel_prenom')), info_style)],
            [Paragraph("<b>Fonction</b>", label_style), Paragraph(str(_v(chirurgie,'personnel_fonction')), info_style)],
            ["", ""],
        ], [3*cm, 5.5*cm])

        elements.append(Spacer(1, 0.3*cm))
        duo = Table([[frame_patient, "", frame_personnel]], colWidths=[8.5*cm, 0.5*cm, 8.5*cm])
        duo.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
            ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
        elements.append(duo)
        elements.append(Spacer(1, 0.8*cm))

        elements.append(Paragraph("DÉTAILS DE LA CHIRURGIE", section_style))
        elements.append(Spacer(1, 0.3*cm))

        frais = _v(chirurgie, 'frais_chururgie', 0)
        try:
            frais_fmt = f"{float(frais):,.0f} GNF".replace(',', ' ')
        except Exception:
            frais_fmt = f"{frais} GNF"

        data_chir = [
            [Paragraph("<b>Code Chirurgie</b>", label_style), Paragraph(str(_v(chirurgie,'code')), info_style),
             Paragraph("<b>Date</b>", label_style),            Paragraph(str(_v(chirurgie,'date_chururgie')), info_style)],
            [Paragraph("<b>Libellé</b>", label_style),         Paragraph(str(_v(chirurgie,'libelle_chururgie')), info_style),
             Paragraph("<b>Frais</b>", label_style),            Paragraph(frais_fmt, info_style)],
            [Paragraph("<b>Statut Facture</b>", label_style),  Paragraph(str(_v(chirurgie,'statut_facture')), info_style),
             "", ""],
        ]
        chir_table = Table(data_chir, colWidths=[4*cm, 5*cm, 3*cm, 5*cm])
        chir_table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),colors.Color(0.98,0.98,0.99)),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
            ('TOPPADDING',(0,0),(-1,-1),8),  ('BOTTOMPADDING',(0,0),(-1,-1),8),
            ('BOX',(0,0),(-1,-1),1.5,colors.Color(0.90,0.91,0.93)),
            ('ROUNDEDCORNERS',[10,10,10,10]),
        ]))
        elements.append(chir_table)
        elements.append(Spacer(1, 1*cm))

        def ajouter_entete(c, doc):
            dessiner_entete_et_fond(c, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf

    @staticmethod
    def generer_pdf_chirurgie_avec_compte_rendu(chirurgie, info_cabinet, chemin_pdf=None):
        import tempfile
        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="chirurgie_cr_")
            os.close(fd)

        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        bleu = colors.Color(0.15, 0.38, 0.93)

        titre_style   = ParagraphStyle('ChirCRTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu)
        date_style    = ParagraphStyle('ChirCRDate', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray)
        section_style = ParagraphStyle('ChirCRSection', parent=styles['Heading2'],
            fontSize=13, spaceAfter=8, textColor=bleu, fontName='Helvetica-Bold')
        info_style    = ParagraphStyle('ChirCRInfo', parent=styles['Normal'],
            fontSize=10, spaceAfter=4, leading=12)
        label_style   = ParagraphStyle('ChirCRLabel', parent=styles['Normal'],
            fontSize=9, textColor=colors.Color(0.42, 0.45, 0.50), spaceAfter=2)
        body_style    = ParagraphStyle('ChirCRBody', parent=styles['Normal'],
            fontSize=10, leading=14, spaceAfter=6)

        def _v(obj, key, default='N/A'):
            return obtenir_valeur(obj, key, default)

        elements.append(Paragraph("RAPPORT DE CHIRURGIE — COMPTE RENDU OPÉRATOIRE", titre_style))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style))
        elements.append(Spacer(1, 0.5*cm))

        frais = _v(chirurgie, 'frais_chururgie', 0)
        try:
            frais_fmt = f"{float(frais):,.0f} GNF".replace(',', ' ')
        except Exception:
            frais_fmt = f"{frais} GNF"

        elements.append(Paragraph("PATIENT", section_style))
        info_pat = Table([
            [Paragraph("<b>Nom</b>", label_style),
             Paragraph(f"{_v(chirurgie,'patient_nom')} {_v(chirurgie,'patient_prenom')}", info_style),
             Paragraph("<b>Téléphone</b>", label_style), Paragraph(str(_v(chirurgie,'patient_telephone')), info_style)],
            [Paragraph("<b>Adresse</b>", label_style), Paragraph(str(_v(chirurgie,'patient_adresse')), info_style), "", ""],
        ], colWidths=[3*cm, 5.5*cm, 3*cm, 5.5*cm])
        info_pat.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),colors.Color(0.97,0.97,0.99)),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
            ('TOPPADDING',(0,0),(-1,-1),6), ('BOTTOMPADDING',(0,0),(-1,-1),6),
            ('BOX',(0,0),(-1,-1),1,colors.Color(0.88,0.88,0.90)),
        ]))
        elements.append(info_pat)
        elements.append(Spacer(1, 0.5*cm))

        elements.append(Paragraph("DÉTAILS DE LA CHIRURGIE", section_style))
        info_chir = Table([
            [Paragraph("<b>Code</b>", label_style),      Paragraph(str(_v(chirurgie,'code')), info_style),
             Paragraph("<b>Date</b>", label_style),        Paragraph(str(_v(chirurgie,'date_chururgie')), info_style)],
            [Paragraph("<b>Libellé</b>", label_style),    Paragraph(str(_v(chirurgie,'libelle_chururgie')), info_style),
             Paragraph("<b>Frais</b>", label_style),        Paragraph(frais_fmt, info_style)],
            [Paragraph("<b>Chirurgien</b>", label_style),
             Paragraph(f"Dr. {_v(chirurgie,'personnel_nom')} {_v(chirurgie,'personnel_prenom')} — {_v(chirurgie,'personnel_fonction')}", info_style),
             Paragraph("<b>Statut</b>", label_style), Paragraph(str(_v(chirurgie,'statut_facture')), info_style)],
        ], colWidths=[3*cm, 5.5*cm, 3*cm, 5.5*cm])
        info_chir.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),colors.Color(0.98,0.98,0.99)),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
            ('TOPPADDING',(0,0),(-1,-1),6), ('BOTTOMPADDING',(0,0),(-1,-1),6),
            ('BOX',(0,0),(-1,-1),1,colors.Color(0.88,0.88,0.90)),
        ]))
        elements.append(info_chir)
        elements.append(Spacer(1, 0.8*cm))

        elements.append(Paragraph("COMPTE RENDU OPÉRATOIRE", section_style))
        elements.append(Spacer(1, 0.3*cm))
        compte_rendu = _v(chirurgie, 'compte_rendu_operatoire', '')
        cr_text = str(compte_rendu).strip() if compte_rendu else "Aucun compte rendu disponible."
        cr_frame = Table([[Paragraph(cr_text, body_style)]], colWidths=[17.5*cm])
        cr_frame.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),colors.Color(0.98,0.98,0.98)),
            ('BOX',(0,0),(-1,-1),1.5,colors.Color(0.85,0.85,0.85)),
            ('ROUNDEDCORNERS',[10,10,10,10]),
            ('LEFTPADDING',(0,0),(-1,-1),15), ('RIGHTPADDING',(0,0),(-1,-1),15),
            ('TOPPADDING',(0,0),(-1,-1),12),  ('BOTTOMPADDING',(0,0),(-1,-1),12),
        ]))
        elements.append(cr_frame)
        elements.append(Spacer(1, 1*cm))

        def ajouter_entete(c, doc):
            dessiner_entete_et_fond(c, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf

    @staticmethod
    def generer_pdf_chirurgie_avec_resultat(chirurgie, resultat, info_cabinet, chemin_pdf=None,
                                             fichier_bytes=None, type_fichier_res=None):
        import tempfile
        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="chirurgie_resultat_")
            os.close(fd)

        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        bleu = colors.Color(0.15, 0.38, 0.93)

        titre_style   = ParagraphStyle('ChirResTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu)
        date_style    = ParagraphStyle('ChirResDate', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray)
        section_style = ParagraphStyle('ChirResSection', parent=styles['Heading2'],
            fontSize=13, spaceAfter=8, textColor=bleu, fontName='Helvetica-Bold')
        info_style    = ParagraphStyle('ChirResInfo', parent=styles['Normal'],
            fontSize=10, spaceAfter=4, leading=12)
        label_style   = ParagraphStyle('ChirResLabel', parent=styles['Normal'],
            fontSize=9, textColor=colors.Color(0.42, 0.45, 0.50), spaceAfter=2)

        def _v(obj, key, default='N/A'):
            return obtenir_valeur(obj, key, default)

        def _make_frame(titre_txt, rows, col_widths):
            inner = Table(rows, colWidths=col_widths)
            inner.setStyle(TableStyle([
                ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
                ('TOPPADDING',(0,0),(-1,-1),6), ('BOTTOMPADDING',(0,0),(-1,-1),6),
            ]))
            frame = Table([[Paragraph(titre_txt, section_style)], [inner]], colWidths=[8.5*cm])
            frame.setStyle(TableStyle([
                ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('LEFTPADDING',(0,0),(-1,0),0),('RIGHTPADDING',(0,0),(-1,0),0),
                ('TOPPADDING',(0,0),(-1,0),0), ('BOTTOMPADDING',(0,0),(-1,0),8),
                ('BOX',(0,1),(0,1),1.5,colors.Color(0.85,0.85,0.85)),
                ('ROUNDEDCORNERS',[10,10,10,10]),
                ('LEFTPADDING',(0,1),(0,1),15),('RIGHTPADDING',(0,1),(0,1),15),
                ('TOPPADDING',(0,1),(0,1),15), ('BOTTOMPADDING',(0,1),(0,1),15),
            ]))
            return frame

        elements.append(Paragraph("RAPPORT DE CHIRURGIE AVEC RÉSULTAT", titre_style))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style))
        elements.append(Spacer(1, 0.5*cm))

        frame_patient = _make_frame("INFORMATIONS PATIENT", [
            [Paragraph("<b>Nom</b>", label_style),       Paragraph(str(_v(chirurgie,'patient_nom')), info_style)],
            [Paragraph("<b>Prénom</b>", label_style),    Paragraph(str(_v(chirurgie,'patient_prenom')), info_style)],
            [Paragraph("<b>Téléphone</b>", label_style), Paragraph(str(_v(chirurgie,'patient_telephone')), info_style)],
            [Paragraph("<b>Adresse</b>", label_style),   Paragraph(str(_v(chirurgie,'patient_adresse')), info_style)],
        ], [3*cm, 5.5*cm])
        frame_personnel = _make_frame("CHIRURGIEN", [
            [Paragraph("<b>Nom</b>", label_style),      Paragraph(str(_v(chirurgie,'personnel_nom')), info_style)],
            [Paragraph("<b>Prénom</b>", label_style),   Paragraph(str(_v(chirurgie,'personnel_prenom')), info_style)],
            [Paragraph("<b>Fonction</b>", label_style), Paragraph(str(_v(chirurgie,'personnel_fonction')), info_style)],
            ["", ""],
        ], [3*cm, 5.5*cm])

        elements.append(Spacer(1, 0.3*cm))
        duo = Table([[frame_patient, "", frame_personnel]], colWidths=[8.5*cm, 0.5*cm, 8.5*cm])
        duo.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
            ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
        elements.append(duo)
        elements.append(Spacer(1, 0.8*cm))

        elements.append(Paragraph("DÉTAILS DE LA CHIRURGIE", section_style))
        elements.append(Spacer(1, 0.3*cm))
        frais = _v(chirurgie, 'frais_chururgie', 0)
        try:
            frais_fmt = f"{float(frais):,.0f} GNF".replace(',', ' ')
        except Exception:
            frais_fmt = f"{frais} GNF"

        data_chir = [
            [Paragraph("<b>Code Chirurgie</b>", label_style), Paragraph(str(_v(chirurgie,'code')), info_style),
             Paragraph("<b>Date</b>", label_style),            Paragraph(str(_v(chirurgie,'date_chururgie')), info_style)],
            [Paragraph("<b>Libellé</b>", label_style),         Paragraph(str(_v(chirurgie,'libelle_chururgie')), info_style),
             Paragraph("<b>Frais</b>", label_style),            Paragraph(frais_fmt, info_style)],
            [Paragraph("<b>Statut Facture</b>", label_style),  Paragraph(str(_v(chirurgie,'statut_facture')), info_style),
             "", ""],
        ]
        chir_table = Table(data_chir, colWidths=[4*cm, 5*cm, 3*cm, 5*cm])
        chir_table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),colors.Color(0.98,0.98,0.99)),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
            ('TOPPADDING',(0,0),(-1,-1),8),  ('BOTTOMPADDING',(0,0),(-1,-1),8),
            ('BOX',(0,0),(-1,-1),1.5,colors.Color(0.90,0.91,0.93)),
            ('ROUNDEDCORNERS',[10,10,10,10]),
        ]))
        elements.append(chir_table)
        elements.append(Spacer(1, 0.8*cm))

        if resultat:
            inner_res = Table([
                [Paragraph("<b>Référence</b>", label_style),     Paragraph(str(_v(resultat,'id_resultat')), info_style),
                 Paragraph("<b>Date</b>", label_style),           Paragraph(str(_v(resultat,'date_upload')), info_style)],
                [Paragraph("<b>Type de fichier</b>", label_style),Paragraph(str(_v(resultat,'type_fichier')), info_style),
                 Paragraph("<b>Confidentialité</b>", label_style),Paragraph(str(_v(resultat,'niveau_confidentialite')), info_style)],
                [Paragraph("<b>Description</b>", label_style),    Paragraph(str(_v(resultat,'description')), info_style), "", ""],
            ], colWidths=[4*cm, 5.5*cm, 3*cm, 5*cm])
            inner_res.setStyle(TableStyle([
                ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
                ('TOPPADDING',(0,0),(-1,-1),6), ('BOTTOMPADDING',(0,0),(-1,-1),6),
            ]))
            frame_res = Table([[Paragraph("RÉSULTAT MÉDICAL", section_style)], [inner_res]], colWidths=[17.5*cm])
            frame_res.setStyle(TableStyle([
                ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('LEFTPADDING',(0,0),(-1,0),0),('RIGHTPADDING',(0,0),(-1,0),0),
                ('TOPPADDING',(0,0),(-1,0),0), ('BOTTOMPADDING',(0,0),(-1,0),8),
                ('BOX',(0,1),(0,1),1.5,colors.Color(0.85,0.85,0.85)),
                ('ROUNDEDCORNERS',[10,10,10,10]),
                ('LEFTPADDING',(0,1),(0,1),15),('RIGHTPADDING',(0,1),(0,1),15),
                ('TOPPADDING',(0,1),(0,1),15), ('BOTTOMPADDING',(0,1),(0,1),15),
            ]))
            elements.append(frame_res)

        if fichier_bytes and type_fichier_res == 'image':
            import io
            from reportlab.platypus import Image as RLImage
            try:
                elements.append(Spacer(1, 0.6*cm))
                img = RLImage(io.BytesIO(fichier_bytes), width=14*cm, height=10*cm, kind='proportional')
                frame_img = Table([[Paragraph("FICHIER RÉSULTAT", section_style)], [img]], colWidths=[17.5*cm])
                frame_img.setStyle(TableStyle([
                    ('VALIGN',(0,0),(-1,-1),'TOP'), ('ALIGN',(0,1),(0,1),'CENTER'),
                    ('LEFTPADDING',(0,0),(-1,0),0), ('RIGHTPADDING',(0,0),(-1,0),0),
                    ('TOPPADDING',(0,0),(-1,0),0),  ('BOTTOMPADDING',(0,0),(-1,0),8),
                    ('BOX',(0,1),(0,1),1.5,colors.Color(0.85,0.85,0.85)),
                    ('ROUNDEDCORNERS',[10,10,10,10]),
                    ('LEFTPADDING',(0,1),(0,1),15), ('RIGHTPADDING',(0,1),(0,1),15),
                    ('TOPPADDING',(0,1),(0,1),15),  ('BOTTOMPADDING',(0,1),(0,1),15),
                ]))
                elements.append(frame_img)
            except Exception:
                pass

        elements.append(Spacer(1, 1*cm))

        def ajouter_entete(c, doc):
            dessiner_entete_et_fond(c, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf
