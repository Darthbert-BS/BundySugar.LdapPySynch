import logging
import os
import sys
from dotenv import load_dotenv
from constants import ERROR_SYNCHRONIZATION, LDAP_SERVER_LIST, LDAP_SYNC_VERBOSITY, LOG_FILE
from sync_service import LdapSynchronizer

if __name__ == "__main__":
    #loads the environment variables
    load_dotenv(".config")
    
    #gets the variables needed
    verbosity =os.getenv("LDAP_SYNC_VERBOSITY", str(LDAP_SYNC_VERBOSITY)) 
    servers = [server.strip() for server in os.getenv("LDAP_SERVER_LIST", LDAP_SERVER_LIST).split(",") if server.strip()]
    log_file = os.getenv("LOG_FILE", LOG_FILE)

    #Logging Settings. 
    logging.basicConfig(
        format='%(asctime)s,%(msecs)d %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()]
        )
    
    try:
        sync = LdapSynchronizer(servers, logging)
        sync.synchronize()

    except Exception as error:
        logging.error(f"Error while synchronizing LDAP Directories with Oracle: {sys.exc_info()[1]}", error)
        exit(ERROR_SYNCHRONIZATION)
