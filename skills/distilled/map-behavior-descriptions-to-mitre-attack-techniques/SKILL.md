---
name: map-behavior-descriptions-to-mitre-attack-techniques
description: Use this skill when given malware, intrusion, threat activity, or adversary behavior descriptions and asked to infer the best-supported MITRE ATT&CK technique IDs. It is designed for portable text-to-technique mapping across the ATT&CK lifecycle, including pre-compromise, enterprise, cloud, network, mobile, and multi-technique scenarios.
---

# Map Behavior Descriptions to MITRE ATT&CK Techniques

## When to use
Use this skill when given malware, intrusion, threat activity, or adversary behavior descriptions and asked to infer the best-supported MITRE ATT&CK technique IDs. It is designed for portable text-to-technique mapping across the ATT&CK lifecycle, including pre-compromise, enterprise, cloud, network, mobile, and multi-technique scenarios.

## Parameters
- **input_path** — Path to the input file containing at least a row identifier and free-text description column. (default: input.tsv)
- **output_path** — Path where the JSON predictions file should be written. (default: predictions.json)
- **row_id_column** — Name of the column containing the row identifier. (default: row_id)
- **description_column** — Name of the column containing the behavior description text. (default: description)
- **output_format** — Expected JSON structure for predictions. (default: [{"row_id":"<id>","prediction":["T####","T####.###"]}])

## References
Bundled knowledge — open a file only when a step below tells you to:
- `references/attack-technique-mapping-reference.md` — Use when converting extracted behaviors, artifacts, protocols, and platform cues into ATT&CK technique IDs.
- `references/attack-technique-decision-rules.md` — Use when wording is ambiguous, indirect, overlapping, or could fit multiple ATT&CK techniques.

## Requirements
- read a delimited text file
- write a JSON file
- extract actions, objects, mechanisms, and platform cues from prose
- normalize free text to MITRE ATT&CK techniques
- reason about ambiguity and overlapping ATT&CK behaviors

## Procedure
1. Read the input file and identify the row ID and description columns.
2. For each description, extract concrete evidence rather than malware family names or broad labels. Capture: action, target/object, mechanism or artifact, platform, scope, and whether the behavior is pre-compromise or post-compromise.
3. Normalize the description into short evidence statements such as: 'user opens malicious file', 'uses exposed VPN for access', 'executes JavaScript', 'creates scheduled task', 'dumps LSA secrets', 'sniffs traffic', 'captures clipboard', 'uses HTTP/HTTPS for C2', or 'stages data locally'.
4. Determine ATT&CK scope and platform before mapping. Separate enterprise host behaviors from pre-compromise targeting/resource-development behaviors, and note Windows, Linux, macOS, cloud, mobile, identity, or network-device cues. Consult references/attack-technique-mapping-reference.md.
5. Map each evidence statement to candidate ATT&CK techniques using references/attack-technique-mapping-reference.md. Start with the most explicit mechanism or artifact, then add other independently supported behaviors from the same description.
6. Prefer the most specific sub-technique when the text names a distinctive mechanism, protocol, binary, store, service, or artifact. If the wording is not specific enough for a sub-technique, use the parent technique instead. Consult references/attack-technique-decision-rules.md.
7. When wording is indirect, map from strong behavioral implication rather than exact ATT&CK phrasing. Use recognizable mechanisms, outcomes, and artifacts, but do not infer techniques solely from malware type, campaign name, or stereotype. Consult references/attack-technique-decision-rules.md.
8. Check common distinctions carefully: initial access versus execution, execution versus persistence, discovery versus collection, sniffing versus adversary-in-the-middle, protocol versus encoding versus encrypted artifact, masquerading versus hidden artifacts, and remote-service access versus remote command execution. Consult references/attack-technique-decision-rules.md.
9. If a description spans multiple tactics, include all independently supported techniques. Multi-technique rows are normal when the text describes separate behaviors such as phishing plus user execution, downloader plus execution, persistence plus privilege escalation, credential access plus discovery, collection plus staging, or C2 plus defense evasion.
10. For each selected technique, ensure you can point to a phrase or strong implication in the text. If two nearby techniques compete, choose the one anchored by the clearest mechanism; if neither is specific enough, fall back to the broader parent or omit the weaker candidate.
11. Build the output as a JSON list with one object per input row containing the row ID and a deduplicated list of ATT&CK IDs.
12. Validate that no row is omitted, every prediction matches T#### or T####.### format, duplicate IDs within a row are removed, and the JSON is syntactically valid.
13. Write the JSON to the requested output path.

## Pitfalls
- Do not return empty predictions simply because the wording is indirect; many ATT&CK behaviors are implied by mechanisms, artifacts, or outcomes rather than exact ATT&CK phrasing.
- Do not rely on malware family names, campaign names, or generic labels like RAT, trojan, stealer, worm, or backdoor without extracting the concrete behaviors described.
- Do not confuse delivery with execution: a phishing attachment or link may support a phishing technique, while the user opening or clicking it may separately support a user execution technique.
- Do not confuse exposed remote access services used for entry with generic remote shell execution or lateral movement; external remote services require evidence of leveraging an external-facing remote access service.
- Do not confuse HTTP/HTTPS command-and-control with encoding or encrypted artifacts; one description may support T1071.001 together with T1132.001/T1132.002 and/or T1027.013.
- Do not map passive packet capture to adversary-in-the-middle unless the text indicates positioning between parties, relaying, spoofing, downgrading, or modifying communications.
- Do not map file enumeration or metadata inspection to data theft unless the text indicates actual collection of file contents; use staging only when the text indicates local organization before exfiltration.
- Do not add persistence unless startup, boot, logon, scheduled recurrence, service creation, agent/daemon creation, or another re-launch mechanism is described.
- Do not force Windows-specific techniques onto non-Windows descriptions; use platform cues such as Keychain, Gatekeeper, launch agents, sudo, cron, or VNC appropriately.
- Do not overuse parent techniques when a named mechanism clearly supports a sub-technique such as JavaScript, Rundll32, Mavinject, Scheduled Task, Active Setup, Windows Service, LSA Secrets, Keychain, Password Managers, VNC, or Web Protocols.
- Do not suppress valid pre-compromise mappings; victim profiling, purchased technical data, compromised network devices, and drive-by target preparation are legitimate ATT&CK behaviors.
- When multiple independent behaviors appear in one description, include multiple techniques rather than choosing only one tactic category.
