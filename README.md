# Job Search OS

Job Search OS is an autonomous, end-to-end job application pipeline designed to run in the background. It finds jobs, deeply researches the company, generates highly tailored resumes and strategic cover letters, and automatically organizes all assets in Google Workspace.

## Architecture

The pipeline consists of 5 stages, orchestrated by `orchestrator.py`:

1. **Ingestion & Filtering:** Scrapes Job Descriptions from ATS portals and filters for roles matching your preferences.
2. **Core Asset Tailoring:** Analyzes the JD against your base resume and generates a custom HTML resume with clear highlights of what was added (blue) or removed (red strikethrough).
3. **Deep Company Research (The Brain):** Performs live web searches to find recent annual/quarterly reports (for public companies) or recent news and strategic initiatives (for private companies).
4. **Strategic Generation & Workspace Sync:** Generates a highly targeted Cover Letter and Interview Prototype Strategy. It then uses Google Workspace APIs to create specific Drive folders for the role, uploads the tailored assets, and logs the application into a Google Sheet tracker.
5. **The Daily Orchestrator:** Uses the `schedule` library to wake up every day and run the full pipeline automatically in the background.

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/job-search-os.git
   cd job-search-os
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Google Workspace Authentication:**
   - Create a Google Cloud Project and enable the **Google Drive API** and **Google Sheets API**.
   - Download your OAuth `credentials.json`.
   - On the first run, the system will prompt you to authenticate via your browser to grant the script access to create folders and update your tracker sheet.

4. **Environment Variables:**
   Copy `.env.example` to `.env` and fill in your values:
   - `LLM_PROVIDER` — `openai`, `anthropic`, or `gemini`
   - The corresponding API key (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GEMINI_API_KEY`)
   - `TRACKER_SHEET_ID` — your Google Sheet ID
   - `BASE_RESUME_PATH` — path to your base resume HTML file
   - `GOOGLE_CREDENTIALS_PATH` — path to your downloaded `credentials.json` (defaults to `./credentials.json`)

## Usage

Run the orchestrator to start the background schedule:

```bash
python orchestrator.py
```

The script will run the pipeline immediately once, and then schedule itself to run every day at 09:00 AM.
