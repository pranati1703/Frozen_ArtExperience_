import sounddevice as sd
import numpy as np
import random
import threading

class AudioManager:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.volume = 0.0
        self.target_volume = 0.0
        self.running = False
        
        # Audio state
        self.phase = 0
        self.shimmers = [] # List of active shimmer notes
        
        # Zen Pad frequencies (D Major: D3, F#3, A3) -> Warm and happy
        self.drone_freqs = [146.83, 185.00, 220.00] 
        self.drone_phases = [random.uniform(0, 2*np.pi) for _ in self.drone_freqs]
        
    def start(self):
        if self.running: return
        self.running = True
        try:
            # Low latency output stream
            self.stream = sd.OutputStream(
                channels=1, 
                callback=self._audio_callback,
                samplerate=self.sample_rate,
                blocksize=1024
            )
            self.stream.start()
        except Exception as e:
            print(f"Audio Error: {e}")
            self.running = False

    def stop(self):
        if self.running:
            self.running = False
            self.stream.stop()
            self.stream.close()

    def update_intensity(self, intensity):
        # Intensity 0.0 to 1.0
        # Base ambient volume = 0.3 (Zen music always audible)
        # Max volume = 1.0 (Intense sparkles)
        self.target_volume = 0.3 + (intensity * 0.7)
        self.target_volume = max(0.0, min(self.target_volume, 1.0))

    def _audio_callback(self, outdata, frames, time, status):
        if status:
            print(status)
            
        t = (np.arange(frames) + self.phase) / self.sample_rate
        self.phase += frames
        
        # Smooth volume transition
        if self.volume < self.target_volume:
            self.volume += 0.01
        elif self.volume > self.target_volume:
            self.volume -= 0.01
            
        # 1. Zen Pad Layer (DISABLED - User Request)
        # Gentle, slow-moving sine waves
        pad_signal = np.zeros(frames)
        # for i, freq in enumerate(self.drone_freqs):
        #     # Very slow breath/swell
        #     swell = (np.sin(t * 0.2 + self.drone_phases[i]) + 1) * 0.5 # 0 to 1
        #     # Add slight detune for richness
        #     pad_signal += np.sin(2 * np.pi * freq * t) * (0.5 + 0.5 * swell)
        
        # pad_signal *= 0.15 # Gentle background level over master
        
        # 2. Shimmer Layer (Sparkles)
        # Probability scales aggressively with volume
        # Low vol (0.3) -> Rare sparkles
        # High vol (1.0) -> Intense shower
        spawn_prob = 0.02 + (self.volume ** 3) * 0.5
        
        if random.random() < spawn_prob:
            # High magical notes (D Major Lydianish)
            notes = [1174, 1318, 1480, 1760, 1975, 2217, 2349, 2637, 2960]
            freq = random.choice(notes)
            self.shimmers.append({
                'freq': freq,
                'life': 1.0,
                'decay': random.uniform(0.03, 0.08), 
                'phase': 0
            })
            
        shimmer_signal = np.zeros(frames)
        active_shimmers = []
        for s in self.shimmers:
            s_t = np.arange(frames) / self.sample_rate + s['phase']
            wave = np.sin(2 * np.pi * s['freq'] * s_t)
            s['life'] -= s['decay']
            
            # Sparkles get louder with hand distance (self.volume)
            shimmer_gain = 0.2 * self.volume 
            shimmer_signal += wave * max(0, s['life']) * shimmer_gain
            
            s['phase'] += frames / self.sample_rate
            
            if s['life'] > 0:
                active_shimmers.append(s)
        
        self.shimmers = active_shimmers
        
        # Mix: Pad is constant-ish, Shimmers sit on top
        # We apply master volume mostly to shimmers, but let pad breathe?
        # Actually, let's keep Pad constant ambient, and Volume controls shimmer intensity
        
        final_signal = pad_signal + shimmer_signal
        
        # Output
        outdata[:] = final_signal.reshape(-1, 1).astype(np.float32)
