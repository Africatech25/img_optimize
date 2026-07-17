import { NavLink, Outlet, Link, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Users, ListChecks, MessageSquare, LogOut, ArrowLeft } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

const NAV_ITEMS = [
  { to: '/admin', end: true, icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/admin/users', icon: Users, label: 'Utilisateurs' },
  { to: '/admin/jobs', icon: ListChecks, label: 'Jobs' },
  { to: '/admin/reviews', icon: MessageSquare, label: 'Avis' },
]

export default function AdminLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-[#050505]">
      {/* Barre admin dédiée : pas de nav publique (marketing, CTA optimiseur...) */}
      <header className="sticky top-0 z-50 border-b border-slate-800 bg-black/80 backdrop-blur-xl px-6 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center">
              <i className="fa-solid fa-shield-halved text-white text-sm"></i>
            </div>
            <span className="text-lg font-bold text-white">
              Img<span className="text-violet-400">Opt</span> Admin
            </span>
          </div>

          <div className="flex items-center gap-4">
            <span className="hidden sm:inline text-sm text-slate-400">{user?.email}</span>
            <Link
              to="/"
              className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="hidden sm:inline">Retour au site</span>
            </Link>
            <button
              onClick={handleLogout}
              className="inline-flex items-center gap-2 px-3 py-1.5 text-sm text-slate-400 hover:text-red-400 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Déconnexion</span>
            </button>
          </div>
        </div>
      </header>

      <div className="px-6 py-8">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-[220px_1fr] gap-8">
          <aside className="bg-slate-900/50 border border-slate-800 rounded-[2rem] p-4 space-y-1 h-fit lg:sticky lg:top-24">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-violet-600 text-white'
                        : 'text-slate-400 hover:text-white hover:bg-slate-800'
                    }`
                  }
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </NavLink>
              )
            })}
          </aside>

          <main>
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}
