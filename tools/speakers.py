# -*- coding: utf-8 -*-
"""说话者代号 -> 可读名字。
分层:① 固定特殊 ② 泛指队友/船员 ③ 已知命名 NPC ④ 智能美化 fallback。
"""
import re

# ① 固定特殊
EXACT = {
    "Hero": "Ryder",
    "SAM": "SAM",
    "Narration": "Narration",
    "?": "?",
    "global_dad": "Alec Ryder (Dad)",
    "global_sibling_male": "Scott Ryder (Sibling)",
    "global_sibling_female": "Sara Ryder (Sibling)",
    "global_main_villain": "The Archon",
    "global_main_villain_lieutenant": "Archon's Lieutenant",
    "global_kalinda": "Kalinda",
    "global_jaal_mom": "Jaal's Mother (Sahuna)",
}

# ② 泛指队友(按种族) / 船员岗位 — 用描述性名字
GENERIC = {
    "global_squad_male_human": "Squadmate (Human ♂)",
    "global_squad_female_human": "Squadmate (Human ♀)",
    "global_squad_asari": "Squadmate (Asari / Peebee)",
    "global_squad_angara": "Squadmate (Angara / Jaal)",
    "global_squad_krogan": "Squadmate (Krogan / Drack)",
    "global_squad_turian": "Squadmate (Turian / Vetra)",
    "global_crew_co-pilot": "Kallo (Co-pilot)",
    "global_crew_science_officer": "Suvi (Science Officer)",
    "global_crew_tech_officer": "Gil (Tech Officer)",
    "global_crew_doctor_multi": "Lexi (Doctor)",
}

# ③ 已知命名 NPC(高频)
NAMED = {
    "kad_charlatan": "The Charlatan",
    "kad_queen": "Krogan Overlord (Nakmor Morda)",
    "aya_curator_avela_multi": "Avela Kjar (Curator)",
    "global_nexus_colonial_director_multi": "Foster Addison (Colonial Director)",
    "global_nexus_PI_director": "Jarun Tann (Director)",
    "global_nexus_militia_leader": "Tiran Kandros (Militia Leader)",
    "angararesleader_multi": "Evfra de Tershaav (Resistance Leader)",
    "global_angaran_elder_multi": "Angaran Elder",
    "hub_aya_gov_leader_multi": "Paaran Shie (Aya Governor)",
    "global_humanark_captain_multi": "Captain Dunn",
    "global_humanark_asari_dr": "Dr. Lexi / Asari Doctor",
    "global_salarian_pathfinder_multi": "Salarian Pathfinder (Hayjer)",
    "global_turian_pathfinder_multi": "Turian Pathfinder (Avitus Rix)",
    "global_arkcon_superintendent": "Ark Superintendent",
    "nex_vetra_sister_multi": "Sid (Vetra's Sister)",
}

# 区域前缀(美化时剥离)
REGION_PREFIX = re.compile(
    r'^(nex|nexus|kad|aya|dune|olw|ice|stm|crit|loy|loyalty|mp|bio|mer|hyp|pro|rem|tem|oasis|agm|rydfam|ust[l]?)_',
    re.I)
# 常见噪声后缀
SUFFIX = re.compile(r'(_multi|_amb(_\d+)?|_\d+|_0\d|_[abcdi])+$', re.I)
SPECIES = {
    "human":"Human","asari":"Asari","angara":"Angara","angaran":"Angara",
    "krogan":"Krogan","turian":"Turian","salarian":"Salarian",
    "genhuman":"Human","genangara":"Angara","gensalarian":"Salarian","genturian":"Turian",
}

def prettify(code):
    if code in EXACT: return EXACT[code]
    if code in GENERIC: return GENERIC[code]
    if code in NAMED: return NAMED[code]
    # 敌人/泛型
    if code.startswith("global_enemy_"):
        return "Enemy"
    if code.startswith("global_gen"):
        m=re.match(r'global_gen([a-z]+)_([fm])',code)
        if m:
            sp=SPECIES.get(m.group(1),m.group(1).title())
            g="♀" if m.group(2)=="f" else "♂"
            return f"{sp} Civilian ({g})"
    # 美化 fallback:剥区域前缀 + 噪声后缀 + 下划线转空格 + 标题化
    s=code
    s=REGION_PREFIX.sub('',s)
    s=SUFFIX.sub('',s)
    # 剩余内部噪声词
    s=re.sub(r'\b(rp|amb|gen|ang|hmm|agf|agm|tum|salm|asa|abt)\b','',s)
    s=s.replace('_',' ')
    s=re.sub(r'\s+',' ',s).strip()
    if not s: s=code
    # 已含大写(原本就是名字如 Pro_Shp_xxx)保持,否则 title
    s=' '.join(w if w.isupper() or w[:1].isupper() else w.capitalize() for w in s.split())
    return s
