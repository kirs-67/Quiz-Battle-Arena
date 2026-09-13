"""
game.py - QUIZ BATTLE ARENA (Console Version)
Group 2 | DSA Prelim Project

Run with:  python game.py

This is the CONSOLE version. All the actual list logic lives in
engine.py, which the optional gui.py also uses — so both versions
control the exact same data.
"""

import engine

# ============================================================
# FUNCTIONS
# ============================================================

def show_title():
    print("=" * 40)
    print("       QUIZ BATTLE ARENA")
    print("=" * 40)
    print("Answer correctly to defeat the enemy!")
    print("Answer wrong, and you lose a life.")
    print("Use lifelines wisely — you only get one of each!")
    print("Survive all rounds with enough points to win.\n")


def choose_difficulty():
    print("Choose your difficulty:")
    print("1 - Easy")
    print("2 - Medium")
    print("3 - Hard")
    print("4 - Mixed (all difficulties)")
    while True:
        choice = input("Enter 1-4: ").strip()
        mapping = {"1": "Easy", "2": "Medium", "3": "Hard", "4": "Mixed"}
        if choice in mapping:
            return mapping[choice]
        print("Invalid input. Please enter a number from 1 to 4.")


def get_valid_choice(lifelines_left):
    """Input validation: accepts A/B/C, or a lifeline keyword if still available."""
    while True:
        prompt = "Answer (A/B/C)"
        options = []
        if lifelines_left.get("5050", 0) > 0:
            options.append("5050")
        if lifelines_left.get("SKIP", 0) > 0:
            options.append("SKIP")
        if options:
            prompt += f" or lifeline [{'/'.join(options)}]"
        prompt += ": "

        answer = input(prompt).strip().upper()
        if answer in ("A", "B", "C"):
            return answer
        if answer in options:
            return answer
        print("Invalid input. Try again.")


def ask_question(question_data, lifelines_left):
    """Displays one question, handles lifeline use, returns True/False/'SKIPPED'."""
    question, choice_a, choice_b, choice_c, correct, difficulty, explanation = question_data
    choices = {"A": choice_a, "B": choice_b, "C": choice_c}

    print(f"\n[{difficulty}] {question}")

    while True:
        print("A.", choices["A"])
        print("B.", choices["B"])
        print("C.", choices["C"])

        answer = get_valid_choice(lifelines_left)

        if answer == "5050":
            hidden_letter = engine.apply_fifty_fifty(question_data)
            choices[hidden_letter] = "(removed)"
            lifelines_left["5050"] -= 1
            print("\n50/50 used! One wrong choice has been removed.")
            continue  # re-show the question with the option hidden

        if answer == "SKIP":
            lifelines_left["SKIP"] -= 1
            print("\nSkipped! No life lost, no points earned.")
            return "SKIPPED"

        return engine.check_answer(question_data, answer)


def play_round(player_name):
    lifelines_left = engine.DEFAULT_LIFELINES.copy()
    wrong_answers = []
    score = 0

    difficulty = choose_difficulty()
    health = engine.LIVES_BY_DIFFICULTY.get(difficulty, 3)
    question_pool = engine.filter_by_difficulty(engine.QUESTIONS, difficulty)
    num_rounds = engine.NUM_ROUNDS_BY_DIFFICULTY.get(difficulty, 10)
    num_rounds = min(num_rounds, len(question_pool))  # never exceed the pool size

    round_questions = engine.build_round_questions(question_pool, num_rounds)
    win_threshold = engine.get_win_threshold(round_questions)

    print(f"\n{player_name}, prepare for battle! You have {health} lives.")
    print(f"There are {len(round_questions)} questions this round.")
    print(f"You need {win_threshold:.0f}+ points to win.")
    print(f"Lifelines available: 50/50 x{lifelines_left['5050']}, Skip x{lifelines_left['SKIP']}\n")

    round_number = 1
    for question_data in round_questions:
        if health <= 0:
            break
        print(f"\n--- Round {round_number} ---")
        result = ask_question(question_data, lifelines_left)

        if result == "SKIPPED":
            pass
        elif result:
            points = engine.get_points(question_data)
            score += points
            print(f"Correct! +{points} points")
            print(f"Why: {question_data[6]}")
        else:
            health -= 1
            wrong_answers.append(question_data[0])
            print(f"Wrong! The correct answer was {question_data[4]}.")
            print(f"Why: {question_data[6]}")
            print(f"You lost a life. Lives left: {health}")

        round_number += 1

    won = health > 0 and score >= win_threshold

    print("\n" + "=" * 40)
    print("BATTLE SUMMARY")
    print("=" * 40)
    print(f"Player: {player_name}")
    print(f"Final Score: {score}")
    print(f"Lives Remaining: {health}")
    print(f"Questions Missed: {len(wrong_answers)}")

    if wrong_answers:
        print("Topics you missed:")
        for topic in wrong_answers:
            print(" -", topic)
        if engine.search_wrong_topics(wrong_answers, "list"):
            print("\nTip: Review basic list methods before your next attempt!")

    if won:
        print("\nYOU WIN! You defeated the Quiz Arena!")
    else:
        print("\nGAME OVER. The Arena defeats you this time.")

    engine.add_to_leaderboard(player_name, score, difficulty)
    return won


def show_leaderboard():
    print("\n=========== LEADERBOARDS ===========")
    for tier in ["Easy", "Medium", "Hard", "Mixed"]:
        print(f"\n--- {tier} ---")
        ranked = engine.get_ranked_leaderboard(tier)
        if not ranked:
            print("No scores yet.")
            continue
        for position, entry in enumerate(ranked, start=1):
            name, score, _ = entry
            print(f"{position}. {name} - {score} points")


def get_valid_name():
    """Input validation: keeps asking until a non-empty name is entered."""
    while True:
        name = input("Enter your fighter name: ").strip()
        if name:
            return name
        print("Name cannot be empty. Please enter your fighter name.")


def main():
    show_title()
    while True:
        player_name = get_valid_name()
        play_round(player_name)
        show_leaderboard()

        again = input("\nPlay again? (y/n): ").strip().lower()
        if again != "y":
            print("\nThanks for playing Quiz Battle Arena!")
            break


if __name__ == "__main__":
    main()
