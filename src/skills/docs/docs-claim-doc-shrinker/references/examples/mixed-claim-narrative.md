# On Why We Built This

When the team first sat down together at the old whiteboard, we did not have a name for what we were building. We had a feeling — a shared frustration with tools that summarised our work without preserving the parts that mattered. The wall was covered in sticky notes by lunch.

## Principles

We believe lossy compression is the wrong default for documents whose value is their claims. We believe the human, not the model, should decide what survives a rewrite. We believe verification must follow generation, not precede it.

It took us months to put those three sentences together. There were arguments, mostly civil. There was at least one weekend where nobody talked to each other. And then one Monday it was just obvious; we wrote them down and moved on.

## What this means in practice

The shrinker enforces a two-phase workflow. Audit decides what to keep. Compress rewrites only against that kept set. Every kept claim is independently judged for entailment after the rewrite, and the source is only modified if the coverage check passes.

We could have shipped a one-shot rewrite tool in a fortnight. The team voted against it. Sometimes the right answer takes longer.
