from services.pdf_actes._base import (
    dessiner_entete_et_fond,
    A4, cm, colors, SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, getSampleStyleSheet, ParagraphStyle,
    datetime, os
)

class RapportActivitesFournisseurPDF:

    @staticmethod
    def _create_styles():
        styles = getSampleStyleSheet()
        bleu = colors.Color(0.15, 0.38, 0.93)
        return {
            'titre': ParagraphStyle(
                'RptActFourTitle', parent=styles['Heading1'],
                fontSize=16, spaceAfter=20, alignment=1, textColor=bleu
            ),
            'date_gen': ParagraphStyle(
                'RptActFourDateGen', parent=styles['Normal'],
                fontSize=10, alignment=2, textColor=colors.gray
            ),
            'sous_titre': ParagraphStyle(
                'RptActFourSousTitre', parent=styles['Normal'],
                fontSize=12, fontName='Helvetica-Bold', textColor=bleu,
                spaceBefore=10, spaceAfter=8
            ),
            'stats': ParagraphStyle(
                'RptActFourStats', parent=styles['Normal'],
                fontSize=10, textColor=colors.black,
                spaceBefore=2, spaceAfter=2
            ),
            'cell': ParagraphStyle(
                'RptActFourCell', parent=styles['Normal'],
                fontSize=9, leading=11
            ),
            'header': ParagraphStyle(
                'RptActFourHdr', parent=styles['Normal'],
                fontSize=10, textColor=colors.white, fontName='Helvetica-Bold'
            ),
            'total': ParagraphStyle(
                'RptActFourTot', parent=styles['Normal'],
                fontSize=10, fontName='Helvetica-Bold', textColor=bleu, alignment=2
            ),
            'bleu': bleu
        }

    @staticmethod
    def generer_pdf_activites_un_fournisseur(fournisseur, stats, info_cabinet, chemin_pdf=None):
        """
        Génère le PDF des activités pour un seul fournisseur.
        """
        import tempfile
        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="activites_fournisseur_")
            os.close(fd)

        doc = SimpleDocTemplate(
            chemin_pdf, pagesize=A4,
            leftMargin=1.5*cm, rightMargin=1.5*cm,
            topMargin=3*cm, bottomMargin=1.5*cm
        )
        s = RapportActivitesFournisseurPDF._create_styles()
        elements = []

        elements.append(Paragraph("RAPPORT — ACTIVITÉS DU FOURNISSEUR", s['titre']))
        elements.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            s['date_gen']
        ))
        elements.append(Spacer(1, 0.3*cm))

        nom = fournisseur.get('nom_entreprise', '')
        email = fournisseur.get('email_fournisseur', '')
        elements.append(Paragraph(f"Fournisseur : {nom} ({email})", s['sous_titre']))
        elements.append(Paragraph(f"Nombre de produits : {stats.get('nb_produits', 0)}", s['stats']))
        elements.append(Paragraph(f"Quantité totale fournie : {stats.get('quantite_totale', 0)}", s['stats']))
        elements.append(Spacer(1, 0.5*cm))

        produits = stats.get("produits", [])
        if produits:
            header_row = [
                Paragraph("<b>Nom du Produit / Code</b>", s['header']),
                Paragraph("<b>Quantité Fournie</b>", s['header']),
            ]
            data = [header_row]

            total_qte = 0
            for prod in produits:
                nom_prod = str(prod.get("nom", prod.get("code_produit", "")))
                qte = prod.get("quantite", 0)
                try:
                    total_qte += int(float(qte))
                except:
                    pass
                data.append([
                    Paragraph(nom_prod, s['cell']),
                    Paragraph(str(qte), s['cell']),
                ])

            nb = len(data)
            data.append([
                Paragraph("Total Global :", s['total']),
                Paragraph(str(total_qte), s['total']),
            ])

            col_widths = [11.0*cm, 5.0*cm]
            tbl = Table(data, colWidths=col_widths, repeatRows=1)
            tbl.setStyle(TableStyle([
                ('BACKGROUND',    (0, 0), (-1, 0),      s['bleu']),
                ('TEXTCOLOR',     (0, 0), (-1, 0),      colors.white),
                ('FONTNAME',      (0, 0), (-1, 0),      'Helvetica-Bold'),
                ('ALIGN',         (0, 0), (-1, 0),      'CENTER'),
                ('VALIGN',        (0, 0), (-1, -1),     'MIDDLE'),
                ('LEFTPADDING',   (0, 0), (-1, -1),     8),
                ('RIGHTPADDING',  (0, 0), (-1, -1),     8),
                ('TOPPADDING',    (0, 0), (-1, -1),     6),
                ('BOTTOMPADDING', (0, 0), (-1, -1),     6),
                ('BACKGROUND',    (0, 1), (-1, nb - 1), colors.Color(0.98, 0.98, 0.99)),
                ('LINEBELOW',     (0, 0), (-1, 0),      1,   s['bleu']),
                ('LINEBELOW',     (0, 1), (-1, nb - 1), 0.5, colors.Color(0.90, 0.91, 0.93)),
                ('BACKGROUND',    (0, -1), (-1, -1),    colors.Color(0.92, 0.95, 1.0)),
                ('BOX',           (0, 0), (-1, -1),     1.5, colors.Color(0.90, 0.91, 0.93)),
            ]))
            elements.append(tbl)
        else:
            elements.append(Paragraph("<i>Aucun produit fourni enregistré pour ce fournisseur.</i>", s['cell']))

        def ajouter_entete(c, doc):
            dessiner_entete_et_fond(c, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf

    @staticmethod
    def generer_pdf_toutes_activites(liste_fournisseurs_stats, info_cabinet, chemin_pdf=None):
        """
        Génère le PDF global des activités pour tous les fournisseurs.
        liste_fournisseurs_stats est une liste de dicts:
        [{'fournisseur': {...}, 'stats': {...}}, ...]
        """
        import tempfile
        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="rapport_global_activites_")
            os.close(fd)

        doc = SimpleDocTemplate(
            chemin_pdf, pagesize=A4,
            leftMargin=1.5*cm, rightMargin=1.5*cm,
            topMargin=3*cm, bottomMargin=1.5*cm
        )
        s = RapportActivitesFournisseurPDF._create_styles()
        elements = []

        elements.append(Paragraph("RAPPORT GLOBAL — ACTIVITÉS DES FOURNISSEURS", s['titre']))
        elements.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            s['date_gen']
        ))
        elements.append(Spacer(1, 0.5*cm))

        for idx, item in enumerate(liste_fournisseurs_stats):
            fournisseur = item.get('fournisseur', {})
            stats = item.get('stats', {})
            nom = fournisseur.get('nom_entreprise', '')
            email = fournisseur.get('email_fournisseur', '')
            
            elements.append(Paragraph(f"Fournisseur : {nom} ({email})", s['sous_titre']))
            
            produits = stats.get("produits", [])
            if produits:
                header_row = [
                    Paragraph("<b>Nom du Produit / Code</b>", s['header']),
                    Paragraph("<b>Quantité Fournie</b>", s['header']),
                ]
                data = [header_row]

                total_qte = 0
                for prod in produits:
                    nom_prod = str(prod.get("nom", prod.get("code_produit", "")))
                    qte = prod.get("quantite", 0)
                    try:
                        total_qte += int(float(qte))
                    except:
                        pass
                    data.append([
                        Paragraph(nom_prod, s['cell']),
                        Paragraph(str(qte), s['cell']),
                    ])

                nb = len(data)
                data.append([
                    Paragraph("Total pour ce fournisseur :", s['total']),
                    Paragraph(str(total_qte), s['total']),
                ])

                col_widths = [11.0*cm, 5.0*cm]
                tbl = Table(data, colWidths=col_widths, repeatRows=1)
                tbl.setStyle(TableStyle([
                    ('BACKGROUND',    (0, 0), (-1, 0),      s['bleu']),
                    ('TEXTCOLOR',     (0, 0), (-1, 0),      colors.white),
                    ('FONTNAME',      (0, 0), (-1, 0),      'Helvetica-Bold'),
                    ('ALIGN',         (0, 0), (-1, 0),      'CENTER'),
                    ('VALIGN',        (0, 0), (-1, -1),     'MIDDLE'),
                    ('LEFTPADDING',   (0, 0), (-1, -1),     8),
                    ('RIGHTPADDING',  (0, 0), (-1, -1),     8),
                    ('TOPPADDING',    (0, 0), (-1, -1),     6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1),     6),
                    ('BACKGROUND',    (0, 1), (-1, nb - 1), colors.Color(0.98, 0.98, 0.99)),
                    ('LINEBELOW',     (0, 0), (-1, 0),      1,   s['bleu']),
                    ('LINEBELOW',     (0, 1), (-1, nb - 1), 0.5, colors.Color(0.90, 0.91, 0.93)),
                    ('BACKGROUND',    (0, -1), (-1, -1),    colors.Color(0.92, 0.95, 1.0)),
                    ('BOX',           (0, 0), (-1, -1),     1.5, colors.Color(0.90, 0.91, 0.93)),
                ]))
                elements.append(tbl)
            else:
                elements.append(Paragraph("<i>Aucun produit fourni enregistré pour ce fournisseur.</i>", s['cell']))
            
            elements.append(Spacer(1, 0.8*cm))

        def ajouter_entete(c, doc):
            dessiner_entete_et_fond(c, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf
