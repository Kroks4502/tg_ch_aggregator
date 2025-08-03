# Telegram Channel Aggregator

[![Deploy Telegram Channel Aggregator](https://github.com/Kroks4502/tg_ch_aggregator/actions/workflows/deploy.yml/badge.svg)](https://github.com/Kroks4502/tg_ch_aggregator/actions/workflows/deploy.yml)
[![codestyle](https://github.com/Kroks4502/tg_ch_aggregator/actions/workflows/codestyle.yml/badge.svg)](https://github.com/Kroks4502/tg_ch_aggregator/actions/workflows/codestyle.yml)

[![Python][Python-badge]][Python-url]
[![Pyrogram][Pyrogram-badge]][Pyrogram-url]
[![Postgres][Postgres-badge]][Postgres-url]
[![Docker][Docker-badge]][Docker-url]

Create your own news feeds from Telegram channels!

## Features

- Create categories where messages from sources will be placed
- Filter messages from sources to prevent forwarding of unwanted messages by hashtags, links, text, entities (entity_type), or message types
- Forward/repost messages into categories
- Clean message texts (in reposting mode) from unwanted content
- Bot notifications based on the number of messages or matching regular expressions
- Full management of categories, sources, filters, and text cleaning via the bot

## Installation

### Prerequisites

- Docker 24.0.0 or higher
- Docker Compose 2.25.0 or higher
- PostgreSQL 14 or higher
- Python 3.10 or higher
- Pyrogram 2.0
- Telegram API credentials

### Telegram App Setup

To set up your Telegram bot and obtain necessary credentials, follow these steps:
1. **Get Telegram Bot Token**: Create a new bot using [@BotFather](https://t.me/BotFather) on Telegram to obtain your `BOT_TOKEN`.
2. **Creating your Telegram Application**: Follow the instructions on [Telegram Core](https://core.telegram.org/api/obtaining_api_id) to get your `API_ID` and `API_HASH`.

### Quick Start Development

1. **Clone the Repository**

   ```bash
   git clone https://github.com/Kroks4502/tg_ch_aggregator.git
   cd tg_ch_aggregator
   ```

2. **Configure Environment Variables**

   Create a [.env](.env.template) file in the root directory with the following content:

   ```env
   TELEGRAM_API_ID=
   TELEGRAM_API_HASH=
   TELEGRAM_BOT_TOKEN=
   
   POSTGRES_DB=tgbot
   POSTGRES_USER=tgbot
   POSTGRES_PASSWORD=tgbot
   POSTGRES_HOST=postgres
   POSTGRES_PORT=5432
   ```

3. **Create Telegram sessions (this will be interactive)**

   - Enter User phone number
   - Enter confirmation code
   - Enter two-step verification password (if it's enabled)

   ```shell
   ./docker/docker-dev-run.sh create_sessions
   ```

4. **Start the main application**

   ```shell
   ./docker/docker-dev-run.sh start
   ```

### Deployment

1. **Fork the repository**

2. **Configure Secrets**

   Create secrets in the repository settings "Settings" -> "Secrets and variables" -> "Actions" -> "New repository secret":

   Telegram API credentials:
   - `APP_TELEGRAM_API_ID`
   - `APP_TELEGRAM_API_HASH`
   - `APP_TELEGRAM_BOT_TOKEN`

   PostgreSQL credentials:
   - `APP_POSTGRES_DB`
   - `APP_POSTGRES_USER`
   - `APP_POSTGRES_PASSWORD`
   - `APP_POSTGRES_HOST`
   - `APP_POSTGRES_PORT`

   Deployment credentials:
   - `DEPLOY_HOST`
   - `DEPLOY_HOST_SSH_USER`
   - `DEPLOY_HOST_SSH_KEY`

   Integration tests credentials:
   - `TEST_TELEGRAM_BOT_TOKEN` - bot token for integration tests (should be added to channels as administrator). Recommended not to use the same bot as the main bot, because it can cause throttling.
   - `TEST_TELEGRAM_SOURCE_CHANNEL_ID`
   - `TEST_TELEGRAM_AGGREGATOR_CHANNEL_ID`

3. **Deploy**

   Run the workflow "[Deploy Telegram Channel Aggregator](.github/workflows/deploy.yml)"

4. **Create Telegram sessions in Docker container (this will be interactive)**

   The workflow "[Deploy Telegram Channel Aggregator](.github/workflows/deploy.yml)" will start the container `create_sessions` and wait for the authorization parameters if don't have session files.

   Check last logs:
   ```shell
   docker logs --tail 20 tg_ch_aggregator-create_sessions-1
   ```

   Attach to the container to enter the authorization parameters:
   ```shell
   docker attach tg_ch_aggregator-create_sessions-1
   ```

5. **Check the deployment**

   ```shell
   docker ps
   docker logs
   ```

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

[Python-url]: https://www.python.org/
[Python-badge]: https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54

[Pyrogram-url]: https://docs.pyrogram.org/
[Pyrogram-badge]: https://img.shields.io/badge/Pyrogram-ff1709?style=for-the-badge&logo=telegram&color=bf431d

[Postgres-url]: https://www.postgresql.org/
[Postgres-badge]: https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white

[Docker-url]: https://www.docker.com/
[Docker-badge]: https://img.shields.io/badge/docker-%23316192.svg?style=for-the-badge&logo=docker&logoColor=white
