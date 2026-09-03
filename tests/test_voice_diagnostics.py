from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from vibebar_modular.clock import FixedClock
from vibebar_windows.diagnostics import JsonLineDiagnosticLog, text_fingerprint
from vibebar_windows.transcription import NullAudioTranscriber
from vibebar_windows.voice import CaptureSettings, VoiceController
from vibebar_voice.speech_boundary import AdaptiveBoundarySettings, AdaptiveSpeechBoundary


ROOT = Path(__file__).resolve().parents[1]


class FakeStream:
    def __init__(self, levels: list[int]) -> None:
        self.levels = levels
        self.reads = 0

    def read(self, _size: int) -> tuple[np.ndarray, bool]:
        level = self.levels[min(self.reads, len(self.levels) - 1)]
        self.reads += 1
        return np.full((1_280, 1), level, dtype=np.int16), False


class RecordingDiagnostics:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, object]]] = []

    def event(self, name: str, **fields: object) -> None:
        self.events.append((name, fields))


class CapturePolicyTests(unittest.TestCase):
    def test_silence_does_not_stop_capture_before_speech(self) -> None:
        trace = RecordingDiagnostics()
        stream = FakeStream([0, 0, 0, 0, 180, 180, 0, 0])
        controller = VoiceController(
            lambda _text: None,
            lambda _status: None,
            NullAudioTranscriber(),
            diagnostics=trace,
            capture=CaptureSettings(start_timeout_blocks=8, trailing_silence_blocks=2, maximum_blocks=20),
        )
        audio = controller._capture_command(stream, ignore_stop=True)
        self.assertEqual(stream.reads, 8)
        self.assertEqual(audio.size, 8 * 1_280)
        self.assertEqual(trace.events[-1][1]["reason"], "silence_after_speech")

    def test_adaptive_boundary_learns_constant_background_noise(self) -> None:
        settings = AdaptiveBoundarySettings(
            calibration_seconds=0.16, end_silence_seconds=0.16, noise_multiplier=1.6,
        )
        boundary = AdaptiveSpeechBoundary(settings)
        noise = np.full(1_280, 300, dtype=np.int16)
        for _index in range(boundary.calibration_blocks):
            boundary.calibrate(noise)
        speech = boundary.observe(np.full(1_280, 900, dtype=np.int16))
        self.assertTrue(speech.speech_seen)
        self.assertFalse(boundary.observe(noise).finished)
        self.assertTrue(boundary.observe(noise).finished)

    def test_release_hysteresis_ends_when_noise_rises_after_calibration(self) -> None:
        settings = AdaptiveBoundarySettings(
            calibration_seconds=0.08, end_silence_seconds=0.16, noise_multiplier=1.6,
        )
        boundary = AdaptiveSpeechBoundary(settings)
        boundary.calibrate(np.full(1_280, 100, dtype=np.int16))
        boundary.observe(np.full(1_280, 2_500, dtype=np.int16))
        raised_noise = np.full(1_280, 300, dtype=np.int16)
        self.assertFalse(boundary.observe(raised_noise).finished)
        self.assertTrue(boundary.observe(raised_noise).finished)


class DiagnosticLogTests(unittest.TestCase):
    def test_json_log_contains_metadata_without_spoken_text(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "diagnostics.jsonl"
            log = JsonLineDiagnosticLog(path, FixedClock(datetime(2030, 1, 2, 3, 4, 5)))
            spoken = "private spoken words"
            log.event("transcription_completed", characters=len(spoken), fingerprint=text_fingerprint(spoken))
            record = json.loads(path.read_text(encoding="utf-8"))
            self.assertNotIn(spoken, path.read_text(encoding="utf-8"))
            self.assertEqual(record["characters"], len(spoken))


if __name__ == "__main__":
    unittest.main()
