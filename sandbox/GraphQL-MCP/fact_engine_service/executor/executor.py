"""Fact executor - executes FactPlans using extractors"""
import time
import json
import logging
from typing import Dict, Any, List, Optional
from collections import defaultdict

from models.fact_plan import FactPlan, Filter, Aggregation
from models.fact_result import FactResult, ProjectFacts, ElementFacts, FactValue, Evidence
from executor.registry import registry
from executor.caching import RequestCache
from db.connection import db
from db.queries import build_candidate_discovery_query
from db.graphql_client import graphql_client
from extractors.project_summary import ProjectSummaryExtractor

logger = logging.getLogger(__name__)


class FactExecutor:
    """Executes FactPlans to extract facts"""
    
    def __init__(self, use_graphql: bool = False):
        self.use_graphql = use_graphql
        self.cache = RequestCache()
    
    def execute(self, plan: FactPlan) -> FactResult:
        """
        Execute a FactPlan and return extracted facts.
        
        This implements the two-phase execution strategy:
        1. Phase 1: Candidate Discovery (SQL/GraphQL, cheap)
        2. Phase 2: Fact Confirmation (Python, precise)
        """
        logger.info("=" * 80)
        logger.info("EXECUTOR: Starting execution phase")
        logger.info(f"EXECUTOR: Using GraphQL: {self.use_graphql}")
        start_time = time.time()
        
        # Phase 1: Candidate Discovery
        logger.info("EXECUTOR: Phase 1 - Candidate Discovery")
        candidates = self._discover_candidates(plan)
        logger.info(f"EXECUTOR: Phase 1 complete - Found {len(candidates)} candidate elements")
        
        if candidates:
            logger.debug(f"EXECUTOR: Sample candidate: {candidates[0] if len(candidates) > 0 else 'N/A'}")
        
        # Phase 2: Fact Confirmation
        logger.info("EXECUTOR: Phase 2 - Fact Confirmation")
        fact_graph = self._extract_facts(candidates, plan)
        logger.info(f"EXECUTOR: Phase 2 complete - Extracted facts for {len(fact_graph)} projects")
        
        # Build result
        execution_time = (time.time() - start_time) * 1000  # ms
        logger.info(f"EXECUTOR: Computing global facts")
        global_facts = self._compute_global_facts(fact_graph, plan)
        logger.info(f"EXECUTOR: Global facts computed: {list(global_facts.keys())}")
        
        result = FactResult(
            projects=fact_graph,
            global_facts=global_facts,
            execution_time_ms=execution_time,
            total_elements_processed=len(candidates)
        )
        
        logger.info(f"EXECUTOR: Execution complete - {execution_time:.2f}ms, {len(candidates)} elements processed, {len(fact_graph)} projects")
        logger.info("=" * 80)
        
        return result
    
    def _discover_candidates(self, plan: FactPlan) -> List[Dict[str, Any]]:
        """Phase 1: Discover candidate elements using coarse filters"""
        logger.info("EXECUTOR: Starting candidate discovery")
        logger.info(f"EXECUTOR: Plan has {len(plan.filters)} filters")
        
        candidates = []
        
        if self.use_graphql and graphql_client.client:
            logger.info("EXECUTOR: Using GraphQL for candidate discovery")
            candidates = self._discover_candidates_graphql(plan)
        else:
            logger.info("EXECUTOR: Using SQL for candidate discovery")
            candidates = self._discover_candidates_sql(plan)
        
        logger.info(f"EXECUTOR: Candidate discovery complete - {len(candidates)} candidates found")
        return candidates
    
    def _discover_candidates_sql(self, plan: FactPlan) -> List[Dict[str, Any]]:
        """Discover candidates using SQL"""
        logger.info("EXECUTOR: SQL discovery - checking psycopg2 availability")
        # Check if psycopg2 is available
        try:
            from db.connection import HAS_PSYCOPG2
            if not HAS_PSYCOPG2:
                logger.error("EXECUTOR: SQL discovery requires psycopg2. Install with: pip install psycopg2-binary")
                logger.error("EXECUTOR: Or use GraphQL by setting GRAPHQL_ENDPOINT in .env")
                return []
        except ImportError:
            logger.error("EXECUTOR: Cannot check psycopg2 availability")
            return []
        
        logger.info("EXECUTOR: SQL discovery - building coarse filters from plan")
        # Build coarse filters from plan
        speckle_types = []
        string_filters = {}
        
        for filter_obj in plan.filters:
            logger.debug(f"EXECUTOR: Processing filter - fact: {filter_obj.fact}, op: {filter_obj.op}, value: {filter_obj.value}")
            extractor = registry.get_extractor(filter_obj.fact)
            if extractor:
                sql_filter = extractor.coarse_filter_sql(filter_obj.op, filter_obj.value)
                if sql_filter:
                    # Extract type hints from filter
                    if filter_obj.fact == "element_type":
                        speckle_types.append(filter_obj.value)
                        logger.debug(f"EXECUTOR: Added speckle type filter: {filter_obj.value}")
            else:
                logger.warning(f"EXECUTOR: No extractor found for fact: {filter_obj.fact}")
        
        logger.info(f"EXECUTOR: SQL discovery - built filters: speckle_types={speckle_types}, string_filters={string_filters}")
        
        # Build and execute query
        logger.info("EXECUTOR: SQL discovery - building query")
        query, params = build_candidate_discovery_query(
            speckle_types=speckle_types if speckle_types else None,
            string_filters=string_filters if string_filters else None
        )
        logger.debug(f"EXECUTOR: SQL discovery - query built with {len(params)} parameters")
        
        candidates = []
        try:
            logger.info("EXECUTOR: SQL discovery - executing query")
            with db.sync_connection() as conn:
                cursor = conn.cursor()
                try:
                    # Convert named parameters to positional for psycopg2
                    # Replace %(param_name)s with %s and build param list
                    param_values = []
                    param_names = []
                    
                    # Extract parameter names from query
                    import re
                    param_pattern = r'%\((\w+)\)s'
                    matches = re.findall(param_pattern, query)
                    
                    # Build ordered parameter list
                    for match in matches:
                        if match in params and match not in param_names:
                            param_names.append(match)
                            param_values.append(params[match])
                    
                    # Replace named params with %s
                    query_psycopg = re.sub(param_pattern, '%s', query)
                    
                    # Execute with proper parameter binding
                    cursor.execute(query_psycopg, param_values)
                    rows = cursor.fetchall()
                    logger.info(f"EXECUTOR: SQL discovery - query returned {len(rows)} rows")
                    
                    for row in rows:
                        candidates.append({
                            "id": row[0],
                            "speckleType": row[1],
                            "data": row[2] if isinstance(row[2], dict) else {},
                            "root_id": row[3],
                            "root_name": row[4],
                            "root_number": row[5]
                        })
                finally:
                    cursor.close()
        except ImportError as e:
            logger.error(f"EXECUTOR: SQL discovery requires psycopg2: {e}")
            return []
        except Exception as e:
            logger.error(f"EXECUTOR: SQL discovery error: {e}", exc_info=True)
        
        logger.info(f"EXECUTOR: SQL discovery complete - {len(candidates)} candidates")
        return candidates
    
    def _discover_candidates_graphql(self, plan: FactPlan) -> List[Dict[str, Any]]:
        """
        Scalable GraphQL discovery with parallel processing:
        1. Get all projects (one query)
        2. For each project in parallel: get root → ONE children query with filter
        3. Server filters by speckleType (not fetching everything)
        4. Material filtering happens client-side on filtered results
        """
        import concurrent.futures
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        logger.info("EXECUTOR: GraphQL discovery - fetching projects")
        # Get projects first
        # For testing, limit to very small number; increase for production
        max_projects = 1  # Start with 1 for testing, can increase to 1000+
        projects = graphql_client.get_projects(limit=max_projects)
        
        if not projects:
            logger.warning("EXECUTOR: GraphQL discovery - No projects found")
            return []
        
        logger.info(f"EXECUTOR: GraphQL discovery - Processing {len(projects)} projects (limited to {max_projects} for testing)")
        
        # Extract speckleType filter from plan
        logger.info("EXECUTOR: GraphQL discovery - extracting element type filter from plan")
        speckle_type_filter = None
        for filter_obj in plan.filters:
            if filter_obj.fact == "element_type":
                # Map element type to Speckle type pattern
                elem_type = filter_obj.value.lower()
                logger.debug(f"EXECUTOR: GraphQL discovery - mapping element type '{elem_type}' to Speckle type")
                if elem_type == "column":
                    speckle_type_filter = "Column"
                elif elem_type == "beam":
                    speckle_type_filter = "Beam"
                elif elem_type == "wall":
                    speckle_type_filter = "Wall"
                elif elem_type == "slab":
                    speckle_type_filter = "Slab"
                elif elem_type == "brace":
                    speckle_type_filter = "Brace"
                logger.info(f"EXECUTOR: GraphQL discovery - using Speckle type filter: {speckle_type_filter}")
                break
        
        if not speckle_type_filter:
            logger.info("EXECUTOR: GraphQL discovery - no element type filter found, will fetch all types")
        
        candidates = []
        project_names = {p.get("id"): p.get("name") for p in projects}
        logger.debug(f"EXECUTOR: GraphQL discovery - project names: {project_names}")
        
        # Process projects in parallel (up to 20 concurrent)
        def process_project(project: Dict[str, Any]) -> List[Dict[str, Any]]:
            project_id = project.get("id")
            project_name = project.get("name", project_id)
            if not project_id:
                logger.warning(f"EXECUTOR: GraphQL discovery - project missing ID, skipping")
                return []
            
            try:
                logger.info(f"EXECUTOR: GraphQL discovery - processing project: {project_name} ({project_id})")
                # ONE query per project with server-side filtering
                logger.debug(f"EXECUTOR: GraphQL discovery - calling discover_candidates_canonical for project {project_id}")
                objects = graphql_client.discover_candidates_canonical(
                    project_id=project_id,
                    speckle_type_filter=speckle_type_filter
                )
                
                logger.info(f"EXECUTOR: GraphQL discovery - project {project_name}: found {len(objects)} objects")
                
                if not objects:
                    logger.debug(f"EXECUTOR: GraphQL discovery - project {project_name}: no matching elements")
                    return []  # No matching elements in this project
                
                # Add project context
                result = []
                for obj in objects:
                    # Handle data field - it might be a string (JSON) or dict
                    data = obj.get("data", {})
                    if isinstance(data, str):
                        try:
                            data = json.loads(data)
                        except (json.JSONDecodeError, TypeError):
                            logger.debug(f"EXECUTOR: GraphQL discovery - failed to parse JSON data for object {obj.get('id')}")
                            data = {}
                    
                    result.append({
                        "id": obj.get("id"),
                        "speckleType": obj.get("speckleType", ""),
                        "data": data,
                        "root_id": obj.get("root_id") or project_id,
                        "root_name": project_names.get(project_id),
                        "root_number": project.get("number")
                    })
                
                logger.info(f"EXECUTOR: GraphQL discovery - project {project_name}: processed {len(result)} candidates")
                return result
            except Exception as e:
                logger.warning(f"EXECUTOR: GraphQL discovery - error processing project {project_id}: {e}", exc_info=True)
                return []
        
        # For initial testing, process sequentially to see errors clearly
        # Once working, switch to parallel
        use_parallel = False  # Set to True once basic flow works
        
        if use_parallel:
            # Parallel processing with thread pool
            max_workers = min(5, len(projects))
            completed = 0
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_project = {
                    executor.submit(process_project, project): project 
                    for project in projects
                }
                
                for future in as_completed(future_to_project, timeout=300):
                    completed += 1
                    try:
                        project_candidates = future.result(timeout=60)
                        candidates.extend(project_candidates)
                        logger.info(f"Processed {completed}/{len(projects)} projects, found {len(candidates)} candidates so far")
                    except concurrent.futures.TimeoutError:
                        project = future_to_project[future]
                        logger.warning(f"Timeout processing project {project.get('id')} - skipping")
                    except Exception as e:
                        project = future_to_project[future]
                        logger.warning(f"Error processing project {project.get('id')}: {e}")
        else:
            # Sequential processing for debugging
            logger.info("EXECUTOR: GraphQL discovery - using sequential processing (parallel disabled)")
            for i, project in enumerate(projects, 1):
                logger.info(f"EXECUTOR: GraphQL discovery - Processing project {i}/{len(projects)}: {project.get('name', project.get('id'))}")
                try:
                    project_candidates = process_project(project)
                    candidates.extend(project_candidates)
                    logger.info(f"EXECUTOR: GraphQL discovery - Project {i} complete: found {len(project_candidates)} candidates (total: {len(candidates)})")
                except Exception as e:
                    logger.error(f"EXECUTOR: GraphQL discovery - error processing project {project.get('id')}: {e}", exc_info=True)
        
        logger.info(f"EXECUTOR: GraphQL discovery complete: {len(candidates)} candidates across {len(projects)} projects")
        return candidates
    
    def _extract_facts(
        self,
        candidates: List[Dict[str, Any]],
        plan: FactPlan
    ) -> Dict[str, ProjectFacts]:
        """Phase 2: Extract facts from candidates"""
        logger.info("EXECUTOR: Fact extraction - starting")
        logger.info(f"EXECUTOR: Fact extraction - processing {len(candidates)} candidates")
        
        fact_graph: Dict[str, ProjectFacts] = {}
        
        # Determine which facts we need to extract
        logger.info("EXECUTOR: Fact extraction - determining needed facts")
        needed_facts = set()
        for filter_obj in plan.filters:
            needed_facts.add(filter_obj.fact)
        for agg in plan.aggregations:
            if agg.fact:
                needed_facts.add(agg.fact)
            if agg.by:
                needed_facts.add(agg.by)
        needed_facts.update(plan.outputs)
        
        logger.info(f"EXECUTOR: Fact extraction - needed facts: {list(needed_facts)}")
        
        # Get extractors for needed facts
        extractors = registry.get_extractors_for_facts(list(needed_facts))
        logger.info(f"EXECUTOR: Fact extraction - found {len(extractors)} extractors")
        for ext in extractors:
            logger.debug(f"EXECUTOR: Fact extraction - extractor: {ext.fact_name}")
        
        # Process each candidate
        matched_count = 0
        for idx, candidate in enumerate(candidates):
            if (idx + 1) % 10 == 0 or idx == 0:
                logger.debug(f"EXECUTOR: Fact extraction - processing candidate {idx + 1}/{len(candidates)}")
            element_id = candidate.get("id")
            project_id = candidate.get("root_id") or "unknown"
            
            # Initialize project in graph if needed
            if project_id not in fact_graph:
                fact_graph[project_id] = ProjectFacts(
                    project_id=project_id,
                    project_name=candidate.get("root_name"),
                    project_number=candidate.get("root_number")
                )
            
            project = fact_graph[project_id]
            
            # Extract facts for this element
            element_facts = {}
            for extractor in extractors:
                fact_name = extractor.fact_name
                
                # Check cache first
                if self.cache.has(element_id, fact_name):
                    fact_value = self.cache.get(element_id, fact_name)
                    logger.debug(f"EXECUTOR: Fact extraction - using cached value for {fact_name} on element {element_id}")
                else:
                    # Extract fact
                    logger.debug(f"EXECUTOR: Fact extraction - extracting {fact_name} from element {element_id}")
                    if self.use_graphql:
                        fact_value = extractor.extract_from_graphql(candidate)
                    else:
                        fact_value = extractor.extract(candidate)
                    
                    # Cache it
                    self.cache.set(element_id, fact_name, fact_value)
                
                # Convert FactValue to dict
                if hasattr(fact_value, 'model_dump'):
                    element_facts[fact_name] = fact_value.model_dump()
                elif hasattr(fact_value, 'dict'):
                    element_facts[fact_name] = fact_value.dict()
                else:
                    element_facts[fact_name] = fact_value
                
                # Log extracted fact value
                fact_val = element_facts[fact_name]
                if isinstance(fact_val, dict):
                    fact_val_display = fact_val.get("value", "N/A")
                else:
                    fact_val_display = fact_val
                logger.debug(f"EXECUTOR: Fact extraction - {fact_name} = {fact_val_display} for element {element_id}")
            
            # Apply filters
            logger.debug(f"EXECUTOR: Fact extraction - checking filters for element {element_id}")
            if self._matches_filters(element_facts, plan.filters):
                matched_count += 1
                logger.debug(f"EXECUTOR: Fact extraction - element {element_id} matches all filters")
                # Aggregate into project facts
                self._aggregate_element_facts(project, element_facts)
            else:
                logger.debug(f"EXECUTOR: Fact extraction - element {element_id} does not match filters, skipping")
        
        logger.info(f"EXECUTOR: Fact extraction - {matched_count}/{len(candidates)} candidates matched filters")
        
        # Compute project summaries
        logger.info("EXECUTOR: Fact extraction - computing project summaries")
        summary_extractor = ProjectSummaryExtractor()
        for project_id, project in fact_graph.items():
            logger.debug(f"EXECUTOR: Fact extraction - computing summary for project {project_id} ({project.project_name})")
            # Get all elements for this project (simplified - would need to track)
            project.summary = summary_extractor.compute_project_summary([], {})
            logger.debug(f"EXECUTOR: Fact extraction - project {project_id} has {len(project.elements)} element types")
        
        logger.info(f"EXECUTOR: Fact extraction complete - {len(fact_graph)} projects with facts")
        return fact_graph
    
    def _matches_filters(self, element_facts: Dict[str, Any], filters: List[Filter]) -> bool:
        """Check if element facts match all filters"""
        for filter_obj in filters:
            fact_value = element_facts.get(filter_obj.fact)
            if not fact_value:
                logger.debug(f"EXECUTOR: Filter check - fact '{filter_obj.fact}' not found in element facts")
                return False
            
            # Extract actual value from FactValue dict
            value = fact_value.get("value") if isinstance(fact_value, dict) else fact_value
            
            # Apply operator
            matches = self._apply_filter(value, filter_obj.op, filter_obj.value)
            logger.debug(f"EXECUTOR: Filter check - {filter_obj.fact} {filter_obj.op} {filter_obj.value}: value={value}, matches={matches}")
            if not matches:
                return False
        
        return True
    
    def _apply_filter(self, value: Any, op: str, filter_value: Any) -> bool:
        """Apply a filter operator"""
        if op == "=":
            return str(value).lower() == str(filter_value).lower()
        elif op == "!=":
            return str(value).lower() != str(filter_value).lower()
        elif op == "in":
            return str(value).lower() in [str(v).lower() for v in filter_value]
        elif op == "not_in":
            return str(value).lower() not in [str(v).lower() for v in filter_value]
        elif op == "contains":
            return str(filter_value).lower() in str(value).lower()
        elif op == "not_contains":
            return str(filter_value).lower() not in str(value).lower()
        elif op == ">":
            return float(value) > float(filter_value)
        elif op == "<":
            return float(value) < float(filter_value)
        elif op == ">=":
            return float(value) >= float(filter_value)
        elif op == "<=":
            return float(value) <= float(filter_value)
        return False
    
    def _aggregate_element_facts(self, project: ProjectFacts, element_facts: Dict[str, Any]):
        """Aggregate element facts into project structure"""
        element_type = element_facts.get("element_type", {}).get("value", "unknown")
        material = element_facts.get("material", {}).get("value", "unknown")
        
        # Initialize nested structure
        if element_type not in project.elements:
            project.elements[element_type] = {}
        
        if material not in project.elements[element_type]:
            project.elements[element_type][material] = 0
        
        project.elements[element_type][material] += 1
        
        # Track systems
        system_role = element_facts.get("system_role", {}).get("value")
        if system_role:
            if isinstance(system_role, list):
                for sys in system_role:
                    project.systems[sys] = True
            else:
                project.systems[system_role] = True
    
    def _compute_global_facts(
        self,
        fact_graph: Dict[str, ProjectFacts],
        plan: FactPlan
    ) -> Dict[str, Any]:
        """Compute global-level aggregations"""
        logger.info(f"EXECUTOR: Global facts - computing {len(plan.aggregations)} aggregations")
        global_facts = {}
        
        for agg in plan.aggregations:
            logger.debug(f"EXECUTOR: Global facts - processing aggregation: type={agg.type}, fact={agg.fact}, by={agg.by}")
            if agg.type == "count" and not agg.by:
                # Global count
                total = sum(
                    sum(sum(counts.values()) for counts in proj.elements.values())
                    for proj in fact_graph.values()
                )
                global_facts["total_count"] = total
                logger.info(f"EXECUTOR: Global facts - computed total_count: {total}")
        
        logger.info(f"EXECUTOR: Global facts - computed {len(global_facts)} global facts")
        return global_facts

