# brief工具HTML 填写操作指南

## 工具文件

- 主文件：Skill 目录下的 `蔡氏福宁_产品brief_填写工具.html`
- 建议：填写前先备份，另存为 `蔡氏福宁_产品brief_[产品名].html`

## 操作方式

由于brief工具是纯前端HTML（数据存储在DOM中，无后端），填写方式为：

### ☑SHOULD 方案A（推荐）：生成Markdown → 通过「导入Markdown」功能填入

1. AI在阶段1确认所有内容后，生成符合导入格式的Markdown
2. 审核人在浏览器打开brief工具 → 点击「导入Markdown」→ 粘贴 → 确认导入
3. 优势：最小化HTML操作风险，审核人可直接在工具中预览和微调

**Markdown导入格式**：详见brief工具HTML中 `importMarkdownFromText` 函数的解析逻辑。基本格式为：
```markdown
# 产品名称
蔡氏福宁·XXX

## 战略层
- 产品名称: 蔡氏福宁·XXX
- 品类定义: XXX
- 产品规格: XXX
- 战略角色: 引流款
- 角色理由: XXX

## 心智层
- 产品口号: XXX
- 口号方向: 核心卖点直给
- 产品口播: XXX

... (依此类推，按版块组织)
```

### ✔MAY 方案B（备用）：直接编辑HTML DOM

如果方案A不可用，AI通过bash操作HTML文件修改 `value` 属性。但由于这是交互式网页（动态创建DOM元素），直接修改HTML源码的初始值不一定有效（初始模板可能无预设值）。

**如需方案B**，AI应该：
1. 读取完整的JS初始化逻辑（`addIngredient()`/`addCompetitor()` 等函数）
2. 确认每个动态组件创建时的默认 `value` 如何设置
3. 如初始模板无预设值，则需要修改JS逻辑或改用方案A

## Markdown导出格式解析

brief工具中 `generateMarkdown()` 和 `exportMarkdown()` 函数定义了导出格式。导入也用相同格式解析。AI生成的Markdown必须严格遵循此格式。

关键格式要素：
- 用 `# 标题` 表示产品名称
- 用 `## 版块名` 表示版块
- 用 `- 字段名: 内容` 表示普通字段
- 动态列表（成分/竞品/人群/场景/POP/POD/QA）使用编号格式

> ⚠️ AI在阶段2应优先导出Markdown内容，让审核人在brief工具中通过「导入Markdown」功能填入，避免直接修改HTML文件导致意外损坏。
