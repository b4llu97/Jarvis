import requests
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

RELEVANT_DOMAINS = ["light", "switch", "sensor", "media_player", "climate", "cover", "fan", "binary_sensor"]


class HomeAssistantClient:
    """Client for interacting with Home Assistant REST API"""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        timeout: int = 10
    ) -> Optional[Any]:
        """Make a request to Home Assistant API"""
        url = f"{self.base_url}/api{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=timeout)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout:
            logger.error(f"Request to {url} timed out")
            raise Exception("Home Assistant request timed out")
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Home Assistant at {self.base_url}")
            raise Exception("Cannot connect to Home Assistant")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("Invalid Home Assistant token")
                raise Exception("Invalid Home Assistant token")
            elif e.response.status_code == 404:
                logger.warning(f"Resource not found: {endpoint}")
                return None
            else:
                logger.error(f"HTTP error: {e}")
                raise Exception(f"Home Assistant API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    def check_connection(self) -> bool:
        """Check if we can connect to Home Assistant"""
        try:
            result = self._make_request("GET", "/")
            return result is not None and "message" in result
        except Exception:
            return False
    
    def get_entities(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all entities from Home Assistant.
        Optionally filter by domain.
        """
        try:
            states = self._make_request("GET", "/states")
            if not states:
                return []
            
            filtered_entities = []
            for entity in states:
                entity_id = entity.get("entity_id", "")
                entity_domain = entity_id.split(".")[0] if "." in entity_id else ""
                
                if domain:
                    if entity_domain == domain:
                        filtered_entities.append(entity)
                elif entity_domain in RELEVANT_DOMAINS:
                    filtered_entities.append(entity)
            
            return filtered_entities
        
        except Exception as e:
            logger.error(f"Error fetching entities: {e}")
            raise
    
    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get the state of a specific entity"""
        try:
            return self._make_request("GET", f"/states/{entity_id}")
        except Exception as e:
            logger.error(f"Error fetching entity {entity_id}: {e}")
            raise
    
    def call_service(
        self,
        domain: str,
        service: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Call a Home Assistant service.
        
        Args:
            domain: Service domain (e.g., 'light', 'switch')
            service: Service name (e.g., 'turn_on', 'turn_off')
            data: Service data including entity_id
        
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self._make_request(
                "POST",
                f"/services/{domain}/{service}",
                data=data
            )
            return result is not None
        except Exception as e:
            logger.error(f"Error calling service {domain}.{service}: {e}")
            raise
    
    def get_config(self) -> Optional[Dict[str, Any]]:
        """Get Home Assistant configuration"""
        try:
            return self._make_request("GET", "/config")
        except Exception as e:
            logger.error(f"Error fetching config: {e}")
            return None
