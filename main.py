import base64
import logging
import os
import sys
import time

import requests
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

stop_event = None
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a file handler and set its level to INFO
file_handler = logging.FileHandler('logs.txt')
file_handler.setLevel(logging.INFO)

# Create a formatter and add it to the file handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s %(message)s')
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)

os.environ["AZURE_CLIENT_ID"] = ""
os.environ["AZURE_CLIENT_SECRET"] = ""
os.environ["AZURE_TENANT_ID"] = ""

# Phone numbers
User = "+447904750242"

OnCallNumber = User

# Set up Twilio API credentials
twilio_account_sid_secret_name = "twilio-account-sid-secret-name"
twilio_auth_token_secret_name = "twilio-auth-token-secret-name"
keyvault_name = 'APICredentials'

try:
    # Retrieve Twilio API credentials from KeyVault
    credential = DefaultAzureCredential()
    vault_url = f"https://{keyvault_name}.vault.azure.net"
    secret_client = SecretClient(vault_url=vault_url, credential=credential)
    twilio_account_sid = secret_client.get_secret(twilio_account_sid_secret_name).value
    twilio_auth_token = secret_client.get_secret(twilio_auth_token_secret_name).value

    # Set up Twilio client
    client = Client(twilio_account_sid, twilio_auth_token)
except ResourceNotFoundError as ex:
    logger.error(f"An error occurred: {ex}")
    exit(1)

# Set up Zendesk API credentials
zendesk_email_secret_name = "zendesk-email"
zendesk_api_token_secret_name = "zendesk-api-auth"

try:
    # Retrieve Zendesk API credentials from KeyVault
    credential = DefaultAzureCredential()
    vault_url = f"https://{keyvault_name}.vault.azure.net"
    secret_client = SecretClient(vault_url=vault_url, credential=credential)
    zendesk_email = secret_client.get_secret(zendesk_email_secret_name).value
    zendesk_api_token = secret_client.get_secret(zendesk_api_token_secret_name).value
except ResourceNotFoundError as ex:
    logger.error(f"An error occurred: {ex}")
    exit(1)

custom_field_id = "31181498"
custom_field_value = "severity-1"
# Set up Zendesk API endpoint for ticket search
query = f'type:ticket status:new custom_field_{custom_field_id}:{custom_field_value}'
zendesk_api_url = "https://.zendesk.com/api/v2/search.json?query=" + query

logs = []

if len(sys.argv) > 1:
    OnCallNumber = sys.argv[1]


def main(OnCallNumber, stop_event=None):
    global logger
    while not stop_event.is_set():
        try:
            # Send request to Zendesk API to search for P1 tickets in "New" status
            headers = {
                'Authorization': f'Basic {base64.b64encode((zendesk_email + "/token:" + zendesk_api_token).encode("utf-8")).decode("utf-8")}'}
            response = requests.get(zendesk_api_url, headers=headers)

            # Check if any P1 tickets were found
            if response.status_code == 200:
                results = response.json()
                count = results['count']
                log_message = f"Checked for new P1 tickets: {count} found"
                logger.info(log_message)
            else:
                logger.error(f"An error occurred while searching for P1 tickets: {response.text}")
                # raise an exception to exit the program
                raise Exception(f"An error occurred while searching for P1 tickets: {response.text}")

            if count > 0:
                # Use Twilio API to initiate phone call
                message = client.calls.create(
                    to=OnCallNumber,
                    from_='',
                    twiml='<Response><Say>Hello, a P1 support ticket has been received. Please check Zendesk.</Say></Response>')
                logger.info('Phone call initiated with message: {}'.format(message.sid))
                log_message = f"{time.strftime('%Y-%m-%d %H:%M:%S')} Call initiated to {OnCallNumber}"
                logger.info(log_message)
                try:
                    message = client.messages.create(
                        body=" a P1 support ticket has been received. Please check Zendesk.",
                        from_='',
                        to=OnCallNumber
                    )
                except TwilioRestException as e:
                    logger.info('Error sending SMS:', str(e))
            else:
                logger.debug("No P1 tickets found.")

            # Check if the stop event has been set
            if stop_event.wait(60):
                # Stop the loop if the stop event has been set
                logger.info("Stopping main.py...")
                break

        except requests.exceptions.RequestException as ex:
            logger.error(f"An error occurred: {ex}")
            # raise an exception to exit the program
            raise Exception(f"An error occurred: {ex}")

        except Exception as ex:
            # log the exception
            logger.error(f"An error occurred: {ex}")
            # exit the program
            sys.exit(1)


if __name__ == "__main__":
    main(OnCallNumber, stop_event)
