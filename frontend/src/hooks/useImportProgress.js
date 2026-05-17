import { useEffect, useMemo, useRef, useState } from 'react'
import { API_BASE_URL } from '../utils/constants'

const defaultState = {
  processed_emails: 0,
  total_emails: 0,
  total_attachments: 0,
  processed_attachments: 0,
  emails_per_second: 0,
  estimated_remaining_seconds: null,
  current_subject: null,
  phase: 'uploading',
  status: 'pending',
  current_batch: null,
}

export function useImportProgress(jobId) {
  const [progress, setProgress] = useState(defaultState)
  const wsRef = useRef(null)
  const reconnectTimerRef = useRef(null)

  useEffect(() => {
    if (!jobId) {
      return undefined
    }

    let cancelled = false

    const connect = () => {
      if (cancelled) {
        return
      }
      const baseUrl = new URL(API_BASE_URL)
      const wsProtocol = baseUrl.protocol === 'https:' ? 'wss:' : 'ws:'
      const ws = new WebSocket(`${wsProtocol}//${baseUrl.host}/ws/progress/${jobId}`)
      wsRef.current = ws

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data)
          setProgress((prev) => ({ ...prev, ...payload }))
        } catch {
          // ignore malformed payload
        }
      }

      ws.onclose = () => {
        if (cancelled) {
          return
        }
        reconnectTimerRef.current = window.setTimeout(connect, 2000)
      }

      ws.onerror = () => ws.close()
    }

    connect()

    return () => {
      cancelled = true
      if (reconnectTimerRef.current) {
        window.clearTimeout(reconnectTimerRef.current)
      }
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [jobId])

  const percentage = useMemo(() => {
    if (!progress.total_emails) {
      return 0
    }
    return Math.min(100, Math.round((progress.processed_emails / progress.total_emails) * 100))
  }, [progress.processed_emails, progress.total_emails])

  return { progress, percentage }
}
