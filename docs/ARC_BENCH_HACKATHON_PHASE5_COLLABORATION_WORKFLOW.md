# ARC-Bench 阶段 5 多会话协作与条件交接

> 版本：v1.0；日期：2026-09-20。此文档定义流程，不代表任何候选已获平台验证。
>
> 权威入口：[执行计划](./ARC_BENCH_HACKATHON_EXECUTION_PLAN.md)（总体目标）、[项目记忆](./ARC_BENCH_HACKATHON_PROJECT_MEMORY.md)（持续背景）、[阶段 3→4 工作流](./ARC_BENCH_HACKATHON_PHASE4_THREAD_WORKFLOW.md)（上游门禁）、[阶段 5 决策台账](./ARC_BENCH_HACKATHON_PHASE5_DECISION_REGISTER.md)（唯一决策记录）、[精简交接](./ARC_BENCH_HACKATHON_PHASE5_CONTEXT_HANDOFF.md)（新会话启动卡）。聊天摘要不是事实源。

## 1. 会话职责和唯一写入者

| 固定会话 | 输入 | 产出与写入范围 | 不得做的事 |
|---|---|---|---|
| `项目阶段5｜跨 Run 决策台账` | 已核验的阶段 4 结果、阶段 3 manifest、已核实的复现/实现/指标结果 | 维护唯一决策台账；按机制归并、选择复现/修改/暂缓；签发下一步任务卡 | 不替代阶段 3/4；不直接改 Agent、运行平台或把同名失败合并 |
| `项目阶段5｜隔离复现` | 台账发出的实验卡，或用户提供的本地复现包 | 给出步骤、核验用户实验、在隔离副本做获准的本地对照；保存可重放证据和缺口 | 不改官方 spec、原始 ZIP 或 Agent 正式代码；不把产物级修复当作 Agent 收益 |
| `项目阶段5｜Agent 实现` | 台账批准的单一问题/切片与代码基线 | 在隔离工作树实施最小改动、定点与相关回归、记录提交/构建身份 | 不从聊天推断修改授权；不覆盖证据分支、官方测试或其他候选；不自行发起平台 Run/推送 |
| `项目阶段5｜指标与 A/B 验收` | 阶段 3 归一化计量、阶段 4 复核、候选提交/ZIP/配置绑定 | 审计可比性、功能与成本指标；给出 go/no-go 和证据缺口 | 不发明缺失的 SHA/快照；不把本地通过当平台通过；不自行上传或运行平台 |

每个写入中的工作树同一时刻只有一名写入者。阶段 3/4 的证据写入与台账写入若共用工作树，必须串行交接；实现使用独立工作树。不同工作树的未提交文件不会自动共享，交接必须引用可读绝对路径或已提交的完整 SHA。候选工作树中的未跟踪 ZIP 属用户资产，不自动移动、暂存或覆盖。

## 2. 事实来源与身份门禁

阶段 5 首入口只接收经阶段 3→4 SOP 验证的 `phase4-result.json`。先用 `manifest.json` 核对 `run_id`、任务身份和原始来源，再核对 `phase4-handoff.json`、`phase4-ack.json`、`phase4-result.json` 的 `run_id`、`task_key`、`handoff_id` 和 Thread ID；阶段 4 注册表状态须为 `verified`。只有聊天“完成”、`result.status=complete` 但注册表未核验，或文件字段冲突时，进入 `needs_reconciliation`，不自动向下游转派。历史上已被台账人工纳入的记录保留原结论，但不因此放宽未来门禁。

每个新 Run 独立记录 competition/catalog、submission、Agent 代码 SHA、上传 ZIP SHA-256、官方快照/测试哈希、模型/配置、平台最终结果、内部验收和计量口径。缺失字段写 `missing`，不得以展示名、生成应用的 `template.zip` 或最好一次内部验收补齐。平台新 Run **先回阶段 3 冻结、再回阶段 4 诊断**，最后才进入阶段 5；用户的本地隔离实验直接提交复现会话，不伪装成平台 Run。

## 3. 条件状态机

一个工作项只对应一个 `run_id + issue_id + evidence_digest`；后续证据变化产生新 revision，保留旧结论及撤回原因。机器索引 `evidence/arc-bench/phase5-coordination.json` 只记录会话 ID、工作项身份、状态、已发送/已确认的交接 ID 和证据路径；长篇判断只写决策台账。

