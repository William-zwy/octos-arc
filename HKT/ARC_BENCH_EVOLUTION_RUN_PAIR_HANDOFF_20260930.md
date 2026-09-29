# ARC-Bench Evolution 配对 Run 证据交接

日期：2026-09-30
用途：为后续多 Run 决策提供可追溯的阶段 3/4 事实、根因边界和合并规则。
范围：`a774fb34f1b6`（BookStack Lite）与 `82a833cabe9e`（Keep Lite）。
状态：阶段 3/4 均已闭合；本次未修改 Agent、官方测试、源 ZIP，也未启动平台 Run。

## 1. 结论摘要

两个 Run 必须分开判定，不能相加分数，也不能因为使用了同一候选 ZIP 就视为严格 A/B。两者的共同 submission 是 `a9475f8e5f57`，本地附件 SHA-256 为
`9F8EE636363A5BCA75EA9E15E4403C83401965443EB0BC0941BBE6E09ADD890E`，但平台没有提供 submission→上传 ZIP/build/task snapshot 的独立绑定。

已确认、适合进入共享 Agent 契约的机制：

1. 成功写入后的结果应在当前页面原地稳定更新，避免立即 `reload` 或 full navigation 破坏测试观察上下文。
2. 实体动作必须位于目标实体自己的可访问作用域内；不能只把动作放在编辑器或全局区域。
3. 控件写入的 `data-*` 属性必须与事件处理器读取的字段一致，并用最小 locator 回归覆盖。

不能在本次归并中升级的项目：Keep 的 `REQ-7.2`、`REQ-9.1`；它们没有被同一干净平台种子和精确测试源复现。结构检查器路径、runner 状态映射、进程清理和 API key 候选字段属于流程/安全风险，不是这两个 Run 的直接业务根因。

## 2. Run 结果与身份

| Run | 任务 | 最终结果 | 通过/总数 | 阶段 4状态 | 阶段 5 |
|---|---|---:|---:|---|---|
| `a774fb34f1b6` | `arc-bench-lite-evolution--bookstack` | FAILED | 4/6，66.7 | complete | 未触发 |
| `82a833cabe9e` | `arc-bench-lite-evolution--keep` | FAILED | 2/6，33.3 | complete | 未触发 |

共同身份信息：submission `a9475f8e5f57`；模型 `deepseek-v4-flash`（Keep manifest 明示）；平台均未提供 `task_snapshot_id`、agent build ID、commit SHA 或 platform upload SHA 的闭合绑定。

### 阶段文件哈希

