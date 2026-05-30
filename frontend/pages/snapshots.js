import useSWR from 'swr'

const fetcher = (url) => fetch(url).then((r) => r.json())

export default function Snapshots() {
  const { data, error } = useSWR('http://localhost:8000/snapshots/', fetcher)

  if (error) return <div className="p-8">Failed to load snapshots.</div>
  if (!data) return <div className="p-8">Loading snapshots...</div>

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold">Snapshots</h1>
            <p className="text-slate-400 mt-2">Browse captured snapshots and change summaries.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <a href="/" className="rounded-2xl border border-slate-700 px-4 py-3 text-slate-100 hover:bg-slate-800">Dashboard</a>
            <a href="/monitors" className="rounded-2xl border border-slate-700 px-4 py-3 text-slate-100 hover:bg-slate-800">Monitors</a>
            <a href="/integrations" className="rounded-2xl border border-slate-700 px-4 py-3 text-slate-100 hover:bg-slate-800">Integrations</a>
            <a href="/rules" className="rounded-2xl border border-slate-700 px-4 py-3 text-slate-100 hover:bg-slate-800">AI Rules</a>
            <a href="/alerts" className="rounded-2xl border border-slate-700 px-4 py-3 text-slate-100 hover:bg-slate-800">Alerts</a>
          </div>
        </div>

        <div className="space-y-4">
          {data.length === 0 ? (
            <div className="rounded-3xl bg-slate-900 border border-slate-800 p-6">No snapshots available yet.</div>
          ) : (
            data.map((snapshot) => (
              <div key={snapshot.id} className="rounded-3xl bg-slate-900 border border-slate-800 p-6">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="text-lg font-semibold">Snapshot {snapshot.id.slice(0, 8)}</div>
                    <div className="text-sm text-slate-400">Monitor: {snapshot.monitor_id}</div>
                  </div>
                  <div className="text-sm text-slate-400">{snapshot.run_at || 'Unknown run time'}</div>
                </div>
                <div className="mt-4 text-slate-300">Status: {snapshot.status}</div>
                <div className="mt-3 text-sm text-slate-400">Diff summary: {snapshot.diff_summary ? JSON.stringify(snapshot.diff_summary) : 'No diff data'}</div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
