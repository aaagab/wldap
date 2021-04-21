#!/usr/bin/env python3
from pprint import pprint
import json
import os
import re
import sys

import ldap3
from ldap3 import Server, Connection, SAFE_SYNC, ALL, NTLM, SUBTREE, ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES, ObjectDef, Reader

from ..gpkgs import message as msg

def get_search_filter(dy_conf):
    search_filter="""
        (&
            (&
                (objectCategory=person)
                (objectClass=user)
                # UserAccountControl will only Include Non-Disabled Users.
                (!(userAccountControl:1.2.840.113556.1.4.803:=2))
                #  (cn=cn)
                # (userPrincipalName=email)
                {{elem}}
            )
            {groups}
        )
    """

    groups=""
    # if len(dy_conf["groups"]) > 0:
    #     groups+="(|"
    #     for group in dy_conf["groups"]:
    #         groups+="(memberOf=CN={},OU=Groups,{})".format(group, dy_conf["dc"])
    #     groups+=")"

    search_filter=search_filter.format(groups=groups)

    tmp_text=""
    for line in search_filter.splitlines():
        line=line.strip()
        if len(line) > 0:
            if line[0] != "#":
                tmp_text+=line

    return tmp_text

def get_search_filter_email(search_filter, email):
    return search_filter.format(elem="(userPrincipalName={})".format(email))

def get_search_filter_cn(search_filter, cn):
    return search_filter.format(elem="(cn={})".format(cn))

def get_attributes(conn):
    person = ObjectDef(['person', 'user'], conn)
    values=[]
    for line in repr(person).splitlines():
        reg=re.match(r"^(?P<key>[A-Z]+)\s*?:\s+(?P<values>.+)$", line.strip())
        if reg.group("key") in ["MUST", "MAY"]:
            values.extend(reg.group("values").split(", "))
    values=list(set(values))
    return values

def search(
    attrs=[],
    cns=[],
    emails=[],
    filenpa_conf=None,
    get_attrs=False,
    get_all_attrs=False,
):
    dy_conf=dict()
    with open(filenpa_conf, "r") as f:
        dy_conf=json.load(f)

    search_filter=get_search_filter(dy_conf)

    dy_search=dict()
    server = Server(dy_conf["domain"], port=636, use_ssl=True, get_info=ALL)
    with Connection(server, dy_conf["account"], dy_conf["password"], auto_bind=True) as conn:
        if get_all_attrs is True:
            return get_attributes(conn)

        for filter_type in ["cns", "emails"]:
            values=[]
            if filter_type == "cns":
                values=cns
            elif filter_type == "emails":
                values=emails

            for value in values:
                elem_search_filter=None
                if filter_type == "cns":
                    elem_search_filter=get_search_filter_cn(search_filter, value)
                elif filter_type == "emails":
                    if value[-len(dy_conf["email_suffix"]):] != dy_conf["email_suffix"]:
                        value="{}{}".format(value, dy_conf["email_suffix"])
                    elem_search_filter=get_search_filter_email(search_filter, value)
                
                if len(attrs) == 0 or get_attrs is True:
                    attrs=ALL_ATTRIBUTES
                try:
                    conn.search(dy_conf["dc"], elem_search_filter, attributes=attrs)
                except ldap3.core.exceptions.LDAPAttributeError as e:

                    conn.search(dy_conf["dc"], elem_search_filter, attributes=ALL_ATTRIBUTES)
                    msg.error(str(e))
                    if len(conn.entries) == 1:
                        entry=json.loads(conn.entries[0].entry_to_json())["attributes"]
                        print("Authorized attributes are:")
                        pprint(sorted(entry))
                    sys.exit(1)

                if len(conn.entries) == 1:
                    entry=json.loads(conn.entries[0].entry_to_json())["attributes"]
                    if get_attrs is True:
                        return sorted(entry)
                    for key, val in entry.items():
                        if isinstance(val, list):
                            if len(val) == 0:
                                entry[key]=None
                            elif len(val) == 1:
                                entry[key]=val[0]
                    dy_search[value]=entry
                elif len(conn.entries) > 1:
                    msg.error("There are '{}' entries not 1".format(len(conn.entries)), exit=1)
                        
    return dy_search
