# Phase 3 analysis: `f1ff68f69dac`

> **ANALYSIS-ONLY / REPOSITORY-SYNC AUTHORIZED（2026-10-01）**：用户已授权将本分析和归一化证据同步到协作分支；仍不授权修改 Agent、Skill、ZIP、requirements、官方测试或启动平台 Run。

## 已确认事实

- 任务为 `hackathon--sheet`，平台终态为 `FAILED`，得分 `0/100`，feature 结果 `0/24`。
- `run_tests` 为 `completed / Evaluation completed`，因此官方评测已到达；但 `tests=[]`，没有逐测试 ID、断言、timeout 类型、Playwright report 或 trace。官方测试级 timeout 数只能记录为 `unknown`，不能写成 0。
- submission 为 `0c13f59053b0`，本地归档 ZIP SHA-256 为 `9E4484F788B40BD6CC04BA2E4BFF841305E7E7969D92B76B5E8DF60C3624BADB`。
- ZIP 内 `agent-build.json` 声明 commit `7fc462066c29908ac23c18c0c58805d5e664a0cb`、build ID `arc-agent-v1-41b572af40cbfc7982254a32` 和 payload tree `3707AD5C10EECDD56F7372E13AB71553AD68F53ADDF66627213F7994A515CEAA`。这是归档包内身份，不是平台回传绑定。
- Agent 产生 24 次内部 `implement ok` 标签，未出现 `implement FAILED` 或 Agent turn timeout；其中 11 个内部 `verified=True`、13 个 `verified=False`，23 个 `wrote=True`、1 个 `wrote=False`。这些是内部状态标签，不等同于“24 个节点全部实现”或“11 个节点自验通过”。
- 最终 frontend build、backend install 和 port 3000 监听成功。startup rehearsal 第一次出现 `/favicon.ico` ConnectionResetError，第二次通过。
- 没有上游 HTTP 402/500、BrokenPipe、OOM、RuntimeError、TypeError 或 Traceback 证据。

## 去重、事实纠错与对原分析的批判

平台日志同时保留 Agent stdout/stderr 镜像。按时间戳和消息体去重后：

| 指标 | 原始行数 | 独立逻辑事件 |
|---|---:|---:|
| `implement ok` | 48 | 24 |
| `implement FAILED` | 0 | 0 |
| request-budget hit | 54 | 27：skeleton cap 28 × 1、nudge cap 18 × 1、业务节点 cap 18 × 24、rehearsal repair cap 10 × 1 |
| startup rehearsal failure | 2 | 1：favicon ConnectionResetError |

原分析需要以下修正：

1. **“24 节点全部实现”不成立。**只能写成“24 次内部 `implement ok` 标签”。至少 11 个 ok 摘要明确自述未完成、仍需后续、行为未接线或没有写入；另有 1 个摘要存在未解决歧义。平台 feature 仍为 `0/24`，最终 traceability 也是 `{"interfaces":[],"tests":[]}`。
2. **“11 个 Agent 自验通过”证据等级过高。**`REQ-1-2-1` 标记 verified 却承认没有执行 smoke；`REQ-3-1-2` 标记 verified 却承认页面 Ctrl+V/菜单 handler 尚未接线。它们说明内部 verified 语义本身存在假阳性，不只是与隐藏测试“不对齐”。
3. **skeleton 是更直接的假收敛证据。**attempt 1 标记 `wrote=True, verified=True`，摘要和随后 flow 却都明确没有 frontend/backend；nudge 1 同样标记 wrote，却明确自述 no writes。nudge 2 后才出现骨架，harness 随后记录 deterministic fallback 补齐缺失部署文件。
4. **27 次 cap 的计数成立，但“实现均被掐断/文件都写了一半”过度概括。**24/24 业务节点都耗尽 cap 18，说明预算策略系统性失效；但部分 turn 在触顶前确实执行了 build/curl。准确结论是：没有业务节点自然结束，cap 后流程仍发出 ok 标签，无法可靠区分完整、部分和无实现，也没有为独立外部验证保留预算。
5. **不能称“repair 已完成”。**rehearsal repair turn 运行 191 秒，却是 `wrote=False, verified=True` 并触及 cap 10；随后第二次 rehearsal 通过。可以确认的是“重试后恢复”，不能确认代码修复生效，原因也可能是既有 catch-all 或瞬态连接恢复。
6. **`tests=[]` 和 report 404 不表示官方测试未执行。**平台明确记录 `run_tests=completed`。report 404 目前只存在于用户收集的汇总陈述，7 件原始附件中没有独立 HTTP 响应件，因此在 manifest 中标为派生证据。
7. **“新包导致回退”不成立。**相对 `12b3dea74607` 的 `1/100`，本 Run 观察到 `0/100`；需求文本哈希相同增强了可比性，但隐藏 scenario identity、平台 generation identity/build binding 均缺失，最终生成产品也不同。只能写 observed regression，不能形成因果判断。

