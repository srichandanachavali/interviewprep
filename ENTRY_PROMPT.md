You are starting work on **InterviewPrep AI**, a project that uses a
structured context file system. Before writing a single line of code,
do the following setup steps in order:

## STEP 1 — Copy context files into the repo

Copy these three files into the root of `interviewprep-main/`:

- `CLAUDE.md` (already provided — your persistent brain)
- `PLANNING.md` (already provided — full specs)
- `TASKS.md` (already provided — your task board)

If they are not already there, create them now with the exact content
provided to you. These files are the source of truth for this entire
project. Never contradict them.

## STEP 2 — Read CLAUDE.md fully

Read `CLAUDE.md` now. It tells you:

- What the app is and who it's for
- The locked tech stack
- The coding rules you must always follow
- The context loading rules (which files to load for which task types)
- The canonical weakness tags you must never add to

Do not proceed until you have read CLAUDE.md.

## STEP 3 — Read TASKS.md

Read `TASKS.md`. Find the first uncompleted task (marked `[ ]`).
That is where you start. Work top to bottom. Do not skip phases.

## STEP 4 — Load context correctly before each task

Before building any task, check the context loading table in CLAUDE.md:

- New feature / new page → load CLAUDE.md + PLANNING.md §relevant section
- Bug fix / small edit → load CLAUDE.md + the relevant file only
- Database change → load CLAUDE.md + PLANNING.md §Schema
- Full build from scratch → load CLAUDE.md + PLANNING.md (full)

Load only what you need. Do not load PLANNING.md for a bug fix.
This keeps context lean and your work fast.

## STEP 5 — Build, test, update TASKS.md

For each task:

1. Read the task from TASKS.md
2. Load the right context files (per Step 4)
3. Build the thing
4. Run the test command listed in the task
5. Mark the task `[x]` in TASKS.md with a one-line note
6. Move to the next task

If you hit an error you cannot resolve, mark the task `[~]`,
write why under BLOCKED in TASKS.md, and skip to the next task.

## STEP 6 — When to update CLAUDE.md

Update the `## LAST UPDATED` line in CLAUDE.md only when:

- You make a structural change to the repo (new directory, renamed file)
- You add a new canonical weakness tag
- You change a core tool in the tech stack

Do not edit CLAUDE.md for normal feature work.

---

## WHAT YOU ARE BUILDING (summary — full spec in PLANNING.md)

InterviewPrep AI is a full-stack AI interview prep tool with 5 USPs:

1. JD → 20 personalised questions in <10s
2. Voice mock interview + per-answer STAR scoring (0-100)
3. Cross-session Weakness Pattern Tracker
4. Crowdsourced Company Question Bank
5. 60-Second Rapid Fire Mode

Stack: Next.js 14 + FastAPI + Supabase + Anthropic Claude API + Vercel/Railway.
Constraint: free tiers only. No paid services except Claude API.
Target users: Indian job seekers, freshers, career switchers.

All AI calls use `claude-sonnet-4-20250514`.
All AI prompts return JSON only (enforced by system prompt).
All voice features use `lang: 'en-IN'` for Indian English.

---

## GO

Start with STEP 1. Then STEP 2. Then open TASKS.md and begin P1-1.
Do not ask for permission between tasks. Build, test, mark done, next.
