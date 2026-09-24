# ARC-Bench 近期 Run 与阶段 3/4/5 队友协作交接

> 更新时间：2026-09-24（Asia/Shanghai）
>
> 适用范围：近期 Lite BookStack / Lite Keep 平台 Run、本地隔离复现、阶段五 Agent 候选与验收门禁
>
> 权威原则：平台最终 run/test 事实优先；阶段 3 负责证据归一化，阶段 4 负责单 Run 只读诊断，阶段 5 才能做跨 Run 决策。聊天摘要只作导航，不代替文件证据。

## 1. 给新队友的结论

目前不是“再加一点 timeout 就能全过”的状态。近期失败至少包含四类不同机制：

1. **异步动作后的可访问语义与测试契约不一致。** 创建成功后实体名称只作为 link 或普通文本出现；官方 helper 可能在动作完成前固定到 heading fallback，随后只等待永不存在的 heading。`d9a97cb4c92d` 的 `REQ-4.3.1`、`REQ-6.1.1` 已通过隔离复现确认。
2. **确定性的服务端模板/路由缺陷。** `4bab82404c52` 的保存页面与保存草稿并非单纯 locator 问题：一个模板占位符未全局替换，另一个静态子路由被通用 `:pageId` 路由遮蔽，最终均落到 404 JSON。
3. **生成/验收 harness 本身也会失败。** `6d41952769f7` 内部 full-suite 的 `0/34` 是无效 `trace.snapshots` 配置导致，不能当成应用 34 项全失败；本地 e04 的 `13/34` 又混入 implement 请求上限和 API 429，不能当成 `P5-017` 的平台成绩。
4. **平台身份链仍不完整。** 多个 Run 缺 `task_snapshot_id`、平台上传 ZIP SHA、platform build/code SHA 或 ZIP→build 绑定。即使文件名、用户提供 ZIP 或运行时自报 identity 一致，也不能反向构成严格 A/B。

当前阶段五裁决：

- `REQ-4.3.1`、`REQ-6.1.1`：`confirmed`，可进入**待用户授权**的一个“通用创建后结果语义契约”最小 Agent 切片。
- `REQ-8.1`：`strong_candidate / timing_sensitive`，**不得**并入上述切片；先闭合平台评分前 seed 与多轮时序证据。
- `4bab82404c52` 的模板占位符与草稿路由：隔离复现已确认，但目前只证明该次生成应用的具体缺陷；是否转换为通用 Agent 提示、repair 诊断或生成后静态门禁，需要另立最小切片和授权。
- `32e08aaca2e4`、`88c08161c4d3`：阶段 4 尚未形成完整可核验结论，阶段 5不得越级归因或直接改 Keep。
- 当前 `business_go=false`、`strict_ab_comparable=false`；本文件不授权改 Agent、不授权上传、不授权新平台 Run。

## 2. 近期平台 Run 总表

| Run | 阶段/身份 | 任务 | 平台结果 | 主要失败 | 当前判定 |
|---|---|---|---:|---|---|
| `1b0eaf914e94` | 阶段 3/4 完成；运行时 V4.1 identity | BookStack | 33/34，97.1 | `REQ-2.2` 登录后昵称 heading | 已本地复现为昵称文本可见但非 heading，并形成 Agent 候选；新 Agent 端到端生成效果仍未证明 |
| `88c08161c4d3` | 阶段 3 `needs_reconciliation` | Keep | 30/32，93.8 | `REQ-2.4`、`REQ-2.7.6.3` | 阶段 4缺失；不得并入旧 Keep 根因 |
| `4bab82404c52` | 阶段 3/4 完成；运行时为 `7f3c0b...` 候选 | BookStack | 31/34，91.2 | `REQ-6.1.1`、`6.1.2`、`9.1` | 隔离复现确认两个独立服务端缺陷；平台成绩较 33/34 回退，但不是单一语义回归 |
| `6d41952769f7` | `P5-015`，阶段 3/4 完成；运行时自报 `adfe398...` | BookStack | 30/34，88.2 | `6.1.1`、`6.2.1`、`7.2`、`8.1` | 三项 UI 语义为 strong candidate；`7.2` 未闭合；内部 `0/34` 已确认是 harness 配置错误 |
| `d9a97cb4c92d` | `P5-017`，阶段 3/4 + 部分阶段 5复现 | BookStack | 31/34，91.2 | `4.3.1`、`6.1.1`、`8.1` | 前两项 confirmed；收藏项继续第二阶段隔离 |
| `32e08aaca2e4` | 阶段 3完成、阶段 4待处理 | Keep | 27/32，84.4 | `2.4`、`2.7.1`、`2.7.2`、`2.7.5`、`2.7.6.3` | 最新 Keep 明显低于既有 no-regression floor；因身份/日志缺口和阶段 4未完成，暂不归因 |

