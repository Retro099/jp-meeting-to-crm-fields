# 評価結果 (Evaluation Results)

Measured at temperature=0 on 2026-09-30 with `qwen/qwen-2.5-72b-instruct` on the 30 labelled notes in `data/gold_30.jsonl`.

## フィールド別精度 (Field Accuracy)

| フィールド (Field) | Exact match | 正解数 (Correct/Total) | LLM-judge (semantic) | LLM-judge strict (match only) |
| --- | --- | --- | --- | --- |
| 会社名 | 93.3% | 28/30 | — | — |
| 相手 | 100.0% | 30/30 | — | — |
| 次アクション | 23.3% | 7/30 | 91.7% (25 match / 5 partial / 0 miss) | 83.3% (25/30) |
| 期限 | 80.0% | 24/30 | — | — |
| リスク | 0.0% | 0/30 | 75.0% (15 match / 15 partial / 0 miss) | 50.0% (15/30) |
| **Overall** | **59.3%** | **89/150** | — | — |

- **Exact match**: the predicted string must equal the gold string after trimming whitespace.
- **LLM-judge (semantic)**: only for 次アクション and リスク. The same model grades each prediction against the gold answer (`eval/judge.py`, prompt in `eval/judge_prompt.txt`, temperature 0): match = 1, partial = 0.5, miss = 0. The strict column counts `match` only.
- **Limitation**: the judge is the same model family as the extractor, so it may be biased in favour of its own wording (self-judging bias). Treat the semantic column as a rough guide, not ground truth.

## History (overall exact match)

| Iteration | Overall |
| --- | --- |
| Iteration 1 | 28.7% |
| Iteration 2 | 53.3% |
| Iteration 3 — before temperature=0 ([details](results_pre_t0.md)) | 56.0% |
| Iteration 4 — same prompt, temperature=0 (this run) | 59.3% |

## Cost and latency (measured)

| Run | API calls | Prompt tokens | Completion tokens | Total tokens | Est. cost | Avg latency |
| --- | --- | --- | --- | --- | --- | --- |
| Extraction (30 notes) | 30 | 14,382 | 2,133 | 16,515 | ≈ ₹0.64 | 4.6 s / note |
| LLM judge | 60 | 34,532 | 1,893 | 36,425 | ≈ ₹1.40 | 2.58 s / call |

Cost is an estimate: $0.36/M input and $0.4/M output tokens (upstream rate), × 1.05 forex buffer × 1.05 platform fee (AICredits pricing docs), at USD/INR 96.06 (open.er-api.com rate, 2026-09-30). The AICredits dashboard shows the exact amount charged.

An AI-assisted spot-check (all 60 verdicts) of the judge verdicts is in [judge_spotcheck.md](judge_spotcheck.md); manual verification by the author is pending.

## 抽出エラー (Failure Logs, exact match)

### Note 1
**Input:** 【MTGメモ】株式会社ABCの田中部長と商談。今期の予算取りについて、かなり難航している模様。来週の水曜までに弊社から見積もりを再提示することになった。それを見て社内稟議にかけるとのこと。

- **リスク**
  - Expected: `予算取りが難航している`
  - Extracted: `予算取りの難航`
  - LLM judge: match — The predicted answer captures the key point of the gold answer with the same meaning, despite minor differences in phrasing.

### Note 2
**Input:** 10/12 吉田産商さま（鈴木さん、佐藤さん） 先方の要件ヒアリング。セキュリティ要件が厳しく、クラウド版ではなくオンプレ版を希望している（これがネックになるかも）。次回打ち合わせ前にオンプレ版の構成案を出す必要あり。10月20日がデッドライン。

- **次アクション**
  - Expected: `オンプレ版の構成案を提出`
  - Extracted: `オンプレ版の構成案の提出`
  - LLM judge: match — The predicted answer covers the key point of submitting the on-premises version configuration proposal with the same meaning as the gold answer.
- **リスク**
  - Expected: `セキュリティ要件が厳しく、オンプレ版希望がネック`
  - Extracted: `セキュリティ要件の厳しさによるクラウド版の採用難`
  - LLM judge: match — The predicted answer captures the key point of the security requirements being strict and the difficulty in adopting the cloud version.

