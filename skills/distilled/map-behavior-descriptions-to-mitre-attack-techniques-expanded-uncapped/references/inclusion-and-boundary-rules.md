# Inclusion and boundary rules for ATT&CK prediction from prose

## Include a technique when the text gives direct behavioral evidence

Strong evidence includes:
- Explicit mechanism names: HTTP, HTTPS, DNS, FTP, MQTT, AMQP, cmd.exe, PowerShell, JavaScript, WMI, WMI event subscription, Run key, Startup folder, Keychain, Credential Manager, password manager, SAM, LSA secrets, PubPrn.vbs, rundll32, InstallUtil, mavinject, VPN, Citrix, DLL hijacking, UAC bypass, Active Setup.
- Explicit actions: list directories, collect local files, automate collection, enumerate processes, enumerate services, enumerate drivers, detect antivirus, inject code into a process, execute via WMI, clear command history, delete files, modify timestamps, steal clipboard data, collect email, collect from databases, sniff traffic, perform AiTM, stage data locally, keylog, create service, modify service, use initialization scripts, search victim-owned websites, search passive DNS, purchase technical data, gather victim host information before compromise.
- Explicit targets: domain users, domain groups, cloud accounts, trusts, Wi-Fi profiles, Internet connectivity, backup software, security software, victim host hardware, password stores, excluded paths.

Direct evidence can be short. If the wording clearly states the action or mechanism, that is enough.

## Prefer the most specific supported technique

Examples:
- HTTP/HTTPS/web C2 -> **T1071.001**, not only **T1071**.
- DNS C2 -> **T1071.004**.
- Pub/sub C2 -> **T1071.005**.
- cmd.exe / Windows command shell -> **T1059.003**.
- PowerShell -> **T1059.001**.
- JavaScript/JScript -> **T1059.007**.
- WMI execution -> **T1047**.
- WMI event subscription -> **T1546.003**.
- Browser credential theft -> **T1555.003**.
- Windows Credential Manager theft -> **T1555.004**.
- Keychain theft -> **T1555.001**.
- Password manager theft -> **T1555.005**.
- SAM dumping -> **T1003.002**.
- LSA secrets extraction -> **T1003.004**.
- Run keys / Startup folder -> **T1547.001**.
- PowerShell profile persistence -> **T1546.013**.
- File-type disguise via extension/icon/signature/content -> **T1036.008**.
- Hidden files/directories -> **T1564.001**.
- AV-excluded path abuse -> **T1564.012**.
- Fast flux -> **T1568.001**.
- Victim hardware research before compromise -> **T1592.001**.
- Windows service creation or modification -> **T1543.003**.
- Active Setup persistence -> **T1547.014**.
- Spearphishing email with malicious link -> **T1566.002**.
- InstallUtil abuse -> **T1218.004**.
- Mavinject abuse -> **T1218.013**.
- PubPrn.vbs abuse -> **T1216.001**.
- Rundll32 abuse -> **T1218.011**.
- Keylogging -> **T1056.001**.
- Search victim-owned websites -> **T1594**.
- Search DNS/passive DNS for victim information -> **T1596.001**.
- Purchase technical data about victims -> **T1597.002**.

## Use the parent technique when specificity is not supported

Examples:
- Generic application-layer C2 with no protocol named -> **T1071**.
- Generic command interpreter use with no interpreter named -> **T1059**.
- Generic password-store theft with no store named -> **T1555**.
- Generic OS credential dumping with no source named -> **T1003**.
- Generic event-triggered execution with no mechanism named -> **T1546**.
- Generic boot/logon autostart with no mechanism named -> **T1547**.
- Generic account discovery with no scope named -> **T1087**.
- Generic group/role discovery with no scope named -> **T1069**.
- Generic infrastructure acquisition with no type named -> **T1583**.
- Generic victim host information gathering before compromise -> **T1592**.
- Generic create or modify system process with no OS-specific service detail -> **T1543**.

## Allow multiple valid techniques when the text supports multiple behaviors

Include all distinct behaviors explicitly present, for example:
- **T1083** plus **T1005** when the text says the malware both enumerates files and collects them.
- **T1033** plus **T1082** plus **T1016** when the text separately mentions current user, host details, and network configuration.
- **T1087.002** plus **T1069.002** plus **T1482** plus **T1018** when the text separately mentions domain users, domain groups, trusts, and remote systems.
- **T1071.001** plus **T1105** when the text says the malware uses HTTP/HTTPS C2 and downloads payloads.
- **T1119** plus **T1074.001** when the text says data is automatically collected and then staged locally.
- **T1557** plus **T1040** only when the text explicitly supports both active interception and passive sniffing.
- **T1543.003** plus **T1548.002** may both apply when a Windows service is created or modified and the text separately states privilege elevation via UAC bypass.

