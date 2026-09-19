# 阶段 4 只读诊断：arc-bench-lite--bookstack

## Run 范围

- Run：5669f7d1777c
- Submission：b88949d044c2
- 代码版本边界：首次修改版代码；不是冻结 A0，也不是 Stage5 输出
- 最终状态：FAILED
- 成绩：94.1%，32/34
- 本阶段仅分析本 Run；未创建新 Run、未重跑、未上传、未修改代码或官方测试。

## 1. 已确认事实

- 平台使用了入口 main.py 和测试目录 /workspace/tests。
- bundled tests 回退命中为 0，日志没有明文 API Key。
- 前端构建、后端启动和 http://127.0.0.1:3000 可达性均通过。
- 最终 Playwright 使用 1 worker，34 个测试耗时约 39.9s，失败恰好是两个保存后结果断言。
- REQ-5.6.1 在 helpers.ts:137 等待 Book Created 5.6.1，10 秒内找不到元素。
- REQ-6.1.1 在 helpers.ts:137 等待 Page Created 6.1.1，10 秒内找不到元素；日志显示最后已导航到 /books/8。
- Agent 内部验收与平台最终结果不一致：
  - REQ-5.6.1：round 0、round 1、round 2 均为 0/1；
  - REQ-6.1.1：round 0 为 1/1；
  - 内部 full suite：round 0 为 33/34，失败 REQ-2.2；round 1 为 34/34；
  - 随后平台重新构建并执行最终 Playwright，得到 32/34。
- 最终模板静态代码中存在两条目标流程的名义实现：
  - Shelf 上下文新建 Book 路由、表单、POST /api/books、shelfId 关联和 Shelf 书籍渲染；
  - 新建 Page 路由、表单、POST /api/pages 和 Book 页面列表服务端渲染。
- 最终模板的 db.json 含有 Shelf 5.6.1（id 10）、Book Created 5.6.1（shelfId 10）和 Page Created 6.1.1（bookId 8）。
- Page 的 updatedAt=1789832818343，对应 2026-09-19 15:46:58Z，落在平台最终测试窗口内。
- 因此，至少 REQ-6.1.1 的页面数据曾在相关执行窗口被写入持久化文件，但现有证据无法证明后续 /books/8 响应的 DOM 暴露了该文本。

## 2. 最终失败链路

### REQ-5.6.1

官方流程是：打开 Shelf 5.6.1，点击 New Book，填写 Book 名称、描述和标签，点击 Save Book，在返回的 Shelf 页面检查 Book Created 5.6.1 和 Shelf 名称。

最终失败发生在最后一步。Playwright 只确认目标 locator 在 10 秒内没有出现；没有最终 HTML、响应体或服务端请求日志，无法断定是 POST 未成功、重定向错误、Shelf 关联读取失败，还是 DOM 未更新。

### REQ-6.1.1

官方流程是：打开 Book 6.1.1，打开新建 Page 页面，填写 Page 标题和内容，点击 Save Page，返回 /books/8 后检查 Page Created 6.1.1。

最终失败发生在最后一步。日志显示已导航到 /books/8，而最终数据库中存在对应 Page 记录；因此“保存请求已产生数据但最终页面未被 locator 看到”是强候选链路，但缺少最终 DOM 证据，不能升级为已确认根因。

## 3. 根因候选及证据等级

| 候选 | 等级 | 判断 |
|---|---|---|
| 最终平台保存后的 Shelf/Book 页面没有向官方 locator 暴露新记录 | 强候选 | 两个失败都在保存后的 expectTextsVisible；静态路由存在，但无最终 DOM |
| Agent 内部验收与平台最终评测使用了不等价的数据库/构建状态 | 强候选 | 内部 full suite 34/34 后，平台又重新 build；最终包含有大量运行后状态，未见干净 DB 边界 |
| 最终 package 与内部验收使用的 frontend/dist 或源文件不完全一致 | 未确认至强候选 | 平台确实在 Agent 退出后重新 build，但没有前后文件 hash |
| 只是 Playwright 10 秒太短 | 不太可能 | 报告是 element(s) not found；没有元素随后出现的证据 |
| 缺少目标路由、表单或 API | 已排除 | 最终模板静态检查均可找到对应实现 |

## 4. 已排除原因

