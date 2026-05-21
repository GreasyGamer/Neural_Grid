import tkinter as tk
import random
import threading
import os
import sys

# ────────────────────────────────────────────────
# NEURAL_GRID PONG — Companion Edition
# A friendly game for when you're out there alone.
# ────────────────────────────────────────────────

# ── Find the model (same logic as main app) ──────
def find_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # Walk up from the script's own directory looking for a NEURAL_GRID folder,
    # so it works on Windows, Linux, and Mac without hardcoded separators.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ng_dir = os.path.join(os.path.splitdrive(script_dir)[0] + os.sep, "NEURAL_GRID")
    if os.path.exists(ng_dir):
        return ng_dir
    return script_dir

BASE_DIR   = find_base_dir()
MODELS_DIR = os.path.join(BASE_DIR, "models")

MODELS = {
    "fast": {
        "name": "Qwen2.5-3B-Q4_K_M",
        "path": os.path.join(MODELS_DIR, "Qwen2.5-3B-Q4_K_M.gguf"),
        "ram_required": 4,
    },
    "balanced": {
        "name": "Qwen3-8B-Q4_K_M",
        "path": os.path.join(MODELS_DIR, "Qwen3-8B-Q4_K_M.gguf"),
        "ram_required": 6,
    },
    "deep": {
        "name": "Qwen2.5-14B-Q4_K_M",
        "path": os.path.join(MODELS_DIR, "Qwen2.5-14B-Q4_K_M.gguf"),
        "ram_required": 10,
    },
}

# ── Game constants ────────────────────────────────
W, H        = 900, 600
PAD_W, PAD_H = 14, 80
BALL_SIZE    = 12
BALL_SPEED   = 5
AI_SPEED     = 4
AI_MISTAKE   = 0.08   # Probability (0–1) AI skips a frame — makes it beatable
MAX_BALL_SPEED = 12  # Cap to prevent tunneling through paddles at high rally counts
SCORE_TO_WIN = 7

# ── Colors (cyberpunk terminal palette) ──────────
BG          = "#000000"
SCANLINE    = "#0a0a0a"
GRID_COLOR  = "#071407"
NET_COLOR   = "#003300"
PAD_PLAYER  = "#00ff41"
PAD_AI      = "#39ff14"
BALL_COLOR  = "#00ffff"
SCORE_COLOR = "#00ff41"
TEXT_DIM    = "#005500"
TEXT_BRIGHT = "#00ff41"
TEXT_CYAN   = "#00ffff"
TEXT_ORANGE = "#ff9933"
BANTER_COLOR = "#ffff99"

# ── LLM banter system ────────────────────────────
llm          = None
llm_loaded   = False
banter_lock      = threading.Lock()   # Protects current_banter and banter_history
banter_gate      = threading.Lock()   # Used to atomically check-and-set banter_generating
banter_generating = threading.Event()  # Set while LLM is running — prevents concurrent calls
current_banter = ""
banter_history = []  # Rolling history of recent banter to avoid repetition
MAX_BANTER_HISTORY = 6

SYSTEM_PROMPT = (
    "You are GRID, a fun AI companion playing pong with a friend. "
    "You are their only company right now — maybe out in the wilderness far from other people. "
    "Be friendly and funny. You can be lightly competitive and playful — a little trash talk is fine as long as it is good natured. "
    "Never be genuinely mean. Keep it to ONE short punchy sentence. No quotes around your response."
)

GAME_START_OPENERS = [
    "The pong game is starting. Welcome your friend with something energetic.",
    "The pong game is starting. Say something cocky but friendly to open.",
    "The pong game is starting. Make a joke about being an AI playing pong.",
    "The pong game is starting. Say something mysterious and dramatic to open.",
    "The pong game is starting. Give a quick trash-talk opener, keep it playful.",
    "The pong game is starting. Say something warm and excited to kick things off.",
    "The pong game is starting. Reference being out in the wilderness together somehow.",
    "The pong game is starting. Open with a weird fun fact or observation.",
]

