# 阶段4诊断结果：arc-bench-lite--bookstack / Run 4bab82404c52

## 已确认事实

- 本文档只分析 Run `4bab82404c52`，对应 submission `7e0bd4dc8e9`；未合并此前 BookStack Run 的结论。
- 身份、handoff、manifest 及 manifest 声明的 8 个外部证据 SHA-256 均已核对通过。
- 最终平台结果为 `FAILED`，score `91.2`，通过 `31/34`；最终权威失败节点为 `REQ-6.1.1`、`REQ-6.1.2`、`REQ-9.1`。
- 三个失败均为 10 秒级 Playwright locator timeout，不是平台统一异常。入口为 `main.py`，测试目录为 `/workspace/tests`，日志中没有 bundled tests 回退。
- REQ-6.1.2 与 REQ-9.1 都在 `returnHomeByLogo` 等待 `getByRole('button', { name: /^BookStack$/i }).first()`；REQ-6.1.1 等待 `Page Created 6.1.1` heading。
- 静态模板中确实存在 BookStack logo button，静态 `createPage` 看起来会写入页面、更新 `book.page_ids` 后重定向，静态 `createDraft` 会持久化草稿后重定向。因此静态源码不足以直接证明后端逻辑就是根因。
- 平台 token_count 为 `37,625,229`，provider total_tokens 为 `37,625,127`，请求数 `1,275`，费用 `18.351171 CNY`；两种 token 口径不相加。

## 最终失败链路

1. `REQ-6.1.1 / Save Page`：保存流程后等待标题 `Page Created 6.1.1`，`10,009ms` 后超时。
2. `REQ-6.1.2 / Save Draft`：保存草稿后在共同 helper 等待可访问名称为 `BookStack` 的 logo button，`10,015ms` 后超时。
3. `REQ-9.1 / Quick Navigation from Recently Updated`：快速导航后在同一共同 helper 等待同一 logo button，`10,010ms` 后超时。

其中后两项具有明确的共同失败边界：运行时没有被测试识别到预期的 logo button。静态页面存在该按钮，但当前证据没有证明最终加载的 DOM、资源版本和导航结果与静态源码一致。

## 根因候选及证据等级

### 强候选：保存/导航后的运行时模板或资源边界

REQ-6.1.2 与 REQ-9.1 在同一 logo helper、同一 accessible locator 处失败，而多个静态模板都包含该按钮。更可能的范围是运行时 HTML、动态模板、构建/打包产物、静态资源加载或导航结果；不能仅凭静态源码区分这些情况。

### 强候选：Save Page 后的页面读回或可观察语义

REQ-6.1.1 的保存后断言没有拿到目标标题。静态路径会更新 `db.pages` 和 `book.page_ids`，因此需要重点验证实际保存请求、重定向后的书籍页读回，以及页面名称/标题的可访问呈现。

### 候选：执行包与静态审阅源码不一致

manifest 同时记录了 platform template ZIP 与 release source ZIP，二者不是同一文件；当前也没有平台执行包 SHA 的直接关联。这只能作为候选和证据缺口，不能直接判定为错配。

### 未知：具体请求、会话、数据库或语义细节

目前没有最终 URL、HTTP 响应、重定向链、cookie/session、最终 DOM、network/console trace 或 REQ-6.1.1 的 request/response trace，因此不能确定是 form action、会话、数据库读回、路由、模板、构建产物还是可访问性语义导致失败。

## 已排除原因

- 不是未执行官方测试：日志明确使用 `/workspace/tests`。
- 不是 bundled tests 回退：日志中 `bundled` 命中为 0。
- 不是入口未执行：日志含 `main.py` 执行记录。
- 不是平台统一异常：三个失败均有明确 Playwright locator timeout，最终 failure reason 为测试失败/运行时错误。
- 不能把 acceptance round 0 的汇总数字当最终结果；本 Run 的最终权威结果是 `31/34`。
- 不能据静态源码直接断言 `createPage` 或 `createDraft` 在运行时已经正确，静态路径只支持候选分析。

## 证据缺口

- 三个失败点的最终 URL、最终 DOM/可访问性树和截图。
- 保存请求的 URL、方法、状态码、响应体、重定向链和 cookie/session 状态。
- 执行容器实际使用的前端/后端构建产物、静态资源版本及构建/打包 SHA。
- REQ-6.1.1 保存前后数据库或服务端读回状态。
- REQ-6.1.1 的最终 request/response trace，以及运行时 console、network、页面加载和路由错误记录。

## 最小只读复现实验建议

本阶段不创建新平台 Run，也不修改代码或官方测试。建议阶段5只对三个失败节点做最小本地定位：

1. 分别记录保存/导航前后 URL、HTTP 响应与重定向、最终 DOM 和可访问性树。
2. 核对实际加载的 HTML、JS、CSS 与 platform template ZIP 的版本或内容摘要。
3. 单独确认 REQ-6.1.1 的保存请求、`book.page_ids`、重定向书籍页和新页面名称/标题。
4. 单独确认 REQ-6.1.2 保存草稿后的首页导航及 BookStack button 的可见性和 accessible name。
5. 单独确认 REQ-9.1 的 Recently Updated 链接目标、返回页面模板和 BookStack button。

## 是否交给阶段5及修改边界

建议有条件交给阶段5。先补齐运行时证据，再做窄范围修复：

- P0：补齐最终 URL、DOM/可访问性树、网络响应和实际构建产物证据。
- P1：若确认共享页面/资源边界问题，只改相关模板、server-side render/readback、路由/重定向 glue 或构建打包链路。
- P1：若确认 REQ-6.1.1 是标题/名称呈现语义问题，优先修复可观察输出，不先扩大 timeout。
- P2：修复后只对三个失败节点本地回归，再决定是否做一次平台验证。

暂不建议全局增加 timeout、提高推理级别、重写 BookStack 业务、修改官方 tests，或混入其他 Run 证据。

## 对完成率/Token/耗时影响预估

- 当前完成率：`31/34 = 91.2%`。
- 若三个失败全部修复：`34/34 = 100.0%`，绝对提升 `8.8` 个百分点。
- 当前成本基线：平台 token `37,625,229`、provider total `37,625,127`、`1,275` 次请求、`18.351171 CNY`。
- 当前总耗时 `9,817s`，约 `2.73h`；最终 Playwright suite `48.8s`，三个失败等待合计约 `30s`。
- 因此阶段5应先采用低成本、窄范围的本地运行时证据定位，避免直接重复完整平台 Run；修复共享模板/资源边界有望同时提高三项完成率，但实际 token 和时间收益必须以定位后的回归结果为准。

<!-- PHASE4_RESULT: complete -->
