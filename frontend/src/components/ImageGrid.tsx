import type { ImageRecord } from '../api/client'

interface ImageGridProps {
  images: ImageRecord[]
  label: string
  emptyMessage: string
  showFlags?: boolean
}

export default function ImageGrid({ images, label, emptyMessage, showFlags }: ImageGridProps) {
  if (images.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center py-16 text-gray-500 text-sm">
        {emptyMessage}
      </div>
    )
  }

  return (
    <div className="flex-1">
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
        {images.map((img) => (
          <div
            key={img.id}
            className="group relative bg-surface-800 rounded-xl overflow-hidden border border-surface-600/50 hover:border-accent/50 transition-all"
          >
            {/* Thumbnail */}
            <div className="aspect-[3/2] overflow-hidden bg-surface-700">
              <img
                src={`/api/media/${img.id}?size=thumb`}
                alt={img.filename}
                className="w-full h-full object-cover transition-transform group-hover:scale-105"
                loading="lazy"
              />
            </div>

            {/* Overlay info */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
              <div className="absolute bottom-0 left-0 right-0 p-2 text-xs text-gray-200 space-y-0.5">
                <p className="truncate font-medium">{img.filename}</p>
                {img.sharpness_score !== null && (
                  <p>Sharpness: {img.sharpness_score.toFixed(1)}</p>
                )}
                {img.global_quality_score !== null && (
                  <p>Quality: {(img.global_quality_score * 100).toFixed(0)}%</p>
                )}
                {img.exposure_flag && img.exposure_flag !== 'NORMAL' && (
                  <p className="text-warning">{img.exposure_flag}</p>
                )}
                {img.is_best_in_burst && (
                  <p className="text-positive">★ Best in burst</p>
                )}
              </div>
            </div>

            {/* Flag badge */}
            {showFlags && img.flag_reasons.length > 0 && (
              <div className="absolute top-2 left-2 flex flex-wrap gap-1">
                {img.flag_reasons.map((reason) => (
                  <span
                    key={reason}
                    className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                      reason === 'CLOSED_EYES'
                        ? 'bg-negative/80 text-white'
                        : reason === 'BLURRED_FACE'
                        ? 'bg-warning/80 text-black'
                        : 'bg-surface-600/80 text-gray-200'
                    }`}
                  >
                    {reason.replace('_', ' ')}
                  </span>
                ))}
              </div>
            )}

            {/* Best-in-burst star */}
            {img.is_best_in_burst && (
              <div className="absolute top-2 right-2 text-positive text-lg drop-shadow-lg">
                ★
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Count */}
      <p className="text-xs text-gray-500 mt-3 text-center">
        {images.length} {label.toLowerCase()} photo{images.length !== 1 ? 's' : ''}
      </p>
    </div>
  )
}
