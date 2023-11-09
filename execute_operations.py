import json
import parse_files
import requests
import prepare_operation_bodies
import boto3
import os

url = f'{parse_files.MIGRATE_TO}/pf-admin-api/v1'
endpoints = {
             "accessTokenManagers": "/oauth/accessTokenManagers",
             "accessTokenMappings": "/oauth/accessTokenMappings",
             "authPolicies": "/authenticationPolicies/default",
             "authPolicyFragments": "/authenticationPolicies/fragments",
             "authPolicyContracts": "/authenticationPolicyContracts",
             "idpAdapters": "/idp/adapters",
             "passwordCredentialValidators": "/passwordCredentialValidators",
             "spConnections": "/idp/spConnections",
             "clients": "/oauth/clients"
}

def get_secret(secret_name):
    with open(os.environ.get('SECRETS_FILE')) as f:
        return json.load(f)[secret_name]


session = requests.Session()
secrets = get_secret('API_SECRET')
session.auth = (secrets["username"], secrets["password"])
session.headers.update({'X-XSRF-Header': 'PingFederate'})
session.verify = False

def execute_calls():
    #PUTs and POSTs have the same key values in the same order, so we can iterate this way
    try:
        for key, val in prepare_operation_bodies.PUT_Bodies.items():
            #Run POST operations then PUTs
            print(f'\n\n\n\nOperations running now on {key}...\n')
            for i in range(0, len(prepare_operation_bodies.POST_Bodies[key])):
                json_body = json.loads(json.dumps(prepare_operation_bodies.POST_Bodies[key][i]))
                response = session.post(url=f'{url}{endpoints[key]}', json=json_body)
                if not response.ok and key != 'dataStores':
                    print(f'Request body: {response.request.body}')
                    print(response.url)
                    print(f'\n\nResponse body is as follows:\n {response.content}\n\n\n')
                    raise Exception(f'HTTP Error: {response.status_code} - {response.reason}')
                else:
                    print(f'Response code for POST to {url}{endpoints[key]} is {response.status_code} for call'
                          f' made with following JSON:\n {json_body}\n')
                    print(f'Response body is as follows:\n {response.content}\n\n\n')
            if key not in ('authPolicies', 'OAuthKeys', 'virtualHosts', 'redirectValidation'):
                for i in range(0, len(prepare_operation_bodies.PUT_Bodies[key])):
                    json_body = json.loads(json.dumps(prepare_operation_bodies.PUT_Bodies[key][i]))
                    response = session.put(url=f'{url}{endpoints[key]}/{prepare_operation_bodies.PUT_IDs[key][i]}',
                                           json=json_body)
                    if not response.ok and key != 'dataStores':
                        print(f'Request body: {response.request.body}')
                        print(response.url)
                        print(f'\n\nResponse body is as follows:\n {response.content}\n\n\n')
                        raise Exception(f'HTTP Error: {response.status_code} - {response.reason}')
                    else:
                        print(f'Response code for PUT to {url}{endpoints[key]}/{prepare_operation_bodies.PUT_IDs[key][i]} is '
                              f'{response.status_code} with the following JSON:\n {json_body}\n')
                        print(f'Response body is as follows:\n {response.content}\n\n\n')
            else:
                for j in range(0, len(prepare_operation_bodies.PUT_Bodies[key])):
                    json_body = json.loads(json.dumps(prepare_operation_bodies.PUT_Bodies[key][j]))
                    response = session.put(url=f'{url}{endpoints[key]}', json=json_body)
                    if not response.ok and key != 'dataStores':
                        print(f'Request body: {response.request.body}\n\n' )
                        print(response.url)
                        print(f'\n\nResponse body is as follows:\n {response.content}\n\n\n')
                        raise Exception(f'HTTP Error: {response.status_code} - {response.reason}')
                    else:
                        print(f'Response code for PUT to {url}{endpoints[key]} is'
                              f' {response.status_code} with the following JSON:\n {json_body}\n')
                        print(f'Response body is as follows:\n {response.content}\n\n\n')
    except requests.exceptions.RequestException as e:
        print(f'An error occurred during the HTTP request: {e}')
    except Exception as e:
        print(f'Unexpected error occured {e}')

execute_calls()

print('\n\n\n\nOperations Completed.  Migration Complete!\n\n\n\n')
