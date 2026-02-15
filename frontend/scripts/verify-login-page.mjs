#!/usr/bin/env node
/**
 * Verifies the login page loads at http://localhost:5173/
 * Run while the dev server is running: node scripts/verify-login-page.mjs
 */
import http from 'http'

const PORT = 5173
const url = `http://127.0.0.1:${PORT}/`

function fetch(url) {
  return new Promise((resolve, reject) => {
    const req = http.get(url, { timeout: 8000 }, (res) => {
      let body = ''
      res.on('data', (chunk) => { body += chunk })
      res.on('end', () => resolve({ statusCode: res.statusCode, body }))
    })
    req.on('error', reject)
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')) })
  })
}

async function main() {
  try {
    const { statusCode, body } = await fetch(url)
    if (statusCode !== 200) {
      console.error(`FAIL: Got HTTP ${statusCode} from ${url}`)
      process.exit(1)
    }
    const hasTitle = body.includes('DawaiRx') || body.includes('Pharmacy Audit')
    const hasRoot = body.includes('id="root"') || body.includes('id=\'root\'')
    if (!hasTitle || !hasRoot) {
      console.error('FAIL: Response does not look like the app (missing DawaiRx/root)')
      process.exit(1)
    }
    console.log('OK: Login page loads at', url)
    console.log('   HTTP 200, contains app shell (DawaiRx, #root)')
  } catch (err) {
    console.error('FAIL: Could not load', url, err.message)
    process.exit(1)
  }
}

main()
