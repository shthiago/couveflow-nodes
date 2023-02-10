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

DHT_PIN = pinmap.D3
HYDROMETER_PIN = 0
LOCK_PIN = pinmap.D5
LED_PIN = pinmap.D4

HYGROMETER_DRY = 732
HYGROMETER_WATER = 321


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

def led_up():
    p = machine.Pin(LED_PIN, machine.Pin.OUT)
    p.off()

def led_down():
    p = machine.Pin(LED_PIN, machine.Pin.OUT)
    p.on()


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


def send_hygrometer_data(token):
    hygrometer = machine.ADC(HYDROMETER_PIN)
    value = hygrometer.read()
    pctg = 100 * (1 - ((value - HYGROMETER_WATER) / (HYGROMETER_DRY - HYGROMETER_WATER)))
    pctg = round(pctg, 2)
    send_measure(env.hygrometer_value, pctg, token)


def pin_lock():
    # External lock, to avoid measure being sent before
    # setup is complete
    p2 = machine.Pin(LOCK_PIN, machine.Pin.IN)

    led_up()
    while p2.value() == 1:
        pass
    led_down()

def main():
    token = get_token()
    register_device(token)
    while True:
        try:
            pin_lock()
            send_dht_data(token)
            send_hygrometer_data(token)
            gc.collect()
            wait_next_loop()
            token = get_token()  # Re-auth, in case token was invalidated
        except:
            machine.reset()

main()
