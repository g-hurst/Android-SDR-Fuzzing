# uhd info


The installation for uhd can be found here

https://files.ettus.com/manual/page_install.html

Or, the command for the wsl install is: `sudo apt-get install libuhd-dev uhd-host`


A few helpful commands:
* `uhd_find_devices` lists the device that is connected to your machine.


If no device is found, you may need to change the ip of the ethernet adapter. The command to do this is

`sudo ifconfig <eth-device> 192.168.20.1`

For the lab devices, they are either on the ip `192.168.20.1` or `192.168.10.1`

When running this on wsl, make sure that the ethernet adapter for your computer is being picked up.
This will probaly require a bit of googling, but it should show up when you run `ifconfig`
