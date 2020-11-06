"""
Worker

A worker is the one who does a job, outlined by the config.

Possible Improvements:
    -Multithreading
    -aiohttp - investigated, may not be worth it for the kinds of queries being run

Changelog:
    2020-09-20  -   Version 1 is completed.

"""
__author__ = "Sean Breen"
__version__ = "1.0.0"
__email__="sean.breen@crowdstrike.com"


import sys
import requests
import json
import pymysql
import slack
import auth
import logwork
from datetime import datetime

class worker(object):
    """Class: worker

    Description:
    A worker is a class that does a job, defined by the config. It can query a database, query an API, query a website, create a jira ticket
    or a slack alert.

    Variables:
        worker_name (str)               - The name of the configuration (from the configuration file) 
        config (dict)                   - The dictionary of configuration options read from the config file
        type (str)                      - A string that represents the type of worker - there are currently 4 supported types: api, auditdb, url and alert
        severity (str)                  - The severity of the job, doesn't have any impact on prioritising the job itself from running.
        parameters (str)                - Extra parameters and customisation for the type of alert. I.e: custom headers for URL requests, or the SQL query for the auditdb.
        medium (str)                    - The medium to notify the user on, currently only supports slack.
        channel (str)                   - The slack channel to message.
        oauth_token (str)               - The OAuth token, only set and used when querying the Falcon API
        time_weeks (int)                - An integer representing how many weeks to wait before triggering again.
        time_days (int)                 - An integer representing how many days to wait before triggering again.
        time_hours (int)                - An integer representing how many hours to wait before triggering again.
        time_minutes (int)              - An integer representing how many minutes to wait before triggering again.
        time_seconds (int)              - An integer representing how many seconds to wait before triggering again.
        time_startdate (datetime)       - The date to commence running the rule.
        time_enddate (datetime)         - The date to end running the rule.
        time_zone (tzinfo)              - The time zone information.
        time_jitter (int)               - The jitter for when the rule runs. If a rule is taking longer instead of waiting for it to execute next, it can execute immediently if it's within the jitter period.

    Functions:
        get_time_weeks                  - Retrieves the time in weeks from the configuration, or sets it to a value.
        get_time_days                   - Retrieves the time in days from the configuration, or sets it to a value.
        get_time_hours                  - Retrieves the time in hours from the configuration, or sets it to a value.
        get_time_minutes                - Retrieves the time in minutes from the configuration, or sets it to a value.
        get_time_seconds                - Retrieves the time in seconds from the configuration, or sets it to a value.
        get_time_startdate              - Converts a string in the format '%b %d %Y %H:%M:%S %z' into a datetime object.
        get_time_enddate                - Converts a string in the format '%b %d %Y %H:%M:%S %z' into a datetime object.
        get_time_zone                   - Grabs the %z from the datetime object and converts it into a valid tzinfo object.
        get_time_jitter                 - Retrieves the jitter as an interger.
        get_options                     - Converts the parameters of the config file from a string into a dict.
        read_config                     - Sets internal variables, after getting the options.
        trigger_slack_notification      - Sends a message to a provided slack channel
        request_url                     - Given a dictionary of options, will use the requests library to return the URL
        get_oauth_token                 - Queries the Falcon API to create an oauth token when given a valid client_id and client_secret
        call_api                        - Will acquire an oauth token, then query the provided Falcon API endpoint, returning the JSON.
        call_url                        - Uses the request_url function and returns the text from a given URL.
        call_audit_database             - Runs a provided SQL query and returns the results.
        call_alert                      - Simply messages the provided Slack Channel.
        get_to_work                     - Checks the type against a function mapping, then executes the relevant function.
    """
    def __init__(self,worker_name,config):
        self._worker_name = worker_name
        self._config = config
        self._read_config()
    
    """
    Get Functions:
    """
    def _get_config(self):
        return self._config

    def get_time_weeks(self):
        config = self._get_config()
        if config['weeks']:
            self._time_weeks = int(config['weeks'])
        else:
            self._time_weeks = 0
        return self._time_weeks

    def get_time_days(self):
        config = self._get_config()
        if config['days']:
            self._time_days = int(config['days'])
        else:
            self._time_days = 0
        return self._time_days

    def get_time_hours(self):
        config = self._get_config()
        if config['hours']:
            self._time_hours = int(config['hours'])
        else:
            self._time_hours = 0
        return self._time_hours

    def get_time_minutes(self):
        config = self._get_config()
        if config['minutes']:
            self._time_minutes = int(config['minutes'])
        else:
            self._time_minutes = 0
        return self._time_minutes

    def get_time_seconds(self):
        config = self._get_config()
        if config['seconds']:
            self._time_seconds = int(config['seconds'])
        else:
            self._time_seconds = 0
        return self._time_seconds  

    def get_time_startdate(self):
        config = self._get_config()
        if config['startdate']:
            self._time_start_date = datetime.strptime(config['startdate'], '%b %d %Y %H:%M:%S %z') #Format Oct 10 2020 23:23:23 +1000
        else:
            self._time_start_date = None
        return self._time_start_date  

    def get_time_enddate(self):
        config = self._get_config()
        if config['enddate']:
            self._time_end_date = datetime.strptime(config['startdate'], '%b %d %Y %H:%M:%S %z')
        else:
            self._time_end_date = None
        return self._time_end_date   

    def get_time_zone(self):
        config = self._get_config()
        if config['startdate']:
            self._time_zone = self._time_start_date.tzinfo
        else:
            self._time_zone = None
        return self._time_zone

    def get_time_jitter(self):
        config = self._get_config()
        if config['jitter']:
            self._time_jitter = int(config['jitter'])
        else:
            self._time_jitter = None
        return self._time_jitter  

    def _get_options(self):
        try:
            options = json.loads(self._get_config()['parameters'])
        except ValueError:
            logwork.log_work('ERROR: Rule {} does not contain valid JSON in the Parameters. Please review and amend.'.format(self._worker_name))
        return options

    """
    Functions
    """
    def _read_config(self):
        '''Function: read_config

        Description: Reads the config dictionary, and splits that out into class object variables.

        Input Variables:
        None

        Returns:            
        None
        '''
        config = self._get_config()
        self._type = config['type']
        self._severity = config['severity']
        self._parameters = config['parameters']
        self._medium = config['medium']
        self._channel=config['channel'].strip('\"')
        self._oauth_token = None

    def trigger_slack_notification(self,message):
        '''Function: trigger_slack_notification

        Description: Sends the provided message to a specified channel in slack.

        Input Variables:
        message (str)       - The blurb of text to include in the message.

        Returns:            
        None
        '''
        slack_token = auth.get_slack_token()['slack_bot_token']
        try:
            current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            formatted_message= f"[{current_time}] [Severity: {self._severity}] [Rule: {self._worker_name}] {message}"
            client = slack.WebClient(token=slack_token)
            client.chat_postMessage(channel=self._channel,text=formatted_message)
        except Exception as e:
            logwork.log_work('ERROR: Slack Exception thrown, please see the following for further information Rule {}'.format(e))

    def _request_url(self,options):
        '''Function: request_url

        Description: Uses the request library to undertake some HTTP operation (such as GET, POST, etc). 

        Input Variables:
        options (str, dict) - A json string, or dictionary of options for the request. Allows you to set any option that can be used with requests.

        Returns:            
        response (requests) - A requests object for the request.
        '''
        if type(options['request_params']) is str:
            try:
                request_parameters = json.loads(options['request_params'])
            except ValueError:
                logwork.log_work('ERROR: Rule {} does not contain valid JSON in the Request_Parms field. Please review and amend.'.format(self._worker_name))
        else:
            request_parameters = dict(options['request_params'])

        try:
            response = requests.request(options['type'],url=options['url'],**request_parameters)
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError as e: 
            logwork.log_work('ERROR: Failed to connect to {}. See the following for further information: {}'.format(options['url'], e))
        except requests.exceptions.Timeout:
            logwork.log_work('ERROR: Timed out attempting to connect to the following url: {}'.format(options['url']))
        except requests.exceptions.TooManyRedirects:
            logwork.log_work('ERROR: Too many URL redirects')
        except requests.exceptions.RequestException as e:
            logwork.log_work('ERROR: Error arose attempting to connect to {}, please investigation further: {}'.format(options['url'], e))


    def _call_url(self,options):
        '''Function: call_url

        Description: Calls the request_url function, with options and pushes the response to Slack.

        Input Variables:
        Options (dict)      - A dictionary of extra options to provide to the requests library (for things like Headers, etc)

        Returns:            
        None
        '''
        resp = self._request_url(options=options)
        self.trigger_slack_notification(resp.text)

    def _call_audit_database(self,options):
        '''Function: call_audit_database

        Description: Runs an SQL query against the audit database.

        Input Variables:
        Options (dict)      - The parameters (including the query) to run against the database.

        Returns:            
        None
        '''
        database_info = auth.credential_store_auditdb()
        db_connection = pymysql.connect(host=database_info['host'],user=database_info['user'],password=database_info['password'],db=database_info['database'])

        try:
            with db_connection.cursor() as db_cursor:
                db_cursor.execute(options['query'])
                results = db_cursor.fetchall()
                db_connection.close()
                self.trigger_slack_notification(results)
        except:
            logwork.log_work('ERROR: Failed to connect to database, this has thrown an exception. Please investigate and try again.')
            db_connection.close()

    def _call_alert(self,options):
        '''Function: call_alert

        Description: Sends a message to a provided slack channel

        Input Variables:
        Options (dict)      - The parameters (including the message), to send to slack.

        Returns:            
        None
        '''
        self.trigger_slack_notification(message=options['message'])

    def get_to_work(self):
        '''Function: get_to_work

        Description: Compares the class object type, against a function mapping, and then executes the relevant function.

        Input Variables:
        None

        Returns:            
        None
        '''
        options = self._get_options()
        function_map = {'url': self._call_url, 'auditdb': self._call_audit_database, 'alert': self._call_alert}
        if self._type in function_map:
            function_map[self._type](options=options)
        else:
            logwork.log_work('ERROR: Rule {} is an invalid rule type provided: {}'.format(self._worker_name, self._type))
            sys.exit()


