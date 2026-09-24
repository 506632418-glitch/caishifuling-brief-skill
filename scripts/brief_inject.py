#!/usr/bin/env python3
"""
brief_inject.py — 将 brief 数据注入 HTML 文件的 localStorage 预加载脚本

用法:
  python3 brief_inject.py <html_file> [json_data_file] [--section N]

如果省略 json_data_file，默认读取 /tmp/brief_data.json

板块闸口（v1.9.1 起，防跳板块）:
  阶段1逐板块注入必须带 --section N（N=1..8），此时 JSON 必须含 progress 状态，
  脚本按三条规则硬校验，任一不满足输出 ERROR: GATE-FAIL* 并非零退码、拒绝写入：
    G1 连续性：1..N-1 全部在 progress.confirmed（progress.skipped 中的豁免）
    G2 当前确认：N 本身必须在 progress.confirmed（审核人没确认的板块不许注入）
    G3 超前确认：N 已确认且其后板块也已确认时输出 WARN（视为补正重注入，须审核人已同意）；
       未确认板块的超前确认由 G2 硬拦
  不带 --section = 旧版全量注入模式（阶段0初始化/历史数据兼容），不触发闸口。

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
    "current": 3,
    "confirmed": [1, 2, 3],
    "skipped": []
  }
}
"""

import json
import sys
import base64
import re
import os

STORAGE_KEY = "caishifuling_brief_v6"


def check_section_gate(data, section, json_path):
    """板块闸口：G1连续性 / G2当前确认 / G3禁预确认。不满足即退出。"""
    progress = data.get("progress")
    if not isinstance(progress, dict):
        print(f"ERROR: GATE-NO-PROGRESS 注入板块{section}需要 {json_path} 内含 progress 字段"
              f"（current/confirmed/skipped），请先按 SKILL.md 步骤B 更新进度再注入")
        sys.exit(1)
    confirmed = sorted(set(progress.get("confirmed", [])))
    skipped = set(progress.get("skipped", []))
    missing_before = [n for n in range(1, section) if n not in confirmed and n not in skipped]
    if missing_before:
        print(f"ERROR: GATE-FAIL 板块{section}注入被拒：前序板块 {missing_before} 未确认"
              f"（confirmed={confirmed} skipped={sorted(skipped)}），不许跳板块")
        sys.exit(1)
    if section not in confirmed:
        print(f"ERROR: GATE-FAIL 板块{section}尚未确认，不许注入——先完成步骤A审核人确认，"
              f"将其计入 progress.confirmed")
        sys.exit(1)
    future = [n for n in confirmed if n > section]
    if future:
        # 补正通道：N 已在 confirmed（G2 已验）且其后板块已确认 → 视为「修改已确认版块」重注入。
        # 该操作是 SKILL 可逆性分级 🟡（执行前须审核人同意），此处 WARN 留痕不拦截；
        # 若 N 未确认而 future 已确认，属超前确认造假，已被上面 G2 硬拦。
        print(f"WARN: 板块{section}为已确认板块的修改重注入（其后已确认板块 {future}）——"
              f"请确认本次修改已获审核人同意（🟡级操作）")


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

    # Base64 encode to avoid any escaping issues
    json_str = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    b64 = base64.b64encode(json_str.encode("utf-8")).decode("ascii")

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
