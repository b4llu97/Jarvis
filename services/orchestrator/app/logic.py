import os
import requests
import json
import re
from typing import Dict, List, Optional, Any

TOOLSERVER_URL = os.getenv("TOOLSERVER_URL", "http://toolserver:8002")
LLM_GATEWAY_URL = os.getenv("LLM_GATEWAY_URL", "http://llm_gateway:8007")
USE_LLM_GATEWAY = os.getenv("USE_LLM_GATEWAY", "true").lower() == "true"

# Legacy Ollama settings (for backward compatibility)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://llama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

SYSTEM_PROMPT_PATH = "/app/config/system_prompt.txt"
PERSONA_PROMPT_PATH = "/app/config/persona_prompt.txt"

def load_prompts() -> tuple[str, str]:
    with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
        system_prompt = f.read()
    
    with open(PERSONA_PROMPT_PATH, "r", encoding="utf-8") as f:
        persona_prompt = f.read()
    
    return system_prompt, persona_prompt

def get_available_tools() -> List[Dict[str, Any]]:
    try:
        response = requests.get(f"{TOOLSERVER_URL}/v1/tools", timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get("tools", [])
    except Exception as e:
        print(f"Error fetching tools: {e}")
        return []

def call_llm_gateway(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """Call the new LLM Gateway service"""
    try:
        payload = {
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        response = requests.post(
            f"{LLM_GATEWAY_URL}/v1/chat",
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        
        result = response.json()
        return {
            "content": result.get("content", ""),
            "model": result.get("model", "unknown"),
            "provider": result.get("provider", "unknown")
        }
    
    except Exception as e:
        print(f"Error calling LLM Gateway: {e}")
        raise

def call_ollama(messages: List[Dict[str, str]]) -> str:
    """Legacy Ollama call (for backward compatibility)"""
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False
        }
        
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        return result.get("message", {}).get("content", "")
    
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return f"Fehler bei der LLM-Anfrage: {str(e)}"

def call_llm(messages: List[Dict[str, str]]) -> tuple[str, Optional[Dict[str, str]]]:
    """
    Unified LLM call function
    Returns: (response_text, metadata)
    """
    if USE_LLM_GATEWAY:
        try:
            result = call_llm_gateway(messages)
            metadata = {
                "model": result["model"],
                "provider": result["provider"]
            }
            return result["content"], metadata
        except Exception as e:
            print(f"LLM Gateway failed, falling back to direct Ollama: {e}")
            # Fallback to direct Ollama
            response = call_ollama(messages)
            metadata = {
                "model": OLLAMA_MODEL,
                "provider": "ollama_direct"
            }
            return response, metadata
    else:
        # Use legacy Ollama directly
        response = call_ollama(messages)
        metadata = {
            "model": OLLAMA_MODEL,
            "provider": "ollama_direct"
        }
        return response, metadata

def parse_tool_calls(text: str) -> List[Dict[str, Any]]:
    tool_call_pattern = r'<tool_call>(.*?)</tool_call>'
    matches = re.findall(tool_call_pattern, text, re.DOTALL)
    
    tool_calls = []
    for match in matches:
        match = match.strip()
        
        if match.startswith("get_fact("):
            key_match = re.search(r'get_fact\(["\'](.+?)["\']\)', match)
            if key_match:
                tool_calls.append({
                    "function": "get_fact",
                    "key": key_match.group(1)
                })
        
        elif match.startswith("set_fact("):
            params_match = re.search(r'set_fact\(["\'](.+?)["\']\s*,\s*["\'](.+?)["\']\)', match)
            if params_match:
                tool_calls.append({
                    "function": "set_fact",
                    "key": params_match.group(1),
                    "value": params_match.group(2)
                })
        
        elif match.startswith("search_docs("):
            query_match = re.search(r'search_docs\(["\'](.+?)["\']\)', match)
            if query_match:
                tool_calls.append({
                    "function": "search_docs",
                    "query": query_match.group(1)
                })
    
    return tool_calls

def execute_tool_call(tool_call: Dict[str, Any]) -> Dict[str, Any]:
    function = tool_call.get("function")
    
    try:
        if function == "get_fact":
            key = tool_call.get("key")
            response = requests.get(f"{TOOLSERVER_URL}/v1/facts/{key}", timeout=5)
            
            if response.status_code == 404:
                return {"success": False, "error": "Fakt nicht gefunden"}
            
            response.raise_for_status()
            data = response.json()
            return {"success": True, "result": data.get("value")}
        
        elif function == "set_fact":
            key = tool_call.get("key")
            value = tool_call.get("value")
            response = requests.put(
                f"{TOOLSERVER_URL}/v1/facts/{key}",
                json={"value": value},
                timeout=5
            )
            response.raise_for_status()
            return {"success": True, "result": "Fakt gespeichert"}
        
        elif function == "search_docs":
            query = tool_call.get("query")
            response = requests.post(
                f"{TOOLSERVER_URL}/v1/search",
                json={"query": query, "n_results": 3},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            
            if results:
                formatted_results = []
                for result in results:
                    doc = result.get("text", "")
                    metadata = result.get("metadata", {})
                    distance = result.get("distance", 0)
                    formatted_results.append(f"- {doc[:200]}... (Relevanz: {1-distance:.2f})")
                
                return {
                    "success": True,
                    "result": "\n".join(formatted_results)
                }
            else:
                return {"success": True, "result": "Keine Dokumente gefunden"}
        
        else:
            return {"success": False, "error": f"Unbekannte Funktion: {function}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_learning_context() -> str:
    """Get learning context from feedback database"""
    try:
        response = requests.get(f"{TOOLSERVER_URL}/v1/learning/context?limit=5", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("context", "")
    except Exception as e:
        print(f"Error fetching learning context: {e}")
    return ""

def process_query(
    query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    system_prompt, persona_prompt = load_prompts()
    tools = get_available_tools()
    
    tools_description = "\n".join([
        f"- {tool['name']}: {tool['description']}"
        for tool in tools
    ])
    
    # Get learning context from feedback
    learning_context = get_learning_context()
    
    # Build full system prompt with learning context
    full_system_prompt = f"{system_prompt}\n\n{persona_prompt}\n\nVerfügbare Tools:\n{tools_description}"
    
    if learning_context:
        full_system_prompt += f"\n\n{learning_context}\n\nBitte berücksichtige diese früheren Korrekturen und Feedback bei deiner Antwort."
    
    messages = [{"role": "system", "content": full_system_prompt}]
    
    if conversation_history:
        messages.extend(conversation_history)
    
    messages.append({"role": "user", "content": query})
    
    # Call LLM (with new gateway or legacy)
    llm_response, llm_metadata = call_llm(messages)
    
    tool_calls = parse_tool_calls(llm_response)
    
    tool_results = []
    if tool_calls:
        for tool_call in tool_calls:
            result = execute_tool_call(tool_call)
            tool_results.append({
                "tool_call": tool_call,
                "result": result
            })
        
        tool_results_text = "\n".join([
            f"Tool: {tr['tool_call']['function']} -> {tr['result']}"
            for tr in tool_results
        ])
        
        messages.append({"role": "assistant", "content": llm_response})
        messages.append({
            "role": "user",
            "content": f"Tool-Ergebnisse:\n{tool_results_text}\n\nBitte formuliere jetzt eine finale Antwort für den Benutzer basierend auf diesen Ergebnissen."
        })
        
        final_response, final_metadata = call_llm(messages)
        
        return {
            "response": final_response,
            "tool_calls": tool_calls,
            "tool_results": tool_results,
            "raw_llm_response": llm_response,
            "llm_metadata": final_metadata
        }
    
    else:
        return {
            "response": llm_response,
            "tool_calls": [],
            "tool_results": [],
            "raw_llm_response": llm_response,
            "llm_metadata": llm_metadata
        }
