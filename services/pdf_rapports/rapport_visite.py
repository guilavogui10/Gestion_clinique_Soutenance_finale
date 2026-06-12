from services.pdf_actes._base import (
    dessiner_entete_et_fond, obtenir_valeur,
    A4, cm, colors, SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, PageBreak, getSampleStyleSheet, ParagraphStyle,
    datetime, os
)


class RapportVisitePDF:

    @staticmethod
    def generer_fiche_visite(code_visite, patient_name, visite,
                              details, info_cabinet, chemin_pdf=None):
        """
        Génère une fiche détaillée d'une visite.
        Structure identique à RapportConsultationPDF.
        Retourne le chemin du PDF généré.
        """
        import tempfile
        if chemin_pdf is None:
            fd, chemin_pdf = tempfile.mkstemp(suffix=".pdf", prefix="fiche_visite_")
            os.close(fd)

        doc = SimpleDocTemplate(
            chemin_pdf, pagesize=A4,
            leftMargin=1.5*cm, rightMargin=1.5*cm,
            topMargin=3*cm, bottomMargin=1.5*cm
        )
        styles = getSampleStyleSheet()
        elements = []

        bleu      = colors.Color(0.15, 0.38, 0.93)
        bleu_fond = colors.Color(0.92, 0.95, 1.0)
        gris_bord = colors.Color(0.90, 0.91, 0.93)
        gris_fond = colors.Color(0.98, 0.98, 0.99)

        titre_style = ParagraphStyle(
            'RptVTitle', parent=styles['Heading1'],
            fontSize=16, spaceAfter=4, alignment=1, textColor=bleu
        )
        date_gen_style = ParagraphStyle(
            'RptVDateGen', parent=styles['Normal'],
            fontSize=10, alignment=2, textColor=colors.gray
        )
        section_style = ParagraphStyle(
            'RptVSection', parent=styles['Normal'],
            fontSize=11, fontName='Helvetica-Bold',
            textColor=bleu, spaceBefore=10, spaceAfter=4
        )
        label_style = ParagraphStyle(
            'RptVLabel', parent=styles['Normal'],
            fontSize=9, textColor=colors.Color(0.42, 0.45, 0.50),
            fontName='Helvetica-Bold'
        )
        val_style = ParagraphStyle(
            'RptVVal', parent=styles['Normal'],
            fontSize=9
        )
        header_cell_style = ParagraphStyle(
            'RptVHdr', parent=styles['Normal'],
            fontSize=9, textColor=colors.white, fontName='Helvetica-Bold'
        )
        cell_style = ParagraphStyle(
            'RptVCell', parent=styles['Normal'],
            fontSize=8, leading=10
        )
        acte_titre_style = ParagraphStyle(
            'RptVActeTitre', parent=styles['Normal'],
            fontSize=10, fontName='Helvetica-Bold', textColor=bleu,
            spaceBefore=6, spaceAfter=3
        )
        acte_item_style = ParagraphStyle(
            'RptVActeItem', parent=styles['Normal'],
            fontSize=9, leftIndent=12, spaceAfter=2
        )

        def _vget(attr, default="—"):
            if visite is None:
                return default
            getter = getattr(visite, f'get_{attr}', None)
            if getter:
                try:
                    v = getter()
                    if v is None:
                        return default
                    if attr == 'date_visite' and hasattr(v, 'strftime'):
                        return v.strftime('%d/%m/%Y %H:%M')
                    return str(v)
                except Exception:
                    return default
            return str(getattr(visite, attr, default) or default)

        def _bloc_infos(rows_data):
            """Tableau 2 colonnes label / valeur dans un cadre."""
            tbl_data = [
                [Paragraph(lbl, label_style), Paragraph(str(val) or "—", val_style)]
                for lbl, val in rows_data
            ]
            t = Table(tbl_data, colWidths=[4*cm, 13.5*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND',    (0, 0), (-1, -1), gris_fond),
                ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING',   (0, 0), (-1, -1), 10),
                ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
                ('TOPPADDING',    (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LINEBELOW',     (0, 0), (-1, -2),  0.4, gris_bord),
                ('BOX',           (0, 0), (-1, -1),  1.2, gris_bord),
            ]))
            return t

        # ── Titre + date ──────────────────────────────────────────────
        elements.append(Paragraph(f"FICHE DE VISITE — {code_visite}", titre_style))
        elements.append(Paragraph(
            f"Générée le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            date_gen_style
        ))
        elements.append(Spacer(1, 0.4*cm))

        # ── Section patient ───────────────────────────────────────────
        tel = getattr(visite, 'tel_patient', '—') if visite else '—'
        code_pat = _vget('code_patient')

        elements.append(Paragraph("INFORMATIONS PATIENT", section_style))
        elements.append(_bloc_infos([
            ("Nom complet",   patient_name or "—"),
            ("Téléphone",     str(tel) or "—"),
            ("Code patient",  code_pat),
        ]))

        # ── Section visite ────────────────────────────────────────────
        elements.append(Paragraph("INFORMATIONS DE LA VISITE", section_style))
        elements.append(_bloc_infos([
            ("Type de visite", _vget('type_visite')),
            ("Urgence",        _vget('urgent')),
            ("Statut",         _vget('statut_patient')),
            ("Date de visite", _vget('date_visite')),
        ]))

        # ── Actes médicaux ────────────────────────────────────────────
        elements.append(Paragraph("ACTES MÉDICAUX", section_style))

        actes_config = [
            ("Consultation",  "consultations",
             [("Diagnostic",  "diagnostique"),
              ("Résultat",    "resultat_consultation")]),
            ("Examens",       "examens",
             [("Examen",      "libelle_examen"),
              ("Conclusion",  "conclusion_medicale")]),
            ("Prescriptions", "prescriptions",
             [("Produit",     "designation"),
              ("Quantité",    "quantite_prescript"),
              ("Prix",        "prix_applique")]),
            ("Chirurgies",    "chirurgies",
             [("Acte",        "libelle_chururgie"),
              ("Date",        "date_chururgie")]),
            ("Optique",       "lunettes",
             [("Cadre",       "numero_cadre"),
              ("Verre",       "numero_verre")]),
        ]

        has_actes = False
        for section_titre, key, champs in actes_config:
            items = (details or {}).get(key, [])
            if not items:
                continue
            has_actes = True
            elements.append(Paragraph(section_titre.upper(), acte_titre_style))

            acte_rows = []
            for item in items:
                parts = []
                for label, col in champs:
                    val = item.get(col, "") if isinstance(item, dict) else getattr(item, col, "")
                    if val:
                        parts.append(f"{label} : {val}")
                if parts:
                    acte_rows.append([
                        Paragraph("•  " + "   |   ".join(parts), acte_item_style),
                    ])

            if acte_rows:
                acte_tbl = Table(acte_rows, colWidths=[17.5*cm])
                nb_r = len(acte_rows)
                acte_tbl.setStyle(TableStyle([
                    ('BACKGROUND',    (0, 0), (-1, -1), gris_fond),
                    ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING',   (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
                    ('TOPPADDING',    (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LINEBELOW',     (0, 0), (-1, -2),  0.3, gris_bord),
                    ('BOX',           (0, 0), (-1, -1),  1,   gris_bord),
                    ('LINEBELOW',     (0, 0), (-1, 0),   1.5, bleu),
                ]))
                elements.append(acte_tbl)

        if not has_actes:
            elements.append(Paragraph(
                "Aucun acte médical enregistré pour cette visite.",
                ParagraphStyle('RptVAucun', parent=styles['Normal'],
                               textColor=colors.gray, alignment=1)
            ))

        elements.append(Spacer(1, 1*cm))

        def ajouter_entete(c, doc):
            dessiner_entete_et_fond(c, doc.pagesize[0], doc.pagesize[1], info_cabinet)

        doc.build(elements, onFirstPage=ajouter_entete, onLaterPages=ajouter_entete)
        return chemin_pdf
