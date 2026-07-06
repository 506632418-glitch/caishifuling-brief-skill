#!/usr/bin/env python3
"""
brief_inject.py — 将 brief 数据注入 HTML 文件的 localStorage 预加载脚本

用法:
  python3 brief_inject.py <html_file> [json_data_file]

如果省略 json_data_file，默认读取 /tmp/brief_data.json

工作原理:
  1. 读取 JSON 数据文件
  2. Base64 编码（消除所有转义问题）
  3. 移除 HTML 中已有的旧 preload 脚本
  4. 在 </body> 前注入新脚本，页面加载时自动预填 localStorage

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
  }
}
"""

import json
import sys
import base64
import re
import os

STORAGE_KEY = "caishifuling_brief_v6"


def main():
    html_path = sys.argv[1]
    json_path = sys.argv[2] if len(sys.argv) > 2 else "/tmp/brief_data.json"

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
