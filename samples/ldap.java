/**
 *
 * Synchronise LDAP data from Active Directory to the IT Database.
 *
 * $Id: LdapDbSync.java,v 1.8 2016/05/30 04:19:52 mabyrne Exp mabyrne $
 *
 * @version 1.1
 * @author Malcolm Byrne
 * @since 1.1
 *
 * Synchronize data from the Active Directory to the following tables:
 *
 *     LDAP_SYNC
 *     LDAP_GROUPS
 *     LDAP_USER_GROUPS
 *
 * This program does lazy sync, (delete all, then repopulate). Please don't
 * run this too frequently as it will stress the database!
 *
 * ARG[0]  -  Database connect string.
 *
 *  Database activity is summarised as:
 *
 *      Table               Purpose                 Actions
 *      LDAP_SYNC           User details            Mass delete then mass insert.
 *      LDAP_GROUPS         AD groups               Mass delete then mass insert.
 *      LDAP_USER_GROUPS    User group membership   Mass delete then mass insert.
 *
 *
 *
 *  Changes:
 *
 *    30-AUG-2010    M.A.Byrne            Added attribute extensionAttribute1
 *
 *    31-MAY-2016    M.A.Byrne            Added accountExpires
 */


import java.util.Hashtable;
import javax.naming.*;
import javax.naming.directory.*;
import java.sql.SQLException;
import java.text.*;
import java.sql.*;

import java.util.ArrayList;
import java.util.Calendar;
import java.util.Enumeration;
import java.util.GregorianCalendar;
import java.util.List;
import java.util.ListIterator;


public class


