# Ollama Bridge for LinkedIn Jobs MCP Server

This directory contains everything you need to use the LinkedIn Jobs MCP server with Ollama local LLMs.

## 📁 Files Overview

- **`mcp-server.js`** - The Model Context Protocol server that exposes LinkedIn job search as a tool
- **`mcp-config.json`** - Configuration file for MCP servers (used by ollmcp client)
- **`start-ollmcp.bat`** - Windows batch script to launch the interactive Ollama client
- **`README.md`** - This file - setup and usage instructions
- **`SETUP_SUMMARY.md`** - Detailed summary of what was implemented and why
- **`.venv/`** - Python virtual environment (auto-created, in .gitignore)

## 🚀 Quick Start

This uses the `ollmcp` (MCP Client for Ollama) which provides an interactive terminal UI with tool management.

**Prerequisites:**
- Python 3.11+
- Ollama running locally (`http://localhost:11434`)
- Node.js installed

**Setup:**

1. **Create and activate virtual environment:**
   ```bash
   cd ollama_bridge
   uv venv .venv --python 3.11
   source .venv/Scripts/activate  # On Windows Git Bash
   # OR
   .venv\Scripts\activate  # On Windows CMD/PowerShell
   ```

2. **Install ollmcp:**
   ```bash
   uv pip install --python .venv/Scripts/python.exe ollmcp
   ```

3. **Run from Windows CMD or PowerShell:**
   ```cmd
   cd ollama_bridge
   start-ollmcp.bat
   ```

   Or manually:
   ```cmd
   .venv\Scripts\python.exe -m mcp_client_for_ollama -j mcp-config.json -m olmo-3.1:latest
   ```

**Note:** The interactive client requires a proper Windows console (CMD/PowerShell), not Git Bash.

**Usage:**

Once the client starts, you'll see an interactive terminal. Simply type your query:

```
User: get me jobs for Software engineer fulltime in this recent week in the area of Erlangen Germany
```

The LLM will automatically use the `search_linkedin_jobs` tool to find jobs!

**Interactive Commands:**
- `t` or `tools` - Enable/disable specific tools
- `m` or `model` - Switch between Ollama models
- `mc` or `model-config` - Configure model parameters
- `hil` or `human-in-loop` - Toggle approval prompts for tool execution
- `rs` or `reload-servers` - Hot-reload MCP servers
- `q` or `quit` - Exit

## 🔧 Configuration

### MCP Server Configuration (`mcp-config.json`)

```json
{
  "mcpServers": {
    "linkedin-jobs": {
      "command": "node",
      "args": [
        "c:/Users/Srinjoy Ghosh/Desktop/lookinto/linkedin job mcp/ollama_bridge/mcp-server.js"
      ]
    }
  }
}
```

**Important:** Update the path in `args` to match your actual installation directory.

### Supported Ollama Models

Models that support tool calling:
- ✅ `olmo-3.1:latest`
- ✅ `mistral-small3.2:latest`
- ✅ `qwen3-coder:latest`
- ✅ `gemma3:27b`
- ✅ `phi4:latest`

