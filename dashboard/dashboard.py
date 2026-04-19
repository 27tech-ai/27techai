import json
import requests
import base64
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from cryptography.fernet import Fernet
import os
import re

# ========== Load Secrets ==========
# Replace with your actual encryption key
KEY = b'QmCdSageTLb3vtbFmVbz6BjAvzKd7x1oTwjL3Ko-3SA='

def load_secrets():
    """Load and decrypt secrets from secrets.enc"""
    try:
        cipher = Fernet(KEY)
        enc_file = os.path.join(os.path.dirname(__file__), "secrets.enc")
        
        with open(enc_file, "rb") as f:
            encrypted = f.read()
        
        decrypted = cipher.decrypt(encrypted)
        return json.loads(decrypted.decode())
    except FileNotFoundError:
        messagebox.showerror("Error", "secrets.enc not found. Run encrypt_secrets.py first.")
        return None
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load secrets: {e}")
        return None

# Load secrets on startup
secrets = load_secrets()
if not secrets:
    exit()

GITHUB_USERNAME = secrets["GITHUB_USERNAME"]
GITHUB_REPO = secrets["GITHUB_REPO"]
GITHUB_TOKEN = secrets["GITHUB_TOKEN"]
OPENROUTER_API_KEY = secrets.get("OPENROUTER_API_KEY", "")
OPENAI_API_KEY = secrets.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = secrets.get("ANTHROPIC_API_KEY", "")
GOOGLE_AI_API_KEY = secrets.get("GOOGLE_AI_API_KEY", "")
HUGGINGFACE_API_KEY = secrets.get("HUGGINGFACE_API_KEY", "")
TELEGRAM_BOT_TOKEN = secrets.get("TELEGRAM_BOT_TOKEN", "")
DISCORD_WEBHOOK_URL = secrets.get("DISCORD_WEBHOOK_URL", "")
SITE_URL = secrets.get("SITE_URL", "")

# GitHub API endpoints
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/data.json"
DATA_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/data.json"

