# Mini 操作
所有脚本相对于本Skill；Python 使用 3.11+。共享契约的 AUTO Gate 方法保持不变。

- init REVIEW --source MANUSCRIPT；baseline 后完成 00_baseline_audit.md。
- packet REVIEW --round 1；分别调用隔离 Agent A/B，保存 round_1/reviewer_A.md 与 .json（B同理），register-report --round 1 --reviewer A --context-id 真实ID；freeze-round --round 1。需要时 C 同样注册。
- 报告冻结后写 round_1/consensus.md，汇总 issues.csv；A Gate 后修订，revision/changes.md 保存动作/结果。不重复维护 round_N/triage.csv。
- 科学修订完做 fact-lock REVIEW --record revision/changes.md。无需润色时写有理由的语言检查记录并运行 language-check REVIEW --record polishing/language_check.md。需要润色则执行引擎与事实/语义校验，最后记录 polishing_status=COMPLETE；不伪造已执行。
- 完成修订后写 revision/risk.json，字段：material_change、unresolved_disagreement（真实布尔值）；change_summary、scientific_and_structural_impact、evidence_pointers、closure_summary（实质说明，含实际文件/问题定位）。assess-risk REVIEW --record revision/risk.json 保存内容/台账指纹，不能凭文件存在跳过。
- 若返回 fresh_review_required，packet --round 2 后用新隔离上下文复审并冻结，汇总共识和新增意见到同一台账。台账变化后重新评估风险；若再改科学内容，重新冻结事实/检查语言并 reopen 受影响轮次，旧指纹不能复用。
- 完成 qa/combined_audit.md 全部维度，audit-all REVIEW --record qa/combined_audit.md。C记录当前复核完成（有条件的独立复审或定点复核），D记录最终定稿；依据共享规则 AUTO 或实际用户选择。
- check / finalize / package REVIEW --output DEST。导出真实 review_coverage，保留原版出版格式。

修改性质由 Agent 对照首轮稿件实际判断；脚本额外保守检测非正文证据/资产变化、接受的重大意见和过期记录。代码不能识别所有文字语义变化，不能把通过机械检查当科学审查。
