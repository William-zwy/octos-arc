# ARC-Bench 阶段 5 跨 Run 问题与优化决策台账

> 版本：v1.24；建立日期：2026-09-19；状态：V3 已冻结；用户明确确认 BookStack `cca008377368` 与 Keep `bf5e742c15a4` 是冻结 V3 返回的 Run ID。该版本归属作为用户 provenance 登记；两份 manifest 同时把原始上传文件名记为 `octos-arc-bundle-13173bb50e55.zip`，与台账中冻结 V3 的 `d2fe4dbc…` / `FC83EA…` 本地身份存在未闭合冲突，平台又缺少 ZIP→build/code 与 task snapshot 绑定，因此不能升级为源码级身份、业务验收、平台收益或严格 A/B。`cca008377368` 仍只确认 `P5-012` 的 401→exit 2 运行事实；`bf5e742c15a4` 仍因阶段 4 结果身份不完整而隔离。`P5-005` 的 V4.1 build provenance 切片已由 Agent 实现会话本地实现、提交并打包，精确产物已转交离线受控复现；在三项复现和平台外部绑定完成前，上传建议仍为 `NO-GO`。
>
> 范围：阶段 3 归一化证据、阶段 4 单 Run 诊断进入阶段 5 后的跨 Run 归并、方案选择、实现盘点与 A/B 决策。本文件不是原始日志、阶段 3 manifest 或阶段 4 分析的替代品。
>
> 授权历史与当前边界：用户此前报告已人工上传冻结 V3；随后明确授权创建 V3.1/V4 修复切片，并要求交付下一次平台测试 ZIP。该授权覆盖本地实现、验证、打包和向用户交付文件，不授权本工作区代为上传或启动平台 Run；本轮未改官方测试、未推送远程、未上传、未创建平台 Run。

> 会话分工：本文件是唯一跨 Run 决策记录；新会话职责、复现回交、指标门禁和条件转派见[阶段 5 多会话工作流](./ARC_BENCH_HACKATHON_PHASE5_COLLABORATION_WORKFLOW.md)。2026-09-20 新建会话的精简入口见[上下文交接](./ARC_BENCH_HACKATHON_PHASE5_CONTEXT_HANDOFF.md)。
>
> 自 2026-09-21 起，用户将本会话固定为**决策台账/信息收敛角色**：允许读取证据、作出裁决并维护文档和协同元数据；禁止在本会话直接修改 Agent、业务代码、测试代码或打包实现。凡需代码写入，一律形成可核验 handoff 后转交“项目阶段5｜Agent 实现”（Thread `01a0bd66-75bd-7801-97fc-b3d1e136c112`），再由本会话接收提交 SHA、验证结果和产物身份。

## 1. 决策原则与证据口径

1. 决策顺序：功能完成率与回归可靠性优先；通过率相同才优先比较 Token，再比较耗时、请求数及修复轮数。遵循[完整执行计划](./ARC_BENCH_HACKATHON_EXECUTION_PLAN.md)。
2. 先按**失败机制**归并，再比较表面症状。同为 Playwright 十秒超时，不等于同一根因；同一 Run 内两个失败，也不自动等于已经跨 Run 验证的共性问题。
3. 证据等级：`confirmed` 表示原始结构化证据、生成代码或当前 Agent 代码直接支持；`strong_candidate` 表示多项证据一致但缺运行时链路确认；`unknown` 表示不能判断。机制的确认程度与其跨任务适用程度分别记录。
4. 来源优先级：平台 `run.json` 最终结果；原始日志、Playwright 产物、最终生成代码及 `.arc` 快照；阶段 3 manifest；阶段 4 分析；旧项目记忆。冲突须保留，不用推测填平。
5. 状态词严格区分：`现有`、`拟议`、`待证据`、`实施中`、`本地已验证`、`平台已验证`、`已回退`、`决定不改`。`本地已验证`须有实际代码、完整提交 SHA 和测试；`平台已验证`还须有构建 ID、上传 ZIP SHA、新 Run 及同条件 A/B。
6. 每次改动前重新核对当前代码与工作树；台账只是索引，不以文档中旧的“现有能力”替代代码检查。每个实现切片必须回答：服务哪个真实失败、改善哪个用户可见行为、由哪个测试证明，以及是否与已有机制重复或冲突。
7. 不复制原始日志、完整 snapshots 或密钥；按 `run_id` 引用阶段 3 manifest。优化版新 Run 必须先回阶段 3 冻结，再回阶段 4 诊断，最后更新本台账。

## 2. 本版证据范围与基线

本版基线表列出四个历史 Lite Run、一个 Web BookStack Run 和一个 ticket-booking Run；其余已登记 Run 在后续单独章节保留。Lite Run 现按用户提供的 provenance 暂标为 A0/V1/V2/V3：A0=`ea503546`、V1=`c53c333d`、V2=`dddc9431`；冻结 V3 的本地身份仍为 `d2fe4dbc…` / `FC83EA…`，用户现明确将 BookStack `cca008377368` 与 Keep `bf5e742c15a4` 归入其 Run 分组。本地冻结 ZIP 的 `main.py`/`acceptance.py` 规范化 Git blob 已由实现线程核对为与对应提交精确一致，本台账复核了完整提交和 ZIP SHA；但两个新 Run 的 manifest 原始文件名均为 `octos-arc-bundle-13173bb50e55.zip`，且仍缺 `task_snapshot_id` 及平台独立的 build/code/ZIP 绑定，故版本标签可用于组织证据，**不能单独证明平台执行的具体构建、任务快照和配置可比**。各 Run 的 `template.zip` 是生成应用快照，不是上传的 Agent ZIP。

待纳入队列：[Web Keep `4b792b72d7dd`](../evidence/arc-bench/runs/4b792b72d7dd/manifest.json) 已有阶段 3 manifest（平台 `30/32`），但阶段 4 会话映射处于 `quarantined`，本台账尚未收到可复核的机制结论；先解决会话身份与结果回读，不自动转派，也不把它与 Lite Keep 的同名任务或本切片缺路由机制合并。

新待纳入队列：Lite Keep V2 [`737b56972d5a`](../evidence/arc-bench/runs/737b56972d5a/manifest.json) 已有阶段 4 [核验结果](../evidence/arc-bench/runs/737b56972d5a/phase4-result.json)，平台 `30/32`；用户 provenance 将其映射到 `dddc9431`/ZIP `984D818A…`，平台绑定仍待独立确认。它不能直接与旧 Run 计算阶段 5 A/B；当前仅按已确认的 Run-local 机制登记，不据版本标签自动开工。

新条件接收队列：Lite BookStack V2 [`4ef2cf139806`](../evidence/arc-bench/runs/4ef2cf139806/manifest.json) 的阶段 4 结果已核验，平台 `31/34`，失败 `REQ-2.2`、`REQ-6.3.1`、`REQ-9.1`。用户 provenance 将其映射到 `dddc9431`/ZIP `984D818A…`，而 `5669f7d1777c` 映射为 V1；这修正了临时版本标签，但不替代平台构建绑定。三项具体运行时机制仍未闭合，当前保持 `needs_repro`，不直接并入 `P5-009`。

新成功基线：ticket-booking [`1aac5ece078e`](../evidence/arc-bench/runs/1aac5ece078e/manifest.json) 的阶段 4 结果已核验，平台与内部验收均为 `10/10`、`PASSED`、score `100.0`；无失败链、无 P5 问题、无需复现。它可作为后续 ticket-booking 比较的成功基线，但缺少 `agent_build_id`、`code_sha`、`task_snapshot_id` 和 ZIP-to-build 绑定，不能单独证明代码包身份或阶段五 A/B 可比性。

新生成门禁 intake：Keep Lite [`ff12a7ff45f8`](../evidence/arc-bench/runs/ff12a7ff45f8/manifest.json) 的平台结果为 `FAILED`、score `0`、`0/0`，但应用服务与 Playwright 均未启动。该 Run 只证明认证失败观察、skeleton 无产出和模板前置拒绝，不能判断 Keep 业务功能，也不进入业务完成率或版本 A/B 表；详见 `P5-012` 与第 17 节。

新包形状门禁 intake：BookStack Lite [`d4acec5dbbdf`](../evidence/arc-bench/runs/d4acec5dbbdf/manifest.json) 的平台结果为 `FAILED`、score `0`、`0/0`，runner 在业务测试前因最终 ZIP 缺少 `frontend/` 与 `backend/` 拒绝模板；归档清单还显示 `main.py` 与 `tests/` 均不存在。该 Run 仅用于追查 workspace/staging 到最终 ZIP 的生成与打包链路，必须与其他 BookStack Run 分开，不进入业务完成率、失败机制归并或版本 A/B 表；详见 `P5-013` 与第 18 节。

新 fail-fast 平台观察：BookStack Lite [`cca008377368`](../evidence/arc-bench/runs/cca008377368/manifest.json) 是 submission `0b90e43b07b7` 下的独立 Run，用户明确归入冻结 V3。平台执行 `/workspace/submission/main.py` 后遇到 HTTP `401` 永久认证失败并以 exit `2` 在生成前终止，最终 `0/0`；该行为与后续 V3.1 fail-fast 候选相符，但这只形成版本归属冲突，不能反向证明平台运行了 V3.1/V4。上传文件名只能提供候选来源线索，缺少平台 ZIP SHA/build/code 绑定，不能升级为已验证的构建归因。空模板是认证中止后的下游状态，不作为 `P5-013` 的独立根因；详见第 21 节。

隔离 intake：Keep Lite [`bf5e742c15a4`](../evidence/arc-bench/runs/bf5e742c15a4/manifest.json) 同样由用户明确归入冻结 V3，但在阶段 4 连续两次返回空回合，随后才迟到写入 ACK/result。ACK 身份可匹配，但 `phase4-result.json` 的 `manifest_sha256` 为空，约定的 JSON 完成标记字段也未通过校验；Markdown 标记不能替代结构化身份验证。注册表现为 `quarantined / late_result_incomplete_unverified`，因此 V3 分组归属不改变其证据状态：本台账不读取诊断结论、不创建 P5 问题、不判断是否复现、不派 Agent 实现；下一步只允许修复并复核既有阶段 4 会话，不 fork 补偿性重复会话。

| Run 与原始证据索引 | 平台最终结果 / 内部验收 | 请求与计量 | 当前用途 |
|---|---|---|---|
| Keep Lite A0 [`0cef369cc925`](../evidence/arc-bench/runs/0cef369cc925/manifest.json) | 平台 `31/32`、FAILED，`REQ-2.5.4 Unarchive` 十秒超时；内部 round 0 `31/32`（失败 `REQ-2.8.2`）→ round 1 `32/32` | 1,004 次；输入 24,772,611、输出 660,754、缓存命中 22,496,000、推理 436,764、Provider total 25,433,365、平台 Token 58,278,570；13,576 秒；¥31.453807 | 功能可靠性疑点及成本基线；A0 为用户 provenance |
| BookStack Lite A0 [`00c59e0762fb`](../evidence/arc-bench/runs/00c59e0762fb/manifest.json) | 平台 `32/34`、FAILED，`REQ-4.5.1` 和 `REQ-6.1.3` 十秒超时；内部 round 0、round 1 均 `32/34`、同两题失败 | 1,324 次；输入 35,214,173、输出 681,758、缓存命中 32,267,264、推理 401,979、Provider total 35,895,931、平台 Token 60,951,255；14,338 秒；¥32.962032 | 已确认的功能缺陷及成本基线；A0 为用户 provenance |
| BookStack Web [`c31c51f2400b`](../evidence/arc-bench/runs/c31c51f2400b/manifest.json)（[阶段 4 结果](../evidence/arc-bench/runs/c31c51f2400b/phase4-result.md)） | 冻结 A0；平台 `34/34`、PASSED、score 100；内部 round 0 `34/34`，修复轮次 0 | 1,095 次；输入 27,791,179、输出 494,827、缓存命中 25,721,344、推理 243,817、Provider total 28,286,006、平台 Token 28,219,131；7,362 秒；¥13.216805 | 功能通过样本；仅评审效率与回归门槛，不立功能补丁 |
| Keep Lite V1 [`0aa6820e0b82`](../evidence/arc-bench/runs/0aa6820e0b82/manifest.json)（[阶段 4 文稿](../evidence/arc-bench/runs/0aa6820e0b82/phase4-result.md)，交接已核验） | 候选 ZIP 用户指认；平台 `29/32`、FAILED：`REQ-2.3.2` Undo、`REQ-2.5.4` 归档前置、`REQ-2.7.5` Save 脱离 DOM；内部 round 0/1/2 均 `29/32` | 1,291 次；输入 34,395,140、输出 717,795、缓存命中 31,627,392、推理 444,073、Provider total 35,112,833、平台 Token 35,112,935；9,777 秒；¥17.926147 | 三种独立机制的诊断样本；V1 映射未获平台独立绑定 |
| BookStack Lite V1 [`5669f7d1777c`](../evidence/arc-bench/runs/5669f7d1777c/manifest.json)（[阶段 4 结果](../evidence/arc-bench/runs/5669f7d1777c/phase4-result.json)） | 此前称首次修改版；平台 `32/34`、FAILED：`REQ-5.6.1`、`REQ-6.1.1` 保存后目标文本定位超时；内部全套 round 0 `33/34` → round 1 `34/34`，但 `REQ-5.6.1` 定点验收三轮均 `0/1` | 1,275 次；输入 32,112,397、输出 693,949、缓存命中 29,468,416、推理 420,911、Provider total 32,806,346、平台 Token 32,806,461；12,739 秒；¥17.124841 | 保存后展示/定位器选择的新诊断样本；V1 映射未获平台独立绑定 |
| ticket-booking [`1aac5ece078e`](../evidence/arc-bench/runs/1aac5ece078e/manifest.json)（[阶段 4 结果](../evidence/arc-bench/runs/1aac5ece078e/phase4-result.json)） | submission `67a8e2ef92a4`；平台与内部均 `10/10`、PASSED、score 100；无失败链 | 2 次；Provider total 37,107、平台 Token 79,281；231 秒；¥0.484403 | 成功基线；身份缺口保留，不作为已绑定的阶段五 A/B |

