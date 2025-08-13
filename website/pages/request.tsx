import { useState, useEffect, useCallback } from 'react'
import Layout from '../components/Layout'
import MetricsWidget from '../components/MetricsWidget'

interface JobItem {
  id: string
  timestamp: string
}

interface CompletedJob {
  uuid: string
  timestamp: string
}

export default function Request() {
  const [formData, setFormData] = useState({
    height: 512,
    width: 512,
    steps: 50,
    seed: 0,
    cfg: 5.0,
    prompt: '',
    negativePrompt: 'blurry, low quality, distorted, ugly, bad anatomy, deformed, poorly drawn',
    model: 'flux',
    regenerateSeed: true
  })
  const [errorMsg, setErrorMsg] = useState('')
  const [successMsg, setSuccessMsg] = useState('')
  const [jobs, setJobs] = useState<JobItem[]>([])
  const [completedJobs, setCompletedJobs] = useState<CompletedJob[]>([])
  const [lastCompletedUuids, setLastCompletedUuids] = useState<string[]>([])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    
    if (type === 'checkbox') {
      const target = e.target as HTMLInputElement
      setFormData(prev => ({ ...prev, [name]: target.checked }))
    } else {
      setFormData(prev => ({ ...prev, [name]: type === 'number' ? Number(value) : value }))
    }
  }

  const loadJobsFromStorage = () => {
    try {
      const jobs = localStorage.getItem('submittedJobs')
      if (jobs) {
        setJobs(JSON.parse(jobs))
      }
    } catch (error) {
      console.error('Error reading jobs from storage:', error)
    }
  }

  const saveJobToStorage = (id: string, timestamp: string) => {
    const newJob = { id, timestamp }
    const updatedJobs = [newJob, ...jobs].slice(0, 10)
    setJobs(updatedJobs)
    localStorage.setItem('submittedJobs', JSON.stringify(updatedJobs))
  }

  const loadCompletedJobs = useCallback(async () => {
    try {
      const response = await fetch('https://api.mcneely.io/v1/ai/s3list')
      if (!response.ok) throw new Error('Network response was not ok')
      const completedJobsData = await response.json()
      
      if (Array.isArray(completedJobsData) && completedJobsData.length > 0) {
        const newUuids = completedJobsData.map((job: CompletedJob) => job.uuid).sort()
        const currentUuids = lastCompletedUuids.slice().sort()
        
        // Only update if the UUID list has changed
        if (JSON.stringify(newUuids) !== JSON.stringify(currentUuids)) {
          setCompletedJobs(completedJobsData)
          setLastCompletedUuids(newUuids)
          
          // Remove submitted jobs that are now in completed jobs
          const completedUuids = new Set(newUuids)
          setJobs(prevJobs => {
            const filteredJobs = prevJobs.filter(job => !completedUuids.has(job.id))
            // Update localStorage if jobs were removed
            if (filteredJobs.length !== prevJobs.length) {
              localStorage.setItem('submittedJobs', JSON.stringify(filteredJobs))
            }
            return filteredJobs
          })
        }
      }
    } catch (error) {
      console.error('Failed to fetch completed jobs:', error)
    }
  }, [lastCompletedUuids])

  useEffect(() => {
    loadJobsFromStorage()
    loadCompletedJobs()
    
    // Set up interval to refresh completed jobs every 30 seconds
    const interval = setInterval(() => {
      loadCompletedJobs()
    }, 30000)
    
    // Cleanup interval on unmount
    return () => clearInterval(interval)
  }, [loadCompletedJobs])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg('')
    setSuccessMsg('')

    // Validation
    if (formData.height > 1024 || formData.width > 1024) {
      setErrorMsg('Height and width must not exceed 1024.')
      return
    }
    if (formData.steps > 100) {
      setErrorMsg('Steps must not exceed 100.')
      return
    }
    if (!formData.prompt) {
      setErrorMsg('Prompt is required.')
      return
    }
    if (formData.prompt.length > 10000) {
      setErrorMsg('Prompt must not exceed 10000 characters.')
      return
    }
    if (formData.negativePrompt.length > 10000) {
      setErrorMsg('Negative prompt must not exceed 10000 characters.')
      return
    }

    // Generate random seed if needed
    let finalSeed = formData.seed
    if (formData.regenerateSeed || formData.seed === 0) {
      finalSeed = Math.floor(Math.random() * (2**53 - 1))
      setFormData(prev => ({ ...prev, seed: finalSeed }))
    }

    const payload = {
      height: formData.height,
      width: formData.width,
      steps: formData.steps,
      seed: finalSeed,
      cfg: formData.cfg,
      prompt: formData.prompt,
      negativePrompt: formData.negativePrompt,
      model: formData.model
    }

    try {
      const response = await fetch('https://api.mcneely.io/v1/ai/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      
      if (!response.ok) {
        throw new Error('API request failed')
      }
      
      const result = await response.json()
      const jobId = result.data.id || 'Unknown'
      const timestamp = new Date().toLocaleString()
      
      saveJobToStorage(jobId, timestamp)
      
      setSuccessMsg(`Request submitted successfully! ID: ${jobId}`)
      setTimeout(() => setSuccessMsg(''), 3000)
    } catch (err) {
      setErrorMsg('Error: ' + (err as Error).message)
    }
  }

  return (
    <Layout title="Image Generation Request" description="Generate AI images with custom prompts">
      <div className="request-form">
        <h2>Image Generation Request</h2>
        <form onSubmit={handleSubmit}>
          <label>
            <span>Model:</span>
            <select name="model" value={formData.model} onChange={handleInputChange}>
              <option value="flux">flux</option>
              <option value="hidream">hidream</option>
              <option value="omnigen">omnigen</option>
              <option value="sd3.5">sd3.5</option>
            </select>
          </label>
          
          <label>
            <span>Height:</span>
            <input
              type="number"
              name="height"
              value={formData.height}
              min="1"
              max="1024"
              required
              onChange={handleInputChange}
            />
          </label>
          
          <label>
            <span>Width:</span>
            <input
              type="number"
              name="width"
              value={formData.width}
              min="1"
              max="1024"
              required
              onChange={handleInputChange}
            />
          </label>
          
          <label>
            <span>Steps:</span>
            <input
              type="number"
              name="steps"
              value={formData.steps}
              min="1"
              max="100"
              required
              onChange={handleInputChange}
            />
          </label>
          
          <label title="Prompt adherence - higher values make the AI follow the prompt more closely">
            <span>CFG:</span>
            <input
              type="number"
              name="cfg"
              value={formData.cfg}
              min="0"
              max="10"
              step="0.1"
              required
              onChange={handleInputChange}
            />
          </label>
          
          <div className="seed-container">
            <label title="Random number seed for reproducible results - use 0 for random generation">
              <span>Seed:</span>
              <input
                type="number"
                name="seed"
                value={formData.seed}
                min="0"
                max="9007199254740991"
                style={{ width: '200px' }}
                onChange={handleInputChange}
              />
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                name="regenerateSeed"
                checked={formData.regenerateSeed}
                onChange={handleInputChange}
              />
              regenerate
            </label>
          </div>
          
          <label>
            <span>Prompt:</span>
            <textarea
              name="prompt"
              value={formData.prompt}
              rows={4}
              required
              onChange={handleInputChange}
            />
          </label>
          
          <label>
            <span>Negative Prompt:</span>
            <textarea
              name="negativePrompt"
              value={formData.negativePrompt}
              rows={4}
              onChange={handleInputChange}
            />
          </label>
          
          {errorMsg && <div className="error">{errorMsg}</div>}
          {successMsg && <div className="success" style={{ display: 'block' }}>{successMsg}</div>}
          
          <button type="submit">Submit</button>
        </form>
      </div>
      
      <div className="jobs-panel">
        <h3>Submitted Jobs</h3>
        <div className="jobs-list">
          {jobs.map((job, idx) => (
            <div key={idx} className="job-item">
              <div className="job-timestamp">{job.timestamp}</div>
              <div className="job-id">ID: {job.id}</div>
            </div>
          ))}
          
          {completedJobs.length > 0 && (
            <>
              <div className="job-separator">--- Completed Jobs ---</div>
              {completedJobs.map((job, idx) => (
                <div key={idx} className="job-item completed-job">
                  <div className="job-timestamp">
                    {new Date(job.timestamp).toLocaleString()}
                  </div>
                  <div className="job-id">UUID: {job.uuid}</div>
                  <div className="job-status">COMPLETED</div>
                </div>
              ))}
            </>
          )}
        </div>
        
        <div style={{ marginTop: '16px' }}>
          <MetricsWidget />
        </div>
      </div>
    </Layout>
  )
}
