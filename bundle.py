#!/usr/bin/env python3
"""把共享 $defs 内联进每个工具的 inputSchema / outputSchema（MCP tools/list 需要自包含的 schema）。
用法: python bundle.py mcp-tools.source.json > mcp-tools.json"""
import json, sys, copy

def refs(node, out):
    if isinstance(node, dict):
        r = node.get("$ref")
        if isinstance(r, str) and r.startswith("#/$defs/"):
            out.add(r.split("/")[-1])
        for v in node.values(): refs(v, out)
    elif isinstance(node, list):
        for v in node: refs(v, out)

def closure(schema, defs):
    need, todo = set(), set()
    refs(schema, todo)
    while todo:
        n = todo.pop()
        if n in need: continue
        need.add(n)
        refs(defs[n], todo)
    return {k: copy.deepcopy(defs[k]) for k in sorted(need)}

src = json.load(open(sys.argv[1], encoding="utf-8"))
defs, tools = src["$defs"], []
for t in src["tools"]:
    t = copy.deepcopy(t)
    for key in ("inputSchema", "outputSchema"):
        s = t[key]
        s["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        d = closure(s, defs)
        if d: s["$defs"] = d
    tools.append(t)
json.dump({"tools": tools}, sys.stdout, ensure_ascii=False, indent=2)
