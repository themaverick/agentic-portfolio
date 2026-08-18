import React, { useEffect, useState } from 'react';
import { useAgentStore } from '../store/agentStore';
import { getApiUrl } from '../config/api';
import { FolderGit2, ExternalLink, Code2, CheckCircle2 } from 'lucide-react';

interface Project {
  id: string;
  slug: string;
  title: string;
  tagline: string;
  problem_statement: string;
  solution_overview: string;
  architecture_metadata: Record<string, string>;
  impact_metrics: string[];
  github_url: string | null;
  live_demo_url: string | null;
  is_featured: boolean;
}

export const ProjectsView: React.FC = () => {
  const { activeUiHighlight } = useAgentStore();
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    fetch(getApiUrl('/api/v1/portfolio/projects'))
      .then((res) => res.json())
      .then((data) => {
        setProjects(data);
      })
      .catch((err) => {
        console.error('Error fetching projects:', err);
      });
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12" id="projects-grid">
      {/* Header */}
      <div className="space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs font-mono">
          <FolderGit2 className="w-3.5 h-3.5" />
          <span>Engineering Showcase</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-extrabold text-slate-100 tracking-tight">
          System Architecture & <span className="text-gradient">Projects</span>
        </h1>
        <p className="text-slate-400 text-sm max-w-2xl">
          Deep dives into full-stack systems engineering, vector retrieval pipelines, research contributions, and distributed event architectures.
        </p>
      </div>

      {/* Projects List */}
      <div className="grid grid-cols-1 gap-8">
        {projects.map((project) => {
          const isHighlighted = activeUiHighlight === project.slug || activeUiHighlight === 'projects-grid';
          return (
            <div
              key={project.id}
              id={project.slug}
              className={`glass-panel rounded-3xl p-8 border transition-all duration-500 space-y-6 ${
                isHighlighted ? 'border-sky-400 glow-cyan ring-1 ring-sky-500/50' : 'border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-2xl font-bold text-slate-100">{project.title}</h2>
                    {project.is_featured && (
                      <span className="px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-purple-500/20 text-purple-300 border border-purple-500/30 rounded-full">
                        Featured
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-sky-400 font-medium mt-1">{project.tagline}</p>
                </div>

                <div className="flex items-center gap-3">
                  {project.github_url && (
                    <a
                      href={project.github_url}
                      target="_blank"
                      rel="noreferrer"
                      className="p-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white rounded-xl transition-all cursor-pointer flex items-center gap-2 text-xs font-semibold"
                    >
                      <Code2 className="w-4 h-4" />
                      <span>Code Repo</span>
                    </a>
                  )}
                  {project.live_demo_url && (
                    <a
                      href={project.live_demo_url}
                      target="_blank"
                      rel="noreferrer"
                      className="p-2.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xl transition-all cursor-pointer flex items-center gap-2 text-xs font-semibold shadow-lg"
                    >
                      <ExternalLink className="w-4 h-4" />
                      <span>Live System</span>
                    </a>
                  )}
                </div>
              </div>

              {/* Grid Content */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Problem & Solution */}
                <div className="space-y-4">
                  <div>
                    <h4 className="text-xs font-mono uppercase text-slate-400 font-bold tracking-wider mb-1">Problem Statement</h4>
                    <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-4 rounded-xl border border-slate-800">
                      {project.problem_statement}
                    </p>
                  </div>
                  <div>
                    <h4 className="text-xs font-mono uppercase text-slate-400 font-bold tracking-wider mb-1">Architecture Solution</h4>
                    <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-4 rounded-xl border border-slate-800">
                      {project.solution_overview}
                    </p>
                  </div>
                </div>

                {/* Technical Specifications & Metrics */}
                <div className="space-y-4">
                  <div>
                    <h4 className="text-xs font-mono uppercase text-slate-400 font-bold tracking-wider mb-2">Technical Specification</h4>
                    <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-2">
                      {Object.entries(project.architecture_metadata || {}).map(([key, val]) => (
                        <div key={key} className="flex justify-between items-center text-xs border-b border-slate-900 pb-1.5 last:border-0 last:pb-0">
                          <span className="font-mono text-slate-400 capitalize">{key.replace('_', ' ')}:</span>
                          <span className="font-mono text-sky-300 font-semibold">{val}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="text-xs font-mono uppercase text-slate-400 font-bold tracking-wider mb-2">Impact Metrics</h4>
                    <ul className="space-y-2">
                      {project.impact_metrics?.map((metric, idx) => (
                        <li key={idx} className="flex items-center gap-2 text-xs text-slate-300 bg-emerald-500/5 border border-emerald-500/20 px-3 py-2 rounded-xl">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                          <span>{metric}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