### Note 3
**Input:** 打ち合わせ記録：(株)フロントライン 開発チーム 高橋様。API連携の件、先方のエンジニアリソースが足りておらず、実装フェーズでスケジュール遅延の懸念あり。とりあえず今月末までにAPI仕様書をこっちでまとめて送る。

- **リスク**
  - Expected: `先方エンジニアリソース不足による実装遅延`
  - Extracted: `エンジニアリソース不足によるスケジュール遅延`
  - LLM judge: match — The predicted answer covers the key point of resource shortage causing schedule delay, which is the same as the gold answer.

### Note 4
**Input:** テックビジョン 山本社長との会食にて。AI導入には前向きだが、費用対効果を社内で説明しきれないとのこと。導入事例のレポートを今週の金曜までにメールで送付する。競合のX社も接触しているらしいので注意。

- **次アクション**
  - Expected: `導入事例レポートの送付`
  - Extracted: `導入事例のレポートの送付`
  - LLM judge: match — The predicted answer covers the key point of sending the report of implementation cases with the same meaning as the gold answer.
- **リスク**
  - Expected: `競合（X社）の接触、費用対効果の社内説得が困難`
  - Extracted: `競合のX社も接触している`
  - LLM judge: partial — The predicted answer covers only one of the two key risks mentioned in the gold answer.

### Note 5
**Input:** 2026/09/28 インターネットソリューションズ合同会社 カスタマーサクセス部 伊藤さん。現状の運用フローに不満がある模様。解約をちらつかせている。至急、来週の月曜までに改善提案書を作成して持参すること。

- **次アクション**
  - Expected: `改善提案書の作成と持参`
  - Extracted: `改善提案書の作成`
  - LLM judge: partial — The predicted answer is missing the part about bringing the proposal document.
- **リスク**
  - Expected: `現状の運用フローへの不満、解約の可能性`
  - Extracted: `解約の可能性`
  - LLM judge: partial — The predicted answer only covers one of the two key points in the gold answer.

### Note 6
**Input:** サクラコマース 渡辺様とオンラインMTG。先方代表が今月末で退任予定らしく、意思決定者が変わると案件が白紙になる危険性あり。次回定例（10/5）までに新体制向けの概要資料を作成しておくこと。

- **次アクション**
  - Expected: `新体制向け概要資料の作成`
  - Extracted: `新体制向けの概要資料作成`
  - LLM judge: match — The predicted answer covers the same key point as the gold answer with the same meaning.
- **リスク**
  - Expected: `代表退任による意思決定者交代、案件白紙の可能性`
  - Extracted: `意思決定者の変更による案件の白紙化`
  - LLM judge: match — The predicted answer covers all key points of the gold answer with the same meaning.

### Note 7
**Input:** 10/3 有限会社マルエイ商事（小林専務）。他社ツール（セールスフォース）からの乗り換え検討中だが、現場オペレーターのITリテラシーが低く、移行後の定着に強い不安を抱いている。移行支援プランの詳細とお見積りを10月15日までに提示する約束。

- **次アクション**
  - Expected: `移行支援プラン詳細および見積もりの提示`
  - Extracted: `移行支援プランの詳細とお見積りの提示`
  - LLM judge: match — The predicted answer covers all key points of the gold answer with the same meaning.
- **リスク**
  - Expected: `現場のITリテラシー不足による移行後の定着不安`
  - Extracted: `現場オペレーターのITリテラシーが低く、移行後の定着に不安`
  - LLM judge: match — The predicted answer covers all key points of the gold answer with the same meaning.

### Note 8
**Input:** 【社内議事録】ネクストイノベーション訪問（弊社：鈴木・山田、先方：中村CTO）。現在のDB構成だと負荷に耐えられないかもしれないとのこと。要件定義のすり合わせが必須。来週火曜の夕方までにベンチマークテストの結果を連携する。

- **リスク**
  - Expected: `現行DB構成の負荷懸念、要件定義の不整合`
  - Extracted: `DB構成の負荷耐えられない可能性`
  - LLM judge: partial — The prediction covers only one of the two key points in the gold answer.

