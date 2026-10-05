# ATT&CK decision rules for ambiguous behavior descriptions

## 1) Extract evidence as action + object + mechanism + platform + scope

Do not map from isolated nouns alone. Convert text into evidence such as:
- **action**: execute, dump, enumerate, hide, sniff, collect, persist, elevate, exfiltrate, impair
- **object**: credentials, files, services, domain users, traffic, payloads, websites, network devices
- **mechanism**: HTTP, JavaScript, rundll32, scheduled task, Active Setup, Keychain, VNC, Gatekeeper, COM, VPN
- **platform**: Windows, Linux, macOS, cloud, mobile, network device, identity, pre-compromise
- **scope**: initial access, execution, persistence, discovery, collection, C2, exfiltration, impact

This reduces false matches between nearby techniques.

## 2) Prefer explicit mechanisms, but allow strong implication

Use the most specific sub-technique when the mechanism is named or unmistakable.
Examples:
- `HTTP`, `HTTPS`, `GET`, `POST`, `web request`, `beacon to URL` -> **T1071.001**
- `JavaScript`, `JScript`, `JXA`, `.js` -> **T1059.007**
- `COM object`, `Component Object Model` -> **T1559.001**
- `rundll32` -> **T1218.011**
- `mavinject` -> **T1218.013**
- `scheduled task`, `Task Scheduler` -> **T1053.005**
- `Active Setup` -> **T1547.014**
- `Windows service` -> **T1543.003**
- `LSA Secrets` -> **T1003.004**
- `Keychain` -> **T1555.001**
- `password manager` -> **T1555.005**
- `VNC` -> **T1021.005**
- `malicious file/attachment opened by user` -> **T1204.002**
- `website infects visitors through browsing` -> **T1608.004**
- `exposed VPN/Citrix/remote gateway access` -> **T1133**

If the mechanism is not specific enough, use the parent technique instead of forcing a sub-technique.

## 3) Do not over-constrain to exact keywords

Descriptions may imply ATT&CK behaviors indirectly. Accept common paraphrases and outcomes when they clearly indicate the same mechanism.
Examples:
- `beacons to a web server`, `posts to a panel`, `contacts URL endpoint` -> **T1071.001**
- `records keyboard input`, `captures typed credentials` -> **T1056.001**
- `profiles victim hardware before targeting` -> **T1592.001**
- `uses exposed remote access portal` -> **T1133**
- `creates recurring job for execution` on Windows -> **T1053.005** if clearly a scheduled task
- `stores collected files in a temp folder before sending` -> **T1074.001**

Strong implication is enough when the mechanism is standard and recognizable.

## 4) Initial access vs user execution

These often co-occur but are not interchangeable.
- Delivery by phishing link -> **T1566.002**
- Delivery by phishing attachment -> **T1566.001**
- User opens malicious file -> **T1204.002**
- User clicks malicious link -> **T1204.001**
- Drive-by website prepared to infect visitors -> **T1608.004**

If both delivery and user action are described, include both.

## 5) Protocol vs encoding vs encrypted artifact

These often co-occur and should not replace one another.
- Web-based C2 channel -> **T1071.001**
- Standard encoding such as Base64 -> **T1132.001**
- Non-standard/custom encoding -> **T1132.002**
- Encrypted or encoded file/payload/config artifact -> **T1027.013**

A single description may support more than one of these.

## 6) Discovery vs collection vs staging

Use **Discovery** when the adversary learns what exists.
Use **Collection** when the adversary gathers the content itself.
Use **Staging** when collected data is organized before exfiltration.

Examples:
- list files, inspect directories, retrieve metadata -> **T1083**
- gather local files for theft -> **T1005**
- collect screenshots -> **T1113**
- collect clipboard contents -> **T1115**
- automated recurring collection -> **T1119**
- store gathered data in a local staging folder -> **T1074.001**

Do not map file enumeration alone to data theft.

## 7) Sniffing vs adversary-in-the-middle

- Passive packet capture or traffic sniffing -> **T1040**
- Positioning between parties to intercept, relay, downgrade, or alter communications -> **T1557**

If both are clearly described, include both.
Do not map passive capture alone to adversary-in-the-middle.

## 8) Execution vs persistence vs privilege escalation

