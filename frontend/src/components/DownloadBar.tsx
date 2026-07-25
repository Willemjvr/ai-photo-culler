interface DownloadBarProps {
  jobId: string
  cleanUrl: string
  flaggedUrl: string
  hasClean: boolean
  hasFlagged: boolean
}

export default function DownloadBar({
  jobId,
  cleanUrl,
  flaggedUrl,
  hasClean,
  hasFlagged,
}: DownloadBarProps) {
  return (
    <div className="bg-surface-800 rounded-xl p-4 border border-surface-600 flex flex-col sm:flex-row gap-3 items-center justify-between">
      <p className="text-sm text-gray-400">
        Download processed results as ZIP archives:
      </p>
      <div className="flex gap-3">
        <a
          href={cleanUrl}
          download
          className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all ${
            hasClean
              ? 'bg-positive text-white hover:bg-positive/80 shadow-lg shadow-positive/20'
              : 'bg-surface-600 text-gray-500 pointer-events-none'
          }`}
        >
          <span>⬇</span> Download Clean
        </a>
        <a
          href={flaggedUrl}
          download
          className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all ${
            hasFlagged
              ? 'bg-negative text-white hover:bg-negative/80 shadow-lg shadow-negative/20'
              : 'bg-surface-600 text-gray-500 pointer-events-none'
          }`}
        >
          <span>⬇</span> Download Flagged
        </a>
      </div>
    </div>
  )
}
