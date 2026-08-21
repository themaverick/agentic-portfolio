import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAgentStore } from '../store/agentStore';
import { getApiUrl } from '../config/api';
import { Bot, X, Send, Terminal, Brain, CheckCircle2, Loader2, Wrench } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

export const AgentDrawer: React.FC = () => {
  const {
    isOpen,
    toggleDrawer,
    setIsOpen,
    sessionId,
    messages,
    addMessage,
    appendThoughtToLastMessage,
    appendTokenToLastMessage,
    addOrUpdateToolCallInLastMessage,
    isStreaming,
    setIsStreaming,
    activeTool,
    setActiveTool,
    setUiHighlight,
  } = useAgentStore();

  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  // Global Keyboard Trigger (Cmd + K or Ctrl + K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        toggleDrawer();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toggleDrawer]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeTool]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const userMsg = input.trim();
    setInput('');
    addMessage({ role: 'user', content: userMsg });

    // Prepare assistant message target
    addMessage({ role: 'assistant', content: '', isStreaming: true });
    setIsStreaming(true);
    setActiveTool(null);

    try {
      const response = await fetch(getApiUrl('/api/v1/agent/chat'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, message: userMsg }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) return;

      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const block of lines) {
          if (!block.trim()) continue;

          let eventType = 'chunk';
          let dataStr = '';

          for (const line of block.split('\n')) {
            if (line.startsWith('event: ')) {
              eventType = line.replace('event: ', '').trim();
            } else if (line.startsWith('data: ')) {
              dataStr = line.replace('data: ', '').trim();
            }
          }

          if (!dataStr) continue;

          try {
            const data = JSON.parse(dataStr);

            if (eventType === 'thought') {
              if (data.token) {
                appendThoughtToLastMessage(data.token);
              }
            } else if (eventType === 'tool_call') {
              addOrUpdateToolCallInLastMessage(data);
              if (data.status === 'running') {
                setActiveTool(data.tool);
              } else if (data.status === 'completed') {
                setActiveTool(null);
              }
            } else if (eventType === 'tool_start') {
              setActiveTool(data.tool);
            } else if (eventType === 'ui_action') {
              if (data.action === 'navigate' && data.route) {
                navigate(data.route);
              }
              if (data.target) {
                setUiHighlight(data.target);
                setTimeout(() => {
                  const el = document.getElementById(data.target);
                  el?.scrollIntoView({ behavior: 'smooth' });
                }, 300);
              }
            } else if (eventType === 'chunk') {
              if (data.token) {
                appendTokenToLastMessage(data.token);
              }
            } else if (eventType === 'done') {
              setIsStreaming(false);
              setActiveTool(null);
            }
          } catch (err) {
            console.error('SSE JSON parse error:', err);
          }
        }
      }
    } catch (err) {
      console.error('Chat error:', err);
      appendTokenToLastMessage('Sorry, I encountered an error connecting to the backend proxy.');
    } finally {
      setIsStreaming(false);
      setActiveTool(null);
    }
  };

  const handlePromptClick = (prompt: string) => {
    if (!isOpen) setIsOpen(true);
    setInput(prompt);
  };

  return (
    <>
      {/* Floating Trigger Badge */}
      {!isOpen && (
        <button
          onClick={toggleDrawer}
          className="fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-3.5 rounded-full glass-panel-glow text-sky-400 hover:text-white hover:scale-105 transition-all duration-300 shadow-2xl group cursor-pointer"
          id="agent-trigger"
        >
          <div className="relative">
            <Bot className="w-5 h-5 group-hover:rotate-12 transition-transform" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full animate-ping" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full" />
          </div>
          <span className="font-semibold text-sm tracking-wide">Ask AI Proxy</span>
          <span className="hidden sm:inline-block px-2 py-0.5 text-[10px] font-mono font-bold bg-sky-950/80 border border-sky-500/30 text-sky-300 rounded">
            ⌘K
          </span>
        </button>
      )}

      {/* Drawer Overlay Panel */}
      {isOpen && (
        <div className="fixed bottom-4 right-4 z-50 w-full max-w-lg h-[640px] max-h-[90vh] glass-panel-glow rounded-2xl flex flex-col shadow-2xl border border-sky-500/30 overflow-hidden animate-in fade-in slide-in-from-bottom-8 duration-300">
          {/* Header */}
          <div className="px-5 py-4 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-sky-500/10 border border-sky-500/30 rounded-xl text-sky-400">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-slate-100 text-sm">Yogesh’s AI Proxy</h3>
                  <span className="px-2 py-0.5 text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full flex items-center gap-1">
                    <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
                    Gemini 2.5 Flash
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">Dynamic Tool Calling • Reasoning • pgvector</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 text-sm">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-7 h-7 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 shrink-0 mt-1">
                    <Bot className="w-4 h-4" />
                  </div>
                )}
                <div
                  className={`max-w-[85%] px-4 py-3 rounded-2xl ${
                    msg.role === 'user'
                      ? 'bg-sky-600 text-white rounded-br-none'
                      : 'bg-slate-900/90 border border-slate-800 text-slate-200 rounded-bl-none shadow-md'
                  }`}
                >
                  {msg.role === 'assistant' ? (
                    <div>
                      {/* Thought / Reasoning Block */}
                      {msg.thought && (
                        <div className="mb-3 p-3 rounded-xl bg-purple-950/40 border border-purple-500/30 text-purple-200 text-xs shadow-inner">
                          <div className="flex items-center gap-2 mb-1.5 font-semibold text-[11px] text-purple-300 tracking-wide uppercase">
                            <Brain className="w-3.5 h-3.5 text-purple-400 animate-pulse" />
                            <span>Thought Process</span>
                          </div>
                          <p className="text-[11px] leading-relaxed text-purple-200/90 font-mono whitespace-pre-wrap">
                            {msg.thought}
                          </p>
                        </div>
                      )}

                      {/* Tool Executions List */}
                      {msg.toolCalls && msg.toolCalls.length > 0 && (
                        <div className="mb-3 space-y-2">
                          {msg.toolCalls.map((tc) => (
                            <div
                              key={tc.id || tc.tool}
                              className="p-2.5 rounded-xl bg-slate-950/80 border border-cyan-500/30 text-slate-200 text-[11px] font-mono shadow-sm flex flex-col gap-1"
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2 text-cyan-400 font-bold">
                                  <Wrench className="w-3.5 h-3.5 text-cyan-400" />
                                  <span>{tc.tool}</span>
                                </div>
                                <span className="flex items-center gap-1 text-[10px]">
                                  {tc.status === 'completed' ? (
                                    <span className="text-emerald-400 flex items-center gap-1 font-sans font-medium">
                                      <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Executed
                                    </span>
                                  ) : (
                                    <span className="text-amber-400 flex items-center gap-1 font-sans font-medium">
                                      <Loader2 className="w-3 h-3 animate-spin text-amber-400" /> Running
                                    </span>
                                  )}
                                </span>
                              </div>
                              {tc.args && Object.keys(tc.args).length > 0 && (
                                <div className="text-[10px] text-slate-400 bg-slate-900/60 p-1.5 rounded border border-slate-800">
                                  {JSON.stringify(tc.args)}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Final Answer Text */}
                      {msg.content ? (
                        <div className="prose prose-invert text-xs leading-relaxed max-w-none">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                      ) : (
                        !msg.thought && (!msg.toolCalls || msg.toolCalls.length === 0) && (
                          <div className="text-slate-500 text-xs italic">Thinking...</div>
                        )
                      )}
                    </div>
                  ) : (
                    <p className="text-xs">{msg.content}</p>
                  )}
                </div>
              </div>
            ))}

            {/* Active Tool Execution Pill */}
            {activeTool && (
              <div className="flex items-center gap-2 px-3 py-2 bg-purple-500/10 border border-purple-500/30 text-purple-300 rounded-xl text-xs w-fit animate-pulse">
                <Terminal className="w-3.5 h-3.5 text-purple-400 animate-spin" />
                <span>Executing tool: <code className="font-mono text-[11px] font-bold">{activeTool}</code>...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Starter Chips */}
          <div className="px-4 py-2 bg-slate-950/40 border-t border-slate-800/60 overflow-x-auto flex gap-2 no-scrollbar">
            {[
              'What projects has Yogesh built?',
              'Why RRF over Linear Hybrid search?',
              'Summarize Yogesh’s experience',
            ].map((starter, i) => (
              <button
                key={i}
                onClick={() => handlePromptClick(starter)}
                className="px-3 py-1 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-[11px] rounded-full shrink-0 transition-colors cursor-pointer"
              >
                {starter}
              </button>
            ))}
          </div>

          {/* Input Form */}
          <form onSubmit={handleSubmit} className="p-3 border-t border-slate-800 bg-slate-950/80 flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about projects, Kafka, pgvector, or trade-offs..."
              className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-colors"
            />
            <button
              type="submit"
              disabled={isStreaming || !input.trim()}
              className="p-2.5 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white rounded-xl transition-all cursor-pointer shadow-lg"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      )}
    </>
  );
};
