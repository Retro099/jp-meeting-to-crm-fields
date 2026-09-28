# jp-meeting-to-crm-fields

Japanese meeting notes to structured CRM JSON fields pipeline. This project demonstrates a production-focused approach to deterministic entity extraction from unstructured sales transcripts, prioritizing strict evaluation and exact JSON schemas.

## プロジェクト概要 (Overview)
営業MTGや商談メモから、CRM（顧客管理）に必要な5つの重要フィールドを自動抽出する検証パイプラインです。公開デモに加えて、固定データセットに対する評価スコアも公開しています。

*   **入力 (Input)**: 日本語の議事録・商談メモ
*   **出力 (Output JSON)**: `会社名`, `相手`, `次アクション`, `期限`, `リスク`[cite: 1]
*   **評価 (Evaluation)**: 30件の固定テストデータ(`gold_30.jsonl`)を使用した抽出精度の測定

## Architecture & Stack
*   **Frontend**: Streamlit Community Cloud (Zero-maintenance UI)
*   **Inference Gateway**: OpenRouter API (Frozen Model ID: `qwen/qwen-2.5-72b-instruct`)
*   **Validation**: Pure Python evaluation script measuring exact/semantic match per field.

## Limitations & Cost
*   The Streamlit application will enter a sleep state if unvisited for several days, requiring a 10-second cold start upon the next visit.
*   The inference pipeline relies on the OpenRouter API (~$0.0007 per extraction) to guarantee high-quality JSON adherence. 

## 使い方 (How to Run Locally)
*(To be populated after the evaluation script is built)*