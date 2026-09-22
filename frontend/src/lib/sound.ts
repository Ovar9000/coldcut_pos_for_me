// Web Audio API offline sound synthesizer for POS scanner feedback
// Zero external audio files required, runs 100% offline

class SoundController {
  private ctx: AudioContext | null = null
  private _enabled: boolean = true

  constructor() {
    try {
      const saved = localStorage.getItem('pos_sound_enabled')
      this._enabled = saved !== null ? saved === 'true' : true
    } catch {
      this._enabled = true
    }
  }

  get enabled(): boolean {
    return this._enabled
  }

  set enabled(val: boolean) {
    this._enabled = val
    try {
      localStorage.setItem('pos_sound_enabled', String(val))
    } catch {
      // ignore
    }
  }

  private initCtx() {
    if (!this.ctx) {
      const AudioCtxClass = window.AudioContext || (window as any).webkitAudioContext
      if (AudioCtxClass) {
        this.ctx = new AudioCtxClass()
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume()
    }
  }

  playBeep(type: 'scan' | 'error' | 'success' = 'scan') {
    if (!this._enabled) return

    try {
      this.initCtx()
      if (!this.ctx) return

      const osc = this.ctx.createOscillator()
      const gain = this.ctx.createGain()
      osc.connect(gain)
      gain.connect(this.ctx.destination)

      const now = this.ctx.currentTime

      if (type === 'scan') {
        // High, crisp 880Hz single blip (barcode scan confirmation)
        osc.type = 'sine'
        osc.frequency.setValueAtTime(880, now)
        gain.gain.setValueAtTime(0.12, now)
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08)
        osc.start(now)
        osc.stop(now + 0.08)
      } else if (type === 'error') {
        // Low double buzz (e.g. not found, insufficient cash)
        osc.type = 'sawtooth'
        osc.frequency.setValueAtTime(220, now)
        gain.gain.setValueAtTime(0.15, now)
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18)
        osc.start(now)
        osc.stop(now + 0.18)
      } else if (type === 'success') {
        // Ascending pleasant two-tone chime (sale completed)
        osc.type = 'triangle'
        osc.frequency.setValueAtTime(587.33, now) // D5
        osc.frequency.setValueAtTime(880, now + 0.09) // A5
        gain.gain.setValueAtTime(0.15, now)
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22)
        osc.start(now)
        osc.stop(now + 0.22)
      }
    } catch (e) {
      // Audio autoplay policy or device mute fallback
    }
  }
}

export const sound = new SoundController()
