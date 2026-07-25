"""
Yas Customer Support RAG Chatbot — Flask backend.

Loads a pre-built FAISS index (HuggingFace all-MiniLM-L6-v2 embeddings)
and answers questions with Google Gemini via LangChain.

Run:
    pip install -r requirements.txt
    python app.py
"""

import os
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

load_dotenv()  # inasoma backend/.env wakati wa maendeleo local


# ─── Config ────────────────────────────────────────────────────────────────────
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY environment variable is not set. "
        "Create a .env file locally (see .env.example) or set it in your "
        "hosting provider's dashboard before starting the app."
    )
FAISS_DIR = os.environ.get("FAISS_DIR", "./faiss_index")


# ─── Load Vector Store & LLM ───────────────────────────────────────────────────
print("🔄 Loading embeddings model...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

print("🔄 Loading FAISS index...")
db = FAISS.load_local(FAISS_DIR, embeddings, allow_dangerous_deserialization=True)

print("🔄 Initializing Gemini...")
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.01,
    google_api_key=GOOGLE_API_KEY,
)


# ─── Domain Filter Constants ───────────────────────────────────────────────────
NO_ANSWER_MESSAGE = (
    "We could not locate the requested information in our available resources.\n\n"
    "For additional support, please 🙏 contact the YAS Customer Care team below.\n\n"
    "📞 YAS Customers: Dial 100 directly from your YAS line.\n"
    "☎️ Customer Care: Dial 101 or +255 711 100 101.\n"
    "💬 WhatsApp Support: +255 714 100 100.\n"
    "🌍 International Roaming Support: +255 714 100 100."
)

REFUSAL_MESSAGE = (
    "Sorry, I can only answer questions about YAS Tanzania — 🙏 "
    "bundles, airtime, SIM cards, roaming, fiber, offers, and customer support."
)

YAS_KEYWORDS = [
    "yas", "myyas", "mixx by yas", "yas tanzania", "simcard", "sim card",
    "bundle", "data bundle", "airtime", "recharge", "topup", "top up",
    "minutes", "sms", "call", "network", "coverage", "plan", "package",
    "offer", "subscription", "internet bundle", "internet package",
    "4g", "5g", "roaming", "balance", "prepaid", "postpaid",
    "billing", "invoice", "activation", "deactivation",
    "esim", "ussd", "fiber", "wakishua",
]
YAS_BRAND_WORDS = ["yas", "myyas", "mixx by yas", "yas tanzania"]
YAS_ACTION_WORDS = [
    "buy", "subscribe", "activate", "deactivate", "check", "dial", "pay",
    "recharge", "top up", "use", "get", "how much", "price", "cost",
    "validity", "contact",
]
YAS_COMPANY_WORDS = [
    "your ceo", "yas ceo", "ceo of yas", "about yas",
    "yas company", "yas support", "yas customer care",
]


def is_yas_related(question: str) -> bool:
    q = question.lower().strip()
    if any(kw in q for kw in YAS_BRAND_WORDS):
        return True
    if any(kw in q for kw in YAS_COMPANY_WORDS):
        return True
    return any(kw in q for kw in YAS_KEYWORDS) and any(
        kw in q for kw in YAS_ACTION_WORDS
    )


# ─── Website Fallback Scraper ──────────────────────────────────────────────────
def get_relevant_pages(question: str) -> list:
    q = question.lower()
    selected = {"https://www.yas.co.tz/"}
    rules = {
        ("bundle", "data bundle", "internet", "gb", "mb"): [
            "https://www.yas.co.tz/consumer/mobile-plans/internet/",
            "https://www.yas.co.tz/consumer/mobile-plans/mix/",
            "https://www.yas.co.tz/consumer/mobile-plans/best-deals/",
        ],
        ("voice", "sms", "call", "minutes", "airtime"): [
            "https://www.yas.co.tz/consumer/mobile-plans/voice-sms/",
        ],
        ("international", "roaming"): [
            "https://www.yas.co.tz/consumer/mobile-plans/international/",
            "https://www.yas.co.tz/consumer/mobile-plans/roaming/",
        ],
        ("fiber", "home", "broadband", "wifi"): [
            "https://www.yas.co.tz/fiber-home/",
        ],
        ("business", "sme", "corporate", "enterprise"): [
            "https://www.yas.co.tz/business/",
        ],
        ("about yas", "yas ceo", "ceo of yas", "yas company"): [
            "https://www.yas.co.tz/about/",
            "https://www.yas.co.tz/about-yas-faqs/",
        ],
        ("yas support", "contact yas", "assistance"): [
            "https://www.yas.co.tz/assistance",
            "https://www.yas.co.tz/consumer-faqs",
        ],
        ("device", "phone", "smartphone"): ["https://www.yas.co.tz/devices/"],
        ("store", "location", "shop", "branch"): [
            "https://www.yas.co.tz/store-locator/",
        ],
        ("mixx", "lifestyle"): ["https://www.yas.co.tz/mixx-by-yas/"],
        ("wakishua", "offer", "deal", "promotion"): [
            "https://www.yas.co.tz/consumer/mobile-plans/wakishua/",
        ],
    }
    for keywords, pages in rules.items():
        if any(kw in q for kw in keywords):
            selected.update(pages)
    return list(selected)


