# Octos Agent Optimization - Round 1 v2 最终版（成功率优先）

## 优化迭代历史

### v1.0 基线 (0925)
- 成功率：96.9% (31/32)
- 执行时间：5.2小时
- 失败：REQ-2.7.5（Edit labels 功能）

### v1.1 激进优化 (0926-失败)
- 成功率：90.6% (29/32) ❌ 比基线差
- 执行时间：3.4小时 ✅ 快35%
- **问题**：900s 超时太短，导致实现质量下降
  - REQ-2.7.5 ✅ 修复成功
  - REQ-2.3.3, REQ-2.4, REQ-2.7.6.3 ❌ 新增失败（并发竞态）

### v2 最终版（成功率优先）
**核心策略**：只改 Prompt，不改超时参数

## v2 最终参数

| 参数 | 基线 (0925) | v1.1 (失败) | v2 最终 | 决策理由 |
|------|-------------|-------------|---------|----------|
| `NODE_TIMEOUT` | 1200s | 900s | **1200s** ✅ | **回退基线** - 比赛优先成功率 |
| `MIN_REPAIR_SECONDS` | 300s | 200s | **300s** ✅ | **回退基线** - 给足修复机会 |
| `IMPLEMENT_FRACTION` | 0.6 | 0.5 | **0.6** ✅ | **回退基线** - 确保实现质量 |

**关键决策**：
- 比赛规则：**先比成功率，再看速度**
- v1.1 教训：快速但质量差 = 失败
- v2 策略：保守但可靠 = 成功

## 保留的优化（已验证有效）

### 1. 测试驱动的需求理解 ✅ **（核心优化）**
**NODE_PROMPT 增强** - 强制分析测试代码

```python
CRITICAL - Before writing any code:
1. Read and analyze the test helper functions (like renameLabel, clickNamed, etc.) to understand the EXACT DOM structure and accessibility labels expected
2. List all required HTML elements with their roles, names, and ARIA labels that the test will query
3. Verify your understanding: describe what UI the test expects to see
```

**效果**：
- ✅ 成功修复了 REQ-2.7.5（从失败变为通过）
- ✅ 强制 agent 理解测试期望的 DOM 结构
- ✅ 避免"Edit labels"和"Change labels"的混淆

### 2. 增量验证指导 ✅
**VERIFY_FULL 修改** - 每 5-10 分钟测试

```python
Verify incrementally as you implement — test every major UI component or API endpoint immediately after writing it (every 5-10 minutes of work). ... Run verification early and often to catch mistakes before running out of time.
```

**效果**：
- 减少在错误方向上的时间浪费
- 早发现早修正

### 3. 失败模式识别 ✅
**REPAIR_PROMPT 增强** - 检测重复错误

```python
CRITICAL - Before attempting repairs:
1. If this is your second repair attempt and the error is similar to the first, your approach is fundamentally wrong - read the test code carefully and implement a COMPLETELY DIFFERENT solution
2. Analyze the test helper functions to understand what DOM structure and accessibility labels are expected
3. Check if you misunderstood the requirement (e.g., "Edit labels" means editing label definitions, NOT assigning labels to notes)
```

**效果**：
- 避免在相同错误上浪费时间
- 强制切换策略

### 4. 时间预算感知 ✅
动态注入时间压力提示

```python
# 实现阶段
if time_left < 600:
    time_pressure_hint = f"\n⚠️ TIME CONSTRAINT: You have only {time_left:.0f}s remaining..."
elif time_left < 900:
    time_pressure_hint = f"\n⏱️ TIME AWARENESS: You have {time_left:.0f}s for this node..."

# 修复阶段
if left < 400:
    time_pressure_repair = f"\n⚠️ CRITICAL: Only {left:.0f}s remaining..."
```

**效果**：
- 帮助 agent 意识到时间限制
- 合理分配时间预算

## v1.1 失败深度分析

### 并发竞态问题
3个新失败的测试特征：
- **单独运行时通过** (round 0/1: 1/1)
- **并行运行时失败** (full suite: FAILED)

```
REQ-2.3.3:   单独 round 1: 1/1 ✅ → full suite: FAILED ❌
REQ-2.4:     单独 round 0: 1/1 ✅ → full suite: FAILED ❌
REQ-2.7.6.3: 单独 round 1: 1/1 ✅ → full suite: FAILED ❌
```

### 根本原因：时间压力导致质量下降
900s 超时让 agent 实现得**太快太粗糙**：
- REQ-2.4: 只用了 **139s**（正常应该 300-500s）
  - 可能缺少充分的错误处理
  - 可能没有考虑并发场景
