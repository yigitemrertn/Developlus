import { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send } from 'lucide-react';
import { sendChatMessage } from '../api/analyzeApi';

const INITIAL_MESSAGE = {
  role: 'ai',
  text: 'Hello! 👋 I am the Developlus AI assistant. I can answer questions about your project idea.'
};

export default function ChatPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([INITIAL_MESSAGE]);
  const [inputVal, setInputVal] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function handleSend(e) {
    e.preventDefault();
    const msg = inputVal.trim();
    if (!msg) return;

    setMessages(prev => [...prev, { role: 'user', text: msg }]);
    setInputVal('');
    setIsTyping(true);

    const reply = await sendChatMessage(msg);
    setIsTyping(false);
    setMessages(prev => [...prev, { role: 'ai', text: reply }]);
  }

  return (
    <>
      <button
        className="chat-toggle"
        id="chatToggle"
        onClick={() => setIsOpen(prev => !prev)}
        aria-label="Toggle Chat"
      >
        <MessageCircle size={24} />
      </button>

      <div className={`chat-panel ${isOpen ? 'open' : 'closed'}`} id="chatPanel">
        <div className="chat-header">
          <div className="dot" />
          <span>Developlus AI Assistant</span>
        </div>

        <div className="chat-messages" id="chatMessages">
          {messages.map((m, i) => (
            <div key={i} className={`chat-msg ${m.role}`}>
              {m.text}
            </div>
          ))}
          {isTyping && (
            <div className="chat-msg ai" style={{ opacity: 0.6 }}>
              <span>●</span><span style={{ animationDelay: '.2s' }}>●</span><span style={{ animationDelay: '.4s' }}>●</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          <form onSubmit={handleSend}>
            <div className="chat-input-row">
              <input
                type="text"
                id="chatInput"
                placeholder="Ask a question..."
                autoComplete="off"
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
              />
              <button type="submit" className="chat-send-btn" aria-label="Send">
                <Send size={16} />
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  );
}
