from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
import os


class HistoriquePatientPDFService:
    """
    Service pour générer des rapports PDF de l'historique patient.
    """

    @staticmethod
    def _obtenir_valeur(obj, cle, valeur_par_defaut=''):
        """Obtient une valeur d'un objet ou d'un dictionnaire."""
        if isinstance(obj, dict):
            return obj.get(cle, valeur_par_defaut)
        else:
            return getattr(obj, cle, valeur_par_defaut)

    @staticmethod
    def dessiner_entete_et_fond(c, width, height, info_cabinet):
        """
        Gère l'aspect visuel commun : Entête de la clinique.
        """
        nom_clinique = info_cabinet.get("nom_cabinet", "CLINIQUE")
        adresse_clinique = info_cabinet.get("adresse_cabinet", "")
        logo_path = info_cabinet.get("logo")
        bleu_medical = colors.Color(0.15, 0.38, 0.93)  # Bleu

        # --- ENTÊTE (Texte à gauche + Logo à droite) ---
        # Texte à gauche
        c.setFillColor(bleu_medical)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(0.6*cm, height - 1.1*cm, nom_clinique.upper())

        c.setFillColor(colors.black)
        c.setFont("Helvetica", 7)
        c.drawString(0.6*cm, height - 1.5*cm, adresse_clinique)
        
        # Logo à droite
        if logo_path and os.path.exists(logo_path):
            # Positionner le logo en haut à droite
            c.drawImage(logo_path, width - 2*cm, height - 2*cm, width=1.3*cm, height=1.3*cm, mask='auto')

        # Ligne de séparation sous l'entête
        c.setStrokeColor(bleu_medical)
        c.setLineWidth(1.5)
        c.line(0.6*cm, height - 2.3*cm, width - 0.6*cm, height - 2.3*cm)

    @staticmethod
    def generer_pdf_consultation(consultation, info_cabinet, chemin_pdf=None):
        """
        Génère un PDF pour une consultation complète.
        
        Args:
            consultation: Dictionnaire contenant les détails de la consultation
            info_cabinet: Informations du cabinet (nom, logo, adresse)
            chemin_pdf: Chemin où sauvegarder le PDF (si None, crée un fichier temporaire)
        
        Returns:
            str: Chemin du fichier PDF généré
        """
        import tempfile
        
        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="consultation_")
            os.close(fd)
        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Style personnalisé pour le titre
        titre_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1,  # Centré
            textColor=colors.Color(0.15, 0.38, 0.93)  # Bleu
        )

        # Titre du rapport
        titre = Paragraph("RAPPORT DE CONSULTATION", titre_style)
        elements.append(titre)
        elements.append(Spacer(1, 0.5*cm))

        # Date de génération
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=2,  # Droite
            textColor=colors.gray
        )
        date_texte = f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
        elements.append(Paragraph(date_texte, date_style))
        elements.append(Spacer(1, 0.5*cm))

        # Informations de la consultation dans des sections
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            leading=12
        )
        
        label_style = ParagraphStyle(
            'LabelStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.Color(0.42, 0.45, 0.50),
            spaceAfter=2
        )

        code = HistoriquePatientPDFService._obtenir_valeur(consultation, 'code', 'N/A')
        date_consultation = HistoriquePatientPDFService._obtenir_valeur(consultation, 'date_consultation', 'N/A')
        diagnostique = HistoriquePatientPDFService._obtenir_valeur(consultation, 'diagnostique', 'N/A')
        frais = HistoriquePatientPDFService._obtenir_valeur(consultation, 'frais_consultation', 0)
        statut_facture = HistoriquePatientPDFService._obtenir_valeur(consultation, 'statut_facture', 'N/A')

        # Informations patient
        patient_nom = HistoriquePatientPDFService._obtenir_valeur(consultation, 'patient_nom', 'N/A')
        patient_prenom = HistoriquePatientPDFService._obtenir_valeur(consultation, 'patient_prenom', 'N/A')
        patient_telephone = HistoriquePatientPDFService._obtenir_valeur(consultation, 'patient_telephone', 'N/A')
        patient_adresse = HistoriquePatientPDFService._obtenir_valeur(consultation, 'patient_adresse', 'N/A')

        # Informations personnel
        personnel_nom = HistoriquePatientPDFService._obtenir_valeur(consultation, 'personnel_nom', 'N/A')
        personnel_prenom = HistoriquePatientPDFService._obtenir_valeur(consultation, 'personnel_prenom', 'N/A')
        personnel_fonction = HistoriquePatientPDFService._obtenir_valeur(consultation, 'personnel_fonction', 'N/A')

        # Style pour les titres de section
        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Heading2'],
            fontSize=13,
            spaceAfter=8,
            textColor=colors.Color(0.15, 0.38, 0.93),
            fontName='Helvetica-Bold'
        )

        # === SECTION 1 : PATIENT ET PERSONNEL CÔTE À CÔTE ===
        elements.append(Spacer(1, 0.3*cm))
        
        # Créer deux frames séparés côte à côte
        # Frame Patient
        frame_patient = Table([
            [Paragraph("INFORMATIONS PATIENT", section_style)],
            [Table([
                [Paragraph("<b>Nom</b>", label_style), Paragraph(str(patient_nom), info_style)],
                [Paragraph("<b>Prénom</b>", label_style), Paragraph(str(patient_prenom), info_style)],
                [Paragraph("<b>Téléphone</b>", label_style), Paragraph(str(patient_telephone), info_style)],
                [Paragraph("<b>Adresse</b>", label_style), Paragraph(str(patient_adresse), info_style)]
            ], colWidths=[3*cm, 5.5*cm])]
        ], colWidths=[8.5*cm])
        
        frame_patient.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, 0), 0),
            ('RIGHTPADDING', (0, 0), (-1, 0), 0),
            ('TOPPADDING', (0, 0), (-1, 0), 0),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            # Bordure autour du contenu
            ('BOX', (0, 1), (0, 1), 1.5, colors.Color(0.85, 0.85, 0.85)),
            ('ROUNDEDCORNERS', [10, 10, 10, 10]),
            ('LEFTPADDING', (0, 1), (0, 1), 15),
            ('RIGHTPADDING', (0, 1), (0, 1), 15),
            ('TOPPADDING', (0, 1), (0, 1), 15),
            ('BOTTOMPADDING', (0, 1), (0, 1), 15),
        ]))
        
        # Frame Personnel
        frame_personnel = Table([
            [Paragraph("PERSONNEL SOIGNANT", section_style)],
            [Table([
                [Paragraph("<b>Nom</b>", label_style), Paragraph(str(personnel_nom), info_style)],
                [Paragraph("<b>Prénom</b>", label_style), Paragraph(str(personnel_prenom), info_style)],
                [Paragraph("<b>Fonction</b>", label_style), Paragraph(str(personnel_fonction), info_style)],
                ["", ""]  # Ligne vide pour alignement
            ], colWidths=[3*cm, 5.5*cm])]
        ], colWidths=[8.5*cm])
        
        frame_personnel.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, 0), 0),
            ('RIGHTPADDING', (0, 0), (-1, 0), 0),
            ('TOPPADDING', (0, 0), (-1, 0), 0),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            # Bordure autour du contenu
            ('BOX', (0, 1), (0, 1), 1.5, colors.Color(0.85, 0.85, 0.85)),
            ('ROUNDEDCORNERS', [10, 10, 10, 10]),
            ('LEFTPADDING', (0, 1), (0, 1), 15),
            ('RIGHTPADDING', (0, 1), (0, 1), 15),
            ('TOPPADDING', (0, 1), (0, 1), 15),
            ('BOTTOMPADDING', (0, 1), (0, 1), 15),
        ]))
        
        # Style pour les sous-tableaux internes des deux frames
        for frame in [frame_patient, frame_personnel]:
            inner_table = frame._cellvalues[1][0]
            if inner_table:
                inner_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
        
        # Mettre les deux frames côte à côte avec un espace de 0.5cm entre eux
        patient_personnel_table = Table([[frame_patient, "", frame_personnel]], colWidths=[8.5*cm, 0.5*cm, 8.5*cm])
        patient_personnel_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        elements.append(patient_personnel_table)
        elements.append(Spacer(1, 0.8*cm))

        # === SECTION 2 : DÉTAILS CONSULTATION ===
        elements.append(Paragraph("DÉTAILS DE LA CONSULTATION", section_style))
        elements.append(Spacer(1, 0.3*cm))
        
        # Création du tableau pour afficher les informations en grille
        data = [
            [Paragraph("<b>Code Consultation</b>", label_style), Paragraph(str(code), info_style),
             Paragraph("<b>Date</b>", label_style), Paragraph(str(date_consultation), info_style)],
            [Paragraph("<b>Frais</b>", label_style), Paragraph(f"{frais:,.0f} GNF".replace(',', ' '), info_style),
             Paragraph("<b>Statut Facture</b>", label_style), Paragraph(str(statut_facture), info_style)],
            [Paragraph("<b>Diagnostique</b>", label_style), 
             Paragraph(str(diagnostique), info_style), "", ""]
        ]
        
        info_table = Table(data, colWidths=[4*cm, 5*cm, 3*cm, 5*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.98, 0.98, 0.99)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.Color(0.90, 0.91, 0.93)),
            ('ROUNDEDCORNERS', [10, 10, 10, 10]),
        ]))
        
        elements.append(info_table)

        elements.append(Spacer(1, 1*cm))

        # Génération du PDF avec entête personnalisé
        def ajouter_entete(canvas, doc):
            HistoriquePatientPDFService.dessiner_entete_et_fond(canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)

        return chemin_pdf

    @staticmethod
    def generer_pdf_consultation_avec_resultat(consultation, resultat, info_cabinet, chemin_pdf=None,
                                                fichier_bytes=None, type_fichier_res=None):
        """
        Génère un PDF combiné consultation + résultat médical, même format que generer_pdf_consultation.

        Args:
            consultation: dict des détails de la consultation
            resultat: dict des détails du résultat médical
            info_cabinet: Informations du cabinet (nom, logo, adresse)
            chemin_pdf: Chemin de sortie (None = fichier temporaire)

        Returns:
            str: Chemin du PDF généré
        """
        import tempfile

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="consultation_resultat_")
            os.close(fd)

        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        bleu = colors.Color(0.15, 0.38, 0.93)

        titre_style = ParagraphStyle(
            'CustomTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu
        )
        date_style = ParagraphStyle(
            'DateStyle', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        section_style = ParagraphStyle(
            'SectionStyle', parent=styles['Heading2'],
            fontSize=13, spaceAfter=8, textColor=bleu, fontName='Helvetica-Bold'
        )
        info_style = ParagraphStyle(
            'InfoStyle', parent=styles['Normal'],
            fontSize=10, spaceAfter=4, leading=12
        )
        label_style = ParagraphStyle(
            'LabelStyle', parent=styles['Normal'],
            fontSize=9, textColor=colors.Color(0.42, 0.45, 0.50), spaceAfter=2
        )

        def _v(obj, key, default='N/A'):
            return HistoriquePatientPDFService._obtenir_valeur(obj, key, default)

        # ---- Titre ----
        elements.append(Paragraph("RAPPORT DE CONSULTATION AVEC RÉSULTAT", titre_style))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style))
        elements.append(Spacer(1, 0.5*cm))

        # ---- Section Patient + Personnel côte à côte ----
        patient_nom = _v(consultation, 'patient_nom')
        patient_prenom = _v(consultation, 'patient_prenom')
        patient_telephone = _v(consultation, 'patient_telephone')
        patient_adresse = _v(consultation, 'patient_adresse')
        personnel_nom = _v(consultation, 'personnel_nom')
        personnel_prenom = _v(consultation, 'personnel_prenom')
        personnel_fonction = _v(consultation, 'personnel_fonction')

        def _make_frame(titre_txt, rows, col_widths):
            inner = Table(rows, colWidths=col_widths)
            inner.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            frame = Table([
                [Paragraph(titre_txt, section_style)],
                [inner]
            ], colWidths=[8.5*cm])
            frame.setStyle(TableStyle([
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
            return frame

        frame_patient = _make_frame("INFORMATIONS PATIENT", [
            [Paragraph("<b>Nom</b>", label_style), Paragraph(str(patient_nom), info_style)],
            [Paragraph("<b>Prénom</b>", label_style), Paragraph(str(patient_prenom), info_style)],
            [Paragraph("<b>Téléphone</b>", label_style), Paragraph(str(patient_telephone), info_style)],
            [Paragraph("<b>Adresse</b>", label_style), Paragraph(str(patient_adresse), info_style)],
        ], [3*cm, 5.5*cm])

        frame_personnel = _make_frame("PERSONNEL SOIGNANT", [
            [Paragraph("<b>Nom</b>", label_style), Paragraph(str(personnel_nom), info_style)],
            [Paragraph("<b>Prénom</b>", label_style), Paragraph(str(personnel_prenom), info_style)],
            [Paragraph("<b>Fonction</b>", label_style), Paragraph(str(personnel_fonction), info_style)],
            ["", ""],
        ], [3*cm, 5.5*cm])

        elements.append(Spacer(1, 0.3*cm))
        duo = Table([[frame_patient, "", frame_personnel]], colWidths=[8.5*cm, 0.5*cm, 8.5*cm])
        duo.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(duo)
        elements.append(Spacer(1, 0.8*cm))

        # ---- Détails consultation ----
        elements.append(Paragraph("DÉTAILS DE LA CONSULTATION", section_style))
        elements.append(Spacer(1, 0.3*cm))

        code = _v(consultation, 'code')
        date_consultation = _v(consultation, 'date_consultation')
        diagnostique = _v(consultation, 'diagnostique')
        frais = _v(consultation, 'frais_consultation', 0)
        statut_facture = _v(consultation, 'statut_facture')

        data_consult = [
            [Paragraph("<b>Code Consultation</b>", label_style), Paragraph(str(code), info_style),
             Paragraph("<b>Date</b>", label_style), Paragraph(str(date_consultation), info_style)],
            [Paragraph("<b>Frais</b>", label_style),
             Paragraph(f"{frais:,.0f} GNF".replace(',', ' '), info_style),
             Paragraph("<b>Statut Facture</b>", label_style), Paragraph(str(statut_facture), info_style)],
            [Paragraph("<b>Diagnostique</b>", label_style), Paragraph(str(diagnostique), info_style), "", ""],
        ]
        consult_table = Table(data_consult, colWidths=[4*cm, 5*cm, 3*cm, 5*cm])
        consult_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.98, 0.98, 0.99)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.Color(0.90, 0.91, 0.93)),
            ('ROUNDEDCORNERS', [10, 10, 10, 10]),
        ]))
        elements.append(consult_table)
        elements.append(Spacer(1, 0.8*cm))

        # ---- Section Résultat médical (frame identique aux autres sections) ----
        if resultat:
            id_res = _v(resultat, 'id_resultat')
            date_upload = _v(resultat, 'date_upload')
            type_fichier_val = _v(resultat, 'type_fichier')
            niveau = _v(resultat, 'niveau_confidentialite')
            description = _v(resultat, 'description')

            inner_res = Table([
                [Paragraph("<b>Référence</b>", label_style), Paragraph(str(id_res), info_style),
                 Paragraph("<b>Date</b>", label_style), Paragraph(str(date_upload), info_style)],
                [Paragraph("<b>Type de fichier</b>", label_style), Paragraph(str(type_fichier_val), info_style),
                 Paragraph("<b>Confidentialité</b>", label_style), Paragraph(str(niveau), info_style)],
                [Paragraph("<b>Description</b>", label_style), Paragraph(str(description), info_style), "", ""],
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
        else:
            no_res_style = ParagraphStyle(
                'NoRes', parent=styles['Normal'],
                fontSize=11, textColor=colors.gray, alignment=1
            )
            elements.append(Paragraph("Aucun résultat médical disponible.", no_res_style))

        # ---- Image du résultat ----
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
            HistoriquePatientPDFService.dessiner_entete_et_fond(
                canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet
            )

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf

    @staticmethod
    def generer_pdf_examen(examen, info_cabinet, chemin_pdf=None):
        """
        Génère un PDF pour un examen complet (même format que generer_pdf_consultation).

        Args:
            examen: Dict contenant les détails de l'examen (résultat de examen_complet)
            info_cabinet: Informations du cabinet (nom, logo, adresse)
            chemin_pdf: Chemin de sortie (None = fichier temporaire)

        Returns:
            str: Chemin du PDF généré
        """
        import tempfile

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="examen_")
            os.close(fd)

        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        bleu = colors.Color(0.15, 0.38, 0.93)

        titre_style = ParagraphStyle(
            'CustomTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu
        )
        date_style = ParagraphStyle(
            'DateStyle', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        section_style = ParagraphStyle(
            'SectionStyle', parent=styles['Heading2'],
            fontSize=13, spaceAfter=8, textColor=bleu, fontName='Helvetica-Bold'
        )
        info_style = ParagraphStyle(
            'InfoStyle', parent=styles['Normal'],
            fontSize=10, spaceAfter=4, leading=12
        )
        label_style = ParagraphStyle(
            'LabelStyle', parent=styles['Normal'],
            fontSize=9, textColor=colors.Color(0.42, 0.45, 0.50), spaceAfter=2
        )

        def _v(obj, key, default='N/A'):
            return HistoriquePatientPDFService._obtenir_valeur(obj, key, default)

        elements.append(Paragraph("RAPPORT D'EXAMEN", titre_style))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style))
        elements.append(Spacer(1, 0.5*cm))

        patient_nom = _v(examen, 'patient_nom')
        patient_prenom = _v(examen, 'patient_prenom')
        patient_telephone = _v(examen, 'patient_telephone')
        patient_adresse = _v(examen, 'patient_adresse')
        personnel_nom = _v(examen, 'personnel_nom')
        personnel_prenom = _v(examen, 'personnel_prenom')
        personnel_fonction = _v(examen, 'personnel_fonction')

        def _make_frame(titre_txt, rows, col_widths):
            inner = Table(rows, colWidths=col_widths)
            inner.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            frame = Table([[Paragraph(titre_txt, section_style)], [inner]], colWidths=[8.5*cm])
            frame.setStyle(TableStyle([
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
            return frame

        frame_patient = _make_frame("INFORMATIONS PATIENT", [
            [Paragraph("<b>Nom</b>", label_style), Paragraph(str(patient_nom), info_style)],
            [Paragraph("<b>Prénom</b>", label_style), Paragraph(str(patient_prenom), info_style)],
            [Paragraph("<b>Téléphone</b>", label_style), Paragraph(str(patient_telephone), info_style)],
            [Paragraph("<b>Adresse</b>", label_style), Paragraph(str(patient_adresse), info_style)],
        ], [3*cm, 5.5*cm])

        frame_personnel = _make_frame("PERSONNEL SOIGNANT", [
            [Paragraph("<b>Nom</b>", label_style), Paragraph(str(personnel_nom), info_style)],
            [Paragraph("<b>Prénom</b>", label_style), Paragraph(str(personnel_prenom), info_style)],
            [Paragraph("<b>Fonction</b>", label_style), Paragraph(str(personnel_fonction), info_style)],
            ["", ""],
        ], [3*cm, 5.5*cm])

        elements.append(Spacer(1, 0.3*cm))
        duo = Table([[frame_patient, "", frame_personnel]], colWidths=[8.5*cm, 0.5*cm, 8.5*cm])
        duo.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(duo)
        elements.append(Spacer(1, 0.8*cm))

        elements.append(Paragraph("DÉTAILS DE L'EXAMEN", section_style))
        elements.append(Spacer(1, 0.3*cm))

        code = _v(examen, 'code')
        date_examen = _v(examen, 'date_examen')
        libelle = _v(examen, 'libelle_examen')
        conclusion = _v(examen, 'conclusion_medicale')
        frais = _v(examen, 'frais_examen', 0)
        statut_facture = _v(examen, 'statut_facture')

        try:
            frais_fmt = f"{float(frais):,.0f} GNF".replace(',', ' ')
        except Exception:
            frais_fmt = f"{frais} GNF"

        data_examen = [
            [Paragraph("<b>Code Examen</b>", label_style), Paragraph(str(code), info_style),
             Paragraph("<b>Date</b>", label_style), Paragraph(str(date_examen), info_style)],
            [Paragraph("<b>Libellé</b>", label_style), Paragraph(str(libelle), info_style),
             Paragraph("<b>Frais</b>", label_style), Paragraph(frais_fmt, info_style)],
            [Paragraph("<b>Statut Facture</b>", label_style), Paragraph(str(statut_facture), info_style),
             Paragraph("<b>Conclusion</b>", label_style), Paragraph(str(conclusion), info_style)],
        ]
        examen_table = Table(data_examen, colWidths=[4*cm, 5*cm, 3*cm, 5*cm])
        examen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.98, 0.98, 0.99)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.Color(0.90, 0.91, 0.93)),
            ('ROUNDEDCORNERS', [10, 10, 10, 10]),
        ]))
        elements.append(examen_table)
        elements.append(Spacer(1, 1*cm))

        def ajouter_entete(canvas, doc):
            HistoriquePatientPDFService.dessiner_entete_et_fond(
                canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet
            )

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf

    @staticmethod
    def generer_pdf_examen_avec_resultat(examen, resultat, info_cabinet, chemin_pdf=None,
                                          fichier_bytes=None, type_fichier_res=None):
        """
        Génère un PDF combiné examen + résultat médical (même format que generer_pdf_consultation_avec_resultat).

        Args:
            examen: Dict des détails de l'examen (résultat de examen_complet)
            resultat: Dict des détails du résultat médical
            info_cabinet: Informations du cabinet (nom, logo, adresse)
            chemin_pdf: Chemin de sortie (None = fichier temporaire)
            fichier_bytes: Bytes de l'image du résultat (optionnel)
            type_fichier_res: Type du fichier résultat (optionnel)

        Returns:
            str: Chemin du PDF généré
        """
        import tempfile

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="examen_resultat_")
            os.close(fd)

        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        bleu = colors.Color(0.15, 0.38, 0.93)

        titre_style = ParagraphStyle(
            'CustomTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu
        )
        date_style = ParagraphStyle(
            'DateStyle', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        section_style = ParagraphStyle(
            'SectionStyle', parent=styles['Heading2'],
            fontSize=13, spaceAfter=8, textColor=bleu, fontName='Helvetica-Bold'
        )
        info_style = ParagraphStyle(
            'InfoStyle', parent=styles['Normal'],
            fontSize=10, spaceAfter=4, leading=12
        )
        label_style = ParagraphStyle(
            'LabelStyle', parent=styles['Normal'],
            fontSize=9, textColor=colors.Color(0.42, 0.45, 0.50), spaceAfter=2
        )

        def _v(obj, key, default='N/A'):
            return HistoriquePatientPDFService._obtenir_valeur(obj, key, default)

        elements.append(Paragraph("RAPPORT D'EXAMEN AVEC RÉSULTAT", titre_style))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style))
        elements.append(Spacer(1, 0.5*cm))

        patient_nom = _v(examen, 'patient_nom')
        patient_prenom = _v(examen, 'patient_prenom')
        patient_telephone = _v(examen, 'patient_telephone')
        patient_adresse = _v(examen, 'patient_adresse')
        personnel_nom = _v(examen, 'personnel_nom')
        personnel_prenom = _v(examen, 'personnel_prenom')
        personnel_fonction = _v(examen, 'personnel_fonction')

        def _make_frame(titre_txt, rows, col_widths):
            inner = Table(rows, colWidths=col_widths)
            inner.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            frame = Table([[Paragraph(titre_txt, section_style)], [inner]], colWidths=[8.5*cm])
            frame.setStyle(TableStyle([
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
            return frame

        frame_patient = _make_frame("INFORMATIONS PATIENT", [
            [Paragraph("<b>Nom</b>", label_style), Paragraph(str(patient_nom), info_style)],
            [Paragraph("<b>Prénom</b>", label_style), Paragraph(str(patient_prenom), info_style)],
            [Paragraph("<b>Téléphone</b>", label_style), Paragraph(str(patient_telephone), info_style)],
            [Paragraph("<b>Adresse</b>", label_style), Paragraph(str(patient_adresse), info_style)],
        ], [3*cm, 5.5*cm])

        frame_personnel = _make_frame("PERSONNEL SOIGNANT", [
            [Paragraph("<b>Nom</b>", label_style), Paragraph(str(personnel_nom), info_style)],
            [Paragraph("<b>Prénom</b>", label_style), Paragraph(str(personnel_prenom), info_style)],
            [Paragraph("<b>Fonction</b>", label_style), Paragraph(str(personnel_fonction), info_style)],
            ["", ""],
        ], [3*cm, 5.5*cm])

        elements.append(Spacer(1, 0.3*cm))
        duo = Table([[frame_patient, "", frame_personnel]], colWidths=[8.5*cm, 0.5*cm, 8.5*cm])
        duo.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(duo)
        elements.append(Spacer(1, 0.8*cm))

        elements.append(Paragraph("DÉTAILS DE L'EXAMEN", section_style))
        elements.append(Spacer(1, 0.3*cm))

        code = _v(examen, 'code')
        date_examen = _v(examen, 'date_examen')
        libelle = _v(examen, 'libelle_examen')
        conclusion = _v(examen, 'conclusion_medicale')
        frais = _v(examen, 'frais_examen', 0)
        statut_facture = _v(examen, 'statut_facture')

        try:
            frais_fmt = f"{float(frais):,.0f} GNF".replace(',', ' ')
        except Exception:
            frais_fmt = f"{frais} GNF"

        data_examen = [
            [Paragraph("<b>Code Examen</b>", label_style), Paragraph(str(code), info_style),
             Paragraph("<b>Date</b>", label_style), Paragraph(str(date_examen), info_style)],
            [Paragraph("<b>Libellé</b>", label_style), Paragraph(str(libelle), info_style),
             Paragraph("<b>Frais</b>", label_style), Paragraph(frais_fmt, info_style)],
            [Paragraph("<b>Statut Facture</b>", label_style), Paragraph(str(statut_facture), info_style),
             Paragraph("<b>Conclusion</b>", label_style), Paragraph(str(conclusion), info_style)],
        ]
        examen_table = Table(data_examen, colWidths=[4*cm, 5*cm, 3*cm, 5*cm])
        examen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.98, 0.98, 0.99)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.Color(0.90, 0.91, 0.93)),
            ('ROUNDEDCORNERS', [10, 10, 10, 10]),
        ]))
        elements.append(examen_table)
        elements.append(Spacer(1, 0.8*cm))

        # ---- Section Résultat médical ----
        if resultat:
            id_res = _v(resultat, 'id_resultat')
            date_upload = _v(resultat, 'date_upload')
            type_fichier_val = _v(resultat, 'type_fichier')
            niveau = _v(resultat, 'niveau_confidentialite')
            description = _v(resultat, 'description')

            inner_res = Table([
                [Paragraph("<b>Référence</b>", label_style), Paragraph(str(id_res), info_style),
                 Paragraph("<b>Date</b>", label_style), Paragraph(str(date_upload), info_style)],
                [Paragraph("<b>Type de fichier</b>", label_style), Paragraph(str(type_fichier_val), info_style),
                 Paragraph("<b>Confidentialité</b>", label_style), Paragraph(str(niveau), info_style)],
                [Paragraph("<b>Description</b>", label_style), Paragraph(str(description), info_style), "", ""],
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
        else:
            no_res_style = ParagraphStyle(
                'NoRes', parent=styles['Normal'],
                fontSize=11, textColor=colors.gray, alignment=1
            )
            elements.append(Paragraph("Aucun résultat médical disponible.", no_res_style))

        # ---- Image du résultat ----
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
            HistoriquePatientPDFService.dessiner_entete_et_fond(
                canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet
            )

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf

    @staticmethod
    def generer_pdf_chirurgie(chirurgie, info_cabinet, chemin_pdf=None):
        """
        Génère un PDF pour une chirurgie (fiche de base sans compte rendu).

        Args:
            chirurgie: Dict ou objet contenant les détails de la chirurgie
            info_cabinet: Informations du cabinet (nom, logo, adresse)
            chemin_pdf: Chemin de sortie (None = fichier temporaire)

        Returns:
            str: Chemin du PDF généré
        """
        import tempfile

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="chirurgie_")
            os.close(fd)

        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        bleu = colors.Color(0.15, 0.38, 0.93)

        titre_style = ParagraphStyle(
            'ChirTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu
        )
        date_style = ParagraphStyle(
            'ChirDate', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        section_style = ParagraphStyle(
            'ChirSection', parent=styles['Heading2'],
            fontSize=13, spaceAfter=8, textColor=bleu, fontName='Helvetica-Bold'
        )
        info_style = ParagraphStyle(
            'ChirInfo', parent=styles['Normal'],
            fontSize=10, spaceAfter=4, leading=12
        )
        label_style = ParagraphStyle(
            'ChirLabel', parent=styles['Normal'],
            fontSize=9, textColor=colors.Color(0.42, 0.45, 0.50), spaceAfter=2
        )

        def _v(obj, key, default='N/A'):
            return HistoriquePatientPDFService._obtenir_valeur(obj, key, default)

        elements.append(Paragraph("RAPPORT DE CHIRURGIE", titre_style))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style))
        elements.append(Spacer(1, 0.5*cm))

        patient_nom      = _v(chirurgie, 'patient_nom')
        patient_prenom   = _v(chirurgie, 'patient_prenom')
        patient_telephone= _v(chirurgie, 'patient_telephone')
        patient_adresse  = _v(chirurgie, 'patient_adresse')
        personnel_nom    = _v(chirurgie, 'personnel_nom')
        personnel_prenom = _v(chirurgie, 'personnel_prenom')
        personnel_fonction = _v(chirurgie, 'personnel_fonction')

        def _make_frame(titre_txt, rows, col_widths):
            inner = Table(rows, colWidths=col_widths)
            inner.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            frame = Table([[Paragraph(titre_txt, section_style)], [inner]], colWidths=[8.5*cm])
            frame.setStyle(TableStyle([
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
            return frame

        frame_patient = _make_frame("INFORMATIONS PATIENT", [
            [Paragraph("<b>Nom</b>", label_style),       Paragraph(str(patient_nom), info_style)],
            [Paragraph("<b>Prénom</b>", label_style),    Paragraph(str(patient_prenom), info_style)],
            [Paragraph("<b>Téléphone</b>", label_style), Paragraph(str(patient_telephone), info_style)],
            [Paragraph("<b>Adresse</b>", label_style),   Paragraph(str(patient_adresse), info_style)],
        ], [3*cm, 5.5*cm])

        frame_personnel = _make_frame("CHIRURGIEN", [
            [Paragraph("<b>Nom</b>", label_style),      Paragraph(str(personnel_nom), info_style)],
            [Paragraph("<b>Prénom</b>", label_style),   Paragraph(str(personnel_prenom), info_style)],
            [Paragraph("<b>Fonction</b>", label_style), Paragraph(str(personnel_fonction), info_style)],
            ["", ""],
        ], [3*cm, 5.5*cm])

        elements.append(Spacer(1, 0.3*cm))
        duo = Table([[frame_patient, "", frame_personnel]], colWidths=[8.5*cm, 0.5*cm, 8.5*cm])
        duo.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(duo)
        elements.append(Spacer(1, 0.8*cm))

        elements.append(Paragraph("DÉTAILS DE LA CHIRURGIE", section_style))
        elements.append(Spacer(1, 0.3*cm))

        code           = _v(chirurgie, 'code')
        date_chir      = _v(chirurgie, 'date_chururgie')
        libelle        = _v(chirurgie, 'libelle_chururgie')
        frais          = _v(chirurgie, 'frais_chururgie', 0)
        statut_facture = _v(chirurgie, 'statut_facture')

        try:
            frais_fmt = f"{float(frais):,.0f} GNF".replace(',', ' ')
        except Exception:
            frais_fmt = f"{frais} GNF"

        data_chir = [
            [Paragraph("<b>Code Chirurgie</b>", label_style), Paragraph(str(code), info_style),
             Paragraph("<b>Date</b>", label_style), Paragraph(str(date_chir), info_style)],
            [Paragraph("<b>Libellé</b>", label_style), Paragraph(str(libelle), info_style),
             Paragraph("<b>Frais</b>", label_style), Paragraph(frais_fmt, info_style)],
            [Paragraph("<b>Statut Facture</b>", label_style), Paragraph(str(statut_facture), info_style),
             "", ""],
        ]
        chir_table = Table(data_chir, colWidths=[4*cm, 5*cm, 3*cm, 5*cm])
        chir_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.98, 0.98, 0.99)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.Color(0.90, 0.91, 0.93)),
            ('ROUNDEDCORNERS', [10, 10, 10, 10]),
        ]))
        elements.append(chir_table)
        elements.append(Spacer(1, 1*cm))

        def ajouter_entete(canvas, doc):
            HistoriquePatientPDFService.dessiner_entete_et_fond(
                canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet
            )

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf

    @staticmethod
    def generer_pdf_chirurgie_avec_compte_rendu(chirurgie, info_cabinet, chemin_pdf=None):
        """
        Génère un PDF chirurgie incluant le compte rendu opératoire.

        Args:
            chirurgie: Dict ou objet contenant les détails de la chirurgie
            info_cabinet: Informations du cabinet
            chemin_pdf: Chemin de sortie (None = fichier temporaire)

        Returns:
            str: Chemin du PDF généré
        """
        import tempfile

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="chirurgie_cr_")
            os.close(fd)

        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        bleu = colors.Color(0.15, 0.38, 0.93)

        titre_style = ParagraphStyle(
            'ChirCRTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu
        )
        date_style = ParagraphStyle(
            'ChirCRDate', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        section_style = ParagraphStyle(
            'ChirCRSection', parent=styles['Heading2'],
            fontSize=13, spaceAfter=8, textColor=bleu, fontName='Helvetica-Bold'
        )
        info_style = ParagraphStyle(
            'ChirCRInfo', parent=styles['Normal'],
            fontSize=10, spaceAfter=4, leading=12
        )
        label_style = ParagraphStyle(
            'ChirCRLabel', parent=styles['Normal'],
            fontSize=9, textColor=colors.Color(0.42, 0.45, 0.50), spaceAfter=2
        )
        body_style = ParagraphStyle(
            'ChirCRBody', parent=styles['Normal'],
            fontSize=10, leading=14, spaceAfter=6
        )

        def _v(obj, key, default='N/A'):
            return HistoriquePatientPDFService._obtenir_valeur(obj, key, default)

        elements.append(Paragraph("RAPPORT DE CHIRURGIE — COMPTE RENDU OPÉRATOIRE", titre_style))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style))
        elements.append(Spacer(1, 0.5*cm))

        # Infos patient / chirurgien
        patient_nom       = _v(chirurgie, 'patient_nom')
        patient_prenom    = _v(chirurgie, 'patient_prenom')
        patient_telephone = _v(chirurgie, 'patient_telephone')
        patient_adresse   = _v(chirurgie, 'patient_adresse')
        personnel_nom     = _v(chirurgie, 'personnel_nom')
        personnel_prenom  = _v(chirurgie, 'personnel_prenom')
        personnel_fonction= _v(chirurgie, 'personnel_fonction')

        code           = _v(chirurgie, 'code')
        date_chir      = _v(chirurgie, 'date_chururgie')
        libelle        = _v(chirurgie, 'libelle_chururgie')
        frais          = _v(chirurgie, 'frais_chururgie', 0)
        statut_facture = _v(chirurgie, 'statut_facture')
        compte_rendu   = _v(chirurgie, 'compte_rendu_operatoire', '')

        try:
            frais_fmt = f"{float(frais):,.0f} GNF".replace(',', ' ')
        except Exception:
            frais_fmt = f"{frais} GNF"

        elements.append(Paragraph("PATIENT", section_style))
        info_pat = Table([
            [Paragraph("<b>Nom</b>", label_style), Paragraph(f"{patient_nom} {patient_prenom}", info_style),
             Paragraph("<b>Téléphone</b>", label_style), Paragraph(str(patient_telephone), info_style)],
            [Paragraph("<b>Adresse</b>", label_style), Paragraph(str(patient_adresse), info_style), "", ""],
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
        elements.append(Spacer(1, 0.5*cm))

        elements.append(Paragraph("DÉTAILS DE LA CHIRURGIE", section_style))
        info_chir = Table([
            [Paragraph("<b>Code</b>", label_style), Paragraph(str(code), info_style),
             Paragraph("<b>Date</b>", label_style), Paragraph(str(date_chir), info_style)],
            [Paragraph("<b>Libellé</b>", label_style), Paragraph(str(libelle), info_style),
             Paragraph("<b>Frais</b>", label_style), Paragraph(frais_fmt, info_style)],
            [Paragraph("<b>Chirurgien</b>", label_style),
             Paragraph(f"Dr. {personnel_nom} {personnel_prenom} — {personnel_fonction}", info_style),
             Paragraph("<b>Statut</b>", label_style), Paragraph(str(statut_facture), info_style)],
        ], colWidths=[3*cm, 5.5*cm, 3*cm, 5.5*cm])
        info_chir.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.98, 0.98, 0.99)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 1, colors.Color(0.88, 0.88, 0.90)),
        ]))
        elements.append(info_chir)
        elements.append(Spacer(1, 0.8*cm))

        elements.append(Paragraph("COMPTE RENDU OPÉRATOIRE", section_style))
        elements.append(Spacer(1, 0.3*cm))
        cr_text = str(compte_rendu).strip() if compte_rendu else "Aucun compte rendu disponible."
        cr_frame = Table([[Paragraph(cr_text, body_style)]], colWidths=[17.5*cm])
        cr_frame.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.98, 0.98, 0.98)),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.Color(0.85, 0.85, 0.85)),
            ('ROUNDEDCORNERS', [10, 10, 10, 10]),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(cr_frame)
        elements.append(Spacer(1, 1*cm))

        def ajouter_entete(canvas, doc):
            HistoriquePatientPDFService.dessiner_entete_et_fond(
                canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet
            )

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf

    @staticmethod
    def generer_pdf_chirurgie_avec_resultat(chirurgie, resultat, info_cabinet, chemin_pdf=None,
                                             fichier_bytes=None, type_fichier_res=None):
        """Génère un PDF combiné chirurgie + résultat médical (même structure que generer_pdf_examen_avec_resultat)."""
        import tempfile

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="chirurgie_resultat_")
            os.close(fd)

        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        bleu = colors.Color(0.15, 0.38, 0.93)

        titre_style = ParagraphStyle(
            'ChirResTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu
        )
        date_style = ParagraphStyle(
            'ChirResDate', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        section_style = ParagraphStyle(
            'ChirResSection', parent=styles['Heading2'],
            fontSize=13, spaceAfter=8, textColor=bleu, fontName='Helvetica-Bold'
        )
        info_style = ParagraphStyle(
            'ChirResInfo', parent=styles['Normal'],
            fontSize=10, spaceAfter=4, leading=12
        )
        label_style = ParagraphStyle(
            'ChirResLabel', parent=styles['Normal'],
            fontSize=9, textColor=colors.Color(0.42, 0.45, 0.50), spaceAfter=2
        )

        def _v(obj, key, default='N/A'):
            return HistoriquePatientPDFService._obtenir_valeur(obj, key, default)

        elements.append(Paragraph("RAPPORT DE CHIRURGIE AVEC RÉSULTAT", titre_style))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style))
        elements.append(Spacer(1, 0.5*cm))

        patient_nom       = _v(chirurgie, 'patient_nom')
        patient_prenom    = _v(chirurgie, 'patient_prenom')
        patient_telephone = _v(chirurgie, 'patient_telephone')
        patient_adresse   = _v(chirurgie, 'patient_adresse')
        personnel_nom     = _v(chirurgie, 'personnel_nom')
        personnel_prenom  = _v(chirurgie, 'personnel_prenom')
        personnel_fonction= _v(chirurgie, 'personnel_fonction')

        def _make_frame(titre_txt, rows, col_widths):
            inner = Table(rows, colWidths=col_widths)
            inner.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            frame = Table([[Paragraph(titre_txt, section_style)], [inner]], colWidths=[8.5*cm])
            frame.setStyle(TableStyle([
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
            return frame

        frame_patient = _make_frame("INFORMATIONS PATIENT", [
            [Paragraph("<b>Nom</b>", label_style),       Paragraph(str(patient_nom), info_style)],
            [Paragraph("<b>Prénom</b>", label_style),    Paragraph(str(patient_prenom), info_style)],
            [Paragraph("<b>Téléphone</b>", label_style), Paragraph(str(patient_telephone), info_style)],
            [Paragraph("<b>Adresse</b>", label_style),   Paragraph(str(patient_adresse), info_style)],
        ], [3*cm, 5.5*cm])

        frame_personnel = _make_frame("CHIRURGIEN", [
            [Paragraph("<b>Nom</b>", label_style),      Paragraph(str(personnel_nom), info_style)],
            [Paragraph("<b>Prénom</b>", label_style),   Paragraph(str(personnel_prenom), info_style)],
            [Paragraph("<b>Fonction</b>", label_style), Paragraph(str(personnel_fonction), info_style)],
            ["", ""],
        ], [3*cm, 5.5*cm])

        elements.append(Spacer(1, 0.3*cm))
        duo = Table([[frame_patient, "", frame_personnel]], colWidths=[8.5*cm, 0.5*cm, 8.5*cm])
        duo.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(duo)
        elements.append(Spacer(1, 0.8*cm))

        elements.append(Paragraph("DÉTAILS DE LA CHIRURGIE", section_style))
        elements.append(Spacer(1, 0.3*cm))

        code           = _v(chirurgie, 'code')
        date_chir      = _v(chirurgie, 'date_chururgie')
        libelle        = _v(chirurgie, 'libelle_chururgie')
        frais          = _v(chirurgie, 'frais_chururgie', 0)
        statut_facture = _v(chirurgie, 'statut_facture')

        try:
            frais_fmt = f"{float(frais):,.0f} GNF".replace(',', ' ')
        except Exception:
            frais_fmt = f"{frais} GNF"

        data_chir = [
            [Paragraph("<b>Code Chirurgie</b>", label_style), Paragraph(str(code), info_style),
             Paragraph("<b>Date</b>", label_style), Paragraph(str(date_chir), info_style)],
            [Paragraph("<b>Libellé</b>", label_style), Paragraph(str(libelle), info_style),
             Paragraph("<b>Frais</b>", label_style), Paragraph(frais_fmt, info_style)],
            [Paragraph("<b>Statut Facture</b>", label_style), Paragraph(str(statut_facture), info_style),
             "", ""],
        ]
        chir_table = Table(data_chir, colWidths=[4*cm, 5*cm, 3*cm, 5*cm])
        chir_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.98, 0.98, 0.99)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.Color(0.90, 0.91, 0.93)),
            ('ROUNDEDCORNERS', [10, 10, 10, 10]),
        ]))
        elements.append(chir_table)
        elements.append(Spacer(1, 0.8*cm))

        if resultat:
            id_res        = _v(resultat, 'id_resultat')
            date_upload   = _v(resultat, 'date_upload')
            type_fich     = _v(resultat, 'type_fichier')
            niveau        = _v(resultat, 'niveau_confidentialite')
            description   = _v(resultat, 'description')

            inner_res = Table([
                [Paragraph("<b>Référence</b>", label_style), Paragraph(str(id_res), info_style),
                 Paragraph("<b>Date</b>", label_style), Paragraph(str(date_upload), info_style)],
                [Paragraph("<b>Type de fichier</b>", label_style), Paragraph(str(type_fich), info_style),
                 Paragraph("<b>Confidentialité</b>", label_style), Paragraph(str(niveau), info_style)],
                [Paragraph("<b>Description</b>", label_style), Paragraph(str(description), info_style), "", ""],
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
            HistoriquePatientPDFService.dessiner_entete_et_fond(
                canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet
            )

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf

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
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        elements.append(Paragraph("ORDONNANCE MÉDICALE", titre_style))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Générée le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style))
        elements.append(Spacer(1, 0.5*cm))

        # Infos patient
        patient_nom    = _v(prescription_group, 'patient_prenom', '') + ' ' + _v(prescription_group, 'patient_nom', '')
        code_acte      = _v(prescription_group, 'code_acte', 'N/A')
        date_cons      = _v(prescription_group, 'date_consultation', 'N/A')

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

        # Tableau des produits
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
        prod_style = [
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
        ]
        prod_table.setStyle(TableStyle(prod_style))
        elements.append(prod_table)
        elements.append(Spacer(1, 1*cm))

        def ajouter_entete(canvas, doc):
            HistoriquePatientPDFService.dessiner_entete_et_fond(
                canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet
            )

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf

    @staticmethod
    def generer_pdf_prescription_avec_resultat(prescription_group, lignes, resultat, info_cabinet,
                                                chemin_pdf=None, fichier_bytes=None, type_fichier_res=None):
        """Génère un PDF ordonnance + résultat médical (même structure que examen/chirurgie avec résultat)."""
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
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

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

        # Tableau produits
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

        # Section résultat médical
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
            HistoriquePatientPDFService.dessiner_entete_et_fond(
                canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet
            )

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf

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
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default) if hasattr(obj, key) else default

        elements.append(Paragraph("BON DE COMMANDE LUNETTES", titre_style))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style))
        elements.append(Spacer(1, 0.5*cm))

        # Infos patient & commande côte à côte
        patient_nom  = f"{_v(commande, 'patient_prenom', '')} {_v(commande, 'patient_nom', '')}".strip()
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

        # Détails commande
        elements.append(Paragraph("DÉTAILS DE LA COMMANDE", section_style))
        elements.append(Spacer(1, 0.3*cm))

        numero_verre  = _v(commande, 'numero_verre', 'N/A')
        numero_cadre  = _v(commande, 'numero_cadre', 'N/A')
        prix          = _v(commande, 'prix', 0)
        statut        = _v(commande, 'statut', 'N/A')
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
            HistoriquePatientPDFService.dessiner_entete_et_fond(
                canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet
            )

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
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default) if hasattr(obj, key) else default

        elements.append(Paragraph("BON DE COMMANDE LUNETTES AVEC RÉSULTAT", titre_style))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style))
        elements.append(Spacer(1, 0.5*cm))

        # Infos patient & commande
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

        # Détails commande
        elements.append(Paragraph("DÉTAILS DE LA COMMANDE", section_style))
        elements.append(Spacer(1, 0.3*cm))

        numero_verre  = _v(commande, 'numero_verre', 'N/A')
        numero_cadre  = _v(commande, 'numero_cadre', 'N/A')
        prix          = _v(commande, 'prix', 0)
        statut        = _v(commande, 'statut', 'N/A')
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

        # Section résultat médical
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
            HistoriquePatientPDFService.dessiner_entete_et_fond(
                canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet
            )

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf

    @staticmethod
    def generer_pdf_consultations_multiples(consultations, info_cabinet, chemin_pdf=None):
        """
        Génère un PDF pour plusieurs consultations.
        
        Args:
            consultations: Liste de dictionnaires contenant les consultations
            info_cabinet: Informations du cabinet
            chemin_pdf: Chemin où sauvegarder le PDF (si None, crée un fichier temporaire)
        
        Returns:
            str: Chemin du fichier PDF généré
        """
        import tempfile
        
        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="consultations_")
            os.close(fd)
        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Titre
        titre_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1,
            textColor=colors.Color(0.15, 0.38, 0.93)  # Bleu
        )

        titre = Paragraph("RAPPORT DES CONSULTATIONS", titre_style)
        elements.append(titre)
        elements.append(Spacer(1, 0.5*cm))

        # Date de génération
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=2,
            textColor=colors.gray
        )
        date_texte = f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
        elements.append(Paragraph(date_texte, date_style))
        elements.append(Spacer(1, 0.3*cm))

        # Nombre de consultations
        stats_style = ParagraphStyle(
            'StatsStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.green
        )
        stats_texte = f"Nombre total de consultations : {len(consultations)}"
        elements.append(Paragraph(stats_texte, stats_style))
        elements.append(Spacer(1, 0.5*cm))

        if consultations:
            # En-têtes du tableau
            headers = ['Code', 'Date', 'Diagnostique', 'Frais', 'Statut']

            # Données du tableau
            data = [headers]

            for consultation in consultations:
                code = HistoriquePatientPDFService._obtenir_valeur(consultation, 'code', 'N/A')
                date_val = HistoriquePatientPDFService._obtenir_valeur(consultation, 'date_consultation')
                date_str = ''
                if date_val:
                    if isinstance(date_val, str):
                        date_str = date_val
                    elif hasattr(date_val, 'strftime'):
                        date_str = date_val.strftime('%d/%m/%Y')
                
                diagnostique = HistoriquePatientPDFService._obtenir_valeur(consultation, 'diagnostique', 'N/A')
                if len(diagnostique) > 30:
                    diagnostique = diagnostique[:30] + "..."
                
                frais = HistoriquePatientPDFService._obtenir_valeur(consultation, 'frais_consultation', 0)
                statut = HistoriquePatientPDFService._obtenir_valeur(consultation, 'statut_facture', 'N/A')
                
                row = [code, date_str, diagnostique, f"{frais} GNF", statut]
                data.append(row)

            # Création du tableau
            table = Table(data, colWidths=[3*cm, 3*cm, 5*cm, 3*cm, 3*cm])

            # Style du tableau
            table_style = TableStyle([
                # En-tête
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.15, 0.38, 0.93)),  # Bleu
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

                # Corps du tableau
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),

                # Bordures
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ])

            table.setStyle(table_style)
            elements.append(table)

        # Génération du PDF
        def ajouter_entete(canvas, doc):
            HistoriquePatientPDFService.dessiner_entete_et_fond(canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)

        return chemin_pdf

    @staticmethod
    def generer_pdf_acte(acte, type_acte, info_cabinet, chemin_pdf=None):
        """
        Génère un PDF pour un acte médical.
        
        Args:
            acte: Dictionnaire contenant les détails de l'acte
            type_acte: Type d'acte (examen, chirurgie, lunette, prescription)
            info_cabinet: Informations du cabinet
            chemin_pdf: Chemin où sauvegarder le PDF (si None, crée un fichier temporaire)
        
        Returns:
            str: Chemin du fichier PDF généré
        """
        import tempfile
        
        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix=f"{type_acte}_")
            os.close(fd)
        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Titre
        titre_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1,
            textColor=colors.Color(0.15, 0.38, 0.93)  # Bleu
        )

        titre = Paragraph(f"RAPPORT D'ACTE MÉDICAL - {type_acte.upper()}", titre_style)
        elements.append(titre)
        elements.append(Spacer(1, 0.5*cm))

        # Date de génération
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=2,
            textColor=colors.gray
        )
        date_texte = f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
        elements.append(Paragraph(date_texte, date_style))
        elements.append(Spacer(1, 0.5*cm))

        # Informations de l'acte dans des sections
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            leading=12
        )
        
        label_style = ParagraphStyle(
            'LabelStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.Color(0.42, 0.45, 0.50),
            spaceAfter=2
        )

        if acte:
            # Informations patient
            patient_nom = HistoriquePatientPDFService._obtenir_valeur(acte, 'patient_nom', 'N/A')
            patient_prenom = HistoriquePatientPDFService._obtenir_valeur(acte, 'patient_prenom', 'N/A')
            patient_telephone = HistoriquePatientPDFService._obtenir_valeur(acte, 'patient_telephone', 'N/A')
            patient_adresse = HistoriquePatientPDFService._obtenir_valeur(acte, 'patient_adresse', 'N/A')

            # Informations personnel
            personnel_nom = HistoriquePatientPDFService._obtenir_valeur(acte, 'personnel_nom', 'N/A')
            personnel_prenom = HistoriquePatientPDFService._obtenir_valeur(acte, 'personnel_prenom', 'N/A')
            personnel_fonction = HistoriquePatientPDFService._obtenir_valeur(acte, 'personnel_fonction', 'N/A')

            # Style pour les titres de section
            section_style = ParagraphStyle(
                'SectionStyle',
                parent=styles['Heading2'],
                fontSize=13,
                spaceAfter=8,
                textColor=colors.Color(0.15, 0.38, 0.93),
                fontName='Helvetica-Bold'
            )

            # === SECTION 1 : PATIENT ET PERSONNEL CÔTE À CÔTE ===
            elements.append(Spacer(1, 0.3*cm))
            
            # Créer deux frames séparés côte à côte
            # Frame Patient
            frame_patient = Table([
                [Paragraph("INFORMATIONS PATIENT", section_style)],
                [Table([
                    [Paragraph("<b>Nom</b>", label_style), Paragraph(str(patient_nom), info_style)],
                    [Paragraph("<b>Prénom</b>", label_style), Paragraph(str(patient_prenom), info_style)],
                    [Paragraph("<b>Téléphone</b>", label_style), Paragraph(str(patient_telephone), info_style)],
                    [Paragraph("<b>Adresse</b>", label_style), Paragraph(str(patient_adresse), info_style)]
                ], colWidths=[3*cm, 5.5*cm])]
            ], colWidths=[8.5*cm])
            
            frame_patient.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, 0), 0),
                ('RIGHTPADDING', (0, 0), (-1, 0), 0),
                ('TOPPADDING', (0, 0), (-1, 0), 0),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                # Bordure autour du contenu
                ('BOX', (0, 1), (0, 1), 1.5, colors.Color(0.85, 0.85, 0.85)),
                ('ROUNDEDCORNERS', [10, 10, 10, 10]),
                ('LEFTPADDING', (0, 1), (0, 1), 15),
                ('RIGHTPADDING', (0, 1), (0, 1), 15),
                ('TOPPADDING', (0, 1), (0, 1), 15),
                ('BOTTOMPADDING', (0, 1), (0, 1), 15),
            ]))
            
            # Frame Personnel
            frame_personnel = Table([
                [Paragraph("PERSONNEL SOIGNANT", section_style)],
                [Table([
                    [Paragraph("<b>Nom</b>", label_style), Paragraph(str(personnel_nom), info_style)],
                    [Paragraph("<b>Prénom</b>", label_style), Paragraph(str(personnel_prenom), info_style)],
                    [Paragraph("<b>Fonction</b>", label_style), Paragraph(str(personnel_fonction), info_style)],
                    ["", ""]  # Ligne vide pour alignement
                ], colWidths=[3*cm, 5.5*cm])]
            ], colWidths=[8.5*cm])
            
            frame_personnel.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, 0), 0),
                ('RIGHTPADDING', (0, 0), (-1, 0), 0),
                ('TOPPADDING', (0, 0), (-1, 0), 0),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                # Bordure autour du contenu
                ('BOX', (0, 1), (0, 1), 1.5, colors.Color(0.85, 0.85, 0.85)),
                ('ROUNDEDCORNERS', [10, 10, 10, 10]),
                ('LEFTPADDING', (0, 1), (0, 1), 15),
                ('RIGHTPADDING', (0, 1), (0, 1), 15),
                ('TOPPADDING', (0, 1), (0, 1), 15),
                ('BOTTOMPADDING', (0, 1), (0, 1), 15),
            ]))
            
            # Style pour les sous-tableaux internes des deux frames
            for frame in [frame_patient, frame_personnel]:
                inner_table = frame._cellvalues[1][0]
                if inner_table:
                    inner_table.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ]))
            
            # Mettre les deux frames côte à côte avec un espace de 0.5cm entre eux
            patient_personnel_table = Table([[frame_patient, "", frame_personnel]], colWidths=[8.5*cm, 0.5*cm, 8.5*cm])
            patient_personnel_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            
            elements.append(patient_personnel_table)
            elements.append(Spacer(1, 0.8*cm))

            # Informations communes de l'acte
            elements.append(Paragraph("INFORMATIONS GÉNÉRALES", section_style))
            elements.append(Spacer(1, 0.3*cm))
            
            code_acte = HistoriquePatientPDFService._obtenir_valeur(acte, 'code_acte', 'N/A')
            decision = HistoriquePatientPDFService._obtenir_valeur(acte, 'decision_medicale', 'N/A')
            choix = HistoriquePatientPDFService._obtenir_valeur(acte, 'choix_patient', 'N/A')
            statut = HistoriquePatientPDFService._obtenir_valeur(acte, 'statut_acte', 'N/A')

            # Section informations générales
            data_general = [
                [Paragraph("<b>Code Acte</b>", label_style), Paragraph(str(code_acte), info_style),
                 Paragraph("<b>Type</b>", label_style), Paragraph(type_acte.capitalize(), info_style)],
                [Paragraph("<b>Décision médicale</b>", label_style), Paragraph(str(decision), info_style),
                 Paragraph("<b>Choix patient</b>", label_style), Paragraph(str(choix), info_style)],
                [Paragraph("<b>Statut</b>", label_style), Paragraph(str(statut), info_style),
                 "", ""]
            ]
            
            general_table = Table(data_general, colWidths=[4*cm, 5*cm, 3*cm, 5*cm])
            general_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.98, 0.98, 0.99)),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BOX', (0, 0), (-1, -1), 1.5, colors.Color(0.90, 0.91, 0.93)),
                ('ROUNDEDCORNERS', [10, 10, 10, 10]),
            ]))
            
            elements.append(general_table)
            elements.append(Spacer(1, 0.6*cm))

            # Informations spécifiques selon le type
            elements.append(Paragraph("INFORMATIONS SPÉCIFIQUES", section_style))
            elements.append(Spacer(1, 0.3*cm))
            if type_acte == 'examen':
                libelle = HistoriquePatientPDFService._obtenir_valeur(acte, 'libelle_examen', 'N/A')
                frais = HistoriquePatientPDFService._obtenir_valeur(acte, 'frais_examen', 0)
                conclusion = HistoriquePatientPDFService._obtenir_valeur(acte, 'conclusion_medicale', 'N/A')
                
                data_specifique = [
                    [Paragraph("<b>Libellé</b>", label_style), Paragraph(str(libelle), info_style),
                     Paragraph("<b>Frais</b>", label_style), Paragraph(f"{frais} GNF", info_style)],
                    [Paragraph("<b>Conclusion</b>", label_style), Paragraph(str(conclusion), info_style),
                     "", ""]
                ]

            elif type_acte == 'chirurgie':
                libelle = HistoriquePatientPDFService._obtenir_valeur(acte, 'libelle_chururgie', 'N/A')
                frais = HistoriquePatientPDFService._obtenir_valeur(acte, 'frais_chururgie', 0)
                compte_rendu = HistoriquePatientPDFService._obtenir_valeur(acte, 'compte_rendu_operatoire', 'N/A')
                
                data_specifique = [
                    [Paragraph("<b>Libellé</b>", label_style), Paragraph(str(libelle), info_style),
                     Paragraph("<b>Frais</b>", label_style), Paragraph(f"{frais} GNF", info_style)],
                    [Paragraph("<b>Compte rendu</b>", label_style), Paragraph(str(compte_rendu), info_style),
                     "", ""]
                ]

            elif type_acte == 'lunette':
                type_verre = HistoriquePatientPDFService._obtenir_valeur(acte, 'type_verre', 'N/A')
                prix = HistoriquePatientPDFService._obtenir_valeur(acte, 'prix_total', 0)
                statut_commande = HistoriquePatientPDFService._obtenir_valeur(acte, 'statut_commande', 'N/A')
                
                data_specifique = [
                    [Paragraph("<b>Type de verre</b>", label_style), Paragraph(str(type_verre), info_style),
                     Paragraph("<b>Prix total</b>", label_style), Paragraph(f"{prix} GNF", info_style)],
                    [Paragraph("<b>Statut commande</b>", label_style), Paragraph(str(statut_commande), info_style),
                     "", ""]
                ]

            elif type_acte == 'prescription':
                produits = HistoriquePatientPDFService._obtenir_valeur(acte, 'produits', [])
                
                data_specifique = [
                    [Paragraph("<b>Nombre de produits</b>", label_style), Paragraph(str(len(produits)), info_style),
                     "", ""]
                ]
            else:
                data_specifique = []
            
            if data_specifique:
                specifique_table = Table(data_specifique, colWidths=[4*cm, 5*cm, 3*cm, 5*cm])
                specifique_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.98, 0.98, 0.99)),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('BOX', (0, 0), (-1, -1), 1.5, colors.Color(0.90, 0.91, 0.93)),
                    ('ROUNDEDCORNERS', [10, 10, 10, 10]),
                ]))
                
                elements.append(specifique_table)

        elements.append(Spacer(1, 1*cm))

        # Génération du PDF
        def ajouter_entete(canvas, doc):
            HistoriquePatientPDFService.dessiner_entete_et_fond(canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)

        return chemin_pdf

    @staticmethod
    def generer_pdf_consultations_par_date(consultations_details, info_cabinet, chemin_pdf=None):
        """
        Génère un PDF avec toutes les consultations groupées par date.
        Un tableau par date, avec total nombre et montant en bas de chaque groupe.

        Args:
            consultations_details: Liste de dicts (résultat de obtenir_consultation_complete)
            info_cabinet: Infos cabinet pour l'entête
            chemin_pdf: Chemin de sortie (None = fichier temporaire)

        Returns:
            str: Chemin du PDF généré
        """
        import tempfile
        from collections import defaultdict

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="rapport_consultations_")
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
            'RptCpdTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu
        )
        date_gen_style = ParagraphStyle(
            'RptCpdDateGen', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        date_section_style = ParagraphStyle(
            'RptCpdSection', parent=styles['Normal'],
            fontSize=11, fontName='Helvetica-Bold',
            textColor=bleu, spaceBefore=10, spaceAfter=4
        )
        cell_style = ParagraphStyle(
            'RptCpdCell', parent=styles['Normal'],
            fontSize=8, leading=10
        )
        header_cell_style = ParagraphStyle(
            'RptCpdHdr', parent=styles['Normal'],
            fontSize=9, textColor=colors.white, fontName='Helvetica-Bold'
        )
        total_label_style = ParagraphStyle(
            'RptCpdTotLbl', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold', textColor=bleu
        )
        total_val_style = ParagraphStyle(
            'RptCpdTotVal', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold', textColor=bleu, alignment=2
        )

        def _v(obj, key, default=''):
            return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

        def _get_date_key(d):
            if not d:
                return '9999-99-99'
            if hasattr(d, 'date'):
                return d.date().strftime('%Y-%m-%d')
            if hasattr(d, 'strftime'):
                return d.strftime('%Y-%m-%d')
            s = str(d)
            return s[:10] if len(s) >= 10 else s

        def _fmt_date_display(d):
            if not d:
                return 'Date inconnue'
            if hasattr(d, 'strftime'):
                return d.strftime('%d/%m/%Y')
            s = str(d)
            if len(s) >= 10 and s[4] == '-':
                return f"{s[8:10]}/{s[5:7]}/{s[:4]}"
            return s

        elements.append(Paragraph("RAPPORT DES CONSULTATIONS PAR DATE", titre_style))
        elements.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            date_gen_style
        ))
        elements.append(Spacer(1, 0.3*cm))

        if not consultations_details:
            elements.append(Paragraph("Aucune consultation à afficher.", styles['Normal']))
        else:
            groupes = defaultdict(list)
            for c in consultations_details:
                groupes[_get_date_key(_v(c, 'date_consultation'))].append(c)

            for date_key in sorted(groupes.keys()):
                groupe = groupes[date_key]
                date_label = _fmt_date_display(_v(groupe[0], 'date_consultation'))
                elements.append(Paragraph(f"Date : {date_label}", date_section_style))

                header_row = [
                    Paragraph("<b>Code</b>", header_cell_style),
                    Paragraph("<b>Patient</b>", header_cell_style),
                    Paragraph("<b>Diagnostic</b>", header_cell_style),
                    Paragraph("<b>Médecin</b>", header_cell_style),
                    Paragraph("<b>Frais (GNF)</b>", header_cell_style),
                    Paragraph("<b>Statut</b>", header_cell_style),
                ]
                data = [header_row]
                total_frais = 0.0

                for c in groupe:
                    code = str(_v(c, 'code', 'N/A'))
                    patient = f"{_v(c, 'patient_nom', '')} {_v(c, 'patient_prenom', '')}".strip() or 'N/A'
                    diagnostic = str(_v(c, 'diagnostique', '-'))
                    if len(diagnostic) > 35:
                        diagnostic = diagnostic[:35] + '…'
                    medecin = f"Dr. {_v(c, 'personnel_nom', '')} {_v(c, 'personnel_prenom', '')}".strip()
                    if medecin == 'Dr. ':
                        medecin = '-'
                    frais_val = _v(c, 'frais_consultation', 0)
                    try:
                        total_frais += float(frais_val or 0)
                        frais_fmt = f"{float(frais_val or 0):,.0f}".replace(',', ' ')
                    except Exception:
                        frais_fmt = '0'
                    statut = str(_v(c, 'statut_facture', '-'))

                    data.append([
                        Paragraph(code, cell_style),
                        Paragraph(patient, cell_style),
                        Paragraph(diagnostic, cell_style),
                        Paragraph(medecin, cell_style),
                        Paragraph(frais_fmt, cell_style),
                        Paragraph(statut, cell_style),
                    ])

                total_frais_fmt = f"{total_frais:,.0f}".replace(',', ' ') + " GNF"
                data.append([
                    Paragraph(f"Total : {len(groupe)} consultation(s)", total_label_style),
                    '', '', '',
                    Paragraph(total_frais_fmt, total_val_style),
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
                elements.append(Spacer(1, 0.5*cm))

        def ajouter_entete(c, doc):
            HistoriquePatientPDFService.dessiner_entete_et_fond(
                c, doc.pagesize[0], doc.pagesize[1], info_cabinet
            )

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf

    @staticmethod
    def generer_pdf_consultations_date_precise(consultations_details, date_cible, info_cabinet, chemin_pdf=None):
        """
        Génère un PDF pour les consultations d'une date précise.

        Args:
            consultations_details: Liste de dicts (résultat de obtenir_consultation_complete)
            date_cible: datetime.date, datetime.datetime ou str YYYY-MM-DD / DD/MM/YYYY
            info_cabinet: Infos cabinet pour l'entête
            chemin_pdf: Chemin de sortie (None = fichier temporaire)

        Returns:
            str: Chemin du PDF généré
        """
        import tempfile

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="rapport_date_")
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
            d = c.get('date_consultation') if isinstance(c, dict) else getattr(c, 'date_consultation', None)
            return _normalize_key(d)

        cible_key = _normalize_key(date_cible)
        filtrees = [c for c in (consultations_details or []) if _get_date_key(c) == cible_key]

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
            'RptDpTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu
        )
        date_gen_style = ParagraphStyle(
            'RptDpDateGen', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        cell_style = ParagraphStyle(
            'RptDpCell', parent=styles['Normal'],
            fontSize=8, leading=10
        )
        header_cell_style = ParagraphStyle(
            'RptDpHdr', parent=styles['Normal'],
            fontSize=9, textColor=colors.white, fontName='Helvetica-Bold'
        )
        total_label_style = ParagraphStyle(
            'RptDpTotLbl', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold', textColor=bleu
        )
        total_val_style = ParagraphStyle(
            'RptDpTotVal', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold', textColor=bleu, alignment=2
        )

        def _v(obj, key, default=''):
            return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

        elements.append(Paragraph(
            f"RAPPORT DES CONSULTATIONS DU {date_affichee}", titre_style
        ))
        elements.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            date_gen_style
        ))
        elements.append(Spacer(1, 0.4*cm))

        if not filtrees:
            elements.append(Paragraph(
                f"Aucune consultation trouvée pour le {date_affichee}.",
                styles['Normal']
            ))
        else:
            header_row = [
                Paragraph("<b>Code</b>", header_cell_style),
                Paragraph("<b>Patient</b>", header_cell_style),
                Paragraph("<b>Diagnostic</b>", header_cell_style),
                Paragraph("<b>Médecin</b>", header_cell_style),
                Paragraph("<b>Frais (GNF)</b>", header_cell_style),
                Paragraph("<b>Statut</b>", header_cell_style),
            ]
            data = [header_row]
            total_frais = 0.0

            for c in filtrees:
                code = str(_v(c, 'code', 'N/A'))
                patient = f"{_v(c, 'patient_nom', '')} {_v(c, 'patient_prenom', '')}".strip() or 'N/A'
                diagnostic = str(_v(c, 'diagnostique', '-'))
                if len(diagnostic) > 35:
                    diagnostic = diagnostic[:35] + '…'
                medecin = f"Dr. {_v(c, 'personnel_nom', '')} {_v(c, 'personnel_prenom', '')}".strip()
                if medecin == 'Dr. ':
                    medecin = '-'
                frais_val = _v(c, 'frais_consultation', 0)
                try:
                    total_frais += float(frais_val or 0)
                    frais_fmt = f"{float(frais_val or 0):,.0f}".replace(',', ' ')
                except Exception:
                    frais_fmt = '0'
                statut = str(_v(c, 'statut_facture', '-'))

                data.append([
                    Paragraph(code, cell_style),
                    Paragraph(patient, cell_style),
                    Paragraph(diagnostic, cell_style),
                    Paragraph(medecin, cell_style),
                    Paragraph(frais_fmt, cell_style),
                    Paragraph(statut, cell_style),
                ])

            total_frais_fmt = f"{total_frais:,.0f}".replace(',', ' ') + " GNF"
            data.append([
                Paragraph(f"Total : {len(filtrees)} consultation(s)", total_label_style),
                '', '', '',
                Paragraph(total_frais_fmt, total_val_style),
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
            HistoriquePatientPDFService.dessiner_entete_et_fond(
                c, doc.pagesize[0], doc.pagesize[1], info_cabinet
            )

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf

    @staticmethod
    def generer_pdf_examens_par_date(examens_details, info_cabinet, chemin_pdf=None):
        """
        Génère un PDF groupant tous les examens par date.
        Un tableau par date, avec total nombre + total GNF en bas de chaque groupe.

        Args:
            examens_details: Liste de dicts (résultat de obtenir_examen_complet)
            info_cabinet: Infos cabinet pour l'entête
            chemin_pdf: Chemin de sortie (None = fichier temporaire)

        Returns:
            str: Chemin du PDF généré
        """
        import tempfile
        from collections import defaultdict

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="rapport_examens_")
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
            d = c.get('date_examen') if isinstance(c, dict) else getattr(c, 'date_examen', None)
            return _normalize_key(d)

        def _key_to_display(k):
            if len(k) == 10 and k[4] == '-':
                return f"{k[8:10]}/{k[5:7]}/{k[:4]}"
            return k

        groupes = defaultdict(list)
        for c in (examens_details or []):
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
            'RptEpdTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu
        )
        date_gen_style = ParagraphStyle(
            'RptEpdDateGen', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        date_groupe_style = ParagraphStyle(
            'RptEpdDateGroupe', parent=styles['Normal'],
            fontSize=11, fontName='Helvetica-Bold', textColor=bleu, spaceAfter=4
        )
        cell_style = ParagraphStyle(
            'RptEpdCell', parent=styles['Normal'],
            fontSize=8, leading=10
        )
        header_cell_style = ParagraphStyle(
            'RptEpdHdr', parent=styles['Normal'],
            fontSize=9, textColor=colors.white, fontName='Helvetica-Bold'
        )
        total_label_style = ParagraphStyle(
            'RptEpdTotLbl', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold', textColor=bleu
        )
        total_val_style = ParagraphStyle(
            'RptEpdTotVal', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold', textColor=bleu, alignment=2
        )

        def _v(obj, key, default=''):
            return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

        elements.append(Paragraph("RAPPORT DES EXAMENS", titre_style))
        elements.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            date_gen_style
        ))
        elements.append(Spacer(1, 0.4*cm))

        if not dates_triees:
            elements.append(Paragraph("Aucun examen trouvé.", styles['Normal']))
        else:
            header_row = [
                Paragraph("<b>Code</b>", header_cell_style),
                Paragraph("<b>Patient</b>", header_cell_style),
                Paragraph("<b>Libellé examen</b>", header_cell_style),
                Paragraph("<b>Médecin</b>", header_cell_style),
                Paragraph("<b>Frais (GNF)</b>", header_cell_style),
                Paragraph("<b>Statut</b>", header_cell_style),
            ]
            col_widths = [2.2*cm, 3.5*cm, 3.8*cm, 3.2*cm, 2.6*cm, 2.7*cm]

            for i, date_key in enumerate(dates_triees):
                groupe = groupes[date_key]
                date_affichee = _key_to_display(date_key) if date_key else "Date inconnue"

                elements.append(Paragraph(f"Date : {date_affichee}", date_groupe_style))

                data = [header_row[:]]
                total_frais = 0.0

                for c in groupe:
                    code = str(_v(c, 'code', 'N/A'))
                    patient = f"{_v(c, 'patient_nom', '')} {_v(c, 'patient_prenom', '')}".strip() or 'N/A'
                    libelle = str(_v(c, 'libelle_examen', '-'))
                    if len(libelle) > 35:
                        libelle = libelle[:35] + '…'
                    medecin = f"Dr. {_v(c, 'personnel_nom', '')} {_v(c, 'personnel_prenom', '')}".strip()
                    if medecin == 'Dr. ':
                        medecin = '-'
                    frais_val = _v(c, 'frais_examen', 0)
                    try:
                        total_frais += float(frais_val or 0)
                        frais_fmt = f"{float(frais_val or 0):,.0f}".replace(',', ' ')
                    except Exception:
                        frais_fmt = '0'
                    statut = str(_v(c, 'statut_facture', '-'))

                    data.append([
                        Paragraph(code, cell_style),
                        Paragraph(patient, cell_style),
                        Paragraph(libelle, cell_style),
                        Paragraph(medecin, cell_style),
                        Paragraph(frais_fmt, cell_style),
                        Paragraph(statut, cell_style),
                    ])

                total_frais_fmt = f"{total_frais:,.0f}".replace(',', ' ') + " GNF"
                data.append([
                    Paragraph(f"Total : {len(groupe)} examen(s)", total_label_style),
                    '', '', '',
                    Paragraph(total_frais_fmt, total_val_style),
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
            HistoriquePatientPDFService.dessiner_entete_et_fond(
                c, doc.pagesize[0], doc.pagesize[1], info_cabinet
            )

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf

    @staticmethod
    def generer_pdf_examens_date_precise(examens_details, date_cible, info_cabinet, chemin_pdf=None):
        """
        Génère un PDF pour les examens d'une date précise.

        Args:
            examens_details: Liste de dicts (résultat de obtenir_examen_complet)
            date_cible: datetime.date, datetime.datetime ou str YYYY-MM-DD / DD/MM/YYYY
            info_cabinet: Infos cabinet pour l'entête
            chemin_pdf: Chemin de sortie (None = fichier temporaire)

        Returns:
            str: Chemin du PDF généré
        """
        import tempfile

        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="rapport_examens_date_")
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
            d = c.get('date_examen') if isinstance(c, dict) else getattr(c, 'date_examen', None)
            return _normalize_key(d)

        cible_key = _normalize_key(date_cible)
        filtrees = [c for c in (examens_details or []) if _get_date_key(c) == cible_key]

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
            'RptEdpTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=20, alignment=1, textColor=bleu
        )
        date_gen_style = ParagraphStyle(
            'RptEdpDateGen', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        cell_style = ParagraphStyle(
            'RptEdpCell', parent=styles['Normal'],
            fontSize=8, leading=10
        )
        header_cell_style = ParagraphStyle(
            'RptEdpHdr', parent=styles['Normal'],
            fontSize=9, textColor=colors.white, fontName='Helvetica-Bold'
        )
        total_label_style = ParagraphStyle(
            'RptEdpTotLbl', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold', textColor=bleu
        )
        total_val_style = ParagraphStyle(
            'RptEdpTotVal', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold', textColor=bleu, alignment=2
        )

        def _v(obj, key, default=''):
            return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

        elements.append(Paragraph(
            f"RAPPORT DES EXAMENS DU {date_affichee}", titre_style
        ))
        elements.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            date_gen_style
        ))
        elements.append(Spacer(1, 0.4*cm))

        if not filtrees:
            elements.append(Paragraph(
                f"Aucun examen trouvé pour le {date_affichee}.",
                styles['Normal']
            ))
        else:
            header_row = [
                Paragraph("<b>Code</b>", header_cell_style),
                Paragraph("<b>Patient</b>", header_cell_style),
                Paragraph("<b>Libellé examen</b>", header_cell_style),
                Paragraph("<b>Médecin</b>", header_cell_style),
                Paragraph("<b>Frais (GNF)</b>", header_cell_style),
                Paragraph("<b>Statut</b>", header_cell_style),
            ]
            data = [header_row]
            total_frais = 0.0

            for c in filtrees:
                code = str(_v(c, 'code', 'N/A'))
                patient = f"{_v(c, 'patient_nom', '')} {_v(c, 'patient_prenom', '')}".strip() or 'N/A'
                libelle = str(_v(c, 'libelle_examen', '-'))
                if len(libelle) > 35:
                    libelle = libelle[:35] + '…'
                medecin = f"Dr. {_v(c, 'personnel_nom', '')} {_v(c, 'personnel_prenom', '')}".strip()
                if medecin == 'Dr. ':
                    medecin = '-'
                frais_val = _v(c, 'frais_examen', 0)
                try:
                    total_frais += float(frais_val or 0)
                    frais_fmt = f"{float(frais_val or 0):,.0f}".replace(',', ' ')
                except Exception:
                    frais_fmt = '0'
                statut = str(_v(c, 'statut_facture', '-'))

                data.append([
                    Paragraph(code, cell_style),
                    Paragraph(patient, cell_style),
                    Paragraph(libelle, cell_style),
                    Paragraph(medecin, cell_style),
                    Paragraph(frais_fmt, cell_style),
                    Paragraph(statut, cell_style),
                ])

            total_frais_fmt = f"{total_frais:,.0f}".replace(',', ' ') + " GNF"
            data.append([
                Paragraph(f"Total : {len(filtrees)} examen(s)", total_label_style),
                '', '', '',
                Paragraph(total_frais_fmt, total_val_style),
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
            HistoriquePatientPDFService.dessiner_entete_et_fond(
                c, doc.pagesize[0], doc.pagesize[1], info_cabinet
            )

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf

    @staticmethod
    def generer_pdf_actes_multiples(actes, info_cabinet, chemin_pdf=None):
        """
        Génère un PDF pour plusieurs actes médicaux.
        
        Args:
            actes: Liste de dictionnaires contenant les actes
            info_cabinet: Informations du cabinet
            chemin_pdf: Chemin où sauvegarder le PDF (si None, crée un fichier temporaire)
        
        Returns:
            str: Chemin du fichier PDF généré
        """
        import tempfile
        
        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="actes_")
            os.close(fd)
        doc = SimpleDocTemplate(chemin_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Titre
        titre_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1,
            textColor=colors.Color(0.15, 0.38, 0.93)  # Bleu
        )

        titre = Paragraph("RAPPORT DES ACTES MÉDICAUX", titre_style)
        elements.append(titre)
        elements.append(Spacer(1, 0.5*cm))

        # Date de génération
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=2,
            textColor=colors.gray
        )
        date_texte = f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
        elements.append(Paragraph(date_texte, date_style))
        elements.append(Spacer(1, 0.3*cm))

        # Nombre d'actes
        stats_style = ParagraphStyle(
            'StatsStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.green
        )
        stats_texte = f"Nombre total d'actes : {len(actes)}"
        elements.append(Paragraph(stats_texte, stats_style))
        elements.append(Spacer(1, 0.5*cm))

        if actes:
            # En-têtes du tableau
            headers = ['Code', 'Type', 'Décision', 'Choix', 'Statut']

            # Données du tableau
            data = [headers]

            for acte in actes:
                code = HistoriquePatientPDFService._obtenir_valeur(acte, 'code_acte', 'N/A')
                type_acte = HistoriquePatientPDFService._obtenir_valeur(acte, 'type_acte', 'N/A')
                decision = HistoriquePatientPDFService._obtenir_valeur(acte, 'decision_medicale', 'N/A')
                if len(decision) > 25:
                    decision = decision[:25] + "..."
                
                choix = HistoriquePatientPDFService._obtenir_valeur(acte, 'choix_patient', 'N/A')
                statut = HistoriquePatientPDFService._obtenir_valeur(acte, 'statut_acte', 'N/A')
                
                row = [code, type_acte.capitalize(), decision, choix, statut]
                data.append(row)

            # Création du tableau
            table = Table(data, colWidths=[3*cm, 2.5*cm, 5*cm, 2.5*cm, 3*cm])

            # Style du tableau
            table_style = TableStyle([
                # En-tête
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.15, 0.38, 0.93)),  # Bleu
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

                # Corps du tableau
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),

                # Bordures
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ])

            table.setStyle(table_style)
            elements.append(table)

        # Génération du PDF
        def ajouter_entete(canvas, doc):
            HistoriquePatientPDFService.dessiner_entete_et_fond(canvas, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)

        return chemin_pdf


# ── Compat shim : expose les nouvelles classes modulaires via cet ancien chemin ──
try:
    from services.pdf_actes.consultation_pdf import ConsultationPDF
    from services.pdf_actes.examen_pdf import ExamenPDF
    from services.pdf_actes.chirurgie_pdf import ChirurgiePDF
    from services.pdf_actes.prescription_pdf import PrescriptionPDF
    from services.pdf_actes.lunette_pdf import LunettePDF
    from services.pdf_rapports.rapport_consultation import RapportConsultationPDF
    from services.pdf_rapports.rapport_examen import RapportExamenPDF
except ImportError:
    pass
