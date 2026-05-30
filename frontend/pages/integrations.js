import { useState } from 'react'
import useSWR from 'swr'

const fetcher = (url) => fetch(url).then((r) => r.json())

const typeToFields = {
  telegram: ['bot_token', 'chat_id'],
  discord: ['webhook_url'],
  slack: ['webhook_url'],
  webhook: ['url'],
  email: ['host', 'port', 'username', 'password', 'sender', 'recipient'],
}

export default function Integrations() {
  const { data, error, mutate } = useSWR('http://localhost:8000/integrations/', fetcher)
  const [form, setForm] = useState({ type: 'telegram', name: '', config: {} })
  const [message, setMessage] = useState('')
  const [testing, setTesting] = useState({})
  const [health, setHealth] = useState({})

  if (error) return <div className="p-8">Failed to load integrations.</div>
  if (!data) return <div className="p-8">Loading integrations...</div>

  const handleField = (key, value) => {
    setForm((current) => ({
      ...current,
      config: {
        ...current.config,
        [key]: value,
      },
    }))
  }

  const handleCreate = async () => {
    const response = await fetch('http://localhost:8000/integrations/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    })
    const result = await response.json()
    if (response.ok) {
      setMessage('Integration created successfully.')
      setForm({ type: form.type, name: '', config: {} })
      mutate()
    } else {
      setMessage(result.detail || JSON.stringify(result))
    }
  }

  const handleTest = async (id) => {
    setTesting((s) => ({ ...s, [id]: 'running' }))
    const response = await fetch(`http://localhost:8000/integrations/${id}/test`, {
      method: 'POST',
    })
    const result = await response.json()
    if (response.ok) {
      setTesting((s) => ({ ...s, [id]: `ok: ${JSON.stringify(result.details)}` }))
    } else {
      setTesting((s) => ({ ...s, [id]: `failed: ${result.detail || JSON.stringify(result)}` }))
    }
  }

  const handleHealth = async (id) => {
    setHealth((s) => ({ ...s, [id]: 'checking' }))
    const response = await fetch(`http://localhost:8000/integrations/${id}/health`)
    const result = await response.json()
    if (response.ok) {
      setHealth((s) => ({ ...s, [id]: `ok: ${result.last_success || 'no recent successes'}` }))
    } else {
      setHealth((s) => ({ ...s, [id]: `failed: ${result.detail || JSON.stringify(result)}` }))
    }
  }

  const handleDelete = async (id) => {
    const response = await fetch(`http://localhost:8000/integrations/${id}`, { method: 'DELETE' })
    if (response.ok) {
      setMessage('Integration deleted successfully.')
      mutate()
    } else {
      const result = await response.json()
      setMessage(result.detail || JSON.stringify(result))
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold">Integration Management</h1>
            <p className="text-slate-400 mt-2">Configure Telegram, Discord, Slack, Webhooks, or SMTP providers.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <a href="/" className="rounded-2xl border border-slate-700 px-4 py-3 text-slate-100 hover:bg-slate-800">Dashboard</a>
            <a href="/rules" className="rounded-2xl border border-slate-700 px-4 py-3 text-slate-100 hover:bg-slate-800">AI Rules</a>
            <a href="/alerts" className="rounded-2xl border border-slate-700 px-4 py-3 text-slate-100 hover:bg-slate-800">Alerts</a>
            <a href="/snapshots" className="rounded-2xl border border-slate-700 px-4 py-3 text-slate-100 hover:bg-slate-800">Snapshots</a>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
          <div className="space-y-6">
            <section className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl shadow-slate-950/20">
              <h2 className="text-2xl font-semibold mb-4">Active integrations</h2>
              {data.length === 0 ? (
                <p className="text-slate-400">No integrations configured yet.</p>
              ) : (
                <div className="space-y-4">
                  {data.map((integration) => (
                    <div key={integration.id} className="p-4 bg-slate-800 rounded-3xl border border-slate-700">
                      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                        <div>
                          <div className="text-lg font-semibold">{integration.name}</div>
                          <div className="text-sm text-slate-500">{integration.type}</div>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <button
                            className="rounded-full bg-cyan-500 px-4 py-2 text-slate-950 hover:bg-cyan-400"
                            onClick={() => handleTest(integration.id)}
                          >
                            Test
                          </button>
                          <button
                            className="rounded-full bg-slate-700 px-4 py-2 text-slate-100 hover:bg-slate-600"
                            onClick={() => handleHealth(integration.id)}
                          >
                            Health
                          </button>
                          <button
                            className="rounded-full bg-rose-500 px-4 py-2 text-slate-100 hover:bg-rose-400"
                            onClick={() => handleDelete(integration.id)}
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                      <div className="mt-3 text-sm text-slate-400 break-words">
                        {integration.config ? JSON.stringify(integration.config, null, 2) : 'No config'}
                      </div>
                      <div className="mt-3 flex flex-col gap-2 text-sm text-slate-300">
                        {testing[integration.id] && <span>Test: {testing[integration.id]}</span>}
                        {health[integration.id] && <span>Health: {health[integration.id]}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>

          <section className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl shadow-slate-950/20">
            <h2 className="text-2xl font-semibold mb-4">Add new integration</h2>
            <div className="space-y-4">
              <label className="block text-sm text-slate-300">Type</label>
              <select
                className="w-full rounded-2xl border border-slate-700 bg-slate-950 p-3 text-slate-100"
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value, config: {} })}
              >
                {Object.keys(typeToFields).map((type) => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
              <label className="block text-sm text-slate-300">Name</label>
              <input
                className="w-full rounded-2xl border border-slate-700 bg-slate-950 p-3 text-slate-100"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="My Telegram Bot"
              />
              <div className="space-y-3">
                {typeToFields[form.type].map((field) => (
                  <div key={field}>
                    <label className="block text-sm text-slate-300">{field}</label>
                    <input
                      className="w-full rounded-2xl border border-slate-700 bg-slate-950 p-3 text-slate-100"
                      value={form.config[field] || ''}
                      onChange={(e) => handleField(field, e.target.value)}
                      placeholder={field}
                    />
                  </div>
                ))}
              </div>
              <button
                className="w-full rounded-2xl bg-sky-500 px-4 py-3 text-slate-950 font-semibold hover:bg-sky-400"
                onClick={handleCreate}
              >
                Create Integration
              </button>
              {message && <p className="text-sm text-slate-300">{message}</p>}
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
