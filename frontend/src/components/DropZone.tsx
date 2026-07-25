import { useRef, useState, useCallback, type DragEvent } from 'react'

interface DropZoneProps {
  onDrop: (files: File[]) => void
  uploading: boolean
  progress: number
}

export default function DropZone({ onDrop, uploading, progress }: DropZoneProps) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault()
    setDragging(true)
  }, [])

  const handleDragLeave = useCallback(() => {
    setDragging(false)
  }, [])

  const extractFiles = useCallback((items: DataTransferItemList | FileList): File[] => {
    const files: File[] = []
    const webkitItems = (items as DataTransferItemList)
    if (webkitItems.length && webkitItems[0].webkitGetAsEntry) {
      // Walk directory entries
      const entries: FileSystemEntry[] = []
      for (let i = 0; i < webkitItems.length; i++) {
        const entry = webkitItems[i].webkitGetAsEntry()
        if (entry) entries.push(entry)
      }

      const walk = (entry: FileSystemEntry): Promise<File[]> => {
        return new Promise((resolve) => {
          if (entry.isFile) {
            (entry as FileSystemFileEntry).file((file) => {
              resolve([file])
            })
          } else if (entry.isDirectory) {
            const dirReader = (entry as FileSystemDirectoryEntry).createReader()
            dirReader.readEntries((childEntries) => {
              Promise.all(childEntries.map(walk)).then((nested) => {
                resolve(nested.flat())
              })
            })
          }
        })
      }

      Promise.all(entries.map(walk)).then((nested) => {
        onDrop(nested.flat())
      })
      return []
    }

    // Fallback: just use file list
    for (let i = 0; i < items.length; i++) {
      files.push(items[i] as File)
    }
    return files
  }, [onDrop])

  const handleDrop = useCallback((e: DragEvent) => {
    e.preventDefault()
    setDragging(false)
    if (uploading) return
    const files = extractFiles(e.dataTransfer.items)
    if (files.length > 0) onDrop(files)
  }, [uploading, extractFiles, onDrop])

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onDrop(Array.from(e.target.files))
    }
  }, [onDrop])

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => !uploading && inputRef.current?.click()}
      className={`
        relative border-2 border-dashed rounded-2xl p-10 cursor-pointer
        transition-all duration-200 text-center
        ${dragging
          ? 'border-accent bg-accent/5 dropzone-active'
          : 'border-surface-600 hover:border-surface-500 bg-surface-800/50'
        }
        ${uploading ? 'pointer-events-none opacity-60' : ''}
      `}
    >
      <input
        ref={inputRef}
        type="file"
        webkitdirectory="true"
        multiple
        className="hidden"
        onChange={handleInputChange}
      />

      {uploading ? (
        <div className="space-y-3">
          <div className="text-3xl">⏳</div>
          <p className="text-gray-300 font-medium">Uploading folder...</p>
          <div className="h-2 bg-surface-600 rounded-full max-w-xs mx-auto overflow-hidden">
            <div
              className="h-full bg-accent rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="text-4xl">📁</div>
          <p className="text-gray-200 font-medium text-lg">
            Drop a folder of photos here
          </p>
          <p className="text-gray-500 text-sm">
            Supports JPEG, PNG, TIFF, WebP, and RAW (CR2, NEF, ARW, DNG)
          </p>
          <p className="text-gray-600 text-xs mt-2">or click to browse</p>
        </div>
      )}
    </div>
  )
}
