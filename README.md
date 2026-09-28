# Manuscript Review Mini

对完整初稿做独立审查、问题分流、最小必要修订和风险驱动复审，输出审后稿及排版交接。

## 安装

需要 Python 3.11+。完整保留仓库目录，不能只复制 SKILL.md。以下为 macOS/Linux 示例；Windows 使用对应虚拟环境和目录链接命令。

```bash
git clone https://github.com/Mysticor/manuscript-review-mini-skill.git
cd manuscript-review-mini-skill
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
ln -s "$PWD/module/codex-skill/manuscript-review-mini" "${CODEX_HOME:-$HOME/.codex}/skills/manuscript-review-mini"
```

已有同名 Skill 时先检查位置，不覆盖。重新加载 Codex Skill 列表后调用 `$manuscript-review-mini`，提供独立的研究项目目录；运行脚本时使用已安装依赖的 Python 环境。不要把研究资料保存在本工具仓库中。

写作和审稿需要符合文档约定的证据/稿件交接目录；缺失材料应补齐或明确记录，不能制造证据。

## 依赖与边界

共享状态库位于 workflow-contract。必要 Nature Skills 工具随写作/审稿仓库提供；已安装的同名工具可覆盖内置版本。需要凭据的可选服务由使用者配置，仓库不含个人账户或密钥。跨阶段 Skill 单独安装；缺少时交付材料并报告可用的下一步，不假装已经执行。审稿中的独立评审需要支持隔离 Agent 的运行环境，无法隔离时应明确限制。

保留真实证据、数值与引用追溯、内容一致性检查和 MOCK 隔离。自动化测试不能替代科学判断或逐页视觉审查，也不能保证网络和长会话稳定性。

## 校验

```bash
python -B -m unittest discover -s module/codex-skill/manuscript-review-mini/tests -p 'test_*.py'
python -B -m unittest discover -s workflow-contract/tests -p 'test_*.py'
```

测试数据仅为合成 MOCK/FIXTURE，不是真实研究。可选跨阶段测试通过 `DOWNSTREAM_SKILL_ROOT` 指定另一个仓库的 Skill 目录，未提供时明确跳过。排版验收请使用不存在的新临时目录；所需系统工具缺失时先安装依赖。

## 许可证

原创部分采用 MIT，见 LICENSE。第三方代码遵循其各自许可，见 THIRD_PARTY.md 与组件内保留的声明。

配图使用 Python 后端时，另运行 `python -m pip install -r module/vendor/nature-skills/skills/nature-figure/requirements.txt`；R 后端按组件的 R 指南配置。可选学术搜索 MCP 服务使用其目录内 requirements.txt。按实际任务安装，不强制使用付费图像服务。
