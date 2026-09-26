# ARC-Bench 优化实施文档

> 创建时间：2026-09-24  
> 基于：minimax-code 和 octos-p 测试框架的最佳实践  
> 目标：降低成本、提升证据链完整性、隔离噪声问题

---

## 📋 实施概览

本次实施借鉴 `minimax-code` 的性能回归框架和 `octos-p` 的多层里程碑结构，为 ARC-Bench 项目创建了三个新脚本，解决 HKT 文档中识别的核心瓶颈。

### 创建的脚本

| 脚本路径 | 用途 | 估算成本 | 估算时长 |
|---------|------|---------|---------|
| `scripts/arc-bench-gate.sh` | 多层验证门槛 | ¥0-37（按模式） | 5分钟-10小时 |
| `scripts/arc-bench-milestone.sh` | A/B 身份绑定与上传协调 | ¥0（管理脚本） | 按需 |
| `scripts/arc-bench-repro-matrix.sh` | 时序敏感问题的噪声隔离 | ¥6-12/矩阵 | 1-2小时/矩阵 |

---

## 🎯 脚本 1：arc-bench-gate.sh

### 借鉴来源

**minimax-code 的 performance-ci.md（49-71 行）：**
- 三级裁决：PASS / REGRESSION / INCONCLUSIVE
- basic 模式的 INCONCLUSIVE 转 pass+警告（避免阻塞无关 PR）
- full 模式的 INCONCLUSIVE 保持失败（性能工作必须真实 PASS）

**octos-p 的 TESTING.md（25-36 行）：**
- 规范的里程碑命令：`hosted-fast`, `workspace-all-features`, `dashboard`
- 清晰的门槛分层：静态检查 → 本地测试 → 平台集成

### 四种模式

#### 1. Quick Mode（快速门槛）

**目的：** 在提交到平台前捕获明显错误，节省¥15-30/次

**执行内容：**
```bash
./scripts/arc-bench-gate.sh quick
```

- `cargo fmt --all -- --check`（格式检查）
- `cargo clippy --workspace --all-targets -- -D warnings`（Lint）
- `cargo test --workspace --lib`（单元测试）
- Agent 提示模板格式验证

**标准：** 0 个新 lint 错误，所有单元测试通过

**失败处理：** NO-GO，不进入平台 Run

**成本：** ¥0，本地 5 分钟

---

#### 2. Preflight Mode（上传前验证）

**目的：** 避免 P5-012（401 认证）和 P5-013（包结构缺失）

**执行内容：**
```bash
./scripts/arc-bench-gate.sh preflight
```

- 检查 `OCTOS_ARC_IMPLEMENT_REQUESTS` 环境变量（≥100）
- 测试认证端点（避免 401 Unauthorized）
- 验证生成包结构（frontend/backend/main.py/tests）
- 写入 `evidence/arc-bench/preflight-manifest.json`

**标准：** 认证 2xx，包结构完整

**失败处理：** 修复环境后重试，不允许带缺陷上传

**成本：** ¥0，本地 1 分钟

---

#### 3. Canary Mode（金丝雀单任务）

**目的：** 在全量 A/B 前用单任务验证，失败时节省~¥15

**执行内容：**
```bash
./scripts/arc-bench-gate.sh canary --task bookstack --baseline-score 31/34
```

- 运行单个任务（BookStack 或 Keep）
- 对比基线分数（no-regression floor）
- 快速失败，避免双任务成本

**标准：** 分数 ≥ baseline（BookStack 31/34，Keep 27/32）

**失败处理：** 退回阶段 3 分析，不进入 full 模式

**成本：** ~¥6，1 小时

**状态：** 🚧 执行逻辑待实现（当前为模板）

---

#### 4. Full Mode（完整 A/B）

**目的：** 严格的 A/B 对比，证明无功能回退

**执行内容：**
```bash
./scripts/arc-bench-gate.sh full --base <commit> --head <commit>
```

