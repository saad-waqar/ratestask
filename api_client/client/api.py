from flask import request
from flask import abort, jsonify


from . import app
from .queries import average_rates_query, average_rates_query_null, insert_price
from .helpers import prepare_rates_response, convert_currency_in_param_dict


@app.route('/rates', methods=['GET'])
@app.route('/rates_null', methods=['GET'])
def rates():
    required_params = ('date_from', 'date_to', 'origin', 'destination')
    params = dict()

    try:
        params.update(
            {param: request.args[param] for param in required_params}
        )
        if not all(params.values()):
            raise KeyError

    except KeyError:
        abort(400, 'Params date_from, date_to, origin, destination are required')

    if request.path == '/rates_null':
        iterable = average_rates_query_null(**params)
    else:
        query = average_rates_query(**params)
        iterable = query.all()

    return jsonify(prepare_rates_response(iterable))


@app.route('/upload_price', methods=['POST'])
def upload_price():
    required_params = ('date_to', 'origin_code', 'destination_code', 'price')
    optional_params = ('date_from', 'currency')
    params = dict()

    try:
        params.update(
            {param: request.form[param] for param in required_params}
        )
        if not all(params.values()):
            raise KeyError

        for param in optional_params:
            if param in request.form:
                params[param] = request.form[param]

    except KeyError:
        abort(400, 'Please provide all the following params: '
                   'date_from date_to origin_code destination_code price000')
    try:
        params['price'] = float(params['price'])
    except ValueError:
        abort(400, 'Please give price in proper format')

    if params.get('currency') and params.get('currency') != 'USD':
        params = convert_currency_in_param_dict(params)
        del params['currency']

    response = insert_price(**params)

    if response == 'success':
        return response, 200

    abort(400, response)
