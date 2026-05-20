"""
Script de test pour vérifier l'intégrité d'un résultat médical
"""
import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from controllers.controleur_resultat_medical import ResultatMedicalControleur

def tester_integrite(id_resultat):
    """Teste la vérification d'intégrité d'un résultat"""
    print(f"\n{'='*60}")
    print(f"TEST DE VÉRIFICATION D'INTÉGRITÉ")
    print(f"{'='*60}\n")
    
    ctrl = ResultatMedicalControleur()
    
    # 1. Récupérer le résultat
    print(f"1. Récupération du résultat {id_resultat}...")
    resultat = ctrl.obtenir_resultat(id_resultat)
    
    if not resultat:
        print(f"❌ Résultat {id_resultat} introuvable !")
        return
    
    print(f"✅ Résultat trouvé")
    print(f"   - Type fichier: {resultat.type_fichier}")
    print(f"   - Chemin MinIO: {resultat.chemin_fichier}")
    print(f"   - Empreinte SHA-256: {resultat.empreinte_sha256 or 'NON DÉFINIE'}")
    print(f"   - HMAC Vault: {resultat.hmac_integrite or 'NON DÉFINI'}")
    
    # 2. Vérifier l'intégrité
    print(f"\n2. Vérification de l'intégrité...")
    integrite_ok, message = ctrl.verifier_integrite_resultat(id_resultat)
    
    print(f"\n{'='*60}")
    print(f"RÉSULTAT DE LA VÉRIFICATION")
    print(f"{'='*60}")
    print(f"Statut: {'✅ INTÉGRITÉ OK' if integrite_ok else '❌ INTÉGRITÉ COMPROMISE'}")
    print(f"Message: {message}")
    print(f"{'='*60}\n")
    
    # 3. Diagnostic
    if not resultat.empreinte_sha256 or not resultat.hmac_integrite:
        print("⚠️  DIAGNOSTIC:")
        print("   Le fichier n'a pas d'empreinte SHA-256 ou de signature HMAC.")
        print("   Cela signifie qu'il a été uploadé AVANT l'implémentation de la vérification d'intégrité.")
        print("\n💡 SOLUTION:")
        print("   1. Supprimez ce résultat")
        print("   2. Re-uploadez le fichier")
        print("   3. Le nouveau fichier aura une empreinte et une signature")
        print("   4. Testez à nouveau la modification dans MinIO")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_integrite_resultat.py <ID_RESULTAT>")
        print("Exemple: python test_integrite_resultat.py RES-00000001")
        sys.exit(1)
    
    id_resultat = sys.argv[1]
    tester_integrite(id_resultat)
