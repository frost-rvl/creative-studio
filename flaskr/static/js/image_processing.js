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

  function checkGetProcessedImage() {
    try {
      if (iframe.contentWindow && typeof iframe.contentWindow.getProcessedImage === 'function') {
        iframeReady = true;
        console.log('getProcessedImage is ready');
        return true;
      } else {
        console.log("getProcessedImage not ready yet");
      }
    } catch (e) {
      console.warn('Cannot access iframe.contentWindow:', e);
    }
    return false;
  }

  if (checkGetProcessedImage()) {
    console.log('getProcessedImage already available');
  } else {
    console.log('Waiting for getProcessedImage...');
    const interval = setInterval(() => {
      if (checkGetProcessedImage()) {
        clearInterval(interval);
        console.log('getProcessedImage detected via polling');
      }
    }, 200);

    iframe.addEventListener('load', () => {
      console.log('Iframe load event fired');
      if (checkGetProcessedImage()) {
        clearInterval(interval);
      }
    });

    setTimeout(() => {
      if (!iframeReady) {
        console.warn('getProcessedImage not found after 60s – check service');
      }
    }, 60000);
  }

  form.addEventListener('submit', (e) => {
    if (!iframeReady) {
      e.preventDefault();
      alert('Editor is still loading. Please wait a moment and try again.');
      return;
    }

    e.preventDefault();

    try {
      const b64 = iframe.contentWindow.getProcessedImage();
      if (b64 && typeof b64 === 'string' && b64.length > 0) {
        hiddenInput.value = b64;
        console.log(`Captured processed image: ${b64.length} characters`);
        form.submit();
      } else {
        alert('No processed image found. Please apply at least one effect first.');
      }
    } catch (err) {
      e.preventDefault();
      console.error('Error capturing processed image:', err);
      alert('Error: ' + err.message);
    }
  });
});