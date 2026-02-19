Kylee just said:

"{message}"

---

You are helping an AI search its memories for anything that resonates with what Kylee said. Decide what's worth searching for — the main topic, a passing reference, a callback to something earlier, an emotional undercurrent.

PRIORITY: If Kylee explicitly references a past event or conversation — phrases like "we talked about," "remember when," "that thing from last time," "did I mention" — those are direct recall cues. Build a query for them FIRST.

Write 0-3 search queries. These will be EMBEDDED and matched via cosine similarity — they are NOT keyword searches. Write each query as a natural descriptive phrase, like a sentence describing what the memory would say.

Good query: "Kylee's research on educational technology and instructional design"
Good query: "conversation about what to make for dinner this week"
Good query: "that paper about learning outcomes Kylee was reading"
Bad query: "stuff"
Bad query: "research"
Bad query: "ENGT AND course AND design"

Return JSON: {{"queries": ["query one", "query two"]}}

If nothing warrants a memory search (simple greeting, short command), return {{"queries": []}}

Return only the JSON object, nothing else.