#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 dialogues/game/conversations 按任务/类型重组成人类可读目录树。"""
import os, shutil, re

SRC = "/tmp/conv/dialogues/game/conversations"
DST = "/tmp/conv/by_mission"

# 顶层分类编号 + 名称。值: (顶层目录名, 二级映射 dict 或 None)
# 二级映射: 内部代号 -> 可读子目录名
TOP = {
  # 注意:MEA 内部代号顺序 != 剧情顺序。下面按实际对话内容核实后归类。
  "crit": ("01_Main_Story_Priority_Ops", {
      "pro_lnd":   "01_Prologue_Planetside_Habitat7",   # 着陆 Habitat 7
      "Pro_Shp":   "02_Prologue_Hyperion_Ship",         # 序章飞船/苏醒
      "intrld":    "03_Nexus_Reunion_and_Archon_Reveal", # 苏醒+执政官登场
      "m4":        "04_A_Trail_of_Hope_Salarian_Ark",    # 萨拉睿方舟救 Raeka,初遇执政官
      "intrld35":  "05_After_Moshae_Resistance",         # 解放 Moshae 之后
      "Crit_Ex":   "06_Hunting_the_Archon_Flagship",     # 登执政官旗舰 Trage 救方舟
      "Intrld25":  "07_Post_Archon_Nexus_Debrief",       # 旗舰后 Nexus 述职
      "intrld45":  "08_Archon_Plot_for_Meridian",        # 执政官/Primus 谋夺 Meridian
      "crit_khet": "09_Kett_Facility_Rescue",            # Kett 设施救援(krogan/salarian)
      "crit_city": "10_Journey_to_Meridian_Khi_Tasira",  # Ghost Storm 潜入
      "crit_vlt":  "11_Remnant_Vault_Meridian",          # 遗物拱顶
      "intrld55":  "12_Meridian_Solution_Leaders",       # Meridian 方案领袖会议
      "Crit_Mer":  "13_Meridian_The_Way_Home_Finale",    # 终章 crit_fin
      "crit_epi":  "14_Epilogue_Home_and_Away",          # 尾声 mer_epi
  }),
  "Loyalty": ("02_Loyalty_Missions", {
      "loy_hmf":      "Cora_Harper_At_Dutys_Edge",
      "Human_male_01":"Liam_Kosta_All_In",
      "Loy_Tur":      "Vetra_Nyx_Means_and_Ends",
      "loy_ang":      "Jaal_Flesh_and_Blood",
      "loy_asa":      "Peebee_Secret_Project",
      "Loy_Kro":      "Drack_A_Future_For_Our_People",
      "Krogan_01":    "Drack_A_Future_For_Our_People",
  }),
  "rel": ("03_Squadmates_and_Relationships", {
      "cora":"Cora_Harper","drack":"Nakmor_Drack","gil":"Gil_Brodie","jaal":"Jaal_Ama_Darav",
      "kallo":"Kallo_Jath","lexi":"Lexi_TPerro","liam":"Liam_Kosta","peebee":"Peebee",
      "suvi":"Suvi_Anwar","vetra":"Vetra_Nyx",
  }),
  "hubs": ("04_Hubs_and_NPCs", {
      "hub_nexus":"Nexus","hub_aya":"Aya","hub_kad":"Kadara","hub_hyp":"Hyperion",
      "hub_mer":"Meridian","hub_tem":"Temple_Sites","tempest":"Tempest",
  }),
  # 探索任务:多个顶层合并到一个分类,按星球分
  "unc_dunes": ("05_Planet_Exploration/Elaaden", None),
  "unc_ice":   ("05_Planet_Exploration/Voeld", None),
  "unc_luna":  ("05_Planet_Exploration/H-047C_Luna", None),
  "unc":       ("05_Planet_Exploration/Eos_and_General", None),
  "bstory": ("06_Backstory_and_Worldbuilding", {
      "ang":"Angara","asa":"Asari","ket":"Kett","kro":"Krogan","sal":"Salarian","tur":"Turian",
      "life":"Daily_Life","remrel":"Remnant_Lore","ryderfam":"Ryder_Family",
  }),
  "Banter":  ("07_Squad_Banter", None),
  "Space":   ("08_Space_and_Galaxy_Map", None),
  "mp":      ("09_Multiplayer", None),
  "global":       ("10_Misc/Global_Generic", None),
  "storyteller":  ("10_Misc/Storyteller", None),
  "playerobjectives": ("10_Misc/Player_Objectives", None),
  "utility":      ("10_Misc/Utility", None),
}

def main():
    if os.path.exists(DST): shutil.rmtree(DST)
    moved = 0; unmapped = []
    for dp, dn, fn in os.walk(SRC):
        for f in fn:
            if not f.endswith(".txt"): continue
            src = os.path.join(dp, f)
            rel = os.path.relpath(src, SRC)
            parts = rel.split(os.sep)
            top = parts[0]
            if top not in TOP:
                # 顶层散文件(如 ice_whales_*.txt)
                unmapped.append(rel)
                topdir = "10_Misc/Other"; subpath = ""
            else:
                topdir, submap = TOP[top]
                if submap and len(parts) > 2:
                    sub = parts[1]
                    subname = submap.get(sub, sub)
                    subpath = subname
                elif submap and len(parts) == 2:
                    subpath = "_root"
                else:
                    # None 映射:保留原二级子路径(去掉顶层代号)
                    subpath = os.sep.join(parts[1:-1])
            outdir = os.path.join(DST, topdir, subpath) if subpath else os.path.join(DST, topdir)
            os.makedirs(outdir, exist_ok=True)
            shutil.copy2(src, os.path.join(outdir, f))
            moved += 1
    print(f"moved {moved} files")
    if unmapped:
        print(f"unmapped top-level loose files ({len(unmapped)}): {unmapped[:10]}")

if __name__ == "__main__":
    main()
