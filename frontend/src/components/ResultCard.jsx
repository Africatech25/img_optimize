import { CheckCircle, TrendingDown, FileCheck, Download } from 'lucide-react'

export default function ResultCard({ result, totalImages, onDownload, onReset }) {
  const { stats, total_images, processed_images } = result

  const formatSize = (bytes) => {
    if (bytes >= 1_000_000) {
      return `${(bytes / 1_000_000).toFixed(1)} Mo`
    }
    return `${(bytes / 1_000).toFixed(0)} Ko`
  }

  const isSingleImage = totalImages === 1

  return (
    <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-[2.5rem] p-8 space-y-8 animate-fade-in">
      {/* Success Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-green-600 to-green-800 mb-4">
          <CheckCircle className="w-10 h-10 text-white" />
        </div>
        <h2 className="text-3xl font-bold text-white mb-2">
          Optimisation terminée !
        </h2>
        <p className="text-slate-400">
          {stats.successful} image{stats.successful > 1 ? 's' : ''} optimisée{stats.successful > 1 ? 's' : ''} avec succès
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Images Processed */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-3xl p-6 text-center">
          <div className="w-12 h-12 mx-auto rounded-2xl bg-gradient-to-br from-violet-600 to-violet-800 flex items-center justify-center mb-3">
            <FileCheck className="w-6 h-6 text-white" />
          </div>
          <p className="text-3xl font-bold text-white mb-1">{stats.successful}</p>
          <p className="text-sm text-slate-400">Images optimisées</p>
        </div>

        {/* Size Reduction */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-3xl p-6 text-center">
          <div className="w-12 h-12 mx-auto rounded-2xl bg-gradient-to-br from-cyan-600 to-cyan-800 flex items-center justify-center mb-3">
            <TrendingDown className="w-6 h-6 text-white" />
          </div>
          <p className="text-3xl font-bold text-gradient mb-1">
            {stats.reduction_percent}%
          </p>
          <p className="text-sm text-slate-400">Réduction moyenne</p>
        </div>

        {/* Total Saved */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-3xl p-6 text-center">
          <div className="w-12 h-12 mx-auto rounded-2xl bg-gradient-to-br from-green-600 to-green-800 flex items-center justify-center mb-3">
            <CheckCircle className="w-6 h-6 text-white" />
          </div>
          <p className="text-3xl font-bold text-white mb-1">
            {formatSize(stats.total_before - stats.total_after)}
          </p>
          <p className="text-sm text-slate-400">Espace économisé</p>
        </div>
      </div>

      {/* Size Comparison */}
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
                style={{ width: `${(stats.total_after / stats.total_before) * 100}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Errors if any */}
      {stats.errors > 0 && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-4">
          <p className="text-sm text-red-400">
            ⚠️ {stats.errors} erreur{stats.errors > 1 ? 's' : ''} rencontrée{stats.errors > 1 ? 's' : ''} pendant le traitement
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
          {isSingleImage ? 'Télécharger l\'image' : 'Télécharger le ZIP'}
        </button>

        <button
          onClick={onReset}
          className="flex-1 px-6 py-2.5 bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-2xl transition-all duration-300"
        >
          Nouvelle optimisation
        </button>
      </div>
    </div>
  )
}
