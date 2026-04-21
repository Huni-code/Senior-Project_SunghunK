# Demo Video Narration Script
*Mapping the U.S. Digital Economy — Sunghun Kim*

---

Hi, my name is Sunghun, and this is a short intro video for my senior project,
Mapping the U.S. Digital Economy.

This is Dohun. He's struggling hard in the stock market.
He doesn't know anything about the tech industry, but he wants some insight into which sectors to bet on.

This is the main question: "Where should my dollar go?"

Well — you found the right person for that.

For my senior project, I originally wanted to map Michigan's tech industry,
but I ran into data limitations — and most major tech companies sit outside Michigan anyway.
So I expanded the scope to the whole United States.

I built a dashboard that maps this across three key factors:
what companies are **Learning**,
what companies are **Inventing**,
and what companies are **Investing** in.

Here's where the data came from.

I started by scraping builtin.com, a public directory of tech companies, which gave me 7,600 raw entries that I deduplicated down to 4,000 unique companies.

From there, I built several parallel pipelines to enrich that data.

First, I sent all 4,000 companies to the Claude Haiku API
with a structured prompt that classified each one into sixteen sectors and five revenue models.

Second, I matched companies to their SEC CIK identifiers
and pulled revenue, R&D expense, and operating cash flow from SEC EDGAR's API.
After cleanup, I narrowed it down to 481 public companies,
each with full annual financials from 2015 to 2024.

I also have two other datasets —
the Stack Overflow Developer Survey, and employment and wage data from the BLS.
Honestly, I'm still figuring out how to weave them into the storyline alongside the SEC financials.
But hey — I need to show my professors I did *something* this semester.

So, what did I actually find?
Let's take a look.

---

*Thanks to Dohun for the video edit.*
*He's open to work — hire him!*
