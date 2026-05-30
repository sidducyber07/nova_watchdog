import useSWR from 'swr'

const fetcher = (url) => fetch(url).then((r) => r.json())

export default function Home() {
  const { data, error } = useSWR('http://localhost:8000/monitors/', fetcher)

  if (error) return <div className="p-8">Failed to load</div>
  if (!data) return <div className="p-8">Loading...</div>

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="flex flex-col gap-6 max-w-6xl mx-auto">
        <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-4xl font-semibold">Nova Watchdog</h1>
            <p className="text-gray-400 mt-2">Monitor websites, capture snapshots, and manage integrations with AI-driven rules.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <a href="/monitors" className="rounded-2xl bg-sky-500 px-4 py-3 text-slate-950 font-semibold hover:bg-sky-400">Monitors</a>
            <a href="/integrations" className="rounded-2xl border border-slate-700 px-4 py-3 text-white hover:bg-slate-800">Integrations</a>
            <a href="/rules" className="rounded-2xl border border-slate-700 px-4 py-3 text-white hover:bg-slate-800">AI Rules</a>
            <a href="/alerts" className="rounded-2xl border border-slate-700 px-4 py-3 text-white hover:bg-slate-800">Alerts</a>
            <a href="/snapshots" className="rounded-2xl border border-slate-700 px-4 py-3 text-white hover:bg-slate-800">Snapshots</a>
          </div>
        </header>

        <section className="rounded-3xl bg-slate-800 p-6 shadow-lg shadow-slate-950/20">
          <h2 className="text-2xl font-semibold mb-4">Active monitors</h2>
          <div className="grid gap-4">
            {data.map((m) => (
              <div key={m.id} className="p-4 bg-slate-900 rounded-3xl border border-slate-700">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="text-lg font-medium">{m.name}</div>
                    <div className="text-sm text-slate-400">{m.url}</div>
                  </div>
                  <div className="text-sm text-slate-400">{m.last_status ?? 'No recent status'}</div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
