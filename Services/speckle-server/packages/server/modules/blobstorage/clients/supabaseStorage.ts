import {
  getSupabaseUrl,
  getSupabaseServiceRoleKey,
  getSupabaseBucketName
} from '@/modules/shared/helpers/envHelper'
import { createClient, type SupabaseClient } from '@supabase/supabase-js'
import type { Optional } from '@speckle/shared'
import type {
  GetBlobMetadataFromStorage,
  GetSignedUrl
} from '@/modules/blobstorage/domain/operations'
import type {
  DeleteObject,
  EnsureStorageAccess,
  GetObjectAttributes,
  GetObjectStream,
  StoreFileStream
} from '@/modules/blobstorage/domain/storageOperations'
import {
  BadRequestError,
  EnvironmentResourceError,
  NotFoundError
} from '@/modules/shared/errors'
import { ensureError } from '@speckle/shared'
import { Readable } from 'stream'
import crypto from 'crypto'

export type GetProjectSupabaseStorage = (args: {
  projectId: string
}) => Promise<SupabaseStorage>

export type SupabaseStorageParams = {
  url: string
  serviceRoleKey: string
  bucket: string
}

export type SupabaseStorage = {
  client: SupabaseClient
  bucket: string
  params: SupabaseStorageParams
}

/**
 * Get Supabase storage client
 */
export const getSupabaseStorage = (params: SupabaseStorageParams): SupabaseStorage => {
  const { url, serviceRoleKey, bucket } = params

  const client = createClient(url, serviceRoleKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false
    }
  })

  return { client, bucket, params }
}

let mainSupabaseStorage: Optional<SupabaseStorage> = undefined

/**
 * Get main Supabase storage client
 *
 * This is used for connecting the server to Supabase Storage.
 * Uses the service role key for full access to storage operations.
 */
export const getMainSupabaseStorage = (): SupabaseStorage => {
  if (mainSupabaseStorage) return mainSupabaseStorage

  const mainParams: SupabaseStorageParams = {
    url: getSupabaseUrl(),
    serviceRoleKey: getSupabaseServiceRoleKey(),
    bucket: getSupabaseBucketName()
  }

  mainSupabaseStorage = getSupabaseStorage(mainParams)
  return mainSupabaseStorage
}

/**
 * Convert Buffer or Uint8Array to Node.js Readable stream
 */
const bufferToStream = (buffer: Buffer | Uint8Array): Readable => {
  const stream = new Readable()
  stream.push(buffer)
  stream.push(null) // End the stream
  return stream
}

/**
 * Convert Readable stream to Buffer
 */
const streamToBuffer = async (stream: Readable): Promise<Buffer> => {
  const chunks: Buffer[] = []
  for await (const chunk of stream) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  return Buffer.concat(chunks)
}

/**
 * Get object stream from Supabase Storage
 * Returns a Readable stream for the file
 */
export const getObjectStreamFactory = (deps: {
  storage: SupabaseStorage
}): GetObjectStream => {
  const { storage } = deps
  return async ({ objectKey }) => {
    const { data, error } = await storage.client.storage
      .from(storage.bucket)
      .download(objectKey)

    if (error) {
      if (
        error.message.includes('not found') ||
        error.message.includes('404') ||
        error.message.includes('NotFound')
      ) {
        throw new NotFoundError(`Blob not found: ${objectKey}`)
      }
      throw new Error(`Failed to get object from Supabase: ${error.message}`)
    }

    if (!data) {
      throw new NotFoundError(`No data returned for object: ${objectKey}`)
    }

    // Convert Blob to Buffer, then to Readable stream
    const arrayBuffer = await data.arrayBuffer()
    const buffer = Buffer.from(arrayBuffer)
    return bufferToStream(buffer)
  }
}

/**
 * Get object attributes (file size) from Supabase Storage
 *
 * Note: Supabase Storage doesn't have a HEAD operation like S3.
 * We download the file to get accurate size. For better performance,
 * consider caching file sizes or storing metadata during upload.
 */
