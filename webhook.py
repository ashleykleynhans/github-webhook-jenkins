#!/usr/bin/env python3
import os
import sys
import argparse
import requests
import logging
import logging.handlers
from flask import Flask, request, jsonify, make_response, abort

LOG_LEVEL = logging.INFO
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
    logging.info(f'Forwarding to Jenkins URL: {jenkins_webhook_url}')

    headers = {
        'Content-Type': 'application/json',
        'X-GitHub-Event': request.headers.get('X-GitHub-Event', ''),
        'X-GitHub-Delivery': request.headers.get('X-GitHub-Delivery', ''),
        'X-GitHub-Hook-ID': request.headers.get('X-GitHub-Hook-ID', ''),
        'X-GitHub-Hook-Installation-Target-ID': request.headers.get('X-GitHub-Hook-Installation-Target-ID', ''),
        'X-GitHub-Hook-Installation-Target-Type': request.headers.get('X-GitHub-Hook-Installation-Target-Type', ''),
        'User-Agent': request.headers.get('User-Agent', 'GitHub-Hookshot')
    }

    r = requests.post(
        jenkins_webhook_url,
        json=request.get_json(),
        headers=headers
    )

    if r.status_code == 404:
        logging.error(r.text)
        abort(404)

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


def setup_logging():
    logging.getLogger().setLevel(LOG_LEVEL)
    formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logging.getLogger().addHandler(stream_handler)


# Configure logging at module load time (required for AWS Lambda/Zappa)
setup_logging()


if __name__ == '__main__':
    args = get_args()
    app.run(host=args.host, port=args.port)
