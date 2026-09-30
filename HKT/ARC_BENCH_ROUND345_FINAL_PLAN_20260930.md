# ARC-Bench Round 3/4/5 Agent 优化协作计划

日期：2026-09-30
状态：`IMPLEMENTING`（本轮已开始落地） 仅修改 Agent 与本协作文档；官方测试、需求 ZIP 和平台 Run 不修改。
目标分支：`codex/hkt-round345-integration`
基线：`codex/urgent-bookstack-contract-fix-r2` @ `f10bd9f42429c09672c9a68b79f486c44cc41e9f`

## 1. 最新决策

用户已接受新分支名，并要求在方案形成后直接开始 Agent 修改。新的硬约束是：

- 探索预算：`200–300 CNY`，建议目标 `250 CNY`，`300 CNY` 为硬上限。
- 剩余窗口：`36 小时`，必须冻结并提交终版。
- 新题官方测试/snapshot 不公开，不能宣称平台因果 A/B。
- 优先级：提高完成率 > 防止配额/超时中断 > Token/耗时优化 > 完整领域架构。
- 后续优化不得绑定旧题名称、旧 REQ 编号、旧实体或旧 locator。

因此原计划的“四个 Run 串行、严格 A/B、先做完整架构”已收缩为：

1. 先实现一组高收益 runtime 硬门禁。
2. Sheet 做第一主探针；只有成本和时间都在阈值内，才运行 GitHub 探针。
3. 每题最多一次探索性 Run，必要时一次定点修复；不称为严格 A/B。
4. 至少保留 25% 预算给 final check、定点修复和终版证据。

## 2. 原计划（预算调整前）

原计划拟在 `codex/hkt-round345-integration` 中从指定基线整合 Round 3/4/5，并安排 Sheet A/B、GitHub A/B 共四个串行 Run，预算约 `1600 CNY`、窗口约 `72 小时`。

原计划的实施顺序：

1. quota guard、usage ledger、project/source map shadow；
2. Round 4 有界 rewrite budget；
3. Round 5 impact regression shadow；
4. Round 3 checkpoint/observability；
5. source-cache/context shadow；
6. 最后才启用实际 context compaction 和 repair strategy switch。

原计划的主要收益：较完整地覆盖额度、长上下文、循环修复、恢复和跨节点回归。主要问题是预算不足时无法完成四组 Run，且会把架构建设成本置于比赛交付之前。

## 2A. 当前已落地的第一批改动

为满足“方案确定后直接出手”，当前分支已先实现以下最小切片；每项均保留短注释、测试和 checkpoint 证据：

- `arc/llm_proxy.py`：识别 `402` 与带 billing 标记的 `429`，第一次命中后进入代理级 `quota_gated`，后续 chat completion 直接拒绝；额度错误不再进入 transient retry。
- `arc/run_controls.py`：新增原子 JSON checkpoint store，临时文件 flush/fsync 后 rename，保留编号快照和 manifest。
- `arc/main.py`：写入 requirements/spec/build identity；在 run/node/turn/acceptance/quota 边界写 checkpoint；quota-gated 跳过剩余节点、full-suite repair 和 rehearsal；区分 implemented、built、smoke_verified、acceptance_verified、inconclusive；将多节点 rewrite 从无界改成有限预算；同一 failure digest 重复后切换策略并停止；读取缓存和 omitted-range 摘要避免超限后整文件重读；允许两种后端入口路径，降低结构检查器误报。
- `arc/tests/test_llm_proxy.py`、`arc/tests/test_main_helpers.py`、`arc/tests/test_run_controls.py`：覆盖 billing gate、有限 rewrite、spec omitted 摘要、回归上限和 checkpoint 原子写入。

本地定向验证：`58 tests` 通过；`py_compile` 和 `git diff --check` 通过。完整测试集合仍有基线中的 Windows 临时目录权限、npm cache 路径和路径分隔符断言问题，未归因于本切片。测试命令必须从 `arc/` 目录运行，避免把仓库外部同名 `tests` 包误当作项目测试。

### 2C. 首次打包门禁（已落地，平台前置）

Round 3/4/5 的运行时保护只有在交付包不丢文件、身份不漂移时才有意义，因此新增提交 `61ab832c`、`f086f729`、`2b35512a`：