缓存命中 Token 是输入 Token 的子集，推理 Token 通常包含在输出口径内，不能再加到 Provider total；平台 Token 与 Provider total 口径不同，不能互相替代。旧 Keep 的人工摘要曾将内部 round 0 写为 `26/32`，与原始日志 `31/32` 冲突；新 BookStack 的 summary 将内部 round 0 写为 `26/34`，原始日志是 `33/34`；本台账均按日志与 manifest 的口径保留冲突。六个 Run 均核验平台入口 `main.py` 和 `/workspace/tests`，没有 bundled tests 回退；这不能代替未来每次 Run 的独立核验。Web 与 Lite 虽同为 BookStack、测试数量也同为 34，但属不同赛道，不构成同任务、同快照的 A/B；两个 Lite BookStack 也因代码血缘与快照绑定不足，不得直接计算阶段五收益。两个 Keep Lite 的 `REQ-2.5.4` 失败发生在**不同操作阶段**，不能仅凭相同编号归并。

## 3. 跨 Run 问题索引

| ID | 失败机制或决策问题 | 当前证据等级 / 适用范围 | 当前状态 | 优先级与依赖 |
|---|---|---|---|---|
| `P5-001` | 设计中声明的路由未接入生成应用主路由 | `confirmed`：BookStack 同一 Run 的两处漏接；**尚未跨 Run 确认** | 本地已验证；平台效果未验证 | P0；平台 A/B 前先确认身份 |
| `P5-002` | 状态写入与随即导航/读取可能竞态 | `strong_candidate`：Keep 一处；缺最终网络/DOM 时序 | 待证据，不修改 | P1；需 Keep trace 或等效复现 |
| `P5-003` | A0 超时摘要可能把缺路由误导成等待/性能问题 | A0 措辞 `confirmed`；对修复结果的因果影响 `unknown` | 已在 `P5-001` 同一切片本地修改；平台效果未验证 | P0，随 `P5-001` 一起 A/B |
| `P5-004` | 五个 Run 的请求、Token、耗时均可计量，但瓶颈来源未定位 | 指标 `confirmed`；根因 `unknown`；新 Keep 有请求级 meter 但缺阶段归因 | 暂缓 5C/5D 调参 | P2；功能率稳定且完成请求级归因后重开 |
| `P5-005` | A/B 的上传 Agent 构建、任务快照绑定不完整 | 多个 manifest 缺字段 `confirmed`；`cca008377368`/`bf5e742c15a4` 的用户版本归属与 manifest 文件名冲突，且无平台独立 ZIP→build/code 绑定 | V4.1 build provenance 已本地实现并通过包身份/shape 核验；三项离线复现进行中，平台外部绑定仍未闭合 | P0；复现通过后才可形成上传建议，平台 Run 仍须逐项绑定 |
| `P5-006` | Undo 可访问名称被生成代码覆盖 | 原版失败、修正版及 32 题回归通过：产物级 `confirmed` | Agent 通用契约/失败提示本地已验证；平台未验证 | P0；与消息文本契约一起回归 |
| `P5-007` | Keep 归档测试前置数据与生成应用 seed 不一致 | 原版与分步对照 `confirmed`；评分后 ZIP 的 `24/32` **不是**平台启动基线 | 默认 seed 和按钮修复在干净 seed 下通过；评分时目标仍为归档态，精确启动策略未知 | P0；不得用删库回归代替交付验收 |
| `P5-008` | 重复加载标签与整表重绘打断编辑 | 干净 seed 的 50ms 对照原版 3/3 失败、去重版 3/3 通过；平台精确时序/根因 `unknown` | Agent 通用契约/失败提示本地已验证；平台未验证 | P0；保留全量回归和受控时序 |
| `P5-009` | BookStack 异步保存后过早选择 heading 定位器，而结果页只以链接展示新实体 | `confirmed`；两题 POST/DB/HTML/helper 链条在受控 150ms 延迟下各 3/3 复现；平台收益和 Agent 归因未知 | V3 本地候选已冻结、用户报告已人工上传；当前 `NO-GO` 业务 Run，等待 P5-012/P5-013 与身份门禁 | P0；门禁闭合后先跑 BookStack V3，并核验两题与 34 题回归 |
| `P5-010` | Keep 初始数据契约遗漏必需的 `Work editable` 标签 | `confirmed`：平台失败、bundle `loadDB()`/`seedDefaults()` 链路、设计快照三方闭合；当前仅 Run-local，跨 Run 适用性未知 | `approval_required` + `deferred`；冻结 V3 不混入本项改动 | P0；待有效 V3 Keep 结果后，必要时作为独立 V4 通用切片 |
| `P5-011` | Keep 静态 Reminders 导航与动态 Reminders 标签产生重复 accessible name | `confirmed`：平台 strict-mode 失败、评分前 DOM、最终包源码三方闭合；当前仅 Run-local，跨 Run 适用性未知 | `approval_required` + `deferred`；冻结 V3 不混入本项改动 | P0；待有效 V3 Keep 结果后，必要时作为独立 V4 通用切片 |
| `P5-012` | 模型认证失败后生成链无产出，平台在业务测试前停止 | `ff12a7ff45f8` 的 401/无写入链和 `cca008377368` 的 401→exit 2 链均为各自 Run-local `confirmed`；认证责任归因仍 `unknown`；`cca` 的冻结 V3 用户归属与 manifest 文件名/行为线索冲突，具体 build 来源未绑定 | V3.1 本地控制面切片已验证；平台已观察到 fail-fast 行为，但不能归因于 V3 或 V3.1/V4 的具体代码，认证正路径与业务生成仍未验证 | P0 gate；仅补认证正路径、endpoint/权限/meter 与 build/ZIP 身份，不派业务代码修改 |
| `P5-013` | 最终包缺少 frontend/backend/main.py/tests，平台在业务测试前拒绝模板 | 最终 ZIP 形状与拒绝原因为 Run-local `confirmed`；旧 Run 上游首断点仍 `unknown` | V4 本地门禁已验证：workspace/staging/final ZIP 清单、首坏阶段、Agent ZIP 根层级；历史首断点与平台未验证 | P0 gate；新 Run 回收 pipeline 清单并绑定 build→ZIP/task snapshot |

**当前跨 Run 结论：**多个 Lite Run 都有十秒超时且请求较多，但 Keep 的可访问名称、seed、DOM 重绘，与 BookStack 的缺路由、保存后展示/定位边界是不同机制。A0 BookStack 的 `P5-001` 缺接线，V1 BookStack 的 `P5-009` 名义路由/API 已存在，不能把两次 `32/34` 合并成一种故障；A0/V1/V2 标签只修正谱系组织，不自动证明阶段五收益。A0 Web BookStack 已 `34/34` 通过，说明漏路由不是所有 BookStack Run 的必然结果，却不能推翻 Lite 的具体漏接证据。禁止按“超时”这一表面标签做单一补丁。

## 4. 决策记录与现有能力盘点

### `P5-001`｜生成路由契约未闭环

- **已确认事实：**BookStack 的 `.arc/design/REQ-4.5.1.json` 声明 `POST /shelf/:id/edit`；最终生成包 `backend/server.js` 有 `handleShelfEdit` 和提交表单，但主请求分发没有该 POST 分支。`.arc/design/REQ-6.1.3.json` 声明 `GET/POST /page/:id/delete`；最终生成包有删除页面/处理函数，却没有对应 GET/POST 分支。两类漏接在相关 codegen 快照中已出现并延续到最终生成包。Playwright 分别等不到更新后的 Shelf 标题和 `Confirm Delete` 按钮。因此“十秒超时”只是外部表现，缺路由是可直接定位的生成应用缺陷。
- **共性边界：**“设计—代码接线遗漏”可作为通用 Agent 防线候选；目前只在 Lite BookStack 一个 Run 中观察到两次。冻结 A0 的 Web BookStack `c31c51f2400b` 首轮和平台最终均 `34/34`，可作为功能通过的回归样本，但赛道不同，不能据此判断 Lite 的缺路由已自愈，也不能宣称所有 Lite/Web 任务都存在该缺陷。
- **A0 已有与候选新增：**A0 的 [`arc/main.py`](../arc/main.py) 已让模型产出 `.arc/design` 的 `routes`，并有逐节点 acceptance、修复轮次、无进展切换与最佳状态保留；[`arc/acceptance.py`](../arc/acceptance.py) 已生成失败摘要，但无通用路由接线提示。独立候选分支 `codex/arc-bench-phase5-route-contract`（完整提交 `c53c333d5205fb98bf168c1f4fc670c0eec7432f`）只在**测试失败时**读取当前节点设计与生成的 `backend/server.js`，把未在受支持的显式分发条件中检出的路由加入原有修复摘要；不另建验收循环，也不覆盖最佳状态机制。
- **方案形式与选择：**已采用保守的本地静态诊断，而非执行生成代码或对有副作用的 POST 发探测请求。支持真实快照中同时出现的字符串路由（如 `"POST /shelf/:id/edit"`）和对象路由；只识别同一行的显式 `req.method` 加路径条件，同一路由族已有可识别分支时才给出最多 3 条“待核查”提示。未知路由风格保持沉默，提示不阻断测试。单纯追加提示词不能识别漏接；按 BookStack 任务名写补丁会过拟合，均未采用。
- **已改边界：**候选只改 `arc/main.py` 的现有 acceptance 入口、`arc/acceptance.py` 的摘要与路由候选函数、对应两份单元测试及 `CHANGELOG.md`；未改 `arc/codegen.py`、官方需求/测试、生成应用快照或冻结 A0。
- **可验证行为：**在缺路由的最小生成样例中识别遗漏，在已接路由样例中不误报；BookStack 同任务、同快照、同配置的新候选平台 Run 不再因这两个路由失败，且 Smoke 无回归。目标是提升 32/34，不保证仅此改动就能达到 34/34。
- **本地验证与当前决策：**新增 4 项定向测试通过；用 BookStack 最终生成包及 `.arc` 设计快照检出 `POST /shelf/:id/edit`、`GET/POST /page/:id/delete`，Keep 失败节点没有误报。候选 `arc/tests` 81 项仍有 3 fail + 1 error；A0 78 项在同一 Windows 环境中有**完全相同的四项**路径/临时 Git 权限失败，故没有新增失败。状态为**本地已验证、BookStack 平台收益未验证**；现已有用户指认的候选 ZIP 和 Keep 新 Run，但 Keep 并非此路由诊断的有效功能验收。

### `P5-002`｜Keep 归档后立即打开列表的时序疑点

- **已确认事实：**Keep 最终测试在 `Unarchive` 按钮定位处超时。生成前端执行归档 `PUT`，成功回调后才移除当前卡片；侧栏打开 Archive 会立即发起一次归档列表 `GET`，没有等待该 `PUT`，失败也可能被静默吞掉。后端归档查询、`PUT` 和 `Unarchive` 按钮生成逻辑均存在。内部全量验收曾是 32/32，而平台最终是 31/32。
- **推论与替代解释：**若 `GET` 先于 `PUT` 完成，列表可能暂时缺目标卡片且不会自动重载，这是 `strong_candidate`，不是已证明的最终事件序列；DOM 定位、网络错误或其他状态污染仍未排除。
- **方案形式与选择：**可能需要通用的“写操作完成后再导航/刷新”生成约束及对应快速交互回归测试；目前**不对 Keep 写题目特例，也不把该候选并入 `P5-001` 的路由切片**。先取得失败时的 `error-context.md`、Playwright trace/截图或等效请求时序复现。补证据后让阶段 4 复核，再决定是否作为独立阶段 5 切片。
- **重开条件：**观察到请求时序、归档列表状态与按钮缺失之间的直接链路；或后续其他 Run 出现同类“写入后立即读取旧状态”机制。

### `P5-003`｜超时分类的措辞偏差

- **已确认事实：**A0 的 [`failure_summaries`](../arc/acceptance.py) 对 `timedOut` 添加“page or a request never settled”的概括。这是对可能原因的推断，不适用于 BookStack 已定位的漏路由情形。
- **未知：**没有证据证明模型确实因该措辞才未修好 BookStack，不能将它单独记为失败根因。
- **已实施形式与关系：**候选在同一失败摘要中把 timeout 改为“超过测试截止时间；原因未确认”，并加入有边界的路由候选提示；未增加分类器、重试器或等待时间。是否实际帮助平台修复仍需 A/B，不能把本地文本变化宣称为成绩收益。

### `P5-004`｜Token、请求数和运行时间

- **已确认事实：**先前两个 Lite Run 分别有 1,004/1,324 次模型请求、约 3.77/3.98 小时耗时；A0 Web BookStack 在 `34/34`、零修复轮次下仍有 1,095 次请求、7,362 秒耗时。新 Keep `0aa6820e0b82` 为 1,291 次请求、9,777 秒，输入缓存命中 31,627,392 / 34,395,140（约 91.95%）；已有请求级 meter 导出，但尚未关联到设计/实现/修复阶段。总量不能准确指认费用瓶颈；跨赛道或不完整身份绑定下的差异不能解释为 Agent 优化收益。
- **当前代码已有：**[`arc/main.py`](../arc/main.py) 已设置请求预算、修复轮数、无进展停止和最佳状态保留；[`arc/llm_proxy.py`](../arc/llm_proxy.py) 与 [`arc/metrics.py`](../arc/metrics.py) 有代理计量与汇总。不得把这些能力当成“尚未实现”再做重复预算层。
- **当前决策：**完成率优先。Web BookStack 阶段 4 建议 `review_only`：无功能补丁，`34/34` 是后续效率实验不可降低的回归门槛。暂不全局缩短预算、改模型、压缩所有节点上下文或调大并发；先在 Lite BookStack 的 `P5-001` A/B 中观察修复轮数和请求变化。若同任务功能率相同，再用请求级明细选择 5C/5D 的单变量实验。
- **重开条件：**把新 Keep 的请求级 meter 与日志轮次/节点时间戳关联，找出前几类高成本调用；或后续 Run 显示重复失败、重复视觉分析、无进展循环等明确机制。末轮三个约 10 秒失败合计约 30 秒，占 9,777 秒总 Run 低于 0.4%；不能把消除这三次等待夸大成显著的总耗时优化。

### `P5-005`｜A/B 身份与任务快照绑定

