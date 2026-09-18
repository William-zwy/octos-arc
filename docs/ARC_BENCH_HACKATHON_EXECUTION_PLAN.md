# ARC-Bench AI Agent 黑客松完整执行计划（队内共享版）

> 版本：v1.0；更新日期：2026-09-18
>
> 当前状态：阶段 0、1、2 已完成；阶段 2.5 已准备、等待官网首个 Smoke 提交
>
> 适用范围：基于队友现有 Agent，完成当前 6 个官方赛道的基线复跑、通用优化、回归验证与最终候选交付

## 1. 一页结论

我们的正确起点不是官网历史成绩，而是已经冻结的队友原始 Agent。官网现有历史记录来自官方 Demo，只能帮助理解平台，不能代表本队 Agent 的能力。因此，Smoke、Smoke Evolution、Ticket Booking、ARC-Bench Lite 和 ARC-Bench Web 的 13 个已发布子任务都必须重新运行。

整个项目按以下优先级决策：

1. **任务完成率和功能通过率**：不能为了省 Token 或缩短时间牺牲正确性。
2. **回归可靠性与 Evolution 能力**：修改后不能破坏已通过能力，增量需求应尽量只影响必要范围。
3. **多模态输入理解质量**：快速提取图片、需求和测试中的有效约束，并允许官方缺图时安全降级。
4. **Token 消耗**：在完成率不下降的前提下减少重复上下文、重复视觉分析和无效修复。
5. **运行时间**：减少无效请求、无进展循环、重复测试和资源泄漏。
6. **维护成本与证据完整性**：优先在现有 Python 适配层做小范围、可回滚的通用增强。

第一项正式执行任务必须是 `smoke--counter`。它用于确认上传包、入口、运行时、模型配置、测试来源和计量链路都正确；门禁通过前，不启动 13 题批量基线。

## 2. 目标与成功标准

### 2.1 项目目标

在队友现有 Agent 代码上进行最小必要修改，使其能够：

- 覆盖当前已发布的所有 ARC-Bench Competition 类型；
- 对文本、需求树、测试和参考图片进行快速、清晰的联合理解；
- 针对简单、复杂、前后端、状态型和 Evolution 任务选择合适策略；
- 生成可运行代码，并通过有上限、可观测的验收与修复循环提高完成率；
- 在完成率不下降的情况下压缩 Token、运行时间和请求次数；
- 通过任务指纹、依赖影响分析和回归测试形成可验证的自进化能力。

### 2.2 成功判断

优化候选只有在相同任务快照和可比平台配置下，满足以下规则才可进入最终版本：

- 功能通过率提高：优先接受，并检查成本增长是否在可控范围内；
- 功能通过率相同：Token 更低者优先，其次比较总耗时、请求数和修复轮数；
- 功能通过率下降：默认拒绝，除非能证明是独立的平台故障且复跑已排除；
- 任何成绩都必须能追溯到 Agent 构建、任务快照、平台配置、submission ID 和 run ID；
- 不选取偶然最好的一次运行作为结论，不把官方 Demo 历史成绩混入本队基线。

本计划不预设未经实测的绝对分数目标。阶段 3 完成后，以 A0 原始基线建立各题的具体提升目标。

## 3. 已冻结的事实基线

### 3.1 官方 Competition 快照

- 快照 ID：`20260917-150121Z`
- 赛道数：6
- 当前可运行子任务：13
- 官方测试计数：566
- 清单文件：821
- 总字节数：95,423,217
- 清单校验：821 个文件的大小与 SHA-256 已全部通过
- 状态：`complete_with_official_asset_gaps`
- 清单：[`workstreams/arc-bench/official-snapshots/20260917-150121Z/manifest.json`](../workstreams/arc-bench/official-snapshots/20260917-150121Z/manifest.json)

官方快照存在 5 个确定的 404 图片引用：

- Ctrip：`index.jpg`；
- ARC-Bench Web Keep：`label_filtered_list.png`、`search_keyword.png`；
- ARC-Bench Lite Keep：`label_filtered_list.png`、`search_keyword.png`。

这些是官方资产缺口，不是本地下载失败。Agent 必须记录缺图、继续使用剩余需求/测试/图片，并避免无限重试。