# ========== GitHub Functions ==========
def get_file_sha():
    """Get the SHA of data.json for update tracking"""
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        response = requests.get(GITHUB_API_URL, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()['sha']
        else:
            messagebox.showerror("GitHub Error", f"Failed to get file SHA: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Connection Error", f"Network error: {e}")
        return None

def load_data():
    """Load data from GitHub"""
    try:
        response = requests.get(DATA_RAW_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"cards": []}
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Connection Error", f"Failed to load data: {e}")
        return {"cards": []}

def save_data(data, sha):
    """Save data to GitHub via API"""
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        content = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode()).decode()
        
        payload = {
            "message": "Update data from 27TechAI Dashboard",
            "content": content,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha
        
        response = requests.put(GITHUB_API_URL, headers=headers, json=payload, timeout=15)
        
        if response.status_code in [200, 201]:
            return True
        else:
            messagebox.showerror("GitHub Error", f"Save failed: {response.status_code}\n{response.text}")
            return False
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Connection Error", f"Network error: {e}")
        return False

# ========== UI Functions ==========
def refresh_list():
    """Refresh the script list"""
    global current_data, current_sha
    current_data = load_data()
    current_sha = get_file_sha()
    
    listbox.delete(0, tk.END)
    for i, card in enumerate(current_data.get('cards', [])):
        listbox.insert(tk.END, f"{i+1}. {card.get('title', 'Untitled')}")
    
    status_label.config(text=f"📦 Loaded {len(current_data.get('cards', []))} scripts")

def add_card():
    """Add a new script card"""
    title = entry_title.get().strip()
    desc = entry_desc.get().strip()
    img = entry_img.get().strip()
    link = entry_link.get().strip()
    
    if not title or not desc:
        messagebox.showwarning("Warning", "Title and Description are required")
        return
    
    new_card = {
        "title": title,
        "desc": desc,
        "img": img if img else f"https://picsum.photos/id/{len(current_data.get('cards', []))}/400/200",
        "link": link if link else "#"
    }
    
    current_data['cards'].append(new_card)
    
    if save_data(current_data, current_sha):
        messagebox.showinfo("Success", "✅ Script added successfully")
        refresh_list()
        clear_entries()
    else:
        messagebox.showerror("Error", "❌ Failed to save to GitHub")

def delete_card():
    """Delete a selected script card"""
    selected = listbox.curselection()
    if not selected:
        messagebox.showwarning("Warning", "Select a script first")
        return
    
    index = selected[0]
    card_title = current_data['cards'][index]['title']
    
    if messagebox.askyesno("Confirm", f"Delete '{card_title}'?"):
        current_data['cards'].pop(index)
        if save_data(current_data, current_sha):
            messagebox.showinfo("Success", "✅ Script deleted")
            refresh_list()
        else:
            messagebox.showerror("Error", "❌ Failed to delete")

def clear_entries():
    """Clear all input fields"""
    entry_title.delete(0, tk.END)
    entry_desc.delete(0, tk.END)
    entry_img.delete(0, tk.END)
    entry_link.delete(0, tk.END)

def generate_with_claude():
    """Generate content using Claude AI via OpenRouter"""
    prompt = text_prompt.get("1.0", tk.END).strip()
    
    if not prompt:
        messagebox.showwarning("Warning", "Enter a prompt first")
        return
    
    btn_gen.config(text="⏳ Generating...", state="disabled")
    root.update()
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "anthropic/claude-3-haiku",
                "messages": [
                    {"role": "user", "content": f"Generate a script tool description. {prompt}. Give me: TITLE: (catchy title in 3 languages Arabic/English/French) then DESC: (short description in 3 languages)"}
                ],
                "max_tokens": 300
            },
            timeout=30
        )
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # Extract title and description
        title_match = re.search(r'TITLE:\s*(.+?)(?=DESC:|$)', content, re.IGNORECASE)
        desc_match = re.search(r'DESC:\s*(.+?)$', content, re.IGNORECASE | re.DOTALL)
        
        if title_match:
            entry_title.delete(0, tk.END)
            entry_title.insert(0, title_match.group(1).strip()[:60])
        if desc_match:
            entry_desc.delete(0, tk.END)
            entry_desc.insert(0, desc_match.group(1).strip()[:100])
        
        messagebox.showinfo("Success", "✨ Generated! Review the fields above")
        
    except requests.exceptions.Timeout:
        messagebox.showerror("Error", "Request timed out. Try again.")
    except Exception as e:
        messagebox.showerror("Error", f"Generation failed: {str(e)}")
    finally:
        btn_gen.config(text="🤖 Generate with Claude", state="normal")

def generate_with_openai():
    """Generate content using OpenAI GPT"""
    prompt = text_prompt.get("1.0", tk.END).strip()
    
    if not prompt:
        messagebox.showwarning("Warning", "Enter a prompt first")
        return
    
    if not OPENAI_API_KEY:
        messagebox.showerror("Error", "OpenAI API Key not configured")
        return
    
    btn_gen_openai.config(text="⏳ Generating...", state="disabled")
    root.update()
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": f"Generate a script tool description. {prompt}. Give me: TITLE: (catchy title in 3 languages Arabic/English/French) then DESC: (short description in 3 languages)"}
                ],
                "max_tokens": 300
            },
            timeout=30
        )
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # Extract title and description
        title_match = re.search(r'TITLE:\s*(.+?)(?=DESC:|$)', content, re.IGNORECASE)
        desc_match = re.search(r'DESC:\s*(.+?)$', content, re.IGNORECASE | re.DOTALL)
        
        if title_match:
            entry_title.delete(0, tk.END)
            entry_title.insert(0, title_match.group(1).strip()[:60])
        if desc_match:
            entry_desc.delete(0, tk.END)
            entry_desc.insert(0, desc_match.group(1).strip()[:100])
        
        messagebox.showinfo("Success", "✨ Generated with OpenAI! Review the fields above")
        
    except requests.exceptions.Timeout:
        messagebox.showerror("Error", "Request timed out. Try again.")
    except Exception as e:
        messagebox.showerror("Error", f"Generation failed: {str(e)}")
    finally:
        btn_gen_openai.config(text="🤖 Generate with OpenAI", state="normal")

