# Agent 创建后结果语义契约变更

日期：2026-09-25。读者：维护 ARC-Bench Agent 和接手验证的开发者。

## 状态与范围

用户已在本会话明确要求修改 Agent。本次完成一个本地提示契约候选，不是平台问题已经解决的证明。`business_go=false`、`strict_ab_comparable=false` 保持不变。

基线提交：`e72ba3c92272b2e8e6d3fd05ff460017c882e569`。修改在 `D:/items/Hackathon/octos-p` 工作区，未提交、未打包、未上传、未运行平台任务，没有新产物 SHA 或 build ID。已有 docs 删除状态、HKT 文件及三个脚本均保留。

对应交接文档中的 P5-017 两个 confirmed 创建题：REQ-4.3.1、REQ-6.1.1。记录中的机制是写入成功后最终页面只有实体链接、没有同名 heading。REQ-8.1、Keep、登录身份、服务端模板/路由问题不纳入本次切片。

## 实际修改

| 文件 | 修改 |
|---|---|
| [arc/main.py](../arc/main.py) | 新增共享 `CREATE_RESULT_CONTRACT`，接入 UI core、独立 design、codegen、repair 提示；design 的角色枚举增加 heading |
| [arc/tests/test_main_helpers.py](../arc/tests/test_main_helpers.py) | 新增 5 项提示契约测试 |
| [CHANGELOG.md](../CHANGELOG.md) | 登记本地 Agent 候选及验证边界 |
| [阶段五台账](ARC_BENCH_HACKATHON_PHASE5_DECISION_REGISTER.md) | 追加本次授权、改动和验证记录，保留历史结论 |
| [协同索引](../evidence/arc-bench/phase5-coordination.json) | 为 P5-017 增加本次本地候选子记录，不冒充历史线程派发或平台验收 |

实际平台入口是 Python `arc/main.py` 的 `Flow`，经 `OctosDriver` 调用 Octos runtime；不是独立 Rust `octos arc` runner 的 `policy.txt`。历史文档提及的旧候选不等于当前 checkout 已包含对应代码，本次基线未找到共享创建结果契约。

契约要求：仅对具有命名实体的创建/保存流程，在成功 2xx 响应且持久化后，稳定目标页以一个可见语义 heading 显示精确实体名；保留导航链接，推荐将链接嵌入适当层级的标题，例如 `<h2><a href="...">name</a></h2>`。不另加同名成功标题、链接或 toast。失败时保留表单和错误反馈，不显示成功标题；其他交互保持既有语义。

普通实现和 inline design 通过 `Flow.ui_contract()` 获得规则；独立 codegen 与 repair 直接复用同一常量，避免遗漏或多份规则漂移。没有新增模型调用、改变请求预算/repair 轮数/timeout、修改后端协议或官方 spec/helper，也没有硬编码应用名、需求编号或测试实体名。

## 验证结果

使用 Python 3.12.4 / Windows。先添加测试再修改实现。

| 检查 | 结果 |
|---|---|
| 新 5 项测试在改实现前 | exit 1：共享常量不存在，design schema 缺 heading；符合预期 RED |
| 新 5 项 + 既有 codegen 格式测试 | 6/6，exit 0 |
| 改动前完整 arc/tests | 78 项，75 通过、3 失败，exit 1 |
| 改动后完整 arc/tests | 83 项，80 通过、3 失败，exit 1；失败名称与基线一致 |
| `git diff --check` | exit 0 |

三项既有 Windows 路径相关失败：

- `PrivateInstallTests.test_should_keep_every_write_inside_the_private_root`
- `ProtectedTreeTests.test_should_restore_changed_deleted_and_added_files`
- `InlineSourcesTests.test_should_quote_small_files_and_omit_those_over_budget`

全量测试不绿，不能标记全量验证通过。首个基线命令未配置 PYTHONPATH，导致导入失败；修正后才得到上述有效基线。

从仓库根目录，在 PowerShell 复跑：

```powershell
$env:PYTHONPATH = (Resolve-Path ./arc).Path
python -m unittest tests.test_main_helpers.CreateResultContractTests tests.test_main_helpers.CodegenPromptTests
python -m unittest discover -s arc/tests -p 'test_*.py'
git diff --check
```

新增测试验证：共享规则在各提示中出现一次、inline design 接线、成功/失败分支文本、导航和去重约束、通用性及长度上界、design schema 支持 heading。长度检查为英文空白分词数，不是模型 tokenizer 测量，也不构成 token 成本保证。

## 尚未验证

- 未用真实模型生成新应用，未启动生成应用服务器、未进行浏览器功能验证。
- 未跑两个 confirmed 题的 3/3、邻接回归、33 项非收藏集合三轮、完整 34 项或跨任务 canary。
- 未构建上传包，未闭合平台身份链，也未取得平台 A/B 结果。
- 当前环境未安装 Python Playwright，检查的 e2e 目录亦无本地 Playwright 依赖；本次没有安装浏览器或依赖来代替真实生成验证。

下一步是按原交接门禁验证新 Agent 的实际生成结果；需要真实模型预算和平台操作时另行授权。提示测试只能证明规则被传给模型，不能保证模型遵守或平台得分提升。

## 对此前说明的更正

2026-09-24 创建的三个 `arc-bench-*.sh` 是未验证、核心执行缺失的模板，不是已完成的诊断或平台验证设施。此前声称 P5-005 已解决、100% A/B 可追溯、费用已下降均无验证依据。

尤其不得使用当前 milestone 脚本的 `strict_comparable` 作为平台身份已闭合的证据：平台 metadata 核验仍未实现。repro-matrix 未执行真实测试，也不能用多数通过或丢弃时长极值判定 `false_alarm`，或自动把某机制升级为 confirmed。本次不调用、不修订这些脚本，后续应单独修正后才能使用。
