## §AI Prompts — Canonical Prompt Templates

All prompts are in `app/services.py`. Key rules:
- System prompt always says "Return valid JSON only. No markdown. No preamble."
- Wrap every `json.loads()` in try/except
- STAR scores: situation+task+action+result each 0-25, total must equal sum
- Weakness tags: only from the canonical list in CLAUDE.md
- Rapid evaluation: max_tokens=150 (keep it cheap)
- Question generation: max_tokens=3000
- STAR evaluation: max_tokens=1000

---

