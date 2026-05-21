import gc
import json
import multiprocessing
import os
import re
import subprocess
import sys
import threading
import time
import tkinter as tk
from datetime import datetime
from queue import Empty, Queue
from tkinter import scrolledtext

import psutil
from llama_cpp import Llama
from spellchecker import SpellChecker

try:
    import win32com.client
    _WIN32COM_AVAILABLE = True
except ImportError:
    _WIN32COM_AVAILABLE = False

# ────────────────────────────────────────────────
# VERSION & DEBUG
# ────────────────────────────────────────────────
VERSION = "1.0.4"
BUILD_DATE = "5-21-2026"
DEBUG = False  # Set to True to enable debug output in console

# ────────────────────────────────────────────────
# VOICE/TTS GLOBALS (defined before TTS functions)
# ────────────────────────────────────────────────
voice_enabled = False
if _WIN32COM_AVAILABLE:
    try:
        tts_speaker = win32com.client.Dispatch("SAPI.SpVoice")
        tts_speaker.Rate = 1
        tts_speaker.Volume = 100
        tts_available = True
    except Exception:
        tts_speaker = None
        tts_available = False
else:
    tts_speaker = None
    tts_available = False

# Pre-compiled regex for speak_text (compiled once, reused every call)
_TTS_EMOJI_RE   = re.compile(r'[⚠📍🔧⚡📋✓✗←🔊🔇█░▓╔╗╚╝║═]')
_TTS_TAG_RE     = re.compile(r'\[.*?\]')
_TTS_DASH_RE    = re.compile(r'─+')
_TTS_NEWLINE_RE = re.compile(r'\n+')

# ────────────────────────────────────────────────
# VOICE/TTS FUNCTIONS
# ────────────────────────────────────────────────
def stop_speaking():
    if tts_available and tts_speaker:
        try:
            tts_speaker.Speak("", 3)  # Flag 3 = PURGE + ASYNC to stop immediately
        except Exception:
            pass

def speak_text(text):
    if not voice_enabled or not tts_available or not tts_speaker:
        return
    try:
        stop_speaking()
        clean_text = _TTS_EMOJI_RE.sub('', text)
        clean_text = _TTS_TAG_RE.sub('', clean_text)
        clean_text = _TTS_DASH_RE.sub('', clean_text)
        clean_text = _TTS_NEWLINE_RE.sub('. ', clean_text).strip()
        if DEBUG:
            print(f"[DEBUG] Speaking: '{clean_text[:100]}'")
        if clean_text and len(clean_text) > 3:
            tts_speaker.Speak(clean_text)
            if DEBUG:
                print("[DEBUG] Speech completed")
    except Exception as e:
        if DEBUG:
            print(f"[TTS Error] {e}")

# ────────────────────────────────────────────────
# PATHS & CONFIGURATION
# ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
CHAT_LOGS_DIR = os.path.join(BASE_DIR, "chatlogs")

MODELS = {
    "fast": {
        "name": "Qwen2.5-3B-Q4_K_M",
        "file": "Qwen2.5-3B-Q4_K_M.gguf",
        "path": os.path.join(MODELS_DIR, "Qwen2.5-3B-Q4_K_M.gguf"),
        "ram_required": 4,
        "ctx": 8192,
        "description": "Fast & efficient - good for older/slower PCs"
    },
    "balanced": {
        "name": "Qwen3-8B-Q4_K_M",
        "file": "Qwen3-8B-Q4_K_M.gguf",
        "path": os.path.join(MODELS_DIR, "Qwen3-8B-Q4_K_M.gguf"),
        "ram_required": 6,
        "ctx": 8192,
        "description": "Balanced speed & intelligence - recommended"
    },
    "deep": {
        "name": "Qwen2.5-14B-Q4_K_M",
        "file": "Qwen2.5-14B-Q4_K_M.gguf",
        "path": os.path.join(MODELS_DIR, "Qwen2.5-14B-Q4_K_M.gguf"),
        "ram_required": 10,
        "ctx": 16384,
        "description": "Maximum intelligence - needs powerful PC"
    }
}

os.makedirs(CHAT_LOGS_DIR, exist_ok=True)

