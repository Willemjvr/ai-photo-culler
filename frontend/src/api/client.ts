import axios from 'axios'

const API = axios.create({ baseURL: '/api' })

export interface ImageRecord {
  id: number
  filename: string
  status: string
  is_flagged: boolean
  flag_reasons: string[]
  sharpness_score: number | null
  global_quality_score: number | null
  eye_aspect_ratio: number | null
  exposure_flag: string | null
  burst_group_id: string | null
  is_best_in_burst: boolean
  thumbnail_path: string | null
  retouched_path: string | null
  image_width: number | null
  image_height: number | null
  is_raw: boolean
}

export interface JobStatus {
  job_id: string
  folder_name: string | null
  total_images: number
  processed: number
  clean_count: number
  flagged_count: number
  status: string
}

// Upload a folder of images
export async function uploadImages(
  files: File[],
  jobId: string,
  onProgress?: (pct: number) => void,
): Promise<{ uploaded: number; image_ids: number[] }> {
  const form = new FormData()
  form.append('job_id', jobId)
  files.forEach((f) => form.append('files', f))

  const res = await API.post('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (e.total && onProgress) onProgress(Math.round((e.loaded / e.total) * 100))
    },
  })
  return res.data
}

// List images with optional filters
export async function listImages(params?: {
  flagged?: boolean
  job_id?: string
  burst_group?: string
}): Promise<ImageRecord[]> {
  const res = await API.get('/images', { params })
  return res.data
}

export async function getJob(jobId: string): Promise<JobStatus> {
  const res = await API.get(`/jobs/${jobId}`)
  return res.data
}

export function imageUrl(id: number, size: 'thumb' | 'full' = 'thumb'): string {
  return `/api/media/${id}?size=${size}`
}

export function downloadCleanUrl(jobId: string): string {
  return `/api/download/clean/${jobId}`
}

export function downloadFlaggedUrl(jobId: string): string {
  return `/api/download/flagged/${jobId}`
}

export async function applyRetouch(imageIds: number[], style = 'ppr10k') {
  const res = await API.post('/retouch', { image_ids: imageIds, style })
  return res.data
}
