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
            Retour à l'accueil
          </Link>
          <h1 className="text-4xl lg:text-7xl font-bold mb-6">
            Sécurité & <span className="text-gradient">Confidentialité</span>
          </h1>
          <p className="text-xl text-slate-400 font-light leading-relaxed">
            Pourquoi ImgOpt est la solution la plus sûre pour vos assets numériques.
          </p>
        </div>

        {/* Content Bento Style */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-20">
          <div className="glass-card gradient-border p-8 rounded-[2.5rem]">
            <div className="w-12 h-12 glass-card rounded-2xl flex items-center justify-center mb-6">
              <i className="fa-solid fa-microchip text-xl text-violet-400"></i>
            </div>
            <h3 className="text-2xl font-bold text-white mb-4">Traitement 100% Local</h3>
            <p className="text-slate-400 leading-relaxed font-light">
              Contrairement aux autres outils, vos images ne sont <strong>jamais</strong> envoyées sur un serveur. 
              Tout le traitement s'effectue directement dans <strong>votre navigateur</strong> grâce à la puissance du WebAssembly.
            </p>
          </div>

          <div className="glass-card gradient-border p-8 rounded-[2.5rem]">
            <div className="w-12 h-12 glass-card rounded-2xl flex items-center justify-center mb-6">
              <i className="fa-solid fa-shield-halved text-xl text-cyan-400"></i>
            </div>
            <h3 className="text-2xl font-bold text-white mb-4">Zéro Serveur</h3>
            <p className="text-slate-400 leading-relaxed font-light">
              Puisque aucune donnée n'est transmise, il n'y a aucun risque de fuite de données ou d'interception. 
              Même si vous débranchez votre connexion internet, l'outil continue de fonctionner.
            </p>
          </div>

          <div className="md:col-span-2 glass-card gradient-border p-10 rounded-[2.5rem] flex flex-col md:flex-row items-center gap-10">
            <div className="w-20 h-20 glass-card rounded-3xl flex-shrink-0 flex items-center justify-center">
              <i className="fa-solid fa-eye-slash text-4xl text-pink-500"></i>
            </div>
            <div>
              <h3 className="text-2xl font-bold text-white mb-2">Pas de Cookies, Pas de Tracking</h3>
              <p className="text-slate-400 font-light text-lg">
                Nous ne stockons aucune information vous concernant. Pas d'historique de fichiers, pas de tracking publicitaire. 
                Une expérience purement technique et privée.
              </p>
            </div>
          </div>
        </div>

        {/* Technical Explanation */}
        <div className="glass-card gradient-border p-12 rounded-[3rem] bg-white/[0.01]">
          <h2 className="text-3xl font-bold text-white mb-8 border-b border-white/5 pb-4">La Tech derrière ImgOpt</h2>
          <div className="space-y-6 text-slate-400">
            <p className="leading-relaxed">
              Nous utilisons des bibliothèques de compression de pointe compilées en <strong>WebAssembly (WASM)</strong>. 
              C'est une technologie qui permet d'exécuter du code performant (initialement écrit en C++ ou Rust) directement à l'intérieur du navigateur web.
            </p>
            <p className="leading-relaxed">
              Cela signifie que vous bénéficiez de la puissance d'un logiciel de bureau (comme Photoshop) combinée à la simplicité d'une interface web, sans les compromis de sécurité habituels liés au Cloud.
            </p>
          </div>
          
          <div className="mt-12 pt-8 border-t border-white/5 flex flex-wrap gap-4">
            <span className="px-4 py-2 glass-card text-xs font-bold text-slate-300 rounded-lg">WASM</span>
            <span className="px-4 py-2 glass-card text-xs font-bold text-slate-300 rounded-lg">LOCAL-FIRST</span>
            <span className="px-4 py-2 glass-card text-xs font-bold text-slate-300 rounded-lg">GDPR-READY</span>
            <span className="px-4 py-2 glass-card text-xs font-bold text-slate-300 rounded-lg">ZERO-DATA</span>
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
