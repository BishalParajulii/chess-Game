# Chess Game in Python

This project is a simple two-player chess game built with Python and `pygame`. It opens a desktop window with a playable chessboard, highlights legal moves, tracks captured pieces, stores move history, and detects checkmate or stalemate.

## Features

- Two-player local chess on one computer
- Piece movement with legal move checking
- Castling support
- En passant support
- Automatic pawn promotion to queen
- Check, checkmate, and stalemate detection
- Captured piece display
- Move history panel
- Restart and quit controls

## Requirements

- Python 3
- `pygame`

## Install

Install `pygame` if it is not already available:

```bash
pip install pygame
```

## Run

From the project folder, start the game with:

```bash
python chess.py
```

## Controls

- Left click to select a piece
- Left click on a highlighted square to move
- Press `R` to restart the game
- Press `Esc` to quit

## Project File

- `chess.py`: main game file containing the board setup, move validation, drawing logic, and game loop

## References

This project was created with learning support and inspiration from:

- ChatGPT, used for coding help, explanation, and implementation guidance
- YouTube video: [Python Chess Tutorial / Reference Video](https://www.youtube.com/watch?v=OpL0Gcfn4B4&t=256s)

## Notes

This project is intended as a learning project for building a graphical chess game in Python. It focuses on playable core chess rules in a clean desktop interface using `pygame`.
