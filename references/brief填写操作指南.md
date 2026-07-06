# brief工具HTML 填写操作指南

## 核心原则

- **原始模板永不修改**。Skill 目录下的 `蔡氏福宁_产品brief_填写工具.html` 是干净的模板源文件。
- **阶段0复制模板**：`cp [Skill目录]/蔡氏福宁_产品brief_填写工具.html [工作区]/蔡氏福宁_产品brief_[产品名].html`
- **阶段1逐版块注入**：每版块确认后，AI更新JSON数据并用 `brief_inject.py` 注入HTML。
- **所有操作针对副本**，原始模板始终可供下次使用。

## 数据流向

brief工具的数据源是 **localStorage**，不是 HTML DOM。数据写入必须走以下路径：

```
AI填写 → /tmp/brief_data.json → brief_inject.py → HTML中的<script>预加载脚本
                                                          ↓
浏览器打开 → 脚本执行 → localStorage.setItem() → loadFromLocal() → 渲染字段
```

## ⛔ 防沉默失败铁律

`brief_inject.py` 输出格式为 `OK: N fields injected (ing:X persona:Y ...)`。

AI **绝对不得**在没有看到 `OK:` 输出的情况下声称"写入成功"——必须以脚本的实际输出为准。

## 写入三步流程（缺一不可）

1. **更新JSON数据** — 用 Python 读取 `/tmp/brief_data.json`，添加/更新字段值，写回
2. **注入HTML** — 运行 `brief_inject.py` 将 JSON 数据 base64 编码后注入 HTML
3. **验证输出** — 检查脚本输出是否以 `OK:` 开头

## JSON 数据格式

`/tmp/brief_data.json` 的数据结构：

```json
{
  "fields": {
    "字段ID": "填写内容",
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
```

**fields**：所有字段的 ID → 值映射。包括静态字段（如 `f-s-name`）和动态字段（如 `f-ing-1-name`）。

**struct 计数规则**：记录各类动态列表的项数。浏览器加载时，`loadFromLocal()` 根据这些计数重建表单元素：
- `ingCount` → 成分/技术项数
- `compCount` → 竞品项数
- `personaCount` → 目标人群项数
- `sceneCount` → 使用场景项数
- `popCount` → POP（品类基本盘）项数
- `podCount` → POD（差异点）项数
- `qaCount` → 常见问题项数

> ⚠️ 若 struct 计数与实际字段数量不一致，浏览器会重建错误数量的表单元素，导致部分字段显示异常。

## 完整字段ID对照

见 `brief工具字段对照表.md`，列出所有字段的ID、所属版块、是否必填。

### 字段类型说明

| 类型 | ID示例 | 说明 |
|------|--------|------|
| 静态 input | `f-s-name`, `f-pd-color`, `f-s-shelf-life` | 单行文本框 |
| 静态 textarea | `f-s-category`, `f-m-broadcast`, `f-s-usage` | 多行文本框 |
| 静态 select | `f-s-role-1`, `f-s-role-2`, `f-m-slogan-type` | 下拉选择（值填选项文本） |
| 动态成分 | `f-ing-{n}-name`, `f-ing-{n}-func`, `f-ing-{n}-source` | n 从 1 开始递增 |
| 动态竞品 | `f-comp-{n}-name`, `f-comp-{n}-position`, `f-comp-{n}-advantage` | n 从 1 开始递增 |
| 动态人群 | `f-p-who-{n}` | n 从 1 开始递增 |
| 动态场景 | `f-scene-{n}` | n 从 1 开始递增 |
| 动态POP | `f-v-pop-{n}` | n 从 1 开始递增 |
| 动态POD | `f-v-pod{n}-name`, `f-v-pod{n}-desc`, `f-v-pod{n}-comp`, `f-v-pod{n}-rtb` | n 从 1 开始递增 |
| 动态QA | `f-qa-{n}-q`, `f-qa-{n}-a` | n 从 1 开始递增 |

## brief_inject.py 使用

```bash
python3 [Skill目录]/scripts/brief_inject.py [HTML文件] [JSON数据文件]
```

若省略 JSON 文件路径，默认读取 `/tmp/brief_data.json`。

**成功输出示例**：
```
OK: 12 fields injected (ing:2 persona:1 scene:3 comp:3 pop:2 pod:2 qa:2)
```

**失败输出示例**：
```
ERROR: JSON data file not found: /tmp/brief_data.json
ERROR: HTML file not found: /path/to/html
ERROR: </body> tag not found in HTML
```

## 验证注入结果（每次注入后必须执行）

```bash
python3 -c "
import json, base64, re
with open('HTML_FILE') as f:
    html = f.read()
m = re.search(r'atob\\(\"([^\"]+)\"\\)', html)
if m:
    data = json.loads(base64.b64decode(m.group(1)))
    print(f'OK: {sum(1 for v in data[\"fields\"].values() if v and str(v).strip())} fields loaded')
else:
    print('FAIL: preload script not found')
"
```

## Markdown导入（HTML工具内置功能，备用）

HTML工具仍保留Markdown导入功能，支持两种格式：

### 格式1：AI生成格式（`- key: value`）

```markdown
## 战略层
- 产品名称: XXX
- 品类定义: XXX
```

### 格式2：HTML工具导出格式（`### 字段`）

从HTML工具自身「导出Markdown」功能生成的格式。

### 文件上传导入

1. 点击「📥 导入Markdown」
2. 点击「📂 选择 .md 文件」或粘贴内容
3. 确认导入

> ⚠️ 注意：导入前会清空当前已填内容。已有数据请先导出备份。
