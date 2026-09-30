import json
import os
import sys
import time
from openai import OpenAI
from dotenv import load_dotenv

# Make the repo root importable so the shared prompt is used (python eval/run_eval.py)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from prompts import API_BASE_URL, MODEL_NAME, SYSTEM_PROMPT, TEMPERATURE  # noqa: E402

# Load environment variables
load_dotenv()

# Initialize client securely
client = OpenAI(
    api_key=os.getenv("AICREDITS_API_KEY"),
    base_url=API_BASE_URL
)

def call_extractor(text):
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"入力メモ:\n{text}"}
            ],
            response_format={"type": "json_object"},
            temperature=TEMPERATURE,
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