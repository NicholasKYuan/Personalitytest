/**
 * markdown.js — 轻量 Markdown → HTML 渲染器
 * 面向 wx <rich-text> 组件输出（支持 h1-h4 / p / 列表 / 粗体 / 斜体 / 行内代码 / 分割线）。
 *
 * 说明：不依赖 towxml/mp-html 等第三方库，体积小、零安装，足够渲染 AI 报告章节。
 * 如需更复杂语法（表格/图片/代码块高亮）再替换为 mp-html。
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
  s = s.replace(/`([^`]+)`/g, '<code>$1</code>')
  // 加粗
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  // 斜体（避免误伤连续星号）
  s = s.replace(/(^|[^*])\*([^*\s][^*]*)\*/g, '$1<em>$2</em>')
  return s
}

/**
 * 将 markdown 文本转为可渲染 HTML 字符串。
 * 列表用带前缀的 <p> 输出（rich-text 跨平台渲染 ul/ol 标记不可靠，手动保证显示）。
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

    // 围栏代码块：不渲染代码块，直接按段落输出（AI 报告少见）
    if (/^```/.test(t)) {
      inCode = !inCode
      continue
    }
    if (inCode) {
      html += `<p style="margin:6px 0;color:rgba(255,255,255,0.85);">${inline(t)}</p>`
      continue
    }

    // 空行 → 重置列表编号
    if (!t) {
      olCounter = 0
      continue
    }

    // 分割线
    if (/^(-{3,}|\*{3,}|_{3,})$/.test(t)) {
      html += '<hr style="border:none;border-top:1px solid rgba(255,255,255,0.15);margin:16px 0;"/>'
      continue
    }

    // 标题
    const h = t.match(/^(#{1,4})\s+(.+)/)
    if (h) {
      const level = h[1].length
      html += `<h${level} style="color:#fff;font-weight:700;line-height:1.5;margin:18px 0 8px;">${inline(h[2])}</h${level}>`
      continue
    }

    // 引用
    const bq = t.match(/^>\s?(.*)/)
    if (bq) {
      html += `<p style="margin:8px 0;padding:8px 14px;border-left:3px solid #E94560;background:rgba(255,255,255,0.06);border-radius:0 10px 10px 0;color:rgba(255,255,255,0.85);">${inline(bq[1])}</p>`
      continue
    }

    // 无序列表
    const ul = t.match(/^[-*+]\s+(.+)/)
    if (ul) {
      html += `<p style="margin:6px 0 6px 4px;color:rgba(255,255,255,0.85);"><span style="color:#E94560;">·</span> ${inline(ul[1])}</p>`
      continue
    }

    // 有序列表
    const ol = t.match(/^(\d+)[.、)\s]\s*(.*)/)
    if (ol) {
      olCounter += 1
      const num = ol[1] !== '0' ? ol[1] : String(olCounter)
      html += `<p style="margin:6px 0 6px 4px;color:rgba(255,255,255,0.85);"><span style="color:#E94560;">${num}.</span> ${inline(ol[2])}</p>`
      continue
    }

    // 普通段落
    html += `<p style="margin:8px 0;color:rgba(255,255,255,0.85);line-height:1.8;">${inline(t)}</p>`
  }

  return html
}

module.exports = { render, escapeHtml }