def search_yas_website(question: str) -> str:
    pages = get_relevant_pages(question)
    all_text = ""
    headers = {"User-Agent": "Mozilla/5.0"}
    for url in pages:
        try:
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer"]):
                    tag.decompose()
                text = soup.get_text(separator=" ", strip=True)
                all_text += f"\n\n[Source: {url}]\n{text[:2000]}"
        except Exception:
            continue
    return all_text.strip()


# ─── Prompts & Chains ──────────────────────────────────────────────────────────
RAG_PROMPT = PromptTemplate.from_template("""
You are Yas Tanzania Customer Care AI.

Rules:
- Answer ONLY using the provided context.
- Answer ONLY the user's question.
- Keep answers short and clear.
- Never repeat information.
- Do not mention services the user did not ask about.
- Use bullet points only if necessary.
- If there are USSD codes or phone numbers, show them clearly.
- If the answer is not found, reply exactly:
NOT_IN_DOCUMENT.

Context:
{context}

Chat History:
{chat_history}

Question:
{question}

Answer:
""")

WEBSITE_PROMPT = PromptTemplate.from_template("""
You are Yas Tanzania Customer Care AI.

Rules:
- Answer ONLY using the website content below.
- Keep answers short and clear.
- Never guess.
- If the answer is not found, reply exactly:
NOT_ON_WEBSITE

Website Content:
{website_content}

Chat History:
{chat_history}

Question:
{question}

Answer:
""")

retriever = db.as_retriever(search_kwargs={"k": 4})


def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)


rag_chain = (
    {
        "context": RunnableLambda(
            lambda x: format_docs(retriever.invoke(x["question"]))
        ),
        "question": RunnableLambda(lambda x: x["question"]),
        "chat_history": RunnableLambda(lambda x: x.get("chat_history", "")),
    }
    | RAG_PROMPT
    | llm
    | StrOutputParser()
)

website_chain = WEBSITE_PROMPT | llm | StrOutputParser()


def ask(question: str, chat_history=None, similarity_threshold: float = 1.2):
    chat_history = chat_history or []

    if not is_yas_related(question):
        return {"answer": REFUSAL_MESSAGE, "source": "filter"}

    docs_with_scores = db.similarity_search_with_score(question, k=3)
    best_score = docs_with_scores[0][1] if docs_with_scores else 999

    if best_score < similarity_threshold:
        answer = rag_chain.invoke(
            {"question": question, "chat_history": chat_history}
        ).strip()
        # Clean answer
        answer = answer.replace("• •", "•")
        answer = answer.replace("\n\n\n", "\n\n")

        # Remove duplicate lines
        #lines = []
        #seen = set()

        #for line in answer.split("\n"):
            #line = line.strip()
            #if line and line not in seen:
                #seen.add(line)
                #lines.append(line)

        #answer = "\n".join(lines)
        
        if "NOT_IN_DOCUMENT" not in answer:
            return {"answer": answer, "source": "documents", "score": float(best_score)}

    website_content = search_yas_website(question)
    if website_content:
        for _ in range(3):
            try:
                answer = website_chain.invoke(
                    {
                        "website_content": website_content,
                        "question": question,
                        "chat_history": chat_history,
                    }
                ).strip()
                # Clean answer
                answer = answer.replace("• •", "•")
                answer = answer.replace("\n\n\n", "\n\n")
                
                # Remove duplicate lines
                #lines = []
                #seen = set()
                
                #for line in answer.split("\n"):
                    #line = line.strip()
                    #if line and line not in seen:
                        #seen.add(line)
                        #lines.append(line)
                
                    #answer = "\n".join(lines)
                if "NOT_ON_WEBSITE" not in answer:
                    return {"answer": answer, "source": "website"}
                break
            except Exception as e:
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    time.sleep(2)
                    continue
                break

    return {"answer": NO_ANSWER_MESSAGE, "source": "none"}


# ─── Flask App ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True) or {}
    question = (data.get("message") or data.get("question") or "").strip()
    history = data.get("history", [])
    if not question:
        return jsonify({"error": "message is required"}), 400
    try:
        result = ask(question, chat_history=history)
        return jsonify(result)
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
