# 阶段 4 只读诊断：arc-bench-lite--bookstack / Run d4acec5dbbdf

PHASE4_RESULT: complete

- handoff_id：`d4acec5dbbdf-686648028D9A`
- run_id：`d4acec5dbbdf`
- submission_id：`535d25f72007`
- task_key：`arc-bench-lite--bookstack`
- Thread：`01a0b582-3586-7bc1-875e-d4670592d5ba`
- manifest SHA-256：`686648028D9A709FE16FAE29AAE4B4B188DCFF30230AAECB876A45DA7F9FAA05`

## 范围与身份

本结果只分析 Run `d4acec5dbbdf`，不继承 `ff12a7ff45f8` 或其他 BookStack Run 的业务根因结论。同一 `submission_id` 不代表相同 build；本 Run 没有平台提供的 ZIP-to-build 绑定。

本阶段全程只读：未创建新会话、未创建新 Run、未重跑、未上传、未修改 Agent 代码、官方测试、需求或运行配置。

## 1. 已确认事实

- 平台状态：`FAILED`，score `0.0`，`0/0`。
- 总耗时：`1096s`。
- 环境预检完成；随后生成/启动步骤因模板不完整失败。
- 平台明确报告：`web template is incomplete: expected frontend/ and backend/ directories`。
- `run_tests` 状态为 `pending / not reached`，`tests[]` 为空，失败详情中没有失败测试。
- 模板 ZIP 共 25 个条目；`frontend/`、`backend/`、`main.py`、`tests/` 条目数均为 0，现有内容主要是 `template/requirements/` 和元数据。
- 原始 logs JSON 有效但只有 `events=[]`、`stdout=[]`、`pages=0`，不能独立证明 `main.py`、`/workspace/tests`、bundled fallback 或 API Key 检查结果。
- `run.json` 的 `node_states` 虽全部为 `test-failed`，但不能解释为业务测试已执行失败；权威链路显示业务测试未到达。

## 2. 最终失败链路

```text
生成 Agent 结束
  -> 模板完整性检查
  -> 缺少 frontend/ 与 backend/
  -> start_agent 失败
  -> run_tests 未执行
  -> 0/0、score 0、FAILED
```

这是生成/打包前置阻断，不是 BookStack 业务功能完成率测量。

## 3. 根因候选及证据等级

| 候选 | 证据等级 | 判断 |
| --- | --- | --- |
| 产物缺少所需的 `frontend/`、`backend/`，且没有 `main.py`、`tests/` | 已确认（高） | `run.json` 明确报错，ZIP 清单独立印证 |
| 生成到模板的复制、打包或上传组装阶段丢失应用目录 | 合理候选（中） | Agent 被记录为生成结束，但 ZIP 只保留 requirements；缺少生成 stdout/stderr，无法定位具体环节 |
| BookStack 业务实现、登录、Playwright selector、服务端行为或视觉模型导致失败 | 未建立 | 应用服务未启动，业务测试未执行，没有浏览器页面或测试错误上下文 |

## 4. 已排除或不能归因的原因

- 不能归因于某个业务需求失败，例如登录、页面导航或草稿删除；没有任何业务测试执行。
- 不能归因于官方测试或 helper 回归；测试调用尚未发生。
- 不能把 summary 中“main.py 执行”“使用 `/workspace/tests`”“bundled=0”“无明文 API Key”等说法当作已验证事实；原始 logs 为空，只能保留为未验证声明。
- 不能把 `node_states=test-failed` 当作测试失败清单。
- 当前证据不足以判断模型质量、Token 消耗、API Key、平台业务测试故障或运行时服务故障。

## 5. 证据缺口

- 非空的生成 stdout/stderr、工作区清单和生成到上传的 staging manifest。
- 平台提供的 `agent_build_id`、代码 SHA 及 ZIP-to-build 绑定。
- 生成后的 `frontend/`、`backend/`、`main.py`、`tests/` 源文件树。
- task snapshot ID 和完整运行配置。
- Playwright report、trace、HAR、浏览器 pages 及响应/错误 body。
- 能验证入口、测试目录、bundled fallback 和密钥扫描的原始日志。

## 6. 最小只读复现实验

1. 对提交 ZIP 做归档清单检查，验证 `frontend/`、`backend/`、`main.py`、`tests/` 是否位于平台要求的路径。
2. 若仍能访问生成工作区，只读比较 workspace 清单、staging manifest 与最终 ZIP 清单，区分“生成时缺失”和“打包/上传时丢失”。
3. 对已知合格包与本 ZIP 执行相同的 archive-shape gate；本 ZIP 应在启动服务和浏览器测试前被拒绝。

这些实验不修改代码、不修改 ZIP、不创建 Run。

## 7. 阶段 5 建议

阶段5可以接收本结果，但只能按“生成/打包阻断”处理，不能将其作为业务代码缺陷或业务测试质量结论。

优先级：

1. P0：加入上传前 archive-shape gate，强制要求 `frontend/`、`backend/`、`main.py`、`tests/` 位于准确路径。
2. P0：保留生成工作区，并输出非空的生成/打包 manifest、stdout 和 stderr。
3. P0：本地校验 ZIP 内容及哈希；shape gate 通过后再做最小本地启动 smoke check。
4. P1：只有产物包含完整应用树且记录了 build-to-upload 绑定后，才重新执行官方任务。

本 Run 不建议进行业务功能重写、selector 调整、超时扩大或全量平台重跑。不得把本 Run 与 `ff12a7ff45f8` 或其他 BookStack Run 的结论合并。

## 8. 指标影响

- `0/0` 是生成阶段失败，不是业务功能完成率。
- Token、费用和 LLM 请求数：权威 run 对象与原始日志均不可用。
- 业务测试耗时：不适用；`1096s` 仅是 Run 总耗时。
- 在包结构可运行之前，提升 Token、运行时间或业务完成率没有评估意义；当前最高优先级是产物完整性和可追溯性。

## 证据文件

- [manifest.json](manifest.json)
- [phase4-handoff.json](phase4-handoff.json)
- [phase4-ack.json](phase4-ack.json)
- [phase4-result.json](phase4-result.json)

外部原始证据位于 manifest 中列出的 Downloads 路径，哈希均已复核通过。
