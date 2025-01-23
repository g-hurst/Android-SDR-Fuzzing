# srsRAN Docker Container setup

This is an overview on how to setup srsRAN in a docker container for the project.

There is not much of a tutorial yet. For now... it is just a working collection of 
the notes that I (garrett) am taking while figuring some stuff out. 


A few useful commands have been created at the root our repo here in the Makefile. 
There are currently commands to 
* clone the srsRAN project 
* start docker will all the services for srsRAN

Docker appears to be set up to build several services:
* a open5GS 5gc container 
* a srsRAN gnb 
* a metrics server (not sure what the role of this is yet)
* influxdb (some sort of db, but not quite sure what this does)
* grafana (not sure what this is, but putting it here for completeness)