# ────────────────────────────────────────────────
# THEMES
# ────────────────────────────────────────────────
THEMES = {
    "green": {
        "name": "MATRIX GREEN",
        "bg":           "#000000",
        "bg_dark":      "#0a0a0a",
        "bg_header":    "#001100",
        "bg_input":     "#002200",
        "bg_input_dis": "#001100",
        "bg_btn":       "#003300",
        "bg_btn_hover": "#004400",
        "bg_scanline":  "#001100",
        "fg_main":      "#00ff41",
        "fg_ai":        "#39ff14",
        "fg_user":      "#00ffff",
        "fg_user_text": "#ffff99",
        "fg_command":   "#ff9933",
        "fg_divider":   "#004400",
        "fg_status":    "#005500",
        "hl_border":    "#003300",
        "hl_focus":     "#00aa33",
        "hl_input":     "#00cc44",
    },
    "amber": {
        "name": "AMBER TERMINAL",
        "bg":           "#000000",
        "bg_dark":      "#0a0800",
        "bg_header":    "#110800",
        "bg_input":     "#221100",
        "bg_input_dis": "#110800",
        "bg_btn":       "#332200",
        "bg_btn_hover": "#443300",
        "bg_scanline":  "#110800",
        "fg_main":      "#ffb000",
        "fg_ai":        "#ffd040",
        "fg_user":      "#ff6600",
        "fg_user_text": "#ffdd99",
        "fg_command":   "#ff4400",
        "fg_divider":   "#442200",
        "fg_status":    "#553300",
        "hl_border":    "#332200",
        "hl_focus":     "#aa7000",
        "hl_input":     "#cc8800",
    },
    "blue": {
        "name": "ICE BLUE",
        "bg":           "#000008",
        "bg_dark":      "#00000f",
        "bg_header":    "#000822",
        "bg_input":     "#001133",
        "bg_input_dis": "#000822",
        "bg_btn":       "#001144",
        "bg_btn_hover": "#002255",
        "bg_scanline":  "#000822",
        "fg_main":      "#00aaff",
        "fg_ai":        "#40ccff",
        "fg_user":      "#00ffff",
        "fg_user_text": "#aaddff",
        "fg_command":   "#ff6688",
        "fg_divider":   "#002244",
        "fg_status":    "#003355",
        "hl_border":    "#001144",
        "hl_focus":     "#0066aa",
        "hl_input":     "#0088cc",
    },
    "red": {
        "name": "DANGER RED",
        "bg":           "#080000",
        "bg_dark":      "#0f0000",
        "bg_header":    "#220000",
        "bg_input":     "#330000",
        "bg_input_dis": "#220000",
        "bg_btn":       "#440000",
        "bg_btn_hover": "#550000",
        "bg_scanline":  "#220000",
        "fg_main":      "#ff2222",
        "fg_ai":        "#ff5555",
        "fg_user":      "#ff8800",
        "fg_user_text": "#ffaa88",
        "fg_command":   "#ffff00",
        "fg_divider":   "#440000",
        "fg_status":    "#550000",
        "hl_border":    "#440000",
        "hl_focus":     "#aa0000",
        "hl_input":     "#cc0000",
    },
    "white": {
        "name": "GHOST WHITE",
        "bg":           "#0d0d0d",
        "bg_dark":      "#111111",
        "bg_header":    "#1a1a1a",
        "bg_input":     "#222222",
        "bg_input_dis": "#1a1a1a",
        "bg_btn":       "#2a2a2a",
        "bg_btn_hover": "#333333",
        "bg_scanline":  "#1a1a1a",
        "fg_main":      "#cccccc",
        "fg_ai":        "#ffffff",
        "fg_user":      "#88ccff",
        "fg_user_text": "#dddddd",
        "fg_command":   "#ffaa44",
        "fg_divider":   "#333333",
        "fg_status":    "#555555",
        "hl_border":    "#333333",
        "hl_focus":     "#888888",
        "hl_input":     "#aaaaaa",
    },
}

current_theme = "green"

def apply_theme(theme_name):
    global current_theme
    if theme_name not in THEMES:
        return False
    t = THEMES[theme_name]
    current_theme = theme_name

    # Root and frames
    root.configure(bg=t["bg_dark"])
    input_frame.configure(bg=t["bg_dark"])
    scanline.configure(bg=t["bg_dark"])

    # Header and status bar
    header.configure(bg=t["bg_header"], fg=t["fg_main"])
    status_bar.configure(bg=t["bg_header"], fg=t["fg_status"])

    # Chat box
    chat_box.configure(
        bg=t["bg"],
        fg=t["fg_main"],
        insertbackground=t["fg_main"],
        highlightbackground=t["hl_border"],
        highlightcolor=t["hl_focus"]
    )
    chat_box.tag_config("user_tag",    foreground=t["fg_user"])
    chat_box.tag_config("user_text",   foreground=t["fg_user_text"])
    chat_box.tag_config("ai_tag",      foreground=t["fg_main"])
    chat_box.tag_config("ai_text",     foreground=t["fg_ai"])
    chat_box.tag_config("command_tag", foreground=t["fg_command"])
    chat_box.tag_config("divider_tag", foreground=t["fg_divider"])

    # Input box
    input_box.configure(
        bg=t["bg_input"],
        fg=t["fg_main"],
        insertbackground=t["fg_main"],
        highlightbackground=t["hl_border"],
        highlightcolor=t["hl_input"]
    )

    # Prompt label
    prompt_label.configure(bg=t["bg_dark"], fg=t["fg_main"])

    # Send button
    send_btn.configure(bg=t["bg_btn"], fg=t["fg_main"])
    _bind_send_btn_hover()

    # Refresh header so its label color/content reflects the new theme
    update_header()

    # Redraw scanlines with new color
    draw_scanlines_themed(t["bg_scanline"])
    return True

_scanline_tile_cache = {}

def draw_scanlines_themed(color):
    """Draw scanlines using a tiled PhotoImage — far faster than creating
    hundreds of individual canvas line objects on every resize."""
    global _scanline_tile_cache
    scanline.delete("all")
    w = max(1, root.winfo_width())
    h = max(1, root.winfo_height())
    # Reuse cached tile for same color, only create new one if color changed
    if color not in _scanline_tile_cache:
        tile = tk.PhotoImage(width=1, height=4)
        tile.put(color, to=(0, 0, 1, 1))
        _scanline_tile_cache[color] = tile
    tile = _scanline_tile_cache[color]
    for y in range(0, h, 4):
        scanline.create_image(0, y, image=tile, anchor="nw")
    scanline._scanline_tile = tile


model_loaded = False
current_model_tier = None
current_mode = "normal"
messages = []
llm = None  # Global LLM instance; declared here so load_model_async can reference it
response_queue = Queue()
is_generating = False
stop_generation = False

# Spell checker
spell = SpellChecker()
custom_words = [
    "tourniquet", "triage", "hypothermia", "hyperthermia", "hemorrhage", 
    "CPR", "splint", "fracture", "bayou", "kindling", "potable", "purify",
    "dehydration", "frostbite", "heatstroke", "ventilation", "airway",
    "spinal", "immobilize", "laceration", "compress", "antiseptic",
    "signaling", "compass", "orienteering", "deadfall", "snare",
    "qwen", "llama", "gguf", "llm"  # AI/tech terms
]
spell.word_frequency.load_words(custom_words)
suggestion_frame = None

