import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../lib/api'

const EXAMPLE_COMPANIES = [
  { company: 'Stripe', icp: 'B2B payment processors scaling engineering teams and developer infrastructure' },
  { company: 'HubSpot', icp: 'B2B SaaS platforms scaling GTM systems and engineering teams for enterprise growth' },
  { company: 'Vercel', icp: 'Developer tooling companies hiring platform and infrastructure engineers' },
]

const FEATURES = [
  {
    icon: '📡',
    title: 'Real Signal Ingestion',
    desc: 'Fetches live funding, hiring, and expansion data from Serper — zero hallucination.',
  },
  {
    icon: '🧠',
    title: 'LLM-Powered Reasoning',
    desc: 'Groq Llama 3.3 analyzes signals against your ICP. Ollama fallback for local runs.',
  },
  {
    icon: '📊',
    title: 'Deterministic Scoring',
    desc: 'Math-based opportunity score 0–1. No guessing. Score < 0.5 = skip automatically.',
  },
  {
    icon: '✉️',
    title: 'Personalized Emails',
    desc: 'Unique email per contact. Max 120 words. Cites real signals. No generic templates.',
  },
]

export default function Home() {
  const [company, setCompany] = useState('')
  const [icp, setIcp] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [autoSend, setAutoSend] = useState(false)
  const navigate = useNavigate()
  const formRef = useRef(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!company.trim() || !icp.trim()) return
    setLoading(true)
    setError('')

    try {
      const res = await apiFetch('/run-agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company: company.trim(),
          icp: icp.trim(),
          send_email: autoSend,
        }),
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Agent run failed')
      }
      const result = await res.json()
      navigate('/results', { state: { result } })
    } catch (err) {
      setError(err.message || 'Something went wrong. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const fillExample = (ex) => {
    setCompany(ex.company)
    setIcp(ex.icp)
    formRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <section className="flex-1 flex flex-col items-center justify-center px-6 py-24">
        {/* Badge */}
        <div className="animate-fade-in mb-8">
          <div className="inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-xs font-semibold"
            style={{ background: 'rgba(255,90,0,0.12)', border: '1px solid rgba(255,90,0,0.25)', color: '#FF9A00' }}>
            <span className="glow-dot w-1.5 h-1.5" />
            Agentic Outreach · LangGraph + Groq + Serper
          </div>
        </div>

        {/* Headline */}
        <div className="animate-fade-in delay-100 text-center max-w-3xl mb-6">
          <h1 className="text-5xl sm:text-6xl font-black tracking-tight text-white leading-tight mb-4">
            <span>Signal-driven</span>
            <br />
            <span className="text-fire">outreach that</span>
            <br />
            <span>actually converts</span>
          </h1>
          <p className="text-lg text-slate-400 max-w-xl mx-auto leading-relaxed">
            FireReach fetches real company signals, scores the opportunity, and writes
            a hyper-personalized email — in under 10 seconds.
          </p>
        </div>

        {/* Input Form */}
        <div ref={formRef}
          className="animate-fade-in delay-200 glass-card w-full max-w-2xl p-8 mt-4">
          <form id="analyze-form" onSubmit={handleSubmit} className="space-y-5">
            {/* Company input */}
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2">
                Company Name
              </label>
              <input
                id="company-input"
                type="text"
                className="input-field text-base"
                placeholder="e.g. Stripe, Notion, Vercel"
                value={company}
                onChange={e => setCompany(e.target.value)}
                required
                autoFocus
              />
            </div>

            {/* ICP textarea */}
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2">
                Ideal Customer Profile (ICP)
              </label>
              <textarea
                id="icp-input"
                className="input-field text-base resize-none"
                rows={4}
                placeholder="Describe your ideal customer — industry, size, growth stage, pain points..."
                value={icp}
                onChange={e => setIcp(e.target.value)}
                required
              />
              <p className="mt-1.5 text-xs text-slate-600">
                More detail = better signal alignment and email quality
              </p>
            </div>

            {/* Error */}
            {error && (
              <div className="flex items-start gap-3 rounded-xl p-4 text-sm text-red-400"
                style={{ background: 'rgba(248,113,113,0.08)', border: '1px solid rgba(248,113,113,0.2)' }}>
                <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {error}
              </div>
            )}

            {/* Submit */}
            <button
              id="run-analysis-btn"
              type="submit"
              disabled={loading || !company.trim() || !icp.trim()}
              className="btn-fire w-full py-4 text-base"
            >
              {loading ? (
                <>
                  <span className="relative z-10 flex items-center gap-3">
                    <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Running Agent (fetching signals → scoring → generating email)
                  </span>
                </>
              ) : (
                <span className="relative z-10 flex items-center gap-2">
                  <span>🔥</span>
                  Run Analysis
                </span>
              )}
            </button>
            {/* Auto-send toggle */}
            <div className="flex items-center justify-between pt-2">
              <label className="flex items-center gap-2 text-xs text-slate-400">
                <input
                  type="checkbox"
                  className="form-checkbox h-3.5 w-3.5 text-orange-500 rounded border-slate-600 bg-slate-900/40"
                  checked={autoSend}
                  onChange={e => setAutoSend(e.target.checked)}
                />
                <span>
                  Auto-send email when score ≥ threshold
                </span>
              </label>
            </div>
          </form>
        </div>

        {/* Quick examples */}
        <div className="animate-fade-in delay-300 mt-6 flex flex-wrap items-center justify-center gap-3">
          <span className="text-xs text-slate-600">Try:</span>
          {EXAMPLE_COMPANIES.map(ex => (
            <button key={ex.company}
              onClick={() => fillExample(ex)}
              className="text-xs font-medium px-3 py-1.5 rounded-full transition-all duration-200"
              style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)', color: '#64748B' }}
              onMouseEnter={e => { e.target.style.color = '#94A3B8'; e.target.style.borderColor = 'rgba(255,90,0,0.2)' }}
              onMouseLeave={e => { e.target.style.color = '#64748B'; e.target.style.borderColor = 'rgba(255,255,255,0.07)' }}
            >
              {ex.company}
            </button>
          ))}
        </div>
      </section>

      {/* ── Feature grid ──────────────────────────────────────────────────── */}
      <section className="px-6 pb-24 max-w-6xl mx-auto w-full">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {FEATURES.map((f, i) => (
            <div key={f.title}
              className={`glass-card p-6 animate-fade-in-up`}
              style={{ animationDelay: `${i * 80}ms` }}>
              <div className="text-3xl mb-3">{f.icon}</div>
              <h3 className="text-sm font-semibold text-white mb-1.5">{f.title}</h3>
              <p className="text-xs text-slate-500 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
