# VibeBar for macOS

Run `./macos/install-modular.sh` on a Mac. The installer keeps the original
SwiftBar integration and connects the shared modular voice, language,
categories, reports, custom commands, clipboard, and absence-break services.

The SwiftBar menu exposes the same user capabilities as the Windows desktop:
current-task timing, journal entry, tasks, breaks, ideas, reminders, clipboard
operations, daily and weekly reports, category assignment, custom commands,
language switching, local voice control, and opening the journal.

Hebrew is the default language. Use the language item in the menu to cycle
between Hebrew, Russian, and English. Input and selection actions use native
macOS dialogs. The local voice listener can be disabled or enabled from the
same menu; changing custom voice commands restarts it so the new vocabulary is
loaded immediately.

The installer asks macOS for Microphone and Accessibility permissions. The
Bluetooth absence service is installed only when `VIBEBAR_BLUETOOTH_DEVICE` is
configured. Its five-minute grace period and retroactive journal entries use
the same shared engine as Windows.