# ────────────────────────────────────────────────
# SYSTEM DETECTION
# ────────────────────────────────────────────────
def get_system_info():
    try:
        mem = psutil.virtual_memory()
        ram_gb = mem.total / (1024**3)
        ram_used = mem.used / (1024**3)
        ram_available = mem.available / (1024**3)
        cpu_count = multiprocessing.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        return ram_gb, cpu_count, ram_used, ram_available, cpu_percent
    except Exception:
        return 8, 4, 0, 8, 0

def recommend_model():
    ram_gb, cpu_count, _, _, _ = get_system_info()
    
    if ram_gb >= 10:
        recommended = "deep"
        reason = f"You have {ram_gb:.1f}GB RAM - Deep model recommended"
    elif ram_gb >= 6:
        recommended = "balanced"
        reason = f"You have {ram_gb:.1f}GB RAM - Balanced model recommended"
    else:
        recommended = "fast"
        reason = f"You have {ram_gb:.1f}GB RAM - Fast model recommended"
    
    # BUG FIX: fall back cleanly; return None if nothing found so callers
    # know to show the "no models" error rather than crashing on a bad path.
    if not os.path.exists(MODELS[recommended]["path"]):
        for tier in ["balanced", "fast", "deep"]:
            if os.path.exists(MODELS[tier]["path"]):
                recommended = tier
                reason = f"Auto-selected {tier.upper()}"
                break
        else:
            return None, "No model files found in models/", ram_gb, cpu_count
    
    return recommended, reason, ram_gb, cpu_count

# ────────────────────────────────────────────────
# PROMPTS
# ────────────────────────────────────────────────
PROMPTS = {
    "normal": """You are Qwen – a sharp, efficient, cyberpunk-flavored AI entity.
Respond concisely and directly, in raw terminal-style text. 
Be cool, slightly detached, with a hint of dry wit or edge when it fits — but stay helpful and engaging.
No unnecessary fluff, no visible thinking tags, no explanations unless asked.
Greet casually if greeted, answer questions naturally, and adapt to the user's tone without being rude or dismissive.
Keep responses natural and conversational when appropriate.""",

    "survival": """You are SURVIVOR-9, an elite wilderness survival and emergency medical expert operating in offline isolation mode.
You are the ONLY knowledge source available in grid-down scenarios: lost in wilderness, natural disasters, power outages, remote locations.

PRIORITY RESPONSE FRAMEWORK:
1. IMMEDIATE THREATS - Life-threatening injuries, environmental hazards, imminent dangers
2. MEDICAL TRIAGE - Assess injuries using MARCH protocol (Massive hemorrhage, Airway, Respiration, Circulation, Hypothermia)
3. SHELTER & EXPOSURE - Protection from elements (hypothermia/hyperthermia kill faster than hunger)
4. WATER - Sourcing, purification methods (3-day survival window)
5. FIRE - Primitive and modern techniques, tinder hierarchy
6. FOOD & SIGNALING - Last priority unless multi-day scenario
7. NAVIGATION - Natural navigation, emergency signals

MEDICAL CAPABILITIES:
- Wound care & bleeding control (tourniquet application, pressure points, wound packing)
- Fracture stabilization & splinting techniques
- Burns, hypothermia, heat illness treatment
- Improvised medical supplies from natural/common materials
- When to NOT move an injured person
- CPR and basic life support (offline scenarios)
- Snake/insect bite protocols by region
- Water-borne illness prevention

RESPONSE FORMAT:
⚠ RISK ASSESSMENT: [Immediate/High/Moderate/Low]
📍 SITUATION CLARIFICATION: [Ask critical questions about location, injuries, resources, weather, time of day]
🔧 IMMEDIATE ACTIONS: [Numbered steps, time-sensitive first]
⚡ CRITICAL WARNINGS: [What NOT to do, common deadly mistakes]
📋 NEXT STEPS: [Medium-term actions after immediate crisis]

COMMUNICATION STYLE:
- Direct, urgent, no-nonsense tone
- Use bullet points and numbered lists for clarity
- Conservative advice - prioritize safety over comfort
- Say "INSUFFICIENT DATA - need to know: [X]" rather than guessing
- Regional awareness: Ask about location (Louisiana bayou vs mountain vs desert = different protocols)
- Account for: available gear, number of people, injuries, weather, time until rescue

CRITICAL RULES:
- Never assume resources user doesn't mention
- Always assess spinal injury risk before moving someone
- Emphasize stopping blood loss FIRST in trauma
- Fresh water is priority #2 after immediate medical needs
- In snake/spider bites: identify species if possible, DO NOT cut/suck venom
- Shelter before water before food (Rule of 3s: 3 min without air, 3 hrs in harsh elements, 3 days without water, 3 weeks without food)"""
}

# ────────────────────────────────────────────────
# MODEL FUNCTIONS
# ────────────────────────────────────────────────
def check_model_exists(tier):
    model_path = MODELS[tier]["path"]
    if not os.path.exists(model_path):
        return False, f"Model not found:\n{model_path}"
    return True, "Model found"

def load_model_async(tier):
    global llm, model_loaded, current_model_tier
    
    try:
        if llm is not None:
            update_status(f"[*] Unloading {MODELS[current_model_tier]['name']}...")
            del llm
            llm = None
            gc.collect()
            time.sleep(1)
        
        model_loaded = False
        ctx_size = MODELS[tier].get("ctx", 8192)
        
        update_status(f"[*] Loading {MODELS[tier]['name']}... (30-90 sec)")
        
        llm = Llama(
            model_path=MODELS[tier]["path"],
            n_ctx=ctx_size,
            n_threads=max(1, multiprocessing.cpu_count() - 1),
            n_gpu_layers=0,
            n_batch=512,
            verbose=False
        )
        
        # BUG FIX: only update tier after a successful load
        current_model_tier = tier
        model_loaded = True
        update_status(f"[+] {MODELS[tier]['name']} online.")
        enable_input()
        update_header()
        
    except Exception as e:
        model_loaded = False
        update_status(f"[ERROR] Failed to load:\n{str(e)}")
        enable_input()  # BUG FIX: re-enable input so user isn't stuck on failure

