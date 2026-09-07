# Medical Chatbot (Système RAG)

Application web de questions-réponses médicales développée avec Flask et LangChain, exploitant la génération augmentée par récupération (RAG) sur des documents médicaux de référence indexés dans Pinecone.

## Présentation

L'application traite des documents médicaux, stocke leurs plongements vectoriels (embeddings) dans un index Pinecone et génère des réponses fiables et contextualisées à l'aide d'un agent conversationnel basé sur Google Gemini.

Composants clés :
- Recherche vectorielle : Pinecone avec Sentence Transformers (`sentence-transformers/all-MiniLM-L6-v2`)
- Modèle de langage : Google Gemini via LangChain
- Interface web : Application Flask avec interface interactive en temps réel

## Installation et configuration

### Prérequis

- Python 3.9+
- Un compte et une clé API Pinecone
- Une clé API Google Gemini
- Un token API Hugging Face

### 1. Variables d'environnement

Créez un fichier `.env` à la racine du projet :

```env
GOOGLE_API_KEY=votre_cle_google_api
HUGGING_FACE_KEY=votre_cle_huggingface
PINECONE_API_KEY=votre_cle_pinecone
PINECONE_INDEX_NAME=medical-chatbot
FLASK_SECRET_KEY=votre_secret_flask
PORT=5000
FLASK_DEBUG=False
```

### 2. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 3. Lancement de l'application

Démarrez le serveur Flask :

```bash
python app.py
```

L'application est accessible à l'adresse `http://localhost:5000`.

