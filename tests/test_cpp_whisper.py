from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
import wave

import numpy as np

from vibebar_windows.cpp_whisper import TurboPaths, _save_wav
from vibebar_windows.transcription import NullAudioTranscriber


ROOT = Path(__file__).resolve().parents[1]


class TurboPathsTests(unittest.TestCase):
    def test_existing_cpp_components_are_discovered(self) -> None:
        paths = TurboPaths.discover(ROOT)
        paths.validate()
        self.assertEqual(paths.server.name, "whisper-server.exe")
        self.assertIn("large-v3-turbo", paths.model.name)
        self.assertEqual(paths.adapter.name, "turbo.py")


class AudioBoundaryTests(unittest.TestCase):
    def test_temporary_wav_contract_is_16khz_mono_pcm(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "audio.wav"
            _save_wav(np.zeros(1_600, dtype=np.int16), path)
            with wave.open(str(path), "rb") as audio:
                self.assertEqual(audio.getframerate(), 16_000)
                self.assertEqual(audio.getnchannels(), 1)
                self.assertEqual(audio.getsampwidth(), 2)

    def test_null_transcriber_is_sealed(self) -> None:
        transcriber = NullAudioTranscriber()
        self.assertEqual(transcriber.transcribe(np.ones(10, dtype=np.int16)), "")
        transcriber.close()


if __name__ == "__main__":
    unittest.main()
