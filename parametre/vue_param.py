import customtkinter as ctk
from tkinter import filedialog
from PIL import Image
from parametre.controleur_param import CabinetController

class VueParamatre(ctk.CTkFrame):
    def  __init__(self, master):
        super().__init__(master)
        self.pack(fill= "both", expand =True)

        self.controleur_param= CabinetController()
        self.path_photo= None

        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Enregistrement des parametres de l'application", font=("Arial", 20, "bold")).pack(pady=20)
            
                # Champs de saisie
        self.nom_entry = self.create_input_field("Nom")
        self.adresse_entry = self.create_input_field("Adresse")
        
            
        # Bouton et affichage de la photo
        ctk.CTkButton(self, text="Sélectionner une photo (optionnel)", command=self.select_photo).pack(pady=10)
        self.photo_label = ctk.CTkLabel(self, text="Aucune photo sélectionnée", fg_color="transparent")
        self.photo_label.pack(pady=5)
            
        # Bouton d'enregistrement
        ctk.CTkButton(self, text="Enregistrer", command=self.enregistrer).pack(pady=20)

    def create_input_field(self, label_text):
        frame = ctk.CTkFrame(self)
        frame.pack(pady=5)
        ctk.CTkLabel(frame, text=f"{label_text}:", width=120, anchor="w").pack(side="left", padx=5)
        entry = ctk.CTkEntry(frame, width=200)
        entry.pack(side="left")
        return entry
    
    def select_photo(self):
        file_path = filedialog.askopenfilename(
            title="Sélectionner une photo",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg")]
        )
        if file_path:
            self.photo_path = file_path
            try:
                img = Image.open(self.photo_path)
                img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                img_ctk = ctk.CTkImage(img, size=(150, 150))
                self.photo_label.configure(image=img_ctk, text="")
            except Exception as e:
                self.photo_label.configure(text=f"Erreur de chargement : {e}", image=None)
        else:
            self.photo_path = None
            self.photo_label.configure(text="Aucune photo sélectionnée", image=None)

    def enregistrer(self):
        nom = self.nom_entry.get()
        adresse = self.adresse_entry.get()
        
        # Vérification des champs requis
        if not all([nom, adresse]):
            print("Veuillez remplir tous les champs obligatoires.")
            return

        resultat = self.controleur_param.create_initial_info(nom,self.photo_path, adresse )
        
        if resultat["status"] == "success":
            print(resultat["message"])
            self.reset_form()
        else:
            print(resultat["message"])

    def reset_form(self):
        self.nom_entry.delete(0, "end")
        self.adresse_entry.delete(0, "end")
        self.photo_label.configure(image=None, text="Aucune photo sélectionnée")
        self.photo_path = None

    
if __name__ == "__main__":
    app = ctk.CTk()
    app.geometry("400x700")
    app.title("Test d'enregistrement de personnel")
    VueParamatre(app)
    app.mainloop()
