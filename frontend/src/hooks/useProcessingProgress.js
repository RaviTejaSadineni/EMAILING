import { useEffect, useMemo, useRef, useState } from 'react'
import { API_BASE_URL } from '../utils/constants'

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const ALLOWED_HOSTNAMES = new Set([window.location.hostname, 'localhost', '127.0.0.1'])

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
      } catch (error) {
        console.warn('Processing status polling failed', error)
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
    if (!UUID_REGEX.test(status.job_id)) {
      console.warn('Skipping WebSocket connection due to invalid job_id')
      return
    }
    const baseUrl = new URL(API_BASE_URL)
    if (!ALLOWED_HOSTNAMES.has(baseUrl.hostname)) {
      console.warn('Skipping WebSocket connection due to disallowed API host', baseUrl.hostname)
      return
    }
    const protocol = baseUrl.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${baseUrl.host}/ws/progress/${status.job_id}`)
    wsRef.current = ws
    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        setStatus((prev) => ({ ...prev, ...payload }))
      } catch (error) {
        console.warn('Malformed processing WebSocket payload', error)
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
