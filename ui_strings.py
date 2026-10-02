"""UI text for the Streamlit app in Japanese (default) and English.

Both languages must have the same keys (checked in tests/test_ui_strings.py).
Strings with {placeholders} are filled in with str.format.
"""

DEFAULT_LANG = "ja"
LANG_LABELS = {"ja": "日本語", "en": "English"}

STRINGS = {
    "ja": {
        "language": "表示言語 / Language",
        "sidebar_header": "⚙️ システム情報",
        "sidebar_engine": "**モデル:** Qwen 2.5 72B Instruct",
        "sidebar_gateway": "**ゲートウェイ:** AICredits（OpenAI互換API）",
        "sidebar_task": "**タスク:** CRM項目の抽出",
        "sidebar_caption": "日本語のビジネス文書向けに設計しています。",
        "title": "📝 日本語の商談メモ → CRM項目",
        "input_header": "1. 入力",
        "input_label": "日本語の商談メモを貼り付けてください：",
        "input_help": "1件あたり最大 {max_chars} 文字です。",
        "privacy_note": "🔒 入力したテキストは API プロバイダー（AICredits）と上流のモデル提供元に送信されます。"
                        "機密情報や個人情報は貼り付けないでください。",
        "usage_caption": "{chars}/{max_chars} 文字 · このセッションの残り実行回数 {left}/{max_runs}",
        "run_button": "抽出を実行",
        "results_header": "2. 抽出結果",
        "spinner": "Qwen 72B で処理中…",
        "extraction_failed": "抽出に失敗しました: {error}",
        "extraction_done": "抽出が完了しました（{latency} 秒）⚡",
        "metric_latency": "処理時間",
        "metric_prompt_tokens": "入力トークン",
        "metric_completion_tokens": "出力トークン",
        "metric_total_tokens": "合計トークン",
        "output_header": "### 📋 CRM項目（編集できます）",
        "edit_help": "内容を確認し、必要に応じて修正してください。メモに見つからない項目は「{not_found}」と表示されます。",
        "field_会社名": "🏢 会社名",
        "field_相手": "👤 相手",
        "field_次アクション": "🎯 次アクション",
        "field_期限": "📅 期限",
        "field_リスク": "⚠️ リスク",
        "edited_json_label": "編集後の JSON（右上のアイコンでコピー）",
        "download_button": "編集後の JSON をダウンロード",
        "raw_json_expander": "🛠️ 開発者向け（モデルの生の JSON 出力）",
        "empty_note": "商談メモを入力してください。",
        "note_too_long": "メモが長すぎます（{length} 文字）。上限は {max_chars} 文字です。",
        "session_limit": "このセッションのデモ実行回数（{max_runs} 回）を使い切りました。お試しいただきありがとうございます。"
                         "さらに実行するには、リポジトリをクローンしてご自身の API キーをお使いください。",
        "daily_limit": "本日のデモ実行回数の上限（全利用者共通）に達しました。明日（UTC）以降に再度お試しください。",
        "missing_key": "**AICREDITS_API_KEY が設定されていません。**\n\n"
                       "- ローカル: リポジトリ直下の `.env` に `AICREDITS_API_KEY=\"your_key\"` を追加してください。\n"
                       "- Docker: `--env-file .env` を付けて起動してください。\n"
                       "- Streamlit Community Cloud: App settings → Secrets に `AICREDITS_API_KEY = \"your_key\"` を追加してください。",
    },
    "en": {
        "language": "表示言語 / Language",
        "sidebar_header": "⚙️ System Telemetry",
        "sidebar_engine": "**Engine:** Qwen 2.5 72B Instruct",
        "sidebar_gateway": "**Gateway:** AICredits (OpenAI-compatible API)",
        "sidebar_task": "**Task:** CRM Entity Extraction",
        "sidebar_caption": "Designed for Japanese business contexts.",
        "title": "📝 Japanese Meeting Note to CRM Fields",
        "input_header": "1. Input Data",
        "input_label": "Paste a Japanese meeting note here:",
        "input_help": "Up to {max_chars} characters per note.",
        "privacy_note": "🔒 Text you paste is sent to the API provider (AICredits) and the upstream model host. "
                        "Don't paste confidential or personal data.",
        "usage_caption": "{chars}/{max_chars} characters · {left}/{max_runs} demo runs left this session",
        "run_button": "Run Extraction",
        "results_header": "2. Extraction Results",
        "spinner": "Processing via Qwen 72B...",
        "extraction_failed": "Extraction failed: {error}",
        "extraction_done": "Extraction complete in {latency} seconds ⚡",
        "metric_latency": "Latency",
        "metric_prompt_tokens": "Prompt Tokens",
        "metric_completion_tokens": "Completion Tokens",
        "metric_total_tokens": "Total Tokens",
        "output_header": "### 📋 CRM Output (editable)",
        "edit_help": "Review and correct the fields if needed. Fields not found in the note are shown as \"{not_found}\".",
        "field_会社名": "🏢 会社名 (Company)",
        "field_相手": "👤 相手 (Contact)",
        "field_次アクション": "🎯 次アクション (Next Action)",
        "field_期限": "📅 期限 (Deadline)",
        "field_リスク": "⚠️ リスク (Risk)",
        "edited_json_label": "Edited JSON (copy with the icon at the top right)",
        "download_button": "Download edited JSON",
        "raw_json_expander": "🛠️ Developer View (raw model JSON)",
        "empty_note": "Please enter a meeting note first.",
        "note_too_long": "The note is too long ({length} characters). The limit is {max_chars} characters.",
        "session_limit": "You've used all {max_runs} demo runs for this session. Thanks for trying it! "
                         "To run more, clone the repo and use your own API key.",
        "daily_limit": "The shared daily demo limit has been reached. Please try again tomorrow (UTC).",
        "missing_key": "**AICREDITS_API_KEY is not set.**\n\n"
                       "- Local: add `AICREDITS_API_KEY=\"your_key\"` to a `.env` file in the repo root.\n"
                       "- Docker: run with `--env-file .env`.\n"
                       "- Streamlit Community Cloud: add `AICREDITS_API_KEY = \"your_key\"` under App settings → Secrets.",
    },
}


def t(lang, key, **kwargs):
    """Look up a UI string; unknown languages fall back to DEFAULT_LANG."""
    text = STRINGS.get(lang, STRINGS[DEFAULT_LANG])[key]
    return text.format(**kwargs) if kwargs else text
