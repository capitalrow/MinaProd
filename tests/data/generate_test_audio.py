#!/usr/bin/env python3
"""
Generate test audio files for E2E testing
"""
import wave
import struct
import math
import numpy as np
from pathlib import Path

def generate_sine_wave(frequency, duration, sample_rate=16000, amplitude=0.7):
    """Generate a sine wave audio signal."""
    frames = int(duration * sample_rate)
    samples = []
    
    for i in range(frames):
        t = float(i) / sample_rate
        sample = int(amplitude * 32767 * math.sin(2 * math.pi * frequency * t))
        samples.append(sample)
    
    return samples

def generate_speech_pattern(words, sample_rate=16000):
    """Generate audio pattern that simulates speech cadence."""
    samples = []
    
    for i, word in enumerate(words):
        # Varying fundamental frequency for different words
        fundamental = 150 + (i * 30)  # 150-300 Hz range
        word_duration = 0.6  # 600ms per word
        silence_duration = 0.2  # 200ms pause
        
        # Generate word audio with harmonics
        word_samples = []
        for j in range(int(sample_rate * word_duration)):
            t = float(j) / sample_rate
            
            # Multiple harmonics to simulate speech
            sample = (
                0.5 * math.sin(2 * math.pi * fundamental * t) +
                0.3 * math.sin(2 * math.pi * fundamental * 2 * t) +
                0.2 * math.sin(2 * math.pi * fundamental * 3 * t)
            )
            
            # Add slight noise for realism
            noise = (np.random.random() - 0.5) * 0.1
            sample += noise
            
            # Convert to 16-bit integer
            sample_int = int(max(-1, min(1, sample)) * 32767)
            word_samples.append(sample_int)
        
        samples.extend(word_samples)
        
        # Add silence between words
        silence_samples = [0] * int(sample_rate * silence_duration)
        samples.extend(silence_samples)
    
    return samples

def save_wav_file(samples, filename, sample_rate=16000):
    """Save samples as a WAV file."""
    with wave.open(str(filename), 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        for sample in samples:
            wav_file.writeframes(struct.pack('<h', sample))

def generate_test_audio_files():
    """Generate all test audio files."""
    data_dir = Path(__file__).parent
    data_dir.mkdir(exist_ok=True)
    
    print("🎵 Generating test audio files...")
    
    # 1. Clear speech pattern
    clear_speech_words = ["hello", "world", "this", "is", "a", "test"]
    clear_speech_samples = generate_speech_pattern(clear_speech_words)
    save_wav_file(clear_speech_samples, data_dir / "clear_speech.wav")
    print("✅ Generated clear_speech.wav")
    
    # 2. Short audio clip
    short_samples = generate_sine_wave(440, 1.5)  # 1.5 seconds
    save_wav_file(short_samples, data_dir / "short_audio.wav")
    print("✅ Generated short_audio.wav")
    
    # 3. Long audio clip (30 seconds)
    long_words = ["this", "is", "a", "very", "long", "test", "audio", "clip", 
                  "that", "should", "test", "extended", "recording", "sessions"]
    long_samples = []
    for _ in range(3):  # Repeat 3 times for longer duration
        long_samples.extend(generate_speech_pattern(long_words))
    save_wav_file(long_samples, data_dir / "long_audio.wav")
    print("✅ Generated long_audio.wav")
    
    # 4. Silence (no speech)
    silence_samples = [0] * (16000 * 3)  # 3 seconds of silence
    save_wav_file(silence_samples, data_dir / "silence.wav")
    print("✅ Generated silence.wav")
    
    # 5. Noisy audio
    noisy_words = ["background", "noise", "test"]
    noisy_samples = generate_speech_pattern(noisy_words)
    
    # Add background noise
    for i in range(len(noisy_samples)):
        noise = int((np.random.random() - 0.5) * 8000)  # More aggressive noise
        noisy_samples[i] = max(-32767, min(32767, noisy_samples[i] + noise))
    
    save_wav_file(noisy_samples, data_dir / "noisy_audio.wav")
    print("✅ Generated noisy_audio.wav")
    
    # 6. Multiple frequencies (edge case)
    multi_freq_samples = []
    frequencies = [220, 440, 880, 1760]  # Multiple frequencies
    for freq in frequencies:
        freq_samples = generate_sine_wave(freq, 1.0)
        multi_freq_samples.extend(freq_samples)
    save_wav_file(multi_freq_samples, data_dir / "multi_frequency.wav")
    print("✅ Generated multi_frequency.wav")
    
    # 7. Very short clip (edge case)
    very_short_samples = generate_sine_wave(440, 0.3)  # 300ms
    save_wav_file(very_short_samples, data_dir / "very_short.wav")
    print("✅ Generated very_short.wav")
    
    print(f"🎯 Generated {7} test audio files in {data_dir}")

if __name__ == "__main__":
    # Install numpy if not available
    try:
        import numpy as np
    except ImportError:
        print("Installing numpy...")
        import subprocess
        subprocess.run(["pip", "install", "numpy"], check=True)
        import numpy as np
    
    generate_test_audio_files()