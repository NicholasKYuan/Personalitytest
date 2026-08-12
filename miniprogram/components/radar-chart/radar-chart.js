/**
 * radar-chart.js — Canvas 2D 雷达图组件
 *
 * properties:
 *  - items:    [{ label, value }]  轴标签与得分
 *  - color:    数据多边形主色
 *  - maxValue: 坐标上限（0 时自动取最大值的 1.15 倍）
 *  - size:     画布边长（px）
 *
 * 特性：从中心向外展开的入场动画；items 变化时自动重绘（tab 切换）。
 */
Component({
  properties: {
    items: { type: Array, value: [] },
    color: { type: String, value: '#F2545B' },
    maxValue: { type: Number, value: 0 },
    size: { type: Number, value: 320 }
  },

  data: {
    inited: false
  },

  observers: {
    items(nv) {
      if (nv && nv.length && this.data.inited) {
        this.draw()
      }
    }
  },

  lifetimes: {
    ready() {
      this.setData({ inited: true })
      // 等布局完成后再取节点尺寸
      setTimeout(() => {
        if (this.data.items && this.data.items.length) this.draw()
      }, 80)
    }
  },

  methods: {
    hexToRgba(hex, alpha) {
      let h = String(hex || '#F2545B').replace('#', '')
      if (h.length === 3) h = h.split('').map((c) => c + c).join('')
      const r = parseInt(h.substr(0, 2), 16)
      const g = parseInt(h.substr(2, 2), 16)
      const b = parseInt(h.substr(4, 2), 16)
      return `rgba(${r},${g},${b},${alpha})`
    },

    draw() {
      const items = this.data.items
      if (!items || items.length < 3) return

      const query = this.createSelectorQuery()
      query
        .select('#radarCanvas')
        .fields({ node: true, size: true })
        .exec((res) => {
          if (!res || !res[0] || !res[0].node) return
          const canvas = res[0].node
          const ctx = canvas.getContext('2d')
          const w = res[0].width
          const h = res[0].height
          const dpr = (wx.getSystemInfoSync().pixelRatio) || 2
          canvas.width = w * dpr
          canvas.height = h * dpr
          ctx.scale(dpr, dpr)

          const cx = w / 2
          const cy = h / 2
          const radius = Math.min(w, h) / 2 - 30
          const n = items.length
          const rawMax = items.reduce((m, i) => Math.max(m, i.value || 0), 0)
          const maxV =
            this.data.maxValue > 0 ? this.data.maxValue : rawMax * 1.15 || 20
          const step = (Math.PI * 2) / n
          const start = -Math.PI / 2

          let progress = 0
          const frame = () => {
            progress = Math.min(1, progress + 0.08)
            ctx.clearRect(0, 0, w, h)
            this.paint(ctx, items, n, cx, cy, radius, maxV, step, start, progress)
            if (progress < 1 && canvas.requestAnimationFrame) {
              canvas.requestAnimationFrame(frame)
            }
          }
          frame()
        })
    },

    paint(ctx, items, n, cx, cy, radius, maxV, step, start, progress) {
      const r = radius * progress
      const color = this.data.color

      // 网格环（4 层）
      const levels = 4
      for (let lvl = 1; lvl <= levels; lvl++) {
        const lr = (r * lvl) / levels
        ctx.beginPath()
        for (let i = 0; i < n; i++) {
          const a = start + i * step
          const x = cx + lr * Math.cos(a)
          const y = cy + lr * Math.sin(a)
          if (i === 0) ctx.moveTo(x, y)
          else ctx.lineTo(x, y)
        }
        ctx.closePath()
        ctx.strokeStyle = '#EFE9E0'
        ctx.lineWidth = 1
        ctx.stroke()
      }

      // 轴线
      for (let i = 0; i < n; i++) {
        const a = start + i * step
        ctx.beginPath()
        ctx.moveTo(cx, cy)
        ctx.lineTo(cx + r * Math.cos(a), cy + r * Math.sin(a))
        ctx.strokeStyle = '#EFE9E0'
        ctx.lineWidth = 1
        ctx.stroke()
      }

      // 数据多边形
      ctx.beginPath()
      for (let i = 0; i < n; i++) {
        const v = Math.max(0, Math.min(1, (items[i].value || 0) / maxV))
        const a = start + i * step
        const x = cx + r * v * Math.cos(a)
        const y = cy + r * v * Math.sin(a)
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      }
      ctx.closePath()
      ctx.fillStyle = this.hexToRgba(color, 0.18)
      ctx.fill()
      ctx.strokeStyle = color
      ctx.lineWidth = 2
      ctx.stroke()

      // 顶点
      for (let i = 0; i < n; i++) {
        const v = Math.max(0, Math.min(1, (items[i].value || 0) / maxV))
        const a = start + i * step
        const x = cx + r * v * Math.cos(a)
        const y = cy + r * v * Math.sin(a)
        ctx.beginPath()
        ctx.arc(x, y, 3, 0, Math.PI * 2)
        ctx.fillStyle = color
        ctx.fill()
      }

      // 轴标签
      ctx.font = '11px sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillStyle = `rgba(110,102,94,${(0.55 + 0.45 * progress).toFixed(2)})`
      for (let i = 0; i < n; i++) {
        const a = start + i * step
        const lx = cx + (radius + 16) * Math.cos(a)
        const ly = cy + (radius + 16) * Math.sin(a)
        ctx.fillText(items[i].label, lx, ly)
      }
    }
  }
})
