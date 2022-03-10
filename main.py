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
    args=pkg.Nargs(
        options_file="config/options.yaml", 
        path_etc=etconf.direpa_configuration,
    ).get_args()

    if args.search._here:

        get_attrs=None
        if args.search.get_attrs._here:
            get_attrs=args.search.get_attrs._values
    
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

        results=[]
        if args.search.user._here:
            results=pkg.user_search(
                attr=args.search.user.attr._value,
                count=args.search.count._here,
                get_attrs=get_attrs,
                get_all_attrs=args.search.user.get_all_attrs._here,
                ldap_srv=ldap_srv,
                member_of=args.search.user.member_of._values,
                search_values=args.search.user._values,
                show_filter=args.search.show_filter._here,
                size_limit=args.search.size_limit._value,
            )

        elif args.search.raw._here:
            results=pkg.raw_search(
                count=args.search.count._here,
                get_attrs=get_attrs,
                ldap_srv=ldap_srv,
                less=args.search.raw.less._here,
                search_filter=args.search.raw._value,
                show_filter=args.search.show_filter._here,
                size_limit=args.search.size_limit._value,
            )
        else:
            print("Error command-line either --user or --raw is needed")
            sys.exit(1)


        results=json.dumps(results, indent=4, sort_keys=True)
        if args.search.to_file._here:
            with open(args.search.to_file._value, "w", encoding="utf-8") as f:
                f.write("{}".format(results))
        else:
            print(results)
