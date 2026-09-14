# 本机 keep 试跑 4（main@803f14c3 适配包 = A1–A7 + Playwright 修复 + 并行安全持久化，魔改内核 2.0.3-rc.11）

- 参数：OCTOS_SECONDS_PER_NODE=1500 OCTOS_TIME_BUDGET=48000 OCTOS_NODE_TIME_BUDGET=1500 OCTOS_NODE_TIMEOUT=1500 OCTOS_IMPLEMENT_FRACTION=0.6 OCTOS_REPAIR_ROUNDS=2 OCTOS_DESIGN_MODE=inline OCTOS_FINAL_REPAIR_ROUNDS=2（与 A 在 aab51793 之后的默认值等价）
- 时间：2026-09-13 01:55:01 → 06:56:00 UTC，共 5 h 01 min；骨架 312 s；32 个节点轮合计约 16,600 s（平均 519 s/节点，adapter.log 每行打印两次，turn-summary 里的秒数按一次计）；全套并行验收 round 0 28/32 → 一轮全套修复 1061 s → round 1 32/32；启动演练通过
- **官方评分 grade-local：32/32（100%）**（grade-final.log）
- 节点验收：30 个节点首轮 1/1；REQ-2.3.1 与 REQ-6.2 首轮 0/1、一轮修复后 1/1；实现轮触顶 900 s 上限的节点：REQ-2.3.1、2.5.1、2.7.1、2.7.4（tools 100–190）
- Token（事件流 turn/completed，73 轮，不含超时轮）：tokens_in 2,593,001、tokens_out 1,116,085；内核 token_cost_update 各会话累计见 cost.txt
- 对照：试跑 3（480 s/节点）17 轮里 16 轮超时、停在第 10 节点时 8/32；试跑 2（旧整体式流程）26/32、83 min
