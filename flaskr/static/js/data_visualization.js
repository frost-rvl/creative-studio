document.addEventListener('DOMContentLoaded', () => {
  const iframe = document.querySelector('iframe');
  if (!iframe) {
    console.error('No iframe found');
    return;
  }
  const form = document.getElementById('artworkForm');
  const hiddenInput = document.getElementById('image_data');
  if (!hiddenInput) {
    console.error('Hidden input #image_data not found');
    return;
  }

  let iframeReady = false;

  function checkGetVisualization() {
    try {
      if (iframe.contentWindow && typeof iframe.contentWindow.getVisualization === 'function') {
        iframeReady = true;
        console.log('getVisualization is ready');
        return true;
      }
    } catch (e) {
      console.warn('Cannot access iframe.contentWindow:', e);
    }
    return false;
  }

  if (checkGetVisualization()) {
    console.log('getVisualization already available');
  } else {
    console.log('Waiting for getVisualization...');
    const interval = setInterval(() => {
      if (checkGetVisualization()) {
        clearInterval(interval);
        console.log('getVisualization detected via polling');
      }
    }, 200);
    iframe.addEventListener('load', () => {
      console.log('Iframe load event fired');
      if (checkGetVisualization()) clearInterval(interval);
    });
    setTimeout(() => {
      if (!iframeReady) console.warn('getVisualization not found after 60s');
    }, 60000);
  }

  form.addEventListener('submit', (e) => {
    if (!iframeReady) {
      e.preventDefault();
      alert('Editor is still loading. Please wait.');
      return;
    }
    e.preventDefault();
    try {
      const b64 = iframe.contentWindow.getVisualization();
      if (b64 && typeof b64 === 'string' && b64.length > 0) {
        hiddenInput.value = b64;
        console.log(`Captured visualization: ${b64.length} characters`);
        form.submit();
      } else {
        alert('No visualization generated yet.');
      }
    } catch (err) {
      e.preventDefault();
      console.error('Error:', err);
      alert('Error: ' + err.message);
    }
  });
});