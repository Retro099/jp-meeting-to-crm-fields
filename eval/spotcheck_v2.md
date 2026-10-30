# Judge spot-check (random seed 42)

**Result:** 20 of 20 sampled judge grades checked by hand (Prithivi, 2026-10-30): 20/20 agree on verdict, 20/20 agree on supported. Small sample, so it supports that the judge is reasonable, not that it is perfect.

Mark each row: **agree** / **disagree** with the judge, for both verdict and supported.

| # | Key | Field | Gold | Predicted | Judge verdict | Judge supported | Your verdict | Your supported |
|---|---|---|---|---|---|---|---|---|
| 1 | judge-r3|old|n13|期限 | 期限 | 明日中 | 明日中 | match | True | agree | agree |
| 2 | judge-r1|old|n23|リスク | リスク | 動画配信遅延に対するクレーム、損害賠償の可能性 | 損害賠償の可能性 | partial | True | agree | agree |
| 3 | judge-r1|old|n06|会社名 | 会社名 | サクラコマース | サクラコマース | match | True | agree | agree |
| 4 | judge-r3|agent|n04|期限 | 期限 | 今週の金曜 | 今週の金曜 | match | True | agree | agree |
| 5 | judge-r1|agent|n28|期限 | 期限 | 金曜夕方 | 金曜夕方 | match | True | agree | agree |
| 6 | judge-r1|agent|n22|次アクション | 次アクション | データ移行ロードマップと工数見積もりの提出 | データ移行のロードマップと工数見積もりの提出 | match | True | agree | agree |
| 7 | judge-r1|agent|n17|会社名 | 会社名 | ダイナミック物流 | ダイナミック物流 | match | True | agree | agree |
| 8 | judge-r1|old|n29|リスク | リスク | 決済連携のセキュリティ基準不適合、スクラッチ開発の可能性 | セキュリティ基準の不一致によるスクラッチ開発の可能性 | match | True | agree | agree |
| 9 | judge-r3|agent|n03|期限 | 期限 | 今月末 | 今月末 | match | True | agree | agree |
| 10 | judge-r1|old|n21|リスク | リスク | 24時間サポート非対応に対する不満 | サポート体制の不安 | partial | True | agree | agree |
| 11 | judge-r3|old|n21|相手 | 相手 | 吉田 | 吉田 | match | True | agree | agree |
| 12 | judge-r3|agent|n04|次アクション | 次アクション | 導入事例レポートの送付 | 導入事例のレポート送付 | match | True | agree | agree |
| 13 | judge-r2|agent|n24|次アクション | 次アクション | セキュリティチェックシート追加項目の記入・返送 | セキュリティチェックシートの追加項目の埋め込み | match | True | agree | agree |
| 14 | judge-r1|old|n18|リスク | リスク | APIレスポンス速度への懸念 | APIのレスポンス速度 | match | True | agree | agree |
| 15 | judge-r3|old|n03|期限 | 期限 | 今月末 | 今月末 | match | True | agree | agree |
| 16 | judge-r2|old|n29|相手 | 相手 | 高田 | 高田 | match | True | agree | agree |
| 17 | judge-r1|old|n07|次アクション | 次アクション | 移行支援プラン詳細および見積もりの提示 | 移行支援プランの詳細とお見積りの提示 | match | True | agree | agree |
| 18 | judge-r1|old|n07|会社名 | 会社名 | 有限会社マルエイ商事 | 有限会社マルエイ商事 | match | True | agree | agree |
| 19 | judge-r1|old|n20|会社名 | 会社名 | サンライズ不動産 | サンライズ不動産 | match | True | agree | agree |
| 20 | judge-r1|agent|n16|会社名 | 会社名 | 株式会社スマートコミュニケーション | 株式会社スマートコミュニケーション | match | True | agree | agree |

Note: row 13 is a borderline case (predicted 埋め込み 'embed' vs gold 記入・返送 'fill in and return'); the judge said match and the recorded answer is kept as given.
