# Phase 3 分析：`b4e114e9c001`

> **ANALYSIS-ONLY / REPOSITORY-SYNC AUTHORIZED（2026-10-01）**：用户已授权将本分析和归一化证据同步到协作分支；仍不授权修改 Agent、Skill、ZIP、requirements、官方测试或启动平台 Run。

## 1. 结论摘要

本 Run 不是官方测试 `0/100`，而是部署就绪门禁失败后的 `0/0`：平台 `start_agent=failed`、`run_tests=pending`，因此没有官方代码质量信号。日志中的 `listening on 0.0.0.0:3000` 只证明 TCP bind callback 到达，不证明平台要求的 HTTP readiness contract 已满足。

最强候选根因不是“平台忽略了已就绪服务”，而是最终产物启动入口漂移：`backend/package.json` 实际启动 `node lib/server.js`，该入口仅让 `GET /api/health` 返回 200，`GET /` 与 `/health` 都进入 JSON 404，也不提供 frontend/dist；同一 ZIP 中能服务根页面和两个 health 路径的 `backend/server.js` 没有被 `npm start` 使用。平台未回流 probe 路径、期望状态、重试响应或进程退出状态，所以不能断言平台一定探测 `/`，但产物的 HTTP readiness/SPA 启动契约缺陷有直接静态证据，证据等级为 **HIGH candidate**。

同时，“代码全部生成完毕”不成立。47 次 `implement ok` 是内部 turn 标签，不是 47 个实现完成：只有 11 个 `verified=True`，36 个未验证，3 个 `wrote=False`；人工保守核验至少 19 个 ok 摘要明确承认未实现、无代码、待后续或未验证，其中至少 3 个 `verified=True` 直接自我否定，另有 3 个 verified 节点明确保留启动、交互或验证缺口。最终 traceability 为 0 interfaces / 0 tests。

## 2. 对外部终态分析的逐项纠错

| 外部判断 | 审计判断 | 纠正理由 |
| --- | --- | --- |
| `65 atomic nodes` | **错误** | run 有 65 个 node-state 记录，其中 18 个 design（含 ROOT）、47 个 implement；Agent flow 明确是 47 个 atomic leaf nodes。 |
| `47 叶子全部实现`、`代码全部生成完毕` | **错误** | 只能确认 47 次内部 `implement ok`；11 verified / 36 unverified、44 wrote / 3 no-write，且人工保守确认至少 19 个摘要自述未完成。 |
| `47 节点逐节点全部被 budget 掐断` | **错误一项** | 独立 cap 是 48：skeleton 1、nudge 1、业务节点 46/47；`REQ-1-1-3` 没有命中 cap。 |
| server 已 listening，因此 runner 判定矛盾 | **因果表述错误** | listening callback 只证明 bind；最终 canonical start 入口不服务 `/`，只服务 `/api/health`。平台 HTTP ready 失败与监听日志并不矛盾。 |
| 推断探针要求 HTTP 200 且路径不匹配 | **方向合理，但需降级为强候选** | 平台 failure reason 和产物契约支持该方向，但 probe 请求、路径、状态码与重试日志均未回流，不能断言具体探针。 |
| 端口差异可能是主因 | **证据较弱** | 最终日志已证明 `PORT/HOST` 生效并监听 `0.0.0.0:3000`；更具体的问题是 canonical entrypoint 不服务根页面/SPA。 |
| rehearsal 证明部署正常 | **不成立** | rehearsal 只记录“builds and starts cleanly”，没有路径、状态码或 final-contract probe；随后平台 ready 失败说明门禁不等价。 |
| 测试超时数量为 0 | **口径错误** | 官方测试未运行，应记 `not reached / not applicable`，不是测试超时 0；Agent turn timeout 才可明确为 0。 |
| 同一个 Sheet 包跑 GitHub 是部署根因 | **不成立；身份风险成立** | 通用 Agent 跨任务是项目目标；文件名本身不会导致部署失败。但 task/suite binding 为空、平台身份缺失，使严格 A/B 与追溯不闭合。 |
| 0 分可用于评价生成代码质量 | **不成立** | 测试未执行，只能评价 deployment gate；不过内部摘要、空 traceability 和入口契约已独立否定“全部完成”。 |

## 3. 部署时间线与产物契约

| 时间（UTC） | 证据 |
| --- | --- |
| `05:53:32` | 业务 node turn 结束；内部 verification 明确官方 acceptance 不可用。 |
| `05:53:33` | rehearsal 仅报告 `app builds and starts cleanly`，无 probe 明细。 |
| `05:53:34` | provider usage 汇总；cgroup current 504,827,904 B、peak 569,958,400 B、max 2 GiB、OOM 事件为 0。 |
| `05:53:36` | postflight 清理残留进程，确认 port 3000 free，frontend/backend 目录存在。 |
| `05:53:37` | frontend build 与 backend npm install 完成。 |
| `05:53:38` | 平台按 `npm start -> node lib/server.js` 启动，打印监听 `0.0.0.0:3000`。 |
| `05:55:39` | 平台以 `template application server did not become ready within 120 seconds` 结束；run_tests 仍 pending。 |

最终产物还存在第二个独立运行契约缺口：frontend `API_BASE` 固定为 `http://127.0.0.1:3001`，而平台实际 backend 监听 3000。即使只修复 readiness，浏览器侧 API 也会指向错误端口。该事实进一步说明内部 `verified`/rehearsal 未覆盖最终产品契约，但本阶段不实施修复。