原始证据位于外部工作区：
`D:\DataMove\codex\worktrees\9015\AI智能体软件工厂黑客松\evidence\arc-bench\runs\`

| Run | 文件 | SHA-256 |
|---|---|---|
| `a774fb34f1b6` | `manifest.json` | `5C8C42D4648800CD74693170F471B196C68E8012FDCACD4B5C02475837A87DF3` |
| `a774fb34f1b6` | `phase4-handoff.json` | `55F49A0AF220A1EC426FFF916E489504441A974B012B52FBCEB3648306890B45` |
| `a774fb34f1b6` | `phase4-ack.json` | `F4CDEABF39B44811B816DBA39D5F2F35DDB820E8995BCD4A66F39E4A6BF319FE` |
| `a774fb34f1b6` | `phase4-result.json` | `4D07E124EF00CA1150A7DBEEEB9B2026FE57722ABFFEDC5AEFA1946A7B5570DF` |
| `a774fb34f1b6` | `phase4-result.md` | `45030C87A3223447B5C1979684659A6B255FC8EECE4BCC76E6C33FD2C4F43BF9` |
| `82a833cabe9e` | `manifest.json` | `CFC4FE4C8DA468453658200FA87F88D345486F59B45E676FCA2539ADF319F934` |
| `82a833cabe9e` | `phase4-handoff.json` | `28F350B166B47D6D96EF5BA080802F1779F6288921707699AFE2358B43FEE307` |
| `82a833cabe9e` | `phase4-ack.json` | `FF09E0DB869BFEBD7A4ECEBE16F48074564586D4CECB1D3FBB3ACA8585B1BFA8` |
| `82a833cabe9e` | `phase4-result.json` | `22FCF5E4E735A7B5FD3712B81E460C5C9A54307D5B2410C3B093B3F6479BD260` |
| `82a833cabe9e` | `phase4-result.md` | `52DCAD176F3EFF781A3C40D90668532974009813B918572546F58658218172E8` |

## 3. BookStack Run：`a774fb34f1b6`

### 终态

通过 `REQ-10.1`、`REQ-11.2`、`REQ-12.1`、`REQ-12.2`；失败 `REQ-10.2`、`REQ-11.1`。平台运行约 5143 秒，平台 token 计数 52,743,819，成本记录为 ¥30.110252。上述指标只属于该 Run，不与 Keep 合并。

### 已确认根因

- `REQ-10.2`：排序 PUT 本身持久化了 `contentsOrder`，但前端成功/失败后立即执行 `window.location.href`。官方测试在保存后读取列表时执行上下文被导航销毁，故根因是客户端导航生命周期竞态，不是排序算法或后端写入失败。修复边界是成功后原地更新或保留排序列表、关闭面板；失败时显示错误且不导航。
- `REQ-11.1`：评论 POST 追加、持久化并返回 `201`，但前端只把评论渲染成 `li`，测试寻找提交文本对应的 heading；成功回调还调用 `window.location.reload()`。主因是可访问 DOM 语义契约不匹配，reload 是次级生命周期风险。修复边界是 201 后原地追加、使用官方可观察的 heading/文本契约、清空输入且不立即 reload。

### 流程与观测风险

- 结构检查器查找 `backend/server.js`，而实际生成文件为 `backend/src/server.js`，会制造误报。
- `node_states` 将所有节点标为 passed，但最终 Playwright 为 4/6；最终官方测试优先级高于中间状态。
- 实现轮次达到 900 秒上限；`/workspace/tests` 在生成阶段没有 `.spec.ts`，内部检查由需求文本构造，不能当作官方 Playwright 覆盖。
- 出现 defunct Chrome/Node/npm 等进程和宽泛清理行为；这是生成器可靠性风险，不是两个业务失败的替代解释。

## 4. Keep Run：`82a833cabe9e`

### 终态

通过 `REQ-8.1`、`REQ-9.2`；失败 `REQ-7.1`、`REQ-7.2`、`REQ-8.2`、`REQ-9.1`。平台运行约 6809 秒，平台 token 计数 74,573,398，成本记录为 ¥43.156152；实现状态为 6/6 implemented、0/6 verified，六个实现轮次触及 900 秒上限，final check 触及 1200 秒上限。

### 已确认根因

- `REQ-7.1`：搜索建议按钮写入 `data-type="lists|reminders"`，事件处理器读取 `data-label`，因此 `activeLabel` 变为 `null`，Lists 过滤无效，Groceries 仍显示。隔离 Chrome replay 已复现。该问题可抽象为 data 属性命名与事件读取字段必须有单一契约。
- `REQ-8.2`：测试在 `Call dentist` 卡片内部查找 `Remind me`；当前卡片内按钮数为 0，编辑器内为 1。提醒功能存在，但动作不在测试要求的实体作用域。该问题可抽象为实体动作必须在目标实体的可访问作用域内出现。

### 未确认项目

- `REQ-7.2`：平台只给出 10 秒 timeout，无 assertion stack；派生 clean-seed replay 中 settings GET/PUT、checklist PUT、排序和 reload 均通过。缺原始平台干净种子与精确生成 spec，保持 unknown。
- `REQ-9.1`：平台找不到初始 Groceries；派生 seed replay 中静态 DOM、API、清空/重绘和最终卡片均保留 Groceries。由于种子是派生的，不升级为已确认根因。

### 流程与安全风险

- 生成日志报告 `/workspace/tests` 中无 `.spec.ts`，但最终 Playwright 有 6 个 requirement-derived specs；两层必须分开记录，不能把 runner 的 6/6 implemented 或 feature count 2/6 当成最终测试结果。
- 出现多次 `BrokenPipeError` 和 favicon `ConnectionResetError`，目前只能作为运行时噪声/生命周期风险。
- 原始附件扫描发现 4 个未脱敏 `api_key` 字段候选；值未复制或写入本仓库。若源处确认为有效凭据，应在源处检查、脱敏并轮换。

## 5. 多 Run 决策规则

1. 单 Run 事实优先：最终 Playwright 结果 > 平台 failure details > raw runner logs > 中间 node state；中间态只用于解释过程和风险。
2. 跨任务只合并机制，不合并分数：只有至少两个独立 Run 共享同一可观察机制，或一个 Run 有完整隔离复现，才可升级为共享契约。
3. `unknown` 不作为修复目标的确定根因：先补精确 spec、平台前置种子、请求/DOM 时间线；没有这些证据，不用全局 timeout、模型、预算或清库规避。
4. 平台身份必须闭合：submission、ZIP SHA、build/commit、task snapshot 和 Run 配置缺一不可时，只能做 Run-local 结论，不能做严格 A/B 归因。
5. 共享 Agent 修复必须保持任务条件化，不写入 BookStack/Keep 专用名称或 REQ 字面量；修复后至少覆盖创建/保存、列表过滤、实体作用域和重绘保状态的 locator-level regression。
6. 代码修改仍交给 Agent 实现会话；本决策台账只做证据归并、门禁和 go/no-go，不直接改 Agent 代码。

## 6. 当前决策

状态：`EVIDENCE_ARCHIVED / IMPLEMENTATION_NOT_DISPATCHED`。

本归档允许后续实现会话参考三项共享契约，但不授权本会话修改代码、打包、上传或创建新平台 Run。下一次多 Run 输入应追加到机器索引，并明确每个结论是 `confirmed`、`strong_candidate` 还是 `unknown`，避免覆盖这两次 Run 的原始结论。
