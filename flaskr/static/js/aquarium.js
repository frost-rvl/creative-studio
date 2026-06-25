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

  function checkCapture() {
    try {
      if (iframe.contentWindow && typeof iframe.contentWindow.captureAquarium === 'function') {
        iframeReady = true;
        console.log('captureAquarium is ready');
        return true;
      }
    } catch (e) {
      console.warn('Cannot access iframe.contentWindow:', e);
    }
    return false;
  }

  if (checkCapture()) {
    console.log('captureAquarium already available');
  } else {
    console.log('Waiting for captureAquarium...');
    const interval = setInterval(() => {
      if (checkCapture()) {
        clearInterval(interval);
        console.log('captureAquarium detected via polling');
      }
    }, 200);
    iframe.addEventListener('load', () => {
      console.log('Iframe load event fired');
      if (checkCapture()) clearInterval(interval);
    });
    setTimeout(() => {
      if (!iframeReady) console.warn('captureAquarium not found after 60s');
    }, 60000);
  }

  form.addEventListener('submit', (e) => {
    if (!iframeReady) {
      e.preventDefault();
      alert('Editor is still loading. Please wait.');
      return;
    }
    try {
      let b64 = iframe.contentWindow.captureAquarium();
      if (b64 && typeof b64 === 'string' && b64.length > 0) {
        if (b64.startsWith('data:image')) b64 = b64.split(',')[1];
        hiddenInput.value = b64;
        console.log(`Captured aquarium: ${b64.length} characters`);
      } else {
        e.preventDefault();
        alert('Failed to capture aquarium.');
      }
    } catch (err) {
      e.preventDefault();
      console.error('Error:', err);
      alert('Error: ' + err.message);
    }
  });
});