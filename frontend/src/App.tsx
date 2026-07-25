import { useState, useEffect, useCallback, useRef } from 'react'
import { uploadImages, listImages, getJob, imageUrl, downloadCleanUrl, downloadFlaggedUrl, type ImageRecord, type JobStatus } from './api/client'
import DropZone from './components/DropZone'
import ImageGrid from './components/ImageGrid'
import TabBar from './components/TabBar'
import DownloadBar from './components/DownloadBar'
import RetouchPanel from './components/RetouchPanel'

export type Tab = 'clean' | 'flagged' | 'retouch'

function App() {
  const [jobId, setJobId] = useState<string | null>(null)
  const [job, setJob] = useState<JobStatus | null>(null)
  const [cleanImages, setCleanImages] = useState<ImageRecord[]>([])
  const [flaggedImages, setFlaggedImages] = useState<ImageRecord[]>([])
  const [activeTab, setActiveTab] = useState<Tab>('clean')
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Poll job progress
  const startPolling = useCallback((id: string) => {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      try {
        const j = await getJob(id)
        setJob(j)
        if (j.status === 'completed' || j.status === 'failed') {
          if (pollRef.current) clearInterval(pollRef.current)
          pollRef.current = null
          // Load final results
          const [clean, flagged] = await Promise.all([
            listImages({ flagged: false }),
            listImages({ flagged: true }),
          ])
          setCleanImages(clean)
          setFlaggedImages(flagged)
        }
      } catch { /* ignore */ }
    }, 1500)
  }, [])

  // Handle folder drop
  const handleDrop = useCallback(async (files: File[]) => {
    const id = `job_${Date.now()}`
    setJobId(id)
    setUploading(true)
    setUploadProgress(0)
    setCleanImages([])
    setFlaggedImages([])

    try {
      const result = await uploadImages(files, id, setUploadProgress)
      setUploading(false)
      startPolling(id)
    } catch (err) {
      console.error('Upload failed:', err)
      setUploading(false)
    }
  }, [startPolling])

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  const totalImages = cleanImages.length + flaggedImages.length

  return (
    <div className="min-h-screen bg-surface-900 flex flex-col">
      {/* Header */}
      <header className="border-b border-surface-600 px-6 py-4 flex items-center justify-between bg-surface-800/80 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <span className="text-2xl">📸</span>
          <h1 className="text-xl font-semibold text-gray-100">AI Photo Culler</h1>
        </div>
        <div className="text-sm text-gray-400">
          {job && (
            <span>
              {job.total_images} images ·{' '}
              {job.status === 'completed'
                ? `${job.clean_count} clean, ${job.flagged_count} flagged`
                : `${job.processed}/${job.total_images} processed`}
            </span>
          )}
        </div>
      </header>

      <main className="flex-1 flex flex-col p-4 md:p-6 gap-4 max-w-7xl mx-auto w-full">
        {/* Drop zone */}
        <DropZone onDrop={handleDrop} uploading={uploading} progress={uploadProgress} />

        {/* Upload progress / job status */}
        {uploading && (
          <div className="bg-surface-800 rounded-xl p-4 border border-surface-600">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-300">Uploading folder...</span>
              <span className="text-accent font-mono">{uploadProgress}%</span>
            </div>
            <div className="h-2 bg-surface-600 rounded-full overflow-hidden">
              <div
                className="h-full bg-accent rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}

        {job && job.status === 'running' && !uploading && (
          <div className="bg-surface-800 rounded-xl p-4 border border-surface-600">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-300">AI analysis in progress...</span>
              <span className="text-accent font-mono">
                {job.processed}/{job.total_images}
              </span>
            </div>
            <div className="h-2 bg-surface-600 rounded-full overflow-hidden">
              <div
                className="h-full bg-accent rounded-full transition-all duration-300"
                style={{
                  width: `${job.total_images > 0 ? (job.processed / job.total_images) * 100 : 0}%`,
                }}
              />
            </div>
          </div>
        )}

        {/* Tabbed results */}
        {(cleanImages.length > 0 || flaggedImages.length > 0) && (
          <>
            <TabBar
              activeTab={activeTab}
              onTabChange={setActiveTab}
              cleanCount={cleanImages.length}
              flaggedCount={flaggedImages.length}
            />

            {activeTab === 'clean' && (
              <ImageGrid
                images={cleanImages}
                label="Clean"
                emptyMessage="No clean photos — all were flagged."
              />
            )}

            {activeTab === 'flagged' && (
              <ImageGrid
                images={flaggedImages}
                label="Flagged"
                emptyMessage="No flagged photos — everything looks good!"
                showFlags
              />
            )}

            {activeTab === 'retouch' && (
              <RetouchPanel images={[...cleanImages, ...flaggedImages]} />
            )}

            {/* Download bar */}
            {jobId && (
              <DownloadBar
                jobId={jobId}
                cleanUrl={downloadCleanUrl(jobId)}
                flaggedUrl={downloadFlaggedUrl(jobId)}
                hasClean={cleanImages.length > 0}
                hasFlagged={flaggedImages.length > 0}
              />
            )}
          </>
        )}

        {!jobId && !uploading && (
          <div className="flex-1 flex items-center justify-center text-gray-500 text-sm">
            Drop a folder of photos to begin AI culling
          </div>
        )}
      </main>
    </div>
  )
}

export default App
