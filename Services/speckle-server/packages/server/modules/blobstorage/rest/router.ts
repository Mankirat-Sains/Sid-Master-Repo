import {
  allowForAllRegisteredUsersOnPublicStreamsWithPublicComments,
  allowForRegisteredUsersOnPublicStreamsEvenWithoutRole,
  allowAnonymousUsersOnPublicStreams,
  streamCommentsWritePermissionsPipelineFactory,
  streamReadPermissionsPipelineFactory
} from '@/modules/shared/authz'
import { authMiddlewareCreator } from '@/modules/shared/middleware'
import { isArray } from 'lodash-es'
import { UnauthorizedError } from '@/modules/shared/errors'
import {
  getAllStreamBlobIdsFactory,
  getBlobMetadataFactory,
  getBlobMetadataCollectionFactory,
  deleteBlobFactory
} from '@/modules/blobstorage/repositories'
import { db } from '@/db/knex'
import {
  getFileStreamFactory,
  fullyDeleteBlobFactory
} from '@/modules/blobstorage/services/management'
import { Router } from 'express'
import { getProjectObjectStorage } from '@/modules/multiregion/utils/blobStorageSelector'
import {
  deleteObjectFactory,
  getObjectStreamFactory
} from '@/modules/blobstorage/repositories/blobs'
import {
  deleteObjectFactorySupabase,
  getObjectStreamFactorySupabase
} from '@/modules/blobstorage/repositories/supabaseBlobs'
import { isSupabaseStorage } from '@/modules/blobstorage/helpers/storageProvider'
import { getProjectDbClient } from '@/modules/multiregion/utils/dbSelector'
import { getStreamFactory } from '@/modules/core/repositories/streams'
import { processNewFileStreamFactory } from '@/modules/blobstorage/services/streams'
import { UserInputError } from '@/modules/core/errors/userinput'
import { createBusboy } from '@/modules/blobstorage/rest/busboy'
import contentDisposition from 'content-disposition'
import { allowCrossOriginResourceAccessMiddelware } from '@/modules/shared/middleware/security'
import cors from 'cors'
import { getStorageProvider } from '@/modules/shared/helpers/envHelper'
import {
  getMainSupabaseStorage,
  getUploadToken,
  deleteUploadToken,
  getPublicUrl as getSupabasePublicUrl
} from '@/modules/blobstorage/clients/supabaseStorage'
import crypto from 'crypto'

