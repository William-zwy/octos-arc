# Octos Agent 优化计划：Round 3 Agent Runtime

> 计划日期：2026-09-27  
> 当前分支：`0924_hkt-20260926`  
> 适用仓库：`D:\items\Hackathon\octos-p`  
> 本轮主题：session 生命周期、checkpoint/resume、上下文裁剪与压缩、repair 策略

## 1. 背景

前两轮优化已经解决了编排层最直接的几个问题：

- Round 1 重点修复节点顺序、实现阶段、验收阶段和 repair 阶段之间的编排关系。
- Round 2 增加了 `.arc/application-contract.json`，让后续节点能够看到前置节点的路由、页面、数据模型、设计摘要、已通过节点和不变量。
- Round 2 增加祖先节点 spec 回归、shared/integration failure 归因、唯一 traceability owner 和 full-suite 共享故障处理。
- 当前 Windows 打包脚本已经具备：`arc/pack.ps1`、`arc/pack.cmd` 和原有的 `arc/pack.sh`。

但是，当前 runtime 仍然主要是“按 prompt 驱动的一次次 turn”。这在短任务上足够，在多节点、长 repair 链和云端中断场景下会暴露以下问题：

1. session 的生命周期虽然支持 `turn`、`node`、`run` 三种 scope，但缺少统一的 session 状态记录。
2. 运行中断后只能依赖当前进程和工作树，不能从最近的可靠边界恢复。
3. application contract 已经有长度裁剪，但 transcript、失败历史、工具输出和源码摘要还没有分层压缩策略。
4. repair 已经支持最佳状态回退和重复失败检测，但还没有将失败类别、repair 策略、重试事件和 checkpoint 统一起来。
5. 当前默认 `OCTOS_SESSION_SCOPE=turn` 是有意选择：每个 prompt 自包含，避免共享 session 导致上下文膨胀。后续不能直接把默认值改成 `node` 或 `run`，必须通过固定题目和云端 A/B 验证确认收益。

本轮的目标不是照搬任何一个参考仓库，而是把其中适合当前 ARC harness 的机制缩小、落地，并保持现有低成本的 prompt 编排结构。

## 2. 参考仓库中可迁移的机制

本轮参考了：

- `D:\items\Hackathon\claude-code`
- `D:\items\Hackathon\codex`
- `D:\items\Hackathon\minimax-code`
- `D:\items\Hackathon\ZCode`

### 2.1 Claude Code

已核对的入口包括：

- `claude-code/src/QueryEngine.ts`
- `claude-code/docs/internals/session-transcript-persistence.md`
- `claude-code/src/utils/sessionStorage.ts`
- `claude-code/src/utils/conversationRecovery.ts`
- `claude-code/src/services/compact/*`

可迁移思想：

- transcript 是追加记录，运行状态和 transcript 不应该混成一份不可解释的字符串。
- 恢复时重建有效消息链，而不是无条件重放所有文件内容。
- compact 应该写入边界和摘要，不能把历史直接删除到无法追溯。
- 文件修改历史、归因信息和任务状态需要有独立快照。
- 中断、恢复、分支和 sidechain 的身份要明确区分。

当前 Octos 不需要直接引入完整 JSONL transcript graph，但应该先建立轻量版的 event log、state snapshot 和 checkpoint manifest。

### 2.2 MiniMax Code

已核对的入口包括：

- `minimax-code/third_party/pi-mono/packages/coding-agent/src/core/compaction/compaction.ts`
- `minimax-code/packages/local-runtime-v2/src/service/session-system/index.ts`
- `minimax-code/packages/shared/src/llm-retry-event.ts`

可迁移思想：

- compaction 逻辑应尽量是独立、可测试的纯逻辑，I/O 和 session manager 分开。
- session system 负责生命周期、消息、队列、usage 和报告，而不是由 UI 或单个 turn 函数隐式维护。
- retry 事件应结构化记录 scope、attempt、reason、delay 和最终状态。
- compaction 不仅要保留文字摘要，还应保留读过的文件、修改过的文件等结构化信息。

