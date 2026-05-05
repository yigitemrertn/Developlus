import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User } from 'lucide-react';

export default function ChatView({ project, chatHistory, onSendMessage }) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim() || !project) return;
    onSendMessage(project.id, input);
    setInput('');
  };

  return (
    <div className="view-container chat-view glass">
      <div className="view-header">
        <h2>{project?.name || 'Proje Seçilmedi'} - Chat</h2>
        <p className="subtitle">Mimari ve teknik kararlar için danışın</p>
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
                  {msg.content.split('\n').map((line, i) => (
                    <span key={i}>{line}<br /></span>
                  ))}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="empty-state">
            <Bot size={48} className="empty-icon" />
            <h3>Henüz mesaj yok</h3>
            <p>Projeye dair aklınızdaki soruları aşağıdan sorabilirsiniz.</p>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-wrapper">
        <form onSubmit={handleSend} className="chat-input-form">
          <input
            type="text"
            placeholder="Kullanıcı mesajı buraya girilecek..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={!project}
          />
          <button type="submit" disabled={!input.trim() || !project} className="send-btn">
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
