# 本机 keep 试跑 2（arc-bench-web--keep，32 节点 / 32 测试）

- 二进制：`target/release/octos` = octos 2.0.3-rc.11 (82e3bef3)，SHA-256 360dd4216d933369bb7c2a39cca1438d6bd076571c6324cd571a961b17d12f30
- 适配包：main 82e3bef3 的 `arc/`（未含工作流 A 的改动），`OCTOS_NODE_TIMEOUT=3600 OCTOS_TIME_BUDGET=14400 OCTOS_MAX_ITERATIONS=80`
- 时间：18:08:47 → 19:31:42 UTC，共 83 分钟；官方评分脚本 `grade-local.py`：**26/32（81%）**
- 骨架轮：模型读完全部 32 个 spec 后在一轮内把整个应用写完并自行用 Playwright 跑验收（自测到 25/32），到 3600 s 超时；适配包把超时当瞬时错误、开新会话重试，重试会话只做验证 14 分钟即结束（日志记为 attempt 1 ok in 4120s）
- 32 个节点轮：每轮 19–38 s、tokens_in 4–6k、tokens_out 1–3k，全部「无需改动」
- 终检 99 s；启动演练 1 s 通过
- 事件流合计（不含超时那一轮，内核未发 turn/completed）：turn/completed 35 次，tokens_in 330,030，tokens_out 116,829；reasoning 文本 152.9 万字符，工具调用 243 次
- 试跑 1（`../local-keep-1-timeout/`）：`OCTOS_NODE_TIMEOUT=900` 时骨架轮两次超时，每会话约 40 万字符 reasoning，只写出 2 个文件 —— 说明云端默认 1200 s 单轮上限下本题会在骨架轮死掉，因此本分支给 main.py 加了按节点数放大时限、骨架超时但目录已存在则继续的两处改动（2a7433ac）

## 6 条失败测试归因（回流给工作流 A）

| 测试 | 现象 | 归因 |
|---|---|---|
| REQ-2.3.3 Trash list | 删除后进入 Trash，`Delete me 2.3.3` 不可见 | 代码错：垃圾箱视图没有列出刚删除的笔记（或删除走了软删除以外的路径） |
| REQ-2.5.3 Show archived notes | 归档视图里 `Travel plans 2.5.3` 不可见 | 代码错：Archive 视图过滤条件不对 |
| REQ-2.5.4 Unarchive | hover 卡片按钮 `Travel plans 2.5.4` 60 s 超时 | 代码错（同上，卡片未出现在归档视图）；超时是等待元素导致 |
| REQ-2.7.1 Assign label | 加标签后按标签筛选，`Team retro add label` 不可见 | 代码错：标签筛选视图未包含新加标签的笔记 |
| REQ-2.7.2 Remove label | 移除标签后仍在标签视图出现 1 次 | 代码错：移除标签未生效或视图未刷新 |
| REQ-2.7.5 Edit labels | 60 s 超时，`keyboard.press` 时页面已关闭 | 代码错：编辑标签对话框的键盘交互流程不符合 spec |

共同点：模型自测时 4 个 worker 并行改同一个 JSON 存储，和评分时一致；6 条都集中在「视图过滤 / 标签」这一簇，属于同一块代码。
