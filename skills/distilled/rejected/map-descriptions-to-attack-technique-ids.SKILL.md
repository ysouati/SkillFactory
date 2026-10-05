---
name: map-descriptions-to-attack-technique-ids
---

# Map text descriptions to ATT&CK technique IDs

## When to use
Use this skill when given a small tabular file of free-text behavior descriptions and asked to predict MITRE ATT&CK technique IDs for each row without access to labels. It is appropriate when ATT&CK KB/search tools are available and the task requires producing a JSON file of per-row technique-ID lists based only on evidence in each description.

## Parameters
- **input_tsv_path** — Path to the input TSV file containing one row per example. (default: input.tsv)
- **output_json_path** — Path where the predictions JSON list should be written. (default: predictions.json)
- **row_id_column** — Name of the integer identifier column in the TSV. (default: row_id)
- **text_column** — Name of the free-text description column in the TSV. (default: description)
- **doc_type** — Knowledge-base document type to search for ATT&CK techniques. (default: attack-technique)
- **prior_solves_query** — Short query used to retrieve prior attempts for the same task family. (default: Map TSV row descriptions to MITRE ATT&CK technique IDs and write predictions.json)

## Dependencies
- Tools: search_prior_solves, read_file, write_file, final_answer, search_docs, kb_get, kb_find, kb_entity_types
- Libraries: json

## Procedure
1. Call search_prior_solves with {prior_solves_query}. Read the returned traces, especially failures, and adopt the best-scoring pattern while avoiding diagnosed mistakes.
2. Read {input_tsv_path} as a UTF-8 TSV text file. Assume tab delimiter and a header row. Verify that columns {row_id_column} and {text_column} exist; if either is missing, stop and report the malformed input rather than guessing.
3. Inspect the rows and treat each description independently. Do not search for labels, benchmarks, or any ground truth; the task is prediction-only from the description text.
4. Optionally call kb_entity_types once to confirm ATT&CK technique entities are available in the KB before doing targeted lookups.
5. For each row, extract concrete behavioral clues from the description: communication protocol, execution method, persistence mechanism, discovery actions, credential/data access, privilege escalation, injection, transfer/download behavior, mobile-specific capabilities, etc. Prefer explicit behaviors over malware-family names.
6. Turn those clues into a short list of targeted ATT&CK search queries aimed at techniques, not broad tactics. Use search_docs with doc_type={doc_type} and queries that combine the platform/behavior with likely ATT&CK wording, such as protocol + command-and-control, shell execution, process discovery, registry run keys, WMI persistence, domain enumeration, clipboard access, credential theft, or mobile permission abuse.
7. From search results, collect candidate technique IDs and names. Verify each candidate with kb_get before using it. If kb_get fails or returns no object for an ID, discard that candidate instead of keeping an unverified guess.
8. When search results are noisy or ambiguous, use kb_find with exact or near-exact technique names suggested by the search results to resolve the correct ATT&CK technique entity ID. Prefer verified ATT&CK names/IDs over approximate memory.
9. Map only behaviors that are actually supported by the row text. Be conservative: include a technique when the description clearly indicates that behavior; omit speculative techniques that are only weakly implied.
10. Use ATT&CK sub-techniques when the behavior is specific enough and the KB confirms them; otherwise use the parent technique only if that is what the evidence supports. Keep IDs in ATT&CK format (for example T#### or T####.### exactly as returned by the KB).
11. Build one prediction object per input row in the form {"{row_id_column}": <int>, "prediction": [<technique-id strings>]}. Ensure prediction is always a JSON array, even if empty or containing one item.
12. Before writing output, validate the schema: the top-level value must be a JSON list; each element must contain the original row identifier and a list of strings; every predicted string should match ATT&CK ID formatting and should have been KB-verified.
13. Write the full list to {output_json_path} as JSON.
14. Call final_answer with a one-line summary stating that predictions were written to {output_json_path} using targeted ATT&CK KB lookups and conservative technique mapping.

## Pitfalls
- Do not invent or keep technique IDs that are not confirmed by the KB; in the trace, several remembered mobile IDs were invalid and kb_get returned errors.
- Generic ATT&CK searches can return irrelevant top hits; refine queries around the exact behavior and verify with kb_get/kb_find before deciding.
- Avoid over-relying on malware names or broad narratives; map explicit observed behaviors in the description to techniques.
- Prediction-only means no downloading labels, no self-scoring, and no benchmark lookup.
- Input assumptions matter: the file is a TSV with a header row and required columns; validate this before processing.
- Output schema matters: write a JSON list of objects, one per row, preserving the row ID and using a list of technique-ID strings for prediction.
