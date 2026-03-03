import { useEffect, useMemo, useState } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
const FILE_BASE = API_BASE_URL.replace('/api/v1', '')

const CATEGORIES = [
  'Road & Infrastructure',
  'Water & Drainage',
  'Sanitation',
  'Electricity',
  'Public Safety',
  'Other',
]
const STATUS = ['Pending', 'Not Started', 'Completed']

const emptyIssue = {
  title: '',
  description: '',
  category: CATEGORIES[0],
  latitude: '',
  longitude: '',
  image_base64: '',
}

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '')
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user') || 'null'))
  const [authMode, setAuthMode] = useState('login')
  const [authForm, setAuthForm] = useState({ name: '', identifier: '', password: '', otp: '', role: 'citizen' })
  const [otpMessage, setOtpMessage] = useState('')

  const [issueForm, setIssueForm] = useState(emptyIssue)
  const [preview, setPreview] = useState('')

  const [issues, setIssues] = useState([])
  const [analytics, setAnalytics] = useState({ total_issues: 0, pending: 0, completed: 0 })
  const [filters, setFilters] = useState({ status: '', category: '', search: '', page: 1, page_size: 8 })
  const [resolutionDrafts, setResolutionDrafts] = useState({})

  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')

  const isAuthority = user?.role === 'authority'

  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token])

  async function api(path, options = {}) {
    const resp = await fetch(`${API_BASE_URL}${path}`, options)
    const data = await resp.json().catch(() => ({}))
    if (!resp.ok) throw new Error(data.detail || data.message || `Request failed (${resp.status})`)
    return data
  }

  async function fetchIssues(nextFilters = filters) {
    try {
      const qs = new URLSearchParams(Object.entries(nextFilters).filter(([, v]) => v !== '' && v !== null))
      const data = await api(`/issues?${qs.toString()}`)
      setIssues(data.items || [])
    } catch (err) {
      setMessage(err.message)
    }
  }

  async function fetchAnalytics() {
    try {
      const data = await api('/dashboard/analytics')
      setAnalytics(data)
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    fetchIssues()
    fetchAnalytics()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function requestOtp() {
    try {
      setBusy(true)
      const data = await api('/auth/request-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifier: authForm.identifier, purpose: authMode }),
      })
      setOtpMessage(`${data.message}. Demo OTP: ${data.demo_otp}`)
      setMessage('OTP generated. Use it to continue.')
    } catch (err) {
      setMessage(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function submitAuth(e) {
    e.preventDefault()
    try {
      setBusy(true)
      const payload =
        authMode === 'register'
          ? {
              name: authForm.name,
              identifier: authForm.identifier,
              password: authForm.password,
              otp: authForm.otp,
              role: authForm.role,
            }
          : {
              identifier: authForm.identifier,
              password: authForm.password,
              otp: authForm.otp,
            }
      const data = await api(`/auth/${authMode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      setToken(data.access_token)
      setUser(data.user)
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      setMessage(`Welcome ${data.user.name}`)
      setOtpMessage('')
    } catch (err) {
      setMessage(err.message)
    } finally {
      setBusy(false)
    }
  }

  function readBase64(file, cb) {
    const reader = new FileReader()
    reader.onload = () => cb(String(reader.result || ''))
    reader.readAsDataURL(file)
  }

  async function createIssue(e) {
    e.preventDefault()
    if (!token) return setMessage('Please login first')
    try {
      setBusy(true)
      await api('/issues', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders },
        body: JSON.stringify(issueForm),
      })
      setIssueForm(emptyIssue)
      setPreview('')
      setMessage('Issue submitted')
      fetchIssues({ ...filters, page: 1 })
      fetchAnalytics()
    } catch (err) {
      setMessage(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function deleteIssue(issueId) {
    try {
      await api(`/issues/${issueId}`, { method: 'DELETE', headers: authHeaders })
      setMessage('Issue deleted')
      fetchIssues(filters)
      fetchAnalytics()
    } catch (err) {
      setMessage(err.message)
    }
  }

  async function updateStatus(issueId, status) {
    const draft = resolutionDrafts[issueId] || { comment: '', resolution_image_base64: '' }
    try {
      await api(`/issues/${issueId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', ...authHeaders },
        body: JSON.stringify({ status, comment: draft.comment || '', resolution_image_base64: draft.resolution_image_base64 || null }),
      })
      setMessage('Status updated')
      fetchIssues(filters)
      fetchAnalytics()
    } catch (err) {
      setMessage(err.message)
    }
  }

  function logout() {
    setToken('')
    setUser(null)
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  function fillCurrentLocation() {
    if (!navigator.geolocation) return
    navigator.geolocation.getCurrentPosition((position) => {
      setIssueForm((prev) => ({
        ...prev,
        latitude: Number(position.coords.latitude).toFixed(6),
        longitude: Number(position.coords.longitude).toFixed(6),
      }))
    })
  }

  const mapUrl = `https://www.openstreetmap.org/export/embed.html?bbox=${(Number(issueForm.longitude) || 77) - 0.01}%2C${(Number(issueForm.latitude) || 28.6) - 0.01}%2C${(Number(issueForm.longitude) || 77) + 0.01}%2C${(Number(issueForm.latitude) || 28.6) + 0.01}&layer=mapnik&marker=${Number(issueForm.latitude) || 28.6}%2C${Number(issueForm.longitude) || 77}`

  return (
    <div className="min-h-screen bg-slate-100 p-4 md:p-8 text-slate-800">
      <div className="mx-auto max-w-7xl space-y-4">
        <div className="rounded-xl bg-white p-4 shadow flex flex-wrap justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold">Smart City Issue Detection</h1>
            <p className="text-sm">Common dashboard for citizens and authorities. Public issue visibility with role-based editing.</p>
          </div>
          <div className="text-sm flex gap-2 items-center">
            {user ? <span className="px-2 py-1 bg-blue-100 rounded">{user.name} ({user.role})</span> : <span>Guest</span>}
            {user ? <button onClick={logout} className="px-3 py-2 bg-slate-800 text-white rounded">Logout</button> : null}
          </div>
        </div>

        {!user ? (
          <form onSubmit={submitAuth} className="rounded-xl bg-white p-4 shadow grid md:grid-cols-5 gap-2">
            {authMode === 'register' ? <input className="border p-2 rounded" placeholder="Name" value={authForm.name} onChange={(e) => setAuthForm({ ...authForm, name: e.target.value })} /> : null}
            <input className="border p-2 rounded" placeholder="Email or phone" value={authForm.identifier} onChange={(e) => setAuthForm({ ...authForm, identifier: e.target.value })} />
            <input className="border p-2 rounded" type="password" placeholder="Password" value={authForm.password} onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })} />
            <input className="border p-2 rounded" placeholder="OTP" value={authForm.otp} onChange={(e) => setAuthForm({ ...authForm, otp: e.target.value })} />
            {authMode === 'register' ? (
              <select className="border p-2 rounded" value={authForm.role} onChange={(e) => setAuthForm({ ...authForm, role: e.target.value })}>
                <option value="citizen">citizen</option>
                <option value="authority">authority</option>
              </select>
            ) : null}

            <button className="px-3 py-2 rounded bg-indigo-600 text-white" type="button" onClick={requestOtp} disabled={busy}>Get OTP</button>
            <button className="px-3 py-2 rounded bg-blue-600 text-white" type="submit" disabled={busy}>{authMode === 'register' ? 'Sign up' : 'Login'}</button>
            <button className="px-3 py-2 rounded bg-slate-200" type="button" onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}>Switch to {authMode === 'login' ? 'signup' : 'login'}</button>
            {otpMessage ? <div className="md:col-span-5 text-xs text-emerald-700">{otpMessage}</div> : null}
          </form>
        ) : null}

        {user ? (
          <form onSubmit={createIssue} className="rounded-xl bg-white p-4 shadow space-y-2">
            <h2 className="font-semibold">Report Issue</h2>
            <div className="grid md:grid-cols-2 gap-2">
              <input className="border p-2 rounded w-full" placeholder="Title" value={issueForm.title} onChange={(e) => setIssueForm({ ...issueForm, title: e.target.value })} />
              <select className="border p-2 rounded w-full" value={issueForm.category} onChange={(e) => setIssueForm({ ...issueForm, category: e.target.value })}>
                {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
              </select>
            </div>
            <textarea className="border p-2 rounded w-full" placeholder="Description" value={issueForm.description} onChange={(e) => setIssueForm({ ...issueForm, description: e.target.value })} />
            <div className="grid grid-cols-2 gap-2">
              <input className="border p-2 rounded" placeholder="Latitude" value={issueForm.latitude} onChange={(e) => setIssueForm({ ...issueForm, latitude: e.target.value })} />
              <input className="border p-2 rounded" placeholder="Longitude" value={issueForm.longitude} onChange={(e) => setIssueForm({ ...issueForm, longitude: e.target.value })} />
            </div>
            <button type="button" className="text-sm px-2 py-1 bg-slate-100 rounded" onClick={fillCurrentLocation}>Use current location</button>
            <iframe title="map" src={mapUrl} className="w-full h-44 rounded border" />
            <input
              type="file"
              accept="image/*"
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (!file) return
                readBase64(file, (b64) => {
                  setIssueForm({ ...issueForm, image_base64: b64 })
                  setPreview(b64)
                })
              }}
            />
            {preview ? <img src={preview} alt="preview" className="h-24 rounded object-cover" /> : null}
            <button className="w-full py-2 rounded bg-emerald-600 text-white" disabled={busy}>Submit Issue</button>
          </form>
        ) : null}

        <div className="rounded-xl bg-white p-4 shadow space-y-3">
          <h2 className="font-semibold">Common Dashboard (All users)</h2>
          <div className="grid md:grid-cols-3 gap-2">
            <div className="p-3 rounded bg-slate-100">Total: <strong>{analytics.total_issues}</strong></div>
            <div className="p-3 rounded bg-amber-100">Pending/Not Started: <strong>{analytics.pending}</strong></div>
            <div className="p-3 rounded bg-green-100">Completed: <strong>{analytics.completed}</strong></div>
          </div>

          <div className="grid md:grid-cols-5 gap-2">
            <select className="border p-2 rounded" value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
              <option value="">All Status</option>
              {STATUS.map((s) => <option key={s}>{s}</option>)}
            </select>
            <select className="border p-2 rounded" value={filters.category} onChange={(e) => setFilters({ ...filters, category: e.target.value })}>
              <option value="">All Categories</option>
              {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
            </select>
            <input className="border p-2 rounded md:col-span-2" placeholder="Search title/description" value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} />
            <button className="bg-blue-600 text-white rounded p-2" type="button" onClick={() => fetchIssues(filters)}>Apply</button>
          </div>

          <div className="space-y-2">
            {issues.map((issue) => {
              const draft = resolutionDrafts[issue.id] || { comment: '', resolution_image_base64: '' }
              return (
                <div key={issue.id} className="border rounded p-3 space-y-2">
                  <div className="flex justify-between gap-2 flex-wrap">
                    <div>
                      <h3 className="font-semibold">{issue.title}</h3>
                      <p className="text-sm">{issue.description}</p>
                      <p className="text-xs text-slate-500">{issue.category} · <b>{issue.status}</b> · by {issue.reporter_name} ({issue.reporter_contact})</p>
                      <a className="text-xs text-blue-700" href={`https://maps.google.com/?q=${issue.latitude},${issue.longitude}`} target="_blank">View location</a>
                    </div>
                    <div className="space-y-1">
                      {issue.image_path ? <img src={`${FILE_BASE}/${issue.image_path.replace('backend/', '')}`} alt="issue" className="w-20 h-20 object-cover rounded" /> : null}
                      {issue.resolution_image_path ? <img src={`${FILE_BASE}/${issue.resolution_image_path.replace('backend/', '')}`} alt="resolution" className="w-20 h-20 object-cover rounded border-2 border-emerald-400" /> : null}
                      {(user?.id === issue.user_id || isAuthority) && token ? <button className="text-xs px-2 py-1 bg-red-100 rounded" type="button" onClick={() => deleteIssue(issue.id)}>Delete</button> : null}
                    </div>
                  </div>

                  {isAuthority ? (
                    <div className="grid md:grid-cols-3 gap-2 items-center">
                      <input
                        className="border p-2 rounded"
                        placeholder="Resolution comment"
                        value={draft.comment}
                        onChange={(e) => setResolutionDrafts({ ...resolutionDrafts, [issue.id]: { ...draft, comment: e.target.value } })}
                      />
                      <input
                        type="file"
                        accept="image/*"
                        onChange={(e) => {
                          const file = e.target.files?.[0]
                          if (!file) return
                          readBase64(file, (b64) => setResolutionDrafts({ ...resolutionDrafts, [issue.id]: { ...draft, resolution_image_base64: b64 } }))
                        }}
                      />
                      <div className="flex gap-1 flex-wrap">
                        {STATUS.map((s) => (
                          <button key={s} className="px-2 py-1 rounded bg-slate-100 text-xs" type="button" onClick={() => updateStatus(issue.id, s)}>
                            {s}
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </div>
              )
            })}
          </div>

          <div className="flex gap-2">
            <button className="px-3 py-1 rounded bg-slate-200" type="button" onClick={() => { const p = Math.max(1, filters.page - 1); const f = { ...filters, page: p }; setFilters(f); fetchIssues(f) }}>Prev</button>
            <button className="px-3 py-1 rounded bg-slate-200" type="button" onClick={() => { const f = { ...filters, page: filters.page + 1 }; setFilters(f); fetchIssues(f) }}>Next</button>
            <span className="text-sm self-center">Page {filters.page}</span>
          </div>
        </div>

        {message ? <div className="rounded bg-slate-800 text-white px-3 py-2 text-sm">{message}</div> : null}
      </div>
    </div>
  )
}

export default App
