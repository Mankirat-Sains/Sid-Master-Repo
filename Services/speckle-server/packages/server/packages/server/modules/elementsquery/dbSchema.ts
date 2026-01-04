import { buildTableHelper } from '@/modules/core/dbSchema'
import type { Optional } from '@speckle/shared'

/**
 * Database schema helper for the elements_queryable table
 * 
 * Usage:
 * - ElementsQueryable.name - Table name
 * - ElementsQueryable.col.element_id - Get column names
 * - ElementsQueryable.knex() - Get knex() instance for this table
 * - ElementsQueryable.withoutTablePrefix.col.element_id - Column without table prefix
 */
export const ElementsQueryable = buildTableHelper(
  'elements_queryable',
  [
    'element_id',
    'stream_id',
    'project_id',
    'project_name',
    'model_id',
    'model_name',
    'version_id',
    'version_message',
    'root_object_id',
    'speckle_type',
    'created_at',
    'total_children_count',
    'ifc_type',
    'element_name',
    'material',
    'building_storey',
    'tag',
    'revit_type',
    'revit_family',
    'revit_category',
    'revit_material',
    'volume',
    'length',
    'width',
    'height',
    'area',
    'level',
    'full_data',
    'last_updated'
  ]
)
