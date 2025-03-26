import sys
import cx_Oracle
import os
from datetime import datetime, timezone

ERROR_SYSTEM = 100
ERROR_DATABASE_CONNECTION = 1000
ERROR_DATABASE_INSERT = 1010

sql_user_verify = "SELECT COUNT(*) FROM HELPDESK.LDAP_SYNC WHERE <FIELD HERE> LIKE :domain'"
sql_group_verify = "SELECT COUNT(*)  FROM HELPDESK.LDAP_GROUPS WHERE <FIELD HERE> LIKE :domain"
sql_user_groups_verify = "SELECT COUNT(*)  FROM HELPDESK.LDAP_USER_GROUPS WHERE <FIELD HERE> LIKE :domain"

sql_user_delete = "DELETE FROM HELPDESK.LDAP_SYNC"
sql_group_delete = "DELETE FROM HELPDESK.LDAP_GROUPS"
sql_user_groups_delete = "DELETE FROM HELPDESK.LDAP_USER_GROUPS"

sql_user_insert = """
    INSERT INTO HELPDESK.LDAP_SYNC (
        SAMACCOUNTNAME, SN, GIVENNAME,
        LASTLOGONTIMESTAMP, PHYSICALDELIVERYOFFICENAME, TITLE,
        WHENCHANGED, DEPARTMENT, MANAGER,
        MAIL, MOBILE, DISPLAYNAME,
        TELEPHONENUMBER, USERACCOUNTCONTROL, DESCRIPTION, DISTINGUISHEDNAME,
        MDBOVERQUOTALIMIT, MDBSTORAGEQUOTA, MDBUSEDEFAULTS, VASCOLOCKED,
        PWDLASTSET, WHENCREATED, EXTENSIONATTRIBUTE1, ACCOUNTEXPIRES,
        DOMAIN
    )
    VALUES (
        :sam, :sn, :given,
        :lastlogOn, :physycal, :title, 
        :whenChanged, :department, :manager, 
        :mail, :mobile, :displayName,
        :telephone, :uacc, :description, :distinguishedName, 
        :mdbo, :mdbs, :mdbu, :vasco, 
        :pwdLastSet, :whenCreated, :extensionAttr, :acctExpires,
        :domain
        )
"""

sql_group_insert ="""
    INSERT INTO HELPDESK.LDAP_GROUPS ( 
        NAME, DISTINGUISHEDNAME, DESCRIPTION, 
        WHENCHANGED, DISPLAYNAME, MANAGEDBY
    ) VALUES (
        :groupName, :distinguishedName, :description,
        :whenChanged, :displayName, :managedBy
    )
"""

sql_user_groups_insert ="""
    INSERT INTO HELPDESK.LDAP_USER_GROUPS (USER_DN, GROUP_DN) 
    VALUES (:user_dn, :group_dn)
"""

