================================================================================
                    27TechAI - SETUP & CONFIGURATION GUIDE
              Scripts & Automation Hub | Built by Lhousin Elhamidy
================================================================================

TABLE OF CONTENTS:
1. Project Overview
2. Prerequisites
3. Initial Setup
4. Managing Secrets & API Keys
5. GitHub Configuration
6. OpenRouter API Setup
7. Running the Dashboard
8. Running the Frontend
9. Security Best Practices
10. Troubleshooting

================================================================================
1. PROJECT OVERVIEW
================================================================================

27TechAI is a script and automation tools platform consisting of:
- Frontend (index.html): A beautiful web interface to browse scripts
- Dashboard (dashboard/): Python admin panel to manage scripts
- Data Storage (data.json): Script information stored in JSON
- Encrypted Secrets (secrets.enc): Secure storage for API keys and tokens

================================================================================
2. PREREQUISITES
================================================================================

Required Software:
- Python 3.8 or higher
- Git (for version control)
- A GitHub account
- OpenRouter account (for Claude AI integration)

================================================================================
3. INITIAL SETUP
================================================================================

Step 1: Install Python Dependencies
------------------------------------
Open terminal/command prompt and navigate to the dashboard folder:

    cd dashboard
    pip install -r requirements.txt

This will install:
- requests (for API calls)
- cryptography (for encrypting secrets)

Step 2: Set Up GitHub Repository
----------------------------------
1. Create a new GitHub repository (or use existing one)
2. Upload data.json to the repository
3. Make sure the file is in the root directory
4. Note your:
   - GitHub username
   - Repository name

================================================================================
4. MANAGING SECRETS & API KEYS
================================================================================

⚠️ CRITICAL: Never share or commit your secrets to GitHub!

The project uses encrypted storage (secrets.enc) to protect sensitive data.

Step 1: Generate Encryption Key
---------------------------------
Run the key generator:

    cd dashboard
    python generate_key.py

This will output a unique encryption key like:
    b'YourUniqueKeyHere=='

🔴 IMPORTANT: Save this key securely! It cannot be recovered if lost.

Step 2: Configure Your Secrets
-------------------------------
1. Open encrypt_secrets.py in a text editor
2. Replace KEY with your generated key:
   
   KEY = b'YourGeneratedKeyFromStep1=='

3. Update the secrets dictionary with your actual credentials:

   secrets = {
       "GITHUB_USERNAME": "your_actual_github_username",
       "GITHUB_REPO": "your_actual_repo_name",
       "GITHUB_TOKEN": "ghp_your_actual_token",
       "OPENROUTER_API_KEY": "sk-or-v1-your_actual_key"
   }

Step 3: Encrypt the Secrets
-----------------------------
Run the encryption script:

    python encrypt_secrets.py

This creates secrets.enc file (encrypted, safe to keep locally)

🔴 NEVER upload secrets.enc to GitHub!

Step 4: Update Dashboard Key
------------------------------
Open dashboard.py and replace the KEY variable with your encryption key:

    KEY = b'YourGeneratedKeyFromStep1=='

================================================================================
5. GITHUB CONFIGURATION
================================================================================

Creating a GitHub Personal Access Token:
-----------------------------------------
1. Go to GitHub.com → Settings → Developer Settings → Personal Access Tokens
2. Click "Generate new token (classic)"
3. Select these permissions:
   ✅ repo (Full control of private repositories)
   ✅ workflow (Update GitHub Action workflows)
4. Generate and copy the token (starts with ghp_)
5. Add this token to encrypt_secrets.py as GITHUB_TOKEN

Repository Structure Required:
-------------------------------
Your GitHub repo should contain:
your-repo/
├── data.json          (required - script data)
├── index.html         (optional - frontend)
└── README.md          (optional)

Update index.html:
-------------------
In index.html, line 81, replace with your GitHub info:

    const GITHUB_RAW_URL = 'https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/data.json';

================================================================================
6. OPENROUTER API SETUP
================================================================================

OpenRouter provides access to Claude AI and other models.

Getting Your API Key:
----------------------
1. Go to https://openrouter.ai/
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with sk-or-v1-)
6. Add this to encrypt_secrets.py as OPENROUTER_API_KEY

Usage in Dashboard:
--------------------
The Claude AI generator uses:
- Model: anthropic/claude-3-haiku
- Purpose: Generate script titles and descriptions
- Cost: Very low (fractions of cents per request)

================================================================================
7. RUNNING THE DASHBOARD
================================================================================

Starting the Admin Panel:
--------------------------
1. Navigate to the dashboard folder:

    cd dashboard

2. Run the dashboard:

    python dashboard.py

