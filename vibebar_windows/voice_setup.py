"""Compatibility entry point for installing shared wake-word assets."""

from vibebar_voice.setup_assets import COMPUTER_SHA256, COMPUTER_URL, install_computer_model, main

__all__ = ["COMPUTER_SHA256", "COMPUTER_URL", "install_computer_model", "main"]

if __name__ == "__main__":
    main()
