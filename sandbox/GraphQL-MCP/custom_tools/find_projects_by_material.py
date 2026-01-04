#!/usr/bin/env python3
"""
Fast Project Material Search Tool

Solves the problem of finding projects with specific materials across hundreds of projects:
- Samples a small number of elements from each project (not full data)
- Uses parallel queries for speed
- Handles IFC/Revit/ETABS differences via ElementNormalizer
- Scores and ranks projects
- Returns top N results without exceeding context limits
"""

import json
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from custom_tools.base_tool import BaseTool, ToolDefinition
from custom_tools.element_normalizer import ElementNormalizer
from custom_tools.project_material_cache import ProjectMaterialCache

logger = logging.getLogger(__name__)


@dataclass
class ProjectMaterialScore:
    """Score for a project based on material matches"""
    project_id: str
    project_name: str
    score: float
    match_count: int
    sample_size: int
    materials_found: List[str]
    confidence: str  # "high", "medium", "low"


class FindProjectsByMaterialTool(BaseTool):
    """
    Fast tool to find projects containing specific materials.
    
    Strategy:
    1. List all projects (fast, lightweight query)
    2. Sample 20-50 elements from each project in parallel
    3. Extract materials using ElementNormalizer (handles IFC/Revit/ETABS)
    4. Score projects based on material matches
    5. Return top N projects
    
    This avoids loading full project data and exceeding context limits.
    """
    
    # Configuration
    SAMPLE_SIZE = 50  # Number of elements to sample per project
    MAX_PARALLEL_QUERIES = 10  # Max concurrent project queries
    MIN_MATCH_THRESHOLD = 0.1  # Minimum score to consider a match
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="find_projects_by_material",
            description="""Find projects containing specific materials (e.g., timber, steel, concrete).
            
This tool efficiently searches across hundreds of projects by:
- Sampling a small number of elements from each project
- Extracting material information (handles IFC/Revit/ETABS differences)
- Scoring and ranking projects
- Returning top N matches

Use this when users ask:
- "Find me 3 projects with timber"
- "Which projects use steel?"
- "Show projects with concrete materials"
- "Find projects containing [material]"

The tool is fast and doesn't load full project data, making it suitable for large-scale searches.""",
            parameters={
                "material": {
                    "type": "string",
                    "description": "Material to search for (e.g., 'timber', 'steel', 'concrete', 'wood')",
                    "required": True
                },
                "top_n": {
                    "type": "integer",
                    "description": "Number of top projects to return (default: 3)",
                    "required": False,
                    "default": 3
                },
                "sample_size": {
                    "type": "integer",
                    "description": f"Number of elements to sample per project (default: {self.SAMPLE_SIZE})",
                    "required": False,
                    "default": self.SAMPLE_SIZE
                },
                "min_confidence": {
                    "type": "string",
                    "description": "Minimum confidence level: 'high', 'medium', or 'low' (default: 'low')",
                    "required": False,
                    "default": "low",
                    "enum": ["high", "medium", "low"]
                }
            },
            handler=self.execute
        )
    
    def execute(
        self,
        material: str,
        top_n: int = 3,
        sample_size: int = None,
        min_confidence: str = "low"
    ) -> Dict[str, Any]:
        """
        Find projects containing the specified material.
        
        Args:
            material: Material to search for
            top_n: Number of top projects to return
            sample_size: Elements to sample per project
            min_confidence: Minimum confidence level
            
        Returns:
            Dict with project results
        """
        if not self.graphql_client:
            return {
                "isError": True,
                "content": [{"type": "text", "text": "GraphQL client not available"}]
            }
        
        sample_size = sample_size or self.SAMPLE_SIZE
        material_lower = material.lower().strip()
        
        try:
            # Step 1: Get all projects (fast)
            logger.info(f"Fetching project list...")
            projects = self._get_all_projects()
            
            if not projects:
                return {
                    "isError": False,
                    "content": [{"type": "text", "text": "No projects found"}]
                }
            
            logger.info(f"Found {len(projects)} projects. Sampling elements in parallel...")
            
            # Step 2: Check cache first, then sample projects in parallel
            project_scores = self._find_projects_with_material(
                projects,
                material_lower,
                sample_size,
                min_confidence
            )
            
            # Step 3: Sort by score and get top N
            project_scores.sort(key=lambda x: x.score, reverse=True)
            top_projects = project_scores[:top_n]
            
            # Step 4: Format results
            if not top_projects:
                return {
                    "isError": False,
                    "content": [{
                        "type": "text",
                        "text": f"No projects found containing '{material}'"
                    }]
                }
            
            result_text = self._format_results(top_projects, material, len(projects))
            
            return {
                "isError": False,
                "content": [{"type": "text", "text": result_text}],
                "data": {
                    "projects": [
                        {
                            "id": p.project_id,
                            "name": p.project_name,
                            "score": p.score,
                            "match_count": p.match_count,
                            "sample_size": p.sample_size,
                            "materials_found": p.materials_found,
                            "confidence": p.confidence
                        }
                        for p in top_projects
                    ],
                    "total_projects_searched": len(projects),
                    "material_searched": material
                }
            }
            
        except Exception as e:
            logger.error(f"Error finding projects by material: {e}", exc_info=True)
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Error: {str(e)}"}]
            }
    
    def _get_all_projects(self) -> List[Dict[str, str]]:
        """Get list of all projects (lightweight query)"""
        query = """
        query ListProjects {
          activeUser {
            projects(limit: 1000) {
              items {
                id
                name
              }
            }
          }
        }
        """
        
        result = self.graphql_client.query(query)
        
        if result.get("errors"):
            logger.error(f"GraphQL errors: {result['errors']}")
            return []
        
        projects_data = result.get("data", {}).get("activeUser", {}).get("projects", {}).get("items", [])
        return [{"id": p["id"], "name": p["name"]} for p in projects_data]
    
    def _find_projects_with_material(
        self,
        projects: List[Dict[str, str]],
        material: str,
        sample_size: int,
        min_confidence: str
    ) -> List[ProjectMaterialScore]:
        """
        Find projects with material, using cache when available.
        
        Strategy:
        1. Check cache for each project
        2. If cached and material found, create score from cache
        3. If not cached, sample and score project
        4. Update cache with results
        """
        project_scores = []
        projects_to_sample = []
        
        # First pass: Check cache
        for project in projects:
            if self.cache:
                cached_materials = self.cache.get_project_materials(project["id"])
                if cached_materials is not None:
                    # Cache hit - check if material is in cached materials
                    if material in " ".join(cached_materials).lower():
                        # Create score from cache (lower confidence since it's cached)
                        project_scores.append(ProjectMaterialScore(
                            project_id=project["id"],
                            project_name=project["name"],
                            score=0.5,  # Medium score for cached matches
                            match_count=1,  # Unknown, but material exists
                            sample_size=sample_size,
                            materials_found=list(cached_materials),
                            confidence="medium"
                        ))
                        continue
            
            # Not cached or cache miss - need to sample
            projects_to_sample.append(project)
        
        logger.info(f"Cache hits: {len(projects) - len(projects_to_sample)}, Cache misses: {len(projects_to_sample)}")
        
        # Second pass: Sample projects not in cache
        if projects_to_sample:
            sampled_scores = self._sample_projects_parallel(
                projects_to_sample,
                material,
                sample_size,
                min_confidence
            )
            project_scores.extend(sampled_scores)
            
            # Update cache with sampled results
            if self.cache:
                for score in sampled_scores:
                    self.cache.set_project_materials(
                        score.project_id,
                        set(score.materials_found),
                        sample_size=sample_size
                    )
        
        return project_scores
    
    def _sample_projects_parallel(
        self,
        projects: List[Dict[str, str]],
        material: str,
        sample_size: int,
        min_confidence: str
    ) -> List[ProjectMaterialScore]:
        """
        Sample elements from projects in parallel and score them.
        
        Uses ThreadPoolExecutor for parallel queries.
        """
        project_scores = []
        
        with ThreadPoolExecutor(max_workers=self.MAX_PARALLEL_QUERIES) as executor:
            # Submit all project sampling tasks
            future_to_project = {
                executor.submit(
                    self._sample_and_score_project,
                    project["id"],
                    project["name"],
                    material,
                    sample_size,
                    min_confidence
                ): project
                for project in projects
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_project):
                project = future_to_project[future]
                try:
                    score = future.result()
                    if score and score.score >= self.MIN_MATCH_THRESHOLD:
                        project_scores.append(score)
                except Exception as e:
                    logger.warning(f"Error sampling project {project['name']}: {e}")
        
        return project_scores
    
    def _sample_and_score_project(
        self,
        project_id: str,
        project_name: str,
        material: str,
        sample_size: int,
        min_confidence: str
    ) -> Optional[ProjectMaterialScore]:
        """
        Sample elements from a single project and score it.
        
        Returns ProjectMaterialScore or None if no matches found.
        """
        try:
            # Get latest version's root object
            root_object_id = self._get_project_root_object(project_id)
            if not root_object_id:
                return None
            
            # Sample elements (query with limit)
            elements = self._sample_project_elements(project_id, root_object_id, sample_size)
            
            if not elements:
                return None
            
            # Extract materials and score
            matches = []
            materials_found = set()
            
            for element in elements:
                element_data = element.get("data")
                if not element_data:
                    continue
                
                # Parse JSON if it's a string
                if isinstance(element_data, str):
                    try:
                        element_data = json.loads(element_data)
                    except json.JSONDecodeError:
                        continue
                
                # Extract material using normalizer
                material_info = ElementNormalizer.extract_material(element, element_data)
                extracted_material = material_info.get("material", "").lower()
                confidence = material_info.get("confidence", "low")
                
                # Check if material matches
                if extracted_material and material in extracted_material:
                    # Check confidence threshold
                    confidence_levels = {"high": 3, "medium": 2, "low": 1}
                    min_conf_level = confidence_levels.get(min_confidence, 1)
                    conf_level = confidence_levels.get(confidence, 1)
                    
                    if conf_level >= min_conf_level:
                        matches.append({
                            "material": extracted_material,
                            "confidence": confidence,
                            "source": material_info.get("source", "unknown")
                        })
                        materials_found.add(extracted_material)
            
            if not matches:
                return None
            
            # Calculate score
            # Score = (match_count / sample_size) * confidence_weight
            match_count = len(matches)
            match_ratio = match_count / sample_size
            
            # Weight by confidence (high confidence matches count more)
            confidence_weights = {"high": 1.0, "medium": 0.7, "low": 0.4}
            avg_confidence_weight = sum(
                confidence_weights.get(m["confidence"], 0.4) for m in matches
            ) / match_count
            
            score = match_ratio * avg_confidence_weight
            
            # Determine overall confidence
            confidences = [m["confidence"] for m in matches]
            overall_confidence = "high" if "high" in confidences else ("medium" if "medium" in confidences else "low")
            
            return ProjectMaterialScore(
                project_id=project_id,
                project_name=project_name,
                score=score,
                match_count=match_count,
                sample_size=sample_size,
                materials_found=sorted(list(materials_found)),
                confidence=overall_confidence
            )
            
        except Exception as e:
            logger.warning(f"Error sampling project {project_name} ({project_id}): {e}")
            return None
    
    def _get_project_root_object(self, project_id: str) -> Optional[str]:
        """Get the root object ID from the latest version"""
        query = """
        query GetRootObject($projectId: String!) {
          project(id: $projectId) {
            versions(limit: 1) {
              items {
                referencedObject
              }
            }
          }
        }
        """
        
        result = self.graphql_client.query(query, {"projectId": project_id})
        
        if result.get("errors"):
            return None
        
        versions = result.get("data", {}).get("project", {}).get("versions", {}).get("items", [])
        if not versions:
            return None
        
        return versions[0].get("referencedObject")
    
    def _sample_project_elements(
        self,
        project_id: str,
        root_object_id: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Sample a limited number of elements from a project.
        
        Uses a shallow query to get diverse element types quickly.
        """
        query = """
        query SampleElements($projectId: String!, $objectId: String!, $limit: Int!) {
          project(id: $projectId) {
            object(id: $objectId) {
              children(limit: $limit, depth: 2) {
                objects {
                  id
                  speckleType
                  data
                }
              }
            }
          }
        }
        """
        
        result = self.graphql_client.query(query, {
            "projectId": project_id,
            "objectId": root_object_id,
            "limit": limit
        })
        
        if result.get("errors"):
            return []
        
        objects = result.get("data", {}).get("project", {}).get("object", {}).get("children", {}).get("objects", [])
        return objects
    
    def _format_results(
        self,
        top_projects: List[ProjectMaterialScore],
        material: str,
        total_projects: int
    ) -> str:
        """Format results as readable text"""
        lines = [
            f"Found {len(top_projects)} project(s) containing '{material}' (searched {total_projects} projects):",
            ""
        ]
        
        for i, project in enumerate(top_projects, 1):
            lines.append(f"{i}. {project.project_name} (ID: {project.project_id})")
            lines.append(f"   Score: {project.score:.2f} | Matches: {project.match_count}/{project.sample_size} elements")
            lines.append(f"   Confidence: {project.confidence} | Materials: {', '.join(project.materials_found[:5])}")
            if len(project.materials_found) > 5:
                lines.append(f"   ... and {len(project.materials_found) - 5} more")
            lines.append("")
        
        return "\n".join(lines)

