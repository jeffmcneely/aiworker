// Simulate fetching 5 image URLs (replace with real fetch as needed)
async function fetchImageUrls() {
  try {
        const response = await fetch('https://api.mcneely.io/v1/ai/s3list');
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        // Expecting an array of objects with filename and url properties
        return Array.isArray(data) ? data : [];
    } catch (error) {
        console.error('Failed to fetch image URLs:', error);
        return [];
    }
}

let lastImageFilenames = null;

async function refreshSidebar() {
    const imageUrls = await fetchImageUrls();
    
    // Extract just the filenames for comparison
    const currentFilenames = imageUrls.map(imageData => imageData.filename);
    
    // Check if the filenames differ from the last ones
    if (lastImageFilenames && JSON.stringify(currentFilenames) === JSON.stringify(lastImageFilenames)) {
        return; // No changes, skip redraw
    }
    
    lastImageFilenames = currentFilenames;
    const sidebar = document.getElementById('sidebar');
    const expandedImage = document.getElementById('expandedImage');

    // Clear existing thumbnails but keep the generation link
    const genLink = sidebar.querySelector('.gen-link');
    sidebar.innerHTML = '';
    if (genLink) {
        sidebar.appendChild(genLink);
    }

    // Populate sidebar with thumbnails
    if (imageUrls.length === 0) {
        const noImages = document.createElement('p');
        noImages.textContent = 'No images found.';
        sidebar.appendChild(noImages);
        return;
    }
    imageUrls.forEach((imageData, idx) => {
        const thumb = document.createElement('img');
        thumb.src = imageData.url;
        thumb.alt = imageData.filename;
        thumb.title = imageData.filename; // Show filename on hover
        thumb.addEventListener('click', () => {
            expandedImage.src = imageData.url;
            expandedImage.classList.add('visible');
            // Show filename at the top of the page
            const imageTitle = document.getElementById('imageTitle');
            imageTitle.textContent = imageData.filename;
        });
        sidebar.appendChild(thumb);
    });
}

async function onPageLoad() {
    const expandedImage = document.getElementById('expandedImage');

    // Initial load
    await refreshSidebar();

    // Set up auto-refresh every 30 seconds
    setInterval(refreshSidebar, 30000);

    // Hide expanded image on click
    if (expandedImage) {
        expandedImage.addEventListener('click', () => {
            expandedImage.classList.remove('visible');
            // Clear filename when hiding image
            const imageTitle = document.getElementById('imageTitle');
            if (imageTitle) {
                imageTitle.textContent = '';
            }
            // Optional: clear src after transition
            setTimeout(() => { expandedImage.src = ''; }, 300);
        });
    }
    
    // Load submitted jobs from storage
    loadJobsFromStorage();
}

window.onload = onPageLoad;

// Job tracking functionality
function addJobToList(id, timestamp) {
    const jobsList = document.getElementById('jobsList');
    if (!jobsList) return; // Jobs panel not available on this page
    
    const jobItem = document.createElement('div');
    jobItem.className = 'job-item';
    
    const timestampDiv = document.createElement('div');
    timestampDiv.className = 'job-timestamp';
    timestampDiv.textContent = timestamp;
    
    const idDiv = document.createElement('div');
    idDiv.className = 'job-id';
    idDiv.textContent = `ID: ${id}`;
    
    jobItem.appendChild(timestampDiv);
    jobItem.appendChild(idDiv);
    
    // Add to the top of the list
    jobsList.insertBefore(jobItem, jobsList.firstChild);
    
    // Keep only the last 10 jobs
    while (jobsList.children.length > 10) {
        jobsList.removeChild(jobsList.lastChild);
    }
    
    // Save to localStorage
    saveJobToStorage(id, timestamp);
}

function saveJobToStorage(id, timestamp) {
    const jobs = getJobsFromStorage();
    jobs.unshift({ id, timestamp });
    
    // Keep only the last 10 jobs
    const limitedJobs = jobs.slice(0, 10);
    localStorage.setItem('submittedJobs', JSON.stringify(limitedJobs));
}

function getJobsFromStorage() {
    try {
        const jobs = localStorage.getItem('submittedJobs');
        return jobs ? JSON.parse(jobs) : [];
    } catch (error) {
        console.error('Error reading jobs from storage:', error);
        return [];
    }
}

function loadJobsFromStorage() {
    const jobsList = document.getElementById('jobsList');
    if (!jobsList) return; // Jobs panel not available on this page
    
    const jobs = getJobsFromStorage();
    jobs.forEach(job => {
        const jobItem = document.createElement('div');
        jobItem.className = 'job-item';
        
        const timestampDiv = document.createElement('div');
        timestampDiv.className = 'job-timestamp';
        timestampDiv.textContent = job.timestamp;
        
        const idDiv = document.createElement('div');
        idDiv.className = 'job-id';
        idDiv.textContent = `ID: ${job.id}`;
        
        jobItem.appendChild(timestampDiv);
        jobItem.appendChild(idDiv);
        jobsList.appendChild(jobItem);
    });
}

// Initialize jobs list when page loads
document.addEventListener('DOMContentLoaded', loadJobsFromStorage);

// JavaScript for request.html
async function submitRequest(event) {
  event.preventDefault();
  const height = parseInt(document.getElementById('height').value, 10);
  const width = parseInt(document.getElementById('width').value, 10);
  const steps = parseInt(document.getElementById('steps').value, 10);
  const prompt = document.getElementById('prompt').value.trim();
  const model = document.getElementById('model').value;
  const errorMsg = document.getElementById('errorMsg');
  const successMsg = document.getElementById('successMsg');
  errorMsg.textContent = '';
  successMsg.style.display = 'none';
  successMsg.textContent = '';

  if (height > 1024 || width > 1024) {
    errorMsg.textContent = 'Height and width must not exceed 1024.';
    return;
  }
  if (steps > 100) {
    errorMsg.textContent = 'Steps must not exceed 100.';
    return;
  }
  if (!prompt) {
    errorMsg.textContent = 'Prompt is required.';
    return;
  }
  if (prompt.length > 10000) {
    errorMsg.textContent = 'Prompt must not exceed 10000 characters.';
    return;
  }

  const payload = { height, width, steps, prompt, model };

  try {
    const response = await fetch('https://api.mcneely.io/v1/ai/request', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      throw new Error('API request failed');
    }
    const result = await response.json();
    const jobId = result.data.id || 'Unknown';
    const timestamp = new Date().toLocaleString();
    
    // Add job to the submitted jobs list
    addJobToList(jobId, timestamp);
    
    successMsg.textContent = `Request submitted successfully! ID: ${jobId}`;
    successMsg.style.display = 'block';
    setTimeout(() => {
      successMsg.style.display = 'none';
      successMsg.textContent = '';
    }, 3000);
  } catch (err) {
    errorMsg.textContent = 'Error: ' + err.message;
  }
}
