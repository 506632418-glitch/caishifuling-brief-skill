#!/usr/bin/env python3
"""
brief_inject.py — 将 brief 数据注入 HTML 文件的 localStorage 预加载脚本

用法:
  python3 brief_inject.py <html_file> [json_data_file] [--section N]

如果省略 json_data_file，默认读取 /tmp/brief_data.json

板块闸口（v1.9.1 起防跳板块；v1.9.9 起接状态机）:
  阶段1逐板块注入必须带 --section N（N=1..8），此时 JSON 必须含 progress 状态，
  脚本按四条规则校验，硬规则不满足即输出 ERROR: GATE-* 并以非零退码拒绝写入：
    G1 连续性（硬拦）：1..N-1 全部在 progress.confirmed（progress.skipped 中的豁免）
    G2 当前确认（硬拦）：N 本身必须在 progress.confirmed（审核人没确认的板块不许注入）
    G3 重开须留痕（硬拦，v1.9.9 新）：N 之后仍有已确认板块 ⇒ 判定为「重开已确认板块」
       （🟡级操作），必须在 progress.revisions 中存在 section==N 且 closed_at 为空的
       留痕记录，否则 ERROR: GATE-REOPEN-UNTRACKED。放行时附「下游待裁决项」提醒。
    G4 账一致性体检（仅 WARN）：pending 未清 / 已闭环 revisions 缺 downstream_resolved
       裁决记录 —— 只提醒不拦截。
  不带 --section = 旧版全量注入模式（阶段0初始化/历史数据兼容），不触发闸口。

  注：progress 为「账」，六态由账派生（SKILL.md §板块状态机）。脚本只读账、写 HTML，
  ⛔ 不改 JSON —— revisions/pending 的写入由 AI 按 SKILL.md 步骤B 执行。

JSON 数据结构示例:
{
  "fields": {
    "f-s-name": "蔡氏福宁·泡脚包",
    "f-s-category": "中药泡脚",
    "f-ing-1-name": "艾叶",
    ...
  },
  "struct": {
    "ingCount": 2,
    "personaCount": 1,
    "sceneCount": 3,
    "popCount": 2,
    "podCount": 2,
    "compCount": 3,
    "qaCount": 2
  },
  "progress": {
    "confirmed": [1, 2, 3],
    "skipped": [],
    "pending": null,
    "revisions": [
      {"section": 2, "reason": "POD 优势句改写（去竞品名）",
       "downstream_check": [3], "downstream_resolved": [{"section": 3, "decision": "确认无影响"}],
       "opened_at": "2026-09-28 17:05", "closed_at": "2026-09-28 17:16"}
    ]
  }
}
（v1.9.9 起 progress 不再含 current —— 它是派生量，由 confirmed ∪ skipped 推导）
"""

import json
import sys
import base64
import re
import os

STORAGE_KEY = "caishifuling_brief_v6"


def check_section_gate(data, section, json_path):
    """板块闸口（v1.9.9 接状态机）：
    G1连续性 / G2当前确认 → 硬拦；G3重开须留痕 → 硬拦；G4账一致性体检 → 仅 WARN。
    判定权在脚本，AI 不得以任何理由豁免。
    """
    progress = data.get("progress")
    if not isinstance(progress, dict):
        print(f"ERROR: GATE-NO-PROGRESS 注入板块{section}需要 {json_path} 内含 progress 字段"
              f"（confirmed/skipped/pending/revisions），请先按 SKILL.md 步骤B 更新进度再注入")
        sys.exit(1)
    confirmed = sorted(set(progress.get("confirmed", [])))
    skipped = set(progress.get("skipped", []))
    pending = progress.get("pending")
    revisions = progress.get("revisions") or []
    if not isinstance(revisions, list):
        revisions = []

    # --- G1 连续性（硬拦）---
    missing_before = [n for n in range(1, section) if n not in confirmed and n not in skipped]
    if missing_before:
        print(f"ERROR: GATE-FAIL 板块{section}注入被拒：前序板块 {missing_before} 未确认"
              f"（confirmed={confirmed} skipped={sorted(skipped)}），不许跳板块")
        sys.exit(1)

    # --- G2 当前确认（硬拦）---
    if section not in confirmed:
        print(f"ERROR: GATE-FAIL 板块{section}尚未确认，不许注入——先完成步骤A审核人确认，"
              f"将其计入 progress.confirmed")
        sys.exit(1)

    # --- G3 重开须留痕（v1.9.9：原「补正通道 WARN」升级为硬拦）---
    # 重开判据：section 之后仍有已确认板块（section < max(confirmed)）。
    # 正常推进时 N 恒为最新确认板块，不会进入此分支；进入即说明是「修改已确认板块」。
    future = [n for n in confirmed if n > section]
    if future:
        open_revs = [
            r for r in revisions
            if isinstance(r, dict) and r.get("section") == section and not r.get("closed_at")
        ]
        if not open_revs:
            print(
                f"ERROR: GATE-REOPEN-UNTRACKED 板块{section}被判定为「重开已确认板块」"
                f"（其后已确认板块 {future}），但 progress.revisions 中没有该板块未闭环的留痕记录。\n"
                f"  重开＝🟡级操作（SKILL.md §板块状态机 · T4），须先审核人明示同意，"
                f"再于注入前写入 revisions：\n"
                f"    {{\"section\": {section}, \"reason\": \"<改什么+为什么，禁空话>\", "
                f"\"downstream_check\": {future}, \"downstream_resolved\": [], "
                f"\"opened_at\": \"<YYYY-MM-DD HH:MM>\", \"closed_at\": null}}"
            )
            sys.exit(1)
        r = open_revs[-1]
        dc = list(r.get("downstream_check") or [])
        resolved = {
            x.get("section")
            for x in (r.get("downstream_resolved") or [])
            if isinstance(x, dict)
        }
        unmet = [n for n in dc if n not in resolved]
        msg = (f"WARN: 板块{section}走重开通道（其后已确认板块 {future}）——"
               f"已登记 revisions（opened_at={r.get('opened_at') or '未填'}）")
        if unmet:
            msg += f"；⏳下游待裁决: {unmet}（闭环前须逐项裁决并写入 downstream_resolved）"
        elif dc:
            msg += f"；下游 {dc} 均已裁决，本轮可填 closed_at 闭环"
        else:
            msg += "；本轮可填 closed_at 闭环"
        print(msg)

    # --- G4 账一致性体检（仅 WARN，不拦截）---
    if pending not in (None, "", []) and pending != section:
        print(f"WARN: 账上 pending={pending}（有已呈报未裁决的板块），本次注入的是板块{section}"
              f"——请确认是否应先收尾板块{pending}")
    for r in revisions:
        if not isinstance(r, dict) or not r.get("closed_at"):
            continue
        dc = list(r.get("downstream_check") or [])
        resolved = {
            x.get("section")
            for x in (r.get("downstream_resolved") or [])
            if isinstance(x, dict)
        }
        unmet = [n for n in dc if n not in resolved]
        if unmet:
            print(f"WARN: revisions 板块{r.get('section')} 已闭环"
                  f"（closed_at={r.get('closed_at')}）但 downstream_check {unmet} 无裁决记录"
                  f"——请补 downstream_resolved（SKILL.md §板块状态机 · T5）")


