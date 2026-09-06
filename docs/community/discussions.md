# GitHub Discussions setup

[Discussions](https://github.com/dqflow/dqflow/discussions) is where open-ended
conversation happens. Issues stay for specific, actionable bugs and changes.

## Categories

| Category | Format | Purpose |
| --- | --- | --- |
| **Announcements** | Announcement | Releases and project news. Maintainers post; anyone comments |
| **Q&A** | Question / Answer | "How do I…?" — the **help** channel. Answers can be marked accepted |
| **Roadmap** | Open | Feedback on [ROADMAP.md](https://github.com/dqflow/dqflow/blob/main/ROADMAP.md) items — priorities, gaps, "we need X before Y" |
| **RFC** | Open | Design proposals for non-trivial changes, before an issue or PR |
| **Show and tell** | Open | What people built with dqflow |
| **General** | Open | Everything else |

`Polls` and `Ideas` from the default set are not used — `Ideas` is covered by
**RFC** (proposals) and the feature-request issue form (concrete asks).

### Creating `Roadmap` and `RFC`

GitHub has no API for discussion categories — a maintainer creates them once in
**Settings → General → Features → Discussions → Set up categories**:

- **Roadmap** — format *Open*, description
  *"Feedback on the project roadmap: priorities, missing pieces, sequencing."*
- **RFC** — format *Open*, description
  *"Request for comments: propose a design before an issue or PR."*

The discussion forms in `.github/DISCUSSION_TEMPLATE/` (`rfc.yml`,
`roadmap.yml`) activate automatically once the matching category slug exists.

## Seed threads

Post these once the categories exist, so the space is not empty on arrival.

### Q&A — "Ask anything about getting dqflow running"

> New to dqflow? Ask here — installing, writing your first contract, wiring it
> into a pipeline or CI, choosing pandas vs. Polars, reading a validation
> report. No question is too small.
>
> Before posting, the [5-minute quickstart](https://dqflow.readthedocs.io/en/latest/getting-started/quickstart/)
> and [first PR gate tutorial](https://dqflow.readthedocs.io/en/latest/getting-started/first-pr-gate/)
> cover the common paths. If something there did not work, tell us which step and
> what you saw.

### Show and tell — "What did you build with a contract?"

> Share a contract you put into production, a CI gate that caught something real,
> a pattern you worked out, or an integration with your orchestrator. Screenshots
> of a failing check that saved you are very welcome.

### Roadmap — "What should dqflow prioritise next?"

> The [roadmap](https://github.com/dqflow/dqflow/blob/main/ROADMAP.md) is
> organised into eight categories with priorities and dependencies. If you use
> dqflow (or want to and can't yet), tell us:
>
> - Which single missing capability blocks you?
> - Where is the priority order wrong for your use case?
> - What would you take *off* the roadmap?
>
> Concrete "we can't adopt until X" is the most useful.

### RFC — "How this category works"

> Open an RFC before a non-trivial change — a new engine, a contract-schema
> addition, a CLI behaviour change, severity levels. Use the RFC form: problem,
> proposal, alternatives, compatibility impact. An RFC that reaches rough
> consensus becomes a tracked issue.
>
> Small, obvious changes skip this — open an issue or PR directly.

## Posting the seeds

A maintainer can post them from the CLI once the categories exist:

```bash
# list category IDs
gh api graphql -f query='
  { repository(owner:"dqflow", name:"dqflow") {
      discussionCategories(first:20){ nodes { id name } } } }'

# create one discussion (repeat per seed)
gh api graphql -f query='
  mutation($repo:ID!,$cat:ID!,$title:String!,$body:String!){
    createDiscussion(input:{repositoryId:$repo,categoryId:$cat,title:$title,body:$body}){
      discussion{ url } } }' \
  -f repo="$(gh api repos/dqflow/dqflow --jq .node_id)" \
  -f cat="<category-id>" -f title="<title>" -f body="<body>"
```
