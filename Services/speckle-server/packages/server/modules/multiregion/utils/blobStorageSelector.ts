import type { ObjectStorage } from '@/modules/blobstorage/clients/objectStorage'
import type { SupabaseStorage } from '@/modules/blobstorage/clients/supabaseStorage'
import {
  getMainObjectStorage,
  getObjectStorage,
  getPublicMainObjectStorage
} from '@/modules/blobstorage/clients/objectStorage'
import { getMainSupabaseStorage } from '@/modules/blobstorage/clients/supabaseStorage'
import { ensureStorageAccessFactory } from '@/modules/blobstorage/repositories/blobs'
import type {
  GetProjectObjectStorage,
  GetRegionObjectStorage
} from '@/modules/multiregion/domain/operations'
import { getAvailableRegionConfig } from '@/modules/multiregion/regionConfig'
import {
  getProjectRegionKey,
  getRegisteredRegionConfig,
  getRegisteredRegionConfigs
} from '@/modules/multiregion/utils/regionSelector'
import { MisconfiguredEnvironmentError } from '@/modules/shared/errors'
import { getFeatureFlags, getStorageProvider } from '@/modules/shared/helpers/envHelper'
import type { Optional } from '@speckle/shared'
import type { BlobStorageConfig } from '@speckle/shared/environment/db'

type RegionStorageClients = {
  [regionKey: string]: {
    private: ObjectStorage | SupabaseStorage
    public: ObjectStorage | SupabaseStorage
  }
}

let initializedClients: Optional<RegionStorageClients> = undefined

export const isMultiRegionBlobStorageEnabled = () =>
  !!getFeatureFlags().FF_WORKSPACES_MULTI_REGION_ENABLED

export const initializeRegion = async (params: {
  regionKey: string
  /**
   * As an optimization measure (when doing this in batch), you can pass in the config which would
   * otherwise be resolved from scratch
   */
  config?: BlobStorageConfig
}) => {
  if (!isMultiRegionBlobStorageEnabled())
    return { private: getMainObjectStorage(), public: getPublicMainObjectStorage() }

  const { regionKey } = params
  let config = params.config
  if (!config) {
    // getAvailableRegionConfig allows getting configs that may not be registered yet
    const regionConfigs = await getAvailableRegionConfig()
    config = regionConfigs[regionKey].blobStorage
    if (!config)
      throw new MisconfiguredEnvironmentError(
        `RegionKey ${regionKey} not available in config`
      )
  }

  const storage = getObjectStorage({
    credentials: {
      accessKeyId: config.accessKey,
      secretAccessKey: config.secretKey
    },
    endpoint: config.endpoint,
    region: config.s3Region,
    bucket: config.bucket
  })

  // ensure it works
  const ensure = ensureStorageAccessFactory({ storage })
  await ensure({ createBucketIfNotExists: config.createBucketIfNotExists })

  // Only add, if clients already initialized
  if (initializedClients) {
    initializedClients[regionKey] = { private: storage, public: storage }
  }

  if (config.publicEndpoint) {
    const publicStorage = getObjectStorage({
      credentials: {
        accessKeyId: config.accessKey,
        secretAccessKey: config.secretKey
      },
      endpoint: config.publicEndpoint,
      region: config.s3Region,
      bucket: config.bucket
    })

    // ensure it works
    const ensure = ensureStorageAccessFactory({ storage: publicStorage })
    await ensure({ createBucketIfNotExists: config.createBucketIfNotExists })

    // Only add, if clients already initialized
    if (initializedClients) {
      initializedClients[regionKey] = { private: storage, public: publicStorage }
    }

    return { private: storage, public: publicStorage }
  }

  return { private: storage, public: storage }
}

/**
 * Idempotently initialize registered region clients
 */
export const initializeRegisteredRegionClients =
  async (): Promise<RegionStorageClients> => {
    const configs = await getRegisteredRegionConfigs()

    const newRet: RegionStorageClients = Object.fromEntries(
      await Promise.all(
        Object.entries(configs).map(async ([regionKey, { blobStorage: config }]) => {
          return [regionKey, await initializeRegion({ regionKey, config })]
        })
      )
    )
    initializedClients = newRet

    return newRet
  }

export const getRegisteredRegionClients = async (): Promise<RegionStorageClients> => {
  if (!initializedClients) {
    initializedClients = await initializeRegisteredRegionClients()
  }
  return initializedClients
}

export const getRegionObjectStorage: GetRegionObjectStorage = async ({ regionKey }) => {
  if (!isMultiRegionBlobStorageEnabled())
    return { private: getMainObjectStorage(), public: getPublicMainObjectStorage() }

  const clients = await getRegisteredRegionClients()
  let storage = clients[regionKey]
  if (!storage) {
    // Region may have been initialized in a different server instance
    const config = await getRegisteredRegionConfig({ regionKey })
    if (config) {
      storage = await initializeRegion({ regionKey, config: config.blobStorage })
    }
  }
  if (!storage) {
    throw new MisconfiguredEnvironmentError(
      `Region ${regionKey} blobStorage region not found`
    )
  }

  return storage
}

export const getProjectObjectStorage: GetProjectObjectStorage = async ({
  projectId
}) => {
  const provider = getStorageProvider()

  console.log('📦 [STORAGE_SELECTOR] Getting project storage:', {
    projectId,
    provider,
    timestamp: new Date().toISOString()
  })

  // If using Supabase, return Supabase storage (multi-region not supported for Supabase yet)
  if (provider === 'supabase') {
    const storage = getMainSupabaseStorage()
    console.log('✅ [STORAGE_SELECTOR] Using Supabase storage:', {
      projectId,
      bucket: storage.bucket
    })
    return { private: storage, public: storage }
  }

  // For S3, use existing multi-region logic
  console.log('📦 [STORAGE_SELECTOR] Using S3 storage')
  const regionKey = await getProjectRegionKey({ projectId })
  return regionKey
    ? getRegionObjectStorage({ regionKey })
    : { private: getMainObjectStorage(), public: getPublicMainObjectStorage() }
}
