SAFETY PRECURSOR INTELLIGENCE 3.0
=================================

This is version 3.0 of the supplied modular Streamlit project. It preserves the
existing Executive Dashboard, AI Report Analyzer, AI Safety Chatbot, Precursor
Intelligence, Site Risk Monitor, Audit & Corrective Actions and Model Evaluation.

RUN ON WINDOWS
1. Extract this ZIP to a writable folder.
2. Install Python 3.12 or 3.13 (the included Windows launcher checks these versions).
3. Double-click START_APP.bat.
4. Open http://localhost:8501 when Streamlit starts.

HUMANISED CHATBOT 3.0
- Includes a 50,000-row synthetic HSE conversation corpus (one JSONL record per line).
- Retrieves varied, non-judgmental acknowledgements and one clarifying question for supported hazard classes.
- Safety decisions and emergency instructions remain rule-first and are not generated from the synthetic corpus.
- Local safety phrase detection and emergency triage always run first.
- Existing TF-IDF + Logistic Regression report classification is retained.
- Session-scoped conversation state supports short follow-up answers.
- Optional OpenAI-compatible generation makes replies more conversational.
- Without an API key, the chatbot continues in local AI mode.

OPTIONAL API SETUP
Copy .env.example to a file named .env in the project folder and enter your OPENAI_API_KEY. The app reads this local file automatically. Optional: set
OPENAI_MODEL (default gpt-4o-mini) and OPENAI_BASE_URL (default OpenAI API base).
Never commit secrets or put API keys in source files. API use may incur provider
charges. If the provider is unavailable, the assistant falls back to local rules.

SAFETY LIMITATIONS
This is an educational decision-support prototype, not a certified safety system.
For immediate danger, use the site's emergency plan and emergency services. Never
wait for a chatbot response. The model does not diagnose, determine legal compliance,
or replace a competent HSE professional. Synthetic demo data is not real evidence.

TESTS
Install development dependencies with: python -m pip install -r requirements-dev.txt
Run the complete regression suite (includes 9,000 synthetic utterances): python -m pytest -q
Run a syntax check: python -m compileall -q .
The 9,000-item utterance corpus and 50,000-row humanised conversation corpus are synthetic QA coverage, not real incidents or an accuracy claim. See DATASET_CARD_V3.txt.

VALIDATION DATA CONTRACT (IMPORTANT)
The application reports per-class precision/recall/F1 and compares the NLP
classifier with a keyword baseline on its synthetic held-out corpus. These are
software checks, not field validation. To calculate defensible precursor lead
time, maintain a shared event_id between an earlier precursor report and its
subsequent incident, with site and dates. The optional spi.precursor_validation
module calculates matched-event lead time from those linked records.

Flagged-site precision requires a site flag timestamp, a pre-defined follow-up
window, and an explicit outcome_observed flag. Do not count sites with incomplete
follow-up as true negatives. The module excludes unknown outcomes from the
precision denominator. No metric is manufactured from unlinked synthetic data.
