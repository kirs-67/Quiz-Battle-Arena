# Test Cases — Quiz Battle Arena

Manual test log for both the console version (`game.py`) and the Tkinter GUI
(`gui_pixel.py`). Both share the same underlying logic in `engine.py`, so a
test that touches list operations (scoring, lifelines, leaderboard) applies
to either front end unless noted.

Legend: ✅ Pass · ❌ Fail 

## Core Gameplay

| # | Test | Steps | Expected Result | Status |
|---|---|---|---|---|
| 1 | Invalid answer input (console) | Type a letter outside A/B/C | Game reprompts, does not crash | ✅ |
| 2 | Invalid answer input (GUI) | N/A — answers are buttons only | No free-text input possible, so no invalid state | ✅ |
| 3 | Empty name (console) | Press Enter with no name | Reprompts until a non-empty name is given | ✅ |
| 4 | Empty name (GUI) | Click START BATTLE with the name field blank | Warning popup: "Please enter your fighter name" | ✅ |
| 5 | 50/50 lifeline | Use `5050` / click 50/50 mid-question | One wrong choice is hidden; cannot be reused this game | ✅ |
| 6 | Skip lifeline | Use `SKIP` / click Skip mid-question | Moves to next question, no life lost, cannot be reused | ✅ |
| 7 | Health reaches 0 | Answer wrong until lives hit 0 | Round ends immediately, GAME OVER shown | ✅ |
| 8 | Win condition | Score at/above the round's win threshold with lives remaining | Shows YOU WIN! | ✅ |
| 9 | Small question pool | Choose a difficulty with fewer questions than `NUM_ROUNDS_BY_DIFFICULTY` | Round length shortens instead of crashing (`min()` guard) | ✅ |
| 10 | Leaderboard sorting | Play multiple rounds with different scores | Leaderboard sorted highest to lowest per difficulty tier | ✅ |
| 11 | Play again | Answer "n" / re-open title after a round | Game exits cleanly (console) / returns to title (GUI) | ✅ |
| 12 | Per-question explanation | Answer any question, correct or wrong | Popup / console line shows a "Why" explanation matching the correct answer | ✅ |

## Persistence

| # | Test | Steps | Expected Result | Status |
|---|---|---|---|---|
| 13 | Leaderboard saves to disk | Finish a round, close the game, reopen | `leaderboard.json` still has the previous scores | ✅ |
| 14 | Corrupted/missing leaderboard file | Delete `leaderboard.json`, launch the game | Starts with an empty leaderboard instead of crashing | ✅ |
| 15 | Reset leaderboard | Click "Reset Leaderboard" on the Leaderboard screen, confirm | All entries cleared from memory and from `leaderboard.json` | ✅ |
| 16 | Reset leaderboard — cancel | Click "Reset Leaderboard", choose "No" on the confirm dialog | Leaderboard is untouched | ✅ |

## GUI Navigation

| # | Test | Steps | Expected Result | Status |
|---|---|---|---|---|
| 17 | Title → How To Play → Back | Click HOW TO PLAY, then BACK | Instructions screen shows the rules; BACK returns to the title screen with entered name/difficulty intact | ✅ |
| 18 | Title → Leaderboard → Back | Click LEADERBOARD, then BACK | Leaderboard screen shows up to 8 entries per tier; BACK returns to title | ✅ |
| 19 | Title → Exit → Back | Click EXIT, then BACK | Exit screen appears; BACK returns to the title screen without closing | ✅ |
| 20 | Title → Exit → Quit | Click EXIT, then QUIT GAME | Application window closes, background music stops | ✅ |
| 21 | Home button mid-question | During any question, click "⌂ HOME" | Confirmation dialog appears; "Yes" returns to title, current round is abandoned and not saved to the leaderboard | ✅ |
| 22 | Home button — cancel | Click Home, choose "No" | Stays on the current question, round state unaffected | ✅ |
| 23 | Difficulty selector highlight | Click each difficulty option | Selector box moves to highlight the chosen difficulty | ✅ |

## Audio

| # | Test | Steps | Expected Result | Status |
|---|---|---|---|---|
| 24 | Background music loops | Let the title/question screens sit idle | `bgmusic.mp3` loops continuously without restarting audibly | ✅ |
| 25 | Music pauses for Correct/Wrong | Answer a question | Bg music pauses, the matching stinger plays, then bg music resumes from the same spot (not from 0:00) | ✅ |
| 26 | Music continues through result screen | Finish a round (win or lose) | Bg music keeps playing under the win/lose stinger instead of stopping | ✅ |
| 27 | Music restarts on Play Again | Click PLAY AGAIN from the result screen | Bg music restarts from 0:00 | ✅ |
| 28 | Missing `sounds/` folder | Rename/remove the `sounds/` folder, launch the game | Game runs normally with no audio and no crash; `[DEBUG]` lines explain why | ✅ |
| 29 | pygame not installed | Uninstall pygame, launch the game | Game runs silently without audio instead of crashing | ✅ |

## Visual / Readability

| # | Test | Steps | Expected Result | Status |
|---|---|---|---|---|
| 30 | Question text legibility | Load any question screen | Dark backing panel keeps white question text readable over the background art | ✅ |
| 31 | Correct/Wrong popup position | Trigger either popup | Popup is centered over the game window, not the top-left corner of the screen | ✅ |
| 32 | Yellow-button label contrast | View 50/50, Skip, Home, and the popup's OK button when their background is yellow | Label text renders dark, not pale-yellow-on-yellow | ✅ |
| 33 | Leaderboard legibility | Open the Leaderboard screen or result screen | Dark panel keeps entries readable regardless of background art | ✅ |

## Notes on Failures Found During Development

- Adding the 7th field (`explanation`) to `QUESTIONS` initially broke `gui_pixel.py`'s
  question-unpacking line, which still expected 6 values — this crashed
  `build_question_screen()` right after the background rendered, leaving a
  blank-looking screen. Fixed by updating the unpack line to include
  `explanation`. Covered going forward by test #12.
