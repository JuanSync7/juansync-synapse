# Why we wrote the shrinker

The first time I tried to compress a long-running identity document, I lost three commitments I had not realized were load-bearing. The rewrite read better — tighter, punchier — but downstream agents that had been quietly relying on those commitments started producing inconsistent behavior. It took a week of debugging to realize that a paraphrase had silently dropped a qualifier, and the qualifier was the entire point of one particular line.

That experience, more than any abstract design principle, is why this skill exists. We could not trust ourselves to compress claim-bearing prose without a structural guarantee. Every time we tried, we lost something we did not know we needed. The shrinker is, at its heart, an apology to a future maintainer for a mistake we keep making in the present. It is also a wager that the cost of the audit phase — slow, deliberate, requiring a human edit — is much less than the cost of the silent loss it prevents.

The story keeps repeating across teams. Someone writes an identity doc. Months pass. The doc grows. They try to tighten it with a single-shot LLM rewrite. They feel good about the result for about two days. Then the cracks appear, and they cannot tell which of the dozen claims they had originally written are still in the file and which have evaporated into a smoother surface.