### Note 9
**Input:** 大同ロジスティクス 佐々木課長。現場の反発が予想以上に激しいらしい。「使い勝手が変わると困る」とのこと。とりあえずデモ画面の動画を撮って、今週中（金曜18時）に共有することになった。導入見送りの可能性大。

- **次アクション**
  - Expected: `デモ画面動画の撮影と共有`
  - Extracted: `デモ画面の動画撮影`
  - LLM judge: partial — The prediction covers the main point but misses the detail of sharing the video.
- **リスク**
  - Expected: `現場の強い反発、導入見送りの可能性`
  - Extracted: `現場の反発、導入見送りの可能性`
  - LLM judge: match — The predicted answer covers all key points of the gold answer with the same meaning.

### Note 10
**Input:** メディカルサポート（株） 木村さん。コンプライアンス審査で引っかかる可能性があるとのこと。個人情報の取り扱い規約について法務チェック待ち。明日中に弊社側のセキュリティチェックシートを記入して返送する手はず。

- **次アクション**
  - Expected: `セキュリティチェックシートの記入・返送`
  - Extracted: `セキュリティチェックシートの返送`
  - LLM judge: partial — The predicted answer is missing the key point of filling out the security checklist.
- **期限**
  - Expected: `明日中`
  - Extracted: `明日`
- **リスク**
  - Expected: `コンプライアンス審査での懸念、法務チェック待ち`
  - Extracted: `コンプライアンス審査の問題`
  - LLM judge: partial — The predicted answer covers the main point of compliance review concerns but lacks the specific detail about the legal check pending.

### Note 11
**Input:** グローバルエージェンシーの林さんと電話。先方の社長が予算承認を渋っているとのことで、ROIのシミュレーションを出し直してほしいと依頼された。明後日の正午までにエクセルで提出。他社の類似システムに乗り換える可能性も匂わせていた。

- **次アクション**
  - Expected: `ROIシミュレーションの再提出`
  - Extracted: `ROIのシミュレーションの提出`
  - LLM judge: match — The predicted answer covers the key point of resubmitting the ROI simulation with the same meaning as the gold answer.
- **リスク**
  - Expected: `予算承認の難航、他社システムへの乗り換え`
  - Extracted: `他社システムへの乗り換え`
  - LLM judge: partial — The predicted answer only covers one of the two key risks mentioned in the gold answer.

### Note 12
**Input:** 【訪問記録】10月5日 (株)フロンティアテック 松本本部長。前回提案したUIについて「少し複雑すぎる」とのフィードバックあり。操作マニュアルが充実していないと現場が混乱すると懸念。来週の定例（10/12）で簡易版のプロトタイプを見せる。

- **リスク**
  - Expected: `UIの複雑さへの不満、現場の混乱懸念`
  - Extracted: `操作マニュアルの不足による現場の混乱`
  - LLM judge: partial — The predicted answer covers the concern about confusion at the site but misses the dissatisfaction with the complexity of the UI.

### Note 13
**Input:** グリーンエネルギーホールディングス 高田様、清水様。基本合意に向けて最終確認。ただ、契約書の特約条項で法務部門からストップがかかっている模様。具体的な修正要望を今日の15時までにテキストで送ってくれるとのこと。確認後、明日中にこちらから回答する。

- **次アクション**
  - Expected: `修正要望の確認および回答`
  - Extracted: `確認後、回答`
  - LLM judge: match — The predicted answer covers the key points of confirming and responding to the revision requests.
- **期限**
  - Expected: `明日中`
  - Extracted: `明日`
- **リスク**
  - Expected: `契約書の特約条項に対する先方法務のストップ`
  - Extracted: `契約書の特約条項で法務部門からストップ`
  - LLM judge: match — The predicted answer covers all key points of the gold answer with the same meaning.

### Note 14
**Input:** 北斗建材 鈴木係長。トライアル利用の進捗確認MTG。全くログインしていないユーザーが半数以上いる。現場への浸透が遅れているのが致命的。今週末までに使い方セミナーの動画リンクを送付して、各部署のマネージャーに周知してもらう。

- **次アクション**
  - Expected: `使い方セミナー動画リンクの送付`
  - Extracted: `使い方セミナーの動画リンクの送付`
  - LLM judge: match — The predicted answer covers the key point of sending the seminar video link with the same meaning as the gold answer.
