# LDAP Synchronizer

## Description

A Python base application to synchronize user data from LDAP to ORACLE

### Dependencies

The fiile [requirements.txt](./requirements.txt) stores the python libraries the application uses.
To install the dependencies run:

```sh
    pip install -r requirements.txt
```

* `python-dotenv` is used to read environment variables if set up. The application checks for environment variables to allow easier deployment and development. Environment variables can be set in the machine environment, or in an `.env` file in the application directory. If none are specified the application will use the default values hardcoded in the source.  

* `python-ldap` or `ldap3`. These libraries handle the connection to the LDAP server. Only one is needed. At the moment Ldap3 seems promising due to less requirements during install.

* 'pyodbc' handles the connection to SQL databases.
  
* `cx-oracle` handles the connection to the Oracle database. It is frozen to version `8.3.0`.
  
### Environment Variables

The application relies on several variables:

* `ORACLE_LIB_DIR` stores the path to the Oracle InstantClient installation. The application can read it from the machine environment or the '.env' file. If none found it defaults on windows to: `C:/oracle/product/instantclient/instantClient_<VERSION>_64bit`. The version is not important (latest is best), however it MUST be 64bit.
* `ORACLE_TNS_DIR` has the path to the tnsnames.ora file. The default in windows is `C:/oracle/TNS_ADMIN`.
* `LOG_FILE` has the path and name of the log file. In windows it defaults to `C:/ProgramData/BBS/Focus/ldap-synchronizer.log`.
* `LDAP_Server` the address of thje LDAP server to connect to.
* `LDAP_Username` the cn string with the user the connect as. For example `CN=<name>,OU=Service Accounts,OU=Administrative Objects, dc=bundysugar,dc=com,dc=au`
* `LDAP_Password` the password for the specified user.
* `DB_Name` the target database form the synchronization.
* `DB_User` the database user to connect as.
* `DB_Password` the database user password.
  