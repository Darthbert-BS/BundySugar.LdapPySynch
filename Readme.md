<!-- omit in toc -->
# LDAP Synchronizer

- [Description](#description)
  - [Application Flow](#application-flow)
- [Dependencies](#dependencies)
  - [Dependency Description](#dependency-description)
- [Environment Variables](#environment-variables)
  - [Database connection variables](#database-connection-variables)
  - [LDAP Connection variables](#ldap-connection-variables)
  - [Other Configuration variables](#other-configuration-variables)
  - [Testing](#testing)
  - [Deployment](#deployment)
    - [Development](#development)
    - [Testing or Production](#testing-or-production)
- [Examples](#examples)
  - [Configuration file](#configuration-file)
  - [Batch file](#batch-file)

## Description

A Python base application to synchronize user data from LDAP to ORACLE for the HelpDesk.

### Application Flow

The application loads the configuration settings and initiates a synchronization event.

The synchronization event consists of reading user, groups, and group-users data from an Active Directory Server, and storing the retrieved information inside a set of tables in Oracle.

The entire synchronization cycle runs inside a transaction to ensure data is not lost if an error occurs.

The main steps are:

1. Establish connection to Oracle.
2. Initialize a transaction.
3. Remove existing data.
4. Connect to an Active Directory Server via LDAP protocol.
5. Read User data attributes and store them in the LDAP_SYNC table.
6. Verify all the users have been inserted.
7. Read Group data attributes and store them in the LDAP_GROUP table.
8. Verify all the groups have been inserted.
9. Read Group_User Data with a configurable recursion limit and store them to the LDAP_USER_GROUP table
10. Verify all the group_users_ have been inserted.
11. Close the LDAP connection to the AD Derver.
12. If more than one server was configured return to step 3 for the next AD Server
13. If no more AD Servers are configured, commit the Oracle Transaction and exit.
14. At any given time during the process, if an error occurs, it is logged and the Oracle transaction is rolled back.  

## Dependencies

The application requires Python 3.13.2

The application relies on the correct installation of `Oracle InstantClient`. The version number is not important (latest is best), however it MUST be a **64bit** version.

The python libraries the application depend upon are defined in the [requirements.txt](./requirements.txt) file. To install them run:

```sh
    pip install -r requirements.txt
```

### Dependency Description

- `python-dotenv`: is used to read environment variables if set up. The application checks for environment variables to allow easier deployment and development. Environment variables can be set in the machine environment, or in an `.config` file in the application directory. If none are specified, the application will use the default values hardcoded in the source for some of the settings.
**NB: The application will error out if the required variables are not set. See the [Environment Variables](#environment-variables) section for which variables MUST be configured.**

- `ldap3`: handles the connection and querying LDAP servers.
  
- `cx-oracle` handles the connection to the Oracle database. It is frozen to version `8.3.0`. The library `cx-oracle` is not available as a binary for direct download, therefore `pip` attempts to build a wheel. If the wheel compilation fails, please make sure the Microsoft dependencies [MSBuild Tools](./dependencies/vs_BuildTools.exe) and [VC++ 1.4 (or newer)](./dependencies/VC_redist.x64.exe) are installed.

## Environment Variables

As mentioned above, for security issues the some of the configuration values for the application should **NOT** be stored as hardcoded values in the source code. This also helps to prevent the accidental checking into the github repository of potential sensitive data. The application reads its configuration from environment variables set up either in a `.config` file or the machine environmet itself.
Other values, such as paths used are not sensitive and a default is hardcoded in the source.

The following is a list of variables the application uses with corresponding descriptions and examples.

### Database connection variables

**ORACLE_LIB_DIR and ORACLE_TNS_DIR are optional. The DB variables are compulsory.**

- `ORACLE_LIB_DIR`: (optional) the path to the `Oracle InstantClient` installation. The application can read it from the machine environment or the '.config' file. If not set, it defaults to a Windows path: `C:/oracle/product/instantclient/instantClient_11_2_64bit`.

- `ORACLE_TNS_DIR`: (optional) the path to the 'tnsnames.ora' file. If not set, The default in windows is `C:/oracle/TNS_ADMIN`.

- `DB_Name`: the target database form the synchronization. Example: `DB_Name = "ITD"`

- `DB_User`: the database user to connect as. Example: `DB_User = "Albonfiglio"`

- `DB_Password`: the database user password. Example: `DB_Password = "mysupersecureandunguessablepassword"`

### LDAP Connection variables

**All variables in this section are compulsory.**

- `LDAP_SERVER_LIST`: a string containing a comma separated list of prefixes. The prefixes identify the `Active Directory` (AD) Server to connect to. At the moment, only `BundySugar` with prefix `BS` and `MacNut` with prefix `MN` are used. Example: `LDAP_SERVER_LIST = "BS, MN"`

- `LDAP_<PREFIX>_Server`: the URL address of the AD Server to connect to for a given prefix. Example: `LDAP_BS_Server = "bsldc.bundysugar.com.au"`

- `LDAP_<PREFIX>_Username`: the AD `Common Name` string representing the user that has permission to connect to the AD Server. Example: `CN=<USER NAME>,OU=Service Accounts,OU=Administrative Objects, dc=bundysugar,dc=com,dc=au`

- `LDAP_<PREFIX>_Password` the password for the AD user.

**NB: For each entry in `LDAP_SERVER_LIST` there must be a corresponding set of LDAP_PREFIX_Value settings.**

### Other Configuration variables  

**All variables in this section are optional and if omitted they will default to the hard coded values.**

- `LOG_FILE`: (optional) the full path and name of the log file. In windows it defaults to `C:/ProgramData/BBS/Focus/ldap-synchronizer.log`.

- `LDAP_SYNC_VERBOSITY`: (optional) the amount of logging information outputted to the log file and the console. Valid values are `0 = errors`, `1 = errors and warnings`, `2 = errors, warnings and info`. Default is `2`.
  
### Testing

Testing should to be done on the `ITD` Oracle server. This is achieved by simply changing the `DB_Name` to `ITD` and the `DB_User` and `DB_Password` accordingly.

### Deployment

#### Development

Follow these steps to deploying to a development environment:

1. Ensure `Python 3.13.2` is installed on the machine and works:
  
        python --version
        or
        python3 --version

2. Ensure the necessary 64bit `Oracle InstantClient` library is installed. In Windows it should be located in `C:/oracle/product/instantclient/instantClient_11_2_64bit`. Also make sure the 'tnsnames.ora' is present. In Windows it should be located in `C:/oracle/TNS_ADMIN`.

3. Clone the repository from [github project](link to github repo), and navigate into the folder.

4. Create a Python environment in the folder by running:

        python -m venv .env
        or 
        python3 -m venv .env

5. Install the dependencies by running:

        pip install -r requirements.txt

6. Edit the `.config file` with the appropriate configuration data. An example of complete `.config` file is given [below](#configuration-file)  

7. Use the editor of choice for development.

#### Testing or Production

Follow these steps to deploying to a testing or production environment:

1. Ensure `Python 3.13.2` is installed on the machine and works:
  
        python --version
        or
        python3 --version

2. Ensure the necessary 64bit `Oracle InstantClient` library is installed. In Windows it should be located in `C:/oracle/product/instantclient/instantClient_11_2_64bit`. Also make sure the 'tnsnames.ora' is present. In Windows it should be located in `C:/oracle/TNS_ADMIN`.

3. Create a directory where to deploy the source code, and navigate to it.

4. Create a Python environment in the directory. This can be done by running:

        python -m venv .env
        or 
        python3 -m venv .env

5. Install the dependencies by running:

        pip install -r requirements.txt

6. Copy the '.config file', the 'sync.bat' file, and the content of the 'src' folder to the folder just created.

7. Edit the `.config file` with the appropriate configuration data. An example of complete `.config` file is given [below](#configuration-file)  

8. Run the application by executing the `sync.bat` batch file (see [below](#batch-file)) or by running

        .env\Scripts\activate
        or 
        .env/bin/activate
        
        python main.py
        or 
        python3 main.py

## Examples

### Configuration file

```txt
LOG_FILE            = "<PATH/FILENAME.log>"
LDAP_SYNC_VERBOSITY = 2

ORACLE_LIB_DIR      = "<PATH TO ORACLE_LIB_DIR>"
ORACLE_TNS_DIR      = "PATH TO ORACLE_TNA_ADMIN"
DB_Name             = "<MY ORACLE DB>"
DB_User             = "<MY USER ID>"
DB_Password         = "<MY USER PASSWORD>"

LDAP_SERVER_LIST    = "BS, MN"

LDAP_BS_Server      = "bsldc.bundysugar.com.au"
LDAP_BS_Port        = 389
LDAP_BS_Username    = "<BS CN USER>"
LDAP_BS_Password    = "<BS CN USER PASSWORD>"

LDAP_MN_Server      = "mia-dc-01.macnut.com.au"
LDAP_MN_Port        = 389
LDAP_MN_Username    = "<MN CN USER>"
LDAP_MN_Password    = "<MN CN USER>"
```

### Batch file

```sh
@echo off
setlocal enabledelayedexpansion

REM Check for python3
where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Python 3 found, running script with python3
    python3 main.py
    goto :eof
)

REM Check for python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    REM Check if it is Python 3.x
    for /f "tokens=1,2 delims=." %%a in ('python -c "import sys; print(sys.version)"') do (
        set PYTHON_MAJOR=%%a
        set PYTHON_MINOR=%%b
    )
    if !PYTHON_MAJOR! EQU 3 (
        echo Python 3.x found, running script with python
        python main.py
    ) else (
        echo Python 2.x found. This script requires Python 3.x.
        pause
    )
    goto :eof
)

REM If we get here, no suitable Python was found
echo No suitable Python installation found. Please install Python 3.x.
pause

:eof
endlocal
```
