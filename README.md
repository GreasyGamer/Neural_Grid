# ⚡ NEURAL_GRID v1.1

> A portable, fully offline AI assistant that runs from a USB drive on any Windows PC.  
> No internet. No cloud. No data collection. Just raw local inference.  
> Runs Qwen out of the box — swap in any GGUF-compatible model your PC can handle.

![Python](https://img.shields.io/badge/Python-3.12-green?style=flat-square&logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows-blue?style=flat-square&logo=windows)
![Offline](https://img.shields.io/badge/Mode-100%25%20Offline-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-orange?style=flat-square)

---

## What is this?

NEURAL_GRID is a self-contained AI assistant built to run completely offline from a USB drive. Plug it into any Windows machine, double-click the launcher, and you have a fully functional local LLM terminal — no installation, no accounts, no internet required.

Built with a cyberpunk terminal aesthetic and designed for portability, privacy, and survival.

---

## Features

- **100% offline** — no API keys, no cloud, no telemetry
- **Portable** — runs entirely from a USB drive on any Windows PC
- **Bring your own model** — ships with Qwen but works with any GGUF-compatible model
- **Three model tiers** — auto-selects based on host machine RAM, swap models mid-session with a command
- **Streaming responses** — AI output appears token by token, no waiting for full response
- **Stop generation** — cancel a response mid-stream with the STOP button or Enter key
- **Survival mode** — dedicated wilderness/emergency medical expert persona
- **Voice output** — Windows SAPI TTS reads responses aloud (offline)
- **Spell check** — live suggestions as you type
- **Context memory** — tracks up to 24 messages with a visual memory bar
- **Chat logging** — saves conversations as `.json` and `.txt`
- **Themes** — 5 built-in color themes, switch instantly with `/theme`
- **GRID Pong** — play pong against your AI companion with live LLM banter, launch with `/pong`

---

## Models

NEURAL_GRID uses [Qwen GGUF](https://huggingface.co/Qwen) models via `llama-cpp-python` out of the box, with three tiers that auto-select based on available RAM:

| Tier | Model | RAM Required | Best For |
|------|-------|-------------|----------|
| Fast | Qwen2.5-3B-Q4_K_M | ~4GB | Older or low-spec PCs |
| Balanced | Qwen3-8B-Q4_K_M | ~6GB | Most machines (recommended) |
| Deep | Qwen2.5-14B-Q4_K_M | ~10GB | High-spec machines |

### Using a different model

NEURAL_GRID supports **any GGUF-compatible model** — not just Qwen. If your PC can run it, you can use it. Popular alternatives include Mistral, LLaMA, Phi, Gemma, and others available on [Hugging Face](https://huggingface.co/models?library=gguf).

To swap in a custom model, open `neural_grid_usbv1.py` and find the `MODELS` dictionary near the top of the file:

```python
MODELS = {
    "fast": {
        "name": "Qwen2.5-3B-Q4_K_M",
        "file": "Qwen2.5-3B-Q4_K_M.gguf",
        "path": os.path.join(MODELS_DIR, "Qwen2.5-3B-Q4_K_M.gguf"),
        "ram_required": 4,
        "description": "Fast & efficient - good for older/slower PCs"
    },
    ...
}
```

Replace the `file`, `path`, `ram_required`, and `description` fields for whichever tier you want to swap. Drop the `.gguf` file into the `models\` folder on your USB and you're done. You can switch between loaded models mid-session using `/fast`, `/balanced`, or `/deep`.

**Note on "thinking" models:** Some models (like Qwen3 and others built on reasoning architectures) output internal `<think>...</think>` blocks before their response. NEURAL_GRID filters these automatically for the built-in balanced tier, but if you swap in a third-party thinking model and see `<think>` tags appearing in the chat, that's why. Stick to non-thinking variants (usually labeled `instruct` rather than `thinking` or `reasoner`) if you want clean output without extra config.

**Tips for picking a model:**
- Q4_K_M quantization is the sweet spot — good quality, reasonable size
- Check the model's RAM requirement before downloading — larger models need more
- 7B–8B models run well on most modern PCs with 8GB+ RAM
- 13B–14B models need 10GB+ RAM to run smoothly

---

## USB Structure

```
USB Drive (e.g. E:\)
├── setup.bat                    ← Run this first
└── NEURAL_GRID\
    ├── launch.bat               ← Launch NEURAL_GRID (double-click to run)
    ├── neural_grid_usbv1.py     ← Main application
    ├── neural_grid_pong.py      ← Pong companion game (launched via /pong)
    ├── requirements.txt         ← Dependency list
    ├── models\                  ← Place your .gguf model files here
    │   ├── Qwen2.5-3B-Q4_K_M.gguf
    │   ├── Qwen3-8B-Q4_K_M.gguf
    │   └── Qwen2.5-14B-Q4_K_M.gguf
    ├── chatlogs\                ← Chat logs saved here
    └── WinPython\               ← Portable Python runtime
        └── WPy64-31241\
            └── python-3.12.4.amd64\
```

---

## Setup

### ⚡ Quick Setup (Recommended)

1. Copy all files from this repo to your USB drive — keep `setup.bat` at the root and everything else inside a `NEURAL_GRID\` folder
2. Download [WinPython 3.12](https://winpython.github.io/) and extract it into `NEURAL_GRID\WinPython\`
3. Double-click `setup.bat` from the root of the USB
4. The script will create your folder structure, install all dependencies, and give you direct download links for the models
5. Download at least one model, place the `.gguf` file in `NEURAL_GRID\models\`
6. Double-click `NEURAL_GRID\launch.bat` to start

> `setup.bat` only needs to be run once. After that just use `launch.bat`.

---

### 🔧 Manual Setup (Advanced)

If you prefer to set things up yourself:

**1. Get WinPython**
Download [WinPython 3.12](https://winpython.github.io/) and extract it to your USB at `NEURAL_GRID\WinPython\`.

**2. Install dependencies**
Open the WinPython command prompt and run:
```bash
pip install llama-cpp-python pywin32 psutil pyspellchecker
```

**3. Create folders**
Inside `NEURAL_GRID\` create two folders manually:
```
NEURAL_GRID\models\
NEURAL_GRID\chatlogs\
```

**4. Download a model**
Grab at least one Qwen GGUF model from Hugging Face and place it in `NEURAL_GRID\models\`. The balanced 8B model is recommended for most use cases.

| Model | Link |
|-------|------|
| Qwen2.5-3B (Fast) | [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF) |
| Qwen3-8B (Balanced) | [Hugging Face](https://huggingface.co/Qwen/Qwen3-8B-GGUF) |
| Qwen2.5-14B (Deep) | [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF) |

Download the `Q4_K_M` version — best balance of quality and file size.

**5. Launch**
Double-click `NEURAL_GRID\launch.bat` — it auto-detects the drive letter so it works on any PC regardless of what letter Windows assigns the USB.

---

## Commands

| Command | Description |
|---------|-------------|
| `/fast` | Switch to fast 3B model |
| `/balanced` | Switch to balanced 8B model |
| `/deep` | Switch to deep 14B model |
| `/models` | Show available models and system info |
| `/pong` | Launch GRID Pong companion game |
| `/survivalmode` | Activate wilderness/emergency medical expert |
| `/normal` | Return to standard chat mode |
| `/voice` | Toggle text-to-speech (offline, Windows SAPI) |
| `/theme` | List available themes |
| `/theme <name>` | Switch color theme (green/amber/blue/red/white) |
| `/clear` | Clear chat window and reset context |
| `/reset` | Reset conversation context |
| `/save` | Save chat log to `chatlogs\` |
| `/sysinfo` | Show RAM, CPU usage, and paths |
| `/version` | Show version, model, system info |
| `/help` | Show all commands |
| `/quit` | Exit |

---

## Memory System

NEURAL_GRID tracks conversation context with a visual bar in the header:

```
Recall: ▓▓▓▓▓░░░░░ (12/24)
```

When memory fills up, the oldest messages are purged and the bar rolls back — the model keeps the most recent 16 exchanges and rebuilds from there.

---

## GRID Pong

Type `/pong` inside NEURAL_GRID to launch a pong game against your AI companion GRID.

GRID isn't just a scoreboard — the local LLM watches the game and generates friendly banter in real time based on what's happening. Every comment is freshly generated, so it never gets old.

**Controls**

| Key | Action |
|-----|--------|
| W / ↑ | Move paddle up |
| S / ↓ | Move paddle down |
| Space | Serve / restart |
| Escape | Quit |

**When GRID talks:**
- Game start — a warm welcome
- Every point scored — reacts based on who scored and the score gap
- Long rallies — gets excited about the back and forth
- Game over — celebrates your win or stays humble about theirs

GRID is your companion out there, not your opponent. Friendly, funny, never mean. The banter generates on a background thread so the game never pauses — comments pop up naturally between points like a friend reacting from the sideline.

If no model is found, the game still runs fine — GRID just stays quiet.

---

## Why offline?

Modern "smart" devices ship with Wi-Fi modules, telemetry, and persistent connections to manufacturer servers — even when you don't use those features. NEURAL_GRID was built on the opposite philosophy: your hardware, your data, your control. Nothing leaves the machine.

---

## Built With

- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) — local LLM inference
- [Qwen models](https://huggingface.co/Qwen) — by Alibaba Cloud (GGUF quantized)
- [WinPython](https://winpython.github.io/) — portable Python for Windows
- [tkinter](https://docs.python.org/3/library/tkinter.html) — GUI
- [pywin32](https://github.com/mhammond/pywin32) — Windows SAPI TTS

---

## Disclaimer

This project was built with AI assistance (Claude by Anthropic). The concept, design decisions, and direction are original. Models are third-party and subject to their own licenses — check Qwen's license on Hugging Face before commercial use.

---

*Plug in. Boot up. Stay offline.*
