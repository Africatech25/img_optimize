import { useEffect, useState, useCallback } from 'react'
import { Trash2 } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

const STATUS_OPTIONS = ['', 'pending', 'processing', 'completed', 'error']
const MODE_OPTIONS = ['', 'optimize_image', 'optimize_video', 'sign', 'smooth']

const STATUS_BADGE = {
  completed: 'bg-emerald-900/30 text-emerald-300',
  error: 'bg-red-900/30 text-red-300',
  processing: 'bg-violet-900/30 text-violet-300',
  pending: 'bg-slate-800 text-slate-400',
}

function formatBytes(bytes) {
  if (!bytes) return '—'
  if (bytes >= 1_000_000) return `${(bytes / 1_000_000).toFixed(1)} Mo`
  return `${(bytes / 1_000).toFixed(0)} Ko`
}

export default function AdminJobs() {
  const { authFetch } = useAuth()
  const [jobs, setJobs] = useState([])
  const [status, setStatus] = useState('')
  const [mode, setMode] = useState('')
  const [query, setQuery] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const loadJobs = useCallback(async () => {
    setIsLoading(true)
    setError('')
    try {
      const params = new URLSearchParams()
      if (status) params.set('status', status)
      if (mode) params.set('mode', mode)
      if (query) params.set('q', query)
      const res = await authFetch(`/api/admin/jobs?${params.toString()}`)
      if (!res.ok) throw new Error('Erreur de chargement')
      setJobs(await res.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }, [authFetch, status, mode, query])

  useEffect(() => {
    const timeout = setTimeout(loadJobs, 300)
    return () => clearTimeout(timeout)
  }, [loadJobs])

  const handleDelete = async (job) => {
    if (!window.confirm(`Supprimer ce job (${job.job_id.slice(0, 8)}) et ses fichiers ?`)) return
    try {
      const res = await authFetch(`/api/admin/jobs/${job.job_id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Suppression impossible')
      setJobs((prev) => prev.filter((j) => j.job_id !== job.job_id))
    } catch (err) {
      alert(err.message)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Jobs</h1>
        <p className="text-sm text-slate-400">{jobs.length} job{jobs.length > 1 ? 's' : ''}</p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Rechercher par email ou job_id..."
          className="flex-1 px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
        />
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
        >
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>{s || 'Tous les statuts'}</option>
          ))}
        </select>
        <select
          value={mode}
          onChange={(e) => setMode(e.target.value)}
          className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
        >
          {MODE_OPTIONS.map((m) => (
            <option key={m} value={m}>{m || 'Toutes les actions'}</option>
          ))}
        </select>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-left text-xs text-slate-500 uppercase tracking-wider">
              <th className="px-4 py-3">Job</th>
              <th className="px-4 py-3">Utilisateur</th>
              <th className="px-4 py-3">Action</th>
              <th className="px-4 py-3">Statut</th>
              <th className="px-4 py-3">Fichiers</th>
              <th className="px-4 py-3">Réduction</th>
              <th className="px-4 py-3">Créé le</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={8} className="px-4 py-6 text-center text-slate-500">Chargement...</td></tr>
            ) : jobs.length === 0 ? (
              <tr><td colSpan={8} className="px-4 py-6 text-center text-slate-500">Aucun job</td></tr>
            ) : (
              jobs.map((job) => {
                const before = job.stats?.total_before || 0
                const after = job.stats?.total_after || 0
                const reduction = before > 0 ? Math.round((1 - after / before) * 100) : null
                return (
                  <tr key={job.job_id} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-white font-mono text-xs" title={job.job_id}>
                      {job.job_id.slice(0, 8)}
                    </td>
                    <td className="px-4 py-3 text-slate-400">{job.user_email || 'Anonyme'}</td>
                    <td className="px-4 py-3 text-slate-400">{job.mode}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 text-xs rounded-full ${STATUS_BADGE[job.status] || 'bg-slate-800 text-slate-400'}`}>
                        {job.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-400">{job.processed_files}/{job.total_files}</td>
                    <td className="px-4 py-3 text-slate-400">
                      {reduction !== null ? `${reduction}% (${formatBytes(before)} → ${formatBytes(after)})` : '—'}
                    </td>
                    <td className="px-4 py-3 text-slate-400">
                      {new Date(job.created_at).toLocaleString('fr-FR')}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleDelete(job)}
                        className="p-2 text-slate-400 hover:text-red-400 transition-colors"
                        title="Supprimer"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
