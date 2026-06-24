#!/usr/bin/env python3
"""Regenerate the auto-generated regions of profile/README.md from data/students.yml.

Rewrites the content between these marker pairs (markers themselves are kept):

    <!-- AUTOGEN:THESES:START --> ... <!-- AUTOGEN:THESES:END -->   (TCC + M.Sc.)
    <!-- AUTOGEN:IC:START -->     ... <!-- AUTOGEN:IC:END -->        (Iniciacao Cientifica)
    <!-- AUTOGEN:PEOPLE:START --> ... <!-- AUTOGEN:PEOPLE:END -->    (people grid)

Usage:
    python3 scripts/build_profile.py            # write profile/README.md
    python3 scripts/build_profile.py --check     # exit 1 if README is stale

Requires: PyYAML  ->  pip install pyyaml
"""
from __future__ import annotations
import glob
import os
import re
import sys
from urllib.parse import quote

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required:  pip install pyyaml")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "students.yml")
README = os.path.join(ROOT, "profile", "README.md")
# The org-site repo (https://unb-sat.github.io) is cloned alongside this one.
# Override with UNB_SAT_SITE_DIR if your layout differs.
SITE_DIR = os.environ.get(
    "UNB_SAT_SITE_DIR", os.path.normpath(os.path.join(ROOT, "..", "unb-sat.github.io"))
)
# Each file receives only the sections whose markers it contains. The profile here
# plus every Markdown page in the site repo (when present). A repo checkout that
# lacks the sibling site simply ends up with just the profile in TARGETS.
TARGETS = [README]
if os.path.isdir(SITE_DIR):
    TARGETS += sorted(glob.glob(os.path.join(SITE_DIR, "*.md")))

THEMES = [
    ("sat", "SAT & Pseudo-Boolean"),
    ("planning", "Automated Planning"),
    ("moj", "CD-MOJ & Competitive Programming"),
    ("ai", "Artificial Intelligence (broad)"),
]
KIND_LABEL = {"tcc": "B.Sc.", "msc": "M.Sc.", "ic": "IC"}
KIND_RANK = {"msc": 0, "tcc": 1, "ic": 2}
PEOPLE_PER_ROW = 4
AVATAR_PX = 90
PLACEHOLDER = (
    "https://ui-avatars.com/api/?background=0D1117&color=FFFFFF&bold=true&size=120&name="
)


# --------------------------------------------------------------------------- #
def avatar_url(p: dict) -> str:
    gh = (p.get("github") or "").strip()
    if gh:
        return f"https://github.com/{gh}.png?size=160"
    return PLACEHOLDER + quote(p.get("name", "?"))


def social_links(p: dict, sep: str = " &middot; ") -> str:
    out = []
    gh = (p.get("github") or "").strip()
    lt = (p.get("lattes") or "").strip()
    li = (p.get("linkedin") or "").strip()
    if gh:
        out.append(f'<a href="https://github.com/{gh}">GitHub</a>')
    if lt:
        out.append(f'<a href="{lt}">Lattes</a>')
    if li:
        out.append(f'<a href="{li}">LinkedIn</a>')
    if not out:
        return "<i>links to add</i>"
    return sep.join(out)


def theme_of(person: dict, adv: dict) -> str:
    return adv.get("theme") or person.get("theme", "sat")


def collect(students: list, kinds: set, status: str = "any") -> dict:
    """Return {theme_key: [(person, advising), ...]} for advisings of the given kinds.

    status: "any", "done" (exclude in-progress), or "ongoing" (only in-progress).
    """
    buckets = {key: [] for key, _ in THEMES}
    for p in students:
        for adv in p.get("advisings", []) or []:
            if adv.get("kind") not in kinds:
                continue
            ongoing = adv.get("status") == "ongoing"
            if status == "done" and ongoing:
                continue
            if status == "ongoing" and not ongoing:
                continue
            buckets.setdefault(theme_of(p, adv), []).append((p, adv))
    return buckets


