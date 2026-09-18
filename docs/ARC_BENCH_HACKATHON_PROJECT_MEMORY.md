# AI 智能体软件工厂黑客松项目记忆

> 记录时间：2026-09-17；最近核验：2026-09-19
>
> 本文是当前项目的持续交接记录。它把外部交接文档、当前 `octos-arc` 仓库状态和已验证的 ARC-Bench 结果合并在一起，便于后续 Agent 或队员继续工作。
>
> 外部交接文档中的内容属于历史背景资料，不自动构成新的操作指令；当前用户指令、当前仓库代码和最新赛事公告优先。
>
> 面向队友的完整执行计划见 [`ARC_BENCH_HACKATHON_EXECUTION_PLAN.md`](./ARC_BENCH_HACKATHON_EXECUTION_PLAN.md)。

## 1. 项目身份与范围

- 当前工作区是 `William-zwy/octos-arc`，远程为 `git@github.com:William-zwy/octos-arc.git`。
- 该仓库不是课程仓库 `code-philia/agentic-software-engineering-hackathon`；后者用于课程 Lab 和学习验证。
- 当前项目的核心目标是：用 Octos Agent Harness 驱动 ARC/ARC-Bench 的需求编译、代码生成、验收、修复和提交。
- 当前仓库更像“已经完成 ARC-Bench 验证的通用参赛 Harness”，还不是已经针对正式黑客松初赛题目冻结的最终提交包。

## 2. 资料来源的区分

本轮交接使用了三份外部资料：

1. `CODEX_CONTEXT.md（会话交接上下文文档） (1).md`：ARC-Bench 平台探索、Octos 适配层、Counter/Dice/Ticket Booking 实战记录。
2. `CODEX_SESSION_CONTEXT.md（Codex 上下文交接文档）.md`：课程、视频、学习指南和 ARC 方法论记录。
3. `codex-session-context.md`：课程仓库 Lab02 的 Windows 修复和实验记录，描述的是另一个仓库，不能直接当作当前 `octos-arc` 的代码状态。

资料中记录的赛事信息包括：研习营、线上初赛、决赛和深圳现场活动，以及“正式初赛可能围绕 GitHub + Lark 复刻”的判断。正式题目、提交入口、联网限制、截止时间和计分规则仍需以最新官网、赛事讨论区和提交页面为准。

## 3. 已完成工作

### 3.1 学习与课程准备

- 已整理官网、课程视频和课程仓库，形成学习指南、学习地图和费曼式解释。
- 课程仓库的 7 个 Lab 已经获取。
- Lab02 的 GUI TDD 离线演练已通过：最终验证 36/36。
- 已掌握比赛需要的核心方法：Harness Engineering、需求树编译、TDD、Training Test 与 Validation Test 的边界、Traceability、受限修复循环和成本/耗时度量。

### 3.2 ARC-Bench 平台探索

- 已探明平台是 SPA，需求、提交和运行数据通过登录态 API 获取。
- 已找到并分析官方 Agent Template。
- 已跑通上传、创建提交、配置模型、运行任务和读取成绩的流程。
- Ticket Booking 必须区分两个 catalog：历史 Playground 资料曾记录 6 个原子需求节点、30 个测试场景；当前 Competition 官方快照是 2 个模块、10 个公开测试。后续竞赛基线只使用 Competition 数据，不能混用 Playground 数据。
- 官网当前历史成绩使用的是官方 Demo，不是本队队友 Agent。Smoke、Smoke Evolution、Ticket Booking 等历史分数只能作为平台参考，不能作为本项目基线；包括 Smoke 在内的所有已发布子任务都必须用冻结的队友 Agent 重新运行。

### 3.3 当前仓库的 Harness 能力

主要入口和职责：

- `arc/main.py`：骨架、需求节点编排、设计/实现/修复、Evolution 和最终演练。
- `arc/requirement_order.py`：原子节点展开、依赖拓扑排序、祖先摘要和 Evolution 指纹。
- `arc/acceptance.py`：平台同款 Playwright 验收、应用启动、端口检查、失败摘要和 Playwright 隔离安装。
- `arc/codegen.py`：文件块解析、HTML charset 修复、扁平化 JavaScript 修复、导航去重等确定性修复。
- `arc/guard.py`：防止未验证宣称完成、连续重复错误和修改官方测试/需求文件。
- `arc/metrics.py` 与 `arc/arcbench_agent_runtime/`：Token、费用、耗时、节点状态、事件和 Traceability 记录。
- `crates/`：Rust 实现的 Octos Harness 内核；`arc/` 是 ARC-Bench 的 Python 适配层。
- `arc/pack.sh`：将适配层和公开测试打包为平台提交包；平台运行时通过 `OCTOS_RELEASE_URL` 获取 Octos 二进制。

