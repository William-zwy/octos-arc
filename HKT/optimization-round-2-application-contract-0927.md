# Octos Agent 优化实施记录：Round 2

> 实施日期：2026-09-27  
> 分支：`0924_hkt-20260926`  
> 本轮主题：跨节点应用契约、依赖回归验收、共享故障归因  
> 当前目标：提高两个云端题目的整体通过率，重点减少后续节点破坏前序功能的问题

---

## 1. 背景

当前两个云端题目合计只能通过约 13% 的测试。结合已有运行现象，本轮没有继续单纯增加 prompt，而是优先修复编排层的结构性问题：

1. 每个节点独立实现，后续节点不知道已有页面、路由、数据模型和接口。
2. 后续节点的验收只关注自己的 spec，可能悄悄破坏祖先节点已经实现的功能。
3. full-suite 失败可能来自启动、共享服务或重复命名的 spec，原有归因逻辑容易错误地把失败归给某个节点。
4. repair prompt 缺少跨节点持久状态，模型只能看到局部错误，难以保持整体一致性。
5. 测试追踪结果可能把依赖回归错误记录到当前节点，影响后续判断。

本轮参考了以下四个 agent 仓库中体现的通用思路：

- `D:\items\Hackathon\claude-code`
- `D:\items\Hackathon\codex`
- `D:\items\Hackathon\minimax-code`
- `D:\items\Hackathon\ZCode`

借鉴的方向包括持久化 session 状态、单一状态源、任务依赖意识、checkpoint/resume 思路和验证闭环。本轮没有直接复制这些仓库的实现代码。

---

## 2. 本轮修改范围

本轮只修改以下四个文件：

| 文件 | 修改内容 |
|---|---|
| `arc/main.py` | 增加应用契约、依赖 spec 回归、契约注入（skeleton/空契约除外，见 §3.7）、测试归因和 full-suite 共享故障处理 |
| `arc/acceptance.py` | 修复重复 basename 或未映射 spec 的失败归因 |
| `arc/tests/test_acceptance.py` | 增加重复 spec basename 的归因测试 |
| `arc/tests/test_main_helpers.py` | 增加应用契约和依赖 spec 上限测试 |

官方 requirements 和官方 acceptance tests 没有修改。

`arc/pack.sh` 当前已经包含 `main.py`、`acceptance.py` 以及相关运行时文件，因此本轮核心逻辑会进入提交包。

---

## 3. 已实现功能

### 3.1 增加 harness 维护的应用契约

在 `Flow` 中增加了跨节点状态：

- `tree`
- `ordered_nodes`
- `application_contract`
- `contract_path`
- `implemented_nodes`

运行过程中会在应用输出目录写入：

```text
.arc/application-contract.json
```

该文件由 harness 维护，不属于模型可直接写入的设计目录。模型可以读取契约，但不能通过普通模型写文件流程篡改它。

契约当前包含：

- `requirements`：节点 ID、名称、描述和依赖关系
- `module_by_node`：节点与模块的映射
- `implemented_nodes`：已经进入实现阶段的节点
- `passed_nodes`：当前已通过本地验收的节点
- `routes`：HTTP 方法和路径对应的节点 owner
- `pages`：已知页面信息
- `data_models_by_node`：节点数据模型
- `designs`：各节点设计结果的精简版
- `source_listing`：当前应用源文件摘要
- `acceptance_ownership`：spec 文件与节点的归属
- `invariants`：跨节点必须保持的约束

默认写入的核心不变量包括：

1. 已实现节点的路由、可访问名称和数据不能被后续节点破坏。
2. 扩展共享服务器时，已有路由必须继续可访问，错误应以 JSON 返回而不是让服务崩溃。
3. 依赖节点之间使用统一数据模型，不能为同一实体建立重复存储。
4. 浏览器 session 默认隔离，除非需求明确要求共享状态。

### 3.2 将应用契约注入关键 agent turn

应用契约会在以下阶段注入 prompt：

- design
- normal implementation
- codegen implementation
- node repair
- full-suite repair
- final check

契约文本包含当前节点 ID，方便模型区分“当前要实现的功能”和“必须保持的已有功能”。

> 注意：skeleton 阶段**不再**注入契约。见 §3.7，此阶段契约必然为空，注入只会增加 token 并拖慢脚手架 turn。此外 `application_context_text()` 现在会在契约"实质为空"时直接返回空串，因此第一个节点在其依赖尚未实现前也自动跳过注入。

为避免契约过大导致上下文浪费，`application_context_text()` 增加了压缩策略：

1. 正常情况下使用紧凑 JSON。
2. 超过约 14,000 字符时移除详细 `designs` 和 `pages`。
3. 同时缩短 source listing 和 requirement description。

