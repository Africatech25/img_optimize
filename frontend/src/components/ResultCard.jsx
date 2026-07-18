import { CheckCircle, TrendingDown, FileCheck, Download, Film, Image as ImageIcon } from 'lucide-react'

export default function ResultCard({ result, onDownload, onReset }) {
  const { stats } = result
  // stats.optimized est undefined pour les pages d'optimisation classiques
  // (toujours optimisées) et explicitement false pour un téléchargement par
  // URL où l'utilisateur a désactivé l'optimisation.
  const optimized = stats.optimized !== false

  const formatSize = (bytes) => {
    if (bytes >= 1_000_000) {
      return `${(bytes / 1_000_000).toFixed(1)} Mo`
    }
    return `${(bytes / 1_000).toFixed(0)} Ko`
  }

  const hasImages = stats.images > 0
  const hasVideos = stats.videos > 0
  const isSingleFile = stats.successful === 1

  return (
    <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-[2.5rem] p-8 space-y-8 animate-fade-in">
      {/* Success Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-green-600 to-green-800 mb-4">
          <CheckCircle className="w-10 h-10 text-white" />
        </div>
        <h2 className="text-3xl font-bold text-white mb-2">
          {optimized ? 'Optimisation terminée !' : 'Téléchargement terminé !'}
        </h2>
        <p className="text-slate-400">
          {optimized
            ? <>{stats.successful} fichier{stats.successful > 1 ? 's' : ''} optimisé{stats.successful > 1 ? 's' : ''} avec succès</>
            : <>{stats.successful} fichier{stats.successful > 1 ? 's' : ''} téléchargé{stats.successful > 1 ? 's' : ''} avec succès (sans optimisation)</>
          }
          {hasImages && hasVideos && (
            <span className="block text-sm mt-1">
              ({stats.images} image{stats.images > 1 ? 's' : ''} + {stats.videos} vidéo{stats.videos > 1 ? 's' : ''})
            </span>
          )}
        </p>
      </div>

      {/* Stats Cards */}
      <div className={`grid grid-cols-1 ${optimized ? 'md:grid-cols-3' : 'md:grid-cols-2'} gap-6`}>
        {/* Files Processed */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-3xl p-6 text-center">
          <div className="w-12 h-12 mx-auto rounded-2xl bg-gradient-to-br from-violet-600 to-violet-800 flex items-center justify-center mb-3">
            <FileCheck className="w-6 h-6 text-white" />
          </div>
          <p className="text-3xl font-bold text-white mb-1">{stats.successful}</p>
          <p className="text-sm text-slate-400">{optimized ? 'Fichiers optimisés' : 'Fichiers téléchargés'}</p>
          <div className="flex justify-center gap-2 mt-2">
            {hasImages && (
              <span className="px-2 py-0.5 bg-cyan-900/30 text-cyan-300 text-[10px] font-medium rounded-full flex items-center gap-1">
                <ImageIcon className="w-3 h-3" />
                {stats.images}
              </span>
            )}
            {hasVideos && (
              <span className="px-2 py-0.5 bg-violet-900/30 text-violet-300 text-[10px] font-medium rounded-full flex items-center gap-1">
                <Film className="w-3 h-3" />
                {stats.videos}
              </span>
            )}
          </div>
        </div>

        {optimized && (
          <div className="bg-slate-800/50 border border-slate-700 rounded-3xl p-6 text-center">
            <div className="w-12 h-12 mx-auto rounded-2xl bg-gradient-to-br from-cyan-600 to-cyan-800 flex items-center justify-center mb-3">
              <TrendingDown className="w-6 h-6 text-white" />
            </div>
            <p className="text-3xl font-bold text-gradient mb-1">
              {stats.reduction_percent}%
            </p>
            <p className="text-sm text-slate-400">Réduction moyenne</p>
          </div>
        )}

        {/* Total Saved / Total Size */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-3xl p-6 text-center">
          <div className="w-12 h-12 mx-auto rounded-2xl bg-gradient-to-br from-green-600 to-green-800 flex items-center justify-center mb-3">
            <CheckCircle className="w-6 h-6 text-white" />
          </div>
          <p className="text-3xl font-bold text-white mb-1">
            {optimized ? formatSize(stats.total_before - stats.total_after) : formatSize(stats.total_after)}
          </p>
          <p className="text-sm text-slate-400">{optimized ? 'Espace économisé' : 'Taille du fichier'}</p>
        </div>
      </div>

      {/* Size Comparison (uniquement si une optimisation a réellement eu lieu) */}
      {optimized && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-3xl p-6 space-y-4">
          <h3 className="text-lg font-semibold text-white">Comparaison des tailles</h3>

          <div className="space-y-3">
            {/* Before */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-slate-400">Avant</span>
                <span className="text-sm font-medium text-white">
                  {formatSize(stats.total_before)}
                </span>
              </div>
              <div className="w-full h-3 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-red-500/50"
                  style={{ width: '100%' }}
                />
              </div>
            </div>

            {/* After */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-slate-400">Après</span>
                <span className="text-sm font-medium text-white">
                  {formatSize(stats.total_after)}
                </span>
              </div>
              <div className="w-full h-3 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-green-600 to-green-500"
                  style={{ width: `${stats.total_before > 0 ? (stats.total_after / stats.total_before) * 100 : 0}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Errors if any */}
      {stats.errors > 0 && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-4">
          <p className="text-sm text-red-400">
            {stats.errors} erreur{stats.errors > 1 ? 's' : ''} rencontrée{stats.errors > 1 ? 's' : ''} pendant le traitement
          </p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-4 flex-col sm:flex-row">
        <button
          onClick={onDownload}
          className="flex-1 flex items-center justify-center gap-2 px-6 py-2.5 bg-gradient-to-r from-green-600 to-green-500 hover:from-green-500 hover:to-green-400 text-white font-semibold rounded-2xl transition-all duration-300 shadow-lg hover:shadow-xl hover:scale-105"
        >
          <Download className="w-5 h-5" />
          {isSingleFile ? 'Télécharger le fichier' : 'Télécharger le ZIP'}
        </button>

        <button
          onClick={onReset}
          className="flex-1 px-6 py-2.5 bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-2xl transition-all duration-300"
        >
          {optimized ? 'Nouvelle optimisation' : 'Nouveau téléchargement'}
        </button>
      </div>
    </div>
  )
}
