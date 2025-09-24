let mediaRecorder;
let audioChunks = [];

chrome.runtime.onMessage.addListener((request) => {
    if (request.target !== 'offscreen') return;

    if (request.action === 'startRecording') {
        startRecording();
    } else if (request.action === 'stopRecording') {
        stopRecording();
    }
});

async function startRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        console.log("Recording is already in progress.");
        return;
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

        mediaRecorder.ondataavailable = event => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = () => {
            // Check if any audio data was actually recorded
            if (audioChunks.length === 0) {
                console.warn("No audio data was recorded. Aborting send.");
                chrome.runtime.sendMessage({ action: 'recordingError', error: 'Nothing was recorded.' });
                stream.getTracks().forEach(track => track.stop());
                return; // Exit if no data
            }

            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            const audioDataUrl = URL.createObjectURL(audioBlob);
            chrome.runtime.sendMessage({ action: 'recordingStopped', audioDataUrl: audioDataUrl });
            
            // Stop stream tracks to turn off the mic icon and release resources
            stream.getTracks().forEach(track => track.stop());
            audioChunks = [];
        };

        mediaRecorder.start();
    } catch (error) {
        console.error("Failed to start recording:", error);
        chrome.runtime.sendMessage({ action: 'recordingError', error: error.message });
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
}