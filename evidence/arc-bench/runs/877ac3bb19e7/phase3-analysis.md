# Phase 3 分析：`877ac3bb19e7`

> **ANALYSIS-ONLY / REPOSITORY-SYNC AUTHORIZED（2026-10-01）**：用户已授权将本分析和归一化证据同步到协作分支；仍不授权修改 Agent、Skill、ZIP、requirements、官方测试或启动平台 Run。

## 1. 结论摘要

`13/100` 是可信的平台聚合终态：`deploy_agent`、`start_agent`、`run_tests` 均为 completed，run 对象明确记录 passed 13 / failed 87、feature 3/47。它是当前本地已归档、已比较的 GitHub Run 中最高观测分，也是目前最强的正向信号；但平台没有回传 hidden suite snapshot、测试 ID、Agent build binding 或逐项断言，因此不能外推为平台全部历史最高，也不能将 11 分增量严格归因于新包或某一修复。

外部汇报最大的事实错误在 rehearsal：不是“首次失败、两次 repair 后后端就绪”，而是三次均以 `/favicon.ico` ConnectionResetError 失败，最终 `giving up; submitting as-is`。两个 repair 都打出 `wrote=True / verified=True` 标签，但 repair 1 只增加 lockfile 且没有复现缺陷，repair 2 更明确说没有把拟议修改写入 `backend/server.js`。随后 runner 的 postflight build/start 成功并进入官方测试，说明平台部署成功不能归功于这两个 repair，也再次证明内部 `verified` 语义不可靠。

47 次 `implement ok` 也不等于 47 个节点实现完成：只有 33 个 wrote、11 个 verified；46/47 业务节点命中 cap 18。保守审计至少 17 个 ok 摘要明确承认未实现、无功能代码、仍需后续或未验证，至少 8/11 个 verified 摘要仍包含 seed 污染、端口冲突、启动失败、验证中断或等待 harness 等实质缺口。最直接例子是 `REQ-4-3-2`：`wrote=False / verified=True`，摘要却说 “no verified feature” 且“must not claim completion”。平台 feature 仅 3/47，与假收敛风险一致。

## 2. 对外部终态分析的逐项纠错

| 外部判断 | 审计判断 | 纠正理由 |
| --- | --- | --- |
| `65 节点 / 47 implement 叶子` | **可接受，但需固定口径** | 65 是平台 node-state 总数，含 18 个 design（含 ROOT）和 47 个 implement；Agent flow 的 atomic leaf nodes 是 47。 |
| `47 implement ok` 等于生成完成 | **错误** | ok 是 turn 返回标签；33 wrote / 14 no-write、11 verified / 36 unverified，且至少 17 个摘要自述未完成。 |
| `11 verified=True` 是自验通过 | **错误** | 至少 8 个 verified 摘要保留实质缺口；`REQ-4-3-2` 甚至明确否定自己已完成。 |
| request-budget 独立事件 49 | **成立** | 去重后为 skeleton cap 28 ×1、feature cap 18 ×46、rehearsal repair cap 10 ×2；唯一未见 feature cap 的是 `REQ-1-1-2`。 |
| rehearsal 1/3 失败，repair 1/2 后端就绪 | **严重错误** | attempt 1、2、3 全部失败；两个 repair 都未证明有效产品修复，最后明确 submitting as-is。 |
| 部署成功并执行官方测试 | **成立** | runner postflight 完成 build/install，`npm start -> node server.js` 在 3000 启动，run_tests completed 并报告 13/87。 |
| passed 13 是“逐条真实测试已核” | **过度表述** | 13/87 是可信的平台聚合结果；但 tests=[]、测试 stdout/report 不回流，无法核验哪些用例、断言或 timeout。 |
| 官方测试超时为 0 | **不成立** | 只能确认 Agent turn timeout 为 0；87 个官方失败中的 timeout 数量仍为 unknown。 |
| Proxy/API 错误为无 | **不准确** | 有 1 次本地 `llm_proxy` BrokenPipe，后续继续；无 402/500 和 octos turn timeout。 |
| GitHub 系列历史最高 | **需限定范围** | 在当前已归档/已比较的 GitHub Run 集合中最高成立；不能外推到未归档的平台全部历史。 |
| 新包已证明带来正向收益 | **只能称 observed improvement** | 13 分远高于已归档的 2 分上限，但 hidden suite identity、task snapshot 和平台 Agent binding 缺失，不能形成严格 A/B 因果结论。 |
| 9 件均为独立证据 | **不准确** | 物理文件 9 件，但 midrun logs 与 final logs 字节完全相同，只有 8 份唯一内容；且目录没有 final traceability。 |

