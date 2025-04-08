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
    "How to install part PS67910065?",
    "My Whirlpool dishwasher is leaking. What should I do?",
    "Is this part compatible with manufactere model WDT780SAEM1?"
  ];

  const [messages, setMessages] = useState(defaultMessage);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [inputError, setInputError] = useState(null);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Focus input field when component mounts
  useEffect(() => {
    inputRef.current.focus();
  }, []);

  const validateInput = (text) => {
    if (!text.trim()) {
      setInputError("Please enter a message");
      return false;
    }
    if (text.length < 3) {
      setInputError("Message is too short. Please provide more details.");
      return false;
    }
    setInputError(null);
    return true;
  };

  const handleSend = async (input) => {
    if (!validateInput(input)) {
      return;
    }

    setIsLoading(true);
    setError(null);
    
    // Set user message
    setMessages(prevMessages => [...prevMessages, { role: "user", content: input }]);
    setInput("");

    try {
      // Call API & set assistant message
      const newMessage = await getAIMessage(input);
      
      // Check if the response contains an error
      if (newMessage.error) {
        setError(newMessage.content);
        setMessages(prevMessages => [...prevMessages, {
          role: "assistant",
          content: newMessage.content,
          relevantParts: [],
          isError: true
        }]);
      } else {
        setMessages(prevMessages => [...prevMessages, newMessage]);
      }
    } catch (error) {
      console.error('Error:', error);
      setError("I'm sorry, I encountered an error. Please try again.");
      setMessages(prevMessages => [...prevMessages, {
        role: "assistant",
        content: "I'm sorry, I encountered an error. Please try again.",
        relevantParts: [],
        isError: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExampleClick = (prompt) => {
    setInput(prompt);
    setInputError(null);
    // Focus the input field after setting the example
    setTimeout(() => inputRef.current.focus(), 0);
  };

  const handleInputChange = (e) => {
    setInput(e.target.value);
    setInputError(null);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      handleSend(input);
      e.preventDefault();
    }
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
      <div className="chat-header">
        <img 
          src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSwYSmp4PH1yqaz-sOeYITj7XuHlf5wRHkFSVNHPo6r2OLQ0N4G8gPrufJYIMKVCFf1KWw&usqp=CAU" 
          alt="PartSelect Logo" 
          className="partselect-logo"
        />
        <h1 className="chat-title">Appliance Support Assistant</h1>
      </div>
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
        {error && (
          <div className="error-banner">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}
        {messages.map((message, index) => (
          <div key={index} className={`${message.role}-message-container`}>
            {message.content && (
              <div className={`message ${message.role}-message ${message.isError ? 'error-message' : ''}`}>
                <div dangerouslySetInnerHTML={{
                  __html: marked(
                    message.role === "assistant" 
                      ? (() => {
                          // Find the first occurrence of "Hi!"
                          const hiIndex = message.content.indexOf("Hi!");
                          if (hiIndex === -1) return message.content;
                          
                          // Find the next newline after "Hi!"
                          const nextNewlineIndex = message.content.indexOf("\n", hiIndex);
                          if (nextNewlineIndex === -1) return message.content.substring(hiIndex);
                          
                          // Check if the next line starts with a bullet point
                          const afterNewline = message.content.substring(nextNewlineIndex + 1);
                          if (afterNewline.trim().startsWith("-")) {
                            // This is a properly formatted response
                            return message.content.substring(hiIndex);
                          }
                          
                          // If we get here, there might be thought process after "Hi!"
                          // Find the next occurrence of "Hi!" after the first one
                          const secondHiIndex = message.content.indexOf("Hi!", hiIndex + 3);
                          if (secondHiIndex !== -1) {
                            // There's a second "Hi!" - use that as the start
                            return message.content.substring(secondHiIndex);
                          }
                          
                          // If we can't find a second "Hi!", just return from the first one
                          return message.content.substring(hiIndex);
                        })()
                      : message.content
                  ).replace(/<p>|<\/p>/g, "")
                }}></div>
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
          <div className="input-container">
            <input
              ref={inputRef}
              value={input}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              placeholder="Type a message..."
              className={inputError ? "input-error" : ""}
              disabled={isLoading}
            />
            {inputError && <div className="input-error-message">{inputError}</div>}
          </div>
          <button 
            className="send-button" 
            onClick={() => handleSend(input)}
            disabled={isLoading}
          >
            {isLoading ? "Sending..." : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ChatWindow;