### 3.3 增加祖先节点依赖回归验收

新增：

```python
Flow.acceptance_specs_for(node_id, ordered=None)
```

默认策略：

1. 先运行当前节点自己的 spec。
2. 再加入依赖祖先节点的 spec。
3. 自动去重。
4. 默认最多增加 12 个祖先 spec。
5. 当前节点没有自己的 spec 时不额外扩展。

可通过环境变量调节：

```text
OCTOS_ARC_DEP_REGRESSION=0
OCTOS_ARC_DEP_REGRESSION_MAX_SPECS=12
```

该策略已经接入：

- `node_cycle()`
- `regression_cycle()`
- `tests_prompt_for()`
- `spec_bodies()`
- codegen prompt

这样后续节点实现后会尽早发现对祖先功能的回归，而不是等到最后 full-suite 才暴露。

### 3.4 修复重复 basename 的失败归因

测试报告只提供 spec basename 时，单纯使用 basename 可能产生错误归因。例如：

```text
REQ-1.spec.ts
module-a/REQ-1.spec.ts
```

这两个文件 basename 相同，但实际可能属于不同节点。现在的逻辑改为：

- basename 只对应一个节点：归到该节点。
- basename 对应多个节点：归到 `None`。
- spec 没有映射：归到 `None`。
- `None` 在日志和 repair prompt 中显示为 `integration/shared application`。

这样共享故障不会被错误地复制到多个节点上，也不会导致某个节点被错误标记为“通过”。

### 3.5 修复 traceability 测试归属

`Flow.record_tests()` 现在会通过唯一 spec owner 记录测试结果：

- 依赖回归测试结果写回它真正所属的原节点。
- ambiguous basename 不写入错误节点。
- unmapped/shared spec 不写入当前节点。

这使 traceability 数据更接近实际测试归属，避免后续根据错误记录继续做出错误决策。

### 3.6 修复 full-suite 共享故障处理

`final_acceptance()` 现在区分：

- 节点自身 spec 失败
- 重复或未映射 spec 失败
- 应用启动失败
- 共享服务或 integration failure

当 full-suite 出现共享故障时：

- 日志显示 `integration/shared application`
- 所有有 acceptance spec 的节点暂时标为失败，避免错误标记为通过
- repair prompt 明确要求修复共享应用问题
- traceability 不再把同一个结果复制给多个节点

当启动阶段失败时，失败描述会明确包含：

```text
application startup exactly as the grader runs it
```

便于 agent 关注真实启动链路，而不是只修某一个测试文件。

### 3.7 修复 skeleton 阶段的契约注入性能回归

§3.2 最初把契约注入到包括 skeleton 在内的所有关键 turn。实测发现这导致 skeleton 阶段出现明显性能回归（脚手架 turn 从约 419s 拖到 1013s，甚至触及 turn 超时）。根因是：skeleton 运行时契约里还没有任何 implemented/passed/designs，注入的是一份"空壳契约 + 保护已有节点的 invariants"，既浪费 token，其"不要破坏已实现节点"的约束在还没有任何已实现节点时也纯属误导，让模型把本应快速产出脚手架的 turn 当成了整体规划 turn。

采用两个互补的修复：

**方案 A（最小、最对症）：skeleton 阶段不注入契约。**

删除 `Flow.skeleton()` 里的契约注入行（原 `prompt = self.application_context_text(None) + prompt`），改为注释说明。skeleton 只负责脚手架，契约此时无有用信息。

```python
# main.py Flow.skeleton()
prompt = SKELETON_PROMPT.format(...)
# No application_context_text here: at skeleton time the contract holds no
# implemented nodes, designs, or routes, so it is empty overhead. The
# skeleton turn must stay a fast scaffold, not a whole-app planning pass.
```

**方案 B（更稳、覆盖第一个节点）：契约实质为空时直接返回空串。**

`application_context_text()` 增加两道守卫：

```python
# main.py Flow.application_context_text()
# 契约无 implemented/passed/designs 时，注入的是纯噪音，直接返回空串。
if not (payload.get("implemented_nodes") or payload.get("passed_nodes")
        or payload.get("designs")):
    return ""
# 没有已实现节点时，"保护已实现节点"的 invariants 不适用，剔除它们。
if not payload.get("implemented_nodes"):
    payload.pop("invariants", None)
```

这样 skeleton 和第一个节点（其依赖尚未实现前）都会自动跳过注入，后续节点才随着真实跨节点状态的积累逐步获得契约。方案 A 是显式保证 skeleton 绝不注入，方案 B 是让"空契约"在所有调用点都自动降级，两者叠加确保不会因为某个新调用点漏掉判断而重新引入噪音。

