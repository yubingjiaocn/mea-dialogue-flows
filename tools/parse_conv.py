#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MEA Conversation EBX-XML -> 有序对话流(中英对照)。
节点模型:
  Conversation: 根, ChildNodes=入口
  ConversationLine: 台词节点, TextReference/String/StringId(hex)=文本, ChildNodes=后续
  ConversationLink: 跳转, LinkedLine 指向某 Line(汇合/循环)
ChildNodes Count>1 = 分支。
"""
import os, sys, re, json, html
import xml.etree.ElementTree as ET

ROOT = "/tmp/conv/conv_out"
OUT  = "/tmp/conv/dialogues"
LOOKUP = "/home/ubuntu/me-andromeda-patch/reverse-engineering/zh_lookup.json"
EN_XML = "/tmp/en.xml"

# ---- 加载中文库（可选；本仓库英文版不含） ----
ZH = {}
if os.path.exists(LOOKUP):
    with open(LOOKUP) as f:
        ZH = json.load(f)

# ---- 加载英文全量(TextId->Text) ----
EN = {}
def load_en():
    if not os.path.exists(EN_XML):
        return
    tid = None
    for ev, el in ET.iterparse(EN_XML, events=("end",)):
        if el.tag == "TextId":
            tid = (el.text or "").strip().upper()
        elif el.tag == "Text":
            if tid:
                EN[tid] = el.text or ""
            tid = None
        if el.tag in ("TextRepresentation",):
            el.clear()
load_en()

def key_from_stringid(sid):
    """0x0002e79e -> 0002E79E"""
    sid = sid.strip()
    if sid.lower().startswith("0x"):
        sid = sid[2:]
    try:
        return format(int(sid, 16), "08X")
    except ValueError:
        return sid.upper().zfill(8)

def lookup(sid):
    k = key_from_stringid(sid)
    if k == "00000000":
        return None, "", ""
    zh = ZH.get(k)
    en = EN.get(k, "")
    return k, en, (zh or "")

def short_ebx(ref):
    """[Ebx] game/vocharacters/unc/dunes/dune_colony_junker [guid] -> dune_colony_junker"""
    if not ref or ref == "nullptr":
        return ""
    m = re.search(r'\[Ebx\]\s+([^\[]+?)\s*\[', ref)
    if m:
        p = m.group(1).strip().rstrip('/')
        return p.split('/')[-1]
    return ref

GUID_RE = re.compile(r'\[(ConversationLine|ConversationLink)\]\s+([0-9a-fA-F-]{36})')

def parse_file(path):
    """返回 (conv_name, primary_speaker, entry_guids, nodes{guid:node})"""
    txt = open(path, encoding="utf-8").read()
    # 包一层 root 让它成为合法 XML(多个顶级元素)
    try:
        root = ET.fromstring("<ROOT>" + txt + "</ROOT>")
    except ET.ParseError:
        # 修复 & 未转义
        fixed = re.sub(r'&(?!(amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)', '&amp;', txt)
        # 已知自由文本标签:转义其内部裸 < >
        def esc_inner(m):
            inner = m.group(2).replace('<','&lt;').replace('>','&gt;')
            return m.group(1) + inner + m.group(3)
        for tagname in ('SchematicStartEvent','SchematicOutputStart','SchematicOutputEnd'):
            fixed = re.sub(r'(<'+tagname+r'>)(.*?)(</'+tagname+r'>)', esc_inner, fixed, flags=re.S)
        # 其余裸 < 后跟非标签字符
        fixed = re.sub(r'<(?![/!?A-Za-z])', '&lt;', fixed)
        try:
            root = ET.fromstring("<ROOT>" + fixed + "</ROOT>")
        except ET.ParseError:
            return None
    conv_name = None; primary = ""; entry = []
    nodes = {}
    for el in root:
        tag = el.tag
        if tag == "Conversation":
            conv_name = (el.findtext("Name") or "").strip()
            primary = short_ebx(el.findtext("PrimarySpeaker") or "")
            cn = el.find("ChildNodes")
            if cn is not None:
                for m in cn.findall("member"):
                    mm = GUID_RE.search(m.text or "")
                    if mm: entry.append(mm.group(2))
        elif tag in ("ConversationLine", "ConversationLink"):
            g = el.get("Guid")
            node = {"guid": g, "type": tag, "children": [], "sid": None,
                    "speaker": "", "listener": "", "linked": None,
                    "conditions": 0, "occurrence": ""}
            cn = el.find("ChildNodes")
            if cn is not None:
                for m in cn.findall("member"):
                    mm = GUID_RE.search(m.text or "")
                    if mm: node["children"].append(mm.group(2))
            if tag == "ConversationLine":
                tr = el.find("TextReference/ConversationStringReference")
                if tr is not None:
                    sid = tr.findtext("String/LocalizedStringReference/StringId")
                    node["sid"] = sid
                    node["speaker"] = short_ebx(tr.findtext("Speaker") or "")
                    node["listener"] = short_ebx(tr.findtext("Listener") or "")
                dc = el.find("DisplayConditions")
                ec = el.find("EnabledConditions")
                n = 0
                if dc is not None: n += int(dc.get("Count","0"))
                if ec is not None: n += int(ec.get("Count","0"))
                node["conditions"] = n
                node["occurrence"] = (el.findtext("Occurrence") or "").replace("ConversationLineOccurrence_","")
            else:  # Link
                ll = GUID_RE.search(el.findtext("LinkedLine") or "")
                if ll: node["linked"] = ll.group(2)
            nodes[g] = node
    return {"name": conv_name, "primary": primary, "entry": entry, "nodes": nodes}

def render(data):
    nodes = data["nodes"]; out = []
    visited = set()

    def line_text(node):
        sid = node["sid"]
        if not sid:
            return None
        k, en, zh = lookup(sid)
        if k is None:
            return None  # 0x0 空引用
        spk = node["speaker"] or ""
        cond = " ⟨cond⟩" if node["conditions"] else ""
        occ = "" if node["occurrence"] in ("Always","") else f" [{node['occurrence']}]"
        en = (en or "").replace("\n"," ⏎ ").strip()
        label = f"{spk}" if spk else "?"
        body = en if en else "[empty]"
        return f"{label}{cond}{occ}: {body}"

    def walk(guid, depth, branch_mark=""):
        # 解析 Link 跳转
        hops = 0
        while guid in nodes and nodes[guid]["type"] == "ConversationLink":
            ln = nodes[guid]["linked"]
            if ln is None: 
                return
            guid = ln
            hops += 1
            if hops > 50: return
        if guid not in nodes:
            return
        node = nodes[guid]
        if guid in visited:
            t = line_text(node)
            ind = "    "*depth
            out.append(f"{ind}{branch_mark}↩ (goto) {t if t else guid[:8]}")
            return
        visited.add(guid)
        t = line_text(node)
        ind = "    "*depth
        # 过滤纯占位空节点(0x0/无文本)
        if t is not None and not t.endswith(": [empty]"):
            out.append(f"{ind}{branch_mark}{t}")
        children = node["children"]
        if len(children) <= 1:
            for c in children:
                walk(c, depth, "")
        else:
            # branch
            out.append(f"{ind}┌─ BRANCH ({len(children)}) ─┐")
            for i, c in enumerate(children, 1):
                out.append(f"{ind}├ option {i}:")
                walk(c, depth+1, "")
            out.append(f"{ind}└─ merge ─┘")

    for e in data["entry"]:
        walk(e, 0, "")
    return "\n".join(out)

def main():
    files = []
    for dp, dn, fn in os.walk(ROOT):
        for f in fn:
            if f.endswith(".xml"):
                files.append(os.path.join(dp, f))
    files.sort()
    os.makedirs(OUT, exist_ok=True)
    stats = {"files":0, "lines":0, "translated":0, "untranslated":0, "empty":0, "parse_err":0}
    for path in files:
        data = parse_file(path)
        stats["files"] += 1
        if data is None:
            stats["parse_err"] += 1
            continue
        body = render(data)
        rel = os.path.relpath(path, ROOT)
        outp = os.path.join(OUT, rel.replace(".xml",".txt"))
        os.makedirs(os.path.dirname(outp), exist_ok=True)
        header = f"# {data['name']}\n# Primary speaker: {data['primary']}\n# Source: {rel}\n{'='*50}\n"
        with open(outp, "w", encoding="utf-8") as f:
            f.write(header + body + "\n")
        # 统计
        for n in data["nodes"].values():
            if n["type"]!="ConversationLine" or not n["sid"]: continue
            k,en,zh = lookup(n["sid"])
            if k is None: stats["empty"]+=1; continue
            stats["lines"]+=1
            if zh: stats["translated"]+=1
            elif en: stats["untranslated"]+=1
            else: stats["empty"]+=1
    print(json.dumps(stats, ensure_ascii=False, indent=2))

if __name__=="__main__":
    main()
