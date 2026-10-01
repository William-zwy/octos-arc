# Phase 3 analysis: `12b3dea74607`

## 已确认事实

- 任务为 `hackathon--sheet`，平台终态为 `FAILED`，得分 `1/100`，feature 结果 `0/24`。
- `run_tests` 为 `completed / Evaluation completed`，因此官方评测已到达；但 `tests=[]`，没有逐测试 ID、断言、timeout 类型、Playwright report 或 trace。
- submission 为 `019c8cb3d590`，本地归档 ZIP SHA-256 为 `0E98E7E0DFCF4F893A5CFCE0B8CD8D40168E7EC1FFE505A744E1097FE18FB7C5`。
- ZIP 内 `agent-build.json` 声明 commit `9ff7e750657a1d5c1ba67f71651ed9fe0d56c5c5`、build ID `arc-agent-v1-747e10178d68748225a086dd` 和 payload tree `E022098B6B9B4647D2EA6E5D4C2754845AA161A91DF10D16550A1DD969312DBF`。这是归档包内身份，不是平台回传绑定。
- Agent 遍历了 24 个节点：23 次内部 `implement ok` 标签，`REQ-3-1-1` 一次 900s timeout。所有 24 个节点均为 `wrote=True`，其中仅 3 个 `verified=True`，其余 21 个 `verified=False`。
- skeleton attempt 1 为 `wrote=True, verified=True`；startup rehearsal 一次即通过，随后 frontend build、backend install 和 port 3000 监听成功。
- 无上游 HTTP 402/500、quota 中断或 OOM 证据；存在 1 次本地 `llm_proxy` BrokenPipeError。

## 去重与事实纠错

平台日志同时保留 Agent stdout/stderr 镜像。按时间戳和消息体去重后：

| 指标 | 原始行数 | 独立逻辑事件 |
|---|---:|---:|
| request-budget hit | 48 | 24：skeleton cap 20 × 1、节点 cap 16 × 23 |
| `implement ok` | 46 | 23 |
| `implement FAILED` | 2 | 1：`REQ-3-1-1` |
| rehearsal `FAILED` | 0 | 0；一次 startup rehearsal 即通过 |

因此原汇总中的“46 次 implement ok”“48 次 request budget”和“rehearsal 4 次全部通过”都混入了镜像或 keepalive 口径。更准确的表述是：23 个节点内部标记 ok，1 个节点 timeout；23/24 个可完成节点全部触及 cap，rehearsal 只有 1 次独立执行且成功。官方 99 项失败的类型和 timeout 数仍为 `unknown`。

内部标签还存在假收敛：23 个 `implement ok` 摘要中至少 10 个明确自述“未实现”“只部分应用”“仍需下一轮/额外预算”。`REQ-1-3-2` 虽被标记 `verified=True`，摘要仍报告 404 并要求重新 build/start/验证 route。因此 `ok`/`verified` 只能作为 Agent 内部弱证据，不能等同产品完成；差距也不能集中归因于唯一的 `REQ-3-1-1` timeout。

## 证据与身份边界

- manifest 保存 7 件本地附件的文件名、大小和 SHA-256，不把大型原始附件复制进仓库。
- 平台 token count 为 `9,742,554`，provider totals 为 `9,742,442`，相差 112；`run_duration_seconds=8,518`，而 started/finished wall-clock 差约 9,628 秒。不同口径并列，不互相替代。
- traceability 只有 9 条 interface record，覆盖 2 个 unique requirement ID，全部 `implemented=false`、无 file path、无 tests。这是结构探测结果，不能单独证明产品代码完全未实现。
- 日志中的 runtime `agent_commit=39107edc...` 与包内 commit 不一致，不接受为 Agent 源码身份；平台仍未提供 generation identity、build ID 和 task snapshot。
- 包内 commit `9ff7e750...` 在当前本地对象库和已检查远程 ref 中不可达，源码可复现性未闭合。
- post-run template 中的 `requirements.yaml` 与若干历史 Sheet template 内容哈希一致，只能支持需求文本一致；它不能替代平台 requirements SHA，也不能证明隐藏生成的 100 scenarios 相同。
- 因此本 Run 只能保持 `platform_identity_inconclusive`，不能与历史 Run 构成严格 A/B。

## 历史 Sheet Run 比较

