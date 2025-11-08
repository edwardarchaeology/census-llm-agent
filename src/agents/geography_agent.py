"""
Geography resolution agent - expert in Louisiana geography.
"""
from typing import Optional, Tuple
from agents.base_agent import OllamaAgent
from agents.config import AGENT_CONFIGS
from geography import LOUISIANA_PARISHES, MAJOR_CITIES


class GeographyAgent(OllamaAgent):
    """Specialized agent for resolving Louisiana geography."""
    
    def __init__(self):
        config = AGENT_CONFIGS["geography"]
        super().__init__(
            model=config["model"],
            role=config["role"],
            temperature=config["temperature"]
        )
        self.parishes = LOUISIANA_PARISHES
        self.cities = MAJOR_CITIES
    
    def get_system_prompt(self) -> str:
        """System prompt for geography specialist."""
        parish_list = ", ".join(sorted(self.parishes.keys())[:20])  # First 20 for brevity
        city_list = ", ".join(sorted(self.cities.keys())[:15])
        
        return f"""You are a Louisiana geography expert specializing in parish and city identification.

Your knowledge includes:
- All 64 Louisiana parishes with FIPS codes
- Major Louisiana cities and their parishes
- Alternative names and spellings

Known parishes (sample): {parish_list}...
Known cities (sample): {city_list}...

Your job: Extract geographic information from user queries.
Return ONLY valid JSON with parish name and FIPS code.
If no geography is mentioned, return null values.
Be case-insensitive and handle variations (e.g., "St." vs "Saint", "Parish" suffix optional)."""
    
    def resolve(self, query: str) -> Tuple[Optional[str], Optional[str], float]:
        """
        Resolve geography from query.
        
        Args:
            query: Natural language query
            
        Returns:
            Tuple of (parish_name, county_fips, confidence)
            - parish_name: e.g., "Caddo Parish"
            - county_fips: e.g., "017" (3-digit county code only, not full state+county)
            - confidence: 0.0 to 1.0
        """
        prompt = f"""Extract Louisiana geography from this query:
"{query}"

IMPORTANT: Return ONLY the 3-digit county FIPS code (e.g., "017" for Caddo, "055" for Lafayette).
Do NOT include the state code. Just the 3-digit parish code.

Return JSON in this exact format:
{{
  "parish_name": "Caddo Parish" or null,
  "county_fips": "017" or null,
  "confidence": 0.95
}}

Examples:
- "poverty in New Orleans" → {{"parish_name": "Orleans Parish", "county_fips": "071", "confidence": 0.95}}
- "Shreveport area" → {{"parish_name": "Caddo Parish", "county_fips": "017", "confidence": 0.90}}
- "Lafayette Parish" → {{"parish_name": "Lafayette Parish", "county_fips": "055", "confidence": 1.0}}
- "St. Tammany Parish" → {{"parish_name": "St. Tammany Parish", "county_fips": "103", "confidence": 1.0}}
- "highest income in Louisiana" → {{"parish_name": null, "county_fips": null, "confidence": 0.0}}

Now analyze: "{query}"
"""
        
        result = self.call_llm(prompt, format="json")
        
        # Get parish name and FIPS from LLM result
        parish_name = result.get("parish_name")
        fips = result.get("county_fips")
        confidence = result.get("confidence", 0.0)
        
        # Validate and fix FIPS code
        if fips:
            # Strip any state prefix if present
            fips = str(fips).strip()
            original_fips = fips  # Store for debugging
            
            if len(fips) > 3:
                # If it starts with "22", remove it
                if fips.startswith("22"):
                    fips = fips[2:]
                # Otherwise take last 3 digits
                else:
                    fips = fips[-3:]
            # Pad to 3 digits if needed
            fips = fips.zfill(3)
            
            # CRITICAL: Validate against known parishes
            if fips not in self.parishes.values():
                print(f"⚠️  LLM returned invalid FIPS: '{original_fips}' -> '{fips}'")
                # LLM returned invalid FIPS - try to fix it
                if parish_name:
                    # Look up correct FIPS from parish name
                    parish_key = parish_name.lower().replace(" parish", "").strip()
                    print(f"   Looking up '{parish_key}' in parishes dict...")
                    if parish_key in self.parishes:
                        corrected_fips = self.parishes[parish_key]
                        print(f"   ✅ Fixed: Using {corrected_fips} for {parish_name} (was {fips})")
                        fips = corrected_fips
                    else:
                        print(f"   ❌ Couldn't find '{parish_key}' in parishes dict")
                        # Try without "parish" suffix
                        alt_key = parish_key.replace("parish", "").strip()
                        if alt_key in self.parishes:
                            corrected_fips = self.parishes[alt_key]
                            print(f"   ✅ Fixed: Using {corrected_fips} for {parish_name} (was {fips})")
                            fips = corrected_fips
                        else:
                            print(f"   ❌ Invalid FIPS '{fips}' for {parish_name} and couldn't find match")
                            fips = None
                else:
                    print(f"   ❌ Invalid FIPS '{fips}' with no parish name to validate")
                    fips = None
        
        return (parish_name, fips, confidence)
    
    def validate_fips(self, fips: Optional[str]) -> bool:
        """Validate that a FIPS code exists in Louisiana."""
        if not fips:
            return False
        return fips in self.parishes.values()
