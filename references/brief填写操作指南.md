# brief工具HTML 填写操作指南

## 核心原则

- **原始模板永不修改**。Skill 目录下的 `蔡氏福宁_产品brief_填写工具.html` 是干净的模板源文件。
- **阶段0复制模板**：`cp [Skill目录]/蔡氏福宁_产品brief_填写工具.html [工作区]/蔡氏福宁_产品brief_[产品名].html`
- **阶段1逐版块写入**：每版块确认后，AI立即将字段值写入HTML副本。
- **所有操作针对副本**，原始模板始终可供下次使用。

## AI写入HTML的技术参考

### 静态字段写入

AI使用 `perl` 命令直接修改HTML文件中的字段值。

> ⚠️ **特殊字符与多行内容处理**：字段内容必须通过临时文件传入，**禁止直接拼入命令字符串**。单行用 `echo`，多行用 `cat << 'EOF'`。perl 替换使用 `/e` 修饰符，彻底杜绝内容中 `$1` 等字符被误解释为反向引用。

```bash
# === 临时文件：单行 ===
echo '填写内容' > /tmp/brief_tmp.txt

# === 临时文件：多行（使用规范、口播话术等） ===
cat > /tmp/brief_tmp.txt << 'EOF'
第一行内容
第二行内容
EOF

# === textarea 字段（/e 修饰符安全写法） ===
perl -i -0777 -pe '
  open(F,"/tmp/brief_tmp.txt"); $v=do{local $/;<F>}; close(F); chomp $v;
  s{(<textarea[^>]*id="FIELD_ID"[^>]*>)(.*?)(</textarea>)}{$1 . $v . $3}ges
' HTML_FILE

# === input 字段 ===
perl -i -0777 -pe '
  open(F,"/tmp/brief_tmp.txt"); $v=do{local $/;<F>}; close(F); chomp $v;
  s{(<input[^>]*id="FIELD_ID"[^>]*)(>)}{$1 . qq( value=") . $v . qq(") . $2}ges
' HTML_FILE

# === 动态列表 ===
# 容器ID对照：ingredient-list | competitor-list | persona-list | scene-list | pop-list | pod-list | qa-list
cat > /tmp/brief_tmp.txt << 'EOF'
HTML结构
EOF
perl -i -0777 -pe '
  open(F,"/tmp/brief_tmp.txt"); $ins=do{local $/;<F>}; close(F);
  s{(<div id="CONTAINER_ID">[\s\S]*?)(</div>)}{$1 . $ins . $2}ges
' HTML_FILE
```

适用字段说明：
- **input 字段**：f-s-name, f-s-category, f-s-spec, f-s-role-1, f-s-role-2, f-s-role-reason, f-m-slogan, f-m-slogan-type, f-m-broadcast, f-pd-color, f-pd-texture, f-pd-smell, f-pd-touch, f-pd-sensory-other, f-pd-pack-form, f-pd-pack-color, f-pd-pack-style, f-pd-pack-unbox, f-s-shelf-life, f-s-storage, f-v-pop-{n}, f-v-pod{n}-name, f-v-pod{n}-desc, f-v-pod{n}-comp
- **textarea 字段**：f-pd-mechanism, f-s-usage, f-s-notice, f-m-broadcast, f-pd-sensory-other, f-v-pod{n}-rtb, f-p-who-{n}, f-scene-{n}

### 完整字段ID对照

见 `brief工具字段对照表.md`，列出所有38个字段的ID、所属版块、是否必填。

### 动态列表HTML模板

以下模板供AI在阶段1写入动态项时使用：

