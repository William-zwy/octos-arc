# Octos Agent 优化实施记录：Round 5

> 实施日期：2026-09-27
> 本轮主题：修复跨节点回归漏检——依赖回归只信"声明的依赖边"，抓不住沿"共享 UI/数据面"传播的破坏
> 触发来源：`octos-keep-0927-v2_1`（30/32）里 REQ-2.4「Update Note」自己周期 4/4、full-suite 却挂

---

## 1. 背景与定位

原版 v2_1 完整跑拿到 30/32，两个失败：

- **REQ-6.2**：最后一个节点，撞 402 欠费（`tools=0`），非质量问题。
- **REQ-2.4「Update Note」**：自己节点周期 **round 0: 4/4**，到最终 full-suite 却失败——`dialog[Note editor] → textbox[Note content]` 超时找不到。这是**真正的跨节点回归**。

REQ-2.4 的 spec 本身没问题、单独跑能过。是它**之后**某个改笔记卡片/编辑器的节点（2.5.x 颜色 / 2.7.x 标签 / 2.8.x pin）重写编辑器时，改了对话框结构或 `Note content` 输入框的可访问名，把 2.4 的入口破坏了。

## 2. 根因

依赖回归 `acceptance_specs_for()` 靠 `ancestors_of()` 取回归 spec，而 `ancestors_of()` **只走 requirements 里声明的 `dependencies` 字段**。

用数据验证过覆盖漏洞：
- `REQ-2.4.spec.ts` 在整个跑里只作为回归 spec 出现 **2 次**（基本只有它自己 node 7）。
- 对比 `REQ-2.5.1.spec.ts` 作为依赖被后续节点回归了 **8 次**。

keep 的依赖图里，2.5.x/2.7.x/2.8.x **没有把 REQ-2.4 声明为依赖**（它们逻辑上不依赖"更新笔记"，但物理上都改同一个编辑器 UI）。于是这些节点改坏编辑器时，依赖回归根本不带 2.4 的 spec 跑 → 一路漏检到最后 full-suite 才暴露，而那时 repair 又被 402 饿死（`tools=0`），无从补救。

**根本原因：破坏沿"共享 UI/数据面"传播，依赖回归却只认"逻辑依赖边"，两者不重合。**

---

## 3. 修改内容（方案 1）

本轮只改两个文件：

| 文件 | 修改 |
|---|---|
| `arc/main.py` | `acceptance_specs_for()` 在声明祖先之后，用剩余预算 backfill "已通过的最早节点" spec；新增 `core_regression_specs()` |
| `arc/tests/test_main_helpers.py` | 增加 `CoreRegressionTests`（2 个用例） |

### 3.1 通用策略：不写死题目编号

不硬编码 keep 的 "2.2/2.4/2.3.x"，而是用一个**通用代理**：**已通过的、最早构建的节点**。它们建的是 app 外壳 + CRUD 核心，后续每个节点都在其上叠加——正是最该被保护的"共享地基"。

`acceptance_specs_for()` 的选择顺序（都受同一个 `OCTOS_ARC_DEP_REGRESSION_MAX_SPECS` 上限约束，默认 12）：

1. 当前节点自己的 spec（不计入上限）。
2. 声明的祖先 spec（原有逻辑）。
3. **新增**：用剩余预算 backfill "已通过的非祖先节点" spec，按构建顺序（最早优先）。

```python
# main.py acceptance_specs_for() 新增分支
for spec in self.core_regression_specs(node_id, ordered):
    if not take(spec):
        break
```

```python
# main.py Flow.core_regression_specs()
def core_regression_specs(self, node_id, ordered):
    if os.environ.get("OCTOS_ARC_CORE_REGRESSION", "1") == "0":
        return []
    pinned = os.environ.get("OCTOS_ARC_CORE_REGRESSION_SPECS", "")
    if pinned.strip():                       # 显式覆盖：spec 名单（basename 或全路径）
        wanted = {p.strip() for p in re.split(r"[,\s]+", pinned) if p.strip()}
        ...
    passed = {n for n, v in self.test_verdict.items() if v is True and n != node_id}
    order = {str(n.get("id")): i for i, n in enumerate(ordered)}
    out = []
    for nid in sorted(passed, key=lambda n: order.get(n, 1 << 30)):
        out.extend(self.spec_map.get(nid) or [])
    return out
```

### 3.2 开关

- `OCTOS_ARC_CORE_REGRESSION=0`：关闭 backfill，回到纯依赖回归行为。
- `OCTOS_ARC_CORE_REGRESSION_SPECS="REQ-2.4.spec.ts,..."`：显式指定强制回归的 spec（basename 或全路径均可），不再用"最早通过"启发式。

### 3.3 覆盖效果验证

以 keep 为例，MAX_SPECS=12、后段节点声明祖先通常只有 3~4 个：
- 跑 **REQ-2.5.1**（第一个改编辑器的节点）时，剩余预算会自动带上已通过的 REQ-2.3.x、**REQ-2.4** 等 → 编辑器一被改坏，**当前节点就红**，触发 repair，而不是拖到 full-suite。

---

## 4. 测试

先 RED 后 GREEN：

```
python -m unittest tests.test_main_helpers.CoreRegressionTests
```

- `test_should_regress_passed_nonancestor_spec_when_budget_allows`：节点 C 只声明依赖 A，但已通过的非祖先 B 会被 backfill 进 C 的回归集。
- `test_should_not_add_core_regression_when_disabled`：`OCTOS_ARC_CORE_REGRESSION=0` 时不加 backfill。

结果：2 passed。

```
python -m py_compile arc/main.py arc/tests/test_main_helpers.py   # OK
python -m unittest tests.test_main_helpers                        # 27 passed
```

向后兼容：既有 `DependencyRegressionTests` 全过——它们不设 `test_verdict`，`passed` 集为空，backfill 不加任何 spec，旧行为完全保留。唯一失败 `InlineSourcesTests` 是既有 Windows 路径分隔符问题（Round 2 §5.2 已记录，Linux 通过）。

---

## 5. 预期影响

- **跨节点回归提前暴露**：改坏共享编辑器/外壳的节点，在**自己周期内**就会因为 backfill 的地基 spec 失败而进 repair，不再拖到 full-suite（那时 repair 预算/时间常已耗尽）。
- **成本可控**：受同一个 MAX_SPECS 上限约束；spec 运行本身很便宜（full-suite 32 spec 仅 51s），真正的成本是被触发的 repair turn——而那正是我们想要的（早修早好）。
- **无写死编号**：对任何题目都生效，靠"最早通过节点"这个通用代理，不依赖 requirements 声明质量。

## 6. 尚未验证

- 需独占 key、余额充足、串行重跑 keep，才能干净确认 REQ-2.4 类回归被提前拦下、且总通过率不因额外 repair 而下降。
- backfill 可能让某些节点验收变严（要连带修好它破坏的地基）。这是 Round 2 既定取向"后续节点不得破坏前序功能"的自然结果，但需实测确认不会引入过多 repair 抖动。

## 7. 下一步

1. `sh arc/pack.sh` 重新打包（本轮标记 v2_3）。
2. 独占 key 重跑 keep，对比 REQ-2.4 是否在 2.5.x/2.7.x 阶段就被拦下。
3. 观察额外 repair 带来的 token/time 增量，必要时用 `OCTOS_ARC_DEP_REGRESSION_MAX_SPECS` 调节。
