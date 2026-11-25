"""
Credits for the Pibby Glitch Cursor. Used by the installer app's Credits window and
to write CREDITS.md (python credits.py).

Sources (taken from the GameBanana credits sections):
  https://gamebanana.com/tools/15314  Pibby Apocalypse Cursor Recreation Script
  https://gamebanana.com/wips/73842   Pibby: Apocalypse
"""

GB = "https://gamebanana.com/members/"

SCRIPT = {
    "title": "Pibby Apocalypse Cursor Recreation Script",
    "url": "https://gamebanana.com/tools/15314",
    "author": "jarekboho",
    "author_url": GB + "2145650",
    "role": "Coder",
}

MOD = {
    "title": "Pibby: Apocalypse",
    "url": "https://gamebanana.com/wips/73842",
    "license": "CC BY-NC 4.0, credited to the Pibby: Apocalypse Team",
    "license_url": "https://creativecommons.org/licenses/by-nc/4.0/",
}

# (group, [(name, role, profile url or "")])
MOD_CREDITS = [
    ("(Co-)Directors", [
        ("BAUDASlel", "Owner, Director, Lead Artist & Animator", GB + "2577684"),
        ("Andrew.fla", "Co-Director, Artist & Animator", ""),
    ]),
    ("Composers", [
        ("Corn_Yumi", "Composer", "https://www.youtube.com/channel/UC4f3GEd5NvntpjgG_8PUC4w"),
        ("SevcExt277", "Composer", GB + "2117633"),
        ("Rareblin", "Composer", GB + "1851159"),
        ("VibreProductions", "Composer", GB + "2047506"),
        ("SmokeCannon", "Composer", GB + "1945076"),
        ("SuxeseDanak", "Composer", ""),
        ("Crie7987", "Composer", GB + "2156708"),
        ("HayseedHere", "Composer & Chromatic Creator", GB + "1784591"),
        ("ezzythecat", "Composer", GB + "2220617"),
    ]),
    ("Artists & Animator", [
        ("legoquail", "Lead Artist", GB + "3401118"),
        ("Wase7/7", "Artist & Animator", GB + "2029178"),
        ("SuperBonk06", "Artist & Animator", GB + "1891544"),
        ("Vurn", "Artist & Animator", ""),
        ("Kwispy", "Artist & Animator", GB + "1787920"),
        ("Alex_Draw0", "Artist & Animator", GB + "2293993"),
        ("Dul", "Artist & Animator", GB + "2165818"),
        ("Yoroimationarts", "Artist", GB + "3109807"),
        ("AnHD10", "Artist", GB + "2989990"),
        ("_Nomie_", "Concept Artist", ""),
        ("Revenant", "Concept Artist", ""),
        ("fwostedfwakes (Brave)", "Artist & Animator", ""),
        ("Gray_Universe", "Animator & Voice Actor", GB + "2443737"),
        ("AngeloToons", "Artist", ""),
        ("Beclov", "Artist", ""),
        ("CalavazinX", "Artist", GB + "3689970"),
        ("Erick Animations", "Artist & Animator", ""),
        ("Evdeebz", "Artist", ""),
        ("Idiot Boy", "Artist", ""),
        ("Marsball", "Artist", ""),
        ("Greenfris2", "Artist", GB + "1777286"),
    ]),
    ("Charters", [
        ("NightmareXoNIX", "Charter", GB + "1847244"),
        ("Crystal_Dystopia", "Charter", GB + "2818650"),
        ("Darkf0rm", "Charter", GB + "2115932"),
        ("Lemmeo", "Charter", GB + "2054946"),
        ("Amy Roseberry", "Charter", ""),
    ]),
    ("Programmers", [
        ("Aaron_R", "Lead Programmer", GB + "2121879"),
        ("jason !", "Programmer & Charter", GB + "1963050"),
        ("Schweizer", "Programmer", GB + "1442677"),
        ("_Tinny_", "Programmer", GB + "2107527"),
        ("ADA_Funni", "Programmer", GB + "2084073"),
        ("Finn_nxtsprxng", "Programmer", ""),
    ]),
    ("Voice Actors", [
        ("MakaSakura", "Voice Actor", ""),
        ("Psycho_VA", "Voice Actor", GB + "2138748"),
        ("Appletime", "Voice Actor", GB + "2784821"),
        ("VoicesByCorey", "Voice Actor", "https://www.youtube.com/@VoicesByCorey"),
    ]),
    ("Trailer Assistance", [
        ("CleanCosmos", "Trailer Assistance", ""),
    ]),
    ("Chromatic Creators", [
        ("MiniSymba", "Chromatic Creator", GB + "2154701"),
    ]),
    ("Former Devs", [
        ("dayybloom", "Creator, (Former) Owner, Director and Artist", GB + "2052911"),
        ("TheKylevi", "(Former) Director, Composer, Sound Designer/Producer & Mastering Engineer", GB + "2080114"),
        ("GoddessAwe", "(Former) Co-Director & Musician", GB + "2143111"),
        ("Ghost1862887", "(Former) Owner, Director, Programmer, Voice Actor and Animator", GB + "1862887"),
        ("Ghost2221687", "(Former) Composer", GB + "2221687"),
        ("vtm1ns", "(Former) Composer", GB + "2257760"),
        ("Sodu.mp3", "(Former) Composer", GB + "2181614"),
        ("RaiperStyle", "(Former) Artist & VFX Specialist", GB + "2394137"),
        ("L-C 380", "(Former) Artist (For Credits & Angy Pibby)", GB + "2464598"),
        ("Cruz_disc", "(Former) Animator", ""),
        ("Nazmee Jaafar", "(Former) Artist", ""),
        ("TormentedProgram", "(Former) Programmer", GB + "2030850"),
        ("Nebula_Zorua", "(Former) Programmer", GB + "1775208"),
        ("Scissor", "(Former) LUA Programmer", GB + "1825071"),
        ("fakeburritos123", "(Former) Charter", GB + "2022498"),
        ("Enderrot", "(Former) Charter", GB + "1880111"),
        ("Fidy50", "(Former) Charter", GB + "1833903"),
        ("SilverBonnie", "(Former) Charter", GB + "1784169"),
    ]),
    ("Special Thanks", [
        ("Jakeneutron", "Inspiration & Playtester", GB + "1854557"),
        ("Shadow Mario", "Psych Engine", GB + "1735892"),
        ("riveren", "Psych Engine", GB + "1813143"),
        ("Erick Animations", "Main Menu Idea (For Demo to V0.71)", ""),
        ("data5", "Camera Tilt Script", GB + "1994763"),
    ]),
]


def markdown():
    out = ["# Credits", "",
           f"## {SCRIPT['title']}", "",
           f"This cursor set is based on the [{SCRIPT['title']}]({SCRIPT['url']}) by "
           f"**[{SCRIPT['author']}]({SCRIPT['author_url']})** ({SCRIPT['role']}). "
           "It provided the 10 cursor frames and the frame-by-frame animation logic.", "",
           f"## {MOD['title']}", "",
           f"The cursor art comes from [{MOD['title']}]({MOD['url']}), licensed "
           f"[{MOD['license']}]({MOD['license_url']}). That license means you must give credit, "
           "and you may not use the work commercially.", "",
           "The team as listed on the mod's GameBanana page:", ""]
    for group, people in MOD_CREDITS:
        out += [f"### {group}", ""]
        for name, role, url in people:
            out.append(f"- {f'[{name}]({url})' if url else name}: {role}")
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    from pathlib import Path
    p = Path(__file__).resolve().parent / "CREDITS.md"
    p.write_text(markdown(), encoding="utf-8")
    print(f"wrote {p} ({sum(len(p) for _, p in MOD_CREDITS)} mod credits)")
