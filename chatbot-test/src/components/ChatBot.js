/**
 * PE/VC Chatbot React Component
 * Embed this in your existing React portal
 */

import React, { useState, useRef, useEffect } from "react";
import { sendChatMessage, checkHealth } from "./chatbot-api";
import "./chatbot.css";
import logo from "../assets/UG-Icon.png";

const ChatBot = ({ userId = "anonymous", portalName = "PE/VC Portal" }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const [showChat, setShowChat] = useState(false);
  const messagesEndRef = useRef(null);

  // Check API health on mount
  useEffect(() => {
    checkHealth()
      .then(() => setIsOnline(true))
      .catch(() => setIsOnline(false));
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();

    if (!input.trim() || !isOnline) return;

    // Add user message
    const userMessage = {
      id: Date.now().toString(),
      text: input,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      // Send to API
      const response = await sendChatMessage(
        input,
        userId,
        messages.map((m) => ({
          role: m.sender === "user" ? "user" : "assistant",
          content: m.text,
        }))
      );

      // Add bot response
      const botMessage = {
        id: (Date.now() + 1).toString(),
        text: response.response,
        sender: "bot",
        timestamp: new Date(),
        confidence: response.confidence_score,
        sources: response.sources,
      };

      setMessages((prev) => [...prev, botMessage]);

      // Add warning if low confidence
      if (response.requires_attention) {
        const warningMessage = {
          id: (Date.now() + 2).toString(),
          text: "⚠️ This answer has low confidence. If it doesn't help, please contact our support team.",
          sender: "bot",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, warningMessage]);
      }
    } catch (error) {
      console.error("Chat error:", error);
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        text: "Sorry, I encountered an error. Please try again later.",
        sender: "bot",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  if (!isOnline) {
    return (
      <div className="chatbot-offline">
        <p>❌ Chatbot is currently offline. Please try again later.</p>
      </div>
    );
  }

  return (
    <>
      {/* Floating Chat Button */}
      {!showChat && (
        <button className="chatbot-float-button" onClick={() => setShowChat(true)}>
          💬
        </button>
      )}

      {/* Chat Window */}
      {showChat && (
        <div className="chatbot-container">
          {/* Header */}
          <div className="chatbot-header">
            <div className="chatbot-header-branding">
              <div className="chatbot-logo-container">
                <img src={logo} alt="Alex Logo" className="chatbot-logo" />
              </div>
              <h3>Alex</h3>
            </div>
            <button
              className="chatbot-close-btn"
              onClick={() => setShowChat(false)}
            >
              ✕
            </button>
          </div>

          {/* Messages */}
          <div className="chatbot-messages">
            {messages.length === 0 && (
              <div className="chatbot-welcome">
                <p>👋 Welcome! I'm your {portalName} investment assistant.</p>
                <p>Ask me about:</p>
                <ul>
                  <li>Investment process and requirements</li>
                  <li>Portal features and navigation</li>
                  <li>VC/PE investment topics</li>
                  <li>Document access and downloads</li>
                </ul>
              </div>
            )}

            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`chatbot-message-wrapper ${msg.sender}`}
              >
                <div className="chatbot-message">
                  <p>{msg.text}</p>
                  {/*{msg.sender === "bot" && msg.confidence !== undefined && (
                    <small className="chatbot-confidence">
                      Confidence: {(msg.confidence * 100).toFixed(0)}%
                    </small>
                  )}*/}
                  {/* Sources hidden from UI - data still stored in backend for logging/analytics */}
                  {/* {msg.sources && msg.sources.length > 0 && (
                    <small className="chatbot-sources">
                      📚 Sources: {msg.sources.join(", ")}
                    </small>
                  )} */}
                </div>
              </div>
            ))}

            {loading && (
              <div className="chatbot-message-wrapper bot">
                <div className="chatbot-message loading">
                  <p>🤔 Thinking...</p>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Form */}
          <form onSubmit={handleSendMessage} className="chatbot-form">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question..."
              disabled={loading}
              className="chatbot-input"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="chatbot-send-btn"
            >
              Send
            </button>
          </form>
        </div>
      )}
    </>
  );
};

export default ChatBot;
