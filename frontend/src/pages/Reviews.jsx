import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Star } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const API_BASE = import.meta.env.VITE_API_URL || ''

function StarRating({ value, onChange, readOnly = false }) {
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          disabled={readOnly}
          onClick={() => onChange && onChange(n)}
          className={readOnly ? 'cursor-default' : 'cursor-pointer'}
        >
          <Star
            className={`w-5 h-5 ${n <= value ? 'fill-violet-500 text-violet-500' : 'text-slate-600'}`}
          />
        </button>
      ))}
    </div>
  )
}

function ReviewForm() {
  const { authFetch } = useAuth()
  const [rating, setRating] = useState(0)
  const [text, setText] = useState('')
  const [status, setStatus] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function loadMine() {
      try {
        const res = await authFetch('/api/reviews/me')
        if (res.status === 404) return
        if (!res.ok) throw new Error('Erreur de chargement')
        const data = await res.json()
        if (!cancelled) {
          setRating(data.rating)
          setText(data.text)
          setStatus(data.status)
        }
      } catch {
        // best effort : formulaire vide si le chargement échoue
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }
    loadMine()
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (rating < 1) {
      setError('Choisissez une note de 1 à 5 étoiles.')
      return
    }
    setIsSaving(true)
    try {
      const res = await authFetch('/api/reviews/me', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating, text }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.text?.[0] || data.rating?.[0] || 'Erreur lors de l\'envoi')
      setStatus(data.status)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return <p className="text-slate-400 text-center">Chargement...</p>
  }

  return (
    <form onSubmit={handleSubmit} className="glass-card gradient-border p-8 rounded-[2rem] space-y-4">
      <h2 className="text-xl font-bold text-white">
        {status ? 'Modifier mon avis' : 'Laisser un avis'}
      </h2>
      <StarRating value={rating} onChange={setRating} />
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        maxLength={500}
        rows={4}
        placeholder="Qu'avez-vous pensé de l'outil ?"
        className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
      />
      {error && <p className="text-red-400 text-sm">{error}</p>}
      {status && (
        <p className="text-sm text-slate-400">
          Statut actuel : <span className="font-semibold">{status === 'pending' ? 'en attente de validation' : status === 'approved' ? 'publié' : 'non retenu'}</span>
        </p>
      )}
      <button
        type="submit"
        disabled={isSaving}
        className="px-6 py-2.5 bg-white text-black font-bold rounded-xl hover:scale-105 transition-all disabled:opacity-50"
      >
        {isSaving ? 'Envoi...' : status ? 'Mettre à jour' : 'Envoyer mon avis'}
      </button>
    </form>
  )
}

export default function Reviews() {
  const { isAuthenticated, isLoading: authLoading } = useAuth()
  const [reviews, setReviews] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function loadPublic() {
      try {
        const res = await fetch(`${API_BASE}/api/reviews/public`)
        if (res.ok) setReviews(await res.json())
      } finally {
        setIsLoading(false)
      }
    }
    loadPublic()
  }, [])

  return (
    <div className="min-h-screen bg-[#050505] pt-40 pb-20 px-6">
      <div className="max-w-3xl mx-auto space-y-16">
        <div className="text-center">
          <h1 className="text-4xl lg:text-6xl font-bold text-white mb-4">
            Avis des <span className="text-gradient">utilisateurs</span>
          </h1>
          <p className="text-slate-400">Ce que la communauté pense d'ImgOpt.</p>
        </div>

        {!authLoading && (
          isAuthenticated ? (
            <ReviewForm />
          ) : (
            <div className="glass-card p-8 rounded-[2rem] text-center space-y-4">
              <p className="text-slate-400">Connectez-vous pour laisser votre avis.</p>
              <Link
                to="/login"
                state={{ from: '/avis' }}
                className="inline-block px-6 py-2.5 bg-white text-black font-bold rounded-xl hover:scale-105 transition-all"
              >
                Se connecter
              </Link>
            </div>
          )
        )}

        <div className="space-y-6">
          {isLoading ? (
            <p className="text-slate-400 text-center">Chargement des avis...</p>
          ) : reviews.length === 0 ? (
            <p className="text-slate-400 text-center">Aucun avis publié pour l'instant.</p>
          ) : (
            reviews.map((review, idx) => (
              <div key={idx} className="glass-card p-6 rounded-[1.5rem] border border-white/5">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-white font-bold">{review.display_name}</span>
                  <StarRating value={review.rating} readOnly />
                </div>
                <p className="text-slate-400 italic font-light">"{review.text}"</p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
