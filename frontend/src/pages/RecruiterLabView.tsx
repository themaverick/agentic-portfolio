import React, { useState } from 'react';
import { getApiUrl } from '../config/api';
import { Sparkles, CheckCircle2, AlertTriangle, FileText, Mail } from 'lucide-react';

interface AnalysisResult {
  analysis_id: string;
  company_name: string;
  target_role: string;
  fit_score: number;
  extracted_tech_stack: string[];
  matched_skills: Array<{
    requirement: string;
    matched_experience: string;
    confidence_score: number;
    evidence_source: string;
  }>;
  missing_gaps: string[];
  generated_pitch: string;
}

export const RecruiterLabView: React.FC = () => {
  const [jdText, setJdText] = useState('');
  const [company, setCompany] = useState('');
  const [role, setRole] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  // Recruiter Lead Form state
  const [recruiterName, setRecruiterName] = useState('');
  const [recruiterCompany, setRecruiterCompany] = useState('');
  const [recruiterEmail, setRecruiterEmail] = useState('');
  const [salaryBand, setSalaryBand] = useState('');
  const [leadMessage, setLeadMessage] = useState('');
  const [submittingLead, setSubmittingLead] = useState(false);
  const [leadSubmitted, setLeadSubmitted] = useState(false);

  const handleAnalyzeJD = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!jdText.trim() || analyzing) return;

    setAnalyzing(true);
    try {
      const res = await fetch(getApiUrl('/api/v1/recruiter/analyze-jd'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raw_jd_text: jdText,
          company_name: company || 'Hiring Team',
          target_role: role || 'AI / Systems Engineer',
        }),
      });

      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error('JD analysis error:', err);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleLeadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!recruiterEmail || submittingLead) return;

    setSubmittingLead(true);
    try {
      const res = await fetch(getApiUrl('/api/v1/recruiter/lead'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recruiter_name: recruiterName,
          company: recruiterCompany,
          email: recruiterEmail,
          salary_band: salaryBand,
          message: leadMessage,
        }),
      });

      if (res.ok) {
        setLeadSubmitted(true);
      }
    } catch (err) {
      console.error('Lead capture error:', err);
    } finally {
      setSubmittingLead(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
      {/* Header */}
      <div className="space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-xs font-mono">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Recruiter Alignment Lab</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-extrabold text-slate-100 tracking-tight">
          Job Description <span className="text-gradient">Fit Analyzer</span>
        </h1>
        <p className="text-slate-400 text-sm max-w-2xl">
          Paste your target Job Description below to run instant skill overlap extraction, calculate 0–100 match score, and generate a customized engineering pitch.
        </p>
      </div>

      {/* Split View Container */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Input Form */}
        <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-slate-800 space-y-6">
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <FileText className="w-5 h-5 text-sky-400" />
            <span>Paste Job Description</span>
          </h2>

          <form onSubmit={handleAnalyzeJD} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1.5">Company Name</label>
                <input
                  type="text"
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  placeholder="e.g. Acme AI Corp"
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1.5">Target Role</label>
                <input
                  type="text"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  placeholder="e.g. Senior Systems Engineer"
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1.5">Raw Job Description Text</label>
              <textarea
                rows={8}
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                placeholder="We are looking for an Applied AI Engineer with experience in Python, FastAPI, PostgreSQL pgvector, Apache Kafka, Redis..."
                className="w-full bg-slate-900 border border-slate-800 rounded-xl p-4 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 font-mono"
              />
            </div>

            <button
              type="submit"
              disabled={analyzing || !jdText.trim()}
              className="w-full py-3.5 bg-sky-500 hover:bg-sky-400 disabled:opacity-50 text-white font-semibold rounded-xl text-xs transition-all shadow-lg flex items-center justify-center gap-2 cursor-pointer"
            >
              <Sparkles className="w-4 h-4" />
              <span>{analyzing ? 'Analyzing Alignment...' : 'Run Fit Analysis'}</span>
            </button>
          </form>
        </div>

        {/* Right: Results Output */}
        <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-slate-800 space-y-6">
          {!result ? (
            <div className="h-full min-h-[350px] flex flex-col items-center justify-center text-center p-8 border-2 border-dashed border-slate-800 rounded-2xl text-slate-500 space-y-3">
              <Sparkles className="w-10 h-10 text-slate-600 animate-pulse" />
              <p className="text-xs">Analysis results, skill overlap score, and tailored pitch will render here once submitted.</p>
            </div>
          ) : (
            <div className="space-y-6 animate-in fade-in duration-500">
              {/* Match Score Card */}
              <div className="flex items-center justify-between bg-slate-900 p-5 rounded-2xl border border-slate-800">
                <div>
                  <span className="text-xs font-mono text-slate-400">Match Alignment Score</span>
                  <h3 className="text-3xl font-extrabold text-slate-100 mt-0.5">{result.fit_score}%</h3>
                </div>
                <div className="w-16 h-16 rounded-full bg-sky-500/10 border-4 border-sky-500 flex items-center justify-center font-bold text-sky-400 text-lg">
                  {result.fit_score}%
                </div>
              </div>

              {/* Extracted Tech Stack */}
              <div>
                <h4 className="text-xs font-mono uppercase text-slate-400 font-bold mb-2">Matched Canonical Tech</h4>
                <div className="flex flex-wrap gap-2">
                  {result.extracted_tech_stack.map((tech, i) => (
                    <span key={i} className="px-3 py-1 bg-sky-500/10 border border-sky-500/30 text-sky-300 text-xs rounded-full font-mono">
                      {tech}
                    </span>
                  ))}
                </div>
              </div>

              {/* Tailored Pitch */}
              <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-2">
                <h4 className="text-xs font-mono uppercase text-sky-400 font-bold">Tailored Engineering Pitch</h4>
                <p className="text-xs text-slate-200 leading-relaxed italic">"{result.generated_pitch}"</p>
              </div>

              {/* Identified Skill Gaps */}
              {result.missing_gaps.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-mono uppercase text-amber-400 font-bold">Identified Architecture Gaps</h4>
                  <ul className="space-y-1.5">
                    {result.missing_gaps.map((gap, i) => (
                      <li key={i} className="flex items-center gap-2 text-xs text-amber-300 bg-amber-500/5 border border-amber-500/20 px-3 py-2 rounded-xl">
                        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                        <span>{gap}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Recruiter Lead Capture Form */}
      <section className="glass-panel rounded-3xl p-8 border border-slate-800 space-y-6">
        <div className="space-y-2">
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Mail className="w-5 h-5 text-sky-400" />
            <span>Connect & Schedule Interview</span>
          </h2>
          <p className="text-xs text-slate-400">Capturing lead details triggers instant event dispatch to Yogesh’s Kafka broker and Discord webhook alerts.</p>
        </div>

        {leadSubmitted ? (
          <div className="p-6 bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 rounded-2xl flex items-center gap-3 text-xs">
            <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0" />
            <div>
              <h4 className="font-bold text-sm">Lead Captured Successfully!</h4>
              <p>Your message and details have been logged and produced to the Kafka event broker. Yogesh will get back to you shortly.</p>
            </div>
          </div>
        ) : (
          <form onSubmit={handleLeadSubmit} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <input
              type="text"
              required
              value={recruiterName}
              onChange={(e) => setRecruiterName(e.target.value)}
              placeholder="Your Name *"
              className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
            />
            <input
              type="text"
              required
              value={recruiterCompany}
              onChange={(e) => setRecruiterCompany(e.target.value)}
              placeholder="Company Name *"
              className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
            />
            <input
              type="email"
              required
              value={recruiterEmail}
              onChange={(e) => setRecruiterEmail(e.target.value)}
              placeholder="Work Email *"
              className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
            />
            <input
              type="text"
              value={salaryBand}
              onChange={(e) => setSalaryBand(e.target.value)}
              placeholder="Salary Band / Range (Optional)"
              className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
            />
            <textarea
              rows={3}
              value={leadMessage}
              onChange={(e) => setLeadMessage(e.target.value)}
              placeholder="Custom note or interview invitation..."
              className="sm:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-4 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
            />
            <button
              type="submit"
              disabled={submittingLead}
              className="sm:col-span-2 py-3 bg-sky-500 hover:bg-sky-400 disabled:opacity-50 text-white font-semibold rounded-xl text-xs transition-all shadow-lg cursor-pointer"
            >
              {submittingLead ? 'Submitting to Kafka...' : 'Submit Recruiter Lead'}
            </button>
          </form>
        )}
      </section>
    </div>
  );
};
