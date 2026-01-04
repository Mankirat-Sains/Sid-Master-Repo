"""
Script to identify and extract Speckle RenderMaterial data from elements_queryable CSV.

This script helps identify:
1. Elements that have RenderMaterial data (common Speckle visual properties)
2. Distinguishes between connector-specific materials (Revit, etc.) and Speckle's common RenderMaterial

Note: The CSV only contains flattened columns. To get actual RenderMaterial properties 
(diffuse, opacity, metalness, roughness, emissive), you need to:
- Query the database directly with full_data column
- Or access the actual Speckle objects via the API
"""

import csv
import json
from collections import defaultdict
from typing import Dict, List, Set

def parse_csv(csv_path: str) -> List[Dict]:
    """Parse the CSV file and return rows as dictionaries."""
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def identify_render_material_entries(rows: List[Dict]) -> Dict:
    """
    Identify entries that might contain RenderMaterial data.
    
    Returns a dictionary with:
    - render_material_types: Elements with speckle_type containing RenderMaterial
    - material_entries: Material objects that might reference RenderMaterial
    - elements_with_materials: Elements that reference materials
    """
    results = {
        'render_material_types': [],
        'material_entries': [],
        'elements_with_materials': [],
        'material_references': defaultdict(list)
    }
    
    # Track all material entries
    material_elements = {}
    
    for row in rows:
        speckle_type = row.get('speckle_type', '') or ''
        material = row.get('material', '') or ''
        element_id = row.get('element_id', '')
        
        # Check if this is a RenderMaterial type (Speckle's common render material)
        if 'RenderMaterial' in speckle_type:
            results['render_material_types'].append({
                'element_id': element_id,
                'speckle_type': speckle_type,
                'material': material,
                'element_name': row.get('element_name', ''),
                'revit_material': row.get('revit_material', ''),
                'project_name': row.get('project_name', ''),
                'model_name': row.get('model_name', '')
            })
        
        # Track all Material entries (including RevitMaterial)
        if 'Material' in speckle_type:
            material_elements[element_id] = {
                'element_id': element_id,
                'speckle_type': speckle_type,
                'material': material,
                'element_name': row.get('element_name', ''),
                'revit_material': row.get('revit_material', ''),
                'is_revit': 'RevitMaterial' in speckle_type,
                'is_render_material': 'RenderMaterial' in speckle_type
            }
            results['material_entries'].append(material_elements[element_id])
        
        # Track elements that reference materials
        if material and material != 'NULL':
            # Check if material references a material element
            if material in [m['material'] for m in material_elements.values()]:
                results['elements_with_materials'].append({
                    'element_id': element_id,
                    'speckle_type': speckle_type,
                    'material': material,
                    'element_name': row.get('element_name', ''),
                    'revit_material': row.get('revit_material', ''),
                    'revit_type': row.get('revit_type', ''),
                    'revit_family': row.get('revit_family', ''),
                    'revit_category': row.get('revit_category', '')
                })
                results['material_references'][material].append(element_id)
    
    return results

def find_speckle_common_data(rows: List[Dict]) -> Dict:
    """
    Find Speckle's common visual data (RenderMaterial properties).
    
    Since the CSV doesn't include full_data, this identifies:
    1. Elements that likely have RenderMaterial
    2. Elements that reference materials (which may have RenderMaterial in full_data)
    """
    results = identify_render_material_entries(rows)
    
    # Additional analysis: find elements that might have renderMaterial property
    # in their full_data (we can't access it from CSV, but we can identify candidates)
    
    speckle_common_candidates = []
    for row in rows:
        speckle_type = row.get('speckle_type', '') or ''
        material = row.get('material', '') or ''
        
        # Elements that have geometry and materials likely have RenderMaterial
        if any(geo_type in speckle_type for geo_type in ['Mesh', 'Brep', 'Surface', 'Solid']):
            if material and material != 'NULL':
                speckle_common_candidates.append({
                    'element_id': row.get('element_id', ''),
                    'speckle_type': speckle_type,
                    'material': material,
                    'element_name': row.get('element_name', ''),
                    'note': 'Geometric element with material - likely has RenderMaterial in full_data'
                })
    
    results['speckle_common_candidates'] = speckle_common_candidates
    return results

