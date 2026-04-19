import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Home from './pages/Home'
import Results from './pages/Results'
import History from './pages/History'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Settings from './pages/Settings'
import ProtectedRoute from './components/ProtectedRoute'
import { useAuth } from './context/AuthContext'

function Nav() {
  const { isAuthenticated, user, logout } = useAuth()

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/[0.06]"
      style={{ background: 'rgba(7,10,15,0.85)', backdropFilter: 'blur(20px)' }}>
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <a href="/" className="flex items-center gap-3 group">
          <div className="relative">
            <span className="text-2xl">🔥</span>
            <div className="absolute -inset-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
              style={{ background: 'radial-gradient(circle, rgba(255,90,0,0.2) 0%, transparent 70%)' }} />
          </div>
          <div>
            <span className="text-lg font-bold text-white">FireReach</span>
            <span className="text-lg font-bold text-fire ml-1">AI</span>
          </div>
        </a>

        {/* Nav links */}
        {isAuthenticated ? (
          <>
            <div className="flex items-center gap-1">
              <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Analyze
              </NavLink>
              <NavLink to="/history" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                History
              </NavLink>
              <NavLink to="/settings" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317a1 1 0 011.35-.936l.755.346a1 1 0 00.84 0l.755-.346a1 1 0 011.35.936l.083.819a1 1 0 00.596.804l.751.322a1 1 0 01.557 1.243l-.27.777a1 1 0 00.163.987l.522.636a1 1 0 010 1.264l-.522.636a1 1 0 00-.163.987l.27.777a1 1 0 01-.557 1.243l-.751.322a1 1 0 00-.596.804l-.083.819a1 1 0 01-1.35.936l-.755-.346a1 1 0 00-.84 0l-.755.346a1 1 0 01-1.35-.936l-.083-.819a1 1 0 00-.596-.804l-.751-.322a1 1 0 01-.557-1.243l.27-.777a1 1 0 00-.163-.987l-.522-.636a1 1 0 010-1.264l.522-.636a1 1 0 00.163-.987l-.27-.777a1 1 0 01.557-1.243l.751-.322a1 1 0 00.596-.804l.083-.819z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Settings
              </NavLink>
            </div>

            <div className="flex items-center gap-3 text-xs text-slate-500">
              <div className="glow-dot" />
              <span>{user?.name || 'User'}</span>
              <button onClick={logout} className="btn-ghost text-xs py-1.5 px-3">Logout</button>
            </div>
          </>
        ) : (
          <div className="flex items-center gap-2">
            <NavLink to="/login" className="btn-ghost text-sm py-2 px-4">Login</NavLink>
            <NavLink to="/signup" className="btn-fire text-sm py-2 px-4">Sign up</NavLink>
          </div>
        )}
      </div>
    </nav>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen" style={{ background: '#070A0F' }}>
        {/* Ambient background glows */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-[-10%] left-[20%] w-[600px] h-[600px] rounded-full opacity-[0.04]"
            style={{ background: 'radial-gradient(circle, #FF5A00 0%, transparent 70%)' }} />
          <div className="absolute bottom-[-5%] right-[10%] w-[400px] h-[400px] rounded-full opacity-[0.03]"
            style={{ background: 'radial-gradient(circle, #FF9A00 0%, transparent 70%)' }} />
        </div>

        <Nav />
        <main className="pt-16">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/" element={<ProtectedRoute><Home /></ProtectedRoute>} />
            <Route path="/results" element={<ProtectedRoute><Results /></ProtectedRoute>} />
            <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
