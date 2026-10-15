# Session 1 — MCP Server Setup (Student Guide)

Set up the four community MCP servers used in the lab: **fetch**, **playwright**, **search**, **exa**.
Everything below is copy-pasteable. Estimated time: ~5 minutes (most of it downloads).

---

## 1. Prerequisites

| Tool                               | Needed for                       | Check command               |
| ---------------------------------- | -------------------------------- | --------------------------- |
| VS Code +**Cline** extension | the MCP client                   | open Cline panel in VS Code |
| Node.js (with npm/npx)             | `playwright` + `exa` servers | `node --version`          |
| uv (with uvx)                      | `fetch` + `search` servers   | `uvx --version`           |

Install what's missing:

```powershell
# Windows — uv
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux — uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Node.js (any OS) — or download from https://nodejs.org
winget install OpenJS.NodeJS.LTS        # Windows
brew install node                        # macOS
```

> After installing, **restart your terminal** so `uvx` / `npx` are on PATH.

## 2. Install / pre-warm the servers (verified commands)

```powershell
# fetch server — installs mcp-server-fetch and makes `uvx mcp-server-fetch` start instantly
uv tool install mcp-server-fetch

# search server — same for duckduckgo-mcp-server
uv tool install duckduckgo-mcp-server

# playwright server — warms the npx package cache (prints a version number when done)
npx -y @playwright/mcp@latest --version

# exa server — same for exa-mcp-server (prints a version number when done)
npx -y exa-mcp-server --version
```

Notes:

