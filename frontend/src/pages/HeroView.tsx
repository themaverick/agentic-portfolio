import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAgentStore } from '../store/agentStore';
import { Bot, Terminal, Database, Server, Zap, ArrowRight, CheckCircle2 } from 'lucide-react';

export const HeroView: React.FC = () => {
  const { setIsOpen } = useAgentStore();

  const handlePromptStarter = (promptText: string) => {
    setIsOpen(true);
    console.log("Triggered prompt:", promptText);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16">
      {/* Hero Header */}
      <section className="relative glass-panel rounded-3xl p-8 sm:p-12 overflow-hidden border border-slate-800">
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 space-y-6 max-w-3xl">
          {/* Live Status Pill */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Open to AI / Data Science / ML Engineering Roles ('26 Grad)</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold text-slate-100 tracking-tight leading-tight">
            Applied AI, Machine Learning & <br />
            <span className="text-gradient">Data Engineering Systems</span>
          </h1>

          <p className="text-slate-300 text-base sm:text-lg leading-relaxed">
            I'm <strong className="text-white">Yogesh Sharma</strong>, a 2026 undergraduate at <strong className="text-sky-400">IIT Jodhpur</strong> pursuing a B.Tech with a Minor in Artificial Intelligence & Data Engineering. Experienced across <strong className="text-white">Thuriyam AI</strong>, <strong className="text-white">AI Stealth Startup</strong>, and <strong className="text-white">IISc Bangalore NLP Lab</strong> building low-latency LLM pipelines, fine-tuned BERT guardrails, vector retrieval (RAG), and big data predictive models.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-2">
            <button
              onClick={() => setIsOpen(true)}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-sky-500 hover:bg-sky-400 text-white font-semibold text-sm transition-all shadow-lg hover:shadow-sky-500/25 cursor-pointer"
            >
              <Bot className="w-4 h-4" />
              <span>Talk to AI Proxy</span>
            </button>
            <NavLink
              to="/recruiter-lab"
              className="flex items-center gap-2 px-6 py-3 rounded-xl glass-panel hover:bg-slate-800 text-slate-200 font-semibold text-sm transition-all border border-slate-700 cursor-pointer"
            >
              <span>Recruiter Alignment Lab</span>
              <ArrowRight className="w-4 h-4 text-sky-400" />
            </NavLink>
          </div>
        </div>
      </section>

      {/* Competency Bento Grid */}
      <section className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-slate-100">Core Systems Competencies</h2>
          <span className="text-xs font-mono text-slate-400">Polyglot Persistence • SSE • Event Streaming</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: Dense Retrieval & RAG */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 hover:border-sky-500/40 transition-all space-y-4">
            <div className="p-3 bg-sky-500/10 border border-sky-500/30 text-sky-400 rounded-xl w-fit">
              <Database className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-100">Hybrid Search & Retrieval</h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              PostgreSQL <code className="text-sky-300 font-mono">pgvector</code> HNSW indexing combined with TSVector full-text search using SQL-level <strong>Reciprocal Rank Fusion (RRF)</strong> for rank consolidation.
            </p>
            <ul className="space-y-2 pt-2 text-xs text-slate-400">
              <li className="flex items-center gap-2"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> HNSW vector cosine search (m=16, ef=64)</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> SQL-level RRF stored procedures</li>
            </ul>
          </div>

          {/* Card 2: Distributed Event Streaming */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 hover:border-purple-500/40 transition-all space-y-4">
            <div className="p-3 bg-purple-500/10 border border-purple-500/30 text-purple-400 rounded-xl w-fit">
              <Server className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-100">Event Streaming & Messaging</h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Decoupled async pipelines built with <strong>Apache Kafka</strong> for micro-batch telemetry ingestion and persistent alert notification dispatching.
            </p>
            <ul className="space-y-2 pt-2 text-xs text-slate-400">
              <li className="flex items-center gap-2"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> AIOKafka event producers & consumer workers</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Real-time Discord webhook alert delivery</li>
            </ul>
          </div>

          {/* Card 3: Fast Edge & Rate Limiting */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 hover:border-emerald-500/40 transition-all space-y-4">
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-xl w-fit">
              <Zap className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-100">Edge Defense & Caching</h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Atomic <strong>Redis Lua sliding-window rate limiting</strong> ensuring 10 requests per 10-minute quota enforcement with HTTP 429 response handling.
            </p>
            <ul className="space-y-2 pt-2 text-xs text-slate-400">
              <li className="flex items-center gap-2"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Atomic Lua script evaluation</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Low-latency session state store</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Recruiter Prompt Starters */}
      <section className="glass-panel rounded-2xl p-8 border border-slate-800 space-y-4">
        <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
          <Terminal className="w-5 h-5 text-sky-400" />
          <span>Interactive Agent Prompt Starters</span>
        </h3>
        <p className="text-xs text-slate-400">Click any prompt to trigger the AI proxy with factual grounding:</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[
            'Explain how the Hybrid Search RRF function works in PostgreSQL',
            'What is Yogesh’s research contribution in Attentive Aggregation?',
            'What tech stack was used for the Lead Capture Kafka pipeline?',
            'Why use Redis sliding-window over standard token bucket rate limiting?',
          ].map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handlePromptStarter(prompt)}
              className="text-left p-3.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-800 hover:border-sky-500/40 text-xs text-slate-300 hover:text-white transition-all cursor-pointer flex items-center justify-between group"
            >
              <span>{prompt}</span>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-sky-400 group-hover:translate-x-1 transition-all" />
            </button>
          ))}
        </div>
      </section>
    </div>
  );
};
