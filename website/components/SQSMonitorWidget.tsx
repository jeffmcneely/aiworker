import { useState, useEffect, useRef } from 'react'
import styles from './MetricsWidget.module.css'

interface QueueData {
  queueName: string
  messagesAvailable: number
  messagesInFlight: number
}

export default function SQSMonitorWidget() {
  const [queueData, setQueueData] = useState<QueueData[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isPaused, setIsPaused] = useState(false)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  const fetchQueueData = async () => {
    if (isPaused) return

    try {
      // Try the production API first, fall back to localhost for development
      const apiBase = process.env.NEXT_PUBLIC_API_BASE
      const apiUrl = process.env.NODE_ENV === 'production' 
        ? `${apiBase}/sqs_monitor`
        : 'http://localhost:3001/sqs_monitor'
      
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        // Include credentials for CORS
        credentials: 'omit'
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setQueueData(data)
      setError(null)
      setIsLoading(false)
    } catch (err) {
      console.error('Error fetching queue data:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
      setIsLoading(false)
    }
  }

  const startPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }
    fetchQueueData() // Initial fetch
    intervalRef.current = setInterval(fetchQueueData, 10000) // Poll every 10 seconds
  }

  const stopPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }

  useEffect(() => {
    if (!isPaused) {
      startPolling()
    } else {
      stopPolling()
    }

    return () => stopPolling()
  }, [isPaused])

  const togglePause = () => {
    setIsPaused(!isPaused)
  }

  const getStatusColor = (available: number, inFlight: number) => {
    const total = available + inFlight
    if (total === 0) return '#10b981' // green - no messages
    if (total < 10) return '#f59e0b' // yellow - few messages
    return '#ef4444' // red - many messages
  }

  if (isLoading) {
    return (
      <div className={styles.widget}>
        <div className={styles.header}>
          <h2>SQS Queue Monitor</h2>
        </div>
        <div className={styles.loading}>Loading queue data...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={styles.widget}>
        <div className={styles.header}>
          <h2>SQS Queue Monitor</h2>
        </div>
        <div className={styles.error}>Error: {error}</div>
      </div>
    )
  }

  return (
    <div className={styles.widget}>
      <div className={styles.header}>
        <h2>SQS Queue Monitor</h2>
        <button 
          onClick={togglePause}
          className={styles.pauseButton}
          style={{
            backgroundColor: isPaused ? '#10b981' : '#ef4444',
            color: 'white',
            border: 'none',
            padding: '6px 12px',
            borderRadius: '4px',
            fontSize: '12px',
            cursor: 'pointer'
          }}
        >
          {isPaused ? 'Resume' : 'Pause'}
        </button>
      </div>
      
      <div className={styles.content}>
        {queueData.map((queue, index) => (
          <div key={index} className={styles.metricSection}>
            <h3 style={{ 
              color: getStatusColor(queue.messagesAvailable, queue.messagesInFlight),
              textTransform: 'capitalize',
              marginBottom: '10px'
            }}>
              {queue.queueName} Queue
            </h3>
            <div className={styles.metricGrid}>
              <div className={styles.metric}>
                <span className={styles.label}>Available:</span>
                <span className={styles.value} style={{ 
                  color: getStatusColor(queue.messagesAvailable, 0) 
                }}>
                  {queue.messagesAvailable}
                </span>
              </div>
              <div className={styles.metric}>
                <span className={styles.label}>In Flight:</span>
                <span className={styles.value} style={{ 
                  color: getStatusColor(0, queue.messagesInFlight) 
                }}>
                  {queue.messagesInFlight}
                </span>
              </div>
              <div className={styles.metric}>
                <span className={styles.label}>Total:</span>
                <span className={styles.value} style={{ 
                  color: getStatusColor(queue.messagesAvailable, queue.messagesInFlight) 
                }}>
                  {queue.messagesAvailable + queue.messagesInFlight}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className={styles.footer}>
        <small>Updates every 10 seconds • {isPaused ? 'Paused' : 'Live'}</small>
      </div>
    </div>
  )
}