## 3. rehearsal、部署与官方测试时间线

| 时间（UTC） | 证据 |
| --- | --- |
| `11:27:57–11:27:58` | rehearsal 1/3：`GET /favicon.ico` ConnectionResetError。 |
| `11:29:48` | repair 1 返回 ok/verified，但摘要只确认增加 lockfile、没有复现缺陷；随后 rehearsal 2/3 立即同错失败。 |
| `11:31:46` | repair 2 返回 ok/verified，但摘要承认拟议 server 修改未写入；rehearsal 3/3 再次同错，随后 giving up/submitting as-is。 |
| `11:31:49–11:31:50` | runner postflight 确认 frontend/backend，frontend build、backend install 完成；canonical `node server.js` 在 3000 启动并打印 single-origin。 |
| `11:48:05` | 平台结束 evaluation，聚合结果 13/100、feature 3/47。 |

最终产物确实比 `b4e114e9c001` 的 API-only canonical start 更符合平台契约：本 Run 的 `npm start` 使用 `backend/server.js`，同一服务同时提供根页面、frontend/dist 和 `/api/health`，前端使用相对同源 API 路径。两个上传包除 `main.py` 与 `agent-build.json` 外一致；新拉取的源码进一步确认，`3d6713b1` 相对 `7fc46206` 只在 `ARCHITECTURE_CONTRACT`、`SKELETON_PROMPT` 和 `NODE_PREAMBLE_EXTEND` 增加 single-origin/相对 `/api` 提示，并增加对应测试，没有新增 runtime harness 强制门禁。因此更准确的强关联候选机制是 **prompt-level architecture contract**；但生成具有随机性，平台 readiness probe 未公开，不能写成唯一因果已经证明。

## 4. 去重后的执行、成本与完成度事实

- 平台 node states：65 条（18 design，含 ROOT；47 implement）；Agent 实际遍历 47 个 atomic leaf nodes。
- 内部标签：47 ok / 0 failed；9 wrote+verified、24 wrote+unverified、2 no-write+verified、12 no-write+unverified。
- 46/47 业务节点命中 cap 18，另有 skeleton cap 28 ×1、rehearsal repair cap 10 ×2，共 49 个独立 cap；这说明 cap 仍是系统性终止条件，不是自然完成边界。
- 至少 17 个 ok 摘要明确自我否定；至少 8/11 个 verified 摘要仍有实质缺口。不能用 ok、wrote 或 verified 估算完成率，平台 feature 3/47 才是本 Run 可用的官方聚合完成信号，但具体三个 feature 未公开。
- provider：941 requests、21,331,117 prompt、639,432 completion、488,333 reasoning、18,382,080 cache hit、21,970,549 total；平台 token_count 21,970,646，差 97；成本 16.440548 CNY。
- cache hit 占 prompt 86.18%、占 total 83.67%，只说明共享前缀复用，不证明 Skill 生效、Token 浪费或全价计费。
- run_duration 9,871 秒与平台 started→finished 10,850.241 秒分列保存；后者包含约 16 分钟 evaluation 尾段，不能都称为 Agent 耗时。
- Agent turn timeout、上游 HTTP 402/500、OOM 为 0；有 1 次非致命 BrokenPipe。官方 87 个失败的类型和 timeout 数量 unknown。
- 物理归档 9 件，但 midrun/final logs 完全相同；只有 midrun 空 traceability，没有 final traceability。不能用平台“initialized 65 requirements and 100 scenarios”替代最终映射。

