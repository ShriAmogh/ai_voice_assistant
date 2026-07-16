export class AudioRecorder {
  constructor(onData) {
    this.onData = onData;
    this.stream = null;
    this.audioContext = null;
    this.processor = null;
    this.source = null;
  }

  async start() {
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
    this.source = this.audioContext.createMediaStreamSource(this.stream);

    // Using ScriptProcessorNode for easy 16kHz PCM downsampling in browser
    this.processor = this.audioContext.createScriptProcessor(1024, 1, 1);

    this.processor.onaudioprocess = (e) => {
      const inputData = e.inputBuffer.getChannelData(0);

      // --- PCM encoding and sending ---
      const pcm16 = new Int16Array(inputData.length);
      for (let i = 0; i < inputData.length; i++) {
        let s = Math.max(-1, Math.min(1, inputData[i]));
        pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }

      const buffer = new ArrayBuffer(pcm16.buffer.byteLength);
      const view = new Uint8Array(buffer);
      view.set(new Uint8Array(pcm16.buffer));

      let binary = '';
      for (let i = 0; i < view.byteLength; i++) {
        binary += String.fromCharCode(view[i]);
      }
      const base64 = btoa(binary);
      this.onData(base64);
    };

    this.source.connect(this.processor);
    this.processor.connect(this.audioContext.destination);
  }

  stop() {
    if (this.processor) {
      this.processor.disconnect();
      this.source.disconnect();
    }
    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
    }
    if (this.audioContext) {
      this.audioContext.close();
    }
  }
}