- `arc/pack.ps1` 与 `arc/pack.sh` 都纳入 `run_controls.py`、构建身份和包形状门禁；Windows 使用 Python ZIP 写入，Git Bash 通过 `cygpath` 将 Python 参数转换为原生路径。
- `agent-build.json` 绑定源提交、payload tree SHA 和 build id；sidecar 绑定 task key、suite key、需求包 SHA 与最终 ZIP SHA。
- 离线解包后执行 `import main` smoke，并拒绝危险/重复/禁止条目、缺失身份和 placeholder identity。
- 当前需求包 `E:\飞书下载\arcbench-hackathon-requirements (3).zip` 的 SHA-256 为 `9884F23EA10C3DFEEE170D1EED57966C8FCE9A5CE18A0AC43B3D7942EBA8C414`。它同时包含 `hackathon--sheet` 和 `hackathon--github`；正式上传前必须使用平台实际分配的 suite key，不能用本地猜测值冒充官方绑定。
- 当前 ZIP 仍包含 `public-tests` 作为本地回归夹具；它不是新题私有官方 suite，也不能作为官方成绩证据。若发布流程要求最小包，应在平台契约明确后再单独裁剪并重新计算所有 SHA。

门禁验证：从 `arc/` 运行定向测试共 `60`（`OK, skipped=1`；唯一跳过项是本机没有独立 `sh` 命令的语法测试）；递归 `py_compile`、`git diff --check`、`node skills/arc-project-context/test.js`（8 assertions）通过。PowerShell 和 `E:\Program Files\Git\bin\bash.exe` 两条打包链路均使用真实需求包 SHA 完成结构/离线导入检查；Git Bash 自动跳过无 PyYAML 的 Windows Store `python3` shim，选择可用解释器。修复提交为 `a77443c0c960adf23eb0a01f5e87f4c31453e2e5`，已由 Integrator 接入。

### 2B. 通用上下文 Skill 已落地

已新增可调用 Skill：`skills/arc-project-context/`。

- `project_map`：对工作区做一次有界文件/目录索引，排除 `.git`、`.arc`、`node_modules`、构建产物和缓存目录，并返回稳定 `project_map_hash`、入口/路由/模型线索。
- `source_read`：按 `path + SHA-256 + 行范围 + max_chars` 缓存读取结果；文件变化自动失效；超限时返回 `excerpt`、`returned_line_range` 和 `omitted`，避免 Agent 重新读取整文件。
- 缓存写入 `.arc/context-cache/cache.json`，采用临时文件改名；Skill 不执行 shell、不修改源码、不承担 quota/checkpoint/预算/官方验收职责。
- `manifest.json` 使用标准 stdin/stdout 工具协议，输入路径经过工作区边界和真实路径校验，拒绝路径逃逸与外部 symlink。

验证记录：

- `node skills/arc-project-context/test.js`：退出码 `0`，8 项行为断言通过。
- `python D:/DataMove/codex/skills/.system/skill-creator/scripts/quick_validate.py skills/arc-project-context`：退出码 `0`。
- 尚未进行平台 Run；本 Skill 的缓存命中率和最终比赛完成率仍需在后续探索性 Run 中观察，不能预先宣称因果收益。

开源复用审查：仓库已有 `arc/acceptance.py` 的 SHA-256 文件指纹逻辑、Rust `globset`/`walkdir`/`sha2` 依赖，以及 Agent 内部 `file_state_cache`；这些组件分别服务于 Python 验收、Rust 工具层和进程内文件状态，不能直接作为独立 Skill 的 stdin/stdout 入口。当前 Skill 因需零安装、跨 Windows/Linux 直接运行，使用 Node.js 标准库实现协议适配和原子缓存，不新增重复第三方依赖；其路径边界、SHA 指纹和忽略目录规则与现有实现保持一致。后续若宿主暴露 `file_state_cache` 或稳定的 `walkdir` Skill API，应优先替换此适配层，而不是继续扩展本地实现。

## 3. 新计划（36 小时终版）

### 3.1 P0：必须实现的高收益硬门禁

这些改动直接针对历史中断和错误判定，不依赖任何旧题：

1. **Quota hard-stop**
   - 第一次 `402` 或带明确 billing/quota 标记的 `429` 进入 `quota_gated`。
   - 原子写入 checkpoint 与 usage 摘要。
   - 禁止后续 LLM turn、repair、full-suite repair 和 billing retry。
   - proxy EOF 最多一次有界重试；连续两次立即停止当前 Run。

2. **预算隔离**
   - design、implement、node repair、full-suite repair、final check 分开计量。
   - rewrite 不再使用多节点 `0=requests` 的无界预算。
   - rewrite 最多一次，预算为 `remaining - final_reserve`，并要求 rewrite 后 build/start/smoke。

