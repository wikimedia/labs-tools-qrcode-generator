#!/usr/bin/env python3
# encoding: utf-8

from flask import Flask, render_template, request, Markup, send_from_directory
from flask_mwoauth import MWOAuth
import qrcode
import qrcode.image.svg

import datetime
import urllib
import yaml
import os

app = Flask( __name__ )
app.secret_key = os.urandom(24)

# Load configuration from YAML file
__dir__ = os.path.dirname(__file__)
app.config.update( yaml.safe_load(open(os.path.join(__dir__, 'config.yaml'))))

# Get variables
base_url = app.config['OAUTH_MWURI']
api_endpoint = base_url + '/api.php'
consumer_key = app.config['CONSUMER_KEY']
consumer_secret = app.config['CONSUMER_SECRET']

# Register blueprint to app
mwoauth = MWOAuth(base_url= base_url, consumer_key=consumer_key, consumer_secret=consumer_secret)
app.register_blueprint(mwoauth.bp)

# /index route for return_to
@app.route('/index', methods=['GET'])
@app.route('/', methods=['GET'])
def index():

    # Get the URL from the query string
    url = request.args.get('urltextBox')
    username = mwoauth.get_current_user(True)

    if url is None:
        return render_template('Index.html', username=username)
    else:

        # Escape the unicode encoding from URL
        url = urllib.parse.unquote(url)

        # Get the file name based on current time
        currentTime = str(datetime.datetime.now())
        getfileName = currentTime.replace(':', '_').replace(' ', '_') + '.svg'
        fileWithPath = 'static/qrcodes/' + getfileName

        # Create the QR Code
        img = qrcode.make( url, image_factory=qrcode.image.svg.SvgImage, version=8 )
        img.save(fileWithPath)

        # Read the QR Code
        svg = open(fileWithPath).read()

        return render_template( 'Index.html', url=url, fileName=getfileName, username=username, src= Markup(svg) )


@app.route('/download/<string:filename>', methods=['GET'])
def download(filename):
    return send_from_directory( directory='static/qrcodes', filename=filename, as_attachment=True)


if __name__ == '__main__':
    app.run()