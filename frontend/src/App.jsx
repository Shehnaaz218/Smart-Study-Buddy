
import { useState, useEffect } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

export default function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! I'm your Smart Study Buddy. Ask me about your lecture notes.",
      sources: [],
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [quizTopic, setQuizTopic] = useState("");
  const [quiz, setQuiz] = useState([]);
  const [quizLoading, setQuizLoading] = useState(false);
  const [quizError, setQuizError] = useState("");
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  useEffect(() => {
  fetchConversations();
}, []);


async function fetchConversations() {
  try {
    const response = await fetch(`${API_URL}/api/conversations`);

    if (!response.ok) {
      throw new Error("Could not load conversations.");
    }

    const data = await response.json();
    setConversations(data);

  } catch (error) {
    console.error("Conversation loading error:", error);
  }
}

async function loadConversation(conversationId) {
  try {
    console.log("Loading conversation ID:", conversationId);

    const response = await fetch(
      `${API_URL}/api/conversations/${conversationId}/messages`
    );

    console.log("API response status:", response.status);

    if (!response.ok) {
      throw new Error("Could not load conversation messages.");
    }

    const data = await response.json();

    console.log("Messages received:", data);

    setActiveConversationId(Number(conversationId));

    setMessages(
      data.map((message) => ({
        role: message.role,
        content: message.content,
        sources: [],
      }))
    );

  } catch (error) {
    console.error("Load conversation error:", error);
    alert(error.message);
  }
}







async function sendMessage(e) {
  e.preventDefault();

  const text = question.trim();

  if (!text || loading) return;

  setQuestion("");
  setLoading(true);

  try {
    // 1. Create a conversation if one is not active.
    let conversationId = activeConversationId;

    if (!conversationId) {
      const createResponse = await fetch(
        `${API_URL}/api/conversations`,
        { method: "POST" }
      );

      if (!createResponse.ok) {
        throw new Error("Could not create conversation.");
      }

      const conversationData = await createResponse.json();

      conversationId = conversationData.id;
      setActiveConversationId(conversationId);

      await fetchConversations();
    }

    // 2. Save the user's message.
    const saveUserResponse = await fetch(
      `${API_URL}/api/conversations/${conversationId}/messages`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          role: "user",
          content: text,
        }),
      }
    );

    if (!saveUserResponse.ok) {
      throw new Error("Could not save your message.");
    }

    const savedUserMessage = await saveUserResponse.json();

    // Refresh sidebar to display the updated conversation title.
await fetchConversations();

    setMessages((prev) => [
      ...prev,
      { role: "user", content: text },
    ]);

    // 3. Get the AI response.
    const response = await fetch(`${API_URL}/api/chat`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    question: text,
    conversation_id: conversationId,
    before_message_id: savedUserMessage.id,
  }),
});

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `Server returned ${response.status}`
      );
    }

    const data = await response.json();

    // 4. Save the assistant's response.
    const saveAssistantResponse = await fetch(
      `${API_URL}/api/conversations/${conversationId}/messages`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          role: "assistant",
          content: data.answer,
        }),
      }
    );

    if (!saveAssistantResponse.ok) {
      throw new Error("AI answered, but its response could not be saved.");
    }

    // 5. Display the assistant's response.
    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content: data.answer,
        sources: data.sources || [],
      },
    ]);

  } catch (error) {
    console.error("Chat error:", error);

    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content: `Error: ${error.message}`,
        sources: [],
      },
    ]);

  } finally {
    setLoading(false);
  }
}

  async function generateQuiz() {
  setQuizLoading(true);
  setQuizError("");
  setQuiz([]);
  setSelectedAnswers({});
  setSubmitted(false);

  try {
    const response = await fetch(`${API_URL}/api/quiz`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        topic: quizTopic.trim() || "all lecture notes",
        num_questions: 5,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Quiz generation failed.");
    }

    setQuiz(data.questions || []);
    if (!data.questions?.length) {
      setQuizError("No quiz questions were returned.");
    }
  } catch (error) {
    setQuizError(error.message);
  } finally {
    setQuizLoading(false);
  }
}


  async function startNewChat() {
  try {
    const response = await fetch(`${API_URL}/api/conversations`, {
      method: "POST",
    });

    if (!response.ok) {
      throw new Error("Could not create a new conversation.");
    }

    const data = await response.json();

    setActiveConversationId(data.id);

    setMessages([
      {
        role: "assistant",
        content: "New conversation started. What would you like to learn?",
        sources: [],
      },
    ]);

    await fetchConversations();

  } catch (error) {
    console.error("New conversation error:", error);
    alert(error.message);
  }
}

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">S</div>
          <div>
            <h2>Study Buddy</h2>
            <p>AI Learning Assistant</p>
          </div>
        </div>

        <button className="new-chat" onClick={startNewChat}>
          + New conversation
        </button>