export const getObjectAttributesFactory = (deps: {
  storage: SupabaseStorage
}): GetObjectAttributes => {
  const { storage } = deps
  return async ({ objectKey }) => {
    try {
      // Download file to get accurate size
      // This is necessary because Supabase Storage API doesn't support HEAD requests
      const { data, error } = await storage.client.storage
        .from(storage.bucket)
        .download(objectKey)

      if (error) {
        if (
          error.message.includes('not found') ||
          error.message.includes('404') ||
          error.message.includes('NotFound')
        ) {
          throw new NotFoundError(`Object not found: ${objectKey}`)
        }
        throw new Error(`Failed to get object attributes: ${error.message}`)
      }

      if (!data) {
        throw new NotFoundError(`Object not found: ${objectKey}`)
      }

      // Get file size from downloaded data
      const arrayBuffer = await data.arrayBuffer()
      return { fileSize: arrayBuffer.byteLength }
    } catch (err) {
      if (err instanceof NotFoundError) {
        throw err
      }
      throw new Error(
        `Failed to get object attributes from Supabase: ${ensureError(err).message}`
      )
    }
  }
}

/**
 * Store file stream in Supabase Storage
 * Handles Readable streams, Buffers, and Uint8Arrays
 * Returns fileHash (calculated from content)
 */
export const storeFileStreamFactory = (deps: {
  storage: SupabaseStorage
}): StoreFileStream => {
  const { storage } = deps
  return async ({ objectKey, fileStream, fileName }) => {
    console.log('⬆️ [SUPABASE] Storing file stream:', {
      objectKey,
      fileName,
      bucket: storage.bucket
    })

    let buffer: Buffer

    // Convert various input types to Buffer
    if (Buffer.isBuffer(fileStream)) {
      buffer = fileStream
    } else if (fileStream instanceof Uint8Array) {
      buffer = Buffer.from(fileStream)
    } else if (fileStream instanceof Readable) {
      buffer = await streamToBuffer(fileStream)
    } else if (typeof fileStream === 'string') {
      buffer = Buffer.from(fileStream, 'utf-8')
    } else {
      throw new BadRequestError('Unsupported file stream type')
    }

    // Detect Content-Type from fileName
    // PDFs should be explicitly stored as application/pdf, not application/octet-stream
    let contentType = 'application/octet-stream' // Default for models and other files

    if (fileName) {
      const lowerFileName = fileName.toLowerCase()
      if (lowerFileName.endsWith('.pdf')) {
        contentType = 'application/pdf'
      } else if (lowerFileName.endsWith('.jpg') || lowerFileName.endsWith('.jpeg')) {
        contentType = 'image/jpeg'
      } else if (lowerFileName.endsWith('.png')) {
        contentType = 'image/png'
      } else if (lowerFileName.endsWith('.gif')) {
        contentType = 'image/gif'
      } else if (lowerFileName.endsWith('.webp')) {
        contentType = 'image/webp'
      }
      // For other file types (models, etc.), keep application/octet-stream
    }

    console.log('⬆️ [SUPABASE] File buffer prepared:', {
      objectKey,
      fileName,
      size: buffer.length,
      contentType,
      bucket: storage.bucket
    })

    // Calculate file hash (MD5) for consistency with S3 ETag behavior
    const hash = crypto.createHash('md5').update(buffer).digest('hex')
    const fileHash = hash

    // Upload to Supabase Storage with correct Content-Type
    console.log('⬆️ [SUPABASE] Uploading to Supabase Storage...', {
      objectKey,
      fileName,
      bucket: storage.bucket,
      size: buffer.length,
      contentType
    })

    const { error, data } = await storage.client.storage
      .from(storage.bucket)
      .upload(objectKey, buffer, {
        contentType, // Use detected Content-Type (application/pdf for PDFs)
        upsert: true, // Allow overwriting existing files
        cacheControl: '3600' // Cache for 1 hour
      })

    if (error) {
      console.error('❌ [SUPABASE] Upload failed:', {
        objectKey,
        error: error.message,
        bucket: storage.bucket
      })
      throw new Error(`Failed to upload file to Supabase: ${error.message}`)
    }

    console.log('✅ [SUPABASE] Upload successful!', {
      objectKey,
      bucket: storage.bucket,
      fileHash,
      uploadData: data
    })

    return { fileHash }
  }
}

/**
 * Delete object from Supabase Storage
 */
export const deleteObjectFactory = (deps: {
  storage: SupabaseStorage
}): DeleteObject => {
  const { storage } = deps
  return async ({ objectKey }) => {
    const { error } = await storage.client.storage
      .from(storage.bucket)
      .remove([objectKey])

    if (error) {
      // If file doesn't exist, that's okay for delete operations
      if (
        error.message.includes('not found') ||
        error.message.includes('404') ||
        error.message.includes('NotFound')
      ) {
        return // Silently succeed if already deleted
      }
      throw new Error(`Failed to delete object from Supabase: ${error.message}`)
    }
  }
}

