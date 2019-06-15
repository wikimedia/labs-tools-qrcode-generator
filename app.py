#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, Markup, \
    send_from_directory, session
from flask_mwoauth import MWOAuth
import requests_oauthlib
import requests
import qrcode
import qrcode.image.svg

import datetime
import urllib
import yaml
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load configuration from YAML file
__dir__ = os.path.dirname(__file__)
app.config.update(yaml.safe_load(open(os.path.join(__dir__, 'config.yaml'))))

# Get variables
base_url = app.config['OAUTH_MWURI']
api_endpoint = base_url + '/api.php'
consumer_key = app.config['CONSUMER_KEY']
consumer_secret = app.config['CONSUMER_SECRET']

# Register blueprint to app
mwoauth = MWOAuth(base_url=base_url, consumer_key=consumer_key, consumer_secret=consumer_secret)
app.register_blueprint(mwoauth.bp)


# /index route for return_to
@app.route('/index', methods=['GET'])
@app.route('/', methods=['GET'])
def index():
    # Get the URL from the query string
    url = request.args.get('urltextBox')
    username = mwoauth.get_current_user(True)

    if url is None:
        return render_template('index.html', username=username)
    else:

        # Escape the unicode encoding from URL
        url = urllib.parse.unquote(url)

        # Get the file name based on current time
        currentTime = str(datetime.datetime.now())
        getfileName = currentTime.replace(':', '_').replace(' ', '_') + '.svg'
        fileWithPath = 'static/qrcodes/' + getfileName

        # Create the QR Code File
        img = qrcode.make(url, image_factory=qrcode.image.svg.SvgImage, version=8)
        img.save(fileWithPath)

        # Read the QR Code File
        svg = open(fileWithPath).read()

        return render_template('index.html', url=url, fileName=getfileName, username=username, src=Markup(svg))


@app.route('/download/<string:filename>', methods=['GET'])
def download(filename):
    return send_from_directory(directory='static/qrcodes', filename=filename, as_attachment=True)


@app.route('/upload', methods=['POST'])
def upload():
    # Taken Data from the Form
    oldfileName = request.form.get('oldfileName', None)
    description = request.form.get('description', None)
    newfileName = request.form.get('newfileName', None)

    # Taken Date and Username for Template
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    username = mwoauth.get_current_user(True)

    # Wikitext for File content
    text = "=={{int:filedesc}}==\n{{Information" + \
           "\n|description=" + description + \
           "\n|date=" + date + \
           "\n|source={{own}}" + \
           "\n|author=[[User:" + username + "|" + username + "]]" + \
           "\n}}\n\n=={{int:license-header}}==\n{{self|cc-by-sa-4.0}}"

    # Authenticate Session
    ses = authenticated_session()

    # Variable to set error state
    error = None

    if None not in (oldfileName, newfileName, ses):
        # API Parameter to get CSRF Token
        csrfParam = {
            "action": "query",
            "meta": "tokens",
            "format": "json"
        }

        Response = requests.get(url=api_endpoint, params=csrfParam, auth=ses)
        DATA = Response.json()
        CSRF_TOKEN = DATA["query"]["tokens"]["csrftoken"]

        # API Parameter to upload the file
        uploadParam = {
            "action": "upload",
            "filename": newfileName,
            "text": text,
            "format": "json",
            "token": CSRF_TOKEN,
            "ignorewarnings": 1
        }

        # Read the file for POST request
        FILE = {
            'file': open('static/qrcodes/' + oldfileName, 'rb')
        }

        Response = requests.post(url=api_endpoint, files=FILE, data=uploadParam, auth=ses)
        DATA = Response.json()

        # Try block to get Link and URL
        try:
            wikifileURL = DATA["upload"]["imageinfo"]["descriptionurl"]
            fileLink = DATA["upload"]["imageinfo"]["url"]
        except:
            error = True
            render_template('upload.html', username=username, error=error)

        return render_template('upload.html', wikifileURL=wikifileURL, fileLink=fileLink,
                               username=username, error=error)

    # If everything goes wrong append error
    error = True
    return render_template('upload.html', username=username, error=error)


def authenticated_session():
    if 'mwoauth_access_token' in session:
        auth = requests_oauthlib.OAuth1(
            client_key=consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=session['mwoauth_access_token']['key'],
            resource_owner_secret=session['mwoauth_access_token']['secret']
        )
        return auth
    else:
        return None

if __name__ == '__main__':
    app.run()
