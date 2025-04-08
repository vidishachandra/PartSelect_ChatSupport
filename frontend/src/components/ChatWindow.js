import React, { useState, useEffect, useRef } from "react";
import "./ChatWindow.css";
import { getAIMessage } from "../api/api";
import { marked } from "marked";

function ChatWindow() {
  const defaultMessage = [{
    role: "assistant",
    content: "Hi! I'm your PartSelect support assistant. How can I help you today?",
    relevantParts: []
  }];

  const examplePrompts = [
    "How to install part PS11752778?",
    "My Whirlpool dishwasher is leaking. What should I do?",
    "Is this part compatible with model WDT780SAEM1?"
  ];

  const [messages, setMessages] = useState(defaultMessage);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (input) => {
    if (input.trim() !== "") {
      setIsLoading(true);
      // Set user message
      setMessages(prevMessages => [...prevMessages, { role: "user", content: input }]);
      setInput("");

      try {
        // Call API & set assistant message
        const newMessage = await getAIMessage(input);
        setMessages(prevMessages => [...prevMessages, newMessage]);
      } catch (error) {
        console.error('Error:', error);
        setMessages(prevMessages => [...prevMessages, {
          role: "assistant",
          content: "I'm sorry, I encountered an error. Please try again.",
          relevantParts: []
        }]);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleExampleClick = (prompt) => {
    setInput(prompt);
  };

  const ProductCard = ({ part }) => (
    <div className="product-card">
      <img src={part.image_url} alt={part.title} className="product-image" />
      <div className="product-info">
        <h3>{part.title}</h3>
        <p className="price">${part.price}</p>
        {part.installation_video_url && (
          <a 
            href={part.installation_video_url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="video-link"
          >
            Watch Installation Video
          </a>
        )}
      </div>
    </div>
  );

  return (
    <div className="chat-container">
      <div className="example-prompts">
        <h3>Try These:</h3>
        <div className="prompt-buttons">
          {examplePrompts.map((prompt, index) => (
            <button
              key={index}
              onClick={() => handleExampleClick(prompt)}
              className="prompt-button"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>
      <div className="messages-container">
        {messages.map((message, index) => (
          <div key={index} className={`${message.role}-message-container`}>
            {message.content && (
              <div className={`message ${message.role}-message`}>
                <div dangerouslySetInnerHTML={{__html: marked(message.content).replace(/<p>|<\/p>/g, "")}}></div>
                {message.relevantParts && message.relevantParts.length > 0 && (
                  <div className="relevant-parts">
                    {message.relevantParts.map((part, partIndex) => (
                      <ProductCard key={partIndex} part={part} />
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="loading-container">
            <div className="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
        <div className="input-area">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            onKeyPress={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                handleSend(input);
                e.preventDefault();
              }
            }}
            rows="3"
          />
          <button 
            className="send-button" 
            onClick={() => handleSend(input)}
            disabled={isLoading}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default ChatWindow;
