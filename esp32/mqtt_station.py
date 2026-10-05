import network, json, struct, time
from machine import Pin, I2C
from umqtt.simple import MQTTClient

WIFI_SSID = 'Nothing'
WIFI_PASS = 'daniel321'
BROKER = 'CHANGE_ME'  # VPS domain name (same as DOMAIN in vps/.env)
MQTT_USER = 'esp32'
MQTT_PASS = '585c19bcec027d178d05e21b41c7d9e2'
TOPIC = b'station/meteo'
PERIOD = 5  # seconds between publishes

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
BMP = 0x77
SHT = 0x40
OSS = 3
AC1, AC2, AC3, AC4, AC5, AC6, B1, B2, MB, MC, MD = struct.unpack('>hhhHHHhhhhh', i2c.readfrom_mem(BMP, 0xAA, 22))

def read_bmp():
    i2c.writeto_mem(BMP, 0xF4, b'\x2e'); time.sleep_ms(5)
    ut = struct.unpack('>H', i2c.readfrom_mem(BMP, 0xF6, 2))[0]
    i2c.writeto_mem(BMP, 0xF4, bytes([0x34 + (OSS << 6)])); time.sleep_ms(30)
    d = i2c.readfrom_mem(BMP, 0xF6, 3)
    up = ((d[0] << 16) + (d[1] << 8) + d[2]) >> (8 - OSS)
    x1 = ((ut - AC6) * AC5) >> 15
    x2 = (MC << 11) // (x1 + MD)
    b5 = x1 + x2
    b6 = b5 - 4000
    x1 = (B2 * ((b6 * b6) >> 12)) >> 11
    x2 = (AC2 * b6) >> 11
    x3 = x1 + x2
    b3 = (((AC1 * 4 + x3) << OSS) + 2) >> 2
    x1 = (AC3 * b6) >> 13
    x2 = (B1 * ((b6 * b6) >> 12)) >> 16
    x3 = ((x1 + x2) + 2) >> 2
    b4 = (AC4 * (x3 + 32768)) >> 15
    b7 = (up - b3) * (50000 >> OSS)
    p = (b7 * 2) // b4 if b7 < 0x80000000 else (b7 // b4) * 2
    x1 = ((p >> 8) * (p >> 8) * 3038) >> 16
    x2 = (-7357 * p) >> 16
    p += (x1 + x2 + 3791) >> 4
    return p / 100

def read_sht():
    i2c.writeto(SHT, b'\xf3'); time.sleep_ms(100)
    t = struct.unpack('>H', i2c.readfrom(SHT, 3)[:2])[0] & 0xFFFC
    i2c.writeto(SHT, b'\xf5'); time.sleep_ms(50)
    h = struct.unpack('>H', i2c.readfrom(SHT, 3)[:2])[0] & 0xFFFC
    return -46.85 + 175.72 * t / 65536, -6 + 125 * h / 65536

def wifi():
    w = network.WLAN(network.STA_IF)
    w.active(True)
    if not w.isconnected():
        w.connect(WIFI_SSID, WIFI_PASS)
        t0 = time.time()
        while not w.isconnected():
            if time.time() - t0 > 20:
                raise RuntimeError('wifi timeout')
            time.sleep(0.5)
    return w

w = wifi()
print('IP:', w.ifconfig()[0])
mq = MQTTClient('esp32-station', BROKER, user=MQTT_USER, password=MQTT_PASS, keepalive=30)
mq.connect()
print('MQTT connected to', BROKER)

while True:
    try:
        wifi()
        t, h = read_sht()
        p = read_bmp()
        mq.publish(TOPIC, json.dumps({'t': round(t, 2), 'h': round(h, 1), 'p': round(p, 1)}))
    except Exception as e:
        print('err:', e)
        try:
            mq.connect()
        except Exception:
            pass
    time.sleep(PERIOD)
