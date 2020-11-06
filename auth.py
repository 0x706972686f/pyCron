import os
def get_environment():
    cred_store = {
        'environment': os.getenv('AUDIT_ENVIRONMENT')
    }
    return cred_store

def get_slack_token():
    cred_store = {
        'slack_bot_token': os.getenv('SLACK_BOT_TOKEN')
    }
    return cred_store

def credential_store_api_jira():
    cred_store = {
        'username': os.getenv('JIRA_USERNAME')
        'password': os.getenv('JIRA_PASSWORD')
    }
    return cred_store

def credential_store_auditdb():
    cred_store = {
        'host': os.getenv('MYSQL_HOST')
        'database': os.getenv('MYSQL_DB')
        'user': os.getenv('MYSQL_USER')
        'password': os.getenv('MYSQL_PASSWORD')
        'autocommit': True
    }
    return cred_store