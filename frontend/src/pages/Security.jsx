import { Link } from 'react-router-dom'

export default function Security() {
  return (
    <div className="min-h-screen bg-[#050505] overflow-hidden pt-40 pb-20">
      {/* Background Orbs */}
      <div className="fixed inset-0 pointer-events-none -z-10">
        <div className="absolute top-[-10%] right-[-10%] w-[50vw] h-[50vw] bg-indigo-600/10 blur-[120px] rounded-full"></div>
        <div className="absolute bottom-[-10%] left-[-10%] w-[40vw] h-[40vw] bg-violet-600/10 blur-[120px] rounded-full"></div>
      </div>

      <div className="max-w-4xl mx-auto px-6">
        {/* Header */}
        <div className="text-center mb-16">
          <Link to="/" className="inline-flex items-center gap-2 text-violet-400 font-bold mb-8 hover:gap-4 transition-all uppercase tracking-widest text-xs">
            <i className="fa-solid fa-arrow-left"></i>
            Retour a l'accueil
          </Link>
          <h1 className="text-4xl lg:text-7xl font-bold mb-6">
            Securite & <span className="text-gradient">Confidentialite</span>
          </h1>
          <p className="text-xl text-slate-400 font-light leading-relaxed">
            Pourquoi ImgOpt est la solution la plus sur pour vos assets numeriques.
          </p>
        </div>

        {/* Content Bento Style */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-20">
          <div className="glass-card gradient-border p-8 rounded-[2.5rem]">
            <div className="w-12 h-12 glass-card rounded-2xl flex items-center justify-center mb-6">
              <i className="fa-solid fa-user-secret text-xl text-violet-400"></i>
            </div>
            <h3 className="text-2xl font-bold text-white mb-4">Traitement Ephemere</h3>
            <p className="text-slate-400 leading-relaxed font-light">
              Vos images et videos transitent par un tunnel <strong>HTTPS ultra-securise</strong> vers notre instance privee.
              Le traitement s'effectue exclusivement en <strong>memoire vive (RAM)</strong> et les fichiers sont supprimes
              instantanement apres votre telechargement.
            </p>
          </div>

          <div className="glass-card gradient-border p-8 rounded-[2.5rem]">
            <div className="w-12 h-12 glass-card rounded-2xl flex items-center justify-center mb-6">
              <i className="fa-solid fa-shield-halved text-xl text-cyan-400"></i>
            </div>
            <h3 className="text-2xl font-bold text-white mb-4">Zero Stockage</h3>
            <p className="text-slate-400 leading-relaxed font-light">
              Nous n'avons <strong>aucune base de donnees</strong> d'images ou de videos. Contrairement aux services cloud classiques,
              nous ne conservons aucune copie de vos assets. Ce qui entre sort optimise, puis disparait a jamais de nos serveurs.
            </p>
          </div>

          <div className="md:col-span-2 glass-card gradient-border p-10 rounded-[2.5rem] flex flex-col md:flex-row items-center gap-10">
            <div className="w-20 h-20 glass-card rounded-3xl flex-shrink-0 flex items-center justify-center">
              <i className="fa-solid fa-eye-slash text-4xl text-pink-500"></i>
            </div>
            <div>
              <h3 className="text-2xl font-bold text-white mb-2">Compte Optionnel, Zero Pub</h3>
              <p className="text-slate-400 font-light text-lg">
                L'outil s'utilise sans creer de compte. Si vous choisissez de vous inscrire (pour retrouver votre historique
                de jobs), votre email sert uniquement d'identifiant &mdash; aucune revente, aucun cookie publicitaire.
                Nous utilisons <strong>Vercel Analytics</strong> pour suivre le volume d'utilisation de maniere 100% anonyme
                et sans tracage individuel. Votre identite reste votre propriete exclusive.
              </p>
            </div>
          </div>
        </div>

        {/* Technical Explanation */}
        <div className="glass-card gradient-border p-12 rounded-[3rem] bg-white/[0.01]">
          <h2 className="text-3xl font-bold text-white mb-8 border-b border-white/5 pb-4">La Tech derriere ImgOpt</h2>
          <div className="space-y-6 text-slate-400">
            <p className="leading-relaxed">
              Nous exploitons la puissance de <strong>Django REST Framework</strong> et de bibliotheques de traitement d'image
              de pointe (Pillow) pour les images, et <strong>FFmpeg</strong> pour les videos. L'architecture cloud isole chaque
              job dans un environnement ephemere, et l'authentification (facultative) repose sur des <strong>tokens JWT</strong>
              plutot que sur des sessions persistantes.
            </p>
            <p className="leading-relaxed">
              Cette approche nous permet de supporter des formats de nouvelle generation comme le <strong>WebP</strong> et l'<strong>AVIF</strong>
              pour les images, ainsi que <strong>H.264, H.265, VP9 et AV1</strong> pour les videos, avec une rapidite exceptionnelle,
              tout en garantissant une isolation complete de vos donnees durant les quelques secondes que dure le traitement.
            </p>
          </div>
          
          <div className="mt-12 pt-8 border-t border-white/5 flex flex-wrap gap-4">
            <span className="px-4 py-2 glass-card text-xs font-bold text-slate-300 rounded-lg">HTTPS-ONLY</span>
            <span className="px-4 py-2 glass-card text-xs font-bold text-slate-300 rounded-lg">RAM-CORE</span>
            <span className="px-4 py-2 glass-card text-xs font-bold text-slate-300 rounded-lg">GDPR-READY</span>
            <span className="px-4 py-2 glass-card text-xs font-bold text-slate-300 rounded-lg">EPHEMERAL-DATA</span>
            <span className="px-4 py-2 glass-card text-xs font-bold text-slate-300 rounded-lg">FFMPEG</span>
          </div>
        </div>

        {/* Final Link */}
        <div className="text-center mt-20">
          <Link
            to="/app"
            className="inline-flex items-center gap-4 px-12 py-6 bg-white text-black font-bold rounded-3xl hover:scale-105 transition-all shadow-xl"
          >
            Utiliser l'outil en toute confiance
            <i className="fa-solid fa-arrow-right"></i>
          </Link>
        </div>
      </div>
    </div>
  )
}