// Temporary storage for upload tokens (in production, use Redis or similar)
const uploadTokenCache = new Map<
  string,
  { path: string; token: string; expiresAt: number; bucket: string }
>()

/**
 * Generate signed upload URL for Supabase Storage using native createSignedUploadUrl
 *
 * Supabase's createSignedUploadUrl returns { path, token } which is used with
 * uploadToSignedUrl. Since our clients expect a PUT-able URL (like S3), we:
 * 1. Use createSignedUploadUrl to get the signed token (native Supabase method)
 * 2. Return a URL to our proxy endpoint that accepts PUT and uses Supabase's native upload
 *
 * This gives us the best of both worlds:
 * - Uses Supabase's native createSignedUploadUrl (most secure and recommended)
 * - Maintains compatibility with existing S3-style PUT upload flow
 * - The proxy endpoint uses Supabase's native upload method server-side
 */
export const getSignedUrlFactory = (deps: {
  storage: SupabaseStorage
}): GetSignedUrl => {
  const { storage } = deps
  return async ({ objectKey, urlExpiryDurationSeconds }) => {
    try {
      console.log('🔐 [SIGNED_URL] Creating signed upload URL:', {
        objectKey,
        bucket: storage.bucket,
        expirySeconds: urlExpiryDurationSeconds
      })

      // Use Supabase's native createSignedUploadUrl method
      // This is Supabase's recommended way to create upload URLs
      const { data, error } = await storage.client.storage
        .from(storage.bucket)
        .createSignedUploadUrl(objectKey)

      if (error) {
        console.error('❌ [SIGNED_URL] Error creating signed URL:', error)
        throw new Error(`Failed to create signed upload URL: ${error.message}`)
      }

      if (!data) {
        throw new BadRequestError('No data returned from createSignedUploadUrl')
      }

      // Supabase's createSignedUploadUrl returns { path: string, token: string }
      const { path, token } = data

      console.log('✅ [SIGNED_URL] Signed URL created:', {
        objectKey,
        path,
        pathMatches: path === objectKey,
        tokenLength: token?.length || 0,
        bucket: storage.bucket
      })

      // Generate a unique token ID for this upload session
      const uploadTokenId = crypto.randomBytes(32).toString('hex')
      const expiresAt = Date.now() + urlExpiryDurationSeconds * 1000

      // Store the upload credentials temporarily
      // In production, this should be in Redis with TTL
      uploadTokenCache.set(uploadTokenId, {
        path,
        token,
        expiresAt,
        bucket: storage.bucket
      })

      console.log('💾 [SIGNED_URL] Token cached:', {
        tokenId: uploadTokenId,
        expiresAt: new Date(expiresAt).toISOString(),
        cacheSize: uploadTokenCache.size
      })

      // Clean up expired tokens periodically (simple cleanup, in production use Redis TTL)
      if (uploadTokenCache.size > 1000) {
        const now = Date.now()
        for (const [key, value] of uploadTokenCache.entries()) {
          if (value.expiresAt < now) {
            uploadTokenCache.delete(key)
          }
        }
      }

      // Return URL to our proxy endpoint that will handle the upload using Supabase's native method
      // The endpoint will be implemented in the router
      const baseUrl = process.env.CANONICAL_URL || 'http://localhost:3000'
      const uploadUrl = `${baseUrl}/api/internal/blob/upload/${uploadTokenId}`

      console.log('🔗 [SIGNED_URL] Upload URL generated:', {
        uploadUrl,
        tokenId: uploadTokenId
      })

      return uploadUrl
    } catch (err) {
      console.error('❌ [SIGNED_URL] Exception:', err)
      throw new Error(`Failed to create signed upload URL: ${ensureError(err).message}`)
    }
  }
}

/**
 * Get upload token data (used by the proxy endpoint)
 */
export const getUploadToken = (
  tokenId: string
): {
  path: string
  token: string
  bucket: string
  expiresAt: number
} | null => {
  const cached = uploadTokenCache.get(tokenId)
  if (!cached) return null

  // Check if expired
  if (cached.expiresAt < Date.now()) {
    uploadTokenCache.delete(tokenId)
    return null
  }

  return {
    path: cached.path,
    token: cached.token,
    bucket: cached.bucket,
    expiresAt: cached.expiresAt
  }
}

/**
 * Delete upload token after use (cleanup)
 */
export const deleteUploadToken = (tokenId: string): void => {
  uploadTokenCache.delete(tokenId)
}

