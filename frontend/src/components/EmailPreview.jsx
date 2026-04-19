import { useState } from 'react'
import { apiFetch } from '../lib/api'

function WordCountBadge({ count }) {
  const ok = count <= 120
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium rounded-full px-2.5 py-1 ${
      ok ? 'text-emerald-400' : 'text-red-400'
    }`}
      style={{
        background: ok ? 'rgba(52,211,153,0.1)' : 'rgba(248,113,113,0.1)',
        border: `1px solid ${ok ? 'rgba(52,211,153,0.2)' : 'rgba(248,113,113,0.2)'}`,
      }}>
      {ok ? '✓' : '⚠'} {count} words {ok ? '' : '(over limit!)'}
    </span>
  )
}

export default function EmailPreview({
  company,
  subject,
  body,
  wordCount,
  defaultRecipient = '',
  contactCandidates = [],
}) {
  const [copied, setCopied] = useState(false)
  const [sendOpen, setSendOpen] = useState(false)
  const [recipient, setRecipient] = useState(defaultRecipient || '')
  const [sending, setSending] = useState(false)
  const [sendResult, setSendResult] = useState(null)
  const [sendMessage, setSendMessage] = useState('')

  const copyEmail = async () => {
    const text = `Subject: ${subject}\n\n${body}`
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleSend = async () => {
    if (!recipient) return
    setSending(true)
    setSendResult(null)
    setSendMessage('')
    try {
      const res = await apiFetch('/send-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company,
          to_email: recipient,
          subject: subject || '',
          body: body || '',
        }),
      })
      const rawText = await res.text()
      let data = null
      if (rawText) {
        try {
          data = JSON.parse(rawText)
        } catch {
          data = null
        }
      }

      if (!res.ok) {
        setSendResult('error')
        setSendMessage(
          data?.detail ||
          (rawText ? `HTTP ${res.status}: ${rawText}` : `HTTP ${res.status}: empty response body`)
        )
        return
      }

      if (data?.status === 'sent') {
        setSendResult('success')
        setSendMessage(`Sent via ${data?.method || 'email provider'}.`)
        return
      }

      setSendResult('error')
      setSendMessage(
        data?.error ||
        (data?.status ? `Email service returned "${data.status}".` : (rawText || 'Unknown send failure.'))
      )
    } catch (err) {
      setSendResult('error')
      setSendMessage(err?.message || 'Network error while sending email.')
    } finally {
      setSending(false)
    }
  }

  if (!subject && !body) {
    return (
      <div className="glass-card p-12 text-center">
        <div className="text-4xl mb-4">❄️</div>
        <p className="text-slate-400 font-medium">No email generated</p>
        <p className="text-xs text-slate-600 mt-1">
          Opportunity score was too low — outreach skipped.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Subject line */}
      <div className="glass-card p-5">
        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
          Subject Line
        </div>
        <p className="text-white font-semibold text-base">{subject}</p>
      </div>

      {/* Email body */}
      <div className="glass-card p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Email Body
          </div>
          <div className="flex items-center gap-2">
            {wordCount !== undefined && <WordCountBadge count={wordCount} />}
          </div>
        </div>

        {/* Body preview */}
        <div className="rounded-xl p-5 mb-4 font-mono text-sm text-slate-300 leading-relaxed whitespace-pre-wrap"
          style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}>
          {body}
        </div>

        {/* Actions */}
        <div className="flex flex-wrap items-center gap-3 pt-4 border-t border-white/[0.06]">
          {/* Copy */}
          <button id="copy-email-btn" onClick={copyEmail} className="btn-ghost text-sm">
            {copied ? (
              <>
                <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-emerald-400">Copied!</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Copy Email
              </>
            )}
          </button>

          {/* Send */}
          <button id="send-email-btn"
            onClick={() => setSendOpen(!sendOpen)}
            className="btn-fire text-sm py-2">
            <span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </span>
            <span>Send Email</span>
          </button>
        </div>

        {/* Send panel */}
        {sendOpen && (
          <div className="mt-4 pt-4 border-t border-white/[0.06] animate-fade-in">
            <div className="text-xs font-semibold text-slate-400 mb-3">Send to recipient</div>
            {contactCandidates.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-3">
                {contactCandidates.slice(0, 4).map((candidate) => (
                  <button
                    key={candidate.email}
                    type="button"
                    onClick={() => setRecipient(candidate.email)}
                    className="text-xs font-medium px-3 py-1.5 rounded-full transition-all duration-200"
                    style={{
                      background: 'rgba(255,255,255,0.04)',
                      border: '1px solid rgba(255,255,255,0.08)',
                      color: '#94A3B8',
                    }}
                  >
                    {candidate.email}
                  </button>
                ))}
              </div>
            )}
            <div className="flex gap-3">
              <input
                type="email"
                className="input-field flex-1 text-sm"
                placeholder="prospect@company.com"
                value={recipient}
                onChange={e => setRecipient(e.target.value)}
                id="recipient-email-input"
              />
              <button
                onClick={handleSend}
                disabled={sending || !recipient}
                className="btn-fire text-sm py-2 px-5 flex-shrink-0">
                <span>
                  {sending ? (
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                  ) : 'Send'}
                </span>
              </button>
            </div>

            {sendResult && (
              <div className={`mt-3 text-sm rounded-lg px-4 py-2.5 ${
                sendResult === 'success'
                  ? 'text-emerald-400 bg-emerald-400/10 border border-emerald-400/20'
                  : 'text-red-400 bg-red-400/10 border border-red-400/20'
              }`}>
                {sendResult === 'success'
                  ? `✓ Email sent successfully! ${sendMessage}`
                  : `✗ Send failed. ${sendMessage || 'Check backend logs for details.'}`}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
