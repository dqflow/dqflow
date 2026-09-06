# Release post template

Fill in the blanks. Keep it to one headline change. Delete the guidance in
italics before publishing.

---

## dqflow `X.Y.0` — `<headline in three or four words>`

*One sentence: what is now possible that was not before.*

### The change

*2–4 sentences. The problem, then the new behaviour. Link the guide page.*

```console
$ <the shortest command or code that shows it>
<real output, copied — not paraphrased>
```

### Why it matters

*One short paragraph, from the user's side. Tie it to the*
*`infer → validate → diff → gate` workflow. No superlatives.*

### Also in this release

- `<second-most-important item>` (#NN)
- `<third>` (#NN)

Full list: [CHANGELOG](https://github.com/dqflow/dqflow/blob/main/CHANGELOG.md).

### Honest limitations

*If the headline feature has edges, say so here. Link*
*[How dqflow compares](../comparison/index.md) if relevant.*

### Try it

```bash
pip install --upgrade "dqflow[pandas]"
```

- New? [5-minute quickstart](../getting-started/quickstart.md)
- [First PR gate in ~10 minutes](../getting-started/first-pr-gate.md)
- Feedback: [Discussions](https://github.com/dqflow/dqflow/discussions)

---

**Checklist before posting**

- [ ] Output blocks are copied from a real run, not hand-written
- [ ] Every issue/PR number links
- [ ] Limitations section is not empty unless the feature genuinely has none
- [ ] Cross-posted per the [launch playbook](launch-playbook.md#channels)
- [ ] Logged in the experiment log (channel, date, target funnel stage)