LdapDbSync {
    static Statement stmt = null;
    static ResultSet rs = null;
    static Connection dbh;
    final static String DRIVERCLASS           = "oracle.jdbc.driver.OracleDriver" ;
    final static String LDAP_Server           = "ldap://172.20.40.17:389/";
    final static String LDAP_Username         = "CN=ldapauth ,OU=Service Accounts, OU=Administrative Objects, dc=bundysugar,dc=com,dc=au";
    final static String LDAP_Password         = "Gl3nNw1t";
    static String dbName                      = "bundy:1524:IT";
    static String dbUser                      = "helpdesk";
    static String dbPassword                  = "L2OoOd8";
    static String ident                       = "$Id: LdapDbSync.java,v 1.8 2016/05/30 04:19:52 mabyrne Exp mabyrne $";

    public static void main(String[] args) {

        System.out.println(ident);

        if ( args.length == 1 ) {
            dbName = args[0];
        }

        if ( args.length == 2 ) {
            dbName = args[0];
            dbPassword = args[1];
        }

        try {
            dbConnect();
            SyncUsers();
            SyncGroups();
            SyncGroupMembers();
            dbh.close();
        } catch (SQLException se) {
            System.err.println(se);
            System.err.println(se.getStackTrace());
        }
    }


    public static void SyncUsers() {

        /*
         * Insert and update table : LDAP_SYNC
         */

        String sn;
        String givenName;
        String samAccountName;
        String lastLogonTimestamp;
        String physicalDeliveryOfficeName;
        String title;
        String whenChanged;
        String department;
        String manager;
        String mail;
        String mobile;
        String displayName;
        String telephoneNumber;
        String userAccountControl;
        String description;
        String distinguishedName;
        String mDBUseDefaults;
        String mDBOverQuotaLimit;
        String mDBStorageQuota;
        String vascoLocked;
        String dbWhenChanged;
        String pwdLastSet;
        String whenCreated;
        String extensionAttribute1;
        String accountExpires;
        ArrayList arrUsers;
        Hashtable hUsers = new Hashtable();

        String qryWhenChanged = "select to_char(whenChanged,'YYYYMMDDHH24MISS') from ldap_sync where samAccountName=?";
        String qryInsert =
            "INSERT INTO HELPDESK.LDAP_SYNC ( " +
            "SAMACCOUNTNAME, SN, GIVENNAME, " +
            "LASTLOGONTIMESTAMP, PHYSICALDELIVERYOFFICENAME, TITLE, " +
            "WHENCHANGED, DEPARTMENT, MANAGER, "  +
            "MAIL, MOBILE, DISPLAYNAME, " +
            "TELEPHONENUMBER, USERACCOUNTCONTROL, DESCRIPTION, DISTINGUISHEDNAME, " +
            "MDBOVERQUOTALIMIT, MDBSTORAGEQUOTA, MDBUSEDEFAULTS, VASCOLOCKED, " +
            "PWDLASTSET, WHENCREATED, EXTENSIONATTRIBUTE1, ACCOUNTEXPIRES ) " +
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)";

        String qryDelete = "DELETE from LDAP_SYNC";

        String qryUpdate =
            "UPDATE HELPDESK.LDAP_SYNC set " +
            "sn=?," +
            "givenName=?," +
            "lastLogonTimestamp=?," +
            "physicalDeliveryOfficeName=?," +
            "Title=?," +
            "whenChanged=?," +
            "department=?," +
            "manager=?,"  +
            "mail=?," +
            "mobile=?," +
            "displayName=?," +
            "telephoneNumber=?," +
            "userAccountControl=?," +
            "description=?," +
            "distinguishedName=?," +
            "mDBOverQuotaLimit=?," +
            "mDBStorageQuota=?," +
            "mDBUseDefaults=?," +
            "vascoLocked=?, " +
            "pwdlastset=?" +
            "accountexpires=?" +
            "WHERE samAccountName=?";

        CallableStatement stmtWhenChanged = null;
        CallableStatement stmtInsert = null;
        CallableStatement stmtDelete = null;

        SimpleDateFormat df = new SimpleDateFormat("EEEE d-MMM-yyyy k:mm:ss");
        System.out.println( df.format(new Date( new GregorianCalendar().getTimeInMillis())).toUpperCase() );

        try {
            stmtWhenChanged = dbh.prepareCall(qryWhenChanged);
            stmtInsert = dbh.prepareCall(qryInsert);

            stmtDelete = dbh.prepareCall(qryDelete);    //Delete all LDAP user Records from the database
            stmtDelete.execute();
            stmtDelete.close();

            Hashtable env = new Hashtable();
            env.put(Context.INITIAL_CONTEXT_FACTORY, "com.sun.jndi.ldap.LdapCtxFactory");
            env.put(Context.SECURITY_AUTHENTICATION,"simple");
            env.put(Context.PROVIDER_URL, LDAP_Server);
            env.put(Context.SECURITY_PRINCIPAL, LDAP_Username );
            env.put(Context.SECURITY_CREDENTIALS, LDAP_Password );

            DirContext ctx = new InitialDirContext(env);
            String filter = "(objectClass=Person)";    // LDAP search filter

            String[] attrIDs = {      // Which attributes to return
                "samAccountName",
                "sn",
                "givenName",
                "fullName",
                "lastLogonTimestamp",
                "physicalDeliveryOfficeName",
                "title",
                "whenChanged",
                "department",
                "manager",
                "mail",
                "mobile",
                "displayName",
                "telephoneNumber",
                "description",
                "userAccountControl",
                "distinguishedName",
                "mDBOverQuotaLimit",
                "mDBStorageQuota",
                "mDBUseDefaults",
                "vasco-Locked",
                "pwdLastSet",
                "whenCreated",
                "extensionAttribute1",
                "accountExpires"
            };
            SearchControls ctls = new SearchControls();
            ctls.setReturningAttributes(attrIDs);
            ctls.setSearchScope(ctls.SUBTREE_SCOPE);
            NamingEnumeration answer = ctx.search("CN=Users, dc=bundysugar,dc=com,dc=au", filter, ctls);

            Integer cntInserts = 0;

            while (answer.hasMore()) {
                sn="";
                givenName="";
                samAccountName="";
                lastLogonTimestamp="";
                physicalDeliveryOfficeName="";
                title="";
                whenChanged="";
                department="";
                manager="";
                mail="";
                mobile="";
                displayName="";
                telephoneNumber="";
                userAccountControl="";
                description="";
                distinguishedName="";
                mDBOverQuotaLimit="";
                mDBStorageQuota="";
                mDBUseDefaults="";
                vascoLocked="";
                pwdLastSet="";
                whenCreated="";
                extensionAttribute1="";
                accountExpires="";

                SearchResult sr = (SearchResult)answer.next();
                String dn = sr.getName();
                Attributes attrs = sr.getAttributes();

                samAccountName=GetAttribute(attrs,"samAccountName");
                sn=GetAttribute(attrs,"sn");
                givenName=GetAttribute(attrs,"givenName");
                lastLogonTimestamp=GetAttribute(attrs,"lastLogonTimestamp");
                physicalDeliveryOfficeName=GetAttribute(attrs,"physicalDeliveryOfficeName");
                title=GetAttribute(attrs,"title");
                whenChanged=GetAttribute(attrs,"whenChanged");
                department=GetAttribute(attrs,"department");
                manager=GetAttribute(attrs,"manager");
                mail=GetAttribute(attrs,"mail");
                mobile=GetAttribute(attrs,"mobile");
                displayName=GetAttribute(attrs,"displayName");
                telephoneNumber=GetAttribute(attrs,"telephoneNumber");
                userAccountControl=GetAttribute(attrs,"userAccountControl");
                description=GetAttribute(attrs,"description");
                distinguishedName=GetAttribute(attrs,"distinguishedName");
                mDBOverQuotaLimit=GetAttribute(attrs,"mDBOverQuotaLimit");
                mDBStorageQuota=GetAttribute(attrs,"mDBStorageQuota");
                mDBUseDefaults=GetAttribute(attrs,"mDBUseDefaults");
                vascoLocked=GetAttribute(attrs,"vasco-Locked");
                pwdLastSet=GetAttribute(attrs,"pwdLastSet");
                whenCreated=GetAttribute(attrs,"whenCreated");
                extensionAttribute1=GetAttribute(attrs,"extensionAttribute1");
                accountExpires=GetAttribute(attrs,"accountExpires");
                hUsers.put(samAccountName,new Integer(1));

                // Skip this one if samAccountName is blank
                if ( samAccountName == "" ) {
                    continue;
                }

                try {
                    Long lLastLogonTimestamp = 0L;
                    if ( lastLogonTimestamp != "" ) {
                        lLastLogonTimestamp = Long.parseLong(lastLogonTimestamp);
                    }


                    Long lPwdLastSet = 0L;
                    if ( pwdLastSet != "" ) {
                        lPwdLastSet = Long.parseLong(pwdLastSet);
                    }


                    dbWhenChanged =  null;
                    stmtInsert.setString(1,samAccountName);
                    stmtInsert.setString(2,sn);
                    stmtInsert.setString(3,givenName);
                    stmtInsert.setLong(4,lLastLogonTimestamp);
                    stmtInsert.setString(5,physicalDeliveryOfficeName);
                    stmtInsert.setString(6,title);
                    stmtInsert.setTimestamp( 7,new Timestamp( ParseWackyLDAPDate(whenChanged).getTime())  );
                    stmtInsert.setString(8,department);
                    stmtInsert.setString(9,manager);
                    stmtInsert.setString(10,mail);
                    stmtInsert.setString(11,mobile);
                    stmtInsert.setString(12,displayName);
                    stmtInsert.setString(13,telephoneNumber);
                    stmtInsert.setString(14,userAccountControl);
                    stmtInsert.setString(15,description);
                    stmtInsert.setString(16,distinguishedName);
                    stmtInsert.setString(17,mDBOverQuotaLimit);
                    stmtInsert.setString(18,mDBStorageQuota);
                    stmtInsert.setString(19,mDBUseDefaults);
                    stmtInsert.setString(20,vascoLocked);
                    stmtInsert.setLong(21,lPwdLastSet);
                    stmtInsert.setTimestamp( 22,new Timestamp( ParseWackyLDAPDate(whenCreated).getTime())  );
                    stmtInsert.setString(23,extensionAttribute1);
                    stmtInsert.setString(24,accountExpires);
                    stmtInsert.execute();
                    cntInserts++;
                    //System.out.println( samAccountName + " Inserted " );
                } catch ( SQLException e ) {
                    System.err.println(e);
                    e.printStackTrace();
                }
            }
            ctx.close();
            dbh.commit();
            stmtInsert.close();
            stmtWhenChanged.close();
            System.out.println("  " + cntInserts + " Records inserted");
        } catch(Exception e) {
            System.err.println(e);
            e.printStackTrace();
        }
    }

    public static void SyncGroups () {
        /*
         * Insert and Update data in table :  LDAP_GROUPS
         */

        String name;
        String distinguishedName;
        String description;
        String whenChanged;
        String dbWhenChanged;
        String displayName;
        String managedBy;

        String qryInsert =
            "INSERT INTO HELPDESK.LDAP_GROUPS ( " +
            "NAME,DISTINGUISHEDNAME,DESCRIPTION, WHENCHANGED,DISPLAYNAME,MANAGEDBY )" +
            "VALUES (?,?,?,?,?,?)";

        CallableStatement stmtInsert = null;

        System.out.println("Syncing groups...");
        SimpleDateFormat df = new SimpleDateFormat("EEEE d-MMM-yyyy k:mm:ss");
        System.out.println( "  " + df.format(new Date( new GregorianCalendar().getTimeInMillis())).toUpperCase() );

        try {
            String qryDelete = "DELETE FROM LDAP_GROUPS";
            CallableStatement stmtDel = dbh.prepareCall(qryDelete);
            stmtDel.execute();
            stmtDel.close();

            stmtInsert = dbh.prepareCall(qryInsert);
            Hashtable env = new Hashtable();
            env.put(Context.INITIAL_CONTEXT_FACTORY, "com.sun.jndi.ldap.LdapCtxFactory");
            env.put(Context.SECURITY_AUTHENTICATION,"simple");
            env.put(Context.PROVIDER_URL, LDAP_Server);
            env.put(Context.SECURITY_PRINCIPAL, LDAP_Username );
            env.put(Context.SECURITY_CREDENTIALS, LDAP_Password );
            DirContext ctx = new InitialDirContext(env);

            String filter = "(objectClass=group)";  // LDAP query filter
            String[] attrIDs = {
              "samAccountname",
              "displayName",
              "distinguishedName",
              "description",
              "whenChanged",
              "member",
              "managedBy"
            };
            SearchControls ctls = new SearchControls();
            ctls.setReturningAttributes(attrIDs);
            ctls.setSearchScope(ctls.SUBTREE_SCOPE);
            NamingEnumeration answer = ctx.search("dc=bundysugar,dc=com,dc=au", filter, ctls);
            Integer cntInserts = 0;

            while (answer.hasMoreElements()) {
                name="";
                distinguishedName="";
                whenChanged="";
                description="";
                displayName="";
                managedBy="";

                SearchResult sr = (SearchResult)answer.next();
                String dn = sr.getName();
                Attributes attrs = sr.getAttributes();
                name=GetAttribute(attrs,"samAccountName");
                distinguishedName=GetAttribute(attrs,"distinguishedName");
                description=GetAttribute(attrs,"description");
                whenChanged=GetAttribute(attrs,"whenChanged");
                displayName=GetAttribute(attrs,"displayname");
                managedBy=GetAttribute(attrs,"managedBy");
                if ( displayName.length() == 0 ) {
                    displayName=name;
                }
                try {
                    dbWhenChanged =  null;
                    stmtInsert.setString(1,name);
                    stmtInsert.setString(2,distinguishedName);
                    stmtInsert.setString(3,description);
                    stmtInsert.setTimestamp( 4,new Timestamp( ParseWackyLDAPDate(whenChanged).getTime())  );
                    stmtInsert.setString(5,displayName);
                    stmtInsert.setString(6,managedBy);
                    stmtInsert.execute();
                    cntInserts++;
                } catch (SQLException e) {
                    System.err.println(e);
                    e.printStackTrace();
                }
            }
            System.out.println("  " + cntInserts + " groups inserted.");
            ctx.close();
            dbh.commit();
            stmtInsert.close();
        } catch(Exception e) {
            System.err.println(e);
            e.printStackTrace();
        }
    }


    public static void SyncGroupMembers () {
        String name;
        String distinguishedName;
        String whenChanged;
        String description;
        String dbWhenChanged;
        Hashtable hGroups = new Hashtable();

        System.out.println("Syncing group membership...");
        String qryDrop = "DELETE FROM LDAP_USER_GROUPS";
        // ALB NOT USED String qryClean = "delete from ldap_user_groups where user_dn not in ( select distinguishedname from ldap_sync )";

        CallableStatement stmtWhenChanged = null;
        CallableStatement stmtInsert = null;
        CallableStatement stmtDrop= null;
        CallableStatement stmtClean= null;

        SimpleDateFormat df = new SimpleDateFormat("EEEE d-MMM-yyyy k:mm:ss");
        System.out.println( "  " + df.format(new Date( new GregorianCalendar().getTimeInMillis())).toUpperCase() );

        try {
            stmtDrop = dbh.prepareCall(qryDrop);
            stmtDrop.execute();
            stmtDrop.close();

            Hashtable env = new Hashtable();

            env.put(Context.INITIAL_CONTEXT_FACTORY, "com.sun.jndi.ldap.LdapCtxFactory");
            env.put(Context.SECURITY_AUTHENTICATION,"simple");
            env.put(Context.PROVIDER_URL, LDAP_Server);
            env.put(Context.SECURITY_PRINCIPAL, LDAP_Username );
            env.put(Context.SECURITY_CREDENTIALS, LDAP_Password );

            DirContext ctx = new InitialDirContext(env);
            String filter = "(objectClass=group)";          //LDAP search filter
            String[] attrIDs = { "member; range=0-999" };    //Attributes to return
            SearchControls ctls = new SearchControls();
            ctls.setReturningAttributes(attrIDs);

            ctls.setSearchScope(ctls.SUBTREE_SCOPE);

            NamingEnumeration answer = ctx.search("DC=bundysugar,DC=com,DC=au", filter, ctls);

            while (answer.hasMoreElements()) {
                SearchResult sr = (SearchResult)answer.next();
                String GroupDn = sr.getNameInNamespace();
                hGroups.put(GroupDn, new ArrayList() );      // Store the members list into the group hash
                Attributes attrs = sr.getAttributes();

                if (attrs != null) {
                    try {
                        for (NamingEnumeration ae = attrs.getAll();ae.hasMore();) {
                            Attribute attr = (Attribute)ae.next();
                            if ( attr.getID().contains("member") ) {
                                for (NamingEnumeration e = attr.getAll();e.hasMore();) {
                                    String member = e.next().toString();
                                    ((ArrayList)hGroups.get(GroupDn)).add(member);
                                }
                            }
                        }
                    }  catch (Exception e)   {
                        System.out.println("Problem printing attributes: " + e);
                    }
                }
            }

            /*
             * Loop through all groups and members to identify sub-groups
             * This bit will replace the group name with it's members
             * CAVEAT: Membership replacement can include groups itself:
             *   We need to re-scan the list, to flesh out these sub groups.
             *   But wait!!!
             *     Circular references are possible...  I have averted
             *     this issue by limiting the depth of rescanning to 4
             *     iterations.
             *
             */

            Boolean retry = true;
            Integer loops = 0;
            ArrayList newMembers;

            while ( retry && loops < 4 ) {          // limit loops to avoid cyclic references
                retry = false;
                loops++;
                for (Enumeration e = hGroups.keys() ; e.hasMoreElements() ;) {  // Loop Grops
                    String g = (String) e.nextElement();
                    ListIterator li = ((ArrayList)hGroups.get(g)).listIterator();
                    newMembers = new ArrayList();
                    while(li.hasNext()) {
                        String member = (String)li.next();
                        if (hGroups.get(member) != null ) {   // is this member a group?
                            newMembers.addAll( (ArrayList)hGroups.get(member) );
                            retry = true;
                        } else {
                            newMembers.add(member);
                        }
                    }
                    if (retry) {
                        hGroups.put(g,newMembers);      // Replace the member list with the new one
                    }
                }
            }

            // Now push the data to the database
            String qryInsert = "INSERT INTO LDAP_USER_GROUPS (USER_DN, GROUP_DN ) VALUES (?,?)";
            stmtInsert = dbh.prepareCall(qryInsert);
            Integer cntInserts=0;
            // Loop through all groups and members to identify sub-groups
            for (Enumeration e = hGroups.keys() ; e.hasMoreElements() ;) {  // Loop Grops
                String group = (String) e.nextElement();
                ListIterator li = ((ArrayList)hGroups.get(group)).listIterator();

                int cntGroupMembers = 0;
                while(li.hasNext()) {
                    String member = (String)li.next();
                    stmtInsert.setString(1,member);
                    stmtInsert.setString(2,group);
                    try {
                        stmtInsert.execute();
                        cntInserts++;
                        cntGroupMembers++;
                    } catch(SQLException e2) {
                        if ( e2.toString().contains("ORA-00001")) {
                                // Duplicates are expected
                        } else {
                            //throw new SQLException(e2.toString());
                            System.out.println("ERROR whilst inserting LDAP_USER_GROUPS : " + e2.toString() );
                        }

                    }
                }
            }
            stmtInsert.close();
            System.out.println("  " + cntInserts + " records.");

            ctx.close();
            dbh.commit();

        } catch(Exception e) {
            System.err.println(e);
            e.printStackTrace();
        }
    }