## 5. 横向比较与因果边界

相对 `effd5e7777ce` 的 2/100，本 Run 以约 `0.951×` Token、`0.904×` 成本和 `0.765×` run_duration 获得 `6.5×` 通过项；成本/通过项从约 9.092 CNY 降至 1.265 CNY，是显著的观测效率改善。它不是全历史资源效率最佳：早期 `451174abe760` 虽只有 2 分，但成本低很多；本 Run 相对该样本仍消耗约 `54.5×` Token、`18.72×` 成本和 `16.99×` 时间。

`0564f5955f16`、`effd5e7777ce`、`b4e114e9c001`、本 Run 的 runtime requirements hash 相同，本 Run template 内 `requirements.yaml` SHA-256 也与已归档 GitHub 模板一致，增强需求输入可比性；但 platform task snapshot、hidden scenario identity、suite key 和逐测试 ID 均缺失。因此结论应是：**目前最强的正向观测信号，但不是严格 A/B，也尚未证明 13 分稳定可复现。**

ZIP 内 `agent-build.json` 给出 build `arc-agent-v1-0a4644eeb9d2538950716257`、commit `3d6713b1378af074600223865b40beb91c5957fc` 和 payload tree `0BE08F...`。同步协作分支后，该 commit 已可解析，父提交为 `7fc462066c29908ac23c18c0c58805d5e664a0cb`；下载 ZIP SHA-256 与归档值一致，ZIP 内 `main.py` 与该提交 Git blob 逐字节一致。Windows 工作树副本的不同哈希仅来自 checkout 换行转换。由此可将候选状态提升为 archive source commit resolved，但完整 payload 尚未重建，平台也未回传 binding。runtime `agent_commit=d98f8d3...` 是生成 workspace 身份，不是上传 Agent 源码身份。Sheet 命名本身不是运行根因，但缺 task-correct binding 会制造追溯歧义。

## 6. 优先级建议（只记录，不实施）

1. **P0：保留 single-origin canonical start 约束。** 下一候选必须以唯一 `npm start` 同时提供 `/`、frontend 静态资源、明确 health 和相对 `/api`；这是本轮相对部署失败样本最可信的正向机制。
2. **P0：修正 rehearsal 和 verified 的真实性。** 三次 rehearsal 均失败就必须记录 failure/inconclusive；没有产品源码 delta 的 repair 不得标 completed；模型自述与标签冲突时以外部证据为准。
3. **P0：验证移到 harness。** 使用最终启动命令和 grader-like 环境，由 harness 固定验证 build、start、`GET /`、health、API、未知路径、持久化和最小 DOM 契约；模型不能自报 verified。
4. **P0：继续执行 product-delta、vertical slice、inspect/write/verify 分预算和无进展止损。** 46/47 节点仍以 cap 结束，13 分并未消除系统性假收敛和上下文自旋。
5. **P1：闭合 task-correct binding 和平台身份链。** 分离 Sheet/GitHub 命名，记录可达源码 commit、payload、ZIP、requirements 与 suite；runtime workspace HEAD 不得冒充 Agent commit。
6. **P1：在同一需求/隐藏快照条件下重复短探针。** 先确认 13 分与 single-origin 部署可复现，再决定是否扩大运行预算；不得因一个高分样本直接认定因果。
7. **P1：Skill 必须真实打包、注册、调用后再评价。** 本 ZIP 没有 `skills/arc-project-context` 或 `SKILL.md`，日志没有 `project_map`/`source_read`；内联 `_READ_CACHE` 不等于 Skill 接入。
8. **P2：继续降低 Token/通过项。** 本轮相对 effd 明显改善，但相对早期低成本样本仍昂贵；prompt cache hit 不能替代请求数、首次业务写入位置和 verified slice 成本指标。

本阶段不授权 Agent/Skill 修改、重新打包、发布或平台 Run。Phase 4 仍为 pending，只允许只读诊断。