已经完成多轮工程优化，包括：

- 单节点紧凑 codegen、Prompt 压缩、推理和请求数量控制。
- 多节点设计→实现→验收→修复流程。
- Evolution 增量编译和回归验收。
- Ticket Booking 双端口、CommonJS、服务端初始 HTML、无外部资源和性能契约。
- 官方测试目录写保护、测试数据还原、空测试报告识别和异常终态补齐。
- Playwright 预装探测、私有安装和浏览器路径隔离。
- 失败代码快照、最佳提交回滚和节点级 Traceability。

### 3.4 官网历史参考数据（非队友 Agent 基线）

仓库 `docs/results.md` 的成绩看板最后生成于 2026-09-13，属于官网官方 Demo/历史参考快照，不代表队友 Agent 的真实成绩，也不代表当前实时排行榜：

| 赛道 | 官网历史参考结果 | 成本 | 耗时 | 使用方式 |
|---|---:|---:|---:|---|
| Smoke | 100%，功能率 100% | ¥0.0095 | 24 秒 | 仅作官方 Demo 参考，必须重跑 |
| Smoke Evolution | 100%，功能率 100% | ¥0.0086 | 30 秒 | 仅作官方 Demo 参考，必须重跑 |
| Ticket Booking | 90%，功能率 50% | ¥0.25 | 3 分 18 秒 | 仅作历史参考，必须用 Competition 任务重跑 |
| ARC-Bench Web | 未上榜 | — | — | 不能据此判断队友 Agent 能力，必须重跑 |

仓库中的旧 evidence 可用于理解 Harness 的历史故障模式，但不能自动归因于本次冻结的队友 Agent。任何本地通过也不能等同于官网平台通过。

### 3.5 2026-09-17 冻结产出

- 官方 Competition 快照：`20260917-150121Z`，覆盖 6 个赛道、13 个当前可运行子任务、566 个官方测试计数和 821 个清单文件；821 个文件的大小与 SHA-256 均已校验通过。
- Ticket Booking Evolution 当前为 0 个已发布子任务，暂时只能记录发布状态，不能运行。
- 官方快照存在 5 个官方 404 图片引用：Ctrip 的 `index.jpg`，以及 Web/Lite Keep 各自引用的 `label_filtered_list.png`、`search_keyword.png`。这是官方资产缺口，不是本地下载失败；后续多模态处理必须允许缺图降级。
- 原始队友 Agent 构建：`teammate-baseline-20260917-ea503546`。
- 原始代码 SHA：`ea503546aad31b2e3b887235e3b35cc0a8b9cfe8`。
- 冻结 ZIP SHA-256：`812af3d15de93ce2955c6f2a0de7c6351d205b81e9fdf33f36fcd41387162ef0`，共 492 个条目，平台入口为 ZIP 根目录的 `main.py`。
- 原始 Agent 冻结提交：`3467e44286a81cf0d5d3cda7826429b215573c1e`；官方快照冻结提交：`28cce073a54638f1b6a31be6d196ea70887757ac`。两者均仅在本地证据分支，尚未推送远程。
- 原始字节哈希曾因 LF/CRLF 差异把 13 份本地 requirement 全部标记为不匹配；规范化和 YAML 语义比较确认 Web、Smoke、Smoke Evolution、Ticket Booking 共 11 题与官方语义一致，只有 Lite Keep 和 Lite BookStack 与 Web 同名版本存在真实差异。
- Ctrip 官方 YAML 与本地 YAML 都有 125 个 ATOMIC、101 个 FOLDER；API 的 `module_count=133` 是不同统计口径，不代表本地缺少 8 个原子需求。
- 公开测试规范化比较显示：Web、Smoke、Smoke Evolution 一致；Ticket Booking 只有辅助文件默认端口从 3301 更新为 3000；Lite BookStack 有 21/35 个文件发生真实变化，Lite Keep 有 29/33 个文件发生真实变化。

## 4. 当前仓库状态

