# HKT 目录文档摘要

> 生成时间：2026-09-24  
> 贡献者：dayuruozhi (90 commits)  
> 项目：ARC-Bench Hackathon 阶段 3/4/5 协作与诊断

---

## 📋 文档清单

| 文件名 | 行数 | 核心内容 |
|--------|------|----------|
| [ARC_BENCH_RECENT_RUNS_TEAM_HANDOFF_20260924.md](ARC_BENCH_RECENT_RUNS_TEAM_HANDOFF_20260924.md) | 169 | **最新 Run 交接文档** - 2026-09-24 团队协作交接 |
| [ARC_BENCH_HACKATHON_PHASE5_DECISION_REGISTER.md](ARC_BENCH_HACKATHON_PHASE5_DECISION_REGISTER.md) | 350 | **阶段 5 决策台账** - 跨 Run 问题归并与方案选择 |
| [ARC_BENCH_HACKATHON_EXECUTION_PLAN.md](ARC_BENCH_HACKATHON_EXECUTION_PLAN.md) | 352 | **完整执行计划** - 项目整体架构与工作流 |
| [ARC_BENCH_HACKATHON_PROJECT_MEMORY.md](ARC_BENCH_HACKATHON_PROJECT_MEMORY.md) | 199 | **项目记忆** - 历史决策与经验沉淀 |
| [ARC_BENCH_HACKATHON_PHASE4_THREAD_WORKFLOW.md](ARC_BENCH_HACKATHON_PHASE4_THREAD_WORKFLOW.md) | 240 | **阶段 4 工作流** - 单 Run 诊断流程 |
| [ARC_BENCH_HACKATHON_PHASE5_COLLABORATION_WORKFLOW.md](ARC_BENCH_HACKATHON_PHASE5_COLLABORATION_WORKFLOW.md) | 44 | **阶段 5 协作流程** - 多会话分工机制 |
| [ARC_BENCH_HACKATHON_PHASE5_CONTEXT_HANDOFF.md](ARC_BENCH_HACKATHON_PHASE5_CONTEXT_HANDOFF.md) | 36 | **阶段 5 上下文交接** - 新会话入口 |

---

## 🎯 核心发现与结论

### 当前状态（截至 2026-09-24）

**不是"再加一点 timeout 就能全过"的状态**。近期失败包含四类不同机制：

1. **异步动作后的可访问语义与测试契约不一致**
   - 创建成功后实体名称只作为 link 或普通文本出现
   - 官方 helper 在动作完成前固定到 heading fallback
   - `REQ-4.3.1`、`REQ-6.1.1` 已通过隔离复现确认

2. **确定性的服务端模板/路由缺陷**
   - 模板占位符 `{{PAGE_ACTION}}` 未全局替换
   - 静态子路由被通用 `:pageId` 路由遮蔽
   - 最终均落到 404 JSON

3. **生成/验收 harness 本身失败**
   - 无效 `trace.snapshots` 配置导致 `0/34` 误报
   - 本地 e04 混入 implement 请求上限和 API 429

4. **平台身份链不完整**
   - 多个 Run 缺 `task_snapshot_id`、平台上传 ZIP SHA
   - 不能反向构成严格 A/B

---

## 📊 近期平台 Run 总表

| Run ID | 平台 | 结果 | 主要失败 | 当前判定 |
|--------|------|------|----------|----------|
| `1b0eaf914e94` | BookStack | **33/34 (97.1%)** | `REQ-2.2` 登录后昵称 heading | 已本地复现；Agent 候选未完成端到端证明 |
| `88c08161c4d3` | Keep | **30/32 (93.8%)** | `REQ-2.4`、`REQ-2.7.6.3` | 阶段 4 缺失；不得并入旧 Keep 根因 |
| `4bab82404c52` | BookStack | **31/34 (91.2%)** | `REQ-6.1.1`、`6.1.2`、`9.1` | 隔离复现确认两个独立服务端缺陷 |
| `6d41952769f7` | BookStack | **30/34 (88.2%)** | `6.1.1`、`6.2.1`、`7.2`、`8.1` | 三项 UI 语义为 strong candidate |
| `d9a97cb4c92d` | BookStack | **31/34 (91.2%)** | `4.3.1`、`6.1.1`、`8.1` | 前两项 confirmed；收藏项继续第二阶段隔离 |
| `32e08aaca2e4` | Keep | **27/32 (84.4%)** | 5 项失败 | 最新 Keep 明显低于 no-regression floor |

