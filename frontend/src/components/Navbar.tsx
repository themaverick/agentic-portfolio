import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAgentStore } from '../store/agentStore';
import { Bot, Terminal, Briefcase, FolderGit2, Cpu, Sparkles, Activity } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { toggleDrawer } = useAgentStore();

  const navItems = [
    { label: 'Overview', path: '/', icon: Cpu },
    { label: 'Projects', path: '/projects', icon: FolderGit2 },
    { label: 'Experience', path: '/experience', icon: Briefcase },
    { label: 'Recruiter Lab', path: '/recruiter-lab', icon: Sparkles },
    { label: 'Telemetry', path: '/telemetry', icon: Activity },
  ];

  return (
    <nav className="sticky top-0 z-40 w-full glass-panel border-b border-slate-800/80 bg-slate-950/70">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo */}
        <NavLink to="/" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 p-0.5 shadow-lg group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center text-sky-400">
              <Terminal className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-100 tracking-tight text-base">Yogesh Sharma</span>
              <span className="px-2 py-0.5 text-[10px] font-mono font-bold bg-sky-500/10 text-sky-400 border border-sky-500/20 rounded-full">
                IIT Jodhpur '26
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono">Applied AI & Systems</p>
          </div>
        </NavLink>

        {/* Desktop Links */}
        <div className="hidden md:flex items-center gap-1 bg-slate-900/80 p-1.5 rounded-full border border-slate-800">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-sky-500 text-white shadow-md'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`
                }
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </div>

        {/* Action Button */}
        <button
          onClick={toggleDrawer}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-sky-500/10 border border-sky-500/30 text-sky-400 hover:bg-sky-500/20 hover:text-white transition-all text-xs font-semibold cursor-pointer"
        >
          <Bot className="w-4 h-4" />
          <span className="hidden sm:inline">Ask AI Proxy</span>
        </button>
      </div>
    </nav>
  );
};