### 2.1 不可混用的本地实验

`D:/DataMove/arcbench-local/p5-014-e04/` 的本地 BookStack e04 运行得到 `13/34`，但同时存在：

- 生成应用缺 `POST /login` 等质量问题；
- `OCTOS_ARC_IMPLEMENT_REQUESTS=20` 导致 17 个节点约 250–310 秒被截断；
- 后 12 节点发生 `429 insufficient_quota`；
- skill 记录为 427 requests / 15.73M tokens，而 meter 网关全量为 1,671 requests / 57.88M tokens / 约 24.98 CNY。

它只能用于诊断本地运行资源、请求上限和日志计量口径，不能替代任何平台 Run，也不能作为 `d9a97cb4c92d / P5-017` 的本地 A/B。

## 3. 各 Run 阶段 3→4→5 卡片

### 3.1 `1b0eaf914e94`：33/34 登录身份语义

- submission：`0cb0a4198304`
- 平台运行时 identity：commit `bb70542d7d327b660fa672bfdbc193f3f51b40a5`；build `arc-agent-v1-0851fff1cfb8feeb38544f8c`；payload `B286699D96E3463AC6C8B8C426600BEF01DB7A9A0B43191AE99DFCB32A99C885`
- 阶段 3 manifest：`evidence/arc-bench/runs/1b0eaf914e94/manifest.json`，SHA-256 `73C71551ABB524B5123D8D0DBCFDAAC9DDF4B4E7A103BA463A732F4DCE143437`
- 阶段 4结果：`phase4-result.json`，SHA-256 `0F274A22C861EC57F5AA43A4787F9261F75AD6DC22DF97175D7550EF5DC57C87`
- 平台：33/34，唯一失败 `REQ-2.2`；42,725,779 平台 Token，¥22.194327，8,548 秒。
- 隔离复现：登录 API 200、session cookie 往返正常、最终 `/` 显示 `span.nav-user` 的 `BookStack User`；`getByText` 可见、heading 为 0。冻结 helper 在异步导航前可能固定 heading fallback。
- 隔离证据索引：`D:/DataMove/codex/visualizations/2026/09/20/01a0bd66-60c2-7441-9a85-332c0af24886/phase5-p5014-1b0eaf914e94/summary-v2.json`，SHA-256 `E8B01648EF202A3D5CEFC0128CB754009836623566B92107AFC5CB0519D02FA6`。
- 已实现但未完成端到端证明的 Agent 候选：commit `7f3c0b0c0175701eb8ef6f19776885c521da5e9f`；ZIP `octos-arc-agent-7f3c0b0c0175-95a414940f5b.zip`；SHA-256 `95A414940F5BC69DF4A9ED7EC497A3BBFFDB14697714F8F123A1AEAA03A17D99`。
- 风险：手工修旧模板通过不等于新 Agent 能稳定生成正确实现；需要新 Agent 非 mock 生成 + 冻结 `REQ-2.2` + 完整 34 题。

### 3.2 `88c08161c4d3`：Keep 30/32，尚未完成阶段 4

- 与 `1b0eaf914e94` 同 submission `0cb0a4198304`，运行时 identity 同为 `bb70542...`，但平台上传 ZIP SHA 与 task snapshot 仍缺。
- 阶段 3 manifest：`evidence/arc-bench/runs/88c08161c4d3/manifest.json`，SHA-256 `BF786C6896EABBDE3F6F9AEE00E555E0924F149BC137C5A2CB3FF0EAA8FDE437`。
- 平台：30/32，失败 `REQ-2.4 Update Note`、`REQ-2.7.6.3 View Reminders`；40,784,030 平台 Token，¥21.356714，8,370 秒。
- 当前状态：`normalized_intake_complete_needs_reconciliation`，没有可核验 `phase4-result.json`。
- 下一动作：必须在唯一 Keep 阶段 4会话完成 handoff/ACK/result 身份闭合，才能进入阶段 5。不得把这两题直接并入旧 `P5-010/P5-011`。

