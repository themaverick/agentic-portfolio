import React, { useEffect, useState } from 'react';
import { getApiUrl } from '../config/api';
import { Briefcase, Calendar, MapPin, CheckCircle2 } from 'lucide-react';

interface Experience {
  id: string;
  company: string;
  role: string;
  location: string;
  employment_type: string;
  start_date: string;
  end_date: string | null;
  summary: string;
  achievements: string[];
}

interface Skill {
  id: string;
  name: string;
  category: string;
  proficiency_level: string;
}

export const ExperienceView: React.FC = () => {
  const [experiences, setExperiences] = useState<Experience[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);

  useEffect(() => {
    Promise.all([
      fetch(getApiUrl('/api/v1/portfolio/experiences')).then((r) => r.json()),
      fetch(getApiUrl('/api/v1/portfolio/skills')).then((r) => r.json()),
    ])
      .then(([expData, skillData]) => {
        setExperiences(expData);
        setSkills(skillData);
      })
      .catch((err) => {
        console.error('Error fetching experience/skills:', err);
      });
  }, []);

  const categorizedSkills = skills.reduce((acc, skill) => {
    acc[skill.category] = acc[skill.category] || [];
    acc[skill.category].push(skill);
    return acc;
  }, {} as Record<string, Skill[]>);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16" id="experience-timeline">
      {/* Header */}
      <div className="space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono">
          <Briefcase className="w-3.5 h-3.5" />
          <span>Career History & Skills</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-extrabold text-slate-100 tracking-tight">
          Experience <span className="text-gradient-emerald">& Skill Taxonomy</span>
        </h1>
        <p className="text-slate-400 text-sm max-w-2xl">
          Academic research, applied AI systems engineering, and technical proficiencies.
        </p>
      </div>

      {/* Experience Timeline */}
      <div className="space-y-8">
        <h2 className="text-xl font-bold text-slate-100">Professional Experience & Research</h2>
        <div className="relative border-l border-slate-800 ml-4 pl-8 space-y-8">
          {experiences.map((exp) => (
            <div key={exp.id} className="relative group">
              {/* Timeline Dot */}
              <div className="absolute -left-[41px] top-1.5 w-4 h-4 rounded-full bg-sky-500 border-4 border-slate-950 shadow-md group-hover:scale-125 transition-transform" />

              <div className="glass-panel rounded-2xl p-6 border border-slate-800 hover:border-sky-500/30 transition-all space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-4">
                  <div>
                    <h3 className="text-lg font-bold text-slate-100">{exp.role}</h3>
                    <p className="text-xs text-sky-400 font-medium">{exp.company}</p>
                  </div>

                  <div className="flex items-center gap-4 text-xs text-slate-400 font-mono">
                    <span className="flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-slate-500" />
                      {exp.start_date} — {exp.end_date || 'Present'}
                    </span>
                    <span className="flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-slate-500" />
                      {exp.location}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed">{exp.summary}</p>

                <div className="space-y-2">
                  <h4 className="text-[11px] font-mono uppercase text-slate-400 font-bold tracking-wider">Quantifiable Achievements</h4>
                  <ul className="space-y-2">
                    {exp.achievements?.map((ach, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-xs text-slate-300">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                        <span>{ach}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Skills Matrix Taxonomy */}
      <div className="space-y-6">
        <h2 className="text-xl font-bold text-slate-100">Technical Skills Taxonomy</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {Object.entries(categorizedSkills).map(([category, items]) => (
            <div key={category} className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-sky-400 font-mono uppercase tracking-wider border-b border-slate-800 pb-2">
                {category}
              </h3>
              <div className="flex flex-wrap gap-2">
                {items.map((skill) => (
                  <span
                    key={skill.id}
                    className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 text-xs font-medium hover:border-sky-500/40 transition-colors"
                  >
                    {skill.name}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