## Avoid common over-predictions

Do not add a technique just because it is adjacent or common:
- A malware label such as RAT, downloader, worm, spyware, trojan, stealer, loader, or backdoor does not itself map to a technique.
- Encryption, decryption, hashing, packing, or programming language details do not automatically justify a technique unless tied to an ATT&CK behavior.
- A downloader does not automatically imply persistence.
- A backdoor does not automatically imply keylogging, credential theft, or lateral movement.
- Generic process injection does not automatically imply hollowing, APC, DLL injection, or ptrace.
- Generic masquerading does not automatically imply a specific sub-technique unless the exact method is stated.
- Generic hiding does not automatically imply a specific T1564 sub-technique unless the exact method is stated.
- Generic DNS use does not imply DNS C2; the text must indicate command-and-control or covert communication use.
- Generic WMI mention does not imply WMI event subscription; the text must indicate event consumer/filter/binding or event-triggered persistence.
- Generic DLL use does not imply DLL hijacking; the text must indicate hijacking, side-loading, or search-order/path abuse.
- Mention of phishing alone does not imply spearphishing link; the text must indicate a malicious link rather than an attachment or generic social engineering.
- Mention of remote services alone does not imply external remote services; the service must be external-facing or used for initial access/persistence from outside the environment.

## Resolve common ambiguities carefully

- "list files", "search directories", "get file metadata" -> **T1083**, not **T1005**.
- "read local files", "collect documents", "steal config files" -> **T1005**.
- "automatically gathers internal data" -> **T1119**.
- "stage data locally" -> **T1074.001**.
- "get username/current user" -> **T1033**, not **T1087** unless multiple accounts are enumerated.
- "get OS version/hostname/architecture" -> **T1082**.
- "get IP/MAC/DNS/gateway" -> **T1016**.
- "check Internet access" -> **T1016.001**.
- "enumerate Wi-Fi profiles/passwords" -> **T1016.002**.
- "enumerate installed software" -> **T1518**; if specifically security tools -> **T1518.001**; if specifically backup tools -> **T1518.002**.
- "enumerate services" -> **T1007**.
- "enumerate drivers" -> **T1652**.
- "hide files" -> **T1564.001**; "pretend to be a document/image" -> **T1036.008**.
- "overwrite process arguments" or similar wording may support a hiding or masquerading sub-technique in broader ATT&CK coverage, but only include one if the exact ATT&CK behavior is directly supported by the wording available in your bundled references.
- "sniff traffic" -> **T1040**; "intercept traffic between parties" -> **T1557**.
- "victim host information gathered during targeting" -> **T1592**; "host information gathered on the compromised machine" -> **T1082**.
- "hardware information gathered during targeting" -> **T1592.001**; "hardware details discovered on-host after compromise" -> **T1082**.
- "uses VPN/Citrix/external remote service" -> **T1133** when used for initial access or persistence through external-facing services.
- "uses shared drive/repository to spread payload" -> **T1080**.
- "uses WMI to run commands" -> **T1047**; "creates WMI event consumer/filter/binding" -> **T1546.003**.
- "creates or modifies a Windows service" -> **T1543.003**; if only generic recurring execution via system process is stated -> **T1543**.
- "boot or logon script" -> **T1037**; generic autostart at boot/logon with no script detail -> **T1547**.
- "Active Setup" -> **T1547.014**.
- "rundll32" -> **T1218.011**, not **T1574.001** unless DLL hijacking/search-order abuse is separately described.
- "InstallUtil" -> **T1218.004**.
- "mavinject" -> **T1218.013**.
- "PubPrn.vbs" -> **T1216.001**.
- "search victim-owned websites" -> **T1594**, not generic web browsing.
- "search passive DNS" -> **T1596.001**, not DNS C2.
- "purchase technical victim data" -> **T1597.002**, not generic victim research.
- Spearphishing links may support credential theft follow-on behaviors only if the text separately states credential capture, session theft, or related actions; do not infer those automatically.

## Output hygiene

- Output a list of ATT&CK IDs as strings.
- One object per input row.
- No duplicate IDs within a row.
- Use an empty list if no technique is directly supported.
- Normally do not output both a parent and its child for the same behavior.
- Favor explicit, evidence-backed coverage over overly conservative omission.