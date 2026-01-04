import type { Resolvers } from '@/modules/core/graph/generated/graphql'
import { getProjectDbClient } from '@/modules/multiregion/utils/dbSelector'
import {
  getElementsByMaterialFactory,
  getElementsByStoreyFactory,
  getElementsByVolumeFactory,
  getElementsQueryFactory,
  countElementsFactory,
  type QueryableElementRecord
} from '../../repositories/elementsQuery'

/**
 * Transform database record to GraphQL QueryableElement type
 */
function transformElement(record: QueryableElementRecord) {
  return {
    elementId: record.element_id,
    streamId: record.stream_id,
    projectId: record.project_id,
    modelId: record.model_id || null,
    versionId: record.version_id || null,
    rootObjectId: record.root_object_id || null,
    projectName: record.project_name || null,
    modelName: record.model_name || null,
    versionMessage: record.version_message || null,
    speckleType: record.speckle_type || null,
    createdAt: record.created_at || null,
    totalChildrenCount: record.total_children_count || null,
    ifcType: record.ifc_type || null,
    elementName: record.element_name || null,
    material: record.material || null,
    buildingStorey: record.building_storey || null,
    tag: record.tag || null,
    revitType: record.revit_type || null,
    revitFamily: record.revit_family || null,
    revitCategory: record.revit_category || null,
    revitMaterial: record.revit_material || null,
    volume: record.volume ? parseFloat(record.volume.toString()) : null,
    length: record.length ? parseFloat(record.length.toString()) : null,
    width: record.width ? parseFloat(record.width.toString()) : null,
    height: record.height ? parseFloat(record.height.toString()) : null,
    area: record.area ? parseFloat(record.area.toString()) : null,
    level: record.level || null,
    fullData: record.full_data || null
  }
}

export default {
  Query: {
    async elementsByMaterial(_parent, args, _context) {
      const { projectId, material, ifcType, limit } = args

      // If projectId is provided, use the project's database (multi-region support)
      // Otherwise, use the default database
      const db = projectId
        ? await getProjectDbClient({ projectId })
        : await getProjectDbClient({ projectId: undefined })

      const getElementsByMaterial = getElementsByMaterialFactory({ db })
      const records = await getElementsByMaterial({
        projectId: projectId || undefined,
        material,
        ifcType: ifcType || undefined,
        limit: limit || undefined
      })

      return records.map(transformElement)
    },

    async elementsByStorey(_parent, args, _context) {
      const { projectId, storey, ifcType, limit } = args

      const db = projectId
        ? await getProjectDbClient({ projectId })
        : await getProjectDbClient({ projectId: undefined })

      const getElementsByStorey = getElementsByStoreyFactory({ db })
      const records = await getElementsByStorey({
        projectId: projectId || undefined,
        storey,
        ifcType: ifcType || undefined,
        limit: limit || undefined
      })

      return records.map(transformElement)
    },

    async elementsByVolume(_parent, args, _context) {
      const { projectId, minVolume, maxVolume, ifcType, limit } = args

      const db = projectId
        ? await getProjectDbClient({ projectId })
        : await getProjectDbClient({ projectId: undefined })

      const getElementsByVolume = getElementsByVolumeFactory({ db })
      const records = await getElementsByVolume({
        projectId: projectId || undefined,
        minVolume: minVolume || undefined,
        maxVolume: maxVolume || undefined,
        ifcType: ifcType || undefined,
        limit: limit || undefined
      })

      return records.map(transformElement)
    },

    async elementsQuery(_parent, args, _context) {
      const {
        projectId,
        ifcType,
        material,
        storey,
        minVolume,
        maxVolume,
        level,
        limit
      } = args

      const db = projectId
        ? await getProjectDbClient({ projectId })
        : await getProjectDbClient({ projectId: undefined })

      const getElementsQuery = getElementsQueryFactory({ db })
      const records = await getElementsQuery({
        projectId: projectId || undefined,
        ifcType: ifcType || undefined,
        material: material || undefined,
        storey: storey || undefined,
        minVolume: minVolume || undefined,
        maxVolume: maxVolume || undefined,
        level: level || undefined,
        limit: limit || undefined
      })

      return records.map(transformElement)
    },

    async countElements(_parent, args, _context) {
      const { projectId, ifcType, material } = args

      const db = projectId
        ? await getProjectDbClient({ projectId })
        : await getProjectDbClient({ projectId: undefined })

      const countElements = countElementsFactory({ db })
      return await countElements({
        projectId: projectId || undefined,
        ifcType: ifcType || undefined,
        material: material || undefined
      })
    }
  }
} as Resolvers
