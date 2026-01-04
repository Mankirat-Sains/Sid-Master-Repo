import { moduleLogger } from '@/observability/logging'
import type { SpeckleModule } from '@/modules/shared/helpers/typeHelper'

/**
 * ElementsQuery Module
 * 
 * Provides fast, denormalized queries for elements using the elements_queryable table.
 * This module exposes GraphQL endpoints for querying elements by material, storey,
 * volume, and other criteria without requiring complex joins.
 */
const elementsQueryModule: SpeckleModule = {
  async init() {
    moduleLogger.info('🔍 Init elementsquery module')
    // No special initialization needed - migrations run automatically
    // GraphQL schema and resolvers are auto-loaded by the module system
  }
}

export default elementsQueryModule
