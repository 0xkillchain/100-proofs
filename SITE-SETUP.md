# Research archive hosting

The site uses Quartz 4 and GitHub Pages. The numbered Markdown files and INDEX.md remain at the repository root. Edit those files normally; pushes to main rebuild the site. The build adds research context to every published page and resolves six legacy shorthand wikilinks without modifying source documents.

## First publication

1. Add `.github/workflows/deploy.yml`, `scripts/prepare-site.py`, and this document to the repository and push to `main`. If your default branch has another name, change the workflow's branch first.
2. Open https://github.com/0xkillchain/100-proofs/settings/pages and select **GitHub Actions** as the build source.
3. Open the repository's **Actions** tab and run **Publish research archive**, or push another commit.
4. Check the successful deployment at https://0xkillchain.github.io/100-proofs/.

The public website is separate from repository visibility. Publish only material intended for public access.

## Local preview

With Git, Python 3, Node 22, and npm installed:

```sh
git clone --branch v4 --single-branch https://github.com/jackyzha0/quartz.git /tmp/100-proofs-quartz
python3 scripts/prepare-site.py /tmp/100-proofs-quartz
cd /tmp/100-proofs-quartz
npm ci
npx quartz build --serve
```

Open http://localhost:8080. Use a fresh Quartz checkout before rerunning preparation, because preparation updates its configuration.

## Maintenance

The workflow uses Quartz's maintained `v4` branch rather than importing its implementation into this repository. For fully reproducible builds, replace `ref: v4` with a reviewed commit SHA after a successful build. A later migration to Quartz 5 should update the preparation script and workflow together.

Only numbered source documents and INDEX.md are currently published. Expand the content selection in `scripts/prepare-site.py` when adding rebuttals in other files or folders. Broken wikilinks fail preparation rather than silently publishing dead links.
