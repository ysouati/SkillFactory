# ATT&CK disambiguation notes for short behavior descriptions

## 1) Prefer specific sub-techniques when explicit
- HTTP/HTTPS C2 → **T1071.001**, not just T1071.
- cmd.exe / Windows shell / remote shell on Windows → **T1059.003**, not generic T1059.
- Registry Run key persistence → **T1547.001**, not a broader persistence parent.
- WMI event subscription persistence → **T1546.003**, not T1047.

## 2) Do not over-infer from malware capability lists
Descriptions often list many capabilities. Only map those that are clearly ATT&CK behaviors.

Examples:
- "encrypted with XOR" does **not** by itself imply a separate ATT&CK technique.
- "associated with group X" does **not** imply techniques used by that group in other contexts.
- "written in Delphi/C++" does **not** map to ATT&CK.

## 3) Discovery techniques: keep them separated
- Files/directories/working directory/metadata → **T1083**
- Running processes → **T1057**
- OS version/system properties → **T1082**
- Network settings like IP/MAC/gateway/DNS → **T1016**
- Username/current user → **T1033**
- Domain users → **T1087.002**
- Domain groups → **T1069.002**
- Domain trusts → **T1482**
- Computers/subnets/remote hosts → **T1018**

Do not collapse these into one generic discovery label if the text supports multiple distinct discovery techniques.

## 4) Command execution: choose the narrowest justified label
- If the text explicitly says `cmd.exe`, command shell, or remote shell on Windows, use **T1059.003**.
- If it only says command line execution or execute PE from command line, and no shell is named, **T1059** is safer.

## 5) WMI confusion
- **T1546.003** is for persistence via WMI event subscription.
- **T1047** is for using WMI operationally.
If the text says persistence through WMI scripts/events/subscriptions, choose **T1546.003**.

## 6) Android/mobile disguise and hiding
- Hidden launcher icon or concealed app presence → **T1564 – Hide Artifacts**.
- Pretending to be a legitimate app or replacing one with a malicious version → **T1036 – Masquerading**.
- If infection requires the user to install/open the malicious app/file, **T1204.002 – Malicious File** may also apply.

## 7) Transfer vs execution
- Downloading a payload/tool/file from C2 → **T1105**.
- Executing that payload via shell/interpreter may additionally justify **T1059** or **T1059.003** if explicitly stated.
These are separate techniques and can both be included when both behaviors are present.

## 8) Keep predictions non-empty and validated
A common failure mode is producing no predictions because of uncertainty. If a behavior is explicitly stated and appears in the mapping reference, include it. Then validate formatting before writing output.

## 9) Formatting discipline
- Output ATT&CK IDs as strings.
- Deduplicate within each row.
- Preserve one output object per input row.
- Use only IDs you can justify from the text.