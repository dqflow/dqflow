# Adoption funnel

This page defines *what adoption means* for dqflow and the stages a project moves
through. It is the qualitative model; the **measurement layer** — baselines,
targets, and an automated public dashboard — is
[issue #60](https://github.com/dqflow/dqflow/issues/60) and is not shipped yet.

!!! warning "No runtime telemetry"
    dqflow the package collects nothing. It makes no network calls during
    validation and has no analytics. Every metric below comes from **public,
    aggregate sources** (PyPI download stats, GitHub API, docs-host analytics) —
    never from users' pipelines.

## The stages

```text
discover ─▶ read the docs ─▶ install ─▶ first successful validation ─▶ CI adoption ─▶ retained project
```

| Stage | What it means | Signal (public / aggregate) |
| --- | --- | --- |
| **Discover** | Someone finds dqflow exists | GitHub stars/forks/traffic, repo topics, referrals, mentions |
| **Read the docs** | They evaluate it | Read the Docs page views, top pages, quickstart vs. comparison split |
| **Install** | They try it | PyPI downloads (reach proxy — includes CI and mirrors, not unique users) |
| **First successful validation** | It worked for them once | Proxy: quickstart/tutorial completion signals, example-repo forks, "it works" discussion posts |
| **CI adoption** | It runs on every pull request | Proxy: public repos with a dqflow workflow, `good first issue`/question volume shifting to "how do I in CI" |
| **Retained project** | Still using it a quarter later | Proxy: public dependents that keep the dependency across releases, repeat contributors, adopter interviews |

The deeper stages have no clean public counter — they are triangulated from
several weak signals and a small number of direct conversations, not asserted
precisely.

## Why not "users"

PyPI downloads count CI runs, mirrors, and bots, so they are a **reach proxy, not
a user count**. GitHub stars measure interest, not usage. dqflow therefore tracks
a *hierarchy*: active projects/organisations where observable, monthly downloads
as reach, and activation/contribution proxies — rather than a single vanity
number. The [ROADMAP](https://github.com/dqflow/dqflow/blob/main/ROADMAP.md#adoption-thesis)
holds the current stage table and provisional milestones.

## How this connects to product work

Every growth initiative (a comparison page, the GitHub Action, a launch) should
name the funnel stage it targets and the signal expected to move. When #60 lands
it adds:

- a scheduled workflow snapshotting public metrics into a versioned file,
- a docs page with trends and release annotations,
- quarterly numeric targets and an experiment log.

Until then, this page is the shared definition; changes to it go through an
[RFC discussion](https://github.com/dqflow/dqflow/discussions).
