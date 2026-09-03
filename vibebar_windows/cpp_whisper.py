"""Compatibility imports for the shared whisper.cpp adapter."""

from vibebar_voice.cpp_whisper import CppTurboServer, CppTurboTranscriber, TurboPaths, _save_wav

__all__ = ["CppTurboServer", "CppTurboTranscriber", "TurboPaths", "_save_wav"]
