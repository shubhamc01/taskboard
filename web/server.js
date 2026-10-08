// The board's static page; it calls the API relatively (/api/...) — same host, routed by path.
const http = require('http')
const fs = require('fs')
const path = require('path')

const page = fs.readFileSync(path.join(__dirname, 'index.html'))
const port = Number(process.env.PORT || 3000)

http.createServer((req, res) => {
  if (req.url === '/healthz') { res.end('ok'); return }
  res.setHeader('content-type', 'text/html; charset=utf-8')
  res.end(page)
}).listen(port, () => console.log(`web on ${port}`))
