import type { SupabaseStorage } from '@/modules/blobstorage/clients/supabaseStorage'
import type {
  DeleteObject,
  EnsureStorageAccess,
  GetObjectAttributes,
  GetObjectStream,
  StoreFileStream
} from '@/modules/blobstorage/domain/storageOperations'
import {
  getObjectStreamFactory,
  getObjectAttributesFactory,
  storeFileStreamFactory,
  deleteObjectFactory,
  ensureStorageAccessFactory
} from '@/modules/blobstorage/clients/supabaseStorage'

/**
 * Supabase storage operation factories
 * These wrap the Supabase client functions to match the S3 factory interface
 */

export const getObjectStreamFactorySupabase = (deps: {
  storage: SupabaseStorage
}): GetObjectStream => {
  return getObjectStreamFactory(deps)
}

export const getObjectAttributesFactorySupabase = (deps: {
  storage: SupabaseStorage
}): GetObjectAttributes => {
  return getObjectAttributesFactory(deps)
}

export const storeFileStreamFactorySupabase = (deps: {
  storage: SupabaseStorage
}): StoreFileStream => {
  return storeFileStreamFactory(deps)
}

export const deleteObjectFactorySupabase = (deps: {
  storage: SupabaseStorage
}): DeleteObject => {
  return deleteObjectFactory(deps)
}

export const ensureStorageAccessFactorySupabase = (deps: {
  storage: SupabaseStorage
}): EnsureStorageAccess => {
  return ensureStorageAccessFactory(deps)
}

