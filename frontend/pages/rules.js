import { useState } from 'react'
import useSWR from 'swr'

const fetcher = (url) => fetch(url).then((r) => r.json())

export default function Rules() {
  const { data, error, mutate } = useSWR('http://localhost:8000/rules/', fetcher)
  const [form, setForm] = useState({ name: '', rule_text: '', monitor_id: '', is_active: true })
  const [message, setMessage] = useState('')

  if (error) return <div className="p-8">Failed to load AI rules.</div>
  if (!data) return <div className="p-8">Loading rules...</div>

  const handleCreate = async () => {
    const payload = {
      name: form.name,
      rule_text: form.rule_text,
      monitor_id: form.monitor_id || null,
      is_active: form.is_active,
    }
    const response = await fetch('http://localhost:8000/rules/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const result = await response.json()
    if (response.ok) {
      setMessage('Rule created successfully.')
      setForm({ name: '', rule_text: '', monitor_id: '', is_active: true })
      mutate()
    } else {
      setMessage(result.detail || JSON.stringify(result))
    }
  }

  const handleToggle = async (rule) => {
    const response = await fetch(`http://localhost:8000/rules/${rule.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_active: !rule.is_active }),
    })
    const result = await response.json()
    if (response.ok) {
      mutate()
    } else {
      setMessage(result.detail || JSON.stringify(result))
    }
  }

  const handleDelete = async (id) => {
    const response = await fetch(`http://localhost:8000/rules/${id}`, { method: 'DELETE' })
    if (response.ok) {
      setMessage('Rule deleted successfully.')
      mutate()
    } else {
      const result = await response.json()
      setMessage(result.detail || JSON.stringify(result))
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold">AI Rules Engine</h1>
            <p className="text-slate-400 mt-2">Create rules to control notifications, ignore noise, and trigger only meaningful alerts.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <a href="/" className="rounded-2xl border border-slate-700 px-4 py-3 text-slate-100 hover:bg-slate-800">Dashboard</a>
            <a href="/integrations" className="rounded-2xl border border-slate-700 px-4 py-3 text-slate-100 hover:bg-slate-800">Integrations</a>
            <a href="/alerts" className="rounded-2xl border border-slate-700 px-4 py-3 text-slate-100 hover:bg-slate-800">Alerts</a>
            <a href="/snapshots" className="rounded-2xl border border-slate-700 px-4 py-3 text-slate-100 hover:bg-slate-800">Snapshots</a>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
          <section className="space-y-4">
            {data.length === 0 ? (
              <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6">No rules configured yet.</div>
            ) : (
              data.map((rule) => (
                <div key={rule.id} className="bg-slate-900 border border-slate-800 rounded-3xl p-6 mb-4">
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <div className="text-lg font-semibold">{rule.name}</div>
                      <div className="text-sm text-slate-500">{rule.monitor_id ? `Monitor: ${rule.monitor_id}` : 'Global rule'}</div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button
                        className={`rounded-full px-4 py-2 text-sm ${rule.is_active ? 'bg-emerald-500 text-slate-950' : 'bg-slate-700 text-slate-300'}`}
                        onClick={() => handleToggle(rule)}
                      >
                        {rule.is_active ? 'Disable' : 'Enable'}
                      </button>
                      <button
                        className="rounded-full bg-rose-500 px-4 py-2 text-sm text-slate-100 hover:bg-rose-400"
                        onClick={() => handleDelete(rule.id)}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  <p className="mt-3 text-slate-300">{rule.rule_text}</p>
                </div>
              ))
            )}
          </section>

          <section className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl shadow-slate-950/20">
            <h2 className="text-2xl font-semibold mb-4">Add new AI rule</h2>
            <div className="space-y-4">
              <label className="block text-sm text-slate-300">Rule name</label>
              <input
                className="w-full rounded-2xl border border-slate-700 bg-slate-950 p-3 text-slate-100"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Price change only"
              />
              <label className="block text-sm text-slate-300">Rule text</label>
              <textarea
                rows={4}
                className="w-full rounded-2xl border border-slate-700 bg-slate-950 p-3 text-slate-100"
                value={form.rule_text}
                onChange={(e) => setForm({ ...form, rule_text: e.target.value })}
                placeholder="Alert only when price changes"
              />
              <label className="block text-sm text-slate-300">Monitor ID (optional)</label>
              <input
                className="w-full rounded-2xl border border-slate-700 bg-slate-950 p-3 text-slate-100"
                value={form.monitor_id}
                onChange={(e) => setForm({ ...form, monitor_id: e.target.value })}
                placeholder="Specific monitor ID"
              />
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                />
                <span className="text-sm text-slate-300">Active</span>
              </div>
              <button
                className="w-full rounded-2xl bg-sky-500 px-4 py-3 text-slate-950 font-semibold hover:bg-sky-400"
                onClick={handleCreate}
              >
                Create Rule
              </button>
              {message && <p className="text-sm text-slate-300">{message}</p>}
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