### 3.2 队友原始 Agent（A0）

- 构建 ID：`teammate-baseline-20260917-ea503546`
- 原始代码 SHA：`ea503546aad31b2e3b887235e3b35cc0a8b9cfe8`
- ZIP：`evidence/arc-bench/builds/teammate-baseline-20260917-ea503546/octos-arc-bundle.zip`
- ZIP SHA-256：`812af3d15de93ce2955c6f2a0de7c6351d205b81e9fdf33f36fcd41387162ef0`
- ZIP 条目数：492
- 平台入口：ZIP 根目录的 `main.py`
- 构建清单：[`evidence/arc-bench/builds/teammate-baseline-20260917-ea503546/manifest.json`](../evidence/arc-bench/builds/teammate-baseline-20260917-ea503546/manifest.json)

A0 是不可变的对照组。后续不得覆盖、重打包后仍沿用同一个构建 ID，或把优化代码伪装成 A0。

### 3.3 数据口径说明

- 官网历史成绩来自官方 Demo，不是队友 Agent；所有任务都要重跑。
- `Competition` 与 `Playground` 是两个不同 catalog。Ticket Booking 的 Playground 历史资料是 6 个原子需求、30 个场景；当前 Competition 快照是 2 个模块、10 个测试。基线只能使用 Competition 数据。
- 官方与本地需求经过换行规范化和 YAML 语义比较后，Web、Smoke、Smoke Evolution、Ticket Booking 共 11 题语义一致；Lite Keep 与 Lite BookStack 存在真实版本差异，必须使用官方快照。
- Ctrip API 的 `module_count=133` 与 YAML 节点统计不是同一口径。官方与本地 YAML 都是 125 个 `ATOMIC`、101 个 `FOLDER`，不存在“本地缺少 8 个原子需求”的结论。执行时以官方 Competition 快照为输入，但不能用 133 直接覆盖 YAML 节点。
- Ticket Booking 的公开测试辅助默认端口已由本地旧版 3301 变为官方 3000；Lite BookStack 和 Lite Keep 的公开测试也有大量真实变更。

## 4. 当前官方任务清单与执行顺序

| 顺序 | 赛道 / 子任务 | 模块数 | 测试数 | 主要目的 |
|---:|---|---:|---:|---|
| 1 | `smoke--counter` | 1 | 1 | 平台汇合门禁、最小代码生成 |
| 2 | `smoke--dice` | 1 | 1 | 第二个简单任务，排除单题偶然性 |
| 3 | `smoke-evolution--counter` | 2 | 2 | 增量修改与回归门禁 |
| 4 | `smoke-evolution--dice` | 2 | 2 | 第二条 Evolution 路径 |
| 5 | `arc-bench-lite--keep` | 32 | 32 | 最新 Lite 输入、视觉与交互代表题 |
| 6 | `arc-bench-lite--bookstack` | 34 | 34 | 多页面结构、最新 Lite 测试代表题 |
| 7 | `ticket-booking--ticket-booking` | 2 | 10 | 前后端、认证、状态、双端口与并发 |
| 8 | `arc-bench-web--keep` | 32 | 32 | 与 Lite 同名任务的身份隔离和完整 Web 能力 |
| 9 | `arc-bench-web--bookstack` | 34 | 34 | 同名跨赛道隔离、多页面回归 |
| 10 | `arc-bench-web--stackoverflow` | 66 | 67 | 中大型状态和交互任务 |
| 11 | `arc-bench-web--prestashop` | 86 | 87 | 电商流程、状态和复杂页面 |
| 12 | `arc-bench-web--12306` | 117 | 138 | 超大型复杂流程 |
| 13 | `arc-bench-web--ctrip` | 133（API 口径） | 126 | 最大输入、多模态和上下文压力 |

`ticket-booking-evolution` 在快照时有 0 个已发布子任务，因此当前只能监测发布状态；官方发布后再补做 A0 和最终候选的同配置复跑。

采用这个顺序的原因是：先用最小任务验证链路，再验证 Evolution，然后用 Lite 任务验证最新测试和多模态，再进入状态型任务，最后逐步扩大到大型任务。这样能以较低成本尽早发现系统性问题。

