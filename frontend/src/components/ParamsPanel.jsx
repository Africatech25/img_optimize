import { Sliders } from 'lucide-react'

export default function ParamsPanel({
  prefix,
  setPrefix,
  format,
  setFormat,
  quality,
  setQuality,
  startNumber,
  setStartNumber,
  formats,
  canOptimize,
  onOptimize,
  isProcessing
}) {
  const currentFormat = formats[format]
  const qualityRange = currentFormat?.quality_range || [1, 100]

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-[2.5rem] p-6 space-y-6 sticky top-24">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b border-slate-800">
        <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-violet-600 to-violet-800 flex items-center justify-center">
          <Sliders className="w-5 h-5 text-white" />
        </div>
        <h2 className="text-xl font-semibold text-white">Paramètres</h2>
      </div>

      {/* Préfixe SEO */}
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Préfixe SEO <span className="text-red-400">*</span>
        </label>
        <input
          type="text"
          value={prefix}
          onChange={(e) => setPrefix(e.target.value)}
          placeholder="ex: hotel-bretagne-2026"
          className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
          disabled={isProcessing}
        />
        <p className="mt-1 text-xs text-slate-500">
          Ce préfixe sera utilisé pour nommer vos images
        </p>
      </div>

      {/* Format */}
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Format de sortie
        </label>
        <select
          value={format}
          onChange={(e) => setFormat(e.target.value)}
          className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
          disabled={isProcessing}
        >
          {Object.entries(formats)
            .filter(([_, config]) => config.available !== false)
            .map(([fmt, _]) => (
              <option key={fmt} value={fmt}>
                {fmt.toUpperCase()}
              </option>
            ))
          }
        </select>

        {/* Format Description Badge */}
        {currentFormat && (
          <div className="mt-2 p-3 bg-slate-800/50 border border-slate-700 rounded-xl">
            <p className="text-xs text-slate-400">
              {currentFormat.description}
            </p>
          </div>
        )}
      </div>

      {/* Qualité */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium text-slate-300">
            {format === 'png' ? 'Niveau de compression' : 'Qualité'}
          </label>
          <span className="text-lg font-bold text-white">{quality}</span>
        </div>
        <input
          type="range"
          min={qualityRange[0]}
          max={qualityRange[1]}
          value={quality}
          onChange={(e) => setQuality(parseInt(e.target.value))}
          className="w-full h-2 bg-slate-700 rounded-full appearance-none cursor-pointer accent-violet-600"
          disabled={isProcessing}
        />
        <div className="flex justify-between text-xs text-slate-500 mt-1">
          <span>{qualityRange[0]}</span>
          <span>{qualityRange[1]}</span>
        </div>
      </div>

      {/* Numéro de départ */}
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Numéro de départ
        </label>
        <input
          type="number"
          min="1"
          value={startNumber}
          onChange={(e) => setStartNumber(parseInt(e.target.value) || 1)}
          className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
          disabled={isProcessing}
        />
      </div>

      {/* Button */}
      <button
        onClick={onOptimize}
        disabled={!canOptimize}
        className={`w-full py-2.5 rounded-2xl font-semibold transition-all duration-300 ${
          canOptimize
            ? 'bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-500 hover:to-cyan-500 text-white shadow-lg hover:shadow-xl hover:scale-105'
            : 'bg-slate-800 text-slate-500 cursor-not-allowed'
        }`}
      >
        {isProcessing ? 'Optimisation en cours...' : 'Optimiser les images'}
      </button>
    </div>
  )
}
