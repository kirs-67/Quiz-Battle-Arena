"""
gui.py - QUIZ BATTLE ARENA (Tkinter GUI Version - Optional Bonus)
Group 2 | DSA Prelim Project

Run with:  python gui.py

Requires the built-in tkinter module, plus Pillow for images:
    pip install pillow

This GUI calls the SAME engine.py functions and lists as the console
game (game.py) — no gameplay logic is duplicated here, only the display.

FULLSCREEN + NO SOLID PANEL:
This version runs fullscreen and draws everything (text, buttons,
progress bar) directly onto the canvas over your background image —
no big solid box covering the picture. Text gets a soft black shadow
so it stays readable no matter what's behind it.
Press ESC anytime to exit fullscreen (handy while testing).

BACKGROUND IMAGES:
Put a file named "bg_title.jpg" and/or "bg_game.jpg" inside the
images/ folder to use them as backgrounds. If missing, a solid dark
color is used instead — nothing breaks either way.
"""

import os
import tkinter as tk
from tkinter import messagebox
import engine

try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

ACCENT = "#e94560"
TEXT_LIGHT = "#ffffff"
SHADOW = "#000000"
FALLBACK_BG = "#1e1e2f"

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

        self.build_title_screen()

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

    def draw_text(self, canvas, x, y, text, font, fill=TEXT_LIGHT, width=None):
        """Draws text with a soft shadow so it reads clearly over any photo."""
        canvas.create_text(x + 2, y + 2, text=text, font=font, fill=SHADOW, width=width)
        return canvas.create_text(x, y, text=text, font=font, fill=fill, width=width)

    def draw_button(self, canvas, x, y, text, command, width=260, height=48,
                     bg=ACCENT, font=("Arial", 13, "bold"), fg=TEXT_LIGHT):
        """A clickable rectangle + label — no native Button widget/background."""
        rect = canvas.create_rectangle(x - width / 2, y - height / 2,
                                        x + width / 2, y + height / 2,
                                        fill=bg, outline="")
        label = canvas.create_text(x, y, text=text, font=font, fill=fg)

        def on_click(_event):
            command()

        def on_enter(_event):
            canvas.itemconfig(rect, fill="#c73650" if bg == ACCENT else "#3d3d5c")

        def on_leave(_event):
            canvas.itemconfig(rect, fill=bg)

        for item in (rect, label):
            canvas.tag_bind(item, "<Button-1>", on_click)
            canvas.tag_bind(item, "<Enter>", on_enter)
            canvas.tag_bind(item, "<Leave>", on_leave)
        return rect, label

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

        self.draw_text(canvas, cx, top, "QUIZ BATTLE ARENA", ("Arial", 32, "bold"))
        self.draw_text(canvas, cx, top + 45, "Test your Python list knowledge in battle!",
                        ("Arial", 13, "italic"), fill="#dcdcf5")

        self.draw_text(canvas, cx, top + 100, "Fighter name:", ("Arial", 14))
        self.name_entry = tk.Entry(canvas, font=("Arial", 13), justify="center",
                                     bg="#14141f", fg=TEXT_LIGHT, insertbackground=TEXT_LIGHT,
                                     relief="flat", highlightthickness=1,
                                     highlightbackground=ACCENT, highlightcolor=ACCENT)
        canvas.create_window(cx, top + 135, window=self.name_entry, width=220, height=32)

        self.draw_text(canvas, cx, top + 185, "Choose difficulty:", ("Arial", 14))

        icon_keys = {"Easy": "sword_easy", "Medium": "sword_medium",
                     "Hard": "sword_hard", "Mixed": None}
        levels = ["Easy", "Medium", "Hard", "Mixed"]
        for i, level in enumerate(levels):
            y = top + 225 + i * 40
            icon = self.images.get(icon_keys[level])
            if icon:
                canvas.create_image(cx - 90, y, image=icon)
            text_id = self.draw_text(canvas, cx, y, level, ("Arial", 13, "bold"))
            self.difficulty_text_ids[level] = text_id

            def select(_event=None, lvl=level):
                self.difficulty_var.set(lvl)
                self.refresh_difficulty_highlight()

            canvas.tag_bind(text_id, "<Button-1>", select)

        self.refresh_difficulty_highlight()
        self.draw_button(canvas, cx, top + 420, "Start Battle", self.start_game)

        reset_id = self.draw_text(canvas, cx, top + 470, "Reset Leaderboard",
                                    ("Arial", 10, "underline"), fill="#999999")
        canvas.tag_bind(reset_id, "<Button-1>", lambda e: self.confirm_reset_leaderboard())

    def confirm_reset_leaderboard(self):
        if messagebox.askyesno("Reset Leaderboard",
                                 "Delete ALL saved players from the leaderboard? This cannot be undone."):
            engine.clear_leaderboard()
            messagebox.showinfo("Leaderboard Reset", "The leaderboard has been cleared.")

    def refresh_difficulty_highlight(self):
        selected = self.difficulty_var.get()
        for level, text_id in self.difficulty_text_ids.items():
            color = ACCENT if level == selected else TEXT_LIGHT
            self.title_canvas.itemconfig(text_id, fill=color)

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

        question_data = self.round_questions[self.current_index]
        question, choice_a, choice_b, choice_c, correct, difficulty, explanation = question_data
        self.current_choices = {"A": choice_a, "B": choice_b, "C": choice_c}

        hearts = "❤ " * self.health + "🖤 " * (self.max_health - self.health)
        self.draw_text(canvas, 90, 40, hearts, ("Arial", 16))
        self.draw_text(canvas, self.WIDTH - 130, 40,
                        f"⭐ {self.score} / {self.win_threshold:.0f} pts", ("Arial", 14, "bold"))

        total = len(self.round_questions)
        self.draw_text(canvas, cx, top, f"Round {self.current_index + 1} of {total}  •  {difficulty}",
                        ("Arial", 11), fill="#dcdcf5")
        self.draw_progress_bar(canvas, cx, top + 25, self.current_index, total)

        self.draw_text(canvas, cx, top + 80, question, ("Arial", 16, "bold"), width=560)

        self.choice_rects = {}
        for i, letter in enumerate(["A", "B", "C"]):
            y = top + 170 + i * 60
            rect, label = self.draw_button(
                canvas, cx, y, f"{letter}.  {self.current_choices[letter]}",
                lambda l=letter: self.answer(l), width=440, height=48, bg="#33334d")
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
        canvas = label
        self.build_question_screen()  # simplest reliable refresh after state change

    def use_skip(self):
        self.lifelines_left["SKIP"] -= 1
        self.current_index += 1
        self.build_question_screen()

    def answer(self, letter):
        question_data = self.round_questions[self.current_index]
        correct = engine.check_answer(question_data, letter)

        if correct:
            points = engine.get_points(question_data)
            self.score += points
            self.show_reaction_popup("Correct!", f"+{points} points!", "emoji_correct", ACCENT)
        else:
            self.health -= 1
            self.wrong_answers.append(question_data[0])
            self.show_reaction_popup("Wrong!", f"The correct answer was {question_data[4]}.",
                                       "emoji_wrong", "#33334d")

        self.current_index += 1
        self.build_question_screen()

    def show_reaction_popup(self, title, message, image_key, accent_color):
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("260x260")
        popup.configure(bg=FALLBACK_BG)
        popup.resizable(False, False)

        icon = self.images.get(image_key)
        if icon:
            tk.Label(popup, image=icon, bg=FALLBACK_BG).pack(pady=(15, 5))

        tk.Label(popup, text=title, font=("Arial", 14, "bold"), bg=FALLBACK_BG,
                  fg=TEXT_LIGHT).pack()
        tk.Label(popup, text=message, font=("Arial", 10), bg=FALLBACK_BG,
                  fg="#dcdcf5", wraplength=220, justify="center").pack(pady=5)
        tk.Button(popup, text="OK", command=popup.destroy, bg=accent_color, fg=TEXT_LIGHT,
                  relief="flat", font=("Arial", 10, "bold"), width=10).pack(pady=10)

        popup.transient(self.root)
        popup.grab_set()
        self.root.wait_window(popup)

    # ------------------------------------------------------------
    # SUMMARY SCREEN
    # ------------------------------------------------------------

    def build_summary_screen(self):
        cx = self.WIDTH // 2
        top = self.HEIGHT // 2 - 240
        canvas = self.make_canvas("bg_title")

        won = self.health > 0 and self.score >= self.win_threshold
        engine.add_to_leaderboard(self.player_name, self.score, self.difficulty)

        result_icon = self.images.get("emoji_win") if won else self.images.get("emoji_lose")
        if result_icon:
            canvas.create_image(cx, top, image=result_icon)

        self.draw_text(canvas, cx, top + 90, "YOU WIN!" if won else "GAME OVER",
                        ("Arial", 24, "bold"), fill="#4caf50" if won else ACCENT)

        self.draw_text(canvas, cx, top + 135,
                        f"{self.player_name}  •  {self.score} pts  •  {len(self.wrong_answers)} missed",
                        ("Arial", 12), fill="#dcdcf5")

        self.draw_text(canvas, cx, top + 175, "— LEADERBOARDS BY DIFFICULTY —",
                        ("Arial", 13, "bold"))

        tiers = ["Easy", "Medium", "Hard", "Mixed"]
        column_x_offsets = [-270, -90, 90, 270]

        for tier, offset in zip(tiers, column_x_offsets):
            col_x = cx + offset
            self.draw_text(canvas, col_x, top + 210, tier, ("Arial", 12, "bold"), fill=ACCENT)

            ranked = engine.get_ranked_leaderboard(tier)
            if not ranked:
                self.draw_text(canvas, col_x, top + 235, "No scores yet",
                                ("Arial", 9, "italic"), fill="#888899")
            else:
                for i, entry in enumerate(ranked[:5], start=1):
                    name, score, _ = entry
                    self.draw_text(canvas, col_x, top + 210 + i * 24,
                                    f"{i}. {name} — {score}", ("Arial", 9), fill="#cfcfe8")

        self.draw_button(canvas, cx, top + 440, "Play Again", self.build_title_screen)


def main():
    print("=" * 50)
    print("[DEBUG] Starting Quiz Battle Arena GUI")
    print(f"[DEBUG] Current working directory: {os.getcwd()}")
    print(f"[DEBUG] Pillow installed: {PILLOW_AVAILABLE}")
    images_path = os.path.abspath(IMAGE_FOLDER)
    print(f"[DEBUG] Looking for images folder at: {images_path}")
    if os.path.isdir(IMAGE_FOLDER):
        print(f"[DEBUG] Found images/ folder. Files inside: {os.listdir(IMAGE_FOLDER)}")
    else:
        print("[DEBUG] images/ folder was NOT found at that location!")
    print("=" * 50)

    root = tk.Tk()
    QuizBattleGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