### 2.3 ZCode

已核对的入口包括：

- `ZCode/architecture-policy.yaml`
- `ZCode/packages/rpc/src/persistent-protocol.ts`
- `ZCode/packages/zcode-server-cli/src/runtime/statusSnapshot.ts`
- `ZCode/packages/client/src/remoteServiceAccess.ts`
- `ZCode/packages/client/src/gitCheckpointService/*`（以当前仓库实际存在的接口为准）

可迁移思想：

- runtime 状态不能依附于 UI 或 main 进程中的临时变量。
- workspace identity 和 remote/session identity 必须同时传递，避免恢复到错误工作区。
- reconnect/resume 不是启动一个全新的 session；需要 ACK、重放边界、心跳和有界 buffer。
- status snapshot 要能区分 missing、invalid、unreadable，而不是全部降级为“没有状态”。
- checkpoint 应该是独立 service 或至少独立模块，不应散落在 repair 分支中。

### 2.4 Codex

Codex 本轮只提取通用设计原则，不在文档中绑定未逐一核对的具体路径：

- session、task、turn、event 和 rollout 状态应有清晰边界。
- 恢复时按需加载结构化状态，不应把所有旧上下文无差别塞回当前请求。
- 重试、断线、checkpoint 和 resume 都需要可观察记录，便于判断是模型问题、应用问题还是基础设施问题。

## 3. Round 3 总体目标

### 3.1 主要目标

1. 让每个 node 都有明确的 session 生命周期和状态边界。
2. 让运行可以从最近的完整 checkpoint 恢复，而不是只能从头执行。
3. 让长上下文按照“结构化状态优先、原始历史按需加载”的原则裁剪。
4. 让 repair 从“重复发送相似 prompt”升级为“分类、诊断、尝试、比较、回退”的闭环。
5. 提高云端真实测试通过率，同时控制 token、请求数、耗时和上下文污染。

### 3.2 非目标

本轮暂不做：

- 不修改 `D:\items\Hackathon\req` 中的官方 requirements 或官方 tests。
- 不把 `.arc/application-contract.json` 变成业务数据库。
- 不直接移植完整 Claude Code、Codex 或 MiniMax runtime。
- 不默认启用跨整个 run 的超长共享 session。
- 不因为本地 unittest 的 Windows 临时目录权限问题而修改业务逻辑。
- 不用更多静态 prompt 文字替代实际的状态记录和验证。

## 4. 当前实现基线

当前 `arc/main.py` 已具备以下基础，可以作为 Round 3 的增量入口：

- `OctosDriver.session_scope` 支持：
  - `turn`：每轮创建新 session。
  - `node`：同一 requirement node 的 design、implement、repair 共用 session。
  - `run`：整个运行共用 session。
- `OctosDriver.end_scope("node")` 会在节点边界关闭 session。
- `Flow.turn()` 统一执行 monitor、request budget、driver turn、保护文件恢复和 correction 记录。
- `acceptance_loop()` 已有：
  - repair round 上限。
  - identical failure 检测。
  - no-improvement 停止。
  - regressions 后恢复最佳 git state。
  - `snapshot_sources(node_id, attempt)`。
- `application_context_text()` 已对 application contract 做长度上限和字段裁剪。
- `.arc/octos-events.jsonl` 已记录 stdio 事件。
- `.arc/llm-usage.jsonl` 已记录 provider usage 汇总。

这些能力说明 Round 3 不需要重写主流程，而应增加统一状态层，并把现有散落的日志、快照和回退行为接入它。

## 5. 阶段 A：session 生命周期

### 5.1 目标

为 session 建立明确的状态机和身份信息：

```text
created -> opened -> active -> idle -> closed
                         \-> interrupted -> resumable
                         \-> failed
```

