# Document Intelligence v0.10

Scientific documents are not plain text blobs. The v0.10 representation preserves content-bearing structure before extraction.

## Parsed objects

- ordered sections with parent links;
- equation occurrences with labels and surrounding context;
- figure and table occurrences with captions;
- structured table rows when parsers can recover them;
- reference occurrences retaining original text and known identifiers;
- citation mentions linking prose locations to reference identifiers;
- document-level metadata and parser warnings.

`DocumentIntelligence` is a derived routing summary. It reports counts, section types, math-dense sections, likely problem-statement sections, likely method sections, and parser warnings. It is not a substitute for the source document.

## Format policy

Prefer source-native structure in this order when rights and availability permit: structured XML/JATS/TEI, TeX/source, semantic HTML, plain text, then PDF fallback. OCR remains a last resort. A derived parser representation never overwrites the original acquired bytes or their checksum.

## References

Identifier inference is deliberately conservative. Recognized reference identifiers can later be resolved to canonical works, while unresolved references remain source assertions rather than fabricated citation edges.