| Run | 官方结果 | Requests | Tokens | 费用 | Agent/Run 耗时 | 过程特征 |
|---|---:|---:|---:|---:|---:|---|
| `39626bbcf702` | `0/100` | 254 | 3,307,706 | 3.605376 CNY | 1,338s | 生成与部署到达，业务分为 0 |
| `2b6a1f545c37` | `0/100` | 269 | 4,283,384 | 5.677578 CNY | 2,822s | 24/24 节点 cap 8，2 个业务节点 verified |
| `12b3dea74607` | `1/100` | 429 | 9,742,554 | 9.422114 CNY | 8,518s | 23/24 节点 cap 16，3 个业务节点 verified，1 个 900s timeout |
| `002c882794af` | `1/100` | 1,657 | 约 77.34M | 31.934054 CNY | 16,903s | 历史已出现同分结果 |

相对 `2b6a1f545c37`，本 Run 的 requests、tokens、成本和耗时约为 `1.59× / 2.27× / 1.66× / 3.02×`，业务 verified 节点只从 2 增至 3。相对历史同为 `1/100` 的 `002c882794af`，本 Run 成本和耗时较低，但候选包、平台身份和隐藏测试 snapshot 不闭合，不能归因为本次改动。

所以 `1/100` 只能称为完成率的弱正向、探索性信号，不是 Sheet 首次得分，也不足以确认“实质进展”。可以确认的是生成/部署可靠性提高；不能确认提高 request cap 对官方完成率存在稳定因果收益。23 个完成节点全部触顶且仅 3/24 verified，说明继续全局抬高 cap 不是优先方案。

## Agent 层修复建议（本轮不实施）

1. **产品源码 delta 门禁**：以 `frontend/`、`backend/` fingerprint 作为 implementation 证据；`.arc/design` 不计产品写入，无 product delta 不得标记 implemented。
2. **Harness 外部验证**：模型 turn 后由 harness 执行 build、start、health、route、DOM/可访问语义和持久化读回；模型自述不计 `verified=True`。
3. **Vertical slice 执行**：按共享数据模型、路由和页面簇聚 requirement，优先完成高扇出骨干，不再逐 atomic node 冷启动。
4. **分阶段预算**：inspect、implement、verify 分开计数，为 verify 保留不可侵占额度；达到只读阈值却无 product delta 时压缩上下文或止损，不全局继续抬 cap。
5. **无进展 hard-stop**：连续 slice 无 product delta、无外部验证或单位 verified slice 成本超阈值时停止，保留终版预算。
6. **身份闭合**：运行时读取 ZIP 内 `agent-build.json`，并把 task/suite/requirements binding 与平台回传身份分层记录。

## Skill 层修复建议（本轮不实施）

- ZIP 不含 `skills/` 或 `arc-project-context`，日志中 `project_map`、`source_read`、`source_cache` 调用均为 0。本 Run 不能用于评价该 Skill 收益。
- 复用 Octos 现有 Skill/plugin loader 把 `arc-project-context` 真正注册到运行时，不另造加载框架；解包后必须有 tool registry 和受控调用日志证据。
- project map 应由 harness 在 slice 前主动生成并注入；source cache 必须以实际减少 provider read requests、返回字符和 prompt tokens 验收，不能用本地 cache hit 或 provider prompt cache 命中冒充收益。
- write-first vertical-slice Skill 应限制重复全文读取，并要求前 2–4 个 requests 形成 product delta；完成真实性仍由 Agent/harness 硬门禁保证。
- evidence-normalizer 应统一 stdout/stderr 镜像去重、ZIP/runtime/workspace/platform 身份分类和 unknown 保留。

## Phase 4 输入与当前门禁

- 核验 manifest 中 7 件本地证据的 SHA-256，若后续迁移则保留 provenance。
- 补齐平台 generation identity、task snapshot、requirements archive SHA 和 suite identity。
- 获取逐测试 ID、result、timeout 类型、Playwright report/trace/screenshots；无法获取时保持 unknown。
- 对 24 个节点建立 product delta、验证命令和退出码映射，区分 inferred local 与 official evidence。
- 本轮只做证据归档和阶段 3分析。在身份闭合和结构化失败证据补齐前，仅允许只读诊断，不进行 Agent/Skill 修复、发布或严格 A/B 裁决。
