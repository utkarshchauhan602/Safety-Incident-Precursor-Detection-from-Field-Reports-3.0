# Safety Precursor Intelligence

A Streamlit-based educational HSE decision-support prototype for analysing safety reports, identifying potential precursors, and supporting human-reviewed safety conversations.

## Run locally

```bash
python -m venv .venv
```

Activate the environment, then install dependencies:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit (usually `http://localhost:8501`).

## Deploy on Streamlit Community Cloud

1. Create a GitHub repository (suggested name: `safety-precursor-intelligence`).
2. Upload the contents of this folder to the repository root.
3. In Streamlit Community Cloud, create a new app and select that repository.
4. Set **Main file path** to `app.py` and deploy.

`requirements.txt` is included for dependency installation. The bundled 50,000-row HSE conversation corpus is under `spi/data/`.

## Optional API configuration

Copy `.env.example` to `.env` for local use and add your provider key if you choose to enable optional LLM responses. For Streamlit Cloud, add secrets through the app's **Advanced settings / Secrets** interface; never commit `.env` or API keys to GitHub. The app has a local fallback when no provider key is configured.

## Important safety note

This is an educational prototype, not a certified safety system. It does not replace site procedures, emergency services, or a competent HSE professional. Synthetic datasets and demonstration metrics are not evidence of real-world safety performance. Human review is required before acting on any output.
