export class SimpleCPUChart {
  constructor() { this.isPaused = false; }
  pause() { this.isPaused = true; }
  resume() { this.isPaused = false; }
}

