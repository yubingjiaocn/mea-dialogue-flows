#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 dialogues/game/conversations 按任务/类型重组成人类可读目录树。"""
import os, shutil, re

SRC = "/tmp/conv/dialogues/game/conversations"
DST = "/tmp/conv/by_mission"

# 顶层分类编号 + 名称。值: (顶层目录名, 二级映射 dict 或 None)
# 二级映射: 内部代号 -> 可读子目录名
TOP = {
  # 映射依据:游戏 level 资源直接引用 conversation + journal(三方实锈)。
  # level → journal: pro_lnd=M1, crit_vlt=M2, crit_ex=M3, crit_khet=M4, crit_city=M5, crit_mer=M7。
  # conversation 代号顺序 != 剧情顺序(m4 其实是 M4 Hunting the Archon)。
  "crit": ("01_Main_Story_Priority_Ops", {
      "Pro_Shp":   "00_Prologue_Hyperion",               # M0 序章飞船/苏醒
      "pro_lnd":   "01_Planetside_Habitat7",             # M1 (level pro_lnd→M1_Planetside)
      "crit_vlt":  "02_A_Better_Beginning_Eos",          # M2 (level crit_vlt→M2_FirstVault)
      "Crit_Ex":   "03_A_Trail_of_Hope_Save_Moshae",     # M3 (level crit_ex→M3_Exaltation)
      "m4":        "04_Hunting_the_Archon_Salarian_Ark",  # M4 (level crit_khet→M4_KettFlagship)
      "crit_city": "05_The_Journey_to_Meridian",         # M5 (level crit_city→M5_RemnantCity)
      "Crit_Mer":  "06_Meridian_The_Way_Home",           # M7 (level crit_mer→M7_Meridian)
      "crit_epi":  "07_Epilogue_Home_and_Away",          # 尾声 mer_epi
      # 以下是任务间在据点触发的过场/衔接对话(非单一主线任务,按剧情阶段归)
      "intrld":    "Interludes/Nexus_Reunion_Archon_Reveal",
      "Intrld25":  "Interludes/Post_Archon_Nexus_Debrief",
      "intrld35":  "Interludes/After_Moshae_Aya_Kadara",
      "intrld45":  "Interludes/Archon_Plot_for_Meridian",
      "intrld55":  "Interludes/Meridian_Solution_Leaders",
      "crit_khet": "Interludes/Kett_Facility_Rescue_Bridge",
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
