# ATT&CK behavior-to-technique mapping reference

Use this reference to map explicit behaviors in malware or intrusion descriptions to ATT&CK techniques. Prefer the most specific technique supported by the text.

## Core mappings used in malware/procedure descriptions

| Behavior phrase in description | ATT&CK technique | Notes |
|---|---|---|
| Command and control over HTTP or HTTPS; web-based C2 traffic | **T1071.001 – Web Protocols** | Use when the text says the malware communicates with C2 via HTTP/HTTPS/web requests. |
| File listing, directory listing, current working directory, retrieve file metadata | **T1083 – File and Directory Discovery** | Covers enumerating files/directories and related metadata. |
| Modify file creation/modification/access timestamps; timestomping | **T1070.006 – Timestomp** | Use when timestamps are altered to hide activity. |
| Enumerate running processes | **T1057 – Process Discovery** | Use for process lists or running-process information. |
| Detect installed antivirus or security products | **T1518.001 – Security Software Discovery** | Use for AV/security tool identification. |
| Execute commands via cmd.exe; create remote shell using Windows shell | **T1059.003 – Windows Command Shell** | Prefer over generic command execution when cmd.exe or Windows shell is explicit. |
| Generic command execution via command line or interpreter, but shell type not clear | **T1059 – Command and Scripting Interpreter** | Use only when no more specific sub-technique is justified. |
| Download files, payloads, tools, or additional malware from C2 to victim | **T1105 – Ingress Tool Transfer** | Covers transfer of tools/files into the victim environment. |
| Inject shellcode/code into another process such as svchost.exe | **T1055 – Process Injection** | Use for code injection into a process. |
| Persistence via WMI event subscription | **T1546.003 – Windows Management Instrumentation Event Subscription** | Use when persistence is specifically through WMI event subscription. |
| Use WMI to execute actions or query systems, without event-subscription persistence | **T1047 – Windows Management Instrumentation** | Use for operational WMI usage rather than persistence. |
| Enumerate domain user accounts | **T1087.002 – Domain Account** | Use for domain user discovery. |
| Enumerate domain groups | **T1069.002 – Domain Groups** | Use for domain group discovery. |
| Enumerate domain trusts | **T1482 – Domain Trust Discovery** | Use for trust relationships between domains/forests. |
| Enumerate remote systems, hosts, computers, or subnets on the network | **T1018 – Remote System Discovery** | Good fit for computer/subnet enumeration when the text is about discovering systems on the network. |
| Persistence via registry Run keys or Startup folder | **T1547.001 – Registry Run Keys / Startup Folder** | Use when autorun persistence is established through these locations. |
| Read or steal clipboard contents | **T1115 – Clipboard Data** | Use for clipboard monitoring or theft. |
| Obtain credentials from stored password locations such as FTP clients or wireless profiles | **T1555 – Credentials from Password Stores** | Use when credentials are recovered from local stores/configurations. |
| Hide app icon, hide files, conceal artifacts from user or system view | **T1564 – Hide Artifacts** | Broad hiding/concealment behavior. |
| Disguise malware as a legitimate app/file/package; replace legitimate app with malicious version | **T1036 – Masquerading** | Use when malware pretends to be something legitimate. |
| Spread via USB/removable media | **T1091 – Replication Through Removable Media** | Use for propagation through removable drives. |
| User execution of a malicious file/app is required | **T1204.002 – Malicious File** | Use when infection depends on opening/installing a malicious file or app. |
| Discover OS version, hardware, host details, or general system properties | **T1082 – System Information Discovery** | Use for OS version and general host/system information. |
| Discover IP address, MAC address, gateway, DNS, DHCP, WINS, or network adapter configuration | **T1016 – System Network Configuration Discovery** | Use for network configuration details. |
| Discover current username or account owner | **T1033 – System Owner/User Discovery** | Use for username/current user discovery. |

## Phrase-level guidance

### Network/C2
- "communicates with command and control server via HTTP" → **T1071.001**
- Encryption or obfuscation of C2 traffic alone does **not** change the technique; keep **T1071.001** if the protocol is HTTP/HTTPS.

### Command execution
- "execute commands using cmd.exe" or "create a remote shell" on Windows → **T1059.003**
- "use the command line to execute PEs" without a named shell → **T1059**

### Discovery
- "list files/directories", "retrieve file metadata", "current working directory" → **T1083**
- "running processes" → **T1057**
- "loaded modules" is not covered by this compact reference; only map it if the description also clearly includes process enumeration, in which case **T1057** may still be justified by the process-discovery wording.
- "OS version" → **T1082**
- "username" → **T1033**
- "IP, MAC, gateway, DNS, DHCP, WINS" → **T1016**
- "domain users" → **T1087.002**
- "domain groups" → **T1069.002**
- "domain trusts" → **T1482**
- "computers/subnets" on the network → **T1018**
- "installed anti-virus" → **T1518.001**

### Persistence / execution / transfer
- "registry Run key" → **T1547.001**
- "WMI event subscription" → **T1546.003**
- "download payload/file from C2" → **T1105**
- "inject shellcode into svchost.exe" → **T1055**

### Collection / credential access
- "clipboard" → **T1115**
- "credentials from FTP client" or "wireless profiles" → **T1555**

### Defense evasion / disguise
- "modify timestamps" → **T1070.006**
- "hide icon" or otherwise conceal presence → **T1564**
- "replace legitimate app with malicious version" or disguise as benign software → **T1036**

## What not to map from these descriptions unless explicitly stated
- Malware written in C++, Delphi, etc.
- Use of DES, AES, XOR, MD5, CBC, or other crypto details by themselves
- Malware family names or threat actor names
- Generic mention of beaconing unless the protocol/behavior clearly maps to a known ATT&CK technique
- Extraction of payloads from images unless the description clearly states steganography or another ATT&CK-defined behavior and you are certain of the mapping

## Output rule
Return a **set-like list** of ATT&CK IDs per row: include each justified technique once, omit unsupported guesses.