历史旁证只用于提高候选可信度，不作为严格因果证明：同需求的 `451174abe760` 启动入口显式服务 `/`，`effd5e7777ce` 的启动 router 也显式处理 `/`，两者均进入官方测试；本 Run 同 ZIP 生成的 Sheet 产物 `f1ff68f69dac` 使用 `node server.js` 且处理根路径，也成功进入测试。因此更像本次生成产物的入口/HTTP 契约漂移，而不是该 Agent ZIP 必然无法部署。

## 4. 去重后的执行与成本事实

- 平台 node states：65 条（18 design，含 ROOT；47 implement）；Agent 实际遍历 47 个 atomic leaf nodes。
- 内部标签：47 ok / 0 failed；11 verified / 36 unverified；44 wrote / 3 no-write。
- 人工保守确认至少 19 个 ok 摘要自述未实现、无代码、待后续或未验证；`REQ-1-3`、`REQ-3-2-1`、`REQ-6-6` 三个 `verified=True` 标签直接与“未实现/无代码”摘要矛盾，`REQ-1-1-1`、`REQ-2-2-1`、`REQ-6-2-4` 另有明确启动、交互或验证缺口。
- cap：48 个独立事件；skeleton cap 28 ×1、nudge cap 18 ×1、feature cap 18 ×46。两个 same-error guard 是 skeleton 连续 3 次与 `REQ-1-3` 连续 4 次同错，不是网络错误。
- Agent turn timeout、BrokenPipe、上游 HTTP 402/500、OOM 均为 0；官方测试未执行，官方测试 timeout 不适用。
- provider：958 requests、25,472,522 prompt、665,933 completion、503,425 reasoning、21,912,832 cache hit、26,138,455 total；平台 token_count 26,138,573，差 118；成本 18.864285 CNY。
- cache hit 占 prompt 86.03%、占 total 83.83%，只能说明共享前缀复用，不能证明 Skill 生效、Token 无效或按全价计费。
- 平台 run_duration 为 12,031 秒，started→finished wall clock 为 12,157.131 秒，分列保存，不混为一项。

相对已归档 `effd5e7777ce`，本 Run requests/token/cost/run-duration 约为 `1.14× / 1.13× / 1.04× / 0.93×`，却在 deployment gate 前损失全部预算。由于官方测试未运行，这不是代码质量 A/B，只是“更高资源投入未产生官方测试信号”。

## 5. 身份、测试与可比性边界

- 平台未提供 Agent commit、build ID、generation identity、task snapshot 或 hidden suite identity。
- ZIP 内 `agent-build.json` 给出 build `arc-agent-v1-41b572af40cbfc7982254a32`、commit `7fc462066c29908ac23c18c0c58805d5e664a0cb`、payload tree `3707AD5C...`；同步协作分支后该 commit 已可解析，下载 ZIP 的 `main.py` 与提交 Git blob 逐字节一致。它解决了“源码提交不可达”，但完整 payload 未重建，且这些仍是 archive-derived 证据，不是平台绑定。
- runtime 日志的 `agent_commit=e5e386...` 与 ZIP embedded commit 不同，不能当作 Agent 源码身份。
- post-run template 的 `requirements.yaml` SHA-256 为 `BDC17D23...B0B8F`，与本地 `451174abe760`、`effd5e7777ce` 相同，支持需求文本一致，但不证明 hidden scenario snapshot 相同。
- tests=[]、run_tests=pending、result_path=null；不存在可供分析的官方测试 ID、断言、timeout 或 Playwright trace。
- 最终 traceability 为 `interfaces=[]`、`tests=[]`，不能支持需求覆盖声明。
- submission ZIP 无 `skills/`/`arc-project-context`，日志无 `project_map`、`source_read`、`source_cache` 调用；本 Run 不能评价 Skill 收益。

## 6. 优先级建议（只记录，不实施）

1. **P0：统一唯一 canonical start 入口。** `npm start` 必须同时满足 SPA `GET /`、明确 health endpoint、正确 host/port 和 API 同源；禁止保留“功能入口”和“fallback 入口”二选一漂移。
2. **P0：让 rehearsal 复现平台启动契约。** 必须使用最终 `package.json` 的同一命令与环境，并记录 `GET /`、`GET /health`、`GET /api/health` 的状态码、响应与进程存活；不再以“进程已监听”代替 ready。
3. **P0：消除假收敛。** `ok/wrote/verified` 必须绑定产品源码 delta、build/start、route/DOM/API/持久化探针；摘要承认未完成时强制降为 inconclusive。
4. **P0：修正 budget 策略。** inspect/write/verify 分槽，cap 后不得标记完成；结合 vertical slice 与无进展止损，避免 46 个节点逐一耗尽。
5. **P1：补齐 traceability 与身份链。** 为 GitHub 任务提供正确 binding，并保存 readiness 与测试证据；archive-derived identity 与平台 identity 分列。
6. **P2：Skill 真正打包注册后再评价。** 以 provider read requests、返回字符、首次业务写入位置和 verified slice 成本为指标，不以 prompt cache hit 冒充 Skill 收益。

## 7. 阶段门禁

Phase 4 保持 `pending`，只允许只读诊断。平台 readiness probe 明细、官方测试证据和平台身份均缺失；本地结论不得被解释为已授权修改 Agent/Skill、打包、发布或重跑。

原始 7 件附件仍留在 `C:/Users/dayuruozhi/Downloads/闻悦源代码-首轮测试-hackathon-github/`，仓库仅记录文件名、大小、SHA-256 与 provenance，不复制大型附件。
