"""
engine.py - Quiz Battle Arena SHARED GAME LOGIC

This file holds the lists and functions used by BOTH the console
game (game.py) and the Tkinter GUI (gui.py). Keeping the logic here
means the GUI buttons control the exact same lists as the console
version, instead of duplicating the game separately.

HOW TO ADD YOUR OWN QUESTIONS:
Edit the QUESTIONS list below. Each entry is:
    [ "question text", "choice A", "choice B", "choice C", "correct letter", "difficulty" ]
Difficulty must be "Easy", "Medium", or "Hard".
"""

import random
import json
import os

LEADERBOARD_FILE = "leaderboard.json"

# ============================================================
# GAME DATA (LISTS)
# ============================================================

# 1) NESTED LIST with a 6th value for difficulty tier
# Format: [question, choice A, choice B, choice C, correct letter, difficulty]

QUESTIONS = [
    # ---------------- EASY (10) ----------------
    # Format: [question, A, B, C, correct letter, difficulty, explanation]
    ["Which method adds one item to a list?", "append()", "sort()", "count()", "A", "Easy",
     "append() adds one item to the end of a list."],
    ["What is the index of the first item in a list?", "1", "0", "-2", "B", "Easy",
     "Python list indices start at 0, so the first item sits at index 0."],
    ["Which method removes an item by its index?", "index()", "extend()", "pop()", "C", "Easy",
     "pop(index) removes and returns the item sitting at that index."],
    ["Which loop can traverse a list?", "for", "if", "def", "A", "Easy",
     "A for loop steps through every item in a list one at a time."],
    ["Which method arranges list items in order?", "remove()", "sort()", "append()", "B", "Easy",
     "sort() rearranges the items of a list into order."],
    ["Which function returns the number of items in a list?", "len()", "type()", "sum()", "A", "Easy",
     "len() returns how many items are currently in a list."],
    ["Which method removes an item by its value?", "remove()", "insert()", "pop()", "A", "Easy",
     "remove(value) deletes the first item that matches that value."],
    ["What symbol is used to access a list item by position?", "()", "[]", "{}", "B", "Easy",
     "Square brackets [] are used to index into a list, e.g. my_list[0]."],
    ["Which method adds an item at a specific position?", "insert()", "append()", "sort()", "A", "Easy",
     "insert(index, value) places an item at a specific position instead of the end."],
    ["What does list.count(x) do?", "Removes x", "Counts occurrences of x", "Sorts the list", "B", "Easy",
     "count(x) returns how many times the value x appears in the list."],

    # ---------------- MEDIUM (15) ----------------
    ["What does list[-1] return?", "First item", "Last item", "An error", "B", "Medium",
     "Negative indices count backward from the end, so -1 is the last item."],
    ["Which method extends a list with another list's items?", "append()", "extend()", "add()", "B", "Medium",
     "extend() adds every item from another iterable onto the end of the list."],
    ["What does sorted(my_list, reverse=True) do?", "Sorts ascending", "Sorts descending", "Shuffles it", "B", "Medium",
     "reverse=True flips the order, sorting from highest to lowest."],
    ["Which creates a copy of a list (not a reference)?", "list.copy()", "list2 = list1", "list.link()", "A", "Medium",
     "list.copy() makes an independent copy; list2 = list1 just gives the same list a second name."],
    ["Which method reverses a list in place?", "reverse()", "sort()", "copy()", "A", "Medium",
     "reverse() flips the order of the items directly, without making a new list."],
    ["Which operator checks if an item exists in a list?", "in", "is", "==", "A", "Medium",
     "The in operator tests whether a value exists anywhere in a list."],
    ["Which slice returns the first three items of a list?", "list[:3]", "list[3:]", "list[0,3]", "A", "Medium",
     "list[:3] slices from the start up to, but not including, index 3."],
    ["What does del my_list[2] do?", "Removes the item at index 2", "Removes the value 2", "Clears the list", "A", "Medium",
     "del removes whatever item is sitting at that index, regardless of its value."],
    ["Which method removes all items from a list?", "clear()", "remove()", "pop()", "A", "Medium",
     "clear() empties the list completely, leaving it as []."],
    ["What is the result of [1, 2] + [3, 4]?", "[1, 2, 3, 4]", "[[1, 2], [3, 4]]", "Error", "A", "Medium",
     "The + operator concatenates two lists into one combined list."],
    ["What does [0] * 3 produce?", "[0]", "[0, 0, 0]", "Error", "B", "Medium",
     "Multiplying a list by 3 repeats its contents three times."],
    ["Which function returns the largest item in a list?", "max()", "top()", "sort()[-1]", "A", "Medium",
     "max() scans the whole list and returns its largest value."],
    ["Which function returns the smallest item in a list?", "least()", "min()", "sort()[0]", "B", "Medium",
     "min() scans the whole list and returns its smallest value."],
    ["What happens if you call list.index(5) and 5 is not in the list?", "Returns -1", "Returns None", "Raises ValueError", "C", "Medium",
     "index() doesn't fail silently — it raises a ValueError when the value isn't found."],
    ["Which built-in function gives both index and value while looping?", "enumerate()", "zip()", "range()", "A", "Medium",
     "enumerate() yields an (index, value) pair on every loop iteration."],

    # ---------------- HARD (20) ----------------
    ["What is the time complexity of searching an unsorted list?", "O(1)", "O(n)", "O(log n)", "B", "Hard",
     "Without any ordering to exploit, every element may need checking, giving O(n)."],
    ["What is the amortized time complexity of append() on a list?", "O(1)", "O(n)", "O(n^2)", "A", "Hard",
     "Python over-allocates spare capacity, so append() is O(1) on average."],
    ["What is the time complexity of inserting at the beginning of a list?", "O(1)", "O(n)", "O(log n)", "B", "Hard",
     "Inserting at the front shifts every other element over by one, which is O(n)."],
    ["Which method sorts a list using a custom key function?", "list.sort(key=...)", "list.order(...)", "list.rank(...)", "A", "Hard",
     "The key argument lets you supply a function that decides how items compare."],
    ["What does [x * 2 for x in nums] produce?", "A list with each item doubled", "A doubled-length list of the same items", "An error", "A", "Hard",
     "The comprehension builds a new list where every value from nums is multiplied by 2."],
    ["What is the output of list(range(5))?", "[1, 2, 3, 4, 5]", "[0, 1, 2, 3, 4]", "[0, 1, 2, 3, 4, 5]", "B", "Hard",
     "range(5) generates 5 values starting at 0, so it stops right before 5."],
    ["If list2 = list1 (no copy), what happens when you modify list2?", "list1 also changes", "Only list2 changes", "Python raises an error", "A", "Hard",
     "list2 is just another name for the same list object, so both names see any change."],
    ["What does zip(list1, list2) do?", "Merges both lists into one flat list", "Pairs up elements from each list", "Removes duplicates from both", "B", "Hard",
     "zip() pairs up items from each iterable that share the same position."],
    ["Which sorting algorithm does Python's built-in sort() use internally?", "Quicksort", "Timsort", "Bubble sort", "B", "Hard",
     "CPython's built-in sort() uses Timsort, a hybrid of merge sort and insertion sort."],
    ["What is the output of [1, 2, 3][::-1]?", "[3, 2, 1]", "[1, 2, 3]", "Error", "A", "Hard",
     "A step of -1 walks the list backward, reversing the order of the items."],
    ["If x = [[]] * 3 and you append to x[0], what happens?", "Only x[0] changes", "All three sublists change, since they share one reference", "Python raises an error", "B", "Hard",
     "[[]] * 3 repeats the same inner list object three times, so all three slots point to it."],
    ["Which call removes and returns the LAST item of a list efficiently?", "list.pop()", "list.pop(0)", "list.remove(-1)", "A", "Hard",
     "pop() with no argument removes the last item, which is O(1) since nothing needs to shift."],
    ["What is the time complexity of list.sort()?", "O(n)", "O(n log n)", "O(n^2)", "B", "Hard",
     "Timsort's average and worst-case running time for sort() is O(n log n)."],
    ["Which built-in type, when built from a list, removes duplicate values?", "tuple()", "set()", "dict()", "B", "Hard",
     "A set only ever keeps unique values, so building one from a list drops duplicates."],
    ["Which insertion operation on a list has O(n) complexity due to shifting elements?", "append()", "insert() at an arbitrary index", "len()", "B", "Hard",
     "Inserting in the middle forces every later element to shift over, making it O(n)."],
    ["What is the key difference between list.sort() and sorted(list)?", "sort() modifies in place; sorted() returns a new list", "They are identical", "sorted() only works on tuples", "A", "Hard",
     "sort() mutates the original list and returns None; sorted() leaves the original untouched and returns a new list."],
    ["Which comprehension flattens a list of lists into one list?", "[item for sub in nested for item in sub]", "[sub for item in nested]", "flatten(nested)", "A", "Hard",
     "The nested comprehension loops through each sublist, then each item inside it, flattening everything into one list."],
    ["What is len([[1, 2], [3, 4, 5]])?", "5", "2", "3", "B", "Hard",
     "len() counts the outer elements — here, 2 sublists — not the items nested inside them."],
    ["Which statement about lists vs. tuples is true?", "Lists are mutable, tuples are not", "Tuples are mutable, lists are not", "Both are immutable", "A", "Hard",
     "Lists can be changed after creation, while tuples cannot — that's the core mutable-vs-immutable distinction."],
    ["What does list.copy() create compared to list[:]?", "A functionally equivalent shallow copy", "A deep copy of nested lists", "A reference to the same list", "A", "Hard",
     "list.copy() and list[:] both produce an equivalent shallow copy: same items, new outer list."],
]