def auto_generate_batch():
    """Auto-generate multiple scripts using AI"""
    topic = entry_batch_topic.get().strip()
    count = entry_batch_count.get().strip()
    
    if not topic or not count:
        messagebox.showwarning("Warning", "Enter topic and count")
        return
    
    try:
        count = int(count)
        if count > 10:
            messagebox.showwarning("Warning", "Maximum 10 scripts per batch")
            return
    except ValueError:
        messagebox.showerror("Error", "Count must be a number")
        return
    
    btn_batch.config(text="⏳ Generating...", state="disabled")
    root.update()
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "anthropic/claude-3-haiku",
                "messages": [
                    {"role": "user", "content": f"Generate {count} script/tool ideas about {topic}. For each give: TITLE: (in 3 languages) DESC: (in 3 languages). Separate each script with ---"}
                ],
                "max_tokens": 2000
            },
            timeout=60
        )
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # Parse and add to data
        scripts = content.split('---')
        added = 0
        
        for script in scripts:
            title_match = re.search(r'TITLE:\s*(.+?)(?=DESC:|$)', script, re.IGNORECASE)
            desc_match = re.search(r'DESC:\s*(.+?)$', script, re.IGNORECASE | re.DOTALL)
            
            if title_match and desc_match:
                new_card = {
                    "title": title_match.group(1).strip()[:60],
                    "desc": desc_match.group(1).strip()[:100],
                    "img": f"https://picsum.photos/id/{len(current_data.get('cards', []))}/400/200",
                    "link": "#"
                }
                current_data['cards'].append(new_card)
                added += 1
        
        if save_data(current_data, current_sha):
            messagebox.showinfo("Success", f"✅ Added {added} scripts automatically!")
            refresh_list()
        else:
            messagebox.showerror("Error", "❌ Failed to save")
        
    except Exception as e:
        messagebox.showerror("Error", f"Batch generation failed: {str(e)}")
    finally:
        btn_batch.config(text="🚀 Auto-Generate Batch", state="normal")

def send_notification(message):
    """Send notification to Discord/Telegram"""
    try:
        # Discord
        if DISCORD_WEBHOOK_URL:
            requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, timeout=10)
        
        # Telegram
        if TELEGRAM_BOT_TOKEN:
            telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            # You would need to add CHAT_ID to secrets
            # requests.post(telegram_url, json={"chat_id": CHAT_ID, "text": message})
        
        return True
    except:
        return False

# ========== Build GUI ==========
root = tk.Tk()
root.title("🎛️ 27TechAI Dashboard - Admin Panel")
root.geometry("1400x800")
root.configure(bg="#1a1a2e")

# Create Tab Control
tab_control = ttk.Notebook(root)

# Tab 1: Script Management
tab_scripts = tk.Frame(tab_control, bg="#1a1a2e")
tab_control.add(tab_scripts, text='📦 Scripts')

# Tab 2: AI Auto-Generate
tab_ai = tk.Frame(tab_control, bg="#1a1a2e")
tab_control.add(tab_ai, text='🤖 AI Generator')

# Tab 3: Analytics
tab_analytics = tk.Frame(tab_control, bg="#1a1a2e")
tab_control.add(tab_analytics, text='📊 Analytics')

# Tab 4: Settings
tab_settings = tk.Frame(tab_control, bg="#1a1a2e")
tab_control.add(tab_settings, text='⚙️ Settings')

tab_control.pack(expand=1, fill="both", padx=10, pady=10)

# ========== TAB 1: SCRIPT MANAGEMENT ==========
# Left panel - Script list
left_frame = tk.LabelFrame(tab_scripts, text="📋 Script Library", bg="#1a1a2e", fg="#a855f7", font=("Arial", 12, "bold"))
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

listbox = tk.Listbox(left_frame, bg="#16213e", fg="white", font=("Arial", 10), height=20, selectmode=tk.SINGLE)
listbox.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)

btn_frame = tk.Frame(left_frame, bg="#1a1a2e")
btn_frame.pack(fill=tk.X, pady=5)

tk.Button(btn_frame, text="🔄 Refresh", command=refresh_list, bg="#6c63ff", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="🗑️ Delete", command=delete_card, bg="#ff4444", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)

status_label = tk.Label(left_frame, text="Ready", bg="#1a1a2e", fg="#a855f7", font=("Arial", 9))
status_label.pack(pady=5)

