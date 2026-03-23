import { Link, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const location = useLocation()

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // Close mobile menu on route change
  useEffect(() => {
    setIsOpen(false)
  }, [location])

  const menuLinks = [
    { label: 'Accueil', path: '/' },
    { label: 'Fonctionnalités', path: '/#features' },
    { label: 'Sécurité', path: '/security' }
  ]

  return (
    <>
      <nav 
        className={`fixed top-0 left-0 right-0 z-[110] transition-all duration-500 px-4 md:px-6 ${
          scrolled ? 'py-2 md:py-3' : 'py-4 md:py-6'
        }`}
      >
        <div 
          className={`max-w-7xl mx-auto flex items-center justify-between glass-card gradient-border px-4 md:px-6 py-2 rounded-full md:rounded-[2rem] transition-all duration-500 ${
            scrolled || isOpen ? 'bg-black/80 translate-y-0 shadow-2xl backdrop-blur-2xl' : 'bg-transparent'
          }`}
        >
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 md:gap-3 group transition-transform hover:scale-105 z-[120]">
            <div className="w-8 h-8 md:w-10 md:h-10 rounded-xl md:rounded-2xl bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
              <i className="fa-solid fa-bolt-lightning text-white text-sm md:text-lg group-hover:animate-pulse"></i>
            </div>
            <span className="text-lg md:text-xl font-bold text-white tracking-tight">
              Img<span className="text-violet-400">Opt</span>
            </span>
          </Link>

          {/* Desktop Links */}
          <div className="hidden md:flex items-center gap-8">
            {menuLinks.map((item) => (
              <a 
                key={item.label}
                href={item.path}
                className="text-sm font-medium text-slate-400 hover:text-white transition-colors relative group"
              >
                {item.label}
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-violet-400 transition-all duration-300 group-hover:w-full"></span>
              </a>
            ))}
          </div>

          {/* Right Action */}
          <div className="flex items-center gap-2 md:gap-4">
            <Link
              to="/app"
              className="hidden sm:inline-flex items-center gap-2 px-5 md:px-6 py-1.5 md:py-2 bg-white text-black text-xs md:text-sm font-bold rounded-xl md:rounded-2xl hover:scale-105 active:scale-95 transition-all shadow-xl shadow-white/5"
            >
              Optimiser <span className="hidden lg:inline">mes images</span>
              <i className="fa-solid fa-arrow-right text-[10px]"></i>
            </Link>
            
            <button 
              onClick={() => setIsOpen(!isOpen)}
              className="md:hidden w-10 h-10 flex items-center justify-center text-white z-[120] relative"
            >
              <i className={`fa-solid ${isOpen ? 'fa-xmark' : 'fa-bars-staggered'} text-xl transition-all duration-300`}></i>
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Menu Panel */}
      <div 
        className={`fixed inset-0 z-[105] bg-black/95 backdrop-blur-2xl transition-all duration-500 md:hidden flex flex-col items-center justify-center px-6 gap-8 ${
          isOpen ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-full pointer-events-none'
        }`}
      >
        <div className="flex flex-col items-center gap-8 w-full max-w-sm">
          {menuLinks.map((item, idx) => (
            <a 
              key={item.label}
              href={item.path}
              onClick={() => setIsOpen(false)}
              className={`text-3xl font-bold text-white transition-all duration-500 delay-[${idx * 100}ms] ${
                isOpen ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
              }`}
            >
              {item.label}
            </a>
          ))}
          <Link
            to="/app"
            onClick={() => setIsOpen(false)}
            className={`w-full text-center py-5 bg-white text-black font-bold rounded-2xl transition-all duration-500 delay-300 ${
              isOpen ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
            }`}
          >
            Commencer l'optimisation
          </Link>
        </div>
      </div>
    </>
  )
}
