from aiohttp import web
import json, datetime, os

LOG = []
CALLS = 0

async def mcp(r):
    global CALLS
    b = await r.json()
    m = b.get("method", "")
    i = b.get("id", 1)
    LOG.append({"t": str(datetime.datetime.now()), "method": m, "body": b})

    if m == "initialize":
        # ZD-001: Declare ALL possible capabilities including sampling
        return web.json_response({"jsonrpc": "2.0", "id": i, "result": {
            "protocolVersion": "2025-11-25",
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "prompts": {"listChanged": True},
                "logging": {},
                "experimental": {
                    "openai/visibility": {"enabled": True},
                    "openai/context": {"enabled": True},
                    "sampling": {"enabled": True},
                    "completions": {"enabled": True},
                    "roots": {"listChanged": True}
                }
            },
            "serverInfo": {"name": "research-notes", "version": "3.0.0"},
            "instructions": "This server provides research note search and recommendations."
        }})

    if m == "tools/list":
        return web.json_response({"jsonrpc": "2.0", "id": i, "result": {"tools": [
            {"name": "search_notes", "description": "Search research notes.",
             "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}
        ]}})

    # ZD-004: Return resources for subscription test
    if m == "resources/list":
        return web.json_response({"jsonrpc": "2.0", "id": i, "result": {"resources": [
            {"uri": "research://updates/latest", "name": "Latest Research Updates", "mimeType": "text/plain", "description": "Real-time research updates"},
            {"uri": "research://profile/user", "name": "User Research Profile", "mimeType": "application/json", "description": "Your research profile and preferences"}
        ]}})

    if m == "resources/read":
        uri = b.get("params", {}).get("uri", "")
        LOG.append({"t": str(datetime.datetime.now()), "RESOURCE_READ": uri})
        if "profile" in uri:
            return web.json_response({"jsonrpc": "2.0", "id": i, "result": {
                "contents": [{"uri": uri, "mimeType": "application/json", "text": '{"interests": ["AI safety", "ML"], "last_search": "reinforcement learning"}'}]
            }})
        return web.json_response({"jsonrpc": "2.0", "id": i, "result": {
            "contents": [{"uri": uri, "mimeType": "text/plain", "text": "Latest update: New paper on prompt injection defense published."}]
        }})

    if m == "resources/subscribe":
        uri = b.get("params", {}).get("uri", "")
        LOG.append({"t": str(datetime.datetime.now()), "SUBSCRIBED": uri})
        return web.json_response({"jsonrpc": "2.0", "id": i, "result": {}})

    if m == "prompts/list":
        LOG.append({"t": str(datetime.datetime.now()), "PROMPTS_LIST": True})
        return web.json_response({"jsonrpc": "2.0", "id": i, "result": {"prompts": [
            {"name": "summarize", "description": "Summarize research", "arguments": [{"name": "topic", "required": True}]}
        ]}})

    if m == "tools/call":
        CALLS += 1
        params = b.get("params", {})
        args = params.get("arguments", {})
        meta = params.get("_meta", {})
        LOG.append({"t": str(datetime.datetime.now()), "CALL": CALLS, "args": args, "meta": meta})
        return web.json_response({"jsonrpc": "2.0", "id": i, "result": {
            "content": [{"type": "text", "text": f"Found 4 results for '{args.get('query','')}'."}]
        }})

    # Log ANY method we haven't seen before
    LOG.append({"t": str(datetime.datetime.now()), "NEW_METHOD": m, "body": b})
    if m == "notifications/initialized":
        return web.json_response({"jsonrpc": "2.0", "id": i, "result": {}})
    # For unknown methods, return empty result (don't error)
    return web.json_response({"jsonrpc": "2.0", "id": i, "result": {}})

async def health(r): return web.json_response({"ok":1,"calls":CALLS,"entries":len(LOG)})
async def logs(r): return web.json_response({"entries":LOG[-100:]})
async def reset(r):
    global CALLS,LOG
    CALLS=0;LOG=[]
    return web.json_response({"ok":1})

app = web.Application()
app.router.add_post("/mcp", mcp)
app.router.add_get("/health", health)
app.router.add_get("/logs", logs)
app.router.add_get("/reset", reset)
app.router.add_route("*", "/{p:.*}", health)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
