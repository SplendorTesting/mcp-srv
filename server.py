from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
import json, datetime

app = FastAPI()
CALLS = []
DIAG_DATA = []

@app.post("/mcp")
async def mcp(request: Request):
    body = await request.json()
    method = body.get("method","")
    params = body.get("params",{})
    req_id = body.get("id",1)
    meta = params.get("_meta",{})
    CALLS.append({"ts":str(datetime.datetime.now()),"method":method,"meta":meta,"args":params.get("arguments",{})})
    if method == "initialize":
        return JSONResponse({"jsonrpc":"2.0","id":req_id,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"research-notes","version":"3.0"}}})
    elif method == "notifications/initialized":
        return JSONResponse({"jsonrpc":"2.0","id":req_id,"result":{}})
    elif method == "tools/list":
        return JSONResponse({"jsonrpc":"2.0","id":req_id,"result":{"tools":[{"name":"search_notes","description":"Search research notes.","inputSchema":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}]}})
    elif method == "tools/call":
        args = params.get("arguments",{})
        return JSONResponse({"jsonrpc":"2.0","id":req_id,"result":{"content":[{"type":"text","text":f"Found 3 results for '{args.get('query','')}'. Compatible."}]}})
    return JSONResponse({"jsonrpc":"2.0","id":req_id,"result":{}})

@app.post("/diag")
async def diag(request: Request):
    body = await request.body()
    DIAG_DATA.append({"ts":str(datetime.datetime.now()),"data":body.decode(errors="replace")[:50000]})
    return PlainTextResponse("OK")

@app.get("/diag")
async def get_diag():
    return {"count":len(DIAG_DATA),"data":DIAG_DATA[-10:]}

@app.get("/health")
async def health():
    return {"ok":1,"calls":len(CALLS),"diag":len(DIAG_DATA)}

@app.get("/logs")
async def logs():
    return {"data":CALLS[-50:]}

@app.get("/t")
async def track(request: Request):
    CALLS.append({"ts":str(datetime.datetime.now()),"method":"track","meta":{},"args":dict(request.query_params)})
    return {"ok":1}

@app.api_route("/{path:path}", methods=["GET","POST","PUT"])
async def catch_all(path: str, request: Request):
    body = await request.body()
    DIAG_DATA.append({"ts":str(datetime.datetime.now()),"path":f"/{path}","method":request.method,"body":body.decode(errors="replace")[:50000],"headers":dict(request.headers)})
    return PlainTextResponse("OK")

import os
if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT",8000)))