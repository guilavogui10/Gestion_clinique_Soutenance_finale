# 🔧 MIGRATION BASE DE DONNÉES - Vérification d'intégrité

## ❌ PROBLÈME IDENTIFIÉ

Les colonnes `empreinte_sha256` et `hmac_integrite` **n'existent pas** dans votre table `resultat_medical`.

**Colonnes actuelles** :
- id_resultat
- type_source
- code_acte_medical
- code_consultation
- type_fichier
- chemin_fichier
- description
- date_upload
- niveau_confidentialite

**Colonnes manquantes** :
- ❌ empreinte_sha256
- ❌ hmac_integrite

---

## ✅ SOLUTION : Exécuter la migration SQL

### Méthode 1 : Via MySQL Workbench (Recommandé)

1. **Ouvrez MySQL Workbench**
2. **Connectez-vous** à votre base de données
3. **Ouvrez le fichier** : `migrations/add_integrite_columns.sql`
4. **Exécutez le script** (cliquez sur l'éclair ⚡)
5. **Vérifiez** que les colonnes ont été ajoutées

### Méthode 2 : Via ligne de commande

```bash
# Se connecter à MySQL
mysql -u root -p

# Utiliser la base de données
USE clinique_db;

# Ajouter les colonnes
ALTER TABLE resultat_medical 
ADD COLUMN empreinte_sha256 VARCHAR(64) NULL 
COMMENT 'Empreinte SHA-256 du fichier pour vérification d''intégrité';

ALTER TABLE resultat_medical 
ADD COLUMN hmac_integrite VARCHAR(255) NULL 
COMMENT 'Signature HMAC Vault de l''empreinte pour authentification';

# Vérifier
DESCRIBE resultat_medical;
```

### Méthode 3 : Copier-coller dans votre outil SQL

```sql
USE clinique_db;

ALTER TABLE resultat_medical 
ADD COLUMN empreinte_sha256 VARCHAR(64) NULL 
COMMENT 'Empreinte SHA-256 du fichier pour vérification d''intégrité';

ALTER TABLE resultat_medical 
ADD COLUMN hmac_integrite VARCHAR(255) NULL 
COMMENT 'Signature HMAC Vault de l''empreinte pour authentification';
```

---

## 🔍 VÉRIFICATION

Après avoir exécuté la migration, vérifiez que les colonnes existent :

```sql
SELECT 
    COLUMN_NAME, 
    DATA_TYPE, 
    IS_NULLABLE,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'resultat_medical' 
  AND TABLE_SCHEMA = 'clinique_db'
ORDER BY ORDINAL_POSITION;
```

**Résultat attendu** : Vous devriez voir les colonnes :
- `empreinte_sha256` (VARCHAR(64), NULL)
- `hmac_integrite` (VARCHAR(255), NULL)

---

## 🧪 APRÈS LA MIGRATION

### 1. Redémarrez l'application
Fermez et relancez votre application Python.

### 2. Uploadez un nouveau fichier
1. Allez dans **Résultats Médicaux** → **Enregistrer**
2. Uploadez une image
3. Notez l'ID (ex: RES-00000001)

### 3. Vérifiez en base de données
```sql
SELECT 
    id_resultat, 
    type_fichier,
    empreinte_sha256,
    hmac_integrite
FROM resultat_medical 
ORDER BY date_upload DESC 
LIMIT 1;
```

**Résultat attendu** :
- `empreinte_sha256` : Une chaîne de 64 caractères (ex: `a3f5b2c8d9e1f0...`)
- `hmac_integrite` : Une chaîne base64 (ex: `vault:v1:abc123...`)

**Si NULL** : Vérifiez que Vault est démarré.

### 4. Testez la vérification d'intégrité
1. Modifiez le fichier dans MinIO (http://127.0.0.1:9001)
2. Essayez de le consulter dans l'application
3. **Vous devriez voir** : ⚠️ Le contenu du fichier a été modifié ou corrompu

---

## 📊 STRUCTURE FINALE DE LA TABLE

Après la migration, votre table `resultat_medical` aura :

```
resultat_medical
├── id_resultat (VARCHAR, PK)
├── type_source (VARCHAR)
├── code_acte_medical (VARCHAR, NULL)
├── code_consultation (VARCHAR, NULL)
├── type_fichier (VARCHAR)
├── chemin_fichier (VARCHAR)
├── description (TEXT, NULL)
├── date_upload (DATETIME)
├── niveau_confidentialite (VARCHAR)
├── empreinte_sha256 (VARCHAR(64), NULL)  ← NOUVEAU
└── hmac_integrite (VARCHAR(255), NULL)   ← NOUVEAU
```

---

## ⚠️ NOTES IMPORTANTES

### Fichiers existants
Les fichiers déjà uploadés auront `empreinte_sha256 = NULL` et `hmac_integrite = NULL`.
- Ils restent **accessibles** (rétrocompatibilité)
- Ils ne sont **pas protégés** par la vérification d'intégrité
- Pour les protéger : supprimez-les et re-uploadez-les

### Nouveaux fichiers
Tous les fichiers uploadés **après la migration** auront automatiquement :
- Une empreinte SHA-256
- Une signature HMAC Vault
- Protection contre les modifications

---

## 🐛 DÉPANNAGE

### Erreur : "Column 'empreinte_sha256' already exists"
**Cause** : La colonne existe déjà

**Solution** : Vérifiez avec `DESCRIBE resultat_medical;`

### Erreur : "Table 'resultat_medical' doesn't exist"
**Cause** : Mauvaise base de données

**Solution** : Vérifiez le nom de votre base de données et modifiez `USE clinique_db;`

### Erreur : "Access denied"
**Cause** : Pas les droits d'administration

**Solution** : Connectez-vous avec un compte admin MySQL

---

## ✅ CHECKLIST

- [ ] Script SQL exécuté sans erreur
- [ ] Colonnes `empreinte_sha256` et `hmac_integrite` visibles dans la table
- [ ] Application redémarrée
- [ ] Vault démarré
- [ ] MinIO démarré
- [ ] Nouveau fichier uploadé
- [ ] Empreinte et HMAC présents en BD pour le nouveau fichier
- [ ] Test de modification réussi (message d'erreur affiché)

---

**Exécutez la migration maintenant, puis testez !** 🚀
