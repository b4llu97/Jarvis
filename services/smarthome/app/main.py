from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import logging

from home_assistant import HomeAssistantClient
from websocket_handler import WebSocketHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Jarvis Smart Home Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HOME_ASSISTANT_URL = os.getenv("HOME_ASSISTANT_URL", "http://homeassistant.local:8123")
HOME_ASSISTANT_TOKEN = os.getenv("HOME_ASSISTANT_TOKEN", "")

ha_client = HomeAssistantClient(HOME_ASSISTANT_URL, HOME_ASSISTANT_TOKEN)
ws_handler: Optional[WebSocketHandler] = None


class EntityActionRequest(BaseModel):
    entity_id: str


class ServiceCallRequest(BaseModel):
    entity_id: str
    data: Optional[Dict[str, Any]] = None


class EntityResponse(BaseModel):
    entity_id: str
    state: str
    friendly_name: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    last_changed: Optional[str] = None
    last_updated: Optional[str] = None


class ActionResponse(BaseModel):
    success: bool
    message: str
    entity_id: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    global ws_handler
    if HOME_ASSISTANT_TOKEN:
        ws_handler = WebSocketHandler(HOME_ASSISTANT_URL, HOME_ASSISTANT_TOKEN)
        try:
            await ws_handler.connect()
            logger.info("WebSocket connection to Home Assistant established")
        except Exception as e:
            logger.warning(f"Failed to establish WebSocket connection: {e}")
    else:
        logger.warning("HOME_ASSISTANT_TOKEN not set, WebSocket connection disabled")


@app.on_event("shutdown")
async def shutdown_event():
    global ws_handler
    if ws_handler:
        await ws_handler.disconnect()
        logger.info("WebSocket connection closed")


@app.get("/")
def root():
    return {"service": "Jarvis Smart Home Service", "status": "running"}


@app.get("/health")
def health_check():
    """Check connection to Home Assistant"""
    if not HOME_ASSISTANT_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="HOME_ASSISTANT_TOKEN not configured"
        )
    
    is_connected = ha_client.check_connection()
    if is_connected:
        return {"status": "healthy", "home_assistant": "connected"}
    else:
        raise HTTPException(
            status_code=503,
            detail="Cannot connect to Home Assistant"
        )


@app.get("/v1/entities", response_model=List[EntityResponse])
def get_entities(
    domain: Optional[str] = Query(None, description="Filter by domain (e.g., 'light', 'switch', 'sensor')")
):
    """
    Get all entities from Home Assistant.
    Filters to relevant domains: light, switch, sensor, media_player, climate, cover, fan
    """
    if not HOME_ASSISTANT_TOKEN:
        raise HTTPException(status_code=503, detail="HOME_ASSISTANT_TOKEN not configured")
    
    try:
        entities = ha_client.get_entities(domain=domain)
        return [
            EntityResponse(
                entity_id=e["entity_id"],
                state=e["state"],
                friendly_name=e.get("attributes", {}).get("friendly_name"),
                attributes=e.get("attributes"),
                last_changed=e.get("last_changed"),
                last_updated=e.get("last_updated")
            )
            for e in entities
        ]
    except Exception as e:
        logger.error(f"Error fetching entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/entities/{entity_id}", response_model=EntityResponse)
def get_entity(entity_id: str):
    """Get the state of a specific entity"""
    if not HOME_ASSISTANT_TOKEN:
        raise HTTPException(status_code=503, detail="HOME_ASSISTANT_TOKEN not configured")
    
    try:
        entity = ha_client.get_entity(entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")
        
        return EntityResponse(
            entity_id=entity["entity_id"],
            state=entity["state"],
            friendly_name=entity.get("attributes", {}).get("friendly_name"),
            attributes=entity.get("attributes"),
            last_changed=entity.get("last_changed"),
            last_updated=entity.get("last_updated")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching entity {entity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/services/{domain}/{service}", response_model=ActionResponse)
def call_service(domain: str, service: str, request: ServiceCallRequest):
    """
    Call a Home Assistant service.
    Example: POST /v1/services/light/turn_on with {"entity_id": "light.wohnzimmer"}
    """
    if not HOME_ASSISTANT_TOKEN:
        raise HTTPException(status_code=503, detail="HOME_ASSISTANT_TOKEN not configured")
    
    try:
        service_data = {"entity_id": request.entity_id}
        if request.data:
            service_data.update(request.data)
        
        success = ha_client.call_service(domain, service, service_data)
        
        if success:
            return ActionResponse(
                success=True,
                message=f"Service {domain}.{service} called successfully",
                entity_id=request.entity_id
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to call service {domain}.{service}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calling service {domain}.{service}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/actions/turn_on", response_model=ActionResponse)
def turn_on(request: EntityActionRequest):
    """Turn on a device (light, switch, etc.)"""
    if not HOME_ASSISTANT_TOKEN:
        raise HTTPException(status_code=503, detail="HOME_ASSISTANT_TOKEN not configured")
    
    try:
        domain = request.entity_id.split(".")[0]
        success = ha_client.call_service(domain, "turn_on", {"entity_id": request.entity_id})
        
        if success:
            return ActionResponse(
                success=True,
                message=f"Turned on {request.entity_id}",
                entity_id=request.entity_id
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to turn on {request.entity_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error turning on {request.entity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/actions/turn_off", response_model=ActionResponse)
def turn_off(request: EntityActionRequest):
    """Turn off a device (light, switch, etc.)"""
    if not HOME_ASSISTANT_TOKEN:
        raise HTTPException(status_code=503, detail="HOME_ASSISTANT_TOKEN not configured")
    
    try:
        domain = request.entity_id.split(".")[0]
        success = ha_client.call_service(domain, "turn_off", {"entity_id": request.entity_id})
        
        if success:
            return ActionResponse(
                success=True,
                message=f"Turned off {request.entity_id}",
                entity_id=request.entity_id
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to turn off {request.entity_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error turning off {request.entity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/actions/toggle", response_model=ActionResponse)
def toggle(request: EntityActionRequest):
    """Toggle a device (light, switch, etc.)"""
    if not HOME_ASSISTANT_TOKEN:
        raise HTTPException(status_code=503, detail="HOME_ASSISTANT_TOKEN not configured")
    
    try:
        domain = request.entity_id.split(".")[0]
        success = ha_client.call_service(domain, "toggle", {"entity_id": request.entity_id})
        
        if success:
            return ActionResponse(
                success=True,
                message=f"Toggled {request.entity_id}",
                entity_id=request.entity_id
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to toggle {request.entity_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling {request.entity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
