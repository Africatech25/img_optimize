import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Trash2, Pencil } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

function countryFlag(code) {
  if (!code || code.length !== 2) return null
  return String.fromCodePoint(...[...code.toUpperCase()].map((c) => 127397 + c.charCodeAt(0)))
}

function attributionLabel(u) {
  return u.signup_utm_source || u.signup_referrer_domain || null
}

export default function AdminUsers() {
  const { authFetch, user: currentUser } = useAuth()
  const [users, setUsers] = useState([])
  const [query, setQuery] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  const loadUsers = useCallback(async (q) => {
    setIsLoading(true)
    setError('')
    try {
      const params = q ? `?q=${encodeURIComponent(q)}` : ''
      const res = await authFetch(`/api/admin/users${params}`)
      if (!res.ok) throw new Error('Erreur de chargement')
      setUsers(await res.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }, [authFetch])

  useEffect(() => {
    const timeout = setTimeout(() => loadUsers(query), 300)
    return () => clearTimeout(timeout)
  }, [query, loadUsers])

  const handleDelete = async (userToDelete) => {
    if (!window.confirm(`Supprimer le compte ${userToDelete.email} ?`)) return
    try {
      const res = await authFetch(`/api/admin/users/${userToDelete.id}`, { method: 'DELETE' })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'Suppression impossible')
      }
      setUsers((prev) => prev.filter((u) => u.id !== userToDelete.id))
    } catch (err) {
      alert(err.message)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">Utilisateurs</h1>
          <p className="text-sm text-slate-400">{users.length} compte{users.length > 1 ? 's' : ''}</p>
        </div>
        <Link
          to="/admin/users/new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-violet-600 to-cyan-600 text-white text-sm font-semibold rounded-xl hover:scale-105 transition-all"
        >
          <Plus className="w-4 h-4" />
          Nouvel utilisateur
        </Link>
      </div>

      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Rechercher par email ou nom..."
        className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
      />

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-left text-xs text-slate-500 uppercase tracking-wider">
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Nom</th>
              <th className="px-4 py-3">Rôle</th>
              <th className="px-4 py-3">Provenance</th>
              <th className="px-4 py-3">Jobs</th>
              <th className="px-4 py-3">Inscrit le</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={7} className="px-4 py-6 text-center text-slate-500">Chargement...</td></tr>
            ) : users.length === 0 ? (
              <tr><td colSpan={7} className="px-4 py-6 text-center text-slate-500">Aucun utilisateur</td></tr>
            ) : (
              users.map((u) => (
                <tr key={u.id} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                  <td className="px-4 py-3 text-white">{u.email}</td>
                  <td className="px-4 py-3 text-slate-400">{u.display_name || '—'}</td>
                  <td className="px-4 py-3">
                    {u.is_superuser ? (
                      <span className="px-2 py-0.5 bg-fuchsia-900/30 text-fuchsia-300 text-xs rounded-full">Superuser</span>
                    ) : u.is_staff ? (
                      <span className="px-2 py-0.5 bg-violet-900/30 text-violet-300 text-xs rounded-full">Staff</span>
                    ) : (
                      <span className="px-2 py-0.5 bg-slate-800 text-slate-400 text-xs rounded-full">Utilisateur</span>
                    )}
                    {!u.is_active && (
                      <span className="ml-1 px-2 py-0.5 bg-red-900/30 text-red-300 text-xs rounded-full">Inactif</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-400">
                    {u.signup_country && <span title={u.signup_country}>{countryFlag(u.signup_country)} </span>}
                    {attributionLabel(u) || (!u.signup_country && '—')}
                  </td>
                  <td className="px-4 py-3 text-slate-400">{u.jobs_count}</td>
                  <td className="px-4 py-3 text-slate-400">
                    {new Date(u.date_joined).toLocaleDateString('fr-FR')}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2 justify-end">
                      <Link to={`/admin/users/${u.id}`} className="p-2 text-slate-400 hover:text-white transition-colors">
                        <Pencil className="w-4 h-4" />
                      </Link>
                      <button
                        onClick={() => handleDelete(u)}
                        disabled={u.id === currentUser?.id}
                        className="p-2 text-slate-400 hover:text-red-400 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                        title={u.id === currentUser?.id ? 'Impossible de supprimer votre propre compte' : 'Supprimer'}
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
