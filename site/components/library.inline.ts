import { setupMobileMenu } from "./mobile-menu"
document.addEventListener("nav", () => {
  for (const library of document.querySelectorAll<HTMLElement>(".library")) {
    setupMobileMenu(library)
    const tabs = [...library.querySelectorAll<HTMLButtonElement>("[data-library-tab]")]
    function activate(tab: HTMLButtonElement) {
      for (const button of tabs) {
        const active = button === tab
        button.setAttribute("aria-selected", String(active))
        button.tabIndex = active ? 0 : -1
        const panel = library.querySelector<HTMLElement>(`#${button.getAttribute("aria-controls")}`)
        if (panel) panel.hidden = !active
      }
    }
    for (const tab of tabs) {
      const click = () => activate(tab)
      const key = (e: KeyboardEvent) => {
        if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key)) return
        e.preventDefault()
        let index = tabs.indexOf(tab)
        index = e.key === "Home" ? 0 : e.key === "End" ? tabs.length - 1 : (index + (e.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length
        activate(tabs[index]); tabs[index].focus()
      }
      tab.addEventListener("click", click); tab.addEventListener("keydown", key)
      window.addCleanup(() => { tab.removeEventListener("click", click); tab.removeEventListener("keydown", key) })
    }
  }
  for (const select of document.querySelectorAll<HTMLSelectElement>(".scripture-controls select")) {
    const change = () => { if (select.value) window.spaNavigate(new URL(select.value, window.location.href)) }
    select.addEventListener("change", change)
    window.addCleanup(() => select.removeEventListener("change", change))
  }
})
