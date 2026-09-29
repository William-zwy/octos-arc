# ARC-Bench Web BookStack Run `53a102f3ee96` 证据交接

日期：2026-09-30
用途：保存该 Run 的阶段 3/4输入、终态、中间态和只读判断，供后续多 Run 决策使用。
状态：阶段 3/4已闭合；本次不修改 Agent、官方测试或运行时配置，不打包、不上传、不创建新 Run，不触发阶段 5。

## 1. 基本身份与最终结果

| 字段 | 值 |
|---|---|
| Run | `53a102f3ee96` |
| Submission | `362bc0d7b112` |
| 任务 | `arc-bench-web--bookstack` |
| 模型 / reasoning | `deepseek-v4-flash` / `low` |
| 最终状态 | `PASSED` |
| 最终成绩 | `34/34`，score `100` |
| 平台运行时间 | `16537s` |
| 平台 token 口径 | `315086357` |
| 结构化费用 | `161.881459 CNY` |
| 本地 submission ZIP SHA-256 | `9F8EE636363A5BCA75EA9E15E4403C83401965443EB0BC0941BBE6E09ADD890E` |

最终评测使用 `/workspace/submission/public-tests/arc-bench-web--bookstack` 的 34 个 Playwright spec，应用成功启动，未发现 bundled fallback 命中。

## 2. 阶段文件与身份闭合

原始阶段证据位于外部工作区：
`D:\DataMove\codex\worktrees\9015\AI智能体软件工厂黑客松\evidence\arc-bench\runs\53a102f3ee96\`

| 文件 | SHA-256 | 状态 |
|---|---|---|
| `manifest.json` | `E049C5C5C0119DF24C337D5914C9B92A24F4D05D7553AE4741D909D5762255FF` | 阶段 3 |
| `phase4-handoff.json` | `27133CAC5D7428F48F920B18F8C9D85B61E21D6FD66C0369E2FF3E5B9544379C` | handoff |
| `phase4-ack.json` | `010C4CBA24536BDB5F3597374CFBC3F13F7D14D747DBFED90B5400A3819C2276` | received |
| `phase4-result.json` | `06E7DE6AE04106E43CAC3E7DB45BF33AB694FB780A60D5B6AC0D9334DDC73F37` | complete |
| `phase4-result.md` | `EB206C3ADB7B364528B90F146735504AE5399E01EFD30B2A9FB2727F5C0A9594` | complete |

阶段 4 ACK、result 与 handoff 的 `run_id`、`submission_id`、`task_key`、`thread_id`、`manifest_sha256` 全部匹配，阶段 4为只读诊断。

## 3. 中间态与恢复链

实现阶段共 34 个原子节点，28 个直接完成，6 个出现中间失败；中间态不是最终业务结果：

- `REQ-2.2`：900 秒 turn cap；已写入且已验证，立即验收 `4/4`，无需 repair。
- `REQ-4.2.1`：900 秒 cap 后 `6/7`；589 秒 repair 仍失败并触发 10-request guard，后续共享 server/fixture 修复后通过。精确因果为 `strong_candidate`。
- `REQ-5.5.2`：单请求后上游 HTTP 400 `proxy_error` / `unexpected EOF`，来自 `api.taotoken.net`，不是应用断言失败。
- `REQ-6.1.1`：Name 字段填充超时；两次 repair 添加页面路由和 seed 仍为 `12/13`，后续共享路由实现后恢复。具体最终修复因果未完全闭合。
- `REQ-6.1.2`：同类 Name 字段超时；两次 repair 后仍为 `12/13`，后续 draft-save handler 与 dashboard draft heading 修复后恢复。
- `REQ-6.1.3`：初轮 `0/13` 实际由 `/favicon.ico` `ConnectionResetError` 触发；后续 rewrite/repair 与最终全量测试通过。

最终 traceability 为 34/34 passed；midrun 的失败集合仅作时间序列证据，不能覆盖最终 Playwright 结果。

## 4. 已确认与待观察事项

### Confirmed

- 最终 BookStack Web 公开测试 34/34通过。
- 900 秒是单个 Octos turn cap；不是最终 Playwright 10 秒测试超时。
- 全局预算为 51000 秒，实际 16537 秒，未触顶。
- cgroup 上限 2 GiB，峰值 `1,076,064,256` bytes，无 OOM/OOM-kill。
- provider stdout 记录 1272 requests、40,033,246 tokens；与 run JSON 的 315,086,357 platform tokens 属于不同统计范围，不相加。
- 10-request repair guard 独立触发 8 次；postflight 清理 196 个残留进程。
- 阶段 4没有代码、测试、运行时配置修改，没有重跑或上传，没有触发阶段 5。

### Strong candidate

- 单节点 turn 应设置明确的 stop-and-verify 检查点，避免长时间重复探索后撞 900 秒上限。
- repair 请求应优先保留给有具体失败证据的节点，减少无效 full-file exploration 和 full rewrite。
- 服务应使用 PID 级生命周期管理；未知路径应稳定返回 404，避免 favicon 等辅助请求污染验收。
- 共享 route/fixture 修复可能同时恢复多个后续节点，但该因果没有最终源码 diff 完整证明。

### Unknown / provenance gap

- 没有平台 build ID、commit SHA、task snapshot 或上传 ZIP→build 绑定，不能做严格代码归因或 A/B。
- 没有最终生成源码 diff，不能精确证明每个后续 repair 对单个节点的独立作用。
- 没有 favicon 的完整 runtime trace，不能进一步区分应用路由异常与验收环境观测异常。
- 费用字段存在单位冲突：结构化 Run 对象标记 CNY，外部摘要曾将同值写成 USD；不作换算和效率结论。

## 5. 后续多 Run 使用规则

1. 将本 Run 作为 BookStack `34/34`正向基线，不因其他 Run 的局部失败直接回改已通过的认证、创建、页面、草稿、收藏和导航契约。
2. 只合并跨 Run 重复出现且有可观察机制的生成/运行时问题；单次中间 timeout 不自动升级为业务代码缺陷。
3. 后续若要优化 Agent，优先评估效率与恢复机制，并要求 BookStack 完整回归不降分；不能把全局 timeout、模型或预算调整当作业务修复。
4. 后续多 Run 记录必须分别保存任务、submission、ZIP、build、task snapshot 和测试配置，缺失绑定时只能作 Run-local 判断。
5. 代码修改交由 Agent 实现会话；本决策记录只负责证据归档、比较和门禁。

## 6. 证据源

- 原始 Run 对象：`C:\Users\dayuruozhi\Downloads\闻悦源代码-首轮测试-arc-bench-web-bookstack\arcbench-run-53a102f3ee96.json`
- 阶段 4结果：`C:\Users\dayuruozhi\Downloads\闻悦源代码-首轮测试-arc-bench-web-bookstack\arcbench-run-53a102f3ee96-summary.md`
- 最终 Playwright：`C:\Users\dayuruozhi\Downloads\闻悦源代码-首轮测试-arc-bench-web-bookstack\playwright-report-53a102f3ee96.json`
- 阶段 4只读结果：`D:\DataMove\codex\worktrees\9015\AI智能体软件工厂黑客松\evidence\arc-bench\runs\53a102f3ee96\phase4-result.md`