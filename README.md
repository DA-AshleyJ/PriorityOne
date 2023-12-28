# Support Priority One call automation script


This is an application I built out of hours for a company I worked for which used twilio to call you if there was a P1 zendesk ticket

Requirements: 

Azure KeyVault.
Twilio Subscription for voice calling
Zendesk API token
Python

Set the following inside main.py
os.environ["AZURE_CLIENT_ID"] = "YOURAZURECLIENTID"
os.environ["AZURE_CLIENT_SECRET"] = "YOURAZURECLIENTSECRET"
os.environ["AZURE_TENANT_ID"] = "YOURAZURETENANTID"

You can add as many users / phone numbers by setting the values in main.py 
*** These need to be set up as verified numbers in your Twilio account *** 
# Phone numbers
User = "999999999"

These are the KeyVault names - e.g. Keyvault in your Azure Subscription is called "APICredentials" and the keys needed are twilio-account-sid-secret-name & twilio-auth-token-secret-name as well as others listed below.

# Set up Twilio API credentials
twilio_account_sid_secret_name = "twilio-account-sid-secret-name"
twilio_auth_token_secret_name = "twilio-auth-token-secret-name"
keyvault_name = 'APICredentials'
zendesk_email_secret_name = "zendesk-email"
zendesk_api_token_secret_name = "zendesk-api-auth"

Effectively what this script does is polls the API https://.zendesk.com/api/v2/search.json?query= with the following query f'type:ticket status:new custom_field_{custom_field_id}:{custom_field_value}'

Zendesk doesn't have a specific severity as well as priority. 
So in order to do this, I got an output of all fields and found the field ID for severity
custom_field_id = "31181498"
custom_field_value = "severity-1"

If there is a match and there's an unassigned Severity 1 ticket via the filter in the URL status:new and the count is more than 0, it will send an API request to twilio
Twilio will then initiate a call to the "OnCallNumber" set before starting the script, this will be an automated message saying "Hello, a P1 support ticket has been received. Please check Zendesk."
It will also SMS the user "a P1 support ticket has been received. Please check Zendesk."

Please note, until the ticket is changed from new to open, this will continue to call the user. I have not tested this on multiple users as of yet, but single on call agents do get the calls and texts.

