# Verified ATT&CK technique rows and notes

Each item below is preserved as its own explicit reusable row. Use these rows directly when the prose matches the stated behavior or boundary condition.

| ATT&CK ID | Technique name | Reusable mapping guidance |
|---|---|---|
| T1592 | Gather Victim Host Information | Use for pre-compromise gathering of information about victim hosts that can be used during targeting. Information about hosts may include a variety of host details useful before access is obtained. |
| T1592.001 | Hardware | Use for pre-compromise gathering of victim host hardware information during targeting. This is specifically hardware-focused victim host research before compromise. |
| T1592 | Gather Victim Host Information | Boundary note: this reconnaissance behavior can support later resource development and/or initial access planning, including scenarios related to supply chain compromise or external remote services, but do not replace those later techniques unless those later behaviors are explicitly described. |
| T1594 | Search Victim-Owned Websites | Use when adversaries search websites owned by the victim for information that can be used during targeting. Victim-owned websites may contain useful targeting details. |
| T1596.001 | DNS/Passive DNS | Use when adversaries search DNS data or passive DNS data for information about victims that can be used during targeting. This is reconnaissance, not DNS command and control. |
| T1583 | Acquire Infrastructure | Use when adversaries buy, lease, rent, or otherwise obtain infrastructure that can be used during targeting or operations. This is the parent when the exact infrastructure type is not specified. |
| T1587.001 | Malware | Use when adversaries develop malware or malware components that can be used during targeting or operations. This includes building payloads, droppers, implants, or malware components. |
| T1583.007 | Serverless | Use when adversaries purchase or configure serverless cloud infrastructure, such as cloud functions or worker-style services, for operations. |
| T1597.002 | Purchase Technical Data | Use when adversaries purchase technical information about victims that can be used during targeting. The purchase aspect is required. |
| T1133 | External Remote Services | Use when adversaries leverage external-facing remote services to initially access and/or persist within a network. Examples include VPNs, Citrix, and other externally exposed remote access services. |
| T1566.002 | Spearphishing Link | Use when adversaries send spearphishing emails with a malicious link in an attempt to gain access to victim systems. The link mechanism should be explicit. |
| T1598.003 | Spearphishing Link | Boundary note: spearphishing links may be used to capture credentials and can enable later bypass of MFA via web session cookie theft, but do not infer those follow-on techniques unless the text explicitly states them. |
| T1566.002 | Spearphishing Link | Boundary note: malicious links may use deceptive URL formatting tricks, including integer- or hexadecimal-based hostnames or text before an @ symbol, but the ATT&CK mapping remains spearphishing link when the behavior is phishing via malicious link. |
| T1218.011 | Rundll32 | Use when adversaries abuse rundll32.exe to proxy execution of malicious code. Explicit rundll32 use supports this sub-technique. |
| T1216.001 | PubPrn | Use when adversaries use PubPrn.vbs to proxy execution of malicious remote files. Explicit PubPrn.vbs use supports this sub-technique. |
| T1218.004 | InstallUtil | Use when adversaries use InstallUtil to proxy execution of code through a trusted Windows utility. Explicit InstallUtil use supports this sub-technique. |
| T1218.013 | Mavinject | Use when adversaries abuse mavinject.exe to proxy execution of malicious code. Explicit mavinject use supports this sub-technique. |
| T1059.007 | JavaScript | Use when adversaries abuse JavaScript or JScript implementations for execution. Explicit JavaScript execution supports this sub-technique. |
| T1547 | Boot or Logon Autostart Execution | Use when adversaries configure system settings to automatically execute a program during system boot or logon to maintain persistence or gain higher-level privileges, but the exact autostart mechanism is not specified. |
| T1543 | Create or Modify System Process | Use when adversaries create or modify system-level processes to repeatedly execute malicious payloads as part of persistence. Use the parent when the exact process type is not specified. |
| T1543.003 | Windows Service | Use when adversaries create or modify Windows services to repeatedly execute malicious payloads as part of persistence. Explicit Windows service creation or modification supports this sub-technique. |
| T1037 | Boot or Logon Initialization Scripts | Use when adversaries use scripts automatically executed at boot or logon initialization to establish persistence. |
| T1547.014 | Active Setup | Use when adversaries achieve persistence by adding a Registry key to Active Setup on the local machine. Explicit Active Setup abuse supports this sub-technique. |
| T1548.002 | Bypass User Account Control | Use when adversaries bypass Windows User Account Control mechanisms to elevate process privileges on a system. |
| T1574.001 | DLL | Use when adversaries abuse DLL files to achieve persistence, escalate privileges, or evade defenses. Explicit DLL hijacking, search-order hijacking, side-loading, or related path abuse supports this sub-technique. |
| T1543.003 | Windows Service | Boundary note: Windows service abuse may also involve vulnerable drivers or related elevated execution contexts, but do not infer exploitation for privilege escalation unless that separate behavior is explicitly described. |
| T1027.011 | Fileless Storage | Use when adversaries store data in fileless formats to conceal malicious activity from defenses. This includes non-file storage locations used instead of ordinary files. |
| T1036.008 | Masquerade File Type | Use when adversaries masquerade malicious payloads as legitimate files through changes to formatting, signature, extension, icon, or apparent file type. |
| T1564 | Hide Artifacts | Use when adversaries attempt to hide artifacts associated with their behaviors to evade detection, when the exact hiding method is not specified. |
| T1564.012 | File/Path Exclusions | Use when adversaries hide file-based artifacts by writing them to folders or file names excluded from antivirus or defender scanning. |
| T1027.013 | Encrypted/Encoded File | Use when adversaries encrypt or encode files to obfuscate strings, bytes, or patterns and impede detection. |
| T1003 | OS Credential Dumping | Use when adversaries dump credentials to obtain account login and credential material, such as hashes or cleartext passwords, from OS credential sources when the exact source is not specified. |
| T1056.001 | Keylogging | Use when adversaries log user keystrokes to intercept credentials or other typed information. |
| T1040 | Network Sniffing | Use when adversaries passively sniff network traffic to capture information about an environment, including authentication material passed over the network. |
| T1555.005 | Password Managers | Use when adversaries acquire user credentials from third-party password managers. |
| T1003.004 | LSA Secrets | Use when adversaries with SYSTEM-level access attempt to access Local Security Authority secrets, which can contain credential material. |
| T1033 | System Owner/User Discovery | Use when adversaries identify the primary user, currently logged-in user, common users of a system, or whether a user is actively using the system. |
| T1087.001 | Local Account | Use when adversaries list or discover local system accounts. |
| T1087.002 | Domain Account | Use when adversaries list or discover domain accounts. |

## Additional usage notes

- Treat these rows as authoritative supplemental mappings.
- If a row here is more specific than a parent technique elsewhere, prefer the specific row when the mechanism is explicit.
- Boundary-note rows clarify what not to infer automatically from adjacent behavior.