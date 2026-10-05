# ATT&CK behavior-to-technique family reference

Use this reference to map explicit behaviors in prose to ATT&CK techniques. Prefer the most specific sub-technique when the wording clearly supports it; otherwise use the parent technique. Normally do not output both parent and child for the same behavior unless hierarchical labels are explicitly required.

## High-level workflow

1. Identify the concrete action in the text.
2. Determine the ATT&CK tactic family it belongs to.
3. Check whether the text names a specific mechanism, protocol, artifact, store, or method.
4. If yes, choose the matching sub-technique.
5. If no, choose the parent technique that best matches the explicit behavior.
6. Include multiple techniques only when the text explicitly describes multiple distinct behaviors.

## Tactic-family cues

### Reconnaissance
Use when the text describes gathering information about a target before compromise.
- Victim identity, organization, or host details gathered pre-compromise -> reconnaissance techniques.
- Example distinction: pre-compromise host hardware research -> T1592.001, not post-compromise system information discovery.
- Search victim-owned websites for targeting information -> T1594.
- Search DNS or passive DNS data for victim information -> T1596.001.
- Purchase technical information about victims -> T1597.002.
- Spearphishing links used during targeting or delivery planning may appear in reconnaissance/resource-development context only when the text is clearly about preparing or sending phishing operations; otherwise map to initial access delivery behavior.

### Resource Development
Use when the text describes preparing capabilities or infrastructure before operations.
- Developing malware or malware components -> T1587.001.
- Acquiring domains, servers, VPS, DNS servers, web services, botnets, malvertising, or serverless infrastructure -> T1583 sub-techniques.
- Serverless cloud functions or workers used as attacker infrastructure -> T1583.007.

### Initial Access
Use when the text describes how access is first obtained.
- External remote services such as VPN, Citrix, RDP gateways, or externally exposed remote access services -> T1133.
- Spearphishing emails with malicious links -> T1566.002.
- Shared content used to deliver payloads to remote systems -> T1080.

### Execution
Use when the text describes running commands, scripts, binaries, or code.
- Named interpreters map to T1059 sub-techniques.
- Proxy execution via signed or trusted binaries maps to the relevant T1216 or T1218 sub-technique.
- WMI used to execute commands or payloads -> T1047.
- Named utilities such as rundll32, InstallUtil, PubPrn, or mavinject should map to their specific sub-techniques when explicitly named.

### Persistence
Use when the text describes surviving reboot, logon, or recurring execution.
- Boot/logon autostart mechanisms -> T1547 family.
- Event-triggered execution mechanisms -> T1546 family.
- Creating or modifying services or other system processes for recurring execution -> T1543 family.
- Initialization scripts at boot or logon -> T1037.
- Active Setup registry persistence -> T1547.014.

### Privilege Escalation
Use when the text describes gaining higher privileges.
- UAC bypass -> T1548.002.
- DLL hijacking or vulnerable service/process creation may support persistence and privilege escalation depending on wording.
- Service abuse may also support privilege escalation when the text indicates elevated execution context.

### Defense Evasion
Use when the text describes hiding, obfuscating, masquerading, exclusions, encoded payloads, embedded payloads, fileless storage, or indicator removal.
- Masquerading -> T1036 family.
- Hide artifacts -> T1564 family.
- Obfuscated or compressed files/information and related storage/embedding variants -> T1027 family rows in the catalog.
- Indicator removal and cleanup -> T1070 family.
- DLL hijacking and signed-binary proxy execution may also serve defense evasion when the text emphasizes bypassing detection or trust controls.

### Credential Access
Use when the text describes obtaining passwords, hashes, secrets, or stored credentials.
- OS credential dumping -> T1003 family.
- Password stores -> T1555 family.
- Input capture -> T1056 family.
- Network sniffing or AiTM may also support credential access when credentials are captured in transit.
- Keylogging -> T1056.001.

### Discovery
Use when the text describes learning about the compromised environment.
- Current user -> T1033.
- Accounts -> T1087 family.
- Groups/roles -> T1069 family.
- Host/system details -> T1082.
- Network configuration -> T1016 family.
- Remote systems -> T1018.
- Services -> T1007.
- Drivers -> T1652.
- Processes -> T1057.
- Software/security/backup products -> T1518 family.
- Domain trusts -> T1482.
- Files/directories -> T1083.

### Lateral Movement
Use when the text describes moving to other systems.
- Shared content tainting -> T1080.
- Remote service use may also support lateral movement if the text explicitly describes movement between internal systems.

### Collection
Use when the text describes gathering data after compromise.
- Automated collection -> T1119.
- Email collection -> T1114.
- Database collection -> T1213.006.
- Clipboard data -> T1115.
- Data from local system -> T1005.
- Local data staging -> T1074.001.