- **已确认事实：**本台账最初审查的四份 manifest 的 `task_snapshot_id` 均为 `null`；后纳入的 `5669f7d1777c` 和待决策的 `737b56972d5a` 也缺此字段。各 Run 缺少平台独立记录的上传 Agent ZIP SHA 和代码 SHA 绑定。Web BookStack 的 A0 身份有用户明确确认。新 Keep 的展示名仍为 A0，**不能据此断定上传了旧代码**：用户指认上传 `D:/DataMove/codex/worktrees/9015/AI智能体软件工厂黑客松/.worktrees/phase5-route-contract/arc/arc_first.zip`，本地 SHA-256 `483BB260AB8DAC167059D21E0947DFFEA5495C16EA25510C01BA7DF5A4B2DB21`，ZIP 内 `main.py`/`acceptance.py` 哈希与候选提交 `c53c333d5205fb98bf168c1f4fc670c0eec7432f` 源码一致。这证明本地 ZIP 的内容，不等于平台独立证明该 ZIP 被接收；生成应用 `template.zip` 的 SHA 不能充当上传 Agent ZIP 的 SHA。
- **当前决策：**此项是候选平台复跑前的证据门禁，不默认引发 Agent 主流程改造。先用现有上传、运行和官方快照材料补充/核验 build ID、代码 SHA、上传 ZIP SHA、任务快照或官方任务资产哈希及配置哈希；平台无法给出时记录不可比限制，不填猜测值。
- **重开条件：**现有记录无法完成绑定，且确认需在 `arc/metrics.py` 或运行清单中加入最小元数据输出时，再立项 5A 的窄切片。不要因此提前重构完整 TaskContext。
- **V4.1 转派更新（2026-09-21）：**`cca008377368`/`bf5e742c15a4` 已满足上述重开条件：仅靠上传文件名和用户 provenance 无法区分冻结 V3 与 `13173bb…` 候选，且 401 可在业务生成前终止。用户授权 handoff `phase5-p5005-build-provenance-v41-20260921-v1`，由 Agent 实现会话从 V4 候选 `13173bb50e556c78bcd9cfdcc25c5449eee37f65` 开始，实现不可变 build manifest、网络前身份输出、失败路径身份落盘及 content-addressed 发布 sidecar；冻结 V3 不改。本切片只提高后续 Run 的可归因性，不能反向消解既有两个 Run 的身份冲突，也不能替代平台 submission/build、上传时间和 task snapshot/官方资产哈希的外部记录。

### `P5-006`｜Undo 的可访问名称与官方精确定位冲突

