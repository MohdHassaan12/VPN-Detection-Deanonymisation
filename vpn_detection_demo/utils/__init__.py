# utils/__init__.py
from .device_detection import DeviceInfo, scan_local_devices, get_gateway_ip, get_local_ip, label_device

__all__ = ["DeviceInfo", "scan_local_devices", "get_gateway_ip", "get_local_ip", "label_device"]
