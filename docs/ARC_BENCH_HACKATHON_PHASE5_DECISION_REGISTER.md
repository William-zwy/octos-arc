# ARC-Bench 阶段 5 跨 Run 问题与优化决策台账

> 版本：v1.3；建立日期：2026-09-19；状态：首个 5E 切片已本地验证并有用户指认的候选 ZIP/Keep 新 Run；BookStack 路由收益及 Keep 因果效果均**未**经可比平台 A/B 验证。
>
> 范围：阶段 3 归一化证据、阶段 4 单 Run 诊断进入阶段 5 后的跨 Run 归并、方案选择、实现盘点与 A/B 决策。本文件不是原始日志、阶段 3 manifest 或阶段 4 分析的替代品。
>
> 当前用户授权：已允许按首个 5E 建议做本地 Agent 修改；**未授权启动新平台 Run；暂不推送远程。**

## 1. 决策原则与证据口径

1. 决策顺序：功能完成率与回归可靠性优先；通过率相同才优先比较 Token，再比较耗时、请求数及修复轮数。遵循[完整执行计划](./ARC_BENCH_HACKATHON_EXECUTION_PLAN.md)。
2. 先按**失败机制**归并，再比较表面症状。同为 Playwright 十秒超时，不等于同一根因；同一 Run 内两个失败，也不自动等于已经跨 Run 验证的共性问题。
3. 证据等级：`confirmed` 表示原始结构化证据、生成代码或当前 Agent 代码直接支持；`strong_candidate` 表示多项证据一致但缺运行时链路确认；`unknown` 表示不能判断。机制的确认程度与其跨任务适用程度分别记录。
4. 来源优先级：平台 `run.json` 最终结果；原始日志、Playwright 产物、最终生成代码及 `.arc` 快照；阶段 3 manifest；阶段 4 分析；旧项目记忆。冲突须保留，不用推测填平。
5. 状态词严格区分：`现有`、`拟议`、`待证据`、`实施中`、`本地已验证`、`平台已验证`、`已回退`、`决定不改`。`本地已验证`须有实际代码、完整提交 SHA 和测试；`平台已验证`还须有构建 ID、上传 ZIP SHA、新 Run 及同条件 A/B。
6. 每次改动前重新核对当前代码与工作树；台账只是索引，不以文档中旧的“现有能力”替代代码检查。每个实现切片必须回答：服务哪个真实失败、改善哪个用户可见行为、由哪个测试证明，以及是否与已有机制重复或冲突。
7. 不复制原始日志、完整 snapshots 或密钥；按 `run_id` 引用阶段 3 manifest。优化版新 Run 必须先回阶段 3 冻结，再回阶段 4 诊断，最后更新本台账。

## 2. 本版证据范围与基线

本版纳入三个 Lite Run 和一个 Web BookStack Run。前两个 Lite Run 共享平台 submission ID `59debd594609`，但各自 manifest 尚未填入 `task_snapshot_id`，也缺少可核验的上传 Agent 构建/代码 SHA 绑定；**共享 submission ID 不足以单独证明构建、任务快照和配置均可比**。Web BookStack 的展示名同样指向冻结 A0，用户确认该次上传的是未修改且与远程一致的队友代码；其 manifest 仍缺独立的上传 ZIP SHA、`code_sha` 和 `task_snapshot_id`。新 Keep Run `0aa6820e0b82` 的上传 ZIP 由用户提供本地路径并与候选源码比对，但平台 manifest 未记录上传包哈希。各 Run 的 `template.zip` 是**生成应用快照**，不是上传的 Agent ZIP。

待纳入队列：[Web Keep `4b792b72d7dd`](../evidence/arc-bench/runs/4b792b72d7dd/manifest.json) 已有阶段 3 manifest（平台 `30/32`），但本台账尚未收到可复核的阶段 4 机制结论；暂不把它与 Lite Keep 的同名任务或本切片缺路由机制合并。

