import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function RequireStaff({ children }) {
  const { user, isLoading, isAuthenticated } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center pt-28">
        <p className="text-slate-400">Chargement...</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  if (!user?.is_staff) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center pt-28 px-6">
        <div className="max-w-md text-center bg-slate-900/50 border border-slate-800 rounded-[2.5rem] p-8">
          <h1 className="text-xl font-bold text-white mb-2">Accès refusé</h1>
          <p className="text-slate-400 text-sm">
            Cette section est réservée aux administrateurs.
          </p>
        </div>
      </div>
    )
  }

  return children
}
