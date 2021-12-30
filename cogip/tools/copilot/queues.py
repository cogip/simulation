import asyncio


serial_messages_received: asyncio.Queue = None
"""Queue for messages received from serial port."""

serial_messages_to_send: asyncio.Queue = None
"""Queue for messages waiting to be sent on serial port."""

sio_messages_to_send: asyncio.Queue = None
"""Queue for messages waiting to be sent on SocketIO server."""
