import env
import urequests


def get_token():
    res = urequests.post(env.couveflow_auth_url,
                         json=env.couveflow_auth_payload)
    return res.json()['token']
