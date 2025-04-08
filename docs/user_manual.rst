WiFi Fuzzing Platform User Manual
=================================

Introduction
------------

The WiFi Fuzzing Platform is a tool designed for security researchers to test Android devices for potential WiFi vulnerabilities. This platform monitors device responses to network inputs, collects logs, and analyzes behavior.

Installation
------------

Prerequisites
~~~~~~~~~~~~~

- Linux operating system  
- Python 3.8 or higher  
- Android device with USB debugging enabled  
- USB cable for connecting the Android device  

Required Python Packages
~~~~~~~~~~~~~~~~~~~~~~~~

Install the following packages:

.. code-block:: bash

    apt install python3-pip
    pip install adb-shell[usb]
    pip install scapy

Setup
~~~~~

Clone the repository:

.. code-block:: bash

    git clone https://github.com/g-hurst/Android-SDR-Fuzzing.git
    cd Android-SDR-Fuzzing

Enable USB debugging on your Android device:

- Settings → About phone → Tap "Build number" 7 times  
- Settings → Developer options → Enable "USB debugging"  
- Authorize your computer when prompted  

Running the Application
-----------------------

Interactive Mode
~~~~~~~~~~~~~~~~

.. code-block:: bash

    cd app
    python3 main.py --interactive

Without transmitter (for testing):

.. code-block:: bash

    python3 main.py --interactive --skip-transmitter

Background Mode
~~~~~~~~~~~~~~~

.. code-block:: bash

    cd app
    python3 main.py

CLI Commands
------------

Android Device Commands
~~~~~~~~~~~~~~~~~~~~~~~

+------------------+-----------------------------+----------------------------+
| Command          | Description                 | Example                    |
+==================+=============================+============================+
| adb <command>    | Execute ADB command         | adb shell ls /sdcard       |
| get_ip           | Show device IP address      | get_ip                     |
| device_info      | Show device information     | device_info                |
| wifi_info        | Show WiFi information       | wifi_info                  |
| network_status   | Show connectivity info      | network_status             |
+------------------+-----------------------------+----------------------------+

Logging Commands
~~~~~~~~~~~~~~~~

+----------------------+-----------------------------+--------------------------+
| Command              | Description                 | Example                  |
+======================+=============================+==========================+
| logs                 | Show device logs            | logs                     |
| logs clear           | Clear log buffer            | logs clear               |
| logs filter <tag>    | Filter logs by tag          | logs filter E            |
+----------------------+-----------------------------+--------------------------+

General Commands
~~~~~~~~~~~~~~~~

+-------------------------+--------------------------+--------------------------+
| Command                 | Description              | Example                  |
+=========================+==========================+==========================+
| help                    | List all commands        | help                     |
| help <command>          | Show command help        | help get_ip              |
| exit or quit            | Exit the CLI             | exit                     |
+-------------------------+--------------------------+--------------------------+

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
- Check device authorization  
- Run ``adb devices`` to verify connection  

Network Interface Issues
~~~~~~~~~~~~~~~~~~~~~~~~

If the transmitter fails with "No such device" error:

- Use ``--skip-transmitter`` flag  
- Check network configuration  
- Verify Scapy installation  

Support
-------

For issues or questions, visit:

`https://github.com/g-hurst/Android-SDR-Fuzzing <https://github.com/g-hurst/Android-SDR-Fuzzing