Check [Ollama's tools models page](https://ollama.com/search?c=tools) for the latest list.

## 🛠️ How It Works

### Architecture

```
┌─────────────┐      ┌──────────────┐      ┌────────────────┐
│   ollmcp    │─────>│  MCP Server  │─────>│ LinkedIn Jobs  │
│   Client    │      │ (Node.js)    │      │   (index.js)   │
└─────────────┘      └──────────────┘      └────────────────┘
       │                                             │
       │                                             ▼
       │                                      ┌─────────────┐
       └─────────────────────────────────────>│   Ollama    │
                                              │   (LLM)     │
                                              └─────────────┘
```

1. **ollmcp Client**: Provides the interactive terminal UI and manages the conversation
2. **MCP Server**: Exposes LinkedIn job search as a standardized tool
3. **Ollama**: Runs the local LLM and decides when to use tools
4. **LinkedIn Jobs**: Scrapes LinkedIn for job postings (from parent `index.js`)

### Tool Definition

The MCP server exposes one tool: `search_linkedin_jobs`

**Parameters:**
- `keyword` (required): Job title or keywords
- `location` (required): Location (city, country, or "Worldwide")
- `dateSincePosted`: "past 24 hours", "past week", "past month"
- `jobType`: "full time", "part time", "contract", etc.
- `remoteFilter`: "on site", "remote", "hybrid"
- `limit`: Max results (default: 25)
- `sortBy`: "recent" or "relevant"
- `geoId`: LinkedIn geographic ID (optional)

## 🐛 Troubleshooting

### "ollmcp: command not found" or "module not found"

**Solution:** Make sure you're using the virtual environment:
```bash
source .venv/Scripts/activate
# Then try again
```

Or use the full path:
```bash
.venv/Scripts/python.exe -m mcp_client_for_ollama -j mcp-config.json -m olmo-3.1:latest
```

### "No tools available from the server"

**Problem:** The ollmcp client starts but shows "No tools available from the server".

**Possible causes and solutions:**

1. **MCP server path is incorrect** in `mcp-config.json`:
   - Update the path to the absolute path to `mcp-server.js`
   - Example: `"c:/Users/YourName/Desktop/linkedin job mcp/ollama_bridge/mcp-server.js"`

2. **MCP server is crashing on startup:**
   - Test the server manually: `node mcp-server.js`
   - Should show: "LinkedIn Jobs MCP Server running on stdio"
   - If error "Cannot find module '../index'", the path to parent index.js is wrong

3. **Node.js not in PATH:**
   - Test: `node --version`
   - Make sure Node.js is accessible from the command line

4. **Try reloading servers in ollmcp:**
   - In the client, type `rs` or `reload-servers`
   - This will restart all MCP servers

### "NoConsoleScreenBufferError" or "Found xterm-256color"

**Problem:** The interactive client doesn't work in Git Bash.

**Solution:** Run from Windows CMD or PowerShell:
```cmd
start-ollmcp.bat
```

### "Model does not support tools"

**Problem:** The Ollama model you're using doesn't support function calling.

**Solution:** Switch to a model that supports tools:
```bash
# In the ollmcp client, press 'm' and select a different model
# Or update config.json:
{
  "model": "mistral-small3.2:latest"
}
```

### MCP Server Connection Failed

**Check:**
1. Node.js is installed: `node --version`
2. Path in `mcp-config.json` is correct
3. Parent `index.js` exists and dependencies are installed (`npm install` in parent directory)

### Ollama Not Running

**Solution:**
```bash
# Start Ollama
ollama serve

# Or on Windows, make sure the Ollama desktop app is running
```

## 📚 Examples

### Example 1: Find Remote Jobs

```
User: Find remote software engineer jobs posted in the past week
```

### Example 2: Specific Location

```
User: Get me fulltime data scientist positions in Berlin, Germany from the past month
```

### Example 3: With Salary and Experience

```
User: Search for senior machine learning engineer jobs in San Francisco with 100k+ salary
```

## 🔗 Related Resources

- [ollmcp (MCP Client for Ollama)](https://github.com/jonigl/mcp-client-for-ollama)
- [Model Context Protocol (MCP) Specification](https://spec.modelcontextprotocol.io/)
- [Ollama](https://ollama.com/)
- [Ollama Tool Calling Docs](https://docs.ollama.com/capabilities/tool-calling)

## 📝 Notes

- The MCP server runs on stdio transport (spawned as a subprocess by the client)
- Each tool call fetches fresh data from LinkedIn (with 1-hour caching in `index.js`)
- LinkedIn has bot detection - results may vary based on rate limiting
- This is for educational and personal use only

---

**Need help?** Check the main [README.md](../README.md) in the parent directory or open an issue on GitHub.
