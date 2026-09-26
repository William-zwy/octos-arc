# ARC-Bench 优化实施总结（快速参考）

> 2026-09-24 | 基于 minimax-code 和 octos-p 最佳实践

---

## 🎯 创建了什么

三个新脚本，解决 HKT/SUMMARY.md 中的核心瓶颈：

### 1. arc-bench-gate.sh — 多层验证门槛

**问题：** 每次改动直接跑¥18-37 的平台 Run，没有快速失败机制

**解决：** 四层门槛，按成本递增

| 模式 | 成本 | 时长 | 用途 |
|------|------|------|------|
| `quick` | ¥0 | 5分钟 | 本地 lint/test，过滤明显错误 |
| `preflight` | ¥0 | 1分钟 | 上传前：认证/环境/包结构 |
| `canary` | ~¥6 | 1小时 | 单任务验证，早期失败 |
| `full` | ¥36-74 | 5-10小时 | 完整 A/B，发布前 |

**借鉴：**
- minimax-code 的 basic/full 分层（performance-ci.md 13-14 行）
- octos-p 的里程碑命令结构（TESTING.md 25-36 行）

**快速开始：**
```bash
# 开发迭代
./scripts/arc-bench-gate.sh quick

# 上传前检查
./scripts/arc-bench-gate.sh preflight

# 金丝雀（可选）
./scripts/arc-bench-gate.sh canary --task bookstack

# 完整 A/B
./scripts/arc-bench-gate.sh full --base main --head feature-branch
```

---

### 2. arc-bench-milestone.sh — A/B 身份绑定

**问题：** P5-005 — 平台 Run 缺 task_snapshot_id，无法构成严格 A/B

**解决：** 上传协调 + 身份验证

| 命令 | 用途 |
|------|------|
| `upload-and-bind` | 上传 Agent 构建，记录 task_snapshot_id |
| `validate-ab-pair` | 验证 base/head 身份链完整性 |
| `generate-frozen-seed` | 提取冻结 seed（供复现矩阵使用） |

**输出：**
- `upload-receipt.json` — 含 agent_sha + snapshot_id + upload_url
- `ab-validation.json` — 含 strict_comparable: true/false

**借鉴：**
- octos-p 的里程碑命令结构（TESTING.md 25-36 行）

**快速开始：**
```bash
# 1. 上传并记录 base
./scripts/arc-bench-milestone.sh upload-and-bind \
  --agent-build-sha $(git rev-parse main) \
  --task bookstack

# 2. 上传并记录 head
./scripts/arc-bench-milestone.sh upload-and-bind \
  --agent-build-sha $(git rev-parse HEAD) \
  --task bookstack

# 3. 运行平台 Run，记录 RUN_ID

# 4. 验证 A/B 身份链
./scripts/arc-bench-milestone.sh validate-ab-pair \
  --base-receipt <base.json> \
  --head-receipt <head.json> \
  --run-id <RUN_ID>
```

---

### 3. arc-bench-repro-matrix.sh — 噪声隔离

**问题：** P5-002/008/009 — 时序敏感问题无法与真实缺陷区分

**解决：** 10 次独立运行 + 统计判定

| 裁决 | 条件 | 下一步 |
|------|------|--------|
| `confirmed` | ≥6/8 次 fail | 进入 Agent 实现 |
| `false_alarm` | ≥6/8 次 pass | 排除 |
| `timing_sensitive` | 3-5 次 fail | 增加迭代或添加 trace |

**借鉴：**
- minimax-code 的噪声处理（performance-ci.md 44 行）：
  > "after five pairs the single most extreme sample per revision is discarded"

**快速开始：**
```bash
# REQ-8.1 示例
./scripts/arc-bench-repro-matrix.sh \
  --req REQ-8.1 \
  --seed evidence/arc-bench/frozen-seeds/d9a97cb4c92d-seed.json \
  --iterations 10 \
  --discard-extremes 1
```

---

## 💰 预期收益

| 优化项 | 当前成本 | 优化后 | 节省 |
|--------|---------|--------|------|
| 开发迭代（有 lint 错误） | ¥18-37 | ¥0（本地 quick） | ¥18-37/次 |
| 上传前环境问题 | ¥18-37 | ¥0（preflight） | ¥18-37/次 |
| 金丝雀失败 | ¥36（双任务） | ¥6（单任务） | ¥30/次 |
| REQ-8.1 隔离复现 | ¥180-370（10 次完整） | ¥60-120（矩阵） | ¥120-250 |

**估算：** 5 次迭代周期可节省 **¥200-400**

---

## 📋 当前状态

### ✅ 已完成

- [x] 三个脚本框架（bash）
- [x] 参数解析和帮助文档
- [x] 输出目录结构
- [x] JSON 模板生成
- [x] 详细实施文档

### 🚧 待实现（P1）

- [ ] `canary`/`full` 模式的实际执行逻辑
- [ ] 平台 API 集成（上传/查询）
- [ ] frozen seed 提取逻辑
- [ ] 复现矩阵的技能集成

### ⏸️ 待授权（P2）

- [ ] REQ-4.3.1、REQ-6.1.1 的 frozen seed 提取
- [ ] REQ-8.1 的 10 次隔离复现矩阵
- [ ] 首次带完整身份链的 A/B Run

---

## 🔗 相关文档

- **完整实施文档：** `HKT/ARC_BENCH_OPTIMIZATION_IMPLEMENTATION_20260924.md`
- **决策台账：** `HKT/ARC_BENCH_HACKATHON_PHASE5_DECISION_REGISTER.md`
- **项目总览：** `HKT/SUMMARY.md`

---

## 🚀 立即开始

```bash
# 测试 quick gate
cd D:\items\Hackathon\octos-p
./scripts/arc-bench-gate.sh quick

# 查看帮助
./scripts/arc-bench-gate.sh --help
./scripts/arc-bench-milestone.sh --help
./scripts/arc-bench-repro-matrix.sh --help
```

---

## ⚠️ 关键限制

1. **当前为框架模板**，核心执行逻辑待实现
2. **不授权修改 Agent**，必须先完成验证
3. **不授权上传/Run**，必须先通过 preflight

---

*基于 minimax-code 性能 CI 和 octos-p 测试框架的最佳实践*