| Run 与原始证据索引 | 平台最终结果 / 内部验收 | 请求与计量 | 当前用途 |
|---|---|---|---|
| Keep Lite [`0cef369cc925`](../evidence/arc-bench/runs/0cef369cc925/manifest.json) | 平台 `31/32`、FAILED，`REQ-2.5.4 Unarchive` 十秒超时；内部 round 0 `31/32`（失败 `REQ-2.8.2`）→ round 1 `32/32` | 1,004 次；输入 24,772,611、输出 660,754、缓存命中 22,496,000、推理 436,764、Provider total 25,433,365、平台 Token 58,278,570；13,576 秒；¥31.453807 | 功能可靠性疑点及成本基线 |
| BookStack Lite [`00c59e0762fb`](../evidence/arc-bench/runs/00c59e0762fb/manifest.json) | 平台 `32/34`、FAILED，`REQ-4.5.1` 和 `REQ-6.1.3` 十秒超时；内部 round 0、round 1 均 `32/34`、同两题失败 | 1,324 次；输入 35,214,173、输出 681,758、缓存命中 32,267,264、推理 401,979、Provider total 35,895,931、平台 Token 60,951,255；14,338 秒；¥32.962032 | 已确认的功能缺陷及成本基线 |
| BookStack Web [`c31c51f2400b`](../evidence/arc-bench/runs/c31c51f2400b/manifest.json)（[阶段 4 结果](../evidence/arc-bench/runs/c31c51f2400b/phase4-result.md)） | 冻结 A0；平台 `34/34`、PASSED、score 100；内部 round 0 `34/34`，修复轮次 0 | 1,095 次；输入 27,791,179、输出 494,827、缓存命中 25,721,344、推理 243,817、Provider total 28,286,006、平台 Token 28,219,131；7,362 秒；¥13.216805 | 功能通过样本；仅评审效率与回归门槛，不立功能补丁 |
| Keep Lite [`0aa6820e0b82`](../evidence/arc-bench/runs/0aa6820e0b82/manifest.json)（[阶段 4 文稿](../evidence/arc-bench/runs/0aa6820e0b82/phase4-result.md)，交接已核验） | 候选 ZIP 用户指认；平台 `29/32`、FAILED：`REQ-2.3.2` Undo、`REQ-2.5.4` 归档前置、`REQ-2.7.5` Save 脱离 DOM；内部 round 0/1/2 均 `29/32` | 1,291 次；输入 34,395,140、输出 717,795、缓存命中 31,627,392、推理 444,073、Provider total 35,112,833、平台 Token 35,112,935；9,777 秒；¥17.926147 | 三种独立机制的诊断样本；**不是**已验证的候选收益/A-B |

缓存命中 Token 是输入 Token 的子集，推理 Token 通常包含在输出口径内，不能再加到 Provider total；平台 Token 与 Provider total 口径不同，不能互相替代。旧 Keep 的人工摘要曾将内部 round 0 写为 `26/32`，与原始日志 `31/32` 冲突；本台账按 manifest 的原始证据口径使用 `31/32`。四个 Run 均核验平台入口 `main.py` 和 `/workspace/tests`，没有 bundled tests 回退；这不能代替未来每次 Run 的独立核验。Web 与 Lite 虽同为 BookStack、测试数量也同为 34，但属不同赛道，不构成同任务、同快照的 A/B；不得直接比较费用或把 Web 的成功当作阶段 5 候选代码的收益。两个 Keep Lite 的 `REQ-2.5.4` 失败发生在**不同操作阶段**，不能仅凭相同编号归并。

## 3. 跨 Run 问题索引

