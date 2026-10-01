# ARC-Bench Request Budget 修复交接（2026-10-01）

日期：2026-10-01
分支：`codex/hkt-round345-integration`
修复提交：`9ff7e750657a1d5c1ba67f71651ed9fe0d56c5c5`
改动范围：仅 Agent 侧（`arc/main.py` + `arc/tests/test_main_helpers.py`）；未修改官方测试、requirements ZIP 或平台 Run。

## 1. 一句话结论

两个新平台 Run（`2b6a1f545c37` sheet、`0564f5955f16` github）都是 **0 分，但不是额度中断**：真正的根因是 per-turn `request budget 8` 把每个节点（含 skeleton）在写完代码前强制掐断。本次把多节点 implement 预算 `8 → 16`，并给 skeleton 单独预算 `max(20, implement)`。

## 2. 证据：两份日志

来源：`D:\items\Hackathon\new-octos\log\`（provenance，不可远程读取）。

| Run | 任务 | 节点 | 结果 | 费用 | 时长 | 请求数 | run token_count | `request budget 8 hit` |
|---|---|---:|---|---:|---:|---:|---:|---:|
| `2b6a1f545c37` | `hackathon--sheet` | 24 | `0/24`，feature 0% | `5.677578 CNY` | 2822s（47min） | 269 | 4,283,384 | ×58 |
| `0564f5955f16` | `hackathon--github` | 47 | `0/47`，feature 0% | `10.559866 CNY` | 5584s（93min） | 465 | 8,510,678 | ×102 |

两 Run 共同事实：
- 都用提交包 `arc-agent-hackathon-sheet-1821c3f5.zip`（submission `c2c0b5b2ab3c`，ZIP SHA `9b7b39d3…cd51f1e`）；注意 github Run 也误用了 sheet 命名的包，但内容相同。
- 模型 `deepseek-v4-flash`，`reasoning=low, destream=on, trim=on`。
- **无 402 / 无余额中断 / 无 OOM / 无 workspace_unavailable**。额度保护没有被触发；是预算过紧，不是花费过多。
- `[flow] REQ-* implement ok` 行很多，但大量 `wrote=False verified=False`——工具预算耗尽、代码未落盘/未验证即被掐断，与 feature 0% 一致。
- 第一次 `request budget 8 hit` 发生在 `skeleton attempt 1`，即脚手架阶段就被掐断。
- rehearsal 的 `GET /favicon.ico ... ConnectionResetError`（sheet ×4 / github ×2）是次要噪音：backend 仍在监听，仅未实现 favicon/404，不是根因。

## 3. 根因

`arc/main.py` 的 `implement_request_budget()` 原逻辑：minimal 任务（节点 ≤ `small_task_nodes`，默认 2）给 20，其余多节点任务只给 **8**。

- sheet 24 节点、github 47 节点都不是 minimal → 每个 turn 只有 8 个请求。
- `enforce_turn_budget`（`arc/llm_proxy.py`）在第 8 个请求后剥离工具 schema 并追加结束通知，turn 被强制收尾。
- skeleton turn 走 `turn()` 的默认分支（label 不含 `repair`），同样只拿到 8 —— 而它要一次搭出前后端两个 `package.json`、入口文件、build/start 脚本，8 个请求连骨架都搭不完。

一个中等 Web 节点的真实开销：读 spec/现有文件（1–3）+ 写前端（2–4）+ 写后端（2–4）+ build/验证（2–3）≈ 8–14 次。8 是硬掐在下限上。

## 4. 改动明细（`arc/main.py`）

1. **`implement_request_budget()`**：多节点默认 `8 → 16`。minimal 任务仍为 20。保留 `OCTOS_ARC_IMPLEMENT_REQUESTS` 覆盖。
2. **新增 `skeleton_request_budget()`**：默认 `max(20, implement budget)`，新增 `OCTOS_ARC_SKELETON_REQUESTS` 覆盖。
3. **`skeleton()`**：skeleton 的 `turn()` 调用显式传入 `request_budget=self.skeleton_request_budget()`。
4. **环境变量文档**：更新文件头 `OCTOS_ARC_IMPLEMENT_REQUESTS` 说明，补 `OCTOS_ARC_SKELETON_REQUESTS` 条目。

有界性保持不变：`rewrite_request_budget()` 仍被 `OCTOS_ARC_MAX_REWRITE_REQUESTS`（默认 8）封顶（`min(16, 8)=8`），没有退回"无界预算导致额度尾巴"的老问题（见 quota 分析 E5CB3CA21874 / FB4903ECEF12）。

## 5. 验证

- TDD：新增 2 个测试（`RewriteBudgetTests`）锁定多节点 implement ≥16、skeleton ≥ implement 且 ≥20，先 RED 后 GREEN。
- `python -m unittest tests.test_main_helpers`：42 项全通过。
- `python -m py_compile main.py`：通过。
- `git diff --check`：干净。
- 完整 suite：仅 `test_acceptance.py` 2 项失败（Windows 路径分隔符 `\` vs `/`、npm cache 路径），属基线既有问题（本次未碰该文件，见 FINAL_PLAN 2A 节），非本次引入。

## 6. 成本影响

按最可信单价 ~1.1 CNY/M provider token（round345 自洽数据）估算，implement 从 8 翻倍到 16，单 Run 成本大致：sheet ~11 CNY、github ~21 CNY，仍远低于 Sheet 40–70 CNY 上限、总 250 CNY 目标。这次是朝"能拿分"的方向花钱，而非撞 402。

## 7. 新发布包

从修复提交打包（`arc/pack.sh`，sheet 身份）：

| 字段 | 值 |
|---|---|
| 文件 | `releases/arc-agent-hackathon-sheet-9ff7e750.zip`（357,314 B，511 条目） |
| ZIP SHA-256 | `0e98e7e0dfcf4f893a5cfce0b8cd8d40168e7ec1ffe505a744e1097fe18fb7c5` |
| 源 commit | `9ff7e750657a1d5c1ba67f71651ed9fe0d56c5c5` |
| build id | `arc-agent-v1-747e10178d68748225a086dd` |
| payload tree SHA | `E022098B6B9B4647D2EA6E5D4C2754845AA161A91DF10D16550A1DD969312DBF` |
| task / suite | `hackathon--sheet` / `hackathon--sheet` |
| requirements SHA | `9884f23ea10c3dfeee170d1eed57966c8fce9a5ce18a0ac43b3d7942eba8c414` |
| 门禁 | package_shape ✅ / offline_import ✅ / placeholder_identity_rejected ✅ |

## 8. NO-GO / 待办

- **suite key 为本地沿用值**：`hackathon--sheet` 抄自旧 binding。正式上传须用平台实际分配的 suite key；若不同必须重新打包，不得直接复用本 ZIP（见 FINAL_PLAN 9 节）。
- **本包为 exploratory 探针**：Run 完成后用平台实际扣费/token 回填，校准 ~1.1 CNY/M 单价系数（目前仅 2 个数据点）。
- 预算修复只解决"被掐断"；若放开预算后仍 0 分，需进一步看是生成质量、路由/可见性契约还是平台测试口径问题，不能再归因于 budget。

## 9. 未纳入本次改动

- 主动 token/CNY 预算 hard-stop（撞 402 前主动冻结）：已完成只读核算（见对话记录），实现待定，不在本提交内。
- favicon/404、rehearsal 噪音：非根因，未处理。
