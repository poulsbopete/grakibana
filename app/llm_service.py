"""
LLM service for intelligent dashboard conversion
"""

import json
import logging
from typing import Dict, Any, Optional, List
from .config import get_llm_config, is_llm_enabled

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM-powered dashboard conversion features"""
    
    def __init__(self):
        self.config = get_llm_config() if is_llm_enabled() else None
        self.client = None
        
        if self.config:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        if not self.config:
            return
            
        provider = self.config["provider"]
        
        try:
            if provider == "openai":
                import openai
                self.client = openai.OpenAI(api_key=self.config["api_key"])
            elif provider == "anthropic":
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.config["api_key"])
            elif provider == "google":
                import google.generativeai as genai
                genai.configure(api_key=self.config["api_key"])
                self.client = genai.GenerativeModel(self.config["model"])
            else:
                logger.warning(f"Unsupported LLM provider: {provider}")
                
        except ImportError as e:
            logger.error(f"Failed to import LLM library for {provider}: {e}")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if LLM service is available"""
        return self.client is not None
    
    async def translate_query(self, grafana_query: str, source_datasource: str, target_datasource: str) -> Optional[str]:
        """Translate a Grafana query to Kibana format using LLM"""
        if not self.is_available():
            return None
            
        prompt = f"""
        Translate this Grafana query to Kibana format:
        
        Source Datasource: {source_datasource}
        Target Datasource: {target_datasource}
        Grafana Query: {grafana_query}
        
        Provide only the translated query in Kibana format, no explanations.
        """
        
        try:
            response = await self._call_llm(prompt)
            return response.strip() if response else None
        except Exception as e:
            logger.error(f"Failed to translate query: {e}")
            return None
    
    async def suggest_visualization_type(self, panel_data: Dict[str, Any]) -> Optional[str]:
        """Suggest the best Kibana visualization type for a Grafana panel"""
        if not self.is_available():
            return None
            
        panel_info = {
            "type": panel_data.get("type"),
            "title": panel_data.get("title"),
            "targets": panel_data.get("targets", []),
            "fieldConfig": panel_data.get("fieldConfig", {})
        }
        
        prompt = f"""
        Analyze this Grafana panel and suggest the best Kibana visualization type:
        
        Panel Data: {json.dumps(panel_info, indent=2)}
        
        Available Kibana visualizations: line, area, bar, horizontal_bar, pie, donut, table, metric, gauge, heatmap, histogram, scatter
        
        Respond with only the visualization type name.
        """
        
        try:
            response = await self._call_llm(prompt)
            return response.strip().lower() if response else None
        except Exception as e:
            logger.error(f"Failed to suggest visualization type: {e}")
            return None
    
    async def optimize_panel_config(self, panel_data: Dict[str, Any], kibana_type: str) -> Optional[Dict[str, Any]]:
        """Optimize panel configuration for Kibana using LLM"""
        if not self.is_available():
            return None
            
        prompt = f"""
        Optimize this Grafana panel configuration for Kibana {kibana_type} visualization:
        
        Original Panel: {json.dumps(panel_data, indent=2)}
        Target Kibana Type: {kibana_type}
        
        Return only the optimized configuration as JSON.
        """
        
        try:
            response = await self._call_llm(prompt)
            if response:
                return json.loads(response)
            return None
        except Exception as e:
            logger.error(f"Failed to optimize panel config: {e}")
            return None
    
    async def validate_conversion(self, original_dashboard: Dict[str, Any], converted_dashboard: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the conversion quality using LLM"""
        if not self.is_available():
            return {"valid": True, "score": 1.0, "issues": []}
            
        prompt = f"""
        Validate this Grafana to Kibana dashboard conversion:
        
        Original Grafana Dashboard:
        {json.dumps(original_dashboard, indent=2)}
        
        Converted Kibana Dashboard:
        {json.dumps(converted_dashboard, indent=2)}
        
        Analyze the conversion quality and return a JSON response with:
        - valid: boolean (true if conversion is good)
        - score: float (0.0 to 1.0, quality score)
        - issues: array of strings (any problems found)
        - suggestions: array of strings (improvement suggestions)
        """
        
        try:
            response = await self._call_llm(prompt)
            if response:
                return json.loads(response)
            return {"valid": True, "score": 1.0, "issues": []}
        except Exception as e:
            logger.error(f"Failed to validate conversion: {e}")
            return {"valid": True, "score": 1.0, "issues": []}
    
    async def _call_llm(self, prompt: str) -> Optional[str]:
        """Make a call to the configured LLM"""
        if not self.client:
            return None
            
        try:
            provider = self.config["provider"]
            
            if provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.config["model"],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.config["temperature"],
                    max_tokens=self.config["max_tokens"]
                )
                return response.choices[0].message.content
                
            elif provider == "anthropic":
                response = self.client.messages.create(
                    model=self.config["model"],
                    max_tokens=self.config["max_tokens"],
                    temperature=self.config["temperature"],
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
                
            elif provider == "google":
                response = self.client.generate_content(
                    prompt,
                    generation_config={
                        "temperature": self.config["temperature"],
                        "max_output_tokens": self.config["max_tokens"]
                    }
                )
                return response.text
                
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return None


# Global LLM service instance
llm_service = LLMService() 