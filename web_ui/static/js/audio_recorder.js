/**
 * Ambient Nursing Ally (ANA) — Audio Ingestion & Recording Controller
 * Handles live browser microphone capture, 16kHz PCM WAV encoding,
 * real-time waveform visualization, and audio file uploads.
 */

class ANAAudioRecorder {
    constructor() {
        this.audioContext = null;
        this.mediaStream = null;
        this.analyser = null;
        this.scriptProcessor = null;
        this.audioInput = null;
        
        this.isRecording = false;
        this.recordedChunks = [];
        this.recordingStartTime = null;
        this.timerInterval = null;
        this.animationFrameId = null;
        
        this.canvas = document.getElementById("waveformCanvas");
        this.canvasCtx = this.canvas ? this.canvas.getContext("2d") : null;
        
        this.recordBtn = document.getElementById("btnRecord");
        this.stopBtn = document.getElementById("btnStop");
        this.timerDisplay = document.getElementById("recordTimer");
        this.audioPlayer = document.getElementById("audioPlayback");
        this.recordingStatus = document.getElementById("recordingStatus");
        this.vuMeterBar = document.getElementById("vuMeterBar");
        
        this.currentAudioPayload = null; // { filename, relative_path, duration_sec, size_kb }
        
        this.initEventListeners();
        this.drawIdleWaveform();
    }
    
