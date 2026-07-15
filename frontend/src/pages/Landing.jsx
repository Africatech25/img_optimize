import { Link } from 'react-router-dom'

export default function Landing() {
  return (
    <div className="min-h-screen bg-[#050505] overflow-hidden">
      {/* Background Orbs */}
      <div className="fixed inset-0 pointer-events-none -z-10">
        <div className="absolute top-[-10%] left-[-10%] w-[50vw] h-[50vw] bg-violet-600/10 blur-[120px] rounded-full animate-pulse-slow"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40vw] h-[40vw] bg-cyan-600/10 blur-[120px] rounded-full animate-pulse-slow font-delay-2000"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] bg-indigo-500/5 blur-[100px] rounded-full"></div>
      </div>

      {/* Hero Section */}
      <section className="relative px-6 pt-28 pb-16 lg:pt-36 lg:pb-20 max-w-7xl mx-auto">
        <div className="text-center">
          {/* Title */}
          <h1 className="text-4xl md:text-5xl lg:text-8xl font-bold mb-8 leading-[1.1] tracking-tight max-w-[15ch] mx-auto">
            <span className="text-gradient">Optimisez vos images</span>
            <br />
            <span className="text-white">et vidéos</span>
          </h1>

          {/* Subtitle */}
          <p className="text-lg lg:text-xl text-slate-400 mb-12 max-w-2xl mx-auto font-light leading-relaxed">
            Réduisez significativement le poids de vos fichiers images et vidéos sans sacrifier la qualité.
            H.264, H.265, VP9, AV1, WebP, AVIF — la solution ultime pour un SEO performant.
          </p>

          {/* CTA Group */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-6 animate-slide-up px-4">
            <Link
              to="/app"
              className="w-full sm:w-auto group relative inline-flex items-center justify-center gap-3 px-8 py-3.5 md:px-10 md:py-4 bg-white text-black font-bold rounded-[2rem] transition-all duration-300 hover:scale-105 active:scale-95 shadow-[0_0_20px_rgba(255,255,255,0.1)]"
            >
              <i className="fa-solid fa-bolt text-lg group-hover:animate-bounce"></i>
              Commencer l'optimisation
            </Link>

            <a
              href="#features"
              className="w-full sm:w-auto group inline-flex items-center justify-center gap-3 px-8 py-3.5 md:px-10 md:py-4 bg-[#000000] text-slate-300 font-semibold rounded-[2rem] transition-all duration-300 hover:scale-105 active:scale-95 border border-white/[0.08] shadow-[0_0_20px_rgba(255,255,255,0.02)] hover:text-white"
            >
              Fonctionnalités
              <i className="fa-solid fa-arrow-down text-sm animate-bounce"></i>
            </a>
          </div>

          {/* Hero Image Mockup */}
          <div className="mt-24 relative max-w-5xl mx-auto group animate-float">
            <div className="absolute -inset-1 bg-gradient-to-r from-violet-600 to-cyan-600 rounded-[2rem] blur opacity-20 group-hover:opacity-40 transition duration-1000"></div>
            <div className="relative glass-card gradient-border rounded-[2.5rem] overflow-hidden p-1 lg:p-2">
              <div className="bg-[#0A0A0A] rounded-[2rem] p-4 lg:p-8 aspect-video flex flex-col items-center justify-center border border-white/5">
                <i className="fa-solid fa-cloud-arrow-up text-6xl text-slate-800 mb-6 group-hover:text-violet-500/40 transition-colors duration-500"></i>
                <div className="w-full max-w-md h-2 bg-slate-900 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-violet-500 to-cyan-500 w-[65%] rounded-full shadow-[0_0_10px_rgba(139,92,246,0.5)]"></div>
                </div>
                <div className="mt-8 grid grid-cols-3 gap-4 w-full max-w-lg opacity-40">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-24 glass-card rounded-3xl animate-pulse-slow" style={{ animationDelay: `${i * 200}ms` }}></div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section - 3 Column Grid */}
      <section id="features" className="px-8 md:px-12 lg:px-20 py-20 lg:py-24 relative bg-white/[0.01]">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20 animate-fade-in">
            <span className="text-xs font-bold text-violet-500 uppercase tracking-[0.3em] mb-4 inline-block">Notre Savoir-Faire</span>
            <h2 className="text-4xl lg:text-6xl font-bold mb-6 text-white leading-tight">
              La solution complète <br className="hidden md:block" />
              pour images et vidéos
            </h2>
          </div>

          <div className="flex flex-wrap justify-center gap-8">
            {[
              {
                icon: 'fa-bolt-lightning',
                title: 'Compression Ultra-Rapide',
                desc: 'Réduisez le poids de vos fichiers en quelques secondes sans compromis sur la netteté.',
                color: 'bg-blue-600'
              },
              {
                icon: 'fa-chart-line',
                title: 'Optimisation SEO',
                desc: 'Des assets légers et bien nommés pour grimper au sommet des résultats de recherche Google.',
                color: 'bg-indigo-600'
              },
              {
                icon: 'fa-shield-halved',
                title: 'Sécurité Maximale',
                desc: 'Traitement 100% sur nos serveurs. Vos données restent privées, toujours.',
                color: 'bg-cyan-600'
              },
              {
                icon: 'fa-wand-magic-sparkles',
                title: 'Formats Modernes',
                desc: 'Conversion vers WebP, AVIF pour les images. H.264, H.265, VP9, AV1 pour les vidéos.',
                color: 'bg-fuchsia-600'
              },
              {
                icon: 'fa-film',
                title: 'Optimisation Vidéo',
                desc: 'Compressez vos vidéos avec les codecs les plus efficaces. Contrôle du CRF, résolution et FPS.',
                color: 'bg-rose-600'
              },
              {
                icon: 'fa-layer-group',
                title: 'Workflow Illimité',
                desc: 'Aucun compte requis. Traitez des centaines de fichiers sans file d\'attente ni restriction.',
                color: 'bg-emerald-600'
              }
            ].map((feature, idx) => (
              <div 
                key={idx} 
                className="w-full md:w-[calc(50%-1rem)] lg:w-[calc(33.33%-2rem)] bg-white/[0.03] border border-white/[0.05] p-10 rounded-[2rem] hover:bg-white/[0.05] transition-all duration-500 group flex flex-col items-start"
              >
                <div className={`w-16 h-16 ${feature.color} rounded-full flex items-center justify-center mb-8 shadow-lg ${feature.color.replace('bg-', 'shadow-')}/20 group-hover:scale-110 transition-transform`}>
                  <i className={`fa-solid ${feature.icon} text-2xl text-white`}></i>
                </div>
                <h3 className="text-2xl font-bold text-white mb-4">{feature.title}</h3>
                <p className="text-slate-400 leading-relaxed font-light">
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Info Split Section - Dashboard Visual */}
      <section id="analytics" className="px-8 md:px-12 lg:px-20 py-20 lg:py-24 relative overflow-hidden">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col lg:flex-row items-center gap-24 lg:gap-32">
            {/* Left Column: Text Content */}
            <div className="lg:w-[45%] animate-slide-up">
              <span className="text-xs font-bold text-cyan-500 uppercase tracking-[0.3em] mb-4 inline-block px-3 py-1 bg-cyan-500/10 border border-cyan-500/20 rounded-full">Analyse de Données</span>
              <h2 className="text-4xl lg:text-7xl font-bold mb-8 text-white leading-tight">
                Optimisation <br />
                poussée.
              </h2>
              <p className="text-slate-400 text-xl font-light mb-12 leading-relaxed max-w-xl">
                Suivez en temps réel le gain de performance de vos assets. 
                Notre algorithme analyse chaque octet pour garantir un rendu parfait 
                tout en divisant le poids de vos fichiers par quatre.
              </p>
              
              <Link 
                to="/app" 
                className="group inline-flex items-center gap-3 px-8 py-4 bg-transparent border border-white/20 text-white font-bold rounded-full hover:bg-white/5 transition-all"
              >
                DÉCOUVRIR PLUS
                <i className="fa-solid fa-arrow-right text-xs group-hover:translate-x-1 transition-transform"></i>
              </Link>
            </div>

            {/* Right Column: Visual Mockup */}
            <div className="lg:w-[55%] w-full relative pt-10">
              <div className="absolute -inset-10 bg-violet-600/5 blur-[100px] rounded-full pointer-events-none"></div>
              
              {/* Main Dashboard Window */}
              <div className="relative glass-card premium-rounded border border-white/10 p-8 shadow-[0_50px_100px_rgba(0,0,0,0.5)] bg-[#0A0A0A] animate-float overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-violet-500/20 to-transparent"></div>
                
                {/* Visual Header Mockup */}
                <div className="flex items-center justify-between mb-10 pb-4 border-b border-white/5">
                  <div className="flex gap-2.5">
                    <div className="w-3 h-3 rounded-full bg-[#FF5F56] shadow-[0_0_10px_rgba(255,95,86,0.3)]"></div>
                    <div className="w-3 h-3 rounded-full bg-[#FFBD2E] shadow-[0_0_10px_rgba(255,189,46,0.3)]"></div>
                    <div className="w-3 h-3 rounded-full bg-[#27C93F] shadow-[0_0_10px_rgba(39,201,63,0.3)]"></div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="h-1.5 w-20 bg-white/5 rounded-full"></div>
                    <i className="fa-solid fa-circle-user text-slate-700"></i>
                  </div>
                </div>

                <div className="space-y-10">
                  {[
                    { label: 'Asset Original (RAW)', size: '12.8 MB', progress: 100, color: 'bg-slate-800', icon: 'fa-file-image' },
                    { label: 'Optimisé WebP v2', size: '1.2 MB', progress: 12, color: 'bg-violet-500', saved: '90%', icon: 'fa-file-bolt' },
                    { label: 'Vidéo H.265', size: '8.4 MB → 2.1 MB', progress: 25, color: 'bg-cyan-500', saved: '75%', icon: 'fa-file-video' },
                  ].map((row, idx) => (
                    <div key={idx} className="relative group/row">
                      <div className="flex justify-between mb-4 items-end">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center border border-white/5 group-hover/row:border-violet-500/30 transition-colors">
                            <i className={`fa-solid ${row.icon} ${idx === 1 ? 'text-violet-400' : 'text-slate-500'}`}></i>
                          </div>
                          <div>
                            <p className="text-slate-500 text-[10px] uppercase font-bold tracking-[0.2em] mb-1">{row.label}</p>
                            <p className="text-white font-bold text-xl">{row.size}</p>
                          </div>
                        </div>
                        {row.saved && (
                          <div className="px-3 py-1 bg-green-500/10 border border-green-500/20 rounded-full flex items-center gap-2">
                             <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
                             <span className="text-green-400 font-bold text-[10px] tracking-widest uppercase">Gagné {row.saved}</span>
                          </div>
                        )}
                      </div>
                      <div className="h-2 bg-slate-900 rounded-full overflow-hidden p-[1px]">
                        <div
                          className={`h-full ${row.color} rounded-full transition-all duration-[1500ms] ease-out shadow-[0_0_15px_rgba(139,92,246,0.3)]`}
                          style={{ width: `${row.progress}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Overlapping Stats Card */}
              <div className="absolute -bottom-6 left-0 lg:-left-12 w-48 sm:w-56 glass-card rounded-[2rem] border border-white/10 p-4 sm:p-6 shadow-2xl backdrop-blur-2xl bg-black/60 translate-y-4 animate-float-delayed">
                <div className="flex flex-col items-center">
                   <div className="relative w-20 h-20 sm:w-28 sm:h-28 mb-4">
                      <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                         <circle cx="18" cy="18" r="16" fill="none" className="stroke-white/5" strokeWidth="3"></circle>
                         <circle cx="18" cy="18" r="16" fill="none" className="stroke-cyan-500" strokeWidth="3" strokeDasharray="85, 100" strokeLinecap="round"></circle>
                      </svg>
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className="text-white font-bold text-xl sm:text-2xl leading-none">85%</span>
                        <span className="text-[7px] sm:text-[8px] text-cyan-400 font-bold uppercase tracking-widest mt-1">Score</span>
                      </div>
                   </div>
                   <div className="flex items-center gap-2">
                      <i className="fa-solid fa-arrow-trend-up text-green-400 text-[10px] sm:text-xs"></i>
                      <p className="text-[8px] sm:text-[10px] text-slate-300 font-semibold uppercase tracking-widest">Optimisation SEO</p>
                   </div>
                </div>
              </div>

              {/* Floating Speed Badge */}
              <div className="absolute top-2 right-0 lg:-right-8 glass-card border border-white/10 px-3 py-2 sm:px-4 sm:py-3 rounded-2xl shadow-xl animate-float backdrop-blur-xl bg-violet-600/10 flex items-center gap-2 sm:gap-3">
                 <div className="w-6 h-6 sm:w-8 sm:h-8 rounded-lg bg-violet-500/20 flex items-center justify-center">
                    <i className="fa-solid fa-gauge-high text-violet-400 text-xs sm:text-base"></i>
                 </div>
                 <div>
                    <p className="text-white font-bold text-[10px] sm:text-xs">Vitesse LCP</p>
                    <p className="text-violet-400 text-[8px] sm:text-[10px] font-bold">x4 plus fluide</p>
                 </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA Area - Further Scaled Down */}
      <section className="px-6 py-12 relative">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-[300px] bg-violet-600/5 blur-[100px] rounded-full pointer-events-none"></div>
        <div className="max-w-3xl mx-auto glass-card premium-rounded gradient-border p-8 lg:p-12 text-center relative overflow-hidden group shadow-[0_20px_60px_rgba(0,0,0,0.4)]">
          <div className="absolute inset-0 bg-gradient-to-br from-violet-600/10 via-transparent to-cyan-600/10 opacity-30"></div>
          
          <div className="relative z-10 flex flex-col items-center">
            <div className="w-10 h-10 rounded-full bg-white/5 border border-white/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-500">
               <i className="fa-solid fa-sparkles text-lg text-violet-400"></i>
            </div>
            
            <h2 className="text-2xl lg:text-4xl font-bold mb-4 text-white leading-[1.3] tracking-tight">
              Prêt à booster <br />
              <span className="text-gradient">votre impact ?</span>
            </h2>
            
            <p className="text-slate-400 text-base font-light mb-8 max-w-md">
              Ne laissez pas vos images ni vos vidéos ralentir vos ambitions. Passez à la vitesse supérieure dès aujourd'hui.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto px-4 sm:px-0">
              <Link
                to="/app"
                className="group relative inline-flex items-center justify-center gap-3 px-8 py-3 bg-white text-black font-bold rounded-full hover:scale-105 active:scale-100 transition-all shadow-md w-full sm:w-auto"
              >
                <i className="fa-solid fa-bolt-lightning text-base group-hover:rotate-12 transition-transform"></i>
                Lancer l'optimiseur
              </Link>
              
              <Link
                to="/security"
                className="group relative inline-flex items-center justify-center gap-3 px-8 py-3 bg-transparent text-slate-300 font-bold rounded-full border border-white/10 hover:bg-white/5 hover:text-white transition-all w-full sm:w-auto"
              >
                Voir la sécurité
              </Link>
            </div>

            <p className="mt-6 text-slate-500 text-[10px] flex items-center gap-2">
               <i className="fa-solid fa-check text-green-500/50"></i>
               Utilisation gratuite et illimitée
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-20 border-t border-white/5 bg-black/50 backdrop-blur-md">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-12 text-center md:text-left">
          <div>
            <div className="text-2xl font-bold text-white mb-4">
              Img<span className="text-violet-500">Opt</span>
            </div>
            <p className="text-slate-500 max-w-xs">
              L'outil d'optimisation d'images et vidéos le plus rapide et le plus sécurisé, conçu pour les experts du web.
            </p>
          </div>

          <div className="flex gap-12">
            {[
              { title: 'Produit', links: ['Fonctionnalités', 'Formats', 'Sécurité'] },
              { title: 'Légal', links: ['Confidentialité', 'Mentions'] }
            ].map((col, idx) => (
              <div key={idx} className="space-y-4 text-left">
                <h4 className="text-white font-bold uppercase tracking-widest text-xs">{col.title}</h4>
                <ul className="space-y-2">
                  {col.links.map((lnk, i) => (
                    <li key={i}><a href="#" className="text-slate-500 hover:text-white transition-colors text-sm">{lnk}</a></li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="flex gap-4">
            {[
              { id: 'facebook', icon: 'fa-facebook-f', url: 'https://web.facebook.com/profile.php?id=100070643959821' },
              { id: 'github', icon: 'fa-github', url: '#' },
              { id: 'linkedin', icon: 'fa-linkedin-in', url: 'https://www.linkedin.com/in/maurice-codjo-6a82b82a3/' }
            ].map((social) => (
              <a 
                key={social.id} 
                href={social.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="w-12 h-12 glass-card rounded-full flex items-center justify-center hover:bg-white/10 transition-colors"
                title={social.id}
              >
                <i className={`fa-brands ${social.icon} text-slate-400 hover:text-white`}></i>
              </a>
            ))}
          </div>
        </div>
        <div className="max-w-7xl mx-auto mt-20 pt-8 border-t border-white/5 text-center text-slate-600 text-sm">
          &copy; {new Date().getFullYear()} Image Optimizer. All rights reserved. Made for speed.
        </div>
      </footer>
    </div>
  )
}