# Right panel - Add/Edit
right_frame = tk.LabelFrame(tab_scripts, text="➕ Add New Script", bg="#1a1a2e", fg="#a855f7", font=("Arial", 12, "bold"))
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

tk.Label(right_frame, text="Title:", bg="#1a1a2e", fg="white", font=("Arial", 10)).pack(anchor=tk.W, pady=(10, 0))
entry_title = tk.Entry(right_frame, bg="#16213e", fg="white", font=("Arial", 10), width=50)
entry_title.pack(fill=tk.X, pady=5)

tk.Label(right_frame, text="Description:", bg="#1a1a2e", fg="white", font=("Arial", 10)).pack(anchor=tk.W, pady=(10, 0))
entry_desc = tk.Entry(right_frame, bg="#16213e", fg="white", font=("Arial", 10), width=50)
entry_desc.pack(fill=tk.X, pady=5)

tk.Label(right_frame, text="Image URL:", bg="#1a1a2e", fg="white", font=("Arial", 10)).pack(anchor=tk.W, pady=(10, 0))
entry_img = tk.Entry(right_frame, bg="#16213e", fg="white", font=("Arial", 10), width=50)
entry_img.pack(fill=tk.X, pady=5)

tk.Label(right_frame, text="CPA/Download Link:", bg="#1a1a2e", fg="white", font=("Arial", 10)).pack(anchor=tk.W, pady=(10, 0))
entry_link = tk.Entry(right_frame, bg="#16213e", fg="white", font=("Arial", 10), width=50)
entry_link.pack(fill=tk.X, pady=5)

tk.Button(right_frame, text="➕ Add Script", command=add_card, bg="#6c63ff", fg="white", font=("Arial", 11, "bold")).pack(fill=tk.X, pady=10)
tk.Button(right_frame, text="🧹 Clear Fields", command=clear_entries, bg="#ff8800", fg="white", font=("Arial", 10)).pack(fill=tk.X, pady=5)

# Claude AI section
tk.Label(right_frame, text="🤖 Quick AI Generator:", bg="#1a1a2e", fg="#a855f7", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(20, 0))
text_prompt = scrolledtext.ScrolledText(right_frame, height=4, bg="#16213e", fg="white", font=("Arial", 10))
text_prompt.pack(fill=tk.BOTH, expand=True, pady=5)

btn_frame_ai = tk.Frame(right_frame, bg="#1a1a2e")
btn_frame_ai.pack(fill=tk.X, pady=5)

btn_gen = tk.Button(btn_frame_ai, text="🤖 Claude", command=generate_with_claude, bg="#a855f7", fg="white", font=("Arial", 10, "bold"))
btn_gen.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

btn_gen_openai = tk.Button(btn_frame_ai, text="🤖 OpenAI", command=generate_with_openai, bg="#10a37f", fg="white", font=("Arial", 10, "bold"))
btn_gen_openai.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

# ========== TAB 2: AI AUTO-GENERATOR ==========
ai_main_frame = tk.Frame(tab_ai, bg="#1a1a2e")
ai_main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

tk.Label(ai_main_frame, text="🚀 AI Auto-Generate Multiple Scripts", bg="#1a1a2e", fg="#a855f7", font=("Arial", 16, "bold")).pack(pady=20)

tk.Label(ai_main_frame, text="Topic/Keywords:", bg="#1a1a2e", fg="white", font=("Arial", 12)).pack(anchor=tk.W, pady=(10, 0))
entry_batch_topic = tk.Entry(ai_main_frame, bg="#16213e", fg="white", font=("Arial", 12), width=60)
entry_batch_topic.pack(fill=tk.X, pady=10)

tk.Label(ai_main_frame, text="Number of Scripts (1-10):", bg="#1a1a2e", fg="white", font=("Arial", 12)).pack(anchor=tk.W, pady=(10, 0))
entry_batch_count = tk.Entry(ai_main_frame, bg="#16213e", fg="white", font=("Arial", 12), width=60)
entry_batch_count.pack(fill=tk.X, pady=10)
entry_batch_count.insert(0, "5")