### 3.3 `4bab82404c52`：31/34，隔离复现确认两个后端缺陷

- submission：`7e0bd4dc8e9d`
- 平台运行时 identity：commit `7f3c0b0c0175701eb8ef6f19776885c521da5e9f`；build `arc-agent-v1-3dcd295fd6e1435e09ccc9b7`；payload `760278BF0707784260EECBEE64C143B553794157A1E3CD45754DA1113029FF15`
- 阶段 3 manifest：`evidence/arc-bench/runs/4bab82404c52/manifest.json`，SHA-256 `67C3A1BC3B312DABB0A1E858C6077F826BBC541770B632159A236CC3544DD1A1`
- 阶段 4结果 SHA-256：`619DB204238400CB27985286F5A3E10FBD427E17EFE076C3D115236C272E921D`
- 平台：31/34；失败 `REQ-6.1.1`、`REQ-6.1.2`、`REQ-9.1`；37,625,229 平台 Token，¥18.351171，9,817 秒。
- 隔离报告：`C:/Users/dayuruozhi/Doubao/chats/2026-09-22/new-chat-3/isolation-4bab82404c52/REPORT.md`，SHA-256 `4DF24B7EE6B4E60AC679F703D9D53C3D689D6470F358CDA9C9033F705A6D18A6`。
- 证据清单 SHA-256：`C4FF507531504DF01D868E52C750C1251AF79F042A990885062B888639F71536`。

已确认：

1. `REQ-6.1.1` 与 `REQ-9.1`：`{{PAGE_ACTION}}` 在模板出现两次，但服务端只用单次 `.replace()`；按钮残留字面占位符，最终 POST 到 `%7B%7BPAGE_ACTION%7D%7D`，404、无写入。
2. `REQ-6.1.2`：通用 `/books/:book/pages/:pageId` 路由先于 `/books/:book/pages/drafts`，把 `drafts` 当 pageId，匿名和有效 session 均 404、无写入。
3. trace OFF/ON 行为相同，认证不是 RC-2 原因；早期 `ERR_ABORTED` 只是不可靠观测时序，不作为最终证据。
4. 两处最小生成应用补丁后，三个对应场景 3/3 通过；这证明修复充分性，但不是 Agent 已修复。

注意证据口径：Playwright `response.headers()` 不适合作为 `Set-Cookie` 判据，`request.headers()` 也不适合作为浏览器 Cookie 发送判据；认证证据来自 cookie jar、登录后 `Sign out` 和独立有效 session 直连探针。

### 3.4 `6d41952769f7 / P5-015`：30/34，应用失败与 harness 失败并存

- submission：`14111688f13e`
- 阶段 3 manifest SHA-256：`EDF238B1AA31ECE8A746931980DF5DDB0B66312A0AAF5B1DC7C5EC23D9AF694E`
- 阶段 4结果 SHA-256：`622FECA25C09FF3E5DABF8E7FD7216D27643C7EDCB843C67A8813E3E0CC0B70F`
- 运行时自报：commit `adfe39832dd3d3098efd0a585cd2857f3ca7bc29`；build `arc-agent-v1-9d7c83b9ce8e3c381db3a3a9`；payload `09723C6BAF032F94A50DDA670523899A3BBC06908EB8FD8A59B53B49183C3DAA`。这不是平台上传收据。
- 平台：30/34；失败 `REQ-6.1.1`、`REQ-6.2.1`、`REQ-7.2`、`REQ-8.1`；89,254,641 平台 Token，2,402 requests，¥36.969671，18,827 秒。
- `REQ-6.1.1`、`6.2.1`、`8.1` 静态上支持 link/button 与 heading 契约不一致，但该 Run 本身缺最终 DOM/网络，阶段 4只列 strong candidate。
- `REQ-7.2` 是 `page.goto('/') net::ERR_ABORTED`，后续用例仍通过，不能直接写成服务器永久崩溃。
- 内部 acceptance full-suite `0/34` 的直接原因已确认是无效 `trace.snapshots` 对象配置；Playwright 1.63.0 要求 boolean。它是 harness 配置错误，不是应用完成率。
- 教训：内部 acceptance、最终平台测试和手工 summary 必须分层；有冲突时以最终 run JSON/Playwright 为平台完成率权威。

### 3.5 `d9a97cb4c92d / P5-017`：31/34，阶段五部分确认

