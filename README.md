# Planning des Postes — Guide de déploiement

## Déploiement sur Render.com (gratuit, 5 minutes)

### Étape 1 — Créer un compte GitHub
1. Va sur https://github.com et crée un compte gratuit
2. Clique sur "New repository"
3. Nomme-le `planning-postes`, coche "Public", clique "Create repository"

### Étape 2 — Uploader les fichiers
Dans ton nouveau repo GitHub, clique "uploading an existing file" et uploade ces 4 fichiers :
- `app.py`
- `requirements.txt`
- `Procfile`
- Le dossier `static/index.html` (crée d'abord le dossier static)

### Étape 3 — Déployer sur Render
1. Va sur https://render.com et crée un compte gratuit
2. Clique "New" → "Web Service"
3. Connecte ton repo GitHub `planning-postes`
4. Remplis :
   - **Name** : planning-postes
   - **Runtime** : Python 3
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `gunicorn app:app`
5. Clique "Create Web Service"
6. Attends 2-3 minutes → Render te donne une URL du type `https://planning-postes.onrender.com`

### C'est prêt !
Partage cette URL à ton équipe. Tout le monde peut l'utiliser depuis n'importe quel appareil.

## Utilisation
1. Onglet **Employés** : ajouter les employés et leurs postes maîtrisés
2. Onglet **Postes** : vérifier/modifier les postes et priorités
3. Cliquer **💾 Sauvegarder** pour garder la configuration
4. Onglet **Planning** : générer l'affectation automatique
5. Onglet **Export** : importer le fichier Excel, télécharger le résultat rempli
