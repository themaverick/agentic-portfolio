import { create } from 'zustand';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: string[];
  isStreaming?: boolean;
}

interface AgentStore {
  isOpen: boolean;
  sessionId: string;
  messages: ChatMessage[];
  activeUiHighlight: string | null;
  isStreaming: boolean;
  activeTool: string | null;
  toggleDrawer: () => void;
  setIsOpen: (open: boolean) => void;
  setUiHighlight: (elementId: string | null) => void;
  addMessage: (msg: Omit<ChatMessage, 'id'>) => void;
  appendTokenToLastMessage: (token: string) => void;
  setActiveTool: (tool: string | null) => void;
  setIsStreaming: (streaming: boolean) => void;
}

export const useAgentStore = create<AgentStore>((set) => ({
  isOpen: false,
  sessionId: `session_${Math.random().toString(36).substring(2, 9)}`,
  messages: [
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I am Yogesh Sharma’s AI Technical Proxy. Ask me anything about his projects, architecture decisions (like Kafka vs Celery or pgvector hybrid search), skills, or experience at IIT Jodhpur!',
    },
  ],
  activeUiHighlight: null,
  isStreaming: false,
  activeTool: null,

  toggleDrawer: () => set((state) => ({ isOpen: !state.isOpen })),
  setIsOpen: (open: boolean) => set({ isOpen: open }),
  setUiHighlight: (elementId: string | null) => set({ activeUiHighlight: elementId }),

  addMessage: (msg) =>
    set((state) => ({
      messages: [
        ...state.messages,
        { ...msg, id: `msg_${Date.now()}_${Math.random().toString(36).substring(2, 5)}` },
      ],
    })),

  appendTokenToLastMessage: (token) =>
    set((state) => {
      const newMessages = [...state.messages];
      if (newMessages.length > 0 && newMessages[newMessages.length - 1].role === 'assistant') {
        const lastMsg = { ...newMessages[newMessages.length - 1] };
        lastMsg.content += token;
        newMessages[newMessages.length - 1] = lastMsg;
      }
      return { messages: newMessages };
    }),

  setActiveTool: (tool) => set({ activeTool: tool }),
  setIsStreaming: (streaming) => set({ isStreaming: streaming }),
}));
