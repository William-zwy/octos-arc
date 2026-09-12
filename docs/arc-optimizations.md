# ARC-Bench 内核优化记录

分支：`arc-opt`。所有数字均来自本机事件流或测试输出；评测分数与单元测试结果分开记录。

## 结论摘要

| 项目 | 改前 | 改后 | 证据 |
|---|---:|---:|---|
| stdio/solo `Reply OK` 输入 Token | 17,205 | 5,713 | `turn/completed`，`/private/tmp/arc-stdio-probe-events.jsonl` |
| stdio/solo 模型可见工具数 | 62 | 12 | serve 日志 `tool_count` |
| Counter 轮数 | 3 | 3 | 两个 `.arc/octos-events.jsonl` |
| Counter 输入 Token | 64,658 | 36,384 | 两个 `.arc/octos-events.jsonl` |
| Counter 输出 Token | 20,337 | 18,174 | 两个 `.arc/octos-events.jsonl` |
| Counter 费用 | 0.01474648 | 0.11239816 | 两个 `.arc/octos-events.jsonl` 的 `token_cost_update` |
| Counter 耗时 | 667 秒 | 290 秒 | 两个 `.arc/runner-events.jsonl` 的 running/completed 时间 |
| Counter Playwright | 1/1 | 1/1 | 修正 `baseURL` 后的公开测试 |
| Ticket Booking 轮数 / Token / 费用 | 0 / 0 / 无记录 | 0 / 0 / 无记录 | 两次运行均在首轮长时间停留后人工中断 |
| Ticket Booking 耗时 / Playwright | >10 分钟 / 未执行 | 约 3 分钟 / 未执行 | 两次均无 `turn/completed`，不能算评测通过 |

## P0-0：stdio/solo 提示与工具面瘦身

改动位置：`crates/octos-cli/src/commands/serve.rs`、`runtime/profile.rs`、`api/ui_protocol_transport.rs`。

`serve --stdio --solo` 启动时默认启用 coding profile，严格保留 12 个编码工具；bundled app-skills/platform-skills 不再自动 bootstrap。空 memory 不生成策略段或 `memory-snapshot`，无 active goal 不生成 `session-goal-snapshot`。panes 树仍只属于 `session/open` 的协议返回，不会追加到模型历史。

验证：CLI 单测 `p0_0_tests`、profile 白名单单测；真实 arm64 二进制用同一 API 配置和同一句 `Reply OK` 运行，得到 5,713 输入 Token、12 工具、成功回复 `OK`。

## P0-1：容器沙箱显式降级

改动位置：`crates/octos-agent/src/sandbox/mod.rs`。

启动时检测 `/.dockerenv` 及 docker/containerd/kubepods/podman/libpod cgroup 标记；容器中无可用隔离后端时记录明确 warning 并按容器策略降级，探测函数保持纯函数便于测试。新增 dockerenv、cgroup 和误判排除测试。

本机未运行 Docker 容器验证：本机 Docker 不可用，因此未声称完成 Linux 容器实测。复核步骤是使用无特权 Ubuntu 容器运行 Linux 构建产物，比较 `/.dockerenv` 和 `/proc/1/cgroup` 下的启动日志及 exec 结果。

## P0-2：上下文与 Token 控制

改动位置：`crates/octos-agent/src/compaction_tiered.rs`。

默认每条工具结果最多 8 KiB，超限结果保留头尾并加入截断标记；过期、重复或不在工作集的结果仍折叠为结构化一行摘要，当前工作集文件读取保持可重读性。新增头尾保留、工作集保护和历史折叠测试。

Counter 事件流的输入 Token 从 64,658 降到 36,384；这是同一平台一次运行的真实结果，不把它解释成仅由单个改动独立贡献的因果实验。

Counter 的 arc-opt 费用高于官方这次记录（0.11239816 对 0.01474648）；费用字段按事件流原样保留，不能据此推断成本优化。官方 `grade-local.py` 原始脚本的 Playwright 配置缺少 `baseURL`，本地对照时仅临时补入 `baseURL: process.env.E2E_BASE_URL` 后执行公开测试，随后恢复了脚本，故这里报告的是修正配置后的 1/1，而不是把原始脚本失败冒充产品评测结果。

## P0-3：推理模型空回合恢复

改动位置：`crates/octos-llm/src/context.rs`、`openai.rs`、`crates/octos-agent/src/agent/{detection,llm_call}.rs`。

DeepSeek V4 默认输出上限提高到 provider 级安全值；当 `finish_reason=length` 且无正文、无工具调用时，只重试一次，按配置降低 reasoning effort 或提高 max tokens；再次失败返回明确错误，不计为成功。新增判定与恢复策略测试。

## P1-4：流式失败自动回退

改动位置：`crates/octos-agent/src/agent/{detection,llm_call,mod}.rs`。

识别 SSE/streaming 不支持错误后，同一 session 记录 provider/model，后续请求直接走非流式路径；当前错误回合也自动回退一次。新增错误识别测试。Counter 运行期间平台请求成功，未再依赖适配层的 `OCTOS_DISABLE_STREAMING=1`。

## P1-5：环境事实前置注入

改动位置：`crates/octos-arc/src/runner.rs`。

`octos arc` 每次 session 仅探测一次 node/npm/python、cwd、npm registry 连通性、容器标记和 sandbox 状态，并将短行事实加入稳定基础提示，声明上限为 200 Token。

## P1-6：Playwright 验收 hook

改动位置：`crates/octos-arc/src/runner.rs`。

轮次结束的本地验证会发现显式目录或工作区内的 `*.spec.ts`，从项目及 spec 目录祖先查找 Playwright；存在时运行 `playwright test --reporter=line`，失败内容以 `[hook]` 错误回传。没有 spec 或 Playwright 时记录 skipped 并继续。目录和基址可由 CLI 参数或 `OCTOS_ARC_SPEC_DIR`、`OCTOS_ARC_BASE_URL` 指定。单测用临时 spec 和 fake runner 验证了实际执行、基址注入及 passed 证据记录。

## P2-7：按节点预算

改动位置：`crates/octos-arc/src/runner.rs`。

新增 `--node-budget-seconds`（默认 300）和 `--node-token-budget`（默认 20,000）。每次运行按依赖拓扑逐节点启动 coding turn：进程 deadline 绑定到当前节点，配置中的输出上限绑定到节点 Token 预算；超时或回合失败时记录 `skipped_budget`，继续后续节点并保留已完成部分。预算计划写入 `node-budgets.json`、报告并前置到 coding prompt。依赖排序和预算边界有单测。

## 构建与测试

构建命令：

```text
cargo build --locked -p octos-cli --no-default-features --features api
```

产物为 macOS arm64 Mach-O。`cargo fmt --all -- --check` 和完整工作区 `cargo clippy --locked --all-targets -- -D warnings` 通过；`octos-arc` 测试为 21 passed / 1 ignored，`octos-llm` 为 687 passed / 3 ignored。完整 workspace `cargo test --locked` 在链接阶段因 26 GB 的测试临时产物耗尽磁盘而中止，随后分 crate 的 `octos-agent --lib` 测试完成但有 4 个既有 Docker 后端测试失败。

最终产物：`octos 2.0.3-rc.11 (1af844e9 2026-09-11)`；SHA-256 为 `0a00ba141e27063a5070231f9ad3f0a5496b688cfbf80042d602d893d176aa58`，对应 `aarch64-apple-darwin` 和 Homebrew `rustc 1.98.0`。

`runtime_release` 仍为 `null`，因为没有 GitHub Release；锁文件的 `build` 只记录真实产物元数据。
