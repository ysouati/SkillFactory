# ATT&CK behavior-to-technique mapping reference

Use this as a compact general lookup across the ATT&CK lifecycle. Match on behavior + mechanism + object + platform together, not on isolated keywords.

## Mapping principles

- Prefer rows with a named mechanism, protocol, binary, storage location, service, or artifact.
- If wording is generic, use the parent technique when listed.
- Multiple rows may apply to one description if multiple independent behaviors are present.
- Platform and scope matter: enterprise host, cloud, identity, mobile, network device, ICS, and pre-compromise behaviors should be distinguished when possible.

## Initial Access / Resource Development / Reconnaissance

| Behavior or clue | Technique |
|---|---|
| compromise or use externally exposed VPN, Citrix, remote gateway, remote desktop gateway, or other external-facing remote access service to gain access or maintain access | **T1133 – External Remote Services** |
| spearphishing email containing a malicious link or URL | **T1566.002 – Phishing: Spearphishing Link** |
| spearphishing email containing a malicious attachment | **T1566.001 – Phishing: Spearphishing Attachment** |
| user is tricked into opening a malicious attachment, lure document, or weaponized file | **T1204.002 – User Execution: Malicious File** |
| user is tricked into clicking or opening a malicious link in a browser or application | **T1204.001 – User Execution: Malicious Link** |
| exploit users who browse to a website; compromise visitors through normal browsing; prepare a website to infect visitors | **T1608.004 – Stage Capabilities: Drive-by Target** |
| compromise third-party routers, firewalls, or other network devices for use during targeting or operations | **T1584.008 – Compromise Infrastructure: Network Devices** |
| purchase victim technical information, datasets, or technical details for targeting | **T1597.002 – Gather Victim Host Information: Purchase Technical Data** |
| gather victim host information before intrusion | **T1592 – Gather Victim Host Information** |
| gather victim hardware details, device model, CPU, peripherals, hardware inventory | **T1592.001 – Gather Victim Host Information: Hardware** |
| gather victim software, OS, browser, installed applications, versions, plugins | **T1592.002 – Gather Victim Host Information: Software** |
| gather victim firmware, BIOS, baseband, embedded software details | **T1592.003 – Gather Victim Host Information: Firmware** |
| gather victim client configurations, security products, MDM, policies, settings | **T1592.004 – Gather Victim Host Information: Client Configurations** |
| develop malware or malicious software capabilities | **T1587.001 – Develop Capabilities: Malware** |
| obtain or prepare domains for operations | **T1583.001 – Acquire Infrastructure: Domains** |
| obtain or prepare servers or VPS for operations | **T1583.003 – Acquire Infrastructure: Virtual Private Server** |
| obtain or prepare botnet infrastructure | **T1583.005 – Acquire Infrastructure: Botnet** |
| place malicious content on shared drives, repositories, or shared storage to reach other users/systems | **T1080 – Taint Shared Content** |

## Execution

