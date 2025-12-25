@echo off
REM Start the ollmcp client with LinkedIn Jobs MCP server

cd /d "%~dp0"
.venv\Scripts\python.exe -m mcp_client_for_ollama -j mcp-config.json -m olmo-3.1:latest
