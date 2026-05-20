"""
test_modifier_fichier_minio.py
-------------------------------
Script pour tester la vérification d'intégrité en modifiant un fichier dans MinIO.
"""

import os
import sys
from minio import Minio
from dotenv import load_dotenv

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Charger les variables d'environnement
load_dotenv()

def lister_fichiers():
    """Liste tous les fichiers résultats dans MinIO."""
    client = Minio(
        os.getenv("MINIO_ENDPOINT"),
        access_key=os.getenv("MINIO_ACCESS_KEY"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
        secure=False
    )
    
    bucket = os.getenv("MINIO_BUCKET")
    
    print("=" * 70)
    print("📁 FICHIERS RÉSULTATS DANS MINIO")
    print("=" * 70)
    
    objects = client.list_objects(bucket, prefix="resultats/", recursive=True)
    fichiers = []
    
    for i, obj in enumerate(objects, 1):
        print(f"{i}. {obj.object_name} ({obj.size} bytes)")
        fichiers.append(obj.object_name)
    
    return client, bucket, fichiers


def modifier_fichier(client, bucket, chemin_fichier):
    """Modifie un fichier dans MinIO pour tester l'intégrité."""
    print("\n" + "=" * 70)
    print(f"🔧 MODIFICATION DU FICHIER : {chemin_fichier}")
    print("=" * 70)
    
    temp_file = "temp_test_integrite.tmp"
    
    try:
        # 1. Télécharger le fichier
        print("\n1️⃣ Téléchargement du fichier...")
        client.fget_object(bucket, chemin_fichier, temp_file)
        print(f"   ✅ Fichier téléchargé : {temp_file}")
        
        # 2. Modifier le fichier (ajouter des bytes à la fin)
        print("\n2️⃣ Modification du fichier...")
        with open(temp_file, "ab") as f:
            f.write(b"\x00\x00\x00FICHIER_MODIFIE_POUR_TEST_INTEGRITE\x00\x00\x00")
        print("   ✅ Fichier modifié localement (ajout de bytes à la fin)")
        
        # 3. Re-uploader le fichier modifié
        print("\n3️⃣ Upload du fichier modifié dans MinIO...")
        client.fput_object(bucket, chemin_fichier, temp_file)
        print(f"   ✅ Fichier modifié uploadé : {chemin_fichier}")
        
        # 4. Nettoyer
        os.remove(temp_file)
        print("\n4️⃣ Nettoyage terminé")
        
        print("\n" + "=" * 70)
        print("✅ TEST PRÊT !")
        print("=" * 70)
        print("\n📋 INSTRUCTIONS :")
        print("1. Ouvrez l'application")
        print("2. Allez dans 'Résultats Médicaux'")
        print("3. Essayez d'ouvrir le résultat correspondant")
        print("4. Vous devriez voir : 'Le contenu du fichier a été modifié ou corrompu'")
        print("\n🎯 Si ce message apparaît, la vérification d'intégrité fonctionne !")
        
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)


def main():
    print("\n" + "🧪 TEST DE VÉRIFICATION D'INTÉGRITÉ MINIO ".center(70, "="))
    print()
    
    # Lister les fichiers
    client, bucket, fichiers = lister_fichiers()
    
    if not fichiers:
        print("\n❌ Aucun fichier trouvé dans MinIO.")
        print("   Créez d'abord un résultat médical dans l'application.")
        return
    
    # Demander quel fichier modifier
    print("\n" + "=" * 70)
    choix = input("\n📝 Entrez le numéro du fichier à modifier (ou 'q' pour quitter) : ").strip()
    
    if choix.lower() == 'q':
        print("Annulé.")
        return
    
    try:
        index = int(choix) - 1
        if 0 <= index < len(fichiers):
            modifier_fichier(client, bucket, fichiers[index])
        else:
            print("❌ Numéro invalide.")
    except ValueError:
        print("❌ Veuillez entrer un numéro valide.")


if __name__ == "__main__":
    main()