3. **状态分离**
   - 分开记录 `implemented`、`built`、`smoke_verified`、`acceptance_verified`、`official_verified`、`inconclusive`。
   - `wrote=True`、`implemented` 或中间 runner passed 不能升级为 verified。
   - 没有真实测试证据时只能是 `inconclusive`。

4. **Repair 防循环**
   - 失败生成结构化 digest 和类别。
   - 同一 digest 第二次出现时切换策略；继续出现则停止，不重复同一 prompt。
   - 回归时恢复 best checkpoint，而不是接受局部通过但破坏旧功能的状态。

5. **Suite/build 身份 fail-closed**
   - 记录 task key、suite key、requirements hash、spec hash、Agent commit/build、submission/ZIP SHA（若平台提供）。
   - 发现 suite 与任务不匹配、身份字段缺失或内部 suite 与官方 suite 不同，标记 `identity_inconclusive` 并停止，不继续消耗 repair 预算。

6. **轻量 checkpoint**
   - 在 run start、node start、design saved、turn end、acceptance verdict、timeout、402、run end 写原子 checkpoint。
   - 第一版只支持同一 run、workspace 和 requirements hash 的恢复校验。
   - 不做跨机器 resume，不默认开启 run 级共享 session。

### 3.2 P1：低风险上下文/文件读取优化

第一版不做激进压缩，只做旁路和去重：

- `project-map`：输出入口、路由、文件、数据模型和稳定 hash。
- `source-cache`：按 `path + SHA + range` 缓存读取；写入后失效。
- `inline_sources` 和 `inline_spec_text` 不能因超限返回空串；应返回摘要、引用和 omitted ranges，避免模型重新读整文件。
- 记录 cache hit、读取字节数、prompt hash 和被裁剪区段。
- `change-impact` 先 shadow；无法建立影响面时不得自动扩张全量回归。

### 3.3 P2：Round 5 capped regression

- 只回归当前 node 的 spec、祖先 spec 和最多 `2–3` 个已通过 foundation spec。
- 改动文件未命中 foundation footprint 时不做全历史 backfill。
- 影响面未知时只记录建议，不自动启动更多 LLM 修复。

### 3.4 P3：新题通用语义契约

仅抽象跨任务能力，不写旧题字面量：

- 写入成功后原地更新，并用规范 URL 保持可刷新/可重开的状态；不无条件 full navigation。
- 实体动作位于目标实体自己的可访问作用域。
- `data-*` 写入字段与 handler 读取字段由单一契约生成。
- 认证成功跳转只有一个导航所有者。
- mutation 必须原子提交，失败不得留下半记录。

## 4. 为什么先做 Sheet，再决定 GitHub

新题需求暴露出的共同能力是 Identity/Session、Resource Graph、Scoped Action、Atomic Mutation、Route/Rehydration 和 Semantic Verification。

Sheet 更适合作为第一主探针：原子节点较少，先验证 workbook/worksheet/grid、持久化、规范 URL、grid 语义和 mutation 原子性。GitHub 原子节点更多，涉及认证、组织权限、仓库/分支、issue/PR/review/merge；只有 Sheet 没有触发 P0 告警且成本低于阈值时才运行。

官方 snapshot 不公开时，Run 结论只能标为 `exploratory`，不能把需求派生 smoke 或内部 suite 当作官方成绩。

## 5. 预算与运行策略

### 5.1 动态预算

建议以 `250 CNY` 为目标、`300 CNY` 为硬上限：

| 阶段 | 建议比例 | 250 CNY 参考 | 停止条件 |
|---|---:|---:|---|
| 实现与基础 smoke | 45% | 112 | 仍未 build/start/health 则不进入下游 |
| node repair | 15% | 38 | 同 digest 重复或无进展即停 |
| final check | 25% | 63 | 不得提前消耗 |
| contingency/提交证据 | 15% | 37 | 首次 402 或硬上限立即冻结 |

单题 Run 同时受费用和 request 上限约束，任一先触线即停止。余额低于 final reserve 时禁止 repair。

### 5.2 Run 矩阵

1. Sheet candidate：硬上限约 `40–70 CNY`，最多 `6 小时`。
2. 只有 Sheet 未 quota-gated、完成 build/start/health/smoke 且实际成本低于总预算约 40% 时，才运行 GitHub candidate：约 `80–130 CNY`，最多 `8–10 小时`。
3. 若 Sheet 已消耗过多、出现身份问题或 quota gate，放弃 GitHub 平台 Run，转本地终版交付。
4. 两个 candidate 各一次不能称严格 A/B；严格 A/B 至少需要三组闭合身份配对，本窗口不追求统计结论。

