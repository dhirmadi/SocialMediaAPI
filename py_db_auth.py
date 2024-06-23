import sys
import logging
import dropbox
from dropbox.oauth import DropboxOAuth2FlowNoRedirect
from dotenv import load_dotenv, set_key
import os

"""
Script to manage Dropbox OAuth2 authentication and update configuration.

This script facilitates OAuth2 authentication with Dropbox using the Dropbox SDK.
It reads configuration details from a specified .env file, including app key and secret,
and manages the OAuth2 flow to obtain a refresh token. The refresh token is then used
to create a Dropbox client instance, which can be used to interact with the Dropbox API.

Functions:
- start_initial_auth: Initiates the OAuth2 flow for Dropbox authentication.
- get_dropbox_client: Creates and returns a Dropbox client instance using the refresh token.
- update_env_file: Updates the .env file with the latest refresh token.

Usage:
Ensure the script is run with the path to the .env file as an argument:
    python script.py <path_to_env_file>
    
NOTE: Requires initial temporary DropBox API Key to create full key and refresh key
"""

# Setup basic logging
logging.basicConfig(level=logging.INFO)

def start_initial_auth(app_key, app_secret):
    try:
        auth_flow = DropboxOAuth2FlowNoRedirect(app_key, use_pkce=True, token_access_type='offline')
        authorize_url = auth_flow.start()
        print("1. Go to: " + authorize_url)
        print("2. Click 'Allow' (you might have to log in first).")
        print("3. Copy the authorization code.")
        auth_code = input("Enter the authorization code here: ")
        oauth_result = auth_flow.finish(auth_code)
        return oauth_result
    except Exception as e:
        logging.error(f"Error during authentication: {e}")
        sys.exit(1)

def get_dropbox_client(app_key, app_secret, refresh_token):
    try:
        dbx = dropbox.Dropbox(oauth2_refresh_token=refresh_token, app_key=app_key, app_secret=app_secret)
        return dbx
    except Exception as e:
        logging.error(f"Error creating Dropbox client: {e}")
        sys.exit(1)

def update_env_file(env_file, refresh_token):
    set_key(env_file, "DROPBOX_REFRESH_TOKEN", refresh_token)

def main(env_file):
    load_dotenv(env_file)
    app_key = os.getenv('DROPBOX_APP_KEY')
    app_secret = os.getenv('DROPBOX_APP_PASSWORD')
    refresh_token = os.getenv('DROPBOX_REFRESH_TOKEN')

    if not refresh_token:
        oauth_result = start_initial_auth(app_key, app_secret)
        refresh_token = oauth_result.refresh_token

    dbx = get_dropbox_client(app_key, app_secret, refresh_token)
    # You can now use `dbx` to interact with the Dropbox API.

    update_env_file(env_file, refresh_token)
    logging.info("Configuration updated with the new refresh token.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logging.error("Usage: python script.py <path_to_env_file>")
        sys.exit(1)
    env_file_path = sys.argv[1]
    main(env_file_path)
