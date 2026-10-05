# MITRE ATT&CK Behavior-to-Technique Mapping Reference

Use this reference to map observable adversary behavior in text to ATT&CK technique IDs. Prefer the most specific technique supported by the wording, but do not over-assert sub-techniques when the mechanism is unclear.

## Core rules

- Map **behavior described in the text**, not malware names, actor names, file hashes, languages, or vendor labels.
- Prefer a **sub-technique** when the mechanism is explicit; otherwise use the **parent** technique.
- Include **all independently supported behaviors** in the description.
- Do **not** infer adjacent steps that are plausible but unstated.
- If the text names a utility, protocol, credential store, startup point, or medium that ATT&CK treats as a specific sub-technique, use that sub-technique.
- If the text only states an outcome without mechanism detail, use the nearest justified parent technique.
- Delivery, execution, persistence, credential access, discovery, collection, command and control, exfiltration, and impact can all co-occur in one description.
- Reconnaissance and resource development are valid ATT&CK mappings when the text describes pre-compromise targeting or infrastructure preparation.

---

## High-value decision rules

### Parent vs sub-technique
- Use **T1071.001 Web Protocols** for HTTP/HTTPS C2; **T1071.004 DNS** for DNS C2; **T1071.005 Publish/Subscribe Protocols** for pub/sub protocols such as MQTT or similar brokered publish/subscribe messaging. Use **T1071** only when the application-layer protocol is not specified.
- Use **T1059.003 Windows Command Shell** when `cmd.exe`, command shell, or Windows shell is explicit; otherwise **T1059**.
- Use **T1218.011 Rundll32** when `rundll32.exe` is named.
- Use **T1218.013 Mavinject** when `mavinject.exe` is named.
- Use **T1003.002 Security Account Manager** or **T1003.004 LSA Secrets** when those stores are explicitly targeted; otherwise **T1003** for generic OS credential dumping.
- Use **T1592.001 Hardware** when host hardware details are explicitly gathered during targeting; otherwise **T1592** for generic victim host information gathering.
- Use **T1087.002 Domain Account** and **T1069.002 Domain Groups** when domain scope is explicit; otherwise use the parent techniques.
- Use **T1566.001 Spearphishing Attachment** or **T1566.002 Spearphishing Link** for phishing used to gain access; use **T1598.003 Spearphishing Link** when the phishing link is used to elicit information during targeting rather than to execute malware or gain system access.

### Delivery vs execution
- A malicious attachment sent by email is **T1566.001**.
- A malicious link sent by email for access is **T1566.002**.
- A user opening a malicious document, archive, executable, or lure file is **T1204.002 Malicious File**.
- These may co-occur. Delivery by phishing and execution by user action are separate behaviors.

### Discovery vs collection
- **Discovery** identifies what exists: listing files, users, groups, processes, software, hosts, trusts, or configuration.
- **Collection** obtains the content itself: reading files, capturing clipboard, recording audio, harvesting data, or bulk gathering.
- File listing alone is **T1083 File and Directory Discovery**, not **T1005 Data from Local System**.
- If the text says both enumerate and steal/read/copy, include both discovery and collection techniques.

### Injection and execution nuance
- Generic code injection into another process → **T1055 Process Injection**.
- Explicit **Extra Window Memory Injection** → **T1055.011**.
- Loading a malicious DLL/shared library/module for execution → **T1129 Shared Modules**.
- DLL hijacking/search-order abuse/preload abuse → **T1574.001 DLL**.
- Do not map generic shellcode injection to process hollowing or another named subtype unless that exact mechanism is described.

### Credential access nuance
- Generic dumping of credentials from OS memory or stores → **T1003**.
- SAM database or SAM hashes → **T1003.002**.
- LSA secrets → **T1003.004**.
- Keystroke capture → **T1056.001 Keylogging**.
- macOS Keychain credential theft → **T1555.001 Keychain**.
- Passive packet capture/sniffing → **T1040 Network Sniffing**.
- Positioning between communicating parties to intercept traffic or credentials → **T1557 Adversary-in-the-Middle**.