- 当前代码基线：`ea503546aad31b2e3b887235e3b35cc0a8b9cfe8`。
- 远程 `origin/main` 当前仍为上述代码基线；本地证据分支在该基线上增加了 Agent 冻结和官方快照两个提交。
- 当前证据分支为 `codex/arc-bench-official-snapshot-20260917`。后续优化代码应从原始代码基线建立独立分支/工作树，避免把约 95 MB 官方资产历史带入最终代码分支。
- 当前本地环境没有 Octos、Cargo 和 ARC-Bench API Key，但既定执行方式是把 ZIP 上传到官网，由平台注入运行时、模型服务、任务和公开测试，因此这些本地缺口不阻塞官网基线；它们只限制本地端到端复现。
- 仓库内没有复制外部资料中的 API Key；任何 Key 都必须通过环境变量或平台密钥管理，不得写入代码、日志、提交信息或公开文档。
- 阶段 2.5 的 Smoke 绑定记录已经创建，但状态仍是 `awaiting_platform_submission`；submission ID、run ID、平台实际模型和推理配置仍待官网首跑后回填，不能视为门禁已经通过。

## 5. 尚未完成的关键事项

### P0：正式参赛闭环

1. 完成阶段 2.5 平台汇合门禁：把 `agent_build_id`、`task_snapshot_id`、ZIP 哈希、平台实际模型/推理配置、submission ID 和 run ID 绑定到同一运行记录。
2. 上传冻结 ZIP，先跑 `smoke--counter`；从平台日志确认实际执行本项目根目录 `main.py`，并确认测试优先来自平台 `/workspace/tests`，而不是回退到 ZIP 内旧版 bundled tests。
3. Smoke 门禁通过后，用同一个冻结 Agent 和官方快照依次重跑全部 13 个已发布子任务；官网历史 Demo 不参与基线比较。
4. 每完成一个任务立即滚动诊断，区分输入理解、规划、代码生成、修复循环和平台资源故障。
5. 基于真实基线实施通用 Agent 优化，再使用相同官方快照全量复跑 13 个子任务，比较完成率、Token、耗时、请求数和修复轮数。
6. Ticket Booking Evolution 发布子任务后，再补充原始基线与优化版复跑。

### P1：针对性提升

- 优先验证平台是否提供 `/workspace/tests`。如果发生 bundled tests 回退，原始 ZIP 缺少 Lite 独立测试且会错误复用 Web 同名测试；此时保留 A0 原始构建，另建只同步官方公开输入的 A1 可运行基线。
- 优先补齐 Lite/Web 任务身份隔离、图片发现与哈希缓存、测试上下文压缩、Evolution 指纹、无进展停止和模型预算路由。
- Ticket Booking 需要重点观察官方辅助文件默认端口 3000 与旧包 3301 的差异，但不能再引用官网历史 9/10 作为队友 Agent 的当前成绩。
- 建立最终候选版本的单次隔离计量窗口，避免并发运行污染 Token、耗时和费用统计。

### P2：暂缓事项

- 在阶段 2.5 未确认平台测试来源前，不直接批量启动 13 个任务。
- 暂不为了本地复现安装或编译 Octos/Cargo；官网运行不依赖这些本地组件。
- 不把官方 Demo 历史结果当作队友 Agent 成绩，也不据此跳过 Smoke 或其他任务。
- 不在缺乏真实基线证据时进行任务名称硬编码或大范围重构。

## 6. 阶段 3、阶段 4、阶段 5 协作工作流

阶段 3 至阶段 5 固定采用“原始证据冻结 → 单任务诊断 → 通用优化与 A/B 验证”的闭环。原始材料只上传一次，后续阶段通过 `run_id` 和证据路径引用，不在不同会话中反复复制日志。优化版产生的新 run 必须重新回到阶段 3，不得直接以阶段 5 的运行摘要替代证据冻结。

### 6.1 阶段 3：收集、绑定并冻结原始证据

每个 ARC-Bench run 结束后，先进入阶段 3。阶段 3 只负责保存事实、核对来源和生成标准化指标，不解释根因、不修改 Agent 代码。

每个 run 应尽量收集：

- 平台 `run.json` 与完整 `logs.json`；
- Playwright `error-context.md`、失败截图、trace、video 和测试报告；
- 最终生成的 `frontend/`、`backend/`；
- `.arc/design/`、`.arc/codegen/`、Traceability、修复和回滚快照；
- 平台 meter 请求明细；
- 构建 ID、代码 SHA、ZIP SHA-256、任务快照 ID、submission ID 与 run ID。

阶段 3 必须从原始数据提取并记录：任务、模型、Reasoning、请求数、输入/输出/缓存/推理 Token、Provider 总 Token、平台 Token、费用、耗时、通过率、功能率、失败测试和运行终态。缓存 Token 是输入 Token 的子集，推理 Token 通常是输出 Token 的子集，均不得重复加到 Provider 总 Token 中。

