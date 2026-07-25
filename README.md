# Yas Customer Care RAG Chatbot

A customer support chatbot for Yas Tanzania using RAG (Retrieval Augmented Generation) with FAISS + Google Gemini.

## Structure
```
yas-chatbot/
├── backend/          # Flask API (app.py)
│   ├── app.py
│   ├── requirements.txt
│   ├── index.faiss   # FAISS vector index
│   └── index.pkl     # metadata
├── frontend/         # React (Vite) UI
│   ├── package.json
│   └── src/
└── extract.ipynb     # (optional) notebook used to build the index
```

## 1. Start the Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The server will start on `http://localhost:5000`.

> **API Key**: it is set inside `app.py`. For production, use an environment variable instead:
> `export GOOGLE_API_KEY="your-key"`

### Endpoints
- `GET /health` → status check
- `POST /chat` → `{ "message": "..." }` returns `{ "answer": "...", "sources": [...] }`

## 2. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

For a custom backend URL:
```bash
VITE_API_URL=http://your-server:5000 npm run dev
```

## 3. Features
- 🎧 Customer-care emoji while the bot is replying
- 🎨 Official Yas colors (yellow + navy)
- 🖼️ Yas logo at the top
- 💬 Supports English and Swahili questions
- 🔗 Source URLs shown under answers

## 📸 Screenshot


## Notes
The vector index (`index.faiss` + `index.pkl`) was built with `sentence-transformers/all-MiniLM-L6-v2` (dim 384). The LLM used is `gemini-2.5-flash`.

## 👤 Author
 
**Yahaya Nasoro**
*Data Scientist | Data Analyst*
 
- 📧 [ramadhanyahya16@gmail.com](mailto:ramadhanyahya16@gmail.com)
- 🔗 [LinkedIn:Yahaya Nasoro](https://www.linkedin.com/in/yahaya-nasoro-039bb231a)
  
Designed and developed this project end-to-end — from building the FAISS retrieval pipeline and integrating Google Gemini, to designing the React frontend and deploying the full-stack customer support chatbot for Yas Tanzania.
---

## 📄 License & Disclaimer
This project was built independently for personal learning and portfolio purposes as part of applied research into building RAG-based chatbots. It is **not affiliated with, endorsed by, or officially associated with Yas Tanzania** — the Yas name and branding are used solely for educational/demonstration purposes.
 
Released under the MIT License — you are free to use, modify, and distribute it in accordance with the terms of that license.