- 运行 BookStack + Keep 双任务
- 对比 base/head 分数
- 验证 A/B 身份链完整性

**标准：** 两个任务都 ≥ baseline，无功能回退

**失败处理：** 根据 SUMMARY.md 的阶段 5 裁决流程处理

**成本：** ¥36-74，5-10 小时

**状态：** 🚧 执行逻辑待实现

---

### 使用流程

```bash
# 步骤 1：开发前快速检查（本地迭代）
./scripts/arc-bench-gate.sh quick
# ✓ 通过 → 继续
# ✗ 失败 → 修复 lint/test

# 步骤 2：上传前验证
./scripts/arc-bench-gate.sh preflight
# ✓ 通过 → 可以上传
# ✗ 失败 → 修复环境（API key、包结构）

# 步骤 3：金丝雀验证（可选，用于快速反馈）
./scripts/arc-bench-gate.sh canary --task bookstack
# ✓ 通过 → 进入 full
# ✗ 失败 → 退回分析

# 步骤 4：完整 A/B（发布前）
./scripts/arc-bench-gate.sh full --base main --head feature-branch
# ✓ 通过 → 可合并
# ✗ 失败 → 分析回归
```

---

## 🎯 脚本 2：arc-bench-milestone.sh

### 借鉴来源

**octos-p 的里程碑命令结构（TESTING.md 25-36 行）：**
- 规范的命令入口
- 清晰的输入/输出契约
- 可追溯的证据链

### 解决的问题

**P5-005：A/B 身份链不完整**
- 上传 Agent 构建、任务快照、平台评分的身份绑定缺失
- 无法构成严格 A/B 对比

### 三个命令

#### 1. upload-and-bind

**目的：** 上传 Agent 构建并记录平台返回的 `task_snapshot_id`

**用法：**
```bash
./scripts/arc-bench-milestone.sh upload-and-bind \
  --agent-build-sha abc123def \
  --task bookstack \
  --output evidence/arc-bench/upload-receipts/bookstack-abc123de-20260924.json
```

**输出示例（upload-receipt.json）：**
```json
{
  "timestamp": "2026-09-24T12:34:56Z",
  "agent_build_sha": "abc123def456",
  "task": "bookstack",
  "task_snapshot_id": "snapshot_xyz789",
  "upload_url": "https://arc-bench.example.com/uploads/snapshot_xyz789",
  "platform_response": {
    "status": "success"
  },
  "git_info": {
    "repo": "git@github.com:example/octos-p.git",
    "branch": "feature-branch",
    "commit_timestamp": "2026-09-24 10:20:30 +0000"
  }
}
```

**关键字段：**
- `task_snapshot_id`：平台返回的快照 ID，后续 Run 必须引用它
- `agent_build_sha`：Agent 构建的 Git SHA，确保可追溯

**状态：** 🚧 上传逻辑待实现（当前生成模板）

---

#### 2. validate-ab-pair

**目的：** 验证一对 base/head 的身份链完整性

**用法：**
```bash
./scripts/arc-bench-milestone.sh validate-ab-pair \
  --base-receipt evidence/arc-bench/upload-receipts/base.json \
  --head-receipt evidence/arc-bench/upload-receipts/head.json \
  --run-id 1b0eaf914e94
```

**检查项：**
1. ✓ 同一任务（base.task == head.task）
2. ✓ 不同构建（base.sha != head.sha）
3. ✓ 有效的 snapshot ID（非 PLACEHOLDER）
4. ⚠ Run metadata 引用（需查询平台 API）

**输出示例（ab-validation.json）：**
```json
{
  "run_id": "1b0eaf914e94",
  "timestamp": "2026-09-24T13:00:00Z",
  "base_receipt": "evidence/arc-bench/upload-receipts/base.json",
  "head_receipt": "evidence/arc-bench/upload-receipts/head.json",
  "base": {
    "task": "bookstack",
    "agent_build_sha": "abc123",
    "task_snapshot_id": "snapshot_base"
  },
  "head": {
    "task": "bookstack",
    "agent_build_sha": "def456",
    "task_snapshot_id": "snapshot_head"
  },
  "validation": {
    "strict_comparable": true,
    "issues": []
  }
}
```