/**
 * Get blob metadata from Supabase Storage
 * Returns contentLength and eTag (fileHash)
 *
 * Note: For accurate file size, we download the file.
 * For better performance, consider caching metadata or storing file hash during upload.
 */
export const getBlobMetadataFromStorage = (deps: {
  storage: SupabaseStorage
}): GetBlobMetadataFromStorage => {
  const { storage } = deps
  return async ({ objectKey }) => {
    try {
      // Download file to get accurate size
      // This ensures we have the correct contentLength
      const { data, error } = await storage.client.storage
        .from(storage.bucket)
        .download(objectKey)

      if (error) {
        if (
          error.message.includes('not found') ||
          error.message.includes('404') ||
          error.message.includes('NotFound')
        ) {
          throw new NotFoundError(`Blob not found: ${objectKey}`)
        }
        throw new Error(`Failed to get blob metadata: ${error.message}`)
      }

      if (!data) {
        throw new NotFoundError(`Blob not found: ${objectKey}`)
      }

      // Get file size
      const arrayBuffer = await data.arrayBuffer()
      const contentLength = arrayBuffer.byteLength

      // Calculate eTag (MD5 hash) from file content for consistency with S3
      // This matches the hash calculated during upload
      const buffer = Buffer.from(arrayBuffer)
      const hash = crypto.createHash('md5').update(buffer).digest('hex')
      const eTag = `"${hash}"`

      return {
        contentLength,
        eTag
      }
    } catch (err) {
      if (err instanceof NotFoundError) {
        throw err
      }
      throw new Error(
        `Failed to get blob metadata from Supabase: ${ensureError(err).message}`
      )
    }
  }
}

/**
 * Ensure storage access to Supabase bucket
 * Verifies that the bucket exists and is accessible
 */
export const ensureStorageAccessFactory = (deps: {
  storage: SupabaseStorage
}): EnsureStorageAccess => {
  const { storage } = deps
  return async ({ createBucketIfNotExists }) => {
    try {
      // Try to list files in the bucket to verify access
      const { error } = await storage.client.storage
        .from(storage.bucket)
        .list('', { limit: 1 })

      if (error) {
        // If bucket doesn't exist or access denied
        if (
          error.message.includes('not found') ||
          error.message.includes('404') ||
          error.message.includes('NotFound')
        ) {
          if (createBucketIfNotExists) {
            // Note: Supabase buckets must be created via the dashboard
            // or API. We can't programmatically create them the same way as S3.
            // However, we can check if they exist and provide helpful error messages.
            throw new EnvironmentResourceError(
              `Supabase bucket '{bucket}' does not exist. Please create it in the Supabase dashboard first.`,
              {
                cause: error,
                info: { bucket: storage.bucket }
              }
            )
          } else {
            throw new EnvironmentResourceError(
              `Supabase bucket '{bucket}' does not exist, and bucket creation is disabled.`,
              {
                cause: error,
                info: { bucket: storage.bucket }
              }
            )
          }
        }

        // Handle access denied errors
        if (
          error.message.includes('403') ||
          error.message.includes('permission denied') ||
          error.message.includes('access denied') ||
          error.message.includes('Forbidden')
        ) {
          throw new EnvironmentResourceError(
            `Access denied to Supabase bucket '{bucket}'. Check your service role key and bucket permissions.`,
            {
              cause: error,
              info: { bucket: storage.bucket }
            }
          )
        }

        // Other errors
        throw new EnvironmentResourceError(
          `Failed to access Supabase bucket '{bucket}': ${error.message}`,
          {
            cause: error,
            info: { bucket: storage.bucket }
          }
        )
      }

      // Success - bucket is accessible
      return
    } catch (err) {
      // Re-throw EnvironmentResourceError as-is
      if (err instanceof EnvironmentResourceError) {
        throw err
      }

      // Wrap other errors
      throw new EnvironmentResourceError(
        `Failed to verify access to Supabase bucket '{bucket}'`,
        {
          cause: ensureError(err),
          info: { bucket: storage.bucket }
        }
      )
    }
  }
}

/**
 * Get public URL for a file in Supabase Storage
 * Useful for public buckets or generating direct access URLs
 */
export const getPublicUrl = (deps: { storage: SupabaseStorage }) => {
  const { storage } = deps
  return (objectKey: string): string => {
    const { data } = storage.client.storage.from(storage.bucket).getPublicUrl(objectKey)
    return data.publicUrl
  }
}
