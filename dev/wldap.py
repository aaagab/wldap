#!/usr/bin/env python3
from pprint import pprint
import json
import os
import re
import sys

import ldap3
from ldap3 import Server, Connection, SAFE_SYNC, ALL, NTLM, SUBTREE, ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES, ObjectDef, Reader

from ..gpkgs import message as msg

def get_attributes(conn):
    person = ObjectDef(['person', 'user'], conn)
    values=[]
    for line in repr(person).splitlines():
        reg=re.match(r"^(?P<key>[A-Z]+)\s*?:\s+(?P<values>.+)$", line.strip())
        if reg.group("key") in ["MUST", "MAY"]:
            values.extend(reg.group("values").split(", "))
    values=list(set(values))
    values.sort()
    return values

def get_one_line_filter(search_filter):
    tmp_text=""
    for line in search_filter.splitlines():
        line=line.strip()
        if len(line) > 0:
            if line[0] != "#":
                tmp_text+=line

    return tmp_text
    
class LdapServer():
    def __init__(self,
        account,
        dc,
        domain,
        default_groups,
        email_suffix,
        password,
    ):
        self.server=Server(domain, port=636, use_ssl=True, get_info=ALL)
        self.account=account
        self.dc=dc
        self.default_groups=default_groups
        self.password=password
        self.conn=None
        self.email_suffix=email_suffix

    def __enter__(self):
        self.conn=Connection(self.server, self.account, self.password)
        self.conn.bind()
        return self.conn

    def __exit__(self, type, value, traceback):
        #Exception handling here

        if type == ldap3.core.exceptions.LDAPAttributeError:
            self.conn.search(self.dc, self.search_filter, attributes=ALL_ATTRIBUTES)
            if len(self.conn.entries) == 1:
                entry=json.loads(self.conn.entries[0].entry_to_json())["attributes"]
                print("Authorized attributes are:")
                pprint(sorted(entry))
            else:
                print("Possible attributes are:")
                print(get_attributes(self.conn))
            msg.error(str(value))
            sys.exit(1)
        elif type == ldap3.core.exceptions.LDAPInvalidFilterError:
            msg.error("{}\n{}".format(str(value), self.search_filter))
            sys.exit(1)

        self.conn.unbind()

    def get_search_filter(self, groups=[]):
        search_filter="""
            (&
                (&
                    (objectCategory=person)
                    (objectClass=user)
                    #  (cn=cn)
                    # (userPrincipalName=email)
                    # UserAccountControl will only Include Non-Disabled Users.
                    (!(userAccountControl:1.2.840.113556.1.4.803:=2))
                    {{elem}}
                )
                {groups}
            )
        """

        groups_filter=""
        if len(groups) > 0:
            groups_filter+="(|"
            for group in groups:
                groups_filter+="(memberOf=CN={},OU=Groups,{})".format(group, self.dc)
            groups_filter+=")"

        search_filter=search_filter.format(groups=groups_filter)

        return get_one_line_filter(search_filter)

    def get_generator(self, show_filter, search_filter, get_attrs, size_limit):
        self.search_filter=search_filter
        if self.conn is None or self.conn.closed is True:
            msg.error("LDAP connection not binded", exit=1)
        attrs=get_attrs
        if get_attrs is None or len(get_attrs) == 0:
            attrs=ALL_ATTRIBUTES
            if get_attrs is not None and len(get_attrs) == 0:
                size_limit=1

        entry_generator=None
        # try:
        if show_filter is True:
            print(self.search_filter)
        if size_limit is None:
            size_limit=0

        entry_generator = self.conn.extend.standard.paged_search(
            self.dc, 
            self.search_filter,
            search_scope=SUBTREE, 
            generator=True,
            attributes=attrs,
            size_limit=size_limit,
        )
       
        return entry_generator

def raw_search(
    attr=None,
    count=False,
    get_attrs=None,
    ldap_srv=None,
    less=False,
    search_filter=None,
    show_filter=False,
    size_limit=None,
):
    search_filter=get_one_line_filter(search_filter)
    searches=[]
    counter=0
    with ldap_srv as conn:
        generator=ldap_srv.get_generator(show_filter, search_filter, get_attrs, size_limit)

        try:
            for entry in generator:
                if entry["type"] == "searchResEntry":
                    counter+=1
                    entry=dict(entry["attributes"])
                    if get_attrs is not None and len(get_attrs) == 0:
                        return sorted(entry)
                    for key, val in entry.items():
                        if isinstance(val, list):
                            if len(val) == 0:
                                entry[key]=None
                            elif len(val) == 1:
                                entry[key]=val[0]
                    if less is True:
                        pprint(entry)
                        input()
                    searches.append(entry)
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            sys.exit(1)

    if count is True:
        return counter
    else:   
        return searches

def user_search(
    attr=None,
    count=False,
    get_attrs=None,
    get_all_attrs=False,
    ldap_srv=None,
    member_of=[],
    search_values=[],
    show_filter=False,
    size_limit=None,
):
    
    if len(member_of) == 0:
        member_of=ldap_srv.default_groups
    pre_filter=ldap_srv.get_search_filter(groups=member_of)
    attr=attr.lower()

    dy_search=dict()
    with ldap_srv as conn:
        if get_all_attrs is True:
            return get_attributes(conn)

        counter=0
        for value in search_values:
            if attr in ["mail", "userprincipalname"]:
                if value[-len(ldap_srv.email_suffix):] != ldap_srv.email_suffix:
                    value="{}{}".format(value, ldap_srv.email_suffix)


            search_filter= pre_filter.format(elem="({}={})".format(attr, value))
            generator=ldap_srv.get_generator(show_filter, search_filter, get_attrs, size_limit)

            for entry in generator:
                if entry["type"] == "searchResEntry":
                    counter+=1
                    entry=dict(entry["attributes"])
                    if get_attrs is not None and len(get_attrs) == 0:
                        return sorted(entry)
                    for key, val in entry.items():
                        if isinstance(val, list):
                            if len(val) == 0:
                                entry[key]=None
                            elif len(val) == 1:
                                entry[key]=val[0]
                    if value not in dy_search:
                        dy_search[value]=[]
                    dy_search[value].append(entry)

    if count is True:
        return counter
    else:   
        return dy_search
