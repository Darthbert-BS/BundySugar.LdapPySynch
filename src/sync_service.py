import sys
from db_service import dbService
from ldap_service import LdapService

ERROR_SYNCHRONIZATION = 1000

class LdapSynchronizer:
    def __init__(self, servers, logger):
        self._ldap_Servers  = servers
        self.db = dbService(logger);
        self.logger = logger
    
        
    def synchronize(self):
        self.logger.info('Starting synchronization process...')
        try:
            self.db.connect()
            self.db.clear_tables()

            for server in self._ldap_Servers:
                self.logger.info(f'[{server}] Starting Synchronization run...')
                ldap = LdapService(self.logger);  
                ldap.connect(server)
                self.db.synchronize_users(server, ldap.get_users()) 
                result = ldap.get_groups()
                self.db.synchronize_groups(server, result['groups'])
                self.db.synchronize_group_members(server, result['userGroups']) 
                
                ldap.disconnect()
                self.logger.info(f'[{server}] synchronized.') 
            
            self.db.disconnect()    
            self.logger.info('Synchronization process complete.')
        
        except Exception as error:
            msg = f"Error synchronizing LDAP Directories with Oracle: {sys.exc_info()[1]}"
            self.logger.error(msg, error)
            exit(ERROR_SYNCHRONIZATION)

        finally:
            # clean up
            self.db.disconnect()
      
