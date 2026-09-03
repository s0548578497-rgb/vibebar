from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave
import winsound

import numpy as np

from vibebar_voice.cpp_whisper import TurboPaths, _save_wav
from vibebar_voice.cpp_whisper import _multipart
from vibebar_voice.transcription import NullAudioTranscriber
from vibebar_windows.audio_cue import NullAudioCue, WindowsWaveCue


ROOT = Path(__file__).resolve().parents[1]


class TurboPathsTests(unittest.TestCase):
    def test_existing_cpp_components_are_discovered(self) -> None:
        paths = TurboPaths.discover(ROOT)
        self.assertEqual(paths.server.name, "whisper-server.exe")
        self.assertIn("large-v3-turbo", paths.model.name)
        self.assertEqual(paths.adapter.name, "turbo.py")

    def test_missing_cpp_components_report_every_required_path(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            paths = TurboPaths.discover(Path(directory))
            with self.assertRaisesRegex(FileNotFoundError, "whisper-server"):
                paths.validate()

    def test_macos_paths_are_repository_local_and_have_no_windows_adapter(self) -> None:
        paths = TurboPaths.discover_macos(ROOT)
        self.assertEqual(paths.server.name, "whisper-server")
        self.assertIsNone(paths.vulkan_bin)
        self.assertIsNone(paths.adapter)
        self.assertIn("macos", paths.server.parts)


class AudioBoundaryTests(unittest.TestCase):
    def test_builtin_server_request_contains_audio_and_parameters(self) -> None:
        body = _multipart("boundary", b"wave", 2)
        self.assertIn(b'name="file"', body)
        self.assertIn(b'name="beam_size"', body)
        self.assertIn(b"wave", body)
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

    def test_wave_cue_is_a_valid_local_wav(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            cue = WindowsWaveCue(Path(directory) / "cue.wav")
            with wave.open(str(cue.path), "rb") as sound:
                self.assertEqual(sound.getframerate(), 16_000)
                self.assertEqual(sound.getnchannels(), 1)

    def test_null_audio_cue_is_sealed(self) -> None:
        self.assertFalse(NullAudioCue().play())

    @patch("vibebar_windows.audio_cue.winsound.PlaySound")
    def test_wave_cue_is_queued_asynchronously(self, play: object) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            cue = WindowsWaveCue(Path(directory) / "cue.wav")
            self.assertTrue(cue.play())
            flags = play.call_args.args[1]
            self.assertTrue(flags & winsound.SND_ASYNC)


if __name__ == "__main__":
    unittest.main()
