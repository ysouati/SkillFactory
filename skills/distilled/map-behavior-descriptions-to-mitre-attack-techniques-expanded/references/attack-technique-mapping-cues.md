# ATT&CK behavior-to-technique mapping cues

Map concrete behavior, not malware labels. Prefer the most specific supported sub-technique; otherwise use the parent.

## Resource development and reconnaissance

| Behavior cue in description | ATT&CK ID | Technique |
|---|---:|---|
| Develops malware, payloads, implants, droppers, loaders, or malicious components for operations | T1587.001 | Malware |
| Obtains or uses generative AI or large language models to support operations | T1588.007 | Artificial Intelligence |
| Acquires or registers domains for operations | T1583.001 | Domains |
| Sets up or acquires DNS servers for operations | T1583.002 | DNS Server |
| Rents or acquires VPS infrastructure | T1583.003 | Virtual Private Server |
| Acquires physical or dedicated servers | T1583.004 | Server |
| Acquires or rents a botnet | T1583.005 | Botnet |
| Registers or abuses web services for operations | T1583.006 | Web Services |
| Acquires serverless cloud infrastructure | T1583.007 | Serverless |
| Purchases or uses online ads to distribute malware or lure victims | T1583.008 | Malvertising |
| Gathers information about victim hosts before compromise, such as hostnames, OS, hardware, software, or configurations for targeting | T1592 | Gather Victim Host Information |
| Prepares a website or watering-hole style destination to infect visitors through normal browsing | T1608.004 | Drive-by Target |

## Initial access and delivery

| Behavior cue | ATT&CK ID | Technique |
|---|---:|---|
| Relies on a user opening a malicious attachment, lure document, or other malicious file for execution | T1204.002 | Malicious File |
| Uses external-facing remote services such as VPN, remote desktop, Citrix, or similar remote access services for access or persistence | T1133 | External Remote Services |
| Delivers payloads by placing malicious content in shared network locations, repositories, or shared directories | T1080 | Taint Shared Content |
| Embeds a malicious payload inside another file to conceal or deliver it | T1027.009 | Embedded Payloads |

## Execution

| Behavior cue | ATT&CK ID | Technique |
|---|---:|---|
| Generic command or script interpreter use without a more specific interpreter | T1059 | Command and Scripting Interpreter |
| PowerShell execution | T1059.001 | PowerShell |
| AppleScript execution | T1059.002 | AppleScript |
| Executes commands via cmd.exe, batch files, Windows shell, or clearly Windows remote shell | T1059.003 | Windows Command Shell |
| Bash, sh, zsh, or other Unix shell execution | T1059.004 | Unix Shell |
| Visual Basic or VBScript execution | T1059.005 | Visual Basic |
| Python execution | T1059.006 | Python |
| JavaScript or JScript execution | T1059.007 | JavaScript |
| Network device CLI execution | T1059.008 | Network Device CLI |
| Cloud API used to execute commands or actions | T1059.009 | Cloud API |
| AutoHotKey or AutoIT script execution | T1059.010 | AutoHotKey & AutoIT |
| Lua execution | T1059.011 | Lua |
| Hypervisor CLI execution | T1059.012 | Hypervisor CLI |
| Container CLI or API execution | T1059.013 | Container CLI/API |
| Uses Windows Management Instrumentation to execute commands or payloads | T1047 | Windows Management Instrumentation |
| Uses rundll32.exe to execute malicious DLL code | T1218.011 | Rundll32 |
| Uses mavinject.exe to execute or inject malicious code | T1218.013 | Mavinject |
| Uses COM objects or COM-based execution for local code execution | T1559.001 | Component Object Model |

## Persistence and privilege escalation

