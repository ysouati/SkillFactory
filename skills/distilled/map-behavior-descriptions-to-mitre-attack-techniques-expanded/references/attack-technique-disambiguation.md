# ATT&CK disambiguation and quality checks

## Core rule: map explicit or clearly implied behavior, not labels

Map what the text says the malware or actor does. Do not convert family names, campaign names, or generic malware categories directly into ATT&CK IDs. However, do not be so strict that you ignore broad but clearly supported behaviors.

## Prefer the most specific supported technique

Use the child when the wording clearly supports it:

- HTTP or HTTPS C2 -> **T1071.001** rather than **T1071**
- FTP or SFTP-style C2 -> **T1071.002** rather than **T1071**
- Email-based C2 -> **T1071.003** rather than **T1071**
- DNS C2 -> **T1071.004** rather than **T1071**
- Pub/sub C2 such as MQTT -> **T1071.005** rather than **T1071**
- PowerShell -> **T1059.001** rather than **T1059**
- cmd.exe or clearly Windows shell -> **T1059.003** rather than **T1059**
- Unix shell -> **T1059.004** rather than **T1059**
- JavaScript or JScript execution -> **T1059.007** rather than **T1059**
- Keylogging -> **T1056.001** rather than **T1056**
- Local accounts -> **T1087.001** rather than **T1087**
- Domain accounts -> **T1087.002** rather than **T1087**
- Domain groups -> **T1069.002** rather than **T1069**
- Security software discovery -> **T1518.001** rather than **T1518**
- Windows service creation or modification -> **T1543.003** rather than **T1543**
- WMI event subscription -> **T1546.003** rather than **T1546**
- Registry Run keys or Startup folder -> **T1547.001** rather than **T1547**
- Active Setup persistence -> **T1547.014** rather than **T1547**
- Hidden files or directories -> **T1564.001** rather than **T1564**
- Double extension -> **T1036.007** rather than **T1036**
- Masqueraded file type or fake extension/icon/signature/content -> **T1036.008** rather than **T1036**
- Process hollowing semantics -> **T1055.012** rather than **T1055**
- DLL hijacking or side-loading semantics -> **T1574.001** rather than a generic hijack label
- PATH environment variable hijack -> **T1574.007** rather than a generic hijack label
- Rundll32 execution -> **T1218.011** rather than generic command execution
- Mavinject execution -> **T1218.013** rather than generic process injection
- Disk structure wipe such as boot record or partition structure corruption -> **T1561.002** rather than **T1561**

## When to keep the broader parent

Use the parent when the behavior is clear but the subtype is not:

- **T1059** if command execution is clear but the interpreter is unspecified
- **T1071** if application-layer C2 is clear but the protocol is unspecified
- **T1056** if input capture is clear but not specifically keylogging, GUI capture, portal capture, or API hooking
- **T1087** if account discovery is described but local, domain, email, or cloud scope is unspecified
- **T1069** if group or permission discovery is described but scope is unspecified
- **T1518** if software enumeration is described but not specifically security or backup software
- **T1543** if system process or service-style persistence is clear but the exact mechanism is not
- **T1546** if event-triggered execution is clear but the trigger mechanism is unspecified
- **T1547** if boot or logon autostart is clear but the exact mechanism is unspecified
- **T1036** if masquerading is clear but the exact disguise method is unspecified
- **T1564** if hiding is clear but the exact hiding method is unspecified
- **T1222** if permissions modification is clear but platform-specific subtype is not
- **T1055** if process injection is clear but the exact injection method is not stated
- **T1561** if disk wiping is clear but the text does not specifically indicate disk structures needed for boot

## Do not be too conservative

If the text clearly supports a broad ATT&CK behavior, return the parent technique rather than leaving the row unmapped.

Examples:

- "executes shell commands" with no interpreter -> **T1059**
- "communicates with C2 using an application-layer protocol" -> **T1071**
- "captures user input" -> **T1056**
- "discovers accounts" -> **T1087**
- "enumerates groups" -> **T1069**
- "enumerates installed software" -> **T1518**
- "injects into another process" -> **T1055**
- "wipes disks" -> **T1561**
- "uses boot or logon autostart" -> **T1547**
- "uses event-triggered execution" -> **T1546**

## Multi-technique extraction is expected

Do not force one label per description. Many descriptions contain several independently supported behaviors.

Common valid combinations include:

- **T1083** file listing + **T1005** local data collection
- **T1033** current user discovery + **T1082** system information discovery
- **T1087.002** domain account discovery + **T1069.002** domain group discovery
- **T1113** screen capture + **T1114** email collection + **T1119** automated collection
- **T1074.001** local staging + **T1560.001** archive via utility
- **T1564.001** hidden files + **T1036** masquerading
- **T1557** adversary-in-the-middle + **T1040** network sniffing when both interception and passive capture are described
- **T1204.002** malicious file + **T1027.009** embedded payloads when a lure file contains concealed malicious content
- **T1543.003** Windows service + **T1548.002** UAC bypass when both persistence and elevation are described

