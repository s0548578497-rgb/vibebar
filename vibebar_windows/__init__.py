"""Windows package.

Platform-specific modules are intentionally not imported here: importing a
portable helper such as ``vibebar_windows.custom_commands`` must remain safe on
macOS CI.  Composition roots are imported explicitly from ``assembly``.
"""
