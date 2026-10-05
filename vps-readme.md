# Station météo — VPS stack

ESP32 → MQTT → Mosquitto → Telegraf → InfluxDB → Grafana (HTTPS via Caddy).

Not tested yet: copy to the VPS and fill in the domain first.

## What's in `vps/`

- `docker-compose.yml` runs Mosquitto, Telegraf, InfluxDB, Grafana and Caddy.
- Mosquitto requires a login, with two accounts: `esp32` (publish only) and `telegraf` (read only).
- Telegraf copies the MQTT messages (`station/#`) into InfluxDB.
- Grafana loads a ready-made "Station météo" dashboard: latest values + live graphs for temperature, humidity and pressure.
- Caddy adds HTTPS to Grafana.
- `.env` holds random passwords and tokens (never share it).

## Deploy

1. Create a DNS A record pointing the domain to the VPS IP.
2. Replace `DOMAIN=CHANGE_ME` in `vps/.env` with the domain, and `BROKER = 'CHANGE_ME'` in `mqtt_station.py` with the same domain.
3. Copy the folder: `scp -r vps user@VPS_IP:~/meteo`
4. On the VPS: `cd ~/meteo && sudo chown 1883:1883 mosquitto/passwd mosquitto/acl && docker compose up -d`
5. If the VPS has a firewall: `sudo ufw allow 80,443,1883/tcp`
6. Open `https://<domain>` and log in as `admin` with `GRAFANA_ADMIN_PASSWORD` from `.env`.
7. Run `mqtt_station.py` from Thonny. Data should appear in the dashboard within about 10 s.

## Notes

- `mqtt_station.py` contains the MQTT password and the hotspot Wi-Fi credentials: don't share it.
- MQTT is password-protected but not encrypted (plain port 1883). Fine for a school demo; add TLS later.
- The ESP32 only supports 2.4 GHz Wi-Fi (the hotspot must not be 5 GHz).
- Still missing from the project plan: wind (anemometer), CSV logging / RTC or NTP, alerts.