## 假收敛的直接证据

- 24 个 `implement ok` 摘要中至少 11 个明确报告未完成、仍需后续或行为缺口；`REQ-3-2-1` 另有未解决的命名/工作流歧义，但不计入硬性未完成数量。
- 至少 4 个业务节点标记 `wrote=True`，摘要却明确表示没有写入：`REQ-2-2-1`、`REQ-2-1-2`、`REQ-5-1-1`、`REQ-2-1-4`。
- 两个 `verified=True` 业务节点仍承认验证或行为缺口：`REQ-1-2-1`、`REQ-3-1-2`。
- skeleton attempt 1 同时出现 wrote/verified 标签和“无 frontend/backend”事实冲突；nudge 1 也出现 wrote 标签与 no-write 摘要冲突。
- 因而当前最强根因不是单纯“隐藏测试不对齐”，而是内部 `ok/wrote/verified` 没有与产品源码 delta、build/start 和行为 probe 建立可靠绑定。隐藏测试不透明会放大差距，但不是解释 0 分所必需的唯一假说。

## 证据与身份边界

- manifest 保存 7 件本地附件的文件名、大小和 SHA-256，不把大型原始附件复制进仓库。
- 平台 token count 为 `10,825,873`，provider total 为 `10,825,760`，相差 113；`run_duration_seconds=8,670`，而 started/finished wall-clock 差约 `9,775.709s`。不同口径并列，不互相替代。
- prompt cache hit 占 prompt tokens 约 `84.42%`、占 total tokens 约 `81.47%`。这只能证明大量请求共享可缓存前缀，不能直接等同无效重放、全价 Token 或 Skill 收益。
- deploy_agent 日志称初始化 42 requirements/100 scenarios，但最终 traceability 文件严格为空：0 interfaces、0 tests。它不能支撑需求覆盖或实现完成声明。
- runtime `agent_commit=524c39fc...` 与包内 commit 不一致，不接受为 Agent 源码身份；平台仍未提供 generation identity、build ID 和 task snapshot。
- 同步协作分支后，包内 commit `7fc462066c29908ac23c18c0c58805d5e664a0cb` 已可解析；下载 ZIP 的 SHA-256 仍为 `9E4484...BADB`，其 `main.py` 与该提交 Git blob 逐字节一致。Windows 工作树副本的不同哈希仅来自 checkout 换行转换；尚未执行完整 payload 重建，因此只把状态提升为 archive source commit resolved，不宣称完整可复现或平台绑定。
- 本 Run 和 `12b3dea74607` 的 post-run template 内 `requirements.yaml` SHA-256 均为 `9CDDF67BE50748106289ED158648629A6C50C30A490D0EDA5BD570C557440B96`，runtime requirements content hash 也一致。它支持需求文本相同，但不能证明隐藏生成的 100 scenarios 相同。
- 因此本 Run 只能保持 `platform_identity_inconclusive`，与历史 Run 的比较不是严格 A/B。

## 历史 Sheet Run 比较

| Run | 官方结果 | Requests | Tokens | 费用 | Run 耗时 | 关键特征 |
|---|---:|---:|---:|---:|---:|---|
| `2b6a1f545c37` | `0/100` | 269 | 4,283,384 | 5.677578 CNY | 2,822s | 24/24 节点 cap 8，内部 verified 2 |
| `12b3dea74607` | `1/100` | 429 | 9,742,554 | 9.422114 CNY | 8,518s | 23/24 节点 cap 16，内部 verified 3，1 个 900s timeout |
| `f1ff68f69dac` | `0/100` | 528 | 10,825,873 | 9.167743 CNY | 8,670s | 24/24 节点 cap 18，内部 verified 11，但标签存在直接矛盾 |

