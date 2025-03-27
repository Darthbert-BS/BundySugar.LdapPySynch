import sys
from constants import ERROR_SYNCHRONIZATION
from db_service import dbService
from ldap_service import LdapService



class LdapSynchronizer:
    def __init__(self, servers, logger):
        self._ldap_Servers  = servers
        self._db = dbService(logger);
        self._ldap = None
        self.logger = logger
        
        
    def synchronize(self):
        self.logger.info('Starting synchronization process...')
        try:
            self._db.connect()
            self._db.clear_tables()

            for server in self._ldap_Servers:
                self.logger.info(f'Starting Synchronization run for {server}...')
                self._ldap = LdapService(self.logger);  
                self._ldap.connect(server)
                self._db.synchronize_users(self._ldap.domain_name(), self._ldap.get_users()) 
                result = self._ldap.get_groups()
                self._db.synchronize_groups(self._ldap.domain_name(), result['groups'])
                self._db.synchronize_group_members(self._ldap.domain_name(), result['userGroups']) 
                
                self._ldap.disconnect()
                self.logger.info(f'Synchronization run for {server} complete.') 
            
            self._db.disconnect()    
            self.logger.info('Synchronization process complete.')
        
        except Exception as error:
            msg = f"Error synchronizing LDAP Directories with Oracle: {sys.exc_info()[1]}"
            self.logger.error(msg, error)
            exit(ERROR_SYNCHRONIZATION)

        finally:
            # clean up
            self._db.disconnect()
      
