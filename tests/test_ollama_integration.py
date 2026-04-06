#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


def test_safe_num_ctx_reduces_for_near_vram_limit():
    from speech_scribe.core.ollama_integration import OllamaConfig, OllamaManager

    manager = OllamaManager(OllamaConfig(num_ctx=8192))
    manager.gpu_info = {"name": "Test GPU", "vram_total_gb": 16.0}
    manager._model_details_cache = {
        "deepseek-r1:14b-qwen-distill-q8_0": {"size_gb": 15.0},
        "qwen3.5:9b-q8_0": {"size_gb": 10.0},
    }

    assert manager._get_safe_num_ctx("deepseek-r1:14b-qwen-distill-q8_0") == 4096
    assert manager._get_safe_num_ctx("qwen3.5:9b-q8_0") == 8192


def test_auto_model_selection_prefers_vram_fit():
    from speech_scribe.core.ollama_integration import OllamaManager

    manager = OllamaManager()
    manager.gpu_info = {"name": "Test GPU", "vram_total_gb": 16.0}
    manager.available_models = [
        "deepseek-r1:14b-qwen-distill-q8_0",
        "gpt-oss:20b",
        "qwen3.5:9b-q8_0",
    ]
    manager._model_details_cache = {
        "deepseek-r1:14b-qwen-distill-q8_0": {"size_gb": 15.0},
        "gpt-oss:20b": {"size_gb": 13.0},
        "qwen3.5:9b-q8_0": {"size_gb": 10.0},
    }
    manager.get_available_models = lambda: manager.available_models

    selected = manager.get_best_available_model("sentiment")

    assert selected == "gpt-oss:20b"


def test_analyze_transcription_sends_safe_num_ctx(monkeypatch):
    from speech_scribe.core.ollama_integration import OllamaConfig, OllamaManager

    manager = OllamaManager(OllamaConfig(num_ctx=8192, keep_alive="10m"))
    manager.gpu_info = {"name": "Test GPU", "vram_total_gb": 16.0}
    manager.available_models = ["qwen3.5:9b-q8_0"]
    manager._model_details_cache = {
        "qwen3.5:9b-q8_0": {"size_gb": 10.0}
    }

    monkeypatch.setattr(manager, "check_service_status", lambda: True)
    monkeypatch.setattr(manager, "is_model_available", lambda model_name: True)

    def preload(model_name):
        manager._gpu_preloaded_model = model_name
        return {"loaded": True, "processor": "100% GPU", "context_length": 8192}

    monkeypatch.setattr(manager, "preload_model_gpu", preload)

    captured = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse(200, {"response": "ok", "done": True})

    monkeypatch.setattr("speech_scribe.core.ollama_integration.requests.post", fake_post)

    result = manager.analyze_transcription(
        "texto de teste",
        model_name="qwen3.5:9b-q8_0",
        analysis_type="general"
    )

    assert captured["json"]["options"]["num_gpu"] == -1
    assert captured["json"]["options"]["num_ctx"] == 8192
    assert captured["json"]["keep_alive"] == "10m"
    assert result["config_used"]["num_ctx"] == 8192


def test_correction_uses_dynamic_num_predict(monkeypatch):
    from speech_scribe.core.ollama_integration import OllamaConfig, OllamaManager

    manager = OllamaManager(OllamaConfig(num_ctx=8192, keep_alive="10m"))
    manager.gpu_info = {"name": "Test GPU", "vram_total_gb": 16.0}
    manager.available_models = ["gpt-oss:20b"]
    manager._model_details_cache = {
        "gpt-oss:20b": {"size_gb": 13.0}
    }

    monkeypatch.setattr(manager, "check_service_status", lambda: True)
    monkeypatch.setattr(manager, "is_model_available", lambda model_name: True)
    monkeypatch.setattr(
        manager,
        "preload_model_gpu",
        lambda model_name: {"loaded": True, "processor": "100% GPU", "context_length": 8192},
    )

    captured = {}

    def fake_send(model_name, prompt, temperature, num_predict, num_ctx):
        captured["num_predict"] = num_predict
        return {"response": "Texto corrigido.", "done": True, "eval_count": 120}

    monkeypatch.setattr(manager, "_send_generate_request", fake_send)

    result = manager.analyze_transcription(
        "palavra " * 120,
        model_name="gpt-oss:20b",
        analysis_type="correction"
    )

    assert captured["num_predict"] < 4096
    assert captured["num_predict"] >= 256
    assert result["result"] == "Texto corrigido."
    assert result["config_used"]["num_predict"] == captured["num_predict"]


def test_correction_retries_when_response_is_empty(monkeypatch):
    from speech_scribe.core.ollama_integration import OllamaManager

    manager = OllamaManager()
    manager.gpu_info = {"name": "Test GPU", "vram_total_gb": 16.0}
    manager.available_models = ["gpt-oss:20b", "qwen3.5:9b-q8_0"]
    manager._model_details_cache = {
        "gpt-oss:20b": {"size_gb": 13.0},
        "qwen3.5:9b-q8_0": {"size_gb": 10.0},
    }

    monkeypatch.setattr(manager, "check_service_status", lambda: True)
    monkeypatch.setattr(manager, "is_model_available", lambda model_name: True)
    monkeypatch.setattr(
        manager,
        "preload_model_gpu",
        lambda model_name: {"loaded": True, "processor": "100% GPU", "context_length": 8192},
    )

    calls = []

    def fake_send(model_name, prompt, temperature, num_predict, num_ctx):
        calls.append((model_name, prompt, num_predict))
        if len(calls) == 1:
            return {"response": "", "done": True, "eval_count": num_predict}
        return {
            "response": "**Transcrição Corrigida**\n\nTexto final revisado.\n\n### Análise de Correções\n- item",
            "done": True,
            "eval_count": 120,
        }

    monkeypatch.setattr(manager, "_send_generate_request", fake_send)

    result = manager.analyze_transcription(
        "texto de teste com erro",
        model_name="gpt-oss:20b",
        analysis_type="correction"
    )

    assert len(calls) == 2
    assert result["result"] == "Texto final revisado."