### 🚫 不可混用的本地实验

`p5-014-e04` 本地 BookStack 得到 `13/34`，但存在：
- 生成应用缺 `POST /login` 等质量问题
- `OCTOS_ARC_IMPLEMENT_REQUESTS=20` 导致截断
- 后 12 节点发生 `429 insufficient_quota`
- 427 requests vs 1,671 requests 计量口径差异

**只能用于诊断本地运行资源，不能替代任何平台 Run**。

---

## 🔍 跨 Run 问题索引（P5-001 ~ P5-014）

### ✅ 已确认问题

| ID | 机制 | 证据等级 | 状态 |
|------|------|----------|------|
| **P5-001** | 设计中声明的路由未接入生成应用主路由 | `confirmed` | 本地已验证；平台效果未验证 |
| **P5-006** | Undo 可访问名称被生成代码覆盖 | `confirmed` | Agent 通用契约本地已验证 |
| **P5-007** | Keep 归档测试前置数据与生成应用 seed 不一致 | `confirmed` | 默认 seed 和按钮修复通过 |
| **P5-008** | 重复加载标签与整表重绘打断编辑 | `confirmed` | Agent 通用契约本地已验证 |
| **P5-009** | BookStack 异步保存后过早选择 heading 定位器 | `confirmed` | V3 本地候选已冻结；等待门禁闭合 |
| **P5-010** | Keep 初始数据契约遗漏 `Work editable` 标签 | `confirmed` | `approval_required` + `deferred` |
| **P5-014** | BookStack 登录后身份读回/可访问语义不满足定位器 | `confirmed` | Agent 候选已归档；功能效果未证明 |

### 🔄 待证据或待闭合

| ID | 机制 | 状态 |
|------|------|------|
| **P5-002** | Keep 归档后立即打开列表的时序疑点 | `strong_candidate`；需 trace 或等效复现 |
| **P5-005** | A/B 的上传 Agent 构建、任务快照绑定不完整 | V4.1 本地实现；外部绑定未闭合 |
| **P5-012** | 模型认证失败后生成链无产出 | 401 链 `confirmed`；用户已修复 API |
| **P5-013** | 最终包缺少 frontend/backend/main.py/tests | 旧 Run-local `confirmed`；新 Run 形状可用 |

---

## 🎬 阶段五裁决

### ✅ Confirmed（可进入 Agent 切片）

- `REQ-4.3.1`、`REQ-6.1.1`：**confirmed**
  - 可进入"通用创建后结果语义契约"最小 Agent 切片
  - 状态：**待用户授权**

### 🔬 Strong Candidate（需进一步验证）

- `REQ-8.1`：**strong_candidate / timing_sensitive**
  - **不得**并入上述切片
  - 需先闭合平台评分前 seed 与多轮时序证据

### ⏸️ 暂不处理

- `4bab82404c52` 的模板占位符与草稿路由：
  - 隔离复现已确认
  - 但只证明该次生成应用的具体缺陷
  - 是否转换为通用 Agent 提示需另立切片

- `32e08aaca2e4`、`88c08161c4d3`：
  - 阶段 4 尚未形成完整可核验结论
  - 阶段 5 不得越级归因或直接改 Keep

### 🚫 当前授权状态

- `business_go=false`
- `strict_ab_comparable=false`
- 本文件**不授权改 Agent**
- **不授权上传**
- **不授权新平台 Run**

---

## 📈 下一步工作流与所有权

| 顺序 | 所有者 | 动作 | 完成门槛 |
|------|--------|------|----------|
| 1 | 阶段 3/4 Keep | 完成 `88c08161c4d3` reconciliation | handoff/ACK/result 身份一致 |
| 2 | 隔离复现 | 完成 `REQ-8.1` seed + 时序矩阵 | 同一闭合 seed 至少 10 个 fresh-copy |
| 3 | 决策台账 | 接收上述结果并裁决 | 每题明确 confirmed/strong_candidate/excluded |
| 4 | 用户 | 授权或拒绝代码切片 | 当前仅两个创建题具备待授权切片 |
| 5 | Agent 实现 | 若获授权，实施最小通用契约切片 | 单一共享规则、无硬编码 |
| 6 | 指标与 A/B | 本地定点、34题、多任务 canary | 任一功能回退 NO-GO |
| 7 | 用户/平台 | 另行授权上传和平台 Run | auth preflight 2xx；A/B 身份全部记录 |