def generate_report(results: Dict, output_path: str):
    """Generate a report of findings."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("SPECKLE RENDER MATERIAL ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("SUMMARY\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total RenderMaterial type entries: {len(results['render_material_types'])}\n")
        f.write(f"Total Material entries (all types): {len(results['material_entries'])}\n")
        f.write(f"Elements referencing materials: {len(results['elements_with_materials'])}\n")
        f.write(f"Geometric elements with materials (RenderMaterial candidates): {len(results['speckle_common_candidates'])}\n\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("RENDER MATERIAL TYPE ENTRIES\n")
        f.write("=" * 80 + "\n")
        if results['render_material_types']:
            for entry in results['render_material_types']:
                f.write(f"\nElement ID: {entry['element_id']}\n")
                f.write(f"  Speckle Type: {entry['speckle_type']}\n")
                f.write(f"  Material Name: {entry['material']}\n")
                f.write(f"  Element Name: {entry['element_name']}\n")
                f.write(f"  Revit Material: {entry['revit_material']}\n")
                f.write(f"  Project: {entry['project_name']}\n")
                f.write(f"  Model: {entry['model_name']}\n")
        else:
            f.write("\nNo RenderMaterial type entries found in CSV.\n")
            f.write("Note: RenderMaterial properties (diffuse, opacity, metalness, roughness, emissive)\n")
            f.write("are stored in the 'full_data' JSONB column, which is not included in this CSV.\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("ALL MATERIAL ENTRIES (Including Connector-Specific)\n")
        f.write("=" * 80 + "\n")
        revit_materials = [m for m in results['material_entries'] if m['is_revit']]
        speckle_materials = [m for m in results['material_entries'] if m['is_render_material']]
        other_materials = [m for m in results['material_entries'] 
                          if not m['is_revit'] and not m['is_render_material']]
        
        f.write(f"\nRevitMaterial entries: {len(revit_materials)}\n")
        f.write(f"RenderMaterial entries: {len(speckle_materials)}\n")
        f.write(f"Other Material entries: {len(other_materials)}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("HOW TO ACCESS RENDER MATERIAL PROPERTIES\n")
        f.write("=" * 80 + "\n")
        f.write("""
The CSV file only contains flattened columns. To access actual RenderMaterial properties
(diffuse, opacity, metalness, roughness, emissive), you need to:

1. QUERY THE DATABASE DIRECTLY:
   SELECT element_id, full_data->'renderMaterial' as render_material
   FROM elements_queryable
   WHERE full_data->'renderMaterial' IS NOT NULL;

2. OR USE THE GRAPHQL API:
   Query the elementsQuery with fullData field, then extract renderMaterial from the JSON.

3. OR ACCESS SPECKLE OBJECTS DIRECTLY:
   Use the Speckle API to fetch objects by element_id and access their renderMaterial property.

RenderMaterial properties structure:
{
  "name": "Steel",
  "diffuse": 4286545792,  // ARGB color as integer
  "opacity": 1.0,
  "metalness": 1.0,
  "roughness": 0.3,
  "emissive": 4278190080  // ARGB color as integer
}
        """)
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("ELEMENTS WITH MATERIALS (Potential RenderMaterial Usage)\n")
        f.write("=" * 80 + "\n")
        f.write(f"\nFound {len(results['elements_with_materials'])} elements that reference materials.\n")
        f.write("These elements likely have RenderMaterial properties in their full_data.\n")
        
        # Group by material
        f.write("\n" + "-" * 80 + "\n")
        f.write("MATERIAL REFERENCE COUNTS\n")
        f.write("-" * 80 + "\n")
        for material, element_ids in sorted(results['material_references'].items(), 
                                           key=lambda x: len(x[1]), reverse=True)[:20]:
            f.write(f"\n{material}: {len(element_ids)} elements\n")
            if len(element_ids) <= 5:
                f.write(f"  Element IDs: {', '.join(element_ids[:5])}\n")

def main():
    csv_path = r'c:\Users\shine\OneDrive\Desktop\elements_queryable.csv'
    output_path = r'c:\Users\shine\OneDrive\Desktop\render_material_analysis.txt'
    
    print(f"Reading CSV file: {csv_path}")
    rows = parse_csv(csv_path)
    print(f"Loaded {len(rows)} rows")
    
    print("Analyzing for RenderMaterial data...")
    results = find_speckle_common_data(rows)
    
    print("Generating report...")
    generate_report(results, output_path)
    
    print(f"\nAnalysis complete! Report saved to: {output_path}")
    print(f"\nSummary:")
    print(f"  - RenderMaterial type entries: {len(results['render_material_types'])}")
    print(f"  - Total Material entries: {len(results['material_entries'])}")
    print(f"  - Elements with materials: {len(results['elements_with_materials'])}")
    print(f"  - Geometric elements (RenderMaterial candidates): {len(results['speckle_common_candidates'])}")

if __name__ == '__main__':
    main()

