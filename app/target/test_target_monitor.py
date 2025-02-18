import os
import threading
import pytest
from unittest import mock
from unittest.mock import patch, MagicMock
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb_shell.adb_device import AdbDeviceUsb
from target_monitor import Target_Monitor  # Assuming the class is in target_monitor.py

@pytest.fixture
def target_monitor():
    return Target_Monitor()

@patch("adb_shell.adb_device.AdbDeviceUsb.connect")
@patch("target_monitor.Target_Monitor.get_adb_signer")
def test_adb_connect(mock_get_signer, mock_connect, target_monitor):
    mock_get_signer.return_value = MagicMock(spec=PythonRSASigner)
    target_monitor.device = MagicMock(spec=AdbDeviceUsb)
    
    target_monitor.adb_connect()
    
    mock_get_signer.assert_called_once()
    target_monitor.device.connect.assert_called_once_with(rsa_keys=[mock_get_signer.return_value], auth_timeout_s=15.0)

@patch("adb_shell.adb_device.AdbDeviceUsb.shell", return_value="mock_output")
def test_adb_exec(mock_shell, target_monitor):
    target_monitor.device = MagicMock(spec=AdbDeviceUsb)
    target_monitor.device.shell.return_value = "mock_output"
    
    output = target_monitor.adb_exec("ls")
    
    target_monitor.device.shell.assert_called_once_with("ls")
    assert output == "mock_output"

@patch("adb_shell.adb_device.AdbDeviceUsb.connect", side_effect=Exception("Connection failed"))
def test_run_connection_failure(mock_connect, target_monitor):
    with patch("builtins.print") as mock_print:
        target_monitor.run()
    
    mock_print.assert_any_call("Target_Monitor: Failed to connect to Android Device")

@patch("threading.Event.clear")
def test_kill(mock_clear, target_monitor):
    target_monitor.kill()
    mock_clear.assert_called_once()

