// Simulate fetching 5 image URLs (replace with real fetch as needed)
async function fetchImageUrls() {
  try {
        const response = await fetch('https://api.mcneely.io/v1/ai/s3list');
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        // Expecting an array of image URLs
        return Array.isArray(data) ? data : [];
    } catch (error) {
        console.error('Failed to fetch image URLs:', error);
        return [];
    }
}

let lastImageUrls = null;

async function refreshSidebar() {
    const imageUrls = await fetchImageUrls();
    
    // Check if the response differs from the last one
    if (lastImageUrls && JSON.stringify(imageUrls) === JSON.stringify(lastImageUrls)) {
        return; // No changes, skip redraw
    }
    
    lastImageUrls = imageUrls;
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
    imageUrls.forEach((url, idx) => {
        const thumb = document.createElement('img');
        thumb.src = url;
        thumb.alt = `Thumbnail ${idx+1}`;
        thumb.addEventListener('click', () => {
            expandedImage.src = url;
            expandedImage.classList.add('visible');
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
    expandedImage.addEventListener('click', () => {
        expandedImage.classList.remove('visible');
        // Optional: clear src after transition
        setTimeout(() => { expandedImage.src = ''; }, 300);
    });
}

window.onload = onPageLoad;

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
    successMsg.textContent = `Request submitted successfully! ID: ${result.data.id || 'Unknown'}`;
    successMsg.style.display = 'block';
    setTimeout(() => {
      successMsg.style.display = 'none';
      successMsg.textContent = '';
    }, 3000);
  } catch (err) {
    errorMsg.textContent = 'Error: ' + err.message;
  }
}
