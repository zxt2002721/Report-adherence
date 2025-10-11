# report_modules/common/html_base.py

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from jinja2 import Environment, BaseLoader, ChainableUndefined
from markdown import markdown
import json

class HTMLBaseGenerator:
    """HTML生成基础类 - 提供通用批注和交互功能"""
    
    # ==================== 通用CSS样式 ====================
    
    BASE_STYLES = """
/* 优化后：添加注释分组 */
:root {
    /* 色彩 - 文本与背景 (Colors - Text & Background) */
    --fg: #222;
    --fg-soft: #444;
    --bg: #fff;
    --muted: #888;
    
    /* 色彩 - 语义 (Colors - Semantic) */
    --pri: #2e7d32;       /* 主要颜色，如成功 */
    --pri-weak: #e9f5eb;  /* 主要颜色的弱化背景 */
    --warn: #c62828;      /* 警告/危险色 */
    --bar: #0f766e;       /* 用于边框、强调条等 */
    
    /* 色彩 - UI组件 (Colors - UI Components) */
    --card: #f6f7f9;      /* 卡片背景 */
    --border: #ddd;       /* 边框 */
    --btn: #0ea5e9;       /* 按钮主色 */
    --btn-hover: #0284c7; /* 按钮悬浮色 */
}

html,body { margin:0; padding:0; background:var(--bg); color:var(--fg); 
    font-family:"Noto Sans CJK SC","Microsoft YaHei","PingFang SC",Arial; }
body { font-size:14.5px; line-height:1.6; }
.page-container { max-width:1100px; margin:0 auto; padding:16px 20px 80px; }
.meta { color:var(--fg-soft); margin-bottom:12px; }
h1,h2,h3,h4 { color:#111; margin:.7em 0 .45em; position:relative; }
table { border-collapse:collapse; width:100%; margin:.4em 0 .8em; }
th,td { border:1px solid #ccc; padding:6px 8px; vertical-align:top; }
th { background:#f6f7f9; }
blockquote { color:#555; margin:.6em 0; padding-left:.8em; border-left:3px solid #ddd; }
img { max-width:100%; }
hr { border: 0; border-top: 1px solid #eee; margin: 1em 0; }

/* 批注工具条（通用） */
.anno-toolbar {
    position:fixed; left:50%; transform:translateX(-50%);
    bottom:16px; z-index:9999; display:flex; gap:8px; align-items:center;
    background:linear-gradient(90deg,#0ea5e9,#06b6d4); color:#fff;
    padding:10px 12px; border-radius:14px; box-shadow:0 8px 20px rgba(0,0,0,.15);
}
.anno-toolbar button, .anno-toolbar label.btn {
    appearance:none; border:0; border-radius:10px; padding:8px 10px; cursor:pointer; 
    font-weight:600; background:#ffffff; color:#0b3b48; transition:all .15s ease;
    box-shadow:0 2px 6px rgba(0,0,0,.12);
}
.anno-toolbar button:hover, .anno-toolbar label.btn:hover { transform:translateY(-1px); }
.anno-toolbar .sep { width:1px; height:20px; background:rgba(255,255,255,.6); margin:0 4px; }
.hidden-input { display:none; }

/* 批注按钮（通用） */
.add-note-btn {
    display:none; position:absolute; right:-4px; top:50%; transform:translate(100%,-50%);
    background:var(--btn); color:#fff; border:0; padding:3px 8px; border-radius:10px; 
    font-size:12px; cursor:pointer;
}
.add-note-btn:hover { background:var(--btn-hover); }

/* 章节交互工具（通用容器） */
.section-tools {
    display:inline-flex; gap:8px; align-items:center; margin-left:8px; 
    transform:translateY(-1px); flex-wrap: wrap;
}
.section-tools select, .section-tools input[type="checkbox"] {
    font-size:12px; padding:2px 6px;
}
.section-tools .chip {
    font-size:12px; padding:2px 8px; border:1px solid var(--border); 
    border-radius:10px; background:#fff;
}
.section-tools .btn-mini {
    font-size:12px; padding:2px 8px; border:1px solid var(--border); 
    border-radius:10px; background:#fff; cursor:pointer;
}
.section-tools .btn-mini:hover { background:#f1f5f9; }

/* 批注卡片（通用） */
.anno-card {
    background:var(--card); border:1px solid var(--border); 
    border-left:4px solid var(--bar); border-radius:12px; padding:10px; 
    margin:8px 0 12px;
}
.anno-card .anno-head { 
    display:flex; justify-content:space-between; align-items:center; 
    margin-bottom:6px; color:var(--fg-soft); font-size:12px; 
}
.anno-card .anno-body[contenteditable="true"] {
    min-height:48px; padding:6px 8px; border-radius:8px; background:#fff; 
    border:1px dashed #cbd5e1; outline:none;
}
.anno-card .anno-actions { text-align:right; margin-top:6px; }
.anno-card .anno-actions button {
    background:#fff; border:1px solid #cbd5e1; border-radius:8px; 
    padding:4px 8px; cursor:pointer; margin-left:6px;
}
.anno-card .anno-actions button:hover { background:#f1f5f9; }

/* 全局批注（通用） */
.global-anno {
    background:#fff; border:1px solid var(--border); border-radius:14px; 
    padding:12px; margin:10px 0 18px; box-shadow:0 2px 10px rgba(0,0,0,.06);
}
.global-anno h3 { margin-top:0; }
.global-anno .area { 
    width:100%; min-height:68px; resize:vertical; padding:8px; 
    border-radius:10px; border:1px solid #cbd5e1; 
}
.global-anno .actions { text-align:right; margin-top:6px; }
.muted { color:var(--muted); font-size:12px; }

@media print {
    .anno-toolbar { display:none!important; }
    .add-note-btn { display:none!important; }
    .section-tools { display:none!important; }
    .page-container { padding-bottom:0; }
    .global-anno { box-shadow:none; border:1px solid #ccc; }
    .anno-card { page-break-inside: avoid; }
}
"""
    
    # ==================== 通用HTML外壳 ====================
    
    @staticmethod
    def build_html_shell(
        title: str,
        content: str,
        patient_id: str = "unknown",
        report_type: str = "report",
        extra_styles: str = "",
        section_kinds: Optional[List[Dict]] = None,
        triage_resources_data: Optional[Dict] = None,
        report_id: Optional[str] = None  # 🔧 新增：报告唯一标识
    ) -> str:
        """
        构建完整的HTML外壳（所有报告类型通用）
        
        Args:
            title: 页面标题
            content: HTML内容
            patient_id: 患者ID
            report_type: 报告类型（用于localStorage命名空间）
            extra_styles: 额外的CSS样式
            section_kinds: （模式A）章节类型配置
            triage_resources_data: （模式B）triage模块专属的数据
            report_id: 报告唯一标识（默认使用时间戳）
        
        Returns:
            str: 完整的HTML字符串
        """
        if report_id is None:
            report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        section_kinds_js = json.dumps(section_kinds) if section_kinds else "[]"
        
        
        data_injection_script = ""
        if triage_resources_data:
            data_injection_script = f"""
<script>
    window.TRIAGE_RESOURCES_DATA = {{
        allResources: {triage_resources_data.get('all_resources_json', '{}')},
        suggestedIds: {triage_resources_data.get('suggested_ids_json', '[]')}
    }};
</script>
"""
        
        toolbar_html = f"""
<div class="anno-toolbar" id="annoToolbar">
    <button id="toggleAnno">关闭批注模式</button>
    <div class="sep"></div>
    <button id="exportAnno">导出批注与交互数据</button>
    <label class="btn" for="importAnnoInput">导入数据</label>
    <input id="importAnnoInput" class="hidden-input" type="file" accept="application/json" />
    <button id="clearAnno">清空本地数据</button>
    <div class="sep"></div>
    <button id="printView">打印友好</button>
</div>"""
        
        interactive_js = HTMLBaseGenerator._get_annotation_js(
            report_type=report_type,
            section_kinds_config=section_kinds_js,
            report_id=report_id  # 传递report_id
        )
        
        return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
