# ARC-Bench 阶段 5 新会话精简交接

> 2026-09-20 启动版。用于会话和队友快速上手；详细推理、证据及后续变动以[决策台账](./ARC_BENCH_HACKATHON_PHASE5_DECISION_REGISTER.md)、各 Run 的阶段 3/4 文件和当前代码为准。不要把本文件当新的平台成绩表。

## 先读什么

1. [阶段 5 多会话工作流](./ARC_BENCH_HACKATHON_PHASE5_COLLABORATION_WORKFLOW.md)：职责、交接和授权门禁。
2. [决策台账](./ARC_BENCH_HACKATHON_PHASE5_DECISION_REGISTER.md)：P5-001～P5-009、已实施与暂缓项。
3. [阶段 3→4 SOP](./ARC_BENCH_HACKATHON_PHASE4_THREAD_WORKFLOW.md)及目标 `evidence/arc-bench/runs/<run_id>/manifest.json`、`phase4-result.json`：只读当前事项的原始身份与诊断。
4. 当前工作树的代码、Git SHA 与测试；历史聊天和项目记忆只补充导航，不覆盖原始证据。

## 仍有效的工作记忆

- 比赛有 6 个赛道、当前 13 个已发布可运行子任务；官方历史 Demo/Playground 不代表队友 Agent 基线。原始 Agent A0 代码 `ea503546aad31b2e3b887235e3b35cc0a8b9cfe8`。官方快照和原始 Agent 均在本地证据分支保存。
- 当前证据工作树在 `D:/DataMove/codex/worktrees/9015/AI智能体软件工厂黑客松`，本地分支为 `codex/arc-bench-official-snapshot-20260917`；Codex 保存的项目默认目录在 `C:/Users/dayuruozhi/Documents/ChatGPT/AI智能体软件工厂黑客松`，其 `main` 仍是 A0。**新会话必须核对实际 cwd/HEAD；不能假定默认项目 worktree 已含证据分支的文档或未提交文件。**
- 上述绝对路径仅用于这台机器上的会话交接；队友在别的电脑应以仓库相对路径、完整提交 SHA 和文件哈希定位，不照抄本机盘符。
- 上述绝对路径仅用于这台机器上的会话交接；队友在别的电脑应以仓库相对路径、完整提交 SHA 和文件哈希定位，不照抄本机盘符。
- 上述绝对路径仅用于这台机器上的会话交接；队友在别的电脑应以仓库相对路径、完整提交 SHA 和文件哈希定位，不照抄本机盘符。
- 阶段 5 Agent 候选位于独立工作树 `.worktrees/phase5-route-contract`、分支 `codex/arc-bench-phase5-route-contract`，截至交接前完整 HEAD 为 `dddc94312d4cd26babdbfb9d7df2a17f08f0a51d`。它是在先前路由诊断切片之上增加 Keep 交互/种子契约的本地候选；不是原始 A0，也尚无该提交对应的可比平台 A/B。该工作树中的未跟踪 ZIP 为用户资产，不自动修改或暂存。
- 完成率和回归可靠性优先；功能相同时比较 Token，再比较耗时/请求。平台最终结果与 Agent 内部验收必须分开。生成应用 `template.zip` 不是上传 Agent ZIP；评分后导出的 DB 不能冒充评分前状态。缓存/推理 Token 不重复求和。所有身份、模型和任务快照冲突必须显式保留。
- 本地隔离产物复现不需要 Octos、Cargo 或本地 ARC-Bench API Key；平台上传/运行需另行授权。当前用户要求**不推送远程**，也未授权本次拆分工作启动新的平台 Run。

## 当前决策状态（只作索引）

| 事项 | 有效状态 | 下一责任 |
|---|---|
| `P5-001/003` Lite BookStack 路由漏接与超时措辞 | 候选本地验证；平台收益未知 | 指标会话核对未来同条件 A/B 身份；台账继续跟踪 |
| `P5-006/007/008` Keep 名称/消息、seed、编辑重绘 | 干净 seed 生成应用 32/32；Agent 通用提示本地验证；平台收益未知。原 ZIP DB 的 24/32 是**评分后快照重放** | 台账及指标会话；不得据此全局清库 |
| `P5-009` BookStack Lite `5669f7d1777c` | 保存后 heading/link 与异步定位为 `strong_candidate`；还缺最终 DOM/导航时序 | 决策台账签发隔离复现卡；复现会话不先改 Agent |
| `P5-002` 旧 Keep 归档后读写时序 | `strong_candidate`，缺 trace/等效请求序列 | 待补证据；不并入 `P5-007` |
| `P5-004/005` 成本机制及 A/B 身份 | 请求/Token 可计量，但阶段归因和上传构建/快照绑定不足 | 指标会话审计；不宣称收益 |

`c31c51f2400b` 是冻结 A0 的 Web BookStack `34/34`，只作回归/效率样本。`5669f7d1777c` 是首次修改版 Lite BookStack，不是阶段 5 候选输出；它与旧 Lite 的同分数也不可直接算 A/B。

## 新到但尚未决策的输入

- Lite Keep `737b56972d5a` 已有阶段 3 [manifest](../evidence/arc-bench/runs/737b56972d5a/manifest.json)和阶段 4 [结果](../evidence/arc-bench/runs/737b56972d5a/phase4-result.json)，注册表标为 `verified`；平台最终 `30/32`，失败 `REQ-2.7.5`、`REQ-2.7.6.3`，并出现内部全套 `31/32 → 24/32 → 30/32` 的回归轨迹。来源标为 post-fix candidate，但上传 Agent/任务快照绑定不足；**应由新决策会话首次正式纳入台账，不能把阶段 4 候选根因自动当成阶段 5 决议。**
- Web Keep `4b792b72d7dd` 的阶段 4 会话映射在[注册表](../evidence/arc-bench/phase4-thread-registry.json)为 `quarantined`，不自动进入阶段 5；先核对实际 Thread ID 和可读结果。
- `5669f7d1777c` 的阶段 4 注册表仅标 `complete`，不是新的自动转派门禁 `verified`；台账已有人工分析，后续若补证据仍需按身份字段复核。

## 四个新会话如何使用本交接

- 决策台账：先审 `737b56972d5a` 的身份与旧 `P5-006/007/008` 的关系，再决定新 ID、复现或暂缓；不能直接派发代码修改。
- 隔离复现：待台账发实验卡；用户提交本地复现时记录原版/对照、单变量、干净 seed、命令/退出码、trace 与哈希，并把结论回交台账。
- Agent 实现：只在获授权的小切片上核对候选分支当前 HEAD、现有提示/验收入口和用户 ZIP；不重复造验收层，不按任务名硬编码。
- 指标与 A/B 验收：先建可比性清单与缺失字段表；没有获准的新平台 Run 时只做只读审计，不发布收益百分比。

历史会话可以回读，但不复制无关长历史；旧消息无法被“压缩删除”。若本文件与新原始证据冲突，应修订本文件并在决策台账留下纠偏记录。
