# 阶段 4 结果：`smoke-evolution--dice`

> PHASE4_RESULT: complete
>
> Run：`c48754c25fcf`
> Submission：`ed11d633b8a6`
> Handoff：`c48754c25fcf-09E043AE8892`
> 分析范围：只读分析本 Run；未创建新 Run、未重跑、未上传、未修改 Agent/测试/需求/资产

## 1. 已确认事实

- 平台最终状态：`FAILED`，score `0`。
- `passed_count=0`、`failed_count=0`、测试总数 `0`。
- 这不是业务测试通过率为 0，而是生成阶段失败导致测试根本未开始。
- 失败阶段：`start_agent`。
- 平台调用命令：

  ```text
  python3 /workspace/submission/main.py /tmp/arcbench/requirements-source --output-dir /workspace/template
  ```

- 入口 `main.py` 已被正确调用。
- Runner 配置了 `/workspace/tests`，bundled tests fallback 为 0；但由于生成前失败，不能声称测试实际执行过。
- Docker、runner image、pip 和 Agent 依赖安装均完成。
- 日志显示 `OPENAI_API_KEY=set`，但没有泄露密钥值。
- Agent 身份日志为：
  - build：`arc-agent-v1-0851fff1cfb8feeb38544f8c`
  - commit：`bb70542d7d327b660fa672bfdbc193f3f51b40a5`
  - payload tree SHA-256：`B286699D96E3463AC6C8B8C426600BEF01DB7A9A0B43191AE99DFCB32A99C885`

## 2. 最终失败链路

1. 平台组装 workspace 并完成环境 preflight。
2. Agent 依赖安装成功。
3. 平台启动 `/workspace/submission/main.py`。
4. Agent 输出环境摘要并进入 API probe。
5. API probe 收到 HTTP 401。
6. Agent 将其判定为 `permanent authentication failure`，以退出码 2 结束。
7. 未进入需求加载、Evolution 编排、代码生成、验收或 Playwright。
8. 平台将 `start_agent` 标记为失败，`run_tests` 保持未到达。

因此，本 Run 的失败链路是：

```text
平台认证/授权拒绝
        ↓
Agent 原始 API probe HTTP 401
        ↓
main.py exit code 2
        ↓
start_agent FAILED
        ↓
测试未执行，结果为 0/0
```

## 3. 根因候选及证据等级

### 高置信度：平台注入凭证被 API 认证层拒绝

证据：

- 原始日志明确记录 API probe HTTP 401；
- 环境中只有 `OPENAI_API_KEY=set`，只能证明存在，不能证明有效；
- 同一 Run 的 meter baseline login 也记录 HTTP 401。

限制：无法获得密钥身份、有效期、权限范围或服务端具体拒绝原因，也不应获取或输出这些信息。

### 高置信度：Agent 的 direct probe 是本次阻断点

当前启动路径在需求加载和 Flow 执行前调用原始 API probe。该 probe 失败后直接退出，因此认证错误被放大为整个任务无法生成。

这解释了“为什么没有进入业务测试”，但不能单独证明“为什么平台凭证失效”。

### 低置信度：模型或 endpoint 配置不匹配

日志能确认模型和 API Base URL 存在，但没有请求体和服务端响应体。HTTP 401 更直接指向认证/授权问题，现有证据不足以把根因归因于模型名称或 URL 形状。

## 4. 已排除原因

- **业务代码失败**：没有完成应用生成，也没有运行应用测试。
- **Playwright 或官方测试失败**：`tests=[]`，`run_tests` 未到达，没有测试执行日志。
- **入口错误**：平台已经成功调用 `/workspace/submission/main.py`。
- **测试目录错误或 bundled fallback**：Runner 选择 `/workspace/tests`，manifest 记录 fallback 为 0；只是测试尚未真正执行。
- **依赖或 Docker 启动失败**：Docker、runner image、pip 和 Agent 依赖都已完成。
- **OOM、超时、端口或生成应用资源问题**：进程在启动后约 3.6 秒即因认证失败退出，尚未进入这些阶段。

## 5. 证据缺口

- API key 的实际值、身份、有效期、权限范围和服务端 401 具体原因不可见。
- Provider Token、平台 Token、费用和 LLM 耗时均为 `null`；不能把 `null` 当作 0。
- Run 对象没有 `task_snapshot_id`。
- 没有 Playwright 报告或业务失败详情，因为生成未到达测试。
- 平台截图只能 corroborate 命令和退出状态，不能提供业务测试证据。
- 平台原生 Run 对象没有提供 `agent_build_id/code_sha` 字段；构建身份来自日志中的 `ARC_AGENT_IDENTITY`。

## 6. 最小只读复现实验建议

不创建新 Run 的前提下：

1. 对照 manifest、run JSON 和 logs JSON 的 SHA-256，确认三者来自同一 Run。
2. 在平台后台查看同一 submission、同一时间点的认证审计信息，只查看脱敏后的凭证状态。
3. 核对 meter 登录和生成 API 是否使用同一授权上下文，不读取或打印密钥。
4. 静态确认上传 `main.py` 在需求加载前调用 raw probe，并将 HTTP 401 映射为退出码 2。
5. 在后续有效 Run 进入生成和 `/workspace/tests` 前，不推断业务完成率、隐藏测试能力或 Agent 代码正确性。

## 7. 是否交给阶段 5及修改边界

应交给阶段 5，但分类为**平台认证门禁问题**，不是业务 Agent 正确性优化问题。

阶段 5 当前不应修改代码。若平台认证审计确认是凭证失效，应在平台 submission/授权侧修复。只有在后续证据证明需要 Agent 侧改动时，才允许考虑：

- 改善认证失败的分类和脱敏诊断；
- 设置有上限的 preflight 行为；
- 将认证阻断与业务生成失败明确区分。

禁止基于本 Run 绕过 HTTP 401、静默使用未认证客户端、修改官方测试/需求/资产或改动业务生成逻辑。

正式 Stage 5 go/no-go 条件：必须先有一个能够进入生成阶段并实际使用 `/workspace/tests` 的有效 Run。

## 8. 对完成率、Token、耗时影响预估

| 指标 | 结论 |
|---|---|
| 完成率 | 本 Run 为 score 0、0/0，但这是生成前认证阻断，不代表业务完成能力为 0。 |
| Token | 未计量；Provider 和平台 Token/费用均为 `null`，不能当作低 Token 成功。 |
| 耗时 | 平台 `run_duration_seconds=0`；从 started 到 finished 的日志时间约 3.566 秒。失败很快，但完全阻断任务。 |
| 后续预估 | 认证修复后，实际业务完成率、Token 和生成耗时均需新的有效 Run 才能判断。 |

## 证据

- manifest：`evidence/arc-bench/runs/c48754c25fcf/manifest.json`
- handoff：`evidence/arc-bench/runs/c48754c25fcf/phase4-handoff.json`
- ACK：`evidence/arc-bench/runs/c48754c25fcf/phase4-ack.json`
- 结构化 RESULT：`evidence/arc-bench/runs/c48754c25fcf/phase4-result.json`
- 原始 run/logs 文件名、路径和 SHA-256：见 manifest；原始文件未复制进仓库。
