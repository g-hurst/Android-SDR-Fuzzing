WiFi Fuzzing Platform User Manual
=================================

Introduction
------------

The WiFi Fuzzing Platform is a tool designed for security researchers 
to test Android devices for potential WiFi vulnerabilities. 
This platform monitors device responses to network inputs, collects logs, 
and analyzes behavior.

Installation
------------

Prerequisites
~~~~~~~~~~~~~

- Linux operating system (or wsl2)
- Python 3.8 or higher  
- `Android Debug Bridge (adb) <https://developer.android.com/tools/adb>`_
- Android device with USB debugging enabled  
- USB cable for connecting the Android device  

Setup
~~~~~

Clone the repository:

.. code-block:: bash

    git clone https://github.com/g-hurst/Android-SDR-Fuzzing.git
    cd Android-SDR-Fuzzing

Install the python dependancies with:

.. code-block:: bash

    make setup

Enable USB debugging on your Android device:

- Settings → About phone → Tap "Build number" 7 times  
- Settings → Developer options → Enable "USB debugging"  
- Authorize your computer when prompted  

Running the Application
-----------------------
This application uses the ``scapy`` package and requires sudo privileges;
the -E flag runs with your current user environment.

Interactive Mode
~~~~~~~~~~~~~~~~
Interactive mode is the how the program is primarily intended to be run.
When in interactive mode, a cli is spawned that allows for commands to 
be run to interactivly monitor the current status of the fuzzer. 

.. code-block:: bash

    cd app
    sudo -E ./main.py --interactive

Without transmitter (for testing)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    cd app
    sudo -E ./main.py --interactive --skip-transmitter

Background Mode
~~~~~~~~~~~~~~~

.. code-block:: bash

    cd app
    sudo -E ./main.py

CLI Commands
------------
The CLI was written with the python ``cmd`` library. In addition to what is described 
below, the class for the commands can be found in the source code :ref:`cli.cli module`.

Android Device Commands
~~~~~~~~~~~~~~~~~~~~~~~
.. list-table::
   :widths: 25 25 50
   :header-rows: 1

   * - Command
     - Description
     - Example
   * - adb <command>
     - Execute ADB command
     - adb shell ls /sdcard
   * - get_ip
     - Show device IP address
     - get_ip
   * - device_info
     - Show device information
     - device_info
   * - wifi_info
     - Show WiFi information
     - wifi_info
   * - network_status
     - Show connectivity info
     - network_status

Logging Commands
~~~~~~~~~~~~~~~~

.. list-table:: 
   :widths: 25 25 50
   :header-rows: 1

   * - Command
     - Description
     - Example
   * - logs
     - Show device logs
     - logs
   * - logs clear
     - Clear log buffer
     - logs clear
   * - logs filter <tag>
     - Filter logs by tag
     - logs filter E

General Commands
~~~~~~~~~~~~~~~~

.. list-table:: 
   :widths: 25 25 50
   :header-rows: 1

   * - Command
     - Description
     - Example
   * - help
     - List all commands
     - help
   * - help <command>
     - Show command help
     - help get_ip
   * - exit or quit
     - Exit the CLI
     - exit

Troubleshooting
---------------

No Device Connected
~~~~~~~~~~~~~~~~~~~

If no device is connected, you'll see messages like:

.. code-block:: text

    "Could not retrieve device IP address"
    "Error: Target Monitor not available"

USB Connection Issues
~~~~~~~~~~~~~~~~~~~~~

If you can't connect to your device:

- Ensure USB debugging is enabled  
- Try a different USB cable  
- Run ``adb kill-server`` (on both host and wsl if running on wsl) to kill any instances of adb that could be preventing a new connection. 
- Run ``adb devices`` to verify connection  

Network Interface Issues
~~~~~~~~~~~~~~~~~~~~~~~~

If the transmitter fails with "No such device" error:

- Use ``--skip-transmitter`` flag  
- Check network configuration  
- Verify Scapy installation  

Source Code
-----------

`https://github.com/g-hurst/Android-SDR-Fuzzing <https://github.com/g-hurst/Android-SDR-Fuzzing>`_