## 5. 阶段状态与完整执行路径

```text
阶段 0/1/2（已完成）
        │
        ▼
阶段 2.5 平台汇合门禁（单线程）
        │
        ▼
阶段 3 A0 全量基线 ──────┐
        │                ├─ 阶段 4 滚动诊断（可并行）
        └─代表题完成──────┘
                 │
                 ▼
        阶段 5 多条优化工作流（隔离并行）
                 │
                 ▼
        阶段 6 分层回归与候选集成
                 │
                 ▼
        阶段 7 同快照全量复跑（隔离计量）
                 │
                 ▼
        阶段 8 版本选择 → 阶段 9 交付
```

### 阶段 0：范围、口径和执行方式确认——已完成

已完成事项：

- 明确 6 个官方赛道、13 个当前可运行子任务和 566 个官方测试计数；
- 确认官网历史数据是官方 Demo，不是队友 Agent 基线；
- 明确 Competition 与 Playground 不能混用；
- 确认采用官网平台执行，平台注入运行时、模型、任务和测试；
- 确认当前不需要在本地安装 Octos、Cargo，也不需要把 ARC-Bench API Key 放到本地仓库。

### 阶段 1：官方任务、测试和图片资产冻结——已完成

已完成事项：

- 冻结官方 Competition 快照；
- 下载任务、需求、公开测试和可用参考图片；
- 生成文件级 SHA-256 清单并完成校验；
- 识别 5 个官方缺图；
- 对比本地与官方需求/测试，确认 Lite 和 Ticket Booking 的真实版本差异；
- 澄清 Ctrip 133 与 125 是统计口径差异，而不是简单的新旧版本替换问题。

### 阶段 2：队友原始 Agent 冻结——已完成

已完成事项：

- 固定 A0 代码 SHA、构建 ID、ZIP 和 SHA-256；
- 确认 ZIP 根目录入口为 `main.py`；
- 保存运行配置默认值、预算、请求上限和运行时版本；
- 保证 A0 后续可重复上传、可与优化版本进行公平比较。

### 阶段 2.5：平台汇合与 Smoke 门禁——Dice 已通过，Counter 待绑定

当前门禁记录：[`preflight-smoke--counter-binding.json`](../evidence/arc-bench/builds/teammate-baseline-20260917-ea503546/preflight-smoke--counter-binding.json) 与 [`preflight-smoke--dice-binding.json`](../evidence/arc-bench/builds/teammate-baseline-20260917-ea503546/preflight-smoke--dice-binding.json)。Smoke Dice 已绑定以下平台运行：

- submission ID：`3ac91524402b`；
- run ID：`1e9d8704a273`；
- 模型：`deepseek-v4-flash`；视觉模型：`deepseek-vl-flash-vision-exp`；推理级别：`reasoning-none`；
- 观测用量：856 tokens、0.00456 CNY、39 s；测试 1 worker，Agent 验收 2 workers / 2048 MiB；
- 配置哈希：`fc3798e84d36b218b7b1d1c0626b710dba18038bc62a8a122e6a4c9594e38bc3`；
- 入口确认是 ZIP 根目录 `main.py`，测试来源确认是 `/workspace/tests`；平台原始日志未复制进仓库，仓库中不保存 API Key 值。

执行步骤：

1. 上传现有 A0 ZIP，禁止重新打包；上传后核对 ZIP SHA-256。
2. 保存平台真实模型、视觉模型、推理级别、Token/时间预算和并发配置。
3. 只启动 `smoke--counter`，暂不并发启动其他题。
4. 从日志确认平台实际执行 ZIP 根目录 `main.py`。
5. 确认运行时和模型由平台正确注入。
6. 确认公开测试来自 `/workspace/tests`，而不是 ZIP 中旧版 bundled tests。
7. 保存 submission ID、run ID、测试结果和计量信息；原始平台日志不复制进仓库，仓库证据中不保存 API Key 值。

门禁通过条件：Counter 和 Dice 两个运行都完成独立绑定，入口、测试来源和结果均有证据，且本地仓库不保存 API Key。当前 Dice 已通过；Counter 仍是 `awaiting_platform_submission`，因此整体 Smoke 门禁尚未关闭。