The same artifact can support different tactics depending on wording.
- `uses WMI to run commands` -> **T1047**
- `scheduled task created for recurring execution` -> **T1053.005**
- `Run key`, `Startup folder`, `Active Setup`, `Office startup` -> persistence under **T1547** / **T1137**
- `creates Windows service` -> **T1543.003**
- `bypasses UAC` -> **T1548.002**
- `uses sudo/sudoers/cached sudo` -> **T1548.003**
- `exploits vulnerability to gain SYSTEM/root/admin` -> **T1068**

Only add persistence when re-execution at boot, logon, startup, scheduled recurrence, or service/agent/daemon creation is supported.

## 9) Masquerading vs hidden artifacts vs trust subversion

- Pretending to be legitimate, trusted, or benign -> **T1036**
- Disguising extension/type/format/signature -> **T1036.008**
- Concealing presence, hidden files, hidden icon, exclusions -> **T1564** or a sub-technique
- Bypassing platform trust controls such as Gatekeeper -> **T1553.001**

A file can be both hidden and masqueraded if both behaviors are described.

## 10) Credential access distinctions

- Generic dumping from OS credential stores -> **T1003**
- LSA Secrets specifically -> **T1003.004**
- LSASS memory specifically -> **T1003.001**
- Password cracking -> **T1110.002**
- Keystroke capture -> **T1056.001**
- Password stores generally -> **T1555**
- macOS Keychain -> **T1555.001**
- Third-party password managers -> **T1555.005**

Prefer the narrower credential source when named.

## 11) Remote access wording

Do not confuse these:
- exposed VPN/Citrix/RDP gateway/remote portal used to gain access -> **T1133**
- remote desktop/SSH/SMB/VNC used to move laterally or control systems -> **T1021** family
- remote shell capability where shell commands are executed -> execution technique such as **T1059** family if shell execution is the described behavior
- downloader behavior -> **T1105**

Remote shell alone does not prove external remote services.
External remote services are about leveraging exposed remote access services.

## 12) Pre-compromise behaviors are valid ATT&CK mappings

Do not force everything into post-compromise enterprise behaviors.
Examples:
- develop malware -> **T1587.001**
- gather victim host information -> **T1592** family
- purchase victim technical data -> **T1597.002**
- compromise third-party network devices for operations -> **T1584.008**
- prepare a drive-by target website -> **T1608.004**

## 13) Platform-sensitive mapping matters

Use platform cues to avoid wrong IDs.
- `Keychain`, `launch agent`, `Gatekeeper` -> macOS-specific techniques
- `rundll32`, `Active Setup`, `Windows service`, `LSA Secrets` -> Windows-specific techniques
- `sudo`, `cron`, Unix shell -> Unix/Linux/macOS techniques
- `VNC` is cross-platform remote control but still maps specifically to **T1021.005**
- network device compromise during targeting points to **T1584.008**, not generic host compromise

Do not force Windows-specific techniques onto non-Windows descriptions.

## 14) Multi-technique rows are normal

Include multiple IDs when the text supports separate behaviors across tactics.
Examples of valid combinations:
- phishing attachment + malicious file user execution
- phishing link + malicious link user execution
- downloader + rundll32 execution + DLL side-loading
- scheduled task + UAC bypass + hidden files
- keylogging + password store theft + clipboard capture
- network sniffing + adversary-in-the-middle
- HTTP C2 + Base64 encoding + encrypted payload file
- collection + local staging + exfiltration over C2

Do not collapse a row to one tactic if multiple independent behaviors are present.

## 15) Family names and labels are weak evidence

Do not map from labels like `RAT`, `trojan`, `stealer`, `worm`, `dropper`, `backdoor`, or a malware family name unless the description also states concrete behavior.
Map from what the text says the adversary does.

## 16) Parent vs sub-technique fallback rule

When a description clearly supports a behavior category but not the exact mechanism, prefer the parent technique.
Examples:
- generic credential dumping -> **T1003**, not a specific sub-technique
- generic startup persistence -> **T1547**, not a specific sub-technique
- generic remote services for lateral movement -> **T1021**, not a specific protocol sub-technique
- generic command/script execution -> **T1059**, not a specific interpreter

Use sub-techniques only when the wording supports them.

## 17) Final selection checklist

Before finalizing each row:
1. Every ID is supported by a phrase or strong implication in the text.
2. No ID is added solely because it is common for that malware family or intrusion set.
3. Sub-techniques are used only when wording supports them.
4. Distinctions like initial access vs user execution, discovery vs collection, and sniffing vs adversary-in-the-middle were checked.
5. Platform cues were checked.
6. Duplicate IDs were removed.
7. IDs are formatted as `T####` or `T####.###`.
