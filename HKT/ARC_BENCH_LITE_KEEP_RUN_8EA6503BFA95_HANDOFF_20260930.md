# ARC-Bench Lite Keep Run `8ea6503bfa95` 证据交接

日期：2026-09-30
用途：保存该 Run 的阶段 3/4 输入、终态、中间态和只读判断，供后续多 Run 决策使用。
状态：阶段 3/4已闭合；本次不修改 Agent、官方测试或运行时配置，不打包、不上传、不创建新 Run，不触发阶段 5。

## 1. 基本身份与最终结果

| 字段 | 值 |
|---|---|
| Run | `8ea6503bfa95` |
| Submission | `6be3ce5a778e` |
| 任务 | `arc-bench-lite--keep` |
| 模型 / reasoning | `deepseek-v4-flash` / `low` |
| 最终状态 | `FAILED` |
| 最终成绩 | `18/32`，score `56.2` |
| 最终失败 | 14 项，全部 `timedOut`，无 failed assertion 状态 |
| 平台运行时间 | `20611s` |
| 平台 token 口径 | `432984489` |
| 结构化费用 | `215.543912 CNY` |
| 本地 submission ZIP SHA-256 | `9F8EE636363A5BCA75EA9E15E4403C83401965443EB0BC0941BBE6E09ADD890E` |

入口 `main.py`、前端 build、后端启动和最终 Playwright 均到达；本 Run不是 Agent 未启动，也没有 OOM 或全局时间预算耗尽证据。

## 2. 阶段文件与身份闭合

原始阶段证据位于外部工作区：
`D:\DataMove\codex\worktrees\9015\AI智能体软件工厂黑客松\evidence\arc-bench\runs\8ea6503bfa95\`

| 文件 | SHA-256 | 状态 |
|---|---|---|
| `manifest.json` | `437048B007EC797D83F8A6784CEEE261F6F01FEF46206FCB92716C054A0CCBCA` | 阶段 3 |
| `phase3-analysis.md` | `B0D4A9218D17A1E158D3C3EEDFD33579B77295229D0AA1C73C4333B70A055D70` | 阶段 3分析 |
| `phase4-handoff.json` | `601F9AF6233CA65186F82B29477A29B1FBFF4E425D0207BCC1AB39DC73A8F018` | handoff |
| `phase4-ack.json` | `F5770BA9414DACF53D1EE3C7B5F4212B4E68617601D4FED70ED77C7A98757F0E` | received |
| `phase4-result.json` | `696C3588EE779A09BD1DF9BD832CE3B8AC5EBAC7E87BE585EDD2B34E623D1D82` | complete |
| `phase4-result.md` | `DF3930EEE38FCE3F8C8361A81200AC56CD06783A36879D8F57F4D7BFAA47658E` | complete |

阶段 4 result 的 manifest SHA、handoff、ACK、result 身份字段均匹配。路由仍标记 `needs_reconciliation`，原因是旧 Keep handoff `32e08aaca2e4` 存在缺失身份字段的晚到结果；本 Run 的阶段 4是在用户明确触发后完成的，注册表没有被静默修改。

## 3. 最重要的阶段 3判断：内部验收套件错配

Run 的实际任务是 `arc-bench-lite--keep`。但在 `/workspace/tests` 找不到 spec 后，Agent 选择了：

`/workspace/submission/public-tests/arc-bench-web--keep`

因此内部 `29/32` 只验证了 Web Keep 套件，不是 Lite Keep 套件，不能作为本 Run 的通过预测。内部 round 0/1均为 `29/32`，失败节点为 Web 套件的 `REQ-2.6.1`、`REQ-2.7.4`、`REQ-2.7.5`；最终 Lite Keep 官方 suite 是 `18/32`。

该问题是 confirmed harness/orchestration defect，优先级高于继续调大 timeout：suite identity 必须 fail-closed，找不到匹配 spec 时应报告无法验收，不能自动选择同名但不同 competition 的测试目录。

## 4. 最终失败分组与阶段 4结论

### Confirmed UI/状态契约问题

- `REQ-2.3.1`：测试等待 `Note trashed` button；模板虽执行 DELETE 并显示 `Note deleted` status/Undo，但没有测试要求的可访问状态契约。
- `REQ-2.5.1`–`REQ-2.5.4`：note card 内操作名为 `Archive note`，测试要求精确的 `Archive`；后端 archive/unarchive 路径存在，不能把它归因为 PATCH 缺失。
- `REQ-2.6.1`：note card 内使用 `Background options`，测试要求 `Change color`；颜色后端路径存在，但 per-note accessible name 不匹配。
- `REQ-2.7.1`、`REQ-2.7.2`：checkbox 位于 `Label editor`，测试在 `Note editor`作用域内寻找 `Work`；属于编辑器作用域/可访问语义不匹配。
- `REQ-2.7.4`：`Call dentist created` 数据中已有 `Reminders`，但 note card 不渲染 labels 文本，导致卡片断言不可见。
- `REQ-3.1`：搜索建议渲染为 `role=option`，测试要求 listbox 内的 button `Reminders`。
- `REQ-4.1`、`REQ-4.2`：顶层按钮 accessible name 为 `Settings menu`，测试要求精确的 `Settings`，导致设置菜单无法打开。

### Strong candidate，暂不直接升级为确定代码根因

- `REQ-2.8.1`、`REQ-2.8.3`：模板 seed 中 `Meeting agenda 2.8.1` 已是 `pinned=true`，`Meeting agenda created` 也已预存在且 pinned；这与测试前置条件冲突，并可能造成 first-match 选中错误记录。seed 污染已确认，但具体浏览器选择顺序与单项失败因果仍为 strong candidate。

### 运行过程风险，不是 14 项最终失败的替代解释

- 5 个 implementation turn 达到 900 秒上限；`REQ-2.7.1`/`REQ-2.7.4` repair 分别在 584/599 秒中断。
- `REQ-2.6.2` repair 发生一次上游 `proxy_error` / `unexpected EOF`。
- request-budget-10 guard 触发 13 次；postflight 清理 402 个残留进程。
- 这些因素降低了修复收敛率，但没有证据证明它们单独造成最终 14 个 locator/state timeout。

## 5. 资源与评测边界

- Agent 自报预算 48000 秒，Run 实际 20611 秒；不是全局预算耗尽。
- 最终测试使用 1 worker、10 秒单测 timeout，Playwright 版本 1.57.0。
- provider stdout：1180 requests、34,526,353 tokens；Run JSON：432,984,489 platform tokens；两种统计范围不相加。
- 没有平台 build ID、commit SHA、task snapshot 或上传 ZIP→build 绑定，不能做严格源码归因或 A/B。
- 没有平台原生 trace、HAR、截图和最终 `/workspace/tests` source fingerprint；部分初始 DOM/seed 运行顺序仍无法完全重建。

## 6. 后续多 Run 决策规则

1. 先修正内部 suite identity fail-closed，再评估 UI 契约；不能继续用 Web Keep 的 29/32作为 Lite Keep 的自验依据。
2. 删除状态、归档/颜色动作、标签作用域、卡片标签可见性、搜索建议 role、Settings accessible name 可作为后续 Agent 条件化契约候选。
3. 置顶问题先保留 seed/first-match 风险，除非出现相同 seed 与相同 locator 的独立复现，不直接扩大为全局 pin 修复。
4. 不能因为本 Run 失败就回改已在 BookStack `53a102f3ee96` 通过的通用认证、创建、页面和草稿契约；后续修改必须做跨任务回归。
5. 多 Run 输入完成前不派发最大适用化 Agent 修改；代码修改必须交给 Agent 实现会话。
