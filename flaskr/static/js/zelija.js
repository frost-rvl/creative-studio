function b64toBlob(b64, type) {
  const byteString = atob(b64);
  const bytes = new Uint8Array(byteString.length);
  for (let i = 0; i < byteString.length; i++) {
    bytes[i] = byteString.charCodeAt(i);
  }
  return new Blob([bytes], { type });
}

document.addEventListener('DOMContentLoaded', () => {
  const iframe = document.querySelector('iframe[src^="/pygbag"]');
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

  function checkCaptureGrid() {
    try {
      if (iframe.contentWindow && typeof iframe.contentWindow.captureGrid === 'function') {
        iframeReady = true;
        console.log('captureGrid is ready');
        return true;
      }
    } catch (e) {
      console.warn('Cannot access iframe.contentWindow:', e);
    }
    return false;
  }

  if (checkCaptureGrid()) {
    console.log('captureGrid already available');
  } else {
    console.log('Waiting for captureGrid...');
    const interval = setInterval(() => {
      if (checkCaptureGrid()) {
        clearInterval(interval);
        console.log('captureGrid detected via polling');
      }
    }, 200);

    iframe.addEventListener('load', () => {
      console.log('Iframe load event fired');
      if (checkCaptureGrid()) {
        clearInterval(interval);
      }
    });

    setTimeout(() => {
      if (!iframeReady) {
        console.warn('captureGrid not found after 10s – check Pygbag script');
      }
    }, 10000);
  }

  form.addEventListener('submit', (e) => {
    if (!iframeReady) {
      e.preventDefault();
      alert('Editor is still loading. Please wait a moment and try again.');
      return;
    }

    try {
      const b64 = iframe.contentWindow.captureGrid();
      if (b64 && typeof b64 === 'string' && b64.length > 0) {
        if (b64.startsWith('data:image'))
          b64 = b64.split(',')[1];
        if (!/^[A-Za-z0-9+/=]+$/.test(b64))
          console.warn('Captured string does not look like valid base64 – might be corrupt');
        hiddenInput.value = b64;
        console.log(`Captured grid: ${b64.length} characters`);
      } else {
        e.preventDefault();
        alert('Failed to capture grid – returned empty.');
      }
    } catch (err) {
      e.preventDefault();
      console.error('Error capturing grid:', err);
      alert('Error capturing grid: ' + err.message);
    }
  });
});