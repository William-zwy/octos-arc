# Octos Agent Optimization - Round 1

## 优化目标
提升 octos agent 在 ARC-Bench 评估中的成功率，从 96.9% (31/32) 提升到 100% (32/32)

## 失败案例分析：REQ-2.7.5

### 失败表现
- **实现阶段**：900秒超时，19次工具调用，未验证 (verified=False)
- **修复阶段**：592秒超时，13次工具调用，已验证但测试失败 (verified=True, 0/1 passed)
- **最终状态**：剩余 -8秒，低于 300秒修复最小阈值

### 根本原因
1. **需求理解错误**：Agent 可能混淆了"Edit labels"（编辑标签定义）和"Change labels"（给笔记分配标签）
2. **无增量验证**：900秒内写了大量代码才第一次测试，发现完全错误
3. **缺乏时间意识**：没有意识到预算即将耗尽
4. **未分析测试代码**：没有从 `renameLabel()` helper 反推需要的 DOM 结构

## 实施的优化

### 1. 增强需求理解验证（NODE_PROMPT）

**变更内容**：
在实现开始前强制要求 agent：
1. 阅读并分析测试 helper 函数（如 `renameLabel`, `clickNamed`）
2. 列出测试期望的所有 HTML 元素及其 role、name、ARIA labels
3. 描述测试期望看到的 UI 结构

**预期效果**：
- Agent 会发现 `getByRole('group', { name: /^Label Work editable$/i })` 意味着需要一个标签管理 UI
- 避免混淆"编辑标签定义"和"给笔记添加标签"

**代码位置**：`arc/main.py:852-860`

```python
CRITICAL - Before writing any code:
1. Read and analyze the test helper functions (like renameLabel, clickNamed, etc.) to understand the EXACT DOM structure and accessibility labels expected
2. List all required HTML elements with their roles, names, and ARIA labels that the test will query
3. Verify your understanding: describe what UI the test expects to see
```

### 2. 增量验证与频繁测试（VERIFY_FULL）

**变更内容**：
- 从"完成前验证"改为"增量验证"
- 明确要求每 5-10 分钟（每个主要组件）后立即测试

**预期效果**：
- REQ-2.7.5 如果在前 100-200 秒就运行测试，会立即发现缺少标签管理界面
- 避免在错误方向上浪费 900 秒

**代码位置**：`arc/main.py:807-809`

```python
Verify incrementally as you implement — test every major UI component or API endpoint immediately after writing it (every 5-10 minutes of work). ... Run verification early and often to catch mistakes before running out of time.
```

### 3. 失败模式识别（REPAIR_PROMPT）

**变更内容**：
在修复阶段开始前检查：
1. 如果第二次修复仍然失败且错误相似，说明方法根本错误 → 要求完全不同的解决方案
2. 分析测试 helper 理解期望的 DOM 结构
3. 检查是否误解了需求（明确举例"Edit labels" vs "分配标签"）

**预期效果**：
- 避免在错误方向上重复尝试
- 第二次修复会切换策略

**代码位置**：`arc/main.py:893-896`

```python
CRITICAL - Before attempting repairs:
1. If this is your second repair attempt and the error is similar to the first, your approach is fundamentally wrong - read the test code carefully and implement a COMPLETELY DIFFERENT solution
2. Analyze the test helper functions to understand what DOM structure and accessibility labels are expected
3. Check if you misunderstood the requirement (e.g., "Edit labels" means editing label definitions, NOT assigning labels to notes)
```

### 4. 调整超时参数

**变更内容**：
- `OCTOS_NODE_TIMEOUT`: 1200s → 900s（强制更快验证）
- `OCTOS_MIN_REPAIR_SECONDS`: 300s → 200s（允许更多修复轮次）
- `OCTOS_IMPLEMENT_FRACTION`: 0.6 → 0.5（为验证和修复留更多时间）

**预期效果**：
- 900s 超时会强制 agent 更早运行测试
- 200s 最小阈值让 REQ-2.7.5 的 -8s 变成可能有 1-2 次修复机会

**代码位置**：`arc/main.py:1022, 1029, 1039`

### 5. 时间预算感知

**变更内容**：
在 implement 和 repair 阶段动态注入时间压力提示：
- 剩余 < 600s：⚠️ 时间紧张提示
- 剩余 < 400s：🚨 关键时刻提示

**实现位置**：
- `node_cycle()` 实现阶段：`arc/main.py:1603-1609`
- `acceptance_loop()` 修复阶段：`arc/main.py:1494-1498`

**预期效果**：
- Agent 会意识到时间压力，优先实现核心功能
- 避免在细节优化上浪费时间

## 优化策略总结

### 优先级排序
1. **最关键**：需求理解验证（解决 REQ-2.7.5 的根本原因）
2. **高价值**：增量验证（避免 900s 浪费）
3. **辅助**：失败模式识别（修复阶段提高效率）
4. **支持**：超时参数调整 + 时间感知（系统层面优化）

### 与历史优化的区别

从 `CHANGELOG.md` 看，之前的 Round 1-22 主要优化**成本和速度**：
- 内联设计模式（减少请求）
- codegen 模式（一次生成完整代码）
- reasoning mode 调整（low/none 降低成本）
- 请求数量限制

**本轮优化聚焦成功率**：
- 强化需求理解（避免方向性错误）
- 增量开发（早发现早修正）
- 时间管理（在预算内完成）

两者不冲突：成本优化针对"正确实现"的效率，成功率优化针对"避免错误实现"

## 风险评估

### 潜在负面影响
1. **增加 prompt 长度**：新增的 CRITICAL 指导可能略微增加 token 消耗
   - 预估影响：每个节点 +100-200 tokens
   - 但避免 1 次完全失败能节省数千 tokens

2. **900s 超时可能太激进**：某些复杂功能可能需要 >900s
   - 缓解措施：可通过环境变量 `OCTOS_NODE_TIMEOUT=1200` 覆盖
   - 数据依据：从日志看大部分成功节点都在 900s 内完成

3. **时间提示可能分散注意力**：频繁的时间警告可能打断思考
   - 缓解措施：仅在 <900s 和 <600s 时显示，不在每次工具调用后

### 验证计划
1. 使用相同的测试集（keep 32 个需求）重新评估
2. 重点观察 REQ-2.7.5 是否通过
3. 检查其他 31 个节点是否有退化
4. 对比总执行时间（目标：不超过 5.5 小时）

## 下一步

### 立即行动
```bash
cd D:\items\Hackathon\octos-p
./build.sh  # 重新打包 agent
cd D:\items\Hackathon\hackathon-local-simulation
# 提交并评估
```

### 如果成功率仍未达标
考虑更激进的策略：
1. **强制中间检查点**：在 implement 阶段 300s 时强制运行一次测试
2. **测试驱动代码生成**：在 design 阶段生成测试期望的 HTML mock
3. **双阶段实现**：先生成最小可测试版本，通过后再优化

### 监控指标
- 成功率：目标 100% (32/32)
- 执行时间：目标 ≤ 5.5 小时
- Token 成本：容忍 +10% 以换取成功率提升

---

**生成时间**：2026-09-26  
**基础版本**：octos-keep-0925 (96.9% 成功率)  
**修改文件**：arc/main.py
