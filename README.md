# jupyter_mysql
A module to help interaction with Jupyter Notebooks and MySQL

------
This is a python module that helps to connect Jupyter Notebooks to various datasets. 
It's based on (and requires) https://github.com/JohnOmernik/jupyter_integration_base 


## Initialization 
----
After installing this, to instantiate the module so you can use %mysql and %%mysql put this in a cell:

the Mysql() init can take the following arguments, or they can be left off to use these defaults

debug=False, pd_display_grid="html", mysql_conn_url_default=""

- debug
  - Turns on addition logging
- pd_display_grid
  - html - Use standard html display in data frames (default)
  - qgrid - Use qgrid (https://github.com/quantopian/qgrid v. 1.3 or higher) Recommended 
- mysql_conn_url_default
  - Can set the default connection url at instantiation (Can only set the one instance, use ENV variables for multiple instances)



### Example Inits

#### Debug false, using qgrid, no connection URL specified
```
ipy = get_ipython()

from mysql_core import Mysql
Mysql = Mysql(ipy, debug=False, pd_display_grid="qgrid")
ipy.register_magics(Mysql)
```


## Instance Usage
--------
You can use multiple instances of Drill with the same magic function.  You do this by specifying instances in the ENV variables (see ENV Variables below).  Multiple functions can use the instances, connect, disconnect and queries. 

In addition, you can look and see instance information by typing %mysql instances

One more thing: If you are connecting to an instance that requires a password, and you have ALREADY set a password on the default instance, it WILL attempt to connect with the default instance password.  In many installations, the password is the same. 

If you wish to set a different password for a non-default instance, you have two options:

### Option one connect alt
```
%mysql connect myinstance alt
```
This will ask for the connection URL, and password for an instance. If you dont' want to type the connection url every time, try:


### Option two setpass
```
%mysql setpass myinstance
```
This will set the password for my instance, but DOES NOT connect to it. After you have set the password then type

```
%mysql connect myinstance
```
And this will use the instance set password. 


Normally, if you provide a magic line function like

```
%mysql connect
```

It will automatically default to the instance specified in the JUPYTER_DRILL_CONN_DEFAULT Env Variable. If you want to use a specific instance, you can use:

```
%mysql connect myinstance
```
And it will utilize that instance. 

In addition for queries, the same applies, if you do not specify an instance name, the query will be submitted to the JUPYTER_MYSQL_CONN_DEFAULT Env Variable value

```
%%mysql
select * from sys.options
```

However, if you wish to specify an instance name you can use:

```
%%mysql myinstance
select * from sys.options
```

## ENV Variables
--------
To allow multiple instances, mysql lets you specify two main ENV variables:
  - JUPTYER_MYSQL_CONN_URL_X - The connection URL for the instance x
    - Note in the ENV variable, you ucase the instance name (X) in the JUPYTER_MYSQL_CONN_URL_ variable
    - However, it is referenced both in the magics and in the default ENV as lcase (x)
  - JUPYTER_MYSQL_CONN_DEFAULT - This (not the lack of URL) is the DEFAULT connection instance that Mysql will use. 


### URL Format
```
scheme://user@host:port?option1=option1val&option2=option2val&option3=option3val
```

For mysql here are the items to consider:
- scheme
  - This is ignored, just put mysql
- user
  - This is the username to connect with.
- host
  - Hostname to connect with.
  - Default (and embedded mode host) should be localhost
- port
  - Port to connect with
  - Default (and embedded mode) is 3306
- Options
  - after the ? options are k=v pairs sep by &


### Example ENVs when starting Jupyter Lab
---- 
``` 
export JUPYTER_MYSQL_CONN_URL_DEFAULT="http://mysql@ localhost:3306" 
export JUPYTER_MYSQL_CONN_DEFAULT="default"
```

This creates a default instance, uses embedded mode, and sets the default instance to the instance name of "default"