**标准：** `strict_comparable: true` 才能用于 A/B 对比

**状态：** ✅ 本地验证已实现，平台查询待实现

---

#### 3. generate-frozen-seed

**目的：** 从参考 Run 提取冻结的初始状态（用于复现矩阵）

**用法：**
```bash
./scripts/arc-bench-milestone.sh generate-frozen-seed \
  --run-id d9a97cb4c92d \
  --output evidence/arc-bench/frozen-seeds/d9a97cb4c92d-seed.json
```

**输出示例（frozen-seed.json）：**
```json
{
  "source_run_id": "d9a97cb4c92d",
  "timestamp": "2026-09-24T13:30:00Z",
  "seed_version": "v2",
  "tasks": {
    "bookstack": {
      "initial_db_state": "...",
      "fixture_data": "..."
    },
    "keep": {
      "initial_db_state": "...",
      "fixture_data": "..."
    }
  }
}
```

**用途：** 供 `arc-bench-repro-matrix.sh` 使用，确保每次复现从同一状态开始

**状态：** 🚧 提取逻辑待实现

---

### 完整工作流

```bash
# 1. 构建并上传 base
./scripts/arc-bench-milestone.sh upload-and-bind \
  --agent-build-sha $(git rev-parse main) \
  --task bookstack
# 记录 receipt 路径：BASE_RECEIPT

# 2. 构建并上传 head
./scripts/arc-bench-milestone.sh upload-and-bind \
  --agent-build-sha $(git rev-parse HEAD) \
  --task bookstack
# 记录 receipt 路径：HEAD_RECEIPT

# 3. 运行平台 Run（在平台 UI 或 API 中执行）
# 记录返回的 RUN_ID

# 4. 验证 A/B 身份链
./scripts/arc-bench-milestone.sh validate-ab-pair \
  --base-receipt $BASE_RECEIPT \
  --head-receipt $HEAD_RECEIPT \
  --run-id $RUN_ID
# ✓ strict_comparable: true → 可用于对比
# ✗ strict_comparable: false → 身份链断裂，不可比
```

---

## 🎯 脚本 3：arc-bench-repro-matrix.sh

### 借鉴来源

**minimax-code 的 performance-ci.md（44 行）：**
```
Noise limit: Range exceeds 30% of median on either revision; 
after five pairs the single most extreme sample per revision 
is discarded before measuring the range
```

**关键思想：**
- 多次重复测量
- 丢弃极端值（最快/最慢各 N 次）
- 统计判定：≥ threshold 的一致性 → confirmed

### 解决的问题

**P5-002, P5-008, P5-009：** 时序敏感问题无法与真实缺陷区分
- REQ-8.1（收藏项）需要"至少 10 个 fresh-copy 的同一 seed"
- 无法区分：runner 噪声 vs 真实异步竞态

### 用法

```bash
./scripts/arc-bench-repro-matrix.sh \
  --req REQ-8.1 \
  --seed evidence/arc-bench/frozen-seeds/d9a97cb4c92d-seed.json \
  --iterations 10 \
  --discard-extremes 1 \
  --threshold 0.75
```

**参数说明：**
- `--req`：需求 ID（用于目录命名和追溯）
- `--seed`：冻结的初始状态（确保每次从同一起点）
- `--iterations`：独立运行次数（默认 10）
- `--discard-extremes`：丢弃最快/最慢各 N 次（默认 1）
- `--threshold`：确认阈值（默认 0.75，即保留 8 次中需 6 次一致）

### 执行逻辑

