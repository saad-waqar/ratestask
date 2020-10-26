import json
import requests

from .settings import OPENEXCHANGE_API_KEY
from .constants import OPENEXCHANGE_CONVERSION_URL


def prepare_rates_response(query_iterable):
    results = []

    for day, avg in query_iterable:
        results.append(
            {
                "day": str(day),
                "average_price": float(avg) if avg is not None else None
            }
        )

    return results


def convert_currency_in_param_dict(params):
    currency = params['currency']
    price = params['price']

    url = OPENEXCHANGE_CONVERSION_URL.format(OPENEXCHANGE_API_KEY)
    response = requests.get(url, timeout=60)

    try:
        response.raise_for_status()
    except Exception:
        raise Exception('Currency conversion failed')

    json_response = json.loads(response.text)

    if currency not in json_response['rates']:
        raise Exception('Given currency is not supported')

    params['price'] = price/json_response['rates'][currency]
    return params
