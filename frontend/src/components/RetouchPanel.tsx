import { useState, useEffect } from 'react'
import { applyRetouch, imageUrl, listImages, type ImageRecord } from '../api/client'

interface RetouchPanelProps {
  images: ImageRecord[]
}

export default function RetouchPanel({ images }: RetouchPanelProps) {
  const [selected, setSelected] = useState<number[]>([])
  const [retouching, setRetouching] = useState(false)
  const [previewUrls, setPreviewUrls] = useState<string[]>([])
  const [style, setStyle] = useState<'ppr10k' | 'fivek'>('ppr10k')

  const toggleSelect = (id: number) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    )
  }

  const handleRetouch = async () => {
    if (selected.length === 0) return
    setRetouching(true)
    try {
      const result = await applyRetouch(selected, style)
      setPreviewUrls(result.preview_urls || [])
    } catch (err) {
      console.error('Retouch failed:', err)
    }
    setRetouching(false)
  }

  return (
    <div className="space-y-4">
      {/* Style selector + action */}
      <div className="bg-surface-800 rounded-xl p-4 border border-surface-600 flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-400">Style:</span>
          <select
            value={style}
            onChange={(e) => setStyle(e.target.value as 'ppr10k' | 'fivek')}
            className="bg-surface-700 text-gray-200 border border-surface-600 rounded-lg px-3 py-1.5 text-sm"
          >
            <option value="ppr10k">PPR10K (Natural)</option>
            <option value="fivek">MIT-Adobe FiveK (Vivid)</option>
          </select>
          <span className="text-xs text-gray-500">
            {selected.length} photo{selected.length !== 1 ? 's' : ''} selected
          </span>
        </div>
        <button
          onClick={handleRetouch}
          disabled={selected.length === 0 || retouching}
          className="px-5 py-2.5 rounded-lg text-sm font-medium bg-accent text-white hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-accent/20"
        >
          {retouching ? 'Applying retouch...' : 'Apply Color Retouch'}
        </button>
      </div>

      {/* Image grid with select */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
        {images.map((img) => {
          const isSelected = selected.includes(img.id)
          const hasPreview = previewUrls.includes(`/api/media/${img.id}?retouched=1`)

          return (
            <div
              key={img.id}
              onClick={() => toggleSelect(img.id)}
              className={`
                relative aspect-[3/2] bg-surface-800 rounded-xl overflow-hidden border-2 cursor-pointer
                transition-all duration-150
                ${isSelected ? 'border-accent ring-2 ring-accent/30' : 'border-surface-600/50 hover:border-surface-500'}
              `}
            >
              <img
                src={`/api/media/${img.id}?size=thumb`}
                alt={img.filename}
                className="w-full h-full object-cover"
                loading="lazy"
              />
              {isSelected && (
                <div className="absolute top-2 right-2 w-6 h-6 bg-accent rounded-full flex items-center justify-center text-white text-xs font-bold shadow-lg">
                  ✓
                </div>
              )}
              {hasPreview && (
                <div className="absolute bottom-2 left-2 px-2 py-0.5 bg-positive/80 text-white text-[10px] rounded font-medium">
                  Retouched
                </div>
              )}
            </div>
          )
        })}
      </div>

      {images.length === 0 && (
        <p className="text-gray-500 text-sm text-center py-8">
          Upload photos to enable color retouching
        </p>
      )}
    </div>
  )
}