```
迭代 1-10：
  1. 从 frozen seed 恢复初始状态
  2. 运行测试并记录 pass/fail + duration
  3. 保存完整 trace 到 iteration-NNN/

分析：
  1. 按 duration 排序
  2. 丢弃最快 1 次 + 最慢 1 次
  3. 保留 8 次中统计一致性：
     - ≥6 次 fail → confirmed（真实问题）
     - ≥6 次 pass → false_alarm（已修复或误报）
     - 其他 → timing_sensitive（需进一步分析）
```

### 输出结构

```
evidence/arc-bench/repro-matrix/REQ-8.1-20260924T130000Z/
├── matrix-summary.json          # 汇总结果
├── iteration-001/
│   ├── result.txt               # pass/fail
│   ├── duration.txt             # 耗时（秒）
│   ├── metadata.json            # 元数据
│   └── trace.log                # 完整 trace
├── iteration-002/
│   └── ...
└── ...
```

**matrix-summary.json 示例：**
```json
{
  "req_id": "REQ-8.1",
  "seed": "evidence/arc-bench/frozen-seeds/d9a97cb4c92d-seed.json",
  "timestamp": "2026-09-24T13:00:00Z",
  "config": {
    "iterations": 10,
    "discard_extremes": 1,
    "retained_count": 8,
    "confirmation_threshold": 6
  },
  "results": {
    "total": 10,
    "passed": 2,
    "failed": 8,
    "verdict": "confirmed",
    "noise_ratio": "15%"
  }
}
```

### 三种裁决

| 裁决 | 条件 | 下一步 |
|------|------|--------|
| **confirmed** | ≥6/8 次 fail | 进入 Agent 实现切片 |
| **false_alarm** | ≥6/8 次 pass | 更新决策台账为 excluded |
| **timing_sensitive** | 其他（3-5 次 fail） | 增加迭代次数或添加 trace 分析 |

### 当前状态

**✅ 已实现：**
- 脚本框架和参数解析
- 输出目录结构
- 汇总 JSON 生成

**🚧 待实现：**
- 实际测试执行（与技能集成）
- Duration 排序和极端值丢弃
- 噪声比计算

---

## 📊 预期收益对比

### 成本节省

| 场景 | 当前成本 | 优化后成本 | 节省 |
|------|---------|-----------|------|
| 单次开发迭代（有明显错误） | ¥18-37 平台 Run | ¥0 本地 quick | ¥18-37 |
| 单次上传前验证（环境问题） | ¥18-37 平台 Run 失败 | ¥0 本地 preflight | ¥18-37 |
| 金丝雀失败（一个任务不通过） | ¥36 双任务 | ¥6 单任务 | ¥30 |
| REQ-8.1 隔离复现（10 次矩阵） | ¥180-370（10 次完整 Run） | ¥60-120（复用生成） | ¥120-250 |

**总结：**
- 每次开发迭代：省 15-30 CNY（通过 quick gate 过滤）
- 每次环境问题：省 18-37 CNY（通过 preflight 捕获）
- 每次早期失败：省 30 CNY（金丝雀单任务验证）
- 每个时序问题诊断：省 120-250 CNY（复用矩阵而非全量重跑）

### 证据链完整性

**P5-005 解决方案：**
- ✅ 每次上传生成 receipt（含 task_snapshot_id）
- ✅ Run 前强制验证 A/B 身份链
- ✅ `strict_comparable: true/false` 明确标记

**效果：**
- 不再出现"平台 Run 无法反向构成 A/B"的情况
- 每个对比都有可追溯的 Git SHA → snapshot ID → Run ID 链

### 噪声隔离

**P5-002, P5-008, P5-009 解决方案：**
- ✅ 统计判定（6/8 阈值）区分 confirmed vs timing_sensitive
- ✅ 冻结 seed 确保可重复性
- ✅ 丢弃极端值减少 runner 噪声影响