```html
<!-- 核心技术/成分 — 追加到 #ingredient-list 容器结束标签前 -->
<div class="item-card ingredient-item" data-idx="N">
  <div class="item-card-header">
    <span class="item-card-label" style="color:var(--sky-800)">📌 技术N</span>
    <button type="button" class="btn btn-ghost" onclick="removeItem(this)" style="font-size:11px;padding:2px 8px;">✕ 删除</button>
  </div>
  <div class="item-card-fields">
    <input type="text" id="f-ing-N-name" placeholder="技术/成分名称" value="成分名">
    <textarea id="f-ing-N-func" placeholder="作用">作用描述</textarea>
    <input type="text" id="f-ing-N-source" placeholder="来源/依据" value="来源">
  </div>
</div>

<!-- 竞品 — 追加到 #competitor-list 容器结束标签前 -->
<div class="item-card competitor-item" data-idx="N">
  <div class="item-card-header">
    <span class="item-card-label" style="color:var(--rose-800)">📌 竞品N</span>
    <button type="button" class="btn btn-ghost" onclick="removeItem(this)" style="font-size:11px;padding:2px 8px;">✕ 删除</button>
  </div>
  <div class="item-card-fields">
    <input type="text" id="f-comp-N-name" placeholder="竞品名称" value="竞品名">
    <input type="text" id="f-comp-N-position" placeholder="定位" value="定位">
    <textarea id="f-comp-N-advantage" placeholder="优势">优势</textarea>
  </div>
</div>

<!-- 人群 — 追加到 #persona-list 容器结束标签前 -->
<div class="item-card persona-item" data-idx="N">
  <div class="item-card-header">
    <span class="item-card-label" style="color:var(--blue-800)">📌 人群N</span>
    <button type="button" class="btn btn-ghost" onclick="removeItem(this)" style="font-size:11px;padding:2px 8px;">✕ 删除</button>
  </div>
  <textarea class="tall" id="f-p-who-N" placeholder="身份标签 + 从哪来 + 要什么 / 忍不了什么">人群描述</textarea>
</div>

<!-- 场景 — 追加到 #scene-list 容器结束标签前 -->
<div class="item-card scene-item" data-idx="N">
  <div class="item-card-header">
    <span class="item-card-label" style="color:var(--blue-800)">📌 场景N</span>
    <button type="button" class="btn btn-ghost" onclick="removeItem(this)" style="font-size:11px;padding:2px 8px;">✕ 删除</button>
  </div>
  <textarea class="tall" id="f-scene-N" placeholder="场景描述">场景描述</textarea>
</div>

<!-- POP — 追加到 #pop-list 容器结束标签前 -->
<div class="item-card pop-item" data-idx="N">
  <div class="item-card-header">
    <span class="item-card-label" style="color:var(--green-800)">📌 POPN</span>
    <button type="button" class="btn btn-ghost" onclick="removeItem(this)" style="font-size:11px;padding:2px 8px;">✕ 删除</button>
  </div>
  <input type="text" id="f-v-pop-N" placeholder="品类基本盘描述" value="POP内容">
</div>

<!-- POD — 追加到 #pod-list 容器结束标签前 -->
<div class="item-card pod-item" data-idx="N">
  <div class="item-card-header">
    <span class="item-card-label" style="color:var(--green-800)">📌 POD-N</span>
    <button type="button" class="btn btn-ghost" onclick="removeItem(this)" style="font-size:11px;padding:2px 8px;">✕ 删除</button>
  </div>
  <div class="item-card-fields">
    <input type="text" id="f-v-podN-name" placeholder="差异点名称" value="POD名称">
    <textarea id="f-v-podN-desc" placeholder="FAB差异描述">差异描述</textarea>
    <input type="text" id="f-v-podN-comp" placeholder="vs竞品对比" value="竞品对比">
    <textarea id="f-v-podN-rtb" placeholder="RTB证据">证据</textarea>
  </div>
</div>

<!-- Q&A — 追加到 #qa-list 容器结束标签前 -->
<div class="item-card qa-item" data-idx="N">
  <div class="item-card-header">
    <span class="item-card-label" style="color:var(--purple-800)">📌 Q&AN</span>
    <button type="button" class="btn btn-ghost" onclick="removeItem(this)" style="font-size:11px;padding:2px 8px;">✕ 删除</button>
  </div>
  <div class="item-card-fields">
    <textarea id="f-qa-N-q" placeholder="问题">问题</textarea>
    <textarea id="f-qa-N-a" placeholder="回答">回答</textarea>
  </div>
</div>
```

> 动态项写入时使用perl追加到容器结束标签 `</div>` 之前。N按顺序递增。

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
