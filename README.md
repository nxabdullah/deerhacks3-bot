
# DeerHacks Discord Bot


[![DeerHacks Image](https://github.com/utmmcss/deerhacks/blob/c097731ac1a95f138462fbac6aa87ed0c7bfd191/public/backgrounds/collage.jpg?raw=true)](https://deerhacks.ca)

> DeerHacks Hackathon 2024 Discord Bot

[![Website Status](https://img.shields.io/website?down_color=red&down_message=offline&up_color=green&up_message=online&url=https%3A%2F%2Fdeerhacks.ca)](https://deerhacks.ca)

## Setup

1. Run `pip install -r requirements.txt` to install dependencies
2. Add the required `.env` file with the schema specified below
3. Gather credentials from Discord Developer Portal and add it to the `.env` file

## Relevant URL'S

- [Discord Developer Portal](https://discord.com/developers/docs/intro)

  

## Running the bot

Mac/Linux
```bash
python3 app.py
```

Windows
```bash
py app.py
```

### .env format

```bash
# Discord Bot Token taken from Discord Developer Portal
TOKEN=
# Prefix for commands
PREFIX="dh."

# Database credentials which have all user data (should be identical to database used in DeerHacks API)
DB_USER=
DB_PASS=
DB_NAME=
DB_HOST=
```
