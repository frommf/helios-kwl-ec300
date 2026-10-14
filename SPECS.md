# Helios easyControls API Specification

> [!IMPORTANT]
> **Governance & Maintenance**
> - **Purpose:** This document is the authoritative "Single Source of Truth" for the Helios API. It is designed to be parsed quickly by AI agents to ensure safe and efficient interaction.
> - **When to Update:** Agents must update this document whenever they discover and **verify** a new variable ID, endpoint, or hardware quirk.
> - **Style:** Keep updates technical, concise, and structured. Avoid boilerplate.

**Critical Safety Requirement:** Read-only access with party mode control exception. Never send state-altering variables (`v00xxx=y`) except for session establishment and party mode control.

## 1. Protocol & Authentication
- **Host:** `helios.fritz.box` (port 80)
- **Session:** IP-based tracking. Must establish a session before XML endpoints become accessible.
- **Login Command:** `POST /info.htm`
- **Body:** `v00402=!helios!` (Default password)
- **Quirk:** The embedded webserver is non-standard. Use `HTTP/1.0`. Modern `HTTP/1.1` clients often fail because the server closes connections early or omits mandatory headers.

## 2. Data Retrieval (Read-Only)
- **Method:** `POST` (A standard `GET` returns a fake 404/SD-Card error).
- **Target:** `/data/werte8.xml`
- **Body:** `xml=/data/werte8.xml` (**Crucial**: You must tell the server which file to buffer).
- **Example:** `curl -s -d "xml=/data/werte8.xml" http://helios.fritz.box/data/werte8.xml`

## 3. Core Variable Reference (`werte8.xml`)

| Category | ID | Description | Values / Units |
| :--- | :--- | :--- | :--- |
| **Temperatures** | `v00104` | Outdoor air | °C (float) |
| | `v00105` | Supply air | °C (float) |
| | `v00106` | Exhaust air | °C (float) |
| | `v00107` | Extract air | °C (float) |
| **Fan Speed** | `v00102` | Current Stage | 1–4 (Int) — Note: During party mode, display v00092 instead |
| | `v00103` | Current Flow | % (Float) |
| | `v00348` | Supply RPM | RPM (Int) |
| | `v00349` | Extract RPM | RPM (Int) |
| **Mode** | `v00101` | Base Mode | 0=Auto, 1=Manual |
| | `v00094` | Party Mode Active | 0=Off, 1=On (read-only in werte8.xml) |
| | `v00099` | Quiet Mode | 0=Off, 1=On |
| | `v00601` | Holiday Mode | 0=Off, 1=On |
| **Party Config** | `v00091` | Party Duration | 5-180 minutes (multiples of 5) |
| | `v00092` | Party Fan Stage | 1-4 |
| | `v00093` | Remaining Time | Minutes (read-only, server-calculated) |
| **Status** | `v01306` | State Flags | 32-bitmask (Binary string) |

## 4. Operational Logic
The **Effective Mode** is determined by priority override:
1. `v00094 == 1` → **Party**
2. `v00099 == 1` → **Quiet**
3. `v00601 == 1` → **Holiday**
4. `v00101 == 1` → **Manual**
5. Else → **Automatic**

## 5. Forbidden Operations (Audit strictly)
- Writing to `/ruhe.htm`, `/urlaub.htm`, or `/syst.htm`.
- Sending variables that modify state is forbidden, **EXCEPT**:
  - `v00402` to `/info.htm` for login (always permitted)
  - `v00091`, `v00092`, `v00094` to `/party.htm` for party mode control (explicitly allowed)

## 6. Party Mode Control (Explicitly Allowed)

Party mode is the **ONLY** write operation permitted beyond authentication.

**Endpoint:** `/party.htm` (POST)

**Display Behavior:** When party mode is active (`v00094 == 1`), the fan stage should display `v00092` (party target stage) instead of `v00102` (current actual stage). This matches the web interface behavior and shows the intended target stage rather than the ramping/transitional stage.

### Activation
**Body:** `v00092=<stage>&v00091=<minutes>&v00093=0&v00094=1`

Parameters:
- `v00091`: Duration in minutes (5-180, multiples of 5)
- `v00092`: Fan stage (1-4)
- `v00093`: Remaining time (always 0 for activation, server calculates)
- `v00094`: Activation flag (1=activate)

**Example:**
```bash
# Activate party mode for 90 minutes at fan stage 3
curl -d "v00092=3&v00091=90&v00093=0&v00094=1" http://helios.fritz.box/party.htm
```

### Deactivation
**Body:** `v00094=0`

**Example:**
```bash
# Deactivate party mode
curl -d "v00094=0" http://helios.fritz.box/party.htm
```

### Authentication
Like data endpoints, `/party.htm` requires prior authentication. If a 403 response is received, perform login via `/info.htm` and retry.

**Reference:** See `start_party.sh` for working implementation.

## 7. Resources

### Documentation
- **[README.md](README.md)** — Main documentation: installation, usage examples, troubleshooting
- **[AGENTS.md](AGENTS.md)** — Development guidance, architecture, safety mandates
- **`vendor/helios_web_dump/README.md`** — Web interface structure documentation (local-only, git-ignored reference material; never modify or commit)

### Implementation
- **`src/helios-kwl-ec300/`** — Modern async Python library (recommended)
- **`helios_status.py`** — Original monolithic script (DEPRECATED, kept for reference)

### Data Files
- **`vendor/helios_web_dump/data/`** — Local copies of labels (`lab*_de.xml`) and dropdowns (`dl*_de.xml`) — read-only, git-ignored reference material (never modify or commit; see AGENTS.md Safety Mandate 8)
