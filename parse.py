import sys
from collections import defaultdict

# -----------------------------
# State (Earley Item)
# -----------------------------
class State:
    def __init__(self, lhs, rhs, dot, start, prob=1.0):
        self.lhs = lhs
        self.rhs = rhs
        self.dot = dot
        self.start = start
        self.prob = prob  # best probability

    def is_complete(self):
        return self.dot == len(self.rhs)

    def next_symbol(self):
        if not self.is_complete():
            return self.rhs[self.dot]
        return None

    def advance(self):
        return State(self.lhs, self.rhs, self.dot + 1, self.start, self.prob)

    def key(self):
        return (self.lhs, tuple(self.rhs), self.dot, self.start)

    def __str__(self):
        rhs = list(self.rhs)
        rhs.insert(self.dot, "•")
        return f"{self.lhs} -> {' '.join(rhs)} [{self.start}] (p={self.prob:.6f})"


# -----------------------------
# Read Grammar
# -----------------------------
def read_grammar(filename):
    grammar = defaultdict(list)
    probs = {}

    with open(filename) as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue

            prob = float(parts[0])
            lhs = parts[1]
            rhs = parts[2:]

            grammar[lhs].append(rhs)
            probs[(lhs, tuple(rhs))] = prob

    return grammar, probs


# -----------------------------
# Read Sentences
# -----------------------------
def read_sentences(filename):
    sentences = []
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if line:
                sentences.append(line.split())
    return sentences


# -----------------------------
# Add state with duplicate check
# -----------------------------
def add_state(chart_col, state):
    key = state.key()

    if key not in chart_col:
        chart_col[key] = state
        return True
    else:
        # keep better probability
        if state.prob > chart_col[key].prob:
            chart_col[key].prob = state.prob
            return True
    return False


# -----------------------------
# Earley Parser
# -----------------------------
def earley_parse(words, grammar, probs):
    n = len(words)

    # chart[i] = dict of states
    chart = [dict() for _ in range(n + 1)]

    # Start symbol assumed S
    start_state = State("γ", ["S"], 0, 0, 1.0)
    add_state(chart[0], start_state)

    for i in range(n + 1):
        changed = True

        while changed:
            changed = False
            states = list(chart[i].values())

            for state in states:

                # -----------------
                # PREDICT
                # -----------------
                next_sym = state.next_symbol()
                if next_sym in grammar:
                    for rhs in grammar[next_sym]:
                        prob = probs[(next_sym, tuple(rhs))]
                        new_state = State(next_sym, rhs, 0, i, prob)

                        if add_state(chart[i], new_state):
                            changed = True

                # -----------------
                # COMPLETE
                # -----------------
                elif state.is_complete():
                    for prev in chart[state.start].values():
                        if prev.next_symbol() == state.lhs:

                            new_prob = prev.prob * state.prob
                            new_state = State(
                                prev.lhs,
                                prev.rhs,
                                prev.dot + 1,
                                prev.start,
                                new_prob
                            )

                            if add_state(chart[i], new_state):
                                changed = True

        # -----------------
        # SCAN
        # -----------------
        if i < n:
            word = words[i]
            for state in chart[i].values():
                if state.next_symbol() == word:
                    new_state = State(
                        state.lhs,
                        state.rhs,
                        state.dot + 1,
                        state.start,
                        state.prob
                    )
                    add_state(chart[i + 1], new_state)

    return chart


# -----------------------------
# Print Chart
# -----------------------------
def print_chart(chart):
    for i, col in enumerate(chart):
        print(f"\nChart[{i}]")
        for state in col.values():
            print(state)


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python parse.py grammar.gr sentences.sen")
        sys.exit(1)

    grammar_file = sys.argv[1]
    sentence_file = sys.argv[2]

    grammar, probs = read_grammar(grammar_file)
    sentences = read_sentences(sentence_file)

    for sent in sentences:
        print("\n==============================")
        print("Sentence:", " ".join(sent))

        chart = earley_parse(sent, grammar, probs)
        print_chart(chart)