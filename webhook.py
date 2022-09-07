#!/usr/bin/env python3
import os
import sys
import argparse
import requests
from flask import Flask, request, jsonify, make_response


app = Flask(__name__)

try:
    jenkins_url = os.environ['JENKINS_URL']
except KeyError as e:
    print('JENKINS_URL environment variable is not set')
    sys.exit(1)


def get_args():
    parser = argparse.ArgumentParser(
        description='Github Webhook proxy for Jenkins'
    )

    parser.add_argument(
        '-p', '--port',
        help='Port to listen on',
        type=int,
        default=8090
    )

    parser.add_argument(
        '-H', '--host',
        help='Host to bind to',
        default='0.0.0.0'
    )

    return parser.parse_args()


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify(
        {
            'status': 'error',
            'msg': f'{request.url} not found',
            'detail': str(error)
        }
    ), 404)


@app.errorhandler(500)
def internal_server_error(error):
    return make_response(jsonify(
        {
            'status': 'error',
            'msg': 'Internal Server Error',
            'detail': str(error)
        }
    ), 500)


@app.route('/')
def ping():
    return make_response(jsonify(
        {
            'status': 'ok'
        }
    ), 200)


@app.route('/', methods=['POST'])
def webhook_handler():
    jenkins_webhook_url = f'{jenkins_url}/github-webhook/'

    r = requests.post(
        jenkins_webhook_url,
        json=request.get_json(),
        headers=request.headers
    )

    if not r.status_code == 200:
        return make_response(jsonify(
            {
                'status': 'error',
                'msg': f'Failed to trigger jenkins webhook ({jenkins_webhook_url}), received HTTP status code: {r.status_code}'
            }
        ), 500)

    return make_response(jsonify(
        {
            'status': 'ok'
        }
    ), 200)


if __name__ == '__main__':
    args = get_args()
    app.run(host=args.host, port=args.port)
