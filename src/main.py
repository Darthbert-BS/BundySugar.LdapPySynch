import logging
import os
from dotenv import load_dotenv
from sync_service import LdapSynchronizer

log_file = "C:\\ProgramData\\BBS\\Focus\\ldap-synchronizer.log"

#Set verbosity here
# 0 means show and log errors
# 1 means show and log errors and warnings
# 2 means show and log errors, warnings and info 
verbosity = 2

if __name__ == "__main__":
    #loads the environment variables
    load_dotenv()
    
    #gets the variables needed
    os.environ["LDAP_SYNC_VERBOSITY"] = str(verbosity)
    servers = os.getenv("LDAP_SERVER_LIST", "BS,MN").split(",")
    log_file = os.getenv("LOG_FILE", log_file)

    #Logging Settings. 
    logging.basicConfig(
        filename=log_file,
        filemode='a',
        format='%(asctime)s,%(msecs)d %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG)
    
    sync = LdapSynchronizer(servers, logging)
    sync.synchronize()
