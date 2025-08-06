import { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import MetricsWidget from '../components/MetricsWidget'
import Link from 'next/link'

interface ImageData {
  filename: string
  url: string
  prompt: string | null
  timestamp: string
  uuid: string
}

export default function Home() {
  const [imageUrls, setImageUrls] = useState<ImageData[]>([])
  const [lastImageFilenames, setLastImageFilenames] = useState<string[] | null>(null)
  const [expandedImage, setExpandedImage] = useState<ImageData | null>(null)

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

  const refreshSidebar = async () => {
    const newImageUrls = await fetchImageUrls()
    
    const currentFilenames = newImageUrls.map(imageData => imageData.filename)
    
    if (lastImageFilenames && JSON.stringify(currentFilenames) === JSON.stringify(lastImageFilenames)) {
      return
    }
    
    setLastImageFilenames(currentFilenames)
    setImageUrls(newImageUrls)
  }

  useEffect(() => {
    refreshSidebar()
    const interval = setInterval(refreshSidebar, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleImageClick = (imageData: ImageData) => {
    setExpandedImage(imageData)
  }

  const handleExpandedImageClick = () => {
    setExpandedImage(null)
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
                  <img
                    src={imageData.url}
                    alt={imageData.filename}
                    title={imageData.filename}
                    onClick={() => handleImageClick(imageData)}
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
          <>
            <div className="image-title">{expandedImage.filename}</div>
            {expandedImage.prompt && (
              <div className="image-prompt" style={{ display: 'block' }}>
                {expandedImage.prompt}
              </div>
            )}
          </>
        )}
        <img
          className={`expanded-image ${expandedImage ? 'visible' : ''}`}
          src={expandedImage?.url || ''}
          alt="Expanded"
          onClick={handleExpandedImageClick}
        />
      </div>
    </Layout>
  )
}