<div className="conversation-list">
  <h3>Recent conversations</h3>

  {conversations.map((conversation) => (
    <button
      key={conversation.id}
      className={`conversation-item ${
        activeConversationId === conversation.id ? "active" : ""
      }`}
      onClick={() => loadConversation(conversation.id)}
    >
      {conversation.title || `Conversation ${conversation.id}`}
    </button>
  ))}
</div>


        <div className="sidebar-note">
          <span className="status-dot" />
          <span>Lecture notes assistant</span>
        </div>

        <div className="sidebar-footer">
          Powered by React + FastAPI
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <h1>Smart Study Buddy</h1>
            <p>Learn faster with your lecture notes</p>
          </div>
          <span className="online-badge">
            ● {loading ? "Thinking..." : "Connected"}
          </span>
        </header>
        <section className="quiz-panel">
  <h2>Practice Quiz</h2>
  <p>Generate a quiz from your lecture notes.</p>

  <div className="quiz-controls">
    <input
      value={quizTopic}
      onChange={(e) => setQuizTopic(e.target.value)}
      placeholder="Enter a topic, e.g. Cell Biology"
      aria-label="Quiz topic"
    />

    <button onClick={generateQuiz} disabled={quizLoading}>
      {quizLoading ? "Generating..." : "Generate Quiz"}
    </button>
  </div>

  {quizError && <p className="quiz-error">{quizError}</p>}

  {quiz.length > 0 && (
    <div className="quiz-questions">
      {quiz.map((item, index) => (
        <div className="quiz-card" key={index}>
          <h3>
            {index + 1}. {item.question}
          </h3>

          {item.options.map((option, optionIndex) => (
            <label className="quiz-option" key={optionIndex}>
              <input
                type="radio"
                name={`quiz-${index}`}
                value={option}
                checked={selectedAnswers[index] === option}
                disabled={submitted}
                onChange={() =>
                  setSelectedAnswers((prev) => ({
                    ...prev,
                    [index]: option,
                  }))
                }
              />
              {option}
            </label>
          ))}

          {submitted && (
            <div className="quiz-feedback">
              <p>
                <strong>Correct answer:</strong> {item.answer}
              </p>
              <p>
                <strong>Explanation:</strong> {item.explanation}
              </p>
            </div>
          )}
        </div>
      ))}

      {!submitted ? (
        <button
          onClick={() => setSubmitted(true)}
          disabled={Object.keys(selectedAnswers).length !== quiz.length}
        >
          Check Answers
        </button>
      ) : (
        <p className="quiz-score">
          Score:{" "}
          {quiz.filter(
            (item, index) => selectedAnswers[index] === item.answer
          ).length}{" "}
          / {quiz.length}
        </p>
      )}
    </div>
  )}
</section>

        <section className="chat">
          {messages.map((message, index) => (
            <div
              className={`message-row ${message.role}`}
              key={index}
            >
              <div className="avatar">
                {message.role === "assistant" ? "S" : "You"}
              </div>

              <div className="message-content">
                <span className="sender">
                  {message.role === "assistant" ? "Study Buddy" : "You"}
                </span>

                <div className="bubble">{message.content}</div>

                {message.role === "assistant" &&
                  message.sources?.length > 0 && (
                    <div className="sources">
                        <h4>📚 Sources ({message.sources.length})</h4>

                      {message.sources.map((source, sourceIndex) => (
                        <div
                          className="source-card"
                          key={`${source.source}-${sourceIndex}`}
                        >
                          <div className="source-title">
                            {source.source || "Lecture notes"}
                          </div>

                          {source.snippet && (
                            <p className="source-snippet">
                              {source.snippet}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
              </div>
            </div>
          ))}

          {loading && (
            <p className="composer-hint">
              Study Buddy is thinking...
            </p>
          )}
        </section>

        <form className="composer" onSubmit={sendMessage}>
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about your lecture notes..."
            aria-label="Your question"
          />

          <button type="submit" disabled={!question.trim() || loading}>
            {loading ? "Wait..." : "Send ↑"}
          </button>

          <p className="composer-hint">
            Answers come from your lecture notes using AI.
          </p>
        </form>
      </main>
    </div>
  );
}
