/**
 * markdown.js — 轻量 Markdown → HTML 渲染器
 * 面向 wx <rich-text> 组件输出（支持 h1-h4 / p / 列表 / 粗体 / 斜体 / 行内代码 / 分割线 / 引用块）。
 */

function escapeHtml(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/** 行内格式化：**加粗** / *斜体* / `行内代码` */
function inline(md) {
  let s = escapeHtml(md)
  // 行内代码
  s = s.replace(/`([^`]+)`/g, '<code style="background:#F5F0E8;padding:2px 8px;border-radius:6px;font-size:0.9em;color:#8B5CF6;">$1</code>')
  // 加粗 — 用品牌色高亮
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong style="color:#2B2622;font-weight:700;">$1</strong>')
  // 斜体（避免误伤连续星号）
  s = s.replace(/(^|[^*])\*([^*\s][^*]*)\*/g, '$1<em style="color:#8B5CF6;">$2</em>')
  return s
}

/**
 * 将 markdown 文本转为可渲染 HTML 字符串。
 */
function render(md) {
  if (!md) return ''
  const lines = String(md).split('\n')
  let html = ''
  let inCode = false
  let olCounter = 0

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const t = line.trim()

    // 围栏代码块
    if (/^```/.test(t)) {
      inCode = !inCode
      continue
    }
    if (inCode) {
      html += `<p style="margin:6px 0;padding:10px 14px;background:#F5F0E8;border-radius:8px;color:#6E665E;font-size:0.92em;">${inline(t)}</p>`
      continue
    }

    // 空行 → 重置列表编号
    if (!t) {
      olCounter = 0
      continue
    }

    // 分割线
    if (/^(-{3,}|\*{3,}|_{3,})$/.test(t)) {
      html += '<hr style="border:none;border-top:1px dashed #E0D8CC;margin:18px 0;"/>'
      continue
    }

    // 标题
    const h = t.match(/^(#{1,4})\s+(.+)/)
    if (h) {
      const level = h[1].length
      const sizes = { 1: '32px', 2: '30px', 3: '28px', 4: '26px' }
      const margins = { 1: '20px 0 10px', 2: '18px 0 8px', 3: '16px 0 6px', 4: '14px 0 6px' }
      html += `<h${level} style="color:#2B2622;font-weight:700;line-height:1.5;margin:${margins[level] || margins[4]};font-size:${sizes[level] || sizes[4]};">${inline(h[2])}</h${level}>`
      continue
    }

    // 引用块 — 品牌色左边框高亮
    const bq = t.match(/^>\s?(.*)/)
    if (bq) {
      html += `<p style="margin:10px 0;padding:12px 16px;border-left:4px solid #F2545B;background:linear-gradient(90deg,rgba(242,84,91,0.06),rgba(139,92,246,0.03));border-radius:0 12px 12px 0;color:#2B2622;line-height:1.8;">${inline(bq[1])}</p>`
      continue
    }

    // 无序列表 — 品牌色圆点
    const ul = t.match(/^[-*+]\s+(.+)/)
    if (ul) {
      html += `<p style="margin:6px 0 6px 4px;color:#6E665E;line-height:1.8;padding-left:4px;"><span style="color:#F2545B;margin-right:8px;">●</span> ${inline(ul[1])}</p>`
      continue
    }

    // 有序列表 — 品牌色数字
    const ol = t.match(/^(\d+)[.、)\s]\s*(.*)/)
    if (ol) {
      olCounter += 1
      const num = ol[1] !== '0' ? ol[1] : String(olCounter)
      html += `<p style="margin:6px 0 6px 4px;color:#6E665E;line-height:1.8;padding-left:4px;"><span style="display:inline-block;width:28px;height:28px;line-height:28px;text-align:center;background:linear-gradient(135deg,#F2545B,#8B5CF6);color:#fff;border-radius:50%;font-size:0.82em;margin-right:10px;font-weight:700;">${num}</span> ${inline(ol[2])}</p>`
      continue
    }

    // 普通段落
    html += `<p style="margin:10px 0;color:#6E665E;line-height:1.85;">${inline(t)}</p>`
  }

  return html
}

module.exports = { render, escapeHtml }
