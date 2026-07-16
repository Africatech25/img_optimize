import { useEffect, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

const EMPTY_FORM = {
  email: '', password: '', display_name: '',
  is_active: true, is_staff: false, is_superuser: false,
}

export default function AdminUserForm() {
  const { authFetch } = useAuth()
  const navigate = useNavigate()
  const { id } = useParams()
  const isEdit = Boolean(id)

  const [form, setForm] = useState(EMPTY_FORM)
  const [isLoading, setIsLoading] = useState(isEdit)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isEdit) return
    let cancelled = false
    authFetch(`/api/admin/users/${id}`)
      .then((res) => {
        if (!res.ok) throw new Error('Utilisateur introuvable')
        return res.json()
      })
      .then((data) => {
        if (cancelled) return
        setForm({
          email: data.email,
          password: '',
          display_name: data.display_name || '',
          is_active: data.is_active,
          is_staff: data.is_staff,
          is_superuser: data.is_superuser,
        })
      })
      .catch((err) => { if (!cancelled) setError(err.message) })
      .finally(() => { if (!cancelled) setIsLoading(false) })
    return () => { cancelled = true }
  }, [id, isEdit, authFetch])

  const updateField = (field, value) => setForm((prev) => ({ ...prev, [field]: value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setIsSubmitting(true)
    try {
      const payload = { ...form }
      if (isEdit && !payload.password) delete payload.password

      const res = await authFetch(isEdit ? `/api/admin/users/${id}` : '/api/admin/users', {
        method: isEdit ? 'PATCH' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json()
      if (!res.ok) {
        const firstError = data.detail || Object.values(data)[0]
        throw new Error(Array.isArray(firstError) ? firstError[0] : (firstError || 'Erreur'))
      }
      navigate('/admin/users')
    } catch (err) {
      setError(err.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return <p className="text-slate-400">Chargement...</p>
  }

  return (
    <div className="max-w-lg space-y-6">
      <div>
        <Link to="/admin/users" className="text-sm text-slate-400 hover:text-white">&larr; Retour aux utilisateurs</Link>
        <h1 className="text-2xl font-bold text-white mt-2">
          {isEdit ? 'Modifier l\'utilisateur' : 'Nouvel utilisateur'}
        </h1>
      </div>

      <form onSubmit={handleSubmit} className="bg-slate-900/50 border border-slate-800 rounded-[2rem] p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Email</label>
          <input
            type="email"
            required
            value={form.email}
            onChange={(e) => updateField('email', e.target.value)}
            className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
            disabled={isSubmitting}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Mot de passe {isEdit && <span className="text-slate-500">(laisser vide pour ne pas changer)</span>}
          </label>
          <input
            type="password"
            required={!isEdit}
            minLength={8}
            value={form.password}
            onChange={(e) => updateField('password', e.target.value)}
            placeholder={isEdit ? '••••••••' : '8 caractères minimum'}
            className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
            disabled={isSubmitting}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Nom affiché</label>
          <input
            type="text"
            value={form.display_name}
            onChange={(e) => updateField('display_name', e.target.value)}
            className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
            disabled={isSubmitting}
          />
        </div>

        <div className="space-y-3 pt-2">
          {[
            { field: 'is_active', label: 'Compte actif' },
            { field: 'is_staff', label: 'Accès administrateur (staff)' },
            { field: 'is_superuser', label: 'Superutilisateur (tous les droits)' },
          ].map(({ field, label }) => (
            <label key={field} className="flex items-center gap-3 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={form[field]}
                onChange={(e) => updateField(field, e.target.checked)}
                className="w-4 h-4 rounded accent-violet-600"
                disabled={isSubmitting}
              />
              {label}
            </label>
          ))}
        </div>

        {error && (
          <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-2">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className={`w-full py-2.5 rounded-2xl font-semibold transition-all duration-300 ${
            isSubmitting
              ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
              : 'bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-500 hover:to-cyan-500 text-white'
          }`}
        >
          {isSubmitting ? 'Enregistrement...' : isEdit ? 'Enregistrer les modifications' : 'Créer l\'utilisateur'}
        </button>
      </form>
    </div>
  )
}