def main():
    args = sys.argv[1:]
    section = None
    if "--section" in args:
        i = args.index("--section")
        if i + 1 >= len(args):
            print("ERROR: --section 需要一个数字参数（1..8）")
            sys.exit(1)
        try:
            section = int(args[i + 1])
        except ValueError:
            print(f"ERROR: --section 参数非数字: {args[i + 1]}")
            sys.exit(1)
        if not 1 <= section <= 8:
            print(f"ERROR: --section 超出板块范围 1..8: {section}")
            sys.exit(1)
        args = args[:i] + args[i + 2:]

    html_path = args[0] if len(args) > 0 else None
    json_path = args[1] if len(args) > 1 else "/tmp/brief_data.json"
    if html_path is None:
        print("用法: python3 brief_inject.py <html_file> [json_data_file] [--section N]")
        sys.exit(1)

    if not os.path.exists(json_path):
        print(f"ERROR: JSON data file not found: {json_path}")
        sys.exit(1)

    if not os.path.exists(html_path):
        print(f"ERROR: HTML file not found: {html_path}")
        sys.exit(1)

    # Read JSON data
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "fields" not in data:
        data = {"fields": data, "struct": {}}

    # === 板块闸口（v1.9.1 防跳板块，判定权在脚本） ===
    if section is not None:
        check_section_gate(data, section, json_path)

    # Count non-empty fields for verification
    filled_count = sum(1 for v in data.get("fields", {}).values() if v and str(v).strip())

    # Build inject script — TWO-PATH approach for maximum compatibility:
    # Path 1 (primary): window.__BRIEF_DATA — direct JS variable, works in ALL environments
    #   including WorkBuddy embedded webview where localStorage may be disabled.
    # Path 2 (fallback): localStorage.setItem — for data persistence across page refreshes.
    # The init code checks window.__BRIEF_DATA first, then localStorage.
    json_str_compact = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    b64 = base64.b64encode(json_str_compact.encode("utf-8")).decode("ascii")
    inject = (
        '<script id="brief-preload">'
        # === Path 1: Direct JS variable (no localStorage dependency) ===
        "window.__BRIEF_DATA=" + json_str_compact + ";"
        'window.__brief_preload_ok=true;'
        # === Path 2: localStorage (for persistence) ===
        "(function(){"
        "try{"
        f'var s=atob("{b64}");'
        'var b=new Uint8Array(s.length);'
        'for(var i=0;i<s.length;i++)b[i]=s.charCodeAt(i);'
        "var j=new TextDecoder('utf-8').decode(b);"
        "var d=JSON.parse(j);"
        f'localStorage.setItem("{STORAGE_KEY}",JSON.stringify(d));'
        '}catch(e){'
        "console.warn('brief-preload localStorage fallback failed (may be normal in embedded webview):',e.message);"
        "}"
        "})();"
        "</script>"
    )

    # Read HTML
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Remove old preload script if it exists
    html = re.sub(
        r'<script id="brief-preload">.*?</script>',
        "",
        html,
        flags=re.DOTALL,
    )

    # Inject before </body>
    if "</body>" not in html:
        print("ERROR: </body> tag not found in HTML")
        sys.exit(1)

    html = html.replace("</body>", inject + "\n</body>")

    # Write back
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    # Output verification info
    struct_counts = data.get("struct", {})
    print(
        f"OK: {filled_count} fields injected "
        f"(ing:{struct_counts.get('ingCount',0)} "
        f"persona:{struct_counts.get('personaCount',0)} "
        f"scene:{struct_counts.get('sceneCount',0)} "
        f"comp:{struct_counts.get('compCount',0)} "
        f"pop:{struct_counts.get('popCount',0)} "
        f"pod:{struct_counts.get('podCount',0)} "
        f"qa:{struct_counts.get('qaCount',0)})"
    )


if __name__ == "__main__":
    main()
