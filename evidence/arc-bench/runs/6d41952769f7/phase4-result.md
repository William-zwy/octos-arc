# 阶段4诊断结果：arc-bench-lite--bookstack / Run 6d41952769f7

## 已确认事实

- 本文档只分析 Run `6d41952769f7`（P5-015），对应 submission `14111688f13e`；上一 Run 不并入本次结论。
- handoff、manifest 身份一致；manifest 声明的 7 个外部证据 SHA-256 均核对通过。
- 最终平台结果为 `FAILED`，score `88.2`，通过 `30/34`；最终权威失败节点为 `REQ-6.1.1`、`REQ-6.2.1`、`REQ-7.2`、`REQ-8.1`。
- REQ-6.1.1 和 REQ-6.2.1 等待 heading 分别超时；REQ-8.1 等待 `Unfavorite` heading 超时；REQ-7.2 在 `page.goto('/')` 收到 `net::ERR_ABORTED`。
- 本 Run 的最终套件中，REQ-6.1.2、REQ-6.1.3、REQ-8.2、REQ-9.1 均通过。因此不能把上一 Run 的 logo 定位失败迁移到本 Run。
- 入口为 `main.py`，官方测试目录为 `/workspace/tests`，bundled fallback 为 0，API key 只有掩码状态。
- 平台计量：`89,254,641` token、provider total `89,254,545`、`2,402` 次请求、`36.969671 CNY`、运行时长 `18,827s`；两种 token 口径不相加。
- canonical logs 启动阶段输出 `ARC_AGENT_IDENTITY`：build `arc-agent-v1-9d7c83b9ce8e3c381db3a3a9`、commit `adfe39832dd3d3098efd0a585cd2857f3ca7bc29`、managed files `494`、payload tree SHA `09723C6BAF032F94A50DDA670523899A3BBC06908EB8FD8A59B53B49183C3DAA`。这是运行时自报告身份，不是平台上传收据；upload-package SHA 和 task snapshot 仍缺失。
- internal full-suite 的 `0/34` 已确认是 harness 配置错误：P5-015 生成的 Playwright `trace.snapshots` 为对象，而 Playwright 1.63.0 要求 boolean；repair 输出要求改成 `snapshots:false`，但预算耗尽且未实施应用修复。因此 `0/34` 不是应用 34 项全部失败的证据。
- REQ-6.1.2 和 REQ-9.1 在最终平台套件中通过，但没有证据证明这两个历史失败的通过由 P5-015 最终 repair 导致。
- 静态模板显示：创建页面/章节后前端跳到 `/books/:id`，书籍详情页把页面/章节作为链接列表渲染；收藏状态由 button 文本和 `aria-pressed` 表示。

## 最终失败链路

1. `REQ-6.1.1 / Save Page`：最终导航到 `/books/11` 后等待 `Page Created 6.1.1` heading，`10,013ms` 后元素不存在。
2. `REQ-6.2.1 / Create Chapter`：最终导航到 `/books/11` 后等待 `Chapter Created 6.2.1` heading，`10,011ms` 后元素不存在。
3. `REQ-7.2 / Quick Navigation from Recently Viewed`：在业务断言前，`openShelfDetails -> openShelves -> openHome -> page.goto('/')` 于 `http://127.0.0.1:3000/` 失败，耗时 `1,322ms`。
4. `REQ-8.1 / Favorite Items`：等待 `Unfavorite` heading，`10,015ms` 后元素不存在。

前三项中的前两项和第四项是可观察 UI 语义问题的强候选；REQ-7.2 是独立的导航/连接生命周期问题，不能强行合并。

## 根因候选及证据等级

### 强候选：页面/章节创建后的反馈语义不符合测试契约

`template/backend/server.js` 的 `createPage` 和 `createChapter` 接口返回 JSON，`template/frontend/src/app.js` 成功后导航到 `/books/:id`。静态 `bookDetailsHtml` 只将书名输出为 `h1`，章节名和页面名分别放在列表链接中，没有 `Page Created ...` 或 `Chapter Created ...` heading。

这与两个最终失败都在 `/books/11` 上等待 heading 的证据一致。仍需最终 DOM 和响应链确认，因而记录为强候选而不是运行时已证实根因。

### 强候选：Favorite/Unfavorite 的角色不匹配

静态 `favoriteButtonHtml` 输出的是 `<button>`，favorited 状态的文本为 `Unfavorite`；`app.js` 只修改该 button 的文本和 `aria-pressed`。而最终失败 locator 是 `getByRole('heading', { name: /^Unfavorite$/i }).first()`。这是一个高度具体的静态语义不一致，但最终 DOM 和收藏 API 响应尚未交付，因此仍保留证据等级边界。

### 已确认：internal full-suite 的 harness 配置错误

canonical logs 明确记录 P5-015 生成的 Playwright trace 配置把 `trace.snapshots` 写成对象，而 Playwright 1.63.0 要求 boolean。full-suite repair 明确建议改为 `snapshots:false`，同时记录 request budget exhausted、未实施 application fix；随后 round 1 仍为 `0/34`。

因此 C4 的正确结论是：internal `0/34` 属于 harness/configuration failure，不能解释为应用 34 项全部失败，也不能覆盖最终平台独立执行的 `30/34`。

### 候选/未知：REQ-7.2 的导航连接中止

