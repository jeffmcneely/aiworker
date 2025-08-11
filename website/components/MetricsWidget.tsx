import { useEffect, useState } from 'react'
import styles from './MetricsWidget.module.css'

interface MetricsData {
  timestamp: string
  hostname: string
  cpu: {
    usage_percent: number
  }
  memory: {
    virtual: {
      percent: number
    }
    swap: {
      percent: number
    }
  }
  gpu: Array<{
    memory: {
      percent: number
    }
    temperature: number
  }>
}

interface MetricsList {
  [key: string]: string // hostname -> timestamp
}

interface MetricsCollection {
  [hostname: string]: MetricsData
}

interface MetricBarProps {
  label: string
  value: number
  unit: string
  max?: number
  min?: number
}

const MetricBar: React.FC<MetricBarProps> = ({ label, value, unit, max = 100, min = 0 }) => {
  const normalizedValue = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100))
  
  const getColor = (percentage: number) => {
    if (percentage <= 50) return '#4ade80' // green
    if (percentage <= 80) return '#fbbf24' // yellow
    return '#ef4444' // red
  }

  return (
    <div className={styles.metricBar}>
      <div className={styles.metricLabel}>
        {label}: {value.toFixed(1)}{unit}
      </div>
      <div className={styles.barContainer}>
        <div 
          className={styles.barFill}
          style={{ 
            width: `${normalizedValue}%`,
            backgroundColor: getColor(normalizedValue)
          }}
        />
      </div>
    </div>
  )
}