实测：skeleton 从 1013s 降回 419s，行为与注入前一致。

---

## 4. 运行流程变化

本轮后的简化流程如下：

```text
解析 requirements/tree
        |
初始化 .arc/application-contract.json
        |
每个节点读取全局契约
        |
设计阶段写回契约
        |
实现阶段读取契约并保护已有路由/数据
        |
当前节点 spec + 有界祖先 spec 回归
        |
记录唯一 owner 的 traceability
        |
full-suite 检查节点失败与 shared failure
        |
更新契约并进入下一个节点
```

契约会在设计、实现、验收和 repair 后持续更新，因此后续节点能看到前面节点的最新状态。

---

## 5. 测试和静态验证

### 5.1 已通过

```powershell
python -m py_compile arc/main.py arc/acceptance.py arc/tests/test_acceptance.py arc/tests/test_main_helpers.py
```

结果：通过。

```text
git diff --check
```

结果：通过，没有发现 diff 空白错误。

本轮新增和相关定向测试：

```text
7 tests OK
```

覆盖内容包括：

- 重复 spec basename 被放入 shared integration bucket。
- 应用契约可以写入 `.arc/application-contract.json`。
- 契约包含 route、requirement、acceptance ownership 和 invariants。
- 祖先 spec 会被加入回归测试。
- `OCTOS_ARC_DEP_REGRESSION_MAX_SPECS` 能限制额外 spec 数量。

### 5.2 完整测试的已知环境问题

完整测试命令曾运行：

```powershell
python -m unittest discover -s arc/tests -t arc
```

当前 Windows 环境中，多个既有测试无法在临时目录创建目录，主要表现为：

- `C:\Users\16062\AppData\Local\Temp` 下的临时目录 ACL/权限错误。
- 改用工作区临时目录后仍有类似权限问题。
- 总体出现约 14 个临时目录权限错误。
- 另有 1 个既有环境路径断言失败。

这些失败不是本轮核心逻辑的语法错误，也没有发现由本轮新增逻辑直接导致的失败。后续仍需要在权限正常的环境中重新跑完整测试。

### 5.3 尚未完成

本轮修改尚未重新提交云端运行，因此以下指标还没有实测结果：

- 两个题目的云端总通过率
- 节点通过率
- full-suite 通过数
- shared/integration failure 数量
- repair 次数
- token 和时间消耗

---

## 6. 风险和注意事项

### 6.1 Prompt 长度增加

应用契约会增加 prompt 内容，尤其是在节点较多、设计信息较丰富时。当前已经增加长度裁剪，但仍需观察云端 token 消耗和模型注意力是否下降。

### 6.2 祖先 spec 增加本地验收成本

默认每个节点最多额外运行 12 个祖先 spec，可能增加验收时间。若云端题目节点较多，可先通过：

```text
OCTOS_ARC_DEP_REGRESSION_MAX_SPECS=4
```

进行成本对比，但默认不建议直接关闭，因为当前核心问题正是后续节点破坏已有功能。

### 6.3 basename 映射仍受报告格式限制

如果云端报告只提供 basename，重复 basename 无法可靠判断具体 owner，只能归到 shared integration。更理想的方案是让 runner 保留相对路径或稳定 test ID。

### 6.4 契约不是业务数据库

`.arc/application-contract.json` 用于 agent 编排和上下文传递，不应替代应用自己的数据库、API schema 或前端状态管理。模型仍必须在真实代码中实现持久化和一致性。

---

## 7. 下一步建议

1. 使用 `sh arc/pack.sh` 重新生成提交包。
2. 在权限正常的环境重新运行完整本地测试。
3. 重新提交两个云端题目，记录节点通过率和 shared failure。
4. 对比本轮前后：
   - 后续节点是否仍然破坏前序路由。
   - full-suite 中 shared failure 的数量。
   - repair 是否更少重复修复同一个错误。
   - 契约注入带来的 token/time 增量。
5. 如果通过率仍然很低，第二轮重点考虑：
   - 更细粒度的 checkpoint/resume。
   - repair 前后的持久化状态快照。
   - 对已经通过节点的文件和路由增加更强保护。
   - 对并发测试、共享数据库和 session 隔离加入明确的 runtime 检查。

---

## 8. 变更摘要

本轮的核心不是让单个节点写更多代码，而是让整个 agent 在多个节点之间保持一致：

```text
全局应用契约
+ 依赖节点回归验收
+ 正确的 shared failure 归因
+ 唯一 owner 的 traceability
```

这四项改动共同服务于一个目标：后续节点继续开发时，能够看到并保护已经完成的应用，而不是把每个节点当成互相隔离的小项目。

