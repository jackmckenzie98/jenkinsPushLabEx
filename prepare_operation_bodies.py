import json
import parse_files
import os

PUT_IDs = {
           "accessTokenManagers": [],
           "accessTokenMappings": [],
           "authPolicies": [],
           "authPolicyFragments": [],
           "authPolicyContracts": [],
           "idpAdapters": [],
           "passwordCredentialValidators": [],
           "spConnections": [],
           "clients": []
           }
PUT_Bodies = {
              "accessTokenManagers": [],
              "accessTokenMappings": [],
              "authPolicies": [],
              "authPolicyFragments": [],
              "authPolicyContracts": [],
              "idpAdapters": [],
              "passwordCredentialValidators": [],
              "spConnections": [],
              "clients": []
              }
POST_Bodies = {
               "accessTokenManagers": [],
               "accessTokenMappings": [],
               "authPolicies": [],
               "authPolicyFragments": [],
               "authPolicyContracts": [],
               "idpAdapters": [],
               "passwordCredentialValidators": [],
               "spConnections": [],
               "clients": []
               }

#Special case to format the key pair operations as they won't exist at first
# def prepare_keyPair_operations():
#     cert_list = []
#     encryption_pass = parse_files.get_secret(os.environ.get('ENCRYPTION_PASS_NAME'))["encryptionPass"]
#     for file in os.listdir(parse_files.CERT_FILES):
#         with open(os.path.join(parse_files.CERT_FILES, file)) as f:
#             cert_list.append(f.read())
#     for i in range(0, len(parse_files.keyPairsArt['items'])):
#         POST_Bodies["keyPairs"].append({"id": parse_files.keyPairsArt['items'][i]['id'],
#                                         "fileData": "",
#                                         "format": "PEM",
#                                         "password": f"{encryption_pass}"
#                                         })
#         POST_Bodies["keyPairs"][i]["fileData"] = cert_list[i]


def replace_location_recursive(data, target_substring, replacement):
    if isinstance(data, str):
        return data.replace(target_substring, replacement)
    elif isinstance(data, list):
        return [replace_location_recursive(item, target_substring, replacement) for item in data]
    elif isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            new_dict[key] = replace_location_recursive(value, target_substring, replacement)
        return new_dict
    else:
        return data


def inject_secret_values(d, old_key, new_key, new_value):
    if isinstance(d, dict):
        new_data = {}
        for key, value in d.items():
            if key == old_key:
                new_data[new_key] = new_value
            else:
                new_data[key] = inject_secret_values(value, old_key, new_key, new_value)
        return new_data
    elif isinstance(d, list):
        return [inject_secret_values(item, old_key, new_key, new_value) for item in d]
    else:
        return d

