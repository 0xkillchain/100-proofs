const KEY = "proofs.graphGeometry.v1"
type Geometry = { width?: number; height?: number; left?: number; top?: number; inlineHeight?: number }
const clamp = (n: number, min: number, max: number) => Math.max(min, Math.min(n, max))
export function setupGraphWindows() {
  let saved: Geometry = {}
  try {
    const value = JSON.parse(localStorage.getItem(KEY) ?? "{}")
    if (value && typeof value === "object") {
      for (const key of ["width", "height", "left", "top", "inlineHeight"] as const) {
        if (typeof value[key] === "number" && Number.isFinite(value[key])) saved[key] = value[key]
      }
    }
  } catch { /* storage is optional */ }
  function save(next: Geometry) {
    saved = { ...saved, ...next }
    try { localStorage.setItem(KEY, JSON.stringify(saved)) } catch { /* private browsing may disable persistence */ }
  }
  for (const graph of document.querySelectorAll<HTMLElement>(".graph")) {
    const frame = graph.querySelector<HTMLElement>(".graph-window")!
    const overlay = graph.querySelector<HTMLElement>(".global-graph-outer")!
    const bar = frame.querySelector<HTMLElement>(".graph-titlebar")!
    const inline = graph.querySelector<HTMLElement>(".graph-outer")!
    const reset = frame.querySelector<HTMLButtonElement>(".graph-reset")!
    const maxWidth = () => Math.max(280, window.innerWidth - 24)
    const maxHeight = () => Math.max(220, window.innerHeight - 24)
    function restore() {
      const width = clamp(saved.width ?? window.innerWidth * .9, 280, maxWidth())
      const height = clamp(saved.height ?? window.innerHeight * .85, 220, maxHeight())
      frame.style.width = `${width}px`; frame.style.height = `${height}px`
      frame.style.left = `${clamp(saved.left ?? (window.innerWidth - width)/2, 12, window.innerWidth - width - 12)}px`
      frame.style.top = `${clamp(saved.top ?? (window.innerHeight - height)/2, 12, window.innerHeight - height - 12)}px`
      if (saved.inlineHeight) inline.style.height = `${clamp(saved.inlineHeight, 280, maxHeight())}px`
    }
    restore()
    const remember = new ResizeObserver(() => {
      if (overlay.classList.contains("active")) {
        const left = clamp(frame.offsetLeft, 12, window.innerWidth-frame.offsetWidth-12)
        const top = clamp(frame.offsetTop, 12, window.innerHeight-frame.offsetHeight-12)
        frame.style.left = `${left}px`; frame.style.top = `${top}px`
        save({ width: frame.offsetWidth, height: frame.offsetHeight, left, top })
      }
      if (inline.offsetHeight > 0) save({ inlineHeight: inline.offsetHeight })
    })
    remember.observe(frame); remember.observe(inline)
    let drag: { x: number; y: number; left: number; top: number } | null = null
    const down = (e: PointerEvent) => {
      if (e.button !== 0 || (e.target as HTMLElement).closest("button")) return
      e.preventDefault()
      drag = { x:e.clientX, y:e.clientY, left:frame.offsetLeft, top:frame.offsetTop }
      bar.setPointerCapture(e.pointerId)
    }
    const move = (e: PointerEvent) => {
      if (!drag) return
      frame.style.left = `${clamp(drag.left + e.clientX - drag.x, 12, window.innerWidth - frame.offsetWidth - 12)}px`
      frame.style.top = `${clamp(drag.top + e.clientY - drag.y, 12, window.innerHeight - frame.offsetHeight - 12)}px`
    }
    const up = () => {
      if (!drag) return
      drag = null; save({ left: frame.offsetLeft, top: frame.offsetTop })
    }
    const clear = () => {
      saved = {}; inline.style.height = ""; restore()
      try { localStorage.removeItem(KEY) } catch { /* optional */ }
    }
    const resize = () => restore()
    bar.addEventListener("pointerdown", down); bar.addEventListener("pointermove", move)
    bar.addEventListener("pointerup", up); bar.addEventListener("pointercancel", up)
    reset.addEventListener("click", clear); window.addEventListener("resize", resize)
    window.addCleanup(() => {
      remember.disconnect(); bar.removeEventListener("pointerdown", down); bar.removeEventListener("pointermove", move)
      bar.removeEventListener("pointerup", up); bar.removeEventListener("pointercancel", up)
      reset.removeEventListener("click", clear); window.removeEventListener("resize", resize)
    })
  }
}
