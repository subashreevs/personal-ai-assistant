import { useState, useEffect, useRef } from "react";
import axios from "axios";
import "./App.css";

type Role = "user" | "assistant";

type Theme = "dark" | "light";

interface Source {
  id: string;
  score?: number;
  source: string;
}

interface Message {
  id: number;
  role: Role;
  content: string;
  sources?: Source[];
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const LINKEDIN_URL = "https://www.linkedin.com/in/subashreevs";

const promptIdeas = [
  "Tell me about Subashree",
  "What kind of work has she done?",
  "What is she good at?",
  "What projects should I ask her about?",
];

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [theme, setTheme] = useState<Theme>(() => {
    const savedTheme = window.localStorage.getItem("assistant-theme");
    if (savedTheme === "dark" || savedTheme === "light") return savedTheme;
    return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  });

  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    window.localStorage.setItem("assistant-theme", theme);
  }, [theme]);

  const sendQuestion = async (questionText?: string) => {
    const question = (questionText ?? input).trim();
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

      const history = messages.slice(-6).map(({ role, content }) => ({ role, content }));

      const response = await axios.post(`${API_BASE_URL}/chat`, {
        question,
        history,
      });

      const answerText: string = response.data.answer || "No answer returned.";
      const sources: Source[] = response.data.sources || [];

      const botMessage: Message = {
        id: Date.now() + 1,
        role: "assistant",
        content: answerText,
        sources,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      console.error(err);
      setError("I could not reach the assistant server. Try again in a bit.");

      const errorMessage: Message = {
        id: Date.now() + 2,
        role: "assistant",
        content:
          "Sorry, I could not get an answer right now. Please try again.",
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = () => {
    sendQuestion();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleTheme = () => {
    setTheme((current) => (current === "dark" ? "light" : "dark"));
  };


  const renderMessageContent = (content: string) => {
    const lines = content.split("\n");
    const elements: React.ReactNode[] = [];
    let bullets: string[] = [];

    const flushBullets = () => {
      if (bullets.length === 0) return;
      elements.push(
        <ul key={`list-${elements.length}`}>
          {bullets.map((bullet, index) => (
            <li key={`${bullet}-${index}`}>{bullet}</li>
          ))}
        </ul>,
      );
      bullets = [];
    };

    lines.forEach((line, index) => {
      const trimmed = line.trim();
      if (!trimmed) {
        flushBullets();
        return;
      }

      if (trimmed.startsWith("- ")) {
        bullets.push(trimmed.slice(2));
        return;
      }

      flushBullets();
      elements.push(<p key={`p-${index}`}>{trimmed}</p>);
    });

    flushBullets();
    return elements;
  };

  return (
    <div className={`app-root theme-${theme}`}>
      <section className="chat-card" aria-label="Subashree personal assistant chat">
        <header className="chat-header">
          <div className="header-main">
            <img src="/suba.jpg" alt="Subashree" className="profile-photo" />
            <div className="header-copy">
              <p className="chat-kicker">Hi, I am Subashree's assistant</p>
              <h1>Ask me anything about her.</h1>
            </div>
          </div>
          <div className="header-actions">
            <button
              type="button"
              className="theme-toggle"
              onClick={toggleTheme}
              aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
              title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            >
              {theme === "dark" ? (
                <svg className="theme-icon" viewBox="0 0 24 24" aria-hidden="true">
                  <circle cx="12" cy="12" r="4" />
                  <path d="M12 2v2" />
                  <path d="M12 20v2" />
                  <path d="m4.93 4.93 1.41 1.41" />
                  <path d="m17.66 17.66 1.41 1.41" />
                  <path d="M2 12h2" />
                  <path d="M20 12h2" />
                  <path d="m6.34 17.66-1.41 1.41" />
                  <path d="m19.07 4.93-1.41 1.41" />
                </svg>
              ) : (
                <svg className="theme-icon" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M21 12.8A8.5 8.5 0 1 1 11.2 3 6.5 6.5 0 0 0 21 12.8z" />
                </svg>
              )}
            </button>
            <nav className="header-links" aria-label="Profile links">
              <a href="/resume.pdf" target="_blank" rel="noreferrer" aria-label="Open resume" title="Resume">
                <svg className="link-icon" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M7 3h7l5 5v13H7z" />
                  <path d="M14 3v6h5" />
                  <path d="M9.5 13h5" />
                  <path d="M9.5 16h5" />
                </svg>
                <span className="link-label">Resume</span>
              </a>
              <a href={LINKEDIN_URL} target="_blank" rel="noreferrer" aria-label="Open LinkedIn" title="LinkedIn">
                <svg className="link-icon" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M6.5 10v8" />
                  <path d="M6.5 6.5v.01" />
                  <path d="M11 18v-8" />
                  <path d="M11 13.5c0-2 1.2-3.5 3.2-3.5s3.3 1.3 3.3 3.8V18" />
                </svg>
                <span className="link-label">LinkedIn</span>
              </a>
            </nav>
          </div>
        </header>

        <main className="chat-main">
          {messages.length === 0 && (
            <div className="welcome-panel">
              <p>
                I can help with quick questions about her background, work, projects,
                or what she might be a good fit for.
              </p>
              <div className="prompt-grid">
                {promptIdeas.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    className="prompt-chip"
                    onClick={() => sendQuestion(prompt)}
                    disabled={loading}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="chat-messages" aria-live="polite">
            {messages.map((msg) => {
              return (
                <div
                  key={msg.id}
                  className={`message-row ${
                    msg.role === "user" ? "message-user" : "message-assistant"
                  }`}
                >
                  <div className="message-bubble">
                    <div className="message-content">{renderMessageContent(msg.content)}</div>
                  </div>
                </div>
              );
            })}

            {loading && (
              <div className="message-row message-assistant">
                <div className="message-bubble loading-bubble">
                  <div className="typing-indicator" aria-label="Assistant is thinking">
                    <span />
                    <span />
                    <span />
                  </div>
                </div>
              </div>
            )}

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
              {loading ? "..." : "Send"}
            </button>
          </div>
        </footer>
      </section>
    </div>
  );
}

export default App;







