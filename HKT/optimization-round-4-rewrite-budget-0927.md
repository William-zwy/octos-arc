# Octos Agent 优化实施记录：Round 4

> 实施日期：2026-09-27
> 本轮主题：修复"超时→整体重写"恢复路径被请求预算腰斩的尾部丢分
> 触发来源：对比 `octos-keep-0927-v2_1`（原版，30/32）与 `octos-keep-0927-v2_1-f`（改后变体）两次本地完整跑

---

## 1. 背景与定位

对比两次 keep 完整跑：

| | 原版 v2_1 | -f 变体 |
|---|---|---|
| 结果 | 30/32 (93.8%) | 15/32 |
| 撞 402 欠费时刻 | 13:27:45 @REQ-6.1 (node 31) | 13:27:42 @REQ-2.7.6.1 (node 19) |

两次跑撞 402 只差 3 秒，是**并行共用同一 API key、共享余额同时耗尽**。`-f` 起步晚 1h47m，到断供时只跑到 node 19，所以 15/32 主要是**欠费时机**造成，不是质量退化。

**但 `-f` 有一个不能用欠费解释的真实退化：REQ-2.5.1。** 它跑在 11 点多，远早于 13:27 的欠费：

- 原版 v2_1：`REQ-2.5.1 implement ok in 303s (tools=30)` → round 0: **4/4**
- -f 变体：`REQ-2.5.1 implement FAILED in 900s (tools=42)` → rewrite → 仍 **0/4**

逐节点耗时对比后确认：**两次跑各有 3 个 implement 超时，只是落点不同**（v2_1: 2.2/2.7.1/2.7.5；-f: 2.3.1/2.5.1/2.7.5），且速度双向抖动。这是 deepseek-v4-flash 在难节点上的采样抖动，**不是本轮之前改动（Fix A/B skeleton 不注入契约）造成的**——2.5.1 在 node 8、契约非空，两次注入内容一致。

真正的差别在**超时之后能否恢复**。

---

## 2. 根因

`node_cycle` 的 repair 循环里，当 round 0 一个都没过（`passed == 0`）时，会触发**一次整体重写**（rewrite）代替 patch。问题出在这个重写调用点硬编码了请求预算：

```python
# main.py（改前）
self.turn(prompt, min(self.node_timeout, left), f"{node_id} rewrite (repair {attempt + 1})",
          request_budget=int(os.environ.get("OCTOS_ARC_IMPLEMENT_REQUESTS", "20")))
```

而正常 implement turn 的预算逻辑是（同一个 env，但 default 不同）：

```python
# main.py turn()
request_budget = ... else int(os.environ.get(
    "OCTOS_ARC_IMPLEMENT_REQUESTS",
    "20" if self.minimal_mode(n_nodes) else "0"))   # 多节点 → "0" 无限
```

**致命的不对称**：keep 是 32 节点任务，`minimal_mode=False`，所以：

- 超时被杀的**原始 implement**：`request_budget=0`（无限工具调用，只受时间约束）
- 救场的**整体重写**：硬编码 default **`"20"`**

成功的 implement 普遍用 30~56 个工具调用，重写却被砍到 20 次。REQ-2.5.1 的重写日志：

```
[flow] REQ-2.5.1: nothing passed; one full rewrite turn instead of a patch
[flow] REQ-2.5.1 rewrite (repair 1) ok in 304s (tools=20 wrote=True verified=True)
[guard] REQ-2.5.1 rewrite (repair 1): request budget 20 hit; turn forced to finish  ← 写到一半被砍
[acceptance] REQ-2.5.1 round 1: 0/4                                                  ← 重写没写完
[flow] REQ-2.5.1: 296s left, below the 300s a repair needs; keeping the best state   ← 没时间再来
```

重写在 304s（还有约 300s 时间预算）就因为撞 20 次请求上限被强制收尾，frontend/backend 没写完 → 验收 0/4 → 时间也不够再来一轮 → 放弃。

对照 v2_1 的超时节点为什么没坏：
- REQ-2.7.1：900s 超时那刻的半成品**碰巧就是好的**，round 0 直接 4/4（运气）。
- REQ-2.2：900s 超时 → 重写这轮**跑完了** → round 1: 3/3。

