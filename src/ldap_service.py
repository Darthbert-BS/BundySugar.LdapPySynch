import os
from ldap3 import SUBTREE,Server, Connection, ALL

ERROR_LDAP_CONNECTION = 200
ERROR_LDAP_SEARCH_USERS = 210
ERROR_LDAP_SEARCH_GROUPS = 220

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

class LdapService:
    def __init__(self, logger):
        self.logger = logger
        self.ldapConnection = None


    def connect(self, prefix='BS'):
        try:
            self._prefix = prefix
            self.logger.info("")
            self.logger.info(f"[{self._prefix}] Connecting to LDAP Server")

            server = Server(
                os.getenv(f"LDAP_{prefix}_Server"), 
                port=int(os.getenv(f"LDAP_{prefix}_Port", 389)), 
                get_info=ALL
            )            
            
            self.ldapConnection = Connection(
                server, 
                user=os.getenv(f"LDAP_{prefix}_Username"), 
                password=os.getenv(f"LDAP_{prefix}_Password"),
                return_empty_attributes=True,
                auto_bind=True
            )
            
            self.logger.info(f"[{self._prefix}] {self.ldapConnection}") 
            self.logger.info(f"[{self._prefix}] {self.ldapConnection.extend.standard.who_am_i()}")
            self.logger.info(f"[{self._prefix}] LDAP Connection established...")

        except Exception as error:
            self.logger.error(f"[{self._prefix}] Error connecting to LDAP", error)
            exit(ERROR_LDAP_CONNECTION)    


    def get_users(self):
        object_class= 'person' 
        server_name = os.getenv(f"LDAP_{self._prefix}_Username").split(',dc=')[1] 
        search_base = f'cn=users,dc={server_name},dc=com,dc=au'
        search_filter = f'(&(objectcategory={object_class})(objectclass=user)(samAccountName=*)(sn=*))'

        self.logger.info(f"[{self._prefix}] Searching LDAP Users for:{search_base} with filter: {search_filter}")

        try:
            self.ldapConnection.search(
                search_base, 
                search_filter=search_filter,
                attributes=USER_ATTRIBUTES,
                search_scope = SUBTREE,
                get_operational_attributes=True
            )
            self.logger.info(f'[{self._prefix}] Found {len(self.ldapConnection.entries)} user entries.')
                
            return self.ldapConnection.entries   
        except Exception as error:
            self.logger.error(f"[{self._prefix}] Error searching Users", error)
            exit(ERROR_LDAP_SEARCH_USERS)


    def get_groups(self):
        object_class= 'group' 
        server_name = os.getenv(f"LDAP_{self._prefix}_Username").split(',dc=')[1] 
        search_base = f'dc={server_name},dc=com,dc=au'
        search_filter = f'(&(objectclass={object_class})(samAccountName=*))'

        self.logger.info(f"[{self._prefix}] Searching LDAP Groups for:{search_base} with filter: {search_filter}")
        try:
            self.ldapConnection.search(
                search_base, 
                search_filter=search_filter,
                attributes=GROUP_ATTRIBUTES,
                search_scope = SUBTREE,
                get_operational_attributes=True
            )
           
            self.logger.info(f'[{self._prefix}] Found {len(self.ldapConnection.entries)} group entries.')
            
            return {
                'groups': self.ldapConnection.entries,
                'userGroups': self._get_group_members(self.ldapConnection.entries)
            }
            
        except Exception as error:
            self.logger.error(f"[{self._prefix}] Error searching LDAP Groups:", error)
            exit(ERROR_LDAP_SEARCH_GROUPS)
    

    def _get_group_members(self, entries ):
        try:
            # gets the groups               
            groups_hash_table = self._get_groups_hash(entries)
            # expands them recursively
            expanded_groups = self._expand_nested_groups(groups_hash_table)
            self.logger.info(f'[{self._prefix}] Found {len(expanded_groups)} group member entries.')
            return expanded_groups

        except Exception as error:
            self.logger.error(f"[{self._prefix}] Error searching LDAP Groups Members", error)
            exit(ERROR_LDAP_SEARCH_GROUPS)


    def _get_groups_hash(self, entries):
        groups_hash_table = {}
        for entry in entries:
            # Get the Distinguished Name of the group and 
            # Initialize an empty list for this group's members
            group_dn = entry.entry_dn
            groups_hash_table[group_dn] = set()

            if entry.entry_attributes:
                try:
                    # Iterate over all attributes 
                    for attr_name in entry.entry_attributes:
                        # Check if the attribute name contains 'member'
                        if 'member' in attr_name.lower():
                            # Get all values of this attribute
                            members = entry[attr_name]
                            # Add each member to the group's set
                            groups_hash_table[group_dn].update(str(member) for member in members)
                except Exception as e:
                    self.logger.warn(f"[{self._prefix}] Problem processing attributes for {group_dn}: {e}")

        return groups_hash_table


    def _expand_nested_groups(self, groups_hash, max_depth=MAX_LOOP_DEPTH):
        """
        Expand nested groups in the given dictionary of groups and their members.
        
        :param h_groups: Dictionary where keys are group DNs and values are lists of member DNs
        :return: Updated dictionary with expanded group memberships
        """
        retry = True
        loops = 0

        while retry and loops < max_depth:  # limit loops to avoid cyclic references
            retry = False
            loops += 1
            for group_dn, members in list(groups_hash.items()):  # Use list() to allow dict modification during iteration
                new_members = set()
                for member in members:
                    if member in groups_hash:  # is this member a group?
                        new_members.update(groups_hash[member])
                        retry = True
                    else:
                        new_members.add(member)
                if retry:
                    groups_hash[group_dn] = new_members  # Replace the member list with the new one

        return groups_hash


    def _flatten_list (self, nested_list):
        # Flatten the list for debugging
        array = []     
        for group_dn, members in nested_list.items():
            for member in members:
                array.append({'group_dn': group_dn, 'member_dn': member})
        
        self.logger.info(f'[{self._prefix}] Flattened to {len(array)} member entries.')
        return array        

    def _compare_group_changes(self, original_groups, expanded_groups):
        """
        Compare original and expanded group memberships and return differences.
        Used for testing purposes
        
        :param original_groups: Original dictionary of groups and their members
        :param expanded_groups: Expanded dictionary of groups and their members
        :return: Dictionary of groups with changed memberships
        """
        changes = {}

        for group, expanded_members in expanded_groups.items():
            if group in original_groups:
                original_members = set(original_groups[group])
                expanded_members_set = set(expanded_members)
                
                if original_members != expanded_members_set:
                    added = expanded_members_set - original_members
                    removed = original_members - expanded_members_set
                    
                    changes[group] = {
                        "added": list(added),
                        "removed": list(removed)
                    }
            else:
                # This case shouldn't occur if expanded_groups is derived from original_groups,
                # but we include it for completeness
                changes[group] = {
                    "added": expanded_members,
                    "removed": []
                }

        return changes


    def disconnect(self):
        self.ldapConnection.unbind()    
        self.logger.info(f"[{self._prefix}] LDAP Connection closed...")