### Obfuscation and concealment nuance
- Generic hidden files/windows/artifacts → **T1564 Hide Artifacts**.
- Mailbox rules used to hide inbound emails → **T1564.008 Email Hiding Rules**.
- AV/EDR exclusions or excluded paths/files → **T1564.012 File/Path Exclusions**.
- Payload embedded inside another file → **T1027.009 Embedded Payloads**.
- Data stored in non-file or fileless formats to conceal activity → **T1027.011 Fileless Storage**.
- Files encrypted or encoded to impede analysis/detection → **T1027.013 Encrypted/Encoded File**.
- Symbols/strings stripped from payloads → **T1027.008 Stripped Payloads**.
- Standard encoding applied to command-and-control data → **T1132.001 Standard Encoding**.
- Do not map generic “encrypted traffic” or “packed malware” unless the wording clearly matches one of these ATT&CK behaviors.

### Social engineering and targeting nuance
- Spearphishing can appear in two ATT&CK phases: **T1566.x** for access and **T1598.x** for information gathering during targeting.
- Compromised social media accounts used for targeting/social engineering → **T1586.001 Social Media Accounts**.
- Purchased victim technical information → **T1597.002 Purchase Technical Data**.
- Acquired vulnerability information for targeting or operations → **T1588.006 Vulnerabilities**.
- Queries to public AI services to support targeting or operations → **T1682 Query Public AI Services**.
- Obtaining access to generative AI tools for operations → **T1588.007 Artificial Intelligence**.

### Infrastructure and protocol nuance
- External-facing VPN, Citrix, remote desktop gateway, or similar remote service used for access/persistence → **T1133 External Remote Services**.
- Own or attacker-controlled DNS server infrastructure → **T1583.002 DNS Server**.
- Fast Flux DNS used to hide or rotate C2 infrastructure → **T1568.001 Fast Flux DNS**.
- Third-party network devices compromised for targeting or infrastructure use → **T1584.008 Network Devices**.

---

## Behavior mapping table

