# ARC-Bench 阶段 3 → 阶段 4 会话复用与分支工作流

> 版本：v1.1；更新日期：2026-09-19
>
> 适用范围：当前项目的 ARC-Bench 阶段 3 证据接收和阶段 4 单 run 只读诊断

## 1. 目标

每当用户上传一个包含单个 ARC-Bench run 产物的文件夹时：

1. 当前父会话只负责解析、登记和压缩阶段 3 事实；
2. 阶段 3 解析完成后，优先复用已有的同任务阶段 4 会话；只有找不到时才 fork 新会话；
3. 阶段 4 会话按稳定的任务名命名，Run ID 不进入标题；
4. 阶段 4 会话只分析该 run，不执行其他任务、其他阶段或代码修改；
5. 阶段 4 会话只接收阶段 3 关键卡片和阶段 4 所需证据，忽略无关历史。

当前会话是“阶段 3 接收/记录会话”，不是单任务分析会话。父会话完成分支后应停止对该 run 的诊断，不在父会话和子会话重复分析。

## 2. 角色边界

### 父会话：阶段 3 Intake

允许：

- 枚举上传文件夹；
- 读取文件类型、大小、SHA-256 和结构；
- 提取 run/submission/task、最终状态、测试结果、计量和平台核验信息；
- 建立或更新 `evidence/arc-bench/runs/<run_id>/manifest.json`；
- 记录来源冲突和缺失项；
- 创建阶段 4 分支并发送紧凑 handoff。

禁止：

- 分析业务根因；
- 修改 Agent、官方测试或运行配置；
- 创建新 run 或重跑任务；
- 把不同 run 的数据合并成一个结论；
- 将完整日志全文复制到父会话或 handoff。

### 子会话：阶段 4 Diagnosis

允许：

- 读取该 run 的阶段 3 manifest 和用户提供的原始附件；
- 分析失败测试、内部验收、最终平台结果、生成快照和证据链；
- 输出根因候选、已排除原因、证据缺口和阶段 5 建议入口；
- 在需要时只读查看当前 Agent 代码以定位责任边界。

禁止：

- 创建新 run、重跑、上传或改写提交；
- 修改仓库代码、官方测试、需求或资产；
- 直接实施阶段 5 优化；
- 分析其他 run，除非阶段 3 handoff 明确提供了可比较的对照字段；
- 将推测写成已经确认的事实。

## 3. 触发与分支命名

### 3.1 触发条件

收到用户上传的文件夹或一组明确属于同一 run 的文件后，父会话执行阶段 3 Intake。默认约定：一个文件夹对应一个 `run_id`。

如果一个文件夹中发现多个不同 `run_id`：

- 不合并记录；
- 为每个 run 建立独立 manifest；
- 每个 run 分别 fork 一个阶段 4 会话；
- 编号和分支创建按顺序执行，避免 handoff 交叉。

如果无法从文件中确定 run 名称，先使用文件夹名作为临时名称并标记 `run_name_pending`，不猜测任务身份。

### 3.2 标题格式与任务会话复用

标准标题：

```text
NN 项目阶段4 + <competition_id>--<task_id>
```

示例：

```text
05 项目阶段4 + arc-bench-lite--keep
```

编号规则：

1. 读取当前项目已有会话标题；
2. 找出匹配 `^\d{2} 项目阶段4 \+` 的标题；
3. 取现有最大编号加一，使用两位数字；
4. 编号只用于稳定展示和人工排序，任务身份以规范化的 `<competition_id>--<task_id>` 为准；
5. 如果目标任务会话已存在，不创建重复分支，改为向已有会话发送该新 Run 的重置 handoff；
6. Run ID 必须写入 manifest、handoff 和阶段 4 分析正文，用于区分同一任务的不同数据版本。

当前已统一的六个任务标题为：

```text
01 项目阶段4 + smoke--counter
02 项目阶段4 + smoke--dice
03 项目阶段4 + smoke-evolution--counter
04 项目阶段4 + smoke-evolution--dice
05 项目阶段4 + arc-bench-lite--keep
06 项目阶段4 + arc-bench-lite--bookstack
```

## 4. 父会话执行步骤

### Step 1：建立轻量文件索引

只读完成以下动作：

- 列出文件名、扩展名、字节数和 SHA-256；
- 识别 `run.json`、`logs.json`、summary、failure details、Playwright report、snapshots、template ZIP；
- 判断是否有缺失的关键附件；
- 检查是否存在明文 API Key。

不要先把完整日志读入上下文，也不要默认解压 ZIP。

### Step 2：按证据层级提取阶段 3 卡片

按以下顺序提取：

1. `run.json`：最终状态、score、通过/失败数、失败测试、模型、费用、平台 Token、耗时和 ID；
2. `logs.json`：入口、`/workspace/tests`、bundled 回退、provider totals、内部 acceptance round 和最终事件；
3. 失败时读取 Playwright report 和 failure details：locator、超时、调用栈和 error-context；
4. 需要生成状态时才读取失败节点及直接依赖的 snapshots；
5. 需要复现包身份时才读取 ZIP 清单和哈希。

阶段 3 卡片只保存：

```json
{
  "run_id": "...",
  "submission_id": "...",
  "competition_id": "...",
  "task_id": "...",
  "platform_final": {},
  "internal_acceptance": {},
  "metering": {},
  "platform_validation": {},
  "evidence_manifest": "evidence/arc-bench/runs/<run_id>/manifest.json",
  "conflicts": [],
  "missing": []
}
```

