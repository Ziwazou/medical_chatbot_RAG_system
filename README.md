# Medical Chatbot - RAG System 🏥

A modern, AI-powered medical information chatbot built with Flask and LangChain, using Retrieval-Augmented Generation (RAG) to provide accurate, evidence-based medical information.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.1.1-green.svg)
![LangChain](https://img.shields.io/badge/langchain-0.3+-orange.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Features

- 🤖 **AI-Powered Responses**: Uses Google Gemini for intelligent, context-aware answers
- 📚 **RAG System**: Retrieval-Augmented Generation with Pinecone vector database
- 🎨 **Modern UI**: Beautiful, responsive interface with dark mode support
- 💬 **Real-time Chat**: Smooth, interactive chat experience
- 🔒 **Safe & Reliable**: Evidence-based medical information with appropriate disclaimers
- 📱 **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- 🌙 **Theme Toggle**: Light and dark mode for comfortable viewing

## 🏗️ Architecture

```
medical_chatbot_RAG_system/
├── app.py                  # Flask application
├── chatbot_engine.py       # RAG system integration
├── templates/              # HTML templates
│   ├── index.html         # Main chat interface
│   ├── 404.html           # Error page
│   └── 500.html           # Error page
├── static/                # Static assets
│   ├── css/
│   │   └── style.css      # Modern styling
│   └── js/
│       └── main.js        # Chat functionality
├── data/                  # Medical documents (PDFs)
├── requirements.txt       # Python dependencies
└── env.example           # Environment variables template
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Pinecone account and API key
- Google AI (Gemini) API key
- HuggingFace API token

### Installation

1. **Clone the repository**
   ```bash
   cd medical_chatbot_RAG_system
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv medbot
   
   # On Windows
   medbot\Scripts\activate
   
   # On Mac/Linux
   source medbot/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Copy `env.example` to `.env` and fill in your API keys:
   ```bash
   cp env.example .env
   ```
   
   Then edit `.env` with your actual values:
   ```env
   GOOGLE_API_KEY=your_google_api_key
   HUGGING_FACE_KEY=your_huggingface_token
   PINECONE_API_KEY=your_pinecone_api_key
   FLASK_SECRET_KEY=your_secret_key
   ```

5. **Prepare your data**
   
   Place your medical PDF documents in the `data/` directory.

6. **Initialize the vector database**
   
   Run the data ingestion notebook or script:
   ```bash
   jupyter notebook research/trials.ipynb
   ```

7. **Run the application**
   ```bash
   python app.py
   ```

8. **Open your browser**
   
   Navigate to: `http://localhost:5000`

