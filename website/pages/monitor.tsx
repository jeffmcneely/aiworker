import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import MetricsWidget from '../components/MetricsWidget'
import Link from 'next/link'

export default function Monitor() {
  const [isClient, setIsClient] = useState(false)

  // Handle client-side initialization to prevent hydration mismatch
  useEffect(() => {
    setIsClient(true)
  }, [])

  return (
    <Layout title="System Monitor" description="Real-time system resource monitoring">
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        height: '100vh',
        padding: '20px',
        gap: '20px'
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid #374151',
          paddingBottom: '20px'
        }}>
          <h1 style={{
            margin: 0,
            fontSize: '24px',
            fontWeight: '600',
            color: 'white'
          }}>
            System Resource Monitor
          </h1>
          
          <Link href="/" style={{
            display: 'inline-block',
            padding: '8px 16px',
            backgroundColor: '#1976d2',
            color: 'white',
            textDecoration: 'none',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: '500',
            transition: 'background-color 0.2s ease'
          }}>
            ← Back to Gallery
          </Link>
        </div>

        {/* Content Area */}
        <div style={{
          flex: 1,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'flex-start',
          paddingTop: '40px'
        }}>
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '20px',
            maxWidth: '800px',
            width: '100%'
          }}>
            {/* Description */}
            <div style={{
              textAlign: 'center',
              color: '#d1d5db',
              fontSize: '16px',
              lineHeight: '1.5',
              marginBottom: '20px'
            }}>
              <p>
                Monitor real-time system metrics including CPU usage, memory consumption, 
                GPU utilization, and temperature across connected hosts.
              </p>
            </div>

            {/* Metrics Widget */}
            <div style={{
              transform: 'scale(2)',
              transformOrigin: 'center top',
              marginTop: '40px',
              marginBottom: '100px'
            }}>
              {isClient && <MetricsWidget />}
            </div>

            {/* Additional Info */}
            <div style={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '8px',
              padding: '20px',
              maxWidth: '600px',
              width: '100%',
              marginTop: '20px'
            }}>
              <h3 style={{
                margin: '0 0 12px 0',
                fontSize: '16px',
                fontWeight: '600',
                color: 'white'
              }}>
                Monitoring Features
              </h3>
              <ul style={{
                margin: 0,
                paddingLeft: '20px',
                color: '#d1d5db',
                fontSize: '14px',
                lineHeight: '1.6'
              }}>
                <li>Real-time CPU usage tracking</li>
                <li>Memory and swap utilization</li>
                <li>GPU memory and temperature monitoring</li>
                <li>Multi-host support with automatic discovery</li>
                <li>Live updates with pause/resume functionality</li>
                <li>Color-coded alerts (green/yellow/red)</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
