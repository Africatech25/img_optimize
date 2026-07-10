import { Sliders, Sparkles, PenTool } from 'lucide-react'
import { useState } from 'react'

export default function ParamsPanel({
  prefix,
  setPrefix,
  format,
  setFormat,
  quality,
  setQuality,
  startNumber,
  setStartNumber,
  smoothing,
  setSmoothing,
  watermark,
  setWatermark,
  formats,
  canOptimize,
  canSmooth,
  onProcess,
  isProcessing
}) {
  const [activeTab, setActiveTab] = useState('main') // 'main', 'smoothing' or 'signature'
  const currentFormat = formats[format]
  const qualityRange = currentFormat?.quality_range || [1, 100]

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-[2.5rem] p-6 space-y-6 sticky top-24">
      {/* Tab Header */}
      <div className="flex p-1 bg-slate-800/50 rounded-2xl border border-slate-800">
        <button
          onClick={() => setActiveTab('main')}
          className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-xl text-sm font-medium transition-all ${
            activeTab === 'main' 
              ? 'bg-violet-600 text-white shadow-lg shadow-violet-900/20' 
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <Sliders className="w-4 h-4" />
          Général
        </button>
        <button
          onClick={() => setActiveTab('signature')}
          className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-xl text-sm font-medium transition-all ${
            activeTab === 'signature' 
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20' 
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <PenTool className="w-4 h-4" />
          Signature
        </button>
        <button
          onClick={() => setActiveTab('smoothing')}
          className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-xl text-sm font-medium transition-all ${
            activeTab === 'smoothing' 
              ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-900/20' 
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          Lissage
        </button>
      </div>

      {activeTab === 'main' && (
        <div className="space-y-6 animate-in fade-in slide-in-from-left-4 duration-300">
          {/* ... (existing fields) ... */}
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

          <button
            onClick={() => onProcess('general')}
            disabled={!canOptimize || isProcessing}
            className={`w-full py-3 rounded-2xl font-semibold transition-all duration-300 ${
              canOptimize && !isProcessing
                ? 'bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white shadow-lg hover:shadow-xl hover:scale-[1.02]'
                : 'bg-slate-800 text-slate-500 cursor-not-allowed'
            }`}
          >
            {isProcessing ? 'En cours...' : 'Optimiser uniquement'}
          </button>
        </div>
      )}

      {activeTab === 'signature' && (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
          {/* Activation Watermark */}
          <div className="flex items-center justify-between p-4 bg-slate-800/30 rounded-2xl border border-slate-700/50">
            <span className="text-sm font-medium text-slate-200">Activer la signature</span>
            <button
              onClick={() => setWatermark({ ...watermark, enabled: !watermark.enabled })}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                watermark.enabled ? 'bg-blue-600' : 'bg-slate-700'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  watermark.enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div className={!watermark.enabled ? 'opacity-40 pointer-events-none' : ''}>
            {/* Type de signature */}
            <div className="flex gap-2 p-1 bg-slate-800 rounded-xl mb-4">
              <button
                onClick={() => setWatermark({ ...watermark, type: 'text' })}
                className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-all ${
                  watermark.type === 'text' ? 'bg-slate-700 text-white' : 'text-slate-400'
                }`}
              >
                Texte
              </button>
              <button
                onClick={() => setWatermark({ ...watermark, type: 'image' })}
                className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-all ${
                  watermark.type === 'image' ? 'bg-slate-700 text-white' : 'text-slate-400'
                }`}
              >
                Logo
              </button>
            </div>

            {watermark.type === 'text' ? (
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5 ml-1">VOTRE SIGNATURE</label>
                <input
                  type="text"
                  value={watermark.text}
                  onChange={(e) => setWatermark({ ...watermark, text: e.target.value })}
                  placeholder="ex: @MonStudioPhoto"
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm"
                />
              </div>
            ) : (
              <div className="group relative border-2 border-dashed border-slate-700 rounded-xl p-4 text-center hover:border-blue-500/50 transition-all cursor-pointer">
                <input 
                  type="file" 
                  className="absolute inset-0 opacity-0 cursor-pointer" 
                  accept="image/png,image/svg+xml" 
                  onChange={(e) => {
                    const file = e.target.files[0]
                    if (file) setWatermark({ ...watermark, logo: file })
                  }}
                />
                {watermark.logo ? (
                  <p className="text-xs text-blue-400 font-medium">{watermark.logo.name}</p>
                ) : (
                  <p className="text-xs text-slate-400">Cliquez pour importer votre logo (PNG/SVG)</p>
                )}
              </div>
            )}

            {/* Position (Grid 3x3) */}
            <div className="mt-6">
              <label className="block text-xs font-medium text-slate-400 mb-2 ml-1">PLACEMENT</label>
              <div className="grid grid-cols-3 gap-1.5 w-32 mx-auto">
                {['top-left', 'top-center', 'top-right', 'middle-left', 'middle-center', 'middle-right', 'bottom-left', 'bottom-center', 'bottom-right'].map((pos) => (
                  <button
                    key={pos}
                    onClick={() => setWatermark({ ...watermark, position: pos })}
                    className={`aspect-square rounded-md border transition-all ${
                      watermark.position === pos 
                        ? 'bg-blue-600 border-blue-400 shadow-sm' 
                        : 'bg-slate-800 border-slate-700 hover:border-slate-500'
                    }`}
                  />
                ))}
              </div>
            </div>

            {/* Opacité */}
            <div className="mt-6">
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-medium text-slate-400 ml-1">OPACITÉ</label>
                <span className="text-sm font-bold text-white">{watermark.opacity}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="100"
                value={watermark.opacity}
                onChange={(e) => setWatermark({ ...watermark, opacity: parseInt(e.target.value) })}
                className="w-full h-1.5 bg-slate-700 rounded-full appearance-none cursor-pointer accent-blue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 mt-4">
            <button
              onClick={() => onProcess('signature_only')}
              disabled={isProcessing || !watermark.enabled || !canOptimize}
              className={`py-3 rounded-2xl text-xs font-semibold transition-all duration-300 ${
                watermark.enabled && !isProcessing && canOptimize
                  ? 'bg-slate-800 text-slate-200 border border-slate-700 hover:bg-slate-700'
                  : 'bg-slate-900/30 text-slate-600 border border-slate-800 cursor-not-allowed'
              }`}
            >
              Signer sans compresser
            </button>
            <button
              onClick={() => onProcess('watermark')}
              disabled={!canOptimize || isProcessing || !watermark.enabled}
              className={`py-3 rounded-2xl text-xs font-semibold transition-all duration-300 ${
                watermark.enabled && canOptimize && !isProcessing
                  ? 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white shadow-lg shadow-blue-900/20'
                  : 'bg-slate-800 text-slate-500 cursor-not-allowed'
              }`}
            >
              {isProcessing ? 'En cours...' : 'Optimiser & Signer'}
            </button>
          </div>
        </div>
      )}

      {activeTab === 'smoothing' && (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
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

          <p className="text-xs text-slate-400 bg-emerald-500/10 border border-emerald-500/20 p-4 rounded-2xl italic leading-relaxed">
            Le lissage applique un flou gaussien pour réduire le grain. Dans ce mode, la qualité est maintenue au maximum.
          </p>

          <button
            onClick={() => onProcess('smoothing')}
            disabled={!canSmooth}
            className={`w-full py-3 rounded-2xl font-semibold transition-all duration-300 ${
              canSmooth
                ? 'bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-lg hover:shadow-xl hover:scale-[1.02]'
                : 'bg-slate-800 text-slate-500 cursor-not-allowed'
            }`}
          >
            {isProcessing ? 'En cours...' : 'Lisser uniquement'}
          </button>
        </div>
      )}

      {/* Button Global (Optionnel, si on veut encore faire les deux) */}
      <div className="pt-4 border-t border-slate-800">
        <button
          onClick={() => onProcess('both')}
          disabled={!canOptimize || isProcessing}
          className={`w-full py-3 rounded-2xl font-semibold border border-slate-700 transition-all duration-300 ${
            canOptimize && !isProcessing
              ? 'bg-slate-800 hover:bg-slate-700 text-slate-200'
              : 'bg-slate-900/50 text-slate-600 cursor-not-allowed'
          }`}
        >
          {isProcessing ? 'Traitement...' : 'Appliquer tout'}
        </button>
      </div>
    </div>
  )
}
