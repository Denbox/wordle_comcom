# wordle_comcom
Live coded wordle scraper + solver, based off of Cory Doctorow's competitive compatibility concept. There have been many wordle *solvers*, but not many wordle *interfaces*. This project will allow us to enter wordle guesses on the command line. Instead of doing this ourselves, we will write a solver to do it. We can watch the computer load the website and play by itself. Fun!

# Changes
The original code was live coded in about 1 hour, with 30 minutes of fixes afterwards.
This version is cleaned up, easier to read, and emphasizes the competitive compatibility concept.

## Dependencies
`python3` with the `playwright` package

## Run
`python3 solve.py` to play via the command line, or `python3 solve.py --auto` to let the computer do it.
Without an alternative wordle client, it would not be easy to add a solver to wordle itself.
