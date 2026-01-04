#!/usr/bin/env python3
"""
Find Member Sections using GraphQL MCP
Similar to find_member_sections.py but using GraphQL queries
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict

# Load environment
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

from python_client import create_graphql_client

# Configuration
SPECKLE_SERVER = "http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com"
TARGET_PROJECT_NAME = "S22_2022-0482-10_Central"

def find_project_by_name(client, project_name):
    """Find project by name using GraphQL"""
    query = """
    query {
      activeUser {
        projects {
          items {
            id
            name
            models {
              items {
                id
                name
                versions(limit: 1) {
                  items {
                    id
                    referencedObject
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    
    result = client.query(query)
    
    if result.get("errors"):
        print(f"❌ Query errors: {result['errors']}")
        return None
    
    projects = result.get("data", {}).get("activeUser", {}).get("projects", {}).get("items", [])
    
    for project in projects:
        if project_name in project.get("name", ""):
            print(f"✓ Found project: {project['name']} ({project['id']})")
            return project
    
    print(f"❌ Project '{project_name}' not found")
    return None

def extract_member_section(data_json: dict) -> dict:
    """Extract member section information from IFC data"""
    section_info = {
        'section': None,
        'type': None,
        'family': None,
        'material': None,
        'category': None,
        'ifc_type': None,
    }
    
    # Get IFC type
    section_info['ifc_type'] = data_json.get('ifcType') or data_json.get('speckle_type')
    
    # Check properties
    properties = data_json.get('properties', {})
    if isinstance(properties, dict):
        # Check various property locations
        attrs = properties.get('Attributes', {})
        if isinstance(attrs, dict):
            section_info['type'] = attrs.get('Type') or attrs.get('type')
            section_info['section'] = attrs.get('Section') or attrs.get('section') or section_info['type']
            section_info['family'] = attrs.get('Family') or attrs.get('family')
            section_info['category'] = attrs.get('Category') or attrs.get('category')
            section_info['material'] = attrs.get('Material') or attrs.get('material')
        
        # Check PropertySets
        prop_sets = properties.get('PropertySets', {})
        if isinstance(prop_sets, dict):
            for prop_set_name, prop_set in prop_sets.items():
                if isinstance(prop_set, dict):
                    # Look for section-related properties
                    for prop_name in ['Type', 'Section', 'Profile', 'Size', 'Member Size']:
                        if prop_name in prop_set:
                            section_info['section'] = str(prop_set[prop_name])
                            break
    
    # Check direct fields
    if not section_info['section']:
        section_info['section'] = data_json.get('type') or data_json.get('section') or data_json.get('profile')
    
    if not section_info['family']:
        section_info['family'] = data_json.get('family')
    
    if not section_info['material']:
        section_info['material'] = data_json.get('material')
    
    return section_info

def is_member(data_json: dict) -> bool:
    """Check if object is a beam, column, brace, or member"""
    if not isinstance(data_json, dict):
        return False
    
    ifc_type = (data_json.get('ifcType') or data_json.get('speckle_type') or '').upper()
    
    return any(x in ifc_type for x in ['BEAM', 'COLUMN', 'BRACE', 'MEMBER'])

def find_member_sections_in_object(client, project_id: str, object_id: str, depth: int = 5):
    """Find all member sections in an object's children tree"""
    query = """
    query GetObjectChildren($projectId: String!, $objectId: String!, $depth: Int!) {
      project(id: $projectId) {
        id
        name
        object(id: $objectId) {
          id
          speckleType
          data
          children(limit: 10000, depth: $depth) {
            totalCount
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
    
    variables = {
        "projectId": project_id,
        "objectId": object_id,
        "depth": depth
    }
    
    result = client.query(query, variables)
    
    if result.get("errors"):
        print(f"❌ Query errors: {result['errors']}")
        return []
    
    project_data = result.get("data", {}).get("project", {})
    object_data = project_data.get("object", {})
    children = object_data.get("children", {})
    objects = children.get("objects", [])
    
    member_sections = defaultdict(set)
    all_members = []
    
    print(f"  Processing {len(objects)} objects...")
    
    for obj in objects:
        data = obj.get("data")
        
        # Parse data if it's a string
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                continue
        
        if not isinstance(data, dict):
            continue
        
        # Check if it's a member
        if is_member(data):
            section_info = extract_member_section(data)
            section_info['id'] = obj.get('id')
            section_info['speckle_type'] = obj.get('speckleType')
            section_info['name'] = data.get('name', 'unnamed')
            
            all_members.append(section_info)
            
            if section_info['section']:
                member_sections[section_info['section']].add(section_info['id'])
    
    return all_members, member_sections

def main():
    print("=" * 80)
    print("MEMBER SECTIONS FINDER (GraphQL MCP)")
    print("=" * 80)
    print(f"Target Project: {TARGET_PROJECT_NAME}")
    
    # Get endpoint from environment
    endpoint = os.getenv("GRAPHQL_ENDPOINT")
    if not endpoint:
        # Construct from server URL
        endpoint = f"{SPECKLE_SERVER}/graphql"
    
    auth_token = os.getenv("GRAPHQL_AUTH_TOKEN")
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    print(f"\n[1] Connecting to GraphQL endpoint: {endpoint}")
    
    # Create GraphQL MCP client
    client = create_graphql_client(
        endpoint=endpoint,
        headers=headers if headers else None,
        allow_mutations=False
    )
    
    try:
        client.start()
        print("✓ GraphQL MCP client started")
        
        # Find project
        print(f"\n[2] Finding project: {TARGET_PROJECT_NAME}")
        project = find_project_by_name(client, TARGET_PROJECT_NAME)
        
        if project is None:
            return
        
        project_id = project['id']
        project_name = project['name']
        
        # Get first model
        models = project.get('models', {}).get('items', [])
        if not models:
            print("❌ No models found")
            return
        
        model = models[0]
        model_id = model['id']
        model_name = model['name']
        versions = model.get('versions', {}).get('items', [])
        
        if not versions:
            print("❌ No versions found")
            return
        
        root_object_id = versions[0]['referencedObject']
        print(f"\n[3] Root object: {root_object_id}")
        print(f"    Model: {model_name}")
        
        # Find member sections
        print(f"\n[4] Finding member sections (this may take a while)...")
        all_members, member_sections = find_member_sections_in_object(
            client, project_id, root_object_id, depth=5
        )
        
        # Print results
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        
        print(f"\n📐 MEMBER SECTIONS FOUND:")
        print("-" * 80)
        sorted_sections = sorted(member_sections.items(), key=lambda x: len(x[1]), reverse=True)
        
        for section, ids in sorted_sections:
            print(f"  • {section}: {len(ids)} instances")
        
        if not member_sections:
            print("  ⚠️  No member sections found in type/parameters")
            print("  Showing sample members:")
            for member in all_members[:20]:
                print(f"    - {member['name']} ({member['speckle_type']})")
                if member.get('type'):
                    print(f"      Type: {member['type']}")
                if member.get('ifc_type'):
                    print(f"      IFC Type: {member['ifc_type']}")
        
        print(f"\nSummary:")
        print(f"  • Unique member sections: {len(member_sections)}")
        print(f"  • Total members analyzed: {len(all_members)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.stop()
        print("\n✓ GraphQL MCP client stopped")

if __name__ == "__main__":
    main()