| Behavior cue | ATT&CK ID | Technique |
|---|---:|---|
| Generic event-triggered execution when only the broad concept is supported | T1546 | Event Triggered Execution |
| WMI event subscription for persistence or execution | T1546.003 | Windows Management Instrumentation Event Subscription |
| Modifies Unix shell configuration files for execution at shell start | T1546.004 | Unix Shell Configuration Modification |
| Uses PowerShell profile for persistence | T1546.013 | PowerShell Profile |
| Uses COM hijacking | T1546.015 | Component Object Model Hijacking |
| Generic boot or logon autostart execution | T1547 | Boot or Logon Autostart Execution |
| Registry Run keys or Startup folder persistence | T1547.001 | Registry Run Keys / Startup Folder |
| Uses Active Setup registry mechanism for persistence | T1547.014 | Active Setup |
| Uses boot or logon initialization scripts for persistence | T1037 | Boot or Logon Initialization Scripts |
| Generic create or modify system process for persistence or privilege escalation | T1543 | Create or Modify System Process |
| Creates or modifies a Windows service for persistence or execution | T1543.003 | Windows Service |
| Creates or abuses scheduled tasks for one-time or recurring execution | T1053.005 | Scheduled Task |
| Bypasses User Account Control to elevate privileges | T1548.002 | Bypass User Account Control |
| Hijacks service registry entries or abuses weak service registry permissions to execute payloads | T1574.011 | Services Registry Permissions Weakness |
| Hijacks DLL search order, side-loading, or malicious DLL replacement/load path abuse | T1574.001 | DLL |
| Hijacks PATH environment variable resolution to execute malicious binaries or libraries | T1574.007 | Path Interception by PATH Environment Variable |

## Defense evasion and concealment

| Behavior cue | ATT&CK ID | Technique |
|---|---:|---|
| Generic masquerading: artifact made to appear legitimate or benign | T1036 | Masquerading |
| Mimics or abuses invalid code signatures | T1036.001 | Invalid Code Signature |
| Uses right-to-left override character to disguise names | T1036.002 | Right-to-Left Override |
| Renames legitimate utilities to evade controls | T1036.003 | Rename Legitimate Utilities |
| Gives a task or service a benign-looking name | T1036.004 | Masquerade Task or Service |
| Matches legitimate file, registry, or resource name or location | T1036.005 | Match Legitimate Resource Name or Location |
| Uses trailing space after filename to disguise type | T1036.006 | Space after Filename |
| Uses double file extension to disguise type | T1036.007 | Double File Extension |
| Disguises payload by file signature, extension, icon, or contents to appear as another file type | T1036.008 | Masquerade File Type |
| Breaks or spoofs process tree relationships, parent process spoofing, or PPID manipulation | T1036.009 | Break Process Trees |
| Creates account names resembling legitimate ones | T1036.010 | Masquerade Account Name |
| Overwrites process arguments to change apparent process name | T1036.011 | Overwrite Process Arguments |
| Spoofs browser or system fingerprint to blend with legitimate traffic | T1036.012 | Browser Fingerprint |
| Generic indicator removal or artifact cleanup | T1070 | Indicator Removal |
| Clears command history | T1070.003 | Clear Command History |
| Deletes files to remove evidence | T1070.004 | File Deletion |
| Removes network share connections | T1070.005 | Network Share Connection Removal |
| Modifies file timestamps, timestomping | T1070.006 | Timestomp |
| Clears network connection history or configurations | T1070.007 | Clear Network Connection History and Configurations |
| Clears mailbox data | T1070.008 | Clear Mailbox Data |
| Removes persistence artifacts after use | T1070.009 | Clear Persistence |
| Relocates malware to new paths to reduce evidence or evade defenses | T1070.010 | Relocate Malware |
| Generic hide artifacts behavior without a more specific subtype | T1564 | Hide Artifacts |
| Sets files or directories hidden | T1564.001 | Hidden Files and Directories |
| Hides user accounts | T1564.002 | Hidden Users |
| Uses hidden windows | T1564.003 | Hidden Window |
| Uses NTFS file attributes to hide data | T1564.004 | NTFS File Attributes |
| Uses hidden file systems | T1564.005 | Hidden File System |
| Runs a virtual instance to avoid detection | T1564.006 | Run Virtual Instance |
| Uses email rules to hide messages | T1564.008 | Email Hiding Rules |
| Uses resource forks to hide code or data | T1564.009 | Resource Forking |
| Spoofs or overwrites process command-line arguments to hide them | T1564.010 | Process Argument Spoofing |
| Ignores process interrupts or signals to evade interruption | T1564.011 | Ignore Process Interrupts |
| Uses file or path exclusions to hide artifacts from scanning | T1564.012 | File/Path Exclusions |
| Uses bind mounts to hide activity or artifacts | T1564.013 | Bind Mounts |
| Uses extended attributes to hide data | T1564.014 | Extended Attributes |
| Performs system or environment checks to detect virtualization, sandboxes, debuggers, or analysis environments | T1497.001 | System Checks |

