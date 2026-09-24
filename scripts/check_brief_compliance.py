#!/usr/bin/env python3
"""
check_brief_compliance.py — brief 注入结果复核 + 合规机器校验（蔡氏福宁·日用品红线）

用法:
  python3 check_brief_compliance.py <html_file> [--json <data_file>]

数据源优先级: --json 文件 > HTML 内 window.__BRIEF_DATA（通道1）

四项检查（判定权在本脚本，AI 不得以"语境合理"自行豁免 FAIL）:
  1. 注入复核     — 数据可解析且非空字段 > 0，否则 FAIL
  2. 占位符残留   — 字段值含 XXX/TBD/TODO/待补充/[生成内容] 等模板残留 → FAIL
  3. 禁用词扫描   — 硬禁用（医疗宣称/承诺/贬低，源自 SKILL 合规规范表）→ FAIL
                    极限词（最/第一/唯一/独家/100%/彻底/完全/绝对）→ WARN（逐条呈现审核人裁决）
  4. 免责声明     — 注意事项(f-s-notice)已填写时必须包含日用品免责句 → FAIL

标准免责句本身含"预防/治疗"字样，扫描前自动剔除，不算命中。

输出协议:
  PASS: N fields checked, ...   （退出码 0，允许有 WARN 但必须列出）
  FAIL: <field_id> <检查类别> <命中词>   （退出码 1）
  ERROR: <原因>                 （退出码 2）
"""

import json
import re
import sys

# 硬禁用词（FAIL）：治疗宣称/疾病关联/预防宣称/诊断宣称/承诺性/比较性贬低 —— 与 SKILL.md 合规规范表同源
HARD_BANNED = [
    "治疗", "治愈", "疗程", "疗效", "根治", "祛除", "药到病除",
    "消炎", "抗菌", "杀菌", "抗病毒",
    "增强免疫力", "提高抵抗力", "预防疾病",
    "诊断", "筛查",
    "保证有效", "绝对有效", "肯定有效", "必定有效",
    "远胜于", "碾压", "智商税", "秒杀",
]
# 极限词（WARN，需人工裁决）：负向预查排除常见合法用法（最近/最终/初始/最后/首先/最初）
WARN_PATTERNS = [
    (r"最(?!近|终|初|后|先|低配|高配)", "最"),
    (r"第一(?!次|天|步|阶段)", "第一"),
    (r"唯一", "唯一"),
    (r"独家", "独家"),
    (r"100%", "100%"),
    (r"彻底", "彻底"),
    (r"完全", "完全"),
    (r"绝对(?!值)", "绝对"),
]
PLACEHOLDER_PATTERNS = ["XXX", "xxx", "TBD", "TODO", "待补充", "[生成内容]", "字段A", "字段B"]
DISCLAIMER = "不具有疾病预防、治疗功能"
DISCLAIMER_RE = r"本品(属于|为)日用品[，,]?[^。]*(不可替代药品或医疗器械|非药品)?"

usage = "用法: python3 check_brief_compliance.py <html_file> [--json <data_file>]"


def load_data(argv):
    html_path = argv[0]
    json_path = None
    if "--json" in argv:
        i = argv.index("--json")
        if i + 1 < len(argv):
            json_path = argv[i + 1]
    if json_path:
        with open(json_path, encoding="utf-8") as f:
            return json.load(f)
    with open(html_path, encoding="utf-8") as f:
        html = f.read()
    m = re.search(r"window\.__BRIEF_DATA=(\{.+?\});window", html, re.DOTALL)
    if not m:
        print("ERROR: no window.__BRIEF_DATA found in HTML — injection missing")
        sys.exit(2)
    return json.loads(m.group(1))


def scan_fields(data):
    fails, warns = [], []
    fields = data.get("fields", {})
    checked = 0
    for fid, val in fields.items():
        if not val or not str(val).strip():
            continue
        checked += 1
        text = str(val)
        # 检查2：占位符残留
        for p in PLACEHOLDER_PATTERNS:
            if p in text:
                fails.append(f"FAIL: {fid} 占位符残留 「{p}」")
        # 检查3：禁用词（先剔除标准免责句防自伤误报）
        clean = re.sub(DISCLAIMER_RE, "", text)
        for w in HARD_BANNED:
            if w in clean:
                idx = clean.find(w)
                ctx = clean[max(0, idx - 8): idx + len(w) + 8]
                fails.append(f"FAIL: {fid} 禁用词 「{w}」 …{ctx}…")
        for pat, label in WARN_PATTERNS:
            for m in re.finditer(pat, clean):
                idx = m.start()
                ctx = clean[max(0, idx - 8): idx + len(m.group(0)) + 8]
                warns.append(f"WARN: {fid} 极限词 「{label}」 …{ctx}… （呈现审核人裁决）")
    # 检查4：免责声明
    notice = str(fields.get("f-s-notice", "")).strip()
    if notice and DISCLAIMER not in notice:
        fails.append("FAIL: f-s-notice 缺日用品免责声明（须含「本品属于日用品，不具有疾病预防、治疗功能…」）")
    return checked, fails, warns


def main():
    if len(sys.argv) < 2:
        print(usage)
        sys.exit(2)
    try:
        data = load_data(sys.argv[1:])
    except FileNotFoundError as e:
        print(f"ERROR: file not found: {e}")
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON parse failed: {e}")
        sys.exit(2)

    checked, fails, warns = scan_fields(data)
    for line in fails:
        print(line)
    for line in warns:
        print(line)
    if checked == 0:
        print("ERROR: 0 non-empty fields — nothing injected")
        sys.exit(2)
    if fails:
        print(f"RESULT: FAIL（{len(fails)} 项硬违规，{len(warns)} 项待裁决极限词）——整改后重跑")
        sys.exit(1)
    print(f"PASS: {checked} fields checked, 0 hard-banned, {len(warns)} warn（WARN项需审核人逐条确认）")
    sys.exit(0)


if __name__ == "__main__":
    main()
