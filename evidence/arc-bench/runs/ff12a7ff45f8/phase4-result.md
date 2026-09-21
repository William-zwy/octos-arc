# 阶段 4 只读诊断报告：arc-bench-lite--keep / `ff12a7ff45f8`

PHASE4_RESULT: complete

## 结论

本报告仅分析 Run `ff12a7ff45f8`，不引用此前其他 Keep Run 的工作假设作为当前事实。

该 Run 不是业务功能失败，而是“生成阶段阻断 + 平台模板前置拒绝”：

```text
模型请求持续 HTTP 401
→ 4 次 skeleton 尝试均未写入/验证产物
→ generation agent 中止
→ 没有 frontend/ 和 backend/
→ runner 在测试启动前拒绝模板
→ FAILED，score 0，0/0
```

当前 Run 没有生成可运行的 Web 应用，因此不能诊断 Keep 的业务实现，也不能把平台的 `0/0` 解读为业务完成率。认证失败是已确认的运行观察，但其底层责任边界（密钥有效性、账号权限、provider 路由、平台凭据绑定或临时平台状态）仍需隔离复现。

## 身份核验

| 字段 | 值 |
|---|---|
| handoff_id | `ff12a7ff45f8-D42FCA49784D` |
| run_id | `ff12a7ff45f8` |
| submission_id | `535d25f72007` |
| task | `arc-bench-lite--keep` |
| thread_id | `01a0b57a-7a65-77d0-a08a-e202167e4f70` |
| manifest SHA-256 | `D42FCA49784DCFF82C502474AA17A676C8C7028E048AD4196645ABC6B2942F6E`，与 handoff 一致 |
| ACK | 已写入并包含当前 handoff_id |

## 1. 已确认事实

- 平台最终状态为 `FAILED`，score `0`，通过/总数为 `0/0`。
- 平台 failure reason：`web template is incomplete: expected frontend/ and backend/ directories`。
- `main.py` 已执行；runner spec 使用 `/workspace/tests`；bundled fallback 命中为 `0`。
- 环境预检和 Agent 依赖安装成功，生成 Agent 已被启动。
- 生成代理的模型探测连续收到 HTTP `401 Unauthorized`；后续 driver 错误记录为脱敏的 `invalid_api_key`。
- 4 次 skeleton 尝试均为 `tools=0`、`wrote=False`、`verified=False`。
- 生成阶段最终中止：`no frontend/ and backend/ after 4 attempts`。
- postflight 明确警告工作区中不存在 `frontend/` 和 `backend/`；runner 随后拒绝模板。
- 应用服务没有启动，Playwright 没有执行。
- 最终模板 ZIP 共 25 个条目，只有 requirements 和 reference 图片等输入资产，`frontend/` 条目数为 0，`backend/` 条目数为 0。
- meter baseline 登录也出现脱敏的 401，因此本 Run 没有 token、provider totals、请求数或费用数据。
- 当前证据目录没有 `ff12a7ff45f8` 对应的 snapshots 文件。

日志中的 `OPENAI_API_KEY=set(len=9)` 和 manifest 的 plaintext hit `0` 只说明密钥值被掩码；不能把 401 直接扩展成密钥泄露结论。

## 2. 最终失败链路

### 生成阶段

1. runner 完成环境预检、依赖安装，并调用：

   ```text
   python3 /workspace/submission/main.py /tmp/arcbench/requirements-source --output-dir /workspace/template
   ```

2. 约 10 分钟内，模型探测尝试 21 次，均返回 HTTP 401。
3. 在探测仍失败的情况下，流程继续进入生成/验收路径。
4. skeleton attempt 1 至 4 均遇到认证错误，且没有工具调用、文件写入或验证成功。
5. Agent 抛出 skeleton scaffolding failed，中止生成。

### 平台阶段

1. postflight 检查工作区，发现没有 `frontend/` 和 `backend/`。
2. 生成代理进程退出码为 0，但产物完整性检查失败。
3. runner 报告模板不完整并结束执行。
4. 应用服务和 Playwright 均未启动，平台最终记录 `FAILED / 0 / 0`。

这里的 runner 模板拒绝是生成失败的下游结果，不是独立的业务测试失败。

## 3. 根因候选及证据等级

### RC-GEN-1：模型认证请求失败

- 证据等级：`confirmed_observation_not_attribution`
- 置信度：高（针对“发生了认证失败”这一观察）
- 证据：21 次 probe 均 401；driver 记录 `invalid_api_key`；生成 Agent 未产生文件。

已确认的是认证失败确实阻断了生成；尚未确认的是具体责任来源。当前不能仅凭日志判断是 API Key 失效、账号权限、模型权限、provider 路由、平台凭据绑定还是临时认证状态。

### RC-GEN-2：认证失败后的生成流程没有产出可验证 skeleton

- 证据等级：`confirmed_behavior`
- 证据：4 次尝试均 `tools=0 / wrote=False / verified=False`，最终没有 `frontend/` 和 `backend/`。

