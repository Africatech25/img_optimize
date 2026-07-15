import { Link } from 'react-router-dom'
import { Image as ImageIcon, Film, PenTool, Sparkles, ArrowRight } from 'lucide-react'

const ACTIONS = [
  {
    to: '/app/images',
    icon: ImageIcon,
    title: 'Optimiser des images',
    description: 'Compressez et convertissez vos images (JPEG, WebP, AVIF, PNG) pour réduire leur poids.',
    accent: 'from-cyan-600 to-cyan-800',
    ring: 'hover:border-cyan-500/50',
  },
  {
    to: '/app/videos',
    icon: Film,
    title: 'Optimiser des vidéos',
    description: 'Compressez et convertissez vos vidéos (H.264, H.265, VP9, AV1) sans perdre en qualité perçue.',
    accent: 'from-violet-600 to-violet-800',
    ring: 'hover:border-violet-500/50',
  },
  {
    to: '/app/sign',
    icon: PenTool,
    title: 'Signer des images',
    description: 'Ajoutez une signature texte ou un logo à vos images, à qualité maximale, sans compression.',
    accent: 'from-blue-600 to-blue-800',
    ring: 'hover:border-blue-500/50',
  },
  {
    to: '/app/smooth',
    icon: Sparkles,
    title: 'Lisser des images',
    description: 'Réduisez le grain de vos images avec un flou gaussien, à qualité maximale, sans compression.',
    accent: 'from-emerald-600 to-emerald-800',
    ring: 'hover:border-emerald-500/50',
  },
]

export default function Hub() {
  return (
    <div className="min-h-screen pt-28">
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="text-center mb-12">
          <h1 className="text-3xl sm:text-4xl font-bold text-white mb-3">
            Que souhaitez-vous faire ?
          </h1>
          <p className="text-slate-400">
            Chaque action a son propre espace, avec les réglages qui lui sont propres.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {ACTIONS.map((action) => {
            const Icon = action.icon
            return (
              <Link
                key={action.to}
                to={action.to}
                className={`group bg-slate-900/50 border border-slate-800 rounded-[2.5rem] p-8 transition-all duration-300 ${action.ring} hover:scale-[1.02]`}
              >
                <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${action.accent} flex items-center justify-center mb-6`}>
                  <Icon className="w-7 h-7 text-white" />
                </div>
                <h2 className="text-xl font-semibold text-white mb-2">{action.title}</h2>
                <p className="text-sm text-slate-400 mb-6">{action.description}</p>
                <span className="inline-flex items-center gap-2 text-sm font-medium text-slate-300 group-hover:gap-3 transition-all">
                  Commencer
                  <ArrowRight className="w-4 h-4" />
                </span>
              </Link>
            )
          })}
        </div>
      </div>
    </div>
  )
}
