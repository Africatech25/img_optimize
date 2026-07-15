import { Sparkles } from 'lucide-react'

export default function SmoothParamsPanel({
  smoothing, setSmoothing,
  prefix, setPrefix,
  startNumber, setStartNumber,
  canProcess, onProcess, isProcessing,
}) {
  const isValid = smoothing > 0

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-[2.5rem] p-6 space-y-6 sticky top-24">
      <div className="flex items-center gap-3 pb-4 border-b border-slate-800">
        <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-emerald-600 to-emerald-800 flex items-center justify-center">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <h2 className="text-xl font-semibold text-white">Lisser des images</h2>
      </div>

      <p className="text-xs text-slate-400 bg-emerald-500/10 border border-emerald-500/20 p-4 rounded-2xl italic leading-relaxed">
        Le lissage applique un flou gaussien pour réduire le grain, sans compression : format et qualité d'origine sont conservés.
      </p>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Préfixe SEO <span className="text-red-400">*</span>
        </label>
        <input
          type="text"
          value={prefix}
          onChange={(e) => setPrefix(e.target.value)}
          placeholder="ex: hotel-bretagne-2026"
          className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
          disabled={isProcessing}
        />
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium text-slate-300">
            Intensité du lissage
          </label>
          <span className="text-lg font-bold text-white">{smoothing}</span>
        </div>
        <input
          type="range"
          min="0"
          max="10"
          step="1"
          value={smoothing}
          onChange={(e) => setSmoothing(parseInt(e.target.value))}
          className="w-full h-2 bg-slate-700 rounded-full appearance-none cursor-pointer accent-emerald-500"
          disabled={isProcessing}
        />
        <div className="flex justify-between text-xs text-slate-500 mt-1">
          <span>Aucun (0)</span>
          <span>Max (10)</span>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Numéro de départ
        </label>
        <input
          type="number"
          min="1"
          value={startNumber}
          onChange={(e) => setStartNumber(parseInt(e.target.value) || 1)}
          className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
          disabled={isProcessing}
        />
      </div>

      <button
        onClick={onProcess}
        disabled={!canProcess || !isValid}
        className={`w-full py-2.5 rounded-2xl font-semibold transition-all duration-300 ${
          canProcess && isValid
            ? 'bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-lg hover:shadow-xl hover:scale-105'
            : 'bg-slate-800 text-slate-500 cursor-not-allowed'
        }`}
      >
        {isProcessing ? 'Lissage en cours...' : 'Lisser les images'}
      </button>
    </div>
  )
}
