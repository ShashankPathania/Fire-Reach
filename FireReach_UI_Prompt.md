# 🎨 FireReach AI – React Dashboard Prompt (for Agentic Coder)

## OBJECTIVE

Build a **production-grade React dashboard** for FireReach AI that displays:
- Input form for company + ICP
- Real-time agent execution steps
- Signals visualization
- Lead scoring display
- Email preview
- Send/History functionality

---

## 🎯 DESIGN SYSTEM

### Colors
```
Primary: #2563eb (blue)
Success: #10b981 (green)
Warning: #f59e0b (amber)
Danger: #ef4444 (red)
BG: #f9fafb (light gray)
Text: #1f2937 (dark gray)
```

### Typography
```
Font: Inter or system font
Title: 28px bold
Heading: 18px bold
Body: 14px regular
Small: 12px
```

### Spacing
```
Base unit: 8px
Standard padding: 16px, 24px
Standard margin: 16px, 24px
Border radius: 8px, 12px
```

---

## 📄 PAGE 1: HOME (Input)

### Layout
```
Header
  Logo + Title "FireReach AI"
  Subtitle "Signal-driven outreach automation"

Main Content
  Input Form
    - Company Name (text input, required)
    - ICP (textarea, required)
    - Send Email toggle (optional)
    - Recipient Email (conditional, required if toggle on)
    - Analyze button

Footer
  "Powered by Serper + LangGraph"
```

### Form Validation
```
- Company: min 2 chars, max 100
- ICP: min 10 chars, max 500
- Email: valid email format
- Show error messages inline
- Disable submit if validation fails
```

### Component

```jsx
// pages/Home.jsx
export default function Home() {
  const [company, setCompany] = useState("");
  const [icp, setIcp] = useState("");
  const [sendEmail, setSendEmail] = useState(false);
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch("/api/run-agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company,
          icp,
          send_email: sendEmail,
          recipient_email: sendEmail ? email : null
        })
      });

      if (!response.ok) throw new Error("API error");
      
      const data = await response.json();
      navigate("/results", { state: data });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Header />
      
      <main className="max-w-2xl mx-auto px-6 py-12">
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold mb-2 text-gray-900">
            Analyze Your Next Prospect
          </h1>
          <p className="text-gray-600 mb-8">
            Enter a company and your ICP. We'll find signals and draft an email.
          </p>

          {error && <ErrorAlert message={error} />}

          {/* Company Input */}
          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Company Name *
            </label>
            <input
              type="text"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="e.g., Stripe, Notion, Figma"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          {/* ICP Input */}
          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Ideal Customer Profile (ICP) *
            </label>
            <textarea
              value={icp}
              onChange={(e) => setIcp(e.target.value)}
              placeholder="e.g., B2B SaaS companies scaling engineering teams rapidly"
              rows="4"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          {/* Email Toggle */}
          <div className="mb-6 flex items-center">
            <input
              type="checkbox"
              id="sendEmail"
              checked={sendEmail}
              onChange={(e) => setSendEmail(e.target.checked)}
              className="w-4 h-4 text-blue-600 rounded"
            />
            <label htmlFor="sendEmail" className="ml-3 text-sm font-medium text-gray-700">
              Send email automatically
            </label>
          </div>

          {/* Email Input (Conditional) */}
          {sendEmail && (
            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Recipient Email *
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="prospect@company.com"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required={sendEmail}
              />
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !company.trim() || !icp.trim()}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 rounded-lg transition"
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <Spinner className="mr-2" />
                Analyzing...
              </span>
            ) : (
              "Run Analysis"
            )}
          </button>
        </form>
      </main>
    </div>
  );
}
```

---

## 📊 PAGE 2: RESULTS

### Layout
```
Header
  Company name + "Results"
  Back button

Tabs
  [Overview] [Signals] [Email]

Tab 1: Overview
  Score Card (big, visual)
  Insights (2 paragraphs)
  Strategy
  Quick actions

Tab 2: Signals
  Funding signal card
  Hiring signal card
  Expansion signal card
  Tech stack signal card
  Confidence indicators

Tab 3: Email
  Subject line display
  Email body (formatted)
  Send button
  Copy button
```

### Score Card Component

