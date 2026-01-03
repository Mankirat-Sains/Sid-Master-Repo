"""Extractor for system role (gravity, lateral, etc.)"""
from typing import Dict, Any, Optional
from extractors.base import FactExtractor
from models.fact_result import FactValue, Evidence


class SystemRoleExtractor(FactExtractor):
    """Extracts structural system role from Speckle data"""
    
    @property
    def fact_name(self) -> str:
        return "system_role"
    
    def applies(self, fact_request: str) -> bool:
        return fact_request == "system_role"
    
    def extract(self, element_json: Dict[str, Any]) -> FactValue:
        """Extract system role"""
        evidence = []
        roles = []
        confidence = 0.0
        
        data = element_json.get("data", {})
        
        # Check for explicit system role
        system_role = data.get("systemRole", "") or data.get("role", "") or data.get("structuralRole", "")
        if system_role:
            evidence.append(Evidence(
                source="data.systemRole",
                value=system_role,
                path="data.systemRole"
            ))
            role_lower = str(system_role).lower()
            if "gravity" in role_lower:
                roles.append("gravity")
            if "lateral" in role_lower or "wind" in role_lower or "seismic" in role_lower:
                roles.append("lateral")
            if roles:
                confidence = 0.9
        
        # Check for load-bearing property
        if not roles:
            is_load_bearing = data.get("isLoadBearing", False) or data.get("loadBearing", False)
            if is_load_bearing:
                roles.append("gravity")
                confidence = 0.7
                evidence.append(Evidence(
                    source="data.isLoadBearing",
                    value=is_load_bearing,
                    path="data.isLoadBearing"
                ))
        
        # Check for bracing/brace indicator
        if not roles:
            element_type = element_json.get("speckleType", "").lower()
            if "brace" in element_type:
                roles.append("lateral")
                confidence = 0.8
                evidence.append(Evidence(
                    source="speckleType",
                    value=element_type,
                    path="speckleType"
                ))
        
        # Check for connections that indicate lateral system
        if not roles:
            connections = data.get("connections", [])
            if isinstance(connections, list) and connections:
                # If has diagonal connections, likely lateral
                for conn in connections:
                    if isinstance(conn, dict):
                        conn_type = str(conn.get("type", "")).lower()
                        if "diagonal" in conn_type or "brace" in conn_type:
                            roles.append("lateral")
                            confidence = 0.6
                            break
        
        # Default: assume gravity if no other indication
        if not roles:
            roles = ["gravity"]
            confidence = 0.5
        
        value = roles if len(roles) > 1 else roles[0] if roles else "unknown"
        
        return FactValue(
            value=value,
            confidence=confidence,
            evidence=evidence
        )

