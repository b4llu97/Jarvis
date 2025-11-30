import asyncio
import json
import logging
from typing import Optional, Callable, Any
import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """
    WebSocket handler for Home Assistant real-time updates.
    
    This handler connects to Home Assistant's WebSocket API and listens
    for state change events. Currently, events are logged for future use
    by the proactivity service.
    """
    
    def __init__(self, base_url: str, token: str):
        ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
        self.ws_url = f"{ws_url}/api/websocket"
        self.token = token
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.message_id = 0
        self.running = False
        self.event_callback: Optional[Callable[[dict], Any]] = None
        self._listen_task: Optional[asyncio.Task] = None
    
    def _get_next_id(self) -> int:
        """Get the next message ID for WebSocket communication"""
        self.message_id += 1
        return self.message_id
    
    async def connect(self) -> bool:
        """
        Connect to Home Assistant WebSocket API and authenticate.
        Returns True if connection and authentication successful.
        """
        try:
            self.websocket = await websockets.connect(self.ws_url)
            
            auth_required = await self.websocket.recv()
            auth_msg = json.loads(auth_required)
            
            if auth_msg.get("type") != "auth_required":
                logger.error(f"Unexpected message type: {auth_msg.get('type')}")
                return False
            
            await self.websocket.send(json.dumps({
                "type": "auth",
                "access_token": self.token
            }))
            
            auth_result = await self.websocket.recv()
            auth_result_msg = json.loads(auth_result)
            
            if auth_result_msg.get("type") == "auth_ok":
                logger.info("WebSocket authentication successful")
                self.running = True
                self._listen_task = asyncio.create_task(self._subscribe_and_listen())
                return True
            elif auth_result_msg.get("type") == "auth_invalid":
                logger.error("WebSocket authentication failed: Invalid token")
                return False
            else:
                logger.error(f"Unexpected auth result: {auth_result_msg}")
                return False
        
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            return False
    
    async def _subscribe_and_listen(self):
        """Subscribe to state change events and listen for updates"""
        if not self.websocket:
            return
        
        try:
            subscribe_msg = {
                "id": self._get_next_id(),
                "type": "subscribe_events",
                "event_type": "state_changed"
            }
            await self.websocket.send(json.dumps(subscribe_msg))
            
            while self.running:
                try:
                    message = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=30.0
                    )
                    data = json.loads(message)
                    await self._handle_message(data)
                
                except asyncio.TimeoutError:
                    continue
                except ConnectionClosed:
                    logger.warning("WebSocket connection closed")
                    break
        
        except Exception as e:
            logger.error(f"Error in WebSocket listener: {e}")
        
        finally:
            self.running = False
    
    async def _handle_message(self, data: dict):
        """Handle incoming WebSocket messages"""
        msg_type = data.get("type")
        
        if msg_type == "event":
            event = data.get("event", {})
            event_type = event.get("event_type")
            
            if event_type == "state_changed":
                event_data = event.get("data", {})
                entity_id = event_data.get("entity_id", "unknown")
                old_state = event_data.get("old_state", {})
                new_state = event_data.get("new_state", {})
                
                old_state_val = old_state.get("state", "unknown") if old_state else "unknown"
                new_state_val = new_state.get("state", "unknown") if new_state else "unknown"
                
                logger.info(
                    f"State changed: {entity_id} - {old_state_val} -> {new_state_val}"
                )
                
                if self.event_callback:
                    try:
                        await self.event_callback({
                            "entity_id": entity_id,
                            "old_state": old_state_val,
                            "new_state": new_state_val,
                            "attributes": new_state.get("attributes", {}) if new_state else {}
                        })
                    except Exception as e:
                        logger.error(f"Error in event callback: {e}")
        
        elif msg_type == "result":
            success = data.get("success", False)
            if not success:
                error = data.get("error", {})
                logger.warning(f"WebSocket command failed: {error}")
    
    def set_event_callback(self, callback: Callable[[dict], Any]):
        """Set a callback function to be called when state changes occur"""
        self.event_callback = callback
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        self.running = False
        
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        logger.info("WebSocket disconnected")
