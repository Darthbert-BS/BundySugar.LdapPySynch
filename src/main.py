import logging
import os
import sys
from dotenv import load_dotenv
from constants import ERROR_SYNCHRONIZATION, LDAP_SERVER_LIST, LDAP_SYNC_VERBOSITY, LOG_FILE
from sync_service import LdapSynchronizer

"""
 *
 * Python port of Malcolm Byrne's LdapDbSync.java 
 *
 * Synchronise LDAP data from Active Directory to the IT Database.
 *
 * $Id: LDAP PySync v1.0 2025/03/25  $
 *
 * @version 1.0.0
 * @author Alberto L. Bonfiglio
 * @since 1.0.0
 *
 * Synchronize data from Active Directory Servers to the following tables:
 *
 *     LDAP_SYNC
 *     LDAP_GROUPS
 *     LDAP_USER_GROUPS
 *
 * This program does lazy sync, (delete all, then repopulate). Please don't
 * run this too frequently as it will stress the database!
 * Please consult the Readme.md for more information.
 *
 *  Database activity is summarised as:
 *
 *      Table               Purpose                 Actions
 *      LDAP_SYNC           User details            Mass delete then mass insert.
 *      LDAP_GROUPS         AD groups               Mass delete then mass insert.
 *      LDAP_USER_GROUPS    User group membership   Mass delete then mass insert.
 *
 *
 *  Changes:
 *
 """
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