换个随机种子，v2_1 也会坏节点。所以这是**结构性尾部风险**，不是某一版特有。

---

## 3. 修改内容

本轮只改两个文件：

| 文件 | 修改 |
|---|---|
| `arc/main.py` | 抽出 `implement_request_budget()`，让 implement 与 rewrite 共用同一预算逻辑；rewrite 增加独立覆盖 env |
| `arc/tests/test_main_helpers.py` | 增加 `RewriteBudgetTests`（2 个用例） |

### 3.1 抽取共享的预算辅助方法

```python
# main.py Flow.implement_request_budget()
def implement_request_budget(self) -> int:
    """Per-turn request cap for implement AND full-rewrite turns. A rewrite
    re-implements the whole node, so it must share the implement budget:
    multi-node tasks are uncapped (0), small tasks keep the 20 cap."""
    return int(os.environ.get("OCTOS_ARC_IMPLEMENT_REQUESTS",
                              "20" if self.minimal_mode(getattr(self, "n_nodes", 99)) else "0"))
```

`turn()` 里的 implement 分支改为调用它，逻辑不变（重构）：

```python
request_budget = int(os.environ.get("OCTOS_ARC_REPAIR_REQUESTS", "10")) if "repair" in label \
    else self.implement_request_budget()
```

### 3.2 rewrite 调用点跟随同一预算 + 独立覆盖开关

```python
# main.py node_cycle() 重写分支（改后）
rewrite_budget = int(os.environ["OCTOS_ARC_REWRITE_REQUESTS"]) \
    if os.environ.get("OCTOS_ARC_REWRITE_REQUESTS") else self.implement_request_budget()
self.turn(prompt, min(self.node_timeout, left), f"{node_id} rewrite (repair {attempt + 1})",
          request_budget=rewrite_budget)
```

效果：
- 32 节点任务：重写预算 = `0`（无限），与它要救的 implement 一致，能写完整个节点。
- 小任务（≤2 节点）：重写预算 = `20`，与 implement 一致，行为不变。
- `OCTOS_ARC_REWRITE_REQUESTS` 可单独限制重写预算而不影响 implement。

### 3.3 为什么不动 `min_repair_seconds`

"296s < 300s 放弃"是**次生现象**：只要重写不被腰斩、round 1 能过，就根本走不到那个临界判断。降低 `min_repair_seconds` 反而有风险（时间太少的 repair 一样会超时），故保持默认 300s 不变。

---

## 4. 测试

先 RED 后 GREEN：

```
python -m unittest tests.test_main_helpers.RewriteBudgetTests
```

- `test_should_give_rewrite_unlimited_requests_on_multi_node_tasks`：32 节点 → 预算 0
- `test_should_cap_rewrite_like_implement_on_small_tasks`：1 节点 → 预算 20

结果：2 passed。

```
python -m py_compile arc/main.py arc/tests/test_main_helpers.py   # OK
python -m unittest tests.test_main_helpers                        # 25 passed
```

唯一失败 `InlineSourcesTests` 是既有的 Windows 路径分隔符问题（`frontend\src` vs `frontend/src`），Round 2 §5.2 已记录，Linux 上通过，与本轮无关。

---

## 5. 预期影响

- **降低"超时→重写"路径的尾部丢分**：重写能用满时间预算把节点写完，而不是在 20 次请求处被砍断。
- 不改变正常 implement、正常 patch repair、小任务的行为。
- 无跨节点副作用：重写受 `min(node_timeout, left)` 时间约束，不会吃掉后续节点预算。

## 6. 尚未验证

- 需在**独占 key、余额充足、串行不并行**的环境重跑 keep，才能干净对比通过率。现有两次跑都被 402 污染。
- REQ-2.4 的跨节点回归（编辑器 UI 被后续节点改坏、依赖回归未覆盖）是另一独立问题，本轮未处理，留待后续。

## 7. 下一步

1. `sh arc/pack.sh` 重新打包。
2. 独占 key 重跑 keep，对比 REQ-2.5.1 类"超时节点"是否能被重写救回。
3. 若通过率提升，再评估 REQ-2.4 依赖回归覆盖策略（共享编辑器面的节点强制回归基础 CRUD spec）。
