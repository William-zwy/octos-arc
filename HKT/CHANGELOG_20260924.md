# HKT 目录文档更新日志

> 最后更新：2026-09-24

---

## 2026-09-30

- 归档 Web Keep Run `c68bef1a6343` 的阶段 3输入、终态/中间态指标、原始证据 SHA-256 和阶段 4待闭合状态。
- 新增 `ARC_BENCH_WEB_KEEP_RUN_C68BEF1A6343_HANDOFF_20260930.md` 与 `evidence/arc-bench/web-keep-run-c68bef1a6343.json`。
- 明确该 Run 的 Web Keep suite identity 匹配；阶段 4缺少 ACK/result，暂不升级代码根因、不派发 Agent 修改、不触发平台 Run。

## 📁 文档列表

| 文件名 | 类型 | 创建/更新日期 | 摘要 |
|--------|------|--------------|------|
| `SUMMARY.md` | 总览 | 2026-09-24 | HKT 目录所有文档的总览与核心发现 |
| `ARC_BENCH_RECENT_RUNS_TEAM_HANDOFF_20260924.md` | 交接 | 2026-09-24 | 最新 Run 交接文档 |
| `ARC_BENCH_HACKATHON_PHASE5_DECISION_REGISTER.md` | 台账 | - | 阶段 5 决策台账 |
| `ARC_BENCH_HACKATHON_EXECUTION_PLAN.md` | 计划 | - | 完整执行计划 |
| `ARC_BENCH_HACKATHON_PROJECT_MEMORY.md` | 记忆 | - | 项目记忆 |
| `ARC_BENCH_HACKATHON_PHASE4_THREAD_WORKFLOW.md` | 工作流 | - | 阶段 4 工作流 |
| `ARC_BENCH_HACKATHON_PHASE5_COLLABORATION_WORKFLOW.md` | 工作流 | - | 阶段 5 协作流程 |
| `ARC_BENCH_HACKATHON_PHASE5_CONTEXT_HANDOFF.md` | 交接 | - | 阶段 5 上下文交接 |
| **`ARC_BENCH_OPTIMIZATION_IMPLEMENTATION_20260924.md`** | **实施** | **2026-09-24** | **优化实施详细文档（新增）** |
| **`QUICK_REFERENCE_OPTIMIZATION_20260924.md`** | **参考** | **2026-09-24** | **优化快速参考（新增）** |

---

## 🆕 2026-09-24 更新内容

### 新增文档（2 个）

#### 1. ARC_BENCH_OPTIMIZATION_IMPLEMENTATION_20260924.md

**内容：** 完整的优化实施文档，包含三个新脚本的详细说明

**章节：**
- 📋 实施概览
- 🎯 脚本 1：arc-bench-gate.sh（四种模式：quick/preflight/canary/full）
- 🎯 脚本 2：arc-bench-milestone.sh（三个命令：upload-and-bind/validate-ab-pair/generate-frozen-seed）
- 🎯 脚本 3：arc-bench-repro-matrix.sh（噪声隔离与统计判定）
- 📊 预期收益对比
- 🚀 下一步工作（P0/P1/P2）
- 📚 参考文档
- ⚠️ 重要提示

**适用场景：** 需要了解完整技术细节、使用方法、借鉴来源

---

#### 2. QUICK_REFERENCE_OPTIMIZATION_20260924.md

**内容：** 优化方案的快速参考卡片

**章节：**
- 🎯 创建了什么（三个脚本的一句话描述）
- 💰 预期收益（成本对比表）
- 📋 当前状态（已完成/待实现/待授权）
- 🔗 相关文档
- 🚀 立即开始
- ⚠️ 关键限制

**适用场景：** 快速查阅、向他人解释、记忆关键点

---

### 新增脚本（3 个）

**路径：** `../scripts/`（上级目录的 scripts/）

| 脚本文件 | 行数 | 功能 |
|---------|------|------|
| `arc-bench-gate.sh` | ~250 | 多层验证门槛（quick/preflight/canary/full） |
| `arc-bench-milestone.sh` | ~280 | A/B 身份绑定（upload-and-bind/validate-ab-pair/generate-frozen-seed） |
| `arc-bench-repro-matrix.sh` | ~200 | 噪声隔离矩阵（10 次独立运行 + 统计判定） |

**当前状态：** ✅ 框架完成，🚧 核心执行逻辑待实现

---

## 🎯 优化目标

基于 `SUMMARY.md` 识别的三大瓶颈：

### 1. 成本控制（解决：每次改动¥18-37）

**方案：** `arc-bench-gate.sh` 的四层门槛

| 层级 | 成本 | 时长 | 过滤内容 |
|------|------|------|---------|
| quick | ¥0 | 5分钟 | Lint/格式/单元测试错误 |
| preflight | ¥0 | 1分钟 | 环境/认证/包结构问题 |
| canary | ~¥6 | 1小时 | 单任务早期失败 |
| full | ¥36-74 | 5-10小时 | 完整 A/B |

**预期：** 每 5 次迭代节省 ¥200-400

---

### 2. A/B 身份链（解决：P5-005）

**问题：** 多个 Run 缺 `task_snapshot_id`，无法反向构成严格 A/B

**方案：** `arc-bench-milestone.sh` 的身份绑定

**输出：**
- `upload-receipt.json`（含 agent_sha + snapshot_id）
- `ab-validation.json`（含 strict_comparable: true/false）