- **直接证据：**新 Keep 官方 `helpers.ts` 用 `getByRole('button', { name: /^Undo$/i })`。生成应用 `index.html` 的按钮文本和初始 `aria-label` 都是 `Undo`，但 `trashNote()` 在删除成功后调用 `showSnackbar('Note deleted', true, 'Note trashed')`，后者把按钮 `aria-label` 改成 `Note trashed`。按 [W3C 可访问名称规则](https://www.w3.org/WAI/ARIA/apg/practices/names-and-descriptions/)，显式标签优先于可见文本；即使按钮出现，官方精确 locator 也匹配不到。这比阶段 4 的“等待请求/ready”解释更直接。最终失败是否还有网络延迟，需要 trace 排除；不能仅凭静态证据声称运行时链路已完整证明。
- **最小方案：**先在隔离生成应用副本里让按钮的可访问名称保持 `Undo`，把 `Note trashed` 留在提示消息区；不改官方测试或扩大超时。验证默认状态、删除后、点击 Undo 后的角色/名称及功能回归。
- **Agent 方案形式：**若验证成立，优先复用现有 `arc/acceptance.py` 失败摘要，把“官方 role/name 与生成 DOM 的实际 accessible name 不一致”作为有证据、有限长度的修复提示；不新增 Keep 专用分支或第二套验收器。先证明这类提示能正确指导修复，再决定是否加入通用静态/浏览器检查。
- **复现后更新（2026-09-19）：**原版 `REQ-2.3.2` 失败；只去掉第三参虽使本题通过，却使 `REQ-2.3.1` 因缺少 `Note trashed` 消息而回归失败。最终产物方案是 `showSnackbar('Note trashed', true)`：状态消息与 `Undo` 按钮名称各归其位，干净 seed 的 32 题全过。候选 Agent 仅增加通用名称契约和有界诊断，未硬编码 Keep 文案；见第 10 节。原段的“若验证成立”保留为决策历史，不再表示尚未复现。

### `P5-007`｜REQ-2.5.4 前置 seed 状态不满足测试契约

- **直接证据：**新 Keep 官方 `REQ-2.5.4` 是 `openHome → archiveNote('Travel plans 2.5.4') → openArchive → unarchiveNote`，失败发生在首个 `archiveNote` hover；生成应用 `renderNotes` 会过滤已归档 note。该生成包的 `backend/server.js` `DEFAULT_DB` 中 `seed-archive-254` 已为 `archived: true`，最终 `backend/data/db.json` 中也为 `true`。因此“只删或重建 `db.json`”会从同样不满足前置条件的 `DEFAULT_DB` 再生出错误状态；阶段 4 的清库建议**不能直接执行**。最终平台是否从此文件直接启动仍待平台构建/启动证据确认。
- **最小方案：**在隔离副本中分别保存原始 `db.json`、从 `DEFAULT_DB` 再生的 seed、仅把该目标 note 设为 `archived:false` 的实验变体，三者各跑一次单题，记录 `GET /api/notes` 响应与首次首页 DOM。原始和 DEFAULT_DB 均缺目标首页卡片、实验变体通过，才支持前置 seed 是主因；若实验变体仍失败，再查网络/渲染时序。不要覆盖官方快照、原始 ZIP 或其他 fixture。
- **Agent 方案形式：**优先让现有逐节点验收/修复回路携带“测试动作要求的初始数据状态”及失败首步，而不是写死 note 名称或全局清库。仅在跨 Run 反复出现相同 fixture 漂移且现有摘要不足时，考虑小型通用 seed 合同检查。旧 Keep `0cef369cc925` 在 **Unarchive 按钮**处失败，保留为 `P5-002`，不并入本项。
- **复现后更新（2026-09-19）：**分步对照确认须同时修正 `DEFAULT_DB` 中该 note 的 `archived:false` 和归档态按钮的精确名称 `Unarchive`，干净 seed 全量 32/32。原始 `template.zip` **自带** `backend/data/db.json`，其中该 note 仍为 `archived:true`；`loadDb()` 只有文件不存在才使用修正后的默认值。保留该数据库并使用相同修复版前后端的全量对照实测 `24/32`，`REQ-2.5.4` 仍在首次首页 hover 失败；还有其他已被删除、归档或固定的 fixture。**时序纠偏：该 ZIP 数据库已被平台最终评分写入，不是评分前交付态；`24/32` 只能证明评分后状态重放会污染测试，不能据此断言平台以此状态开跑或仅改默认 seed 必然无法交付。**但本 Run 的 `DEFAULT_DB` 原本就把目标设为归档态，评分时首页也找不到它，仍须修正生成时的前置数据契约。平台具体重置/导出策略待确认；不可盲目删除数据。Agent 改动只在共享契约中要求首步前置状态及生成时持久数据一致，未写题目特例；详见第 11 节。

### `P5-008`｜标签重复加载与编辑行重绘

- **直接证据：**新 Keep 生成前端 Edit labels 点击处理器连续调用两次 `loadLabels()`；每个响应都调用 `renderLabels()`，把 `labelsList.innerHTML` 清空重建。官方测试填入 `Work editable → Projects` 后点击 Save，平台报告按钮先解析成功，后因不稳定并从 DOM 脱离而失败。代码中的重复请求和重建已确认；第二个响应是否恰在点击期间触发，尚缺 trace/DOM mutation 时间戳。
- **最小方案：**隔离副本中先只去掉重复调用，复跑本题；若仍不稳定，再以请求序号丢弃过期响应或在编辑期间保留当前行，优先避免重复拉取和 DOM 替换。必须回归标签创建、删除、重命名；不引入 React 或新状态管理依赖。
- **Agent 方案形式：**复用现有 Playwright call log 摘要，针对“resolved but detached”给出检查并发请求/整表重绘的**候选**提示；只有 trace 证明后才加更窄的自动检测。不要因为所有失败都叫 timeout 而统一加等待。
- **复现后更新（2026-09-19）：**旧 250ms 实验曾被复用数据库污染，已废弃。新实验每轮重建 seed，记录 DB 前后哈希及 DOM/请求时间线：第二次 `GET /api/labels` 在 fill 后、Save 完成前重建行；原版 +50ms 3/3 失败，删重复 `loadLabels()` 后 3/3 通过。平台 trace 是按钮脱离后超时，本地受控实验是 Playwright 重试后提交旧值、最终断言失败；**两者相容，但平台的精确因果链尚未证实**，3/3 也不是生产抖动率估计。评分后 ZIP 的本地重放中，去重版 `REQ-2.7.5` 仍 Save-detach：静态 HTML 是 `Work editable`，持久 DB 却已为 `Projects`，一次异步加载也会重建编辑行。由于此 DB 是评分后快照，不能据此证明平台评分前就有 `Projects`，也不能把该次重放当作去重方案的交付反证。`renderLabels` 整表重建仍是潜在风险，现阶段不重写渲染层；若新 Run 再现才考虑 stale-response guard 或局部 patch。

## 5. 暂不修改事项与重评条件

| 工作流 / 事项 | 当前决定与理由 | 重评触发 |
|---|---|---|
| 5A 完整 TaskContext 重构 | 暂缓；两个 Lite Run 的 `/workspace/tests` 来源已核验，眼前功能缺陷是路由接线。仅 `P5-005` 的身份绑定属于 A/B 前置工作 | 出现跨赛道同名任务错配、bundled tests 回退或现有元数据无法绑定构建 |
| 5B 多模态清单与视觉缓存 | 暂缓；这两处最终失败没有证据指向图片理解或官方缺图处理 | 新 Run 证明图片重复分析、理解错误或缺图卡死 |
| 5C 全局需求上下文压缩 | 暂缓；不能只凭总输入 Token 大就安全裁剪需求 | 请求级计量与失败链路表明重复上下文是瓶颈，且能设完整性回归 |
| 5D 全局模型/推理/预算路由 | 暂缓；先处理功能缺陷，现有预算机制也需复用而非重造 | 同通过率下可比 Run 证明某一请求类别可低成本替代 |
| 5E 的任务名特例、全局延长超时、重复验收器 | 决定不采用；分别有过拟合、掩盖根因和代码冗余风险 | 仅在新证据推翻现有机制判断后重新论证 |
| 5F Evolution 指纹与增量编译 | 本轮暂缓；两个 Lite Run 不足以证明 Evolution 故障 | 对应 Evolution 基线显示全量重建、错误影响范围或回归 |
| 5G 进程/端口/OOM 治理 | 本轮暂缓；失败可定位到生成应用/交互，尚无进程资源故障证据 | 新 Run 提供端口冲突、启动失败、OOM、泄漏或超时层级证据 |
| Keep 的具体生成代码补丁 | 旧 Keep `P5-002` 仍待证据；新 Keep 的四处生成应用改动已在隔离副本通过干净 seed 的 32 题，但不是永久 Agent 修改；评分后 ZIP 的 `24/32` 不能视作交付态验收 | 取得评分前状态/启动策略证据、可比平台 Run 或新 Run 同机制反证 |
| 新 Keep 一律清库/全局等待/重写前端 | 决定不采用；`DEFAULT_DB` 自身就有错误归档前置状态，Undo 是名称契约，Save 是 DOM 替换候选；全局手段可能掩盖或制造新问题 | 有新的直接证据表明这些动作必要且不伤其他 fixture |
| 为 Keep 引入 React、TanStack 或新验收循环 | 暂不修改；现有前端为原生 JS、Agent 已有验收/摘要循环，增加依赖或并行机制会放大维护成本 | 最小现有路径无法解决且有多 Run 复现 |
| BookStack 一律清空 DB、全局加 heading 或改官方 helper | 暂不采用；`5669f7d1777c` 下载 ZIP 是评分后产物，不能证明评分前状态污染；新增 heading 应先在隔离产物中验证语义、时序和全套回归，官方测试不改 | 评分前 DB 哈希/快照与定点对照、真实浏览器 DOM/网络链路证明具体机制 |
| 上传 ZIP 打包卫生 | 下次候选建议使用现有 [`arc/pack.sh`](../arc/pack.sh) 的白名单；`arc_first.zip` 根目录正确但含额外脚本、文档、缓存目录和 7 个 `.pyc`；**没有证据证明这些造成 Keep 失败** | 下次打包前做条目清单、入口与 SHA 校验 |
| Web BookStack 功能补丁 | 决定不改；冻结 A0 的 `c31c51f2400b` 已首轮及最终 `34/34`，阶段 4 仅建议效率评审 | 新的同任务失败链路或可复现回归；效率优化必须保持 `34/34` |

暂缓不是“永不处理”。每个新 Run 都须检索上述触发条件；无新证据时保留决定，不因看到同名任务或同样的超时字符串就自动翻案。

## 6. 新 Run 进入阶段 5 时的更新流程

此节由专门的“跨 Run 决策台账”会话执行；复现、Agent 实现和指标会话仅通过[多会话工作流](./ARC_BENCH_HACKATHON_PHASE5_COLLABORATION_WORKFLOW.md)中的核验状态与短卡回交，不平行修改本台账。

1. 以 `run_id` 找到阶段 3 manifest、阶段 4 单 Run 结论和必要原始附件；核对 competition/task、submission、构建、快照、模型与最终平台状态，保留缺失和冲突。
2. 把失败拆成**现象、可证实的机制、仍待排除的解释**。对照第 3 节的机制 ID：相同机制追加 Run 证据；只相似但机制不同则建新 ID；不足以判断时列为开放关联，不强行归并。
3. 重新检查当前分支代码与已有实现清单：现有机制、入口、调用关系、测试、配置、提交和候选构建。列出复用点、潜在冗余、过度嵌套、竞态及与其他切片的冲突；不能只依据本文件中的旧描述。
4. 对每个方案记录：影响完成率/Token/耗时的预期方向、适用范围、备选方案与拒绝理由、方案形式、改动文件/接口、依赖和风险、最小本地验证、代表题回归、平台 A/B 可比条件、回退条件。预期方向不是已实测收益。
5. 一次只实施一个主要变量。不同工作流可在隔离工作树并行研究，但同一工作树只允许一名写入者；由单一集成人串行合并，避免两项改动在 `arc/main.py` 或验收路径上互相覆盖。
6. 新候选 Run 先交回阶段 3 记录原始事实，再由阶段 4 独立复核，最后在本文件更新“平台已验证/失败/已回退”。不以最好一次或本地测试通过冒充最终结论。

每条后续决策至少补齐以下字段：`问题 ID / Run ID / 当前代码基线 / 证据等级 / 跨 Run 适用性 / 决策因素与备选方案 / 方案形式 / 已有能力与重叠 / 修改位置 / 验证与 A/B / 完整提交及构建身份 / 状态 / 未解疑问 / 重开条件`。只记录能支持未来决策的简短理由，不复制完整推理或日志。

## 7. 首轮执行门禁（本地切片完成，平台待启动）

1. 先解决 `P5-005` 的可比性记录：至少能区分 A0 与新候选上传包，并确认同任务官方版本、模型、推理级别、预算、测试来源和并发条件。Keep 与 BookStack 预算不同，**只能在各自任务内做同条件 A/B**，不能直接跨任务比绝对费用。
2. `P5-001` 与 `P5-003` 已在一个本地切片实现并做最小样例、真实生成包核验；已有用户指认的候选 ZIP 和 Keep Run，但**仍未进行 BookStack 或 Smoke 的候选平台复跑**。后续复跑须在用户明确安排后进行，不混入 5B/5C/5D/F/G。
3. 旧 Keep 的 `P5-002` 保持待证据。新 Keep `P5-006/007/008` 已按第 10 节完成定点复现及窄 Agent 切片；原包 DB 的本地 `24/32` 已重分类为**评分后快照重放**（第 11 节），下一门槛是取得评分前状态/启动策略证据、候选 ZIP 身份绑定和用户安排的同条件平台 A/B。不要把两个 Keep 的同编号失败混成一个“归档竞态”。
4. A/B 比较至少覆盖：平台通过数、首轮通过数、请求数、输入/输出/缓存/推理 Token、平台 Token、费用、总耗时和修复轮数；功能下降默认拒绝，平台异常需标记而非静默挑选最好结果。

## 8. 当前实现与验证流水账

| 日期 | 事项 | 状态 | 代码提交 / 构建 / Run | 结果 |
|---|---|---|---|---|
| 2026-09-19 | 建立阶段 5 跨 Run 决策台账 | 文档建立；Agent 改动未授权 | 尚无优化代码提交、候选 ZIP 或优化版 Run | 仅完成执行前核验，不宣称阶段 5 或 G6 完成 |
| 2026-09-19 | `P5-001` + `P5-003` 保守路由诊断与中性超时摘要 | 本地已验证；BookStack 平台待验证 | `codex/arc-bench-phase5-route-contract`，`c53c333d5205fb98bf168c1f4fc670c0eec7432f`；用户指认 ZIP 见 `P5-005`；Keep `0aa6820e0b82` 仅供诊断 | 4 项定向测试通过；真实 BookStack 检出 3 条、Keep 0 条；完整候选 81 项/A0 78 项均为相同 3 fail + 1 error（Windows 基线问题） |
| 2026-09-19 | 纳入 A0 Web BookStack `c31c51f2400b` | 阶段 3/4 证据已验证；阶段 5 决定仅评审效率 | A0 原版 Run；非候选构建，非 A/B | 平台与内部首轮均 `34/34`；阶段 4 ACK/结果四项身份字段匹配；无功能补丁，`34/34` 作为回归门槛 |
| 2026-09-19 | 纳入候选 Keep `0aa6820e0b82`，建立 `P5-006/007/008` | 平台最终事实已读；阶段 4 交接已核验；未做本地复现/Agent 新改动 | 用户指认 ZIP SHA-256 见 `P5-005`；生成包 `template.zip` SHA-256 `9B46EC5C3D55FEDD1E986BC6733E05CFA8C95C76723EFF42B67C22CF8DE93EC4` | 平台 `29/32`；三项失败机制分开记录，不能从 31/32→29/32 直接推断路由切片造成退步 |
| 2026-09-19 | `P5-006/007/008` 定点复现后加入通用交互/种子契约与失败提示 | 生成产物干净 seed 本地 `32/32`；原包 DB `24/32` 为评分后快照重放；Agent 定向测试通过，平台收益未验证 | `codex/arc-bench-phase5-route-contract`，`dddc94312d4cd26babdbfb9d7df2a17f08f0a51d`；尚无此提交构建的上传 Agent ZIP/新平台 Run | `arc/main.py`、`arc/acceptance.py`、两份单测及根 `CHANGELOG.md`；定向 10/10，完整 84 项仍为原有 3 fail + 1 error；评分前 DB 精确状态和平台启动内部策略待核对 |
| 2026-09-20 | 纳入首次修改版 BookStack Lite `5669f7d1777c`，建立 `P5-009` | 阶段 3 manifest/阶段 4 JSON 已读，平台 `32/34`；保存后定位机制为强候选，暂不改 Agent | 上传构建 SHA 与任务快照缺失；此 Run 非 `dddc943...` 阶段五产物 | 原始报告两题均固定等 `heading`，生成详情页以链接展示新实体；先在隔离生成包定点复现并收集 DOM/请求/评分前 DB 哈希，见第 12 节 |

后续新增一行时，若状态为“实施中”或以上，必须写出实际文件、完整提交 SHA、构建 ID、测试命令及结果；若状态为“平台已验证”，还须写出新 Run ID 和 A/B 结论。不得把本文件的建立提交误写成 Agent 优化提交。

## 9. `0aa6820e0b82` 无 Octos/Cargo/API Key 的本地定点复现与后续切片

> 本节保留复现前的执行计划与当时的证据状态；实际完成情况、纠偏和最新门槛以第 10 节为准。不要再把本节“尚未执行”当作当前状态。

### 9.1 复现对象、前提和隔离

- **对象不是重新生成应用或重跑 Agent**，而是重放新 Keep Run 的最终生成应用 ZIP：`C:/Users/dayuruozhi/Downloads/闻悦源代码-首轮测试-keep-lite/0aa6820e0b82-template.zip`；官方公开测试取自 `workstreams/arc-bench/official-snapshots/20260917-150121Z/competitions/arc-bench-lite/tasks/arc-bench-lite--keep/public-tests`。此法可验证生成应用中的三种失败机制，不证明 Agent 生成过程、平台环境或得分会完全相同。
- 本机已检测到 Node/npm/npx；生成前、后端 `package.json` 的 `dependencies` 均为空。仍需 **Playwright Test 与匹配的 Chromium 浏览器**；本工作区 `arc/local-grader/node_modules` 和根 `node_modules` 当前均无 Playwright。若本机其他位置也没有，首次安装需要 npm/浏览器下载或已有离线缓存，**不需要 Octos、Cargo 或平台 API Key**。缺浏览器时不能把环境错误算成应用失败。
- 在唯一新建的临时目录解压 ZIP，不覆盖 ZIP、官方快照、当前仓库或 `.worktrees`。每一个单题、重复轮次或 seed 变体都从原始 ZIP 建立**独立应用副本**；保留各副本测试前/后的 `backend/data/db.json` SHA-256、目标 note/label 状态、服务日志和报告。只暴露给隔离本机/容器，禁用额外端口（`ARC_EXTRA_PORTS=0`），不要携带密钥或生产数据。**不调用现有 `arc/grade-local.py`**：它是旧 Unix 风格全套脚本，含 `preexec_fn=os.setsid`、`git checkout/clean` 和隐式安装，既不适合本机 Windows 定点复现，也可能改动目标目录。
- 阶段 4 交接门禁现已核验：`phase4-ack.json`、`phase4-result.json` 和 `phase4-handoff.json` 的 `handoff_id/run_id/task_key/thread_id` 一致，`phase4-thread-registry.json` 的 `arc-bench-lite--keep` 为 `verified`。结果 JSON 当前仍为另一个任务的未跟踪文件，阶段 5 只读取，不暂存或修改。这里的 `P5-006/007/008` 是对[阶段 4 分析](../evidence/arc-bench/runs/0aa6820e0b82/phase4-result.md)补充原始测试与生成包静态核查后的**更高优先级候选**，还未做本地运行时验证。

### 9.2 可复用的本机执行骨架（PowerShell）

以下是**建议操作，尚未执行**。对每个实验重新创建唯一 `$caseRoot`；在临时 runner 中放一份未改动的 `helpers.ts` 和三份相关 `.spec.ts`，让测试从 runner 的 `node_modules` 正常解析。首次安装 Playwright 后其余实验可复用该安装，但每次应用与持久数据必须隔离。

```powershell
$caseRoot = Join-Path $env:TEMP ('arc-keep-repro-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $caseRoot | Out-Null
Expand-Archive -LiteralPath 'C:\Users\dayuruozhi\Downloads\闻悦源代码-首轮测试-keep-lite\0aa6820e0b82-template.zip' -DestinationPath $caseRoot
$app = Join-Path $caseRoot 'template'
$runner = Join-Path $caseRoot 'runner'
New-Item -ItemType Directory -Path (Join-Path $runner 'tests') | Out-Null
Copy-Item -LiteralPath 'D:\DataMove\codex\worktrees\9015\AI智能体软件工厂黑客松\workstreams\arc-bench\official-snapshots\20260917-150121Z\competitions\arc-bench-lite\tasks\arc-bench-lite--keep\public-tests\helpers.ts' -Destination (Join-Path $runner 'tests')
# 同样 Copy-Item 三份 REQ-2.3.2/2.5.4/2.7.5.spec.ts；不要编辑官方内容。
Push-Location (Join-Path $app 'frontend'); node scripts/build.js; Pop-Location
Push-Location $runner; npm install --no-save @playwright/test; npx playwright install chromium; Pop-Location
$env:PORT = '43300'; $env:ARC_EXTRA_PORTS = '0'; $env:E2E_BASE_URL = 'http://127.0.0.1:43300'
$server = Start-Process -FilePath (Get-Command node).Source -ArgumentList 'server.js' -WorkingDirectory (Join-Path $app 'backend') -WindowStyle Hidden -PassThru
# 等待本机 43300 端口就绪；在 runner 下运行下面的 Playwright 命令。结束后 Stop-Process -Id $server.Id。
```

在**临时 runner** 手工创建 `playwright.config.ts`（不是改官方测试或仓库文件），内容控制在最小范围；`retries:0` 时使用 `retain-on-failure`，不要误用只在重试时才记录的 `on-first-retry`。Playwright 文档确认 [单文件测试、workers 与 trace CLI](https://playwright.dev/docs/test-cli) 以及 [失败时保留 trace](https://playwright.dev/docs/trace-viewer) 的用法。

```ts
import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', timeout: 10000, retries: 0, workers: 1,
  reporter: [['json', { outputFile: 'report.json' }], ['line']],
  use: { headless: true, baseURL: process.env.E2E_BASE_URL, trace: 'retain-on-failure' },
});
```

```powershell
Push-Location $runner
npx playwright test -c .\playwright.config.ts .\tests\REQ-2.3.2.spec.ts --workers=1 --retries=0
# 另起全新应用副本，依次替换为 REQ-2.5.4.spec.ts、REQ-2.7.5.spec.ts。
Pop-Location
```

每轮记录 `report.json`、`test-results/**/trace.zip`、前后 DB、`GET /api/notes`/相关请求及服务日志；本机查看 trace 用 `npx playwright show-trace <trace.zip>`，不上传含可能敏感数据的 trace 到公共网站。若浏览器版本、平台端口、测试超时或打包状态不同，标明差异。浏览器 context 隔离不等于后端 `db.json` 隔离，故必须为每轮复制应用副本。

### 9.3 三项对照实验与停止/通过标准

| 实验 | 原版先观察 | 只改变一个变量的副本 | 支持/推翻条件 |
|---|---|---|---|
| `REQ-2.3.2` Undo | 删除后在 trace/DOM 查 `#snackbar-undo` 的可见文本、`aria-label`、`getByRole('button',{name:/^Undo$/i})`，记删除请求状态/耗时 | 只让按钮可访问名称保持 `Undo`，消息文本仍可为 `Note trashed` | 原版按钮出现但角色/名称找不到、修正版能点并恢复 note：支持名称主因；若按钮根本未出现或请求失败，再查异步链路 |
| `REQ-2.5.4` 归档前置 | 原始 `db.json` 的 `seed-archive-254` 已 `archived:true`；再在**副本**中把该文件移走并启动，让 `DEFAULT_DB` 再生，检查是否仍为 `true` | 仅在另一副本中将该 note 的测试前置 `archived` 设为 `false`，保留其他 fixture | 原版/再生版首页都缺卡片，而前置正确版能完成测试：支持 seed 主因；若仍失败，则查 `GET /api/notes`、卡片渲染和后续 Archive/Unarchive 时序 |
| `REQ-2.7.5` 标签 Save | 记录两次 `GET /api/labels` 与 `#labels-list` 重绘、输入框填充、Save 点击的时间顺序 | 先只删第二次 `loadLabels()`；若失败仍在，再增加 stale-response guard 或编辑行稳定策略 | 去重即过关：优先最小修复；若仍 detach，依据 trace 决定是否需要更窄的 DOM 稳定策略 |

单题成立后，在新副本中用与平台一致的 `workers=1`、`retries=0` 跑这三题和相关前置题，再跑 32 项公开测试；每组从同一明确 seed 起步，记录顺序与数据变更。若单题过、全套不过，优先查共享后端状态和测试顺序；本机 32/32 **不等于**平台 32/32。全套官方测试只读使用，绝不改 locator 或放宽断言来“通过”。

### 9.4 本地复现之后才考虑的 Agent 改动与验收

1. **先保留证据和阶段 4 更正。**阶段 4 对 Undo 的“仅异步 readiness”、归档的“仅首屏异步”、以及“直接删/重建 db.json”都不足以解释当前静态证据；请阶段 4 所有者在后续诊断附注中复核并补充这些相反证据，而非由阶段 5 静默覆盖。标签第二次请求导致实际 detach 仍需 trace 判定。
2. **生成应用修复只是验证载体。**不把对 `template.zip` 或临时 `app.js`/`db.json` 的修补直接当成可交付 Agent 改动。若三项复现成立，在候选 Agent 分支上优先复用 `arc/acceptance.py` 的现有失败摘要与 `arc/main.py` 的现有修复入口，分别携带“精确 role/name 不符”“测试第一步所需 seed 状态”“按钮 detached + 重绘/并发候选”的短诊断；先加入单元/最小夹具测试，限制提示长度、误报和额外模型调用，不重复造验收器。只有跨 Run 证据支持时才增加常态化静态检测。
3. **防冲突顺序：**先冻结上传包 SHA/官方快照、校验阶段 4 门禁；再三项独立本地复现；再一项主要变量一提交的小切片；再 Smoke、Lite Keep、Lite BookStack 与 Web BookStack 回归（对应任务官方公开测试）；最后经用户安排做同任务、同快照、同模型/配置的候选平台 Run，回阶段 3/4 再入台账。Keep `29/32` 与旧 A0 `31/32` 不能直接证明路由切片导致回退，尤其该切片在 Keep 失败节点上无路由提示。
4. **指标与打包：**以完成率为门槛，随后比较同任务输入/输出/缓存 Token、请求数、修复轮、总耗时；把新 Keep 请求级 meter 与日志时间戳做阶段归因后才讨论 5C/5D。下次使用白名单打包并核验 ZIP 根 `main.py`、排除 `__pycache__`/`.pyc`、记录 ZIP SHA 与源码提交；不要把打包卫生视作本 Run 三项失败的已证实根因。无需 Octos/Cargo/API Key 的本地复现不等于平台 A/B 可省略身份校验。

## 10. Keep 定点复现完成后的决策与第二个 Agent 切片（2026-09-19）

### 10.1 证据、范围与反证

- 来源：用户提供的本地 `C:/Users/dayuruozhi/Doubao/chats/2026-09-19/new-chat-4/repro/REPRO-NOTES.md` 及 `evidence/`；生成应用输入 ZIP SHA-256 为 `9B46EC5C3D55FEDD1E986BC6733E05CFA8C95C76723EFF42B67C22CF8DE93EC4`，冻结官方 `helpers.ts` SHA-256 为 `42AE20F9D533C768E9A96A62F29FE8A36ED1C1CC366638671F4A07782D72C01A`。`final-32/full-regression.log` 为 `32 passed (25.2s)`、exit 0，`results.json` SHA-256 为 `4C5EEFF88849B6B43C82EFF9176FE5A1BB951E47BB97885FF40F8F25AF0DC868`。这是一份**修补生成应用后的重放**，不是 Agent 重跑，也没有 Agent Token/耗时收益数据。
- `P5-006`：只去掉 `showSnackbar` 第三参会修好 Undo，却使 `REQ-2.3.1` 的消息断言回归失败；正确产物修复是消息 `Note trashed` 和按钮名称 `Undo` 分离。`P5-007`：产物需同时修正归档前置状态及归档态按钮名称 `Unarchive`。`P5-008`：用每轮新 seed、MutationObserver/请求时间戳和 50ms 第二响应延迟重做对照，原版 3/3 失败、去重版 3/3 通过；本地最终失败是旧值提交，不能写成与平台完全相同的 Save-detach 超时。
- **评分后快照重放对照（原称“交付条件对照”，现纠偏）：**`template.zip` 内含 `backend/data/db.json`，该文件 SHA-256 `D12C995848309373ED506E5C36756A9896170A733F8B02505ED0167EE1B8CEE6`，目标 note 仍 `archived:true`。生成后端仅在 DB 文件不存在时写入 `DEFAULT_DB`，读取现成 DB 时以其内容覆盖默认值。在同一修复版 `app.js`/`server.js` 下，删除 DB 后重新 seed 为 `32/32`，保留原 ZIP 的 DB 为 **`24/32`**（1 worker、零重试、相同 32 项）。失败：`REQ-2.3.1/.2/.3`、`REQ-2.5.1/.3/.4`、`REQ-2.7.5`、`REQ-2.8.1`；该 DB 中对应删除 note 已 trashed、归档 note 已 archived、目标 note 已 pinned，标签 `Projects` 与静态 HTML 的 `Work editable` 不一致。实验副本与 trace 位于 `D:/Temp/arc-keep-packaged-db-278848bf91cd4be9830fe8ed350336f8/`，前后 DB SHA-256 分别为 `D12C995848309373ED506E5C36756A9896170A733F8B02505ED0167EE1B8CEE6` / `7861C2D628944F3C51079567C88A742219BAFD2D387BCD38225DECCD0A190C14`，Playwright exit 1。**这既不是平台成绩，也不是评分前交付态验证**；时间戳证明 ZIP 含最终评分写入，第 11 节说明其解释边界。
- Delete Note 菜单点击冒泡到卡片、意外打开编辑器是独立缺陷；最终四处产物修复**不含** `stopPropagation`。旧 Keep `0cef369cc925` 的同编号归档失败在 Unarchive 阶段，本 Run 在首次首页 hover 阶段，保持 `P5-002` 与 `P5-007` 分离。

### 10.2 方案选择、复用与代码边界

| 决策对象 | 已采用形式及代码位置 | 共性/特例边界；暂不采用的替代方案 |
|---|---|---|
| 名称与消息 | 在现有 `arc/main.py` 的 `UI_CONTRACT_CORE`、单节点 `CODEGEN_PROMPT` 和设计提示中要求精确可访问名称与动作消息分离；在 `arc/acceptance.py` 对实际 role/name 失败给出有界候选提示 | 通用定位契约；Keep 的 `Note trashed`/`Undo` 仅为产物回归样例，不写入 Agent 分支。参考 [Playwright 角色定位测试](https://github.com/microsoft/playwright/blob/07f1a6154795f055f341b8972086533e8e48b36f/tests/page/selectors-role.spec.ts#L434)。不统一放宽 locator 或延长超时。 |
| 初始数据与交付 | 在常驻 `UI_CONTRACT_CORE`（不受 `needs_data` 分类门控）、设计提示和 `FINAL_CHECK_PROMPT` 中要求首步目标处于可见初态，并从**包内原文件**检查持久数据；失败摘要仅在 hover + 文本目标的证据形态出现时提示核对 seed/视图过滤 | 通用 seed 生命周期约束；`seed-archive-254`、`Unarchive` 是 Keep 产物特例。暂不全局清库、自动重写所有 JSON 或另建静态 seed 扫描器；浏览器 context 隔离不等于后端 DB 隔离。 |
| 异步编辑稳定 | 把现有“加载后不重建控件”的宽泛语句收窄为“交互期间不替换焦点控件或重置草稿”；仅在 Playwright 报 detached/unstable 时追加并发读取、重绘候选提示 | 通用状态一致性规则；删第二次 `loadLabels()` 是 Keep 产物最小修复。暂不重写 `renderLabels`、引入 React/新状态库或把所有超时归为竞态。可借鉴 [stale fetch 响应失效的开源说明](https://github.com/reactjs/react.dev/blob/b011783fcc7a39da9eefd4274147a1444860a12b/src/content/learn/you-might-not-need-an-effect.md#L727)，不引入其依赖。 |
| 失败诊断入口 | 复用 `Flow.failure_diagnostics()` 和原有验收/修复循环；`interaction_failure_hints()` 最多输出三条、仅由失败消息触发，提示声明为假设而非判决 | 与 `P5-001` 路由提示共用摘要但按机制分开，不加模型调用、全局 trace、新验收器或默认等待。Playwright [actionability 规则](https://github.com/microsoft/playwright/blob/07f1a6154795f055f341b8972086533e8e48b36f/docs/src/actionability.md)说明 detached/timeout 不能直接诊断为“页面慢”。 |

候选分支 `codex/arc-bench-phase5-route-contract` 的本地提交为 `dddc94312d4cd26babdbfb9d7df2a17f08f0a51d`，改动 `arc/main.py`、`arc/acceptance.py`、`arc/tests/test_acceptance.py`、`arc/tests/test_main_helpers.py`、根 `CHANGELOG.md`；没有修改生成应用 ZIP、官方 spec、冻结 A0 或三个用户已有的未跟踪 ZIP。与 `P5-001/P5-003` 的关系是**同一入口上的小增量**，不是对路由提示的替代，也没有证明路由切片在 Keep 有收益。

### 10.3 验证、成本与下一门槛

- `python -m unittest tests.test_acceptance.ReportTests tests.test_main_helpers.InteractionDiagnosticsTests tests.test_main_helpers.InteractionPromptTests tests.test_main_helpers.RouteDiagnosticsTests tests.test_main_helpers.CodegenPromptTests`：10/10，exit 0；`git diff --check`：exit 0。
- `python -m unittest discover -s tests`：84 项，exit 1，仍是候选修改前相同的 3 fail + 1 error（Windows 路径表示、临时 Git 文件权限）；未把这四项算作本切片新增失败，也不能宣称全套绿灯。`python -m py_compile` 因本机 `__pycache__` 写入权限失败；单测已成功导入新代码，此错误不代表语法失败。
- **尚未完成：**平台评分前 DB 精确快照及启动/导出内部策略的确认；从该提交重新制作并核验 Agent ZIP 的源码 SHA/ZIP SHA；同任务同快照的 Smoke、Keep、BookStack 平台 A/B；请求级 meter 阶段归因。因此当前状态是“Agent 本地已验证、平台效果未知”，不能推断完成率、Token 或总耗时提升，也不推送远端。
- **重评/回退条件：**若通用提示在新 Run 误导修复或增加显著 Token/修复轮，则先移除相应提示而保留已证实的产物问题；评分后 DB 的重放失败不得直接触发清库或新补丁，应先取评分前状态/启动策略证据；若另一个 Run 出现同类编辑重绘，才考虑比去重更深的 stale-response/局部 DOM 更新方案。

## 11. `0aa6820e0b82` 平台启动与导出时序纠偏（2026-09-19）

- **证据源：**原始平台日志 `C:/Users/dayuruozhi/Downloads/闻悦源代码-首轮测试-keep-lite/arcbench-run-0aa6820e0b82-logs.json`、最终产物 `0aa6820e0b82-template.zip`，以及同目录旧 Run `0cef369cc925` 的日志/产物。均为只读核查；未启动新平台 Run，也未修改官方测试或生成产物。
- **平台可见顺序（UTC）：**runner 指向同一 `/workspace/template` 作为 `project_dir` 和 `output_dir`；Agent 的 `10:43:34` postflight 工作区目录清单已有 `template/backend/data/db.json`（只证明文件存在，未记录内容哈希）。Agent 于 `10:43:39` 退出，随后安装依赖、构建并于 `10:43:40` 启动 `template-app`，`10:43:44` 开始执行 32 项 Playwright，`10:44:31` 报 29/32，`10:44:38` 提交结束。可见日志没有 DB 重置记录；这提高了沿用现成 DB 的可能性，**不等于**证明内部没有未记录的复制、恢复或重置。
- **ZIP 已含评分写入（已确认）：**`seed-delete-231` 的 `updatedAt` 为 `10:43:47.140`、`seed-delete-232` 为 `10:43:47.673`、`seed-archive-251` 为 `10:43:59.857`、`seed-meeting-agenda-281` 为 `10:44:27.455`（均为 UTC），与正式测试期间对应删除、归档、固定动作吻合。另一个 Run `0cef369cc925` 的导出 DB 也有测试期间 `seed-delete-231` 的 `deletedAt=2026-09-18T16:35:14.338Z`。因此导出 `template.zip` 的 DB **不是评分前静态快照**，跨 Run 可重复观察。
- **`REQ-2.5.4` 能确定的范围：**导出 DB 中 `seed-archive-254` 仍 `archived:true`，其 `updatedAt=09:26:47.194 UTC`，早于最终评分；本题在首页第一次 hover 就失败，未执行会改变该 note 的归档动作；生成 `server.js` 的 `DEFAULT_DB` 也设为 `archived:true`。这些共同强力支持**评分时目标处于错误的归档前置状态**，但不区分平台直接沿用 Agent 退出前已有的 DB、重建自错误默认 seed，或恢复包含该状态的快照。不能把“平台必然直接使用最终下载 ZIP 的 DB”写成已证实事实。
- **`P5-008` 未解：**导出 DB 的 `label-work-editable` 为 `Projects`，没有可用更新时间；它可能由评分时 Save 的部分写入、Agent 内部测试或更早持久化造成。故此值不能证明评分前标签已是 `Projects`；本地 50ms 双 GET 竞态虽已受控复现，平台 Save-detach 的精确触发链仍待评分前快照或带时间戳 trace 证实。
- **决策影响：**保留 `32/32` 干净 seed 回归和 `24/32` 评分后快照重放这两项**不同实验**，撤回“`24/32` 证明候选包带旧 DB 开跑/只改默认 seed 不可交付”的推断；不据此追加清库、全局重写持久层或新 Agent 特例。已有通用 seed/可访问名称/交互稳定提示保持本地候选状态，平台收益仍待 A/B。
- **下一步与所需协助：**优先查平台能否导出 Agent 结束、Playwright 开始之间的 `backend/data/db.json` 快照或 runner 启动/导出文档；若不能，待用户授权下一次平台 Run 时，可让候选 Agent 在生成结束前只读记录 DB SHA-256、目标 fixture 的状态及文件存在性，并与评分后的 ZIP 和日志对照。诊断日志不应包含密钥或完整用户数据。当前无需 Octos、Cargo 或 API Key 做本地分析；精确平台内部策略需要平台侧证据，不靠猜测补齐。

## 12. V1 BookStack Lite `5669f7d1777c`（此前称首次修改版）：跨 Run 判别与下一实验（2026-09-20）

- **身份与指标：**阶段 3 [manifest](../evidence/arc-bench/runs/5669f7d1777c/manifest.json) 原按用户说明标为首次修改版；谱系短卡现将其归入 V1 `c53c333d5205fb98bf168c1f4fc670c0eec7432f` / ZIP `483BB260AB8DAC167059D21E0947DFFEA5495C16EA25510C01BA7DF5A4B2DB21`。Run 映射仍是用户 provenance，平台 build/task_snapshot 绑定未独立取证。平台 `32/34`、耗时 `12,739` 秒、1,275 请求、Provider total 32,806,346 Token、平台 32,806,461 Token、¥17.124841；内部全套 round 0 `33/34` → round 1 `34/34`，但 `REQ-5.6.1` 定点三轮始终 `0/1`。与 A0 `00c59e0762fb` 同为 `32/34` 但失败题不同，仍不得宣称阶段五功能或成本收益。
- **平台直接事实：**`REQ-5.6.1` 在 Save Book 后等待 `Book Created 5.6.1` 超时；`REQ-6.1.1` 在 Save Page 后已导航至 `/books/8`，仍等待 `Page Created 6.1.1` 超时。两项最终错误都固定为 `getByRole('heading', {name: ...}).first()`。最终生成 ZIP 中有 `Shelf 5.6.1`、关联的 `Book Created 5.6.1`，以及 `bookId=8` 的 `Page Created 6.1.1`；Page 的更新时间为正式平台测试期间，证明该次保存至少写入了持久层。Book 无同等时间字段，不能确定是内部验收还是最终测试写入。
- **新的共性候选 `P5-009`：**冻结官方 `helpers.ts` 的 `firstVisible()` 在逐个检查定位器的**当下**找不到可见目标时，固定返回列表首个 `heading`；后续 `expect(...).toBeVisible()` 只等该 heading，不会重新选择随后出现的 link。最终生成的 `injectShelfDetails()` 与 `injectBookPages()` 都把新实体名称放在 `<a>` 中，而非 heading；两个表单都在异步 `POST /api/...` 成功后才设置 `window.location.href`。这与两题在跳转完成前选中 heading、跳转后只有 link 的失败链相吻合，`REQ-6.1.1` 还有最终 URL 与评分时 DB 写入佐证。
- **受控复现更新（2026-09-20）：**`REPRO-NOTES.md`（SHA-256 `9B98634EAC3E4D73ADB4DDD50154BFB9C35BF5E356331809A3CA200CB35F5583`）在两个独立副本、每轮全新 seed 下验证：无延迟时 `REQ-6.1.1` 与 `REQ-5.6.1` 分别通过；仅对对应 POST 增加 150ms 延迟时两题各 3/3 失败，失败 locator 均为目标名称的 `heading`，而 GET HTML 中目标实体均为 `a.shelf-link` 且 DB 已写入。官方 spec/helpers 未修改，因此 `P5-009` 从 `strong_candidate` 升级为 `confirmed`，状态为 `repro_verified`。150ms 只是触发受控竞态的变量，不冒充平台真实延迟。
- **Evidence refresh 审计（2026-09-20）：**revision `5669f7d1777c-external-refresh-01`、handoff `5669f7d1777c-EC5A608BB104` 的新 manifest SHA-256 为 `EC5A608BB104C2A9B68249BF6B2B2094AEE107CD9DDA574F75892F6FF19B0BAD`，phase4-result SHA-256 为 `DD1EA3905B4A3BD40E544BAAE1D04A5FC5B41AF734379B3855CD285A57BACD6E`；刷新后的 summary/failure-details 未改变根因、证据缺口或阶段5建议。当时只作审计确认并保留 `repro_verified_approval_required_no_dispatch`；后续实现、上传 provenance 与当前 NO-GO 门禁见本节下一条和第 19 节，历史记录不删除。
- **与既有问题的边界：**旧 Lite BookStack `P5-001` 是声明的路由未接入主分发；此 Run 两题的名义路由、表单、POST/API、后端列表注入都存在，不应继续套用“缺路由”补丁。与 Keep `P5-006` 同属可访问语义，但 Keep 是按钮 `aria-label` 被覆盖；本项是保存后的结果页面角色和异步定位时序，属于**相关但不同机制**。候选 Agent 的通用精确角色/名称契约可能有帮助，但还没有本 Run 的阶段五收益证据。
- **纠偏阶段 4 建议：**[阶段 4 结果](../evidence/arc-bench/runs/5669f7d1777c/phase4-result.json) 提出把最终评测改为“不可变干净 DB”并把状态污染列为强候选。本阶段保留它作为待排除解释，**不把评分后 ZIP 的 DB 当成评分前快照，也不授权全局清库**；上一 Run 第 11 节已实证导出 DB 会含平台测试写入。前后构建不一致亦缺源码/dist 哈希，不能先按此修改 Agent。平台没有提供两题最终 DOM、响应体、请求 trace 或评分前 DB 哈希。
- **最小验证顺序：**在隔离副本使用同一冻结官方 spec：①先运行原版两题，记录点击 Save 前后时间、URL、POST 状态、重定向、返回 HTML、`heading` 与 `link` 可见性，并分别保存每次前后的 DB 哈希；②若目标数据已写入且结果页只呈现 link，则单变量把书/页卡片标题改为语义合理的 heading（可在其中保留 link），原样复跑两题；③两题通过后跑同一份 34 题、比较干净 seed 与预存 DB 两种**明确标记**的起点，防回归。若原版响应根本未含目标记录，再查写入/读取/构建边界；不要先增加超时、全局清库或改官方 helper。以上均为建议，**本次未执行本地复现或新平台 Run**。
- **实现决策门槛（本地阶段已满足）：**受控复现已确认生成应用结果角色/导航闭环问题；用户授权的最小、通用 Agent 切片已形成本地候选。建议复用现有 role/name 与异步稳定契约入口，不把 `h2`/`link` 产物修复硬编码进通用 Agent，也不修改官方 helper。上传 Agent ZIP SHA、平台 build、代码与 `task_snapshot_id` 的绑定仍须补齐，方可谈同条件平台 A/B；当前不声明平台收益。
- **本地实现候选与后续上传 provenance（2026-09-21）：**实现交接 `phase5-p5009-impl-20260921-d2fe4dbc` 提供候选树 `.worktrees/phase5-route-contract` 的提交 `d2fe4dbc7601242896b61b3a790a912732bc5d57`，改动 `arc/main.py`、`arc/acceptance.py`、`arc/tests/test_acceptance.py`、`arc/tests/test_main_helpers.py` 与 `CHANGELOG.md`。定向测试 `11/11`（exit 0）；全量 `85` 项为 `3 fail + 1 error`，交接报告称与既有 Windows 基线一致、未新增失败。实现交接当时记录“未跑平台、未上传、未推送”；后续决策卡报告 ZIP `FC83EA353975F908C9669380146856077647CA5A80CA5A9CE3EB9E45FA6E8820` 已由用户人工上传。上传事实目前只是用户 provenance，缺平台 build、Run ID 与 task snapshot/官方资产哈希绑定，故仍不是 `platform_verified`，也不能宣称平台收益。

## 13. Lite Keep `737b56972d5a` confirmed evidence revision：Run-local 根因已确认，等待实现授权（2026-09-20）

- **revision 与身份：**本 revision 的 intake key 为 `737b56972d5a:intake:BC8FE404B86B`，来源 handoff 为 `737b56972d5a-0BCD0657E978`。谱系短卡将此 Run 归入 V2 `dddc94312d4cd26babdbfb9d7df2a17f08f0a51d` / ZIP `984D818AE6736907925E9ECB3F95A09846F5F3F2203DED8F1960F7728C25BF38`；该 Run 映射仍是用户 provenance。`manifest.json` SHA-256 为 `0BCD0657E978B28B08A0C3F985A31D4D112164B907544B33201072876560883E`；增量 `phase4-result.json` SHA-256 为 `BC8FE404B86BE53C64434DE06F2294CF88C0CDC0DFE74CEBB260EC7B38C12119`；阶段 4 注册表为 `verified`、结果为 `complete`。旧 pilot revision 保留为历史记录。
- **平台与边界：**平台仍为 `30/32`、score `93.8`、`FAILED`；入口 `main.py`、测试目录 `/workspace/tests`、bundled fallback `0` 未变。新增证据闭合 runner → bundle DB/启动链路 → 生成源码/设计快照 → 评分前 DOM 的 Run-local 链条，因此两个失败机制从阶段 4 的候选升级为 `confirmed`。这不等于 Agent 构建、上传 ZIP、任务快照或平台 A/B 身份已确认。
- **`P5-010`｜Work editable seed 契约：**`loadDB()` 清空 labels 后，`seedDefaults()` 只重种 `Work` 与 `Reminders`；设计快照要求 `Work editable`，平台首步定位该标签输入框超时，故“生成应用初始数据未满足需求契约”在本 Run 内确认。它与 `P5-007` 同属 seed/前置数据契约家族，但不是同一 fixture 或归档操作，不把 `Work editable` 写成 `P5-007` 的平台复现。建议复用已有通用 seed 契约提示/验收入口，不写死 Keep 标签名；状态为 `approval_required`，不派发实现。
- **`P5-011`｜Reminders accessible-name 冲突：**评分前 DOM 同时存在 `#nav-reminders` 与 `data-label=Reminders` 按钮，二者 accessible name 均为 `Reminders`，直接解释 `REQ-2.7.6.3` strict-mode failure。它与 `P5-006` 同属可访问语义契约家族，但不是 Undo 名称被覆盖，而是两个控件名称不唯一；建议复用既有 role/name 诊断能力，不硬编码 Keep 导航名；状态为 `approval_required`，不派发实现。
- **转派与复现决策：**本 revision 标记 `needs_repro=false`；不再为这两个 Run-local 根因自动创建隔离复现卡。由于仍缺 `task_snapshot_id`、Agent build/code SHA、上传 Agent ZIP 到平台构建的独立绑定，当前不标 `platform_verified`，也不计算阶段 5 A/B 收益。最新决策把 `P5-010/P5-011` 保持为 `confirmed + approval_required + deferred`：不混入冻结 V3；待 V3 获得有效 Keep 业务结果后，若仍精确复现，再作为两个隔离的通用 V4 小切片裁决，不硬编码 `Work`/`Reminders`。
- **保留缺口：**外部补充证据的 notes 数量存在文字算术不一致，但不影响两个根因的闭合证据；平台总耗时仍不能拆分为 LLM、浏览器和测试阶段。身份缺口是平台 A/B 门禁，不否定本次 Run-local 根因确认。

## 14. Lite BookStack `4ef2cf139806`：条件接收，先做隔离复现（2026-09-20）

- **身份与边界：**manifest SHA-256 为 `F10B7A1DE23B83BF39B46F1CFD76140911C065F75E516CD74BA5685E7D68A5A0`；phase4-result SHA-256 为 `B0AA9FCEDC6719C9527432A2DB6AA6AA4383C978CC00EAB89AF38808527414E9`；result Markdown SHA-256 为 `619D344C89290588C94664EAB43756C9C3E58D4BD39062225DB5CA4B07BCEFE3`。handoff `4ef2cf139806-F10B7A1DE23B8`、Run/task/thread 字段一致，阶段4注册表为 `verified`。谱系短卡将此 Run 归入 V2 `dddc94312d4cd26babdbfb9d7df2a17f08f0a51d` / ZIP `984D818AE6736907925E9ECB3F95A09846F5F3F2203DED8F1960F7728C25BF38`；共享 submission 不足以完成平台绑定，故仍与 V1/A0 Run 分开保留。
- **平台事实：**平台最终 `31/34`、score `91.2`、`FAILED`；入口为 `main.py`，测试目录为 `/workspace/tests`，bundled fallback 为 `0`。失败为 `REQ-2.2` 登录后昵称、`REQ-6.3.1` 阅读页、`REQ-9.1` Recently Updated 导航后三个 heading locator 超时。内部全套为 `31/34 → 32/34 → 31/34`，三个 targeted 节点三轮均失败；不能把局部修复轮或 31 个通过项解释为稳定机制确认。
- **机制分叉：**`REQ-2.2` 的 authenticated nickname role/DOM 与 session readback 是独立候选；`REQ-6.3.1`/`REQ-9.1` 都涉及页面读回、recently-updated 链路和最终 DOM 暴露，但目前只有缺失 locator 与静态源码/DB 证据。它们与已 `repro_verified` 的 `P5-009` 保存后 link/heading 机制相关但未证实相同，不能合并；可变 DB/session 和 acceptance→package→platform 边界也可能是共同上游解释。
- **台账决策：**条件接收为 `conditional_needs_repro_deferred`，暂不分配新的 P5 问题 ID，也不实施三项机制。只有门禁闭合后的冻结 V3 再次出现相同题目/链路，才在 pristine 副本执行既定 request/DOM/DB 复现：保存 login cookie/GET `/`、页面链接/阅读页 GET、create/home/recently-updated 请求、响应体、DOM、trace 和前后 DB 哈希，并对比“干净状态”和“内部全套后状态”。复现结果返回台账后再按机制拆分 ID；不派发实现、不单独创建平台 Run。
- **门禁与缺口：**仍缺 `task_snapshot_id`、agent build/code SHA、上传 ZIP 到平台构建的绑定，以及三条失败的最终 DOM/trace/HAR/响应体/请求级证据。即使隔离复现成立，也不能声明平台 A/B 收益；修复前必须保留 31 个通过场景，并记录 source/dist/database/package 哈希。

## 15. Ticket-booking `1aac5ece078e`：成功基线登记（2026-09-21）

- **身份与证据：**submission `67a8e2ef92a4`；阶段 4 handoff `1aac5ece078e-E437B342477B`；阶段 4 Thread `01a0bf9e-d69b-7f63-a11b-e321298e4292`；registry `status=verified`。manifest SHA-256 为 `E437B342477B7987F1214CCB94E95F032A9AC7CB87D386F256217B7D1CD455DC`；phase4-result SHA-256 为 `A16419527D28163D65BDC948849C5D18B27406AA4BF339E92A9A2AA258527BFC`；result Markdown SHA-256 为 `EBDBACAF3D9AEE16A7649FBD2A0D6C6925DB56116DFC1D639E3662A47FB13758`。ACK、handoff、result 的 run/task/thread/manifest 字段一致，result `status=complete`。
- **成功事实：**平台最终 `PASSED`、score `100.0`、`10/10`；内部验收 round 0 同为 `10/10`；失败链与 root-cause candidates 均为空。入口 `main.py`、测试目录 `/workspace/tests`、bundled fallback `0`、明文 API Key 命中 `0` 均已核验。计量保留两种口径：2 requests、platform token `79,281`、provider total `37,107`、耗时 `231s`、费用 `¥0.484403`。
- **阶段 5 决策：**登记为 `passed_baseline_no_issue`，`needs_repro=false`；不创建 P5 问题、不派发 Agent 实现、不创建平台 Run、不上传、不修改官方测试。阶段 4 明确“无需最小复现”；未来比较必须使用新的 Run ID，不能把本次成功直接归因于某个未绑定的代码包或构建。
- **身份缺口与基线边界：**仍缺 `agent_build_id`、`code_sha`、`task_snapshot_id` 和 ZIP-to-build 绑定；规范化证据已确认 canonical 与根目录重复附件 SHA 一致，但这不替代平台执行构建绑定。缺口不影响本次 `10/10` 成功结果的基线登记，却阻止 `platform_verified` 身份结论和阶段五 A/B 收益声明。

## 16. Lite Agent A0/V1/V2/V3 版本谱系与临时对照分组（2026-09-21）

来源 handoff：`phase5-lite-lineage-ledger-20260921-v1`；补充 handoff：`phase5-lite-lineage-ledger-manifest-20260921-v1`；metrics 独立复核 ACK：`phase5-lite-lineage-metrics-20260921-v1`。实现线程报告已将四个冻结 ZIP 的 `main.py`/`acceptance.py` 规范化为 Git blob，并与对应提交精确匹配；本台账独立复核了四个完整提交 SHA 和四个 ZIP SHA-256。Run 映射由用户提供，平台尚未给出 build/task_snapshot→ZIP 绑定。

| 版本 | 代码提交 | Agent ZIP SHA-256 | 用户 provenance 的 Run 分组 | 当前判定 |
|---|---|---|---|---|
| A0 | `ea503546aad31b2e3b887235e3b35cc0a8b9cfe8` | `812AF3D15DE93CE2955C6F2A0DE7C6351D205B81E9FDF33F36FCD41387162EF0` | BookStack `00c59e0762fb`；Keep `0cef369cc925` | 本地 ZIP↔提交已核对；Run↔平台构建未独立绑定 |
| V1 `arc_first` | `c53c333d5205fb98bf168c1f4fc670c0eec7432f` | `483BB260AB8DAC167059D21E0947DFFEA5495C16EA25510C01BA7DF5A4B2DB21` | BookStack `5669f7d1777c`；Keep `0aa6820e0b82` | 本地 ZIP↔提交已核对；Run 映射为用户 provenance |
| V2 `arc_2rd` | `dddc94312d4cd26babdbfb9d7df2a17f08f0a51d` | `984D818AE6736907925E9ECB3F95A09846F5F3F2203DED8F1960F7728C25BF38` | BookStack `4ef2cf139806`；Keep `737b56972d5a` | 本地 ZIP↔提交已核对；Run 映射为用户 provenance |
| V3 | `d2fe4dbc7601242896b61b3a790a912732bc5d57` | `FC83EA353975F908C9669380146856077647CA5A80CA5A9CE3EB9E45FA6E8820` | BookStack `cca008377368`；Keep `bf5e742c15a4`（用户明确 provenance） | Run ID 已回传；两份 manifest 文件名均指向 `13173bb…` 候选包，故 V3 Run 分组成立但 ZIP/build 身份冲突未闭合；`cca` 无业务测试，`bf5` 仍隔离 |

**manifest 配置复核：**六个历史 Run 均为 `deepseek-v4-flash`、vision `deepseek-v4-flash-vision-exp`、reasoning `low`、acceptance workers `2`、test workers `1`、`main.py`、`/workspace/tests`、fallback `0`；BookStack 三版 budget 均为 `51,000`，Keep 三版均为 `48,000`。六个 `task_snapshot_id` 全为空，且仍无平台 build/code/ZIP→build 绑定。因此它们最多是**同 manifest 配置的描述性版本序列**，不是严格可比 A/B。

**临时对照规则：**BookStack 描述序列现为 `00c59e0762fb`（A0）→`5669f7d1777c`（V1）→`4ef2cf139806`（V2）→`cca008377368`（V3 用户 provenance）；Keep 为 `0cef369cc925`（A0）→`0aa6820e0b82`（V1）→`737b56972d5a`（V2）→`bf5e742c15a4`（V3 用户 provenance）。不同任务之间不计算 A/B；`cca` 未执行业务测试，`bf5` 的阶段 4 结果未通过身份校验，两者都不能提供 V3 业务 A/B。仍须补齐 task snapshot 或官方资产哈希、平台 build/code/ZIP 绑定及同口径指标，才能升级为严格可比 A/B 或 `platform_verified`。本卡不触发 Agent 实现、平台 Run、上传或旧主会话路由。

**发布基线与当前有效门禁：**Lite 发布功能基线继续使用 A0：BookStack `00c59e0762fb=32/34`、Keep `0cef369cc925=31/32`。V1 为 `32/34 + 29/32`，V2 为 `31/34 + 30/32`，均未在两任务上同时超过 A0；其 Token、费用或耗时变化不能覆盖功能回归。冻结 V3 必须同时与 A0 发布基线、V2 增量父版本及 V1 `P5-009` 机制样本比较；功能门槛未满足前，不比较效率指标，也不得用“失败集合换了一组”冒充修复。详见第 19 节。

## 17. Keep Lite `ff12a7ff45f8`：测试前认证/生成门禁（2026-09-21）

- **身份与持久证据：**submission `535d25f72007`；handoff `ff12a7ff45f8-D42FCA49784D`；阶段 4 Thread `01a0b57a-7a65-77d0-a08a-e202167e4f70`。manifest SHA-256 为 `D42FCA49784DCFF82C502474AA17A676C8C7028E048AD4196645ABC6B2942F6E`；handoff 为 `23517093C1A91CE802EFB3B77E7F707852025092E67D81187E01C95C3A9D4C7F`；ACK 为 `692D02F41091040D48CE599FEF7CCF73F419A28703461D190DDE9C5A50490BEA`；phase4-result JSON 为 `18EB3778B6C0AF563DAC53594938CC494456DD1F2FD5129D78EE431C7DC6B36E`；Markdown 为 `9DD0566C66720366CF2017E228E5292D405C45B59088BD3639D2C35DE8A0AEBE`。ACK/结果身份字段一致，两份结果均标记 `PHASE4_RESULT: complete`。
- **已确认失败链：**生成端模型探测连续返回脱敏的 HTTP `401 invalid_api_key`；四次 skeleton 尝试均 `tools=0`、`wrote=false`、`verified=false`，没有生成 `frontend/` 或 `backend/`；runner 随后以 `web template is incomplete: expected frontend/ and backend/ directories` 在测试前拒绝模板。应用服务和 Playwright 均未执行，因此平台 `FAILED / score 0 / 0/0` 不是业务测试结果。
- **责任边界：**已确认“发生认证失败并阻断生成”，未确认具体是密钥有效性、账号/模型权限、provider 路由、平台凭据绑定或临时状态。约 10 分钟的 21 次探测与后续四次 skeleton 重试支持“应评估有界重试/快速失败”的候选，但不能直接据此修改 Agent。日志无明文密钥命中；Token、请求数、provider totals 与费用均不可用，总耗时 `1,095s`。
- **阶段 5 决策：**新建 `P5-012`，状态 `needs_repro`，范围仅限：①分离模型 endpoint 与 meter 认证；②用确定性成功 mock/fixture 验证现有入口能写出并验证 `frontend/`、`backend/`；③注入确定性 401 测量重试次数、耗时和安全 fail-fast 边界。认证与 skeleton 产出未确认前，不实施 Keep 业务修复、不创建新平台 Run、不上传、不修改官方测试。
- **重开与交付门禁：**隔离复现须只记录状态码、错误类别和非秘密指标；若成功响应仍不能产出 skeleton，再定位 Agent 具体写入/验证路径。只有认证链路、skeleton 产出和有界重试均有证据后，才决定是否授权实现或新平台 Run。本 Run 永不用于推断 Keep 页面业务完成率。

## 18. BookStack Lite `d4acec5dbbdf`：测试前包形状/生成门禁（2026-09-21）

- **身份与持久证据：**submission `535d25f72007`；handoff `d4acec5dbbdf-686648028D9A`；阶段 4 Thread `01a0b582-3586-7bc1-875e-d4670592d5ba`。manifest SHA-256 为 `686648028D9A709FE16FAE29AAE4B4B188DCFF30230AAECB876A45DA7F9FAA05`；handoff 为 `844BC1BD79AAA671B735E7EFDF0A7264917DCDB1FEEF677A7812EA7A56E8333E`；ACK 为 `99D078EEDB7880B7B523C399225FDB51D6F1D7B5982DAE6CE7BFF74799D3A5A0`；phase4-result JSON 为 `7A8C8AF29377EB6168610D020E7517907602E916D80E03B46EE2B22AA1302C71`；Markdown 为 `E820C23F90286E9C918FC8D8147BC1403930E83D7AEF1F2CA4D48DF60D6300AA`。registry 已核验，ACK/结果身份字段一致，结果为 `complete`。
- **已确认失败链：**最终 `template.zip` SHA-256 为 `8841987DE1FF6942FEEF151B83B9C73B64D16725E1EE11D71E73A552228FCD10`，共 25 个条目；`frontend/`、`backend/`、`main.py`、`tests/` 的命中数均为 0。runner 以 `web template is incomplete: expected frontend/ and backend/ directories` 在业务测试前停止，`run_tests` 未到达、`tests[]` 为空，因此 `FAILED / score 0 / 0/0` 不是 BookStack 业务测试结果。
- **证据边界：**原始日志只有空的 `events=[]`、`stdout=[]`，页面数为 0；关于 `main.py`、`/workspace/tests`、bundled tests 或 API key 的摘要说法均未获原始记录支持，保持 `unverified`。当前只能确认最终包形状错误，不能确认遗漏发生于生成、workspace 写入、staging 复制、归档根层级还是上传绑定；不与任何既有 BookStack Run 或 `P5-009` 合并。
- **阶段 5 决策：**新建独立 `P5-013`，状态 `needs_repro`，范围仅限只读/受控的包链路诊断：①对精确 ZIP 执行 `frontend/`、`backend/`、`main.py`、`tests/` 根层级门禁；②分别冻结 workspace、staging 与最终 ZIP 清单及 stdout/stderr，定位首次缺失点；③以已知良好包运行同一形状门禁；④补齐平台 build/产物与 ZIP SHA 的绑定。当前不实施 BookStack 业务修复、不修改官方测试、不上传，也不创建新平台 Run。
- **计量与重开门禁：**平台总耗时 `1,096s`；请求数、Token、费用和修复轮次不可用。只有形状门禁能区分已知良好包与本包、且 workspace→staging→ZIP 的首个断点与 build→ZIP 身份均可审计后，才决定是否授权修复或新平台 Run。

## 19. 冻结 V3 的授权历史、指标门槛与当前 NO-GO（2026-09-21）

- **决策来源与时序：**handoff `phase5-v3-conditional-go-20260921-v1` 先记录“认证门禁通过后按 BookStack→Keep 顺序做同包同配置 A/B”；随后指标决策回交把生效门禁收紧为：P5-012 与 P5-013 的确定性复现、workspace→staging→ZIP 首个断点、平台 build→ZIP 和 task snapshot/官方资产哈希未闭合前，`no-go for business/platform benefit claim`，不再启动业务平台 Run。前者作为授权历史保留，后者是当前有效决策。
- **冻结产物与上传状态：**V3 固定为提交 `d2fe4dbc7601242896b61b3a790a912732bc5d57`、ZIP SHA-256 `FC83EA353975F908C9669380146856077647CA5A80CA5A9CE3EB9E45FA6E8820`；本地实现与 ZIP↔提交身份已核验，用户报告已人工上传。用户现明确回传 BookStack `cca008377368` 与 Keep `bf5e742c15a4` 为冻结 V3 Run ID，但两者都没有可用的 V3 业务结果，因此仍仅标 `user_reported_version_provenance / provisional`。
- **版本归属冲突：**两个 Run 共享 submission `0b90e43b07b7`，两份 manifest 的 `original_filename` 又都为 `octos-arc-bundle-13173bb50e55.zip`；该文件名对应台账中的 V3.1/V4 控制面候选，而不是冻结 V3 的本地 ZIP 名称/哈希。用户版本归属优先用于分组，机器记录优先用于保留冲突；在平台给出上传 ZIP SHA、build/code 绑定前，不把任一 Run 源码级归因给 `d2fe4dbc…` 或 `13173bb…`。
- **前置事件边界：**`ff12a7ff45f8` 与 `d4acec5dbbdf` 共享 submission `535d25f72007` 和相近时间窗口，可作为同一提交下的相关运维事件审计；两条证据链仍分别保留为 P5-012（401→skeleton 无产出）与 P5-013（最终产物形状缺失），不互相替代，不计业务完成率，不构成 V3 A/B，也不能独立证明运行了 V3 构建。
- **门禁闭合后的唯一运行顺序：**只重跑冻结 V3；先 BookStack，确认生成链正常且取得新 Run ID，再以同一 ZIP 和同配置跑 Lite Keep，也必须取得独立新 Run ID。两次 Run 都须回传 run/submission/build（如有）、上传文件名与时间、task snapshot 或官方资产哈希、完整配置、总通过数、首轮通过数、失败样本、请求数、输入/输出/缓存/推理 Token、Provider total、平台 Token、费用、耗时与修复轮次。缺 ZIP→build/task snapshot 独立绑定时只能记 `provisional/descriptive`。
- **功能裁决：**最终 `GO` 只接受 BookStack `34/34` 且 Keep `32/32`。若 BookStack 至少 `32/34`、Keep 至少 `31/32`，`P5-009` 的 `REQ-5.6.1`/`REQ-6.1.1` 已通过且没有任何新失败机制，只记“无回归候选”，阶段 5 仍未完成；任一任务低于各自 A0 基线即 `reject/reopen`。失败集合替换不得计为修复。Keep 只作为跨任务回归门禁；P5-010/P5-011 本轮继续 DEFER。
- **效率裁决：**严格比较同时保留 A0 发布基线、V2 `dddc9431…` 增量父版本和 V1 `5669f7d1777c` 的 P5-009 机制样本。只有功能门槛满足且失败集合不劣时，才依次比较请求、输入/输出/缓存/推理 Token、Provider total、平台 Token、费用、耗时和修复轮次；效率改善不能抵消功能回归。
- **本卡不授权：**不授权新的 Agent 或官方测试修改，不授权再次上传，不授权现在启动平台 Run，也不向旧主会话路由。下一动作仅是闭合 P5-012/P5-013 与平台身份门禁；达到门禁后再按上述冻结顺序重新裁决是否放行。

## 20. V3.1/V4 控制面切片与下一平台测试包（2026-09-21）

- **授权与问题绑定：**用户在第 19 节决策之后明确授权创建 V3.1/V4 修复切片，并要求交付下一次平台测试压缩包；本切片只处理 `P5-012` 永久鉴权/有界重试和 `P5-013` 包形状可审计性，不混入 `P5-009/P5-010/P5-011` 业务提示或官方测试改动。相关历史 handoff 为 `ff12a7ff45f8-D42FCA49784D` 与 `d4acec5dbbdf-686648028D9A`。
- **仓库与基线：**远程 `git@github.com:William-zwy/octos-p.git`；工作树 `D:\DataMove\codex\worktrees\9015\AI智能体软件工厂黑客松\.worktrees\phase5-route-contract`；分支 `codex/arc-bench-v4-control-plane-gates`，无上游；冻结父提交 `d2fe4dbc7601242896b61b3a790a912732bc5d57`。本轮未拉取合并、未推送远程。
- **V3.1 原子提交：**`7423bf2c1602598007feb71953b49dc11ef42adf`（`fix(arc): fail fast on permanent provider auth`），改动 `CHANGELOG.md`、`arc/main.py`、`arc/tests/test_main_helpers.py`。行为边界：401/403 或明确鉴权标记首次终止；429、5xx 和网络瞬态仅做可配置的有限次数重试；生成前永久失败返回 2，其他不可恢复探测失败返回 3；skeleton 首次永久鉴权拒绝即停，无可运行应用的致命失败不再返回 0。
- **V4 原子提交：**`21d7a3dd2d530ac0a78caf6ea28bcc1663399385`（`feat(arc): gate generated app package shape`），新增 `arc/package_shape.py`、正反夹具与 `arc/tests/test_package_shape.py`，修改 `arc/main.py`、`arc/pack.sh`、`arc/README.md` 和 `CHANGELOG.md`。生成应用合同只要求 ZIP/目录根层级 `frontend/`、`backend/`；`main.py/tests` 为观察字段，不误列为生成应用必需项。postflight 冻结 workspace 以及可选 staging/final ZIP 的清单、条目哈希和首个失败阶段；Agent 上传 ZIP 使用独立 `arc_agent_bundle_v1` 合同。
- **打包实跑修复提交链：**`7a5f68c7c3b530a1eb0789412beb500d9ae9be0a`（Python launcher fallback）、`9ec8e91fe4374ec3a737772a10dc1bf696cd85e3`（仓库根归档）、`23580b6d3bda953c0469cd773424cc2b1e3ef2bb`（Git Bash 路径转换）、`4d822362ea4d59f33e0a2337d98377df864c76b0`（非登录 Git Bash 工具路径）、`6b56c6d57d45845dba5a526f86f981739f8fcd6f`（可用 Python 探测）、`c5546e5a05bc6d377b8f3b21f43f2ca70ef9629e`（Python 自包含 SHA-256）、`13173bb50e556c78bcd9cfdcc25c5449eee37f65`（Windows `autocrlf` 下保持 Git blob 原字节）。这些提交只收敛 `arc/pack.sh` 与同一 `CHANGELOG.md` 记录，没有改变业务生成提示、官方 spec 或 V4 门禁合同。
- **验证记录：**`python -m unittest tests.test_main_helpers.TransientTests tests.test_main_helpers.EndpointProbeTests tests.test_main_helpers.SkeletonAuthenticationTests tests.test_main_helpers.EntrypointAuthenticationTests` 为 `9/9`、exit `0`；`python -B -m unittest tests.test_package_shape` 最终为 `8/8`、exit `0`；`python -B -m unittest discover -s tests` 为 `99` 项、`3 failures + 1 error`、exit `1`，失败仍是已知 Windows 基线：`PrivateInstallTests.test_should_keep_every_write_inside_the_private_root`、`ProtectedTreeTests.test_should_restore_changed_deleted_and_added_files`、`InlineSourcesTests.test_should_quote_small_files_and_omit_those_over_budget` 和 `WorktreeSnapshotTests.test_should_undo_test_run_mutations_but_keep_uncommitted_edits`，未新增失败；`git diff --check` 与 `bash -n arc/pack.sh` 均 exit `0`。
- **交付包身份与门禁：**最终 HEAD `13173bb50e556c78bcd9cfdcc25c5449eee37f65`；文件 `octos-arc-bundle-13173bb50e55.zip`，大小 `339060` 字节，SHA-256 `FDFA6090FDCCB18553ABEF07C6B5429AAB9B0979FB69A9A5D0053730A159EE1A`。同名 `.shape.json` 记录 `arc_agent_bundle_v1` 为 `ok=true`、508 个条目、条目清单 SHA-256 `D24FF569A0105AC5E960D3ACB1448C8D9B5BF685F999F2D86DE1CD3C2EB7DF6C`，必需项缺失数与不安全路径数均为 0，清单内归档 SHA 与独立 `Get-FileHash` 一致。另以 ZIP 中 `main.py`、`package_shape.py`、`acceptance.py` 对比 `git cat-file blob HEAD:arc/<file>`，三项均原字节相等；打包命令 `arc/pack.sh` exit `0`。
- **当前边界与下一步：**本轮没有平台上传、平台 Run、官方测试修改或远程推送。用户已明确把 `cca008377368` / `bf5e742c15a4` 归为冻结 V3，因此它们不构成 V3.1/V4 的已验证平台 Run；manifest 文件名冲突只保留为待绑定线索。该 ZIP 仍只是可用于下一次**受控生成/包链路测试**的候选；回传时须绑定上传时间、submission/build、task snapshot 或官方资产哈希、最终模板 ZIP、pipeline 清单、Run ID 与完整指标。旧 `d4acec5dbbdf` 缺少 workspace/staging 证据，因此其历史首断点继续为 `unknown`。

## 21. BookStack Lite `cca008377368`：`P5-012` 平台 fail-fast 观察（2026-09-21）

- **独立身份与持久证据：**submission `0b90e43b07b7`；handoff `cca008377368-A8540D0184BB`；阶段 4 Thread `01a0b582-3586-7bc1-875e-d4670592d5ba`。manifest SHA-256 为 `A8540D0184BBCB16249C7D09BA41DA0318705159DF9F2AF00F903C9217ACABA5`；ACK 后 handoff 为 `7BDBE0CE032CFF8F3221C1B89C6C309D4D2F59C111538663A98F5B290E750DD1`；ACK 为 `5BE3D30F845C6B5F37917D33506CE33E07F287DF5AB8D3EA9F83AB05F0963C9F`；phase4-result JSON 为 `B849B84CE5A73A5FCB403C92C1A25E4521CC97925556DF3E4BC9CBD3151640BE`，Markdown 为 `33A7C76FD61AE3FE563246DCD7D36E23A84DA3DBA870B200E4B762F70008ABE6`。身份字段均一致；本 Run 不与 `d4acec5dbbdf`、`ff12a7ff45f8` 或其他 BookStack Run 合并。
- **已确认链路：**环境预检通过后，平台执行 `python3 /workspace/submission/main.py … --output-dir /workspace/template`；生成探测记录 HTTP `401 permanent authentication failure; aborting before generation`，进程以 exit `2` 结束。`run_tests` 未到达、`tests[]` 为空、服务和 Playwright 未启动；平台 `FAILED / score 0 / 0/0` 不是业务结果。最终模板 ZIP SHA-256 `834117533A70FFA8A9D4B16FAF610D0E96CC2DDA35FB9115A1B46B786FDF547E`，23 个条目全部属于模板/依赖材料，没有生成应用树。
- **版本归属与机器证据冲突：**用户明确将本 Run 归入冻结 V3；manifest 原始上传文件名却为 `octos-arc-bundle-13173bb50e55.zip`，exit `2` 和永久认证 fail-fast 文案也与后续候选实现相符。两类证据分别保留：用户 provenance 决定版本分组，机器线索形成待解冲突。平台未提供上传 ZIP SHA、agent build、code SHA 或 ZIP→build 绑定，故既不能宣称 `d2fe4dbc…` 已获平台源码级验证，也不能反向宣称 `13173bb…` 已获验证或取得平台收益。
- **与 `P5-013` 的边界：**本 Run 的空模板发生在认证失败先行且 main.py 明确中止之后，是已知上游阻断的下游产物状态；它没有独立证明 workspace→staging→最终 ZIP 的打包缺陷。V4 的 workspace/staging/final-ZIP 清单和首坏阶段逻辑未被执行，也没有 pipeline manifest，故不重开或关闭 `P5-013`。
- **阶段 5 裁决：**登记为 `P5-012` 的独立复发/平台观察，`needs_repro=true`，但范围仅限环境/认证正路径：用获授权的脱敏 endpoint、账号/权限/provider 路由诊断确认 401 责任边界，再以已知有效认证运行同一精确包的 generation-only 流程并冻结 build/ZIP、输出树和 pipeline manifest。当前无需修改 Agent、业务代码、官方测试或打包器，也不在本台账创建或上传新 Run。
- **指标边界：**平台 run 对象耗时为 `0s`，时间戳推导 wall-clock 为 `7.331646s`；请求、Token、费用均缺失。与 `ff12a7ff45f8` 的 `1,095s` 仅能作为“本次快速终止”的描述性观察，因 submission、配置、provider 状态和计时口径未绑定，不构成严格 A/B，也不支持 Token、成本或平台收益结论。

## 22. V4.1 build provenance 修复、测试与打包交接（2026-09-21）

- **裁决与基线：**新增 handoff `phase5-p5005-build-provenance-v41-20260921-v1`，主问题为 `P5-005`，并覆盖 `P5-012` 的认证失败可诊断性；代码基线固定为 V4 候选 `13173bb50e556c78bcd9cfdcc25c5449eee37f65`。不修改冻结 V3 `d2fe4dbc7601242896b61b3a790a912732bc5d57`，不把既有两个冲突 Run 追认为任一源码构建。实现由“项目阶段5｜Agent 实现”Thread `01a0bd66-75bd-7801-97fc-b3d1e136c112` 承担，本会话只收敛决策与回收证据。
- **避免重复实现：**V3.1 已有 401/403 单次永久失败、429/5xx/网络错误有界重试及 fatal pre-generation 非零退出；V4 已有 workspace/staging/final ZIP 形状清单、首坏阶段定位、根层级 Agent 包契约及 Git blob 字节一致性。V4.1 不新增第二套认证策略、重试器、打包流水线或业务验收循环，只在既有入口补不可变身份并复用现有 manifest/shape 机制。
- **最小修改建议：**发布 ZIP 根目录加入机器可读 `agent-build.json`，至少记录 schema、完整 commit SHA、稳定的 payload/tree SHA-256、package contract 与由这些稳定字段派生的 build ID；不得在 ZIP 内嵌最终 ZIP SHA 造成自引用，也不得放入构建时间等破坏稳定身份的易变字段。打包完成后生成外部 release/provenance JSON、`.sha256` 与既有 `.shape.json`，把 build ID、最终 ZIP SHA、shape manifest SHA 和文件名绑定起来。最终包建议按 `octos-arc-agent-<commit12>-<zipsha12>.zip` 命名；文件名只是人类可见索引，验收仍以完整 SHA 为准。
- **运行时建议：**参数解析和输出目录初始化后、任何 provider/network probe 之前，输出单行、可解析且脱敏的 `ARC_AGENT_IDENTITY {...}`，并把同一身份复制到输出目录 `.arc/agent-build.json` 及既有 pipeline manifest。即使首个请求返回 401/403 并 exit `2`，身份文件也必须留存。可记录模型/配置指纹、credential source 名称与是否存在、脱敏 endpoint host/path 指纹、HTTP 状态和安全的 request ID；禁止记录 key、authorization header、请求/响应正文或由 key 长度猜测“密钥无效”。
- **实现测试建议：**①同一 commit/payload 产生同一 build ID，任一受管 payload 字节变化会改变 identity；②ZIP 根层级存在 `main.py` 与 `agent-build.json`，嵌入 identity、release sidecar、`.sha256`、`.shape.json` 四者相互一致，且无 wrapper、嵌套旧 ZIP、绝对/穿越路径、缓存、临时文件或秘密；③mock 401/403 时 identity 日志早于网络失败日志，仅一次 probe、exit `2`、无业务生成/骨架调用，失败输出仍含 identity；④mock 429/5xx/网络错误只做既有有界重试，成功后继续；⑤已知有效的 mock 正路径生成 `frontend/` 与 `backend/`，通过 package-shape gate，pipeline manifest 记录 build 与各阶段；⑥运行全部 `arc/tests`，新增失败为零，既有 Windows 基线失败须逐项对照而非笼统忽略。
- **受控复现建议：**复现会话只对实现线程交付的**精确 ZIP**做离线 401、403 与已知有效正路径；每轮记录完整 ZIP SHA/build ID、stdout/stderr、exit code、请求次数、耗时、输出树、`.arc/agent-build.json` 和 pipeline manifest。不得改官方 spec/helpers，不使用或打印真实密钥，不启动平台 Run；若精确产物尚未交付，则保持 `waiting_for_implementation_artifact`。
- **A/B 验收建议：**指标会话把“可比较”的最低条件定义为精确 build ID + 上传 ZIP SHA + submission/build/Run 绑定 + 同一 task snapshot 或官方资产哈希 + 相同模型、推理、预算、workers 与测试来源。`0/0` 继续排除在业务完成率之外；401 fail-fast 只单列请求数与终止时延，缺 Token/费用时不得宣称成本收益。业务 GO 仍要求认证后真实生成与 BookStack `34/34`、Keep `32/32`；A0 的 `32/34`、`31/32` 至多作为 no-regression 参照，不能替代最终 GO。
- **实现回交门槛：**实现会话必须回传完整提交 SHA、分支/基线、改动文件、逐条验证命令与退出码、已知基线失败对照、最终 ZIP 的绝对路径/字节数/完整 SHA-256、build ID、release/shape sidecar 路径及未改官方测试声明。未拿到这些字段，不进入平台上传建议；本次授权不包含本会话上传 ZIP、创建平台 Run、推送远程或修改官方测试。
- **实现回交与独立核验（2026-09-21）：**实现线程在隔离分支 `codex/arc-bench-v41-build-provenance` 从精确父提交 `13173bb50e556c78bcd9cfdcc25c5449eee37f65` 形成提交 `bb70542d7d327b660fa672bfdbc193f3f51b40a5`（`feat(arc): bind releases to build identity`），工作树干净、无 upstream、未 push。改动 10 个文件：`.gitignore`、`CHANGELOG.md`、`arc/README.md`、`arc/build_identity.py`、`arc/main.py`、`arc/pack.sh`、`arc/package_shape.py` 及三份对应测试；本台账用 Git 路径差异复核 `arc/public-tests`、spec/helpers 为零差异。定向 20/20、shell 语法、模块导入、打包、identity inspect、shape gate 与 diff/status 检查均 exit `0`；全量从 100 项增至 106 项，仍为同一组 Windows 基线 `3 fail + 1 error`、新增失败为零。首个从仓库根运行导致 7 个收集错误和首个 PATH 缺 `sh` 的命令均已在正确 cwd/绝对 Git sh 下纠正，不把误用命令计为产品回归。
- **精确产物：**`octos-arc-agent-bb70542d7d32-680ba38f027f.zip`，343,822 字节，SHA-256 `680BA38F027F5CF5E60641362D041B791E952771171D3C7F4CAF85794F186783`；build ID `arc-agent-v1-0851fff1cfb8feeb38544f8c`，payload tree SHA-256 `B286699D96E3463AC6C8B8C426600BEF01DB7A9A0B43191AE99DFCB32A99C885`。release JSON SHA-256 `24C211FA113A4D18FF0F3AE6949503C4CFC6390670E96508FB1A6711E3B1538F`，shape JSON SHA-256 `FB5E9EA59FCE23FBF563865F232C9D008893B03932379A5DF3D54341D7CBD76C`；checksum sidecar 内容与 ZIP 完整 SHA 一致。本台账独立运行 identity inspect/agent shape 均 exit `0`：510 entries、required root 全部存在、unsafe/duplicate/forbidden/secret 命中均为 0。该结果只升级为 `local_verified_artifact_ready`，不构成平台身份或业务验收；精确包已派给复现线程执行 401、403 和 known-good 离线正路径。