相对 `12b3dea74607`，本 Run 的 requests、tokens、成本和耗时约为 `1.231× / 1.111× / 0.973× / 1.018×`，观察分数从 1 变为 0。内部 verified 标签从 3 增至 11，却没有官方收益；这更直接地否定“verified 数量可作为完成率代理”，但由于身份和隐藏 suite 未闭合，不能断言新包导致回归。

相对 `2b6a1f545c37`，requests、tokens、成本和耗时约为 `1.963× / 2.527× / 1.615× / 3.072×`，官方结果仍为 0。继续全局提高 cap 没有形成可观测收益。模板基线分仍只是候选假说；需要同一 snapshot 下 deterministic scaffold 与 scaffold+Agent 的配对 probe 才能验证。

## 根因优先级与后续建议（本轮不实施）

| 优先级 | 根因/候选 | 判断 | 后续门禁 |
|---|---|---|---|
| P0-1 | `ok/wrote/verified` 与产品完成脱钩 | 强证据成立 | product-source fingerprint、harness build/start/route/DOM/持久化 probe 同时闭合，才允许 implemented/verified |
| P0-2 | 逐 atomic node 冷启动且 24/24 全部触 cap | 强证据成立 | 改为 vertical slice；比较重复读取、time-to-first-write、单位 verified slice 成本 |
| P0-3 | inspect/write/verify 共用预算，cap 后仍自动 ok | 强证据成立 | 分预算槽；verify 额度不可侵占；cap 后记 inconclusive，不自动完成 |
| P0-4 | requirement-only 且缺少本地 derived contract probes | 成立 | 建立 route、accessible name、mutation/readback/reload/error/404 probe，并标记 inferred_non_official |
| P1-1 | 最终 traceability 为空 | 强证据成立 | 每个完成 slice 必须有 requirement→file→probe 映射和命令退出码 |
| P1-2 | 候选与平台身份链不闭合 | 强证据成立 | ZIP/task/suite/requirements binding 和平台回传身份分别闭合 |
| P1-3 | project-context Skill 已生效但收益不足 | 不成立 | ZIP 无 Skill，日志无调用；先真实打包注册，再以 provider request/字符/token 降幅验收 |
| P1-4 | Token/cache 效率坍塌机制 | 现象成立，机制待测 | 记录每 slice 输入、重复 read、首次写入请求和外部 verified 成本；cache hit 不作为无效 Token 代理 |
| P1-5 | 模板贡献固定基线分 | 合理候选、未确认 | 相同 snapshot 下运行 deterministic scaffold 与 scaffold+Agent 配对 probe |
| P2 | favicon reset | 次要运行信号 | unknown path 必须返回响应且进程存活；不能当作官方 0 分根因 |

Skill 方面，submission ZIP 不含 `skills/` 或 `arc-project-context`，日志中 `project_map`、`source_read`、`source_cache` 调用均为 0。本 Run 不能用于评价 Skill 收益。后续应复用 Octos 现有 Skill/plugin loader，令 project map 在 slice 前由 harness 主动注入，并以实际减少 provider read requests、返回字符和 prompt tokens 为验收指标；Skill 指令不能代替 Agent/harness 的真实性硬门禁。

## Phase 4 输入与当前门禁

- 核验 manifest 中 7 件本地证据的 SHA-256，若后续迁移则保留 provenance。
- 补齐平台 generation identity、task snapshot、requirements archive SHA 和 suite identity。
- 获取逐测试 ID、result、timeout 类型、Playwright report/trace/screenshots；无法获取时保持 unknown。
- 对 24 个节点建立 product delta、验证命令和退出码映射，区分 internal label、inferred local 和 official evidence。
- 本轮只做本地证据归档和阶段 3 分析。在身份闭合和结构化失败证据补齐前，仅允许只读诊断，不进行 Agent/Skill 修复、发布或严格 A/B 裁决。

本文件当前为 **LOCAL-ONLY / UNCOMMITTED**；不得将相对链接或本地路径表述为远程可用归档。
