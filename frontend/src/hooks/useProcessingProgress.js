import { useEffect, useMemo, useRef, useState } from 'react'
import { API_BASE_URL } from '../utils/constants'

export function useProcessingProgress(fetchStatus, initialStatus = null) {
  const [status, setStatus] = useState(initialStatus)
  const wsRef = useRef(null)

  useEffect(() => {
    let cancelled = false
    let intervalId

    const poll = async () => {
      try {
        const data = await fetchStatus()
        if (!cancelled) {
          setStatus(data)
        }
      } catch {
        // ignore transient polling errors
      }
    }

    poll()
    intervalId = window.setInterval(poll, 3000)

    return () => {
      cancelled = true
      if (intervalId) {
        window.clearInterval(intervalId)
      }
      wsRef.current?.close()
    }
  }, [fetchStatus])

  useEffect(() => {
    if (!status?.job_id) {
      return
    }
    const baseUrl = new URL(API_BASE_URL)
    const protocol = baseUrl.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${baseUrl.host}/ws/progress/${status.job_id}`)
    wsRef.current = ws
    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        setStatus((prev) => ({ ...prev, ...payload }))
      } catch {
        // ignore malformed payload
      }
    }
    return () => ws.close()
  }, [status?.job_id])

  const percentage = useMemo(() => {
    if (typeof status?.progress === 'number') {
      return Math.max(0, Math.min(100, status.progress))
    }
    return 0
  }, [status?.progress])

  return { status, percentage, setStatus }
}
