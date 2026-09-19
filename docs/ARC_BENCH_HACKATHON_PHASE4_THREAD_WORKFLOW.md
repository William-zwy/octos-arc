# ARC-Bench 阶段 3 → 阶段 4 会话复用与分支工作流

> 版本：v1.2；更新日期：2026-09-19
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

### 3.3 任务键注册表与单次触发保护

标题搜索只能用于发现候选，不能作为唯一的幂等依据。阶段 3 必须维护任务键注册表：

```text
evidence/arc-bench/phase4-thread-registry.json
```

注册表以规范化的 `<competition_id>--<task_id>` 为键，至少记录：

- `thread_id`、`title`、`project_id`；
- `status`：`candidate`、`handoff_sent`、`verified`、`quarantined` 或 `needs_reconciliation`；
- 最近一次 `run_id`、`manifest`、`handoff_id`；
- 最近一次验证时间、验证结果和失败原因。

每次触发必须遵守单次触发状态机：

1. 先读取注册表，再读取当前会话列表；
2. 注册表中存在唯一 `verified` 会话时，只复用该会话；
3. 存在多个候选、重复标题、注册表与会话列表不一致，或候选会话没有可读最终消息时，标记 `needs_reconciliation`，停止自动 fork；
4. 只有注册表和会话列表都确认“没有候选”时，才允许 fork 一次；
5. fork 后必须立即记录 Thread ID，再改名和发送 handoff；任何步骤失败都不得再次 fork；
6. 只有收到带有相同 `handoff_id` 和 `run_id` 的阶段 4 确认消息，并且最终输出非空，才将状态改为 `verified`；
7. 空输出、异常完成、Thread 不可回读或确认消息缺失的会话必须标记 `quarantined`，不能复用，也不能用同一触发事件继续创建第二个候选。

`run_id` 可以变化，但任务键和规范化阶段 4 Thread ID 不变。同一任务的新 Run 必须在已验证会话中发送新的 `handoff_id`，不能因为旧 Run 分析未完成而再 fork。

### 3.4 持久化回读通道

Thread 消息不是可靠的唯一回读通道。每个 Run 的 manifest 目录必须使用以下三个小文件建立持久化交接：

```text
evidence/arc-bench/runs/<run_id>/phase4-handoff.json
evidence/arc-bench/runs/<run_id>/phase4-ack.json
evidence/arc-bench/runs/<run_id>/phase4-result.json
```

约定如下：

- 阶段 3 在发送 handoff 前写入 `phase4-handoff.json`，记录 `handoff_id`、`run_id`、task key、Thread ID、manifest 和输出文件路径；
- 阶段 4 收到交接后，先写入 `phase4-ack.json`，只记录已收到的 `handoff_id`、`run_id`、Thread ID 和时间，不复制长文本；
- 阶段 4 完成诊断后写入 `phase4-result.json`，正文放在同目录的 `phase4-result.md`，JSON 只保存状态、结论索引、证据路径和阶段 5 建议；
- 阶段 3 直接读取并校验这两个 JSON；Thread 的 `latestAssistantMessageId` 只作为辅助观测，不再决定结果是否可回读；
- 只有 `phase4-ack.json` 与 `phase4-result.json` 的 `handoff_id`、`run_id`、task key 和 Thread ID 全部一致，注册表才可从 `handoff_sent` 变为 `verified`；
- 阶段 5 只消费已验证的 `phase4-result.json`，不消费聊天摘要、空消息或未验证的 Thread 状态。

如果 Thread 已结束但文件回读成功，阶段 4仍视为成功；如果 Thread 有消息但文件缺失或字段不匹配，阶段 4仍视为未验证。

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

1. 生成本次唯一 `handoff_id`，格式为 `<run_id>-<manifest_sha256_prefix>`；
2. 读取任务键注册表和当前阶段 4 会话列表；
3. 如果恰好找到一个 `verified` 会话，向它发送包含新 `run_id` 和 `handoff_id` 的重置 handoff，不 fork；
4. 如果没有找到任何候选，分配新的 `NN`，fork 当前会话到同一项目/工作目录，立即记录 Thread ID，再重命名为标准标题；
5. 如果发现多个候选、旧会话空输出、列表与注册表不一致或 Thread ID 无法回读，标记 `needs_reconciliation`，停止自动分流，不发送重复 handoff；
6. 写入 `phase4-handoff.json`，再发送紧凑 handoff，并要求子会话立即写 `phase4-ack.json`；
7. 用直接文件读取验证 ACK，再等待 `phase4-result.json`；`read_thread` 或 `wait_threads` 只用于辅助观察；
8. 校验两个文件中的 `handoff_id`、`run_id`、task key 和 Thread ID，成功后再把注册表状态改为 `verified`；
9. 记录会话 ID、标题、run ID、handoff ID 和 manifest 路径；
10. 父会话停止该 run 的分析。

