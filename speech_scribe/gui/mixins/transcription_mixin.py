"""
Mixins de referência - Speech Scribe Pro V3

Este módulo documenta a organização lógica do main_window.py.
Os métodos permanecem no main_window.py para evitar refatoração invasiva,
mas estão organizados em seções claramente marcadas:

Seções em main_window.py:
  - UI INITIALIZATION: init_ui, _create_*_tab, _create_header, _create_status_bar
  - EVENT CONNECTIONS: _connect_events
  - FILE HANDLING: select_file, _on_file_dropped, _validate_audio_file
  - TRANSCRIPTION: start_transcription, _cancel_transcription, _transcription_finished, etc.
  - TEXT ACTIONS: _copy_text, _clear_transcription, _save_file, _export_file
  - ANALYSIS: _start_analysis, _display_analysis_results, _export_analysis_results
  - OLLAMA / CHAT: _check_ollama_status, _start_chat_with_ai, _send_chat_message
  - SEARCH: _toggle_search, _on_search_text_changed, _search_next, _search_prev
  - SHORTCUTS: _setup_shortcuts
  - PRESETS: _on_preset_changed
  - HISTORY: _show_history, _load_from_history, _save_to_history
  - SETTINGS ACTIONS: _on_gpu_device_changed, _update_vram_usage, _clear_model_cache
  - THEME / TRANSLATION: _translate_transcription, _toggle_theme
  - TRANSCRIPTION QUEUE: _toggle_queue, _queue_add_files, _queue_start, etc.
  - VERSION CHECK: _check_for_updates
  - USER SETTINGS PERSISTENCE: _restore_user_settings, _save_user_settings, closeEvent
"""
