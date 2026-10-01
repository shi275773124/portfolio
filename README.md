# Data Automation & Adversarial Audit — Portfolio

> 电商运营出身的数据自动化工程师：独立搭建「抓取 → 校验 → 生成 → 复核 → 上线」全管道，自建四层对抗审计体系（falsify），拦截过六位数金额级的口径错误与脏数据上线。

**English tagline:** Ops-turned data automation engineer. Built production-grade ingestion pipelines (CDP/Playwright reverse-engineering, idempotent fetch, dual-source reconciliation) and a four-layer adversarial audit system that caught six-figure data integrity bugs before they reached decision-makers.

---

## 这里面是什么

5 个 sanitized case studies——来自我在直播电商（抖音）一年多的生产实战，所有数字可当面追问展开。原始工作库含 500+ 篇带验证命令的变更记录、240+ 个生产脚本，面试可演示。

| # | 案例 | 核心亮点 | 对标岗位 |
|---|------|---------|---------|
| 1 | [周报全自动化管道](case-studies/01-weekly-report-pipeline.md) | 单份报告人时 20-30min → 5-8min；平台滚动窗钳位（偏差 11%）的发现与根治 | 数据工程 |
| 2 | [falsify 对抗审计体系](case-studies/02-falsify-audit-system.md) | 复核默认它错；拦下口径混淆（差 13.5%）、假 ROI 上线、两次归因反转 | 数据质量 / AI Eval |
| 3 | [素材雷达与量化审计](case-studies/03-material-radar-quant.md) | IC 审计 + 前瞻账本移植到广告素材决策；UNDERPOWERED 如实不判定 | 增长分析 / 数据科学 |
| 4 | [LLM 客户端与故障注入测试](case-studies/04-llm-client-product-falsify.md) | 错误契约表 + NIST 2-way 组合矩阵 32 例；首战抓出 402 重试 3 轮真 bug | AI 应用工程 |
| 5 | [运营决策系统](case-studies/05-ops-decision-systems.md) | 夏普比率排班（分子三连修正）+ 265 项工资闸门 + 目标拆日算法 | 经营分析 / BizOps |

## 方法论签名：falsify

大多数团队的「数据复核」是作者自查。我的立场：**生产与复核不能同一立场**——生成时默认它对，复核时默认它错，且复核者必须自拟 kill-shot，禁止形式审计。

落地成三个硬机制：

1. **机器闸门**：可机器判定的检查固化成脚本（产物↔源对账、脏值量级、假绿检测），agent 无法删改；判据改动必须重跑行为契约夹具
2. **Cutline 三分类**：Must Fix（清空前不许发）/ Known Debt（必须带升级触发器）/ Delete——拒绝「全部通过」的虚假安全感
3. **审计器自审**：一条无法被证明会翻红的护栏不是护栏，只是注释——每个审计器带故障注入 selftest

这套东西在 LLM 时代格外值钱：AI 生成的报告/代码/界面，同样需要默认它错的对抗复核。

## 关键数字速览

- **5-8 分钟**：全自动周报管道（原 20-30 分钟人工）
- **11%**：平台滚动窗钳位导致的口径偏差（发现→download-first 切源根治）
- **13.5%**：跨表口径混淆 Must Fix（子渠道加总 vs 画面 GMV）
- **1.64× → 1.16×**：素材 ROI 差距从脏数据误报到修正后——直接反转经营判断
- **32/32**：故障注入组合矩阵全绿，且首战当场抓出一个真产品 bug
- **265 项**：工资表机器闸门重算，Must Fix 清空才允许打款

---

*注：本仓库为脱敏版（去店名/人名/部分绝对值）。联系我可见内部 receipts 与可运行的机器刀演示。*