## Credential access

| Behavior cue | ATT&CK ID | Technique |
|---|---:|---|
| Dumps credentials, password hashes, or cleartext credentials from the OS or credential-bearing processes | T1003 | OS Credential Dumping |
| Captures user input broadly, form grabbing, input interception | T1056 | Input Capture |
| Logs keystrokes specifically | T1056.001 | Keylogging |
| Fake or mimicked GUI prompt captures credentials | T1056.002 | GUI Input Capture |
| Captures credentials from a web login portal or modified login page | T1056.003 | Web Portal Capture |
| Hooks credential APIs or authentication-related functions to capture credentials | T1056.004 | Credential API Hooking |
| Acquires credentials from third-party password manager applications or stores | T1555.005 | Password Managers |
| Guesses passwords without prior credential knowledge | T1110.001 | Password Guessing |
| Modifies PAM modules to capture credentials or enable unauthorized access | T1556.003 | Pluggable Authentication Modules |
| Passively sniffs network traffic to capture information or credentials | T1040 | Network Sniffing |

## Discovery

| Behavior cue | ATT&CK ID | Technique |
|---|---:|---|
| Discovers remote systems, hosts, subnets, network neighbors, IPs, hostnames | T1018 | Remote System Discovery |
| Enumerates current user, logged-in user, account owner, active user | T1033 | System Owner/User Discovery |
| Enumerates running processes | T1057 | Process Discovery |
| Generic permission groups or role discovery | T1069 | Permission Groups Discovery |
| Enumerates local groups | T1069.001 | Local Groups |
| Enumerates domain groups | T1069.002 | Domain Groups |
| Enumerates cloud groups or roles | T1069.003 | Cloud Groups |
| Generic account discovery | T1087 | Account Discovery |
| Enumerates local accounts | T1087.001 | Local Account |
| Enumerates domain accounts | T1087.002 | Domain Account |
| Enumerates email accounts or address lists | T1087.003 | Email Account |
| Enumerates cloud accounts | T1087.004 | Cloud Account |
| Obtains OS version, architecture, patches, host configuration, adapter, IP, MAC, DNS, or gateway details | T1082 | System Information Discovery |
| Lists files, directories, current working directory, file metadata, or directory contents | T1083 | File and Directory Discovery |
| Checks for Internet connectivity or external network access | T1016.001 | Internet Connection Discovery |
| Enumerates domain trust relationships | T1482 | Domain Trust Discovery |
| Enumerates installed software generally | T1518 | Software Discovery |
| Detects installed anti-virus, EDR, sensors, or defensive tools | T1518.001 | Security Software Discovery |
| Detects installed backup software or backup configuration | T1518.002 | Backup Software Discovery |
| Gathers information about registered local services | T1007 | System Service Discovery |

## Lateral movement and interception

| Behavior cue | ATT&CK ID | Technique |
|---|---:|---|
| Positions between communicating devices, intercepts or relays traffic, or performs man-in-the-middle style interception | T1557 | Adversary-in-the-Middle |

## Collection

