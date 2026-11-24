export function setupMobileMenu(library: HTMLElement) {
  const media = window.matchMedia("(max-width: 1024px)")
  const toggle = library.querySelector<HTMLButtonElement>(".mobile-menu-toggle")!
  const drawer = library.querySelector<HTMLElement>(".library-drawer")!
  const closeButton = library.querySelector<HTMLButtonElement>(".mobile-menu-close")!
  const backdrop = library.querySelector<HTMLButtonElement>(".mobile-menu-backdrop")!
  const toolsSlot = library.querySelector<HTMLElement>(".mobile-menu-tools")!
  const sidebar = library.closest(".sidebar.left")!
  const tools = sidebar.querySelector<HTMLElement>(":scope > .flex-component")
  const marker = document.createComment("mobile navigation tools")
  tools?.before(marker)
  let open = false
  let previousOverflow: string | null = null
  const close = (restoreFocus = true) => {
    open = false; library.dataset.menuOpen = "false"
    toggle.setAttribute("aria-expanded", "false")
    backdrop.hidden = true; drawer.inert = media.matches
    if (previousOverflow !== null) { document.body.style.overflow = previousOverflow; previousOverflow = null }
    if (restoreFocus && media.matches) toggle.focus()
  }
  const show = () => {
    if (!media.matches || open) return
    open = true; library.dataset.menuOpen = "true"
    toggle.setAttribute("aria-expanded", "true")
    drawer.inert = false; backdrop.hidden = false
    previousOverflow = document.body.style.overflow
    document.body.style.overflow = "hidden"
    closeButton.focus()
  }
  const changeMedia = () => {
    close(false)
    if (media.matches) {
      if (tools) toolsSlot.append(tools)
      drawer.setAttribute("role", "dialog"); drawer.setAttribute("aria-modal", "true"); drawer.setAttribute("aria-label", "Navigation")
    } else {
      if (tools) marker.after(tools)
      drawer.removeAttribute("role"); drawer.removeAttribute("aria-modal"); drawer.removeAttribute("aria-label")
    }
  }
  const click = () => open ? close() : show()
  const dismiss = () => close()
  const navigation = (e: MouseEvent) => { if ((e.target as HTMLElement).closest("a[href]")) close(false) }
  const keydown = (e: KeyboardEvent) => {
    if (!open) return
    if (e.key === "Escape") { e.preventDefault(); close(); return }
    if (e.key !== "Tab") return
    const controls = [...drawer.querySelectorAll<HTMLElement>('a[href], button, input, select, [tabindex="0"]')].filter(el => el.offsetParent !== null && !el.hasAttribute("disabled"))
    const first = controls[0], last = controls[controls.length-1]
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last?.focus() }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first?.focus() }
  }
  changeMedia()
  toggle.addEventListener("click", click); closeButton.addEventListener("click", dismiss); backdrop.addEventListener("click", dismiss)
  drawer.addEventListener("click", navigation); document.addEventListener("keydown", keydown); media.addEventListener("change", changeMedia)
  window.addCleanup(() => {
    close(false)
    if (tools) marker.after(tools)
    marker.remove()
    toggle.removeEventListener("click", click); closeButton.removeEventListener("click", dismiss); backdrop.removeEventListener("click", dismiss)
    drawer.removeEventListener("click", navigation); document.removeEventListener("keydown", keydown); media.removeEventListener("change", changeMedia)
  })
}
