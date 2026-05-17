import { useEffect, useRef, useState } from 'react'

export function useWebSocket(jobId) {
  const [lastMessage, setLastMessage] = useState(null)
  const wsRef = useRef(null)

  useEffect(() => {
    if (!jobId) {
      return
    }

    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    wsRef.current = new WebSocket(`${wsProtocol}://${window.location.host}/ws/progress/${jobId}`)
    wsRef.current.onmessage = (event) => setLastMessage(event.data)

    return () => {
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [jobId])

  return { lastMessage }
}