**效果：**
- REQ-8.1 等 strong_candidate 可以升级为 confirmed 或排除
- 避免"看起来像问题但不确定"的长期悬而未决

---

## 🚀 下一步工作

### P0 - 立即可做（已完成）

- [x] 创建 `scripts/arc-bench-gate.sh` 框架
- [x] 创建 `scripts/arc-bench-milestone.sh` 框架
- [x] 创建 `scripts/arc-bench-repro-matrix.sh` 框架
- [x] 文档化实施方案

### P1 - 需代码集成（待授权）

1. **arc-bench-gate.sh 实际执行：**
   - [ ] `canary` 模式：集成技能调用，读取基线配置
   - [ ] `full` 模式：集成双任务 A/B 流程
   - [ ] 退出码规范：0=PASS, 1=FAIL, 2=INCONCLUSIVE

2. **arc-bench-milestone.sh 平台集成：**
   - [ ] `upload-and-bind`：实际调用平台上传 API
   - [ ] `validate-ab-pair`：查询平台 Run metadata
   - [ ] `generate-frozen-seed`：从 Run 目录提取实际 seed

3. **arc-bench-repro-matrix.sh 测试执行：**
   - [ ] 集成技能调用（从 frozen seed 运行）
   - [ ] Duration 排序和极端值丢弃逻辑
   - [ ] 噪声比计算（range / median）

### P2 - 实际验证（待平台授权）

4. **运行 REQ-4.3.1、REQ-6.1.1 的 frozen seed 提取：**
   - [ ] 从 `d9a97cb4c92d` 提取 frozen-seed-v2.json
   - [ ] 验证 seed 可以本地重放

5. **运行 REQ-8.1 的 10 次隔离复现矩阵：**
   - [ ] 执行 10 次独立运行
   - [ ] 分析结果并更新决策台账

6. **首次完整 A/B 身份链：**
   - [ ] 上传 base 和 head（含 receipt）
   - [ ] 运行平台 Run
   - [ ] 验证 strict_comparable: true

---

## 📚 参考文档

### 本仓库

- **决策台账：** `HKT/ARC_BENCH_HACKATHON_PHASE5_DECISION_REGISTER.md`
- **项目记忆：** `HKT/ARC_BENCH_HACKATHON_PROJECT_MEMORY.md`
- **最新交接：** `HKT/ARC_BENCH_RECENT_RUNS_TEAM_HANDOFF_20260924.md`
- **总览：** `HKT/SUMMARY.md`

### 借鉴来源

- **minimax-code：**
  - `docs/performance-ci.md`（回归预算、噪声限制、三级裁决）
  - `.agents/skills/testing-workflow/SKILL.md`（多层门槛）

- **octos-p：**
  - `docs/TESTING.md`（里程碑命令、证据链）
  - `scripts/ci.sh`（脚本结构、pass/fail 标记）

### 外部证据

- `d9a97cb4c92d` 隔离复现：`C:/Users/dayuruozhi/Doubao/chats/2026-09-24/new-chat/repro/`
- `4bab82404c52` 隔离复现：`C:/Users/dayuruozhi/Doubao/chats/2026-09-22/new-chat-3/isolation-4bab82404c52/`

---

## ⚠️ 重要提示

1. **三个脚本当前为框架模板**，核心执行逻辑（平台 API 调用、技能集成）待实现
2. **不授权直接修改 Agent**，必须先完成 P1/P2 验证
3. **不授权直接上传到平台**，必须先通过 preflight 检查
4. **不授权新平台 Run**，必须先完成 A/B 身份链验证

---

## 📝 变更日志

| 日期 | 变更 | 作者 |
|------|------|------|
| 2026-09-24 | 初始版本：创建三个脚本框架和实施文档 | Claude Sonnet 5 |

---

*本文档基于 HKT/SUMMARY.md 的问题分析，借鉴 minimax-code 和 octos-p 的成熟测试框架，为 ARC-Bench 项目提供可落地的优化方案。*