- REQ-2.7.6.3: 只用了 **75s**（正常应该 200-400s）
  - 快速完成但缺少健壮性
  - 并发时共享状态冲突
- REQ-2.3.3: 第一次 **747s 超时**，修复后才通过
  - 时间不够导致初次实现不完整

### 为什么基线更好？
1200s 超时给了 agent：
- ✅ 更充分的测试时间
- ✅ 更健壮的实现（考虑边界情况）
- ✅ 更好的错误处理（并发安全）
- ✅ 更完整的验证

## v2 预期效果

### 成功率目标
- **目标**：100% (32/32) 🎯
- **最低要求**：≥ 96.9% (31/32)
- **策略**：稳定可靠 > 快速但有风险

### 时间预期
- **预期**：5.0-5.5 小时
- **对比基线**：5.2 小时（基本持平）
- **比 v1.1**：慢约 1.5 小时，但成功率高得多

### 关键验证点
1. ✅ REQ-2.7.5 通过（验证 Prompt 优化有效）
2. ✅ REQ-2.3.3, REQ-2.4, REQ-2.7.6.3 恢复通过（验证超时参数充足）
3. ✅ 其他 29 个测试保持通过（无退化）
4. 🎯 总成功率达到 100%

## 核心洞察

### ✅ 什么有效（保留）
1. **测试驱动的需求理解** - 成功修复 REQ-2.7.5，无副作用
2. **增量验证循环** - 减少浪费时间，早发现早修正
3. **失败模式识别** - 避免重复错误，强制换策略
4. **时间预算感知** - 帮助合理分配时间

### ❌ 什么不行（回退）
1. **缩短超时参数** - 导致实现质量下降
2. **过度优化速度** - 忽视了并发健壮性
3. **激进的时间压力** - 让 agent 写得太快太粗糙

### 💡 关键教训
**比赛规则决定优化方向**：
- 规则：先比成功率，再看速度
- 结论：宁可慢 10%，不可失败 1 个测试
- 策略：保守但可靠 > 激进但有风险

## 实施细节

### 代码改动摘要
**修改文件**：`arc/main.py`

**Prompt 优化**（保留）：
- NODE_PROMPT: +13 行（测试驱动理解）
- VERIFY_FULL: +1 行（增量验证）
- REPAIR_PROMPT: +6 行（失败模式识别）
- node_cycle(): +8 行（时间压力提示）
- acceptance_loop(): +6 行（修复时间提示）

**超时参数**（回退基线）：
```python
self.node_timeout = 1200           # 回退
self.min_repair_seconds = 300      # 回退
self.implement_fraction = 0.6      # 回退
```

### 环境变量覆盖（灵活调整）
如果需要微调，可以通过环境变量：
```bash
OCTOS_NODE_TIMEOUT=1200        # 当前值
OCTOS_MIN_REPAIR_SECONDS=300   # 当前值
OCTOS_IMPLEMENT_FRACTION=0.6   # 当前值
```

## 如果 v2 仍未达到 100%

### Plan B：更激进的 Prompt 优化
1. **强制并发测试验证**
   - 在 VERIFY_FULL 中加入："Test with concurrent requests to ensure thread-safety"
   
2. **共享状态检查**
   - 在 NODE_PROMPT 中加入："Check if your implementation is safe for parallel test execution"

3. **更详细的测试分析要求**
   - 要求 agent 明确说明："This implementation handles concurrent access by..."

### Plan C：回到架构层面
- 考虑修改 codegen 模式的提示
- 增加对 full-suite 失败的特殊处理
- 但这些都是更大的改动，v2 应该足够了

## 版本总结对比

| 版本 | 策略 | 成功率 | 时间 | 状态 |
|------|------|--------|------|------|
| v1.0 基线 | 原始 | 96.9% (31/32) | 5.2h | REQ-2.7.5 失败 |
| v1.1 激进 | 速度优先 | 90.6% (29/32) | 3.4h | ❌ 质量下降 |
| **v2 最终** | **成功率优先** | **预期 100%** | **~5.2h** | **🎯 推荐提交** |

## 提交清单

- ✅ `octos-arc-bundle_v2.zip` 已打包
- ✅ SHA256: `743248A8B7CC3C3CFB15F2C4CFC8906C7B67B1EC66601203401B36F20D676BDC`
- ✅ 策略文档已更新
- ✅ 只改 Prompt，不改超时
- ✅ 保守但可靠

---

**生成时间**：2026-09-26  
**版本历程**：v1.0 (96.9%) → v1.1 (90.6% 失败) → v2 (预期 100%)  
**核心原则**：成功率优先 > 速度优化  
**文件**: `octos-arc-bundle_v2.zip`
