#!/usr/bin/env node
/**
 * Simple tee-like utility for logging to both console and file
 * Usage: node tee.js <output_file> <command>
 */

const fs = require('fs')
const { spawn } = require('child_process')
const path = require('path')

const logFile = process.argv[2]
const command = process.argv.slice(3)

if (!logFile || command.length === 0) {
  console.error('Usage: node tee.js <log_file> <command> [args...]')
  process.exit(1)
}

// Ensure log file directory exists
const logDir = path.dirname(logFile)
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true })
}

// Open log file in append mode
const logStream = fs.createWriteStream(logFile, { flags: 'a' })

// Write header
const timestamp = new Date().toISOString()
logStream.write(`\n=== Log started at ${timestamp} ===\n`)

// Spawn the command
const child = spawn(command[0], command.slice(1), {
  stdio: ['inherit', 'pipe', 'pipe'],
  shell: true
})

// Pipe stdout to both console and file
child.stdout.on('data', (data) => {
  process.stdout.write(data)
  logStream.write(data)
})

// Pipe stderr to both console and file
child.stderr.on('data', (data) => {
  process.stderr.write(data)
  logStream.write(data)
})

// Handle process exit
child.on('exit', (code) => {
  const timestamp = new Date().toISOString()
  logStream.write(`\n=== Log ended at ${timestamp} (exit code: ${code}) ===\n`)
  logStream.end()
  process.exit(code || 0)
})

child.on('error', (err) => {
  console.error('Failed to start process:', err)
  logStream.write(`\n=== Error: ${err.message} ===\n`)
  logStream.end()
  process.exit(1)
})

// Handle Ctrl+C
process.on('SIGINT', () => {
  child.kill('SIGINT')
  const timestamp = new Date().toISOString()
  logStream.write(`\n=== Log interrupted at ${timestamp} ===\n`)
  logStream.end()
  process.exit(130)
})

