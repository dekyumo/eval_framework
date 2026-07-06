import { useState } from 'react';
import { MessageBubble } from './MessageBubble';

interface TraceViewProps {
  trace: {
    id: string;
    parts: any[];
    exception?: string;
    latency_ms?: number;
    tokens?: { prompt: number, completion: number, total: number };
  };
}

export function TraceView({ trace }: TraceViewProps) {
  return (
    <div className="flex flex-col h-full bg-background">
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {trace.parts.map((p, idx) => (
          <MessageBubble key={idx} {...p} />
        ))}
        
        {trace.exception && (
          <div className="mt-4 p-4 bg-red-900 text-red-100 rounded-md font-mono text-xs overflow-x-auto">
            <h4 className="font-bold text-red-300 mb-2 uppercase tracking-widest">Exception Traceback</h4>
            <pre>{trace.exception}</pre>
          </div>
        )}
      </div>
      
      <div className="bg-surface-container border-t border-outline-variant p-3 flex justify-between items-center text-xs text-on-surface-variant font-medium">
        <div>
          {trace.tokens && (
            <span>Tokens: {trace.tokens.prompt} prompt + {trace.tokens.completion} completion = {trace.tokens.total} total</span>
          )}
        </div>
        <div>
          {trace.latency_ms && <span>Latency: {trace.latency_ms}ms</span>}
        </div>
      </div>
    </div>
  );
}
