import streamlit as st
import json
import time
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize the client securely using os.getenv
client = OpenAI(
    api_key=os.getenv("AICREDITS_API_KEY"),
    base_url="https://api.aicredits.in/v1"
)

SYSTEM_PROMPT = """あなたは優秀なCRMデータ抽出APIです。
ユーザーが入力する商談メモから、以下の5つのフィールドを抽出し、厳密なJSONフォーマットのみで出力してください。
Markdownブロック（```json）や余計な解説は一切含めないでください。

【抽出ルール】
1. 会社名: 「(株)」「(有)」などの略称は、必ず「株式会社」「有限会社」など正式名称に変換すること。ただし、元のテキストの前後位置（前株・後株）は必ず維持し、元のテキストに法人格がない場合は勝手に「株式会社」を補完しないこと。
2. 相手: 「様」「さん」「社長」「部長」などの敬称や役職名はすべて除外し、氏名のみを抽出すること。複数人の場合は「、」で区切ること。
3. 次アクション: 文末は必ず体言止め（名詞形）で簡潔にまとめること（例：「〜を送付する」ではなく「〜の送付」）。助詞の「の」の有無など、簡潔な名詞句を心がけること。
4. 期限: メモに記載されている期限をそのまま抽出すること。ただし、末尾の「まで」は必ず削除すること（例：「今月末まで」→「今月末」）。
5. リスク: 案件における懸念点やリスクを、簡潔な要約文として抽出すること。

【抽出項目】
- 会社名
- 相手
- 次アクション
- 期限
- リスク
"""

def extract_crm_data(text):
    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model="qwen/qwen-2.5-72b-instruct",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"入力メモ:\n{text}"}
            ],
            response_format={"type": "json_object"}
        )
        end_time = time.time()
        
        # Extract metadata
        latency = round(end_time - start_time, 2)
        usage = response.usage
        
        return {
            "success": True,
            "data": json.loads(response.choices[0].message.content),
            "latency": latency,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- UI Layout & Styling ---
st.set_page_config(page_title="CRM Data Extractor", page_icon="🏢", layout="wide")

# Sidebar: System Telemetry
with st.sidebar:
    st.header("⚙️ System Telemetry")
    st.info("**Engine:** Qwen 2.5 72B Instruct")
    st.info("**Gateway:** AICredits (OpenAI API)")
    st.info("**Task:** CRM Entity Extraction")
    st.markdown("---")
    st.caption("Designed for Japanese Business Contexts.")

st.title("📝 Japanese Meeting Note to CRM Fields")

col1, col2 = st.columns([1, 1.2]) # Slightly wider right column for better data display

with col1:
    st.subheader("1. Input Data")
    note_input = st.text_area(
        "Paste Japanese meeting note here:", 
        height=250, 
        placeholder="【商談メモ】 10/28 (株)グローバルテック 営業部 佐藤部長、田中さん。..."
    )
    extract_btn = st.button("Run Extraction Pipeline", type="primary", use_container_width=True)

with col2:
    st.subheader("2. Extraction Results")
    
    if extract_btn:
        if not note_input.strip():
            st.warning("Please enter a meeting note first.")
        else:
            with st.spinner("Processing via Qwen 72B..."):
                result = extract_crm_data(note_input)
                
                if not result["success"]:
                    st.error(f"Extraction failed: {result['error']}")
                else:
                    st.success(f"Extraction complete in {result['latency']} seconds ⚡")
                    
                    # Performance Metrics Row
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Latency", f"{result['latency']}s")
                    m2.metric("Prompt Tokens", result["prompt_tokens"])
                    m3.metric("Completion Tokens", result["completion_tokens"])
                    m4.metric("Total Tokens", result["total_tokens"])
                    
                    st.divider()
                    
                    # Clean Business Presentation
                    st.markdown("### 📋 CRM Output")
                    data = result["data"]
                    
                    # Using Markdown for a clean, readable layout instead of raw JSON
                    st.markdown(f"**🏢 会社名 (Company):** `{data.get('会社名', 'N/A')}`")
                    st.markdown(f"**👤 相手 (Contact):** `{data.get('相手', 'N/A')}`")
                    st.markdown(f"**📅 期限 (Deadline):** `{data.get('期限', 'N/A')}`")
                    st.markdown(f"**🎯 次アクション (Next Action):** `{data.get('次アクション', 'N/A')}`")
                    
                    # Risk gets a highlight box
                    st.info(f"**⚠️ リスク (Risk):** {data.get('リスク', 'N/A')}")
                    
                    st.divider()
                    
                    # Developer View for the raw JSON payload
                    with st.expander("🛠️ Developer View (Raw JSON Payload)"):
                        st.json(data)