import React, { useEffect, useRef, useState } from "react";

const API_BASE = (process.env.REACT_APP_CHATBOT_API_BASE || "").replace(/\/$/, "");

interface Source {
  title?: string;
  url?: string;
  score?: number;
}

interface ChatTurn {
  role: "user" | "bot";
  text: string;
  sources?: Source[];
}

const ChatWidget: React.FC = () => {
  const [sessionId, setSessionId] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [history, setHistory] = useState<ChatTurn[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const bodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    createSession();
  }, []);

  useEffect(() => {
    bodyRef.current?.scrollTo({ top: bodyRef.current.scrollHeight });
  }, [history, loading]);

  const createSession = async (): Promise<void> => {
    try {
      const res = await fetch(`${API_BASE}/api/session/`, { method: "POST" });
      const data = await res.json();
      setSessionId(data.session_id);
    } catch {
      /* session is optional */
    }
  };

  const handleSend = async (): Promise<void> => {
    const text = message.trim();
    if (!text || loading) return;
    setMessage("");
    setHistory((h) => [...h, { role: "user", text }]);
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: text, language: "auto" }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.session_id) setSessionId(data.session_id);
      setHistory((h) => [...h, { role: "bot", text: data.response, sources: data.sources }]);
    } catch {
      setHistory((h) => [...h, { role: "bot", text: "Sorry, something went wrong. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-widget" style={{ display: "flex" }}>
      <div className="chat-header">Travel Assistant</div>
      <div className="chat-body" ref={bodyRef}>
        {history.map((turn, i) => (
          <div key={i} className={`message ${turn.role}`}>
            {turn.text}
            {turn.sources && turn.sources.length > 0 && (
              <div className="sources">
                {turn.sources
                  .filter((s) => s.url)
                  .map((s, j) => (
                    <a key={j} href={s.url} target="_blank" rel="noopener noreferrer">
                      {s.title || s.url}
                    </a>
                  ))}
              </div>
            )}
          </div>
        ))}
        {loading && <div className="loading">Assistant is typing…</div>}
      </div>
      <div className="chat-input">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Type your message…"
        />
        <button onClick={handleSend} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatWidget;
