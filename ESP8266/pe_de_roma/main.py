from couveflow_auth import get_token
import lolin_v3_gpio_map as pinmap
import dht
import env
import gc
import machine
import sys
import time
import urequests

LOOP_DELAY_MINUTES = 10

HTTP_CREATED = 201
HTTP_CONFLICT = 409

DHT_PIN = pinmap.D4


def register_device(token):
    res = urequests.post(
        env.couveflow_device_register_url,
        json=env.couveflow_device_register_payload,
        headers={'Authorization': 'Token ' + token}
    )
    if res.status_code not in [HTTP_CREATED, HTTP_CONFLICT]:
        sys.exit()


def get_dht():
    return dht.DHT11(machine.Pin(DHT_PIN))


def wait_next_loop():
    time.sleep(LOOP_DELAY_MINUTES * 60)


def send_measure(label, value, token):
    payload = {
        'value': value,
        'source_label': label,
    }
    urequests.post(
        env.couveflow_device_measure_url,
        json=payload,
        headers={
            'Authorization': 'Token ' + token
        }
    )


def send_dht_data(token):
    dht = get_dht()
    dht.measure()
    send_measure(env.dht_temperature, dht.temperature(), token)
    send_measure(env.dht_humidity, dht.humidity(), token)


def main():
    token = get_token()
    register_device(token)
    while True:
        send_dht_data(token)
        gc.collect()
        wait_next_loop()
        token = get_token()  # Re-auth, in case token was invalidated


main()