    initEventListeners() {
        if (this.recordBtn) {
            this.recordBtn.addEventListener("click", () => this.startRecording());
        }
        if (this.stopBtn) {
            this.stopBtn.addEventListener("click", () => this.stopRecording());
        }
        
        // File upload listener
        const fileInput = document.getElementById("audioFileInput");
        if (fileInput) {
            fileInput.addEventListener("change", (e) => this.handleFileUpload(e.target.files[0]));
        }
        
        // Drag and drop zone
        const dropZone = document.getElementById("audioDropZone");
        if (dropZone) {
            ["dragenter", "dragover"].forEach(name => {
                dropZone.addEventListener(name, (e) => {
                    e.preventDefault();
                    dropZone.classList.add("border-blue-500", "bg-blue-50/20");
                });
            });
            ["dragleave", "drop"].forEach(name => {
                dropZone.addEventListener(name, (e) => {
                    e.preventDefault();
                    dropZone.classList.remove("border-blue-500", "bg-blue-50/20");
                });
            });
            dropZone.addEventListener("drop", (e) => {
                if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                    this.handleFileUpload(e.dataTransfer.files[0]);
                }
            });
        }
    }
    
    drawIdleWaveform() {
        if (!this.canvas || !this.canvasCtx) return;
        const width = this.canvas.width;
        const height = this.canvas.height;
        this.canvasCtx.fillStyle = "#0f172a"; // dark slate background
        this.canvasCtx.fillRect(0, 0, width, height);
        
        this.canvasCtx.strokeStyle = "#334155";
        this.canvasCtx.lineWidth = 2;
        this.canvasCtx.beginPath();
        this.canvasCtx.moveTo(0, height / 2);
        this.canvasCtx.lineTo(width, height / 2);
        this.canvasCtx.stroke();
    }
    
    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });
            
            this.mediaStream = stream;
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            this.audioContext = new AudioContextClass({ sampleRate: 16000 });
            
            this.audioInput = this.audioContext.createMediaStreamSource(stream);
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 1024;
            
            // 4096 buffer size, 1 input channel, 1 output channel
            this.scriptProcessor = this.audioContext.createScriptProcessor(4096, 1, 1);
            this.recordedChunks = [];
            
            this.scriptProcessor.onaudioprocess = (e) => {
                if (!this.isRecording) return;
                const channelData = e.inputBuffer.getChannelData(0);
                this.recordedChunks.push(new Float32Array(channelData));
            };
            
            this.audioInput.connect(this.analyser);
            this.analyser.connect(this.scriptProcessor);
            this.scriptProcessor.connect(this.audioContext.destination);
            
            this.isRecording = true;
            this.recordingStartTime = Date.now();
            
            // UI Updates
            if (this.recordBtn) this.recordBtn.classList.add("hidden");
            if (this.stopBtn) this.stopBtn.classList.remove("hidden");
            if (this.recordingStatus) {
                this.recordingStatus.innerHTML = `
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800 animate-pulse">
                        <span class="w-2 h-2 mr-1.5 bg-red-500 rounded-full"></span>
                        RECORDING AMBIENT SPEECH (16 kHz PCM)
                    </span>
                `;
            }
            
            this.startTimer();
            this.visualize();
            
        } catch (err) {
            console.error("Microphone access error:", err);
            alert("Unable to access microphone: " + err.message + "\nPlease check browser microphone permissions.");
        }
    }
    
    startTimer() {
        if (this.timerInterval) clearInterval(this.timerInterval);
        this.timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.recordingStartTime) / 1000);
            const mins = String(Math.floor(elapsed / 60)).padStart(2, "0");
            const secs = String(elapsed % 60).padStart(2, "0");
            if (this.timerDisplay) this.timerDisplay.textContent = `${mins}:${secs}`;
        }, 200);
    }
    
    stopRecording() {
        if (!this.isRecording) return;
        this.isRecording = false;
        
        if (this.timerInterval) clearInterval(this.timerInterval);
        if (this.animationFrameId) cancelAnimationFrame(this.animationFrameId);
        
        // Stop audio tracks
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
        }
        
        if (this.scriptProcessor) {
            this.scriptProcessor.disconnect();
        }
        if (this.analyser) {
            this.analyser.disconnect();
        }
        if (this.audioInput) {
            this.audioInput.disconnect();
        }
        
        // UI Updates
        if (this.recordBtn) this.recordBtn.classList.remove("hidden");
        if (this.stopBtn) this.stopBtn.classList.add("hidden");
        if (this.recordingStatus) {
            this.recordingStatus.innerHTML = `
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                    ✅ RECORDING COMPLETED & ENCODED
                </span>
            `;
        }
        
        // Encode raw PCM to standard 16-bit Mono WAV
        const sampleRate = this.audioContext ? this.audioContext.sampleRate : 16000;
        const wavBlob = this.encodeWAV(this.recordedChunks, sampleRate);
        
        // Set local audio playback
        const audioUrl = URL.createObjectURL(wavBlob);
        if (this.audioPlayer) {
            this.audioPlayer.src = audioUrl;
            this.audioPlayer.classList.remove("hidden");
        }
        
        // Upload audio to server
        this.uploadAudioBlob(wavBlob, "mic_utterance.wav");
        this.drawIdleWaveform();
    }
    
    visualize() {
        if (!this.analyser || !this.canvasCtx || !this.canvas) return;
        
        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        const draw = () => {
            if (!this.isRecording) return;
            this.animationFrameId = requestAnimationFrame(draw);
            
            this.analyser.getByteTimeDomainData(dataArray);
            
            // Calculate VU / volume level
            let sum = 0;
            for (let i = 0; i < bufferLength; i++) {
                const val = (dataArray[i] - 128) / 128;
                sum += val * val;
            }
            const rms = Math.sqrt(sum / bufferLength);
            const vuPercent = Math.min(100, Math.round(rms * 250));
            if (this.vuMeterBar) {
                this.vuMeterBar.style.width = `${vuPercent}%`;
                if (vuPercent > 60) {
                    this.vuMeterBar.className = "h-full bg-amber-500 transition-all duration-75";
                } else if (vuPercent > 80) {
                    this.vuMeterBar.className = "h-full bg-red-500 transition-all duration-75";
                } else {
                    this.vuMeterBar.className = "h-full bg-cyan-400 transition-all duration-75";
                }
            }
            
            const width = this.canvas.width;
            const height = this.canvas.height;
            
            this.canvasCtx.fillStyle = "#090d16";
            this.canvasCtx.fillRect(0, 0, width, height);
            
            // Grid lines
            this.canvasCtx.strokeStyle = "rgba(51, 65, 85, 0.4)";
            this.canvasCtx.lineWidth = 1;
            this.canvasCtx.beginPath();
            this.canvasCtx.moveTo(0, height / 2);
            this.canvasCtx.lineTo(width, height / 2);
            this.canvasCtx.stroke();
            
            // Waveform path
            this.canvasCtx.lineWidth = 2.5;
            this.canvasCtx.strokeStyle = "#38bdf8"; // bright cyan
            this.canvasCtx.shadowBlur = 8;
            this.canvasCtx.shadowColor = "#0284c7";
            this.canvasCtx.beginPath();
            
            const sliceWidth = width / bufferLength;
            let x = 0;
            
            for (let i = 0; i < bufferLength; i++) {
                const v = dataArray[i] / 128.0;
                const y = (v * height) / 2;
                
                if (i === 0) {
                    this.canvasCtx.moveTo(x, y);
                } else {
                    this.canvasCtx.lineTo(x, y);
                }
                x += sliceWidth;
            }
            
            this.canvasCtx.stroke();
            this.canvasCtx.shadowBlur = 0; // reset
        };
        
        draw();
    }
    
    encodeWAV(chunks, sampleRate) {
        // Flatten float32 chunks
        let totalLength = 0;
        for (let i = 0; i < chunks.length; i++) {
            totalLength += chunks[i].length;
        }
        const flatBuffer = new Float32Array(totalLength);
        let offset = 0;
        for (let i = 0; i < chunks.length; i++) {
            flatBuffer.set(chunks[i], offset);
            offset += chunks[i].length;
        }
        
        // 16-bit PCM RIFF WAV creation
        const buffer = new ArrayBuffer(44 + totalLength * 2);
        const view = new DataView(buffer);
        
        const writeString = (view, offset, string) => {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        };
        
        /* RIFF identifier */
        writeString(view, 0, 'RIFF');
        /* file length */
        view.setUint32(4, 36 + totalLength * 2, true);
        /* RIFF type */
        writeString(view, 8, 'WAVE');
        /* format chunk identifier */
        writeString(view, 12, 'fmt ');
        /* format chunk length */
        view.setUint32(16, 16, true);
        /* sample format (1 = PCM) */
        view.setUint16(20, 1, true);
        /* channel count (1 = mono) */
        view.setUint16(22, 1, true);
        /* sample rate */
        view.setUint32(24, sampleRate, true);
        /* byte rate (sampleRate * 1 * 2) */
        view.setUint32(28, sampleRate * 2, true);
        /* block align (1 * 2) */
        view.setUint16(32, 2, true);
        /* bits per sample */
        view.setUint16(34, 16, true);
        /* data chunk identifier */
        writeString(view, 36, 'data');
        /* data chunk length */
        view.setUint32(40, totalLength * 2, true);
        
        // Write PCM samples clamped to signed 16-bit integers
        let pcmOffset = 44;
        for (let i = 0; i < totalLength; i++) {
            const s = Math.max(-1, Math.min(1, flatBuffer[i]));
            view.setInt16(pcmOffset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
            pcmOffset += 2;
        }
        
        return new Blob([view], { type: 'audio/wav' });
    }
    
    async uploadAudioBlob(blob, filename) {
        const formData = new FormData();
        formData.append("audio", blob, filename);
        
        const statusEl = document.getElementById("audioTelemetryBadge");
        if (statusEl) {
            statusEl.innerHTML = `<span class="text-xs text-blue-600 font-medium">Uploading and computing audio telemetry...</span>`;
        }
        
        try {
            const res = await fetch("/api/upload_audio", {
                method: "POST",
                body: formData
            });
            const data = await res.json();
            
            if (data.success) {
                this.currentAudioPayload = data;
                this.updateTelemetryUI(data);
            } else {
                alert("Audio ingestion failed: " + data.error);
            }
        } catch (err) {
            console.error("Upload error:", err);
            alert("Server upload error: " + err.message);
        }
    }
    
    async handleFileUpload(file) {
        if (!file) return;
        
        // Local preview
        const audioUrl = URL.createObjectURL(file);
        if (this.audioPlayer) {
            this.audioPlayer.src = audioUrl;
            this.audioPlayer.classList.remove("hidden");
        }
        
        await this.uploadAudioBlob(file, file.name);
    }
    
    updateTelemetryUI(telemetry) {
        const badge = document.getElementById("audioTelemetryBadge");
        if (badge) {
            badge.innerHTML = `
                <div class="flex items-center space-x-3 text-xs bg-slate-100 dark:bg-slate-800 p-2.5 rounded-lg border border-slate-200 dark:border-slate-700">
                    <span class="font-semibold text-slate-700 dark:text-slate-300">File: <span class="font-mono text-blue-600 dark:text-blue-400">${telemetry.filename}</span></span>
                    <span class="text-slate-400">|</span>
                    <span>⏱️ Duration: <strong>${telemetry.duration_sec}s</strong></span>
                    <span class="text-slate-400">|</span>
                    <span>⚡ Sample Rate: <strong>${telemetry.sample_rate} Hz</strong></span>
                    <span class="text-slate-400">|</span>
                    <span>📦 Size: <strong>${telemetry.size_kb} KB</strong></span>
                </div>
            `;
        }
        
        // Enable Process Button
        const runBtn = document.getElementById("btnRunPipeline");
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.classList.remove("opacity-50", "cursor-not-allowed");
            runBtn.classList.add("hover:bg-blue-700", "shadow-lg");
        }
    }
    
}

// Global instance
window.anaRecorder = null;
document.addEventListener("DOMContentLoaded", () => {
    window.anaRecorder = new ANAAudioRecorder();
});
