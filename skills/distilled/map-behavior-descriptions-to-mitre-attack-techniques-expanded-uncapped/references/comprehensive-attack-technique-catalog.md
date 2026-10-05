# Comprehensive ATT&CK technique catalog for prose mapping

Use this catalog as the explicit lookup table for mapping behavior descriptions to ATT&CK IDs. Prefer the most specific supported sub-technique. Do not output both parent and child for the same behavior unless hierarchical output is explicitly required.

| ATT&CK ID | Technique name | Use when the description explicitly indicates | Common cues / examples | Do not confuse with |
|---|---|---|---|---|
| T1003 | OS Credential Dumping | Dumping credentials, hashes, or secrets from OS credential material when the exact source is unclear | dump credentials, dump hashes, extract passwords from OS stores | T1555 password stores |
| T1003.002 | Security Account Manager | Extracting credential material from the SAM database | SAM dump, local account hashes from SAM | T1003 generic; T1087.001 local account discovery |
| T1003.004 | LSA Secrets | Accessing Local Security Authority secrets | LSA secrets, cached secrets from LSA | T1003 generic |
| T1005 | Data from Local System | Reading, copying, stealing, or extracting local files or data from the compromised host | collect documents, read config files, steal local databases | T1083 if only enumeration is described |
| T1007 | System Service Discovery | Enumerating registered local services | list services, query services, enumerate service names | T1543 service creation/modification |
| T1016 | System Network Configuration Discovery | Gathering network configuration and settings | IP address, MAC, DNS server, DHCP, gateway, adapters, routes | T1082 host details |
| T1016.001 | Internet Connection Discovery | Checking whether Internet connectivity exists | connectivity test, online check, ping external host | T1016 generic network config |
| T1016.002 | Wi-Fi Discovery | Gathering Wi-Fi network information | SSIDs, wireless profiles, Wi-Fi passwords, nearby wireless networks | T1016 generic network config |
| T1018 | Remote System Discovery | Enumerating other systems on the network | list hosts, computers, IP ranges, subnets, neighbors | T1482 domain trusts |
| T1027.009 | Embedded Payloads | Embedding payloads within other files to conceal malicious content | payload embedded in document/script/executable/container file | T1027.011 fileless storage |
| T1027.011 | Fileless Storage | Storing data or payloads in non-file formats to conceal activity | registry, WMI repository, event logs, shortcuts, alternate stores used instead of normal files | T1564 hide artifacts; T1027.009 embedded payloads |
| T1027.013 | Encrypted/Encoded File | Encrypting or encoding files to obfuscate strings, bytes, or patterns | encoded file, encrypted payload file, obfuscated file contents | generic encryption not tied to evasion |
| T1033 | System Owner/User Discovery | Identifying the current or active user | whoami, username, logged-in user, owner | T1087 account discovery |
| T1036 | Masquerading | Making artifacts appear legitimate or benign when the exact method is unclear | fake legitimate name, benign-looking file/app | T1564 hiding |
| T1036.008 | Masquerade File Type | Making a malicious payload appear to be another file type | fake document/image, misleading extension/icon/signature/format | T1036.007 double extension |
| T1037 | Boot or Logon Initialization Scripts | Using scripts automatically executed at boot or logon initialization to establish persistence | login scripts, startup scripts, initialization scripts | T1547 generic autostart; T1546 event-triggered execution |
| T1040 | Network Sniffing | Passively capturing network traffic | sniff traffic, packet capture, monitor network traffic | T1557 AiTM |
| T1047 | Windows Management Instrumentation | Using WMI to execute commands or payloads | WMI execution, process create via WMI, remote/local WMI command execution | T1546.003 WMI event subscription |
| T1056.001 | Keylogging | Logging user keystrokes to intercept credentials or other input | keylogger, captures keystrokes, records typed input | T1115 clipboard data |
| T1057 | Process Discovery | Enumerating running processes | process list, running tasks, enumerate processes | T1518 software discovery |
| T1059 | Command and Scripting Interpreter | Executing commands or scripts via an interpreter when type is unclear | shell commands, script execution, interpreter use | specific T1059 sub-techniques |
| T1059.001 | PowerShell | Using PowerShell for execution | powershell, pwsh, PowerShell script | T1546.013 PowerShell profile persistence |
| T1059.002 | AppleScript | Using AppleScript for execution | AppleScript, osascript | T1059 generic |
| T1059.003 | Windows Command Shell | Using cmd.exe or Windows command shell | cmd.exe, command.com, shell commands on Windows | T1059 generic |
| T1059.004 | Unix Shell | Using sh, bash, zsh, or Unix shell commands | bash, sh, zsh, shell script | T1059 generic |
| T1059.005 | Visual Basic | Using VB or VBS for execution | VBScript, Visual Basic script | T1059 generic |
| T1059.006 | Python | Using Python for execution | python, python script | T1059 generic |
| T1059.007 | JavaScript | Using JavaScript for execution | JavaScript, JScript, Node-based script execution, JXA where described as JavaScript execution | T1059 generic |
| T1059.008 | Network Device CLI | Using network device command-line interfaces | router/switch CLI commands | T1059 generic |
| T1059.009 | Cloud API | Using cloud APIs to execute actions | cloud API calls for execution/management | T1059 generic |
| T1059.010 | AutoHotKey & AutoIT | Using AutoHotKey or AutoIT scripts | AHK, AutoIT | T1059 generic |
| T1059.011 | Lua | Using Lua | lua script | T1059 generic |
| T1059.012 | Hypervisor CLI | Using hypervisor CLI | hypervisor shell/CLI commands | T1059 generic |
| T1059.013 | Container CLI/API | Using container CLI or API as an execution mechanism | container CLI/API commands, orchestration CLI used to run actions | T1059 generic |
| T1071 | Application Layer Protocol | Using an application-layer protocol for C2 when the protocol family is unclear | application-layer C2, protocol-based beaconing | specific T1071 sub-techniques |
| T1071.001 | Web Protocols | Using HTTP/HTTPS or web protocols for C2 | HTTP beaconing, HTTPS C2, web requests for tasking | T1105 if only download is described |
| T1071.002 | File Transfer Protocols | Using FTP or similar file transfer protocols for C2 | FTP, FTPS, TFTP for C2/transfer channel | T1105 if only ingress transfer is described |
| T1071.003 | Mail Protocols | Using email protocols for C2 | SMTP/IMAP/POP-based C2 | T1114 email collection |
| T1071.004 | DNS | Using DNS for C2 | DNS tunneling, TXT record commands, DNS beaconing | ordinary DNS resolution |
| T1071.005 | Publish/Subscribe Protocols | Using pub/sub protocols for C2 | MQTT, AMQP, XMPP-like pub/sub tasking | T1071 generic |
| T1074.001 | Local Data Staging | Staging collected data in a local directory or archive before exfiltration | local staging folder, archive before upload, central local collection point | T1005 direct collection |
| T1080 | Taint Shared Content | Delivering payloads to remote systems by adding content to shared storage or repositories | network share contamination, shared drive payload, internal repo tainting | T1105 ingress transfer |
| T1082 | System Information Discovery | Gathering OS, hardware, or general host details after compromise | OS version, architecture, hostname, hardware info | T1592/T1592.001 pre-compromise victim host info |
| T1083 | File and Directory Discovery | Enumerating files, directories, paths, or metadata | list files, search directories, enumerate paths | T1005 if contents are collected |
| T1087 | Account Discovery | Discovering accounts when scope is unclear | enumerate users/accounts | T1033 current user |
| T1087.001 | Local Account | Discovering local accounts | local users, local account list | T1087 generic |
| T1087.002 | Domain Account | Discovering domain accounts | domain users, AD user enumeration | T1087 generic |
| T1087.003 | Email Account | Discovering email accounts or addresses | mailbox account list, email address enumeration | T1087 generic |
| T1087.004 | Cloud Account | Discovering cloud accounts | IAM users, tenant identities, cloud accounts | T1087 generic |
| T1091 | Replication Through Removable Media | Spreading via removable media | USB propagation, copy to removable drives, autorun on removable media | T1105 network transfer |
| T1105 | Ingress Tool Transfer | Downloading or transferring tools/files into the victim environment | download payload, fetch module, retrieve file from server | exfiltration/upload |
| T1114 | Email Collection | Collecting email data | collect emails, access mailbox contents, steal mail | T1071.003 mail protocols for C2 |
| T1115 | Clipboard Data | Reading or stealing clipboard contents | clipboard theft, monitor clipboard | T1056 input capture |
| T1119 | Automated Collection | Using automated techniques to collect internal data after access is established | automated collection, scheduled collection, scripted bulk collection | T1005 direct local data collection |
| T1133 | External Remote Services | Leveraging external-facing remote services for initial access or persistence | VPN, Citrix, externally exposed remote access service | internal lateral movement via remote services |
| T1213.006 | Databases | Mining or collecting valuable information from databases | query databases, dump database contents, collect from DBs | T1005 generic local file/data collection |
| T1216.001 | PubPrn | Using PubPrn.vbs to proxy execution of malicious remote files | pubprn.vbs execution, remote script via PubPrn | T1059.005 Visual Basic; generic proxy execution |
| T1218.004 | InstallUtil | Using InstallUtil to proxy execution of code through a trusted Windows utility | InstallUtil.exe execution, install utility abused to run malicious assemblies | T1218 generic signed binary proxy execution |
| T1218.011 | Rundll32 | Using rundll32.exe to proxy execution of malicious code | rundll32 execution, DLL export via rundll32 | T1574.001 DLL hijacking |
| T1218.013 | Mavinject | Using mavinject.exe to proxy execution of malicious code | mavinject execution, Microsoft Application Virtualization Injector abuse | T1218 generic signed binary proxy execution |
| T1222 | File and Directory Permissions Modification | Modifying file or directory permissions broadly | change ACLs/permissions to access or hide files | OS-specific sub-techniques |
| T1222.001 | Windows Permissions | Modifying Windows file or directory permissions | icacls, Windows ACL changes | T1222 generic |
| T1222.002 | Linux and Mac Permissions | Modifying Linux/macOS permissions | chmod, chown, permission bit changes | T1222 generic |
| T1482 | Domain Trust Discovery | Discovering domain or forest trust relationships | enumerate trusts, forest trust mapping | T1018 remote systems |
| T1518 | Software Discovery | Enumerating installed software broadly | installed applications, software inventory, version checks | T1518.001 security software |
| T1518.001 | Security Software Discovery | Enumerating security tools or configurations | AV, EDR, firewall, sensors, defensive tools | T1518 generic |
| T1518.002 | Backup Software Discovery | Enumerating backup software or configurations | backup agents, backup products, backup configs | T1518 generic |
| T1543 | Create or Modify System Process | Creating or modifying system-level processes to repeatedly execute payloads | create service/system process, modify service process, recurring execution via system process | T1547 boot/logon autostart |
| T1543.003 | Windows Service | Creating or modifying Windows services to repeatedly execute malicious payloads | create service, modify service, malicious Windows service | T1543 generic |
| T1546 | Event Triggered Execution | Persistence or execution triggered by events when the exact mechanism is unclear | event-based trigger, hook-based execution | specific T1546 sub-techniques |
| T1546.003 | Windows Management Instrumentation Event Subscription | Using WMI event subscriptions for persistence or execution | WMI event consumer/filter/binding | T1047 WMI execution |
| T1546.013 | PowerShell Profile | Executing malicious content via PowerShell profiles | profile.ps1 persistence, PowerShell profile trigger | T1059.001 PowerShell execution alone |
| T1547 | Boot or Logon Autostart Execution | Configuring automatic execution at boot or logon when the exact mechanism is unclear | autostart on boot/login | specific T1547 sub-techniques |
| T1547.001 | Registry Run Keys / Startup Folder | Using Run keys or Startup folder for autostart | HKCU/HKLM Run, Startup folder | T1547 generic |
| T1547.014 | Active Setup | Achieving persistence by adding a Registry key to Active Setup | Active Setup registry key, StubPath abuse | T1547 generic |
| T1548.002 | Bypass User Account Control | Bypassing UAC to elevate privileges | UAC bypass, auto-elevate abuse, eventvwr-style bypass | generic privilege escalation |
| T1555 | Credentials from Password Stores | Stealing credentials from stored password locations when store type is unclear | saved passwords, credential store theft | specific T1555 sub-techniques |
| T1555.001 | Keychain | Acquiring credentials from macOS Keychain | Keychain access, keychain dump | T1555 generic |
| T1555.003 | Credentials from Web Browsers | Stealing browser-stored credentials | browser passwords, browser login DB, saved web creds | T1555 generic |
| T1555.004 | Windows Credential Manager | Stealing from Windows Credential Manager | Credential Manager, vault creds | T1555 generic |
| T1555.005 | Password Managers | Acquiring credentials from third-party password managers | KeePass, 1Password, LastPass-like local stores | T1555 generic |
| T1557 | Adversary-in-the-Middle | Positioning between networked devices to intercept or manipulate communications | AiTM, man-in-the-middle, interception between endpoints | T1040 passive sniffing |
| T1564 | Hide Artifacts | Hiding artifacts broadly when the exact method is unclear | conceal files/processes/windows/artifacts | T1036 masquerading |
| T1564.001 | Hidden Files and Directories | Marking files or directories hidden | hidden attribute, dotfiles for concealment | T1564 generic |
| T1564.012 | File/Path Exclusions | Writing artifacts to AV or defender excluded paths or names | excluded folder/path/file name abuse | T1036.005 lookalike location |
| T1566.002 | Spearphishing Link | Sending spearphishing emails with a malicious link to gain access | phishing email with link, malicious URL in email, credential-harvest or payload-delivery link | generic phishing or attachment-based phishing |
| T1568.001 | Fast Flux DNS | Using fast flux DNS to hide a command and control channel behind rapidly changing IPs | fast flux, rapidly changing IPs for one domain | T1071.004 DNS C2 |
| T1574.001 | DLL | Abusing DLLs for persistence, privilege escalation, or defense evasion, including DLL hijacking/search-order hijacking/side-loading when explicitly described | DLL hijacking, search-order hijack, side-loading, remote share DLL load path abuse | T1218.011 rundll32 |
| T1583 | Acquire Infrastructure | Obtaining infrastructure for operations when the exact type is unclear | acquire infrastructure, rent hosting | specific T1583 sub-techniques |
| T1583.001 | Domains | Acquiring domains | register or buy domains | T1583.002 DNS server |
| T1583.002 | DNS Server | Acquiring or setting up DNS servers | own DNS server, leased DNS infrastructure | T1583.001 domains |
| T1583.003 | Virtual Private Server | Renting or acquiring VPS infrastructure | VPS, rented VM/container hosting | T1583.004 server |
| T1583.004 | Server | Acquiring physical servers | leased or bought server hardware | T1583.003 VPS |
| T1583.005 | Botnet | Acquiring or renting a botnet | rented botnet, purchased botnet access | T1583 generic |
| T1583.006 | Web Services | Registering for web services to support operations | cloud web service, social/web platform service used as infrastructure | T1583.007 serverless |
| T1583.007 | Serverless | Acquiring or configuring serverless infrastructure | functions, workers, serverless scripts | T1583.006 web services |
| T1583.008 | Malvertising | Purchasing online ads for malicious distribution | malicious ads, ad purchase for delivery | T1583 generic |
| T1587.001 | Malware | Developing malware or malware components for use during targeting or operations | build malware, develop payloads, create malware components | T1587 generic capability development |
| T1592 | Gather Victim Host Information | Gathering information about victim hosts for targeting before compromise | victim host research, host details gathered during targeting | T1082 post-compromise system information discovery |
| T1592.001 | Hardware | Gathering victim host hardware information before compromise | hardware inventory, device model, hardware infrastructure research | T1082 post-compromise hardware discovery |
| T1594 | Search Victim-Owned Websites | Searching victim-owned websites for information useful for targeting | victim website research, scrape company site, review public victim web content | generic web browsing not tied to targeting |
| T1596.001 | DNS/Passive DNS | Searching DNS or passive DNS data for victim information useful for targeting | passive DNS lookup, DNS history, subdomain enumeration from DNS data | T1071.004 DNS C2 |
| T1597.002 | Purchase Technical Data | Purchasing technical information about victims for targeting | buy technical data, purchase victim infrastructure details, acquire technical records | generic victim research without purchase |
| T1652 | Device Driver Discovery | Enumerating local device drivers | list drivers, enumerate loaded drivers | T1518 software discovery |

## Notes on use

- If the text explicitly names a sub-technique mechanism, choose that sub-technique.
- If the text only supports the broader behavior, choose the parent technique.
- Include multiple rows only when the description explicitly contains multiple distinct behaviors.
- Do not infer unsupported siblings just because they are commonly associated.
- The catalog is intentionally broad across malware, intrusion, and procedure descriptions; use it to improve recall while keeping evidence-based precision.