def prepare_operations(entity_type, existing_data, art_data, id_key, data_key, secret_key=None):
    if data_key != 'authPolicies':
        env_inject = entity_type['example']['location']
        existing_ids = {item[id_key] for item in existing_data['items']}

        for item in art_data['items']:
            item = replace_location_recursive(item, parse_files.MIGRATE_FROM, env_inject)
            if item[id_key] not in existing_ids:
                POST_Bodies[data_key].append(item)
            else:
                PUT_IDs[data_key].append(item[id_key])
                PUT_Bodies[data_key].append(item)

        # If the body requires a secret to be injected to PUT/POST
        if secret_key is not None:
            for i in range(len(POST_Bodies[data_key])):
                if POST_Bodies[data_key][i][id_key] != "ProvisionerDS":
                    POST_Bodies[data_key][i] = inject_secret_values(POST_Bodies[data_key][i], "encryptedValue", "value",
                                                                    parse_files.get_secret(secret_key))
                    POST_Bodies[data_key][i] = inject_secret_values(POST_Bodies[data_key][i], "encryptedPassword",
                                                                   "password",
                                                                   parse_files.get_secret(secret_key))
            for j in range(len(PUT_Bodies[data_key])):
                PUT_Bodies[data_key][j] = inject_secret_values(PUT_Bodies[data_key][j], "encryptedValue", "value",
                                                              parse_files.get_secret(secret_key))
                PUT_Bodies[data_key][j] = inject_secret_values(PUT_Bodies[data_key][j], "encryptedPassword", "password",
                                                              parse_files.get_secret(secret_key))

    # Handle the case that we're PUT-ing the auth policy since its object is a bit unique.
    else:
        env_inject = entity_type['example']['location']
        for item in art_data['items']:
            item = replace_location_recursive(item, parse_files.MIGRATE_FROM, env_inject)
            PUT_Bodies[data_key].append(item)
        if secret_key is not None:
            for i in range(len(POST_Bodies[data_key])):
                if POST_Bodies[data_key][i][id_key] != "ProvisionerDS":
                    POST_Bodies[data_key][i] = inject_secret_values(POST_Bodies[data_key][i], "encryptedValue", "value",
                                                                    parse_files.get_secret(secret_key))
            for j in range(len(PUT_Bodies[data_key])):
                PUT_Bodies[data_key][j] = inject_secret_values(PUT_Bodies[data_key][j], "encryptedValue", "value",
                                                               parse_files.get_secret(secret_key))

#Prepare operations that don't have an identifier for the objects within, or structured oddly
def prepare_unique_ops(entity_type, art_data, data_key, secret_key=None):
    env_inject = entity_type['example']['location']
    if data_key != 'authSessions':
        for item in art_data['items']:
            item = replace_location_recursive(item, parse_files.MIGRATE_FROM, env_inject)
            PUT_Bodies[data_key].append(item)
    else:
        for item in art_data['items']:
            item = replace_location_recursive(item, parse_files.MIGRATE_FROM, env_inject)
            POST_Bodies[data_key].append(item)


# Prepare the PCV data structures
prepare_operations(parse_files.PCVEnv, parse_files.existingPCVs, parse_files.passwordCredentialValidatorsArt, "id",
                   "passwordCredentialValidators", 'PCVPass')

# Prepare the SP connections data structures
prepare_operations(parse_files.spConnEnv, parse_files.existingSPConns, parse_files.spConnsArt, 'id', 'spConnections')

# Prepare clients data structures
prepare_operations(parse_files.clientsEnv, parse_files.existingClients, parse_files.clientsArt, 'clientId', 'clients')

# Prepare Access Token Manager structures
prepare_operations(parse_files.accessTokenManagersEnv, parse_files.existingAccessTokenManagers,
                   parse_files.accessTokenManagersArt, 'id', 'accessTokenManagers')

# Prepare Access Token Mappings structures
prepare_operations(parse_files.accessTokenMappingsEnv, parse_files.existingAccessTokenMappings,
                   parse_files.accessTokenMappingsArt, 'id', 'accessTokenMappings')

# Prepare IDP Adapters structures
prepare_operations(parse_files.idpAdaptersEnv, parse_files.existingIDPAdapters, parse_files.idpAdaptersArt, 'id',
                   'idpAdapters', 'intune-adapter-secret')

# Prepare Auth Policy Contracts structures
prepare_operations(parse_files.authPolicyContractsEnv, parse_files.existing_authPolicyContracts,
                   parse_files.authPolicyContractsArt, 'id', 'authPolicyContracts')

# Prepare Auth Policy Fragments structures
prepare_operations(parse_files.authPolFragmentsEnv, parse_files.existingAuthPolFragments,
                   parse_files.authPolFragmentsArt, 'id', 'authPolicyFragments')

# Prepare Authentication Policies structures
prepare_operations(parse_files.authPolEnv, parse_files.existingAuthPols, parse_files.authPolsArt,
                   'id', 'authPolicies')

#Last one needs some evaluation
#prepare_keyPair_operations()
print('Body formatting of PUT/POST operations on objects has been completed.')
