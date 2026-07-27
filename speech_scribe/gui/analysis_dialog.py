#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧠 Diálogo de Resultados de Análise - Speech Scribe Pro V3
Janela dedicada para exibir resultados da análise com IA.
"""

import json
from datetime import datetime
from typing import Any, Dict

from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from speech_scribe.utils.logger import logger


class AnalysisResultsDialog(QDialog):
    """Diálogo para exibir resultados de análise com IA em formato estruturado."""

    def __init__(self, results: Dict[str, Any], parent=None):
        super().__init__(parent)
        self._results = results
        self.setWindowTitle("🧠 Resultados da Análise com IA")
        self.setModal(True)
        self.resize(800, 600)
        self._build_ui()

    def _build_ui(self):
        dlg_layout = QVBoxLayout(self)

        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Análise de Sentimento
        if 'sentiment' in self._results:
            group = QGroupBox("😊 Análise de Sentimento")
            grp_layout = QVBoxLayout(group)
            data = self._results['sentiment']
            text = (f"Sentimento: {data.get('sentiment', 'N/A').title()}\n"
                    f"Pontuação: {data.get('score', 0):.2f}\n"
                    f"Palavras Positivas: {data.get('positive_words', 0)}\n"
                    f"Palavras Negativas: {data.get('negative_words', 0)}")
            grp_layout.addWidget(QLabel(text))
            scroll_layout.addWidget(group)

        # Palavras-chave
        if 'keywords' in self._results:
            group = QGroupBox("🔑 Palavras-chave Principais")
            grp_layout = QVBoxLayout(group)
            data = self._results['keywords']
            text = "Top 10 Palavras-chave:\n"
            for word, count in data.get('top_keywords', []):
                text += f"• {word}: {count} ocorrências\n"
            text += f"\nTotal de palavras: {data.get('total_words', 0)}\n"
            text += f"Palavras únicas: {data.get('unique_words', 0)}"
            grp_layout.addWidget(QLabel(text))
            scroll_layout.addWidget(group)

        # Entidades
        if 'entities' in self._results:
            group = QGroupBox("🏷️ Entidades Identificadas")
            grp_layout = QVBoxLayout(group)
            data = self._results['entities']
            text = ""
            for entity_type, entities in data.items():
                if entities:
                    text += f"{entity_type.title()}: {', '.join(entities)}\n"
            if not text:
                text = "Nenhuma entidade específica identificada."
            grp_layout.addWidget(QLabel(text))
            scroll_layout.addWidget(group)

        # Resumo
        if 'summary' in self._results:
            group = QGroupBox("📄 Resumo Automático")
            grp_layout = QVBoxLayout(group)
            data = self._results['summary']
            text = data.get('summary', 'Resumo não disponível')
            text += f"\n\nTaxa de compressão: {data.get('compression_ratio', 0):.2%}"
            lbl = QLabel(text)
            lbl.setWordWrap(True)
            grp_layout.addWidget(lbl)
            scroll_layout.addWidget(group)

        # Tópicos
        if 'topics' in self._results:
            group = QGroupBox("🎯 Tópicos Identificados")
            grp_layout = QVBoxLayout(group)
            data = self._results['topics']
            text = f"Tópico principal: {data.get('main_topic', 'N/A')}\n\n"
            text += "Pontuações por tópico:\n"
            for topic, score in data.get('identified_topics', {}).items():
                text += f"• {topic.title()}: {score} pontos\n"
            grp_layout.addWidget(QLabel(text))
            scroll_layout.addWidget(group)

        # Análise Ollama
        if 'ollama_analysis' in self._results:
            group = QGroupBox("🤖 Análise Avançada (Ollama)")
            grp_layout = QVBoxLayout(group)
            data = self._results['ollama_analysis']
            if 'error' not in data:
                text = f"Modelo usado: {data.get('model_used', 'N/A')}\n\n"
                analyses = data.get('analyses', {})
                for analysis_type, analysis_result in analyses.items():
                    if 'error' not in analysis_result:
                        content = analysis_result.get('result', analysis_result.get('analysis', 'N/A'))
                        text += f"━━━ {analysis_type.upper()} ━━━\n{content}\n\n"
                    else:
                        text += f"━━━ {analysis_type.upper()} ━━━\nErro: {analysis_result['error']}\n\n"
            else:
                text = f"Erro na análise Ollama: {data['error']}"
            lbl = QLabel(text)
            lbl.setWordWrap(True)
            grp_layout.addWidget(lbl)
            scroll_layout.addWidget(group)

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        dlg_layout.addWidget(scroll_area)

        # Botões
        button_layout = QHBoxLayout()

        export_btn = QPushButton("💾 Exportar Análise")
        export_btn.clicked.connect(self._export_results)
        button_layout.addWidget(export_btn)

        close_btn = QPushButton("✖️ Fechar")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        dlg_layout.addLayout(button_layout)

    def _export_results(self):
        """Exporta resultados da análise para arquivo."""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Análise",
                f"analise_ia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON Files (*.json);;Text Files (*.txt)"
            )

            if filename:
                if filename.endswith('.json'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self._results, f, ensure_ascii=False, indent=2)
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"🧠 ANÁLISE COM IA - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                        f.write("=" * 60 + "\n\n")
                        for analysis_type, data in self._results.items():
                            f.write(f"{analysis_type.upper()}:\n")
                            f.write(str(data) + "\n\n")

                QMessageBox.information(self, "Sucesso", f"Análise exportada para: {filename}")
                logger.info(f"Análise exportada: {filename}")

        except Exception as e:
            logger.error(f"Erro ao exportar análise: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao exportar análise: {str(e)}")