- submission：`0faa01c52d4a`
- 阶段 3 manifest：`evidence/arc-bench/runs/d9a97cb4c92d/manifest.json`，SHA-256 `955B36FF6BA46192010C247652D41D345D6669EF38D30AAD96C20D1A0BCA21CA`
- 阶段 4结果：SHA-256 `C1A4BC5956A4B67EC4AE00944133ED5CE10918ED6E4CE51D401C883BB23175AF`
- 平台：31/34；失败 `REQ-4.3.1`、`REQ-6.1.1`、`REQ-8.1`；56,757,262 平台 Token，¥29.912722，12,207 秒。
- 用户提供候选 Agent ZIP SHA-256：`5871FB40AFB203A4554F0620FE6FBA9C7C3E3FD2D4AC62313F725F7FF4661655`；平台没有绑定，不能作为严格上传身份。
- 候选模板 ZIP SHA-256：`389FBAC2F6511F2BD017CA37DC47E2E9027A43149A20F7A53932CBC3D27D7C50`。
- 隔离证据根：`C:/Users/dayuruozhi/Doubao/chats/2026-09-24/new-chat/repro/`。
- `evidence-manifest.json` SHA-256：`ED36A73F09F874216A838BF710C46555B00CF72BF2579C96274B07DD76FBFB98`，清单内逐文件 SHA 已复核通过。
- preflight 实际位于同级 `.../new-chat/preflight/`，不是 `repro/preflight/`。

逐题：

- `REQ-4.3.1 confirmed`：冻结 spec 2/2 同 heading locator 失败；`POST /api/shelves` 201、DB 变化、最终只有 `a.shelf-link`，无同名 heading。
- `REQ-6.1.1 confirmed`：冻结 spec 2/2 同 heading locator 失败；`POST /api/pages` 201、DB 变化、最终只有 `a.page-link`，无同名 heading。
- 两题创建接口的 response body 在导航后读取失败，正式口径只确认请求载荷、status、最终 DOM 与 DB，不声称拿到了 response body。
- 驱动 `result.json` 的 `exit_code=0/pass_replicated` 表示采证驱动完成，不能覆盖 `frozen-run-*.txt` 的失败。
- `REQ-8.1 strong_candidate/timing_sensitive`：手工设为未收藏后 API 200、DB 翻转、按钮变 `Unfavorite`/`aria-pressed=true`；冻结运行一过一失败。导出模板初始已收藏，但可能是评分后写入；手工改 seed 不能冒充平台初态。

第二阶段隔离 handoff：`d9a97cb4c92d:P5-017:repro-8.1-timing-v2`。要求先取得或标明无法取得评分前 seed，再用同 seed、Playwright 1.57.0、workers=1、fresh-copy 做至少 10 轮，记录 click、POST 200、DB 翻转、按钮 mutation 和 helper 选中 locator 的单调时钟。

### 3.6 `32e08aaca2e4`：Keep 27/32，阶段 4待完成

- 与 `d9a97cb4c92d` 同 submission `0faa01c52d4a` 和平台文件名 `octos-arc-agent-e04db1e40084-5871fb40afb2.zip`，但平台仍没有 ZIP SHA/build/task snapshot 绑定。
- 阶段 3 manifest SHA-256：`750C964566657B3126A6B40CE5AA4ACABD6839FEFD98DEEB5D6F543B05AD6996`。
- 平台：27/32；失败 `REQ-2.4`、`REQ-2.7.1`、`REQ-2.7.2`、`REQ-2.7.5`、`REQ-2.7.6.3`；42,677,341 平台 Token，¥23.569978，8,842 秒。
- raw logs 基本为空，model、预算、workers、请求数和 provider token 未获原始日志独立验证。
- 阶段 4尚无结果；当前只可判定低于 Keep A0 no-regression floor `31/32`，不能把五题归因于某个 Agent commit 或旧 Keep 机制。

## 4. 已解决、已纠正与尚未解决

### 4.1 已解决或已确认

- 平台 API 认证问题：此前 Agent 未启动的主要原因确为 API/凭证，用户已修复；后续测试已正常运行。该问题不应再触发 Agent 代码修复。
- V4.1 已具备 build identity、payload identity、package shape 和 401/403 fail-fast；但这些是控制面能力，不等于业务通过。
- `P5-014` 登录 API/session 本身本地成立，失败焦点收敛到昵称 heading 语义与异步 fallback。
- `4bab82404c52` 的 RC-1/RC-2 已确定性复现并由最小补丁对照闭环。
- `d9a97cb4c92d` 两个创建题已从 strong candidate 升级为 confirmed。
- `6d41952769f7` 的内部 `0/34` 已从“应用全面失败”纠正为 harness 配置错误。

