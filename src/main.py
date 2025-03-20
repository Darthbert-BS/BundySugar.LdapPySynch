#import pyodbc 
import cx_Oracle
import datetime
import logging
import os
from os.path import isfile, dirname, abspath
import sys
from dotenv import load_dotenv
# import ldap
from ldap3 import ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES, SUBTREE, ObjectDef, Server, Connection, ALL
from ldap3.utils.dn import parse_dn

oracle_lib_dir = "C:\\oracle\\product\\instantclient\\instantClient_11_2_64bit"
oracle_tns_dir = "C:\\oracle\\TNS_ADMIN"
log_file = "C:\\ProgramData\\BBS\\Focus\\ldap-synchronizer.log"

ERROR_DATABASE_CONNECTION = 100
ERROR_LDAP_CONNECTION = 200
ERROR_LDAP_SEARCH_USERS = 210
ERROR_LDAP_SEARCH_GROUPS = 220

ATTRIBUTES = [
     'samAccountName', 'sn', 'givenName', 'displayName', 'distinguishedName', 'title'
    ,'physicalDeliveryOfficeName', 'mail', 'telephoneNumber', 'mobile'
    ,'department', 'manager', 'description' 
    ,'mDBOverQuotaLimit','mDBStorageQuota', 'mDBUseDefaults', 'vasco-Locked' 
    ,'lastLogonTimestamp', 'pwdLastSet', 'whenCreated', 'whenChanged' 
    ,'extensionAttribute1', 'accountExpires','userAccountControl', 
] 

class LdapSynchronizer:
    def __init__(self, logger):
        self.logger = logger
        self.oracleConnection = None
        self.ldapConnection = None
        self.get_variables()
    

    def get_variables(self):
        self._oracle_lib_dir = os.getenv("ORACLE_LIB_DIR", oracle_lib_dir)
        self._oracle_tns_dir = os.getenv("ORACLE_TNS_DIR", oracle_tns_dir)
        self._log_file = os.getenv("LOG_FILE", log_file)
        self._ldap_Servers = os.getenv("LDAP_SERVER_LIST", "BS,MN").split(",")



    def initialize(self):
        self._connect_database()
        for server in self._ldap_Servers:
            self._connect_ldap(server, False, True)
            self.get_ldap_users(server)
            #self.get_ldap_groups(server)
            self.ldap_close_connections()



    def _connect_database(self):
        """
        Connects to the Oracle Database using the 64 bit Oracle client library

        Exits with ERROR_DATABASE_CONNECTION if the connection fails.
        """
        try:
            cx_Oracle.init_oracle_client(
                lib_dir=self._oracle_lib_dir,
                config_dir=self._oracle_tns_dir)
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
            self.oracleConnection = cx_Oracle.connect(
                user=os.getenv("DB_User"),
                password=os.getenv("DB_Password"),
                dsn=os.getenv("DB_Name"),
            )
            print(f"Oracle Connection to {os.getenv('DB_Name')} established...")

        except:
            logging.error(f"Error connecting to Oracle")
            print(f"Error connecting to Oracle")
            exit(ERROR_DATABASE_CONNECTION)

    

    def _connect_ldap(self, prefix, showServerInfo=False, showConnectionInfo=False):
        try:
            print("Connecting to LDAP Server")
            logging.info(f"Connecting to LDAP Server")
            server = Server(
                os.getenv(f"LDAP_{prefix}_Server"), 
                port=int(os.getenv(f"LDAP_{prefix}_Port", 389)), 
                get_info=ALL
            )            
            if (showServerInfo):
                info = server.info
                print(info)

            self.ldapConnection = Connection(
                server, 
                user=os.getenv(f"LDAP_{prefix}_Username"), 
                password=os.getenv(f"LDAP_{prefix}_Password"),
                return_empty_attributes=True,
                auto_bind=True
            )
            if (showConnectionInfo):    
                print(self.ldapConnection) 
                print(self.ldapConnection.extend.standard.who_am_i())
                
            
            print(f"LDAP Connection to {os.getenv(f"LDAP_{prefix}Server")} established...")

        except:
            logging.error(f"Error connecting to LDAP")
            print(f"Error connecting to LDAP")
            exit(ERROR_LDAP_CONNECTION)


    def get_ldap_users(self, prefix):
        object_class= 'person' 
        server_name = os.getenv(f"LDAP_{prefix}_Username").split(',dc=')[1] 
        #search_base = f'cn=users,dc={server_name},dc=com,dc=au'
        search_base = f'dc={server_name},dc=com,dc=au'
      
        search_filter = f'(&(objectcategory={object_class})(objectclass=user)(samAccountName=*))'
      
      
        print(f"Searching LDAP Users for:{search_base} with filter: {search_filter}")
        try:
            self.ldapConnection.search(
                search_base, 
                search_filter=search_filter,
                attributes=ATTRIBUTES,
                search_scope = SUBTREE,
                get_operational_attributes=True
            )
           
            for entry in self.ldapConnection.entries:
                print(prefix, entry.sn, entry.samAccountName) 
           
            print(f'[{prefix}] Found {len(self.ldapConnection.entries)} user entries.')

        except:
            msg = f"Error searching LDAP Users: {sys.exc_info()[1]}"
            logging.error(msg)
            print(msg)
            exit(ERROR_LDAP_SEARCH_USERS)



    def get_ldap_groups(self, prefix):
        object_class= 'group' 
        server_name = os.getenv(f"LDAP_{prefix}_Username").split(',dc=')[1] 
        search_base = f'dc={server_name},dc=com,dc=au'
        search_filter = f'(&(objectclass={object_class})(samAccountName=*))'
        print(f"Searching LDAP Groups for:{search_base} with filter: {search_filter}")
        try:
            self.ldapConnection.search(
                search_base, 
                search_filter=search_filter,
                attributes=ATTRIBUTES,
                search_scope = SUBTREE,
                get_operational_attributes=True
            )
           
            print(f'[{prefix}] Found {len(self.ldapConnection.entries)} group entries.')
            for entry in self.ldapConnection.entries:
                print(prefix, entry.sn, entry.samAccountName) 
            
        except:
            msg = f"Error searching LDAP Groups: {sys.exc_info()[1]}"
            logging.error(msg)
            print(msg)
            exit(ERROR_LDAP_SEARCH_GROUPS)


    def ldap_close_connections(self):
        self.ldapConnection.unbind()    
        
        print("LDAP Connection closed...")
        self.logger.info("LDAP Connection closed...")



if __name__ == "__main__":
    #loads the environment variables
    load_dotenv()
    #Logging Settings. 
    logging.basicConfig(
        filename=os.getenv("LOG_FILE",log_file),
        filemode='a',
        format='%(asctime)s,%(msecs)d %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG)
    
    logging.info("Starting...")

    sync = LdapSynchronizer(logging)
    sync.initialize()
