# 阶段 4 只读诊断报告：arc-bench-lite--keep / `bf5e742c15a4`

PHASE4_RESULT: complete

## 结论

本报告只分析 Run `bf5e742c15a4`，不合并其他 Keep 或 BookStack Run 的业务结论。该 Run 与 `cca008377368` 共享 submission_id，但任务不同，必须保持独立。

这是一次**生成/认证前置阻断**，不是 Keep 业务功能失败：

```text
生成命令启动
→ 模型认证探测返回 permanent HTTP 401
→ main.py 退出码 2
→ 未生成 frontend/、backend/、main.py 或 tests
→ run_tests 未到达
→ 平台 FAILED，score 0，0/0
```

`0/0` 不代表业务完成率。当前没有任何生成后的应用、验收轮次、Playwright 执行或业务失败测试可诊断。

## 身份核验

| 字段 | 值 |
|---|---|
| handoff_id | `bf5e742c15a4-11DE0A63D4FE` |
| run_id | `bf5e742c15a4` |
| submission_id | `0b90e43b07b7` |
| task | `arc-bench-lite--keep` |
| thread_id | `01a0b57a-7a65-77d0-a08a-e202167e4f70` |
| manifest SHA-256 | `11DE0A63D4FE445FDA8A1016E5271EFD631631BD9C96D81028E3500DA37C554E`，与 handoff 声明一致 |
| ACK | 已写入当前 handoff_id |

## 1. 已确认事实

- 平台最终状态为 `FAILED`，score `0`，通过/总数为 `0/0`。
- failure reason 是 generation command 返回 exit status `2`。
- runner 确实执行了 `main.py`，参数为 `/tmp/arcbench/requirements-source` 和 `--output-dir /workspace/template`。
- runner spec 包含 `/workspace/tests`，bundled fallback 命中为 `0`；这只表示测试准备配置存在。
- 环境预检、Docker 启动和 Agent 依赖安装完成。
- 生成阶段立即观察到脱敏的 `permanent authentication failure; aborting before generation (HTTP 401)`。
- meter baseline login 也观察到脱敏的 HTTP 401。
- main.py 退出码为 `2`，`run_tests` 为 pending/not reached，tests[] 为空，没有 acceptance 记录。
- 应用服务和 Playwright 均未启动。
- 模板 ZIP 有 23 个条目，SHA-256 为 `250177D127D6A398DCFF58EE6429FEE71DCC2C7F3C781CC1B3A9A1F1330EC852`；全部为 requirements/reference 资产，`frontend/`、`backend/`、`main.py`、tests 均为 0。
- 日志只出现掩码的 `OPENAI_API_KEY=set(len=9)`，明文 `sk-` 命中为 0。

## 2. 最终失败链路

### 生成阶段

1. runner 完成环境预检、依赖安装并启动生成命令：

   ```text
   python3 /workspace/submission/main.py /tmp/arcbench/requirements-source --output-dir /workspace/template
   ```

2. Agent 的认证探测立即返回 permanent HTTP 401。
3. 生成命令没有进入有效的应用生成阶段，直接以退出码 2 结束。
4. 没有生成 `frontend/`、`backend/`、`main.py` 或测试目录。

### 平台阶段

1. runner 收到生成命令非零退出。
2. `run_tests` 保持 pending/not reached。
3. 应用服务与 Playwright 未启动。
4. 平台最终记录 `FAILED / score 0 / 0/0`。

因此，平台失败是生成命令失败的直接下游结果，而不是某个 Keep 业务测试失败。

## 3. 根因候选及证据等级

### RC-GEN-1：模型认证请求被拒绝

- 证据等级：`confirmed_observation_not_attribution`
- 置信度：针对“发生认证失败”这一事实为高
- 证据：原始日志记录 permanent authentication failure、HTTP 401 和 main.py 退出码 2；meter 登录也有独立的脱敏 401。

已确认认证失败阻断了生成，但尚不能判断具体是密钥有效性、账号权限、模型授权、provider 路由、平台凭据绑定，还是临时平台状态。

### RC-GEN-2：生成命令未产出所需应用树

- 证据等级：`confirmed_behavior`
- 证据：退出码 2；最终 ZIP 中 `frontend/`、`backend/`、`main.py`、tests 均不存在；服务和测试未启动。

该行为已确认，但由于没有提交源码与 build 绑定，尚不能定位到 Agent 的具体函数。

### RC-PLAT-1：平台无法进入测试阶段

- 证据等级：`confirmed`
- 证据：run failure reason、`run_tests=pending/not reached`、空 tests[] 和模板清单一致。