建议每个 session 至少记录：

```json
{
  "schema_version": 1,
  "session_id": "uuid",
  "run_id": "uuid",
  "node_id": "REQ-1",
  "workspace_id": "stable workspace identity",
  "scope": "turn|node|run",
  "status": "created|active|idle|closed|interrupted|failed",
  "created_at": "...",
  "updated_at": "...",
  "last_turn_id": "uuid",
  "last_checkpoint_id": "cp-...",
  "turn_count": 0
}
```

### 5.2 第一批低风险实现

先不改变默认 session scope，只增加可观察性：

1. 在 `.arc/session/` 下写入 `run.json`、`sessions.jsonl` 或等价的小型记录。
2. 每次 `open`、`run_turn`、`close`、retry、fallback 和 exception 写结构化 event。
3. 为每个 turn 生成稳定的 `run_id`、`node_id`、`turn_id`、`session_id` 关联字段。
4. `close()` 必须幂等，重复关闭不能破坏后续 checkpoint。
5. session 状态写入采用临时文件加 rename，避免进程中断后留下半份 JSON。
6. 启动时遇到 invalid session snapshot，要记录诊断并新建 session，不把损坏状态静默当成正常空状态。

### 5.3 session scope 的验证顺序

依次进行：

1. `OCTOS_SESSION_SCOPE=turn`：作为基线，验证新增状态记录不改变测试结果。
2. `OCTOS_SESSION_SCOPE=node`：只让 design、implement、repair 共享一个 node session。
3. `OCTOS_SESSION_SCOPE=run`：只作为实验选项，不作为默认值。

只有在云端看到 node scope 同时满足以下条件，才考虑调整默认值：

- node pass rate 不下降。
- full-suite pass rate 不下降。
- repair rounds 和重复失败次数下降。
- prompt token 和总耗时没有不可接受的增加。

### 5.4 设计注意事项

- design 输出、implementation 输出和 acceptance verdict 不能只存在模型上下文中；至少要在 checkpoint 中留下摘要。
- node session 不能跨越错误的 workspace 或不同 requirement tree。
- run scope 中必须有上限和 compaction 触发条件，否则长任务会把每个节点的历史都带入后续节点。
- session 关闭不等于任务完成；关闭前应先写出最后一个可恢复 checkpoint 或明确标记为不可恢复。

## 6. 阶段 B：checkpoint/resume

### 6.1 目标

把“可以继续执行的位置”从隐式内存状态变成可验证的磁盘状态。checkpoint 应描述：

- 运行到哪一个 node。
- 当前 node 处于 design、implement、acceptance、repair 还是 finished。
- 当前工作树对应的版本。
- 已通过的节点和测试结果。
- 最近一次 repair 的失败摘要和策略。
- application contract 的版本或 hash。
- session 的身份和最后一个 turn。

### 6.2 建议目录结构

```text
.arc/
  checkpoints/
    manifest.json
    cp-000001.json
    cp-000002.json
  session/
    run.json
    events.jsonl
    sessions.jsonl
  transcripts/
    <session-id>.jsonl
  snapshots/
    REQ-1/
      repair-0/
      repair-1/
```

实际目录名可以配合现有 `.arc` 结构调整，但 checkpoint、session event、transcript 和 source snapshot 应该有清晰边界。

### 6.3 checkpoint schema 草案

```json
{
  "schema_version": 1,
  "checkpoint_id": "cp-000042",
  "run_id": "run-...",
  "workspace_id": "workspace-...",
  "created_at": "...",
  "reason": "node_start|design_saved|implementation_done|repair_round|node_accepted|interrupted",
  "tree_hash": "sha256-or-git-head",
  "contract_hash": "sha256",
  "current": {
    "node_id": "REQ-2",
    "phase": "acceptance",
    "attempt": 2
  },
  "completed_nodes": ["REQ-1"],
  "passed_nodes": ["REQ-1"],
  "node_verdicts": {
    "REQ-2": {
      "passed": 3,
      "total": 5,
      "best_passed": 3,
      "last_failure_digest": "..."
    }
  },
  "session": {
    "session_id": "session-...",
    "scope": "node",
    "last_turn_id": "turn-..."
  },
  "artifacts": {
    "application_contract": ".arc/application-contract.json",
    "design": ".arc/design/REQ-2.json",
    "source_snapshot": ".arc/snapshots/REQ-2/repair-2"
  }
}
```

