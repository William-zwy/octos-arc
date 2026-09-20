# 阶段 4 只读诊断报告：arc-bench-lite--keep

## 结论

本次只分析 Run `737b56972d5a`，没有创建新 Run、上传文件、修改代码或修改测试。

平台最终结果为 **FAILED，30/32，score 93.8%**。失败不是入口、测试目录、bundled tests、API Key 或平台整体异常，而是最终页面/初始数据层的两个确定性问题：

1. `REQ-2.7.5` 找不到 `Work editable` 标签对应的可编辑输入框，等待 10 秒后超时。
2. `REQ-2.7.6.3` 定位 `Reminders` 视图时同时匹配静态导航按钮和动态标签按钮，触发 Playwright strict mode failure。

最终提交包的静态内容直接支持这两个判断：后端只 seed `Work` 与 `Reminders`，没有 `Work editable`；静态 `#nav-reminders` 与动态 `data-label="Reminders"` 按钮也没有区分 accessible name。

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

代码修复记录也提出了补齐 `Work editable` 的候选方案，但该记录属于诊断假设，不能单独作为成功证据；最终包未包含该候选改动。这里的高置信判断来自平台 locator 超时与最终包静态证据的交叉验证。

### REQ-2.7.6.3：两个 Reminders 按钮共享 accessible name

最终错误为 Playwright strict mode violation：

```text
getByRole('complementary')
  .getByRole('button', { name: /^Reminders$/i })
```

实际匹配了两个按钮：

1. `#nav-reminders`：静态 Reminders 视图导航。
2. `button[data-label="Reminders"]`：动态 Reminders 标签按钮。

最终 `index.html` 中静态导航按钮只有可视文字 `Reminders`，没有区分性的 `aria-label`；最终 `app.js` 中动态标签按钮也直接以标签名作为可访问名称。最终 ZIP 中 `Reminders view` 出现次数为 0，说明候选的导航命名修复没有进入最终包。

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

## 阶段 5 建议

建议交给阶段 5 的范围仅限以下内容：

1. 在后端干净初始化路径中补齐 `Work editable`，并确认最终提交包实际携带该状态。
2. 为 `#nav-reminders` 增加区别于动态标签按钮的 accessible name；不要重命名 `Reminders` 标签。
3. 两个修复分别验证，再合并验证；每次从干净状态运行完整 `/workspace/tests`。
4. 不修改官方测试与 helper，不做数据库重构、导航重构或无关 UI 重构。
5. 只有完整套件达到 `32/32` 且无新增失败时，才提交平台重跑。

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

以下内容当前缺失：task snapshot、build/code SHA、上传 ZIP SHA-256、clean-seed 前后数据库哈希、trace/HAR、失败时 error-context body，以及 LLM/浏览器/测试的精确耗时拆分。因此，本报告只把最终 Run 对象、最终 Playwright 报告、失败详情、原始日志和最终模板 ZIP 作为证据；代码修复记录仅作为候选假设，未当作平台成功证明。

## 文件与执行边界

- 结果 JSON：[phase4-result.json](phase4-result.json)
- ACK：[phase4-ack.json](phase4-ack.json)
- 本报告只读分析 `737b56972d5a`，未分析其他任务或其他 Run。
- 未创建新 Run，未上传，未修改代码，未修改测试，未执行远程同步。