```jsx
// components/ScoreDisplay.jsx
export function ScoreDisplay({ score, breakdown }) {
  const getColor = (score) => {
    if (score < 0.3) return "text-red-600";
    if (score < 0.6) return "text-amber-600";
    return "text-green-600";
  };

  const getLabel = (score) => {
    if (score < 0.3) return "Low";
    if (score < 0.6) return "Medium";
    return "High";
  };

  return (
    <div className="bg-white rounded-lg shadow p-8 text-center">
      <h3 className="text-gray-600 text-sm font-semibold mb-4">
        OUTREACH OPPORTUNITY
      </h3>
      
      <div className={`text-6xl font-bold mb-2 ${getColor(score)}`}>
        {(score * 100).toFixed(0)}%
      </div>
      
      <div className="text-gray-600 text-lg mb-6">
        {getLabel(score)} Opportunity
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-3 mb-6">
        <div
          className={`h-3 rounded-full transition-all ${
            score < 0.3 ? "bg-red-600" :
            score < 0.6 ? "bg-amber-600" :
            "bg-green-600"
          }`}
          style={{ width: `${score * 100}%` }}
        />
      </div>

      {/* Breakdown */}
      <div className="grid grid-cols-4 gap-4 text-sm">
        <div>
          <div className="font-semibold">{(breakdown.hiring * 100).toFixed(0)}%</div>
          <div className="text-gray-600 text-xs">Hiring</div>
        </div>
        <div>
          <div className="font-semibold">{(breakdown.funding * 100).toFixed(0)}%</div>
          <div className="text-gray-600 text-xs">Funding</div>
        </div>
        <div>
          <div className="font-semibold">{(breakdown.expansion * 100).toFixed(0)}%</div>
          <div className="text-gray-600 text-xs">Expansion</div>
        </div>
        <div>
          <div className="font-semibold">{(breakdown.tech * 100).toFixed(0)}%</div>
          <div className="text-gray-600 text-xs">Tech</div>
        </div>
      </div>
    </div>
  );
}
```

### Signals Card Component