---

## ⚠️ 禁止事项与常见误判

1. ❌ 不把 heading timeout 自动解释为后端写入失败
2. ❌ 不把静态源码"看起来有控件"当成运行时 DOM 证据
3. ❌ 不把内部 acceptance、平台套件和手工 summary 混成一个分数
4. ❌ 不把用户提供 ZIP SHA 当成平台上传绑定
5. ❌ 不把导出 ZIP 中的 DB 状态当成评分前 seed
6. ❌ 不改官方 tests/helper
7. ❌ 不在未确认前把 `REQ-8.1` 与创建后 heading 机制一起修改
8. ❌ 不把本地 e04 的 13/34、429 归因给平台 `P5-017`
9. ❌ 不把本地通过写成平台收益
10. ❌ 不记录 API Key、Cookie、Authorization header

---

## 📂 证据入口

### 仓库内

- 阶段五决策台账：`docs/ARC_BENCH_HACKATHON_PHASE5_DECISION_REGISTER.md`
- 项目记忆：`docs/ARC_BENCH_HACKATHON_PROJECT_MEMORY.md`
- 阶段五协同索引：`evidence/arc-bench/phase5-coordination.json`
- Run 证据：`evidence/arc-bench/runs/<run_id>/manifest.json`

### 外部只读证据

- `4bab82404c52`：`C:/Users/dayuruozhi/Doubao/chats/2026-09-22/new-chat-3/isolation-4bab82404c52/`
- `d9a97cb4c92d`：`C:/Users/dayuruozhi/Doubao/chats/2026-09-24/new-chat/repro/`
- `1b0eaf914e94`：`D:/DataMove/codex/visualizations/2026/09/20/.../phase5-p5014-1b0eaf914e94/`
- 本地 e04：`D:/DataMove/arcbench-local/p5-014-e04/skill-output/local/bookstack-e04-01/`

---

## 🔧 协作交接状态

| 会话角色 | Thread ID | 职责 |
|----------|-----------|------|
| 决策台账 | `01a0bd66-5680-7e72-9e8a-24290780525e` | 证据、判断、台账与协同记录 |
| 隔离复现 | `01a0bd66-60c2-7441-9a85-332c0af24886` | 已接收 `REQ-8.1` 第二阶段 handoff |
| Agent 实现 | `01a0bd66-75bd-7801-97fc-b3d1e136c112` | 当前无新代码授权 |
| 指标与 A/B | `01a0bd66-8b2a-7fb3-9a25-269204f6dbf1` | 已回传本文件第 6 节门禁 |

---

## 📊 关键指标

### 成本与时长基线

| Run | 平台 Token | 成本 (CNY) | 耗时 (秒) | 请求数 |
|-----|-----------|-----------|----------|--------|
| `1b0eaf914e94` | 42,725,779 | ¥22.19 | 8,548 | - |
| `88c08161c4d3` | 40,784,030 | ¥21.36 | 8,370 | - |
| `4bab82404c52` | 37,625,229 | ¥18.35 | 9,817 | - |
| `6d41952769f7` | 89,254,641 | ¥36.97 | 18,827 | 2,402 |
| `d9a97cb4c92d` | 56,757,262 | ¥29.91 | 12,207 | - |
| `32e08aaca2e4` | 42,677,341 | ¥23.57 | 8,842 | - |

**近期 BookStack 单次约 18–37 CNY、2.7–5.2 小时**

---

## 🎓 核心教训

1. **功能完成率与回归可靠性优先**；通过率相同才比较 Token
2. **先按失败机制归并**，再比较表面症状
3. **同为 Playwright 十秒超时，不等于同一根因**
4. **证据等级严格区分**：`confirmed` / `strong_candidate` / `unknown`
5. **状态词严格区分**：`本地已验证` ≠ `平台已验证`
6. **每个实现切片必须回答**：服务哪个真实失败、改善哪个行为、由哪个测试证明
7. **新 Run 必须先回阶段 3，再回阶段 4，最后更新台账**

---

*本摘要基于 dayuruozhi 的 90 个提交和 7 份核心文档生成。详细内容请参阅各文档原文。*