| Description cue | ATT&CK technique | Notes |
|---|---|---|
| gather victim host information during targeting | **T1592 – Gather Victim Host Information** | Reconnaissance against victim hosts. |
| gather victim hardware details during targeting, such as device model, hardware inventory, peripherals, architecture | **T1592.001 – Hardware** | Use when hardware specifics are explicit. |
| purchase victim technical data or technical information | **T1597.002 – Purchase Technical Data** | Reconnaissance by purchase. |
| acquire information about vulnerabilities for targeting or operations | **T1588.006 – Vulnerabilities** | Resource development / capability acquisition. |
| compromise third-party routers or other network devices for targeting or infrastructure | **T1584.008 – Network Devices** | Compromised infrastructure. |
| query public AI services to support targeting, planning, content generation, or operations | **T1682 – Query Public AI Services** | Publicly accessible AI services. |
| obtain access to generative AI tools for operations | **T1588.007 – Artificial Intelligence** | Acquire capability/tool access. |
| compromise social media accounts for targeting or social engineering | **T1586.001 – Social Media Accounts** | Accounts used during targeting. |
| set up or control DNS server infrastructure | **T1583.002 – DNS Server** | Adversary-owned infrastructure. |
| spearphishing email with malicious attachment for access | **T1566.001 – Spearphishing Attachment** | Initial access via targeted email attachment. |
| spearphishing email with malicious link for access | **T1566.002 – Spearphishing Link** | Initial access via targeted email link. |
| spearphishing message with malicious link to elicit information during targeting | **T1598.003 – Spearphishing Link** | Reconnaissance/social engineering for information. |
| use external-facing VPN, Citrix, remote desktop gateway, or similar remote service for access or persistence | **T1133 – External Remote Services** | Applies to initial access and sometimes persistence. |
| execute commands via shell, command interpreter, or command line with no subtype detail | **T1059 – Command and Scripting Interpreter** | Parent when shell type is unclear. |
| execute commands via `cmd.exe`, Windows shell, or remote Windows command shell | **T1059.003 – Windows Command Shell** | Windows-specific shell execution. |
| user opens malicious document, archive, executable, or lure file | **T1204.002 – Malicious File** | User execution of a malicious file. |
| abuse `rundll32.exe` to execute malicious code | **T1218.011 – Rundll32** | Specific signed binary proxy execution sub-technique. |
| abuse `mavinject.exe` to execute or inject malicious code | **T1218.013 – Mavinject** | Specific signed binary proxy execution sub-technique. |
| load malicious DLL/shared library/module for execution | **T1129 – Shared Modules** | Execution via shared modules. |
| inject code into another process, remote thread injection, shellcode injection | **T1055 – Process Injection** | Generic process injection. |
| extra window memory injection, EWM-based injection | **T1055.011 – Extra Window Memory Injection** | Use only when this mechanism is explicit. |
| boot or logon initialization scripts used for persistence | **T1037 – Boot or Logon Initialization Scripts** | Script-based startup persistence. |
| create or modify service, daemon, launch agent, or other system process for persistence | **T1543 – Create or Modify System Process** | Parent when subtype is not explicit. |
| create or modify Windows service | **T1543.003 – Windows Service** | Use when Windows service semantics are explicit. |
| boot or logon autostart execution with unspecified subtype | **T1547 – Boot or Logon Autostart Execution** | Parent persistence technique. |
| Run keys, Startup folder, CurrentVersion\\Run | **T1547.001 – Registry Run Keys / Startup Folder** | Common Windows persistence. |
| Office add-ins, templates, startup folders, or Office startup persistence | **T1137 – Office Application Startup** | Office-based persistence. |
| scheduled execution via task scheduler or recurring scheduled task | **T1053.005 – Scheduled Task** | Windows scheduled task abuse. |
| DLL hijacking, DLL search order hijacking, preload abuse | **T1574.001 – DLL** | Hijacked DLL loading. |
| bypass UAC, auto-elevate abuse, eventvwr-style UAC bypass | **T1548.002 – Bypass User Account Control** | Privilege escalation or defense evasion. |
| dump credentials from OS stores or memory generically | **T1003 – OS Credential Dumping** | Parent credential dumping technique. |
| dump SAM database or extract SAM hashes | **T1003.002 – Security Account Manager** | Specific credential store. |
| dump LSA secrets | **T1003.004 – LSA Secrets** | Specific credential store. |
| crack password hashes or offline password cracking | **T1110.002 – Password Cracking** | Recover plaintext from hashes. |
| keylogging, capture keystrokes | **T1056.001 – Keylogging** | Specific input capture subtype. |
| generic input capture, form grabbing, intercept user input without clear subtype | **T1056 – Input Capture** | Parent when subtype is unclear. |
| acquire credentials from macOS Keychain | **T1555.001 – Keychain** | macOS credential store theft. |
| sniff network traffic to capture credentials or data | **T1040 – Network Sniffing** | Passive traffic capture. |
| adversary-in-the-middle, man-in-the-middle, intercept traffic between parties | **T1557 – Adversary-in-the-Middle** | Positioning between communicating systems. |
| identify current user, logged-in user, account owner | **T1033 – System Owner/User Discovery** | User identity discovery. |
| enumerate groups or permission groups generically | **T1069 – Permission Groups Discovery** | Parent group discovery. |
| enumerate domain groups | **T1069.002 – Domain Groups** | Domain-scoped group discovery. |
| enumerate accounts generically | **T1087 – Account Discovery** | Parent account discovery. |
| enumerate domain accounts or domain users | **T1087.002 – Domain Account** | Domain-scoped account discovery. |
| list files, directories, paths, or file metadata | **T1083 – File and Directory Discovery** | Discovery only. |
| enumerate processes or running tasks | **T1057 – Process Discovery** | Running process discovery. |
| gather OS version, hostname, hardware, adapters, IP, MAC, DNS, gateway, system configuration | **T1082 – System Information Discovery** | Host/system information discovery. |
| discover installed software generically | **T1518 – Software Discovery** | Generic software enumeration. |
| discover antivirus, EDR, firewall, or security tools | **T1518.001 – Security Software Discovery** | Security-specific software discovery. |
| discover remote hosts, systems, subnets, shares, or network neighbors | **T1018 – Remote System Discovery** | Network/remote system discovery. |
| discover domain trusts | **T1482 – Domain Trust Discovery** | AD trust relationships. |
| collect files or data from local host | **T1005 – Data from Local System** | Reading/copying local data. |
| collect data from removable media | **T1025 – Data from Removable Media** | Search or collect from USB/removable drives. |
| automated harvesting or scheduled/bulk collection of internal data | **T1119 – Automated Collection** | Automated collection workflows. |
| stage data locally before exfiltration | **T1074.001 – Local Data Staging** | Local staging area or archive. |
| capture audio from microphone or calls | **T1123 – Audio Capture** | Audio collection. |
| steal or monitor clipboard contents | **T1115 – Clipboard Data** | Clipboard collection. |
| download payloads, tools, or files from C2 or remote source | **T1105 – Ingress Tool Transfer** | Bringing tools/files into victim environment. |
| command and control over application-layer protocol, protocol unspecified | **T1071 – Application Layer Protocol** | Parent C2 protocol technique. |
| command and control over HTTP or HTTPS | **T1071.001 – Web Protocols** | Web-based C2. |
| command and control over DNS | **T1071.004 – DNS** | Use only when DNS is explicit. |
| command and control over publish/subscribe protocols such as brokered pub/sub messaging | **T1071.005 – Publish/Subscribe Protocols** | Use when pub/sub semantics are explicit. |
| use Fast Flux DNS to hide or rotate C2 infrastructure | **T1568.001 – Fast Flux DNS** | Dynamic DNS/IP rotation. |
| encode C2 data using standard encodings such as base64 | **T1132.001 – Standard Encoding** | Encoding of command/data in C2. |
| hide artifacts, hidden files, hidden windows, conceal presence | **T1564 – Hide Artifacts** | Parent hide-artifacts technique. |
| use mailbox or inbox rules to hide inbound emails | **T1564.008 – Email Hiding Rules** | Email concealment. |
| use AV exclusions, excluded paths, excluded filenames | **T1564.012 – File/Path Exclusions** | Specific hide-artifacts subtype. |
| virtualization, sandbox, debugger, or analysis-environment checks | **T1497.001 – System Checks** | Anti-analysis environment checks. |
| exploit security software or defensive infrastructure to disable or impair it | **T1687 – Exploitation for Defense Impairment** | Defense impairment by exploitation. |
| spoof or alter security tool UI/status indicators | **T1685.003 – Modify or Spoof Tool UI** | Deceptive UI manipulation. |
| payload embedded inside another file to conceal malicious content | **T1027.009 – Embedded Payloads** | Embedded malicious content. |
| store malicious data or payloads in fileless/non-file formats | **T1027.011 – Fileless Storage** | Concealed storage outside normal files. |
| encrypt or encode files to impede analysis or detection | **T1027.013 – Encrypted/Encoded File** | File-level obfuscation. |
| strip symbols, strings, or readable information from payloads | **T1027.008 – Stripped Payloads** | Analysis resistance. |
| masquerade as legitimate file, app, or trusted brand generically | **T1036 – Masquerading** | Parent masquerading technique. |
| disguise malicious file as benign file type or extension | **T1036.008 – Masquerade File Type** | Explicit file-type disguise. |
| replicate or spread via USB/removable media | **T1091 – Replication Through Removable Media** | Propagation via removable media. |