### 6.4 checkpoint 写入时机

第一阶段只在低风险边界写入：

1. run 初始化完成。
2. node 开始前。
3. design 成功保存后。
4. implementation turn 结束后。
5. 每次 acceptance round 得到真实 verdict 后。
6. node accepted 后。
7. 发生 timeout、进程异常、session 中断或全局时间不足时。

不要一开始每个工具调用都写 checkpoint；这会放大 I/O、污染日志并增加损坏面。

### 6.5 原子性和恢复规则

1. 先写 `checkpoint.tmp`，flush 后 rename 为正式文件。
2. `manifest.json` 只指向已经完整存在且 schema 校验通过的 checkpoint。
3. 恢复时从最近的“完整 checkpoint”开始，不从半写文件恢复。
4. 恢复前校验 workspace identity、requirements hash、application contract hash 和 source tree 状态。
5. 如果代码树与 checkpoint 不一致，默认进入 `resume_requires_reconcile`，不要静默覆盖用户修改。
6. 恢复后重新启动 app 并重新执行当前 node 的 acceptance；不能仅凭旧 verdict 标记通过。
7. 已经通过的 node 默认只读保护，但允许显式开启 repair ancestor 的实验开关。

### 6.6 resume 的最小实现

建议先实现“同一进程异常后的本地 resume”：

- 参数或环境变量：`OCTOS_ARC_RESUME=auto|never|<checkpoint-id>`。
- `auto` 只在当前 run、workspace 和 requirements hash 都匹配时恢复。
- 恢复后从 `current.node_id + current.phase` 进入，而不是从第一个 node 重跑。
- 当前 node 若在 repair 中断，恢复为“重新运行最近一次 acceptance，再决定是否 repair”，不要直接续接未知的半个模型 turn。
- 不在第一版实现跨机器、跨 workspace 或远端 session 的 resume。

## 7. 阶段 C：上下文裁剪与压缩

### 7.1 总体原则

上下文应分为四层，并按优先级加载：

1. **硬约束层**：requirements、当前 node spec、官方测试观察、禁止修改文件、application contract 中的不变量。
2. **运行状态层**：当前 phase、已通过节点、最近 checkpoint、最近一次失败摘要、repair strategy。
3. **结构化历史层**：design 摘要、source manifest、读写文件集合、测试结果、usage 和 retry event。
4. **原始历史层**：完整 transcript、长工具输出、旧 repair prompt、重复失败正文。

硬约束层和运行状态层必须优先保留。原始历史只有在诊断需要时才加载。

### 7.2 建议的上下文包

每次 turn 不再直接拼接所有历史，而是由 context builder 生成：

```text
ContextPacket
  - contract
  - current_node
  - current_phase
  - checkpoint_summary
  - recent_failure_digest
  - repair_history_summary
  - source_manifest
  - selected_file_excerpts
  - recent_transcript_tail
  - omitted_sections
```

其中 `omitted_sections` 要明确列出被裁掉的内容，避免模型误以为没有历史。

### 7.3 分层 token 预算

初始预算可以采用比例而不是固定大文本：

| 层级 | 建议占用 | 说明 |
|---|---:|---|
| 硬约束层 | 25% | requirements、spec、invariants、只读规则 |
| 运行状态层 | 15% | checkpoint、phase、当前 verdict、时间预算 |
| 结构化历史层 | 30% | contract、design、source manifest、测试摘要 |
| 原始历史层 | 30% | 最近 transcript、失败原文、必要源码片段 |

