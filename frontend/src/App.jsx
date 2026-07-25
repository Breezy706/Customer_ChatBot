import React, { useEffect, useRef, useState } from "react";
import logo from "./yas-logo.png";

const API = import.meta.env.VITE_API_URL || "http://localhost:5000";

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: "Welcome to Yas! 👋 I'm your assistant. Ask me anything about Yas products, services, networks, or plans.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => { inputRef.current?.focus(); }, []);

  const send = async () => {
    const q = input.trim();
    if (!q || loading) return;
    setMessages((m) => [...m, { role: "user", text: q }]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: q }),
      });
      const data = await res.json();
      setMessages((m) => [...m, {
        role: "bot",
        text: data.answer || "Sorry, I couldn't find an answer.",
        sources: data.sources,
      }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "bot", text: "⚠️ Couldn't reach the server. Please make sure the backend (app.py) is running on port 5000." }]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 30);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="logo-badge"><img src={logo} alt="Yas" /></div>
          <div style={{ flex: 1 }}>
            <div className="title">Yas Assistant</div>
            <div className="subtitle"><span className="status-dot" /> Online • Customer Care</div>
          </div>
          <span className="badge">AI Powered</span>
        </div>
      </header>

      <main className="main">
        <div className="container">
          <div className="chat-card">
            <div className="messages" ref={scrollRef}>
              {messages.map((m, i) => <Bubble key={i} msg={m} />)}
              {loading && <Typing />}
            </div>
            <div className="composer">
              <input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send()}
                placeholder="Type your question here..."
              />
              <button onClick={send} disabled={loading || !input.trim()}>Send</button>
            </div>
            <div className="hint">Answers are based on official Yas Tanzania information.</div>
          </div>
        </div>
      </main>

      <footer className="footer">© {new Date().getFullYear()} Yas Tanzania • Customer Care Assistant</footer>
    </div>
  );
}

function Bubble({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={`row ${isUser ? "user" : ""}`}>
      {!isUser && <div className="avatar bot">🎧</div>}
      <div className={`bubble ${isUser ? "user" : "bot"}`}>
        {msg.text}
        {msg.sources?.length > 0 && (
          <div className="sources">
            <div style={{ fontWeight: 700, marginBottom: 4 }}>Sources:</div>
            {msg.sources.slice(0, 3).map((s, i) => (
              <div key={i} style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                <a href={s} target="_blank" rel="noreferrer">{s}</a>
              </div>
            ))}
          </div>
        )}
      </div>
      {isUser && <div className="avatar user">You</div>}
    </div>
  );
}

function Typing() {
  return (
    <div className="row">
      <div className="avatar bot"><span className="bob">🎧</span></div>
      <div className="bubble bot dots"><span/><span/><span/></div>
    </div>
  );
}