---

## Category checklist for unseen descriptions

Use this checklist to avoid missing whole ATT&CK phases.

### Reconnaissance
- Victim host information → **T1592**
- Victim hardware details → **T1592.001**
- Purchased technical data → **T1597.002**
- Spearphishing link for information gathering → **T1598.003**
- Query public AI services → **T1682**

### Resource Development
- Acquire vulnerabilities → **T1588.006**
- Acquire access to AI tools → **T1588.007**
- Compromise social media accounts → **T1586.001**
- Set up DNS server infrastructure → **T1583.002**
- Compromise network devices for infrastructure/targeting → **T1584.008**

### Initial Access
- Spearphishing attachment → **T1566.001**
- Spearphishing link for access → **T1566.002**
- External remote services → **T1133**

### Execution
- Command/scripting interpreter → **T1059** / **T1059.003**
- Shared modules → **T1129**
- Rundll32 → **T1218.011**
- Mavinject → **T1218.013**
- User opens malicious file → **T1204.002**
- Process injection → **T1055** / **T1055.011**

### Persistence
- Boot/logon initialization scripts → **T1037**
- Boot/logon autostart → **T1547**
- Run keys / Startup folder → **T1547.001**
- Office application startup → **T1137**
- Scheduled task → **T1053.005**
- Create/modify system process → **T1543** / **T1543.003**
- DLL hijacking for persistence → **T1574.001**

### Privilege Escalation
- Bypass UAC → **T1548.002**
- DLL hijacking for escalation → **T1574.001**
- Create/modify privileged service/process → **T1543** / **T1543.003**