| ID | 失败机制或决策问题 | 当前证据等级 / 适用范围 | 当前状态 | 优先级与依赖 |
|---|---|---|---|---|
| `P5-001` | 设计中声明的路由未接入生成应用主路由 | `confirmed`：BookStack 同一 Run 的两处漏接；**尚未跨 Run 确认** | 本地已验证；平台效果未验证 | P0；平台 A/B 前先确认身份 |
| `P5-002` | 状态写入与随即导航/读取可能竞态 | `strong_candidate`：Keep 一处；缺最终网络/DOM 时序 | 待证据，不修改 | P1；需 Keep trace 或等效复现 |
| `P5-003` | A0 超时摘要可能把缺路由误导成等待/性能问题 | A0 措辞 `confirmed`；对修复结果的因果影响 `unknown` | 已在 `P5-001` 同一切片本地修改；平台效果未验证 | P0，随 `P5-001` 一起 A/B |
| `P5-004` | 四个 Run 的请求、Token、耗时均可计量，但瓶颈来源未定位 | 指标 `confirmed`；根因 `unknown`；新 Keep 有请求级 meter 但缺阶段归因 | 暂缓 5C/5D 调参 | P2；功能率稳定且完成请求级归因后重开 |
| `P5-005` | A/B 的上传 Agent 构建、任务快照绑定不完整 | 四个 manifest 缺字段 `confirmed`；新 Keep 有用户指认的 ZIP 及本地源码比对，但无平台独立绑定 | 验证前门禁，不等于 Agent 功能修复 | P0；新候选复跑前处理 |
| `P5-006` | Undo 可访问名称被生成代码覆盖 | 生成应用代码及官方 locator `confirmed`；本机运行复现待做 | 拟议定点修复，不改 Agent 代码 | P0；优先本地验证 |
| `P5-007` | Keep 归档测试前置数据与生成应用 seed 不一致 | `DEFAULT_DB` 和最终 `db.json` 的目标 note 均已归档、官方先从首页归档：产物级 `confirmed`；平台启动状态未知 | 拟议定点修复，不盲目清库 | P0；先做 seed 对照 |
| `P5-008` | 重复加载标签与整表重绘导致 Save 脱离 | 重复调用/重绘 `confirmed`；具体 detach 时序 `strong_candidate` | 拟议定点修复，不改 Agent 代码 | P0；先保留失败 trace |

**当前跨 Run 结论：**多个 Lite Run 都有十秒超时且请求较多，但 Keep 的可访问名称、seed、DOM 重绘与 BookStack 的缺路由是不同机制。A0 Web BookStack 已 `34/34` 通过，说明漏路由不是所有 BookStack Run 的必然结果，却不能推翻 Lite 的具体漏接证据。禁止按“超时”这一表面标签做单一补丁。后续发现同一机制时，在对应 ID 下追加 Run 证据；机制不同则新建 ID，并记录关联而不强行合并。

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

- **已确认事实：**四份 manifest 的 `task_snapshot_id` 均为 `null`；缺少平台独立记录的上传 Agent ZIP SHA 和代码 SHA 绑定。Web BookStack 的 A0 身份有用户明确确认。新 Keep 的展示名仍为 A0，**不能据此断定上传了旧代码**：用户指认上传 `D:/DataMove/codex/worktrees/9015/AI智能体软件工厂黑客松/.worktrees/phase5-route-contract/arc/arc_first.zip`，本地 SHA-256 `483BB260AB8DAC167059D21E0947DFFEA5495C16EA25510C01BA7DF5A4B2DB21`，ZIP 内 `main.py`/`acceptance.py` 哈希与候选提交 `c53c333d5205fb98bf168c1f4fc670c0eec7432f` 源码一致。这证明本地 ZIP 的内容，不等于平台独立证明该 ZIP 被接收；生成应用 `template.zip` 的 SHA 不能充当上传 Agent ZIP 的 SHA。
- **当前决策：**此项是候选平台复跑前的证据门禁，不默认引发 Agent 主流程改造。先用现有上传、运行和官方快照材料补充/核验 build ID、代码 SHA、上传 ZIP SHA、任务快照或官方任务资产哈希及配置哈希；平台无法给出时记录不可比限制，不填猜测值。
- **重开条件：**现有记录无法完成绑定，且确认需在 `arc/metrics.py` 或运行清单中加入最小元数据输出时，再立项 5A 的窄切片。不要因此提前重构完整 TaskContext。

### `P5-006`｜Undo 的可访问名称与官方精确定位冲突

