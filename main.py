#!/usr/bin/env python3

if __name__ == "__main__":
    from pprint import pprint
    import importlib
    import json
    import os
    import sys
    direpa_script=os.path.dirname(os.path.realpath(__file__))
    direpa_script_parent=os.path.dirname(direpa_script)
    module_name=os.path.basename(direpa_script)
    sys.path.insert(0, direpa_script_parent)
    pkg = importlib.import_module(module_name)
    del sys.path[0]

    def seed(pkg_major, direpas_configuration=dict(), fun_auto_migrate=None):
        fun_auto_migrate()
    etconf=pkg.Etconf(enable_dev_conf=False, tree=dict( files=dict({ "settings.json": dict() })), seed=seed)
    args, dy_app=pkg.Options(
        direpa_configuration=etconf.direpa_configuration,
        examples="""
            main.py --user-search tom.garza --attr mail --get-attrs mail --show-filter
            main.py --user-search *garza* --attr mail --get-attrs mail --show-filter --size-limit 10

            main.py --raw-search "(&(&(objectCategory=person)(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2))(mail=tom.garza@university.edu))(|(memberOf=CN=university-faculty,OU=Groups,DC=ad,DC=university,DC=edu)(memberOf=CN=university-staff,OU=Groups,DC=ad,DC=university,DC=edu)(memberOf=CN=university-students,OU=Groups,DC=ad,DC=university,DC=edu)))" --get-attrs mail --show-filter

            main.py --raw-search "(&(&(objectCategory=person)(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))(|(memberOf=CN=university-faculty,OU=Groups,DC=ad,DC=university,DC=edu)))" --get-attrs mail --show-filter --count
            main.py --raw-search "(&(&(objectCategory=person)(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))(|(memberOf=CN=university-faculty,OU=Groups,DC=ad,DC=university,DC=edu)))" --get-attrs mail --show-filter --size-limit 10
        """, 
        filenpa_app="gpm.json", 
        filenpa_args="config/options.json"
    ).get_argsns_dy_app()

    if args.user_search.here or args.raw_search.here:
        get_attrs=None
        if args.get_attrs.here:
            get_attrs=args.get_attrs.values
    
        dy_conf=dict()
        filenpa_conf=os.path.join(etconf.direpa_configuration, "settings.json")
        with open(filenpa_conf, "r") as f:
            dy_conf=json.load(f)

        ldap_srv=pkg.LdapServer(
            account=dy_conf["account"],
            dc=dy_conf["dc"],
            default_groups=dy_conf["groups"],
            domain=dy_conf["domain"],
            email_suffix=dy_conf["email_suffix"],
            password=dy_conf["password"],
        )

        if args.user_search.here:
            pprint(pkg.user_search(
                attr=args.attr.value,
                count=args.count.here,
                get_attrs=get_attrs,
                get_all_attrs=args.get_all_attrs.here,
                ldap_srv=ldap_srv,
                member_of=args.member_of.values,
                search_values=args.user_search.values,
                show_filter=args.show_filter.here,
                size_limit=args.size_limit.value,
            ))

        elif args.raw_search.here:
            pprint(pkg.raw_search(
                count=args.count.here,
                get_attrs=get_attrs,
                ldap_srv=ldap_srv,
                less=args.less.here,
                search_filter=args.raw_search.value,
                show_filter=args.show_filter.here,
                size_limit=args.size_limit.value,
            ))