| Behavior or clue | Technique |
|---|---|
| generic command or script execution with no interpreter specified | **T1059 – Command and Scripting Interpreter** |
| executes shell commands via `cmd.exe`, command shell, batch commands | **T1059.003 – Command and Scripting Interpreter: Windows Command Shell** |
| executes PowerShell | **T1059.001 – Command and Scripting Interpreter: PowerShell** |
| executes Unix shell, bash, sh, zsh | **T1059.004 – Command and Scripting Interpreter: Unix Shell** |
| executes Python | **T1059.006 – Command and Scripting Interpreter: Python** |
| executes JavaScript, JScript, JXA, `.js`, Windows Script Host JavaScript, browser JavaScript used for execution | **T1059.007 – Command and Scripting Interpreter: JavaScript** |
| executes VBScript or `.vbs` | **T1059.005 – Command and Scripting Interpreter: Visual Basic** |
| uses WMI to execute commands or processes | **T1047 – Windows Management Instrumentation** |
| uses COM objects / Component Object Model for local code execution or automation | **T1559.001 – Inter-Process Communication: Component Object Model** |
| uses `rundll32.exe` to execute DLL exports or proxy malicious code | **T1218.011 – System Binary Proxy Execution: Rundll32** |
| uses `mavinject.exe` to inject or proxy execution | **T1218.013 – System Binary Proxy Execution: Mavinject** |
| uses `regsvr32.exe` to execute scriptlets or proxy execution | **T1218.010 – System Binary Proxy Execution: Regsvr32** |
| uses `mshta.exe` to execute HTA or script content | **T1218.005 – System Binary Proxy Execution: Mshta** |
| uses `installutil.exe` to execute code | **T1218.004 – System Binary Proxy Execution: InstallUtil** |
| uses `wmic.exe` for execution | **T1047 – Windows Management Instrumentation** |
| uses `PubPrn.vbs` / PubPrn to execute or proxy remote script/file execution | **T1216.001 – System Script Proxy Execution: PubPrn** |
| injects code, shellcode, or DLL into another process | **T1055 – Process Injection** |
| reflectively loads code into memory without standard loader | **T1620 – Reflective Code Loading** |
| downloads or retrieves tools/payloads from a remote source for later execution | **T1105 – Ingress Tool Transfer** |
| executes malicious Office macros or VBA | **T1059.005 – Command and Scripting Interpreter: Visual Basic** |
| exploit a vulnerability to execute code on a host or application | **T1203 – Exploitation for Client Execution** |

## Persistence / Privilege Escalation

| Behavior or clue | Technique |
|---|---|
| generic startup or logon autostart mechanism is described but exact method is unclear | **T1547 – Boot or Logon Autostart Execution** |
| registry Run keys or Startup folder used for persistence | **T1547.001 – Boot or Logon Autostart Execution: Registry Run Keys / Startup Folder** |
| Active Setup registry keys used to launch code at logon | **T1547.014 – Boot or Logon Autostart Execution: Active Setup** |
| boot or logon scripts, login scripts, initialization scripts used for persistence | **T1037 – Boot or Logon Initialization Scripts** |
| scheduled task or Task Scheduler used for recurring or delayed execution | **T1053.005 – Scheduled Task/Job: Scheduled Task** |
| cron used for recurring execution on Unix-like systems | **T1053.003 – Scheduled Task/Job: Cron** |
| create or modify service, daemon, launch agent, launch daemon, or other system process for persistence | **T1543 – Create or Modify System Process** |
| create or modify Windows service specifically | **T1543.003 – Create or Modify System Process: Windows Service** |
| create or modify launch agent on macOS | **T1543.001 – Create or Modify System Process: Launch Agent** |
| create or modify launch daemon on macOS | **T1543.004 – Create or Modify System Process: Launch Daemon** |
| office add-ins, templates, startup folders, or Office startup behavior used for persistence | **T1137 – Office Application Startup** |
| browser extension installed or modified for persistence or execution | **T1176 – Browser Extensions** |
| account added or modified to maintain access | **T1098 – Account Manipulation** |
| create local account | **T1136.001 – Create Account: Local Account** |
| create domain account | **T1136.002 – Create Account: Domain Account** |
| bypass UAC to elevate privileges | **T1548.002 – Abuse Elevation Control Mechanism: Bypass User Account Control** |
| use sudo, sudoers, or cached sudo credentials to elevate on Unix-like systems | **T1548.003 – Abuse Elevation Control Mechanism: Sudo and Sudo Caching** |
| exploit vulnerability to gain higher privileges | **T1068 – Exploitation for Privilege Escalation** |
| modify domain trust relationships or trust properties | **T1484.002 – Domain or Tenant Policy Modification: Trust Modification** |

## Defense Evasion / Impair Defenses / Obfuscation / Masquerading