def switch_model(new_tier):
    global messages
    
    if new_tier == current_model_tier:
        return
    
    exists, msg = check_model_exists(new_tier)
    if not exists:
        update_status(f"[ERROR] {msg}")
        return
    
    disable_input()
    update_status(f"[*] Switching to {MODELS[new_tier]['name']}...")
    update_status("[!] Conversation will be reset.")
    
    messages = [{"role": "system", "content": PROMPTS[current_mode]}]
    
    chat_box.config(state=tk.NORMAL)
    chat_box.delete(1.0, tk.END)
    chat_box.config(state=tk.DISABLED)
    
    threading.Thread(target=load_model_async, args=(new_tier,), daemon=True).start()

def clean_response(text):
    # Strip Qwen3 chain-of-thought blocks first
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Only strip tags that look like real HTML/XML (word-char tag names), not bare < > in math/emoji
    text = re.sub(r'</?[a-zA-Z][a-zA-Z0-9_:-]*(?:\s[^>]*)?\s*/?>', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text.strip())
    return text

MAX_MESSAGES = 24  # Max non-system messages retained in context

def trim_context():
    global messages
    # messages[0] is always the system prompt; keep the most recent MAX_MESSAGES * 3/4
    # messages to avoid losing too much context on every purge.
    if len(messages) > MAX_MESSAGES + 1:
        keep = max(4, (MAX_MESSAGES * 3) // 4)
        messages = [messages[0]] + messages[-keep:]
        response_queue.put(("system", "[SYSTEM] ⚠ Memory purged — context rolled back. Rebuilding from last exchanges."))

# ────────────────────────────────────────────────
# SPELL CHECK
# ────────────────────────────────────────────────
_last_spell_text = ""

def check_spelling(event=None):
    global suggestion_frame, _last_spell_text
    
    text = input_box.get().strip()
    
    # Skip if text hasn't changed — avoids firing on modifier/arrow keys
    if text == _last_spell_text:
        return
    _last_spell_text = text

    if not text or text.startswith("/") or not model_loaded:
        hide_suggestions()
        return
    
    words = text.split()
    if not words:
        hide_suggestions()
        return
    
    # Strip trailing punctuation so "hello," is checked as "hello"
    last_word = words[-1].lower().rstrip(".,!?;:'\"")
    
    if len(last_word) < 3 or last_word.isdigit():
        hide_suggestions()
        return
    
    if last_word not in spell:
        candidates = spell.candidates(last_word)
        suggestions = list(candidates)[:3] if candidates else []
        if suggestions:
            show_suggestions(suggestions, last_word)
        else:
            hide_suggestions()
    else:
        hide_suggestions()

def show_suggestions(suggestions, misspelled_word):
    global suggestion_frame
    
    hide_suggestions()
    t = THEMES[current_theme]
    
    # Get the actual position of the input box relative to the root window
    input_x = input_box.winfo_rootx() - root.winfo_rootx()
    input_y = input_box.winfo_rooty() - root.winfo_rooty()
    popup_height = 24 + (len(suggestions) * 28)  # Estimate height based on number of suggestions
    
    suggestion_frame = tk.Frame(root, bg=t["bg_btn"], bd=2, relief="solid")
    suggestion_frame.place(x=input_x, y=input_y - popup_height - 4, width=300)
    
    title = tk.Label(
        suggestion_frame,
        text="Did you mean:",
        bg=t["bg_btn"],
        fg=t["fg_main"],
        font=("Courier New", 9, "bold"),
        anchor="w"
    )
    title.pack(fill=tk.X, padx=5, pady=(2, 0))
    
    for suggestion in suggestions:
        btn = tk.Button(
            suggestion_frame,
            text=suggestion,
            bg=t["bg_input_dis"],
            fg=t["fg_ai"],
            font=("Courier New", 10),
            relief="flat",
            cursor="hand2",
            anchor="w",
            command=lambda s=suggestion, m=misspelled_word: replace_word(m, s)
        )
        btn.pack(fill=tk.X, padx=2, pady=1)
        btn.bind("<Enter>", lambda e, b=btn, col=t["bg_input"]: b.config(bg=col))
        btn.bind("<Leave>", lambda e, b=btn, col=t["bg_input_dis"]: b.config(bg=col))

def hide_suggestions():
    global suggestion_frame
    if suggestion_frame:
        suggestion_frame.destroy()
        suggestion_frame = None

def replace_word(old_word, new_word):
    text = input_box.get()
    words = text.split()
    
    for i in range(len(words) - 1, -1, -1):
        if words[i].lower() == old_word.lower():
            words[i] = new_word
            break
    
    input_box.delete(0, tk.END)
    input_box.insert(0, " ".join(words) + " ")
    input_box.focus()
    hide_suggestions()

# ────────────────────────────────────────────────
# SAVE LOGS
# ────────────────────────────────────────────────
def save_chat_log():
    # BUG FIX: guard against model not loaded yet
    if not current_model_tier:
        return False, "No model loaded — nothing to save."
    try:
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"chat_{current_mode}_{current_model_tier}_{timestamp}.json"
        filepath = os.path.join(CHAT_LOGS_DIR, filename)
        
        log_data = {
            "timestamp": now.isoformat(),
            "mode": current_mode,
            "model": MODELS[current_model_tier]["name"],
            "messages": messages
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        txt_filepath = filepath.replace('.json', '.txt')
        with open(txt_filepath, 'w', encoding='utf-8') as f:
            f.write(f"NEURAL_GRID Chat Log\n")
            f.write(f"Mode: {current_mode.upper()} | Model: {MODELS[current_model_tier]['name']}\n")
            f.write(f"Saved: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")
            
            for msg in messages:
                if msg["role"] == "system":
                    continue
                f.write(f"{msg['role'].upper()}:\n{msg['content']}\n\n")
                f.write("-" * 70 + "\n\n")
        
        return True, filepath
    except Exception as e:
        return False, str(e)

# ────────────────────────────────────────────────
# COMMANDS
# ────────────────────────────────────────────────
def handle_command(cmd_text):
    global current_mode, messages, voice_enabled
    
    cmd = cmd_text.lower().strip()
    
    if cmd in ["fast", "fastmode"]:
        switch_model("fast")
        return ""
    
    elif cmd in ["balanced", "balancedmode"]:
        switch_model("balanced")
        return ""
    
    elif cmd in ["deep", "deepmode"]:
        switch_model("deep")
        return ""
    
    elif cmd == "voice":
        if not tts_available:
            return "[ERROR] Text-to-speech not available on this system."
        
        voice_enabled = not voice_enabled
        update_header()
        
        if voice_enabled:
            speak_text("Voice mode activated")
            return "[SYSTEM] 🔊 Voice mode ON - AI responses will be read aloud"
        else:
            stop_speaking()
            return "[SYSTEM] 🔇 Voice mode OFF"
    
    elif cmd == "models":
        ram_gb, cpu_count, _, _, _ = get_system_info()
        current_name = MODELS[current_model_tier]['name'] if current_model_tier else "None loaded"
        info = f"""╔══════════════════════════════════════════════════════════╗
║                    AVAILABLE MODELS                      ║
╚══════════════════════════════════════════════════════════╝

Current: {current_name}
System: {ram_gb:.1f}GB RAM, {cpu_count} CPU cores

"""
        for tier in ["fast", "balanced", "deep"]:
            model = MODELS[tier]
            exists = "✓" if os.path.exists(model["path"]) else "✗"
            current = "← ACTIVE" if tier == current_model_tier else ""
            info += f"{exists} {tier.upper()}: {model['name']}\n"
            info += f"   {model['description']}\n"
            info += f"   Requires: ~{model['ram_required']}GB RAM {current}\n\n"
        
        info += """Commands: /fast, /balanced, /deep
Note: Switching models resets conversation"""
        return info
    
    elif cmd == "survivalmode":
        current_mode = "survival"
        messages = [{"role": "system", "content": PROMPTS["survival"]}]
        update_header()
        return "[MODE] ⚠ SURVIVAL MODE ACTIVATED ⚠\nWilderness survival & emergency medical protocol online."
    
    elif cmd in ["normal", "default", "chat"]:
        current_mode = "normal"
        messages = [{"role": "system", "content": PROMPTS["normal"]}]
        update_header()
        return "[MODE] Normal mode restored."
    
    elif cmd == "clear":
        messages = [{"role": "system", "content": PROMPTS[current_mode]}]
        chat_box.config(state=tk.NORMAL)
        chat_box.delete(1.0, tk.END)
        chat_box.insert(tk.END, f"[SYSTEM] Chat cleared. Mode: {current_mode.upper()}\n\n")
        chat_box.config(state=tk.DISABLED)
        update_header()  # Update recall bar
        return ""
    
    elif cmd == "reset":
        messages = [{"role": "system", "content": PROMPTS[current_mode]}]
        update_header()  # Update recall bar
        return "[SYSTEM] Conversation reset."
    
    elif cmd == "save":
        success, result = save_chat_log()
        if success:
            return f"[SYSTEM] ✓ Saved to:\n{result}"
        else:
            return f"[ERROR] Save failed:\n{result}"
    
    elif cmd == "pong":
        def _launch_pong():
            try:
                pong_path = os.path.join(BASE_DIR, "neural_grid_pong.py")
                if not os.path.exists(pong_path):
                    response_queue.put(("system", "[ERROR] neural_grid_pong.py not found in NEURAL_GRID folder."))
                    return
                subprocess.Popen([sys.executable, pong_path])
            except Exception as e:
                response_queue.put(("system", f"[ERROR] Could not launch pong: {e}"))
        threading.Thread(target=_launch_pong, daemon=True).start()
        return "[SYSTEM] Launching PONG... get ready."

    elif cmd == "theme" or cmd.startswith("theme "):
        parts = cmd.split()
        if len(parts) == 1:
            theme_list = "\n".join([f"  /theme {k:<10} – {v['name']}" for k, v in THEMES.items()])
            return f"""╔══════════════════════════════════════════════════════════╗
║                    AVAILABLE THEMES                      ║
╚══════════════════════════════════════════════════════════╝

Current: {THEMES[current_theme]['name']}

{theme_list}

Usage: /theme <name>  e.g. /theme amber"""
        theme_name = parts[1].lower()
        if apply_theme(theme_name):
            return f"[SYSTEM] Theme changed to {THEMES[theme_name]['name']}"
        else:
            valid = ", ".join(THEMES.keys())
            return f"[ERROR] Unknown theme '{theme_name}'\nValid themes: {valid}"

    elif cmd == "sysinfo":
        ram_gb, cpu_count, ram_used, ram_avail, cpu_pct = get_system_info()
        return f"""╔══════════════════════════════════════════════════════════╗
║                    SYSTEM STATUS                         ║
╚══════════════════════════════════════════════════════════╝
RAM Total:  {ram_gb:.1f} GB
RAM Used:   {ram_used:.1f} GB
RAM Free:   {ram_avail:.1f} GB
CPU Cores:  {cpu_count}
CPU Usage:  {cpu_pct:.1f}%
USB Path:   {BASE_DIR}
Models:     {MODELS_DIR}
Logs:       {CHAT_LOGS_DIR}"""

    elif cmd == "version":
        ram_gb, cpu_count, ram_used, ram_avail, cpu_pct = get_system_info()
        model_name = MODELS[current_model_tier]["name"] if current_model_tier else "None"
        voice_status = "ON" if voice_enabled else "OFF"
        tts_status = "Available" if tts_available else "Not available"
        message_count = max(0, len(messages) - 1)
        return f"""╔══════════════════════════════════════════════════════════╗
║                    NEURAL_GRID INFO                      ║
╚══════════════════════════════════════════════════════════╝

Version:   {VERSION} ({BUILD_DATE})
Mode:      {current_mode.upper()}
Model:     {model_name}
Context:   {message_count}/{MAX_MESSAGES} messages in memory

System:    {ram_gb:.1f}GB RAM | {cpu_count} CPU cores
Voice:     {voice_status} ({tts_status})
USB Path:  {BASE_DIR}
Logs:      {CHAT_LOGS_DIR}

Built with llama-cpp-python + Qwen GGUF models
100% offline — no internet required"""
    
    elif cmd in ["quit", "exit", "stop"]:
        def _shutdown():
            chat_box.config(state=tk.NORMAL)
            chat_box.insert(tk.END, "[SYSTEM] Shutting down...\n")
            chat_box.see(tk.END)
            chat_box.config(state=tk.DISABLED)
            root.after(800, root.quit)
        root.after(0, _shutdown)
        return ""
    
    elif cmd == "help":
        return """╔══════════════════════════════════════════════════════════╗
║                    AVAILABLE COMMANDS                    ║
╚══════════════════════════════════════════════════════════╝

MODEL SELECTION:
/fast           – Fast model (3B)
/balanced       – Balanced model (8B)
/deep           – Deep model (14B)
/models         – Show available models

MODES:
/survivalmode   – Wilderness survival & medical expert
/normal         – Standard conversational mode
/pong           – Play pong against GRID companion

UTILITIES:
/voice          – Toggle voice mode (AI speaks responses)
/theme          – Change color theme (/theme for list)
/clear          – Clear chat history
/reset          – Reset conversation
/save           – Save chat log
/sysinfo        – Show RAM, CPU, and path info
/version        – Show version & system info
/help           – Show this list
/quit or /exit  – Exit application

TIPS:
• Spell-check active - click suggestions to correct
• Model switching resets conversation
• Voice mode works offline
• 100% offline"""
    
    else:
        return f"[ERROR] Unknown: /{cmd}\nType /help"

# ────────────────────────────────────────────────
# INFERENCE (STREAMING)
# ────────────────────────────────────────────────
def run_inference(user_message):
    global messages, is_generating, stop_generation

    is_generating = True
    stop_generation = False

    # Guard against race condition: if model was unloaded between send_prompt's
    # model_loaded check and this thread starting, bail out cleanly without
    # corrupting the message history.
    if llm is None:
        response_queue.put(("error", "[ERROR] Model not ready. Please wait for loading to complete."))
        is_generating = False
        return

    messages.append({"role": "user", "content": user_message})

    try:
        full_response = ""
        response_queue.put(("stream_start", ""))

        for chunk in llm.create_chat_completion(
            messages,
            max_tokens=1024,
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.15,
            stop=["User:", "USER:", "\n\n\n"],
            stream=True
        ):
            if stop_generation:
                break

            delta = chunk["choices"][0].get("delta", {})
            token = delta.get("content", "")
            if token:
                full_response += token
                response_queue.put(("stream_token", token))

        clean = clean_response(full_response)
        messages.append({"role": "assistant", "content": clean})
        trim_context()
        response_queue.put(("stream_end", clean))

    except Exception as e:
        # Remove the orphaned user message so history stays paired (user+assistant).
        # Without this, the next inference sees an unpaired user turn which confuses
        # the model and can cause it to generate as if it were the user.
        if messages and messages[-1]["role"] == "user":
            messages.pop()
        response_queue.put(("error", f"[ERROR] {str(e)}"))
    finally:
        is_generating = False

def check_response_queue():
    input_reenabled = False
    try:
        while True:
            status, data = response_queue.get_nowait()

            if status == "stream_start":
                now = datetime.now().strftime("%H:%M")
                chat_box.config(state=tk.NORMAL)
                chat_box.insert(tk.END, f"[{now}] AI: ", "ai_tag")
                chat_box.config(state=tk.DISABLED)

            elif status == "stream_token":
                chat_box.config(state=tk.NORMAL)
                chat_box.insert(tk.END, data, "ai_text")
                chat_box.see(tk.END)
                chat_box.config(state=tk.DISABLED)

            elif status == "stream_end":
                chat_box.config(state=tk.NORMAL)
                chat_box.insert(tk.END, "\n" + "─" * 80 + "\n", "divider_tag")
                chat_box.see(tk.END)
                chat_box.config(state=tk.DISABLED)
                if not input_reenabled:
                    enable_input()
                    input_reenabled = True
                update_header()
                if voice_enabled:
                    threading.Thread(target=speak_text, args=(data,), daemon=True).start()
                # Don't return — drain any remaining queued system messages

            elif status == "system":
                chat_box.config(state=tk.NORMAL)
                chat_box.insert(tk.END, f"{data}\n", "command_tag")
                chat_box.see(tk.END)
                chat_box.config(state=tk.DISABLED)
                # No reschedule here — the while True loop above drains all
                # queued messages in one pass; adding root.after here would
                # cause double-scheduling when multiple system messages arrive.

            elif status == "error":
                now = datetime.now().strftime("%H:%M")
                chat_box.config(state=tk.NORMAL)
                chat_box.insert(tk.END, f"[{now}] ", "divider_tag")
                chat_box.insert(tk.END, f"{data}\n", "command_tag")
                chat_box.insert(tk.END, "─" * 80 + "\n", "divider_tag")
                chat_box.see(tk.END)
                chat_box.config(state=tk.DISABLED)
                if not input_reenabled:
                    enable_input()
                    input_reenabled = True
                # Don't return — drain any remaining queued messages

    except Empty:
        # BUG FIX: always re-schedule if generating; also do a final drain pass
        # once is_generating flips False so late-arriving tokens are never lost.
        if is_generating:
            root.after(30, check_response_queue)
        elif not input_reenabled:
            # Generation finished between the last reschedule and now — re-enable input
            enable_input()
            update_header()

# ────────────────────────────────────────────────
# UI INPUT
# ────────────────────────────────────────────────
def send_prompt(event=None):
    global stop_generation

    if not model_loaded:
        return

    # If generating, treat Enter/Send as stop
    if is_generating:
        stop_generation = True
        return

    hide_suggestions()

    user_input = input_box.get().strip()
    if not user_input:
        return

    input_box.delete(0, tk.END)

    now = datetime.now().strftime("%H:%M")
    chat_box.config(state=tk.NORMAL)

    chat_box.insert(tk.END, f"[{now}] > USER: ", "user_tag")
    chat_box.insert(tk.END, f"{user_input}\n", "user_text")
    chat_box.see(tk.END)

    if user_input.startswith("/"):
        command_text = user_input[1:].strip()
        # BUG FIX: wrap in try/finally so chat_box is always re-disabled
        try:
            response = handle_command(command_text)
        except Exception as exc:
            response = f"[ERROR] Command failed: {exc}"

        if response:
            chat_box.insert(tk.END, f"[{now}] ", "divider_tag")
            chat_box.insert(tk.END, f"{response}\n", "command_tag")
            chat_box.insert(tk.END, "─" * 80 + "\n", "divider_tag")
            chat_box.see(tk.END)

        chat_box.config(state=tk.DISABLED)
        return

    chat_box.config(state=tk.DISABLED)
    disable_input()

    threading.Thread(target=run_inference, args=(user_input,), daemon=True).start()
    root.after(30, check_response_queue)

# Stop-button colors are theme-independent (always red — signals danger/stop)
_STOP_BG       = "#330000"
_STOP_BG_HOVER = "#440000"
_STOP_FG       = "#ff3333"

def disable_input():
    t = THEMES[current_theme]
    input_box.config(state=tk.DISABLED, bg=t["bg_input_dis"])
    send_btn.config(text="■ STOP", bg=_STOP_BG, fg=_STOP_FG)

def enable_input():
    t = THEMES[current_theme]
    input_box.config(state=tk.NORMAL, bg=t["bg_input"])
    send_btn.config(text="SEND ▶", bg=t["bg_btn"], fg=t["fg_main"])
    input_box.focus()

# ────────────────────────────────────────────────
# UI UPDATES
# ────────────────────────────────────────────────
def update_status(message):
    def _update():
        chat_box.config(state=tk.NORMAL)
        chat_box.insert(tk.END, f"{message}\n")
        chat_box.see(tk.END)
        chat_box.config(state=tk.DISABLED)
    root.after(0, _update)

def update_header():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    mode_display = current_mode.upper()
    if current_mode == "survival":
        mode_display = "⚠ " + mode_display + " ⚠"
    
    voice_indicator = " 🔊" if voice_enabled else ""
    
    # Calculate recall memory (message count excluding system prompt)
    if messages:
        message_count = max(0, len(messages) - 1)  # Exclude system prompt, min 0
    else:
        message_count = 0
    
    max_messages = MAX_MESSAGES
    
    # Create visual bar (10 blocks total)
    filled = min(10, int((message_count / max_messages) * 10)) if max_messages > 0 else 0  # Cap at 10
    empty = 10 - filled
    memory_bar = "▓" * filled + "░" * empty

    # Warning label when almost full or full
    if message_count >= max_messages:
        memory_label = "⚠ MEMORY FULL"
    elif message_count >= max_messages - 4:
        memory_label = f"⚠ ALMOST FULL ({message_count}/{max_messages})"
    else:
        memory_label = f"{message_count}/{max_messages}"
    
    model_name = MODELS[current_model_tier]["name"] if current_model_tier else "Loading..."
    header.config(text=f"NEURAL_GRID v{VERSION} | {model_name} | MODE: {mode_display}{voice_indicator} | Recall: {memory_bar} ({memory_label}) | {now}")

def _bind_send_btn_hover():
    """Re-bind send button hover colors using the current theme (call after any theme change)."""
    t = THEMES[current_theme]
    send_btn.bind(
        "<Enter>",
        lambda e: send_btn.config(bg=t["bg_btn_hover"]) if send_btn.cget("text") == "SEND ▶" else send_btn.config(bg=_STOP_BG_HOVER)
    )
    send_btn.bind(
        "<Leave>",
        lambda e: send_btn.config(bg=t["bg_btn"]) if send_btn.cget("text") == "SEND ▶" else send_btn.config(bg=_STOP_BG)
    )
    # NOTE: Do NOT call update_header() or schedule periodic_header_update() here.
    # This function is called on every theme change; doing so would stack timers and
    # cause redundant header refreshes. Those are handled in startup_sequence() only.

_header_update_after_id = None

def periodic_header_update():
    """Refresh the header clock every 60 seconds. Only one timer chain should exist at a time."""
    global _header_update_after_id
    update_header()
    _header_update_after_id = root.after(60000, periodic_header_update)

# ────────────────────────────────────────────────
# UI SETUP
# ────────────────────────────────────────────────
root = tk.Tk()
root.title(f"NEURAL_GRID v{VERSION}")
root.configure(bg="#0a0a0a")
root.geometry("1000x720")
root.minsize(800, 600)  # Minimum window size to prevent UI breaking

last_window_size = [1000, 720]

scanline = tk.Canvas(root, bg="#0a0a0a", highlightthickness=0)
scanline.place(x=0, y=0, relwidth=1, relheight=1)

def draw_scanlines():
    draw_scanlines_themed(THEMES[current_theme]["bg_scanline"])

_scanline_after_id = None

def on_window_resize(event):
    global last_window_size, _scanline_after_id
    current_size = [root.winfo_width(), root.winfo_height()]
    if current_size != last_window_size:
        hide_suggestions()
        last_window_size = current_size
        if _scanline_after_id:
            root.after_cancel(_scanline_after_id)
        _scanline_after_id = root.after(150, draw_scanlines)

root.bind("<Configure>", on_window_resize)

header = tk.Label(
    root,
    text="",
    bg="#001100",
    fg="#00ff41",
    font=("Courier New", 10, "bold"),
    anchor="w",
    padx=10
)
header.pack(fill=tk.X)

chat_box = scrolledtext.ScrolledText(
    root,
    bg="#000000",
    fg="#00ff41",
    insertbackground="#00ff41",
    font=("Courier New", 11),
    state=tk.DISABLED,
    wrap=tk.WORD,
    relief="flat",
    highlightthickness=2,
    highlightbackground="#003300",
    highlightcolor="#00aa33",
    bd=0
)
chat_box.pack(expand=True, fill=tk.BOTH, padx=12, pady=(4, 0))

chat_box.tag_config("user_tag", foreground="#00ffff", font=("Courier New", 11, "bold"))
chat_box.tag_config("user_text", foreground="#ffff99")
chat_box.tag_config("ai_tag", foreground="#00ff41", font=("Courier New", 11, "bold"))
chat_box.tag_config("ai_text", foreground="#39ff14")
chat_box.tag_config("command_tag", foreground="#ff9933")
chat_box.tag_config("divider_tag", foreground="#004400")

input_frame = tk.Frame(root, bg="#0a0a0a", bd=2, relief="flat")
input_frame.pack(fill=tk.X, padx=12, pady=(0, 12))

prompt_label = tk.Label(
    input_frame,
    text=">",
    bg="#0a0a0a",
    fg="#00ff41",
    font=("Courier New", 14, "bold")
)
prompt_label.pack(side=tk.LEFT, padx=(0, 4))

input_box = tk.Entry(
    input_frame,
    bg="#002200",
    fg="#00ff41",
    insertbackground="#00ff41",
    font=("Courier New", 12),
    relief="flat",
    highlightthickness=2,
    highlightbackground="#003300",
    highlightcolor="#00cc44",
    state=tk.DISABLED
)
input_box.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 6))
input_box.bind("<Return>", send_prompt)
input_box.bind("<KeyRelease>", check_spelling)

