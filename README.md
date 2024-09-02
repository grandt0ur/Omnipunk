# NeoPunkXM Discord Bot

![GitHub Release](https://img.shields.io/github/v/releases/grandt0ur/Omnipunk)
[![Made with Python](https://img.shields.io/badge/Python->=3.10-blue?logo=python&logoColor=white)](https://python.org "Go to Python homepage")
[![Made with SQLite](https://img.shields.io/badge/SQLite-3-blue?logo=sqlite&logoColor=white)](https://www.sqlite.org/index.html "Go to SQLite homepage")
![maintained - yes](https://img.shields.io/badge/maintained-yes-blue)
![GitHub repo size](https://img.shields.io/github/repo-size/metalgearsolid2/Omnipunk)

NeoPunkXM is a Discord bot designed to manage age verification, provide various utility commands, and post YouTube video updates to a specified channel.

## Features

- **Age Verification**: Automatically and manually verify user ages.
- **Content Restriction**: Restrict adult content for underage users.
- **YouTube Integration**: Post YouTube video updates to a specified channel.
- **Utility Commands**: Various utility and fun commands.

## Setup

1. **Clone this repository** to your local machine:
   ```bash
   git clone https://github.com/yourusername/neopunkxm-bot.git
   cd neopunkxm-bot
   ```

2. **Create a virtual environment and activate it**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** in the root directory with the following content:
   ```env
   BOT_TOKEN=your_discord_bot_token
   YOUTUBE_API_KEY=your_youtube_api_key
   YOUTUBE_CHANNEL_ID=your_youtube_channel_id
   DISCORD_CHANNEL_ID=your_discord_channel_id
   ```
   Replace the placeholders with your actual values.

5. **Run the bot**:
   ```bash
   python bot2.py
   ```

## Commands

- `./snipe` or `./s`: Retrieves the last deleted message in the channel.
- `./manualverify` or `./mv`: Manually triggers age verification for a user.
- `./help` or `./h`: Displays the help menu with all available commands.
- `./gotcha`: Displays Destiny's quote.
- `./test1`: Displays a joke.
- `./checkyoutube`: Manually checks and displays the latest YouTube video from the specified channel.

## Permissions

Most commands are restricted to users with the following roles:
- **NeoPunkFM**
- **NPFM Affiliate**
- **Neo-Engineer**

## Age Verification

- **Automatic Verification**: New members are automatically prompted for age verification upon joining.
- **Content Restriction**: Users under 18 are restricted from accessing adult-only channels.
- **Manual Verification**: Can be triggered by moderators using the `./manualverify` command.

## YouTube Integration

- **Automatic Checks**: The bot automatically checks for new videos every 5 minutes.
- **Manual Checks**: Use `./checkyoutube` to manually check for the latest video.

## Logging

The bot logs important events and errors to both the console and a `bot.log` file.

## Database

User age information is stored in an SQLite database (`users.db`) for persistent age verification.

## Contributing

Contributions to improve the bot are welcome. Please follow these steps:
1. Fork the repository
2. Create a new branch for your feature
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