- 不是入口 main.py 错误。
- 不是使用了错误的测试目录。
- 不是 bundled tests 回退。
- 不是 API Key 泄露。
- 不是整个应用不可用；其余 32 个测试通过。
- 不是 OOM 或平台总预算耗尽。
- 不是目标功能的名义路由、表单和 API 完全缺失。

## 5. 证据缺口

- 缺少两个失败用例的 Playwright trace、截图、DOM snapshot 和 HAR。
- 缺少 POST 响应状态、Location、GET /shelves/10 和 GET /books/8 的实际响应体。
- 缺少平台最终测试开始前的 db.json hash，无法确定 Book Created 5.6.1 来自内部验收还是最终测试。
- 缺少内部验收结束到平台最终 build 前的源文件、frontend/dist 和数据库 hash。
- 平台未提供 task_snapshot_id、agent_build_id 和 code_sha。

## 6. 最小只读复现实验建议

1. 用最终模板的干净副本只运行 REQ-5.6.1，记录 POST /api/books、重定向目标、GET /shelves/10 HTML 和最终 locator。
2. 用最终模板的干净副本只运行 REQ-6.1.1，记录 POST /api/pages、重定向目标、GET /books/8 HTML 和最终 locator。
3. 分别比较干净 DB 后直接运行目标测试，以及先运行内部 full suite、保留 DB 后再运行目标测试。
4. 下一次提交前，记录 frontend/src、frontend/dist 和 backend/data/db.json 的 hash，完成目标测试后再恢复或重新生成干净 seed。

## 7. 是否交给阶段 5

是，但阶段 5 的第一步应是验证状态/打包边界，而不是直接重写业务代码。

建议优先级：

1. P0：确保 Agent 验收与最终平台测试使用隔离的、可重建的干净 db.json。
2. P0：为两个目标流程增加本地 post-save 检查：POST 成功、重定向正确、返回 HTML/DOM 包含目标文本。
3. P0：若干净副本仍复现，再针对 Shelf 书籍列表和 Book 页面列表做最小服务端渲染修复。
4. P1：记录源文件、构建产物和数据库 hash，消除内部验收与平台最终评测之间的不可见差异。

允许的修改边界应限制在：

- backend/server.js
- backend/db.js
- backend/data/db.json 或确定性的打包重置逻辑
- frontend/src/app.js
- frontend/src/book-create-shelf.html
- frontend/src/page-create.html
- frontend/src/shelf-details.html
- frontend/src/book-details.html

不要修改官方测试和 helpers，不要先做全局 timeout 增大或大范围前端重写。

## 8. 对完成率、Token 和耗时的影响预估

- 完成率：32/34 = 94.1%；两个问题都闭环后目标为 34/34 = 100%，理论提升约 5.9 个百分点。
- Token：本 Run 已消耗平台 Token 32,806,461、1,275 次请求、费用 17.124841 CNY。不建议在根因未确定前再次走完整生成流程；先做两个目标用例的本地隔离复现。
- 耗时：最终 Playwright 约 39.9s，两个 10 秒超时约占 20s；但整个 Run 为 12,739s，主要成本来自 Agent 生成和修复轮，因此仅修复测试执行时间不会显著降低总成本。
- 风险：当前有 32 个测试通过。未经干净状态复现就改动通用渲染逻辑，可能引入回归。

## 证据文件

- [manifest.json](<D:/DataMove/codex/worktrees/9015/AI智能体软件工厂黑客松/evidence/arc-bench/runs/5669f7d1777c/manifest.json>)
- [phase4-ack.json](<D:/DataMove/codex/worktrees/9015/AI智能体软件工厂黑客松/evidence/arc-bench/runs/5669f7d1777c/phase4-ack.json>)
- [phase4-result.json](<D:/DataMove/codex/worktrees/9015/AI智能体软件工厂黑客松/evidence/arc-bench/runs/5669f7d1777c/phase4-result.json>)
- [failure-details.md](<C:/Users/dayuruozhi/Downloads/闻悦源代码-首轮测试-BookStack-lite/arcbench-5669f7d1777c-failure-details.md>)
- [run JSON](<C:/Users/dayuruozhi/Downloads/闻悦源代码-首轮测试-BookStack-lite/arcbench-run-5669f7d1777c.json>)
- [raw logs](<C:/Users/dayuruozhi/Downloads/闻悦源代码-首轮测试-BookStack-lite/arcbench-run-5669f7d1777c-logs.json>)
