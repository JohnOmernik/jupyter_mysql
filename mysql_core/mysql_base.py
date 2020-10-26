#!/usr/bin/python

# Base imports for all integrations, only remove these at your own risk!
import json
import sys
import os
import time
import pandas as pd
from collections import OrderedDict

from integration_core import Integration

from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic, line_cell_magic)
from IPython.core.display import HTML

# Your Specific integration imports go here, make sure they are in requirements!

import pymysql

#import IPython.display
from IPython.display import display_html, display, Javascript, FileLink, FileLinks, Image
import ipywidgets as widgets

@magics_class
class Mysql(Integration):
    # Static Variables
    # The name of the integration
    name_str = "mysql"
    instances = {} 
    custom_evars = ['mysql_conn_default']
    # These are the variables in the opts dict that allowed to be set by the user. These are specific to this custom integration and are joined
    # with the base_allowed_set_opts from the integration base
    custom_allowed_set_opts = ['mysql_conn_default']

    myopts = {} 
    myopts['mysql_conn_default'] = ['default', 'Default instance name to use for connections']

    # Class Init function - Obtain a reference to the get_ipython()
    def __init__(self, shell, pd_display_grid="html", mysql_conn_url_default="", debug=False, *args, **kwargs):
        super(Mysql, self).__init__(shell, debug=debug, pd_display_grid=pd_display_grid)
        self.debug = debug

        self.opts['pd_display_grid'][0] = pd_display_grid
        if pd_display_grid == "qgrid":
            try:
                import qgrid
            except:
                print ("WARNING - QGRID SUPPORT FAILED - defaulting to html")
                self.opts['pd_display_grid'][0] = "html"

        #Add local variables to opts dict
        for k in self.myopts.keys():
            self.opts[k] = self.myopts[k]

        self.load_env(self.custom_evars)
        if mysql_conn_url_default != "":
            if "default" in self.instances.keys():
                print("Warning: default instance in ENV and passed to class creation - overwriting ENV")
            self.fill_instance("default", mysql_conn_url_default)
                
        self.parse_instances()


    # We use a custom disconnect in pyodbc so we try to close the connection before nuking it
    def customDisconnect(self, instance):
        try:
            self.instances[instance]['connection'].close()
        except:
            pass
        self.instances[instance]['connection'] = None
        self.instances[instance]['session'] = None
        self.instances[instance]['connected'] = False
        #self.instances[instance]['connect_pass'] = None # Should we clear the password when we disconnect? I am going to change this to no for now 


    def req_password(self, instance):
        opts = None
        retval = True
        try:
            opts = self.instances[instance]['options']
        except:
            print("Instance %s options not found" % instance)
        try:
            if opts['use_integrated_security'] == 1:
                retval = False
        except:
            pass
        return retval

    def customAuth(self, instance):
        result = -1
        inst = None
        if instance not in self.instances.keys():
            result = -3
            print("Instance %s not found in instances - Connection Failed" % instance)
        else:
            inst = self.instances[instance]
        # Defaults

        pymysql_def_opts = { "database": None, "unix_socket": None, "charset":'', "sql_mode": None, "read_default_file": None, "conv": None, "use_unicode": None, 
                     "client_flag": 0, "init_command": None, "connect_timeout": 10, "ssl": None,  "read_default_group": None, "compress": None, "named_pipe": None,
                     "autocommit": False, "db": None,  "local_infile": False, "max_allowed_packet": 16777216, "defer_connect": False, "auth_plugin_map": None, 
                     "read_timeout": None, "write_timeout": None, "bind_address": None, "binary_prefix": False, "program_name": None, "server_public_key": None}

        if inst is not None:
            # Get Password, else, get the default connections pass 
            mypass = ""
            if inst['connect_pass'] is not None:
                mypass = inst['connect_pass']
            else:
                mypass = self.instances[self.opts[self.name_str + "_conn_default"][0]]['connect_pass']


            # ALlow any set options
            topts = {}


            # Since we pass the defaults explicitly, basically, if we have the option in our connect string use it, or use the default
            for k in pymysql_def_opts.keys():
                if k in inst['options']:
                    topts[k] = inst['options'][k]
                else:
                    topts[k] = pymysql_def_opts[k]

            try:
                inst['connection'] = pymysql.connect(
                                        user=inst['user'], password=mypass, host=inst['host'], port=inst['port'], 
                                        database=topts['database'], unix_socket=topts['unix_socket'], charset=topts['charset'], sql_mode=topts['sql_mode'],
                                        read_default_file=topts['read_default_file'], conv=topts['conv'], use_unicode=topts['use_unicode'], client_flag=topts['client_flag'],
                                        init_command=topts['init_command'], connect_timeout=topts['connect_timeout'], ssl=topts['ssl'], read_default_group=topts['read_default_group'],
                                        compress=topts['compress'], named_pipe=topts['named_pipe'], autocommit=topts['autocommit'], db=topts['db'], 
                                        local_infile=topts['local_infile'], max_allowed_packet=topts['max_allowed_packet'], defer_connect=topts['defer_connect'], 
                                        auth_plugin_map=topts['auth_plugin_map'], read_timeout=topts['read_timeout'], write_timeout=topts['write_timeout'], 
                                        bind_address=topts['bind_address'], binary_prefix=topts['binary_prefix'], program_name=topts['program_name'], server_public_key=topts['server_public_key']
                                      )