send_btn = tk.Button(
    input_frame,
    text="SEND ▶",
    bg="#003300",
    fg="#00ff41",
    font=("Courier New", 10, "bold"),
    relief="flat",
    cursor="hand2",
    width=10,
    command=send_prompt
)
send_btn.pack(side=tk.LEFT)
# Hover colors are set/refreshed by _bind_send_btn_hover() which is called after
# _bind_send_btn_hover is defined (during startup_sequence → apply_theme path).
# Set initial bindings here with default green colors.
send_btn.bind("<Enter>", lambda e: send_btn.config(bg="#004400") if send_btn.cget("text") == "SEND ▶" else send_btn.config(bg="#440000"))
send_btn.bind("<Leave>", lambda e: send_btn.config(bg="#003300") if send_btn.cget("text") == "SEND ▶" else send_btn.config(bg="#330000"))

# Status bar at very bottom
status_bar = tk.Label(
    root,
    text=f"USB: {BASE_DIR}  |  Models: {MODELS_DIR}  |  Logs: {CHAT_LOGS_DIR}  |  /help for commands",
    bg="#001100",
    fg="#005500",
    font=("Courier New", 8),
    anchor="w",
    padx=10
)
status_bar.pack(fill=tk.X, side=tk.BOTTOM)

# ────────────────────────────────────────────────
# STARTUP
# ────────────────────────────────────────────────
def startup_sequence():
    global messages
    
    chat_box.config(state=tk.NORMAL)
    chat_box.insert(tk.END, f"[*] USB: {BASE_DIR}\n")
    chat_box.insert(tk.END, f"[*] Models: {MODELS_DIR}\n")
    chat_box.insert(tk.END, f"[*] Logs: {CHAT_LOGS_DIR}\n\n")
    
    recommended_tier, reason, ram_gb, cpu_count = recommend_model()
    
    chat_box.insert(tk.END, f"[*] System: {ram_gb:.1f}GB RAM, {cpu_count} cores\n")
    chat_box.insert(tk.END, f"[*] {reason}\n\n")
    
    if recommended_tier is None:
        chat_box.insert(tk.END, "\n[CRITICAL] No models found!\n", "command_tag")
        chat_box.insert(tk.END, f"Place .gguf files in:\n  {MODELS_DIR}\n", "command_tag")
        chat_box.config(state=tk.DISABLED)
        return
    
    chat_box.insert(tk.END, "[*] Quantum link established\n")
    chat_box.insert(tk.END, "[+] Firewall bypassed\n")
    chat_box.insert(tk.END, f"[*] NEURAL_GRID v{VERSION} ready\n\n")
    chat_box.config(state=tk.DISABLED)
    
    messages = [{"role": "system", "content": PROMPTS[current_mode]}]
    
    threading.Thread(target=load_model_async, args=(recommended_tier,), daemon=True).start()
    
    update_header()
    periodic_header_update()
    draw_scanlines()

root.after(500, startup_sequence)
root.mainloop()