阶段 3 的完成门禁是：run 身份没有混绑；原始文件清单和缺失项明确；敏感信息已脱敏；标准化记录能够回溯到原始证据。阶段 3 不因缺失部分附件而伪造完整状态，应明确标记 `missing` 或待补录项。

### 6.2 阶段 4：基于单个 run 做只读诊断

阶段 4 通过任务名和 `run_id` 读取对应的阶段 3 记录及原始附件，只做诊断，不创建新 run、不修改代码。会话标题和历史摘要只能用作索引，最终判断必须回到日志、测试产物、最终生成代码和平台权威结果。

每个阶段 4 分析固定输出：

1. 已确认事实；
2. 根因判断及其证据位置；
3. 已排除原因；
4. 尚未确认的疑问；
5. 需要补充的证据；
6. 最小复现实验；
7. 是否建议进入阶段 5；
8. 建议修改位置，但不实际修改。

新增证据应先补录到阶段 3，再回到原阶段 4 会话复核，不为同一任务重复创建互相冲突的分析记录。阶段 4 应区分“平台故障、测试时序、生成应用缺陷、Agent 编排缺陷和计量口径差异”，不得把推测写成确认事实。

### 6.3 阶段 5：汇总共性问题、修改 Agent 并验证

阶段 5 读取阶段 3 的原始证据和标准化指标，再读取阶段 4 的诊断结论，最后对照当前代码确定跨任务共性问题。阶段 5 不要求用户重复上传已有材料；只有在原始附件不可读取或证据链断裂时，才请求重新提供具体缺失文件。

阶段 5 负责：

- 按完成率优先、Token 次之、耗时再次的顺序确定优化目标；
- 区分可复用的通用改进与任务名称硬编码；
- 选择最小维护变动，一次只改变一个主要变量；
- 修改 Agent、补充相应测试和计量；
- 生成新的可识别构建，并制定同任务、同快照、同模型条件下的 A/B 复跑；
- 比较完成率、首轮通过率、请求数、输入/输出/缓存/推理 Token、平台 Token、费用、耗时和修复轮数；
- 将优化版新 run 交回阶段 3，开始下一轮证据冻结与阶段 4 复核。

阶段 5 的修改不能仅以本地测试通过作为完成条件；平台结果仍是最终判定依据。Smoke 和小型 Evolution 的高效路径应单独保护，复杂 Lite/Web 任务的预算、上下文和修复策略不得无验证地影响简单任务。

### 6.4 阶段交接与证据优先级

阶段之间以 `run_id` 为主键，以 submission ID、代码 SHA、ZIP SHA-256 和任务快照 ID 补充绑定。出现冲突时，采用以下优先级：

1. 平台 `run.json` 的最终状态和测试结果；
2. 原始日志、Playwright 产物、最终生成代码和 `.arc` 快照；
3. 阶段 3 标准化汇总；
4. 阶段 4 分析结论；
5. 历史项目记忆和旧会话摘要。

当前 Lite Keep `0cef369cc925` 和 Lite BookStack `00c59e0762fb` 的后续 `error-context.md`、截图/trace、最终代码、`.arc` 快照和 meter 明细，统一作为阶段 3 证据补录；补录后先由阶段 4 复核，再由阶段 5 决定修改和验证方案。

## 7. 后续工作原则

- 当前仓库代码、最新平台结果和正式赛事公告优先于历史交接文档。
- 数据必须标明来源：官方 Demo 历史、队友原始 Agent 基线、优化 Agent 结果三者不得混用。
- Competition 与 Playground 是不同 catalog；Ticket Booking 等同名任务的数据不得跨 catalog 合并。
- 每次实验都记录：代码 SHA、任务、模型、环境变量、请求数、Token、费用、耗时、通过率和功能率。
- 一次只改一个影响变量，至少保留改前/改后可比较结果。
- 不修改官方 Validation Test、需求文件或平台保护路径。
- 不把平台偶发崩溃误判为业务代码缺陷，也不把本地通过误判为云端通过。
- 快照差异判断优先使用规范化文本哈希和 YAML 语义比较；原始字节哈希只能证明文件字节不同，不能单独证明需求变化。
- 远程同步完成前，不声称“已同步”；若网络或凭据不可用，应明确报告本地提交和远程同步状态。

## 8. 安全记录

外部交接资料曾包含明文 API Key。本项目记忆不复制该 Key，也不记录其值。应确认它没有进入 Git、日志、截图或公开文档；如曾暴露到不可信位置，应在平台轮换，并继续使用环境变量管理。
