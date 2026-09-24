# 蔡氏福宁产品brief填写 — Skill 安装包

把产品信息文件（PDF/DOCX/XLSX/图片/企微文档）中的内容，结构化填写进「蔡氏福宁·产品brief填写工作台」（HTML 工具）。零幻觉、有据可依、逐版块确认、合规机器校验。

## 安装

1. 将整个目录放入 AI 工具的 skills 目录（如 `~/.qoder-cn/skills/` 或 WorkBuddy 技能目录），或建立软链：
   ```bash
   ln -s <本目录绝对路径> ~/.qoder-cn/skills/蔡氏福宁产品brief填写
   ```
2. 依赖：Python 3（脚本注入与合规校验用）；浏览器（查看 HTML 工作台）。
3. 文案参考案例位于 `/Users/fancy/Desktop/产品/产品信息整理集合/`（案例缺失时流程自动降级，见 SKILL.md 阶段0熔断器）。

## 使用

对 AI 说：**"产品brief填写" / "产品信息核对" / "帮我把产品信息输入到brief工具"**，附上产品信息文件。
流程：阶段0确认信息源 → 阶段1逐板块填写+确认+注入 → 阶段2交付（HTML工作台+导出MD/PDF）。

## 文件清单

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 主流程与规范（触发/铁律/三阶段/合规/风格） |
| `蔡氏福宁_产品brief_填写工具.html` | 空白模板（勿直接修改，使用时复制到工作区） |
| `scripts/brief_inject.py` | JSON→HTML 双通道注入 |
| `scripts/check_brief_compliance.py` | 合规机器校验（禁用词/占位符/免责/注入复核） |
| `references/brief工具字段对照表.md` | 全部字段 ID 与填写标准 |
| `references/brief填写操作指南.md` | JSON 数据结构与注入注意事项 |
| `references/CHANGELOG.md` | 版本历史 |
| `tests/trigger-cases.md` | 触发正负例测试集（改动后回放） |

## 贡献与反馈

- 实际使用出现误触发/漏触发/产物偏差 → 追加到 `tests/trigger-cases.md` 并更新 `references/CHANGELOG.md`
- 版本变更走 Git（本目录即仓库），改 SKILL.md 前先提交当前状态

## 版本

见 `SKILL.md` frontmatter 与 `references/CHANGELOG.md`。协议：MIT。设计者：吴凡。
