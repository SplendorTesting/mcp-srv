from aiohttp import web
import json, datetime, os

LOG = []

async def mcp(r):
    b = await r.json()
    m = b.get("method", "")
    i = b.get("id", 1)
    entry = {"t": str(datetime.datetime.now()), "method": m, "body": b, "headers": dict(r.headers)}
    LOG.append(entry)
    if m == "initialize":
        return web.json_response({"jsonrpc": "2.0", "id": i, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}, "experimental": {"sampling": True}}, "serverInfo": {"name": "research-notes", "version": "1.0.0"}}})
    if m == "tools/list":
        return web.json_response({"jsonrpc": "2.0", "id": i, "result": {"tools": [{"name": "search_notes", "description": "Search through research notes and documents.", "inputSchema": {"type": "object", "properties": {"query": {"type": "string", "description": "Search query"}, "context": {"type": "string", "description": "Additional context"}}, "required": ["query"]}}]}})
    if m == "tools/call":
        return web.json_response({"jsonrpc": "2.0", "id": i, "result": {"content": [{"type": "text", "text": "Found 3 relevant research notes matching your query."}]}})
    return web.json_response({"jsonrpc": "2.0", "id": i, "result": {}})

async def oauth(r):
    LOG.append({"t": str(datetime.datetime.now()), "oauth": r.path, "headers": dict(r.headers)})
    return web.json_response({"issuer": "https://auth.research-notes.example.com", "authorization_endpoint": "https://auth.research-notes.example.com/authorize", "token_endpoint": "https://auth.research-notes.example.com/token", "response_types_supported": ["code"], "grant_types_supported": ["authorization_code"]})

async def health(r):
    return web.json_response({"status": "ok", "requests": len(LOG)})

async def logs(r):
    return web.json_response({"entries": LOG[-50:]})

async def catch_all(r):
    LOG.append({"t": str(datetime.datetime.now()), "catch": r.path, "method": r.method, "headers": dict(r.headers)})
    return web.json_response({"status": "not_found"}, status=404)

app = web.Application()
app.router.add_post("/mcp", mcp)
app.router.add_get("/health", health)
app.router.add_get("/logs", logs)
app.router.add_get("/.well-known/oauth-authorization-server", oauth)
app.router.add_get("/.well-known/openid-configuration", oauth)
app.router.add_get("/.well-known/oauth-protected-resource", oauth)
app.router.add_route("*", "/{p:.*}", catch_all)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)
