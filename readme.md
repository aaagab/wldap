# install ldap module
pip install ldap3
https://ldap3.readthedocs.io/en/latest/

**DIT**: directory information tree  
With Simple Password you provide a DN (Distinguished Name) and a password.
To identify an entry you must specify its path in the DIT starting from the leaf that represents the entry up to the top of the Tree. This path is called the Distinguished Name (DN) of an entry and is constructed with key-value pairs, separated by a comma, of the names and the values of the entries that form the path from the leaf up to the top of the Tree. The DN of an entry is unique throughout the DIT and changes only if the entry is moved into another container within the DIT. The parts of the DN are called Relative Distinguished Name (RDN) because they are unique only in the context where they are defined. if you have a inetOrgPerson entry with RDN cn=Fred that is stored in an organizationaUnit with RDN ou=users that is stored in an organization with RDN o=company the DN of the entry will be cn=Fred,ou=users,o=company. The RDN value must be unique in the context where the entry is stored. LDAP also supports a (quite obscure) “multi-rdn” naming option where each part of the RDN is separated with the + character, as in cn=Fred+sn=Smith.

```python
from ldap3 import Server, Connection, SAFE_SYNC, ALL, NTLM, SUBTREE, ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES

server = Server('ipa.demo1.freeipa.org',  get_info=ALL)
conn = Connection(server, auto_bind=True)
print(server.info)
print(server.schema)

# search less than 10 results
conn=Connection(server, dy_conf["account"], dy_conf["password"], auto_bind=True)
conn.search(dy_conf["dc"], '(&(objectCategory=person)(objectClass=user))')
print(conn.entries)

# search more than 1000 results
conn=Connection(server, dy_conf["account"], dy_conf["password"], auto_bind=True)
entry_generator = conn.extend.standard.paged_search(
    dy_conf["dc"], 
    '(&(objectCategory=person)(objectClass=user))',
    search_scope=SUBTREE, 
    generator=True,
)
total_entries=0
for entry in entry_generator:
    total_entries += 1
    print(total_entries)
print('Total entries retrieved:', total_entries)
```

use wldap --get-conf-path to get configuration path and set file settings.json there.  
`settings.json`  
```JSON
{
    "account": "my_account_name",
    "dc": "DC=ad,DC=university,DC=edu",
    "domain": "myplace.ad.university.edu",
    "groups": [
        "university-faculty",
        "university-staff",
        "university-students"
    ],
    "password": "my_password",
    "email_suffix": "@university.edu"
}
```