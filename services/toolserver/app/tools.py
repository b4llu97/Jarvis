import chromadb
from chromadb.config import Settings
import os
import time
import requests
from typing import List, Dict, Optional, Any

CHROMA_HOST = os.getenv("CHROMA_HOST", "http://chroma:8000")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "jarvis_docs")
SMARTHOME_URL = os.getenv("SMARTHOME_URL", "http://smarthome:8008")

def get_chroma_client():
    host = CHROMA_HOST.replace("http://", "").replace("https://", "").split(":")[0]
    port_str = CHROMA_HOST.split(":")[-1]
    port = int(port_str) if port_str.isdigit() else 8000
    
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            client = chromadb.HttpClient(
                host=host,
                port=port,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            client.heartbeat()
            return client
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Chroma connection attempt {attempt + 1} failed, retrying in {retry_delay}s: {e}")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                print(f"Failed to connect to Chroma after {max_retries} attempts: {e}")
                raise

def get_or_create_collection():
    client = get_chroma_client()
    try:
        collection = client.get_collection(name=CHROMA_COLLECTION)
    except Exception as e:
        print(f"Collection not found, creating new one: {e}")
        collection = client.create_collection(
            name=CHROMA_COLLECTION,
            metadata={"description": "Jarvis document collection"}
        )
    return collection

def search_docs(query: str, n_results: int = 5) -> List[Dict]:
    try:
        collection = get_or_create_collection()
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        documents = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                documents.append({
                    "text": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else None
                })
        
        return documents
    except Exception as e:
        return [{"error": str(e)}]

def add_document(text: str, metadata: Dict = None) -> bool:
    try:
        collection = get_or_create_collection()
        import uuid
        doc_id = str(uuid.uuid4())
        
        collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[doc_id]
        )
        return True
    except Exception as e:
        print(f"Error adding document: {e}")
        return False