失败发生在 `page.goto('/')`，早于 Recently Viewed 业务断言。后续 REQ-8.2 和 REQ-9.1 仍通过，说明不能简单判定 server 已永久崩溃。可能范围包括测试顺序状态、socket/响应关闭、服务进程生命周期或瞬时资源问题；当前没有 network trace、server stderr 或 page lifecycle 记录。

### 补充边界：isolated acceptance 与最终平台执行

manifest 记录部分节点的 isolated acceptance 通过，但这不能用于证明 P5-015 最终 repair 修复了 REQ-6.1.2/REQ-9.1，也不能解释 internal `0/34`；后者已有明确的 trace 配置根因。isolated 与最终平台之间的文件快照、数据库和生命周期差异仍是证据缺口。

## 已排除原因

- 不是未执行官方测试：日志明确使用 `/workspace/tests`，最终命令为 `npx playwright test --workers=1`。
- 不是 bundled tests 回退：命中为 0。
- 不是入口未执行：日志含 `main.py` 执行记录。
- 不是上一 Run 的 logo 失败直接迁移：本 Run 的 REQ-6.1.2 和 REQ-9.1 最终通过。
- 不能把人工 summary 的 `24/34` 当作最终结果；最终平台权威结果是 `30/34`。
- internal full-suite 的 `0/34` 已由 canonical logs 定位为 `trace.snapshots` 类型错误，不再作为应用 34 项全部失败或应用回归的证据。
- 不能把 REQ-6.1.2/REQ-9.1 的最终通过归因于 P5-015 最终 repair；当前证据只证明最终状态，不证明修复因果。
- 不能据 `ERR_ABORTED` 单独断言服务器已崩溃，因为后续仍有测试通过。
- 不能把 platform template ZIP 当作上传 Agent release；平台没有提供对应 build、code、payload 或 upload-package SHA。

## 证据缺口

- 三个 heading/button 失败点的最终 DOM、可访问性树和截图。
- Page/Chapter 创建请求的 status、JSON body、Location、重定向链和最终 `/books/11` HTML。
- Favorite toggle 的响应、console、最终 button/heading 可访问性树。
- REQ-7.2 失败时的 network、HTTP、socket、page lifecycle 和 server stderr。
- isolated acceptance 与最终平台执行之间的精确文件快照、数据库重置和启动边界；该缺口只用于解释执行差异，不再用于解释 internal `0/34`。
- P5-015 internal full-suite trace 配置在修复后的最终文件内容和 trace 运行记录。
- 四个节点的 `error-context.md` 本体、完整官方 helper 源码，以及与 original_filename 对应的 Agent release ZIP。

## 最小只读复现建议

本阶段未创建新 Run、未重跑官方测试、未修改代码。建议阶段5在 disposable 本地副本中：

1. 分别记录 Save Page、Create Chapter 的 POST 响应和 `/books/:id` 最终 DOM，确认新对象到底以 heading、link 还是缺失呈现。
2. 记录 Favorite toggle 响应及切换后的可访问性树，比较 button role、文本和 `aria-pressed` 与官方 locator。
3. 对 REQ-7.2 只记录进入流程前后的 URL、未完成请求、GET `/` 状态、socket/server 事件，区分连接中止和业务路由问题。
4. 对比 isolated 与 final 的启动目录、数据库、生成文件 SHA 和测试顺序；同时只读核对 `trace.snapshots` 类型，但不把 internal `0/34` 当应用失败重跑。

## 是否交给阶段5

建议有条件交给阶段5：

- P0：把 internal full-suite `0/34` 标记为已确认的 harness 配置错误，不将其作为应用失败数；以最终平台 `30/34` 和官方 locator 为应用修复契约。
- P0：补齐四个最终平台失败节点的运行时 DOM、网络和构建证据。
- P0：记录 runtime-self-reported `ARC_AGENT_IDENTITY`，但不要把它当作 upload-package SHA 或严格上传收据。
- P1：窄范围调整页面/章节创建后的可观察反馈，使官方 locator 能得到符合契约的 heading/text，同时保留现有详情链接和路由。
- P1：调整收藏状态的可访问语义与交互一致性，不先重写 favorites 数据路径。
- P1：独立排查 REQ-7.2 的首页 GET 连接生命周期和顺序状态，不先增加 timeout。
- P2：本地回归四个失败节点和相邻通过节点；REQ-6.1.2/REQ-9.1 的通过不作为 P5-015 最终 repair 的因果证明，再决定是否申请一次平台验证。

暂不建议修改官方 tests、全局增加 timeout、重写数据库模型或混入上一 Run 结论。

## 对完成率/Token/耗时影响预估

- 当前完成率：`30/34 = 88.2%`。
- 若四个失败全部修复：`34/34 = 100.0%`，绝对提升 `11.8` 个百分点。
- 若只修复前三个可观察语义问题：约 `33/34 = 97.1%`，REQ-7.2 仍需单独处理。
- 当前成本基线：平台 token `89,254,641`、provider total `89,254,545`、`2,402` 次请求、`36.969671 CNY`。
- 总运行时长 `18,827s`，约 `5.23h`；最终 Playwright 套件 `51.3s`，三个 locator 超时约占 `30s`，导航错误耗时 `1.322s`。
- 应先用低成本本地运行时证据定位，避免直接重复完整平台 Run。

<!-- PHASE4_RESULT: complete -->
