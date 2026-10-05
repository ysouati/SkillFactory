---
name: map-behavior-descriptions-to-mitre-attack-techniques-expanded
description: Use this skill to infer MITRE ATT&CK technique IDs from short malware, intrusion, or procedure descriptions. It is designed for row-wise free-text mapping, supports multiple techniques per description, and emphasizes broad coverage across the ATT&CK behavior space while requiring direct textual support.
---

# Map behavior descriptions to MITRE ATT&CK techniques

## When to use
Use this skill to infer MITRE ATT&CK technique IDs from short malware, intrusion, or procedure descriptions. It is designed for row-wise free-text mapping, supports multiple techniques per description, and emphasizes broad coverage across the ATT&CK behavior space while requiring direct textual support.

## Parameters
- **input_path** — Path to the input table containing one row per description. (default: input.tsv)
- **output_path** — Path to write the JSON predictions file. (default: predictions.json)
- **row_id_column** — Column containing the unique row identifier. (default: row_id)
- **text_column** — Column containing the behavior or malware description to map. (default: description)
- **output_format** — JSON structure to emit for each row. (default: {"row_id": <id>, "prediction": ["T####", ...]})

## References
Bundled knowledge — open a file only when a step below tells you to:
- `references/attack-technique-mapping-cues.md` — Use when converting free-text malware or intrusion behaviors into ATT&CK technique IDs.
- `references/attack-technique-disambiguation.md` — Use when deciding between similar ATT&CK techniques, parent vs sub-technique, and checking for missed or overpredicted behaviors.

## Requirements
- read a delimited text file
- write a JSON file
- extract behavioral indicators from prose
- match textual cues to MITRE ATT&CK techniques and sub-techniques
- deduplicate and validate structured outputs

## Procedure
1. Read the input table and identify the row ID column and the free-text description column.
2. For each row, split the description into distinct behaviors, capabilities, or phases. Extract concrete actions, targets, artifacts, protocols, persistence mechanisms, credential sources, discovery actions, collection actions, command-and-control semantics, exfiltration preparation, and impact behaviors.
3. Map each extracted behavior independently using references/attack-technique-mapping-cues.md. Cover the full ATT&CK behavior space relevant to malware and intrusion descriptions: resource development, reconnaissance, initial access, execution, persistence, privilege escalation, defense evasion, credential access, discovery, lateral movement, collection, command and control, exfiltration preparation, and impact.
4. Prefer the most specific supported sub-technique when the wording clearly identifies the method, protocol, artifact, or mechanism. If the text supports only a broader behavior, use the valid parent technique instead of leaving it unmapped. Apply references/attack-technique-disambiguation.md.
5. Extract multiple independent techniques from the same description when separately supported. Do not stop after the first plausible mapping; check whether the text also describes discovery, credential access, collection, staging, persistence, defense evasion, or command-and-control in addition to execution or delivery.
6. Use the disambiguation rules in references/attack-technique-disambiguation.md to separate commonly confused concepts: discovery vs collection, credential dumping vs input capture, hiding vs masquerading, execution vs persistence, protocol use for C2 vs ordinary network traffic, and parent vs child technique selection.
7. Deduplicate technique IDs within each row. Usually keep only the most specific supported child rather than both parent and child, unless the description independently supports both a broad behavior and a distinct child-level behavior.
8. Write the output as a JSON list of objects in the required format, one object per input row.
9. Before finalizing, run the quality checklist in references/attack-technique-disambiguation.md: verify every technique is text-supported, broad valid behaviors were not suppressed, and no independently supported technique categories were missed.

## Pitfalls
- Do not leave rows blank because of uncertainty; if the text clearly supports a broad ATT&CK behavior, use the parent technique.
- Do not rely on malware family labels like RAT, trojan, downloader, worm, or stealer as direct evidence of ATT&CK techniques; map only concrete behaviors described.
- Prefer specific sub-techniques when the text supports them, but do not force a child when only the parent is justified.
- Do not overinterpret cryptographic, hashing, packing, or encoding details as ATT&CK techniques unless the behavior itself is described.
- Be careful not to confuse file listing or enumeration with actual local data collection; T1083 and T1005 are different and may both apply only when both behaviors are stated.
- For process injection, generic shellcode injection supports T1055; reserve T1055.012 for clear hollowing semantics and other children only when the method is explicit.
- Remote shell creation supports T1059.003 only when Windows shell context is evident; otherwise use T1059.
- Masquerading and hiding are different: a benign-looking name or extension suggests the T1036 family, while hidden attributes, hidden windows, or concealed artifacts suggest the T1564 family.
- Account discovery, group discovery, user discovery, service discovery, and system information discovery are separate ATT&CK concepts; include each one that is independently supported.
- Network sniffing and adversary-in-the-middle are related but distinct; passive capture suggests T1040, while interception or relay positioning suggests T1557, and both may apply.
- Do not infer persistence from every execution mechanism; scheduled, startup, boot, service, or trigger semantics are needed for persistence techniques.
- When a description mentions multiple behaviors such as C2, discovery, persistence, credential theft, staging, and payload download, include all independently supported techniques rather than only the most salient one.
- Do not map every mention of a protocol or network traffic to command and control; C2 requires command, beaconing, callback, or controller semantics.
- Do not map every DLL mention to DLL hijacking; the text must indicate hijacking, side-loading, replacement, or load-path abuse.
- Pre-compromise techniques such as malware development, victim host information gathering, AI acquisition, malvertising, and drive-by target preparation should be used only when the description is clearly about preparation or targeting, not ordinary post-compromise behavior.
