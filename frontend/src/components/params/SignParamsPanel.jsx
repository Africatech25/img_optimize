import { PenTool } from 'lucide-react'

const WATERMARK_POSITIONS = [
  'top-left', 'top-center', 'top-right',
  'middle-left', 'middle-center', 'middle-right',
  'bottom-left', 'bottom-center', 'bottom-right',
]

export default function SignParamsPanel({
  watermark, setWatermark,
  prefix, setPrefix,
  startNumber, setStartNumber,
  canProcess, onProcess, isProcessing,
}) {
  const isValid = watermark.type === 'text'
    ? watermark.text.trim() !== ''
    : watermark.logo !== null

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-[2.5rem] p-6 space-y-6 sticky top-24">
      <div className="flex items-center gap-3 pb-4 border-b border-slate-800">
        <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center">
          <PenTool className="w-5 h-5 text-white" />
        </div>
        <h2 className="text-xl font-semibold text-white">Signer des images</h2>
      </div>

      <p className="text-xs text-slate-400 bg-blue-500/10 border border-blue-500/20 p-4 rounded-2xl italic leading-relaxed">
        La signature ne compresse pas vos images : elles sont conservées à qualité maximale, dans leur format d'origine.
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
          className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
          disabled={isProcessing}
        />
      </div>

      {/* Type de signature */}
      <div className="flex gap-2 p-1 bg-slate-800 rounded-xl">
        <button
          type="button"
          onClick={() => setWatermark({ ...watermark, type: 'text' })}
          className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-all ${
            watermark.type === 'text' ? 'bg-slate-700 text-white' : 'text-slate-400'
          }`}
          disabled={isProcessing}
        >
          Texte
        </button>
        <button
          type="button"
          onClick={() => setWatermark({ ...watermark, type: 'image' })}
          className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-all ${
            watermark.type === 'image' ? 'bg-slate-700 text-white' : 'text-slate-400'
          }`}
          disabled={isProcessing}
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
            disabled={isProcessing}
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
            disabled={isProcessing}
          />
          {watermark.logo ? (
            <p className="text-xs text-blue-400 font-medium">{watermark.logo.name}</p>
          ) : (
            <p className="text-xs text-slate-400">Cliquez pour importer votre logo (PNG/SVG)</p>
          )}
        </div>
      )}

      {/* Position (Grid 3x3) */}
      <div>
        <label className="block text-xs font-medium text-slate-400 mb-2 ml-1">PLACEMENT</label>
        <div className="grid grid-cols-3 gap-1.5 w-32 mx-auto">
          {WATERMARK_POSITIONS.map((pos) => (
            <button
              type="button"
              key={pos}
              onClick={() => setWatermark({ ...watermark, position: pos })}
              className={`aspect-square rounded-md border transition-all ${
                watermark.position === pos
                  ? 'bg-blue-600 border-blue-400 shadow-sm'
                  : 'bg-slate-800 border-slate-700 hover:border-slate-500'
              }`}
              disabled={isProcessing}
            />
          ))}
        </div>
      </div>

      {/* Opacité */}
      <div>
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
          disabled={isProcessing}
        />
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
          className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
          disabled={isProcessing}
        />
      </div>

      <button
        onClick={onProcess}
        disabled={!canProcess || !isValid}
        className={`w-full py-2.5 rounded-2xl font-semibold transition-all duration-300 ${
          canProcess && isValid
            ? 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white shadow-lg hover:shadow-xl hover:scale-105'
            : 'bg-slate-800 text-slate-500 cursor-not-allowed'
        }`}
      >
        {isProcessing ? 'Signature en cours...' : 'Signer les images'}
      </button>
    </div>
  )
}