这确认了 Agent 编排在本 Run 中的实际行为，但尚不能仅凭当前材料定位到提交代码中的具体函数，也不能判断是否应当增加本地 fallback skeleton。

### RC-PLAT-1：平台模板前置检查拒绝

- 证据等级：`confirmed`
- 证据：failure reason、postflight 警告、最终 ZIP 清单三者一致。

这是平台对缺失产物的确定性下游拒绝，不是 32 个业务测试中的某一个失败。

### RC-OPT-1：认证错误重试策略可能造成无效耗时

- 证据等级：`strong_candidate`
- 证据：探测阶段约 10 分钟、21 次失败；随后 4 次 skeleton 失败；总耗时 1095 秒。

这提示应在隔离复现后评估 401 的 fail-fast 与重试边界，但阶段 4 不直接修改 Agent。

## 4. 已排除原因

- 不是入口缺失：`main.py` 确实被执行。
- 不是测试目录回退：runner 使用 `/workspace/tests`，bundled fallback 为 0。
- 不是 Playwright 测试失败：应用服务和 Playwright 都没有启动。
- 不是已知的 Keep 页面业务缺陷：本 Run 没有生成任何业务页面。
- 不是已观察到的 API Key 明文泄露：日志只包含掩码状态，明文命中为 0。
- 不是主要的 OOM 失败：日志中的内存使用低于 2048 MiB 限制，`oom_kill=0`；可见失败链是 401 后无产物。
- 不是官方测试套件本身导致的失败：平台在测试前就拒绝了模板。

## 5. 证据缺口

仍缺少：

- 401 的确切责任边界：密钥、账号权限、模型授权、provider 路由或平台凭据绑定；
- provider token totals、请求数和费用；
- task snapshot、Agent build ID、代码 SHA、平台 ZIP-to-build 绑定；
- 当前 Run 的 snapshots、生成源代码、独立 Playwright 报告和 error-context；
- 提交代码中导致 skeleton 未写入的具体函数级定位。

这些缺口不影响“生成阶段阻断、平台未进入业务测试”的判断，但会阻碍对认证责任和 Agent 重试策略的最终归因。当前建议 `needs_repro=true`，范围仅限认证/生成链路，不是要求立即重跑平台任务。

## 6. 最小只读复现实验建议

### 实验一：分离模型认证与 meter 认证

在不输出密钥的前提下，使用相同模型、base URL 和执行配置做一次受控认证预检；模型 endpoint 与 meter login 分开记录状态码和错误类别。不要在本阶段创建平台 Run。

### 实验二：隔离验证 main.py 的 skeleton 产出能力

在本地隔离环境用确定性的 mock/fixture 模型响应运行现有入口，观察是否生成 `frontend/`、`backend/` 并完成验证。不得修改官方测试或当前平台提交。

### 实验三：测量 401 的重试边界

向隔离生成驱动注入确定性的 401，记录探测次数、重试次数、耗时和文件写入状态，再与成功响应对照。用结果决定是否需要 fail-fast，而不是直接从本 Run 修改重试策略。

## 7. 阶段 5 入口建议

建议将本 Run 交给阶段 5，但分类为：

```text
生成管线 / 认证门禁问题
```

阶段 5 的优先顺序应是：

1. 核验模型 endpoint、模型权限、账号和 meter 认证链路；
2. 检查现有 Agent 在成功模型响应下是否能写出 `frontend/` 和 `backend/`；
3. 在隔离实验后评估 401 的有界重试和快速失败；
4. 不基于本 Run 实施 Keep 业务功能修复，因为没有任何业务应用和测试结果；
5. 认证与 skeleton 产出确认后，才考虑新的平台 Run。

本阶段 4 没有直接向阶段 5 会话发送消息，也没有实施任何代码或测试修改。

## 8. 指标影响

- 完成率：`0/0`，不应与业务功能完成率比较。
- 得分：`0`，原因是测试前模板拒绝。
- Token、请求数、费用：均不可用。
- 总耗时：`1095s`；其中约 10 分钟用于重复认证探测，后续还有 4 次 skeleton 失败重试。具体优化收益需要隔离复现测量。

## 证据路径与边界

- [phase4-result.json](phase4-result.json)
- [phase4-ack.json](phase4-ack.json)
- Manifest：`evidence/arc-bench/runs/ff12a7ff45f8/manifest.json`
- 原始日志：`C:/Users/dayuruozhi/Downloads/闻悦源代码-首轮测试-keep-lite/arcbench-run-ff12a7ff45f8-logs.json`
- 模板包：`C:/Users/dayuruozhi/Downloads/闻悦源代码-首轮测试-keep-lite/ff12a7ff45f8-template.zip`

本次仅处理 `ff12a7ff45f8`，未读取或合并其他 Run 的业务结论；未创建新 Run、未重跑、未上传、未修改 Agent/官方测试/运行配置、未执行远程同步。