如果日志显示回退到 ZIP bundled tests：立即暂停批量运行，保留 A0 不变；另建 A1，仅同步官方公开测试和任务身份映射，不修改 Agent 策略。原包没有 Lite 独立测试，错误回退可能把 Lite 与 Web 同名测试混用。

### 阶段 3：A0 全量基线——待执行

门禁通过后，按第 4 节顺序运行全部 13 个任务。所有运行都使用同一 A0 构建、同一官方快照和固定平台配置。

每次运行必须记录：

- `agent_build_id`、代码 SHA、ZIP SHA-256；
- `task_snapshot_id`、competition ID、task ID；
- submission ID、run ID、开始/结束时间；
- 模型、视觉模型、推理级别、Token 上限、超时和并发策略；
- 通过测试数、总测试数、功能率、首轮通过率；
- 输入/输出/缓存 Token、费用、模型请求数；
- 总耗时、LLM 耗时、测试耗时、设计/实现/修复轮数；
- 最终状态、失败分类、平台异常和重跑原因。

原始日志和测试结果应完整保存；汇总表只保存归一化指标。平台异常的运行标记为无效样本，不能静默挑选最好成绩。

### 阶段 4：滚动诊断——与阶段 3 并行

每完成一个任务立即分析，不等待 13 题全部结束。失败至少分为以下类别：

- 输入理解或任务身份错误；
- 图片理解或官方缺图处理错误；
- 需求拆分、依赖排序或规划错误；
- 代码生成、运行时或依赖错误；
- 页面功能、状态、认证、CRUD 或导航错误；
- 测试来源、端口、进程、Playwright 或平台资源错误；
- 修复循环无进展、上下文污染或预算耗尽；
- Evolution 影响范围或回归错误。

每个失败要落到“根因、证据、通用修复候选、受影响任务、预期指标”五个字段，禁止按任务名称写一次性补丁。

当 Smoke、Smoke Evolution 和 Lite Keep 的代表性基线完成后，可以启动对应优化工作流；Ticket Booking 的状态/后端工作流必须等它自己的基线证据。

### 阶段 5：Agent 通用优化——多工作流并行

#### 5A. TaskContext 与任务身份隔离

- 用 `catalog + competition_id + task_id + snapshot_id` 形成唯一身份；
- 显式记录 requirement、tests、assets 和 template 来源；
- 禁止仅按 `keep`、`bookstack` 等短名称选择 bundled tests；
- 在日志和指标中输出最终测试目录与来源优先级。

目标：兼容 Lite/Web 同名任务和未来新增赛道，消除测试错配。

#### 5B. 多模态输入编译与缓存

- 先生成图片清单、哈希、尺寸和需求引用关系；
- 同一图片只分析一次，产出结构化视觉契约并按哈希缓存；
- 优先提取布局、文本、组件、状态、交互和视觉验收约束；
- 将视觉契约关联到需求节点，避免每轮把全部图片重复发给模型；
- 官方缺图时记录缺口，用需求与测试继续执行，不进行无限下载或视觉重试。

目标：提高视觉理解清晰度，同时降低视觉 Token 和重复耗时。

#### 5C. 需求上下文压缩

- 对 YAML、Markdown、公开测试和图片契约只索引一次；
- 每个节点只注入直接需求、祖先约束、依赖摘要和相关测试；
- 对大任务使用分层摘要和哈希缓存，不重复注入完整 125+ 节点规格；
- 保留可追溯引用，避免压缩后丢失关键约束。

目标：减少输入 Token，并使大型任务的上下文更稳定。

#### 5D. 模型、推理与预算路由

- 按任务复杂度、节点类型、图片量和失败类别选择模型/推理级别；
- 简单任务使用最少请求和低推理；复杂规划、视觉冲突或连续失败时再升级；
- 将设计、实现、验收、修复分别设定预算；
- 识别重复错误和无进展状态，触发换策略、回滚最佳版本或停止，而不是盲目加轮次。

目标：在不降低完成率的情况下减少请求、Token 和运行时间。

#### 5E. 代码生成与功能完成率

