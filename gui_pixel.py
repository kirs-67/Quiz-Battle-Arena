import os
import tkinter as tk
from tkinter import messagebox
import engine

try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

# ============================================================
# PIXEL-GAME THEME
# Built-in pixel lettering: no extra font file is required.
# ============================================================
ACCENT = "#ffd900"
ACCENT_DARK = "#d00000"
TEXT_LIGHT = "#fff8b0"
DIM_TEXT = "#6e6e5a"
SHADOW = "#111111"
FALLBACK_BG = "#171717"
BUTTON_BG = "#2b2b2b"
BUTTON_HOVER = "#444444"
WHITE = "#ffffff"
DARK_TEXT = "#1a1a1a"   # used on light/yellow buttons so labels stay readable
PANEL_BG = "#000000"    # backing panel color for text placed over busy art

IMAGE_FOLDER = "images"

IMAGE_FILES = {
    "sword_easy": "sword_easy.png",
    "sword_medium": "sword_medium.png",
    "sword_hard": "sword_hard.png",
    "emoji_correct": "emoji_correct.png",
    "emoji_wrong": "emoji_wrong.png",
    "emoji_win": "emoji_win.png",
    "emoji_lose": "emoji_lose.png",
    "bg_title": "bg_title.PNG",
    "bg_game": "bg_game.PNG",
}

# ------------------------------------------------------------
# AUDIO
# Uses pygame because pygame.mixer.music supports pause()/unpause(),
# which resumes playback from the exact spot it was paused at instead
# of restarting the track — regular tkinter has no built-in equivalent.
# Requires: pip install pygame
# ------------------------------------------------------------
SOUND_FOLDER = "sounds"

SOUND_FILES = {
    "bg": "bgmusic.mp3",
    "correct": "bgmusic_correct.mp3",
    "wrong": "bgmusic_wrong.mp3",
    "win": "bgmusic_win.mp3",
    "lose": "bgmusic_lose.mp3",
}

MUSIC_VOLUME = 0.45
SFX_VOLUME = 0.9


def load_image(key, size=None):
    """Loads an image by key from IMAGE_FILES. Returns None if unavailable.
    Prints a DEBUG line explaining exactly why, if it fails."""
    if not PILLOW_AVAILABLE:
        print(f"[DEBUG] Pillow is not installed — cannot load '{key}'. Run: pip install pillow")
        return None
    filename = IMAGE_FILES.get(key)
    if not filename:
        return None
    path = os.path.join(IMAGE_FOLDER, filename)
    abs_path = os.path.abspath(path)
    if not os.path.exists(path):
        print(f"[DEBUG] File not found for '{key}'. Looked here: {abs_path}")
        return None
    try:
        img = Image.open(path)
        if size:
            img = img.resize(size)
        print(f"[DEBUG] Successfully loaded '{key}' from {abs_path}")
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"[DEBUG] Found file for '{key}' at {abs_path} but failed to open it: {e}")
        return None


def load_sound(key):
    """Loads a short sound effect by key from SOUND_FILES as a pygame
    Sound object. Returns None if unavailable, printing a DEBUG line
    explaining exactly why (mirrors load_image's behavior)."""
    if not PYGAME_AVAILABLE:
        return None
    filename = SOUND_FILES.get(key)
    if not filename:
        return None
    path = os.path.join(SOUND_FOLDER, filename)
    abs_path = os.path.abspath(path)
    if not os.path.exists(path):
        print(f"[DEBUG] Sound file not found for '{key}'. Looked here: {abs_path}")
        return None
    try:
        sound = pygame.mixer.Sound(path)
        sound.set_volume(SFX_VOLUME)
        print(f"[DEBUG] Successfully loaded sound '{key}' from {abs_path}")
        return sound
    except Exception as e:
        print(f"[DEBUG] Found sound file for '{key}' at {abs_path} but failed to load it: {e}")
        return None


class QuizBattleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz Battle Arena")
        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))
        self.root.configure(bg=FALLBACK_BG)
        self.root.update_idletasks()

        self.WIDTH = self.root.winfo_screenwidth()
        self.HEIGHT = self.root.winfo_screenheight()

        # ---- game state ----
        self.player_name = ""
        self.health = 3
        self.max_health = 3
        self.score = 0
        self.wrong_answers = []
        self.lifelines_left = {}
        self.round_questions = []
        self.current_index = 0
        self.current_choices = {}
        self.difficulty_var = tk.StringVar(value="Mixed")
        self.difficulty_text_ids = {}

        # Preload images sized to the real screen resolution
        self.images = {
            "sword_easy": load_image("sword_easy", (40, 40)),
            "sword_medium": load_image("sword_medium", (40, 40)),
            "sword_hard": load_image("sword_hard", (40, 40)),
            "emoji_correct": load_image("emoji_correct", (90, 90)),
            "emoji_wrong": load_image("emoji_wrong", (90, 90)),
            "emoji_win": load_image("emoji_win", (110, 110)),
            "emoji_lose": load_image("emoji_lose", (110, 110)),
            "bg_title": load_image("bg_title", (self.WIDTH, self.HEIGHT)),
            "bg_game": load_image("bg_game", (self.WIDTH, self.HEIGHT)),
        }

        # ---- audio: start the looping bg track, preload the stingers ----
        self.audio_enabled = False
        self.sfx = {"correct": None, "wrong": None, "win": None, "lose": None}
        self.init_audio()

        # Stop the mixer cleanly when the window is closed
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.build_title_screen()

    def init_audio(self):
        """Starts bgmusic.mp3 looping forever and preloads the short
        correct/wrong stinger clips. Safe to call even if pygame or the
        sound files aren't available — the game just runs silently."""
        if not PYGAME_AVAILABLE:
            print("[DEBUG] pygame is not installed — background music disabled. Run: pip install pygame")
            return

        try:
            pygame.mixer.init()
        except Exception as e:
            print(f"[DEBUG] Could not initialize the audio mixer: {e}")
            return

        bg_path = os.path.join(SOUND_FOLDER, SOUND_FILES["bg"])
        abs_bg_path = os.path.abspath(bg_path)
        if not os.path.exists(bg_path):
            print(f"[DEBUG] Background music file not found. Looked here: {abs_bg_path}")
            return

        try:
            pygame.mixer.music.load(bg_path)
            pygame.mixer.music.set_volume(MUSIC_VOLUME)
            pygame.mixer.music.play(loops=-1)  # loop forever from the start
            self.audio_enabled = True
            print(f"[DEBUG] Background music loaded and playing from {abs_bg_path}")
        except Exception as e:
            print(f"[DEBUG] Found background music at {abs_bg_path} but failed to play it: {e}")
            return

        self.sfx["correct"] = load_sound("correct")
        self.sfx["wrong"] = load_sound("wrong")
        self.sfx["win"] = load_sound("win")
        self.sfx["lose"] = load_sound("lose")

    def on_close(self):
        """Stops the mixer before the window closes so audio doesn't
        keep playing in the background after the app quits."""
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        self.root.destroy()

    # ------------------------------------------------------------
    # CANVAS HELPERS — draw straight onto the background, no solid panel
    # ------------------------------------------------------------

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def make_canvas(self, bg_key):
        self.clear_screen()
        canvas = tk.Canvas(self.root, width=self.WIDTH, height=self.HEIGHT,
                            highlightthickness=0, bg=FALLBACK_BG)
        canvas.pack(fill="both", expand=True)
        bg_img = self.images.get(bg_key)
        if bg_img:
            canvas.create_image(0, 0, anchor="nw", image=bg_img)
        return canvas

    # 5x7 chunky pixel alphabet inspired by the supplied reference image.
    PIXEL_FONT = {
        "A":["01110","10001","10001","11111","10001","10001","10001"],
        "B":["11110","10001","10001","11110","10001","10001","11110"],
        "C":["01111","10000","10000","10000","10000","10000","01111"],
        "D":["11110","10001","10001","10001","10001","10001","11110"],
        "E":["11111","10000","10000","11110","10000","10000","11111"],
        "F":["11111","10000","10000","11110","10000","10000","10000"],
        "G":["01111","10000","10000","10111","10001","10001","01111"],
        "H":["10001","10001","10001","11111","10001","10001","10001"],
        "I":["11111","00100","00100","00100","00100","00100","11111"],
        "J":["00111","00010","00010","00010","10010","10010","01100"],
        "K":["10001","10010","10100","11000","10100","10010","10001"],
        "L":["10000","10000","10000","10000","10000","10000","11111"],
        "M":["10001","11011","10101","10101","10001","10001","10001"],
        "N":["10001","11001","10101","10011","10001","10001","10001"],
        "O":["01110","10001","10001","10001","10001","10001","01110"],
        "P":["11110","10001","10001","11110","10000","10000","10000"],
        "Q":["01110","10001","10001","10001","10101","10010","01101"],
        "R":["11110","10001","10001","11110","10100","10010","10001"],
        "S":["01111","10000","10000","01110","00001","00001","11110"],
        "T":["11111","00100","00100","00100","00100","00100","00100"],
        "U":["10001","10001","10001","10001","10001","10001","01110"],
        "V":["10001","10001","10001","10001","10001","01010","00100"],
        "W":["10001","10001","10001","10101","10101","11011","10001"],
        "X":["10001","10001","01010","00100","01010","10001","10001"],
        "Y":["10001","10001","01010","00100","00100","00100","00100"],
        "Z":["11111","00001","00010","00100","01000","10000","11111"],
        "0":["01110","10001","10011","10101","11001","10001","01110"],
        "1":["00100","01100","00100","00100","00100","00100","01110"],
        "2":["01110","10001","00001","00010","00100","01000","11111"],
        "3":["11110","00001","00001","01110","00001","00001","11110"],
        "4":["00010","00110","01010","10010","11111","00010","00010"],
        "5":["11111","10000","10000","11110","00001","00001","11110"],
        "6":["01110","10000","10000","11110","10001","10001","01110"],
        "7":["11111","00001","00010","00100","01000","01000","01000"],
        "8":["01110","10001","10001","01110","10001","10001","01110"],
        "9":["01110","10001","10001","01111","00001","00001","01110"],
        "?":["01110","10001","00001","00010","00100","00100","00100"],
        "!":["00100","00100","00100","00100","00100","00000","00100"],
        "-":["00000","00000","00000","11111","00000","00000","00000"],
        ".":["00000","00000","00000","00000","00000","00110","00110"],
    }

    def draw_text(self, canvas, x, y, text, font, fill=TEXT_LIGHT, width=None):
        """Readable normal text with a small shadow."""
        canvas.create_text(x + 2, y + 2, text=text, font=font,
                           fill=SHADOW, width=width)
        return canvas.create_text(x, y, text=text, font=font,
                                  fill=fill, width=width)

    def draw_pixel_text(self, canvas, x, y, text, scale=4,
                        fill=ACCENT, outline=SHADOW, anchor="center"):
        """Draws chunky yellow/red/black arcade-style pixel text."""
        text = str(text).upper()
        char_width = 5 * scale
        spacing = scale
        total_width = sum(
            (char_width + spacing) if ch != " " else 3 * scale
            for ch in text
        )

        if anchor == "center":
            start_x = x - total_width / 2
        elif anchor == "e":
            start_x = x - total_width
        else:
            start_x = x

        ids = []

        for ch in text:
            if ch == " ":
                start_x += 3 * scale
                continue

            pattern = self.PIXEL_FONT.get(ch)
            if pattern is None:
                start_x += char_width + spacing
                continue

            for row, line in enumerate(pattern):
                for col, pixel in enumerate(line):
                    if pixel == "1":
                        ox = start_x + col * scale
                        oy = y - (7 * scale) / 2 + row * scale

                        # Black outline
                        canvas.create_rectangle(
                            ox - max(1, scale / 3),
                            oy - max(1, scale / 3),
                            ox + scale + max(1, scale / 3),
                            oy + scale + max(1, scale / 3),
                            fill=outline, outline=outline
                        )

                        # Red lower-right shadow
                        canvas.create_rectangle(
                            ox + max(1, scale / 2),
                            oy + max(1, scale / 2),
                            ox + scale + max(1, scale / 2),
                            oy + scale + max(1, scale / 2),
                            fill=ACCENT_DARK, outline=ACCENT_DARK
                        )

                        # Yellow main pixel
                        ids.append(canvas.create_rectangle(
                            ox, oy, ox + scale, oy + scale,
                            fill=fill, outline=fill
                        ))

            start_x += char_width + spacing

        return ids

    def draw_button(self, canvas, x, y, text, command, width=260, height=52,
                    bg=BUTTON_BG, font=("Courier New", 13, "bold"),
                    fg=None, pixel=False, pixel_scale=3):
        """Clickable arcade-style button."""
        rect = canvas.create_rectangle(
            x - width / 2, y - height / 2,
            x + width / 2, y + height / 2,
            fill=bg, outline=SHADOW, width=4
        )
        canvas.create_line(
            x - width / 2 + 4, y + height / 2 - 3,
            x + width / 2 - 4, y + height / 2 - 3,
            fill=ACCENT_DARK, width=4
        )

        # Auto-pick a readable label color: light/yellow buttons get dark
        # text, dark buttons get light text, unless the caller overrides it.
        if fg is None:
            fg = DARK_TEXT if bg in (ACCENT,) else TEXT_LIGHT

        if pixel:
            labels = self.draw_pixel_text(
                canvas, x, y, text, scale=pixel_scale,
                fill=ACCENT, outline=SHADOW
            )
        else:
            labels = [canvas.create_text(
                x, y, text=text, font=font, fill=fg
            )]

        def on_click(_event):
            command()

        def on_enter(_event):
            canvas.itemconfig(rect, fill=BUTTON_HOVER)

        def on_leave(_event):
            canvas.itemconfig(rect, fill=bg)

        for item in [rect] + labels:
            canvas.tag_bind(item, "<Button-1>", on_click)
            canvas.tag_bind(item, "<Enter>", on_enter)
            canvas.tag_bind(item, "<Leave>", on_leave)

        return rect, labels[0]

    def draw_progress_bar(self, canvas, x, y, current, total, width=380, height=14):
        canvas.create_rectangle(x - width / 2, y - height / 2, x + width / 2, y + height / 2,
                                 outline=TEXT_LIGHT, width=1)
        if total > 0:
            fill_width = width * (current / total)
            canvas.create_rectangle(x - width / 2, y - height / 2,
                                     x - width / 2 + fill_width, y + height / 2,
                                     fill=ACCENT, outline="")

    # ------------------------------------------------------------
    # TITLE SCREEN
    # ------------------------------------------------------------

    def build_title_screen(self):
        cx = self.WIDTH // 2
        top = self.HEIGHT // 2 - 260
        canvas = self.make_canvas("bg_title")
        self.title_canvas = canvas

        self.draw_pixel_text(canvas, cx, top, "QUIZ BATTLE ARENA", scale=5)
        self.draw_text(canvas, cx, top + 55,
                       "Test your Python list knowledge in battle!",
                       ("Courier New", 13, "bold"), fill=TEXT_LIGHT)

        self.draw_text(canvas, cx, top + 100, "Fighter name:", ("Arial", 14))
        self.name_entry = tk.Entry(canvas, font=("Arial", 13), justify="center",
                                     bg="#14141f", fg=TEXT_LIGHT, insertbackground=TEXT_LIGHT,
                                     relief="flat", highlightthickness=1,
                                     highlightbackground=ACCENT, highlightcolor=ACCENT)
        canvas.create_window(cx, top + 135, window=self.name_entry, width=220, height=32)

        self.draw_pixel_text(canvas, cx, top + 185,
                             "CHOOSE DIFFICULTY", scale=3)

        icon_keys = {"Easy": "sword_easy", "Medium": "sword_medium",
                     "Hard": "sword_hard", "Mixed": None}
        levels = ["Easy", "Medium", "Hard", "Mixed"]
        self.difficulty_positions = {}

        # Selector box drawn first so text/icons render on top of it
        self.selector_rect = canvas.create_rectangle(
            0, 0, 0, 0, outline=ACCENT, width=3)

        for i, level in enumerate(levels):
            y = top + 225 + i * 40
            self.difficulty_positions[level] = y
            icon = self.images.get(icon_keys[level])
            icon_id = None
            if icon:
                icon_id = canvas.create_image(cx - 90, y, image=icon)
            text_ids = self.draw_pixel_text(canvas, cx, y, level, scale=3)
            self.difficulty_text_ids[level] = text_ids

            def select(_event=None, lvl=level):
                self.difficulty_var.set(lvl)
                self.refresh_difficulty_highlight()

            for text_id in text_ids:
                canvas.tag_bind(text_id, "<Button-1>", select)
            if icon_id is not None:
                canvas.tag_bind(icon_id, "<Button-1>", select)

        self.diff_cx = cx
        canvas.bind("<Button-1>", self.handle_title_click)
        self.refresh_difficulty_highlight()
        self.draw_button(canvas, cx, top + 420, "START BATTLE",
                         self.start_game, width=300, height=58,
                         pixel=True, pixel_scale=3)

        self.draw_button(canvas, cx - 260, top + 480, "HOW TO PLAY",
                         self.build_instructions_screen, width=180, height=44)
        self.draw_button(canvas, cx, top + 480, "LEADERBOARD",
                         self.build_leaderboard_screen, width=180, height=44)
        self.draw_button(canvas, cx + 260, top + 480, "EXIT",
                         self.build_exit_screen, width=180, height=44)

    # ------------------------------------------------------------
    # HOW TO PLAY SCREEN
    # ------------------------------------------------------------

    def build_instructions_screen(self):
        cx = self.WIDTH // 2
        top = self.HEIGHT // 2 - 280
        canvas = self.make_canvas("bg_title")

        self.draw_pixel_text(canvas, cx, top, "HOW TO PLAY", scale=4)

        lines = [
            "1. Enter your fighter name and pick a difficulty tier.",
            "2. Each round asks a question about Python lists — answer A, B, or C.",
            "3. Correct answers earn points; harder tiers are worth more.",
            "4. Wrong answers cost one life — run out of lives and it's game over.",
            "5. 50/50 removes a wrong choice; Skip passes with no penalty.",
            "   Each lifeline can only be used once per game!",
            "6. Score enough points before your lives run out to win the round.",
            "7. Your score is saved to that difficulty's leaderboard.",
        ]

        panel_top = top + 70
        line_height = 34
        panel_bottom = panel_top + len(lines) * line_height + 10

        canvas.create_rectangle(
            cx - 400, panel_top - 25, cx + 400, panel_bottom,
            fill=PANEL_BG, stipple="gray50", outline=ACCENT, width=2
        )

        for i, line in enumerate(lines):
            self.draw_text(canvas, cx, panel_top + i * line_height, line,
                           ("Courier New", 13, "bold"), fill=WHITE, width=760)

        self.draw_button(canvas, cx, panel_bottom + 55, "BACK",
                         self.build_title_screen, width=220, height=52,
                         pixel=True, pixel_scale=3)

    # ------------------------------------------------------------
    # EXIT SCREEN
    # ------------------------------------------------------------

    def build_exit_screen(self):
        cx = self.WIDTH // 2
        cy = self.HEIGHT // 2
        canvas = self.make_canvas("bg_title")

        self.draw_pixel_text(canvas, cx, cy - 100, "LEAVING SO SOON?", scale=4)
        self.draw_text(canvas, cx, cy - 40,
                       "Thanks for battling through the Quiz Arena!",
                       ("Courier New", 14, "bold"), fill=TEXT_LIGHT)

        self.draw_button(canvas, cx - 160, cy + 40, "QUIT GAME",
                         self.on_close, width=220, height=54,
                         pixel=True, pixel_scale=3)
        self.draw_button(canvas, cx + 160, cy + 40, "BACK",
                         self.build_title_screen, width=220, height=54,
                         pixel=True, pixel_scale=3)

    # ------------------------------------------------------------
    # LEADERBOARD SCREEN (also reused by the game-over summary)
    # ------------------------------------------------------------

    def draw_leaderboard_block(self, canvas, cx, y_top, show_count=5):
        """Draws the 4-column (Easy/Medium/Hard/Mixed) leaderboard panel
        starting below y_top. Returns the panel's bottom y-coordinate so
        callers know where to place content underneath it."""
        panel_top = y_top + 18
        panel_height = 32 + 24 * show_count
        panel_bottom = panel_top + panel_height

        canvas.create_rectangle(
            cx - 340, panel_top, cx + 340, panel_bottom,
            fill=PANEL_BG, stipple="gray50", outline=ACCENT, width=2
        )

        tiers = ["Easy", "Medium", "Hard", "Mixed"]
        column_x_offsets = [-255, -85, 85, 255]

        for tier, offset in zip(tiers, column_x_offsets):
            col_x = cx + offset
            self.draw_text(canvas, col_x, panel_top + 17, tier.upper(),
                            ("Courier New", 13, "bold"), fill=ACCENT)

            ranked = engine.get_ranked_leaderboard(tier)
            if not ranked:
                self.draw_text(canvas, col_x, panel_top + 47, "No scores yet",
                                ("Arial", 10, "italic"), fill="#cccccc")
            else:
                for i, entry in enumerate(ranked[:show_count], start=1):
                    name, score, _ = entry
                    self.draw_text(canvas, col_x, panel_top + 17 + i * 24,
                                   f"{i}. {name} - {score}",
                                   ("Courier New", 10, "bold"), fill=WHITE)

        return panel_bottom

    def build_leaderboard_screen(self):
        cx = self.WIDTH // 2
        top = self.HEIGHT // 2 - 260
        canvas = self.make_canvas("bg_title")

        self.draw_pixel_text(canvas, cx, top, "LEADERBOARDS", scale=4)
        self.draw_text(canvas, cx, top + 45,
                       "Top scores for every difficulty tier",
                       ("Courier New", 12, "bold"), fill=TEXT_LIGHT)

        bottom = self.draw_leaderboard_block(canvas, cx, top + 70, show_count=8)

        reset_id = self.draw_text(canvas, cx, bottom + 35, "Reset Leaderboard",
                                    ("Arial", 11, "underline"), fill="#ff8080")
        canvas.tag_bind(reset_id, "<Button-1>", lambda e: self.confirm_reset_leaderboard())

        self.draw_button(canvas, cx, bottom + 90, "BACK",
                         self.build_title_screen, width=220, height=52,
                         pixel=True, pixel_scale=3)

    def confirm_reset_leaderboard(self):
        if messagebox.askyesno("Reset Leaderboard",
                                 "Delete ALL saved players from the leaderboard? This cannot be undone."):
            engine.clear_leaderboard()
            messagebox.showinfo("Leaderboard Reset", "The leaderboard has been cleared.")

    def confirm_go_home(self):
        """Lets the player bail out of the current round mid-question and
        return to the main menu. The bg music just keeps playing through
        this — nothing to pause or restart here."""
        if messagebox.askyesno("Return to Main Menu",
                                 "Leave this round and return to the main menu? "
                                 "Your current progress won't be saved."):
            self.build_title_screen()

    def handle_title_click(self, event):
        """
        Whole-row click detection. The pixel font only fills in the lit
        squares of each letter, leaving lots of empty gaps that aren't
        clickable on their own — so instead we just check if the click
        landed anywhere near a difficulty row (icon + text combined)
        and select that difficulty regardless of the exact pixel hit.
        """
        for level, y in self.difficulty_positions.items():
            if abs(event.y - y) <= 22 and abs(event.x - self.diff_cx) <= 220:
                self.difficulty_var.set(level)
                self.refresh_difficulty_highlight()
                return

    def refresh_difficulty_highlight(self):
        selected = self.difficulty_var.get()
        for level, text_ids in self.difficulty_text_ids.items():
            color = ACCENT if level == selected else DIM_TEXT
            for text_id in text_ids:
                self.title_canvas.itemconfig(text_id, fill=color)

        # Move the selector box to frame whichever difficulty is selected
        y = self.difficulty_positions[selected]
        cx = self.diff_cx
        self.title_canvas.coords(self.selector_rect, cx - 170, y - 20, cx + 170, y + 20)

    def start_game(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Name Required",
                                     "Please enter your fighter name before starting!")
            return
        self.player_name = name
        self.difficulty = self.difficulty_var.get()
        difficulty = self.difficulty

        self.max_health = engine.LIVES_BY_DIFFICULTY.get(difficulty, 3)
        self.health = self.max_health
        self.score = 0
        self.wrong_answers = []
        self.lifelines_left = engine.DEFAULT_LIFELINES.copy()

        question_pool = engine.filter_by_difficulty(engine.QUESTIONS, difficulty)
        num_rounds = engine.NUM_ROUNDS_BY_DIFFICULTY.get(difficulty, 10)
        num_rounds = min(num_rounds, len(question_pool))
        self.round_questions = engine.build_round_questions(question_pool, num_rounds)
        self.win_threshold = engine.get_win_threshold(self.round_questions)
        self.current_index = 0

        self.build_question_screen()

    # ------------------------------------------------------------
    # QUESTION SCREEN
    # ------------------------------------------------------------

    def build_question_screen(self):
        if self.health <= 0 or self.current_index >= len(self.round_questions):
            self.build_summary_screen()
            return

        cx = self.WIDTH // 2
        top = self.HEIGHT // 2 - 260
        canvas = self.make_canvas("bg_game")
        self.question_canvas = canvas

        question_data = self.round_questions[self.current_index]
        question, choice_a, choice_b, choice_c, correct, difficulty, explanation = question_data
        self.current_choices = {"A": choice_a, "B": choice_b, "C": choice_c}

        hearts = "❤ " * self.health + "🖤 " * (self.max_health - self.health)
        self.draw_text(canvas, 90, 30, hearts,
                       ("Courier New", 16, "bold"), fill=ACCENT)
        self.draw_pixel_text(canvas, self.WIDTH - 100, 40,
                             f"{self.score} / {self.win_threshold:.0f} PTS", scale=2.5)

        self.draw_button(canvas, 100, 80, "\u2302 HOME", self.confirm_go_home,
                         width=140, height=42, bg=ACCENT,
                         font=("Courier New", 12, "bold"))

        total = len(self.round_questions)
        self.draw_pixel_text(canvas, cx, top,
                             f"ROUND {self.current_index + 1} OF {total}",
                             scale=2.5)
        self.draw_text(canvas, cx, top + 24, difficulty,
                       ("Courier New", 11, "bold"), fill=TEXT_LIGHT)
        self.draw_progress_bar(canvas, cx, top + 25, self.current_index, total)

        # Dark backing panel behind the question so it stays readable
        # over busy background art, regardless of the art's colors.
        canvas.create_rectangle(
            cx - 340, top + 48, cx + 340, top + 115,
            fill=PANEL_BG, stipple="gray50", outline=ACCENT, width=2
        )
        self.draw_text(canvas, cx, top + 80, question,
                       ("Courier New", 17, "bold"), fill=WHITE, width=620)

        self.choice_rects = {}
        for i, letter in enumerate(["A", "B", "C"]):
            y = top + 170 + i * 60
            rect, label = self.draw_button(
                canvas, cx, y, f"{letter}.  {self.current_choices[letter]}",
                lambda l=letter: self.answer(l), width=500, height=52,
                bg=BUTTON_BG, font=("Courier New", 12, "bold"))
            self.choice_rects[letter] = (rect, label)

        lifeline_y = top + 380
        fifty_bg = ACCENT if self.lifelines_left["5050"] > 0 else "#555566"
        skip_bg = ACCENT if self.lifelines_left["SKIP"] > 0 else "#555566"

        self.draw_button(canvas, cx - 110, lifeline_y, f"50/50 ({self.lifelines_left['5050']})",
                          self.use_fifty_fifty if self.lifelines_left["5050"] > 0 else lambda: None,
                          width=180, height=38, bg=fifty_bg, font=("Arial", 10, "bold"))
        self.draw_button(canvas, cx + 110, lifeline_y, f"Skip ({self.lifelines_left['SKIP']})",
                          self.use_skip if self.lifelines_left["SKIP"] > 0 else lambda: None,
                          width=180, height=38, bg=skip_bg, font=("Arial", 10, "bold"))

    def use_fifty_fifty(self):
        question_data = self.round_questions[self.current_index]
        hidden_letter = engine.apply_fifty_fifty(question_data)
        self.lifelines_left["5050"] -= 1
        rect, label = self.choice_rects[hidden_letter]
        self.question_canvas.itemconfig(rect, fill="#555555")
        self.question_canvas.itemconfig(label, state="hidden")

    def use_skip(self):
        self.lifelines_left["SKIP"] -= 1
        self.current_index += 1
        self.build_question_screen()

    def answer(self, letter):
        question_data = self.round_questions[self.current_index]
        correct = engine.check_answer(question_data, letter)
        explanation = question_data[6]

        if correct:
            points = engine.get_points(question_data)
            self.score += points
            self.show_reaction_popup("Correct!", f"+{points} points!", "emoji_correct",
                                      ACCENT, explanation, sound_key="correct")
        else:
            self.health -= 1
            self.wrong_answers.append(question_data[0])
            self.show_reaction_popup("Wrong!", f"The correct answer was {question_data[4]}.",
                                       "emoji_wrong", "#33334d", explanation, sound_key="wrong")

        self.current_index += 1
        self.build_question_screen()

    def show_reaction_popup(self, title, message, image_key, accent_color,
                             explanation=None, sound_key=None):
        # Duck the looping bg track and play the matching stinger while
        # the popup is open.
        if self.audio_enabled:
            pygame.mixer.music.pause()
            effect = self.sfx.get(sound_key)
            if effect:
                effect.play()

        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup_w, popup_h = 300, 340
        popup.configure(bg=FALLBACK_BG)
        popup.resizable(False, False)

        # Center the popup over the middle of the main window instead of
        # letting it default to the corner of the screen.
        self.root.update_idletasks()
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        pos_x = root_x + (root_w // 2) - (popup_w // 2)
        pos_y = root_y + (root_h // 2) - (popup_h // 2)
        popup.geometry(f"{popup_w}x{popup_h}+{pos_x}+{pos_y}")

        icon = self.images.get(image_key)
        if icon:
            tk.Label(popup, image=icon, bg=FALLBACK_BG).pack(pady=(15, 5))

        # Pick a readable OK-button text color: dark text on the light
        # yellow "Correct!" button, light text on the dark "Wrong!" button.
        button_fg = DARK_TEXT if accent_color == ACCENT else TEXT_LIGHT

        tk.Label(popup, text=title, font=("Arial", 14, "bold"), bg=FALLBACK_BG,
                  fg=TEXT_LIGHT).pack()
        tk.Label(popup, text=message, font=("Arial", 10), bg=FALLBACK_BG,
                  fg="#dcdcf5", wraplength=260, justify="center").pack(pady=5)

        # Explanation card, anchored toward the lower-center of the popup,
        # just above the OK button — explains *why* that's the answer.
        if explanation:
            why_frame = tk.Frame(popup, bg="#14141f", highlightthickness=1,
                                  highlightbackground=ACCENT)
            why_frame.pack(pady=(8, 6), padx=18, fill="x")
            tk.Label(why_frame, text="WHY", font=("Courier New", 9, "bold"),
                      bg="#14141f", fg=ACCENT).pack(pady=(6, 0))
            tk.Label(why_frame, text=explanation, font=("Arial", 9), bg="#14141f",
                      fg=TEXT_LIGHT, wraplength=250, justify="center").pack(pady=(2, 8), padx=8)

        tk.Button(popup, text="OK", command=popup.destroy, bg=accent_color, fg=button_fg,
                  activebackground=accent_color, activeforeground=button_fg,
                  relief="flat", font=("Arial", 10, "bold"), width=10).pack(pady=10)

        popup.transient(self.root)
        popup.grab_set()
        self.root.wait_window(popup)

        # Popup is closed — resume the bg track from the exact spot it
        # was paused at (unpause never restarts from the beginning).
        if self.audio_enabled:
            pygame.mixer.music.unpause()

    # ------------------------------------------------------------
    # SUMMARY SCREEN
    # ------------------------------------------------------------

    def build_summary_screen(self):
        cx = self.WIDTH // 2
        top = self.HEIGHT // 2 - 240
        canvas = self.make_canvas("bg_title")

        won = self.health > 0 and self.score >= self.win_threshold
        engine.add_to_leaderboard(self.player_name, self.score, self.difficulty)

        # Keep the bg loop playing straight through the result screen —
        # just layer the win/lose stinger on top of it instead of
        # stopping it.
        if self.audio_enabled:
            effect = self.sfx.get("win" if won else "lose")
            if effect:
                effect.play()

        result_icon = self.images.get("emoji_win") if won else self.images.get("emoji_lose")
        if result_icon:
            canvas.create_image(cx, top, image=result_icon)

        self.draw_pixel_text(canvas, cx, top + 90,
                             "YOU WIN" if won else "GAME OVER",
                             scale=4)

        self.draw_text(canvas, cx, top + 135,
                        f"{self.player_name}  •  {self.score} pts  •  {len(self.wrong_answers)} missed",
                        ("Arial", 12), fill="#dcdcf5")

        self.draw_pixel_text(canvas, cx, top + 180, "LEADERBOARDS", scale=3)
        self.draw_leaderboard_block(canvas, cx, top + 180)

        self.draw_button(canvas, cx, top + 440, "PLAY AGAIN",
                         self.restart_to_title, width=280, height=58,
                         pixel=True, pixel_scale=3)

    def restart_to_title(self):
        """Called from PLAY AGAIN: restarts the bg music loop from 0:00
        (fresh start, not resumed) before rebuilding the title screen."""
        if self.audio_enabled:
            try:
                pygame.mixer.music.play(loops=-1)
            except Exception as e:
                print(f"[DEBUG] Could not restart background music: {e}")
        self.build_title_screen()


def main():
    print("=" * 50)
    print("[DEBUG] Starting Quiz Battle Arena GUI")
    print(f"[DEBUG] Current working directory: {os.getcwd()}")
    print(f"[DEBUG] Pillow installed: {PILLOW_AVAILABLE}")
    print(f"[DEBUG] pygame installed: {PYGAME_AVAILABLE}")
    images_path = os.path.abspath(IMAGE_FOLDER)
    print(f"[DEBUG] Looking for images folder at: {images_path}")
    if os.path.isdir(IMAGE_FOLDER):
        print(f"[DEBUG] Found images/ folder. Files inside: {os.listdir(IMAGE_FOLDER)}")
    else:
        print("[DEBUG] images/ folder was NOT found at that location!")
    sounds_path = os.path.abspath(SOUND_FOLDER)
    print(f"[DEBUG] Looking for sounds folder at: {sounds_path}")
    if os.path.isdir(SOUND_FOLDER):
        print(f"[DEBUG] Found sounds/ folder. Files inside: {os.listdir(SOUND_FOLDER)}")
    else:
        print("[DEBUG] sounds/ folder was NOT found at that location!")
    print("=" * 50)

    root = tk.Tk()
    QuizBattleGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()