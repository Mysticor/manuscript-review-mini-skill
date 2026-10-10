---
name: manuscript-review-mini
description: >
  Manuscript Review Mini：两位独立审稿、统一问题台账、最小修订和按风险复审，按需润色，
  保留证据核验并交接排版。用于审稿mini、轻量论文审查与修订；不宣称等同原版六人次独立审查。
---
# Manuscript Review Mini

Research Workflow Skills · 03 · Review. See the repository README for the four-stage series and installation.

对完整初稿进行科学审查与最小必要修订，交付 reviewed Markdown 和 PUBLICATION_HANDOFF。先科学，再结构，再语言；不是重写一篇新论文。

## 开始与恢复
沿用实际项目目录，读取 state.json、issues.csv 和 resume.md（若有），按当前问题打开正文与证据。首次审查必须完整通读稿件；进度摘要不能代替独立审稿。
使用 Python 3.11+ 运行 scripts/reviewctl.py。新项目 `init REVIEW --source MANUSCRIPT`，保留不可变输入副本，不覆盖原稿。已有原版项目保留 full 校验，不自动降低审查标准。
运行 scripts/projectctl.py open PROJECT；首次涉及状态、版本或决定读[共享契约](../../../workflow-contract/README.md)，按当前阶段读[流程](references/workflow.md)。

## 独立审查与修订
默认两位互不知晓对方意见的隔离 Agent，A 侧重方法/证据，B 侧重论证/图表/一致性；两者都读完整稿件，使用 nature-reviewer，记录真实 context_id 和冻结报告。有重要专业分歧或缺少专项能力时加入 C，不为凑数量制造问题。无法隔离时明确限制，不认证独立审查。
先向用户简述主要问题、建议修改范围和可能影响，再展开重大修改。明确的局部修正可直接做；重大方向/证据选择需实际决定，已有决定沿用，其他技术检查点 AUTO。
所有意见汇总到 issues.csv；证据、处理决定、修改位置和复核结果记在同一行/对应记录。revision/changes.md 合并必要修订动作和结果，既有正确段落保留。缺核心证据回 Stage1，需重新组织科学内容定点回 Stage2，兼容蓝图/写作的 mini 版本，不擅自扩张研究。

## 复核与语言
修改后逐项核对意见闭合、相关内容和可能回归，通读全稿。填写[风险评估与命令](references/mini-operations.md)中的 JSON，由 assess-risk 判定是否需要全新复审。重大科学/结构变化、接受的重大意见或尚存重要分歧需独立新上下文复审；不能把重大修改标成小修以跳过。
默认没有上述触发时不重复全新审稿，完成有证据的定点复核。需要复审时用两个新上下文（必要时加C），不带首轮意见和修订历史，冻结后再比较。复审后再改内容会使其过期。
语言合格可检查后记录 NOT_NEEDED，不为完成流程改写。需要润色时只处理有问题的段落，调用 nature-polishing；前后做事实锁和语义比较，保留数字、引用和主张强度。Humanizer 仅按共享契约按需使用。

## 交付与接续
用 qa/combined_audit.md 覆盖所有适用检查维度，引用按[文献审计](references/citation-audit.md)检查支持关系与覆盖，不适用项说明理由；audit-all 记录当前内容和问题台账指纹。脚本不能判断科学真伪，逐项复核必须实际完成。
每批保存文件和根目录 resume.md（已处理问题、待办/阻塞、下一步文件和决定，通常一页以内）。长日志与完整报告保存在文件，按需读证据；不自行开新任务。
check/finalize/package 保留数字、引用、来源、核心阻塞和 MOCK 隔离要求。交接包含 review_coverage.json，如实说明人数、轮次与润色情况，不冒充原版完整双轮审稿。止于稿件和出版交接，不编译论文PDF。