应用层 fork 可能保留已完成的历史消息，无法在这里物理删除。子会话必须把 handoff 作为唯一工作上下文，明确忽略此前与该 run 无关的历史；若未来产品提供“无历史 fork”能力，优先使用该能力。

已有会话收到新 Run 时，handoff 必须显式声明“切换当前分析对象”，并清空上一 Run 的工作假设；上一 Run 的结论只能作为已标记的历史记录保留，不能参与当前 Run 的事实判断。

如果 fork 或 handoff 后在规定等待窗口内没有出现 `phase4-ack.json`，父会话只能记录 `handoff_unverified` 并停止；不得通过再次 fork 来“补偿”一次不确定的触发。聊天中的 `PHASE4_HANDOFF_ACK` 可作为人类可读提示，但不能替代文件 ACK。

## 5. 阶段 4 handoff 模板

父会话发送给子会话的内容应控制在必要事实范围内，模板如下：

```text
你是阶段 4 单 run 诊断会话，只处理以下 run。

启动确认：
- 收到后必须先写入 `phase4-ack.json`，再进行证据读取；如 Thread 可正常回复，再额外包含 `PHASE4_HANDOFF_ACK: <handoff_id>`；
- 最终结论必须写入 `phase4-result.json` 和 `phase4-result.md`，并包含 `PHASE4_RESULT: complete|incomplete` 和当前 `run_id`；

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
- handoff_id: <...>
- ack_path: <repo-relative path>
- result_path: <repo-relative path>
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

回交必须写入 `phase4-result.json` 和 `phase4-result.md`，并带有 `PHASE4_RESULT: complete|incomplete`。没有结果文件、没有当前 `run_id`、正文为空或只返回工具过程的会话，不得视为阶段 4 完成。聊天回读失败但结果文件校验通过时，仍可视为阶段 4 完成。

阶段 5 如需修改代码，应在另一个明确的优化工作流中进行；不得把阶段 4 子会话直接变成代码写入会话。

## 8. 失败保护

- 缺少 `run_id`、task 身份或最终结果时，标记 `incomplete`，不要猜测；
- 发现 API Key 明文时，停止继续传播内容，只报告脱敏状态；
- 发现多个 run 混在一起时，拆分 manifest 和子会话；
- 发现 summary 与原始字段冲突时，保留 `conflicts`；
- 发现重复标题或重复 run 时，更新已有阶段 4 会话，不创建重复分析线程；同一任务的新 Run 也复用同一任务会话，但必须使用新的 manifest 和重置 handoff；
- 发现同一任务对应多个阶段 4 会话时，先标记 `thread_mapping_ambiguous` / `needs_reconciliation`，不得自动选择、合并或再次 fork；
- 发现阶段 4 Thread 完成但最终助手消息为空、不可回读或缺少确认标记时，标记 `quarantined`，不得将其当作成功结果；
- 发现 Thread 完成但 `phase4-ack.json` / `phase4-result.json` 缺失时，标记 `handoff_unverified`；只有文件存在但字段不一致时才标记 `quarantined`；
- 发现同一上传事件已经生成 `handoff_id` 时，后续自动继续必须等待原事件完成，禁止重复触发；
- 父会话不得因为等待子会话而继续做阶段 4 分析。

## 9. 当前实现边界

本 SOP 是当前 Codex 协作约定：收到文件夹后由 Agent 执行 manifest 登记、任务键查找、复用或单次 fork、改名、持久化 handoff、文件 ACK/结果回读和注册表更新。它不是后台文件系统监听器；用户未发送上传事件时，不会自行扫描 Downloads 或创建会话。用户明确要求“只记录”时，父会话只记录，不触发阶段 4 分析。
