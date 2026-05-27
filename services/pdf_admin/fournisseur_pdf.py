from fpdf import FPDF
from datetime import datetime


class FournisseurPDFService:
    """
    Service PDF Fournisseur
    -----------------------
    - Ne dépend PAS directement de la base de données
    - Reçoit le contrôleur en paramètre
    - Récupère l'entête via controller.get_cabinet_info()
    - Génère un PDF structuré et réutilisable
    """

    @staticmethod
    def _draw_header(pdf: FPDF, controller, titre: str, font_name: str):
        entete = controller.get_cabinet_info()
        page_width = pdf.w
        marge_droite = 10
        marge_gauche = 10

        if entete.get("logo_url"):
            try:
                pdf.image(entete["logo_url"], x=marge_gauche, y=10, w=30)
            except Exception:
                pass

        pdf.set_font(font_name, "B", 15)
        nom = entete.get("nom_cabinet", "Cabinet Ophtalmologique")
        adresse = entete.get("adresse_cabinet", "")

        pdf.set_font(font_name, "", 15)
        nom_width = pdf.get_string_width(nom)
        pdf.set_font(font_name, "", 10)
        adresse_width = pdf.get_string_width(adresse)

        pdf.set_xy(page_width - marge_droite - nom_width, 10)
        pdf.set_font(font_name, "B", 15)
        pdf.cell(nom_width, 6, nom, ln=True)

        pdf.set_xy(page_width - marge_droite - adresse_width, 16)
        pdf.set_font(font_name, "", 10)
        pdf.cell(adresse_width, 6, adresse, ln=True)

        pdf.ln(10)
        pdf.set_font(font_name, "B", 14)
        pdf.cell(0, 10, titre, ln=True, align="C")

        pdf.set_font(font_name, "", 10)
        pdf.cell(
            0, 6,
            datetime.now().strftime("Édité le %d/%m/%Y à %H:%M"),
            ln=True, align="C"
        )
        pdf.ln(5)

    @staticmethod
    def generer_liste_pdf(controller, chemin_fichier, fournisseurs):
        if not chemin_fichier:
            return False, "Chemin PDF non spécifié."

        try:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=False)
            pdf.set_margins(10, 15, 10)
            font_dir = "../Fonts/"

            try:
                pdf.add_font('YuGothic', '', font_dir + 'YuGothM.ttc', uni=True)
                pdf.add_font('YuGothic', 'B', font_dir + 'YuGothB.ttc', uni=True)
                font_name = 'YuGothic'
            except Exception:
                font_name = 'Helvetica'

            pdf.add_page()
            FournisseurPDFService._draw_header(pdf, controller, "Liste Complète des Fournisseurs", font_name)

            col_widths = [10, 65, 50, 25, 40]
            headers = ["N°", "Email", "Nom", "Téléphone", "Adresse"]
            line_height = 6
            padding_y = 6

            def draw_table_header():
                pdf.set_font(font_name, "B", 10)
                pdf.set_fill_color(240, 240, 240)
                for i, h in enumerate(headers):
                    ln = 1 if i == len(headers) - 1 else 0
                    pdf.cell(col_widths[i], line_height + padding_y, h, 1, ln, "C", fill=True)

            draw_table_header()
            pdf.set_font(font_name, "", 10)

            for i, f in enumerate(fournisseurs, 1):
                row_data = [
                    str(i),
                    str(f.get("email_fournisseur", "")),
                    str(f.get("nom_entreprise", "")),
                    str(f.get("telephone", "")),
                    str(f.get("adresse", ""))
                ]

                max_lines = 1
                for idx, text in enumerate(row_data):
                    text_width = pdf.get_string_width(text)
                    available_width = col_widths[idx] - 4
                    if text_width > available_width:
                        lines_needed = int(text_width / available_width) + 1
                        max_lines = max(max_lines, lines_needed)

                row_height = (max_lines * line_height) + padding_y

                if pdf.get_y() + row_height > 275:
                    pdf.add_page()
                    draw_table_header()
                    pdf.set_font(font_name, "", 10)

                y_start = pdf.get_y()
                x_start = pdf.get_x()
                curr_x = x_start

                for idx, text in enumerate(row_data):
                    pdf.set_xy(curr_x, y_start + (padding_y / 2))
                    align = "C" if idx in [0, 3] else "L"
                    pdf.multi_cell(col_widths[idx], line_height, text, border=0, align=align)
                    pdf.rect(curr_x, y_start, col_widths[idx], row_height)
                    curr_x += col_widths[idx]

                pdf.set_xy(x_start, y_start + row_height)

            pdf.output(chemin_fichier)
            return True, "PDF généré avec succès."

        except Exception as e:
            return False, f"Erreur : {e}"