### 5.3 36 小时排程

| 时间 | 工作 | 交付门槛 |
|---|---|---|
| 0–4h | 分支、接口、checkpoint schema、测试夹具冻结 | 单写者和基线 SHA 明确 |
| 4–14h | P0 quota/预算/状态/repair；P1 source cache shadow | 本地单测可运行 |
| 14–18h | Integrator 合并、静态检查、打包和身份预检 | `py_compile`、diff check、smoke 通过 |
| 18–24h | Sheet 主探针 | 预算、quota、身份三项均正常才继续 |
| 24–32h | GitHub 探针或 Sheet 定点修复 | 不超过一次定点 repair |
| 32–34h | 证据归一化、失败分类、最终构建 | 不再新增大改动 |
| 34–36h | 冻结终版、提交、远程同步 | 工作树干净、SHA 可核验 |

## 6. 验收与 NO-GO

### GO

- quota gate 能在第一次 402/429 billing marker 后触发；
- 不再出现 402 后继续 repair；
- `wrote`、`implemented`、`verified` 互不混淆；
- checkpoint 可原子写入，损坏文件不会覆盖有效状态；
- 相同 failure digest 不会无限循环；
- suite/task/build 身份闭合；
- 没有新增本地硬失败；
- 官方 Run 若未完成，明确标注 `exploratory` 或 `partial`。

### NO-GO

- suite 身份不匹配或缺失关键绑定；
- 第一次 402 后继续计费调用；
- checkpoint 损坏导致覆盖源码；
- 中间 runner 状态覆盖最终官方结果；
- 新增通过率下降证据；
- 余额低于 final reserve 仍启动 full-suite repair。

## 7. 旧方案中不能直接照搬的内容

- Evolution 两个 Run 的分数不能相加，也不能视为严格 A/B；只能合并“原地更新、实体作用域、data-* 契约”机制。
- Keep `REQ-7.2`、`REQ-9.1` 等缺少 clean seed/精确 spec 的项目保持 `unknown`。
- `900s timeout`、proxy EOF、favicon、残留进程不是自动业务根因。
- Lite Keep 存在任务与 suite 错配，说明 suite identity 必须 fail-closed。
- Web Keep 出现提交物携带已运行数据库的污染风险，打包前必须隔离运行数据。
- “禁止 reload”需改为“写入后同文档更新、规范 URL 保持稳定”；新题要求刷新/重开恢复状态。

## 8. 已阅读资料索引

### 8.1 项目权威记录

- `D:/DataMove/codex/worktrees/2c74/AI智能体软件工厂黑客松/HKT/ARC_BENCH_HACKATHON_PROJECT_MEMORY.md`
- `D:/DataMove/codex/worktrees/2c74/AI智能体软件工厂黑客松/HKT/ARC_BENCH_HACKATHON_PHASE5_DECISION_REGISTER.md`
- `D:/DataMove/codex/worktrees/2c74/AI智能体软件工厂黑客松/HKT/ARC_BENCH_HACKATHON_EXECUTION_PLAN.md`
- `D:/DataMove/codex/worktrees/2c74/AI智能体软件工厂黑客松/HKT/ARC_BENCH_HACKATHON_PHASE5_COLLABORATION_WORKFLOW.md`
- `D:/DataMove/codex/worktrees/2c74/AI智能体软件工厂黑客松/HKT/ARC_BENCH_HACKATHON_PHASE5_CONTEXT_HANDOFF.md`
- `D:/DataMove/codex/worktrees/2c74/AI智能体软件工厂黑客松/HKT/SUMMARY.md`
- `D:/DataMove/codex/worktrees/2c74/AI智能体软件工厂黑客松/HKT/CHANGELOG_20260924.md`

### 8.2 Round 3/4/5 方案记录

- `.../HKT/optimization-round-3-agent-runtime-plan-0927.md`
- `.../HKT/optimization-round-4-rewrite-budget-0927.md`
- `.../HKT/optimization-round-5-core-regression-0927.md`
- `.../HKT/optimization-round-2-application-contract-0927.md`
- `.../HKT/optimization-round-1-0926.md`
- `.../HKT/optimization-round-1-v2-0926.md`

### 8.3 最近 Run 与 Evolution 证据