- **リスク**
  - Expected: `トライアル利用率の低迷、現場への浸透遅れ`
  - Extracted: `現場への浸透が遅れている`
  - LLM judge: partial — The predicted answer covers one of the two key points in the gold answer, but misses the other point about the low trial usage rate.

### Note 15
**Input:** アーバンライフデザイン（株）の山田さんとのランチ。上期中に導入したい意向は強いが、競合のA社からかなり安い見積もりを出されているらしい。価格勝負になると厳しい。ひとまず、金曜の午前中に追加の割引オプションを含めた再見積もりを出す。

- **次アクション**
  - Expected: `追加割引オプションを含めた再見積もりの提出`
  - Extracted: `再見積もりの提出`
  - LLM judge: partial — The predicted answer is missing the detail about the additional discount option.
- **期限**
  - Expected: `金曜の午前中`
  - Extracted: `金曜の午前`
- **リスク**
  - Expected: `競合からの安価な見積もり、価格競争による失注懸念`
  - Extracted: `競合の安い見積もり`
  - LLM judge: partial — The predicted answer covers only one of the two key points in the gold answer.

### Note 16
**Input:** 10/18 (株)スマートコミュニケーション 佐藤部長。新システムのUI改修について。デザインが古臭いと指摘あり。とりあえず金曜までに別案を3つ用意してチャットで投げる。最悪、他社コンペになるかも。

- **次アクション**
  - Expected: `UI別案3つの作成と送付`
  - Extracted: `別案3つの用意とチャットでの提出`
  - LLM judge: match — The predicted answer covers all key points of the gold answer with the same meaning.
- **リスク**
  - Expected: `デザインへの不満、他社コンペ化の可能性`
  - Extracted: `他社コンペの可能性`
  - LLM judge: partial — The prediction covers only one of the two key points in the gold answer.

### Note 17
**Input:** ダイナミック物流さん（高橋さん）。料金プランの改定についてクレーム気味。「話が違う」とのこと。来週の火曜の午前中までに、どうしてこの価格になったのか詳細な内訳書を作って提出する。納得いかなければ解約も辞さない構え。

- **次アクション**
  - Expected: `価格改定の詳細内訳書の作成と提出`
  - Extracted: `詳細な内訳書の提出`
  - LLM judge: match — The predicted answer covers the key point of creating and submitting a detailed breakdown of the price revision.
- **リスク**
  - Expected: `価格改定へのクレーム、解約の可能性`
  - Extracted: `解約の可能性`
  - LLM judge: partial — The predicted answer covers only one of the two key points in the gold answer.

### Note 18
**Input:** 【オンライン商談】 ライフスタイルテクノロジーズ 渡辺CTO。APIのレスポンス速度に懸念を示している。実地でのパフォーマンステストが必要。今月中にテスト環境の構築を終わらせてアカウントを発行する。

- **次アクション**
  - Expected: `テスト環境の構築とアカウント発行`
  - Extracted: `テスト環境の構築、アカウントの発行`
  - LLM judge: match — The predicted answer covers all key points of the gold answer with the same meaning.
- **リスク**
  - Expected: `APIレスポンス速度への懸念`
  - Extracted: `APIのレスポンス速度`
  - LLM judge: match — The predicted answer covers the key point of the gold answer with the same meaning.

### Note 19
**Input:** 9/25 訪問記録：エクセル商事（小川課長）。現場の担当者が誰も新しいツールを使いたがらないのが最大の障壁。とにかく現場向けのメリットをまとめたA4の資料を明日の夕方までにPDFで送ってくれと依頼された。

- **次アクション**
  - Expected: `現場向けメリットまとめ資料の送付`
  - Extracted: `A4資料のPDF送付`
  - LLM judge: match — The predicted answer covers the key point of sending the summarized benefits document to the site, matching the gold answer.
- **期限**
  - Expected: `明日の夕方`
  - Extracted: `明日夕方`
- **リスク**
  - Expected: `現場担当者のツール導入への抵抗`
  - Extracted: `現場の担当者が新しいツールを使いたがらない`
  - LLM judge: match — The predicted answer captures the key point of resistance from field staff towards tool adoption, which is the same as the gold answer.

