import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import MetricsWidget from '../components/MetricsWidget'
import SQSMonitorWidget from '../components/SQSMonitorWidget'
import Link from 'next/link'

export default function Monitor() {
  const [isClient, setIsClient] = useState(false)

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

        {/* Widgets Container */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'row',
            justifyContent: 'center',
            alignItems: 'flex-start',
            paddingTop: '40px',
            gap: '40px',
            flexWrap: 'wrap'
          }}
        >
          {/* Metrics Widget (left side on desktop, top on mobile) */}
          <div
            style={{
              flex: '1 1 320px',
              minWidth: '280px',
              maxWidth: '400px',
              marginTop: '20px',
              marginBottom: '60px',
              transform: 'scale(1.2)',
              transformOrigin: 'center top'
            }}
          >
            {isClient && <MetricsWidget />}
          </div>

          {/* SQS Monitor Widget (right side on desktop, bottom on mobile) */}
          <div
            style={{
              flex: '1 1 320px',
              minWidth: '280px',
              maxWidth: '400px',
              marginTop: '20px',
              marginBottom: '60px',
              transform: 'scale(1.2)',
              transformOrigin: 'center top'
            }}
          >
            {isClient && <SQSMonitorWidget />}
          </div>
        </div>
      </div>
      <style jsx>{`
        @media (max-width: 900px) {
          div[style*="flex-direction: row"] {
            flex-direction: column !important;
            gap: 20px !important;
            align-items: center !important;
            padding-top: 20px !important;
          }
          div[style*="transform: scale(1.2)"] {
            margin-bottom: 30px !important;
            margin-top: 10px !important;
            max-width: 100% !important;
            min-width: 0 !important;
            width: 100% !important;
            transform: scale(1) !important;
          }
        }
      `}</style>
    </Layout>
  )
}