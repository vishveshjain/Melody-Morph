const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileName = document.getElementById('fileName');
const convertBtn = document.getElementById('convertBtn');
const instrumentGrid = document.getElementById('instrumentGrid');
const statusText = document.getElementById('statusText');
const statusBar = document.getElementById('statusBar');
const outputLabel = document.getElementById('outputLabel');
const audioPlayer = document.getElementById('audioPlayer');
const downloadLink = document.getElementById('downloadLink');
const audioControls = document.getElementById('audioControls');
const inputViz = document.getElementById('inputViz');
const outputViz = document.getElementById('outputViz');

let selectedFile = null;
let selectedInstrument = 'Flute'; // Default

// Instrument Selection
instrumentGrid.addEventListener('click', (e) => {
    const card = e.target.closest('.inst-card');
    if (card) {
        // Remove active from all
        document.querySelectorAll('.inst-card').forEach(c => c.classList.remove('active'));
        // Add active to clicked
        card.classList.add('active');
        selectedInstrument = card.dataset.value;
        outputLabel.textContent = selectedInstrument.toUpperCase();
    }
});

// File Upload Handling
dropZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
        handleFile(e.target.files[0]);
    }
});

// Drag and Drop
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

dropZone.addEventListener('dragover', () => {
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    dropZone.classList.remove('dragover');
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length) {
        handleFile(files[0]);
    }
});

function handleFile(file) {
    if (!file.type.startsWith('audio/')) {
        alert('Please upload an audio file.');
        return;
    }
    selectedFile = file;
    fileName.textContent = file.name;
    convertBtn.disabled = false;

    // Update Input Viz Placeholder
    inputViz.innerHTML = '<div style="color: #10b981; font-size: 2rem;"><i class="fa-solid fa-file-audio"></i></div>';

    updateStatus('READY TO CONVERT', 'ready');
}

// Conversion
convertBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('instrument', selectedInstrument);

    updateStatus('PROCESSING...', 'processing');
    convertBtn.disabled = true;
    convertBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';

    // Reset output
    audioControls.style.display = 'none';
    outputViz.innerHTML = '<div class="wave-placeholder">Morphing melody...</div>';

    try {
        const response = await fetch('http://localhost:8000/convert', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Conversion failed');
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        audioPlayer.src = url;
        downloadLink.href = url;
        downloadLink.download = `converted_${selectedFile.name.split('.')[0]}_${selectedInstrument}.mp3`;

        audioControls.style.display = 'flex';
        outputViz.innerHTML = '<div style="color: #6366f1; font-size: 2rem;"><i class="fa-solid fa-music"></i></div>';

        updateStatus('COMPLETED', 'ready');
    } catch (error) {
        updateStatus(`ERROR: ${error.message}`, 'error');
        console.error(error);
    } finally {
        convertBtn.disabled = false;
        convertBtn.innerHTML = '<i class="fa-solid fa-play"></i> Start Transformation';
    }
});

// Microphone Handling
let mediaRecorder;
let audioChunks = [];
let isRecording = false;

const micBtn = document.getElementById('micBtn');
const uploadBtn = document.getElementById('uploadBtn');

micBtn.addEventListener('click', async () => {
    if (!isRecording) {
        startRecording();
    } else {
        stopRecording();
    }
});

uploadBtn.addEventListener('click', () => {
    // Switch back to upload mode UI if needed
    micBtn.classList.remove('active');
    uploadBtn.classList.add('active');
    dropZone.style.display = 'block';
});

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const audioFile = new File([audioBlob], "recording.wav", { type: "audio/wav" });
            handleFile(audioFile);

            // Stop all tracks to release mic
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        isRecording = true;

        // UI Updates
        micBtn.classList.add('active');
        micBtn.innerHTML = '<i class="fa-solid fa-stop"></i> Stop Recording';
        micBtn.style.color = '#ef4444';
        uploadBtn.classList.remove('active');

        updateStatus('RECORDING...', 'processing');
        inputViz.innerHTML = '<div style="color: #ef4444; font-size: 2rem;" class="fa-beat"><i class="fa-solid fa-microphone-lines"></i></div>';

    } catch (err) {
        console.error("Error accessing microphone:", err);
        alert("Could not access microphone. Please ensure you have granted permission.");
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;

        // UI Updates
        micBtn.innerHTML = '<i class="fa-solid fa-microphone"></i> Microphone';
        micBtn.style.color = '';
        updateStatus('RECORDING FINISHED', 'ready');
    }
}

function updateStatus(text, type) {
    statusText.textContent = text;
    statusBar.className = 'status-bar ' + type;
}