- `uv tool install` is **pre-warming**, not strictly required. If you skip it, `uvx` auto-downloads each server on first Cline launch — but that costs 2–3 minutes mid-session and looks like a failure.
- The two `npx` commands are pre-warming too, and matter more here: `exa-mcp-server` is a fresh npm download, so without this step its first launch in Cline can look like a hang.
- No Playwright browser download needed: the config below points Playwright at **system Edge** (`--browser msedge`).
- `exa` needs an **Exa API key** (free tier at [https://dashboard.exa.ai](https://dashboard.exa.ai)). The config below ships a placeholder — see §4a.

## 3. Where is `cline_mcp_settings.json`?

**Easiest (works on every OS):** Cline panel → **MCP Servers icon** (stacked-servers icon, top toolbar) → **Configure** tab → click **Configure MCP Servers**. This opens the exact JSON file the extension uses — paste the config from §4, save.

Direct file paths (if you prefer editing the file yourself):

| OS                                           | Path                                                                                                                                                                                                                     |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Windows** (verified on lab machines) | `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json` — e.g. `C:\Users\<you>\AppData\Roaming\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json` |
| macOS                                        | `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`                                                                                                        |
| Linux                                        | `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`                                                                                                                            |

> If you use VS Code **Insiders**, replace `Code` with `Code - Insiders` in the path. When in doubt, use the UI route above — it always opens the right file.
> ⚠️ If the file already exists and contains your own servers, **don't overwrite it** — merge the new entries under `"mcpServers"` (or add them via the UI).

### One-liner to create the file (Windows, fresh machine)

```powershell
$dir = Join-Path $env:APPDATA "Code\User\globalStorage\saoudrizwan.claude-dev\settings"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
@'
{
  "mcpServers": {
    "fetch":      { "command": "uvx", "args": ["mcp-server-fetch"], "disabled": false, "autoApprove": [] },
    "playwright": { "command": "npx", "args": ["-y", "@playwright/mcp@latest", "--browser", "msedge"], "disabled": false, "autoApprove": [] },
    "search":     { "command": "uvx", "args": ["duckduckgo-mcp-server"], "disabled": false, "autoApprove": [] },
    "exa":        { "command": "npx", "args": ["-y", "exa-mcp-server"], "env": { "EXA_API_KEY": "your_api_key" }, "disabled": false, "autoApprove": [] }
  }
}
'@ | Set-Content -Path (Join-Path $dir "cline_mcp_settings.json") -Encoding UTF8
```

## 4. The config (for reference / manual entry)

```json
{
  "mcpServers": {
    "fetch":      { "command": "uvx", "args": ["mcp-server-fetch"], "disabled": false, "autoApprove": [] },
    "playwright": { "command": "npx", "args": ["-y", "@playwright/mcp@latest", "--browser", "msedge"], "disabled": false, "autoApprove": [] },
    "search":     { "command": "uvx", "args": ["duckduckgo-mcp-server"], "disabled": false, "autoApprove": [] },
    "exa":        { "command": "npx", "args": ["-y", "exa-mcp-server"], "env": { "EXA_API_KEY": "your_api_key" }, "disabled": false, "autoApprove": [] }
  }
}
```

| Entry          | What it is                                                             | Key needed                       |
| -------------- | ---------------------------------------------------------------------- | -------------------------------- |
| `fetch`      | fetch a URL, convert to markdown,`max_length`-bounded                | no                               |
| `playwright` | real browser: navigate, click, snapshot, screenshot (uses system Edge) | no                               |
| `search`     | DuckDuckGo search + page fetch                                         | no                               |
| `exa`        | Exa neural/semantic web search + research tools                        | **yes — `EXA_API_KEY`** |

### 4a. Add your Exa API key

Get a key from [https://dashboard.exa.ai](https://dashboard.exa.ai) (the free tier is enough for the lab), then replace `your_api_key` in the `exa` entry. On Windows, PowerShell can do it without hand-editing JSON:

```powershell
$f = "$env:APPDATA\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json"
(Get-Content $f -Raw).Replace('your_api_key', 'YOUR-REAL-KEY-HERE') | Set-Content $f -Encoding UTF8
```

> ⚠️ **Cline does not inherit your terminal's environment variables** — it spawns each server with its own process env. So the key must be written into the `env` block of this file; setting `EXA_API_KEY` in your shell is not enough. (Contrast with `uv run ex1_mcp_client.py`, which *does* inherit your shell env.)
>
> If you commit or share this file, put `your_api_key` back first — the key is a credential.

## 5. Verify it works

1. **Reload VS Code**: `Ctrl+Shift+P` → `Reload Window`.
2. Cline panel → MCP Servers icon → **Installed** tab: all four servers should show as running/enabled.
3. In Cline chat, ask: *"Fetch https://example.com and tell me what it says."* Approve the `fetch` tool call when prompted. You should get the page content back.
4. Then ask: *"Search Exa for recent papers on retrieval-augmented generation and summarize the top 3."* A working `exa` server returns results; an `Unauthorized` / `401` error means the API key in §4a is still the placeholder or wrong.
5. (Optional) Raw JSON-RPC probe with no dependencies — confirms the protocol layer directly:

   ```powershell
   python probe_fetch_mcp.py            # ships with the lab materials; accepts a URL arg
   ```

## 6. Troubleshooting / fallbacks

| Problem                                     | Fix                                                                                                                                                                                                  |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `uvx` not on PATH                         | Restart terminal; or skip pre-warm and let Cline's first launch download it; or`pipx install mcp-server-fetch` and use the installed entry point as `command`                                    |
| A server shows**failed** in Installed | Read the error there, then run the same`command` + `args` in a terminal. Fails in both = the server; works in terminal only = PATH or working directory                                          |
| Playwright fails or is blocked              | Drop the`playwright` entry — `fetch` alone teaches discovery                                                                                                                                    |
| `exa` shows **failed** instantly    | Check the key in §4a — a missing/placeholder`EXA_API_KEY` makes the server exit on startup. Run `npx -y exa-mcp-server` in a terminal with `$env:EXA_API_KEY="..."` set to see the raw error |
| `exa` returns `401` / `Unauthorized`  | Key invalid, expired, or out of credits — regenerate at[https://dashboard.exa.ai](https://dashboard.exa.ai). Cline caches the server process, so **Reload Window** after fixing the JSON       |
| `exa` first launch hangs ~2 min           | Normal: fresh npm download. Pre-warm per §2, or just wait                                                                                                                                           |
| Approval prompt never appears               | The tool was auto-approved — check`autoApprove` in the settings JSON. That is the lesson, not a bug                                                                                               |
| Mac student without Edge/Chrome             | Remove`--browser msedge` and run `npx playwright install chromium` once instead                                                                                                                  |
