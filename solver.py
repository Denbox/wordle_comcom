from playwright.sync_api import sync_playwright
import time, random, sys

# ------------------------------------------------------------------------------
# Scraper Code
# ------------------------------------------------------------------------------

def bypass_rules(page):
    page.locator('game-help').click()

def press_letter(page, key):
    page.locator(f'#keyboard button[data-key={key}]').click()

# assumes words are length 5
def guess_word(page, word):
    for letter in word:
        press_letter(page, letter)
    press_letter(page, '↵')

# this function seems like it should be simple.
# why not just label each letter as correct, absent, or present!
# (this would correspond to green, black, and yellow)

# well... it turns out that wordle colors can mean different things
# guess one letter twice. it might show up as both "present / correct" and "absent"
# this is a problem for us
# because the letter isn't really absent, it's overused

# the following code properly labels these cases as "overused" instead of "absent"
# which vastly simplifies our solver later
def get_hints(page, guess_num):
    rows = page.query_selector_all('game-row')
    tiles = rows[guess_num-1].query_selector_all('div.row game-tile')
    get_letter = lambda tile: tile.get_attribute('letter')
    get_evaluation = lambda tile: tile.get_attribute('evaluation')

    letters = list(map(get_letter, tiles))
    evals = list(map(get_evaluation, tiles))
    hints = list(zip(letters, evals))

    get_all_evals = lambda letter: set([e for l, e in hints if l == letter])
    letter_evals = {letter: get_all_evals(letter) for letter in letters}

    conflicting = lambda l: len(letter_evals[l]) > 1
    fix_conflicting = lambda letter, eval: 'overused' if conflicting(letter) and eval == 'absent' else eval

    cleaned_hints = [(letter, fix_conflicting(letter, eval)) for letter, eval in hints]
    return cleaned_hints

def all_correct(page, hints):
    if len(hints) == 0:
        return False
    return all([i[1] == 'correct' for i in hints[-1]])

# to be run after all 6 guesses were wrong
def read_solution(page):
    element = page.query_selector('game-toast')
    return element.get_attribute('text')


# ------------------------------------------------------------------------------
# Solver Code
# ------------------------------------------------------------------------------

def prune_words(words, all_hints):

    valid_words = [i for i in words]
    for guess_hints in all_hints:
        # for simpler functions, lets get the word letters, hints letters, and evals, all together
        # collate stores data in the following format:
        # [(word_letter, guessed_letter, eval_of_guessed_letter), ...]
        collate = lambda word: zip(word, *zip(*guess_hints))
        is_correct = lambda triple: triple[2] == 'correct'
        is_absent = lambda triple: triple[2] == 'absent'
        is_present = lambda triple: triple[2] == 'present'
        is_overused = lambda triple: triple[2] == 'overused'

        # the correct letter should be in the same place in the word
        keep_correct = lambda word: all(
            [l == g for l, g, _ in filter(is_correct, collate(word))]
        )

        # the absent letter should not be in the word
        exclude_absent = lambda word: all(
            g not in word for _, g, _ in filter(is_absent, collate(word))
        )

        # the guessed letter should not be in the same place, but should be in the word
        move_present = lambda word: all(
            l != g and g in word for l, g, _ in filter(is_present, collate(word))
        )

        # this one is a bit tricky. here we just say "don't put it in the same spot"
        # but in general, we should do something more complicated that depends on how it was overused
        # if it was overused with a green, then exclude it from all other spots (except green spots)
        # if it was overused with a yellow, exclude it from this spot, not other spots, and restrict the number of times this letter can show up in a word
        # if this fancy nonsense were implemented, I think the only optimizations left would be to have heuristics on words to guess
        remove_overused = lambda word: all(
             l != g for l, g, _ in filter(is_overused, collate(word))
        )

        rules = [keep_correct, exclude_absent, move_present, remove_overused]
        is_valid = lambda word: all(f(word) for f in rules)

        valid_words = list(filter(is_valid, valid_words))

    return valid_words




# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------

def make_guess(page, hints, auto=False):
    if auto:
        candidates = prune_words(words, hints)
        guess = random.choice(candidates)
        print(f'Guessing {guess}...')
        guess_word(page, guess)
        return guess

    # manual play
    guess = input('Guess a word: ')
    if len(guess) != 5:
        print(f'Error: {guess} must be 5 letters long.')
        return make_guess(page, hints, auto)
    elif guess not in words:
        print(f'Error: {guess} is not a valid wordle word.')
        return make_guess(page, hints, auto)
    else:
        guess_word(page, guess)
        return guess

if __name__ == '__main__':

    if len(sys.argv) == 1:
        print(f'Playing comamnd line wordle...\nTo use the auto solver, try python3 {sys.argv[0]} --auto')
        auto = False
        headless = True
    elif len(sys.argv) == 2 and sys.argv[1] == '--auto':
        print(f'Using wordle solver...\nTo play manually via command line, try python3 {sys.argv[0]}')
        auto = True
        headless = False
    else:
        print(f'Valid inputs are python3 {sys.argv[0]} with an optional --auto')
        exit(0)

    with open('words.txt', 'r') as f:
        words = [i.strip('\n').strip('"') for i in f.read().split(',')]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto('https://www.nytimes.com/games/wordle/index.html')

        bypass_rules(page)

        guesses = []
        hints = []
        plausible = words

        while not all_correct(page, hints) and len(guesses) < 6:
            guess = make_guess(page, hints, auto)
            guesses.append(guess)
            time.sleep(2.1)
            hints.append(get_hints(page, len(guesses)))
            print(hints[-1])
            plausible = prune_words(words, hints)

        if all_correct(page, hints):
            print(f'The word was {guesses[-1].upper()}, nice job!')
        else:
            print(f'The word was {read_solution(page)}, better luck next time!')