public static Date ParseWackyLDAPDate( String ds ) {
    Calendar c = new GregorianCalendar() ;
    Date dt;

    c.set(Calendar.YEAR, Integer.parseInt( ds.substring(0,4)));
    c.set(Calendar.MONTH,Integer.parseInt( ds.substring(4,6))-1);
    c.set(Calendar.DAY_OF_MONTH,Integer.parseInt( ds.substring(6,8)));
    c.set(Calendar.HOUR_OF_DAY,Integer.parseInt( ds.substring(8,10)));
    c.set(Calendar.MINUTE,Integer.parseInt( ds.substring(10,12)));
    c.set(Calendar.SECOND,Integer.parseInt( ds.substring(12,14)));
    dt = new Date( c.getTimeInMillis());
    return dt;
}


public static String GetAttribute( Attributes attrs, String item ) {
    /*
     * LDAP Attributes are returned in string format with the attribute
     * name and a :
     *
     * Attribute: Value
     *
     * This routine removes the attribute and the colon.
     */
    String result;
    try {
        result = attrs.get(item).toString();
        result = result.substring(result.indexOf(':')+2);   // Remove attribute name and :
    } catch ( Exception err) {
        result = "";
    }
    return result;
}


public static void dbConnect() throws SQLException {
    System.out.println("Connecting to database : " + dbName );
    try  {
        String driver;
        Class.forName(DRIVERCLASS).newInstance();
        driver = "jdbc:oracle:thin:@" + dbName;
        dbh = DriverManager.getConnection(driver, dbUser, dbPassword);
    } catch (InstantiationException e) {
        throw new SQLException(e.toString());
    } catch (ClassNotFoundException e) {
        throw new SQLException(e.toString());
    } catch (IllegalAccessException e) {
        throw new SQLException(e.toString());
    } catch (SQLException e) {
        throw new SQLException(e.toString());
    }
}
}







