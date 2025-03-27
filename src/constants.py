LOG_FILE = "C:/ProgramData/BBS/Focus/ldap-synchronizer.log"
LDAP_SYNC_VERBOSITY = 2 # 0 = errors, 1 = errors and warnings, 2 = errors, warnings and info

LDAP_SERVER_LIST = "BS, MN"

ERROR_SYSTEM = 500
ERROR_SYNCHRONIZATION = 1000

ERROR_DATABASE_CONNECTION = 2000
ERROR_DATABASE_INSERT = 2010

ERROR_LDAP_CONNECTION = 3000
ERROR_LDAP_SEARCH_USERS = 3010
ERROR_LDAP_SEARCH_GROUPS = 3020

USER_ATTRIBUTES = [
     'samAccountName', 'sn', 'givenName', 'displayName', 'distinguishedName', 'title'
    ,'physicalDeliveryOfficeName', 'mail', 'telephoneNumber', 'mobile'
    ,'department', 'manager', 'description' 
    ,'mDBOverQuotaLimit','mDBStorageQuota', 'mDBUseDefaults', 'vasco-Locked' 
    ,'lastLogonTimestamp', 'pwdLastSet', 'whenCreated', 'whenChanged' 
    ,'extensionAttribute1', 'accountExpires','userAccountControl', 
] 

GROUP_ATTRIBUTES = [
    "samAccountname", "displayName", "distinguishedName",
    "description", "whenChanged", "member", "managedBy"
] 

MAX_LOOP_DEPTH = 4


ORACLE_LIB_DIR = "C:/oracle/product/instantclient/instantClient_11_2_64bit"
ORACLE_TNS_DIR = "C:/oracle/TNS_ADMIN"

SQL_USERS_VERIFY = """
    SELECT COUNT(*) FROM HELPDESK.LDAP_SYNC 
    WHERE UPPER(DISTINGUISHEDNAME) LIKE UPPER(:domain)
"""
SQL_GROUPS_VERIFY = """
    SELECT COUNT(*) FROM HELPDESK.LDAP_GROUPS 
    WHERE UPPER(DISTINGUISHEDNAME) LIKE UPPER(:domain)
"""
SQL_USER_GROUPS_VERIFY = """
    SELECT COUNT(*)  FROM HELPDESK.LDAP_USER_GROUPS 
    WHERE UPPER(GROUP_DN) LIKE UPPER(:domain)
"""

SQL_USERS_DELETE = "DELETE FROM HELPDESK.LDAP_SYNC"
SQL_GROUPS_DELETE = "DELETE FROM HELPDESK.LDAP_GROUPS"
SQL_USER_GROUPS_DELETE = "DELETE FROM HELPDESK.LDAP_USER_GROUPS"

SQL_USER_INSERT = """
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

SQL_GROUP_INSERT ="""
    INSERT INTO HELPDESK.LDAP_GROUPS ( 
        NAME, DISTINGUISHEDNAME, DESCRIPTION, 
        WHENCHANGED, DISPLAYNAME, MANAGEDBY
    ) VALUES (
        :groupName, :distinguishedName, :description,
        :whenChanged, :displayName, :managedBy
    )
"""

SQL_USER_GROUP_INSERT ="""
    INSERT INTO HELPDESK.LDAP_USER_GROUPS (USER_DN, GROUP_DN) 
    VALUES (:user_dn, :group_dn)
"""