- **直接证据：**新 Keep 官方 `helpers.ts` 用 `getByRole('button', { name: /^Undo$/i })`。生成应用 `index.html` 的按钮文本和初始 `aria-label` 都是 `Undo`，但 `trashNote()` 在删除成功后调用 `showSnackbar('Note deleted', true, 'Note trashed')`，后者把按钮 `aria-label` 改成 `Note trashed`。按 [W3C 可访问名称规则](https://www.w3.org/WAI/ARIA/apg/practices/names-and-descriptions/)，显式标签优先于可见文本；即使按钮出现，官方精确 locator 也匹配不到。这比阶段 4 的“等待请求/ready”解释更直接。最终失败是否还有网络延迟，需要 trace 排除；不能仅凭静态证据声称运行时链路已完整证明。
- **最小方案：**先在隔离生成应用副本里让按钮的可访问名称保持 `Undo`，把 `Note trashed` 留在提示消息区；不改官方测试或扩大超时。验证默认状态、删除后、点击 Undo 后的角色/名称及功能回归。
- **Agent 方案形式：**若验证成立，优先复用现有 `arc/acceptance.py` 失败摘要，把“官方 role/name 与生成 DOM 的实际 accessible name 不一致”作为有证据、有限长度的修复提示；不新增 Keep 专用分支或第二套验收器。先证明这类提示能正确指导修复，再决定是否加入通用静态/浏览器检查。

### `P5-007`｜REQ-2.5.4 前置 seed 状态不满足测试契约

- **直接证据：**新 Keep 官方 `REQ-2.5.4` 是 `openHome → archiveNote('Travel plans 2.5.4') → openArchive → unarchiveNote`，失败发生在首个 `archiveNote` hover；生成应用 `renderNotes` 会过滤已归档 note。该生成包的 `backend/server.js` `DEFAULT_DB` 中 `seed-archive-254` 已为 `archived: true`，最终 `backend/data/db.json` 中也为 `true`。因此“只删或重建 `db.json`”会从同样不满足前置条件的 `DEFAULT_DB` 再生出错误状态；阶段 4 的清库建议**不能直接执行**。最终平台是否从此文件直接启动仍待平台构建/启动证据确认。
- **最小方案：**在隔离副本中分别保存原始 `db.json`、从 `DEFAULT_DB` 再生的 seed、仅把该目标 note 设为 `archived:false` 的实验变体，三者各跑一次单题，记录 `GET /api/notes` 响应与首次首页 DOM。原始和 DEFAULT_DB 均缺目标首页卡片、实验变体通过，才支持前置 seed 是主因；若实验变体仍失败，再查网络/渲染时序。不要覆盖官方快照、原始 ZIP 或其他 fixture。
- **Agent 方案形式：**优先让现有逐节点验收/修复回路携带“测试动作要求的初始数据状态”及失败首步，而不是写死 note 名称或全局清库。仅在跨 Run 反复出现相同 fixture 漂移且现有摘要不足时，考虑小型通用 seed 合同检查。旧 Keep `0cef369cc925` 在 **Unarchive 按钮**处失败，保留为 `P5-002`，不并入本项。

### `P5-008`｜标签重复加载与编辑行重绘

- **直接证据：**新 Keep 生成前端 Edit labels 点击处理器连续调用两次 `loadLabels()`；每个响应都调用 `renderLabels()`，把 `labelsList.innerHTML` 清空重建。官方测试填入 `Work editable → Projects` 后点击 Save，平台报告按钮先解析成功，后因不稳定并从 DOM 脱离而失败。代码中的重复请求和重建已确认；第二个响应是否恰在点击期间触发，尚缺 trace/DOM mutation 时间戳。
- **最小方案：**隔离副本中先只去掉重复调用，复跑本题；若仍不稳定，再以请求序号丢弃过期响应或在编辑期间保留当前行，优先避免重复拉取和 DOM 替换。必须回归标签创建、删除、重命名；不引入 React 或新状态管理依赖。
- **Agent 方案形式：**复用现有 Playwright call log 摘要，针对“resolved but detached”给出检查并发请求/整表重绘的**候选**提示；只有 trace 证明后才加更窄的自动检测。不要因为所有失败都叫 timeout 而统一加等待。

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
| Keep 的具体生成代码补丁 | 旧 Keep `P5-002` 仍待证据；新 Keep `P5-006/007/008` 可先在**隔离生成应用副本**做最小对照，不把快照补丁当作永久 Agent 修改 | 三项本地复现、阶段 4 交接校验、可比平台 Run |
| 新 Keep 一律清库/全局等待/重写前端 | 决定不采用；`DEFAULT_DB` 自身就有错误归档前置状态，Undo 是名称契约，Save 是 DOM 替换候选；全局手段可能掩盖或制造新问题 | 有新的直接证据表明这些动作必要且不伤其他 fixture |
| 为 Keep 引入 React、TanStack 或新验收循环 | 暂不修改；现有前端为原生 JS、Agent 已有验收/摘要循环，增加依赖或并行机制会放大维护成本 | 最小现有路径无法解决且有多 Run 复现 |
| 上传 ZIP 打包卫生 | 下次候选建议使用现有 [`arc/pack.sh`](../arc/pack.sh) 的白名单；`arc_first.zip` 根目录正确但含额外脚本、文档、缓存目录和 7 个 `.pyc`；**没有证据证明这些造成 Keep 失败** | 下次打包前做条目清单、入口与 SHA 校验 |
| Web BookStack 功能补丁 | 决定不改；冻结 A0 的 `c31c51f2400b` 已首轮及最终 `34/34`，阶段 4 仅建议效率评审 | 新的同任务失败链路或可复现回归；效率优化必须保持 `34/34` |

暂缓不是“永不处理”。每个新 Run 都须检索上述触发条件；无新证据时保留决定，不因看到同名任务或同样的超时字符串就自动翻案。

## 6. 新 Run 进入阶段 5 时的更新流程

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
3. 旧 Keep 的 `P5-002` 保持待证据。新 Keep `P5-006/007/008` 按第 9 节在本地复现；先核查阶段 4 身份交接，再决定窄 Agent 切片。不要把两个 Keep 的同编号失败混成一个“归档竞态”。
4. A/B 比较至少覆盖：平台通过数、首轮通过数、请求数、输入/输出/缓存/推理 Token、平台 Token、费用、总耗时和修复轮数；功能下降默认拒绝，平台异常需标记而非静默挑选最好结果。

## 8. 当前实现与验证流水账

| 日期 | 事项 | 状态 | 代码提交 / 构建 / Run | 结果 |
|---|---|---|---|---|
| 2026-09-19 | 建立阶段 5 跨 Run 决策台账 | 文档建立；Agent 改动未授权 | 尚无优化代码提交、候选 ZIP 或优化版 Run | 仅完成执行前核验，不宣称阶段 5 或 G6 完成 |
| 2026-09-19 | `P5-001` + `P5-003` 保守路由诊断与中性超时摘要 | 本地已验证；BookStack 平台待验证 | `codex/arc-bench-phase5-route-contract`，`c53c333d5205fb98bf168c1f4fc670c0eec7432f`；用户指认 ZIP 见 `P5-005`；Keep `0aa6820e0b82` 仅供诊断 | 4 项定向测试通过；真实 BookStack 检出 3 条、Keep 0 条；完整候选 81 项/A0 78 项均为相同 3 fail + 1 error（Windows 基线问题） |
| 2026-09-19 | 纳入 A0 Web BookStack `c31c51f2400b` | 阶段 3/4 证据已验证；阶段 5 决定仅评审效率 | A0 原版 Run；非候选构建，非 A/B | 平台与内部首轮均 `34/34`；阶段 4 ACK/结果四项身份字段匹配；无功能补丁，`34/34` 作为回归门槛 |
| 2026-09-19 | 纳入候选 Keep `0aa6820e0b82`，建立 `P5-006/007/008` | 平台最终事实已读；阶段 4 交接已核验；未做本地复现/Agent 新改动 | 用户指认 ZIP SHA-256 见 `P5-005`；生成包 `template.zip` SHA-256 `9B46EC5C3D55FEDD1E986BC6733E05CFA8C95C76723EFF42B67C22CF8DE93EC4` | 平台 `29/32`；三项失败机制分开记录，不能从 31/32→29/32 直接推断路由切片造成退步 |

后续新增一行时，若状态为“实施中”或以上，必须写出实际文件、完整提交 SHA、构建 ID、测试命令及结果；若状态为“平台已验证”，还须写出新 Run ID 和 A/B 结论。不得把本文件的建立提交误写成 Agent 优化提交。

## 9. `0aa6820e0b82` 无 Octos/Cargo/API Key 的本地定点复现与后续切片

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