### 4.2 当前关键卡点

1. **平台身份闭环缺失。** 最近多个 Run 没有 platform upload ZIP SHA、task snapshot、build/code SHA；严格 A/B 不能成立。
2. **`REQ-8.1` 的评分前 seed 未闭合。** 导出模板可能包含评分写入；必须区分 seed/lifecycle 问题和 helper timing race。
3. **Keep 阶段 4积压。** `88c08161c4d3` 需要 reconciliation，`32e08aaca2e4` 需要正式阶段 4；在此之前不派 Keep 实现。
4. **Agent 生成稳定性不足。** 修复一个语义提示后，后续 Run 可能生成新的服务端模板/路由错误；不能只围绕单一 locator 调提示。
5. **成本与时长很高。** 近期 BookStack 单次约 18–37 CNY、2.7–5.2 小时；未完成定点门禁前不应盲目重跑平台。
6. **权威工作区存在未提交阶段 3/4文件。** `9015` 当前有修改的 `phase4-thread-registry.json`，以及未跟踪的 `d9a97cb4c92d` manifest/handoff、`32e08aaca2e4` 目录和 skill-output。协作前必须由其原责任会话整理或明确交接；不得自动清理或一并提交。

## 5. 下一步工作流与所有权

| 顺序 | 所有者 | 动作 | 完成门槛 |
|---:|---|---|---|
| 1 | 阶段 3/4 Keep | 完成 `88c08161c4d3` reconciliation 与 `32e08aaca2e4` 单 Run 阶段 4 | handoff/ACK/result 顶层身份字段一致，失败边界和证据缺口明确 |
| 2 | 隔离复现 | 完成 `REQ-8.1` seed + 时序矩阵 | 同一闭合 seed 至少 10 个 fresh-copy；能区分 seed/lifecycle 与 timing race |
| 3 | 决策台账 | 接收上述结果并裁决 | 每题为 confirmed/strong_candidate/unknown/excluded；不混 Run、不跨阶段猜因果 |
| 4 | 用户 | 授权或拒绝代码切片 | 当前仅两个创建题具备待授权通用切片；收藏和 Keep 暂未获授权 |
| 5 | Agent 实现 | 若获授权，实施一个最小通用契约切片 | 单一共享规则、无 BookStack/REQ 字面量、无 timeout/轮数变更、代码与 CHANGELOG 同提交 |
| 6 | 指标与 A/B | 本地定点、34题、多任务 canary、身份核验 | 见下一节；任一功能回退 NO-GO |
| 7 | 用户/平台 | 另行授权上传和平台 Run | auth preflight 2xx；A/B 身份/配置/任务快照全部记录；新 Run 回阶段 3→4→5 |

## 6. 已冻结的未来实现与验收建议

### 6.1 允许评估的最小 Agent 切片

仅针对通用 `create/save` 成功反馈：持久化成功后，稳定目标页应把精确实体名作为唯一可见语义 heading，同时保留交互 link；优先结构为 `<hN><a>name</a></hN>`。规则应由一个共享常量进入 UI core、codegen 和 repair prompt；禁止 BookStack、Shelf、Page、Favorite 或 REQ 硬编码，禁止改官方 helper、全局 timeout、模型轮数或后端协议。

当前状态：`code_change_authorized=false`、`implementation_dispatched=false`。

### 6.2 本地验收

- 平台同版 Playwright `1.57.0`、workers=1、fresh DB。
- `REQ-4.3.1`、`REQ-6.1.1` 各连续 3/3；每次确认 POST 201、DB 恰增 1、刷新保留、URL 正确、同名文本节点=1/heading=1/link=1、无重复写入或 console error。
- 邻接集至少：`REQ-4.1`、`4.2.1`、`4.3.2`、`5.3.1`、`5.3.2`、`6.1.2`、`6.2.1`、`6.3.1`。
- BookStack 34 项 fresh DB 连跑 3轮：剔除未确认的 `REQ-8.1` 后，其余 33 项每轮 33/33；原先通过的 31 项不得新增失败。
- Keep、StackOverflow、PrestaShop、12306、Ctrip、ticket-booking 注册成功 canary，以及 counter/dice smoke/evolution 负对照必须通过。
- 新增提示不增加 LLM 请求/修复轮；每条 prompt 增量建议不超过 120 English tokens。

