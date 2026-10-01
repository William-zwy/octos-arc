# Phase 3 analysis: `effd5e7777ce`

## 已确认事实

- 任务为 `hackathon--github`，平台终态为 `FAILED`，得分 `2/100`，feature 结果 `0/47`。
- 平台的 `run_tests` 步骤为 `completed / Evaluation completed`，因此官方评测已到达；但 `tests=[]`，没有逐测试 ID、断言、timeout 类型、Playwright report 或 trace。
- submission 为 `019c8cb3d590`，本地归档 ZIP SHA-256 为 `0E98E7E0DFCF4F893A5CFCE0B8CD8D40168E7EC1FFE505A744E1097FE18FB7C5`。
- ZIP 内 `agent-build.json` 声明 commit `9ff7e750657a1d5c1ba67f71651ed9fe0d56c5c5`、build ID `arc-agent-v1-747e10178d68748225a086dd` 和 payload tree `E022098B6B9B4647D2EA6E5D4C2754845AA161A91DF10D16550A1DD969312DBF`。这是归档包内身份，不是平台回传绑定。
- 运行日志中的 `agent_commit=eea9ce...` 与包内 commit 不一致，不接受为 Agent 源码身份。平台仍未提供 generation identity、build ID 和 task snapshot。
- Agent 遍历了 47 个节点：46 次内部 `implement ok` 标签，`REQ-1-1-3` 一次 900s timeout。47/47 节点均为 `wrote=True, verified=False`。
- skeleton attempt 1 为 `wrote=True, verified=True`。startup rehearsal 第一次遇到 favicon `ConnectionResetError`，repair 后第二次通过，随后 frontend build、backend install 和 port 3000 监听成功。
- 无上游 HTTP 402/500 或 quota 中断证据；`REQ-1-1-3` timeout 窗口前后有 2 次本地 `llm_proxy` BrokenPipeError。OOM counters 为 0。

## 去重与事实纠错

平台日志同时保留 Agent stdout/stderr 镜像。按时间戳和消息体去重后：

| 指标 | 原始行数 | 独立逻辑事件 |
|---|---:|---:|
| request-budget hit | 98 | 49：skeleton cap 20 × 1、节点 cap 16 × 47、rehearsal repair cap 10 × 1 |
| `implement ok` | 92 | 46 |
| `implement FAILED` | 2 | 1：`REQ-1-1-3` |
| rehearsal `FAILED` | 2 | 1：favicon connection reset；后续 rehearsal 恢复 |

因此原汇总中“98 次 request budget”、“92 次 implement ok”、“2 条 rehearsal 失败”都是镜像行数，不是独立事件数。“Proxy/API 错误：无”也过强：可以说没有上游 HTTP 状态错误，但存在 2 次本地 proxy BrokenPipe。

`2/100` 是该 GitHub 系列的已知第二个非零结果，不是首个：历史 Run `451174abe760` 已经为 `2/100`。平台未公开 98 个失败项的类型，所以不能把它们精确归因为“实现与测试不匹配”，也不能把官方 timeout 数填为 0。

## 证据与身份边界

- manifest 保存 7 件本地附件的文件名、大小和 SHA-256，不把大型原始附件复制进仓库。
- 平台 token count 为 `23,111,524`，provider totals 为 `23,111,409`，相差 115，两者按不同口径并列，不互相替代。
- `run_duration_seconds=12,904`；`started_at` 到 `finished_at` 的 wall-clock 差为 14,005s。两者同样并列。
- traceability 包含 42 条 interface record，但仅覆盖 8 个 unique requirement ID，全部 `implemented=false`、无 file path、无 tests。这是结构探测结果，不能单独证明产品代码完全未实现。
- 包内 commit `9ff7e750...` 在当前本地对象库和已检查远程 ref 中不可达，源码可复现性未闭合。
- ZIP 未包含与 GitHub task 对应的 binding；Sheet 命名的文件名本身不是失败因果，但不能替代 task-correct binding。
- 因此本 Run 只能保持 `platform_identity_inconclusive`，不能与历史 Run 构成严格 A/B。

## 历史 GitHub Run 比较

