# 阶段 4 只读诊断：arc-bench-lite--bookstack / Run 1b0eaf914e94

PHASE4_RESULT: complete

- handoff_id：`1b0eaf914e94-73C71551ABB5`
- run_id：`1b0eaf914e94`
- submission_id：`0cb0a4198304`
- task_key：`arc-bench-lite--bookstack`
- Thread：`01a0b582-3586-7bc1-875e-d4670592d5ba`
- manifest SHA-256：`73C71551ABB524B5123D8D0DBCFDAAC9DDF4B4E7A103BA463A732F4DCE143437`

## 范围与身份

本结果只分析 Run `1b0eaf914e94`，不沿用 `cca008377368`、`d4acec5dbbdf` 或其他 BookStack Run 的业务结论。本 Run 的 `submission_id=0cb0a4198304` 与此前不同，并且 manifest 提供了独立的 generation identity。

全程只读：未创建新 Run、未重跑、未上传、未修改 Agent、官方测试、需求或资产。

## 1. 已确认事实

- 平台最终状态：`FAILED`，score `97.1%`，`33/34`。
- 最终唯一失败：`REQ-2.2: Log In Successfully`。
- 失败类型：`timedOut`，耗时 `10016ms`，测试超时为 `10000ms`。
- Playwright 未找到可见的 `BookStack User`：

  ```text
  getByRole('heading', { name: /BookStack\s+User/i }).first()
  ```

- 定位：`/workspace/tests/helpers.ts:134`、`/workspace/tests/REQ-2.2.spec.ts:9`。
- 同一最终套件的另外 33 项通过，说明应用树、服务启动、主要认证后业务链路和多数页面功能均可运行。
- 内部验收轮次不是最终失败列表：round 0 为 `33/34`、失败 `REQ-2.2`；round 1 为 `33/34`、失败 `REQ-4.3.1`；round 2 为 `32/34`、失败 `REQ-2.2` 与 `REQ-8.2`。
- 最终平台 `run.json/tests` 和 Playwright 报告只保留 `REQ-2.2`，以此为权威。
- 运行配置：`deepseek-v4-flash`、视觉模型 `deepseek-v4-flash-vision-exp`、`reasoning=low`、time budget `51000s`、内部 workers `2`、最终测试 workers `1`。
- Token/费用：provider totals 为 `1215` requests、`31,206,622` tokens；平台计量为 `42,725,779` tokens、`22.194327 CNY`。两者是不同统计口径。
- 模板 ZIP 有完整的 `frontend/`、`backend/` 应用树；静态 `db.json` 含 `BookStack User`，后端存在登录、session cookie 和已认证导航注入逻辑。
- 原始日志确认入口为 `main.py`、测试目录为 `/workspace/tests`、bundled fallback 命中为 0、无 `sk-` 明文。

## 2. 最终失败链路

```text
应用生成并启动成功
  -> 最终 Playwright 运行 34 项测试
  -> REQ-2.2 执行登录后的用户身份可见性断言
  -> BookStack User 未被最终 locator 识别为可见元素
  -> 10 秒超时
  -> 33/34、score 97.1、FAILED
```

注意：内部轮次中出现的 `REQ-4.3.1` 和 `REQ-8.2` 不属于最终平台失败链路。

## 3. 根因候选及证据等级

| 候选 | 证据等级 | 判断 |
| --- | --- | --- |
| 登录后首页没有以最终测试可见/可识别的 DOM 形式暴露 `BookStack User` | strong_candidate | 失败 locator、33 项通过和静态导航代码共同指向登录后身份读回边界 |
| 已认证导航的语义标签与平台实际 helper 的 locator fallback 不兼容 | strong_candidate | 代码将昵称渲染为 `span.nav-user`，报告展示的失败 locator 是 heading；但运行时 helper 版本与最终 DOM 缺失，尚不能确认 |
| 登录 API 或 session cookie 失败 | unknown / weak | 没有 response、Set-Cookie 或最终 DOM；但大量依赖登录的测试通过，因此相对不符合整体证据 |
| 登录后导航渲染或页面跳转存在时序问题 | unknown | 失败为 timeout，但没有 trace、DOM 时间线或网络证据 |