### Defense Evasion
- Hide artifacts → **T1564**
- Email hiding rules → **T1564.008**
- File/path exclusions → **T1564.012**
- Embedded payloads → **T1027.009**
- Fileless storage → **T1027.011**
- Encrypted/encoded file → **T1027.013**
- Stripped payloads → **T1027.008**
- Modify/spoof tool UI → **T1685.003**
- Exploitation for defense impairment → **T1687**
- System checks / anti-analysis → **T1497.001**
- DLL hijacking or UAC bypass may also serve evasion depending on wording.

### Credential Access
- OS credential dumping → **T1003**
- SAM → **T1003.002**
- LSA Secrets → **T1003.004**
- Password cracking → **T1110.002**
- Keylogging → **T1056.001**
- Generic input capture → **T1056**
- Keychain → **T1555.001**
- Network sniffing → **T1040**
- Adversary-in-the-middle → **T1557**

### Discovery
- System owner/user → **T1033**
- Permission groups → **T1069** / **T1069.002**
- Accounts → **T1087** / **T1087.002**
- Files/directories → **T1083**
- Processes → **T1057**
- System information → **T1082**
- Software/security software → **T1518** / **T1518.001**
- Remote systems → **T1018**
- Domain trusts → **T1482**

### Collection
- Data from local system → **T1005**
- Data from removable media → **T1025**
- Automated collection → **T1119**
- Local data staging → **T1074.001**
- Audio capture → **T1123**
- Clipboard data → **T1115**

### Command and Control
- Application layer protocol → **T1071**
- Web protocols → **T1071.001**
- DNS → **T1071.004**
- Publish/subscribe protocols → **T1071.005**
- Standard encoding of C2 data → **T1132.001**
- Fast Flux DNS → **T1568.001**
- Ingress tool transfer often co-occurs with C2 but is separate → **T1105**

### Lateral Movement / Propagation
- Replication through removable media → **T1091**
- External remote services may also support persistence/access across boundaries → **T1133**

---

## Ambiguity guidance

### When to include multiple techniques
Include multiple IDs when the text explicitly supports multiple distinct actions, for example:
- spearphishing attachment + user opens malicious file → **T1566.001** and **T1204.002**
- spearphishing link for access + user clicks/opens malicious content → **T1566.002** and possibly **T1204.002** if a malicious file is opened
- HTTP C2 + payload download → **T1071.001** and **T1105**
- DNS C2 + Fast Flux DNS → **T1071.004** and **T1568.001**
- file listing + file theft → **T1083** and **T1005**
- domain account enumeration + domain group enumeration + trust discovery → **T1087.002**, **T1069.002**, **T1482**
- scheduled task persistence + command shell execution → **T1053.005** and **T1059.003**
- phishing delivery + mailbox hiding rules → **T1566.x** and **T1564.008** when both are explicit

### When not to over-map
- “encrypted traffic” alone does not justify **T1071.001**, **T1071.004**, or **T1132.001**.
- “stealthy,” “evasive,” or “obfuscated” alone does not justify **T1564**, **T1497.001**, **T1687**, or **T1027.x** without concrete behavior.
- “credential theft” alone does not automatically justify **T1003**; require dumping/extraction from OS credential material or another explicit mechanism.
- “uses DLL” alone is not enough for **T1574.001**; ordinary DLL use may instead indicate **T1129** only if malicious module loading for execution is described.
- “downloads and executes” does not imply persistence unless a persistence mechanism is stated.
- “phishing link” is not always **T1566.002**; if the purpose is eliciting information during targeting rather than gaining access, use **T1598.003**.
- “host information” during post-compromise host enumeration is often **T1082**, while victim host information gathered during targeting is **T1592**.
- “AI use” is not always one technique: querying public AI services is **T1682**, while obtaining access to AI tools is **T1588.007**.

### Practical wording cues
- **enumerate, list, query, inspect, gather info about** → often discovery or reconnaissance
- **read, copy, steal, capture, harvest, dump** → often collection or credential access
- **load, execute, run, invoke, launch** → execution
- **persist, autostart, startup, service, run key, scheduled** → persistence
- **inject, hollow, hook** → injection/execution/credential access depending on target and wording
- **hide, exclude, spoof, bypass, impair defenses** → defense evasion
- **targeting, pretext, lure, victim profiling** → reconnaissance/social engineering before compromise
- **beacon, callback, C2, command channel** → command and control

---

## Output reminder

For each row, produce a deduplicated list of ATT&CK IDs justified by the text, for example:

```json
{"row_id": 1, "prediction": ["T1071.001", "T1105"]}
```

Only include IDs that are directly supported by the description.