"""Wearable biometric device connection manager.

Supports BLE (Bluetooth Low Energy) devices like Polar H10, Garmin,
and Apple Watch via the bleak library. Manages device discovery,
connection lifecycle, and data streaming.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class BiometricReading:
    """Single biometric data point from a wearable device."""

    heart_rate_bpm: Optional[float] = None
    hrv_rmssd: Optional[float] = None  # Heart Rate Variability
    hrv_sdnn: Optional[float] = None
    eda: Optional[float] = None  # Electrodermal activity (skin conductance)
    timestamp: datetime = field(default_factory=datetime.now)
    device_name: str = "unknown"
    battery_level: Optional[int] = None


@dataclass
class WearableDevice:
    """Represents a discovered wearable device."""

    name: str
    address: str
    device_type: str  # "polar", "garmin", "apple_watch", "generic_ble"
    rssi: int = 0


class WearableConnectionError(Exception):
    """Raised when wearable connection fails."""


class WearableManager:
    """Manages BLE wearable device discovery, connection, and data streaming.

    Uses bleak for BLE communication. In development mode (no BLE hardware),
    returns synthetic biometric data for testing.
    """

    def __init__(self, use_dummy: bool = True):
        self.use_dummy = use_dummy
        self._connected_device: Optional[WearableDevice] = None
        self._client: Optional[object] = None
        self._running = False
        self._on_reading: Optional[Callable[[BiometricReading], None]] = None
        self._watchdog_task: Optional[asyncio.Task] = None

    async def discover(self, timeout: float = 5.0) -> list[WearableDevice]:
        """Discover nearby BLE wearable devices."""
        if self.use_dummy:
            logger.info("Dummy mode: returning mock wearable devices")
            return [
                WearableDevice(name="Polar H10 (sim)", address="00:AA:BB:CC:DD:01", device_type="polar", rssi=-45),
                WearableDevice(name="Apple Watch (sim)", address="00:AA:BB:CC:DD:02", device_type="apple_watch", rssi=-60),
            ]

        try:
            from bleak import BleakScanner
            logger.info("Scanning for BLE devices...")
            devices = await BleakScanner.discover(timeout=timeout)
            wearables = []
            for d in devices:
                name = d.name or "Unknown"
                # Filter for likely wearable devices by name pattern
                if any(kw in name.lower() for kw in ["polar", "garmin", "apple", "fitbit", "hr", "heart"]):
                    wearables.append(
                        WearableDevice(name=name, address=d.address, device_type=self._classify(name), rssi=d.rssi or 0)
                    )
            logger.info(f"Found {len(wearables)} wearable(s)")
            return wearables
        except ImportError:
            logger.warning("bleak not installed — falling back to dummy wearables")
            return [
                WearableDevice(name="Polar H10 (sim)", address="sim_1", device_type="polar", rssi=-45),
            ]
        except Exception as e:
            logger.warning(f"BLE scan failed: {e}")
            return []

    def _classify(self, name: str) -> str:
        nl = name.lower()
        if "polar" in nl:
            return "polar"
        if "garmin" in nl:
            return "garmin"
        if "apple" in nl:
            return "apple_watch"
        if "fitbit" in nl:
            return "fitbit"
        return "generic_ble"

    async def connect(self, device: WearableDevice) -> bool:
        """Connect to a specific wearable device."""
        if self.use_dummy:
            self._connected_device = device
            logger.info(f"Dummy connected to {device.name}")
            return True

        try:
            from bleak import BleakClient
            self._client = BleakClient(device.address)
            await self._client.connect()
            self._connected_device = device
            logger.info(f"Connected to {device.name} ({device.address})")
            return True
        except Exception as e:
            raise WearableConnectionError(f"Failed to connect to {device.name}: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from the current device."""
        if self._running:
            self._running = False
            if self._watchdog_task:
                self._watchdog_task.cancel()
                self._watchdog_task = None

        if self._client and not self.use_dummy:
            try:
                await self._client.disconnect()
            except Exception:
                pass

        if self._connected_device:
            logger.info(f"Disconnected from {self._connected_device.name}")
        self._connected_device = None
        self._client = None

    async def start_streaming(self, on_reading: Callable[[BiometricReading], None]) -> None:
        """Start streaming biometric data at ~1Hz.

        In dummy mode, generates synthetic but plausible biometric readings.
        In real mode, reads HR/HRV characteristics from the connected BLE device.
        """
        self._on_reading = on_reading
        self._running = True

        if self.use_dummy:
            self._watchdog_task = asyncio.create_task(self._dummy_stream())
        else:
            self._watchdog_task = asyncio.create_task(self._ble_stream())

    async def _dummy_stream(self) -> None:
        """Generate synthetic biometric data for development."""
        import random as rng
        while self._running:
            reading = BiometricReading(
                heart_rate_bpm=round(rng.uniform(60, 100), 1),
                hrv_rmssd=round(rng.uniform(20, 70), 1),
                hrv_sdnn=round(rng.uniform(30, 90), 1),
                eda=round(rng.uniform(0.5, 5.0), 2),
                device_name=self._connected_device.name if self._connected_device else "dummy",
                battery_level=rng.choice([60, 70, 80, 90, 100]),
            )
            if self._on_reading:
                self._on_reading(reading)
            await asyncio.sleep(1.0)

    async def _ble_stream(self) -> None:
        """Stream real biometric data from a BLE device."""
        if not self._client:
            logger.warning("No BLE client connected")
            return

        HR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"  # Standard HR measurement
        try:
            while self._running and self._client.is_connected:
                raw = await self._client.read_gatt_char(HR_UUID)
                bpm = int.from_bytes(raw[1:2], byteorder="little") if len(raw) > 1 else 0
                reading = BiometricReading(
                    heart_rate_bpm=float(bpm),
                    device_name=self._connected_device.name if self._connected_device else "ble",
                )
                if self._on_reading:
                    self._on_reading(reading)
                await asyncio.sleep(1.0)
        except Exception as e:
            logger.error(f"BLE stream error: {e}")
            self._running = False

    @property
    def is_connected(self) -> bool:
        return self._connected_device is not None

    @property
    def device_name(self) -> str:
        return self._connected_device.name if self._connected_device else "none"
