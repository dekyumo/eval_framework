import { useState } from 'react';
import { MessageBubble } from '../components/MessageBubble';
import { Button } from '../components/ui/Button';
import { Heading } from '../components/ui/Typography';
import { PageContainer, PagePane } from '../components/ui/PageLayout';

export function ChatOperator() {
  const [messages, setMessages] = useState<any[]>([
    { role: 'assistant', kind: 'text', text: 'Hello! I am the Chat Operator. How can I help you evaluate your agent?' }
  ]);
  const [input, setInput] = useState('');
  
  const handleSend = () => {
    if (!input.trim()) return;
    setMessages(prev => [...prev, { role: 'user', kind: 'text', text: input }]);
    setInput('');
  };

  return (
    <PageContainer variant="full" className="flex-col">
      <PagePane variant="sidebar" title="Chat Operator" className="w-full h-full flex flex-col">
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((m, i) => (
            <MessageBubble key={i} {...m} />
          ))}
        </div>
        
        <div className="p-4 border-t border-outline-variant bg-surface-container">
          <div className="flex gap-3">
            <input 
              type="text"
              className="flex-1 bg-surface-container-highest border border-outline-variant rounded-md p-3 text-on-surface focus:outline-none focus:border-primary-fixed placeholder:text-on-surface-variant/50"
              placeholder="Ask the operator to run a scan, generate a campaign, etc..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
            />
            <Button 
              variant="cta"
              onClick={handleSend}
            >
              Send
            </Button>
          </div>
        </div>
      </PagePane>
    </PageContainer>
  );
}
