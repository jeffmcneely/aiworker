// Simulate fetching 5 image URLs (replace with real fetch as needed)
async function fetchImageUrls() {
    const sidebar = document.getElementById('image_area');
    sidebar.className = 'loader'; // Show loading state
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

async function onPageLoad() {
    const imageUrls = await fetchImageUrls();
    const sidebar = document.getElementById('image_area');
    const expandedImage = document.getElementById('expandedImage');
    const mainPanel = document.getElementById('mainPanel');

    // Clear existing content
    sidebar.replaceChildren();
    // Populate sidebar with thumbnails
    if (imageUrls.length === 0) {
        sidebar.innerHTML = '<p>No images found.</p>';
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
    successMsg.textContent = 'Request submitted successfully!';
    successMsg.style.display = 'block';
    setTimeout(() => {
      successMsg.style.display = 'none';
      successMsg.textContent = '';
    }, 3000);
  } catch (err) {
    errorMsg.textContent = 'Error: ' + err.message;
  }
}