#                inst['session'] = inst['connection'].cursor()
                result = 0
            except Exception as e:
                # MySQL Errors go here
                print("Unable to connect to Mysql instance %s at %s\n Exception:%s" % (instance, inst["conn_url"], str(e)))
                result = -2

        return result

    def validateQuery(self, query, instance):

        bRun = True
        bReRun = False
        if self.instances[instance]['last_query'] == query:
            # If the validation allows rerun, that we are here:
            bReRun = True
        # Ok, we know if we are rerun or not, so let's now set the last_query (and last use if needed) 
        self.instances[instance]['last_query'] = query
        if query.strip().find("use ") == 0:
            self.instances[instance]['last_use'] = query


        # Example Validation

        # Warn only - Don't change bRun
        # This one is looking for a ; in the query. We let it run, but we warn the user
        # Basically, we print a warning but don't change the bRun variable and the bReRun doesn't matter
        if query.find(";") >= 0:
            print("WARNING - Do not type a trailing semi colon on queries, your query will fail (like it probably did here)")

        # Warn and don't submit after first attempt - Second attempt go ahead and run
        # If the query doesn't have a day query, then maybe we want to WARN the user and not run the query.
        # However, if this is the second time in a row that the user has submitted the query, then they must want to run without day
        # So if bReRun is True, we allow bRun to stay true. This ensures the user to submit after warnings
        if query.lower().find("limit ") < 0:
            print("WARNING - Queries shoud have a limit so you don't bonkers your DOM")
        # Warn and do not allow submission
        # There is no way for a user to submit this query 
#        if query.lower().find('limit ") < 0:
#            print("ERROR - All queries must have a limit clause - Query will not submit without out")
#            bRun = False
        return bRun

    def customQuery(self, query, instance):

        mydf = None
        status = ""
        try:
            mydf = pd.read_sql(query, self.instances[instance]['session'])
            if len(mydf) == 0: # For queries that could have results, but don't (select * from table, but table is empty)
                mydf = "None"
                status = "Success - No Results"
            else:
                status = "Success"
        except TypeError:  # For queries like "use database" that never return results
            mydf = None
            status = "Success - No Results"
        except Exception as e:
            mydf = None
            str_err = str(e)
            if self.debug:
                print("Error: %s" % str(e))
            status = "Failure - query_error: " + str_err
        return mydf, status

# Display Help can be customized
    def customHelp(self):
        self.displayIntegrationHelp()
        self.displayQueryHelp("select * from `mydatabase`.`mytable`")


    # This is the magic name.
    @line_cell_magic
    def mysql(self, line, cell=None):
        if cell is None:
            line = line.replace("\r", "")
            line_handled = self.handleLine(line)
            if self.debug:
                print("line: %s" % line)
                print("cell: %s" % cell)
            if not line_handled: # We based on this we can do custom things for integrations. 
                print("I am sorry, I don't know what you want to do with your line magic, try just %" + self.name_str + " for help options")
        else: # This is run is the cell is not none, thus it's a cell to process  - For us, that means a query
            self.handleCell(cell, line)