## Discovery vs collection vs credential access

Keep these distinct:

- Listing files or directories -> **T1083 File and Directory Discovery**
- Searching local sources for files or reading local data of interest -> **T1005 Data from Local System**
- Searching removable drives for data -> **T1025 Data from Removable Media**
- Enumerating users, accounts, or groups -> **T1033**, **T1087**, **T1069** family as appropriate
- Capturing user input -> **T1056** family
- Dumping OS credentials -> **T1003**
- Sniffing network traffic for credentials or information -> **T1040**
- Stealing stored web session cookies -> **T1539**
- Collecting email content -> **T1114**
- Automated bulk gathering of data -> **T1119**

A single description may support several of these at once.

## Execution vs persistence

Do not confuse one-time execution with persistence:

- Running commands or scripts now -> **T1059** family or **T1047**
- Creating a scheduled task for recurring or delayed execution -> **T1053.005**
- Creating a service for persistence -> **T1543.003**
- Using Run keys or Startup folder -> **T1547.001**
- Using Active Setup -> **T1547.014**
- Using boot or logon initialization scripts -> **T1037**
- WMI event subscription for persistence -> **T1546.003**

If the text only says a mechanism was used to execute code once, do not automatically infer persistence unless recurring, startup, boot, logon, or trigger semantics are present.

## Masquerading vs hiding

These often co-occur but are different:

- **T1036** family: making something appear legitimate or benign
- **T1564** family: concealing the artifact from view or normal inspection

Examples:

- Benign-looking filename, fake extension, fake icon, or legitimate-looking service name -> **T1036** family
- Hidden attribute, hidden directory, hidden window, resource fork, or exclusions -> **T1564** family

If both are present, include both.

## Network communication nuance

Do not map every mention of network traffic to command and control.

Use **T1071** family only when the text indicates command exchange, beaconing, callbacks, remote tasking, or communication with a controller. If the text only says data was sent out, downloaded, relayed, or observed, do not force **T1071** without C2 semantics.

Use **T1040** when the behavior is passive sniffing or packet capture. Use **T1557** when the behavior is active interception or positioning between endpoints. Both may apply if both are described.

Use **T1105** for downloading or transferring tools or payloads into the victim environment, even if the same description also includes C2.

## Delivery and concealment nuance

- A malicious document or file that the user must open supports **T1204.002**.
- A payload concealed inside another file supports **T1027.009**.
- If both user execution and concealed embedding are described, both may apply.
- Shared folders, network drives, or repositories used to spread malicious content support **T1080**.
- Watering-hole or prepared browsing destinations that infect visitors support **T1608.004** when the behavior is about preparing the target environment for delivery.

## Infrastructure and pre-compromise nuance

Use **T1583**, **T1587.001**, **T1588.007**, **T1592**, or **T1608.004** only when the text is about obtaining, developing, or preparing capabilities or gathering victim information for targeting. Do not use them merely because post-compromise malware exists or communicates.

## Command shell nuance

- On Windows, "remote shell" often supports **T1059.003** if the context is clearly Windows shell execution.
- If platform or interpreter is unclear, use **T1059** instead of forcing **T1059.003**.

## Injection and hijack nuance

- Generic shellcode injection -> **T1055** unless the method is explicit.
- Suspended process plus image replacement -> **T1055.012**.
- DLL side-loading, search-order hijacking, or malicious DLL replacement -> **T1574.001**.
- PATH variable hijack -> **T1574.007**.
- Service registry hijack -> **T1574.011**.
- Do not map every DLL mention to **T1574.001**; the text must indicate hijacking, side-loading, replacement, or load-path abuse.

## Impact nuance

- Generic wiping or corruption of disk data -> **T1561**
- Boot record, partition table, or other disk structure corruption needed for boot -> **T1561.002**

Do not infer disk wipe from generic file deletion; file deletion is usually **T1070.004** unless the text clearly indicates destructive disk-level wiping.

## Output quality checklist

Before finalizing each row, verify:

1. Every technique is backed by explicit wording or a strong, direct behavioral implication in the description.
2. You did not miss additional independently supported behaviors in the same row.
3. You used the most specific supported technique, but not a more specific one than the text justifies.
4. You usually kept only the child instead of both parent and child.
5. You did not confuse discovery with collection, or credential dumping with input capture.
6. You did not convert implementation details, algorithms, or malware labels directly into ATT&CK IDs.
7. If the text supports only a broad behavior, you still returned the valid parent technique instead of leaving it blank.
8. You did not overpredict from vague words like "communicates," "uses malware," or "steals data" without enough detail for the specific ATT&CK concept.
9. You checked whether the description contains behaviors from more than one tactic and preserved all independently supported ones.