```jsx
// components/SignalsCard.jsx
export function SignalsCard({ signals }) {
  const signals_list = [
    { key: "funding", icon: "💰", label: "Funding" },
    { key: "hiring", icon: "👥", label: "Hiring" },
    { key: "expansion", icon: "🌍", label: "Expansion" },
    { key: "tech", icon: "⚙️", label: "Tech Stack" }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {signals_list.map(({ key, icon, label }) => {
        const signal = signals[key];
        if (!signal) return null;

        return (
          <div key={key} className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
            <div className="flex items-center mb-4">
              <span className="text-2xl mr-3">{icon}</span>
              <h3 className="text-lg font-semibold text-gray-900">{label}</h3>
            </div>

            <div className="space-y-2 text-sm">
              {signal.status && (
                <div>
                  <span className="text-gray-600">Status:</span>
                  <span className="ml-2 font-medium text-gray-900">{signal.status}</span>
                </div>
              )}

              {signal.amount && (
                <div>
                  <span className="text-gray-600">Amount:</span>
                  <span className="ml-2 font-medium text-gray-900">{signal.amount}</span>
                </div>
              )}

              {signal.roles && (
                <div>
                  <span className="text-gray-600">Open Roles:</span>
                  <span className="ml-2 font-medium text-gray-900">{signal.roles}</span>
                </div>
              )}

              <div className="flex items-center mt-4">
                <span className="text-gray-600 text-xs">Confidence</span>
                <div className="ml-auto flex items-center">
                  <div className="w-24 bg-gray-200 rounded-full h-2 mr-2">
                    <div
                      className="bg-green-500 h-2 rounded-full"
                      style={{ width: `${(signal.confidence || 0) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs font-semibold">
                    {((signal.confidence || 0) * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
```

### Email Preview Component

```jsx
// components/EmailPreview.jsx
export function EmailPreview({ email, subject, onSend, onCopy }) {
  const handleCopy = () => {
    const text = `Subject: ${subject}\n\n${email}`;
    navigator.clipboard.writeText(text);
    alert("Copied to clipboard!");
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      {/* Subject Preview */}
      <div className="bg-gray-100 px-8 py-6 border-b">
        <h4 className="text-xs text-gray-500 font-semibold mb-1">SUBJECT</h4>
        <h3 className="text-xl font-semibold text-gray-900">{subject}</h3>
      </div>

      {/* Body Preview */}
      <div className="px-8 py-6">
        <h4 className="text-xs text-gray-500 font-semibold mb-3">BODY</h4>
        <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
          {email}
        </p>

        {/* Word Count */}
        <div className="mt-6 text-sm text-gray-500">
          {email.split(/\s+/).length} words (max 120)
        </div>
      </div>

      {/* Actions */}
      <div className="bg-gray-50 px-8 py-4 border-t flex gap-4">
        <button
          onClick={handleCopy}
          className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-900 rounded-lg font-medium transition"
        >
          Copy
        </button>
        <button
          onClick={onSend}
          className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition"
        >
          Send Email
        </button>
      </div>
    </div>
  );
}
```

### Results Page

```jsx
// pages/Results.jsx
export default function Results() {
  const location = useLocation();
  const result = location.state;
  const [activeTab, setActiveTab] = useState("overview");

  if (!result) return <div>No results. Go back and run analysis.</div>;

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-6xl mx-auto px-6 py-12">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {result.company}
            </h1>
            <p className="text-gray-600">Analysis Results</p>
          </div>
          <Link to="/" className="text-blue-600 hover:text-blue-700 font-medium">
            ← Back
          </Link>
        </div>

        {/* Tabs */}
        <div className="flex gap-8 mb-8 border-b">
          {["overview", "signals", "email"].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-4 font-medium transition ${
                activeTab === tab
                  ? "text-blue-600 border-b-2 border-blue-600"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Content */}
        {activeTab === "overview" && (
          <div className="space-y-8">
            <ScoreDisplay
              score={result.score}
              breakdown={result.score_breakdown}
            />
            <div className="bg-white rounded-lg shadow p-8">
              <h3 className="text-xl font-bold text-gray-900 mb-4">
                Account Brief
              </h3>
              <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                {result.insights}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-8">
              <h3 className="text-xl font-bold text-gray-900 mb-4">
                Outreach Strategy
              </h3>
              <p className="text-gray-700">{result.strategy}</p>
            </div>
          </div>
        )}

        {activeTab === "signals" && (
          <SignalsCard signals={result.signals} />
        )}

        {activeTab === "email" && (
          <EmailPreview
            email={result.email}
            subject={result.email_subject}
            onSend={() => alert("Email sent!")}
            onCopy={() => {}}
          />
        )}
      </main>
    </div>
  );
}
```

---

## 📜 PAGE 3: HISTORY

### Layout
```
Header "Outreach History"

Table
  Columns:
    - Company
    - Score
    - Date
    - Status
    - Action (View)

Filters
  - Status filter (All, Sent, Failed)
  - Date range
```

### History Page

```jsx
// pages/History.jsx
export default function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await fetch("/api/history");
      const data = await response.json();
      setHistory(data.records);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = filter === "all" 
    ? history 
    : history.filter(h => h.status === filter);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-6xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          Outreach History
        </h1>

        {/* Filter */}
        <div className="mb-8 flex gap-4">
          {["all", "sent", "failed", "stopped"].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filter === status
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-900 border border-gray-300 hover:bg-gray-50"
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>

        {/* Table */}
        {loading ? (
          <Spinner />
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-100 border-b">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">
                    Company
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">
                    Score
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">
                    Status
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">
                    Date
                  </th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-900">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {filtered.map((record) => (
                  <tr key={record.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 font-medium text-gray-900">
                      {record.company}
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-semibold">
                        {(record.score * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={record.status} />
                    </td>
                    <td className="px-6 py-4 text-gray-600">
                      {new Date(record.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={`/record/${record.id}`}
                        className="text-blue-600 hover:text-blue-700 font-medium"
                      >
                        View →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
```

---

## 🧩 SHARED COMPONENTS

### Header

```jsx
// components/Header.jsx
export function Header() {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <span className="text-2xl font-bold text-blue-600">🔥</span>
          <span className="text-xl font-bold text-gray-900">FireReach</span>
        </Link>
        
        <nav className="flex gap-8">
          <Link to="/" className="text-gray-600 hover:text-gray-900">
            Home
          </Link>
          <Link to="/history" className="text-gray-600 hover:text-gray-900">
            History
          </Link>
        </nav>
      </div>
    </header>
  );
}
```

### Status Badge

```jsx
// components/StatusBadge.jsx
export function StatusBadge({ status }) {
  const colors = {
    sent: "bg-green-100 text-green-800",
    failed: "bg-red-100 text-red-800",
    stopped: "bg-yellow-100 text-yellow-800",
    pending: "bg-blue-100 text-blue-800"
  };

  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium ${colors[status]}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}
```

### Spinner

```jsx
// components/Spinner.jsx
export function Spinner() {
  return (
    <div className="inline-block animate-spin">
      <svg
        className="w-5 h-5 text-current"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    </div>
  );
}
```

---

## 🎨 STYLING NOTES

- Use **Tailwind CSS** exclusively
- Dark mode support (optional but nice)
- Mobile responsive
- Smooth transitions (150ms)
- Accessible (proper ARIA labels, color contrast)
- Focus states on interactive elements

---

## 📦 DEPENDENCIES

```json
{
  "dependencies": {
    "react": "^18.0.0",
    "react-router-dom": "^6.0.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "tailwindcss": "^3.0.0",
    "autoprefixer": "^10.0.0"
  }
}
```

---

## 🚀 BUILD CHECKLIST

- [ ] Setup React project with Vite or CRA
- [ ] Install Tailwind CSS
- [ ] Create file structure (pages, components)
- [ ] Build Home page
- [ ] Build Results page (3 tabs)
- [ ] Build History page
- [ ] Implement API calls
- [ ] Add error handling
- [ ] Mobile responsive
- [ ] Deploy to Vercel/Netlify