**效果：** 每个对比都有可追溯的 Git SHA → snapshot ID → Run ID 链

---

### 3. 噪声隔离（解决：P5-002/008/009）

**问题：** REQ-8.1 等 strong_candidate 无法确认是否为真实问题

**方案：** `arc-bench-repro-matrix.sh` 的统计判定

**逻辑：** 10 次独立运行 → 丢弃最快/最慢各 1 次 → 保留 8 次中 ≥6 次一致 → confirmed

**效果：** 
- 可区分 confirmed / false_alarm / timing_sensitive
- 节省 ¥120-250/问题（vs 10 次完整 Run）

---

## 📊 借鉴来源

### minimax-code

**文件：** `docs/performance-ci.md`

**借鉴内容：**
- 三级裁决：PASS / REGRESSION / INCONCLUSIVE（49-60 行）
- basic/full 模式分层（13-14 行）
- 噪声限制：丢弃极端样本（44 行）
- 回归预算：duration +25%+1s, CPU +20%+0.5s（40-42 行）

**应用：**
- `arc-bench-gate.sh` 的模式分层
- `arc-bench-repro-matrix.sh` 的极端值丢弃

---

### octos-p

**文件：** `docs/TESTING.md`, `scripts/ci.sh`

**借鉴内容：**
- 规范的里程碑命令（25-36 行）
- 脚本结构：section/pass/fail 标记（40-42 行）
- 多层门槛：静态检查 → 本地测试 → 平台集成

**应用：**
- 所有三个脚本的框架结构
- `arc-bench-milestone.sh` 的命令设计

---

## 🔄 与现有文档的关系

### SUMMARY.md（总览）

- **引用：** 四类失败机制、近期 Run 总表、跨 Run 问题索引
- **扩展：** 提供具体解决方案和工具

### ARC_BENCH_HACKATHON_PHASE5_DECISION_REGISTER.md（决策台账）

- **依赖：** P5-005（A/B 身份链）的解决方案
- **输入：** `arc-bench-repro-matrix.sh` 的 verdict 更新台账

### ARC_BENCH_HACKATHON_EXECUTION_PLAN.md（执行计划）

- **补充：** 阶段 3 增加 quick/preflight gate
- **补充：** 阶段 4 增加 canary 验证
- **补充：** 阶段 5 增加 A/B 身份验证

---

## 🚦 下一步行动

### P0 - 已完成 ✅

- [x] 创建三个脚本框架
- [x] 编写完整实施文档
- [x] 编写快速参考文档
- [x] 更新 HKT 目录清单

### P1 - 待代码集成 🚧

1. **arc-bench-gate.sh：**
   - 实现 `canary` 和 `full` 模式的实际执行
   - 集成技能调用和分数读取

2. **arc-bench-milestone.sh：**
   - 实现平台 API 调用（上传/查询）
   - 实现 frozen seed 提取逻辑

3. **arc-bench-repro-matrix.sh：**
   - 集成技能调用（从 frozen seed 运行）
   - 实现 duration 排序和噪声计算

### P2 - 待授权验证 ⏸️

4. **REQ-4.3.1、REQ-6.1.1：**
   - 提取 frozen seed
   - 验证本地可重放

5. **REQ-8.1：**
   - 运行 10 次隔离复现矩阵
   - 更新决策台账

6. **首次 A/B：**
   - 上传带 receipt
   - 验证 strict_comparable: true

---

## 📝 使用建议

### 对于开发者

1. **日常迭代：** 每次改动先跑 `./scripts/arc-bench-gate.sh quick`
2. **上传前：** 必跑 `./scripts/arc-bench-gate.sh preflight`
3. **发布前：** 必跑 `./scripts/arc-bench-gate.sh full --base main --head feature`

### 对于决策者

1. **查阅：** 先看 `QUICK_REFERENCE_OPTIMIZATION_20260924.md`（快速了解）
2. **详细：** 再看 `ARC_BENCH_OPTIMIZATION_IMPLEMENTATION_20260924.md`（完整方案）
3. **追溯：** 结合 `SUMMARY.md`（问题来源和证据）

### 对于实施者

1. **框架：** 三个脚本已可执行，有 `--help`
2. **集成：** 按 P1 清单逐项实现核心逻辑
3. **验证：** 按 P2 清单逐项验证实际效果

---

## ⚠️ 关键注意事项

1. **三个脚本当前为框架模板**，核心执行逻辑（平台 API、技能集成）待实现
2. **预期收益基于假设**，实际节省需在 P2 验证后确认
3. **不授权直接改 Agent**，必须先完成隔离复现和决策台账更新
4. **不授权直接上传/Run**，必须先通过 preflight 和身份验证

---

## 🔗 快速导航

| 需求 | 文档 |
|------|------|
| 快速了解优化内容 | `QUICK_REFERENCE_OPTIMIZATION_20260924.md` |
| 完整技术细节 | `ARC_BENCH_OPTIMIZATION_IMPLEMENTATION_20260924.md` |
| 问题来源和证据 | `SUMMARY.md` |
| 跨 Run 问题状态 | `ARC_BENCH_HACKATHON_PHASE5_DECISION_REGISTER.md` |
| 脚本源码 | `../scripts/arc-bench-*.sh` |

---

*本更新日志记录 2026-09-24 的优化实施工作，包含 2 个新文档和 3 个新脚本。*
