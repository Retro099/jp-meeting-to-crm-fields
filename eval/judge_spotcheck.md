# LLM judge — AI-assisted spot-check (2026-09-30)

**Status:** AI-assisted spot-check (all 60 verdicts); manual verification by the author is pending. AIによるスポットチェック（全60件）。作者による手動確認は実施予定。

These are the iteration 4 verdicts (eval run on 2026-09-30, [judge_results.jsonl at ed59caf](https://github.com/Retro099/jp-meeting-to-crm-fields/blob/ed59caf/eval/judge_results.jsonl)). Later eval runs overwrite `judge_results.jsonl`; this check was not repeated for them.

All 60 judge verdicts were read (30 notes × 次アクション / リスク) and each one was compared with the gold and predicted values in judge_results.jsonl (link above).

- **Agreement: 53/60 (88%).** 次アクション 24/30, リスク 29/30.
- **All 7 disagreements are the judge being too lenient** (it said `match` where the AI-assisted check says `partial`). It was never stricter than the AI-assisted check, and it never said `miss`.
- The judge is also inconsistent: dropping one part of a two-part action is `partial` in notes 5, 9, 10 and 15 but `match` in notes 17, 24 and 28.

| Note | Field | Gold | Predicted | Judge | AI-assisted check | Why |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | リスク | `セキュリティ要件が厳しく、オンプレ版希望がネック` | `セキュリティ要件の厳しさによるクラウド版の採用難` | match | partial | Does not mention the on-premises request that is the bottleneck. |
| 11 | 次アクション | `ROIシミュレーションの再提出` | `ROIのシミュレーションの提出` | match | partial | "Re-submit" became "submit". |
| 13 | 次アクション | `修正要望の確認および回答` | `確認後、回答` | match | partial | No object: what is checked and answered is missing. |
| 17 | 次アクション | `価格改定の詳細内訳書の作成と提出` | `詳細な内訳書の提出` | match | partial | Missing 作成 and the price-revision context. |
| 19 | 次アクション | `現場向けメリットまとめ資料の送付` | `A4資料のPDF送付` | match | partial | Format is right but the content (benefits for field staff) is missing. |
| 24 | 次アクション | `セキュリティチェックシート追加項目の記入・返送` | `セキュリティチェックシートの追加項目の埋め込み` | match | partial | Missing 返送 (send back). |
| 28 | 次アクション | `オンボーディング代行の追加見積もりの提出` | `追加見積もりの提出` | match | partial | Missing what the estimate is for. |

With the AI-assisted verdicts the semantic scores would be 次アクション 81.7% (19 match / 11 partial) and リスク 73.3% (14 match / 16 partial), against the judge's 91.7% and 75.0%.

**Limitation:** the judge is the same model (Qwen 2.5 72B) as the extractor, so some self-judging bias is expected. The spot-check was done by an AI assistant, not by the author or a Japanese-speaking domain expert; the author will verify it by hand later.
