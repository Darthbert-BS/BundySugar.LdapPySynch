import pyodbc 
import cx_Oracle
import datetime
import logging
from os.path import isfile, dirname, abspath
import sys

oracle_lib_dir = "C:\\oracle\\product\\instantclient\\instantClient_11_2_64bit"
oracle_tns_dir = "C:\\oracle\\TNS_ADMIN"
log_file = "C:\\ProgramData\\BBS\\Focus\\cofa-focus-to-refis.log"


class LdapSynchronizer:
    def __init__(self, logger):
        self.logger = logger

    ERROR_DATABASE_CONNECTION = 1

    def connect_databases():
        exit(ERROR_DATABASE_CONNECTION)