| Behavior or clue | Technique |
|---|---|
| generic hiding or concealment of artifacts with no narrower method | **T1564 – Hide Artifacts** |
| hide files or directories using hidden attributes or hidden locations | **T1564.001 – Hide Artifacts: Hidden Files and Directories** |
| add AV or security-tool exclusions for files or paths | **T1564.012 – Hide Artifacts: File/Path Exclusions** |
| disguise as legitimate software, app, document, or trusted component | **T1036 – Masquerading** |
| disguise file type, extension, signature, or format to appear benign | **T1036.008 – Masquerading: Masquerade File Type** |
| rename or place malware to look like a legitimate system binary or application | **T1036 – Masquerading** |
| encrypt or encode a file, payload, config, or embedded content to hinder inspection | **T1027.013 – Obfuscated Files or Information: Encrypted/Encoded File** |
| embed malicious payload inside another file or container | **T1027.009 – Obfuscated Files or Information: Embedded Payloads** |
| pack, obfuscate, or otherwise encode scripts/binaries to hinder analysis without a more specific file-artifact clue | **T1027 – Obfuscated Files or Information** |
| modify timestamps to conceal activity | **T1070.006 – Indicator Removal on Host: Timestomp** |
| clear logs or delete event records | **T1070.001 – Indicator Removal on Host: Clear Windows Event Logs** |
| disable, tamper with, or stop security tools or monitoring | **T1562.001 – Impair Defenses: Disable or Modify Tools** |
| exploit vulnerabilities in security software or defensive components to disable or degrade them | **T1687 – Exploitation for Defense Impairment** |
| spoof or manipulate security tool UI to falsely indicate normal operation | **T1685.003 – Modify or Spoof Tool UI: Security Tool UI** |
| bypass macOS Gatekeeper or remove quarantine attributes to run untrusted apps | **T1553.001 – Subvert Trust Controls: Gatekeeper Bypass** |
| signed binary proxy execution using trusted system binaries generally | **T1218 – System Binary Proxy Execution** |

## Credential Access

| Behavior or clue | Technique |
|---|---|
| generic credential dumping from OS stores, memory, SAM, LSASS, or auth subsystems | **T1003 – OS Credential Dumping** |
| dump LSASS memory specifically | **T1003.001 – OS Credential Dumping: LSASS Memory** |
| dump or access LSA secrets specifically | **T1003.004 – OS Credential Dumping: LSA Secrets** |
| dump SAM database | **T1003.002 – OS Credential Dumping: Security Account Manager** |
| dump NTDS or domain credential database | **T1003.003 – OS Credential Dumping: NTDS** |
| log keystrokes, capture typed credentials, keyboard hooks for credential theft | **T1056.001 – Input Capture: Keylogging** |
| capture credentials via GUI prompts or fake login dialogs | **T1056 – Input Capture** |
| steal credentials from password stores generically | **T1555 – Credentials from Password Stores** |
| steal from macOS Keychain | **T1555.001 – Credentials from Password Stores: Keychain** |
| steal from web browsers' saved passwords | **T1555.003 – Credentials from Password Stores: Credentials from Web Browsers** |
| steal from third-party password managers | **T1555.005 – Credentials from Password Stores: Password Managers** |
| crack password hashes or offline password material | **T1110.002 – Brute Force: Password Cracking** |
| sniff credentials from network traffic | **T1040 – Network Sniffing** |

## Discovery

