---
layout: default
title: Command Line Interface (CLI)
nav_order: 8
---

## Install CLI

You can install the CLI dependencies using the below command

```
pip install 'sqlite-rx[cli]'
```

## sqlite-server




`sqlite-server` is a console script to start an SQLiteServer.

```text

sqlite-server   🐾                                                                                    

A simple, fast and secure server for the SQLite database.                                                                

Usage: sqlite-server [OPTIONS]                                                                                                                                                           

                                                                                                
 -l, --log-level LOG_LEVEL             CRITICAL FATAL ERROR WARN WARNING INFO DEBUG NOTSET      
                                       Default value is INFO                                    
                                                                                                
 -a, --tcp-address tcp://<host>:<port> The host and port on which to listen for TCP connections 
                                       Default value is tcp://0.0.0.0:5000                      
                                                                                                
 -d --database PATH                    Path to the database                                     
                                       You can use :memory: for an in-memory database           
                                       Default value is :memory:                                
                                                                                                
 --zap/--no-zap                        Enable/Disable ZAP Authentication                        
                                       Default value is False                                   
                                                                                                
 --curvezmq/--no-curvezmq              Enable/Disable CurveZMQ                                  
                                       Default value is False                                   
                                                                                                
 -c --curve-dir PATH                   Path to the Curve key directory                          
                                       Default value is ~/.curve                                
                                                                                                
 -k --key-id CURVE KEY ID              Server's Curve Key ID                                    
                                                                                                
 -b --backup-database PATH             Path to the backup database                              
                                                                                                
 -i --backup-interval FLOAT            Backup interval in seconds                               
                                                                                                
 --help                                Show this message and exit.                              
```

All docker examples use this console script as an entrypoint

## sqlite-client

```text
Usage: sqlite-client [OPTIONS] exec <query>                                                                                                                                              

                                                                                               
 -l, --log-level LOG_LEVEL                 CRITICAL FATAL ERROR WARN WARNING INFO DEBUG NOTSET 
                                           Default level is CRITICAL                           
                                                                                               
 -a, --connect-address tcp://<host>:<port> The host and port on which to connect               
                                           Default value is tcp://0.0.0.0:5000                 
                                                                                               
 --zap/--no-zap                            Enable/Disable ZAP Authentication                   
                                           Default value is False                              
                                                                                               
 --curvezmq/--no-curvezmq                  Enable/Disable CurveZMQ                             
                                           Default value is False                              
                                                                                               
 -d --curve-dir PATH                       Path to the Curve key directory                     
                                           Default value is ~/.curve                           
                                                                                               
 -c --client-key-id CURVE KEY ID           Client's Curve Key ID                               
                                                                                               
 --help                                    Show this message and exit.                         
                                                                       
```
