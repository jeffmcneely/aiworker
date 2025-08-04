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
  const [metrics, setMetrics] = useState<MetricsData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  const fetchMetrics = async () => {
    try {
      const metricsUrl = process.env.NEXT_PUBLIC_METRICS_URL
      if (!metricsUrl) {
        setError('NEXT_PUBLIC_METRICS_URL environment variable not set')
        return
      }

      const response = await fetch(metricsUrl)
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data: MetricsData = await response.json()
      setMetrics(data)
      setError(null)
      setLastUpdate(new Date())
    } catch (err) {
      console.error('Failed to fetch metrics:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch metrics')
    }
  }

  useEffect(() => {
    fetchMetrics()
    const interval = setInterval(fetchMetrics, 1000)
    return () => clearInterval(interval)
  }, [])

  if (error) {
    return (
      <div className={styles.widget}>
        <div className={styles.header}>
          <h3>System Metrics</h3>
          <div className={styles.status} style={{ color: '#ef4444' }}>Error</div>
        </div>
        <div className={styles.error}>{error}</div>
      </div>
    )
  }

  if (!metrics) {
    return (
      <div className={styles.widget}>
        <div className={styles.header}>
          <h3>System Metrics</h3>
          <div className={styles.status}>Loading...</div>
        </div>
        <div className={styles.loading}>Fetching metrics...</div>
      </div>
    )
  }

  const gpu = metrics.gpu?.[0] // Use first GPU if available

  return (
    <div className={styles.widget}>
      <div className={styles.header}>
        <h3>System Metrics</h3>
        <div className={styles.status} style={{ color: '#4ade80' }}>
          Live • {lastUpdate?.toLocaleTimeString()}
        </div>
      </div>
      
      <div className={styles.metrics}>
        <MetricBar 
          label="CPU Usage" 
          value={metrics.cpu.usage_percent} 
          unit="%" 
        />
        
        <MetricBar 
          label="Memory" 
          value={metrics.memory.virtual.percent} 
          unit="%" 
        />
        
        <MetricBar 
          label="Swap" 
          value={metrics.memory.swap.percent} 
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
        Host: {metrics.hostname}
      </div>
    </div>
  )
}
