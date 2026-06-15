# Mass Effect: Andromeda — Dialogue Flows

> **2369 conversations** extracted from the game's `Conversation` resources, reconstructed into readable, ordered dialogue flows with branching structure.
> For story reference, line lookup, and localization work.

## What this is

MEA's in-game `Conversation` resources (dialogue trees) parsed into **human-readable ordered dialogue flows**:

- **Ordered** — lines follow the actual conversation-node traversal order (not the flat string table)
- **Branching** — player choices / conditional branches shown as an indented tree, with merge points
- **Speakers** — each line is tagged with its speaking character, mapped to readable names (e.g. `Ryder`, `SAM`, `Squadmate (Krogan / Drack)`, `The Charlatan`) instead of raw internal codenames
- **Text IDs** — each line is prefixed with its 8-digit hex TextId (the game's localized-string key), for cross-referencing
- **English text** — original English from the game's localized strings

## Scale

| Item | Count |
|------|-------|
| Conversation files | 2369 |
| Total lines | ~70,800 |
| Empty placeholders (not shown in game) | ~14,000 (filtered from output) |

## How to find what you want

1. **By mission** → see [`MISSIONS.md`](MISSIONS.md): full list of 215 missions (Priority Ops / Allies & Relationships / Heleus Assignments / Additional Tasks) with story order and location.
2. **By codename** → see [`CODENAMES.md`](CODENAMES.md): internal resource codename ↔ human-readable region/mission-type map.
3. **Full index** → see [`conversations/INDEX.md`](conversations/INDEX.md): all 2369 conversations with a first-line preview.
4. **Browse** → go into [`conversations/`](conversations/), organized by mission / type (see layout below).

## Directory layout

Organized by mission / type (numbered to roughly follow story order):

```
conversations/
├── 01_Main_Story_Priority_Ops/      Critical path, sub-folders 01→14 in story order
│                                   (Prologue → Eos → Interludes → Archon → Meridian → Epilogue)
├── 02_Loyalty_Missions/             Per-squadmate loyalty missions
├── 03_Squadmates_and_Relationships/ Relationship dialogue per character
├── 04_Hubs_and_NPCs/                Hub NPCs (Nexus/Aya/Kadara/Hyperion/Meridian/Tempest...)
├── 05_Planet_Exploration/           Heleus tasks by planet (Elaaden/Voeld/Luna/Eos...)
├── 06_Backstory_and_Worldbuilding/  Lore by species (Angara/Kett/Krogan...) + Ryder family
├── 07_Squad_Banter/                 Squad banter
├── 08_Space_and_Galaxy_Map/         Galaxy-map / system dialogue
├── 09_Multiplayer/                  Multiplayer announcer / mission lines
└── 10_Misc/                         Generic / storyteller / utility
```

Every file's header keeps its original internal resource path (`# Source: game/conversations/...`), so the codename map in [`CODENAMES.md`](CODENAMES.md) still applies.

Main-story mission grouping is verified against the game's own level resources: each `levels/crit/*` level resource directly references both its conversations and its journal entry (`Journals/0_PriorityOps/M*`), giving a hard conversation→mission mapping (e.g. the `m4` conversation set belongs to level `crit_khet` = `M4_KettFlagship` = *Hunting the Archon*). Cross-mission interlude/bridge conversations triggered in hubs are grouped under `Interludes/`.

## Reading format

```
# game/conversations/crit/pro_lnd/...   ← conversation resource name
# Primary speaker: Hero
==================================================
[0002D512] SAM: We've reached the navpoint.        ← [TextId] speaker: line
┌─ BRANCH (3) ─┐                                    ← player choice / conditional branch
├ option 1:
    [00013660] Hero ⟨cond⟩: Nice and easy.          ← ⟨cond⟩ = has display conditions
├ option 2:
    [0002307B] Hero: Get ready to fire.
└─ merge ─┘
```

**Markers**:
- `[XXXXXXXX]` — 8-digit hex TextId (localized-string key; matches ParaTranz keys and the game's string table)
- `⟨cond⟩` — line has display/enable conditions (DisplayConditions/EnabledConditions)
- `[OncePerGame]` etc. — occurrence restriction
- `↩ (goto)` — link node (ConversationLink): conversation merge/loop
- `⏎` — in-line line break

## Source & tooling

- **Dialogue structure**: exported from MEA game resources via [Frosty Editor](https://github.com/CadeEvs/FrostyToolsuite) (EBX → XML), then parsed with [`tools/parse_conv.py`](tools/parse_conv.py).
- **Mission data**: [game-maps.com](https://game-maps.com/MEA/) / [Mass Effect Wiki](https://masseffect.fandom.com/).

## Regenerating

```bash
# 1. Frosty Editor: export all EBX as XML
# 2. Filter files whose root tag is <Conversation into conv_out/ (preserve subpaths)
# 3. Run the parser (needs en.xml = full English string dump)
CONV_ROOT=./conv_out EN_XML=./en.xml python3 tools/parse_conv.py
```

The parser also supports an optional `ZH_LOOKUP` JSON for bilingual output; this repository ships **English only**.

## Disclaimer

Non-commercial fan reference, for story reference and localization collaboration only. Mass Effect: Andromeda and all of its text are © BioWare / Electronic Arts.