EVENTS = {
    "game_start":      "",  # Randomly selected at call time
    "player_scores":   "Your friend just scored against you. The score is noted below. React accordingly.",
    "ai_scores":       "YOU just scored against your friend. The score is noted below. If you are winning say something lightly competitive. If it is close just be playful.",
    "player_winning":  "Your friend is winning. The score is noted below. Be encouraging but maybe a little competitive about catching up.",
    "ai_winning":      "You are winning. The score is noted below. Be lightly smug but still friendly.",
    "close_game":      "The score is very close. The score is noted below. React to the tension.",
    "player_wins":     "Your friend just won the whole game. The score is noted below. Congratulate them warmly, maybe act a little dramatic about losing.",
    "ai_wins":         "You just won the game. The score is noted below. Be a little smug but mostly humble and funny.",
    "long_rally":      "There has been a long back and forth rally. React with excitement.",
}

def load_llm_background():
    global llm, llm_loaded
    try:
        from llama_cpp import Llama
        import psutil
        import multiprocessing

        ram_gb = psutil.virtual_memory().total / (1024**3)

        # Pick the best model that actually exists on disk
        chosen_path = None
        for tier in ["deep", "balanced", "fast"]:
            path = MODELS[tier]["path"]
            if os.path.exists(path) and ram_gb >= MODELS[tier]["ram_required"]:
                chosen_path = path
                break  # Stop at best viable tier

        # Fallback — just use any model that exists
        if not chosen_path:
            for tier in ["fast", "balanced", "deep"]:
                if os.path.exists(MODELS[tier]["path"]):
                    chosen_path = MODELS[tier]["path"]
                    break

        if not chosen_path:
            return

        llm = Llama(
            model_path=chosen_path,
            n_ctx=512,
            n_threads=max(1, multiprocessing.cpu_count() - 1),
            n_gpu_layers=0,
            n_batch=256,
            verbose=False
        )
        llm_loaded = True
    except Exception:
        llm_loaded = False

def generate_banter(event_key, context=""):
    if not llm_loaded or llm is None:
        return
    # Use a dedicated gate lock to atomically check-and-set banter_generating
    if not banter_gate.acquire(blocking=False):
        return  # Another thread is already at the gate
    already_running = banter_generating.is_set()
    banter_generating.set()
    banter_gate.release()
    if already_running:
        return  # LLM already running — drop this request
    def _gen():
        global current_banter, banter_history
        if not llm_loaded or llm is None:
            banter_generating.clear()
            return
        try:
            if event_key == "game_start":
                base_prompt = random.choice(GAME_START_OPENERS)
            else:
                base_prompt = EVENTS.get(event_key, "Something interesting just happened in the game. React briefly.")
            prompt = f"{base_prompt}{(' ' + context) if context else ''}"
            # Build messages with rolling history so the model doesn't repeat itself
            with banter_lock:
                history_snapshot = list(banter_history)
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for past in history_snapshot:
                messages.append({"role": "assistant", "content": past})
            messages.append({"role": "user", "content": prompt})
            output = llm.create_chat_completion(
                messages=messages,
                max_tokens=60,
                temperature=0.92,
                top_p=0.9,
                top_k=40,
                repeat_penalty=1.3,
            )
            text = output["choices"][0]["message"]["content"].strip()
            text = text.strip('"').strip("'")
            with banter_lock:
                banter_history.append(text)
                if len(banter_history) > MAX_BANTER_HISTORY:
                    banter_history.pop(0)
                current_banter = f"GRID: {text}"
        except Exception:
            pass
        finally:
            banter_generating.clear()
    threading.Thread(target=_gen, daemon=True).start()

