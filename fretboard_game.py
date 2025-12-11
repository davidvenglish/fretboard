#!/usr/bin/env python3
import random
import time
import os
import sys
import json
import argparse
from typing import Tuple, List, Set

SHARP = '♯'
FLAT = '♭'

NOTES_SHARP = ['C', f'C{SHARP}', 'D', f'D{SHARP}', 'E', 'F', f'F{SHARP}', 'G', f'G{SHARP}', 'A', f'A{SHARP}', 'B']
NOTES_FLAT = ['C', f'D{FLAT}', 'D', f'E{FLAT}', 'E', 'F', f'G{FLAT}', 'G', f'A{FLAT}', 'A', f'B{FLAT}', 'B']

SHARP_TO_FLAT = {
    f'C{SHARP}': f'D{FLAT}',
    f'D{SHARP}': f'E{FLAT}',
    f'F{SHARP}': f'G{FLAT}',
    f'G{SHARP}': f'A{FLAT}',
    f'A{SHARP}': f'B{FLAT}',
}

FLAT_TO_SHARP = {v: k for k, v in SHARP_TO_FLAT.items()}

TUNING = ['E', 'A', 'D', 'G', 'B', 'E']

HIGH_SCORE_FILE = 'fretboard_highscore.json'
LEARNING_DATA_FILE = 'fretboard_learning.json'

RESPONSE_TIME_THRESHOLD = 5.0
LEARNED_THRESHOLD = 3
LEARNED_BANNER_DURATION = 5.0

