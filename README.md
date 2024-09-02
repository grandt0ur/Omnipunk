# NeoPunkXM Discord Bot
![GitHub Release](https://img.shields.io/github/v/release/grandt0ur/Omnipunk)
![Py-Cord Version](https://img.shields.io/pypi/v/py-cord)
![Reddit User Karma](https://img.shields.io/reddit/user-karma/combined/NeoUnmei?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/metalgearsolid2/Omnipunk)

NeoPunkXM is a Discord bot designed to manage age verification, provide various utility commands, and post YouTube video updates to a specified channel.

## Features

- Age verification for new members
- Manual age verification for existing members
- Restriction of adult content for underage users
- YouTube video update notifications
- Various utility and fun commands

## Setup

1. Clone this repository to your local machine.

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install discord.py python-dotenv google-api-python-client
   ```

4. Create a `.env` file in the root directory with the following content:
   ```
   BOT_TOKEN=your_discord_bot_token
   YOUTUBE_API_KEY=your_youtube_api_key
   YOUTUBE_CHANNEL_ID=your_youtube_channel_id
   DISCORD_CHANNEL_ID=your_discord_channel_id
   ```
   Replace the placeholders with your actual values.

5. Run the bot:
   ```
   python bot2.py
   ```

## Commands

- `./snipe` or `./s`: Retrieves the last deleted message in the channel.
- `./manualverify` or `./mv`: Manually triggers age verification for a user.
- `./help` or `./h`: Displays the help menu with all available commands.
- `./testchannel`: Tests the bot's ability to send messages to the specified channel.
- `./gotcha`: Displays Destiny's quote.
- `./test1`: Displays a joke.
- `./checkyoutube`: Manually checks and displays the latest YouTube video from the specified channel.

## Permissions

Most commands are restricted to users with the following roles:
- NeoPunkFM
- NPFM Affiliate
- Neo-Engineer

## Age Verification

- New members are automatically prompted for age verification upon joining.
- Users under 18 are restricted from accessing adult-only channels.
- Manual verification can be triggered by moderators using the `./manualverify` command.

## YouTube Integration

- The bot automatically checks for new videos every 5 minutes.
- New videos are posted to the specified Discord channel.
- Use `./checkyoutube` to manually check for the latest video.

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

None. Code is free. Like me :)

## Support

For support, please pray to God, cause lord knows I have no idea what im doing.
