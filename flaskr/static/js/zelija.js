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
  const form = document.getElementById('artworkForm');

  let iframeReady = false;
  iframe.addEventListener('load', () => {
    iframeReady = true;
    console.log('Iframe loaded');
  });
  if (iframe.contentWindow && typeof iframe.contentWindow.captureGrid === 'function') {
    iframeReady = true;
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!iframeReady) {
      alert('Please wait for the editor to load.');
      return;
    }

    try {
      const csrfToken = document.querySelector('input[name="csrf_token"]').value;
      const b64 = iframe.contentWindow.captureGrid();
      if (!b64) {
        alert('Failed to capture grid – please try again.');
        return;
      }

      const blob = b64toBlob(b64, 'image/png');
      const formData = new FormData();
      formData.append('csrf_token', csrfToken);
      formData.append('artwork_image', blob, 'artwork.png');
      formData.append('title', document.getElementById('title').value);
      formData.append('description', document.getElementById('description').value);
      const action = e.submitter?.value || 'save';
      formData.append('action', action);

      const response = await fetch(location.href, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
      } else {
        const text = await response.text();
        alert(`Upload failed: ${text}`);
      }
    } catch (err) {
      console.error(err);
      alert(err.message || 'An error occurred');
    }
  });
});
