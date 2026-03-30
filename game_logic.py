from collections import Counter

class Game:
    def __init__(self, center, outer, words):
        self.center = center.upper()
        self.outer = [c.upper() for c in outer]
        self.all_words = [w.upper() for w in words]
        self.found_words = {} # word -> username
        self.scores = {} # username -> count
        self.all_letters = sorted([self.center] + self.outer)

    def is_valid_word(self, word):
        word = word.upper()
        return word in self.all_words and word not in self.found_words

    def add_found_word(self, word, username):
        word = word.upper()
        if word not in self.found_words:
            self.found_words[word] = username
            self.scores[username] = self.scores.get(username, 0) + 1
            return True
        return False

    def is_complete(self):
        return len(self.found_words) == len(self.all_words)

    def get_stats_message(self):
        if not self.scores:
            return "No words found yet!"
        sorted_scores = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        stats = "\n".join([f"{user}: {count} words" for user, count in sorted_scores])
        return f"Game Over! Final Scores:\n{stats}"

    def get_hints(self):
        # Remaining words
        remaining = [w for w in self.all_words if w not in self.found_words]
        if not remaining:
            return "All words found!"

        # Letter/Length Grid
        # Row: First Letter, Column: Length
        lengths = sorted(list(set(len(w) for w in self.all_words)))
        first_letters = sorted(list(set(w[0] for w in self.all_words)))
        
        grid = {} # letter -> {length -> count}
        for w in remaining:
            l = w[0]
            length = len(w)
            if l not in grid: grid[l] = {}
            grid[l][length] = grid[l].get(length, 0) + 1

        # Format Grid
        header = "      " + " ".join([f"{l:2}" for l in lengths]) + "  tot"
        rows = []
        total_remaining = len(remaining)
        for fl in first_letters:
            row_vals = []
            row_total = 0
            for l in lengths:
                count = grid.get(fl, {}).get(l, 0)
                if count == 0:
                    row_vals.append("- ")
                else:
                    row_vals.append(f"{count:2}")
                    row_total += count
            if row_total > 0:
                rows.append(f"{fl:2}:   " + " ".join(row_vals) + f"   {row_total}")
        
        grid_msg = "Letter/Length Grid:\n```\n" + header + "\n" + "\n".join(rows) + "\n```"

        # Two-letter combinations
        two_letter_counts = Counter([w[:2] for w in remaining])
        sorted_combos = sorted(two_letter_counts.items())
        combos_msg = "Two-letter combos:\n" + "  ".join([f"{k}-{v}" for k, v in sorted_combos])
        
        return f"{grid_msg}\n{combos_msg}"

    def get_found_words(self):
        if not self.found_words:
            return "No words found yet."
        sorted_found = sorted(self.found_words.keys())
        return "Words found so far:\n" + ", ".join(sorted_found)
