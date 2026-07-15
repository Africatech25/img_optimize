import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Account() {
  const { user, isLoading, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate('/login', { replace: true, state: { from: '/account' } })
    }
  }, [isLoading, isAuthenticated, navigate])

  const handleLogout = async () => {
    await logout()
    navigate('/')
  }

  if (isLoading || !user) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center pt-28">
        <p className="text-slate-400">Chargement...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center px-6 pt-28 pb-16">
      <div className="w-full max-w-md bg-slate-900/50 border border-slate-800 rounded-[2.5rem] p-8 space-y-6">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-violet-600 to-cyan-600 flex items-center justify-center mb-4">
            <span className="text-2xl font-bold text-white">
              {(user.display_name || user.email)[0].toUpperCase()}
            </span>
          </div>
          <h1 className="text-xl font-bold text-white">{user.display_name || 'Mon compte'}</h1>
          <p className="text-sm text-slate-400">{user.email}</p>
        </div>

        <div className="space-y-3 text-sm">
          <div className="flex justify-between px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl">
            <span className="text-slate-400">Membre depuis</span>
            <span className="text-white font-medium">
              {new Date(user.date_joined).toLocaleDateString('fr-FR')}
            </span>
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="w-full py-2.5 rounded-2xl font-semibold bg-slate-800 hover:bg-slate-700 text-white transition-all duration-300"
        >
          Se déconnecter
        </button>
      </div>
    </div>
  )
}