- 先生成最小可运行骨架，再按可验收纵向切片补齐功能；
- 对认证、状态持久化、CRUD、导航、端口和 API 合约建立通用模板；
- 优先使用确定性修复处理 charset、扁平 JavaScript、重复导航、端口和已知构建问题；
- 每轮修复只处理聚类后的高价值失败，并保留最佳可运行版本。

目标：提高首轮通过率和最终功能率，减少大范围重写。

#### 5F. Evolution 增量编译

- 对需求、测试、资产和生成文件建立语义指纹；
- 通过依赖图计算受影响节点，保留未受影响代码；
- 先跑受影响测试，再跑必要回归；
- 将变更前后指纹、影响范围和回归结果写入 Traceability。

目标：使自进化可验证，而不是每次全量重建。

#### 5G. 进程与资源治理

- 加强端口探测、子进程回收、超时分层和 Playwright 生命周期；
- 根据可用内存和任务规模限制 worker；
- 把平台 OOM、端口冲突和测试启动失败与业务失败分开；
- 测试失败后确保环境可被下一轮安全复用。

目标：减少非业务失败和尾部耗时。

### 阶段 6：分层验证与集成——待执行

每条优化先在最小代表集验证，再进入集成候选：

| 变更类型 | 最小验证集 | 扩展验证集 |
|---|---|---|
| TaskContext / 测试来源 | Smoke、Lite Keep | Web Keep、Lite/Web BookStack |
| 多模态与缺图降级 | Lite Keep、Lite BookStack | Web Keep、Ctrip |
| Token/上下文压缩 | Smoke、Lite Keep | 12306、Ctrip |
| Evolution 指纹 | 两个 Smoke Evolution | 后续 Ticket Booking Evolution |
| 状态、认证、双端口 | Ticket Booking | StackOverflow、PrestaShop |
| 资源与进程治理 | Ticket Booking、Web Keep | 全部大型任务 |
| 大型需求规划 | StackOverflow、PrestaShop | 12306、Ctrip |

集成时一次只引入一个有证据的变量；每次合并后至少重跑 Smoke、相关代表题和已经通过的回归集。

### 阶段 7：优化候选全量复跑——待执行

冻结候选构建 ID、代码 SHA、ZIP SHA-256 和配置哈希，使用与 A0 相同的官方快照、任务顺序和平台配置全量复跑 13 题。

用于最终对比的计量运行应隔离执行，避免共享限流、并发任务或后台实验污染 Token、费用和耗时。探索阶段可以有限并发，最终 A/B 评测应串行或使用可证明隔离的资源。

### 阶段 8：版本选择与发布门禁——待执行

按以下顺序做最终选择：

1. 比较总功能通过数和关键任务完成率；
2. 检查 Smoke、Evolution 和已通过题是否回归；
3. 在完成率相同的候选中比较 Token；
4. 再比较总耗时、请求数和修复轮数；
5. 审核平台异常、任务硬编码、测试修改、密钥泄漏和不可复现行为；
6. 对最终 ZIP 再做入口、文件集、SHA-256 和最小 Smoke 复核。

任何修改官方 Validation Test、保护路径或通过任务名硬编码答案的候选直接淘汰。

### 阶段 9：交付与赛后复盘——待执行

最终交付包括：

- 可上传的候选 ZIP 及 SHA-256；
- 构建清单、平台配置和运行绑定记录；
- 13 题 A0 与优化候选的对比表；
- 失败分类、已知限制和平台异常清单；
- Agent 架构与通用优化说明；
- Ticket Booking Evolution 发布后的补跑清单；
- 可供队友复现的上传、运行和证据归档步骤。

## 6. 代码修改边界

优先保持现有编排、验收、修复和 Traceability 流程，不做大范围重构。推荐按以下边界修改：

