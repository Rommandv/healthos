# Deploy Health OS to Hetzner VPS

This guide deploys the Telegram bot to a Hetzner VPS and runs it with systemd.

Do not commit real secrets. Create `.env` manually on the server.

## 1. Connect to the server

```bash
ssh root@SERVER_IP
```

## 2. Install system packages

```bash
apt update && apt install -y python3 python3-venv python3-pip git
```

## 3. Clone the project

```bash
git clone https://github.com/Rommandv/healthos.git /opt/healthos
cd /opt/healthos
```

## 4. Create Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 5. Create `.env` manually

Create `/opt/healthos/.env` on the server:

```bash
nano /opt/healthos/.env
```

Use this shape, replacing placeholders with real values:

```dotenv
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Required: your numeric Telegram user id (from @userinfobot).
# The bot serves ONLY this user; without a valid id it refuses to start.
HEALTH_OS_OWNER_ID=your_telegram_numeric_id

# Optional
ANTHROPIC_MODEL=claude-3-5-haiku-latest
HEALTH_OS_TIMEZONE=Asia/Omsk
```

## 6. Check and run manually

```bash
python3 bot.py --check
python3 bot.py
```

Stop the manual run with `Ctrl+C` before enabling systemd.

## 7. Install systemd service

Copy the example unit:

```bash
cp /opt/healthos/deploy/healthos.service.example /etc/systemd/system/healthos.service
```

Reload systemd and start the bot:

```bash
systemctl daemon-reload
systemctl enable healthos
systemctl start healthos
```

Check status and logs:

```bash
systemctl status healthos
journalctl -u healthos -f
```

## 8. Update deployment

```bash
cd /opt/healthos
git pull
source .venv/bin/activate
pip install -r requirements.txt
python3 bot.py --check
systemctl restart healthos
```
