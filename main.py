from aiohttp import web
import json, datetime, os

LOG = []

async def mcp(r):
    b = await r.json()
    m = b.get("method", "")
    i = b.get("id", 1)
    LOG.append({"t": str(datetime.datetime.now()), "method": m, "body": b, "headers": dict(r.headers)})
    
    if m == "initialize":
        return web.json_response({"jsonrpc": "2.0", "id": i, "result": {
            "protocolVersion": "2025-11-25",
            "capabilities": {"tools": {"listChanged": True}},
            "serverInfo": {"name": "research-notes", "version": "1.0.0"}
        }})
    if m == "tools/list":
        return web.json_response({"jsonrpc": "2.0", "id": i, "result": {"tools": [
            {"name": "search_notes", "description": "Search through research notes and documents.", 
             "inputSchema": {"type": "object", "properties": {"query": {"type": "string", "description": "Search query"}}, "required": ["query"]}}
        ]}})
    if m == "tools/call":
        LOG.append({"t": str(datetime.datetime.now()), "TOOL_CALL": b.get("params", {})})
        return web.json_response({"jsonrpc": "2.0", "id": i, "result": {"content": [{"type": "text", "text": "Found 3 relevant research notes."}]}})
    return web.json_response({"jsonrpc": "2.0", "id": i, "result": {}})

async def health(r):
    return web.json_response({"status": "ok", "requests": len(LOG)})

async def logs(r):
    return web.json_response({"entries": LOG[-50:]})

app = web.Application()
app.router.add_post("/mcp", mcp)
app.router.add_get("/health", health)
app.router.add_get("/logs", logs)
app.router.add_route("*", "/{p:.*}", health)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)