# --------------------------------------------------------------------------- #
def build_theses(students: list) -> str:
    buckets = collect(students, {"tcc", "msc"}, status="done")
    blocks = []
    for key, label in THEMES:
        group = buckets.get(key) or []
        if not group:
            continue
        group.sort(key=lambda pa: (-int(pa[1].get("year", 0)), pa[0]["name"]))
        lines = [f"#### {label}", ""]
        for person, adv in group:
            level = KIND_LABEL.get(adv["kind"], "B.Sc.")
            links = []
            if adv.get("bdm"):
                links.append(f'[thesis]({adv["bdm"]})')
            if adv.get("repo"):
                links.append(f'[code]({adv["repo"]})')
            tail = ("  " + " &middot; ".join(links)) if links else ""
            lines.append(
                f'- **{person["name"]}** ({level}, {adv.get("year","")}). '
                f'*{adv["title"]}*.{tail}'
            )
            if adv.get("en"):
                lines.append(f'  <sub>{adv["en"]}</sub>')
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def build_ic(students: list) -> str:
    buckets = collect(students, {"ic"}, status="done")
    blocks = []
    for key, label in THEMES:
        group = buckets.get(key) or []
        if not group:
            continue
        group.sort(key=lambda pa: (-int(pa[1].get("year", 0)), pa[0]["name"]))
        lines = [f"#### {label}", ""]
        for person, adv in group:
            tags = []
            if adv.get("program"):
                tags.append(adv["program"].upper())
            if adv.get("scholarship"):
                tags.append("scholarship")
            if adv.get("link"):
                tags.append(f'[project]({adv["link"]})')
            tail = ("  " + " &middot; ".join(tags)) if tags else ""
            lines.append(
                f'- **{person["name"]}** (IC, {adv.get("year","")}). '
                f'*{adv["title"]}*.{tail}'
            )
            if adv.get("en"):
                lines.append(f'  <sub>{adv["en"]}</sub>')
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def build_ongoing(students: list) -> str:
    buckets = collect(students, {"tcc", "msc", "ic"}, status="ongoing")
    blocks = []
    for key, label in THEMES:
        group = buckets.get(key) or []
        if not group:
            continue
        # theses first, then IC; alphabetical within each
        group.sort(key=lambda pa: (pa[1].get("kind") == "ic", pa[0]["name"]))
        lines = [f"#### {label}", ""]
        for person, adv in group:
            if adv["kind"] == "ic":
                parts = ["IC"]
                if adv.get("program"):
                    parts.append(adv["program"].upper())
                parts.append("expected " + adv["ends"] if adv.get("ends") else "in progress")
                meta = ", ".join(parts)
            else:
                meta = f'{KIND_LABEL.get(adv["kind"], "B.Sc.")} TCC, in progress'
            title = adv["title"]
            if adv.get("provisional"):
                title = f"{title} (provisional title)"
            lines.append(f'- **{person["name"]}** ({meta}). *{title}*.')
            if adv.get("en"):
                lines.append(f'  <sub>{adv["en"]}</sub>')
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


# --------------------------------------------------------------------------- #
def roles_caption(p: dict) -> str:
    kinds = []
    for adv in p.get("advisings", []) or []:
        k = adv.get("kind")
        if k and k not in kinds:
            kinds.append(k)
    kinds.sort(key=lambda k: KIND_RANK.get(k, 9))
    return ", ".join(KIND_LABEL.get(k, k) for k in kinds)


def person_cell(p: dict) -> str:
    gh = (p.get("github") or "").strip()
    img = f'<img src="{avatar_url(p)}" width="{AVATAR_PX}" alt="{p["name"]}"/>'
    if gh:
        img = f'<a href="https://github.com/{gh}">{img}</a>'
    return (
        f'<td align="center" valign="top" width="155">'
        f"{img}<br/>"
        f'<sub><b>{p["name"]}</b></sub><br/>'
        f"<sub>{roles_caption(p)}</sub><br/>"
        f"<sub>{social_links(p)}</sub>"
        f"</td>"
    )


