// Cross-platform dev runner that starts core workspaces in dev mode
// and the next-gen IFC import service (uv-based). It also ensures
// the server enqueues jobs for the next-gen importer.

import { spawn } from 'node:child_process'
import { platform } from 'node:os'

function run(command, options = {}) {
  const child = spawn(command, {
    shell: true,
    stdio: 'inherit',
    env: { ...process.env, ...options.env }
  })
  child.on('exit', (code) => {
    // Keep process alive while the other child may still be running
  })
  return child
}

// Ensure server uses next-gen importer by default
const sharedEnv = { FF_NEXT_GEN_FILE_IMPORTER_ENABLED: 'true' }

// 1) Start all workspaces in dev, excluding the legacy fileimport-service
const foreachCmd = [
  'yarn workspaces foreach',
  '--parallel',
  '--interlaced',
  '--verbose',
  '--worktree',
  '--jobs unlimited',
  "--exclude '@speckle/fileimport-service'",
  'run dev'
].join(' ')

run(foreachCmd, { env: sharedEnv })

// 2) Start the next-gen IFC import service via platform-specific script
const isWin = process.platform === 'win32'
const ifcCmd = isWin
  ? 'powershell -NoProfile -ExecutionPolicy Bypass -File packages/ifc-import-service/run.ps1'
  : 'sh packages/ifc-import-service/run.sh'

run(ifcCmd, { env: sharedEnv })