### Command and Control
Use when the text describes beaconing, tasking, or remote communications.
- Application-layer protocol family -> T1071 or sub-techniques.
- DNS C2 -> T1071.004.
- Web protocols -> T1071.001.
- Publish/subscribe protocols -> T1071.005.
- Fast flux DNS used to hide C2 infrastructure -> T1568.001.

### Exfiltration
Use when the text describes sending collected data out of the environment.
- Local staging before exfiltration -> T1074.001.
- Protocol-specific exfiltration may overlap with C2 if the same channel is used, but only include what the text explicitly supports.

### Impact
Use when the text describes disruption, destruction, encryption for impact, or service interruption. Only map if the impact behavior is explicit.

## Core distinctions that often decide the right label

### Discovery vs collection
- **T1083 File and Directory Discovery**: listing, searching, enumerating, or locating files/directories.
- **T1005 Data from Local System**: reading, copying, stealing, or extracting actual local file contents or data.
- **T1119 Automated Collection**: automated or scheduled collection of internal data after access is established.
- **T1074.001 Local Data Staging**: consolidating collected data into a local staging directory or archive before exfiltration.
- If the text says the malware searches for files and then copies them, both discovery and collection may be valid.

### Pre-compromise victim host information vs post-compromise host discovery
- **T1592 Gather Victim Host Information** and **T1592.001 Hardware** apply to reconnaissance before compromise.
- **T1082 System Information Discovery** applies to host details gathered on a compromised system.
- Use the wording and context to decide whether the behavior is pre-compromise targeting or post-compromise discovery.

### Current user vs account enumeration
- **T1033 System Owner/User Discovery**: current user, logged-in user, owner, active user.
- **T1087 Account Discovery** and sub-techniques: listing accounts broadly.
- Do not map a single current-user check to account discovery unless multiple accounts are enumerated.

### System information vs network configuration
- **T1082 System Information Discovery**: OS version, architecture, hostname, hardware, service pack, patches, general host details.
- **T1016 System Network Configuration Discovery**: IP, MAC, DNS, DHCP, gateway, adapters, routes, network settings.
- **T1016.001** for Internet connectivity checks.
- **T1016.002** for Wi-Fi profiles, SSIDs, wireless passwords, nearby wireless networks.

### Remote systems vs domain trusts
- **T1018 Remote System Discovery**: hosts, computers, IP ranges, subnets, neighbors, reachable systems.
- **T1482 Domain Trust Discovery**: trust relationships between domains or forests.

### Services, drivers, software, and processes
- **T1007 System Service Discovery**: enumerate services.
- **T1652 Device Driver Discovery**: enumerate drivers.
- **T1518 Software Discovery**: enumerate installed software.
- **T1518.001 Security Software Discovery**: enumerate AV, EDR, firewall, sensors, defensive tools.
- **T1518.002 Backup Software Discovery**: enumerate backup products.
- **T1057 Process Discovery**: enumerate running processes.

### Command and scripting interpreters
- Use **T1059** only when an interpreter is used but the specific interpreter is not clear.
- Use the matching sub-technique when the interpreter is named: PowerShell, cmd.exe, Unix shell, Python, JavaScript, Visual Basic, AppleScript, AutoHotKey/AutoIT, Lua, cloud API, network device CLI, hypervisor CLI, container CLI/API.

### WMI execution vs WMI event subscription
- **T1047 Windows Management Instrumentation**: WMI used to execute commands or payloads.
- **T1546.003 Windows Management Instrumentation Event Subscription**: WMI event consumer/filter/binding used for persistence or event-triggered execution.

### Proxy execution via trusted binaries/scripts
- **T1216.001 PubPrn**: use of PubPrn.vbs to proxy execution of remote files.
- **T1218.011 Rundll32**: use of rundll32.exe to proxy execution of malicious code.
- **T1218.004 InstallUtil**: use of InstallUtil to proxy execution of code through a trusted Windows utility.
- **T1218.013 Mavinject**: use of mavinject.exe to proxy execution of malicious code.
- Prefer these when the binary/script is explicitly named.

### Process injection distinctions
- **T1055 Process Injection** for generic injection into another process.
- Use a sub-technique only when the method is explicit: DLL injection, PE injection, APC, ptrace, /proc memory, hollowing, doppelgänging, VDSO hijacking, listplanting, thread execution hijacking, extra window memory, TLS callbacks.
- Do not assume hollowing from generic injection language.

### Password stores vs OS credential dumping
- **T1555 Credentials from Password Stores** and sub-techniques apply to browser stores, Keychain, Credential Manager, password managers, cloud secrets stores, or securityd memory.
- **T1003 OS Credential Dumping** and sub-techniques apply to dumping hashes/secrets from OS credential stores such as SAM or LSA Secrets.