# 2) POINTS per difficulty tier
POINTS_BY_DIFFICULTY = {"Easy": 10, "Medium": 15, "Hard": 20}

# 2b) NUMBER OF ROUNDS per difficulty tier
NUM_ROUNDS_BY_DIFFICULTY = {"Easy": 5, "Medium": 10, "Hard": 15, "Mixed": 10}

# 2c) STARTING LIVES per difficulty tier
LIVES_BY_DIFFICULTY = {"Easy": 3, "Medium": 4, "Hard": 5, "Mixed": 4}

# 3) LEADERBOARD - list of [name, score] pairs
leaderboard = []

# 4) Starting lifeline counts (used once each per game)
DEFAULT_LIFELINES = {"5050": 1, "SKIP": 1}


# ============================================================
# CORE LOGIC FUNCTIONS (no input()/print() — usable by console or GUI)
# ============================================================

def filter_by_difficulty(all_questions, difficulty):
    """Returns only questions matching a difficulty tier, or all if 'Mixed'."""
    if difficulty == "Mixed":
        return all_questions.copy()
    # list comprehension = traversal + search combined
    return [q for q in all_questions if q[5] == difficulty]


def build_round_questions(question_pool, num_rounds):
    """
    Picks a random sample of questions for this playthrough.
    Uses a COPY of the list so pop() here never damages the master list.
    """
    available = question_pool.copy()
    random.shuffle(available)
    selected = []
    for _ in range(num_rounds):
        if available:
            selected.append(available.pop())  # pop() removes it from the pool
    return selected


