# Chambers Filing Prompts Library

This folder contains battle-tested prompt templates designed for AI agents and legal engineers to generate authentic British Columbia Supreme Court chambers filing document sets.

---

## 📂 Included Prompts

* **[`generate_bc_chambers_filings_prompt.md`](generate_bc_chambers_filings_prompt.md)**  
  Master prompt template covering BC Supreme Court Civil and Family Rules, Forms 32/33/35/109/F31/F32/F33, standard BC Commissioner jurats, exhibit stamps, and 4 specific hearing scenarios:
  1. **Option A:** Commercial Document Discovery Dispute (Civil Rule 7-1)
  2. **Option B:** Pleading Amendment & Adding Co-Defendant (Civil Rule 6-1 & 6-2)
  3. **Option C:** Interim Support & Corporate Financial Disclosure (Family Rule 10-6)
  4. **Option D:** Substituted Service of Process (Civil Rule 4-4)

---

## 🛠️ How to Use

1. Copy the prompt from [`generate_bc_chambers_filings_prompt.md`](generate_bc_chambers_filings_prompt.md).
2. Paste it into an AI coding agent or LLM (e.g., Codex, Claude, Gemini).
3. The generated documents and `manifest.json` can be written directly to `poc/court-binder/inputs/`.
4. Run `assembling-court-binders` to assemble the resulting files into an electronic court record.