| Run | 官方结果 | Requests | Tokens | 费用 | Agent 耗时 | 过程特征 |
|---|---:|---:|---:|---:|---:|---|
| `451174abe760` | `2/100` | 45 | 403,165 | 0.878359 CNY | 581s | 仅 1 个节点后 checkpoint TypeError abort |
| `0564f5955f16` | `0/100` | 465 | 8,510,678 | 10.559866 CNY | 5,584s | 47 节点遍历，cap 8，仅 1 个 verified write |
| `effd5e7777ce` | `2/100` | 838 | 23,111,524 | 18.184308 CNY | 12,904s | 47/47 节点 cap 16，0/47 verified，1 个 900s timeout |

相对 `0564f5955f16`，本 Run 的 score 从 0 变为 2，但 requests 约 1.80 倍、tokens 约 2.72 倍、成本约 1.72 倍、耗时约 2.31 倍。相对 `451174abe760`，得分相同，但成本约 20.70 倍。这不能解读为稳定完成率改善：隐藏 requirements/test snapshot 无 SHA，官方测试明细为空，且身份链未闭合。

可确认的过程结论是：提高单节点 request cap 使 Agent 消耗更多请求和上下文，但仍没有形成节点级外部验证。47/47 cap hit、0/47 verified、一次 timeout 与极低官方通过率共存；官方 98 项失败的精确机制仍未知。

## Agent 层修复建议（本轮不实施）

1. **产品源码 delta 门禁**：以 `frontend/` 和 `backend/` fingerprint 作为 implementation 证据；`.arc/design` 不计产品写入。无 product delta 不得标记 implemented。
2. **Harness 外部验证**：模型 turn 后由 harness 执行 build、start、health、route、DOM/可访问语义和持久化读回；模型自述不计 `verified=True`。
3. **Vertical slice 执行**：按共享数据模型、路由和页面簇聚 requirement，不再对 47 个 atomic node 分别冷启动。优先验证高扇出骨干。
4. **分阶段预算**：将 inspect、implement、verify 预算分离，为 verify 保留不可侵占额度；不再以全局抬高 request cap 替代收敛门禁。
5. **无进展止损**：连续 slice 无 product delta、无外部验证或单位 verified slice 成本超阈值时 hard-stop，不继续遍历全部节点。
6. **身份闭合**：运行时读取 ZIP 内 `agent-build.json`，为 GitHub 产生 task/suite/requirements 正确的专用 binding，并与平台回传身份分层记录。

## Skill 层修复建议（本轮不实施）

- 日志对 `project_map`、`source_read`、`source_cache`、`arc-project-context` 的命中均为 0，ZIP 也不包含 `skills/` 或 project-map/source-cache 文件。provider 的 `prompt_cache_hit_tokens` 不是 project-context Skill 启用证据。本 Run 不能用于评价该 Skill 收益。
- 复用 Octos 现有 Skill/plugin loader 把 `arc-project-context` 真正纳入候选包和 tool registry，不另造加载器；解包后必须有工具可见和受控调用日志。
- project map 应由 harness 主动预计算并注入 slice，包含入口、路由、模型、相关文件及 SHA；source cache 必须以实际减少 provider read requests、返回字符和 prompt tokens 验收，不以本地 cache hit 宣称收益。
- 增加 write-first vertical-slice Skill，限制重复全文读取，在前 2–4 个 requests 内形成 product delta；硬门禁仍由 Agent/harness 负责，不只依赖 `SKILL.md` 指令。
- 引入 evidence-normalizer，强制 stdout/stderr 镜像去重、runtime/workspace/ZIP/platform 身份分类、missing 字段保留 unknown，防止再用原始行数驱动错误优化。

## Phase 4 输入与当前门禁

- 核验 manifest 中 7 件本地证据的 SHA-256，若后续迁移则保留 provenance。
- 补齐平台 generation identity、task snapshot、requirements archive SHA、suite identity 和 task-correct GitHub binding。
- 获取逐测试 ID、result、timeout 类型、Playwright report/trace/screenshots；无法获取时保持 unknown。
- 本轮只做证据归档和阶段 3分析。在身份闭合和结构化失败证据补齐前，仅允许只读诊断，不进行 Agent/Skill 修复、发布或严格 A/B 裁决。