### Network interception distinctions
- **T1557 Adversary-in-the-Middle**: positioning between communicating parties to intercept or manipulate traffic.
- **T1040 Network Sniffing**: passively capturing network traffic.
- Sniffing is passive capture; AiTM implies active positioning or interception between endpoints.

### Masquerading vs hiding vs obfuscation
- **T1036 Masquerading**: making something appear legitimate.
- **T1564 Hide Artifacts**: concealing artifacts from users or defenses.
- **T1027 family variants**: encoding, encrypting, embedding, or storing payload/data in concealed formats to impede detection.
- A disguised file type is masquerading; an excluded path is hiding; an encoded file is obfuscation.

### Event-triggered execution vs boot/logon autostart vs system process creation
- **T1546 Event Triggered Execution** for execution triggered by events or hooks.
- **T1547 Boot or Logon Autostart Execution** for execution at boot or logon.
- **T1543 Create or Modify System Process** for creating or modifying services or other system-level processes to repeatedly execute payloads.

### Application-layer protocol distinctions
- **T1071** when application-layer C2 is clear but protocol family is not specified.
- **T1071.001** for HTTP/HTTPS/web.
- **T1071.002** for FTP/file transfer protocols.
- **T1071.003** for mail protocols.
- **T1071.004** for DNS.
- **T1071.005** for publish/subscribe protocols.
- **T1568.001** for fast flux DNS used to hide C2 infrastructure.

### Shared content and remote services
- **T1080 Taint Shared Content**: adding malicious content to shared storage or repositories to reach remote systems.
- **T1133 External Remote Services**: using external-facing remote services for initial access or persistence.

## Phrase-to-technique shortcuts

These are shortcuts, not substitutes for evidence review.

- "develops malware", "builds payloads", "creates malware components" -> **T1587.001**
- "automatically collects data", "scheduled collection", "automated internal data gathering" -> **T1119**
- "man-in-the-middle", "AiTM", "positions between devices" -> **T1557**
- "sniffs network traffic", "packet capture", "captures traffic passively" -> **T1040**
- "executes via WMI", "uses WMI to run commands" -> **T1047**
- "gathers victim host information before targeting" -> **T1592**
- "gathers victim hardware information before targeting" -> **T1592.001**
- "searches victim-owned websites" -> **T1594**
- "searches DNS or passive DNS for victim information" -> **T1596.001**
- "purchases technical data about victims" -> **T1597.002**
- "gets current user", "whoami", "logged-in user" -> **T1033**
- "enumerates services" -> **T1007**
- "enumerates drivers" -> **T1652**
- "uses JavaScript/JScript" -> **T1059.007**
- "PowerShell profile persistence" -> **T1546.013**
- "uses PubPrn.vbs" -> **T1216.001**
- "uses rundll32" -> **T1218.011**
- "uses InstallUtil" -> **T1218.004**
- "uses mavinject" -> **T1218.013**
- "creates or modifies service/system process" -> **T1543**
- "creates or modifies Windows service" -> **T1543.003**
- "uses VPN/Citrix/external remote service" -> **T1133**
- "stores payload/data in registry/WMI/event logs/other non-file storage" -> **T1027.011**
- "bypasses UAC" -> **T1548.002**
- "DLL hijacking", "search-order hijack", "side-loading via DLL path abuse" -> **T1574.001**
- "hides artifacts" -> **T1564**
- "disguises file as another type" -> **T1036.008**
- "encrypts or encodes files to evade detection" -> **T1027.013**
- "embeds payload in another file" -> **T1027.009**
- "writes to AV-excluded path" -> **T1564.012**
- "dumps credentials" -> **T1003**
- "dumps SAM" -> **T1003.002**
- "extracts LSA secrets" -> **T1003.004**
- "keylogs" -> **T1056.001**
- "steals from password manager" -> **T1555.005**
- "steals from Keychain" -> **T1555.001**
- "taints shared content" -> **T1080**
- "stages data locally before exfiltration" -> **T1074.001**
- "collects from databases" -> **T1213.006**
- "collects email" -> **T1114**
- "uses MQTT/AMQP/XMPP-like pub-sub for C2" -> **T1071.005**
- "uses DNS for C2" -> **T1071.004**
- "uses fast flux" -> **T1568.001**
- "boot or logon initialization scripts" -> **T1037**
- "Active Setup persistence" -> **T1547.014**
- "spearphishing email with malicious link" -> **T1566.002**

## Inclusion notes

- Brief but explicit wording is enough.
- Prefer recall when the mechanism or action is directly named.
- Prefer precision by avoiding unsupported sibling sub-techniques.
- Do not infer from malware labels alone.
- If both a discovery action and a follow-on collection action are explicit, include both.
- If a row contains several independent behaviors, include all supported IDs.
- If the text explicitly names a sub-technique mechanism, do not suppress it just because the description is short.