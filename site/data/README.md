# Scripture text sources

Bible and Apocrypha: public-domain King James Version, retrieved from https://github.com/scrollmapper/bible_databases/blob/master/formats/json/KJVA.json on 2026-11-24. Download SHA-256: `404cc86145f221a5599864a1e20033588ec592933c90bb20fe6c4fa461db945a`. Only cited passages are retained. Chapter-wide citations retain the cited chapter; verse citations retain only those verses, including ranges. Book names and chapter/verse keys are normalized; verse wording is retained.

1 Enoch: only excerpts already quoted in the original proof notes, clearly labeled as incomplete and not independently verified. Project Gutenberg full-text requests returned 503, so no missing text is reconstructed. See https://www.gutenberg.org/ebooks/77935 for the Charles translation.

The corpus is vendored so deployment needs no runtime scripture API.
