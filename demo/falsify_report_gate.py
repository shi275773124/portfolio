#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
falsify_report_gate.py — 对抗审计闸门（脱敏可运行演示版）

我在电商数据管道里自建的机器闸门（falsify 家族）的浓缩演示。
零依赖，Python 3.8+ 标准库即可运行。

编码在这里的三条纪律：

  R1. 生产与复核不同立场
      闸门默认报告是错的。它的工作是找出错误，
      而不是确认数字看起来漂亮。

  R2. 一条无法被证明会翻红的护栏不是护栏，只是注释
      "A guardrail that cannot be proven to turn red is just a comment."
      --selftest 把四个历史 bug 逐个注入干净报告，
      断言每条检查都咬人。任何检查在坏报告上静默通过 = 闸门失效。

  R3. 宣称必须有产物证据
      「已修正/已部署」的声明必须能对上产物里的值，
      否则判假绿（文档说修了，产物没动）。

每条检查对应一个真实生产事故（数值已脱敏为相对值/百分比）：

  C1  跨表闭合        -> 子渠道加总 vs 汇总差 13.5%（成交/支付口径混用）
  C2  量级 sanity     -> CTR 1041%（后台导出列错位）
  C3  宣称 vs 产物    -> ROI「已修正为 7.58」但产物还是脏值 10.79
  C4  窗口自证        -> 自定义周窗口被平台静默钳位成滚动 7 天（偏差 11%）

用法：
  python falsify_report_gate.py             # 审计内置样例（含一个假绿 bug）→ BLOCK
  python falsify_report_gate.py --selftest  # 注入四个历史 bug，证明每条检查都翻红

