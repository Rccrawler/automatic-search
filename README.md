# automatic-search

A Windows-only Python automation tool that simulates human search behavior in Microsoft Edge — typing search queries, scrolling results, and clicking into websites — to generate realistic browser activity.

---

## What it does

The program opens Microsoft Edge and automatically performs a series of web searches from a predefined list. For each search it:

1. Launches Microsoft Edge via a `.bat` file
2. Randomly shuffles and selects search terms from a JSON file
3. Types each query into the address bar **letter by letter** with randomized delays (mimicking human typing speed)
4. Scrolls through the search results page
5. Navigates into one of the result websites using `Tab` + `Enter`
6. Scrolls inside that website
7. Goes back and repeats for the next search term
8. Skips already-used search terms to avoid repetition

All keyboard input is sent to Edge using **PowerShell's** `Wscript.Shell` COM object, which means the tool interacts at the OS level rather than through a browser driver.

---

## ⚠️ Requirements

- **Windows only** (uses PowerShell `Wscript.Shell` and `.bat` files — not compatible with Linux or macOS)
- **Microsoft Edge** installed (the default Windows browser)
- **Python 3.9+**
- No external Python packages required (standard library only)

---

## Project Structure

```
automatic-search/
│
├── run_bat.py        # Main script — orchestrates the entire automation loop
├── MoRandom.py       # Custom random number generator with mixed entropy
├── open_edge.bat     # Batch file that launches Microsoft Edge
├── searches.json     # List of search terms to use
├── config.txt        # User-editable configuration file
└── README.md         # This file
```

---

## File Reference

### `run_bat.py` — Main script

The entry point of the program. Contains all the automation logic:

| Function | Description |
|---|---|
| `open_edge()` | Runs `open_edge.bat` to launch Microsoft Edge |
| `load_searches_from_json()` | Reads `searches.json`, shuffles the list, and applies the search limit |
| `send_keys_to_edge()` | Sends keystrokes to the active Edge window via PowerShell. Supports slow (letter-by-letter) and fast modes |
| `simulate_interaction_in_edge()` | Scrolls the results page, navigates into a website, scrolls inside it, and goes back |
| `load_config()` | Reads `config.txt` and returns the current settings |
| `main()` | Ties everything together: loads config → loads searches → opens Edge → runs the search loop |

### `MoRandom.py` — Custom random generator

A custom implementation of Python's `random.Random` that adds **extra entropy** to avoid generating predictable sequences:

- Seeds itself using a SHA-256 hash of: current time (nanoseconds) + `os.urandom(8)` + any provided value
- Adds a time-based jitter to every `random()` call to break the standard Mersenne Twister pattern
- Provides the same interface as Python's built-in `random` module (`shuffle`, `choice`, `randint`, `sample`, etc.)

This module is imported in `run_bat.py` and used wherever random behavior is needed.

### `open_edge.bat` — Edge launcher

A minimal batch script:
```bat
@echo off
start msedge
```
Launches Microsoft Edge using the Windows `start` command.

### `searches.json` — Search terms list

A JSON file containing an array of search queries (~400 terms). These are everyday topics in Spanish, making the browser activity look like organic human usage.

```json
{
  "searches": [
    "receta de pan casero",
    "tiempo hoy",
    "noticias de hoy",
    ...
  ]
}
```

You can add, remove, or replace any search term freely.

### `config.txt` — Configuration

Plain-text configuration file. Edit this to control the behavior of the script:

```
limite_busquedas = 90     # Max number of searches to run (set to 'none' for all)
hacer_scroll = true       # Whether to scroll through search results and websites
entrar_en_web = true      # Whether to click into result websites
```

---

## How to run

```bash
python run_bat.py
```

> Make sure you run it from the project folder and that Edge is not already open in a state that would block keyboard input.

---

## Architecture overview

```
run_bat.py
    │
    ├── reads ──────────► config.txt
    ├── reads ──────────► searches.json
    ├── imports ────────► MoRandom.py  (shuffle / choice)
    │
    ├── launches ───────► open_edge.bat  ──► msedge (Microsoft Edge)
    │
    └── controls Edge via PowerShell (Wscript.Shell COM)
            │
            ├── Ctrl+L  → focus address bar
            ├── slow typing → send query letter by letter
            ├── PgDn keys  → scroll results
            ├── Tab + Enter → navigate into a website
            ├── PgDn keys  → scroll inside website
            └── Alt+Left   → go back to results
```

---

## Notes

- The script uses **PowerShell** internally for all keyboard simulation — no external libraries like `pyautogui` or `selenium` are needed.
- The `Wscript.Shell.AppActivate("Edge")` call ensures keystrokes are only sent when Edge is the active window, preventing accidental input to other applications.
- Random delays between keystrokes (100–300 ms) and between actions help the activity look more natural.