具体数值必须根据云端模型上下文窗口和真实 token usage 调整。不要把 `14000` 字符的 application contract 上限直接当作整个 prompt 的上限。

### 7.4 compaction 触发条件

建议同时支持：

- token 使用率超过阈值。
- transcript 条目数超过阈值。
- 工具输出累计字节超过阈值。
- repair 失败摘要重复出现。
- session 从 node scope 晋升到 run scope 时。

compaction 产物至少包括：

```json
{
  "summary": "短摘要",
  "preserved_invariants": ["..."],
  "read_files": ["..."],
  "modified_files": ["..."],
  "last_known_verdict": {"passed": 3, "total": 5},
  "supersedes": ["turn-1", "turn-2"],
  "tokens_before": 0,
  "tokens_after": 0
}
```

### 7.5 安全裁剪顺序

推荐顺序：

1. 删除重复的 prompt 前缀和重复 application contract。
2. 将旧 repair 的完整失败正文替换成 digest。
3. 将旧工具输出替换成命令、退出码、关键观察和相关文件。
4. 将旧 design 替换成结构化摘要，但保留 route、data model 和 invariant。
5. 只保留最近若干轮 transcript tail。
6. 仍然超限时，缩短 source listing 和非当前 node 的说明。
7. 最后才裁剪非当前 node 的历史；不能裁剪当前 node spec 和已通过节点保护信息。

### 7.6 先做旁路指标

第一版 context compaction 可以只生成统计，不改变发送给模型的内容：

- 原始字符数、估算 token 数。
- 每个 section 的占比。
- 被裁剪 section 和裁剪比例。
- compaction 前后 prompt hash。
- 当前 turn 是否使用了旧 transcript。

等旁路指标能解释云端 token 和通过率变化后，再启用实际裁剪。

## 8. 阶段 D：repair 策略升级

### 8.1 失败分类

每个 acceptance failure 先归入以下类别之一：

1. `infrastructure`：build、start、端口、依赖、进程启动失败。
2. `shared_application`：多个 spec 或多个 node 同时受影响的服务、路由、schema、初始化问题。
3. `node_functionality`：当前 node 自身功能未实现或行为不符合 spec。
4. `regression`：当前 node 修改破坏了祖先 node 已通过行为。
5. `state_isolation`：并发测试、持久化 seed、session 隔离或共享数据污染。
6. `performance`：超过 grader 的时间预算或出现明显重复请求。
7. `unknown`：证据不足，不能强行归因给当前 node。

unknown 和 shared_application 不应自动被复制到多个 node 的 traceability owner。

### 8.2 失败分类所对应的动作

| 类别 | 首选动作 | 禁止动作 |
|---|---|---|
| infrastructure | 检查 grader-like 启动链，必要时有限重试 | 直接修改业务页面掩盖启动错误 |
| shared_application | 生成共享修复 prompt，运行最小回归集 | 让每个 node 各自修同一个问题 |
| node_functionality | 当前 node 定向 repair | 大范围重写已通过祖先模块 |
| regression | 恢复最佳 checkpoint，带祖先 spec repair | 接受当前 node 局部通过而牺牲旧功能 |
| state_isolation | 分离初始状态和持久化状态，增加并发复现 | 删除需求要求的持久化 |
| performance | 读取 slow test 和工具轨迹，去除延迟 | 只增加 timeout |
| unknown | 保留证据，要求下一轮补充观测 | 把失败标成当前 node 的通过或失败 |

### 8.3 repair 状态机

```text
observe
  -> classify
  -> choose_strategy
  -> snapshot
  -> repair
  -> run_acceptance
  -> compare
      -> accepted
      -> improved: keep and continue
      -> regressed: restore best checkpoint
      -> identical: change strategy
      -> infrastructure: stop or bounded retry
```

### 8.4 重复失败与策略切换

