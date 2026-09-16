"""Small, local audio analysis helpers for beat-aligned property films.

This deliberately accepts a local audio file only.  Rights are recorded by the
caller; the renderer never searches for, downloads, or republishes music.
"""
from __future__ import annotations

import subprocess
import wave
from pathlib import Path

import numpy as np


LUXURY_PALETTES = {
    "warm_luxury": ((220.0, 277.18, 329.63), (196.0, 246.94, 293.66), (174.61, 220.0, 261.63)),
    "coastal": ((196.0, 246.94, 293.66), (220.0, 277.18, 329.63), (174.61, 220.0, 261.63)),
    "urban": ((146.83, 174.61, 220.0), (164.81, 207.65, 246.94), (130.81, 164.81, 196.0)),
}


def create_bespoke_score(output: Path, duration_seconds: float, style: str = "warm_luxury", sample_rate: int = 44_100) -> dict:
    """Create a royalty-free, per-film ambient score locally.

    The score is intentionally understated: a slow pad progression, sparse
    bell/piano-like accents, and a soft edit pulse.  No third-party recording
    or external music catalogue is used.
    """
    duration_seconds = max(2.0, float(duration_seconds))
    count = int(duration_seconds * sample_rate)
    time = np.arange(count, dtype=np.float32) / sample_rate
    signal = np.zeros(count, dtype=np.float32)
    chords = LUXURY_PALETTES.get(style, LUXURY_PALETTES["warm_luxury"])
    section = max(3.5, duration_seconds / len(chords))
    for index, chord in enumerate(chords):
        start, end = index * section, min(duration_seconds, (index + 1) * section + 0.8)
        mask = (time >= start) & (time < end)
        local = time[mask] - start
        envelope = np.minimum(1.0, local / 1.2) * np.minimum(1.0, np.maximum(0.0, end - time[mask]) / 1.4)
        for frequency in chord:
            # Detuned oscillators make a gentle, wide pad without a sample library.
            signal[mask] += .035 * envelope * (np.sin(2*np.pi*frequency*local) + .42*np.sin(2*np.pi*frequency*1.003*local))
    # A restrained 80 BPM pulse gives the editor clear cut anchors.
    beat_seconds = 60 / 80
    for beat in np.arange(0.5, duration_seconds, beat_seconds):
        begin = int(beat * sample_rate); length = min(int(.15 * sample_rate), count - begin)
        local = np.arange(length, dtype=np.float32) / sample_rate
        signal[begin:begin+length] += .08 * np.exp(-local * 20) * np.sin(2*np.pi*92*local)
        if int(beat / beat_seconds) % 2 == 0:
            signal[begin:begin+length] += .025 * np.exp(-local * 8) * np.sin(2*np.pi*880*local)
    fade = min(int(sample_rate * 1.2), count // 2)
    signal[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
    signal[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
    signal /= max(.001, float(np.max(np.abs(signal)))) / .55
    # Subtle stereo movement makes the result feel less synthetic in a room reel.
    left = signal * (.97 + .03*np.sin(2*np.pi*.09*time)); right = signal * (.97 - .03*np.sin(2*np.pi*.09*time))
    stereo = np.stack((left, right), axis=1)
    output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output), "wb") as target:
        target.setnchannels(2); target.setsampwidth(2); target.setframerate(sample_rate)
        target.writeframes((np.clip(stereo, -1, 1) * 32767).astype("<i2").tobytes())
    return {"path": str(output), "style": style, "duration_seconds": round(duration_seconds, 2), "rights": "bespoke_local_generated"}


def _pcm(audio: Path, ffmpeg: str, sample_rate: int = 22_050) -> np.ndarray:
    """Decode audio to mono signed-16-bit PCM without adding a heavyweight ML dependency."""
    if audio.suffix.lower() == ".wav":
        with wave.open(str(audio), "rb") as source:
            if source.getsampwidth() == 2 and source.getnchannels() == 1 and source.getframerate() == sample_rate:
                return np.frombuffer(source.readframes(source.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    result = subprocess.run(
        [ffmpeg, "-v", "error", "-i", str(audio), "-ac", "1", "-ar", str(sample_rate), "-f", "s16le", "pipe:1"],
        check=True, capture_output=True, timeout=120,
    )
    return np.frombuffer(result.stdout, dtype=np.int16).astype(np.float32) / 32768


def detect_beats(audio: Path, ffmpeg: str, sample_rate: int = 22_050) -> dict:
    """Return robust energy-onset cut points and a conservative confidence score.

    This is intentionally an edit-assist rather than a musical-rights or genre
    classifier.  It works well for obvious beat/onset transitions and falls
    back safely when a track is sparse or ambient.
    """
    samples = _pcm(audio, ffmpeg, sample_rate)
    frame, hop = 1_024, 512
    if len(samples) < frame:
        return {"audio": str(audio), "beat_times": [], "confidence": 0.0, "method": "energy_onset_v1"}
    windows = np.lib.stride_tricks.sliding_window_view(samples, frame)[::hop]
    energy = np.sqrt(np.mean(windows * windows, axis=1)) + 1e-8
    novelty = np.maximum(0, np.diff(np.log(energy), prepend=np.log(energy[0])))
    threshold = float(np.percentile(novelty, 88))
    candidates = np.flatnonzero(novelty >= threshold)
    selected: list[int] = []
    min_gap_frames = max(1, round(0.32 * sample_rate / hop))
    for candidate in candidates:
        if not selected or candidate - selected[-1] >= min_gap_frames:
            selected.append(int(candidate))
        elif novelty[candidate] > novelty[selected[-1]]:
            selected[-1] = int(candidate)
    beats = [round(index * hop / sample_rate, 3) for index in selected]
    duration = len(samples) / sample_rate
    expected = max(1, duration / 1.0)
    confidence = round(min(1.0, len(beats) / expected), 3)
    return {"audio": str(audio), "beat_times": beats, "confidence": confidence, "method": "energy_onset_v1", "sample_rate": sample_rate}
