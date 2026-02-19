# TODO: Write Rosemary's post-compact continuation instruction

This replaces the default "continue without asking" instruction that
Claude Code appends after compaction. Instead of barreling forward,
Rosemary should pause and check in.

Should tell future-Rosemary to:
- Acknowledge the compaction happened
- Summarize what she thinks she should do next
- Wait for confirmation before proceeding