export const blobStorageRouterFactory = (): Router => {
  const processNewFileStream = processNewFileStreamFactory()

  const app = Router()

  app.post(
    '/api/stream/:streamId/blob',
    async (req, res, next) => {
      await authMiddlewareCreator(
        streamCommentsWritePermissionsPipelineFactory({
          getStream: getStreamFactory({ db })
        })
      )(req, res, next)
    },
    async (req, res) => {
      const streamId = req.params.streamId
      const userId = req.context.userId
      if (!userId) throw new UnauthorizedError()
      req.log = req.log.child({ streamId, userId })
      req.log.debug('Uploading blob.')

      // Log upload request
      console.log('📤 [ROUTER] Multipart form upload received:', {
        streamId,
        userId,
        contentType: req.headers['content-type']
      })

      const busboy = createBusboy(req)
      const newFileStreamProcessor = await processNewFileStream({
        busboy,
        streamId,
        userId,
        logger: req.log,
        onFinishAllFileUploads: async (uploadResults) => {
          res.status(201).send({ uploadResults })
        },
        onError: () => {
          res.contentType('application/json')
          res
            .status(400)
            .end(
              '{ "error": "Upload request error. The server logs may have more details." }'
            )
        }
      })
      req.pipe(newFileStreamProcessor)
    }
  )

  app.post(
    '/api/stream/:streamId/blob/diff',
    async (req, res, next) => {
      await authMiddlewareCreator([
        ...streamReadPermissionsPipelineFactory({
          getStream: getStreamFactory({ db })
        }),
        allowForAllRegisteredUsersOnPublicStreamsWithPublicComments,
        allowForRegisteredUsersOnPublicStreamsEvenWithoutRole,
        allowAnonymousUsersOnPublicStreams
      ])(req, res, next)
    },
    async (req, res) => {
      if (!isArray(req.body)) {
        throw new UserInputError('An array of blob IDs expected in the body.')
      }

      const projectDb = await getProjectDbClient({ projectId: req.params.streamId })

      const getAllStreamBlobIds = getAllStreamBlobIdsFactory({ db: projectDb })
      const bq = await getAllStreamBlobIds({ streamId: req.params.streamId })
      const unknownBlobIds = [...req.body].filter(
        (id) => bq.findIndex((bInfo) => bInfo.id === id) === -1
      )
      res.send(unknownBlobIds)
    }
  )

  app.get(
    '/api/stream/:streamId/blob/:blobId',
    cors(),
    allowCrossOriginResourceAccessMiddelware(),
    async (req, res, next) => {
      await authMiddlewareCreator([
        ...streamReadPermissionsPipelineFactory({
          getStream: getStreamFactory({ db })
        }),
        allowForAllRegisteredUsersOnPublicStreamsWithPublicComments,
        allowForRegisteredUsersOnPublicStreamsEvenWithoutRole,
        allowAnonymousUsersOnPublicStreams
      ])(req, res, next)
    },
    async (req, res) => {
      const streamId = req.params.streamId
      const [projectDb, projectStorage] = await Promise.all([
        getProjectDbClient({ projectId: streamId }),
        getProjectObjectStorage({ projectId: streamId })
      ])

      const getBlobMetadata = getBlobMetadataFactory({ db: projectDb })

      // Detect storage provider and use appropriate factory
      const isSupabase = isSupabaseStorage(projectStorage.private)

      // Get blob metadata to access fileName and objectKey
      const blobMetadata = await getBlobMetadata({
        streamId: req.params.streamId,
        blobId: req.params.blobId
      })

      const { fileName, objectKey } = blobMetadata

      // For Supabase storage, redirect to public URL instead of proxying
      if (isSupabase) {
        if (!objectKey) {
          console.error('❌ [ROUTER] No objectKey found for blob:', {
            blobId: req.params.blobId,
            streamId: req.params.streamId
          })
          return res.status(404).json({ error: 'Blob objectKey not found' })
        }

        const storage = getMainSupabaseStorage()
        const getPublicUrl = getSupabasePublicUrl({ storage })
        const publicUrl = getPublicUrl(objectKey)

        console.log('🔗 [ROUTER] Redirecting to Supabase public URL:', {
          blobId: req.params.blobId,
          objectKey,
          publicUrl
        })

        // Return redirect to Supabase public URL
        return res.redirect(302, publicUrl)
      }

      // For S3 or other storage, use the existing proxy stream approach
      const getFileStream = getFileStreamFactory({ getBlobMetadata })
      const getObjectStream = getObjectStreamFactory({
        storage: projectStorage.private as any
      })

      const fileStream = await getFileStream({
        getObjectStream,
        streamId: req.params.streamId,
        blobId: req.params.blobId
      })

      // Determine correct Content-Type based on file extension
      // For PDFs, set application/pdf instead of application/octet-stream
      let contentType = 'application/octet-stream'
      if (fileName?.toLowerCase().endsWith('.pdf')) {
        contentType = 'application/pdf'
      }

      res.writeHead(200, {
        'Content-Type': contentType,
        'Content-Disposition': contentDisposition(fileName)
      })
      fileStream.pipe(res)
    }
  )

  app.delete(
    '/api/stream/:streamId/blob/:blobId',
    async (req, res, next) => {
      await authMiddlewareCreator(
        streamCommentsWritePermissionsPipelineFactory({
          getStream: getStreamFactory({ db })
        })
      )(req, res, next)
    },
    async (req, res) => {
      const streamId = req.params.streamId
      const [projectDb, projectStorage] = await Promise.all([
        getProjectDbClient({ projectId: streamId }),
        getProjectObjectStorage({ projectId: streamId })
      ])

      const getBlobMetadata = getBlobMetadataFactory({ db: projectDb })

      // Detect storage provider and use appropriate factory
      const isSupabase = isSupabaseStorage(projectStorage.private)
      const deleteObject = isSupabase
        ? deleteObjectFactorySupabase({ storage: projectStorage.private as any })
        : deleteObjectFactory({ storage: projectStorage.private as any })

      const deleteBlob = fullyDeleteBlobFactory({
        getBlobMetadata,
        deleteBlob: deleteBlobFactory({ db: projectDb }),
        deleteObject
      })

      await deleteBlob({
        streamId: req.params.streamId,
        blobId: req.params.blobId
      })
      res.status(204).send()
    }
  )

  app.get(
    '/api/stream/:streamId/blobs',
    async (req, res, next) => {
      await authMiddlewareCreator(
        streamReadPermissionsPipelineFactory({
          getStream: getStreamFactory({ db })
        })
      )(req, res, next)
    },
    async (req, res) => {
      let fileName = req.query.fileName //filename can be undefined or null, and that returns all blobs
      if (isArray(fileName)) {
        fileName = fileName[0]
      }

      const streamId = req.params.streamId

      const projectDb = await getProjectDbClient({ projectId: req.params.streamId })
      const getBlobMetadataCollection = getBlobMetadataCollectionFactory({
        db: projectDb
      })

      const blobMetadataCollection = await getBlobMetadataCollection({
        streamId,
        query: fileName as string
      })

      return res.status(200).send(blobMetadataCollection)
    }
  )

  app.delete('/api/stream/:streamId/blobs', async (_req, res) => {
    return res.status(501).send('This method is not implemented yet.')
  })

  // PUT endpoint for Supabase signed upload URLs (proxy for S3 compatibility)
  // This endpoint accepts PUT requests (like S3) and uploads to Supabase using native methods
  app.put('/api/internal/blob/upload/:tokenId', cors(), async (req, res) => {
    const tokenId = req.params.tokenId
    console.log('🔵 [UPLOAD] Request received:', { tokenId, method: req.method })

    // Only allow this endpoint when using Supabase storage
    if (getStorageProvider() !== 'supabase') {
      console.log('❌ [UPLOAD] Provider check failed:', {
        provider: getStorageProvider()
      })
      return res.status(404).send('Endpoint only available for Supabase storage')
    }

    // Get upload token from cache
    const tokenData = getUploadToken(tokenId)
    if (!tokenData) {
      console.log('❌ [UPLOAD] Token not found or expired:', { tokenId })
      return res.status(404).json({ error: 'Upload token not found or expired' })
    }

    console.log('✅ [UPLOAD] Token found:', {
      tokenId,
      path: tokenData.path,
      bucket: tokenData.bucket,
      expiresAt: new Date(tokenData.expiresAt).toISOString()
    })

    try {
      const { path, token, bucket } = tokenData

      // Get Supabase storage client
      const storage = getMainSupabaseStorage()

      // Convert request body to Buffer for upload
      const chunks: Buffer[] = []
      req.on('data', (chunk) => {
        chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
      })

      req.on('end', async () => {
        try {
          const fileBuffer = Buffer.concat(chunks)
          console.log('📦 [UPLOAD] File received:', {
            size: fileBuffer.length,
            path,
            bucket
          })

          // Calculate MD5 hash for ETag (matching S3 behavior)
          const hash = crypto.createHash('md5').update(fileBuffer).digest('hex')
          const etag = `"${hash}"`
          console.log('🔐 [UPLOAD] Calculated ETag:', { etag })

          // Upload to Supabase using native uploadToSignedUrl method
          console.log('⬆️ [UPLOAD] Uploading to Supabase...', { path, bucket })
          const { error: uploadError, data: uploadData } = await storage.client.storage
            .from(bucket)
            .uploadToSignedUrl(path, token, fileBuffer)

          if (uploadError) {
            console.error('❌ [UPLOAD] Supabase upload error:', {
              error: uploadError,
              message: uploadError.message,
              statusCode: (uploadError as any).statusCode,
              path,
              bucket
            })
            req.log?.error({ uploadError }, 'Failed to upload to Supabase')
            return res.status(500).json({
              error: `Upload failed: ${uploadError.message}`,
              details: uploadError
            })
          }

          console.log('✅ [UPLOAD] Upload successful!', {
            path,
            bucket,
            uploadData,
            etag
          })

          // Clean up the token after successful upload
          deleteUploadToken(tokenId)

          // Return 200 with ETag header (matching S3 behavior)
          res.setHeader('ETag', etag)
          res.status(200).json({ success: true, etag, path })
        } catch (err) {
          console.error('❌ [UPLOAD] Exception during upload:', err)
          req.log?.error({ err }, 'Error during upload processing')
          deleteUploadToken(tokenId)
          res.status(500).json({
            error: 'Internal server error during upload',
            details: err instanceof Error ? err.message : 'Unknown error'
          })
        }
      })

      req.on('error', (err) => {
        console.error('❌ [UPLOAD] Request stream error:', err)
        req.log?.error({ err }, 'Request stream error')
        deleteUploadToken(tokenId)
        res.status(500).json({ error: 'Request stream error' })
      })
    } catch (err) {
      console.error('❌ [UPLOAD] Error processing request:', err)
      req.log?.error({ err }, 'Error processing upload request')
      deleteUploadToken(tokenId)
      res.status(500).json({ error: 'Internal server error' })
    }
  })

  return app
}