| Behavior or clue | Technique |
|---|---|
| list files, directories, paths, drives, current directory, recursive file enumeration | **T1083 – File and Directory Discovery** |
| enumerate processes or running tasks | **T1057 – Process Discovery** |
| gather OS version, hostname, architecture, installed software, hardware, system details | **T1082 – System Information Discovery** |
| identify current user, logged-in user, account owner, active session user | **T1033 – System Owner/User Discovery** |
| enumerate local accounts | **T1087.001 – Account Discovery: Local Account** |
| enumerate domain accounts / domain users | **T1087.002 – Account Discovery: Domain Account** |
| enumerate groups or permission groups generically | **T1069 – Permission Groups Discovery** |
| enumerate domain groups or domain permission groups | **T1069.002 – Permission Groups Discovery: Domain Groups** |
| enumerate local groups | **T1069.001 – Permission Groups Discovery: Local Groups** |
| enumerate domain trusts or trust relationships | **T1482 – Domain Trust Discovery** |
| enumerate network configuration, adapters, IPs, routes, DNS, subnet info | **T1016 – System Network Configuration Discovery** |
| enumerate network connections or sessions | **T1049 – System Network Connections Discovery** |
| enumerate local or registered services | **T1007 – System Service Discovery** |
| detect antivirus, EDR, firewall, or security software | **T1518.001 – Software Discovery: Security Software Discovery** |
| enumerate installed software generally | **T1518 – Software Discovery** |
| query environment variables | **T1082 – System Information Discovery** |
| discover virtualization or sandbox environment | **T1497.001 – Virtualization/Sandbox Evasion: System Checks** |

## Lateral Movement / Remote Services

| Behavior or clue | Technique |
|---|---|
| remote desktop protocol used to move laterally or remotely control systems | **T1021.001 – Remote Services: Remote Desktop Protocol** |
| SMB/Windows admin shares used for remote access or lateral movement | **T1021.002 – Remote Services: SMB/Windows Admin Shares** |
| SSH used for remote access or lateral movement | **T1021.004 – Remote Services: SSH** |
| VNC used to remotely control systems | **T1021.005 – Remote Services: VNC** |
| remote services used generically for lateral movement | **T1021 – Remote Services** |
| copy itself or payloads to USB or removable media to spread | **T1091 – Replication Through Removable Media** |

## Collection / Staging

| Behavior or clue | Technique |
|---|---|
| collect files or data from local system for theft | **T1005 – Data from Local System** |
| collect data from removable media | **T1025 – Data from Removable Media** |
| collect data from network shared drive | **T1039 – Data from Network Shared Drive** |
| automated bulk collection, scripted collection, periodic collection jobs | **T1119 – Automated Collection** |
| capture clipboard contents | **T1115 – Clipboard Data** |
| take screenshots or capture the desktop | **T1113 – Screen Capture** |
| stage collected data in a local directory or central local location before exfiltration | **T1074.001 – Data Staged: Local Data Staging** |
| collect audio from microphone | **T1123 – Audio Capture** |
| collect email from local client or server | **T1114 – Email Collection** |

## Network Collection / Interception

| Behavior or clue | Technique |
|---|---|
| sniff network traffic, packet capture, passive interception of network communications | **T1040 – Network Sniffing** |
| position between endpoints, intercept, relay, downgrade, or modify traffic as man-in-the-middle or adversary-in-the-middle | **T1557 – Adversary-in-the-Middle** |
| ARP spoofing, DHCP spoofing, LLMNR/NBT-NS poisoning used to intercept traffic or credentials | **T1557 – Adversary-in-the-Middle** |

## Command and Control / Exfiltration Transport Clues

| Behavior or clue | Technique |
|---|---|
| communicates with C2 over HTTP or HTTPS, web requests, GET/POST beacons, browser-like traffic, web-based C2 | **T1071.001 – Application Layer Protocol: Web Protocols** |
| communicates over DNS for C2 | **T1071.004 – Application Layer Protocol: DNS** |
| communicates over mail protocols for C2 | **T1071.003 – Application Layer Protocol: Mail Protocols** |
| communicates over other application-layer protocols generically | **T1071 – Application Layer Protocol** |
| uses standard encoding such as Base64 to package command, beacon, or exfil data | **T1132.001 – Data Encoding: Standard Encoding** |
| uses non-standard/custom encoding for command, beacon, or exfil data | **T1132.002 – Data Encoding: Non-Standard Encoding** |
| encrypted traffic over HTTP/HTTPS still uses web protocols for C2 | **T1071.001 – Application Layer Protocol: Web Protocols** |
| exfiltrates over web service, cloud storage, or web protocol | **T1567 – Exfiltration Over Web Service** |
| exfiltrates over C2 channel | **T1041 – Exfiltration Over C2 Channel** |

