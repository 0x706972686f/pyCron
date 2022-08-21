"""
pyCron

A simple use of Asyncio to schedule jobs.

Changelog:
    2020-10-18  - Initial Version Created (v1 Alpha)

"""
__author__ = "Sean Breen"
__credits__ = ["Sean Breen"]
__version__ = "1.0.0"
__email__="sean@shadow.engineering"


import logging
import asyncio
import configparser
import os
import sys
import worker
import json
import logwork
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

def read_config(config_file):
    '''Function: read_config

    Description: Reads and validates the configuration file provided.

    Input Variables:
    config_file (str)           - The filename of the file to read.

    Returns:            
    config_dictionary (dict)    - A dictionary of the configuration that has been read in.
    '''
    if os.path.isfile(config_file):
        config_dictionary = {}
        config = configparser.ConfigParser()
        config.read(config_file)

        for key, value in config._sections.items():
            config_dictionary[key] = dict(value)

        return config_dictionary

    else:
        logwork.log_work('ERROR: The configuration file {} was not present, or is inaccessible. Please review and provide a legitimate file path'.format(config_file))
        sys.exit()

def create_workers(config_dict):
    '''Function: create_workers

    Description: This function creates worker class objects, using the read in configuration to populate the components.

    Input Variables:
    config_dict (dict)          - The dictionary of configuration that has been read in from the config file.

    Returns:            
    construction (array)        - An array containing all of the worker objects.
    '''
    construction = []
    for condition in config_dict:
        try:
            json.loads(config_dict[condition]['parameters'])
            job=worker.worker(worker_name=condition,config=config_dict[condition])
            construction.append(job)
        except ValueError:
            logwork.log_work('ERROR: Rule {} does not contain valid JSON. Please review and amend'.format(condition))
    return construction

def main(workers):
    '''Function: main

    Description: The main function that triggers the Asynchronous Scheduler. For every worker
    object, a job is added. An asynchio loop is started, and the get_to_work function for each
    object is executed.

    Input Variables:
    workers (list)           - A list considering of each worker object that has been created.

    Returns:            
    None
    '''
    scheduler = AsyncIOScheduler()
    for worker in workers:
        scheduler.add_job(
            worker.get_to_work,
            "interval",
            weeks=worker.get_time_weeks(),
            days=worker.get_time_days(),
            hours=worker.get_time_hours(),
            minutes=worker.get_time_minutes(),
            seconds=worker.get_time_seconds(),
            start_date=worker.get_time_startdate(),
            end_date=worker.get_time_enddate(),
            timezone=worker.get_time_zone(),
            jitter=worker.get_time_jitter())
    scheduler.start()
    loop = asyncio.get_event_loop()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logwork.log_work('KEYBOARD INTERRUPT - SHUTTING DOWN')
        loop.stop()
    finally:
        logwork.log_work('CLOSING PROGRAM - FINAL STEPS')
        loop.close()
        scheduler.shutdown()


if __name__ == "__main__":
    logwork.log_work('COMMENCING PROGRAM')
    logwork.log_work('READING CONFIGURATION FILE')
    dir_path = os.path.dirname(os.path.realpath(__file__))
    logwork.log_work('EXTRACTING CONFIGURATION ITEMS')
    configuration = read_config(dir_path+'/conf.ini')
    logwork.log_work('CREATING WORKFORCE')
    workers = create_workers(configuration)
    logwork.log_work('COMMENCING PROGRAM')
    main(workers)