def check_answer(question_data, answer):
    """Returns True if the given letter matches the correct answer."""
    return answer.upper() == question_data[4]


def get_points(question_data):
    """Returns how many points this question is worth based on difficulty."""
    difficulty = question_data[5]
    return POINTS_BY_DIFFICULTY.get(difficulty, 10)


def apply_fifty_fifty(question_data):
    """
    50/50 lifeline: returns the letter of ONE wrong choice to hide.
    The caller decides how to display that (blank it out, grey it out, etc.)
    """
    letters = ["A", "B", "C"]
    correct = question_data[4]
    wrong_letters = [letter for letter in letters if letter != correct]
    return random.choice(wrong_letters)


def search_wrong_topics(wrong_list, keyword):
    """Traverses missed questions looking for a keyword. Demonstrates search."""
    for item in wrong_list:
        if keyword.lower() in item.lower():
            return True
    return False


def add_to_leaderboard(name, score, difficulty):
    leaderboard.append([name, score, difficulty])
    save_leaderboard()


def save_leaderboard():
    """Writes the leaderboard to a JSON file so it survives closing the game."""
    try:
        with open(LEADERBOARD_FILE, "w") as f:
            json.dump(leaderboard, f, indent=2)
    except Exception as e:
        print(f"[DEBUG] Could not save leaderboard: {e}")


def load_leaderboard():
    """Loads any previously saved leaderboard when the game starts."""
    if not os.path.exists(LEADERBOARD_FILE):
        return
    try:
        with open(LEADERBOARD_FILE, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            leaderboard.clear()
            for entry in data:
                # Migrate old [name, score] entries (before difficulty tracking)
                if len(entry) < 3:
                    entry = list(entry) + ["Mixed"]
                leaderboard.append(entry)
            print(f"[DEBUG] Loaded {len(leaderboard)} saved leaderboard entries.")
    except Exception as e:
        print(f"[DEBUG] Could not load leaderboard: {e}")


def clear_leaderboard():
    """Wipes all saved players from both memory and the JSON file on disk."""
    leaderboard.clear()
    save_leaderboard()


def get_ranked_leaderboard(difficulty=None):
    """
    sort()/sorted() for a meaningful ranking, highest score first.
    Pass a difficulty ("Easy"/"Medium"/"Hard"/"Mixed") to get just that
    tier's leaderboard, or leave it out for every entry combined.
    """
    if difficulty:
        entries = [entry for entry in leaderboard if entry[2] == difficulty]
    else:
        entries = leaderboard.copy()
    return sorted(entries, key=lambda entry: entry[1], reverse=True)


def get_win_threshold(round_questions, ratio=0.6):
    """
    Returns the score needed to win: a percentage of the maximum
    possible score for THIS round (so longer/harder rounds scale
    fairly instead of using one fixed number like 30).
    """
    max_possible = sum(get_points(q) for q in round_questions)
    return max_possible * ratio


# Load any previously saved leaderboard as soon as this module is imported,
# so both game.py and gui_pixel.py automatically pick up saved scores.
load_leaderboard()
