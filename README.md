# Cross-Browser Bookmark Tracker

This program allows you to track and manage bookmarks across multiple web browsers (Chrome, Firefox, and Edge) on your Windows machine.

## Features

- Automatically detects and imports bookmarks from Chrome, Firefox, and Edge
- Maintains a centralized SQLite database of all bookmarks
- Tracks when bookmarks were added and last updated
- Preserves folder structure from each browser
- Simple command-line interface for managing bookmarks

## Requirements

- Python 3.6 or higher
- Windows operating system
- One or more of the following browsers installed:
  - Google Chrome
  - Mozilla Firefox
  - Microsoft Edge

## Installation

1. Clone or download this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the program:
   ```
   python bookmark_tracker.py
   ```

2. Use the menu options:
   - Option 1: Update bookmarks (scans all browsers and updates the database)
   - Option 2: View all bookmarks (displays all bookmarks from all browsers)
   - Option 3: Exit the program

## How It Works

The program:
1. Scans the default locations for each browser's bookmark files
2. Parses the bookmark data from each browser's specific format
3. Stores all bookmarks in a SQLite database
4. Maintains the folder structure from each browser
5. Tracks when bookmarks were added and last updated

## Notes

- The program requires read access to your browser profile directories
- Bookmarks are stored in a local SQLite database file (`bookmarks.db`)
- The program will automatically create the database file when first run
- Each time you update bookmarks, it will sync any changes from your browsers

## Security

- All data is stored locally on your machine
- The program only reads bookmark data, it does not modify your browser bookmarks
- No data is sent over the network