| 位置 | 最小改动方向 |
|---|---|
| `arc/main.py` | 接入 TaskContext、策略路由、预算与运行绑定，不重写主流程 |
| `arc/requirement_order.py` | 增加任务版本身份、语义指纹、依赖切片和 Evolution 影响分析 |
| `arc/acceptance.py` | 记录测试来源，增强端口/进程/超时治理和失败分类 |
| `arc/codegen.py` | 扩展有证据的确定性修复，避免把任务特例写进通用路径 |
| `arc/llm_proxy.py` | 统一模型路由、Token 预算、缓存命中和请求级计量 |
| `arc/metrics.py`、`arc/arcbench_agent_runtime/` | 补齐 build/snapshot/run/config 绑定与阶段级指标 |
| 可选新增小模块 | 只有现有职责无法容纳时，新增 `task_context` 或 `vision_context`；保持接口窄小 |
| `arc/pack.sh` | 仅处理确定的打包与官方公开输入同步问题，不改变 Agent 策略 |

除非平台证据证明 Python 适配层无法解决问题，否则不修改 `crates/` Rust 内核。任何结构性改动都必须先回答：服务哪个真实失败、改善哪个用户可见行为、由哪个测试证明。

## 7. 并线方式与团队分工

### 7.1 可以并行的工作

- 阶段 3 的官网运行与阶段 4 的已完成任务诊断可以流水并行；
- 代表题有基线后，TaskContext、多模态、上下文压缩、Evolution、资源治理可在不同工作树并行；
- 运行证据整理、失败归类和代码实现可以由不同成员并行；
- Ticket Booking Evolution 发布监测可以独立进行，不阻塞当前 13 题。

### 7.2 必须串行的门禁

- 阶段 2.5 必须由一个平台操作人完成，不能多人同时改 submission 配置；
- Smoke 门禁未通过前不能批量启动基线；
- 同一工作树同一时刻只能有一个写入者；
- 多条优化工作流必须先各自验证，再由单一集成人串行合并；
- 最终 A/B 计量必须隔离，不能与其他消耗同一限额的任务并发。

### 7.3 建议角色

| 角色 | 主要责任 |
|---|---|
| 负责人 / 发布经理 | 决定 go/no-go、锁定配置、控制范围和最终候选 |
| 平台运行负责人 | 上传、启动任务、回填绑定、保存原始日志与 ID |
| 输入与数据负责人 | 维护官方快照、任务差异、图片缺口和发布监测 |
| Agent 实现负责人 | 根据真实失败实施通用、小范围代码修改 |
| 验证与指标负责人 | 失败分类、回归矩阵、A/B 对比和结果审计 |

人数较少时可以合并角色，但“平台运行”和“同一工作树代码写入”在任一时刻仍各自只能有一个负责人。

## 8. Git 与产物管理策略

- 当前证据分支 `codex/arc-bench-official-snapshot-20260917` 包含约 95 MB 官方快照和 A0 证据，仅用于本地证据保存，当前不推送远程。
- 优化代码不要直接从证据分支继续开发。应从 A0 代码 SHA `ea503546...`，或经比较确认安全的最新 `origin/main` 建立独立分支/工作树。
- 每条优化工作流使用独立工作树和单一写入者；集成人只合并已验证提交。
- 不使用 `git reset --hard`、强制推送或自动丢弃未知改动。
- 如果后续需要远程共享大快照，优先提交 manifest、下载/校验脚本和报告；原始资产使用 Git LFS 或外部只读归档，避免把 95 MB 证据历史直接混入最终代码分支。
- 当前用户要求暂不推送远程；本计划及其本地提交不代表远程已经同步。

建议的运行证据目录：

```text
evidence/arc-bench/runs/<agent-build-id>/<task-id>/<run-id>/
├── binding.json
├── platform-config.json
├── metrics.json
├── test-results.json
├── raw-log.txt
└── failure-analysis.md
```

所有文件禁止包含 API Key、访问令牌或其他密钥值。

## 9. 主要风险与应对