| 当前状态 | 准入条件 | 下一步 |
|---|---|---|
| `phase4_verified` | 上述四文件和注册表核验通过 | 只向决策台账发送一次 intake 卡 |
| `ledger_triaged` | 台账已列事实、证据等级、已有能力、候选方案及暂缓理由 | `needs_repro` / `review_only` / `needs_evidence` / `approval_required` 四选一；不默认复现 |
| `needs_repro` | 明确原始产物、冻结测试、单变量、干净起点、日志/哈希和停止标准 | 向复现会话发送一次实验卡；用户可在该会话提交实验结果 |
| `repro_verified` | 原版/对照版与每轮 seed、输入和结果可核查；不确定性保留 | **返回决策台账**修订证据等级；失败或不确定可退回 `needs_evidence` |
| `approval_required` | 台账确认需要修改 Agent，且范围、复用点、回归和代码基线明确 | 等用户授权该切片；不自动写代码 |
| `implementation_authorized` | 授权、单写入者、干净代码基线均成立 | 向实现会话转派；一主要变量一切片 |
| `local_verified` | 定点/相关回归、完整提交及构建身份已记录 | 向指标会话发本地验收卡；不声明平台收益 |
| `platform_run_authorized` | 用户另行批准上传/运行，且代码/ZIP/任务快照/配置身份可核验 | 由平台操作人运行；结果回阶段 3→4→台账及指标会话 |
| `ab_reviewed` | 同任务、同快照、同模型/配置且口径一致；异常和缺失已披露 | 台账记 `platform_verified`、`not_comparable`、`regressed` 或 `reopen` |

已通过或无需修改的 Run 可从 `ledger_triaged` 进入 `review_only`；已有充分证据且获授权的事项可跳过重复复现。复现会话不得直接触发实现，指标会话也不得替代用户批准新的平台运行。

## 4. 交接卡与幂等保护

每次转派只发短卡：`handoff_id`、`run_id`、`task_key`、`issue_id`、revision/evidence digest、目标会话 ID、当前代码完整 SHA、必读文件绝对路径、已知事实、缺口、允许动作、禁止动作、完成标准。接收会话先 ACK 相同 `handoff_id` 和基线，再读取相关证据；旧 handoff 的结果不可覆盖新 revision。发现目标会话重复、不可回读、身份不匹配或写入者未交接，标记 `quarantined` / `needs_reconciliation` 并停止，不重新盲发。

`phase5-coordination.json` 的会话映射和已发送状态是幂等索引，不存 API Key、原始日志或完整推理。聊天标题仅供展示，不是任务键。结果文档使用可追溯路径和哈希；不在多份 MD 中复制同一结论。

## 5. 复现与 A/B 的不同入口

本地复现会话接受用户提供的 `run_id`、问题 ID、原始 ZIP/官方 spec 哈希、Node/Playwright 版本、命令/退出码、每轮 DB 前后哈希、唯一变量、日志/trace 路径及结论。它核验后把证据和相反解释回交台账。独立产物修复可能验证机制，却不能证明 Agent 已修好或 Token/耗时降低。

指标会话按功能通过率/回归先行、同等功能下 Token、然后耗时/请求/修复轮的顺序评审。输入缓存 Token 是输入的子集，推理 Token 通常在输出口径内，不能重复计入 Provider total；平台 Token 与 Provider total 不能混用。身份不全时可以做**描述性对照**，不能发布因果 A/B 收益。没有可比平台 Run 时只出“本地验证/等待平台”的结论。

## 6. 自动化边界和启用顺序

优先由阶段 3 接收会话在验证阶段 4 持久化文件后，按工作项状态给决策会话发送一次转派。对迟到或漏接结果，可用**一个只读定时巡检**核对文件与会话 ACK；无变化保持安静。桌面端没有“另一个 Codex 会话已完成”的原生事件触发，本项目不将定时轮询写成实时保证；本地文件巡检还要求电脑和应用可用。参考 [OpenAI Docs：计划任务](https://learn.chatgpt.com/docs/automations)。

先用现有已核验记录手工演练一次、不改 Agent、不启动平台；通过后才启用巡检。巡检不得扫描 Downloads、修改 Git、创建重复任务、运行实验、上传 ZIP、启动平台 Run 或推送远程。`phase4_verified` 与 `repro_verified` 可自动转派**分析**，`implementation_authorized` 与 `platform_run_authorized` 仍需明确的用户授权记录。

## 7. 安全、维护与轮换

- 遵循用户当前要求：不推送远程；未获授权不运行新平台 Run。仓库变更按单写入者、预检、局部提交和验证执行。后续用户更改权限时以最新明确指令为准。
- 不修改官方测试、官方任务快照或原始 ZIP；不把 Octos、Cargo 或本地 ARC-Bench API Key 误列为隔离复现前提。
- 当前阶段 5 长会话是只读历史；新会话从本文件、精简交接和台账启动，不继承无关聊天。收到四个新会话的 ACK 后再考虑归档旧会话；归档不是删除历史。
- 当任一会话再次过长，以同职责新会话轮换，先更新精简交接和会话索引，再停旧会话；不无限新建每 Run 会话。