退出码：0 = PASS / PASS_WITH_DEDT，1 = BLOCK（存在 Must Fix）。
"""

import copy
import sys

# ---------------------------------------------------------------------------
# 样例「报告产物」与「源数据」。数值均为相对值（脱敏）。
# ---------------------------------------------------------------------------

# 干净基线：selftest 用它证明「好报告零误报」
CLEAN = {
    "meta": {"window": "2026-W37", "window_start": "2026-09-07",
             "window_end": "2026-09-13"},
    "summary": {"gmv": 100000, "pay_gmv": 93000},  # 成交口径 / 支付口径，两个都合法但不能混用
    "channels": [
        {"name": "live",        "gmv": 60000},
        {"name": "short_video", "gmv": 20000},
        {"name": "product_card","gmv": 13000},
        {"name": "search",      "gmv":  7000},
    ],
    "material_top": {
        "ctr": 0.021,           # 2.1%
        "cvr": 0.031,           # 3.1%
        "roi_artifact": 7.58,   # 产物里实际渲染的 ROI
    },
    "claims": {"roi_corrected": True, "note": "列错位已修，ROI 按 gmv/cost=7.58 重建"},
}

# 演示样例：带一个假绿 bug（宣称已修，产物没重建）——默认审计它
DEMO = copy.deepcopy(CLEAN)
DEMO["material_top"]["roi_artifact"] = 10.79   # 历史真值：列错位产生的脏 ROI

SOURCE = {
    "window": "2026-W37",
    "gmv": 100000,                              # 源侧成交口径合计
    "sane": {"ctr": (0.0, 0.20), "cvr": (0.0, 0.50), "roi_artifact": (0.0, 50.0)},
    "expected_roi": 7.58,                       # 修正后的正确 ROI
}

# ---------------------------------------------------------------------------
# 四条检查。每条返回 [(check_id, 说明), ...]
# ---------------------------------------------------------------------------

def check_closure(report, source):
    """C1 跨表闭合：分项加总必须等于汇总，汇总必须对上源（同口径家族）。"""
    findings = []
    s = sum(c["gmv"] for c in report["channels"])
    target = report["summary"]["gmv"]
    if abs(s - target) / target > 0.005:  # 0.5% 容差（四舍五入）
        findings.append(("C1", "channel 加总 %d != summary %d（偏差 %+.1f%%）——"
                         "疑似跨表口径混用（成交 vs 支付？）" % (s, target, (s - target) / target * 100)))
    if abs(report["summary"]["gmv"] - source["gmv"]) / source["gmv"] > 0.005:
        findings.append(("C1", "summary GMV 与源聚合对不上（产物↔源对账失败）"))
    return findings


def check_sanity(report, source):
    """C2 量级 sanity：有界指标必须在合理区间（专治列错位脏值）。"""
    findings = []
    m = report["material_top"]
    for key, (lo, hi) in source["sane"].items():
        v = m.get(key)
        if v is None or not (lo <= v <= hi):
            findings.append(("C2", "%s=%s 越出合理区间 [%s, %s]——大概率列错位"
                             "（历史事故：CTR=1041%% 实为订单数）" % (key, v, lo, hi)))
    return findings


def check_claim_vs_artifact(report, source):
    """C3 宣称 vs 产物：「已修正」必须能对上产物值，否则判假绿。"""
    findings = []
    if report["claims"].get("roi_corrected"):
        art = report["material_top"]["roi_artifact"]
        if abs(art - source["expected_roi"]) > 0.01:
            findings.append(("C3", "宣称「ROI 已修正为 %.2f」但产物仍是 %.2f——"
                             "文档说修了、产物没重建（假绿）" % (source["expected_roi"], art)))
    return findings


def check_window(report, source):
    """C4 窗口自证：报告展示的窗口必须等于请求的窗口（防平台静默钳位）。"""
    findings = []
    if report["meta"]["window"] != source["window"]:
        findings.append(("C4", "报告窗口 %s != 请求窗口 %s——平台可能已静默钳位成滚动窗"
                         "（历史事故：周口径被换成滚动 7 天，偏差 11%%）"
                         % (report["meta"]["window"], source["window"])))
    return findings


CHECKS = [check_closure, check_sanity, check_claim_vs_artifact, check_window]

CHECK_DOCS = {
    "C1": "跨表闭合（分项加总=汇总=源）   <- 事故：口径混用差 13.5%",
    "C2": "量级 sanity（有界指标区间）    <- 事故：CTR 1041% 列错位",
    "C3": "宣称 vs 产物（反假绿）         <- 事故：ROI 说修了没修（10.79 vs 7.58）",
    "C4": "窗口自证（展示窗=请求窗）      <- 事故：滚动窗钳位偏差 11%",
}


def audit(report, source):
    findings = []
    for fn in CHECKS:
        findings.extend(fn(report, source))
    return findings


# ---------------------------------------------------------------------------
# selftest：把四个历史 bug 逐个注入，证明每条检查都咬人 + 好报告零误报（R2）
# ---------------------------------------------------------------------------

def selftest():
    cases = [
        # (名字, 变异函数, 期望咬人的检查)
        ("口径混用：支付口径 93000 被当成交口径写进汇总", lambda r: r["summary"].__setitem__("gmv", 93000), "C1"),
        ("列错位：订单数 10.41 落进 CTR 槽（1041%）",    lambda r: r["material_top"].__setitem__("ctr", 10.41), "C2"),
        ("假绿：宣称已修，产物仍是脏 ROI 10.79",          lambda r: r["material_top"].__setitem__("roi_artifact", 10.79), "C3"),
        ("窗口钳位：周窗口被换成 rolling-7d",             lambda r: r["meta"].__setitem__("window", "rolling-7d"), "C4"),
    ]
    clean_findings = audit(CLEAN, SOURCE)
    all_ok = not clean_findings
    print("selftest: 干净基线 %s（%d 误报）" % ("PASS" if all_ok else "FAIL", len(clean_findings)))
    for name, mutate, expect in cases:
        broken = copy.deepcopy(CLEAN)
        mutate(broken)
        findings = audit(broken, SOURCE)
        hit = any(c == expect for c, _ in findings)
        ok = hit
        all_ok = all_ok and ok
        print("selftest: [%s] %-42s -> %s 咬人" % ("OK" if ok else "MISS", name, expect))
    print("SELFTEST_%s" % ("OK" if all_ok else "FAILED"))
    return all_ok


def main(argv):
    if "--selftest" in argv:
        return 0 if selftest() else 1

    print("falsify_report_gate — 对抗审计演示（默认样例含一个假绿 bug）")
    print("检查族：")
    for cid, doc in CHECK_DOCS.items():
        print("  %s  %s" % (cid, doc))
    print()

    findings = audit(DEMO, SOURCE)
    if not findings:
        print("Verdict: PASS（零发现）")
        return 0
    print("Verdict: BLOCK — Must Fix %d 条，清空前不许发：\n" % len(findings))
    for cid, msg in findings:
        print("  [%s][Must Fix] %s" % (cid, msg))
    print("\n（--selftest 可验证这四条检查注入历史 bug 后全部翻红）")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
