import type cron from 'node-cron'
import { db } from '@/db/knex'
import { moduleLogger } from '@/observability/logging'
import {
  createS3Bucket,
  isFileUploadsEnabled,
  getStorageProvider
} from '@/modules/shared/helpers/envHelper'
import type { SpeckleModule } from '@/modules/shared/helpers/typeHelper'
import { ensureStorageAccessFactory } from '@/modules/blobstorage/repositories/blobs'
import { ensureStorageAccessFactorySupabase } from '@/modules/blobstorage/repositories/supabaseBlobs'
import { getMainObjectStorage } from '@/modules/blobstorage/clients/objectStorage'
import { getMainSupabaseStorage } from '@/modules/blobstorage/clients/supabaseStorage'
import { blobStorageRouterFactory } from '@/modules/blobstorage/rest/router'
import { scheduleBlobPendingUploadExpiry } from '@/modules/blobstorage/tasks'
import { scheduleExecutionFactory } from '@/modules/core/services/taskScheduler'
import {
  acquireTaskLockFactory,
  releaseTaskLockFactory
} from '@/modules/core/repositories/scheduledTasks'

const ensureConditions = async () => {
  if (!isFileUploadsEnabled()) {
    moduleLogger.info('📦 Blob storage is DISABLED')
    return
  }

  const provider = getStorageProvider()
  moduleLogger.info(`📦 Init BlobStorage module (provider: ${provider})`)

  if (provider === 'supabase') {
    const storage = getMainSupabaseStorage()
    const ensureStorageAccess = ensureStorageAccessFactorySupabase({ storage })
    await ensureStorageAccess({
      createBucketIfNotExists: false // Supabase buckets are created via dashboard
    })
    moduleLogger.info('✅ Supabase Storage initialized successfully')
  } else {
    const storage = getMainObjectStorage()
    const ensureStorageAccess = ensureStorageAccessFactory({ storage })
    await ensureStorageAccess({
      createBucketIfNotExists: createS3Bucket()
    })
    moduleLogger.info('✅ S3 Storage initialized successfully')
  }
}

const scheduledTasks: cron.ScheduledTask[] = []
export const init: SpeckleModule['init'] = async ({ app }) => {
  await ensureConditions()

  app.use(blobStorageRouterFactory())

  const scheduleExecution = scheduleExecutionFactory({
    acquireTaskLock: acquireTaskLockFactory({ db }),
    releaseTaskLock: releaseTaskLockFactory({ db })
  })

  scheduledTasks.push(await scheduleBlobPendingUploadExpiry({ scheduleExecution }))
}

export const finalize: SpeckleModule['finalize'] = () => {}

export const shutdown: SpeckleModule['shutdown'] = async () => {
  scheduledTasks.forEach((task) => task.stop())
}