| Behavior cue | ATT&CK ID | Technique |
|---|---:|---|
| Searches local file systems, config files, local databases, VM files, or process memory for data of interest | T1005 | Data from Local System |
| Searches connected removable media for files or data of interest | T1025 | Data from Removable Media |
| Collects clipboard contents | T1115 | Clipboard Data |
| Automatically gathers data on a schedule or through scripted bulk collection | T1119 | Automated Collection |
| Collects email messages, mailboxes, or user email content | T1114 | Email Collection |
| Takes screenshots or captures the desktop | T1113 | Screen Capture |
| Steals web session cookies or authentication cookies | T1539 | Steal Web Session Cookie |

## Command and control, transfer, and staging

| Behavior cue in description | ATT&CK ID | Technique |
|---|---:|---|
| Generic application-layer protocol used for C2, but protocol not specified | T1071 | Application Layer Protocol |
| C2 over HTTP or HTTPS, web requests used for beaconing or commands | T1071.001 | Web Protocols |
| C2 over FTP, FTPS, SFTP, or other file-transfer protocol | T1071.002 | File Transfer Protocols |
| C2 over email protocols or email messages used for command exchange | T1071.003 | Mail Protocols |
| C2 over DNS | T1071.004 | DNS |
| C2 over publish/subscribe protocols such as MQTT or similar brokered messaging | T1071.005 | Publish/Subscribe Protocols |
| Encodes C2 data using standard encodings such as Base64 or similar common encodings | T1132.001 | Standard Encoding |
| Downloads or transfers tools, payloads, or files from an external system into the victim environment | T1105 | Ingress Tool Transfer |
| Stages collected data in a local directory or central local location before exfiltration | T1074.001 | Local Data Staging |
| Compresses or archives data using built-in or external utilities before exfiltration | T1560.001 | Archive via Utility |

## Process injection and propagation

| Behavior cue | ATT&CK ID | Technique |
|---|---:|---|
| Generic code or shellcode injection into another process | T1055 | Process Injection |
| DLL injection | T1055.001 | Dynamic-link Library Injection |
| Portable executable injection or reflective PE loading into a process | T1055.002 | Portable Executable Injection |
| Thread execution hijacking | T1055.003 | Thread Execution Hijacking |
| APC queue injection | T1055.004 | Asynchronous Procedure Call |
| Injection via ptrace system calls | T1055.008 | Ptrace System Calls |
| Injection via /proc memory interfaces | T1055.009 | Proc Memory |
| Extra Window Memory injection | T1055.011 | Extra Window Memory Injection |
| Suspended process created then memory or image replaced; hollowed process | T1055.012 | Process Hollowing |
| Process doppelgänging or transacted image replacement | T1055.013 | Process Doppelgänging |
| VDSO hijacking | T1055.014 | VDSO Hijacking |
| ListPlanting or list-view control abuse for injection | T1055.015 | ListPlanting |
| Spreads via removable media, USB propagation, or autorun on removable drives | T1091 | Replication Through Removable Media |

## Permissions modification and impact

| Behavior cue | ATT&CK ID | Technique |
|---|---:|---|
| Generic file or directory permissions modification to bypass access controls | T1222 | File and Directory Permissions Modification |
| Windows ACL or file permission modification | T1222.001 | Windows Permissions |
| Linux or macOS permission or attribute modification | T1222.002 | Linux and Mac Permissions |
| Generic disk wiping or corruption of raw disk data | T1561 | Disk Wipe |
| Corrupts or wipes disk structures needed to boot, such as partition tables or boot records | T1561.002 | Disk Structure Wipe |

## What not to map directly

These details alone usually do **not** justify a technique ID:

- Malware family name or threat group name
- Generic labels like RAT, trojan, worm, downloader, stealer, or backdoor without concrete behaviors
- Programming language used to build malware, unless the language itself is the execution mechanism described
- Encryption, hashing, packing, or encoding names unless the behavior itself is described
- Mere mention of network communication without evidence it is command-and-control, exfiltration preparation, interception, or another ATT&CK behavior
- A protocol name by itself without context showing how it is used
- A process name mentioned only as an implementation detail unless tied to execution, injection, persistence, or masquerading