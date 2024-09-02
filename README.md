# NeoPunkXM Bot v1.0.2

## Overview

NeoPunkXM Bot is a versatile Discord bot designed to enhance your server with a variety of features, including user management, announcements, and miscellaneous fun commands. This release includes several key functionalities and improvements to make your server management more efficient and engaging.

## Key Features

### User Management
- **Manual Verification**: Allows administrators to manually verify users' ages and manage access to age-restricted channels.
  - **Command**: `./manualverify @user`
  - **Description**: Sends an age verification prompt to the specified user.

### Announcements
- **Send Announcements**: Allows users with specific roles to send announcements to any text channel in the server.
  - **Command**: `./announce #channel <message>`
  - **Description**: Sends an announcement to the specified channel as an embed, mentioning the user who sent it.
  - **Roles Required**: `NeoPunkFM`, `NPFM Affiliate`, `Neo-Engineer`

### Miscellaneous
- **Gotcha**: A fun command that sends a predefined message.
  - **Command**: `./gotcha`
  - **Description**: Sends a fun message to the channel.
  
- **Test1**: Another fun command for sending a predefined joke.
  - **Command**: `./test1`
  - **Description**: Sends a joke to the channel.

- **Check YouTube**: Checks and displays the latest YouTube video from a specified channel.
  - **Command**: `./checkyoutube`
  - **Description**: Displays the latest YouTube video link.
  - **Roles Required**: `NeoPunkFM`, `NPFM Affiliate`, `Neo-Engineer`

### Help Command
- **Help Menu**: Provides a detailed help menu with all available commands, grouped into categories.
  - **Command**: `./help` or `./h`
  - **Description**: Displays the help menu with command descriptions and usage.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/neopunkxm-bot.git
   cd neopunkxm-bot
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your `.env` file with the necessary environment variables:
   ```
   BOT_TOKEN=your_discord_bot_token
   ANNOUNCEMENT_CHANNEL_ID=your_announcement_channel_id
   ```

4. Run the bot:
   ```bash
   python bot.py
   ```

## Requirements

- Python 3.8+
- `discord.py`
- `python-dotenv`
- `google-api-python-client`
- `matplotlib`
- `aiohttp`

## Changelog

### v1.0.2
- Improved the `announce` command to allow sending announcements to any specified channel.
- Updated the help command to reflect current commands.
- Removed deprecated and unused commands for a cleaner codebase.
- Fixed an issue with the `announce` command where the `avatar_url` attribute caused an error.

### v1.0.1
- Minor bug fixes and performance improvements.

### v1.0.0
- Initial release with core features:
  - User management with manual
