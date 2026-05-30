import { useState } from 'react'
import useSWR from 'swr'

const fetcher = (url) => fetch(url).then((r) => r.json())

export default function Monitors() {
  const { data, error, mutate } = useSWR('http://localhost:8000/monitors/', fetcher)
  const [form, setForm] = useState({ name: '', url: '', selector: '', frequency_seconds: 3600, mode: 'rendered', config: {} })
  const [message, setMessage] = useState('')
  const [triggering, setTriggering] = useState({})

  if (error) return <div className="p-8">Failed to load monitors.</div>
  if (!data) return <div className="p-8">Loading monitors...</div>

  const handleCreate = async () => {
    const payload = {
      name: form.name,
      url: form.url,
      selector: form.selector || null,
      frequency_seconds: Number(form.frequency_seconds) || 3600,
      mode: form.mode,
      config: form.config,
    }
    const response = await fetch('http://localhost:8000/monitors/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const result = await response.json()
    if (response.ok) {
      setMessage('Monitor created successfully.')
      setForm({ name: '', url: '', selector: '', frequency_seconds: 3600, mode: 'rendered', config: {} })
      mutate()
    } else {
      setMessage(result.detail || JSON.stringify(result))
    }
  }

  const handleRun = async (monitorId) => {
    setTriggering((prev) => ({ ...prev, [monitorId]: 'triggered' }))
    await fetch(`http://localhost:8000/monitors/${monitorId}/run`, { method: 'POST' })
    setTriggering((prev) => ({ ...prev, [monitorId]: 'enqueued' }))
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold">Monitors</h1>
            <p className="text-slate-400 mt-2">Create and run website monitors with capture and alerts.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <a href="/" className="rounded-2xl border border-slate-700 px-4 py-3 text-slate-100 hover:bg-slate-800">Dashboard</a>
            <a href="/integrations" className="rounded-2xl border border-slate-700 px-4 py-3 text-slate-100 hover:bg-slate-800">Integrations</a>
            <a href="/rules" className="rounded-2xl border border-slate-700 px-4 py-3 text-slate-100 hover:bg-slate-800">AI Rules</a>
            <a href="/alerts" className="rounded-2xl border border-slate-700 px-4 py-3 text-slate-100 hover:bg-slate-800">Alerts</a>
            <a href="/snapshots" className="rounded-2xl border border-slate-700 px-4 py-3 text-slate-100 hover:bg-slate-800">Snapshots</a>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
          <section className="space-y-4">
            {data.length === 0 ? (
              <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6">No monitors configured yet.</div>
            ) : (
              data.map((monitor) => (
                <div key={monitor.id} className="bg-slate-900 border border-slate-800 rounded-3xl p-6 mb-4">
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <div className="text-lg font-semibold">{monitor.name}</div>
                      <div className="text-sm text-slate-400">{monitor.url}</div>
                      <div className="text-sm text-slate-500">Mode: {monitor.mode}, Frequency: {monitor.frequency_seconds}s</div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button
                        className="rounded-full bg-sky-500 px-4 py-2 text-slate-950 hover:bg-sky-400"
                        onClick={() => handleRun(monitor.id)}
                      >
                        Run Now
                      </button>
                    </div>
                  </div>
                  <div className="text-sm text-slate-400">{triggering[monitor.id] || 'Ready'}</div>
                </div>
              ))
            )}
          </section>

          <section className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl shadow-slate-950/20">
            <h2 className="text-2xl font-semibold mb-4">Add new monitor</h2>
            <div className="space-y-4">
              <label className="block text-sm text-slate-300">Name</label>
              <input
                className="w-full rounded-2xl border border-slate-700 bg-slate-950 p-3 text-slate-100"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Homepage monitor"
              />
              <label className="block text-sm text-slate-300">URL</label>
              <input
                className="w-full rounded-2xl border border-slate-700 bg-slate-950 p-3 text-slate-100"
                value={form.url}
                onChange={(e) => setForm({ ...form, url: e.target.value })}
                placeholder="https://example.com"
              />
              <label className="block text-sm text-slate-300">CSS selector (optional)</label>
              <input
                className="w-full rounded-2xl border border-slate-700 bg-slate-950 p-3 text-slate-100"
                value={form.selector}
                onChange={(e) => setForm({ ...form, selector: e.target.value })}
                placeholder="#main-content"
              />
              <label className="block text-sm text-slate-300">Frequency (seconds)</label>
              <input
                type="number"
                className="w-full rounded-2xl border border-slate-700 bg-slate-950 p-3 text-slate-100"
                value={form.frequency_seconds}
                onChange={(e) => setForm({ ...form, frequency_seconds: Number(e.target.value) })}
                placeholder="3600"
              />
              <label className="block text-sm text-slate-300">Mode</label>
              <select
                className="w-full rounded-2xl border border-slate-700 bg-slate-950 p-3 text-slate-100"
                value={form.mode}
                onChange={(e) => setForm({ ...form, mode: e.target.value })}
              >
                <option value="rendered">Rendered</option>
                <option value="static">Static</option>
              </select>
              <button
                className="w-full rounded-2xl bg-sky-500 px-4 py-3 text-slate-950 font-semibold hover:bg-sky-400"
                onClick={handleCreate}
              >
                Create Monitor
              </button>
              {message && <p className="text-sm text-slate-300">{message}</p>}
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