这是平台前置阶段的确定性结果，不是独立的业务根因。

### RC-OPT-1：认证错误应有边界明确的快速失败路径

- 证据等级：`strong_candidate`
- 证据：本 Run 在认证探测阶段立即失败，没有任何有效生成工作；提前分类 401 有望避免无效的后续流程。

该建议需要隔离复现和源代码定位，阶段 4 不直接修改重试或认证逻辑。

## 4. 已排除原因

- 不是入口缺失：`main.py` 已被执行。
- 不是 bundled tests 回退：`/workspace/tests` 已配置，bundled 命中为 0。
- 不是 Playwright 失败：应用服务和 Playwright 都没有启动。
- 不是 Keep 业务实现缺陷：没有生成任何业务应用，无法进入功能测试。
- 不是已观察到的明文 API Key 泄露：只记录掩码状态，明文命中为 0。
- 不是官方测试套件导致的失败：平台在测试前就因生成命令退出而停止。

## 5. 证据缺口

仍缺少：

- HTTP 401 的确切责任边界：密钥、账号权限、模型授权、provider 路由或平台凭据绑定；
- task snapshot、Agent build ID、代码 SHA、平台 ZIP-to-build 绑定；
- provider token totals、请求数、费用和 acceptance round；
- 当前 Run 的 snapshots、生成源代码、Playwright report、trace/HAR、error-context；
- 提交代码中导致退出码 2 的具体函数级定位。

这些缺口不影响“生成阶段阻断、没有业务测试”的判断，但会限制认证责任和 Agent 代码责任的最终归因。建议 `needs_repro=true`，仅复现认证/生成链路，不表示当前阶段应立即重跑平台。

## 6. 最小只读复现实验建议

### 实验一：分离模型 endpoint 与 meter 认证

在不输出密钥的前提下，使用相同模型、base URL 和执行配置分别做一次受控认证预检，分别记录状态码和错误类别。不要在本阶段创建平台 Run。

### 实验二：验证 main.py 的生成输出契约

在本地隔离环境使用确定性的 mock/fixture 模型响应运行现有入口，确认是否生成 `frontend/`、`backend/` 并以成功状态退出。不得修改官方测试或当前平台提交。

### 实验三：定位退出码 2 与错误分类

在隔离生成驱动中分别注入 401、可恢复 5xx 和成功响应，记录退出码、重试次数、耗时和文件写入状态，确认 401 是否应快速失败。

## 7. 阶段 5 入口建议

建议将本 Run 交给阶段 5，但分类为：

```text
生成管线 / 认证门禁问题，不是 Keep 业务功能问题
```

优先顺序：

1. 核验模型 endpoint、模型授权、账号和 meter 认证链路；
2. 检查 Agent 在成功模型响应下能否生成 `frontend/` 和 `backend/`；
3. 隔离复现后评估 401 的快速失败和错误分类；
4. 不基于本 Run 修改 Keep 业务实现；
5. 认证与 skeleton 产出确认后，再考虑新的平台 Run。

本阶段 4 未直接向阶段 5发送消息，未实施任何代码、测试或配置修改。

## 8. 指标影响

- 完成率：`0/0`，不应与业务功能完成率比较。
- 得分：`0`，原因是生成命令在业务测试前退出。
- Token、请求数、费用：均不可用。
- run 对象耗时：`0s`；按时间戳推导约 `6.52943s`，两种口径均保留。

## 证据哈希与执行边界

| 证据 | SHA-256 |
|---|---|
| manifest | `11DE0A63D4FE445FDA8A1016E5271EFD631631BD9C96D81028E3500DA37C554E` |
| run JSON | `F22E49E256CBFFCB1AC3C012E25643081DF018A684910F35EFB8863916BDEB08` |
| logs JSON | `A8752C1BEC16451E9E997A40908D73B40F794D975E85A720B803118BB7A172A4` |
| summary | `18FCAE8A2F8E0EE86156ADE2D1758FD729B044E3EF8785030B1FBFE4AA293AA6` |
| failure details | `15AFB8C03B62A3C7540BCAEA2C4E76AD31E2CF30A779A99FCBD60A2F2C8756BB` |
| template ZIP | `250177D127D6A398DCFF58EE6429FEE71DCC2C7F3C781CC1B3A9A1F1330EC852` |

结果文件：[phase4-result.json](phase4-result.json) · [phase4-ack.json](phase4-ack.json)

本次仅处理 `bf5e742c15a4`，未创建新 Run、未重跑、未上传、未修改代码、官方测试或阶段 5台账，也未执行远程同步。