### Note 20
**Input:** サンライズ不動産 伊藤社長との会食。基本的には導入前提で進めているが、競合のB社が強烈な値引きをしてきているとのこと。予算の再調整が必要か。来週月曜の定例までに役員向け決裁資料のドラフトを作る。

- **次アクション**
  - Expected: `役員向け決裁資料ドラフトの作成`
  - Extracted: `役員向け決裁資料のドラフト作成`
  - LLM judge: match — The predicted answer covers the same key point as the gold answer with no significant differences in meaning.
- **リスク**
  - Expected: `競合（B社）の強烈な値引き`
  - Extracted: `競合のB社の強烈な値引き`
  - LLM judge: match — The predicted answer covers every key point of the gold answer with the same meaning.

### Note 21
**Input:** 10/01 (同)オメガパートナーズ 吉田様。サポート体制に不安があるとのこと。24時間対応じゃないと厳しいと。一旦、サポートのSLA定義書を明後日までに提出して、どこまでなら対応可能か線引きする。

- **会社名**
  - Expected: `合同会社オメガパートナーズ`
  - Extracted: `オメガパートナーズ`
- **次アクション**
  - Expected: `サポートSLA定義書の提出`
  - Extracted: `サポートのSLA定義書の提出`
  - LLM judge: match — The predicted answer covers every key point of the gold answer with the same meaning.
- **リスク**
  - Expected: `24時間サポート非対応に対する不満`
  - Extracted: `サポート体制の不安`
  - LLM judge: partial — The prediction captures the general concern about support structure but lacks the specific detail about the dissatisfaction with non-24/7 support.

### Note 22
**Input:** MTG：株式会社フューチャーネット 鈴木さん、田中さん。既存システムからのデータ移行がボトルネック。CSVのフォーマットが合わない。金曜15時までにデータ移行のロードマップと工数見積もりを出す。工数次第では見送られる可能性大。

- **次アクション**
  - Expected: `データ移行ロードマップと工数見積もりの提出`
  - Extracted: `データ移行のロードマップと工数見積もりの提出`
  - LLM judge: match — The predicted answer covers all key points of the gold answer with the same meaning.
- **リスク**
  - Expected: `データ移行の難易度、工数過大による見送り懸念`
  - Extracted: `工数次第で見送られる可能性大`
  - LLM judge: partial — The predicted answer covers the risk of potential cancellation due to workload, but misses the difficulty of data migration.

### Note 23
**Input:** 【定例】 10/10 メディアクロス 斎藤局長。動画配信の遅延が多発している件でかなりお怒り。根本原因のレポートを急ぎで求められた。明日13時までに障害報告書（一次回答）を提出する。損害賠償の話に発展する可能性あり。

- **次アクション**
  - Expected: `障害報告書（一次回答）の提出`
  - Extracted: `障害報告書の提出`
  - LLM judge: match — The predicted answer covers the key point of submitting the initial report on the incident, which is the same as the gold answer.
- **リスク**
  - Expected: `動画配信遅延に対するクレーム、損害賠償の可能性`
  - Extracted: `損害賠償の可能性`
  - LLM judge: partial — The predicted answer only mentions the possibility of compensation, missing the key point about the complaint regarding video streaming delays.

### Note 24
**Input:** グッドウェーブ 中村さん。マーケティング部門での利用は確定だが、全社導入にはまだハードルがある。特にセキュリティ監査。来週末までにセキュリティチェックシートの追加項目を埋めて返送する必要あり。

- **次アクション**
  - Expected: `セキュリティチェックシート追加項目の記入・返送`
  - Extracted: `セキュリティチェックシートの追加項目の埋め込み`
  - LLM judge: match — The predicted answer covers the same key point as the gold answer with the same meaning.
- **リスク**
  - Expected: `全社導入に向けたセキュリティ監査のハードル`
  - Extracted: `全社導入のハードル、特にセキュリティ監査`
  - LLM judge: match — The predicted answer covers all key points of the gold answer with the same meaning.

