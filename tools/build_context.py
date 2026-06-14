#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 Conversation XML 构建 TextId -> 上下文索引。
输出 context_index.json: { "0002E79E": {
    "conv": "game/conversations/...",       # 所属对话资源
    "speaker": "dune_colony_junker",          # 说话者
    "prev": ["0002...","0002..."],            # 前驱节点 TextId(可能多个=多入边)
    "next": ["0002..."],                      # 后继节点 TextId
} }
用对话树的真实 ChildNodes 边构建前后关系。
"""
import os, re, json
import xml.etree.ElementTree as ET

ROOT = os.environ.get("CONV_ROOT", "/tmp/conv/conv_out")
OUT  = os.environ.get("CTX_OUT", "/home/ubuntu/me-andromeda-patch/reverse-engineering/context_index.json")

GUID_RE = re.compile(r'\[(ConversationLine|ConversationLink)\]\s+([0-9a-fA-F-]{36})')

def key_from_sid(sid):
    sid = sid.strip()
    if sid.lower().startswith("0x"): sid = sid[2:]
    try: return format(int(sid,16),"08X")
    except ValueError: return sid.upper().zfill(8)

try:
    import speakers as _spk
    _prettify=_spk.prettify
except Exception:
    _prettify=lambda x:x

def short_ebx(ref):
    if not ref or ref=="nullptr": return ""
    m=re.search(r'\[Ebx\]\s+([^\[]+?)\s*\[',ref)
    code=m.group(1).strip().rstrip('/').split('/')[-1] if m else ref
    return _prettify(code)

def parse_file(path):
    txt=open(path,encoding="utf-8").read()
    try:
        root=ET.fromstring("<ROOT>"+txt+"</ROOT>")
    except ET.ParseError:
        fixed=re.sub(r'&(?!(amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)','&amp;',txt)
        def esc(m): return m.group(1)+m.group(2).replace('<','&lt;').replace('>','&gt;')+m.group(3)
        for tn in ('SchematicStartEvent','SchematicOutputStart','SchematicOutputEnd'):
            fixed=re.sub(r'(<'+tn+r'>)(.*?)(</'+tn+r'>)',esc,fixed,flags=re.S)
        fixed=re.sub(r'<(?![/!?A-Za-z])','&lt;',fixed)
        try: root=ET.fromstring("<ROOT>"+fixed+"</ROOT>")
        except ET.ParseError: return None
    conv=None; nodes={}
    for el in root:
        if el.tag=="Conversation":
            conv=(el.findtext("Name") or "").strip()
        elif el.tag in ("ConversationLine","ConversationLink"):
            g=el.get("Guid")
            node={"type":el.tag,"children":[],"sid":None,"speaker":"","linked":None}
            cn=el.find("ChildNodes")
            if cn is not None:
                for m in cn.findall("member"):
                    mm=GUID_RE.search(m.text or "")
                    if mm: node["children"].append(mm.group(2))
            if el.tag=="ConversationLine":
                tr=el.find("TextReference/ConversationStringReference")
                if tr is not None:
                    node["sid"]=tr.findtext("String/LocalizedStringReference/StringId")
                    node["speaker"]=short_ebx(tr.findtext("Speaker") or "")
            else:
                ll=GUID_RE.search(el.findtext("LinkedLine") or "")
                if ll: node["linked"]=ll.group(2)
            nodes[g]=node
    return conv,nodes

def resolve_link(guid,nodes,depth=0):
    """跟随 Link 到真正的 Line guid。"""
    while guid in nodes and nodes[guid]["type"]=="ConversationLink":
        ln=nodes[guid]["linked"]
        if ln is None or depth>50: return None
        guid=ln; depth+=1
    return guid if guid in nodes else None

def main():
    index={}  # key -> {conv,speaker,prev:set,next:set}
    files=0
    for dp,dn,fn in os.walk(ROOT):
        for f in fn:
            if not f.endswith(".xml"): continue
            r=parse_file(os.path.join(dp,f))
            if not r: continue
            conv,nodes=r; files+=1
            # 建边:每个 Line 节点的 children(解析 Link)的 sid 作为 next
            for g,node in nodes.items():
                if node["type"]!="ConversationLine" or not node["sid"]: continue
                k=key_from_sid(node["sid"])
                if k=="00000000": continue
                rec=index.setdefault(k,{"conv":conv,"speaker":node["speaker"],"prev":set(),"next":set()})
                if not rec.get("conv"): rec["conv"]=conv
                for c in node["children"]:
                    tgt=resolve_link(c,nodes)
                    if tgt and nodes[tgt]["type"]=="ConversationLine" and nodes[tgt]["sid"]:
                        nk=key_from_sid(nodes[tgt]["sid"])
                        if nk!="00000000":
                            rec["next"].add(nk)
                            nrec=index.setdefault(nk,{"conv":conv,"speaker":nodes[tgt]["speaker"],"prev":set(),"next":set()})
                            nrec["prev"].add(k)
    # set -> sorted list
    for k,v in index.items():
        v["prev"]=sorted(v["prev"]); v["next"]=sorted(v["next"])
    json.dump(index,open(OUT,"w"),ensure_ascii=False)
    print(f"files={files} keys={len(index)} -> {OUT}")

if __name__=="__main__":
    main()
