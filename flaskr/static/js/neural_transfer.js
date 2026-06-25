document.addEventListener('DOMContentLoaded', () => {
    const iframe = document.querySelector('iframe[src^="/style-transfer"]');
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

    function checkGetStyledImage() {
        try {
            if (iframe.contentWindow && typeof iframe.contentWindow.getStyledImage === 'function') {
                iframeReady = true;
                console.log('getStyledImage is ready');
                return true;
            }
        } catch (e) {
            console.warn('Cannot access iframe.contentWindow:', e);
        }
        return false;
    }

    if (checkGetStyledImage()) {
        console.log('getStyledImage already available');
    } else {
        console.log('Waiting for getStyledImage...');
        const interval = setInterval(() => {
            if (checkGetStyledImage()) {
                clearInterval(interval);
                console.log('getStyledImage detected via polling');
            }
        }, 200);

        iframe.addEventListener('load', () => {
            console.log('Iframe load event fired');
            if (checkGetStyledImage()) {
                clearInterval(interval);
            }
        });

        setTimeout(() => {
            if (!iframeReady) {
                console.warn('getStyledImage not found after 10s – check service');
            }
        }, 10000);
    }

    let clickedAction = 'save';

    document.querySelectorAll('[name="action"]').forEach(btn => {
        btn.addEventListener('click', () => { clickedAction = btn.value; });
    });

    form.addEventListener('submit', (e) => {
        if (!iframeReady) {
            e.preventDefault();
            alert('Editor is still loading. Please wait and try again.');
            return;
        }

        e.preventDefault(); // stop normal submit to capture

        try {
            const b64 = iframe.contentWindow.getStyledImage();
            if (b64 && b64.length > 0) {
                hiddenInput.value = b64;
                // inject action into form before submitting
                let actionInput = form.querySelector('input[name="action"]');
                if (!actionInput) {
                    actionInput = document.createElement('input');
                    actionInput.type = 'hidden';
                    actionInput.name = 'action';
                    form.appendChild(actionInput);
                }
                actionInput.value = clickedAction;
                form.submit();
            } else {
                alert('No styled image found. Please generate a style transfer first.');
            }
        } catch (err) {
            console.error('Error capturing styled image:', err);
            alert('Error: ' + err.message);
        }
    });
});