### Note 25
**Input:** 10/15 (株)クレセント 山本部長。うちのシステムの機能不足を指摘された。カスタマイズ対応できるか確認してほしいとのこと。開発チームと相談して、今週水曜の午前中に実装可否の一次回答をする。

- **期限**
  - Expected: `今週水曜の午前中`
  - Extracted: `今週水曜`
- **リスク**
  - Expected: `システム機能不足の指摘`
  - Extracted: `システムの機能不足`
  - LLM judge: match — The predicted answer covers the key point of the gold answer with the same meaning.

### Note 26
**Input:** 【ヒアリングメモ】 ベルテクノロジー 佐々木さん。予算は確保済みとのことだが、稟議を通すために競合他社との比較表が欲しいと言われた。来週の火曜までにA社、B社との機能・価格比較表をスプレッドシートで共有する。

- **次アクション**
  - Expected: `競合他社との機能・価格比較表の共有`
  - Extracted: `競合比較表の共有`
  - LLM judge: match — The predicted answer covers all key points of the gold answer with the same meaning.
- **リスク**
  - Expected: `稟議通過のための競合比較の必要性`
  - Extracted: `稟議通過のための競合比較が必要`
  - LLM judge: match — The predicted answer covers the key point of the gold answer with the same meaning.

### Note 27
**Input:** 9/28 (有)大和製作所 小林社長。製造現場でのタブレット利用を想定しているが、通信環境が悪いエリアがあるらしい。オフライン対応が必須条件になりそう。次回MTG（10/8）までにオフライン機能の仕様書を用意する。

- **次アクション**
  - Expected: `オフライン機能の仕様書用意`
  - Extracted: `仕様書の用意`
  - LLM judge: partial — The predicted answer is missing the specific detail of 'オフライン機能'.
- **リスク**
  - Expected: `製造現場の通信環境悪化、オフライン対応の必須化`
  - Extracted: `通信環境が悪いエリアがある`
  - LLM judge: partial — The predicted answer covers only one of the two key points in the gold answer.

### Note 28
**Input:** 株式会社エニシング 渡部マネージャー。現状のトライアル進捗は良好。ただし、導入後のオンボーディングを誰がやるかで揉めている。うちが代行するなら追加費用が必要。金曜夕方までにオンボーディング代行の追加見積もりを出す。

- **次アクション**
  - Expected: `オンボーディング代行の追加見積もりの提出`
  - Extracted: `追加見積もりの提出`
  - LLM judge: match — The predicted answer covers the key point of submitting an additional estimate for onboarding, which is the same as the gold answer.
- **リスク**
  - Expected: `導入後のオンボーディング担当者の不在`
  - Extracted: `導入後のオンボーディング担当者による揉め事`
  - LLM judge: partial — The predicted answer captures the conflict over onboarding but does not specify the lack of a designated person, which is the key point of the gold answer.

### Note 29
**Input:** 【商談メモ】 ファーストステップ合同会社 高田さん。決済システムの連携でセキュリティ基準が合わない可能性。最悪、連携部分だけスクラッチ開発になるかも。来週の水曜15時までに開発要件定義のたたき台を出すことになった。

- **会社名**
  - Expected: `ファーストステップ合同会社`
  - Extracted: `合同会社ファーストステップ`
- **リスク**
  - Expected: `決済連携のセキュリティ基準不適合、スクラッチ開発の可能性`
  - Extracted: `決済システムの連携でセキュリティ基準が合わない可能性、連携部分のスクラッチ開発の必要性`
  - LLM judge: match — The predicted answer covers all key points of the gold answer with the same meaning.

### Note 30
**Input:** 10/05 パイオニア企画 林部長。社長の鶴の一声で、急遽別プロジェクトの予算が優先されることになりそう。うちの導入時期が半年後ろ倒しになる危機。とりあえず、明日中に導入見送り時の機会損失シミュレーションを送って説得を試みる。

- **期限**
  - Expected: `明日中`
  - Extracted: `明日`
- **リスク**
  - Expected: `別プロジェクト優先による導入時期の半年後ろ倒し`
  - Extracted: `導入時期が半年後ろ倒しになる危機`
  - LLM judge: match — The predicted answer covers the key point of the gold answer with the same meaning, despite slight differences in wording.