export default function MetricsWidget() {
  const [metricsList, setMetricsList] = useState<MetricsList | null>(null)
  const [metricsCollection, setMetricsCollection] = useState<MetricsCollection>({})
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [retryCount, setRetryCount] = useState(0)
  const [selectedHost, setSelectedHost] = useState<string | null>(null)
  const [isPaused, setIsPaused] = useState(false)

  const fetchMetricsList = async () => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_METRICS_BUCKET_BASE
      if (!baseUrl) {
        setError('NEXT_PUBLIC_METRICS_BUCKET_BASE environment variable not set')
        return
      }

      const listUrl = `${baseUrl}/list.json`
      const response = await fetch(listUrl, {
        method: 'GET',
        mode: 'cors',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        cache: 'no-cache'
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const list: MetricsList = await response.json()
      setMetricsList(list)
      
      // Set default selected host if none selected
      if (!selectedHost && Object.keys(list).length > 0) {
        setSelectedHost(Object.keys(list)[0])
      }
      
      setError(null)
      setRetryCount(0)
      
    } catch (err) {
      console.error('Failed to fetch metrics list:', err)
      
      let errorMessage = 'Failed to fetch metrics list'
      
      if (err instanceof TypeError && err.message.includes('CORS')) {
        errorMessage = 'CORS error: Check S3 bucket CORS configuration'
      } else if (err instanceof TypeError && err.message.includes('Failed to fetch')) {
        errorMessage = 'Network error: Unable to reach metrics endpoint'
      } else if (err instanceof Error) {
        errorMessage = err.message
      }
      
      setError(errorMessage)
      setRetryCount(prev => prev + 1)
    }
  }

  const fetchMetricsForHost = async (hostname: string) => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_METRICS_BUCKET_BASE
      if (!baseUrl) return

      const metricsUrl = `${baseUrl}/${hostname}.json`
      const response = await fetch(metricsUrl, {
        method: 'GET',
        mode: 'cors',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        cache: 'no-cache'
      })
      
      if (!response.ok) {
        console.warn(`Failed to fetch metrics for ${hostname}: ${response.status}`)
        return
      }
      
      const data: MetricsData = await response.json()
      setMetricsCollection(prev => ({
        ...prev,
        [hostname]: data
      }))
      setLastUpdate(new Date())
      
    } catch (err) {
      console.warn(`Failed to fetch metrics for ${hostname}:`, err)
    }
  }

  const fetchAllMetrics = async () => {
    if (!metricsList) return
    
    // Fetch metrics for all hosts in parallel
    const promises = Object.keys(metricsList).map(hostname => 
      fetchMetricsForHost(hostname)
    )
    
    await Promise.allSettled(promises)
  }

  useEffect(() => {
    if (isPaused) return
    
    fetchMetricsList()
    
    // Fetch list every 30 seconds
    const listInterval = setInterval(fetchMetricsList, 30000)
    
    return () => clearInterval(listInterval)
  }, [isPaused])

  useEffect(() => {
    if (isPaused || !metricsList || retryCount >= 5) return
    
    fetchAllMetrics()
    
    // Fetch individual metrics every 1 second
    const metricsInterval = setInterval(fetchAllMetrics, 1000)
    return () => clearInterval(metricsInterval)
  }, [metricsList, retryCount, isPaused])

  const currentMetrics = selectedHost ? metricsCollection[selectedHost] : null
  const hostOptions = metricsList ? Object.keys(metricsList) : []

  if (error) {
    return (
      <div className={styles.widget}>
        <div className={styles.header}>
          <h3>System Metrics</h3>
          <div className={styles.controls}>
            <button 
              onClick={() => setIsPaused(!isPaused)}
              className={styles.pauseButton}
              title={isPaused ? 'Resume updates' : 'Pause updates'}
            >
              {isPaused ? '▶️' : '⏸️'}
            </button>
            <div className={styles.status} style={{ color: '#ef4444' }}>
              Error {retryCount > 0 && `(${retryCount})`}
            </div>
          </div>
        </div>
        <div className={styles.error}>
          {error}
          {retryCount < 5 && (
            <div style={{ fontSize: '12px', marginTop: '4px', opacity: 0.7 }}>
              Retrying... ({retryCount}/5)
            </div>
          )}
        </div>
      </div>
    )
  }

  if (!metricsList) {
    return (
      <div className={styles.widget}>
        <div className={styles.header}>
          <h3>System Metrics</h3>
          <div className={styles.controls}>
            <button 
              onClick={() => setIsPaused(!isPaused)}
              className={styles.pauseButton}
              title={isPaused ? 'Resume updates' : 'Pause updates'}
            >
              {isPaused ? '▶️' : '⏸️'}
            </button>
            <div className={styles.status}>Loading...</div>
          </div>
        </div>
        <div className={styles.loading}>Fetching metrics list...</div>
      </div>
    )
  }

  if (!currentMetrics) {
    return (
      <div className={styles.widget}>
        <div className={styles.header}>
          <h3>System Metrics</h3>
          <div className={styles.controls}>
            <button 
              onClick={() => setIsPaused(!isPaused)}
              className={styles.pauseButton}
              title={isPaused ? 'Resume updates' : 'Pause updates'}
            >
              {isPaused ? '▶️' : '⏸️'}
            </button>
            <div className={styles.status}>Loading...</div>
          </div>
        </div>
        <div className={styles.loading}>
          {hostOptions.length > 0 ? 'Fetching metrics...' : 'No hosts available'}
        </div>
      </div>
    )
  }

  const gpu = currentMetrics.gpu?.[0] // Use first GPU if available

  return (
    <div className={styles.widget}>
      <div className={styles.header}>
        <h3>System Metrics</h3>
        <div className={styles.controls}>
          <button 
            onClick={() => setIsPaused(!isPaused)}
            className={styles.pauseButton}
            title={isPaused ? 'Resume updates' : 'Pause updates'}
          >
            {isPaused ? '▶️' : '⏸️'}
          </button>
          <div className={styles.status} style={{ color: isPaused ? '#fbbf24' : '#4ade80' }}>
            {isPaused ? 'Paused' : 'Live'} • {lastUpdate?.toLocaleTimeString()}
          </div>
        </div>
      </div>
      
      {hostOptions.length > 1 && (
        <div className={styles.hostSelector}>
          <label htmlFor="host-select">Host: </label>
          <select 
            id="host-select"
            value={selectedHost || ''}
            onChange={(e) => setSelectedHost(e.target.value)}
            className={styles.hostSelect}
          >
            {hostOptions.map(hostname => (
              <option key={hostname} value={hostname}>
                {hostname} {metricsList && metricsList[hostname] ? 
                  `(${new Date(metricsList[hostname]).toLocaleTimeString()})` : ''}
              </option>
            ))}
          </select>
        </div>
      )}
      
      <div className={styles.metrics}>
        <MetricBar 
          label="CPU Usage" 
          value={currentMetrics.cpu.usage_percent} 
          unit="%" 
        />
        
        <MetricBar 
          label="Memory" 
          value={currentMetrics.memory.virtual.percent} 
          unit="%" 
        />
        
        <MetricBar 
          label="Swap" 
          value={currentMetrics.memory.swap.percent} 
          unit="%" 
        />
        
        {gpu && (
          <>
            <MetricBar 
              label="GPU Memory" 
              value={gpu.memory.percent} 
              unit="%" 
            />
            
            <MetricBar 
              label="GPU Temp" 
              value={gpu.temperature} 
              unit="°C"
              min={20}
              max={70}
            />
          </>
        )}
      </div>
      
      <div className={styles.footer}>
        Host: {currentMetrics.hostname}
        {hostOptions.length > 1 && (
          <span style={{ marginLeft: '10px', fontSize: '12px', opacity: 0.7 }}>
            ({Object.keys(metricsCollection).length}/{hostOptions.length} online)
          </span>
        )}
      </div>
    </div>
  )
}