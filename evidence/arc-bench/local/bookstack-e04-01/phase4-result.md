# 阶段4诊断结果：arc-bench-lite--bookstack 本地执行

## 结论

本结果只审阅本地执行 `bookstack-e04-01`，关联事项为 `P5-017`。它不是 ARC-Bench 官方 Run，`platform_run_id=null`，也没有与平台 Run `6d41952769f7` 合并。

本地 runner 最终状态为 `completed`，34 个原子测试中通过 13 个、失败 21 个，完成率 `13/34 = 38.2%`。这个数字不能作为干净的 Agent 质量分数：前 23 个原子节点的 implement turn 以 `octos turn timed out` 结束，之后 11 个节点从 `REQ-6.1.1` 开始受 HTTP 429 配额耗尽影响。

## 已确认事实

- 输入是冻结的 `arc-bench-lite--bookstack` 任务和 34 个 spec 文件。
- 本地 runner 在 `2026-09-23 07:55:47` 开始，在 `2026-09-23 11:00:59` 完成，观测墙钟时间约 11112 秒。
- full-suite round 0 为 `13/34`，失败节点为：

  `REQ-2.1`、`REQ-2.2`、`REQ-3.1`、`REQ-4.3.1`、`REQ-4.3.2`、`REQ-4.5.1`、`REQ-5.3.1`、`REQ-5.3.2`、`REQ-5.4.1`、`REQ-5.6.1`、`REQ-6.1.1`、`REQ-6.1.2`、`REQ-6.1.3`、`REQ-6.2.1`、`REQ-6.3.1`、`REQ-6.3.2`、`REQ-7.1`、`REQ-7.2`、`REQ-8.1`、`REQ-8.2`、`REQ-9.1`。

- full-suite round 1 仍为 `13/34`，日志明确为与上一轮相同失败后停止 repair。
- `llm-usage.jsonl` 可独立核验为 427 个请求、15,463,401 prompt tokens、262,594 completion tokens、15,725,995 total tokens。
- 首个配额错误出现在 `REQ-6.1.1`，`run.log` 第 1526 行附近；日志中有 72 条配额相关记录，错误为 `HTTP 429 insufficient_quota`。
- 生成快照的 Agent identity 为 build `arc-agent-v1-16b029ef0dfee566a03d3c39`、commit `e04db1e40084cfa7b50dce64305f9bc9c59acccb`、payload tree SHA `92FBC2E2B22A1C32D39C3B44E13E2E3B29BFA5489A7E8AF670F1C24BEACC3BE0`。

## 关键代码问题：REQ-2.2

本地生成代码中，`backend/src/server.js` 只有 `GET /login`（第 151 行附近），没有 `POST /login`、密码校验或 session 写入。与此同时，`frontend/src/app.js` 会向 `/login` 发起 POST，`interfaces.json` 也把 REQ-2.2 的 `POST /login` 标为 `implemented=false`。`db.json` 中虽然存在用户昵称 `BookStack User` 和对应邮箱，但这不能弥补后端登录处理缺失。

因此可以确认：REQ-2.2 在本地生成快照中存在代码级缺口。不能进一步把所有依赖登录的失败都无条件归因于这一处，因为本轮后半段还受到配额耗尽和实现 turn 截断影响。

## 需要更正的旧口径

1. “17 个 implement turn 被截断”不准确。原始 `run.log` 显示 23 个唯一原子节点出现 `octos turn timed out`，范围为 `REQ-1.1` 到 `REQ-5.6.1`。
2. “12 个节点受 429 影响”不准确。实际是 11 个叶子节点：`REQ-6.1.1`、`REQ-6.1.2`、`REQ-6.1.3`、`REQ-6.2.1`、`REQ-6.3.1`、`REQ-6.3.2`、`REQ-7.1`、`REQ-7.2`、`REQ-8.1`、`REQ-8.2`、`REQ-9.1`。
3. `error-analysis.json` 的 `other=88`、`playwright-timeout=64`、`api=24`、`locator=2` 是分类记录数，含重复日志、父节点汇总和测试失败汇总，不能直接当作独立根因数。
4. 外部诊断材料中关于平台 Run `6d41952769f7`“同包且 REQ-2.2 失败”的说法不受现有平台证据支持。平台 Run 的最终失败节点是 `REQ-6.1.1`、`REQ-6.2.1`、`REQ-7.2`、`REQ-8.1`，且其运行时自报 identity 与本地 e04 identity 不同；两者必须独立记录。

## 平台对照边界

平台 Run `6d41952769f7` 的阶段4结果为 `30/34`、score `88.2`。它只能作为独立的官方结果和身份对照，不能证明本地执行使用了同一个上传包，也不能覆盖本地 13/34 的资源污染事实。平台 Run 的 runtime identity 是 build `arc-agent-v1-9d7c83b9ce8e3c381db3a3a9`、commit `adfe39832dd3d3098efd0a585cd2857f3ca7bc29`、payload tree SHA `09723C6BAF032F94A50DDA670523899A3BBC06908EB8FD8A59B53B49183C3DAA`。

用户提供的 meter 口径“1671 requests、约 57.88M tokens、约 24.98 CNY”不在本地已收集原始文件中，本次不将其写成独立核验事实。

## 后续建议边界

这些是交给阶段5的建议，不是阶段5已执行结论：

- 优先修复并验证 `POST /login`、密码校验和 session 持久化。
- 在足额 API 配额和干净数据库状态下重新获得可比的生成质量样本。
- 将 implement turn 的请求/时间预算、repair 剩余时间和 API 配额分别观测，避免把资源失败误记为产品失败。
- 下一次本地复现只增加针对登录及首个登录后流程的 DOM、网络和服务端证据，不修改官方测试。

本阶段只读完成，未创建 Run、未重跑测试、未上传、未修改 Agent/官方测试/ZIP/配置，也未执行阶段5。

<!-- PHASE4_RESULT: complete -->
