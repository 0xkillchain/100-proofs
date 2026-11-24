import { QuartzComponent, QuartzComponentConstructor } from "./types"
export default (() => {
  const PageContents: QuartzComponent = ({ fileData }) => {
    if (fileData.slug === "index") return null
    const passages = fileData.frontmatter?.passageSections as { text: string; slug: string; depth: number }[] | undefined
    const entries = fileData.toc ?? passages ?? []
    const selected = entries.some(e => e.depth > 0) ? entries.filter(e => e.depth > 0) : entries
    if (!selected.length) return null
    return <nav class="page-contents" aria-label="On this page">
      <h2>On this page</h2>
      <ul>{selected.map(e => <li class={`contents-depth-${e.depth}`}><a href={`#${e.slug}`}>{e.text}</a></li>)}</ul>
    </nav>
  }
  return PageContents
}) satisfies QuartzComponentConstructor