| 风险 | 影响 | 应对 |
|---|---|---|
| 平台回退到 ZIP bundled tests | Lite/Web 测试错配，基线失真 | 阶段 2.5 强制核验 `/workspace/tests`；否则暂停并建 A1 |
| 官方图片 404 | 多模态流程卡死或错误归因 | 缺图降级、记录来源、禁止无限重试 |
| 官网模型配置未冻结 | A/B 不可比较 | 每次保存实际模型、推理、预算和配置哈希 |
| 共享限流或并发污染 | Token/耗时数据失真 | 探索有限并发，最终评测隔离串行 |
| 按题硬编码或过拟合公开测试 | 隐藏测试和新题失效 | 只接受通用策略，跨代表题回归 |
| 状态、端口、进程或 OOM | 被误判为生成能力问题 | 独立失败分类，资源治理和环境复位 |
| 官方任务继续变化 | 输入与结果不可复现 | 每轮绑定 snapshot ID；新版本另建快照 |
| Ticket Booking Evolution 尚未发布 | 自进化覆盖不完整 | 先验证 Smoke Evolution，发布后补跑 |
| 证据分支过大 | 推送和评审困难 | 代码分支与证据分支隔离；大资产用 LFS/归档 |
| 官网历史数据归因错误 | 错误跳过任务或错误优化 | 明确标注 Demo/A0/候选三类来源 |
| 平台偶发故障 | 误判回归或挑选最好结果 | 标记无效样本，保留原始日志，按规则复跑 |

## 10. Go / No-Go 门禁

| 门禁 | 状态 | 通过条件 |
|---|---|---|
| G0 范围与口径 | 已通过 | 6 赛道、13 可运行任务、数据来源明确 |
| G1 官方快照 | 已通过 | manifest、文件哈希、差异和缺图已核验 |
| G2 A0 冻结 | 已通过 | 代码、ZIP、配置与 SHA-256 已固定 |
| G2.5 平台汇合 | 待通过 | Smoke Counter 的入口、运行时、测试来源和运行绑定有证据 |
| G3 Smoke 基线 | 待通过 | Counter、Dice 正常运行，指标可归因 |
| G4 代表题基线 | 待通过 | Smoke Evolution、Lite Keep；状态流另含 Ticket Booking |
| G5 A0 全量基线 | 待通过 | 13 题全部有有效运行记录与诊断 |
| G6 优化候选 | 待通过 | 最小验证集和相关回归均通过 |
| G7 全量 A/B | 待通过 | 同快照、同配置完成 13 题可比复跑 |
| G8 最终交付 | 待通过 | 候选 ZIP、SHA、报告、限制和复现步骤齐全 |

## 11. 立即执行清单

1. 打开阶段 2.5 绑定记录，确认 A0 ZIP 路径与 SHA-256。
2. 上传现有 A0 ZIP，不重新打包。
3. 固定并记录官网真实模型、视觉模型、推理级别、Token/时间预算和并发策略。
4. 启动 `smoke--counter`。
5. 核验根目录 `main.py`、平台运行时、`/workspace/tests` 和日志无密钥。
6. 回填 submission ID、run ID、平台配置与配置哈希。
7. 做 G2.5 go/no-go：通过则运行 `smoke--dice`；失败则先修复链路，禁止批量运行。
8. 按既定顺序形成 13 题 A0 基线，同时滚动归类失败。
9. 基于真实失败启动隔离优化工作流，不提前做大重构。

## 12. 官方入口

- 比赛官网：<https://create.gosim.org/factory26/>
- ARC-Bench 平台：<https://arc-bench.com/>
- ARC-Bench Web：<https://arc-bench.com/competitions/arc-bench-web>
- Smoke Evolution：<https://arc-bench.com/competitions/smoke-evolution>
- Smoke：<https://arc-bench.com/competitions/smoke>
- Ticket Booking Evolution：<https://arc-bench.com/competitions/ticket-booking-evolution>
- Ticket Booking：<https://arc-bench.com/competitions/ticket-booking>
- ARC-Bench Lite：<https://arc-bench.com/competitions/arc-bench-lite>
- API 用量：<https://meter.arc-bench.com/user>
- 课程仓库：<https://github.com/code-philia/agentic-software-engineering-hackathon>

## 13. 文档维护规则

- 官方任务、测试、图片或计分规则变化时，先建立新快照，再更新本计划；不覆盖旧快照结论。
- 每通过一个门禁，更新状态、证据链接、负责人和日期。
- Agent 构建发生任何字节变化，都必须使用新的 build ID 和 ZIP SHA-256。
- 计划、项目记忆和运行台账必须保持一致；聊天中的临时判断不代替仓库内证据。
