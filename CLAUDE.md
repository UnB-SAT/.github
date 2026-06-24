# CLAUDE.md: UnB-SAT `.github`

This repository holds the **data and the generator**. It feeds two outputs:

- `profile/README.md`: the organization profile at <https://github.com/UnB-SAT>
  (slim, principal investigator only).
- the **website** at <https://unb-sat.github.io>, whose pages live in the sibling
  repository `unb-sat.github.io`.

## Two-repo layout

Clone both repos side by side; the generator writes across the two:

```
UnB-SAT/
├── .github/             # this repo ("dot-github" locally): data + generator
└── unb-sat.github.io/   # the just-the-docs website
```

## Single source of truth

`data/students.yml` is the only place to edit people and advised work (field docs are
at the top of that file). `scripts/build_profile.py` rewrites the content between
`<!-- AUTOGEN:* -->` markers; each file receives only the markers it declares:

| Marker     | Goes to                | Content                              |
|------------|------------------------|--------------------------------------|
| `ADVISOR`  | `profile/README.md`    | PI card only                         |
| `PEOPLE`   | site `people.md`       | PI + full student grid               |
| `ONGOING`  | site `theses.md`       | current students (in progress)       |
| `THESES`   | site `theses.md`       | completed TCC and M.Sc.              |
| `IC`       | site `research.md`     | Iniciação Científica (PIBIC/PIBITI)  |

The generator finds the site repo at `../unb-sat.github.io` (override with the
`UNB_SAT_SITE_DIR` environment variable; the CI for the site sets it).

**Static pages, NOT generated:** site `index.md`, `publications.md`, `teaching.md`.
Publications are edited by hand in `unb-sat.github.io/publications.md`, not here.

## Update flow

1. Edit `data/students.yml`. For work in progress set `status: ongoing`; IC entries
   set `program: PIBIC` or `PIBITI`. Theme is `sat | planning | moj | ai`.
2. `pip install pyyaml` (once), then `python3 scripts/build_profile.py`.
3. Commit `data/students.yml` and `profile/README.md` here, and push.
4. The website rebuilds itself (see CI), so you normally do not touch the site repo.
   The site files the build also wrote locally are just a preview.

## CI

- `.github/workflows/profile.yml`: runs `build_profile.py --check` on PRs and pushes;
  fails if `profile/README.md` is stale (e.g. someone edited the data via the web UI
  without rebuilding). Fix by running the generator and committing.
- `.github/workflows/dispatch-site.yml`: on a push that changes the data or generator,
  sends a `repository_dispatch` (type `rebuild`) to the site repo. Needs the secret
  `SITE_DISPATCH_TOKEN`; without it the job no-ops and the site still rebuilds daily.

## Conventions (keep these)

- **Language: English** in body text. The lab name stays in Portuguese; thesis titles
  stay in their original language with a one-line English gloss (`en:`).
- **No em dash (`—`) anywhere.** Use commas or parentheses. Check: `grep -rn "—" .`
- **Few emojis.** Aim for a researcher tone.
- The profile shows only the PI; the full team, theses, IC and publications live on
  the website.
- Avatars: a `github` handle renders the real avatar, an empty one renders a
  ui-avatars initials image. GitHub strips inline CSS, so avatars are square.
  Confirm a handle exists: `curl -sI https://github.com/<handle>.png`.

## Data sources (when adding entries)

- TCCs: BDM, `https://bdm.unb.br/browse?type=advisor&value=Ribas%2C+Bruno+C%C3%A9sar`.
  Its TLS chain is incomplete; fetch with `curl -k`.
- M.Sc.: `https://repositorio.unb.br/browse?type=advisor&value=Ribas%2C+Bruno+C%C3%A9sar`.
- Publications: DBLP `https://dblp.org/pid/121/4222`. Google Scholar and ResearchGate
  block scraping. The Lattes XML at `/home/ribas/UnB-SAT/lattes.xml` (ISO-8859-1)
  lists IC/PIBIC advisings and Brazilian-venue papers.

## Verify before committing

```bash
python3 scripts/build_profile.py --check    # generated files in sync
grep -rn "—" profile data scripts README.md   # expect no matches (CLAUDE.md excluded: it documents the character)
```
