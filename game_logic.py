from collections import Counter
import discord

class Game:
    def __init__(self, center, outer, words, pangrams, reactions_enabled=False):
        self.center = center.upper()
        self.outer = [c.upper() for c in outer]
        self.all_words = [w.upper() for w in words]
        self.pangrams = [p.upper() for p in pangrams]
        self.found_words = {} # word -> user_mention (e.g. <@id>)
        self.scores = {} # user_mention -> count
        self.all_letters = sorted([self.center] + self.outer)
        self.found_pangrams = {} # pangram -> user_mention
        self.reactions_enabled = reactions_enabled

    def is_valid_word(self, word):
        word = word.upper()
        return word in self.all_words and word not in self.found_words

    def add_found_word(self, word, user_mention):
        word = word.upper()
        if word not in self.found_words:
            self.found_words[word] = user_mention
            self.scores[user_mention] = self.scores.get(user_mention, 0) + 1
            if word in self.pangrams:
                self.found_pangrams[word] = user_mention
            return True
        return False

    def is_complete(self):
        return len(self.found_words) == len(self.all_words)

    def get_game_start_embed(self, sb_number, date_str):
        embed = discord.Embed(
            title=f"Spelling Bee #{sb_number}",
            description=f"Date: {date_str}",
            color=0xF7DA21
        )
        embed.add_field(name="Center Letter", value=f"**{self.center}**", inline=True)
        embed.add_field(name="Outer Letters", value=" ".join(self.outer), inline=True)
        embed.add_field(name="Words to find", value=str(len(self.all_words)), inline=True)
        embed.set_footer(text="Type words in the channel to guess!")
        return embed

    def get_stats_embed(self, title="Game Ended"):
        embed = discord.Embed(title=title, color=0xF7DA21)
        if not self.scores:
            embed.description = "No words found yet!"
            return embed

        sorted_scores = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        leaderboard = []
        for i, (user_mention, count) in enumerate(sorted_scores, 1):
            user_pangrams = [p for p, finder in self.found_pangrams.items() if finder == user_mention]
            pangram_str = f" ({len(user_pangrams)} pangram{'s' if len(user_pangrams) != 1 else ''})" if user_pangrams else ""
            leaderboard.append(f"{i}. {user_mention}: {count} words{pangram_str}")

        embed.add_field(name="Leaderboard", value="\n".join(leaderboard), inline=False)
        embed.set_footer(text=f"Total found: {len(self.found_words)}/{len(self.all_words)}")
        return embed

    def get_hints_embed(self):
        remaining = [w for w in self.all_words if w not in self.found_words]
        if not remaining:
            return discord.Embed(title="Hints", description="All words found! Queen Bee! 🐝", color=0xF7DA21)

        embed = discord.Embed(title="Spelling Bee Hints", color=0xF7DA21)
        embed.add_field(name="Center Letter", value=f"**{self.center}**", inline=True)
        embed.add_field(name="Outer Letters", value=" ".join(self.outer), inline=True)
        embed.description = f"Total words left: **{len(remaining)}**"

        hints_by_length = {}
        for word in remaining:
            length = len(word)
            hints_by_length.setdefault(length, []).append(word)

        for length in sorted(hints_by_length.keys()):
            words_of_length = hints_by_length[length]
            two_letter_counts = Counter([w[:2] for w in words_of_length])
            sorted_combos = sorted(two_letter_counts.items())
            
            combo_str = "  ".join([f"{k}-{v}" for k, v in sorted_combos])
            embed.add_field(
                name=f"{length} Letter Words ({len(words_of_length)} left)", 
                value=combo_str + "\n\n", 
                inline=False
            )
            
        return embed

    def get_found_words_embed(self):
        if not self.found_words:
            return discord.Embed(title="Found Words", description="No words found yet.", color=0xF7DA21)
        
        embed = discord.Embed(
            title="Words Found So Far", 
            description=f"Total words found: **{len(self.found_words)}**", 
            color=0xF7DA21
        )
        
        found_by_two_letters = {}
        for word in sorted(self.found_words.keys()):
            prefix = word[:2]
            found_by_two_letters.setdefault(prefix, []).append(word)

        for prefix in sorted(found_by_two_letters.keys()):
            words = ", ".join(found_by_two_letters[prefix])
            embed.add_field(name=prefix, value=words, inline=False)
            
        return embed