当前已经有 identical failure 检测，后续应从布尔标记升级为结构化 digest：

```json
{
  "failure_digest": "sha256",
  "category": "node_functionality",
  "first_seen_attempt": 0,
  "last_seen_attempt": 2,
  "same_observation_count": 3,
  "strategies_used": ["patch", "patch", "rewrite"],
  "next_strategy": "tool_mode"
}
```

策略切换规则建议：

- 相同失败连续两次：禁止重复原 repair prompt，要求改变实现路径。
- 0/N 连续两轮：允许一次完整重写，但必须保留当前 checkpoint。
- 通过数下降两轮：恢复最佳 checkpoint，并把失败 diff 注入下一次 prompt。
- shared/infrastructure 连续出现：暂停 node-local repair，进入 shared repair 或等待外部环境。
- 超过 repair budget：保留最佳状态，不做最后一轮无证据修改。

### 8.5 repair 前后需要保存的证据

每轮 repair 保存：

- checkpoint id。
- git/tree hash。
- failure digest 和原始失败摘要路径。
- 使用的 strategy。
- prompt/context packet hash。
- 变更文件列表。
- acceptance 结果。
- token、请求数和耗时。

这样才能区分“模型没有理解”“上下文不完整”“测试不稳定”和“修复把问题扩大了”。

## 9. 阶段 E：验证和 A/B 实验

### 9.1 固定实验条件

每次比较只改变一个主要变量，固定：

- 同一份 `req`。
- 同一模型、provider、base URL 和 profile。
- 同一 `OCTOS_*` 预算。
- 同一 worker 数量和 acceptance specs。
- 同一打包内容。
- 同一超时时间。

每个实验至少记录：

```text
run_id
commit/tree hash
session scope
compaction mode
checkpoint mode
repair strategy version
node pass rate
full-suite pass
shared failure count
regression count
repair rounds
requests
prompt/completion/total tokens
duration
resume result
```

### 9.2 推荐实验矩阵

先做四组：

| 实验 | session | checkpoint | compaction | 用途 |
|---|---|---|---|---|
| A | turn | off | off | 当前 Round 2 基线 |
| B | node | off | off | 只验证 session 共享是否有收益 |
| C | turn | on | off | 只验证状态记录和恢复，不改变上下文 |
| D | node | on | shadow | 验证 node session 加旁路 compaction 指标 |

只有 C/D 的指标稳定后，再做实际 context compaction。不要同时切换 session、checkpoint、compaction 和 repair，否则无法解释通过率变化。

### 9.3 验收门槛

每个候选改动至少满足：

1. 本地语法、定向 helper tests 和 `git diff --check` 通过。
2. 现有 Round 2 行为没有回归。
3. 单题 canary 不低于基线。
4. 两个云端题目至少有一个通过率提升，另一个不明显下降。
5. 如果通过率持平，token、耗时或 repair 次数必须有明确收益才保留。

## 10. 风险与回滚开关

建议新增的环境变量都应有保守默认值：

```text
OCTOS_SESSION_SCOPE=turn
OCTOS_ARC_CHECKPOINT=0
OCTOS_ARC_RESUME=never
OCTOS_ARC_COMPACTION=0
OCTOS_ARC_COMPACTION_SHADOW=0
OCTOS_ARC_REPAIR_STRATEGY=v1
OCTOS_ARC_REPAIR_CLASSIFY=1
OCTOS_ARC_CHECKPOINT_KEEP=20
OCTOS_ARC_CONTEXT_BUDGET=auto
```

回滚原则：

- 任何 checkpoint 读取失败都只能降级到从头运行，不能覆盖应用源码。
- compaction 出现不一致时立即关闭实际裁剪，保留 shadow metrics。
- node session 出现 prompt 膨胀或通过率下降时切回 `turn`。
- repair strategy 改动导致回归时恢复最佳 checkpoint，而不是继续追加 patch。
- 所有实验开关必须在日志中打印最终生效值。

