export class AudioPlayer {
  constructor() {
    this.initContext();
  }

  initContext() {
    this.audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
    this.nextPlayTime = 0;
  }

  play(base64Data) {
    if (this.audioContext.state === 'suspended') {
      this.audioContext.resume();
    }
    
    const binary = atob(base64Data);
    const view = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      view[i] = binary.charCodeAt(i);
    }
    const pcm16 = new Int16Array(view.buffer);
    const audioBuffer = this.audioContext.createBuffer(1, pcm16.length, 24000);
    const channelData = audioBuffer.getChannelData(0);
    
    for (let i = 0; i < pcm16.length; i++) {
      channelData[i] = pcm16[i] / 32768.0;
    }
    
    const source = this.audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(this.audioContext.destination);
    
    if (this.nextPlayTime < this.audioContext.currentTime) {
      this.nextPlayTime = this.audioContext.currentTime;
    }
    source.start(this.nextPlayTime);
    this.nextPlayTime += audioBuffer.duration;
  }

  interrupt() {
    // A fast way to clear all queued audio is to kill the context and create a new one
    this.audioContext.close();
    this.initContext();
  }
}
