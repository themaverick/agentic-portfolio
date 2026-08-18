# Frontend Technical Specification (React 18 + TypeScript + Tailwind)

## 1. Routes & Page Hierarchy
- `/` — **Hero & Pitch View:** Quick bio, live status pill, competency bento grid, recruiter prompt starters.
- `/projects` — **Projects Hub:** Interactive cards, modal deep-dives with system architecture diagrams.
- `/experience` — **Experience Matrix:** Chronological career timeline and quantifiable metrics.
- `/recruiter-lab` — **Recruiter Alignment Lab:** Split-view Job Description parser and interview simulator.
- `/telemetry` — **Live System Dashboard:** Real-time token usage, latency percentiles, and tool metrics.

## 2. Global Agent Drawer Component (`src/components/agent/AgentDrawer.tsx`)
- **Docked State:** Collapsible bottom-right drawer with keyboard trigger (`Cmd + K`).
- **SSE Stream Handler:** Listens to `POST /api/v1/agent/chat` using `EventSource` / `fetch` reader.
- **Event Handling:**
  - `event: handshake` -> Set loading state to active.
  - `event: tool_start` -> Render expanding tool pill (e.g., *Executing hybrid search...*).
  - `event: ui_action` -> Parse payload and execute `useNavigate()` or `element.scrollIntoView({ behavior: 'smooth' })`.
  - `event: chunk` -> Append streaming markdown tokens to active message bubble.
  - `event: done` -> Finalize stream state and persist in local session cache.

## 3. Global State (Zustand)
```typescript
interface AgentState {
  isOpen: boolean;
  sessionId: string;
  messages: Array<{ role: 'user' | 'assistant'; content: string; toolCalls?: string[] }>;
  activeUiHighlight: string | null;
  toggleDrawer: () => void;
  setUiHighlight: (elementId: string | null) => void;
}