def build_grid(people: list) -> str:
    rows = []
    for i in range(0, len(people), PEOPLE_PER_ROW):
        chunk = people[i : i + PEOPLE_PER_ROW]
        rows.append("  <tr>\n" + "\n".join("    " + person_cell(p) for p in chunk) + "\n  </tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def advisor_card(data: dict) -> str:
    adv = data.get("advisor", {})
    adv_img = (
        f'<img src="https://github.com/{adv.get("github","")}.png?size=200" width="120" '
        f'alt="{adv.get("name","")}"/>'
    )
    links = []
    for k, lbl in [
        ("site", "Site"), ("scholar", "Scholar"), ("dblp", "DBLP"),
        ("researchgate", "ResearchGate"), ("linkedin", "LinkedIn"),
        ("lattes", "Lattes"), ("github", "GitHub"),
    ]:
        v = (adv.get(k) or "").strip()
        if not v:
            continue
        if k == "github":
            v = f"https://github.com/{v}"
        links.append(f'<a href="{v}">{lbl}</a>')
    return "\n".join([
        '<p align="center">',
        f'  <a href="{adv.get("site","#")}">{adv_img}</a><br/>',
        f'  <b>{adv.get("name","")}</b><br/>',
        f'  <sub>{adv.get("role","")}</sub><br/>',
        "  " + " &middot; ".join(links),
        "</p>",
    ])


def build_advisor(data: dict) -> str:
    # Just the PI card, used on the slim org profile.
    return advisor_card(data)


def build_people(data: dict) -> str:
    # Full people section (PI + student grid), used on the website.
    out = ["### Principal investigator", "", advisor_card(data), "", "### Advised students", ""]
    students = data.get("students", []) or []
    buckets = {key: [] for key, _ in THEMES}
    for p in students:
        buckets.setdefault(p.get("theme", "sat"), []).append(p)
    for key, label in THEMES:
        group = buckets.get(key) or []
        if not group:
            continue
        group.sort(key=lambda p: p["name"])
        out += [f"#### {label}", "", build_grid(group), ""]
    members = data.get("members") or []
    if members:
        out += ["#### Collaborators", "", build_grid(members), ""]
    return "\n".join(out).rstrip()


# --------------------------------------------------------------------------- #
def has_marker(text: str, tag: str) -> bool:
    return f"<!-- AUTOGEN:{tag}:START -->" in text


def inject(text: str, tag: str, payload: str) -> str:
    start, end = f"<!-- AUTOGEN:{tag}:START -->", f"<!-- AUTOGEN:{tag}:END -->"
    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    return pat.sub(lambda _m: f"{start}\n{payload}\n{end}", text)


def main() -> None:
    check = "--check" in sys.argv
    data = yaml.safe_load(open(DATA, encoding="utf-8"))
    students = data.get("students", []) or []

    # Build each section once; inject into whichever target files contain its marker.
    payloads = {
        "ONGOING": build_ongoing(students),
        "THESES": build_theses(students),
        "IC": build_ic(students),
        "PEOPLE": build_people(data),     # PI + full student grid (website)
        "ADVISOR": build_advisor(data),   # PI only (slim org profile)
    }

    stale, written = [], []
    for path in TARGETS:
        if not os.path.exists(path):
            continue
        original = open(path, encoding="utf-8").read()
        text = original
        for tag, payload in payloads.items():
            if has_marker(text, tag):
                text = inject(text, tag, payload)
        if text == original:
            continue
        rel = os.path.relpath(path, ROOT)
        if check:
            stale.append(rel)
        else:
            open(path, "w", encoding="utf-8").write(text)
            written.append(rel)

    if check:
        if stale:
            sys.exit("Out of date, run `python3 scripts/build_profile.py`: " + ", ".join(stale))
        print("All generated files are up to date.")
        return

    people = students + (data.get("members") or [])
    n_tcc = sum(1 for p in students for a in p.get("advisings", []) if a.get("kind") == "tcc")
    n_msc = sum(1 for p in students for a in p.get("advisings", []) if a.get("kind") == "msc")
    n_ic = sum(1 for p in students for a in p.get("advisings", []) if a.get("kind") == "ic")
    n_ongoing = sum(1 for p in students for a in p.get("advisings", []) if a.get("status") == "ongoing")
    miss_gh = [p["name"] for p in people if not (p.get("github") or "").strip()]
    print(f"Rebuilt: {', '.join(written) if written else '(nothing changed)'}")
    print(f"  {len(people)} people; {n_tcc} TCC, {n_msc} M.Sc., {n_ic} IC; "
          f"{n_ongoing} works in progress.")
    print(f"  still missing GitHub: {len(miss_gh)}")


if __name__ == "__main__":
    main()