静态代码可确认“存在登录和昵称注入路径”，不能证明平台运行时实际返回了预期 HTML。

## 4. 已排除或不能归因的原因

- 不能把内部 round 1 的 `REQ-4.3.1`、round 2 的 `REQ-8.2`当作最终失败。
- 不能归因于应用树缺失或全局服务不可用；最终已有 33/34 通过。
- 不能归因于测试未执行或 bundled tests 回退；34 项官方 Playwright 测试已执行，bundled 命中为 0。
- 不能确认是服务端认证逻辑缺陷；缺少登录响应和 Cookie 证据，且大多数认证后流程通过。
- 不能归因于 API Key 泄露；日志没有 `sk-` 明文。

## 5. 证据缺口

- 登录后最终 DOM / accessibility snapshot。
- `/api/login` 响应、`Set-Cookie`、后续 `/` 请求及 Cookie 状态。
- 平台实际使用的 helper 源码版本；仓库官方快照不足以证明运行时 fallback 完全一致。
- Playwright trace、截图、HAR、控制台和网络错误。
- 实际执行的 `frontend/dist` 内容，而不仅是 ZIP 中的 source 内容。
- 独立的 LLM wall-clock 字段和 task snapshot ID。

## 6. 最小只读复现实验建议

1. 使用本 Run 的模板本地启动，只执行 REQ-2.2 流程，捕获 `/api/login` 响应、Cookie、最终 URL、最终 DOM 文本和 accessibility snapshot。
2. 在不修改官方 helper 的前提下，分别检查 `getByRole('heading', ...)` 与 `getByText('BookStack User')`，确认是语义/selector 不兼容，还是文本根本未进入页面。
3. 对比 source 与构建后的 `frontend/dist`，验证已认证导航占位符和昵称注入后的最终 HTML。

这些实验用于定位，不应在本阶段创建新的平台 Run。

## 7. 是否交给阶段 5及修改边界

建议交给阶段5，但限定为“REQ-2.2 登录后身份读回诊断”，不能直接认定登录 API 或服务端认证损坏。

建议边界：

1. P0：先补齐 DOM、响应和 Cookie 证据，并确认平台实际 helper 版本。
2. P1：若复现确认，优先做最小的 authenticated nickname 语义/可见性兼容修改，保持现有 session 路径不变。
3. P1：增加本地定向门禁：登录响应、Cookie、首页昵称和已认证 dashboard headings。
4. 定向收敛后再进行全量平台重跑，避免内部修复轮次破坏已经通过的 33 项。

不要进行全局重写、先行扩大 Playwright timeout、重写认证逻辑或修改官方测试。

## 8. 对完成率 / Token / 耗时影响预估

- 完成率：修复唯一失败后可从 `33/34 = 97.1%` 提升至 `34/34 = 100%`，绝对提升约 `2.9` 个百分点。
- Token：provider totals 为 `31,206,622`，平台计量为 `42,725,779`；本 Run 已经是高消耗执行，应先做低成本定向复现。
- 费用：`22.194327 CNY`；在定向证据收敛前不建议再次消耗完整 Run。
- 耗时：总耗时 `8548s`，约 `2.37h`；最终 Playwright 约 `31.6s`，失败断言占用 `10016ms`。完整运行时间主要由 Agent 生成/修复阶段构成。
- 风险：修改共享认证或 session 逻辑可能回归现有 33 项，通过最小的昵称读回/语义修复控制变更面。

## 证据文件

- [manifest.json](manifest.json)
- [phase4-handoff.json](phase4-handoff.json)
- [phase4-ack.json](phase4-ack.json)
- [phase4-result.json](phase4-result.json)

外部原始证据位于 manifest 列出的 Downloads 路径，哈希均已复核通过。
