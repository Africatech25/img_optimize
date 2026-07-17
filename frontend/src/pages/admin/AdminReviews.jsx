import { useEffect, useState, useCallback } from 'react'
import { Check, X, Trash2 } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

const STATUS_OPTIONS = ['', 'pending', 'approved', 'rejected']

const STATUS_BADGE = {
  pending: 'bg-slate-800 text-slate-400',
  approved: 'bg-emerald-900/30 text-emerald-300',
  rejected: 'bg-red-900/30 text-red-300',
}

export default function AdminReviews() {
  const { authFetch } = useAuth()
  const [reviews, setReviews] = useState([])
  const [status, setStatus] = useState('pending')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const loadReviews = useCallback(async () => {
    setIsLoading(true)
    setError('')
    try {
      const params = status ? `?status=${status}` : ''
      const res = await authFetch(`/api/admin/reviews${params}`)
      if (!res.ok) throw new Error('Erreur de chargement')
      setReviews(await res.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }, [authFetch, status])

  useEffect(() => { loadReviews() }, [loadReviews])

  const updateStatus = async (review, newStatus) => {
    try {
      const res = await authFetch(`/api/admin/reviews/${review.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      })
      if (!res.ok) throw new Error('Mise à jour impossible')
      setReviews((prev) => prev.filter((r) => r.id !== review.id))
    } catch (err) {
      alert(err.message)
    }
  }

  const handleDelete = async (review) => {
    if (!window.confirm(`Supprimer l'avis de ${review.user_email} ?`)) return
    try {
      const res = await authFetch(`/api/admin/reviews/${review.id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Suppression impossible')
      setReviews((prev) => prev.filter((r) => r.id !== review.id))
    } catch (err) {
      alert(err.message)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Avis</h1>
        <p className="text-sm text-slate-400">{reviews.length} avis</p>
      </div>

      <select
        value={status}
        onChange={(e) => setStatus(e.target.value)}
        className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
      >
        {STATUS_OPTIONS.map((s) => (
          <option key={s} value={s}>{s || 'Tous les statuts'}</option>
        ))}
      </select>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-left text-xs text-slate-500 uppercase tracking-wider">
              <th className="px-4 py-3">Utilisateur</th>
              <th className="px-4 py-3">Note</th>
              <th className="px-4 py-3">Texte</th>
              <th className="px-4 py-3">Statut</th>
              <th className="px-4 py-3">Créé le</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={6} className="px-4 py-6 text-center text-slate-500">Chargement...</td></tr>
            ) : reviews.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-6 text-center text-slate-500">Aucun avis</td></tr>
            ) : (
              reviews.map((review) => (
                <tr key={review.id} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                  <td className="px-4 py-3 text-white">{review.display_name || review.user_email}</td>
                  <td className="px-4 py-3 text-slate-400">{review.rating}/5</td>
                  <td className="px-4 py-3 text-slate-400 max-w-xs truncate" title={review.text}>{review.text}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 text-xs rounded-full ${STATUS_BADGE[review.status] || 'bg-slate-800 text-slate-400'}`}>
                      {review.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-400">
                    {new Date(review.created_at).toLocaleDateString('fr-FR')}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2 justify-end">
                      <button
                        onClick={() => updateStatus(review, 'approved')}
                        className="p-2 text-slate-400 hover:text-emerald-400 transition-colors"
                        title="Approuver"
                      >
                        <Check className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => updateStatus(review, 'rejected')}
                        className="p-2 text-slate-400 hover:text-orange-400 transition-colors"
                        title="Rejeter"
                      >
                        <X className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(review)}
                        className="p-2 text-slate-400 hover:text-red-400 transition-colors"
                        title="Supprimer"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
