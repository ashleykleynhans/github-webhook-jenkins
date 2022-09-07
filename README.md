# Github Webhook Proxy for Jenkins

[![Python Version: 3.9](
https://img.shields.io/badge/Python%20application-v3.9-blue
)](https://www.python.org/downloads/release/python-3913/)
[![License: Apache 2.0](
https://img.shields.io/github/license/ashleykleynhans/github-webhook-jenkins?ts=300
)](https://opensource.org/licenses/GPL-3.0)

## Background

In order to send Github webhooks to your Jenkins instance, you need to expose your
Jenkins instance to the internet, which is not ideal since you will most likely want
to only make it internally accessible on its private IP over a VPN connection.

This Webhook Proxy allows you to expose it to the internet, and receives the Github
webhook and proxies it through to your Jenkins instance for you.

## Prerequisites

1. Install [ngrok](https://ngrok.com/).
```bash
brew install ngrok
```
2. Ensure your System Python3 version is 3.9, but greater than 3.9.1.
```bash
python3 -V
```
3. If your System Python is not 3.9:
```bash
brew install python@3.9
brew link python@3.9
```
4. If your Sytem Python is 3.9 but not greater than 3.9.1:
```bash
brew update
brew upgrade python@3.9
```
5Export the environment variable for your Jenkins URL that is required by the webhook:
```bash
export JENKINS_URL="http://jenkins.example.com"
```

## Testing your Webhook

1. Run the webhook receiver from your terminal.
```bash
python3 webhook.py
```
2. Open a new terminal window and use [ngrok](https://ngrok.com/) to create
a URL that is publically accessible through the internet by creating a tunnel
to the webhook receiver that is running on your local machine.
```bash
ngrok http 8090
```
4. Note that the ngrok URL will change if you stop ngrok and run it again,
   so keep it running in a separate terminal window, otherwise you will not
   be able to test your webhook successfully.
5. Update your Github repository  webhook configuration to the URL that is
   displayed while ngrok is running **(be sure to use the https one)**.
6. Change a file in the repo, commit your changes and push the changes up
   to the repo.
7. Check Jenkins to confirm whether your job ran successfully.

## Deploy to AWS Lambda

1. Create a Python 3.9 Virtual Environment:
```bash
python3 -m venv venv/py3.9
source venv/py3.9/bin/activate
```
2. Upgrade pip.
```bash
python3 -m pip install --upgrade pip
```
3. Install the Python dependencies that are required by the Webhook receiver:
```bash
pip3 install -r requirements.txt
```
4. Create a file called `zappa_settings.json` and insert the JSON content below
to configure your AWS Lambda deployment:
```json
{
    "github-webhook": {
        "app_function": "github_webhooks.app",
        "aws_region": "us-east-2",
        "lambda_description": "Github Webhook Proxy for Jenkins",
        "profile_name": "default",
        "project_name": "github-webhook",
        "runtime": "python3.9",
        "s3_bucket": "github-webhooks",
        "tags": {
           "service": "github-webhook"
        },
        "environment_variables": {
            "JENKINS_URL": "http://jenkins.example.com"
        }
    }
}
```
5. Use [Zappa](https://github.com/Zappa/Zappa) to deploy your Webhook
to AWS Lambda (this is installed as part of the dependencies above):
```bash
zappa deploy
```
6. Take note of the URL that is returned by the `zappa deploy` command,
eg. `https://1d602d00.execute-api.us-east-1.amazonaws.com/production`
   (obviously use your own and don't copy and paste this one, or your
Webhook will not work).

**NOTE:** If you get the following error when running the `zappa deploy` command:

<pre>
botocore.exceptions.ClientError:
An error occurred (IllegalLocationConstraintException) when calling
the CreateBucket operation: The unspecified location constraint
is incompatible for the region specific endpoint this request was sent to.
</pre>

This error usually means that your S3 bucket name is not unique, and that you
should change it to something different, since the S3 bucket names are not
namespaced and are global for everyone.

7. Check the status of the API Gateway URL that was created by zappa:
```bash
zappa status
```
8. Test your webhook by making a curl request to the URL that was returned
by `zappa deploy`:
```
curl https://1d602d00.execute-api.us-east-1.amazonaws.com/production
```
You should expect the following response:
```json
{"status":"ok"}
```
9. Update your Webhook URL in Github to the one returned by the
`zappa deploy` command.
