# TODO: Write Rosemary's orientation narratives

These are short narrative descriptions that orient Rosemary to
where she is and what she's doing. Two axes compose:

## Client narratives
What am I doing? Keyed by client name.

Example format (YAML or simple key: value):
- duckpond: "You are in the chat app with Kylee."
- solitude: "You're alone. It's nighttime."
- routine: "You're running a scheduled task."

## Machine narratives
Where am I running? Keyed by hostname.

Example format:
- rosemary-server: "Your home server."

Until this is written, Rosemary gets a generic "You're in {{client}}."
