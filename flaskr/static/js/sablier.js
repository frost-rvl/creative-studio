function b64toBlob(b64, type) {
  const byteString = atob(b64);
  const bytes = new Uint8Array(byteString.length);
  for (let i = 0; i < byteString.length; i++) {
    bytes[i] = byteString.charCodeAt(i);
  }
  return new Blob([bytes], { type });
}

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

  function checkCaptureArt() {
    try {
      if (iframe.contentWindow && typeof iframe.contentWindow.captureArt === 'function') {
        iframeReady = true;
        console.log('captureArt is ready');
        return true;
      } else {
        console.log("captureArt not ready yet");
      }
    } catch (e) {
      console.warn('Cannot access iframe.contentWindow:', e);
    }
    return false;
  }

  if (checkCaptureArt()) {
    console.log('captureArt already available');
  } else {
    console.log('Waiting for captureArt...');
    const interval = setInterval(() => {
      if (checkCaptureArt()) {
        clearInterval(interval);
        console.log('captureArt detected via polling');
      }
    }, 200);

    iframe.addEventListener('load', () => {
      console.log('Iframe load event fired');
      if (checkCaptureArt()) {
        clearInterval(interval);
      }
    });

    setTimeout(() => {
      if (!iframeReady) {
        console.warn('captureArt not found after 60s – check Hourglass script');
      }
    }, 60000);
  }

  form.addEventListener('submit', (e) => {
    if (!iframeReady) {
      e.preventDefault();
      alert('Editor is still loading. Please wait a moment and try again.');
      return;
    }

    try {
      const b64 = iframe.contentWindow.captureArt();
      if (b64 && typeof b64 === 'string' && b64.length > 0) {
        // Strip data URL prefix if present
        if (b64.startsWith('data:image')) {
          b64 = b64.split(',')[1];
        }
        // Basic base64 validation
        if (!/^[A-Za-z0-9+/=]+$/.test(b64)) {
          console.warn('Captured string does not look like valid base64 – might be corrupt');
        }
        hiddenInput.value = b64;
        console.log(`Captured art: ${b64.length} characters`);
      } else {
        e.preventDefault();
        alert('Failed to capture art – returned empty.');
      }
    } catch (err) {
      e.preventDefault();
      console.error('Error capturing art:', err);
      alert('Error capturing art: ' + err.message);
    }
  });
});