# ArcBench Run Evidence — dc1468f35580

日期：2026-10-03（Asia/Shanghai）

## 身份

| 字段 | 值 |
|---|---|
| run_id | `dc1468f35580` |
| task_key | `hackathon--github-stage-1` |
| submission_id | `779a965024b6` |
| agent_commit_sha（日志 identity） | `c5023063aa04a4a04a75193a2b61c79ffb419f6a` |
| agent_zip_sha256 | `BA6267C28B98DE6074E99AB3CE3DEA31E11B1677B5F66A492D1D4175F14BCFD3` |
| requirements_sha256 | `d5392c2c08f6e67b0de8640ba3d74333071e93ef9b3d15610d0b605f9ff7efd8` |
| contract_hash（日志证据） | `59760e1800806118978418ecea8e02010e38a4786a3a592089f4c667ba9875ac` |
| 本地归档目录 | `C:\Users\dayuruozhi\Downloads\闻悦源代码-首轮测试-hackathon-github-stage-1` |

原始材料：`arcbench-run-dc1468f35580.json`、`arcbench-dc1468f35580-failure-details.md`、`arcbench-run-dc1468f35580-logs.json`、`dc1468f35580-template.zip` 及 midrun 三件套。未将外部附件复制进仓库；本文件记录其路径和摘要。

## 已证实事实

- 平台状态 `FAILED`，score `0`，通过 `0/30`，失败 `30`，feature `0/12`。
- 生成阶段 12/12 节点均 `implement ok` / `wrote=True`，无 implement FAILED。
- 部署阶段成功：日志出现 `template-app listening`，端口 `3000` 与 `3301` 均可监听；未出现 `did not become ready`。
- 官方测试阶段已结束，但平台没有返回 `tests[]`、Playwright report 或逐例 stdout，因此不能列出隐藏测试 ID、locator、断言或错误栈。
- guard 双写 42 行，按时间/消息去重后为 21 个 request-budget 事件；事件主要发生在 skeleton、implement 和 continuation 阶段。
- 未见 402、代理错误、网络错误或 OOM。

## 证据解释边界

### 高置信结论

本轮已经排除“生成阶段崩溃”和“部署 readiness 失败”作为首要原因；主要失败形态是：代码写入和服务启动成功，但官方行为验收全部未通过。`wrote=True`、`implement ok`、部署成功都不能解释为业务功能正确。

### 只能推断、不能当作事实

可能存在 API-only、页面语义不匹配、入口/资源作用域错误、真实 mutation 缺失、刷新不持久化或错误原子性不足，但平台没有逐例证据，不能指定其中任何一个为已证实根因。21 个 guard 事件可能降低实现深度，但本轮节点仍全部写入，不能把它认定为 0 分的唯一原因。

### 必须保持 unknown

- 30 个隐藏场景的测试 ID、locator、断言、截图和错误消息；
- 官方测试入口及 fixture 资源；
- 具体失败属于路由、ARIA、作用域、mutation、数据值、持久化还是错误处理；
- 平台真实 build ID、task snapshot 和完整 suite identity。

## 历史对照

| run | task | 结果 | 可靠结论 |
|---|---|---:|---|
| `6ad28fd0ab3d` | github-stage-1 | 5/30 | 零生成失败、部署成功仍有大量隐藏验收失配 |
| `8fca1171db4b` | github-stage-1 | 5/30 | 修复超时后出现非零分，但仍非稳定通过 |
| `7616a1cdbddd` | github-stage-1 | 0/30 | 存在节点超时，不能作为本轮唯一解释 |
| `dc1468f35580` | github-stage-1 | 0/30 | 生成和部署均成功，但行为验收全失配 |
| `9fee9a825b32` | sheet | 0/100 | 写入完成不等于功能契约命中 |
| `7cc1b2ba5b1f` | sheet | 0/100 | 高频 budget guard 与后续半成品扩散存在风险 |
| `877ac3bb19e7` | 完整 github | 13/100 | 拆分前历史最高；不能与本轮作纯单变量因果对照 |

预算、ZIP、commit 和需求身份在不同 run 间同时变化，因此不能声称“提高 cap”或“降低 cap”单独导致分数变化。

## 下一步门禁（记录，不在本次证据分析中宣称已完成）

1. 固定 task/suite/requirements/contract/source/ZIP 的身份链。
2. 共享入口优先：`/`、`/health`、`/api/health`、核心路由、ARIA role/name、实体作用域。
3. 每个能力切片必须有 UI → handler → API → store → visible result → refresh/reopen → error atomicity 的闭环证据。
4. `implement ok` 与 `wrote=True` 只记录过程，不进入 `verified`；完成状态由真实 acceptance/Harness 证据决定。
5. guard 截断只作为风险上下文；不能替代平台逐例失败证据。
6. 平台不回流测试明细时，报告必须区分 confirmed / inferred / unknown，并禁止编造失败用例。

## 来源

- `run-object`: `arcbench-run-dc1468f35580.json`
- `failure-details`: `arcbench-dc1468f35580-failure-details.md`
- `summary`: `arcbench-run-dc1468f35580-summary.md`
- `logs`: `arcbench-run-dc1468f35580-logs.json`
- `template`: `dc1468f35580-template.zip`
- 平台链接：<https://arc-bench.com/runs/dc1468f35580>
