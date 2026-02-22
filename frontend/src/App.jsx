import { useEffect, useState } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const CATEGORIES = [
  '',
  'Road & Infrastructure',
  'Water & Drainage',
  'Sanitation',
  'Electricity',
  'Public Safety',
]

const URGENCIES = ['', 'Low', 'Medium', 'High']

function formatDate(value) {
  try {
    const d = new Date(value)
    return d.toLocaleString()
  } catch {
    return String(value)
  }
}

function truncate(text, max = 80) {
  if (!text) return ''
  return text.length > max ? text.slice(0, max - 1) + '…' : text
}

function App() {
  const [tab, setTab] = useState('citizen')

  // Citizen UI state
  const [complaint, setComplaint] = useState('')
  const [predictLoading, setPredictLoading] = useState(false)
  const [predictError, setPredictError] = useState('')
  const [predictResult, setPredictResult] = useState(null)

  // Authority dashboard state
  const [filterCategory, setFilterCategory] = useState('')
  const [filterUrgency, setFilterUrgency] = useState('')
  const [listLoading, setListLoading] = useState(false)
  const [listError, setListError] = useState('')
  const [complaints, setComplaints] = useState([])

  async function handlePredict(e) {
    e.preventDefault()
    setPredictError('')
    setPredictResult(null)
    setPredictLoading(true)

    try {
      const resp = await fetch(`${API_BASE_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ complaint }),
      })

      if (!resp.ok) {
        const text = await resp.text()
        throw new Error(text || `Request failed (${resp.status})`)
      }

      const data = await resp.json()
      setPredictResult(data)
    } catch (err) {
      setPredictError(err?.message || 'Failed to call API')
    } finally {
      setPredictLoading(false)
    }
  }

  async function fetchComplaints(nextCategory = filterCategory, nextUrgency = filterUrgency) {
    setListError('')
    setListLoading(true)
    try {
      const qs = new URLSearchParams()
      if (nextCategory) qs.set('category', nextCategory)
      if (nextUrgency) qs.set('urgency', nextUrgency)
      const resp = await fetch(`${API_BASE_URL}/complaints?${qs.toString()}`)
      if (!resp.ok) {
        const text = await resp.text()
        throw new Error(text || `Request failed (${resp.status})`)
      }
      const data = await resp.json()
      setComplaints(data.items || [])
    } catch (err) {
      setListError(err?.message || 'Failed to load complaints')
    } finally {
      setListLoading(false)
    }
  }

  // Load authority list when switching to dashboard
  useEffect(() => {
    if (tab === 'authority') fetchComplaints()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab])

  return (
    <div className="app">
      <div className="header">
        <div className="title">
          <h1>Real-Time Smart City Issue Detection</h1>
          <p>ML category + ML urgency + AI-assisted acknowledgment/suggestions</p>
        </div>
        <div className="tabs">
          <button
            className={`tabBtn ${tab === 'citizen' ? 'tabBtnActive' : ''}`}
            onClick={() => setTab('citizen')}
            type="button"
          >
            Citizen
          </button>
          <button
            className={`tabBtn ${tab === 'authority' ? 'tabBtnActive' : ''}`}
            onClick={() => setTab('authority')}
            type="button"
          >
            Authority Dashboard
          </button>
        </div>
      </div>

      {tab === 'citizen' ? (
        <div className="grid">
          <div className="panel">
            <h2>Submit a complaint</h2>
            <form onSubmit={handlePredict}>
              <textarea
                className="textarea"
                value={complaint}
                onChange={(e) => setComplaint(e.target.value)}
                placeholder="Describe the issue (e.g., 'Water main leak flooding the street near 5th Ave')"
              />
              <div className="row">
                <button className="btnPrimary" disabled={predictLoading || complaint.trim().length < 3}>
                  {predictLoading ? 'Analyzing…' : 'Submit'}
                </button>
                <span className="muted">API: {API_BASE_URL}</span>
              </div>
              {predictError ? <p className="muted">Error: {predictError}</p> : null}
            </form>
          </div>

          <div className="panel">
            <h2>Result</h2>
            {!predictResult ? (
              <p className="muted">Submit a complaint to see the predicted category, urgency, and AI response.</p>
            ) : (
              <>
                <div className="pillRow">
                  <span className="pill">Category: {predictResult.category}</span>
                  <span className="pill">Urgency: {predictResult.urgency}</span>
                </div>
                <div className="monoBox">
                  <strong>Acknowledgment</strong>
                  {'\n'}
                  {predictResult.acknowledgment}
                  {'\n\n'}
                  <strong>Suggestion</strong>
                  {'\n'}
                  {predictResult.suggestion}
                </div>
              </>
            )}
          </div>
        </div>
      ) : (
        <div className="panel">
          <h2>Submitted complaints</h2>

          <div className="controls">
            <span className="muted">Filter:</span>
            <select
              value={filterCategory}
              onChange={(e) => {
                const v = e.target.value
                setFilterCategory(v)
                fetchComplaints(v, filterUrgency)
              }}
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c || 'All categories'}
                </option>
              ))}
            </select>
            <select
              value={filterUrgency}
              onChange={(e) => {
                const v = e.target.value
                setFilterUrgency(v)
                fetchComplaints(filterCategory, v)
              }}
            >
              {URGENCIES.map((u) => (
                <option key={u} value={u}>
                  {u || 'All urgencies'}
                </option>
              ))}
            </select>
            <button className="btnPrimary" type="button" onClick={() => fetchComplaints()}>
              Refresh
            </button>
            <span className="muted">API: {API_BASE_URL}</span>
          </div>

          {listError ? <p className="muted">Error: {listError}</p> : null}
          {listLoading ? (
            <p className="muted">Loading…</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Created</th>
                  <th>Complaint</th>
                  <th>Category</th>
                  <th>Urgency</th>
                </tr>
              </thead>
              <tbody>
                {complaints.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="small">
                      No complaints yet.
                    </td>
                  </tr>
                ) : (
                  complaints.map((c) => (
                    <tr key={c.id}>
                      <td className="small">{formatDate(c.created_at)}</td>
                      <td title={c.text}>{truncate(c.text, 110)}</td>
                      <td>{c.category}</td>
                      <td>{c.urgency}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}

export default App
