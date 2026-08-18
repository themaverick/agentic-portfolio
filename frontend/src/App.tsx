import React from 'react';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { AgentDrawer } from './components/AgentDrawer';
import { HeroView } from './pages/HeroView';
import { ProjectsView } from './pages/ProjectsView';
import { ExperienceView } from './pages/ExperienceView';
import { RecruiterLabView } from './pages/RecruiterLabView';
import { TelemetryView } from './pages/TelemetryView';

export const App: React.FC = () => {
  return (
    <Router>
      <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-sans selection:bg-sky-500 selection:text-slate-950">
        <Navbar />

        <main className="flex-1">
          <Routes>
            <Route path="/" element={<HeroView />} />
            <Route path="/projects" element={<ProjectsView />} />
            <Route path="/experience" element={<ExperienceView />} />
            <Route path="/recruiter-lab" element={<RecruiterLabView />} />
            <Route path="/telemetry" element={<TelemetryView />} />
          </Routes>
        </main>

        <footer className="glass-panel border-t border-slate-800/80 py-8 mt-16 text-center text-xs text-slate-500 space-y-2">
          <p>© 2026 Yogesh Sharma • IIT Jodhpur • Autonomous Portfolio Agent Platform</p>
          <p className="font-mono text-[11px] text-slate-600">Built with FastAPI • PostgreSQL pgvector • Apache Kafka • Redis • Vite React TS • Gemini 3.1 Flash</p>
        </footer>

        <AgentDrawer />
      </div>
    </Router>
  );
};

export default App;