### 6.3 打包与平台 A/B

- 只从 clean worktree 构建，记录 branch/upstream/remote、完整 source SHA、运行时/lock hash、命令与退出码、ZIP 文件名/bytes/SHA-256/内容树与入口 hash；排除 tests/repro/trace/cache/secret。
- 闭合 `source SHA → package SHA → submission/build ID → run ID → task snapshot/spec/helper hash`。
- A 必须由基线完整 commit 洁净重包，B 只含共享契约差异；固定 task snapshot/template/seed/tests/helper/model/reasoning/visual/budget/workers/container/Playwright/startup。
- 严格结论至少 3 组配对 A/B 且交替顺序；单组只能 exploratory。上传和预算需另行授权。
- GO：B 的非 `REQ-8.1` 集合每次 33/33，两个 confirmed 题各 3/3；A 对两个题至少各复现 2/3，否则 inconclusive；B 零新失败、不增请求/轮次；B 配对中位 token/cost/wall time 不高于 A +10%，超过 +20% 为 NO-GO。
- 最终业务 GO 仍要求 BookStack `34/34`；`REQ-8.1` 未确认前从当前切片主效应归因中剔除。

## 7. 禁止事项与常见误判

- 不把 heading timeout 自动解释为后端写入失败；必须先查 HTTP、DB、最终 DOM。
- 不把静态源码“看起来有控件”当成运行时 DOM 证据。
- 不把内部 acceptance 轮、最终平台套件和手工 summary 混成一个分数。
- 不把用户提供 ZIP SHA 当成平台上传绑定；不以文件名代替 SHA/build/task snapshot。
- 不把导出 ZIP 中的 DB 状态自动当成评分前 seed；导出物可能含测试写入。
- 不改官方 tests/helper，不通过放宽 locator、增加 timeout 或清空 DB 来制造通过。
- 不在未确认前把 `REQ-8.1` 与创建后 heading 机制一起修改。
- 不把本地 e04 的 13/34、429 或 implement 截断归因给平台 `P5-017`。
- 不把本地通过写成平台收益；平台最终仍需新 Run 回流阶段 3/4。
- 不记录 API Key、Cookie、Authorization header 或生产数据；只记录脱敏状态、哈希和 request ID。

## 8. 证据入口

仓库内：

- 阶段五决策台账：`docs/ARC_BENCH_HACKATHON_PHASE5_DECISION_REGISTER.md`
- 项目记忆：`docs/ARC_BENCH_HACKATHON_PROJECT_MEMORY.md`
- 阶段五协同索引：`evidence/arc-bench/phase5-coordination.json`
- Run 证据：`evidence/arc-bench/runs/<run_id>/manifest.json`、`phase4-handoff.json`、`phase4-ack.json`、`phase4-result.json/.md`

外部只读证据：

- `4bab82404c52`：`C:/Users/dayuruozhi/Doubao/chats/2026-09-22/new-chat-3/isolation-4bab82404c52/`
- `d9a97cb4c92d`：`C:/Users/dayuruozhi/Doubao/chats/2026-09-24/new-chat/repro/` 与同级 `preflight/`
- `1b0eaf914e94`：`D:/DataMove/codex/visualizations/2026/09/20/01a0bd66-60c2-7441-9a85-332c0af24886/phase5-p5014-1b0eaf914e94/`
- 本地 e04：`D:/DataMove/arcbench-local/p5-014-e04/skill-output/local/bookstack-e04-01/`

## 9. 协作交接状态

- 决策会话：`项目阶段5｜跨 Run 决策台账`，Thread `01a0bd66-5680-7e72-9e8a-24290780525e`；只做证据、判断、台账与协同记录。
- 隔离复现：Thread `01a0bd66-60c2-7441-9a85-332c0af24886`；已接收 `REQ-8.1` 第二阶段 handoff。
- Agent 实现：Thread `01a0bd66-75bd-7801-97fc-b3d1e136c112`；当前没有新代码授权，不应空转派发。
- 指标与 A/B：Thread `01a0bd66-8b2a-7fb3-9a25-269204f6dbf1`；已回传本文件第 6 节门禁。
- 新平台 Run 必须先进入阶段 3；任何代码改动必须同时更新 `CHANGELOG.md`、决策台账、协同索引，并回传提交 SHA、验证命令/退出码和产物 SHA。
