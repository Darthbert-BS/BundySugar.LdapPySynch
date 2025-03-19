import pyodbc 
import cx_Oracle
import datetime
import logging
from os.path import isfile, dirname, abspath
import sys


oracle_lib_dir = "C:\\oracle\\product\\instantclient\\instantClient_11_2_64bit"
oracle_tns_dir = "C:\\oracle\\TNS_ADMIN"
log_file = "C:\\ProgramData\\BBS\\Focus\\ldap-synchronizer.log"


class LdapSynchronizer:
    def __init__(self, logger):
        self.logger = logger

    ERROR_DATABASE_CONNECTION = 1

    def connect_databases():
         global oconn
    global sconn

    # Make sure to name 64 bit ODBC drivers ...
    try:
        cx_Oracle.init_oracle_client(lib_dir=oracle_lib_dir,
                                     config_dir=oracle_tns_dir)
    except Exception as e:
        if "Oracle Client library has already been initialized" in str(e):
            # Connections are already established
            return
        else:
            logging.error("Error with Oracle Client Library")
            print("Error with Oracle Client Library")
            logging.error(e)
            print(e)
            exit(ERROR_DATABASE_CONNECTION)
        
    # Connecting to the 64 bit version of the driver...
    try:
        logging.info(f"Connecting to Oracle...")
        print(f"Connecting to Oracle...")
        oconn = cx_Oracle.connect('ssis/ked45ftse4kO@mqncane')
    except:
        logging.error(f"Error connecting to Oracle")
        print(f"Error connecting to Oracle")
        exit(ERROR_DATABASE_CONNECTION)


    try:
        logging.info(f"Connecting to SIRUS...")
        print(f"Connecting to SIRUS...")
        # Driver was set to {SQL Server Native Client 11.0} but was causing 'Error connecting to SQL Server'
        sconn = pyodbc.connect(driver='{ODBC Driver 17 for SQL Server}', #{SQL Server}
                               server='sirus',
                               database='SysproSugar_F',
                               user='focusupload',
                               password='Lou7JhuH%a2',                               
                           )
    except:
        logging.error(f"Error connecting to SQL Server")
        print(f"Error connecting to SQL Server")
        exit(ERROR_DATABASE_CONNECTION)




    if __name__ == "__main__":
        #Logging Settings. 
        logging.basicConfig(
            filename=log_file,
            filemode='a',
            format='%(asctime)s,%(msecs)d %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            level=logging.DEBUG)
        
        logging.info("Starting...")
        connect_databases()