btn_batch = tk.Button(ai_main_frame, text="🚀 Auto-Generate Batch", command=auto_generate_batch, bg="#6c63ff", fg="white", font=("Arial", 14, "bold"), height=2)
btn_batch.pack(fill=tk.X, pady=20)

tk.Label(ai_main_frame, text="💡 Tip: Use broad topics like 'Python automation', 'Web scraping tools', 'Telegram bots' for best results", 
         bg="#16213e", fg="#a855f7", font=("Arial", 10), justify=tk.LEFT).pack(fill=tk.X, pady=10)

# ========== TAB 3: ANALYTICS ==========
analytics_frame = tk.Frame(tab_analytics, bg="#1a1a2e")
analytics_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

tk.Label(analytics_frame, text="📊 Site Analytics & Statistics", bg="#1a1a2e", fg="#a855f7", font=("Arial", 16, "bold")).pack(pady=20)

# Stats boxes
stats_frame = tk.Frame(analytics_frame, bg="#1a1a2e")
stats_frame.pack(fill=tk.X, pady=20)

# Total Scripts
tk.Label(stats_frame, text="Total Scripts", bg="#16213e", fg="#a855f7", font=("Arial", 12, "bold"), width=20, height=3).pack(side=tk.LEFT, padx=10)
label_total_scripts = tk.Label(stats_frame, text="0", bg="#6c63ff", fg="white", font=("Arial", 18, "bold"), width=10, height=3)
label_total_scripts.pack(side=tk.LEFT, padx=10)

# Site URL
tk.Label(stats_frame, text="Site URL", bg="#16213e", fg="#a855f7", font=("Arial", 12, "bold"), width=20, height=3).pack(side=tk.LEFT, padx=10)
label_site_url = tk.Label(stats_frame, text=SITE_URL or "Not configured", bg="#10a37f", fg="white", font=("Arial", 10), width=30, height=3, wraplength=250)
label_site_url.pack(side=tk.LEFT, padx=10)

def update_analytics():
    """Update analytics display"""
    total = len(current_data.get('cards', []))
    label_total_scripts.config(text=str(total))

btn_update_analytics = tk.Button(analytics_frame, text="🔄 Refresh Analytics", command=update_analytics, bg="#6c63ff", fg="white", font=("Arial", 12, "bold"))
btn_update_analytics.pack(pady=20)

# ========== TAB 4: SETTINGS ==========
settings_frame = tk.Frame(tab_settings, bg="#1a1a2e")
settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

tk.Label(settings_frame, text="⚙️ Configuration & API Keys Status", bg="#1a1a2e", fg="#a855f7", font=("Arial", 16, "bold")).pack(pady=20)

# API Keys status
api_status_frame = tk.LabelFrame(settings_frame, text="🔑 API Keys Status", bg="#1a1a2e", fg="#a855f7", font=("Arial", 12, "bold"))
api_status_frame.pack(fill=tk.X, pady=10)

api_keys_info = [
    ("GitHub", bool(GITHUB_TOKEN)),
    ("OpenRouter", bool(OPENROUTER_API_KEY)),
    ("OpenAI", bool(OPENAI_API_KEY)),
    ("Anthropic", bool(ANTHROPIC_API_KEY)),
    ("Google AI", bool(GOOGLE_AI_API_KEY)),
    ("HuggingFace", bool(HUGGINGFACE_API_KEY)),
    ("Discord", bool(DISCORD_WEBHOOK_URL)),
    ("Telegram", bool(TELEGRAM_BOT_TOKEN))
]

row = 0
col = 0
for name, configured in api_keys_info:
    status = "✅ Configured" if configured else "❌ Not Set"
    color = "#10a37f" if configured else "#ff4444"
    
    tk.Label(api_status_frame, text=f"{name}:", bg="#16213e", fg="white", font=("Arial", 11), width=15, anchor=tk.W).grid(row=row, column=col*2, padx=10, pady=5, sticky=tk.W)
    tk.Label(api_status_frame, text=status, bg=color, fg="white", font=("Arial", 10, "bold"), width=15).grid(row=row, column=col*2+1, padx=10, pady=5)
    
    row += 1
    if row > 3:
        row = 0
        col += 1

# Initialize data
current_data = {}
current_sha = None
refresh_list()

root.mainloop()
