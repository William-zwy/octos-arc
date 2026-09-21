# 阶段 4 只读诊断：arc-bench-lite--bookstack / Run cca008377368

PHASE4_RESULT: complete

- handoff_id：`cca008377368-A8540D0184BB`
- run_id：`cca008377368`
- submission_id：`0b90e43b07b7`
- task_key：`arc-bench-lite--bookstack`
- Thread：`01a0b582-3586-7bc1-875e-d4670592d5ba`
- manifest SHA-256：`A8540D0184BBCB16249C7D09BA41DA0318705159DF9F2AF00F903C9217ACABA5`

## 范围与身份

本结果只分析 Run `cca008377368`。该 Run 使用新的 `submission_id=0b90e43b07b7`，不继承 `d4acec5dbbdf`、`ff12a7ff45f8` 或其他 BookStack Run 的业务结论。平台没有 ZIP-to-build 绑定。

全程只读：未创建新会话、未创建新 Run、未重跑、未上传、未修改 Agent 代码、官方测试、需求或运行配置。

## 1. 已确认事实

- 平台状态：`FAILED`，score `0`，`0/0`。
- `main.py` 实际执行命令为：

  ```text
  python3 /workspace/submission/main.py /tmp/arcbench/requirements-source --output-dir /workspace/template
  ```

- 生成探测记录脱敏 HTTP `401`：`permanent authentication failure; aborting before generation`。
- `main.py` 退出码为 `2`，生成阶段在产出应用树之前终止。
- meter baseline 也记录了脱敏 HTTP `401 Unauthorized`；不记录或传播任何密钥值。
- 模板 ZIP 共 23 个条目，内容均位于 `template/requirements/`；`frontend/`、`backend/`、`main.py`、`tests/` 条目数均为 0。
- `run_tests` 为 `pending/not reached`，`tests[]` 为空，应用服务器未启动，Playwright 未执行，失败详情没有执行失败测试。
- 原始日志确认：使用了 `main.py`，runner spec 的测试目录为 `/workspace/tests`，bundled fallback 命中 0 次；无 `sk-` 明文，仅有 `OPENAI_API_KEY=set(len=9)` 掩码。
- 没有 acceptance、provider totals、Token 或费用记录。

## 2. 最终失败链路

```text
环境预检通过
  -> 安装依赖并启动 main.py
  -> 生成探测收到 HTTP 401
  -> main.py 退出码 2
  -> 未生成 frontend/backend 应用树
  -> run_tests 未执行
  -> 0/0、score 0、FAILED
```

这是“生成认证前置阻断”，不是 BookStack 业务失败，也不是业务完成率测量。

## 3. 根因候选及证据等级

| 候选 | 证据等级 | 判断 |
| --- | --- | --- |
| 生成路径被 HTTP 401 认证失败阻断 | confirmed | 原始 generation-agent stdout/stderr 明确记录，且 `main.py` 退出码为 2 |
| 生成 API 凭证、端点认证链路或账号授权被拒绝 | strong_candidate | generation probe 与 meter baseline 均返回 401；但没有凭证值、响应 body 或授权映射 |
| ZIP 不完整是独立的初始根因 | unknown | ZIP 缺少应用树已确认，但日志显示认证失败先发生，缺失应用树更可能是生成中止后的结果 |
| BookStack 业务实现、Playwright selector、服务端行为或视觉模型导致失败 | unknown | 服务未启动，业务测试未执行 |

## 4. 已排除或不能归因的原因

- 不能归因于某个 BookStack 需求失败；没有业务测试执行。
- 不能归因于官方 Playwright 测试/helper 回归；测试调用尚未发生。
- 不能把 `0/0` 当作业务完成率。
- 不能把模板不完整当作先于认证失败的独立根因；它是生成失败后的产物状态，具体因果仍需验证。
- 不能归因于 API Key 泄露；日志没有 `sk-` 明文，只有掩码存在标记。
- 不能根据本 Run 评估 Token、费用、模型质量或业务运行时稳定性。

## 5. 证据缺口

- HTTP 401 的响应 body、授权策略和账号状态；这些信息不能通过猜测或传播密钥补齐。
- 生成 workspace 清单、staging manifest 及安全的生成器诊断。
- 平台提供的 `agent_build_id`、代码 SHA 和 ZIP-to-build 绑定。
- task snapshot ID、推理级别、时间预算、并发配置。
- provider 请求/Token/费用统计。
- snapshots、Playwright report、trace、HAR、浏览器页面和应用响应 body。
- 生成后的 frontend/backend 源代码树。

## 6. 最小只读复现实验

1. 使用平台批准的脱敏健康/认证诊断验证生成端点和账号授权，只记录状态码及脱敏元数据，不记录密钥值。
2. 在已知有效且独立授权的环境中，仅执行同一 `main.py` 生成命令，观察认证成功后是否能产出应用树；不修改官方测试和需求。
3. 生成成功后先检查 `frontend/`、`backend/`、`main.py`、`tests/` 的文件树和 ZIP 清单，再启动服务或浏览器测试。

当前 Run 的可复现边界是：认证失败先发生，应用树和业务测试均未到达。

## 7. 阶段 5 建议

阶段5可以接收本结果，但应按“生成认证前置阻断”处理，不应将其作为业务代码缺陷或完成率结论。

优先级：

1. P0：通过批准的脱敏诊断验证生成 API 的认证路径和端点配置；禁止记录或共享密钥值。
2. P0：让生成失败快速返回清晰的脱敏认证错误，并保留退出码、stderr 和生成 manifest。
3. P0：加入上传前 archive-shape gate，要求 `frontend/`、`backend/`、`main.py`、`tests/` 位于准确路径。
4. P1：认证和结构检查通过后，先做一次生成-only/本地 smoke 验证，再消耗官方 Run。
5. P1：只有生成出可运行包后，才评估 BookStack 业务行为及 Token、耗时、完成率优化。

本 Run 不建议进行业务功能重写、selector 调整、超时扩大或全量平台重跑。不得把本 Run 与 `d4acec5dbbdf` 或其他 BookStack Run 的结论合并。

## 8. 指标影响

- `0/0` 是生成前置失败，不是业务功能完成率。
- Token、费用和请求数：不可用。
- 平台 run 对象耗时为 `0s`；按时间戳推导的 wall-clock 约为 `7.33s`，两者口径不同。
- 在认证和应用产物可用之前，Token、运行时间和业务完成率优化没有评估意义。

## 证据文件

- [manifest.json](manifest.json)
- [phase4-handoff.json](phase4-handoff.json)
- [phase4-ack.json](phase4-ack.json)
- [phase4-result.json](phase4-result.json)

外部原始证据位于 manifest 列出的 Downloads 路径，哈希均已复核通过。
