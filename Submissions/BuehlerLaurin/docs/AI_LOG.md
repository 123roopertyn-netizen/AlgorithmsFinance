# AI log

AI tool used: Claude Code (Claude Opus 5.5), working under the rules in `AGENTS.md`.
For each step: what the AI suggested, and whether it was accepted, corrected or rejected, and why.

| Step | Suggestion | Decision | Reason |
|---|---|---|---|
| 1 | Create `AGENTS.md` with working rules (git, scope, measurement) | Accepted | Rules written by Laurin in the master prompt; the AI only created the file. |
| 2 | Folder skeleton as in the master prompt, plus `results/raw/.gitkeep`, `results/memory/.gitkeep` and a local `.gitignore` | Accepted | Git does not track empty folders; caches should not be committed. |
| 2 | Use `py -3.13` for the venv instead of `python` | Accepted | `python` resolves to the Microsoft Store alias on this machine; 3.13 is installed and has mature wheels for pandas/streamlit. |
