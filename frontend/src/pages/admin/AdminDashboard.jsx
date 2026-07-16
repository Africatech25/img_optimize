import { useEffect, useState } from 'react'
import { useAuth } from '../../context/AuthContext'

function formatBytes(bytes) {
  if (bytes >= 1_000_000) return `${(bytes / 1_000_000).toFixed(1)} Mo`
  return `${(bytes / 1_000).toFixed(0)} Ko`
}

function countryFlag(code) {
  if (!code || code.length !== 2) return '🌐'
  return String.fromCodePoint(...[...code.toUpperCase()].map((c) => 127397 + c.charCodeAt(0)))
}

const STATUS_LABELS = { pending: 'En attente', processing: 'En cours', completed: 'Terminé', error: 'Erreur' }
const MODE_LABELS = {
  optimize_image: 'Optimiser images',
  optimize_video: 'Optimiser vidéos',
  sign: 'Signer',
  smooth: 'Lisser',
}

export default function AdminDashboard() {
  const { authFetch } = useAuth()
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    authFetch('/api/admin/stats')
      .then((res) => {
        if (!res.ok) throw new Error('Erreur de chargement')
        return res.json()
      })
      .then((data) => { if (!cancelled) setStats(data) })
      .catch((err) => { if (!cancelled) setError(err.message) })
    return () => { cancelled = true }
  }, [authFetch])

  if (error) {
    return <p className="text-red-400">{error}</p>
  }
  if (!stats) {
    return <p className="text-slate-400">Chargement...</p>
  }

  const cards = [
    { label: 'Utilisateurs', value: stats.total_users },
    { label: 'Nouveaux (7j)', value: stats.new_users_7d },
    { label: 'Jobs au total', value: stats.total_jobs },
    { label: 'Jobs (7j)', value: stats.jobs_7d },
    { label: 'Fichiers traités', value: stats.total_files_processed },
    { label: 'Erreurs de traitement', value: stats.total_files_errors },
    { label: 'Réduction moyenne', value: `${stats.reduction_percent}%` },
    { label: 'Espace économisé', value: formatBytes(stats.bytes_saved) },
  ]

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Dashboard</h1>
        <p className="text-sm text-slate-400">Statistiques et analytics de la plateforme</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {cards.map((card) => (
          <div key={card.label} className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5">
            <p className="text-2xl font-bold text-white">{card.value}</p>
            <p className="text-xs text-slate-400 mt-1">{card.label}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
          <h2 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Par statut</h2>
          <div className="space-y-2">
            {Object.entries(stats.status_counts).map(([status, count]) => (
              <div key={status} className="flex justify-between text-sm">
                <span className="text-slate-400">{STATUS_LABELS[status] || status}</span>
                <span className="text-white font-medium">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
          <h2 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Par action</h2>
          <div className="space-y-2">
            {Object.entries(stats.mode_counts).map(([mode, count]) => (
              <div key={mode} className="flex justify-between text-sm">
                <span className="text-slate-400">{MODE_LABELS[mode] || mode}</span>
                <span className="text-white font-medium">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div>
        <h2 className="text-lg font-bold text-white mb-1">Provenance des inscriptions</h2>
        <p className="text-sm text-slate-400 mb-4">
          Captée une seule fois, à l'inscription (pays déduit de l'IP, source via referrer/UTM).
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Pays</h3>
            {Object.keys(stats.country_counts).length === 0 ? (
              <p className="text-sm text-slate-500">Aucune donnée</p>
            ) : (
              <div className="space-y-2">
                {Object.entries(stats.country_counts).map(([code, count]) => (
                  <div key={code} className="flex justify-between text-sm">
                    <span className="text-slate-400">{countryFlag(code)} {code}</span>
                    <span className="text-white font-medium">{count}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Referrers</h3>
            {Object.keys(stats.referrer_counts).length === 0 ? (
              <p className="text-sm text-slate-500">Aucune donnée</p>
            ) : (
              <div className="space-y-2">
                {Object.entries(stats.referrer_counts).map(([domain, count]) => (
                  <div key={domain} className="flex justify-between text-sm">
                    <span className="text-slate-400 truncate">{domain}</span>
                    <span className="text-white font-medium">{count}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Sources UTM</h3>
            {Object.keys(stats.utm_source_counts).length === 0 ? (
              <p className="text-sm text-slate-500">Aucune donnée</p>
            ) : (
              <div className="space-y-2">
                {Object.entries(stats.utm_source_counts).map(([source, count]) => (
                  <div key={source} className="flex justify-between text-sm">
                    <span className="text-slate-400 truncate">{source}</span>
                    <span className="text-white font-medium">{count}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