3. The GUI will open with:
   - Left panel: List of all scripts
   - Right panel: Add new scripts
   - AI Generator: Create content with Claude

Dashboard Features:
--------------------
✅ Refresh: Load latest data from GitHub
✅ Add Script: Create new script cards
✅ Delete Script: Remove existing scripts
✅ AI Generator: Auto-generate titles/descriptions
✅ Auto-sync: Changes save directly to GitHub

================================================================================
8. RUNNING THE FRONTEND
================================================================================

Option 1: Direct Browser Open
------------------------------
Simply double-click index.html to open in browser

Option 2: Local Server (Recommended)
-------------------------------------
For better functionality, run a local server:

Using Python:
    python -m http.server 8000

Then open: http://localhost:8000

Using Node.js (if available):
    npx serve

Frontend Features:
-------------------
✅ Beautiful RTL Arabic/English interface
✅ Search functionality
✅ Responsive design
✅ Live data from GitHub
✅ Card-based script display

================================================================================
9. SECURITY BEST PRACTICES
================================================================================

🔐 DO:
------
✅ Use encryption for all secrets
✅ Keep secrets.enc file local only
✅ Use .gitignore to exclude sensitive files
✅ Regularly rotate API tokens
✅ Use strong, unique passwords
✅ Enable 2FA on GitHub account

🚫 DON'T:
---------
❌ Never commit secrets.enc to GitHub
❌ Never share encryption keys
❌ Never hardcode API keys in source code
❌ Never push dashboard.py with real KEY to GitHub
❌ Never store keys in plain text files

.gitignore Configuration:
--------------------------
Make sure your .gitignore includes:

    secrets.enc
    *.key
    *password*
    *secret*
    .env
    dashboard/__pycache__/
    *.pyc

================================================================================
10. TROUBLESHOOTING
================================================================================

Problem: "secrets.enc not found"
Solution: Run encrypt_secrets.py first to create the file

Problem: "Failed to load data from GitHub"
Solution: 
- Check GITHUB_USERNAME and GITHUB_REPO are correct
- Verify data.json exists in your repository
- Check internet connection

Problem: "GitHub API error 401"
Solution:
- GITHUB_TOKEN is expired or invalid
- Generate a new token from GitHub settings
- Update encrypt_secrets.py and re-run encryption

Problem: "Claude AI generation failed"
Solution:
- Verify OPENROUTER_API_KEY is valid
- Check API key has sufficient credits
- Ensure internet connection is stable

Problem: "Encryption/Decryption errors"
Solution:
- KEY in dashboard.py must match the one used to encrypt
- If key is lost, you must re-generate and re-encrypt all secrets
- Never lose your encryption key!

Problem: "Frontend shows no scripts"
Solution:
- Verify GITHUB_RAW_URL in index.html is correct
- Check data.json has valid JSON structure
- Open browser console (F12) to see error messages

================================================================================
QUICK START CHECKLIST
================================================================================

[ ] 1. Install Python dependencies (pip install -r requirements.txt)
[ ] 2. Create GitHub repository and upload data.json
[ ] 3. Generate encryption key (python generate_key.py)
[ ] 4. Get GitHub Personal Access Token
[ ] 5. Get OpenRouter API Key
[ ] 6. Update encrypt_secrets.py with all credentials
[ ] 7. Run encryption (python encrypt_secrets.py)
[ ] 8. Update KEY in dashboard.py
[ ] 9. Update GITHUB_RAW_URL in index.html
[ ] 10. Run dashboard (python dashboard.py)
[ ] 11. Open index.html in browser
[ ] 12. Test adding a new script

================================================================================
PROJECT STRUCTURE
================================================================================

QODER/
├── index.html              → Frontend website
├── data.json               → Script data (synced to GitHub)
├── .gitignore              → Git ignore rules
├── README.txt              → This file
└── dashboard/
    ├── dashboard.py        → Admin panel GUI
    ├── encrypt_secrets.py  → Secret encryption script
    ├── generate_key.py     → Key generator
    ├── requirements.txt    → Python dependencies
    └── secrets.enc         → Encrypted secrets (DO NOT COMMIT!)

================================================================================
SUPPORT & CREDITS
================================================================================

Created by: Lhousin Elhamidy
Project: 27TechAI - Scripts & Automation Hub
Year: 2026

For issues or questions, check the code comments or review this guide.

================================================================================
⚠️ REMEMBER: SECURITY IS YOUR RESPONSIBILITY! ⚠️

Never share, commit, or expose your:
- GitHub tokens
- OpenRouter API keys  
- Encryption keys
- secrets.enc file

================================================================================
END OF DOCUMENTATION
================================================================================