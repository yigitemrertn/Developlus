import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User } from 'lucide-react';

export default function ChatView({ project, chatHistory, onSendMessage, onGoToSurvey }) {
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef(null);
  const isSendingRef = useRef(false); // Strict lock

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  const handleSend = async (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || !project || isStreaming || isSendingRef.current) return;
    
    isSendingRef.current = true;
    const msg = input;
    setInput('');
    setIsStreaming(true);
    
    try {
      await onSendMessage(project.id, msg);
    } catch (err) {
      console.error("Send error:", err);
    } finally {
      setIsStreaming(false);
      isSendingRef.current = false;
    }
  };

  return (
    <div className="view-container chat-view glass">
      <div className="view-header flex-between">
        <div>
          <h2>{project?.name || 'No Project Selected'} - Chat</h2>
          <p className="subtitle">Architectural & Technical AI Consultant</p>
        </div>
        {project && (
          <button className="survey-nav-btn secondary" onClick={onGoToSurvey}>
            <span>View Project Constraints</span>
          </button>
        )}
      </div>

      <div className="chat-messages-container">
        {chatHistory && chatHistory.length > 0 ? (
          chatHistory.map((msg, idx) => (
            <div key={msg.id || idx} className={`message-row ${msg.role}`}>
              <div className="message-avatar">
                {msg.role === 'assistant' ? <Bot size={20} /> : <User size={20} />}
              </div>
              <div className="message-bubble">
                <div className="message-content">
                  {(msg.content || '').split('\n').map((line, i) => (
                    <span key={i}>
                      {line}
                      <br />
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="empty-state">
            <Bot size={48} className="empty-icon" />
            <h3>Consult with Developlus AI</h3>
            <p>Tell me about your project or ask for technical advice.</p>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-wrapper">
        <form 
          onSubmit={handleSend} 
          className="chat-input-form"
        >
          <input
            type="text"
            placeholder={isStreaming ? "Thinking..." : "Describe your project or ask a question..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={!project || isStreaming}
            autoFocus
          />
          <button 
            type="submit" 
            disabled={!input.trim() || !project || isStreaming} 
            className="send-btn"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
