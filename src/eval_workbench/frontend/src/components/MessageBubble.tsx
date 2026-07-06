interface MessageBubbleProps {
  role: "system" | "user" | "assistant" | "tool";
  kind: "text" | "tool_call" | "tool_response" | "media";
  text?: string;
  tool_name?: string;
  tool_args?: any;
  tool_response?: any;
}

export function MessageBubble({ role, kind, text, tool_name, tool_args, tool_response }: MessageBubbleProps) {
  if (kind === 'tool_call') {
    return (
      <div className="bg-surface-container-highest text-on-surface p-3 rounded-md font-mono text-sm my-2 border border-outline-variant">
        <div className="text-primary-fixed font-bold mb-1">🛠️ Call: {tool_name}</div>
        <pre className="whitespace-pre-wrap">{JSON.stringify(tool_args, null, 2)}</pre>
      </div>
    );
  }

  if (kind === 'tool_response') {
    return (
      <div className="bg-surface-container-low text-on-surface-variant p-3 rounded-md font-mono text-sm my-2 border border-outline-variant">
        <div className="text-on-surface font-bold mb-1">↩️ Return: {tool_name}</div>
        <pre className="whitespace-pre-wrap">{JSON.stringify(tool_response, null, 2)}</pre>
      </div>
    );
  }

  const isUser = role === 'user';
  
  return (
    <div className={`flex flex-col my-3 ${isUser ? 'items-end' : 'items-start'}`}>
      <span className="text-xs font-bold text-on-surface-variant mb-1 uppercase tracking-wider">{role}</span>
      <div className={`px-4 py-2.5 rounded-2xl max-w-[85%] ${isUser ? 'bg-primary-fixed text-white rounded-tr-sm' : 'bg-surface-container text-on-surface border border-outline-variant shadow-sm rounded-tl-sm'}`}>
        <div className="whitespace-pre-wrap">{text}</div>
      </div>
    </div>
  );
}