## Impact

| Behavior or clue | Technique |
|---|---|
| encrypt files or systems for impact/ransom | **T1486 – Data Encrypted for Impact** |
| delete files or data for impact | **T1485 – Data Destruction** |
| wipe disks or overwrite data structures | **T1561 – Disk Wipe** |
| stop services to inhibit recovery or operations | **T1489 – Service Stop** |
| deface websites or user-facing content | **T1491.001 – Defacement: Internal Defacement** |
| inhibit system recovery, delete backups, shadow copies, or restore points | **T1490 – Inhibit System Recovery** |
| network denial of service or resource exhaustion | **T1498 – Network Denial of Service** |

## Platform-sensitive cues

| Cue | Prefer |
|---|---|
| `Keychain`, macOS credential store | **T1555.001** |
| `Gatekeeper`, quarantine attribute, notarization bypass | **T1553.001** |
| `launch agent`, `launch daemon` | **T1543.001** / **T1543.004** |
| `sudo`, `sudoers`, cached sudo | **T1548.003** |
| `rundll32` | **T1218.011** |
| `mavinject` | **T1218.013** |
| `COM`, COM object, ActiveX automation for execution | **T1559.001** |
| `scheduled task`, `Task Scheduler` | **T1053.005** |
| `Active Setup` | **T1547.014** |
| `Windows service` | **T1543.003** |
| `LSA Secrets` | **T1003.004** |
| `password manager` | **T1555.005** |
| `clipboard` | **T1115** |
| `screen capture`, screenshot | **T1113** |
| `VNC` | **T1021.005** |
| `HTTP`, `HTTPS`, `GET`, `POST`, URL beaconing | **T1071.001** |

## High-value distinctions

| If the text says... | Prefer |
|---|---|
| exposed VPN/Citrix/remote gateway used to gain access | **T1133** |
| malicious attachment/file opened by user | **T1204.002** |
| malicious link clicked by user | **T1204.001** |
| website prepared to infect visitors through browsing | **T1608.004** |
| third-party network device compromised for operations | **T1584.008** |
| purchased victim technical data | **T1597.002** |
| JavaScript/JScript/JXA execution | **T1059.007** |
| COM object execution | **T1559.001** |
| `rundll32` execution | **T1218.011** |
| `mavinject` execution | **T1218.013** |
| generic startup persistence with no exact mechanism | **T1547** |
| exact startup mechanism such as scheduled task, Run key, Active Setup, Office startup | corresponding **sub-technique** |
| Windows service creation/modification | **T1543.003** |
| generic credential dumping | **T1003** |
| LSA Secrets specifically | **T1003.004** |
| password cracking | **T1110.002** |
| trust relationship modification | **T1484.002** |
| exploit security software to disable defenses | **T1687** |
| spoof security tool UI | **T1685.003** |
| Gatekeeper bypass | **T1553.001** |
| AV/security path exclusions | **T1564.012** |
| keylogging | **T1056.001** |
| passive packet capture | **T1040** |
| Keychain theft | **T1555.001** |
| password manager theft | **T1555.005** |
| domain groups enumeration | **T1069.002** |
| domain account enumeration | **T1087.002** |
| local account enumeration | **T1087.001** |
| victim host profiling before intrusion | **T1592** |
| VNC remote control | **T1021.005** |
| taint shared drives/repos | **T1080** |
| local staging before exfiltration | **T1074.001** |
| clipboard capture | **T1115** |
| screenshot capture | **T1113** |
| automated scripted collection | **T1119** |
