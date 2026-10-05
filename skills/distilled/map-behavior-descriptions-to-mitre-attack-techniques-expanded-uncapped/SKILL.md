---
name: map-behavior-descriptions-to-mitre-attack-techniques-comprehensive
description: Use this skill when given malware, intrusion, campaign, or procedure descriptions and asked to infer relevant MITRE ATT&CK technique IDs from prose alone. It supports portable, evidence-based row-by-row mapping across the ATT&CK lifecycle, with broad coverage, explicit disambiguation rules, and preference for the most specific justified sub-technique.
---

# Map prose behaviors to MITRE ATT&CK techniques

## When to use
Use this skill when given malware, intrusion, campaign, or procedure descriptions and asked to infer relevant MITRE ATT&CK technique IDs from prose alone. It supports portable, evidence-based row-by-row mapping across the ATT&CK lifecycle, with broad coverage, explicit disambiguation rules, and preference for the most specific justified sub-technique.

## Parameters
- **input_path** — Path to the input tabular file containing one row per description. (default: input.tsv)
- **output_path** — Path to write the JSON predictions list. (default: predictions.json)
- **row_id_column** — Column containing the unique row identifier. (default: row_id)
- **text_column** — Column containing the behavior, malware, intrusion, or procedure description to analyze. (default: description)
- **output_prediction_key** — Key name for the list of predicted technique IDs in each output object. (default: prediction)

## References
Bundled knowledge — open a file only when a step below tells you to:
- `references/attack-technique-family-reference.md` — Use when first classifying behaviors by ATT&CK lifecycle stage and deciding parent versus sub-technique.
- `references/comprehensive-attack-technique-catalog.md` — Use when a description mentions a concrete mechanism, artifact, protocol, store, utility, or method and you need an explicit ATT&CK row.
- `references/inclusion-and-boundary-rules.md` — Use when deciding whether evidence is strong enough to include a technique and when resolving ambiguous wording.
- `references/verified-technique-rows.md` — Use as an explicit supplemental ATT&CK lookup table containing verified rows and boundary notes that must be preserved individually.

## Requirements
- read a delimited text file
- write a JSON file
- extract concrete behaviors from prose
- match behaviors to MITRE ATT&CK techniques using bundled references
- deduplicate and validate structured outputs

## Procedure
1. Read the input table and identify the row ID column and the free-text description column.
2. For each row, rewrite the description into a compact evidence list of explicit actions, mechanisms, artifacts, protocols, stores, targets, and outcomes. Separate direct statements from assumptions. Scan across the full ATT&CK lifecycle: Reconnaissance, Resource Development, Initial Access, Execution, Persistence, Privilege Escalation, Defense Evasion, Credential Access, Discovery, Lateral Movement, Collection, Command and Control, Exfiltration, and Impact.
3. Consult references/attack-technique-family-reference.md to place each explicit behavior into the correct tactic family and technique family. Use it first for lifecycle coverage and for parent-versus-sub-technique decisions.
4. Consult references/comprehensive-attack-technique-catalog.md to map each explicit behavior to the best ATT&CK technique or sub-technique. Prefer the most specific sub-technique when the text names the mechanism, protocol, artifact type, credential source, persistence point, execution utility, or discovery target.
5. Consult references/inclusion-and-boundary-rules.md to decide whether evidence is sufficient. Include techniques when the prose directly states the behavior, even if brief. Do not require unnecessary implementation detail once the ATT&CK behavior is explicit.
6. Use references/verified-technique-rows.md as an additional explicit lookup source. Treat every row there as valid reusable ATT&CK knowledge and apply it whenever the description matches the stated behavior or boundary condition.
7. When a description contains multiple distinct behaviors, include multiple techniques. For example, keep separate mappings for discovery plus collection, execution plus persistence, credential access plus command and control, or staging plus exfiltration when each is directly supported.
8. Prefer the most specific supported sub-technique over its parent. Normally output only the child when the child is directly justified. Use the parent only when the text supports the broader behavior but not the exact sub-technique. Keep both parent and child only if hierarchical output is explicitly required.
9. Apply disambiguation carefully: pre-compromise victim research versus post-compromise discovery; current user versus account enumeration; discovery versus collection; passive sniffing versus adversary-in-the-middle; masquerading versus hiding versus obfuscation; generic interpreter use versus named interpreters; generic application-layer C2 versus named protocols; generic password-store theft versus named stores; generic process injection versus named injection methods; generic persistence versus named autostart or event-triggered mechanisms.
10. Do not infer techniques solely from malware family labels, actor names, or broad nouns such as RAT, trojan, worm, spyware, downloader, backdoor, stealer, loader, or bot. Only map behaviors actually described in the text.
11. Build the output as a JSON list of objects, one per row, each containing the row ID and a list of ATT&CK ID strings under the configured prediction key.
12. Before writing the final file, validate that every input row appears exactly once, every prediction is formatted as an ATT&CK-style ID present in the bundled references, there are no duplicates within a row, parent-child redundancy has been minimized, and each included technique is supported by explicit textual evidence.
13. Write the JSON output file.

## Pitfalls
- Do not leave rows unpredicted; produce one output object per input row even if the prediction list is empty.
- A frequent failure mode is low recall from missing whole ATT&CK families. Always scan for behaviors across the full lifecycle: reconnaissance, resource development, initial access, execution, persistence, privilege escalation, defense evasion, credential access, discovery, lateral movement, collection, command and control, exfiltration, and impact.
- Another frequent failure mode is being too conservative and omitting a valid technique even when the mechanism is explicitly named in brief prose. Short but explicit evidence is enough.
- Prefer the most specific supported sub-technique, but do not invent specificity. If the text names DNS C2, use T1071.004; if it only says application-layer C2, use T1071.
- Avoid redundant parent-child predictions for the same behavior family; usually return only the most specific supported ID.
- Do not over-interpret generic process injection, generic DLL use, generic WMI use, generic DNS use, or generic credential theft into narrower sub-techniques unless the method or source is explicit.
- Differentiate discovery from collection: enumeration of files, services, drivers, software, users, or hosts is discovery; reading or extracting the underlying data is collection.
- Differentiate pre-compromise victim host research from post-compromise host discovery: T1592/T1592.001 are for targeting-stage victim host information, while T1082 is for system information discovery on a compromised host.
- Differentiate current-user discovery from account enumeration: T1033 is for the current or active user; T1087 and its sub-techniques are for listing accounts.
- Differentiate passive network sniffing from adversary-in-the-middle: T1040 is passive capture; T1557 implies positioning between communicating parties.
- Differentiate masquerading from hiding and from obfuscation: looking legitimate is T1036-family behavior, concealing artifacts is T1564-family behavior, and encoded/encrypted/embedded/fileless concealment belongs to the relevant T1027-family variants.
- Do not infer techniques solely from malware labels such as RAT, trojan, downloader, worm, spyware, loader, stealer, or backdoor.
- Do not suppress valid mappings just because the prose is short; if a named utility, protocol, store, or persistence point is explicit, map it.
- Do not infer follow-on behaviors from phishing, reconnaissance, or infrastructure setup unless the later action is separately stated. For example, phishing links do not automatically imply credential theft, session theft, or MFA bypass.
- When a named signed-binary proxy execution utility appears, prefer its specific ATT&CK sub-technique over a broader execution or DLL technique unless the broader behavior is separately described.
- When both a parent and child seem plausible, choose the child only if the child-specific mechanism is explicit; otherwise keep the parent.
