import type { ObjectStorage } from '@/modules/blobstorage/clients/objectStorage'
import type { SupabaseStorage } from '@/modules/blobstorage/clients/supabaseStorage'
import { getStorageProvider } from '@/modules/shared/helpers/envHelper'

/**
 * Type guard to check if storage is Supabase
 */
export function isSupabaseStorage(
  storage: ObjectStorage | SupabaseStorage
): storage is SupabaseStorage {
  return (
    storage !== null &&
    typeof storage === 'object' &&
    'client' in storage &&
    storage.client !== null &&
    typeof storage.client === 'object' &&
    'storage' in storage.client
  )
}

/**
 * Type guard to check if storage is S3
 */
export function isS3Storage(
  storage: ObjectStorage | SupabaseStorage
): storage is ObjectStorage {
  return (
    storage !== null &&
    typeof storage === 'object' &&
    'client' in storage &&
    storage.client !== null &&
    typeof storage.client === 'object' &&
    !('storage' in storage.client) &&
    'send' in storage.client
  )
}

/**
 * Get current storage provider type
 */
export function getCurrentStorageProvider(): 's3' | 'supabase' {
  return getStorageProvider()
}

