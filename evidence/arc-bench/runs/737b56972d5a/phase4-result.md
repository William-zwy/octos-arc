# 阶段 4 只读诊断报告：arc-bench-lite--keep

PHASE4_RESULT: complete

当前增量 handoff：`737b56972d5a-0BCD0657E978`<br>
补充证据 SHA-256：`2B38407F84689446ABBEA79237782E2FD52585797C58AF76FF5261978A3C51E2`（已核对一致）

## 结论

本次仍只分析 Run `737b56972d5a`，没有创建新 Run、上传文件、修改代码或修改测试。当前增量复核替代旧 handoff `737b56972d5a-D020E69FCE81` 作为结果文件的当前依据。

平台最终结果为 **FAILED，30/32，score 93.8%**。补充的 runner 链路、bundle DB 和评分前 DOM 证据已将原阶段 4 的两个高置信候选升级为 **confirmed**，且当前不再需要 `needs_repro` 才能确认根因：

1. `REQ-2.7.5` 找不到 `Work editable` 标签对应的可编辑输入框，等待 10 秒后超时。
2. `REQ-2.7.6.3` 定位 `Reminders` 视图时同时匹配静态导航按钮和动态标签按钮，触发 Playwright strict mode failure。

最终提交包、runner 加载链路和评分前 DOM 共同支持这两个判断：后端只 seed `Work` 与 `Reminders`，没有 `Work editable`；静态 `#nav-reminders` 与动态 `data-label="Reminders"` 按钮的 accessible name 都是 `Reminders`。

建议进入阶段 5 做两个最小修复，并在干净状态下重新执行完整 `/workspace/tests`。本报告不实施修复。

## 本 Run 的权威指标

| 项目 | 结果 |
|---|---|
| Run / submission | `737b56972d5a` / `42f4e4ae1e6c` |
| 任务 | `arc-bench-lite--keep` |
| 最终状态 | `FAILED` |
| 通过率 | `30/32 = 93.8%` |
| 平台总耗时 | `8224s` |
| 最终 Playwright 耗时 | `26996.226ms`，`30 passed / 2 unexpected` |
| 模型 | `deepseek-v4-flash` |
| 视觉模型 | `deepseek-v4-flash-vision-exp` |
| 推理级别 | `low` |
| 请求数 | `980` |
| 平台 token_count | `23,452,931` |
| provider total tokens | `23,452,827` |
| 费用 | `13.911794 CNY` |

运行合规性核验通过：入口为 `main.py`，测试目录为 `/workspace/tests`，未回退 bundled tests，日志未出现明文 API Key。

## 两个最终失败点

### REQ-2.7.5：缺少 Work editable 初始标签

最终错误为：

```text
locator.fill timeout after 10000ms
getByRole('group', { name: /^Label Work editable$/i })
  .getByLabel(/^Label Work editable$/i)
```

失败位置为 `/workspace/tests/helpers.ts:354` 与 `/workspace/tests/REQ-2.7.5.spec.ts:11`。

最终模板 ZIP 中，`backend/server.js` 的 `seedDefaults()` 只保证以下两个标签：

```text
Work
Reminders
```

`backend/data/db.json` 同样没有 `Work editable`，最终 ZIP 全文搜索 `Work editable` 次数为 0。因此，干净启动时标签管理页不会生成该标签对应的 group/input，测试的 `fill` 等待超时。标签管理器对“已存在的标签”生成关联 label/input 的结构本身是可用的，缺口在初始数据。

补充证据进一步确认：runner 启动时直接读取 bundle 的 `backend/data/db.json`，`loadDB()` 清空 labels，随后 `seedDefaults()` 只重种 `Work` 与 `Reminders`；因此 Agent 自验中临时创建的 `Work editable` 不会进入平台全量执行。设计快照的 `data_model.labels` 也明确要求 `Work editable`。当前判定为 **confirmed、确定性应用实现缺陷**，不是 flaky 或环境问题。

### REQ-2.7.6.3：两个 Reminders 按钮共享 accessible name

最终错误为 Playwright strict mode violation：

```text
getByRole('complementary')
  .getByRole('button', { name: /^Reminders$/i })
```

实际匹配了两个按钮：

1. `#nav-reminders`：静态 Reminders 视图导航。
2. `button[data-label="Reminders"]`：动态 Reminders 标签按钮。

最终 `index.html` 中静态导航按钮只有可视文字 `Reminders`，没有区分性的 `aria-label`；最终 `app.js` 中动态标签按钮也直接以标签名作为可访问名称。补充 DOM 证据确认评分前两个按钮的 accessible name 都是 `Reminders`；最终 ZIP 中 `Reminders view` 出现次数为 0，说明候选的导航命名修复没有进入最终包。当前判定为 **confirmed、确定性应用实现缺陷**。

最小修复应只区分静态视图导航的 accessible name，例如将 `#nav-reminders` 标记为 `Reminders view`，同时保留标签名称 `Reminders`，避免破坏依赖标签名的其他测试。

