import type { Knex } from 'knex'
import { ElementsQueryable } from '../dbSchema'

/**
 * Type representing a row from the elements_queryable table
 */
export type QueryableElementRecord = {
  element_id: string
  stream_id: string
  project_id: string
  project_name: string | null
  model_id: string | null
  model_name: string | null
  version_id: string | null
  version_message: string | null
  root_object_id: string | null
  speckle_type: string | null
  created_at: Date | null
  total_children_count: number | null
  ifc_type: string | null
  element_name: string | null
  material: string | null
  building_storey: string | null
  tag: string | null
  revit_type: string | null
  revit_family: string | null
  revit_category: string | null
  revit_material: string | null
  volume: number | null
  length: number | null
  width: number | null
  height: number | null
  area: number | null
  level: string | null
  full_data: Record<string, unknown> | null
  last_updated: Date
}

/**
 * Parameters for querying elements by material
 */
export type ElementsByMaterialParams = {
  projectId?: string
  material: string
  ifcType?: string
  limit?: number
}

/**
 * Parameters for querying elements by storey
 */
export type ElementsByStoreyParams = {
  projectId?: string
  storey: string
  ifcType?: string
  limit?: number
}

/**
 * Parameters for querying elements by volume range
 */
export type ElementsByVolumeParams = {
  projectId?: string
  minVolume?: number
  maxVolume?: number
  ifcType?: string
  limit?: number
}

/**
 * Parameters for complex multi-filter query
 */
export type ElementsQueryParams = {
  projectId?: string
  ifcType?: string
  material?: string
  storey?: string
  minVolume?: number
  maxVolume?: number
  level?: string
  limit?: number
}

/**
 * Parameters for counting elements
 */
export type CountElementsParams = {
  projectId?: string
  ifcType?: string
  material?: string
}

/**
 * Factory function to get elements by material
 */
export const getElementsByMaterialFactory =
  (deps: { db: Knex }) =>
  async (params: ElementsByMaterialParams): Promise<QueryableElementRecord[]> => {
    const { projectId, material, ifcType, limit = 100 } = params

    let query = ElementsQueryable.knex(deps.db).select('*')

    if (projectId) {
      query = query.where(ElementsQueryable.col.project_id, projectId)
    }

    // Search in both material and revit_material fields
    query = query.where((builder) => {
      builder
        .where(ElementsQueryable.col.material, 'ILIKE', `%${material}%`)
        .orWhere(ElementsQueryable.col.revit_material, 'ILIKE', `%${material}%`)
    })

    if (ifcType) {
      query = query.where(ElementsQueryable.col.ifc_type, ifcType)
    }

    query = query.limit(limit)

    return await query
  }

/**
 * Factory function to get elements by storey
 */
export const getElementsByStoreyFactory =
  (deps: { db: Knex }) =>
  async (params: ElementsByStoreyParams): Promise<QueryableElementRecord[]> => {
    const { projectId, storey, ifcType, limit = 100 } = params

    let query = ElementsQueryable.knex(deps.db).select('*')

    if (projectId) {
      query = query.where(ElementsQueryable.col.project_id, projectId)
    }

    query = query.where(ElementsQueryable.col.building_storey, storey)

    if (ifcType) {
      query = query.where(ElementsQueryable.col.ifc_type, ifcType)
    }

    query = query.limit(limit)

    return await query
  }

/**
 * Factory function to get elements by volume range
 */
export const getElementsByVolumeFactory =
  (deps: { db: Knex }) =>
  async (params: ElementsByVolumeParams): Promise<QueryableElementRecord[]> => {
    const { projectId, minVolume, maxVolume, ifcType, limit = 100 } = params

    let query = ElementsQueryable.knex(deps.db).select('*')

    if (projectId) {
      query = query.where(ElementsQueryable.col.project_id, projectId)
    }

    if (minVolume !== undefined) {
      query = query.where(ElementsQueryable.col.volume, '>=', minVolume)
    }

    if (maxVolume !== undefined) {
      query = query.where(ElementsQueryable.col.volume, '<=', maxVolume)
    }

    if (ifcType) {
      query = query.where(ElementsQueryable.col.ifc_type, ifcType)
    }

    query = query.limit(limit)

    return await query
  }

/**
 * Factory function for complex multi-filter query
 */
export const getElementsQueryFactory =
  (deps: { db: Knex }) =>
  async (params: ElementsQueryParams): Promise<QueryableElementRecord[]> => {
    const {
      projectId,
      ifcType,
      material,
      storey,
      minVolume,
      maxVolume,
      level,
      limit = 100
    } = params

    let query = ElementsQueryable.knex(deps.db).select('*')

    if (projectId) {
      query = query.where(ElementsQueryable.col.project_id, projectId)
    }

    if (ifcType) {
      query = query.where(ElementsQueryable.col.ifc_type, ifcType)
    }

    if (material) {
      query = query.where((builder) => {
        builder
          .where(ElementsQueryable.col.material, 'ILIKE', `%${material}%`)
          .orWhere(ElementsQueryable.col.revit_material, 'ILIKE', `%${material}%`)
      })
    }

    if (storey) {
      query = query.where(ElementsQueryable.col.building_storey, storey)
    }

    if (minVolume !== undefined) {
      query = query.where(ElementsQueryable.col.volume, '>=', minVolume)
    }

    if (maxVolume !== undefined) {
      query = query.where(ElementsQueryable.col.volume, '<=', maxVolume)
    }

    if (level) {
      query = query.where(ElementsQueryable.col.level, level)
    }

    query = query.limit(limit)

    return await query
  }

/**
 * Factory function to count elements
 */
export const countElementsFactory =
  (deps: { db: Knex }) =>
  async (params: CountElementsParams): Promise<number> => {
    const { projectId, ifcType, material } = params

    let query = ElementsQueryable.knex(deps.db).count('* as count')

    if (projectId) {
      query = query.where(ElementsQueryable.col.project_id, projectId)
    }

    if (ifcType) {
      query = query.where(ElementsQueryable.col.ifc_type, ifcType)
    }

    if (material) {
      query = query.where((builder) => {
        builder
          .where(ElementsQueryable.col.material, 'ILIKE', `%${material}%`)
          .orWhere(ElementsQueryable.col.revit_material, 'ILIKE', `%${material}%`)
      })
    }

    const [result] = await query
    return parseInt((result as { count: string }).count, 10)
  }