- `.../HKT/ARC_BENCH_EVOLUTION_RUN_PAIR_HANDOFF_20260930.md`
- `.../evidence/arc-bench/evolution-run-pair-20260930.json`
- `.../HKT/ARC_BENCH_WEB_BOOKSTACK_RUN_53A102F3EE96_HANDOFF_20260930.md`
- `.../HKT/ARC_BENCH_WEB_KEEP_RUN_C68BEF1A6343_HANDOFF_20260930.md`
- `.../HKT/ARC_BENCH_LITE_KEEP_RUN_8EA6503BFA95_HANDOFF_20260930.md`
- `.../HKT/ARC_BENCH_WEB_STACKOVERFLOW_RUN_CA67B1D8EE97_HANDOFF_20260930.md`
- `.../evidence/arc-bench/web-stackoverflow-run-ca67b1d8ee97.json`
- `.../evidence/arc-bench/runs/ca67b1d8ee97/phase3-analysis.md`
- `.../evidence/arc-bench/runs/ca67b1d8ee97/phase4-handoff.json`
- `.../evidence/arc-bench/phase5-coordination.json`
- `.../evidence/arc-bench/phase4-thread-registry.json`

### 8.4 额度中断记录

- `D:/DataMove/codex/worktrees/9015/AI智能体软件工厂黑客松/docs/ARC_BENCH_RUN_E5CB3CA21874_QUOTA_INTERRUPTION_ANALYSIS.md`
- `D:/DataMove/codex/worktrees/9015/AI智能体软件工厂黑客松/docs/ARC_BENCH_RUN_06612411282D_QUOTA_INTERRUPTION_ANALYSIS.md`
- `D:/DataMove/codex/worktrees/9015/AI智能体软件工厂黑客松/docs/ARC_BENCH_RUN_FB4903ECEF12_QUOTA_INTERRUPTION_ANALYSIS.md`

记录摘要：三次额度中断均出现 timeout/proxy/repair guard 后仍继续计费；项目归纳分别报告约 `71/86`、`32/117`、`83/125`，并确认没有 OOM 作为主因。具体金额、请求数和哈希在最终 Run 前应重新从原文核验。

### 8.5 新题 requirements ZIP

- `E:/飞书下载/arcbench-hackathon-requirements (3).zip`
- `hackathon--sheet/requirements.yaml`：Workbook、Worksheet、Grid、Formula、CSV、排序/过滤、验证、Pivot 等能力。
- `hackathon--sheet/reference/`：9 张界面参考图。
- `hackathon--github/requirements.yaml`：Identity、Organization、Repository、Version Control、Issue、Pull Request、Review、Merge、权限等能力。
- `hackathon--github/reference/`：27 张界面参考图。

### 8.6 Agent 源码与运行时材料

- `D:/DataMove/codex/worktrees/aeb0/AI智能体软件工厂黑客松/arc/main.py`
- `D:/DataMove/codex/worktrees/aeb0/AI智能体软件工厂黑客松/arc/llm_proxy.py`
- `D:/DataMove/codex/worktrees/aeb0/AI智能体软件工厂黑客松/arc/guard.py`
- `D:/DataMove/codex/worktrees/aeb0/AI智能体软件工厂黑客松/arc/acceptance.py`
- `D:/DataMove/codex/worktrees/aeb0/AI智能体软件工厂黑客松/arc/metrics.py`
- `D:/DataMove/codex/worktrees/aeb0/AI智能体软件工厂黑客松/skills/arc-run-log-collector/SKILL.md`
- `D:/DataMove/codex/worktrees/aeb0/AI智能体软件工厂黑客松/docs/app-skill-dev-guide-zh.md`
- `C:/Users/dayuruozhi/.agents/skills/reliable-git-sync/SKILL.md`
- `C:/Users/dayuruozhi/.agents/skills/reliable-git-sync/references/workflow.md`

### 8.7 子智能体只读评估

- `budget_plan`：核算 36 小时/200–300 CNY 下的动态 Run 矩阵、止损线和交付排程。
- `r345_scope`：评估 Round 3/4/5 最小高收益并入范围、失败分类、checkpoint、rewrite 和 capped regression。

## 9. 协作门禁

- 本工作树只允许当前 Integrator 写入；子智能体只读审查或在隔离 worktree 工作。
- Agent 源码、官方测试、requirements ZIP、平台 Run 互相隔离；官方测试禁止修改。
- 每次修改必须记录文件、原因、测试命令、退出码和 commit SHA。
- 平台结果必须绑定 task、suite、requirements、Agent build/commit、ZIP/submission 和 Run 配置；缺字段只能作为 exploratory。
- 终版前必须完成 `git diff --check`、本地测试/静态检查、打包身份检查和工作树清洁验证。