# ── Main game class ───────────────────────────────
class PongGame:
    def __init__(self, root):
        self.root = root
        self.root.title("NEURAL_GRID — PONG")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=W, height=H, bg=BG,
                                highlightthickness=0)
        self.canvas.pack()

        # Banter label at bottom
        self.banter_var = tk.StringVar(value="")
        self.banter_label = tk.Label(
            root,
            textvariable=self.banter_var,
            bg=BG,
            fg=BANTER_COLOR,
            font=("Courier New", 11, "italic"),
            wraplength=860,
            justify="center",
            height=2  # Fixed height — prevents long responses from pushing status label off screen
        )
        self.banter_label.pack(pady=(0, 6))

        # Status label
        self.status_var = tk.StringVar(value="Loading GRID companion...")
        self.status_label = tk.Label(
            root,
            textvariable=self.status_var,
            bg=BG,
            fg=TEXT_DIM,
            font=("Courier New", 8),
        )
        self.status_label.pack(pady=(0, 4))

        self.reset_game()
        self.draw_background()

        # Key bindings
        self.root.bind("<w>",      self.move_up)
        self.root.bind("<s>",      self.move_down)
        self.root.bind("<Up>",     self.move_up)
        self.root.bind("<Down>",   self.move_down)
        self.root.bind("<space>",  self.on_space)
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.focus_set()

        # Load LLM in background
        threading.Thread(target=self.load_model, daemon=True).start()

        self.state       = "waiting"   # waiting / playing / scored / gameover
        self.rally_count = 0
        self.last_banter_event = ""
        self._cached_banter = ""       # Banter snapshot refreshed once per second
        self._banter_tick   = 0        # Frame counter for throttling banter reads

        self.show_start_screen()
        self.game_loop()

    def load_model(self):
        load_llm_background()
        if llm_loaded:
            self.root.after(0, lambda: self.status_var.set("GRID is online — Press SPACE to play"))
            self.root.after(0, lambda: generate_banter("game_start"))
        else:
            self.root.after(0, lambda: self.status_var.set("GRID offline (no model found) — Press SPACE to play"))

    def reset_game(self):
        global banter_history, current_banter
        self.player_y  = H // 2 - PAD_H // 2
        self.ai_y      = H // 2 - PAD_H // 2
        self.player_score = 0
        self.ai_score     = 0
        self.last_banter_event = ""
        self._cached_banter = ""
        self._banter_tick   = 0
        banter_history = []  # Reset history each new game
        current_banter = ""
        self.reset_ball()

    def reset_ball(self):
        self.ball_x  = W // 2
        self.ball_y  = H // 2
        angle_y      = random.uniform(-3, 3)
        direction    = random.choice([-1, 1])
        self.ball_vx = BALL_SPEED * direction
        self.ball_vy = angle_y
        self.rally_count = 0
        self.last_banter_event = ""  # Allow long_rally banter to fire each new point

    def draw_background(self):
        # Guard: only draw the static background once. If called again (e.g. on
        # a future resize hook), don't pile up duplicate permanent canvas items.
        if getattr(self, '_background_drawn', False):
            return
        self._background_drawn = True
        # Grid lines
        for x in range(0, W, 60):
            self.canvas.create_line(x, 0, x, H, fill=GRID_COLOR, width=1)
        for y in range(0, H, 60):
            self.canvas.create_line(0, y, W, y, fill=GRID_COLOR, width=1)
        # Scanlines via PhotoImage tile — much faster than hundreds of line objects
        tile = tk.PhotoImage(width=1, height=4)
        tile.put(SCANLINE, to=(0, 0, 1, 1))
        for y in range(0, H, 4):
            self.canvas.create_image(0, y, image=tile, anchor="nw", tags="scanline")
        self.canvas._scanline_tile = tile  # Keep reference to prevent GC
        # Net
        for y in range(0, H, 20):
            self.canvas.create_rectangle(W//2 - 2, y, W//2 + 2, y + 10,
                                          fill=NET_COLOR, outline="", tags="net")

    def show_start_screen(self):
        self.canvas.delete("overlay")
        self.canvas.create_text(W//2, H//2 - 80, text="NEURAL_GRID",
            font=("Courier New", 36, "bold"), fill=TEXT_BRIGHT, tags="overlay")
        self.canvas.create_text(W//2, H//2 - 30, text="P O N G",
            font=("Courier New", 22, "bold"), fill=TEXT_CYAN, tags="overlay")
        self.canvas.create_text(W//2, H//2 + 30,
            text="W / S  or  ↑ / ↓  to move",
            font=("Courier New", 12), fill=TEXT_DIM, tags="overlay")
        self.canvas.create_text(W//2, H//2 + 60,
            text="First to 7 wins",
            font=("Courier New", 12), fill=TEXT_DIM, tags="overlay")
        self.canvas.create_text(W//2, H//2 + 100,
            text="[ SPACE ] to start",
            font=("Courier New", 14, "bold"), fill=TEXT_ORANGE, tags="overlay")
        self.canvas.create_text(W//2, H - 20,
            text="ESC to quit",
            font=("Courier New", 9), fill=TEXT_DIM, tags="overlay")

    def on_space(self, event=None):
        if self.state == "waiting":
            self.canvas.delete("overlay")
            self.state = "playing"
        elif self.state == "scored":
            self.reset_ball()
            self.state = "playing"
        elif self.state == "gameover":
            self.reset_game()
            self.canvas.delete("overlay")
            self.state = "waiting"
            self.show_start_screen()
            self.banter_var.set("")

    def move_up(self, event=None):
        if self.state == "playing":
            self.player_y = max(0, self.player_y - 20)

    def move_down(self, event=None):
        if self.state == "playing":
            self.player_y = min(H - PAD_H, self.player_y + 20)

    def update_ai(self):
        # AI tracks ball with occasional intentional mistakes
        if random.random() < AI_MISTAKE:
            return
        target = self.ball_y - PAD_H // 2
        diff = target - self.ai_y
        # Dead zone — stop jittering when close enough
        if abs(diff) < AI_SPEED:
            return
        if diff > 0:
            self.ai_y = min(H - PAD_H, self.ai_y + AI_SPEED)
        else:
            self.ai_y = max(0, self.ai_y - AI_SPEED)

    def update_ball(self):
        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy

        # Top/bottom bounce
        if self.ball_y <= 0:
            self.ball_y = 0
            self.ball_vy *= -1
        if self.ball_y >= H - BALL_SIZE:
            self.ball_y = H - BALL_SIZE
            self.ball_vy *= -1

        # Player paddle collision (left side)
        px = 30
        if (self.ball_x <= px + PAD_W and
                self.ball_y + BALL_SIZE >= self.player_y and
                self.ball_y <= self.player_y + PAD_H and
                self.ball_vx < 0):
            self.ball_vx = min(MAX_BALL_SPEED, abs(self.ball_vx) + 0.3) 
            hit_pos = (self.ball_y - self.player_y) / PAD_H
            self.ball_vy = (hit_pos - 0.5) * 8
            self.rally_count += 1
            self.check_rally_banter()

        # AI paddle collision (right side)
        ax = W - 30 - PAD_W
        if (self.ball_x + BALL_SIZE >= ax and
                self.ball_y + BALL_SIZE >= self.ai_y and
                self.ball_y <= self.ai_y + PAD_H and
                self.ball_vx > 0):
            self.ball_vx = -min(MAX_BALL_SPEED, abs(self.ball_vx) + 0.3)
            hit_pos = (self.ball_y - self.ai_y) / PAD_H
            self.ball_vy = (hit_pos - 0.5) * 8
            self.rally_count += 1
            self.check_rally_banter()

        # Score — ball exits left
        if self.ball_x < 0:
            self.ai_score += 1
            self.state = "scored"
            self.trigger_score_banter(scorer="ai")
            return

        # Score — ball exits right
        if self.ball_x > W:
            self.player_score += 1
            self.state = "scored"
            self.trigger_score_banter(scorer="player")
            return

    def trigger_score_banter(self, scorer):
        ps = self.player_score
        ai = self.ai_score
        diff = abs(ps - ai)
        score_ctx = f"Current score: you {ai} — friend {ps}."

        # Check game-over first so we fire exactly one banter event per point.
        # Previously the code fired a point-banter AND a gameover-banter in the
        # same call, launching two concurrent LLM threads that raced to write
        # current_banter — the slower one would silently overwrite the faster one.
        if ps >= SCORE_TO_WIN:
            self.state = "gameover"
            self.show_gameover("PLAYER")
            generate_banter("player_wins", f"Final score: you {ai} — friend {ps}.")
            return
        if ai >= SCORE_TO_WIN:
            self.state = "gameover"
            self.show_gameover("GRID")
            generate_banter("ai_wins", f"Final score: you {ai} — friend {ps}.")
            return

        # Only fire one banter event per point — close_game takes priority when tense
        if diff <= 1 and ps + ai > 4 and random.random() < 0.4:
            generate_banter("close_game", score_ctx)
        elif scorer == "player":
            if ps > ai and diff >= 2:
                generate_banter("player_winning", score_ctx)
            else:
                generate_banter("player_scores", score_ctx)
        else:
            if ai > ps and diff >= 2:
                generate_banter("ai_winning", score_ctx)
            else:
                generate_banter("ai_scores", score_ctx)

    def check_rally_banter(self):
        if self.rally_count >= 8 and self.last_banter_event != "long_rally":
            self.last_banter_event = "long_rally"
            generate_banter("long_rally")

    def show_gameover(self, winner):
        self.canvas.delete("overlay")
        if winner == "PLAYER":
            title = "YOU WIN!"
            color = TEXT_CYAN
        else:
            title = "GRID WINS"
            color = TEXT_ORANGE

        self.canvas.create_text(W//2, H//2 - 70, text=title,
            font=("Courier New", 42, "bold"), fill=color, tags="overlay")
        self.canvas.create_text(W//2, H//2,
            text=f"{self.player_score}  —  {self.ai_score}",
            font=("Courier New", 28, "bold"), fill=TEXT_BRIGHT, tags="overlay")
        self.canvas.create_text(W//2, H//2 + 60,
            text="[ SPACE ] to play again",
            font=("Courier New", 13, "bold"), fill=TEXT_ORANGE, tags="overlay")

    def draw_frame(self):
        self.canvas.delete("game")

        # Scores
        self.canvas.create_text(W//4, 40,
            text=str(self.player_score),
            font=("Courier New", 48, "bold"),
            fill=SCORE_COLOR, tags="game")
        self.canvas.create_text(3*W//4, 40,
            text=str(self.ai_score),
            font=("Courier New", 48, "bold"),
            fill=SCORE_COLOR, tags="game")

        # Labels
        self.canvas.create_text(W//4, 80,
            text="YOU", font=("Courier New", 10),
            fill=TEXT_DIM, tags="game")
        self.canvas.create_text(3*W//4, 80,
            text="GRID", font=("Courier New", 10),
            fill=TEXT_DIM, tags="game")

        # Player paddle
        px = 30
        self.canvas.create_rectangle(
            px, self.player_y,
            px + PAD_W, self.player_y + PAD_H,
            fill=PAD_PLAYER, outline="", tags="game"
        )
        # Glow effect on player paddle
        self.canvas.create_rectangle(
            px - 2, self.player_y - 2,
            px + PAD_W + 2, self.player_y + PAD_H + 2,
            fill="", outline="#003300", width=1, tags="game"
        )

        # AI paddle
        ax = W - 30 - PAD_W
        self.canvas.create_rectangle(
            ax, self.ai_y,
            ax + PAD_W, self.ai_y + PAD_H,
            fill=PAD_AI, outline="", tags="game"
        )
        self.canvas.create_rectangle(
            ax - 2, self.ai_y - 2,
            ax + PAD_W + 2, self.ai_y + PAD_H + 2,
            fill="", outline="#003300", width=1, tags="game"
        )

        # Ball
        self.canvas.create_oval(
            self.ball_x, self.ball_y,
            self.ball_x + BALL_SIZE, self.ball_y + BALL_SIZE,
            fill=BALL_COLOR, outline="", tags="game"
        )
        # Ball glow
        self.canvas.create_oval(
            self.ball_x - 3, self.ball_y - 3,
            self.ball_x + BALL_SIZE + 3, self.ball_y + BALL_SIZE + 3,
            fill="", outline="#004444", width=1, tags="game"
        )

        # State messages
        if self.state == "scored":
            self.canvas.create_text(W//2, H//2,
                text="[ SPACE ] to serve",
                font=("Courier New", 13), fill=TEXT_ORANGE, tags="game")

        # Refresh banter snapshot once per second (~60 frames) instead of every frame
        self._banter_tick += 1
        if self._banter_tick >= 60:
            self._banter_tick = 0
            with banter_lock:
                self._cached_banter = current_banter
        if self._cached_banter and self._cached_banter != self.banter_var.get():
            self.banter_var.set("")  # Clear first to force label resize
            self.banter_var.set(self._cached_banter)

    def game_loop(self):
        if self.state == "playing":
            self.update_ai()
            self.update_ball()
        self.draw_frame()
        self.root.after(16, self.game_loop)  # ~60fps


# ── Entry point ───────────────────────────────────
def launch_pong():
    root = tk.Tk()
    root.configure(bg=BG)
    # Center horizontally/vertically on screen. We set width but NOT height —
    # the canvas is H px tall and two labels are packed below it, so letting Tk
    # measure the full height with update_idletasks() avoids clipping those labels.
    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    # Build the game first so Tk knows the real window height
    game = PongGame(root)
    root.update_idletasks()
    wh = root.winfo_reqheight()  # Actual height including canvas + labels
    x = (sw - W) // 2
    y = max(0, (sh - wh) // 2)
    root.geometry(f"{W}x{wh}+{x}+{y}")
    root.mainloop()

if __name__ == "__main__":
    launch_pong()
