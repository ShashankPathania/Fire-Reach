import { useMemo, useState } from 'react'
import { apiFetch } from '../lib/api'
import { useAuth } from '../context/AuthContext'

export default function Settings() {
  const { user } = useAuth()
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const urlMessage = useMemo(() => {
    const params = new URLSearchParams(window.location.search)
    const ok = params.get('google')
    const email = params.get('email')
    if (ok === 'connected') return `Connected Google sender: ${email || 'account linked'}`
    return ''
  }, [])

  const connectGoogle = async () => {
    setLoading(true)
    setMessage('')
    try {
      const res = await apiFetch('/auth/google/start', { method: 'POST' })
      const data = await res.json()
      if (!res.ok) throw new Error(data?.detail || 'Failed to start Google OAuth')
      window.location.href = data.auth_url
    } catch (err) {
      setMessage(err.message || 'Could not start Google OAuth')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen px-6 py-10 max-w-4xl mx-auto">
      <div className="animate-fade-in mb-8">
        <h1 className="text-4xl font-black text-white mb-2">Account Settings</h1>
        <p className="text-slate-500 text-sm">Manage your sender identity and integrations.</p>
      </div>

      <div className="glass-card p-6 space-y-4">
        <div>
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Profile</div>
          <p className="text-white">{user?.name}</p>
          <p className="text-slate-400 text-sm">{user?.email}</p>
        </div>

        <div className="pt-4 border-t border-white/[0.06]">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Google Sender OAuth</div>
          <p className="text-sm text-slate-400 mb-3">
            Connect your Google account so outreach emails are sent from your own mailbox.
          </p>
          <p className="text-sm mb-3">
            Status:{' '}
            <span className={user?.google_connected ? 'text-emerald-400' : 'text-yellow-300'}>
              {user?.google_connected ? `Connected (${user?.google_email})` : 'Not connected'}
            </span>
          </p>
          <button onClick={connectGoogle} className="btn-fire text-sm" disabled={loading}>
            {loading ? 'Connecting...' : (user?.google_connected ? 'Reconnect Google' : 'Connect Google')}
          </button>
        </div>

        {(message || urlMessage) && (
          <div className="text-sm rounded-lg px-4 py-2.5 text-slate-300 bg-white/[0.03] border border-white/[0.06]">
            {message || urlMessage}
          </div>
        )}
      </div>
    </div>
  )
}
