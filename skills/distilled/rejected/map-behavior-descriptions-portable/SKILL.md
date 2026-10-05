---
name: map-behavior-descriptions-to-mitre-attack-technique-ids
description: Use this skill when given short malware, intrusion, or procedure descriptions and asked to predict the MITRE ATT&CK technique IDs they imply. It is designed for row-by-row extraction from text into technique-ID lists without relying on external lookup services at runtime.
---

# Map behavior descriptions to ATT&CK techniques

## When to use
Use this skill when given short malware, intrusion, or procedure descriptions and asked to predict the MITRE ATT&CK technique IDs they imply. It is designed for row-by-row extraction from text into technique-ID lists without relying on external lookup services at runtime.

## Parameters
- **input_path** — Path to the input table or text file containing row identifiers and behavior descriptions. (default: input.tsv)
- **output_path** — Path where the JSON predictions file should be written. (default: predictions.json)
- **row_id_column** — Name of the column containing the unique row identifier. (default: row_id)
- **description_column** — Name of the column containing the behavior or malware description text. (default: description)
- **output_format** — Structure of each output record. (default: {"row_id": <int|string>, "prediction": ["T####", ...]})

## References
Bundled knowledge — open a file only when a step below tells you to:
- `references/attack-technique-mapping-reference.md` — Consult when converting behavior phrases in a description into ATT&CK technique IDs.
- `references/attack-technique-disambiguation-notes.md` — Consult when a description could fit multiple nearby ATT&CK techniques or when deciding how much to infer.

## Requirements
- read a delimited text file
- parse quoted text fields safely
- write a JSON file
- perform careful text-to-taxonomy mapping
- basic familiarity with MITRE ATT&CK technique notation

## Procedure
1. Read the input file and extract each row's identifier and description text. Preserve the original row order.
2. For each description, identify concrete behaviors, capabilities, or procedures explicitly stated in the text. Ignore malware family names, actor names, programming languages, encryption algorithms, and protocol details unless they directly imply an ATT&CK behavior.
3. Map each explicit behavior to one or more ATT&CK techniques using the decision rules in references/attack-technique-mapping-reference.md.
4. When a description mentions a broad behavior and a more specific ATT&CK sub-technique is available in the reference, prefer the more specific sub-technique. Example: prefer T1071.001 over T1071 for HTTP/HTTPS C2; prefer T1059.003 over T1059 for cmd.exe or remote shell via Windows command shell.
5. Only include techniques supported by the wording of the description. Do not infer extra steps just because malware commonly performs them. Use references/attack-technique-mapping-reference.md to distinguish direct evidence from weak implication.
6. If multiple phrases in the same description map to the same technique, include that technique only once in the row's prediction list.
7. If a phrase could map to several nearby techniques, choose the one whose ATT&CK definition most directly matches the described action. Use references/attack-technique-disambiguation-notes.md for common confusions.
8. Build the output as a JSON list of objects in the form {"row_id": ..., "prediction": [ ... ]}. Keep prediction values as technique-ID strings.
9. Before writing the file, validate that every predicted item matches ATT&CK ID formatting and that each row from the input appears exactly once in the output.
10. Write the JSON predictions file to the requested output path.

## Pitfalls
- Do not leave rows blank because of uncertainty; extract at least the clearly explicit behaviors.
- Do not rely on broad keyword matching alone; verify that the phrase actually describes the ATT&CK behavior, not just adjacent technical detail like encryption or malware implementation.
- A frequent accuracy issue is choosing parent techniques when the description supports a more specific sub-technique, especially T1071.001 vs T1071 and T1059.003 vs T1059.
- Do not over-predict from malware family reputation or common behavior patterns; only use what the row text states.
- When parsing TSV with quoted descriptions, handle embedded quotes safely so rows are not truncated or misread.
- Deduplicate repeated evidence within a row so the prediction is a clean set-like list of IDs.
- Validate every predicted ID string before writing output; formatting mistakes can invalidate otherwise correct mappings.
