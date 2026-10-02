# `8fca1171db4b` 证据归档与截止前第一步方案

日期：2026-10-02（终态证据归档；提交截止为 2026-10-03 23:59）  
范围：只读归一化证据、方案调整；本文件不代表已运行平台测试或完成远程同步。

## 1. 终态事实

| 项目 | 事实 |
|---|---|
| Run | `8fca1171db4b` |
| Task | `hackathon--github-stage-1` |
| 需求规模 | 12 atomic nodes；平台由 requirement text 生成 30 scenarios |
| 平台结果 | 5/30，16.7%；feature 1/12 |
| 生成 | 9 REQ implement ok；无 Agent turn timeout |
| 部署 | frontend build 后 backend 在 `127.0.0.1:3000` 监听 |
| 官方测试 | 已执行；逐条 tests、Playwright report、stdout 未回流 |
| ZIP SHA | `3F4F23F583BDB2D4A2687E4BB02BEFD5ECBD556ED3480C6E7FEC39142108D654` |
| Submission | `aae2ed578267` |
| 成本 | 约 9.31M tokens，¥7.39 |

## 2. 可归因边界

可以确认：

- 该包能够完成构建、启动并进入官方测试；因此已排除上一轮“完全未部署/未进入测试”的主要故障。
- 过程状态与平台行为结果仍有明显差距：`implement ok` 不能等价于 feature 通过。
- 平台只回传总体 5/30，不能从 `tests=[]` 推断具体隐藏测试、locator 或断言。

不能确认：

- 不能证明 25 个失败全部由某个单一需求或某个单一 locator 导致。
- 不能把 8fca 的提升严格归因于某一条 prompt 修改；生成随机性、包版本和任务状态仍可能共同影响结果。
- 平台未提供 generation identity、task snapshot 和官方 suite identity，ZIP SHA 只能作为本地归档证据。

## 3. 与历史结果的定位

- `877ac3bb19e7`：拆分前完整 GitHub，13/100、feature 3/47，是绝对通过数更高的历史基线。
- `6ad28fd0ab3d`：Stage 1，5/30、feature 1/12；与 8fca 相同的 Stage 1 分数。
- `7616a1cdbddd`：Stage 1，0/30，并出现 REQ-2-1-2 的 900 秒超时；不能仅归因于 cap，因为代码包也不同。
- `7cc1b2ba5b1f`：Sheet，0/100；24/24 implement ok，但 36 次 budget guard，说明过程状态与真实完成脱钩。

结论：8fca 证明部署入口和流程稳定性有所恢复，但没有证明需求理解或用户旅程已经解决。拆分后 Stage 1 的 5/30 也没有超过拆分前完整 GitHub 的 13/100，因此下一版必须保留统一领域模型和跨 Stage 共享旅程，不能只做孤立的 Stage 优化。

## 4. 第一优先改动方案

截止前只做一个高收益切片，顺序固定为：

1. **完成状态改为证据驱动**：`source_changed`、`build_passed`、`health_passed`、`semantic_smoke_passed`、`persistence_passed`、`official_acceptance_unknown` 分开记录；`implement ok`、`wrote=True`、`continuation ok` 不得自动升级为 verified。
2. **加入 Stage 1 高扇出合同**：入口、session、列表/详情、创建/编辑、刷新恢复、实体作用域和错误原子性；每项合同包含 fixture、route、role/name、action、mutation、visible result、refresh result。
3. **用真实浏览器 smoke 验收一条完整链路**：入口 → 资源打开 → 核心动作 → 页面可见结果 → refresh/reopen → 错误不污染。
4. **预算采用 `12 + 一次 8` 的受控 continuation**：仅当有 product delta、build/start/health 和 smoke 进展时允许继续；重复读取、无文件变化、相同 failure digest 时停止并保存 checkpoint。
5. **保留最终验证 reserve**：不能将全部请求耗尽在实现循环中。

本步骤不做完整 Spec Kit、工具 API 全量重构或多模型框架引入。

## 5. 实验门禁

下一次比较必须固定：

```text
canonical ZIP
requirements SHA
task/suite key
模型与 prompt 版本
seed/runtime 初始状态
```

只改变预算策略或一个明确的运行时变量。提交前输出 ZIP SHA、source SHA、requirements SHA、package identity，并在身份不匹配时 fail-closed。

