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
const STATUS = ['Pending', 'Processing', 'Completed']

const emptyForm = {
  title: '',
  description: '',
  category: CATEGORIES[0],
  latitude: '',
  longitude: '',
  image: null,
}

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '')
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user') || 'null'))
  const [authMode, setAuthMode] = useState('login')
  const [authForm, setAuthForm] = useState({ name: '', email: '', password: '', role: 'citizen' })
  const [issueForm, setIssueForm] = useState(emptyForm)
  const [preview, setPreview] = useState('')
  const [issues, setIssues] = useState([])
  const [analytics, setAnalytics] = useState({ total_issues: 0, pending: 0, completed: 0 })
  const [filters, setFilters] = useState({ status: '', category: '', search: '', page: 1, page_size: 6 })
  const [message, setMessage] = useState('')

  const isAuthority = user?.role === 'authority'

  const authHeaders = useMemo(
    () =>
      token
        ? {
            Authorization: `Bearer ${token}`,
          }
        : {},
    [token],
  )

  async function fetchIssues(nextFilters = filters) {
    const qs = new URLSearchParams(Object.entries(nextFilters).filter(([, v]) => v !== '' && v !== null))
    const resp = await fetch(`${API_BASE_URL}/issues?${qs.toString()}`)
    const data = await resp.json()
    setIssues(data.items || [])
  }

  async function fetchAnalytics() {
    const resp = await fetch(`${API_BASE_URL}/dashboard/analytics`)
    const data = await resp.json()
    setAnalytics(data)
  }

  useEffect(() => {
    fetchIssues()
    fetchAnalytics()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function submitAuth(e) {
    e.preventDefault()
    const url = `${API_BASE_URL}/auth/${authMode}`
    const body = authMode === 'login' ? { email: authForm.email, password: authForm.password } : authForm
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await resp.json()
    if (!resp.ok) return setMessage(data.detail || 'Authentication failed')
    setToken(data.access_token)
    setUser(data.user)
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    setMessage(`Logged in as ${data.user.role}`)
  }

  async function createIssue(e) {
    e.preventDefault()
    if (!token) return setMessage('Please login first')
    const formData = new FormData()
    Object.entries(issueForm).forEach(([key, value]) => {
      if (value !== null && value !== '') formData.append(key, value)
    })
    const resp = await fetch(`${API_BASE_URL}/issues`, {
      method: 'POST',
      headers: authHeaders,
      body: formData,
    })
    const data = await resp.json()
    if (!resp.ok) return setMessage(data.detail || 'Could not create issue')
    setIssueForm(emptyForm)
    setPreview('')
    setMessage('Issue created successfully')
    fetchIssues({ ...filters, page: 1 })
    fetchAnalytics()
  }

  async function deleteIssue(id) {
    const resp = await fetch(`${API_BASE_URL}/issues/${id}`, {
      method: 'DELETE',
      headers: authHeaders,
    })
    if (resp.ok) {
      setMessage('Issue deleted')
      fetchIssues(filters)
      fetchAnalytics()
    }
  }

  async function updateStatus(id, status) {
    const formData = new FormData()
    formData.append('status', status)
    const resp = await fetch(`${API_BASE_URL}/issues/${id}/status`, {
      method: 'PATCH',
      headers: authHeaders,
      body: formData,
    })
    if (resp.ok) {
      setMessage('Status updated')
      fetchIssues(filters)
      fetchAnalytics()
    }
  }

  function logout() {
    setToken('')
    setUser(null)
    localStorage.clear()
  }

  function fillCurrentLocation() {
    navigator.geolocation.getCurrentPosition((position) => {
      setIssueForm((s) => ({
        ...s,
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
            <p className="text-sm">Public issue board, role-based actions, analytics dashboard, and map-aware reporting.</p>
          </div>
          <div className="text-sm flex gap-2 items-center">
            {user ? <span className="px-2 py-1 bg-blue-100 rounded">{user.name} ({user.role})</span> : <span>Guest</span>}
            {user ? <button onClick={logout} className="px-3 py-2 bg-slate-800 text-white rounded">Logout</button> : null}
          </div>
        </div>

        {!user ? (
          <form onSubmit={submitAuth} className="rounded-xl bg-white p-4 shadow grid md:grid-cols-4 gap-2">
            {authMode === 'register' ? <input className="border p-2 rounded" placeholder="Name" onChange={(e) => setAuthForm({ ...authForm, name: e.target.value })} /> : null}
            <input className="border p-2 rounded" placeholder="Email" onChange={(e) => setAuthForm({ ...authForm, email: e.target.value })} />
            <input className="border p-2 rounded" placeholder="Password" type="password" onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })} />
            {authMode === 'register' ? (
              <select className="border p-2 rounded" onChange={(e) => setAuthForm({ ...authForm, role: e.target.value })}>
                <option value="citizen">citizen</option>
                <option value="authority">authority</option>
              </select>
            ) : null}
            <button className="px-3 py-2 rounded bg-blue-600 text-white" type="submit">{authMode}</button>
            <button className="px-3 py-2 rounded bg-slate-200" type="button" onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}>Switch to {authMode === 'login' ? 'register' : 'login'}</button>
          </form>
        ) : null}

        <div className="grid lg:grid-cols-3 gap-4">
          <form onSubmit={createIssue} className="rounded-xl bg-white p-4 shadow space-y-2 lg:col-span-1">
            <h2 className="font-semibold">Report Issue</h2>
            <input className="border p-2 rounded w-full" placeholder="Title" value={issueForm.title} onChange={(e) => setIssueForm({ ...issueForm, title: e.target.value })} />
            <textarea className="border p-2 rounded w-full" placeholder="Description" value={issueForm.description} onChange={(e) => setIssueForm({ ...issueForm, description: e.target.value })} />
            <select className="border p-2 rounded w-full" value={issueForm.category} onChange={(e) => setIssueForm({ ...issueForm, category: e.target.value })}>
              {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
            </select>
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
                setIssueForm({ ...issueForm, image: file || null })
                if (file) setPreview(URL.createObjectURL(file))
              }}
            />
            {preview ? <img src={preview} alt="preview" className="h-24 rounded object-cover" /> : null}
            <button className="w-full py-2 rounded bg-emerald-600 text-white">Submit Issue</button>
          </form>

          <div className="rounded-xl bg-white p-4 shadow lg:col-span-2 space-y-3">
            <div className="grid md:grid-cols-3 gap-2">
              <div className="p-3 rounded bg-slate-100">Total: <strong>{analytics.total_issues}</strong></div>
              <div className="p-3 rounded bg-amber-100">Pending: <strong>{analytics.pending}</strong></div>
              <div className="p-3 rounded bg-green-100">Completed: <strong>{analytics.completed}</strong></div>
            </div>

            <div className="grid md:grid-cols-5 gap-2">
              <select className="border p-2 rounded" onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
                <option value="">All Status</option>
                {STATUS.map((s) => <option key={s}>{s}</option>)}
              </select>
              <select className="border p-2 rounded" onChange={(e) => setFilters({ ...filters, category: e.target.value })}>
                <option value="">All Categories</option>
                {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
              </select>
              <input className="border p-2 rounded md:col-span-2" placeholder="Search title/description" onChange={(e) => setFilters({ ...filters, search: e.target.value })} />
              <button className="bg-blue-600 text-white rounded p-2" onClick={() => fetchIssues(filters)}>Apply</button>
            </div>

            <div className="space-y-2">
              {issues.map((issue) => (
                <div key={issue.id} className="border rounded p-3">
                  <div className="flex justify-between gap-2 flex-wrap">
                    <div>
                      <h3 className="font-semibold">{issue.title}</h3>
                      <p className="text-sm">{issue.description}</p>
                      <p className="text-xs text-slate-500">{issue.category} · {issue.status} · by {issue.reporter_name}</p>
                      <a className="text-xs text-blue-700" href={`https://maps.google.com/?q=${issue.latitude},${issue.longitude}`} target="_blank">View location</a>
                    </div>
                    <div className="space-y-1">
                      {issue.image_path ? <img src={`${FILE_BASE}/${issue.image_path.replace('backend/', '')}`} alt="issue" className="w-20 h-20 object-cover rounded" /> : null}
                      {(user?.id === issue.user_id || isAuthority) && token ? <button className="text-xs px-2 py-1 bg-red-100 rounded" onClick={() => deleteIssue(issue.id)}>Delete</button> : null}
                    </div>
                  </div>
                  {isAuthority ? (
                    <div className="mt-2 flex gap-2">
                      {STATUS.map((s) => <button key={s} className="px-2 py-1 rounded bg-slate-100 text-xs" onClick={() => updateStatus(issue.id, s)}>{s}</button>)}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>

            <div className="flex gap-2">
              <button className="px-3 py-1 rounded bg-slate-200" onClick={() => { const p = Math.max(1, filters.page - 1); const f = { ...filters, page: p }; setFilters(f); fetchIssues(f) }}>Prev</button>
              <button className="px-3 py-1 rounded bg-slate-200" onClick={() => { const f = { ...filters, page: filters.page + 1 }; setFilters(f); fetchIssues(f) }}>Next</button>
              <span className="text-sm self-center">Page {filters.page}</span>
            </div>
          </div>
        </div>

        {message ? <div className="rounded bg-slate-800 text-white px-3 py-2 text-sm">{message}</div> : null}
      </div>
    </div>
  )
}

export default App
