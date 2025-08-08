import fs from 'node:fs'
import localtunnel from 'localtunnel'

async function main(){
  const port = 8000
  const tunnel = await localtunnel({ port })
  const url = tunnel.url
  fs.writeFileSync('/workspace/tunnel_url.txt', url)
  console.log('Tunnel URL:', url)
  tunnel.on('close', () => {})
}

main().catch(err => { console.error(err); process.exit(1) })