<style>
{HTMLBaseGenerator.BASE_STYLES}
{extra_styles}
</style>
</head>
<body>
<div class="page-container" data-patient-id="{patient_id}" data-report-type="{report_type}" data-report-id="{report_id}">
    <div class="meta">生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | 报告ID：{report_id}</div>
    
    <section class="global-anno" id="global-anno">
        <h3>📝 全局批注（医生）</h3>
        <textarea class="area" id="globalAnnoArea" placeholder="在此填写整体意见；支持导出/导入与自动保存。"></textarea>
        <div class="actions muted">内容自动保存到浏览器（仅本机）。每份报告的批注独立存储。</div>
    </section>
    
    {content}
</div>

{toolbar_html}

{data_injection_script}
<script>
{interactive_js}
</script>
</body>
</html>"""
    
    # ==================== 通用批注与交互JavaScript ====================
    
    @staticmethod
    def _get_annotation_js(report_type: str, section_kinds_config: str, report_id: str) -> str:
        """完整修复版本 - 添加report_id支持 + 保存预设值"""
        return f"""
    (() => {{
    // ==================== A. 通用核心变量与函数 ====================
    const patientId = document.querySelector('.page-container')?.dataset?.patientId || 'unknown';
    const reportType = document.querySelector('.page-container')?.dataset?.reportType || '{report_type}';
    const reportId = document.querySelector('.page-container')?.dataset?.reportId || '{report_id}';
    const LS_ANNOTATIONS = `report-annotations::${{reportType}}::${{patientId}}::${{reportId}}`;
    const LS_GLOBAL = `report-annotations-global::${{reportType}}::${{patientId}}::${{reportId}}`;
    const LS_INTERACTIONS = `report-interactions::${{reportType}}::${{patientId}}::${{reportId}}`;
    let annoMode = true;

    function nowStr() {{
      const d = new Date();
      const pad = n => (n<10? '0'+n : ''+n);
      return `${{d.getFullYear()}}-${{pad(d.getMonth()+1)}}-${{pad(d.getDate())}} ${{pad(d.getHours())}}:${{pad(d.getMinutes())}}`;
    }}
    function loadJSON(key, def) {{ try {{ return JSON.parse(localStorage.getItem(key) || JSON.stringify(def)); }} catch {{ return def; }} }}
    function saveJSON(key, val) {{ localStorage.setItem(key, JSON.stringify(val || {{}})); }}
    function loadAnnotations() {{ return loadJSON(LS_ANNOTATIONS, {{}}); }}
    function saveAnnotations(data) {{ saveJSON(LS_ANNOTATIONS, data); }}
    function loadGlobal() {{ return localStorage.getItem(LS_GLOBAL) || ''; }}
    function saveGlobal(val) {{ localStorage.setItem(LS_GLOBAL, val || ''); }}
    function loadInteracts() {{ return loadJSON(LS_INTERACTIONS, {{}}); }}
    function saveInteracts(obj) {{ saveJSON(LS_INTERACTIONS, obj); }}

    // ==================== B. 资源编辑器专属逻辑 ====================
    function setupResourceEditor() {{
        if (!window.TRIAGE_RESOURCES_DATA) return;
        const {{ allResources: ALL_RESOURCES, suggestedIds: SYSTEM_SUGGESTED_IDS }} = window.TRIAGE_RESOURCES_DATA;
        let currentSelectedResourceIds = new Set();
        const STORAGE_KEY = 'triage_resources_selection';
        const editButton = document.querySelector('[data-act="edit-resources"]');
        if (!editButton) return;
        const modal = document.getElementById('resourceEditorModal');
        const modalBody = document.getElementById('resourceEditorContent');
        const displayAreaList = document.querySelector('#resource-display-area .resource-list');
        const confirmBtn = document.querySelector('.resource-modal-footer button.primary');
        const cancelBtn = document.querySelector('.resource-modal-footer button:not(.primary)');
        const closeIconBtn = document.querySelector('.resource-modal-header button');
        const countDisplay = document.querySelector('#resourceCount strong');

        function initializeState() {{
            currentSelectedResourceIds.clear();
            const store = loadInteracts();
            const savedSelection = store[STORAGE_KEY];
            if (savedSelection && Array.isArray(savedSelection)) {{
                currentSelectedResourceIds = new Set(savedSelection);
                console.log('✅ [资源] 加载已保存的选择:', savedSelection.length, '项');
            }} else {{
                currentSelectedResourceIds = new Set(SYSTEM_SUGGESTED_IDS);
                store[STORAGE_KEY] = Array.from(currentSelectedResourceIds);
                saveInteracts(store);
                console.log('✅ [资源] 使用系统推荐并已保存:', SYSTEM_SUGGESTED_IDS.length, '项');
            }}
        }}

        function updateCounter() {{
            const count = modalBody.querySelectorAll('input:checked').length;
            if(countDisplay) countDisplay.textContent = count;
        }}

        function openResourceEditor() {{
            initializeState();
            modalBody.innerHTML = '';
            Object.entries(ALL_RESOURCES).forEach(([category, resources]) => {{
                const categoryTitle = document.createElement('h4');
                categoryTitle.textContent = category;
                modalBody.appendChild(categoryTitle);
                resources.forEach(item => {{
                    const label = document.createElement('label');
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.value = item.id;
                    checkbox.checked = currentSelectedResourceIds.has(item.id);
                    checkbox.onchange = updateCounter;
                    label.appendChild(checkbox);
                    label.append(` ${{item.name}}`);
                    if(SYSTEM_SUGGESTED_IDS.includes(item.id)) {{
                        const badge = document.createElement('span');
                        badge.className = 'system-badge';
                        badge.textContent = '[系统推荐]';
                        label.appendChild(badge);
                    }}
                    modalBody.appendChild(label);
                }});
            }});
            updateCounter();
            modal.style.display = 'flex';
            document.body.classList.add('modal-open');
        }}

        function closeResourceEditor() {{
            modal.style.display = 'none';
            document.body.classList.remove('modal-open');
        }}

        function saveResourceSelection() {{
            currentSelectedResourceIds = new Set(Array.from(modalBody.querySelectorAll('input:checked')).map(cb => cb.value));
            const store = loadInteracts();
            store[STORAGE_KEY] = Array.from(currentSelectedResourceIds);
            saveInteracts(store);
            console.log('💾 [资源] 已保存选择:', store[STORAGE_KEY].length, '项');
            renderDisplayArea();
            closeResourceEditor();
        }}
        
        function renderDisplayArea() {{
            if(!displayAreaList) return;
            displayAreaList.innerHTML = '';
            const selectedByCategory = {{}};
            const allResourcesFlat = Object.values(ALL_RESOURCES).flat();
            currentSelectedResourceIds.forEach(id => {{
                const item = allResourcesFlat.find(i => i.id === id);
                if(item) {{
                    const category = item.category || '未分类';
                    if (!selectedByCategory[category]) selectedByCategory[category] = [];
                    selectedByCategory[category].push(item);
                }}
            }});
            if (Object.keys(selectedByCategory).length === 0) {{
                displayAreaList.innerHTML = '<li>医生未选择任何资源。</li>';
                return;
            }}
            Object.entries(selectedByCategory).forEach(([categoryName, items]) => {{
                const li = document.createElement('li');
                li.innerHTML = `<strong>${{categoryName}}:</strong> `;
                items.forEach(item => {{
                    const span = document.createElement('span');
                    span.className = 'resource-item';
                    if (!SYSTEM_SUGGESTED_IDS.includes(item.id)) span.classList.add('added-by-user');
                    span.textContent = item.name;
                    li.appendChild(span);
                }});
                displayAreaList.appendChild(li);
            }});
        }}
        
        if (editButton) editButton.addEventListener('click', openResourceEditor);
        if (confirmBtn) confirmBtn.addEventListener('click', saveResourceSelection);
        if (cancelBtn) cancelBtn.addEventListener('click', closeResourceEditor);
        if (closeIconBtn) closeIconBtn.addEventListener('click', closeResourceEditor);
        initializeState();
        renderDisplayArea();
    }}

    // ==================== C. 通用批注与交互逻辑 ====================
    const SectionKindMap = {section_kinds_config};

    function setupSectionAnchors() {{
      const headers = document.querySelectorAll('h1, h2, h3, h4');
      headers.forEach((h, idx) => {{
        if (!h.id) {{
            const text = h.textContent.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '').substring(0, 15);
            h.id = text ? `sec-${{text}}-${{idx}}` : `sec-${{idx}}`;
        }}
        const btn = document.createElement('button');
        btn.className = 'add-note-btn';
        btn.textContent = '➕ 批注';
        btn.addEventListener('click', () => createNoteCard(h.id));
        h.appendChild(btn);
      }});
    }}

    function refreshAnnoButtons() {{
      document.querySelectorAll('.add-note-btn').forEach(b => b.style.display = annoMode ? 'inline-block' : 'none');
    }}

    function renderNotes() {{
      const store = loadAnnotations();
      Object.entries(store).forEach(([secId, arr]) => {{
        const anchor = document.getElementById(secId);
        if (anchor) arr.forEach(n => insertNoteCardAfter(anchor, n));
      }});
    }}

    function createNoteCard(secId) {{
      const payload = {{ id: `n-${{Date.now()}}`, ts: nowStr(), html: '' }};
      const store = loadAnnotations();
      (store[secId] = store[secId] || []).push(payload);
      saveAnnotations(store);
      const anchor = document.getElementById(secId);
      if (anchor) insertNoteCardAfter(anchor, payload, true);
    }}

    function insertNoteCardAfter(anchorEl, note, focus=false) {{
      const card = document.createElement('div');
      card.className = 'anno-card';
      card.dataset.noteId = note.id;
      card.dataset.secId = anchorEl.id;
      card.innerHTML = `<div class="anno-head"><div>章节：<code>${{anchorEl.textContent.replace('➕ 批注','').trim()}}</code></div><div>时间：${{note.ts}}</div></div><div class="anno-body" contenteditable="true" spellcheck="false">${{note.html || ''}}</div><div class="anno-actions"><button data-act="del">删除</button></div>`;
      const body = card.querySelector('.anno-body');
      body.addEventListener('input', () => {{
        const store = loadAnnotations();
        const item = (store[card.dataset.secId] || []).find(x => x.id === card.dataset.noteId);
        if (item) {{ item.html = body.innerHTML; saveAnnotations(store); }}
      }});
      card.querySelector('[data-act="del"]').addEventListener('click', () => {{
        const store = loadAnnotations();
        let list = store[card.dataset.secId] || [];
        store[card.dataset.secId] = list.filter(x => x.id !== card.dataset.noteId);
        saveAnnotations(store);
        card.remove();
      }});
      anchorEl.parentNode.insertBefore(card, anchorEl.nextSibling);
      if (focus) body.focus();
    }}

    function injectToolsHTML() {{
      if (!SectionKindMap || SectionKindMap.length === 0) return;
      const headers = document.querySelectorAll('h1, h2, h3, h4');
      headers.forEach(h => {{
          const titleText = (h.textContent || '').replace(/[\\s➕批注]/g, '');
          const config = SectionKindMap.find(m => m.includes && m.includes.some(k => titleText.includes(k)));
          if (config && config.tools_html) {{
              const wrap = document.createElement('span');
              wrap.className = 'section-tools';
              wrap.innerHTML = config.tools_html;
              h.appendChild(wrap);
          }}
      }});
    }}

    function activateInteractiveElements() {{
        const store = loadInteracts();
        let hasNewValues = false;
        
        document.querySelectorAll('[data-k]').forEach(el => {{
            let header = el.closest('h1, h2, h3, h4');
            if (!header) {{
                const wrapper = el.closest('.decision-interactive, .physician-approval-form');
                if (wrapper && wrapper.previousElementSibling?.matches('h1, h2, h3, h4')) {{
                    header = wrapper.previousElementSibling;
                }}
            }}
            
            if (!header) {{
                console.warn('⚠️ [交互] 无法找到标题，跳过元素:', el.dataset.k);
                return;
            }}
            
            const k = `${{header.id}}::${{el.dataset.k}}`;
            const savedValue = store[k];
            
            let currentValue;
            if (el.tagName === 'SELECT') {{
                currentValue = el.value;
            }} else if (el.type === 'checkbox') {{
                currentValue = el.checked;
            }} else if (el.type === 'radio') {{
                if (el.checked) {{
                    currentValue = el.value;
                }}
            }} else if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {{
                currentValue = el.value;
            }}
            
            if (savedValue !== undefined) {{
                if (el.tagName === 'SELECT') {{
                    el.value = savedValue;
                    console.log('🔄 [交互] 恢复下拉框:', k, '=', savedValue);
                }} else if (el.type === 'checkbox') {{
                    el.checked = !!savedValue;
                    console.log('🔄 [交互] 恢复复选框:', k, '=', savedValue);
                }} else if (el.type === 'radio') {{
                    if (el.value === savedValue) {{
                        el.checked = true;
                        console.log('🔄 [交互] 恢复单选框:', k, '=', savedValue);
                    }}
                }} else if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {{
                    el.value = savedValue;
                    console.log('🔄 [交互] 恢复输入框:', k, '=', savedValue);
                }}
            }} else if (currentValue !== '' && currentValue !== undefined) {{
                store[k] = currentValue;
                hasNewValues = true;
                console.log('💾 [交互] 保存预设值:', k, '=', currentValue);
            }}
            
            el.addEventListener('change', () => {{
                const cur = loadInteracts();
                if (el.type === 'checkbox') {{
                    cur[k] = el.checked;
                }} else if (el.type === 'radio') {{
                    cur[k] = el.value;
                }} else {{
                    cur[k] = el.value;
                }}
                saveInteracts(cur);
                console.log('💾 [交互] 保存:', k, '=', cur[k]);
            }});
        }});
        
        if (hasNewValues) {{
            saveInteracts(store);
            console.log('✅ [交互] 已保存所有预设值到localStorage');
        }}
    }}

    function setupPathSwitching() {{
        const switcher = document.querySelector('.path-switcher-select');
        const pathYes = document.getElementById('path-immediate-care');
        const pathNo = document.getElementById('path-home-observation');
        if (!switcher || !pathYes || !pathNo) return; 
        const handleSwitch = () => {{
            pathYes.style.display = (switcher.value === 'yes') ? 'block' : 'none';
            pathNo.style.display = (switcher.value === 'no') ? 'block' : 'none';
        }};
        switcher.addEventListener('change', handleSwitch);
        handleSwitch();
    }}

    function setupToolbar() {{
      const $toggle = document.getElementById('toggleAnno'), $export = document.getElementById('exportAnno'), $import = document.getElementById('importAnnoInput'), $clear = document.getElementById('clearAnno'), $print = document.getElementById('printView'), $global = document.getElementById('globalAnnoArea');
      $global.value = loadGlobal();
      $global.addEventListener('input', () => saveGlobal($global.value));
      $toggle.addEventListener('click', () => {{
        annoMode = !annoMode;
        $toggle.textContent = annoMode ? '关闭批注模式' : '开启批注模式';
        refreshAnnoButtons();
      }});
      $export.addEventListener('click', () => {{
        const data = {{ patient_id: patientId, report_type: reportType, report_id: reportId, exported_at: nowStr(), global: $global.value || '', sections: loadAnnotations(), interactions: loadInteracts() }};
        const a = document.createElement('a');
        a.href = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], {{ type: 'application/json' }}));
        a.download = `annotations_${{reportType}}_${{patientId}}_${{reportId}}.json`;
        a.click();
        URL.revokeObjectURL(a.href);
      }});
      $import.addEventListener('change', (e) => {{
        const f = e.target.files?.[0];
        if (!f) return;
        const reader = new FileReader();
        reader.onload = () => {{
          try {{
            const data = JSON.parse(reader.result);
            if (data?.global !== undefined) saveGlobal(data.global);
            if (data?.sections) saveAnnotations(data.sections);
            if (data?.interactions) saveInteracts(data.interactions);
            location.reload();
          }} catch (err) {{ alert('导入失败：JSON格式不正确'); }}
        }};
        reader.readAsText(f, 'utf-8');
        e.target.value = '';
      }});
      $clear.addEventListener('click', () => {{
        if (confirm('确定清空本报告的所有本地数据吗？')) {{
            localStorage.removeItem(LS_ANNOTATIONS);
            localStorage.removeItem(LS_GLOBAL);
            localStorage.removeItem(LS_INTERACTIONS);
            location.reload();
        }}
      }});
      $print.addEventListener('click', () => window.print());
    }}

    document.addEventListener('DOMContentLoaded', () => {{
        setupSectionAnchors();
        injectToolsHTML();
        activateInteractiveElements();
        setupPathSwitching();
        setupResourceEditor();
        renderNotes();
        setupToolbar();
        refreshAnnoButtons();
    }});

    }})();"""
    
    # ==================== Markdown渲染 ====================
    
    @staticmethod
    def render_markdown_template(template_path: Path, context: dict) -> str:
        """渲染Markdown模板为HTML"""
        if not template_path.exists():
            raise FileNotFoundError(f"模板文件不存在: {template_path}")
        
        env = Environment(loader=BaseLoader(), autoescape=False, undefined=ChainableUndefined)
        tpl = template_path.read_text(encoding="utf-8")
        md = env.from_string(tpl).render(**context)
        return markdown(md, extensions=["tables", "fenced_code"])