def smarthome_list_devices(domain: str) -> Dict[str, Any]:
    """
    List all Smart Home devices of a specific type.
    
    Args:
        domain: Device type (e.g., 'light', 'switch', 'sensor', 'media_player')
    
    Returns:
        Dictionary with success status and list of devices
    """
    try:
        response = requests.get(
            f"{SMARTHOME_URL}/v1/entities",
            params={"domain": domain},
            timeout=10
        )
        response.raise_for_status()
        entities = response.json()
        
        devices = []
        for entity in entities:
            devices.append({
                "entity_id": entity.get("entity_id"),
                "friendly_name": entity.get("friendly_name") or entity.get("entity_id"),
                "state": entity.get("state")
            })
        
        return {
            "success": True,
            "devices": devices,
            "count": len(devices)
        }
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Smart Home Service nicht erreichbar"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def smarthome_turn_on(entity_id: str) -> Dict[str, Any]:
    """
    Turn on a Smart Home device.
    
    Args:
        entity_id: The entity ID of the device (e.g., 'light.wohnzimmer')
    
    Returns:
        Dictionary with success status and message
    """
    try:
        response = requests.post(
            f"{SMARTHOME_URL}/v1/actions/turn_on",
            json={"entity_id": entity_id},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        return {
            "success": result.get("success", False),
            "message": result.get("message", "Gerät eingeschaltet")
        }
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Smart Home Service nicht erreichbar"}
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {"success": False, "error": f"Gerät '{entity_id}' nicht gefunden"}
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def smarthome_turn_off(entity_id: str) -> Dict[str, Any]:
    """
    Turn off a Smart Home device.
    
    Args:
        entity_id: The entity ID of the device (e.g., 'light.wohnzimmer')
    
    Returns:
        Dictionary with success status and message
    """
    try:
        response = requests.post(
            f"{SMARTHOME_URL}/v1/actions/turn_off",
            json={"entity_id": entity_id},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        return {
            "success": result.get("success", False),
            "message": result.get("message", "Gerät ausgeschaltet")
        }
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Smart Home Service nicht erreichbar"}
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {"success": False, "error": f"Gerät '{entity_id}' nicht gefunden"}
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def smarthome_get_status(entity_id: str) -> Dict[str, Any]:
    """
    Get the status of a Smart Home device or sensor.
    
    Args:
        entity_id: The entity ID of the device (e.g., 'light.wohnzimmer', 'sensor.temperatur')
    
    Returns:
        Dictionary with success status and human-readable status description
    """
    try:
        response = requests.get(
            f"{SMARTHOME_URL}/v1/entities/{entity_id}",
            timeout=10
        )
        response.raise_for_status()
        entity = response.json()
        
        state = entity.get("state", "unknown")
        friendly_name = entity.get("friendly_name") or entity_id
        attributes = entity.get("attributes", {})
        domain = entity_id.split(".")[0] if "." in entity_id else ""
        
        if domain == "light":
            if state == "on":
                brightness = attributes.get("brightness")
                if brightness:
                    brightness_pct = round((brightness / 255) * 100)
                    status_text = f"{friendly_name} ist eingeschaltet mit {brightness_pct}% Helligkeit"
                else:
                    status_text = f"{friendly_name} ist eingeschaltet"
            else:
                status_text = f"{friendly_name} ist ausgeschaltet"
        
        elif domain == "switch":
            status_text = f"{friendly_name} ist {'eingeschaltet' if state == 'on' else 'ausgeschaltet'}"
        
        elif domain == "sensor":
            unit = attributes.get("unit_of_measurement", "")
            device_class = attributes.get("device_class", "")
            
            if device_class == "temperature":
                status_text = f"Die Temperatur ({friendly_name}) beträgt {state}{unit}"
            elif device_class == "humidity":
                status_text = f"Die Luftfeuchtigkeit ({friendly_name}) beträgt {state}{unit}"
            elif device_class == "battery":
                status_text = f"Der Batteriestand ({friendly_name}) beträgt {state}{unit}"
            else:
                status_text = f"{friendly_name}: {state} {unit}".strip()
        
        elif domain == "binary_sensor":
            device_class = attributes.get("device_class", "")
            if device_class == "motion":
                status_text = f"{friendly_name}: {'Bewegung erkannt' if state == 'on' else 'Keine Bewegung'}"
            elif device_class == "door":
                status_text = f"{friendly_name} ist {'offen' if state == 'on' else 'geschlossen'}"
            elif device_class == "window":
                status_text = f"{friendly_name} ist {'offen' if state == 'on' else 'geschlossen'}"
            else:
                status_text = f"{friendly_name}: {state}"
        
        elif domain == "media_player":
            if state == "playing":
                media_title = attributes.get("media_title", "")
                if media_title:
                    status_text = f"{friendly_name} spielt: {media_title}"
                else:
                    status_text = f"{friendly_name} spielt gerade"
            elif state == "paused":
                status_text = f"{friendly_name} ist pausiert"
            elif state == "idle":
                status_text = f"{friendly_name} ist im Leerlauf"
            else:
                status_text = f"{friendly_name}: {state}"
        
        elif domain == "climate":
            current_temp = attributes.get("current_temperature")
            target_temp = attributes.get("temperature")
            hvac_mode = attributes.get("hvac_mode", state)
            
            if current_temp and target_temp:
                status_text = f"{friendly_name}: Aktuell {current_temp}°C, Ziel {target_temp}°C ({hvac_mode})"
            elif current_temp:
                status_text = f"{friendly_name}: Aktuell {current_temp}°C ({hvac_mode})"
            else:
                status_text = f"{friendly_name}: {hvac_mode}"
        
        else:
            status_text = f"{friendly_name}: {state}"
        
        return {
            "success": True,
            "entity_id": entity_id,
            "state": state,
            "status_text": status_text,
            "attributes": attributes
        }
    
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Smart Home Service nicht erreichbar"}
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {"success": False, "error": f"Gerät '{entity_id}' nicht gefunden"}
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_tool_definitions() -> List[Dict]:
    return [
        {
            "name": "get_fact",
            "description": "Ruft einen gespeicherten Fakt aus der Datenbank ab",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Der Schlüssel des Fakts (z.B. 'versicherung.gebaeude.summe')"
                    }
                },
                "required": ["key"]
            }
        },
        {
            "name": "set_fact",
            "description": "Speichert einen neuen Fakt in der Datenbank",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Der Schlüssel des Fakts"
                    },
                    "value": {
                        "type": "string",
                        "description": "Der Wert des Fakts"
                    }
                },
                "required": ["key", "value"]
            }
        },
        {
            "name": "search_docs",
            "description": "Durchsucht die Dokumentensammlung semantisch nach relevanten Informationen",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Die Suchanfrage"
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Anzahl der Ergebnisse (Standard: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "smarthome_list_devices",
            "description": "Listet alle verfügbaren Smart-Home-Geräte eines bestimmten Typs auf (z.B. 'light', 'switch', 'sensor', 'media_player'). Nutze dieses Tool, um herauszufinden, welche Geräte verfügbar sind.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Der Gerätetyp (z.B. 'light' für Lichter, 'switch' für Schalter, 'sensor' für Sensoren, 'media_player' für Mediaplayer)"
                    }
                },
                "required": ["domain"]
            }
        },
        {
            "name": "smarthome_turn_on",
            "description": "Schaltet ein Smart-Home-Gerät ein (z.B. ein Licht oder einen Schalter). Benötigt die entity_id des Geräts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Die Entity-ID des Geräts (z.B. 'light.wohnzimmer', 'switch.steckdose_1')"
                    }
                },
                "required": ["entity_id"]
            }
        },
        {
            "name": "smarthome_turn_off",
            "description": "Schaltet ein Smart-Home-Gerät aus. Benötigt die entity_id des Geräts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Die Entity-ID des Geräts (z.B. 'light.wohnzimmer', 'switch.steckdose_1')"
                    }
                },
                "required": ["entity_id"]
            }
        },
        {
            "name": "smarthome_get_status",
            "description": "Fragt den aktuellen Zustand eines Smart-Home-Geräts oder Sensors ab (z.B. 'ist das Licht an?', 'wie ist die Temperatur?'). Gibt eine menschenlesbare Zusammenfassung zurück.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Die Entity-ID des Geräts oder Sensors (z.B. 'light.wohnzimmer', 'sensor.temperatur_aussen')"
                    }
                },
                "required": ["entity_id"]
            }
        }
    ]
