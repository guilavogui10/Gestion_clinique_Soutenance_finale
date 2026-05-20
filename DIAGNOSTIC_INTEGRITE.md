# 🔍 DIAGNOSTIC - Pourquoi la vérification d'intégrité ne fonctionne pas

## ❓ PROBLÈME IDENTIFIÉ

Vous avez modifié une image dans MinIO mais l'application l'affiche quand même sans erreur.

## 🎯 CAUSES POSSIBLES

### Cause 1 : Fichier uploadé AVANT l'implémentation (99% probable)
Les fichiers uploadés **avant** l'implémentation de la vérification d'intégrité n'ont **PAS** d'empreinte SHA-256 ni de signature HMAC en base de données.

**Vérification** :
```sql
SELECT id_resultat, empreinte_sha256, hmac_integrite 
FROM resultat_medical 
WHERE id_resultat = 'RES-00000001';
```

**Si empreinte_sha256 ou hmac_integrite est NULL** → C'est la cause !

**Solution** :
1. Supprimez ce résultat dans l'application
2. Re-uploadez le même fichier
3. Le nouveau fichier aura une empreinte et une signature
4. Modifiez-le dans MinIO
5. Testez à nouveau → Vous devriez voir l'erreur

---

### Cause 2 : La méthode verifier_integrite_resultat retourne toujours True
Dans `service_metier/resultat_medical_service.py`, ligne ~246 :

```python
if not resultat.empreinte_sha256 or not resultat.hmac_integrite:
    return True, "Aucune signature d'intégrité n'est enregistrée pour ce fichier."
```

**Comportement actuel** : Si pas d'empreinte → Retourne `True` (OK)

**Pourquoi** : Pour la rétrocompatibilité avec les anciens fichiers

**Solution** : C'est normal ! Il faut juste re-uploader le fichier.

---

### Cause 3 : Vault n'est pas démarré
Si Vault n'est pas accessible, la vérification échoue silencieusement.

**Vérification** :
```bash
# Vérifier si Vault est démarré
vault status
```

**Solution** :
```bash
# Démarrer Vault
vault server -dev
```

---

### Cause 4 : MinIO n'est pas accessible
Si MinIO n'est pas accessible, le fichier ne peut pas être téléchargé pour vérification.

**Vérification** :
```bash
# Tester MinIO
curl http://127.0.0.1:9000/minio/health/live
```

**Solution** :
```bash
# Démarrer MinIO
minio server C:\minio\data --console-address ":9001"
```

---

## 🧪 PROCÉDURE DE TEST COMPLÈTE

### Étape 1 : Vérifier la base de données
```sql
-- Voir tous les résultats avec leur empreinte
SELECT 
    id_resultat, 
    type_fichier,
    CASE 
        WHEN empreinte_sha256 IS NULL THEN '❌ PAS D''EMPREINTE'
        ELSE '✅ EMPREINTE OK'
    END as statut_empreinte,
    CASE 
        WHEN hmac_integrite IS NULL THEN '❌ PAS DE HMAC'
        ELSE '✅ HMAC OK'
    END as statut_hmac,
    date_upload
FROM resultat_medical
ORDER BY date_upload DESC;
```

### Étape 2 : Identifier les fichiers à re-uploader
Tous les fichiers avec `empreinte_sha256 = NULL` doivent être re-uploadés.

### Étape 3 : Re-uploader un fichier de test
1. Ouvrez l'application
2. Allez dans **Résultats Médicaux** → **Enregistrer**
3. Uploadez une **nouvelle** image
4. Notez l'ID du résultat (ex: RES-00000005)

### Étape 4 : Vérifier que le nouveau fichier a une empreinte
```sql
SELECT id_resultat, empreinte_sha256, hmac_integrite 
FROM resultat_medical 
WHERE id_resultat = 'RES-00000005';
```

**Résultat attendu** :
- `empreinte_sha256` : Une longue chaîne hexadécimale (64 caractères)
- `hmac_integrite` : Une chaîne base64

### Étape 5 : Modifier le fichier dans MinIO
1. Ouvrez MinIO Console : http://127.0.0.1:9001
2. Login : minioadmin / minioadmin
3. Naviguez vers le fichier : `clinique-data/resultats/images/RES-00000005_image_...`
4. Téléchargez le fichier
5. Modifiez-le avec Paint (changez la couleur de fond)
6. Supprimez l'ancien fichier dans MinIO
7. Uploadez le fichier modifié avec **exactement le même nom**

### Étape 6 : Tester dans l'application
1. Retournez dans l'application
2. Allez dans **Résultats Médicaux** → **Consultations/Examens/Chirurgies**
3. Cliquez sur **Voir** pour le résultat RES-00000005

**Résultat attendu** :
```
⚠️ Le contenu du fichier a été modifié ou corrompu.
```

---

## 📊 TABLEAU DE DIAGNOSTIC

| Symptôme | Cause probable | Solution |
|----------|----------------|----------|
| Fichier modifié s'affiche normalement | Pas d'empreinte en BD | Re-uploader le fichier |
| Message "Aucune signature d'intégrité" | Fichier ancien | Re-uploader le fichier |
| Erreur "Vault indisponible" | Vault arrêté | Démarrer Vault |
| Erreur "Impossible de relire le fichier" | MinIO arrêté | Démarrer MinIO |
| Empreinte NULL en BD | Fichier uploadé avant implémentation | Re-uploader le fichier |

---

## ✅ CHECKLIST DE VÉRIFICATION

Avant de tester, vérifiez :

- [ ] Vault est démarré (`vault status`)
- [ ] MinIO est démarré (http://127.0.0.1:9001 accessible)
- [ ] Le fichier testé a une empreinte SHA-256 en BD
- [ ] Le fichier testé a une signature HMAC en BD
- [ ] Le fichier a été uploadé APRÈS l'implémentation de la vérification
- [ ] Le fichier a bien été modifié dans MinIO (pas juste renommé)

---

## 🎯 SOLUTION RAPIDE

**Si vous voulez tester MAINTENANT** :

1. **Uploadez un NOUVEAU fichier** dans l'application
2. **Vérifiez en BD** qu'il a une empreinte et un HMAC
3. **Modifiez-le dans MinIO**
4. **Testez dans l'application** → Vous devriez voir l'erreur

**NE TESTEZ PAS avec un ancien fichier** uploadé avant l'implémentation !

---

## 💡 POURQUOI LES ANCIENS FICHIERS NE SONT PAS PROTÉGÉS ?

C'est un choix de conception pour la **rétrocompatibilité** :

```python
if not resultat.empreinte_sha256 or not resultat.hmac_integrite:
    return True, "Aucune signature d'intégrité n'est enregistrée pour ce fichier."
```

**Avantages** :
- Les anciens fichiers restent accessibles
- Pas besoin de re-uploader tous les fichiers existants
- Migration progressive

**Inconvénient** :
- Les anciens fichiers ne sont pas protégés

**Alternative** (si vous voulez bloquer les anciens fichiers) :
```python
if not resultat.empreinte_sha256 or not resultat.hmac_integrite:
    return False, "Ce fichier n'a pas de signature d'intégrité. Veuillez le re-uploader."
```

---

## 📝 RÉSUMÉ

**Votre problème** : Vous testez avec un fichier uploadé AVANT l'implémentation

**Solution** : Uploadez un NOUVEAU fichier et testez avec celui-ci

**Vérification** : Le nouveau fichier doit avoir `empreinte_sha256` et `hmac_integrite` en BD

**Test** : Modifiez le nouveau fichier dans MinIO → Vous verrez l'erreur
