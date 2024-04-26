import os
import uuid
from flask import Flask, abort, redirect, request
import requests
from urllib.parse import quote
import logging

app = Flask(__name__)

# comment these lines out to see requests come into the server
# these lines are here because, otherwise, the auth `code` is logged out to the console - which is not good!
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Global vars - we could use a file instead
access_token = None
refresh_token = None
last_state = None

# Constants 
redirect_uri = "http://localhost:5000/callback"
authorize_endpoint = f"https://{os.environ["DOMAIN"]}/authorize"
token_endpoint = f"https://{os.environ["DOMAIN"]}/oauth/token"

def uriencode(string):
    return quote(string, safe='/', encoding=None, errors=None)

# https://auth0.com/docs/get-started/authentication-and-authorization-flow/authorization-code-flow/call-your-api-using-the-authorization-code-flow
# This route is our 'dashboard', which, for this example, we pretend needs an access token to make API calls.
# The API calls are not actually implemented here: instead, for example purposes, we return the tokens to the client. 
# NEVER RETURN THE TOKENS TO THE CLIENT IF DOING THIS FOR REAL. This is only here to illustrate that we have the tokens, ready to be used in the backend.
@app.route("/")
def dashboard():
    if not access_token:
        return f"No access token to access API with! <a href='/login'>Login</a>"
    return f"Dashboard! Ready to make API requests from the backend.<br>Access Token: {access_token}<br>Refresh Token: {refresh_token}"


@app.route("/login")
def step_1():
    # The state param will be repeated back to you by the Auth server. 
    # It can be any value we wish, but should be different each time we complete Step 1.
    # So this bit of the code just generates a new, random string to be our state.
    # I have used a global variable here. We could also save the state off to a file, that would be fine.
    global last_state
    last_state = str(uuid.uuid4())
    scopes = "offline_access"
    
    # Send the user's browser off to authenticate and authorize with the Auth server
    return redirect(
        f"{authorize_endpoint}?response_type=code&client_id={os.environ["CLIENT_ID"]}&redirect_uri={redirect_uri}&scope={scopes}&state={last_state}"
    )
    
    
@app.route("/callback")
def step_2():
    # the url requested of the server looks like: http://localhost:5000/callback?code=329rguicblwdhvhjsvd...
    # the Auth server needs to be configured by the Admin to accept this as a 'callback URL': http://localhost:5000/callback
    code = request.args.get("code", None)
    repeated_state = request.args.get("state", None)
    
    if not code:
        print("No code", request.url)
        abort(400)
    
    if not repeated_state:
        print("No state", request.url)
        abort(400)
    
    # State is an extra layer of security. The state we set in the redirect in Step 1, 
    # should match the `state` query parm in this, Step 2.
    # If they don't match, we should reject the request.
    if last_state != repeated_state:
        print("State doesn't match what we specified!")
        abort(400)
    
    # contact the auth server again, this time to exchange our code for tokens. You should only ever contact the Auth server in this way from your server.
    # this is because we are using the client_secret here, which should NEVER be sent to the user's browser.
    resp = requests.post(f"{token_endpoint}", {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": os.environ["CLIENT_ID"],
            "client_secret": os.environ["CLIENT_SECRET"],
            "redirect_uri": redirect_uri
        }, headers={
        "content-type": "application/x-www-form-urlencoded",
    })
    
    # the JSON response is of the form: { access_token, refresh_token }
    json = resp.json()
    
    # for convenience, I've stored the tokens in memory - they will be lost if the server restarts.
    # A better alternative would be to store them in a file on the system, or in a database, like SQLite3.
    global access_token, refresh_token
    access_token = json["access_token"]
    refresh_token = json["refresh_token"]
    
    # we are now good to go! in this case, we redirect to the homepage, which can now be served properly by this Server as it has its tokens.
    return redirect(
        f"http://localhost:5000"
    )
