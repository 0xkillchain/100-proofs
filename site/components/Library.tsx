import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { resolveRelative } from "../util/path"
// @ts-ignore
import script from "./scripts/library.inline"
import style from "./styles/library.scss"

export default (() => {
  const Library: QuartzComponent = ({ allFiles, fileData }: QuartzComponentProps) => {
    const proofs = allFiles.filter(f => /^\d+---/.test(f.slug ?? "")).sort((a,b) => parseInt(a.slug!) - parseInt(b.slug!))
    const books = allFiles.filter(f => f.frontmatter?.scriptureBookIndex === true).sort((a,b) => Number(a.frontmatter?.bookOrder) - Number(b.frontmatter?.bookOrder))
    const scripture = fileData.slug?.startsWith("Scripture/")
    const link = (f: typeof fileData) => resolveRelative(fileData.slug!, f.slug!)
    return <nav class="library" aria-label="Library">
      <button class="mobile-menu-toggle" type="button" aria-label="Open navigation" aria-controls="library-drawer" aria-expanded="false">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18" /></svg>
      </button>
      <button class="mobile-menu-backdrop" type="button" aria-label="Close navigation" tabIndex={-1} hidden />
      <div class="library-drawer" id="library-drawer">
        <div class="mobile-menu-heading"><strong>Navigation</strong><button class="mobile-menu-close" type="button" aria-label="Close navigation">✕</button></div>
        <div class="mobile-menu-tools" />
      <div class="library-tabs" role="tablist" aria-label="Browse library">
        <button id="proofs-tab" type="button" role="tab" aria-selected={!scripture} aria-controls="proofs-panel" tabIndex={scripture ? -1 : 0} data-library-tab="proofs">Proofs</button>
        <button id="scripture-tab" type="button" role="tab" aria-selected={!!scripture} aria-controls="scripture-panel" tabIndex={scripture ? 0 : -1} data-library-tab="scripture">Scripture</button>
      </div>
      <section id="proofs-panel" role="tabpanel" aria-labelledby="proofs-tab" hidden={scripture}>
        <a class="library-index" href={resolveRelative(fileData.slug!, "index" as any)}>All 100 proofs</a>
        <ol>{proofs.map(f => <li><a href={link(f)} aria-current={f.slug === fileData.slug ? "page" : undefined}>{String(f.frontmatter?.title ?? f.slug).replace(/^(?:Proof \d+:\s*|\d+ - )/, "")}</a></li>)}</ol>
      </section>
      <section id="scripture-panel" role="tabpanel" aria-labelledby="scripture-tab" hidden={!scripture}>
        <a class="library-index" href={resolveRelative(fileData.slug!, "Scripture/index" as any)}>Scripture library</a>
        <ul>{books.map(f => <li><a href={link(f)} aria-current={fileData.slug?.startsWith(f.slug!.replace(/\/index$/, "/")) ? "page" : undefined}>{String(f.frontmatter?.book)}</a></li>)}</ul>
      </section>
      </div>
    </nav>
  }
  Library.css = style
  Library.afterDOMLoaded = script
  return Library
}) satisfies QuartzComponentConstructor