必须将 `internal_acceptance`、`platform_final` 和 `metering` 分开，不能用内部修复通过覆盖最终平台失败。

### Step 3：生成或更新 manifest

manifest 是父会话与子会话之间的唯一事实入口。它必须包含：

- run/submission/task 身份；
- 原始附件名称、大小和 SHA-256；
- 证据角色与来源优先级；
- 最终平台结果；
- 内部验收轮次；
- Token/费用/耗时口径；
- 入口和测试目录核验；
- 冲突和缺失项；
- 是否将原始附件复制进仓库。

人工整理的 summary 只能作为导航。与 `run.json`、原始日志或 Playwright report 冲突时，保留冲突并采用结构化原始证据，禁止静默覆盖。

### Step 4：复用或 fork、命名并发送 handoff

父会话在 manifest 完成后：

1. 按规范化的 `<competition_id>--<task_id>` 查询当前阶段 4 标题；
2. 如果恰好找到一个已有会话，直接向它发送包含新 `run_id` 的重置 handoff，不 fork；
3. 如果没有找到，分配新的 `NN`，fork 当前会话到同一项目/工作目录，并将新会话重命名为标准标题；
4. 如果找到多个候选会话，先停止自动分支，保留歧义记录，不把新 Run 混入任何一个会话；
5. 发送紧凑 handoff；
6. 记录会话 ID、标题、run ID 和 manifest 路径；
7. 父会话停止该 run 的分析。

应用层 fork 可能保留已完成的历史消息，无法在这里物理删除。子会话必须把 handoff 作为唯一工作上下文，明确忽略此前与该 run 无关的历史；若未来产品提供“无历史 fork”能力，优先使用该能力。

已有会话收到新 Run 时，handoff 必须显式声明“切换当前分析对象”，并清空上一 Run 的工作假设；上一 Run 的结论只能作为已标记的历史记录保留，不能参与当前 Run 的事实判断。

## 5. 阶段 4 handoff 模板

父会话发送给子会话的内容应控制在必要事实范围内，模板如下：

```text
你是阶段 4 单 run 诊断会话，只处理以下 run。

范围：
- 只做只读分析；不创建新 run，不修改代码，不实施阶段 5。
- 只使用下面的阶段 3 卡片、manifest 和该 run 的附件。
- 忽略父会话其他历史、其他任务和其他 run。

Run 卡片：
- run_id: <...>
- submission_id: <...>
- competition/task: <...>
- platform_final: <status/score/pass-total/failure>
- internal_acceptance: <round summary>
- metering: <requests/tokens/cost/duration>
- platform_validation: <entrypoint/tests_dir/bundled/key scan>
- manifest: <repo-relative path>
- conflicts: <only unresolved conflicts>
- missing: <only missing evidence>

阶段 4 输出固定为：
1. 已确认事实；
2. 最终失败链路；
3. 根因候选及证据等级；
4. 已排除原因；
5. 证据缺口；
6. 最小只读复现实验建议；
7. 是否交给阶段 5，以及建议修改边界；
8. 对完成率、Token 和耗时的影响预估。
```

不把完整 logs、完整 snapshots 或 ZIP 内容直接放进 handoff；只给 manifest 路径和必要定点摘要。

## 6. 阶段 4 子会话的低 Token 读取顺序

子会话按以下顺序读取，任何一步已能确认结论时立即停止扩大范围：

1. manifest 和阶段 3 卡片；
2. `run.json` 中最终失败测试；
3. Playwright report 中该失败测试的 locator、timeout 和 stack；
4. failure details 和 error-context；
5. 失败节点对应的 `.arc` design/codegen 快照；
6. 相邻依赖节点；
7. 只有仍然无法判断时才查询完整日志。

阶段 4 输出引用文件、字段和时间点，不复制大段原文。结论必须标注：

- `confirmed`：原始结构化证据直接支持；
- `strong_candidate`：多个证据一致但尚未复现；
- `unknown`：证据不足，不能推断。

## 7. 会话结束与回交

阶段 4 子会话完成后，只回交一份短结论：

- `run_id` 和分支标题；
- 最终平台结果；
- 主要失败类别；
- 根因候选和证据等级；
- 是否建议阶段 5；
- 需要保留的证据路径。

阶段 5 如需修改代码，应在另一个明确的优化工作流中进行；不得把阶段 4 子会话直接变成代码写入会话。

## 8. 失败保护

- 缺少 `run_id`、task 身份或最终结果时，标记 `incomplete`，不要猜测；
- 发现 API Key 明文时，停止继续传播内容，只报告脱敏状态；
- 发现多个 run 混在一起时，拆分 manifest 和子会话；
- 发现 summary 与原始字段冲突时，保留 `conflicts`；
- 发现重复标题或重复 run 时，更新已有阶段 4 会话，不创建重复分析线程；同一任务的新 Run 也复用同一任务会话，但必须使用新的 manifest 和重置 handoff；
- 发现同一任务对应多个阶段 4 会话时，先标记 `thread_mapping_ambiguous`，不得自动选择或合并；
- 父会话不得因为等待子会话而继续做阶段 4 分析。

## 9. 当前实现边界

本 SOP 是当前 Codex 协作约定：收到文件夹后由 Agent 执行 fork、改名和 handoff。它不是后台文件系统监听器；用户未发送上传事件时，不会自行扫描 Downloads 或创建会话。用户明确要求“只记录”时，父会话只记录，不触发阶段 4 分析。