class dbService:
    _has_pending_transaction = False

    def __init__(self, logger):
        self.logger = logger
        self.oracleConnection = None


    def _ldap_time_to_oracle_number(self, ldap_time):
        """
        Converts a time from LDAP format to Oracle format (Unix timestamp).

        :param ldap_time: Time in LDAP format (datetime or large integer)
        :return: Time in Oracle format (Unix timestamp)
        """
        
        if ldap_time is None:
            return None
        if isinstance(ldap_time, datetime):
            # If it's already a datetime object, convert it to a Unix timestamp
            return int(ldap_time.replace(tzinfo=timezone.utc).timestamp())
        if isinstance(ldap_time, (int, float)):
            # If it's a large integer (LDAP format), convert it to Unix timestamp
            return int((ldap_time / 10000000) - 11644473600)
        # If it's neither datetime nor number, return None or raise an exception
        return None  # or raise ValueError(f"Unexpected type for ldap_time: {type(ldap_time)}")


    def connect(self):
        """
        Connects to the Oracle Database using the 64 bit Oracle client library

        Exits with ERROR_DATABASE_CONNECTION if the connection fails.
        """
        try:
            cx_Oracle.init_oracle_client(
                lib_dir=os.getenv("ORACLE_LIB_DIR"),
                config_dir=os.getenv("ORACLE_TNS_DIR")
            )
        except Exception as e:
            if "Oracle Client library has already been initialized" in str(e):
                # Connections are already established
                self.logger.info("Oracle Client library has already been initialized")
                return
            else:
                self.logger.error("Error with Oracle Client Library", error)
                exit(ERROR_DATABASE_CONNECTION)
            
        # Connecting to the 64 bit version of the driver...
        try:
            self.logger.info(f"Connecting to Oracle...")
            self.oracleConnection = cx_Oracle.connect(
                user=os.getenv("DB_User"),
                password=os.getenv("DB_Password"),
                dsn=os.getenv("DB_Name"),
            )
            #self.oracleConnection.outputtypehandler = lambda cursor, name, defaultType, size, precision, scale: defaultType if defaultType != cx_Oracle.DATETIME else datetime
            self.oracleConnection.outputtypehandler = dbService._output_type_handler
            self.oracleConnection.autocommit = False
            self._has_pending_transaction = True
            self.logger.info(f"Oracle Connection to {os.getenv('DB_Name')} established...")
            self.logger.info(f"Oracle Transaction initialized...")

        except Exception as error:
            self.logger.error(f"Error connecting to Oracle: {sys.exc_info()[1]}", error)
            exit(ERROR_DATABASE_CONNECTION)  


    def _output_type_handler(cursor, name, defaultType, size, precision, scale):
        if defaultType == cx_Oracle.DATETIME:
            return cursor.var(cx_Oracle.DATETIME, arraysize=cursor.arraysize)
        if defaultType == cx_Oracle.NUMBER:
            return cursor.var(cx_Oracle.NUMBER, arraysize=cursor.arraysize)
        return None



    def clear_tables(self):
        cursor = None
        try: 
            self.logger.info(f"Clearing existing tables...")
            # Create a cursor
            with self.oracleConnection.cursor() as cursor: 
                # Execute the parameterized query
                cursor.execute(sql_user_delete)
                cursor.execute(sql_group_delete)
                cursor.execute(sql_user_groups_delete)

            self.logger.info(f"Tables cleared successfully")

        except cx_Oracle.Error as error:
            self.get_stack_trace(error)

        except Exception as error:
            self.logger.error(f"An Error occurred in clear_tables: {sys.exc_info()[1]}", error)
            exit(ERROR_SYSTEM)  
   

    def synchronize_users(self, server, entries): 
        try: 
            # Create a cursor
            with self.oracleConnection.cursor() as cursor:
                for entry in entries:
                    #self.logger.info(f'[{server}] Storing User: {entry}') 
                    entryParams = {
                        'sam': entry.samAccountName.value,
                        'sn': entry.sn.value,
                        'given': entry.givenName.value,
                        'lastlogOn': self._ldap_time_to_oracle_number(entry.lastLogonTimestamp.value),
                        'physycal': entry.physicalDeliveryOfficeName.value,
                        'title': entry.title.value,
                        'whenChanged': entry.whenChanged.value,
                        'department': entry.department.value,
                        'manager': entry.manager.value,
                        'mail': entry.mail.value,
                        'mobile': entry.mobile.value,
                        'displayName': entry.displayName.value,
                        'telephone': entry.telephoneNumber.value,
                        'uacc': int(entry.userAccountControl.value),
                        'description': entry.description.value,
                        'distinguishedName': entry.distinguishedName.value,
                        'mdbo': int(entry.mdbOverQuotaLimit.value) if entry.mdbOverQuotaLimit else 0,
                        'mdbs': entry.mdbStorageQuota.value,
                        'mdbu': entry.mdbUseDefaults.value,
                        'vasco': entry['vasco-Locked'].value if 'vasco-Locked' in entry else None,
                        'pwdLastSet': self._ldap_time_to_oracle_number(entry.pwdLastSet.value),
                        'whenCreated': entry.whenCreated.value,
                        'extensionAttr': entry.extensionAttribute1.value,
                        'acctExpires': self._ldap_time_to_oracle_number(entry.accountExpires.value),
                        'domain': server
                    }
                    cursor.execute(sql_user_insert, entryParams)

            if self._verify_inserted_rows(server, sql_user_verify, len(entries)):
                self.logger.info(f"[{server}] User data inserted successfully")

        except cx_Oracle.Error as error:
            self.get_stack_trace(error)
            
        except Exception as error:
            self.logger.error(f"An Error occurred in synchronize_users: {sys.exc_info()[1]}", error)
            exit(ERROR_SYSTEM)  


    def synchronize_groups(self, server, entries): 
        try: 
            # Create a cursor
            with self.oracleConnection.cursor() as cursor:
                for entry in entries:
                    #self.logger.info(f'[{server}] Storing Group: ', entry) 

                    entryParams = {
                        'groupName': entry.samAccountName.value,
                        'distinguishedName': entry.distinguishedName.value,
                        'description': entry.description.value,
                        'whenChanged': entry.whenChanged.value,
                        'displayName': entry.displayName.value,
                        'managedBy': entry.managedBy.value,
                    }
                    cursor.execute(sql_group_insert, entryParams)

            if self._verify_inserted_rows(server, sql_group_verify, len(entries)):
                self.logger.info(f"[{server}] Group data inserted successfully")

        except cx_Oracle.Error as error:
            self.get_stack_trace(error)

        except Exception as error:
            self.logger.error(f"An Error occurred in synchronize_groups: {sys.exc_info()[1]}", error)
            exit(ERROR_SYSTEM)  



    def synchronize_group_members(self, server, entries): 
        try: 
            # Create a cursor
            with self.oracleConnection.cursor() as cursor:
                count = 0
                for group_dn, members in entries.items():
                    for member in members:                
                        #self.logger.info(f'[{server}] Storing User: [{member}] for Group: [{group_dn}]' ) 
                        entryParams = {
                            'user_dn': member,
                            'group_dn': group_dn
                        }
                        cursor.execute(sql_user_groups_insert, entryParams)
                        count += 1
                
            if self._verify_inserted_rows(server, sql_user_groups_verify, count):                
                self.logger.info(f"[{server}] User Groups data inserted successfully")

        except cx_Oracle.Error as error:
            self.get_stack_trace(error)

        except Exception as error:
            self.logger.error(f"An Error occurred in synchronize_groups: {sys.exc_info()[1]}", error)
            exit(ERROR_SYSTEM)  


    def _verify_inserted_rows(self, server, qry, expected):
        try: 
            # Create a cursor
            with self.oracleConnection.cursor() as cursor:
                params = {
                    'domain': f'%{server}%'
                }
                cursor.execute(qry, params)
                result = cursor.fetchone()
            
            self.logger.info(f"[{server}] Data inserted {result[0]}, expected {expected}")
            return expected == result[0]

        except cx_Oracle.Error as error:
            self.get_stack_trace(error)
            return False

        except Exception as error:
            self.logger.error(f"An Error occurred in verify_inserted_rows: {sys.exc_info()[1]}", error)
            return False
        
        

    def get_stack_trace(self, error): 
        
        error_obj, = error.args
        self.logger.error("Oracle Error:")
        self.logger.error("Error Code:", error_obj.code)
        self.logger.error("Error Message:", error_obj.message)
        
        # Get detailed error information
        if self.oracleConnection:
            # If an error occurs, rollback the transaction
            self.oracleConnection.rollback()

            cursor = self.oracleConnection.cursor()
            try:
                # Get error stack
                cursor.execute("BEGIN RAISE_APPLICATION_ERROR(-20001, 'Dummy error'); END;")
            except cx_Oracle.Error as exc:
                error_stack = exc.args[0].message
                self.logger.error("Error Stack:")
                self.logger.error(error_stack)

            try:
                cursor.callproc("sys.dbms_utility.format_error_backtrace")
                backtrace = cursor.fetchone()
                if backtrace:
                    self.logger.error("Error Backtrace:")
                    self.logger.error(backtrace[0])

            except cx_Oracle.Error:
                self.logger.error("Unable to retrieve error backtrace")
            cursor.close()

        exit(ERROR_DATABASE_INSERT)


    def is_connection_open(self, connection):
        try:
            # Attempt to ping the database
            connection.ping()
            return True
        except cx_Oracle.Error:
            # If ping fails, the connection is closed or invalid
            return False
    

    def disconnect(self):
        if self.oracleConnection:
            if self._has_pending_transaction:
                self.oracleConnection.commit()
                self._has_pending_transaction = False
                self.logger.info("Oracle Transaction committed...")
            
            if self.is_connection_open(self.oracleConnection):
                self.oracleConnection.close()
                self.logger.info("Oracle Connection closed...")