## Agent 修复过程与回归信号

原始日志记录了以下全套验收链：

```text
round 0: 31/32，失败 REQ-2.7.6.3
round 1: 24/32，失败 8 个节点
round 2: 30/32，失败 REQ-2.7.5、REQ-2.7.6.3
```

这说明修复过程中出现了明显回归，之后虽恢复到 30/32，但没有达到最终平台所需的 32/32。日志中的 targeted node history 曾显示两个相关节点各自 `1/1`，但 targeted 通过与完整套件/最终平台结果不一致，不能作为提交门槛。

阶段 5 应把“干净状态下的完整套件回归”作为唯一提交门槛，并且每次只验证一个小改动，避免再次出现 round 1 的 24/32 回归。

## 增量证据复核

补充文件 `arcbench-737b56972d5a-evidence-chain.md` 的 SHA-256 与 handoff 声明一致。它补齐了旧报告的关键证据链：

- runner 在评分前没有把 `db.json` 重置为另一份 clean-seed，而是直接启动 bundle 中的数据库；
- `loadDB()` 清空 labels，`seedDefaults()` 只生成 `Work` 和 `Reminders`；
- 评分前初始 DOM 同时包含 `#nav-reminders` 与 `data-label="Reminders"`，两个按钮的 accessible name 都为 `Reminders`；
- 设计快照要求 `Work editable`，解释了 targeted Agent 自验通过而平台全量失败的状态差异。

因此，`REQ-2.7.5` 和 `REQ-2.7.6.3` 的根因均升级为 `confirmed`，当前不需要 `needs_repro`。仍然需要阶段 5 做修复后的完整回归；“不需要 needs_repro”表示根因已足够确认，不表示修复后可以跳过验证。

## 阶段 5 建议

建议交给阶段 5 的范围仅限以下内容：

1. 在后端干净初始化路径中补齐 `Work editable`，并确认最终提交包实际携带该状态。
2. 为 `#nav-reminders` 增加区别于动态标签按钮的 accessible name；不要重命名 `Reminders` 标签。
3. 两个修复分别验证，再合并验证；每次从干净状态运行完整 `/workspace/tests`。
4. 不修改官方测试与 helper，不做数据库重构、导航重构或无关 UI 重构。
5. 只有完整套件达到 `32/32` 且无新增失败时，才提交平台重跑。

本次增量复核只更新阶段 4 持久化结果，没有直接向阶段 5 会话发送消息；后续由阶段 3 在身份校验通过后按工作流转交短卡。

### 建议验收标准

- `REQ-2.7.5` 不再出现 10 秒 locator timeout。
- `REQ-2.7.6.3` 的 Reminders 视图定位唯一匹配。
- 完整 `/workspace/tests` 达到 `32/32`。
- 保留每轮失败节点、耗时、token 和最终提交包的哈希/版本信息。

## 对比赛指标的影响

- 当前完成率：`30/32 = 93.8%`。
- 若两个确定性问题均修复且无回归，目标为 `32/32 = 100.0%`，提升 `6.25` 个百分点。
- 当前平台 token_count 为 `23,452,931`，共 `980` 次请求，费用 `13.911794 CNY`。两个小型确定性修复本身不增加运行时 LLM token；主要节省来自减少重复 repair/regression 循环，节省量需要实测。
- 最终 Playwright 约 `27.0s`，其中 `REQ-2.7.5` 的单个失败等待约 `10s`。修复后可减少这部分测试等待，但平台总耗时 `8224s` 主要由 Agent 生成阶段主导，不能把 10 秒直接外推为总耗时下降。

## 证据边界

以下内容仍缺失：task snapshot、build/code SHA、上传 ZIP SHA-256、独立 clean-seed 哈希、trace/HAR、失败时 error-context body，以及 LLM/浏览器/测试的精确耗时拆分。这些缺口不再阻碍本次两个确定性根因升级为 `confirmed`，但仍限制版本追溯和修复后审计的完整性。

补充证据中的 notes 数量文字存在算术不一致（总数 28 与分项 23+8 不完全相符）；该冲突不涉及 labels、初始 DOM 或两个失败用例，因此不改变本次判定。代码修复记录仍只是候选假设，最终包未证明候选改动曾被平台执行。

## 文件与执行边界

- 结果 JSON：[phase4-result.json](phase4-result.json)
- ACK：[phase4-ack.json](phase4-ack.json)
- 补充证据：`C:/Users/dayuruozhi/Downloads/闻悦源代码-首轮测试-keep-lite/arcbench-737b56972d5a-evidence-chain.md`
- 阶段 4 工作流：[`docs/ARC_BENCH_HACKATHON_PHASE4_THREAD_WORKFLOW.md`](../../../docs/ARC_BENCH_HACKATHON_PHASE4_THREAD_WORKFLOW.md)
- 本报告只读分析 `737b56972d5a`，未分析其他任务或其他 Run。
- 未创建新 Run，未上传，未修改代码，未修改测试，未执行远程同步。
