import json
import os
import time
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize client securely
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

def call_extractor(text):
    try:
        response = client.chat.completions.create(
            model="qwen/qwen-2.5-72b-instruct", 
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"入力メモ:\n{text}"}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Extraction error: {e}")
        return {}

def run_eval():
    # Set up relative paths for your directory structure
    base_dir = os.path.dirname(__file__)
    data_path = os.path.join(base_dir, "..", "data", "gold_30.jsonl")
    results_path = os.path.join(base_dir, "results.md")
    
    fields = ["会社名", "相手", "次アクション", "期限", "リスク"]
    scores = {f: {"correct": 0, "total": 0} for f in fields}
    errors = []

    with open(data_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"Starting evaluation of {len(lines)} notes using qwen-2.5-72b-instruct (via AICredits)...")
    
    for idx, line in enumerate(lines):
        record = json.loads(line.strip())
        print(f"Processing note {idx + 1}/30...")
        
        extracted = call_extractor(record["input"])
        expected = record["expected"]
        
        note_errors = {}
        for field in fields:
            gold_val = expected.get(field, "")
            ext_val = extracted.get(field, "")
            
            scores[field]["total"] += 1
            if str(gold_val).strip() == str(ext_val).strip():
                scores[field]["correct"] += 1
            else:
                note_errors[field] = {"expected": gold_val, "extracted": ext_val}
        
        if note_errors:
            errors.append({
                "note_id": idx + 1,
                "input": record["input"],
                "errors": note_errors
            })
        
        time.sleep(1) 

    # Generate the Markdown results table
    with open(results_path, "w", encoding="utf-8") as f:
        f.write("# 評価結果 (Evaluation Results)\n\n")
        f.write("## フィールド別精度 (Field Accuracy)\n\n")
        f.write("| フィールド (Field) | 精度 (Accuracy) | 正解数 (Correct/Total) |\n")
        f.write("| --- | --- | --- |\n")
        
        total_correct = 0
        total_fields = 0
        for field in fields:
            acc = scores[field]["correct"] / scores[field]["total"] * 100
            f.write(f"| {field} | {acc:.1f}% | {scores[field]['correct']}/{scores[field]['total']} |\n")
            total_correct += scores[field]["correct"]
            total_fields += scores[field]["total"]
        
        overall_acc = total_correct / total_fields * 100
        f.write(f"| **Overall** | **{overall_acc:.1f}%** | **{total_correct}/{total_fields}** |\n\n")
        
        f.write("## 抽出エラー (Failure Logs)\n\n")
        for err in errors:
            f.write(f"### Note {err['note_id']}\n")
            f.write(f"**Input:** {err['input']}\n\n")
            for field, diff in err['errors'].items():
                f.write(f"- **{field}**\n")
                f.write(f"  - Expected: `{diff['expected']}`\n")
                f.write(f"  - Extracted: `{diff['extracted']}`\n")
            f.write("\n")

    print(f"\nEvaluation complete. Results saved to {results_path}")

if __name__ == "__main__":
    run_eval()