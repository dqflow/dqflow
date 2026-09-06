# Launch playbook

A repeatable checklist for shipping a dqflow release *and* the content around it,
so distribution gets the same discipline as the code. Maintainer-facing.

## Principles

- **Activation before acquisition.** Do not push a channel until the
  [funnel](adoption-funnel.md) shows people who arrive actually reach a first
  successful validation.
- **Honest claims only.** No invented benchmarks, no "fastest", no inflated
  numbers. Every comparison states limitations too.
- **One story per release.** A release announces one headline change, not a
  changelog dump.

## Reusable assets

Keep these current in the repo so a launch is assembly, not production:

| Asset | Location | Refresh when |
| --- | --- | --- |
| Demo GIF / short video (`infer → validate → diff → gate`) | `docs/assets/` | CLI output format changes |
| Architecture diagram | `docs/assets/` + README "Architecture" | The engine/IR pipeline changes |
| Contract-diff terminal visual | `docs/assets/contract-diff-demo.svg` | `dq diff` output changes |
| Release post template | [release-post-template.md](release-post-template.md) | — |
| Benchmark methodology | `benchmarks/README.md` | Benchmark harness changes |
| Copyable starter | `examples/first-pr-gate/` | CLI flags or workflow shape change |

Benchmark numbers are **only** published with the methodology, the machine spec,
the dataset, and the dqflow + dependency versions next to them. No standalone
"Nx faster" claims.

## Per-release checklist

### Before tagging

- [ ] `CHANGELOG.md` `[Unreleased]` is complete and grouped (Added / Changed /
      Fixed / Removed), each entry links its issue
- [ ] Public API snapshot regenerated if the surface changed
      (`python -m tests.api_surface.collect`)
- [ ] Docs build clean (`mkdocs build --strict`); new pages in `mkdocs.yml` nav
- [ ] README "Features" / "Supported engines" tables still accurate
- [ ] The one headline change has a guide page and, if user-facing, an
      `examples/` entry
- [ ] Migration note written for any break

### Release

- [ ] Follow `RELEASING.md` (version bump, tag, PyPI workflow)
- [ ] GitHub Release notes = the headline story + a link to the changelog
      section, not the raw changelog
- [ ] Post an **Announcements** discussion from the release notes

### Content (within one week of the release)

- [ ] One use-case post: a real problem → the contract → the failing check.
      Publish on the project blog/README-linked location and cross-post
- [ ] Update any comparison page the release affects (e.g. a limitation removed)
- [ ] Update `ROADMAP.md` status for shipped issues

## Monthly cadence

Even with no release, once a month:

| Week | Action |
| --- | --- |
| 1 | Triage sweep: every open issue has a current label + a next step. Close stale |
| 2 | One piece of content (use-case, comparison update, or a `good first issue` write-up) |
| 3 | Roadmap check: is the top of each category still right? Post a [Roadmap discussion](https://github.com/dqflow/dqflow/discussions) note if it moved |
| 4 | Metrics review against the [funnel](adoption-funnel.md); note what moved and why |

## Channels

Ordered by fit. Only use a channel when there is a concrete, honest thing to
show (a release, a real use case) — not to announce the project repeatedly.

1. **GitHub** — Releases, Discussions (Announcements), the `good first issue` label
2. **Python / data-engineering newsletters** — e.g. Data Engineering Weekly,
   Python Weekly, Pycoders — submit release notes / posts
3. **Reddit** — r/dataengineering, r/Python (follow each subreddit's
   self-promotion rules; lead with the problem)
4. **Hacker News** — Show HN for a milestone release only, once
5. **Lobsters** — for a substantive write-up, with the right tags
6. **Orchestrator communities** — Airflow, Dagster, Prefect, dbt Slack/Discord —
   answer real questions, link docs when relevant
7. **LinkedIn / Mastodon / Bluesky** — release + use-case posts

Record every push in the experiment log (part of #60): channel, date, the funnel
stage it targeted, and what actually happened.

## Post-launch review

For any deliberate launch, one week later write three lines in the experiment
log: expected signal, actual signal, what to do differently. A launch with no
review does not count as done.
