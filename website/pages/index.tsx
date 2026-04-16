import { useEffect, useState, useCallback } from 'react'
import Image from 'next/image'
import Layout from '../components/Layout'
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

  const fetchImageUrls = async (): Promise<ImageData[]> => {
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE
      if (!apiBase) {
        throw new Error('NEXT_PUBLIC_API_BASE environment variable is not set')
      }
      const response = await fetch(`${apiBase}/s3list`)
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
    
    // Auto-select first image if there are images and none is currently selected
    if (newImageUrls.length > 0 && !expandedImage) {
      setExpandedImage(newImageUrls[0])
    }
  }, [lastImageFilenames, expandedImage])

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

  return (
    <Layout title="Image Gallery" description="Browse AI generated images">
      <div style={{ display: 'flex', height: '100vh' }}>
        {/* Sidebar */}
        <div className="sidebar" id="sidebar">
          <div className="sidebar-content">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
              <Link href="/request" className="gen-link">
                image generation
              </Link>
              <Link href="/monitor" className="gen-link">
                system monitor
              </Link>
            </div>
            
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
          
          {/* Details Panel - Always Visible at Sidebar Bottom */}
          <div 
            key={expandedImage?.uuid || 'empty'} 
            className="sidebar-details-panel"
          >
            {/* Filename and Prompt */}
            <div className="detail-item rainbow-text" style={{ 
              display: 'flex', 
              justifyContent: 'space-between',
              fontSize: '11px',
              marginBottom: '8px'
            }}>
              <span className="detail-label" style={{ color: '#aaa' }}>File:</span>
              <span className="detail-value">{expandedImage?.filename || ''}</span>
            </div>
            <div className="detail-item rainbow-text" style={{
              fontSize: '11px',
              marginBottom: '8px'
            }}>
              <div className="detail-label" style={{ color: '#aaa', marginBottom: '2px' }}>Prompt:</div>
              <div className="detail-value" style={{ 
                lineHeight: '1.3',
                fontSize: '10px'
              }}>
                {expandedImage?.prompt || ''}
              </div>
            </div>
            
            {/* Technical Details */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '10px' }}>
              <div className="detail-item rainbow-text" style={{ 
                display: 'flex', 
                justifyContent: 'space-between'
              }}>
                <span className="detail-label" style={{ color: '#aaa' }}>Size:</span>
                <span className="detail-value">{expandedImage ? `${expandedImage.width}×${expandedImage.height}` : ''}</span>
              </div>
              <div className="detail-item rainbow-text" style={{ 
                display: 'flex', 
                justifyContent: 'space-between'
              }}>
                <span className="detail-label" style={{ color: '#aaa' }}>Steps:</span>
                <span className="detail-value">{expandedImage?.steps || ''}</span>
              </div>
              <div className="detail-item rainbow-text" style={{ 
                display: 'flex', 
                justifyContent: 'space-between'
              }}>
                <span className="detail-label" style={{ color: '#aaa' }}>CFG:</span>
                <span className="detail-value">{expandedImage?.cfg || ''}</span>
              </div>
              <div className="detail-item rainbow-text" style={{ 
                display: 'flex', 
                justifyContent: 'space-between'
              }}>
                <span className="detail-label" style={{ color: '#aaa' }}>Time:</span>
                <span className="detail-value">{expandedImage?.elapsed ? `${expandedImage.elapsed}s` : ''}</span>
              </div>
            </div>
            
            <div className="detail-item negative-prompt rainbow-text" style={{
              fontSize: '10px',
              marginTop: '8px'
            }}>
              <div className="detail-label" style={{ color: '#aaa', marginBottom: '2px' }}>Negative Prompt:</div>
              <div className="detail-value" style={{ 
                lineHeight: '1.3',
                fontSize: '9px'
              }}>
                {expandedImage?.negativePrompt || ''}
              </div>
            </div>
          </div>
        </div>

        {/* Main Panel - Image Display Area */}
        <div className="main-panel" id="mainPanel" style={{ flex: 1 }}>
          {expandedImage && (
            <div className="image-section" style={{ 
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '100%',
              height: '100vh',
              position: 'relative',
              padding: '20px',
              margin: '0',
              minWidth: '512px',
              minHeight: '512px'
            }}>
              <div style={{
                position: 'relative',
                width: '100%',
                height: '100%',
                minWidth: '512px',
                minHeight: '512px',
                maxWidth: '90%',
                maxHeight: '90%'
              }}>
                <Image
                  className="expanded-image"
                  src={expandedImage.url}
                  alt="Expanded"
                  onMouseDown={handleExpandedImageClick}
                  fill
                  priority
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
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}
