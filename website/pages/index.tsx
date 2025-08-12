import { useEffect, useState, useCallback } from 'react'
import Image from 'next/image'
import Layout from '../components/Layout'
import MetricsWidget from '../components/MetricsWidget'
import Link from 'next/link'

interface ImageData {
  filename: string
  url: string
  prompt: string | null
  height: number | null
  width: number | null
  steps: number | null
  seed: number | null
  cfg: number | null
  negativePrompt: string | null
  model: string | null
  elapsed: number | null
  timestamp: string
  uuid: string
}

export default function Home() {
  const [imageUrls, setImageUrls] = useState<ImageData[]>([])
  const [lastImageFilenames, setLastImageFilenames] = useState<string[] | null>(null)
  const [expandedImage, setExpandedImage] = useState<ImageData | null>(null)
  const [detailsCollapsed, setDetailsCollapsed] = useState<boolean>(true)

  const fetchImageUrls = async (): Promise<ImageData[]> => {
    try {
      const response = await fetch('https://api.mcneely.io/v1/ai/s3list')
      if (!response.ok) throw new Error('Network response was not ok')
      const data = await response.json()
      return Array.isArray(data) ? data : []
    } catch (error) {
      console.error('Failed to fetch image URLs:', error)
      return []
    }
  }

  const refreshSidebar = useCallback(async () => {
    const newImageUrls = await fetchImageUrls()
    
    const currentFilenames = newImageUrls.map(imageData => imageData.filename)
    
    if (lastImageFilenames && JSON.stringify(currentFilenames) === JSON.stringify(lastImageFilenames)) {
      return
    }
    
    setLastImageFilenames(currentFilenames)
    setImageUrls(newImageUrls)
  }, [lastImageFilenames])

  useEffect(() => {
    refreshSidebar()
    const interval = setInterval(refreshSidebar, 30000)
    return () => clearInterval(interval)
  }, [refreshSidebar])

  const handleImageClick = (imageData: ImageData) => {
    setExpandedImage(imageData)
  }

  const handleExpandedImageClick = (e: React.MouseEvent) => {
    // Only close on left click, allow right click for context menu
    if (e.button === 0) { // Left click
      setExpandedImage(null)
    }
  }

  const toggleDetailsPanel = () => {
    setDetailsCollapsed(!detailsCollapsed)
  }

  return (
    <Layout title="Image Gallery" description="Browse AI generated images">
      <div className="sidebar" id="sidebar">
        <div className="sidebar-content">
          <Link href="/request" className="gen-link">
            image generation
          </Link>
          
          {imageUrls.length === 0 ? (
            <p>No images found.</p>
          ) : (
            <div className="image-list">
              {imageUrls.map((imageData, idx) => (
                <div key={idx} className="thumb-container">
                  <Image
                    src={imageData.url}
                    alt={imageData.filename}
                    title={imageData.filename}
                    onClick={() => handleImageClick(imageData)}
                    width={150}
                    height={150}
                    style={{ objectFit: 'cover' }}
                  />
                  <div className="filename-label">
                    {imageData.filename.substring(0, 8)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div className="sidebar-bottom">
          <MetricsWidget />
        </div>
      </div>
      
      <div className="main-panel" id="mainPanel">
        {expandedImage && (
          <div className="image-viewer-container" style={{ 
            display: 'flex', 
            height: '100%', 
            gap: '20px',
            padding: '20px'
          }}>
            {/* Image Section */}
            <div className="image-section" style={{ 
              flex: detailsCollapsed ? '1' : '0 0 70%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'flex 0.3s ease-in-out',
              minHeight: '400px',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
              <Image
                className="expanded-image"
                src={expandedImage.url}
                alt="Expanded"
                onMouseDown={handleExpandedImageClick}
                fill
                style={{
                  objectFit: 'contain',
                  cursor: 'pointer',
                  display: 'block',
                  opacity: 1
                }}
                onLoad={() => console.log('Image loaded successfully')}
                onError={(e) => console.error('Image failed to load:', e)}
                onContextMenu={(e) => {
                  // Allow right-click context menu
                  e.stopPropagation()
                }}
              />
            </div>
            
            {/* Details Panel */}
            <div className="details-panel-container" style={{
              flex: '0 0 30%',
              minWidth: '300px',
              transition: 'all 0.3s ease-in-out',
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              borderRadius: '8px',
              padding: '16px',
              height: 'fit-content',
              maxHeight: '90vh',
              overflowY: 'auto'
            }}>
              {/* Header - Always Visible */}
              <div 
                className="details-header" 
                onClick={toggleDetailsPanel} 
                style={{ 
                  cursor: 'pointer', 
                  userSelect: 'none',
                  borderBottom: detailsCollapsed ? 'none' : '1px solid rgba(255, 255, 255, 0.2)',
                  paddingBottom: detailsCollapsed ? '0' : '12px',
                  marginBottom: detailsCollapsed ? '0' : '12px'
                }}
              >
                <div className="collapse-indicator" style={{ 
                  fontSize: '12px', 
                  opacity: 0.7,
                  color: '#888',
                  textAlign: 'center'
                }}>
                  {detailsCollapsed ? '▶ Show Details' : '▼ Hide Details'}
                </div>
              </div>
              
              {/* Expandable Details */}
              <div 
                className="details-content"
                style={{
                  overflow: 'hidden',
                  maxHeight: detailsCollapsed ? '0' : '1000px',
                  opacity: detailsCollapsed ? 0 : 1,
                  transition: 'max-height 0.4s ease-in-out, opacity 0.3s ease-in-out',
                  transform: detailsCollapsed ? 'translateY(-10px)' : 'translateY(0)',
                }}
              >
                {/* Filename and Prompt at top of expandable content */}
                <div className="detail-item" style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  color: 'white',
                  fontSize: '14px',
                  marginBottom: '12px'
                }}>
                  <span className="detail-label" style={{ color: '#aaa' }}>Filename:</span>
                  <span className="detail-value">{expandedImage.filename}</span>
                </div>
                {expandedImage.prompt && (
                  <div className="detail-item" style={{
                    color: 'white',
                    fontSize: '14px',
                    marginBottom: '16px',
                    paddingBottom: '12px',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
                  }}>
                    <div className="detail-label" style={{ marginBottom: '4px' }}>Prompt:</div>
                    <div className="detail-value" style={{ 
                      lineHeight: '1.4',
                      fontSize: '13px'
                    }}>
                      {expandedImage.prompt}
                    </div>
                  </div>
                )}
                
                <div className="details-grid" style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr',
                  gap: '12px',
                  paddingTop: '4px'
                }}>
                  <div className="detail-item" style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between',
                    color: 'white',
                    fontSize: '14px'
                  }}>
                    <span className="detail-label" style={{ color: '#aaa' }}>Model:</span>
                    <span className="detail-value">{expandedImage.model || 'N/A'}</span>
                  </div>
                  <div className="detail-item" style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between',
                    color: 'white',
                    fontSize: '14px'
                  }}>
                    <span className="detail-label" style={{ color: '#aaa' }}>Size:</span>
                    <span className="detail-value">{expandedImage.width}×{expandedImage.height}</span>
                  </div>
                  <div className="detail-item" style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between',
                    color: 'white',
                    fontSize: '14px'
                  }}>
                    <span className="detail-label" style={{ color: '#aaa' }}>Steps:</span>
                    <span className="detail-value">{expandedImage.steps || 'N/A'}</span>
                  </div>
                  <div className="detail-item" style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between',
                    color: 'white',
                    fontSize: '14px'
                  }}>
                    <span className="detail-label" style={{ color: '#aaa' }}>CFG:</span>
                    <span className="detail-value">{expandedImage.cfg || 'N/A'}</span>
                  </div>
                  <div className="detail-item" style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between',
                    color: 'white',
                    fontSize: '14px'
                  }}>
                    <span className="detail-label" style={{ color: '#aaa' }}>Seed:</span>
                    <span className="detail-value">{expandedImage.seed || 'N/A'}</span>
                  </div>
                  <div className="detail-item" style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between',
                    color: 'white',
                    fontSize: '14px'
                  }}>
                    <span className="detail-label" style={{ color: '#aaa' }}>Generation Time:</span>
                    <span className="detail-value">{expandedImage.elapsed ? `${expandedImage.elapsed}s` : 'N/A'}</span>
                  </div>
                  {expandedImage.negativePrompt && (
                    <div className="detail-item negative-prompt" style={{
                      gridColumn: '1 / -1',
                      color: 'white',
                      fontSize: '14px'
                    }}>
                      <div className="detail-label" style={{ marginBottom: '4px' }}>Negative Prompt:</div>
                      <div className="detail-value" style={{ 
                        lineHeight: '1.4',
                        fontSize: '13px'
                      }}>
                        {expandedImage.negativePrompt}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}
