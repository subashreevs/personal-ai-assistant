import { useState, useEffect, useRef } from "react";
import axios from "axios";
import "./App.css";

type Role = "user" | "assistant";

interface Message {
  id: number;
  role: Role;
  content: string;
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ⬇⬇⬇ AUTO-SCROLL HOOKS
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);
  // ⬆⬆⬆ AUTO-SCROLL HOOKS

  const handleSend = async () => {
    const question = input.trim();
    if (!question || loading) return;

    setInput("");
    setError(null);

    const userMessage: Message = {
      id: Date.now(),
      role: "user",
      content: question,
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      setLoading(true);

      const response = await axios.post(`${API_BASE_URL}/chat`, {
        question,
      });

      const answerText: string = response.data.answer || "No answer returned.";

      const botMessage: Message = {
        id: Date.now() + 1,
        role: "assistant",
        content: answerText,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      console.error(err);
      setError("Something went wrong while talking to the server.");

      const errorMessage: Message = {
        id: Date.now() + 2,
        role: "assistant",
        content:
          "Sorry, I couldn't get an answer from the backend. Please try again.",
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="app-root">
      <div className="chat-container">
        <header className="chat-header">
          <h1>✨ Subashree's Personal AI Assistant</h1>
          <p>Ask me anything about my work, projects, education, skills or background!</p>
        </header>

        <main className="chat-main">
          {messages.length === 0 && (
            <div className="chat-empty">
              <p>Try asking me something like:</p>
              <ul>
                <li>What are her strongest technical skills?</li>
                <li>Tell me about her frontend experience</li>
                <li>Summarize her background in 3 points</li>
              </ul>
            </div>
          )}

          <div className="chat-messages">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`message-row ${
                  msg.role === "user" ? "message-user" : "message-assistant"
                }`}
              >
                <div className="message-bubble">
                  <div className="message-role">
                    {msg.role === "user" ? "YOU" : "ASSISTANT"}
                  </div>
                  <div className="message-content">{msg.content}</div>
                </div>
              </div>
            ))}

            {/* AUTO SCROLL TARGET */}
            <div ref={bottomRef}></div>
          </div>
        </main>

        <footer className="chat-footer">
          {error && <div className="error-banner">{error}</div>}

          <div className="input-row">
            <input
              type="text"
              placeholder="Ask something about Suba..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />
            <button onClick={handleSend} disabled={loading || !input.trim()}>
              {loading ? "Thinking..." : "Send ✨"}
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default App;