## 11. 推荐实施顺序

### 第 1 步：只做观察层

- 增加 `run_id/node_id/turn_id/session_id` 关联。
- 统一记录 session lifecycle event、retry event、acceptance verdict。
- 为现有 `snapshot_sources`、`restore_app` 和 `application-contract` 记录 hash。
- 不改变默认 session scope、prompt 内容和 repair 行为。

### 第 2 步：checkpoint manifest

- 增加 schema、原子写入、manifest、读取校验。
- 在 node start、design saved、acceptance verdict、node accepted 和 interrupted 处写 checkpoint。
- 先只支持本地恢复检查和诊断，不自动 resume。

### 第 3 步：最小 resume

- 支持当前 run、同一 workspace、同一 requirements hash 的 `OCTOS_ARC_RESUME=auto`。
- 从最近 checkpoint 重新执行当前 node 的 acceptance。
- 先不恢复半个模型 turn，也不恢复远端连接。

### 第 4 步：context compaction shadow

- 计算每个 context section 的大小。
- 生成 compaction summary 和 omitted sections。
- 记录使用 shadow packet 时的 token 估算，但继续发送原始 packet。

### 第 5 步：启用低风险裁剪

- 先去重复 contract、旧失败原文和旧工具输出。
- 保留当前 spec、invariants、最近失败和 source manifest。
- 逐题验证，不一次性扩大裁剪范围。

### 第 6 步：repair classifier 和 strategy

- 先分类并记录，不改变修复动作。
- 对 identical、regression、shared failure 启用已有动作的结构化版本。
- 最后才增加新的 rewrite、shared repair 或 resume-aware repair。

### 第 7 步：评估 `node` 默认值

- 只有在 A/B 结果确认收益后，才考虑从 `turn` 调整为 `node`。
- `run` scope 继续保留为实验开关，除非长任务数据明确证明其收益大于上下文和恢复风险。

## 12. 预计改动边界

优先新增或拆分：

```text
arc/runtime_state.py       # session/checkpoint/event schema 与读写
arc/context_budget.py       # context section、预算和 compaction 纯逻辑
arc/repair_policy.py        # failure classification 与 strategy selection
arc/tests/test_runtime_state.py
arc/tests/test_context_budget.py
arc/tests/test_repair_policy.py
```

`arc/main.py` 只保留流程编排和调用这些模块的胶水逻辑。若现有项目结构不适合新增模块，可以先在 `main.py` 内部实现最小版本，再在测试稳定后拆分。

禁止在第一版中把所有 session、checkpoint、compaction 和 repair 逻辑继续堆进 `acceptance_loop()`。

## 13. 本轮完成标准

Round 3 不以“代码新增完成”为完成标准，而以以下结果为完成标准：

- 任意一个 node 在关键边界都有可读取 checkpoint。
- 进程异常后可以判断是否能 resume，以及为什么不能 resume。
- 长上下文被裁剪时，当前 spec、application invariants、最近 verdict 和已通过节点不会丢失。
- repair 日志能回答：失败是什么类别、尝试了什么策略、是否改善、何时回退。
- 云端真实测试中，至少能观察到通过率、shared failure、repair rounds、token 和耗时的可比较变化。
- 所有新机制都能通过环境变量关闭并回到 Round 2 基线。

## 14. 结论

下一轮最重要的不是把更多 agent runtime 代码搬进 Octos，而是先建立一条可解释、可恢复、可比较的运行链：

```text
session identity
  -> structured events
  -> checkpoint
  -> bounded context
  -> classified repair
  -> acceptance verdict
  -> next checkpoint
```

建议从“观察层 + checkpoint manifest”开始。它们对现有通过率风险最低，却能为后续 session 共享、context compaction 和 repair 策略提供可靠证据。只有拿到云端 A/B 结果后，才决定是否改变默认 session scope 和实际上下文压缩强度。