class FretboardGame:
    def __init__(self, use_flats: bool = False, show_labels: bool = False, frets_mode: bool = False):
        self.score = 0
        self.high_score = self.load_high_score()
        self.start_time = None
        self.game_duration = 120
        self.use_flats = use_flats
        self.show_labels = show_labels
        self.frets_mode = frets_mode
        self.notes = NOTES_FLAT if use_flats else NOTES_SHARP
        self.learning_data = self.load_learning_data()
        self.frets_sequence = self.generate_frets_sequence() if frets_mode else []
        self.current_position_index = 0

    def load_high_score(self) -> int:
        if os.path.exists(HIGH_SCORE_FILE):
            try:
                with open(HIGH_SCORE_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('high_score', 0)
            except:
                return 0
        return 0

    def save_high_score(self):
        with open(HIGH_SCORE_FILE, 'w') as f:
            json.dump({'high_score': self.high_score}, f)

    def load_learning_data(self) -> dict:
        if os.path.exists(LEARNING_DATA_FILE):
            try:
                with open(LEARNING_DATA_FILE, 'r') as f:
                    data = json.load(f)
                    if 'random' not in data:
                        data = {
                            'random': {'sharps': data.get('sharps', {}), 'flats': data.get('flats', {})},
                            'sequential': {'sharps': {}, 'flats': {}}
                        }
                    return data
            except:
                pass
        return {
            'random': {'sharps': {}, 'flats': {}},
            'sequential': {'sharps': {}, 'flats': {}}
        }

    def save_learning_data(self):
        with open(LEARNING_DATA_FILE, 'w') as f:
            json.dump(self.learning_data, f)

    def get_position_key(self, string_idx: int, fret: int) -> str:
        return f"{string_idx}-{fret}"

    def get_game_mode_key(self) -> str:
        return 'sequential' if self.frets_mode else 'random'

    def get_note_mode_key(self) -> str:
        return 'flats' if self.use_flats else 'sharps'

    def update_learning_status(self, string_idx: int, fret: int, response_time: float, correct: bool) -> bool:
        game_mode_key = self.get_game_mode_key()
        note_mode_key = self.get_note_mode_key()
        pos_key = self.get_position_key(string_idx, fret)
        note = self.get_note_at_position(string_idx, fret)

        if game_mode_key not in self.learning_data:
            self.learning_data[game_mode_key] = {}

        if note_mode_key not in self.learning_data[game_mode_key]:
            self.learning_data[game_mode_key][note_mode_key] = {}

        if pos_key not in self.learning_data[game_mode_key][note_mode_key]:
            self.learning_data[game_mode_key][note_mode_key][pos_key] = {
                'note': note,
                'correct_count': 0,
                'last_time': None
            }

        position_data = self.learning_data[game_mode_key][note_mode_key][pos_key]
        was_learned = position_data['correct_count'] >= LEARNED_THRESHOLD
        just_learned = False

        if correct:
            if response_time < RESPONSE_TIME_THRESHOLD:
                old_count = position_data['correct_count']
                position_data['correct_count'] = min(position_data['correct_count'] + 1, LEARNED_THRESHOLD)
                if not was_learned and position_data['correct_count'] >= LEARNED_THRESHOLD:
                    just_learned = True
            else:
                position_data['correct_count'] = max(0, position_data['correct_count'] - 1)
            position_data['last_time'] = response_time
        else:
            position_data['correct_count'] = 0
            position_data['last_time'] = None

        return just_learned

    def is_position_learned(self, string_idx: int, fret: int) -> bool:
        game_mode_key = self.get_game_mode_key()
        note_mode_key = self.get_note_mode_key()
        pos_key = self.get_position_key(string_idx, fret)

        if (game_mode_key in self.learning_data and
            note_mode_key in self.learning_data[game_mode_key] and
            pos_key in self.learning_data[game_mode_key][note_mode_key]):
            return self.learning_data[game_mode_key][note_mode_key][pos_key]['correct_count'] >= LEARNED_THRESHOLD
        return False

    def get_learned_count(self) -> Tuple[int, int]:
        all_positions = [(s, f) for s in range(6) for f in range(1, 13)]
        learned_count = sum(1 for s, f in all_positions if self.is_position_learned(s, f))
        return learned_count, len(all_positions)

    def generate_frets_sequence(self) -> List[Tuple[int, int]]:
        fret_order = [3, 5, 7, 9, 12, 1, 6, 8, 10, 2, 4, 11]
        string_order = [5, 4, 3, 2, 1, 0]
        sequence = []
        for fret in fret_order:
            for string in string_order:
                sequence.append((string, fret))
        return sequence

    def select_weighted_position(self) -> Tuple[int, int]:
        all_positions = [(s, f) for s in range(6) for f in range(1, 13)]

        learned = [pos for pos in all_positions if self.is_position_learned(pos[0], pos[1])]
        unlearned = [pos for pos in all_positions if not self.is_position_learned(pos[0], pos[1])]

        if unlearned and random.random() < 0.75:
            return random.choice(unlearned)
        elif learned:
            return random.choice(learned)
        else:
            return random.choice(all_positions)

    def get_note_at_position(self, string_num: int, fret: int) -> str:
        base_note = TUNING[string_num]
        base_index = NOTES_SHARP.index(base_note)
        note_index = (base_index + fret) % 12
        return self.notes[note_index]

    def normalize_note(self, note: str) -> str:
        if self.use_flats and note in SHARP_TO_FLAT:
            return SHARP_TO_FLAT[note]
        elif not self.use_flats and note in FLAT_TO_SHARP:
            return FLAT_TO_SHARP[note]
        return note

    def are_enharmonic(self, note1: str, note2: str) -> bool:
        if note1 == note2:
            return True
        if note1 in SHARP_TO_FLAT and SHARP_TO_FLAT[note1] == note2:
            return True
        if note1 in FLAT_TO_SHARP and FLAT_TO_SHARP[note1] == note2:
            return True
        return False

    def get_chromatic_index(self, note: str) -> int:
        chromatic_order = ['C', 'C♯', 'D♭', 'D', 'D♯', 'E♭', 'E', 'F', 'F♯', 'G♭', 'G', 'G♯', 'A♭', 'A', 'A♯', 'B♭', 'B']
        if note in chromatic_order:
            return chromatic_order.index(note)
        return 0

    def generate_choices(self, correct_note: str) -> List[Tuple[str, str]]:
        all_choices = list(self.notes)
        all_choices.sort(key=self.get_chromatic_index)

        key_mapping = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', '+']
        return [(key_mapping[i], note) for i, note in enumerate(all_choices)]

    def draw_fretboard(self, target_string: int, target_fret: int, flash_red: bool = False):
        print("\033[H\033[J", end="")

        print("\n  FRETBOARD MEMORIZATION GAME")

        mode = "FLATS" if self.use_flats else "SHARPS"
        learned_count, total_count = self.get_learned_count()
        percentage = int((learned_count / total_count) * 100)
        progress = f"{percentage}% ({learned_count}/{total_count})"

        time_display = self.get_time_display()
        if self.frets_mode:
            position_info = f"Position: {self.current_position_index + 1}/72"
            print(f"  {position_info}  |  Time: {time_display}  |  Mode: {mode}  |  {progress}\n")
        else:
            print(f"  Score: {self.score}  |  High Score: {self.high_score}  |  Time: {time_display}  |  Mode: {mode}  |  {progress}\n")

        cell_width = 7
        marker_positions = {3: '•', 5: '•', 7: '•', 9: '•', 12: '••'}

        if self.show_labels:
            fret_numbers = "      "
            for i in range(1, 13):
                fret_numbers += " " + str(i).center(cell_width)
            print(fret_numbers + "\n")

        for string_idx in range(5, -1, -1):
            if self.show_labels:
                string_name = TUNING[string_idx]
                line = f"  {string_name}   "
            else:
                line = "      "

            for fret in range(1, 13):
                fret_char = "\033[36m║\033[0m"

                if fret == target_fret and string_idx == target_string:
                    padding = (cell_width - 1) // 2
                    extra = (cell_width - 1) % 2
                    if flash_red:
                        cell_content = "─" * padding + "\033[91m⬤\033[0m" + "─" * (padding + extra)
                    else:
                        cell_content = "─" * padding + "\033[93m⬤\033[0m" + "─" * (padding + extra)
                else:
                    cell_content = "─" * cell_width

                line += fret_char + cell_content

            print(line)

            if string_idx == 3:
                marker_line = "      "
                for fret in range(1, 13):
                    fret_char = "\033[36m║\033[0m"
                    if fret in marker_positions:
                        marker = marker_positions[fret]
                        cell_content = marker.center(cell_width)
                    else:
                        cell_content = " " * cell_width

                    marker_line += fret_char + cell_content

                print(marker_line)
            elif string_idx > 0:
                spacer_line = "      "
                for fret in range(1, 13):
                    fret_char = "\033[36m║\033[0m"
                    cell_content = " " * cell_width
                    spacer_line += fret_char + cell_content
                print(spacer_line)

        marker_line = "      "
        for fret in range(1, 13):
            if fret in marker_positions:
                marker = marker_positions[fret]
                cell_content = " " + marker.center(cell_width)
            else:
                cell_content = " " + " " * cell_width

            marker_line += cell_content

        print(marker_line)
        print()

    def get_time_display(self) -> str:
        if self.start_time is None:
            if self.frets_mode:
                return "0:00"
            else:
                minutes = self.game_duration // 60
                seconds = self.game_duration % 60
                return f"{minutes}:{seconds:02d}"

        elapsed = time.time() - self.start_time

        if self.frets_mode:
            total_seconds = int(elapsed)
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}:{seconds:02d}"
        else:
            remaining = max(0, self.game_duration - int(elapsed))
            minutes = remaining // 60
            seconds = remaining % 60
            return f"{minutes}:{seconds:02d}"

    def get_time_remaining(self) -> int:
        if self.start_time is None:
            return self.game_duration
        elapsed = time.time() - self.start_time
        remaining = max(0, self.game_duration - int(elapsed))
        return remaining

    def is_time_up(self) -> bool:
        if self.frets_mode:
            return False
        return self.get_time_remaining() <= 0

    def play_round(self):
        if self.frets_mode:
            if self.current_position_index >= len(self.frets_sequence):
                return False
            target_string, target_fret = self.frets_sequence[self.current_position_index]
        else:
            target_string, target_fret = self.select_weighted_position()

        correct_note = self.get_note_at_position(target_string, target_fret)
        question_start_time = time.time()

        choices = self.generate_choices(correct_note)

        def draw_screen(flash_red=False):
            self.draw_fretboard(target_string, target_fret, flash_red)
            print("  What note is highlighted?\n")

            col_width = 5
            numbers_line = "  "
            notes_line = "  "

            for key, note in choices:
                numbers_line += f"{key}".center(col_width)
                notes_line += f"{note}".center(col_width)

            print(numbers_line)
            print(notes_line)
            print("\n  Press 'x' to exit\n")

        import select
        import termios

        termios.tcflush(sys.stdin, termios.TCIFLUSH)

        draw_screen()
        last_draw_time = time.time()

        while True:
            if self.is_time_up():
                return False

            current_time = time.time()
            if current_time - last_draw_time >= 1.0:
                rlist, _, _ = select.select([sys.stdin], [], [], 0)
                if not rlist:
                    draw_screen()
                    last_draw_time = current_time

            try:
                rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
                if not rlist:
                    continue

                choice = sys.stdin.read(1)

                if choice == 'x' or choice == 'X':
                    return False

                choice_dict = {key: note for key, note in choices}
                if choice in choice_dict:
                    chosen_note = choice_dict[choice]
                    response_time = time.time() - question_start_time

                    if self.are_enharmonic(chosen_note, correct_note):
                        self.update_learning_status(target_string, target_fret, response_time, True)

                        if self.frets_mode:
                            self.current_position_index += 1
                        else:
                            self.score += 1
                            if self.score > self.high_score:
                                self.high_score = self.score

                        return True
                    else:
                        self.update_learning_status(target_string, target_fret, response_time, False)
                        for _ in range(2):
                            draw_screen(flash_red=True)
                            time.sleep(0.15)
                            draw_screen(flash_red=False)
                            time.sleep(0.15)
            except KeyboardInterrupt:
                return False
            except Exception:
                continue

    def play_game(self):
        self.score = 0
        self.current_position_index = 0
        self.start_time = time.time()

        import tty
        import termios

        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())

            while not self.is_time_up():
                if not self.play_round():
                    break
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSANOW, old_settings)

        self.save_learning_data()

        final_time = int(time.time() - self.start_time)
        final_minutes = final_time // 60
        final_seconds = final_time % 60

        os.system('clear' if os.name != 'nt' else 'cls')
        print("\n" + "="*60)

        if self.frets_mode:
            print("  COMPLETE!")
            print("="*60)
            print(f"\n  Final Time: {final_minutes}:{final_seconds:02d}")
            print(f"  All 72 positions covered!")
        else:
            print("  TIME'S UP!")
            print("="*60)
            print(f"\n  Final Score: {self.score}")
            print(f"  High Score: {self.high_score}")

            if self.score == self.high_score and self.score > 0:
                print("\n  🎉 NEW HIGH SCORE! 🎉")

            self.save_high_score()

        learned_count, total_count = self.get_learned_count()
        percentage = int((learned_count / total_count) * 100)
        print(f"  Progress: {percentage}% Complete ({learned_count}/{total_count} positions learned)")

        print("\n" + "="*60)

    def run(self):
        while True:
            self.play_game()

            print("\n  Play again? (y/n): ", end="", flush=True)
            response = input().strip().lower()

            if response != 'y' and response != 'yes':
                print("\n  Thanks for playing! 🎸\n")
                break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fretboard Memorization Game')
    parser.add_argument('--flats', action='store_true', help='Use flat notes instead of sharp notes')
    parser.add_argument('--labels', action='store_true', help='Show fret numbers and string names')
    parser.add_argument('--frets', action='store_true', help='Sequential frets mode - go through all positions in order')
    args = parser.parse_args()

    game = FretboardGame(use_flats=args.flats, show_labels=args.labels, frets_mode=args.frets)
    game.run()
