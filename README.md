# ⚡ NEURAL_GRID v1.0

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
- **Survival mode** — dedicated wilderness/emergency medical expert persona
- **Voice output** — Windows SAPI TTS reads responses aloud (offline)
- **Spell check** — live suggestions as you type
- **Context memory** — tracks up to 24 messages with a visual memory bar
- **Chat logging** — saves conversations as `.json` and `.txt`
- **Cyberpunk UI** — green-on-black terminal aesthetic with scanline overlay

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

To swap in a custom model, open `neural_grid_usbv6.py` and find the `MODELS` dictionary near the top of the file:

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

**Tips for picking a model:**
- Q4_K_M quantization is the sweet spot — good quality, reasonable size
- Check the model's RAM requirement before downloading — larger models need more
- 7B–8B models run well on most modern PCs with 8GB+ RAM
- 13B–14B models need 10GB+ RAM to run smoothly

---

## USB Structure

```
USB Drive (e.g. E:\)
├── neural_grid_usbv6.py     ← Main application
├── neural_gridv6.bat        ← Launcher (double-click to run)
├── models\
│   ├── Qwen2.5-3B-Q4_K_M.gguf
│   ├── Qwen3-8B-Q4_K_M.gguf
│   └── Qwen2.5-14B-Q4_K_M.gguf
├── chatlogs\                ← Auto-created on first save
└── WinPython\               ← Portable Python runtime
    └── WPy64-31241\
        └── python-3.12.4.amd64\
```

---

## Setup

### 1. Get WinPython
Download [WinPython 3.12](https://winpython.github.io/) and extract it to your USB drive at `\WinPython\`.

### 2. Install dependencies
Open the WinPython command prompt and run:
```bash
pip install llama-cpp-python pywin32 psutil pyspellchecker
```

### 3. Download a model
Grab at least one Qwen GGUF model from Hugging Face and place it in the `models\` folder on your USB. The balanced 8B model is recommended for most use cases.

### 4. Launch
Double-click `neural_gridv6.bat` — it auto-detects the drive letter, so it works on any PC regardless of what letter Windows assigns the USB.

---

## Commands

| Command | Description |
|---------|-------------|
| `/fast` | Switch to fast 3B model |
| `/balanced` | Switch to balanced 8B model |
| `/deep` | Switch to deep 14B model |
| `/models` | Show available models and system info |
| `/survivalmode` | Activate wilderness/emergency medical expert |
| `/normal` | Return to standard chat mode |
| `/voice` | Toggle text-to-speech (offline, Windows SAPI) |
| `/clear` | Clear chat window and reset context |
| `/reset` | Reset conversation context |
| `/save` | Save chat log to `chatlogs\` |
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
