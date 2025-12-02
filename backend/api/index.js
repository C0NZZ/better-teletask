import fastify from 'fastify'
import { createRequire } from 'module'

const require = createRequire(import.meta.url)
const db = require('./database.js')

const server = fastify({
  trustProxy: true,
  logger: {
    level: 'info',
    transport: {
      target: 'pino/file',
      options: { 
        destination: './logs/access.log',
        mkdir: true
      }
    },
    timestamp: () => `,"time":"${new Date(Date.now()).toISOString()} UTC"`,
    serializers: {
      req(request) {
        return {
          method: request.method,
          url: request.url,
          ip: request.ip,
          userAgent: request.headers['user-agent'] || '-',
          referer: request.headers.referer || '-',
          auth: request.headers.authorization || '-'
        }
      },
      res(reply) {
        return {
          statusCode: reply.statusCode,
          contentLength: reply.getHeader('content-length') || '-'
        }
      }
    }
  }
})

server.get('/ping', async (request, reply) => {
  return 'pong\n'
})

server.get('/', async (request, reply) => {
  return reply.redirect('https://github.com/C0NZZ/better-teletask');
})

async function verifyAuthHeader(request, reply) {
  const authHeader = request.headers['authorization'];
  if (!authHeader) {return reply.code(401).send({ error: 'Missing Authorization header' });}
  else {
    const token = authHeader.replace('Bearer ', '').trim();
    if (!token) {return reply.code(401).send({ error: 'Invalid Authorization header' });}
    else {
      const apiKey = await db.getApiKey(token);
      if (!apiKey) {return reply.code(401).send({ error: 'Invalid API key' });}
      else if (apiKey.status === 'revoked') {return reply.code(403).send({ error: 'API key has been revoked' });}
      else if (apiKey.status === 'expired') {return reply.code(403).send({ error: 'API key has expired' });}
      else if (apiKey.status !== 'active') {return reply.code(403).send({ error: 'API key is not active' });}
      else {
        const now = new Date();
        const expiration = new Date(apiKey.expiration_date);
        if (expiration < now) {return reply.code(403).send({ error: 'API key has expired' });}
        // brauchen wir den key später noch? dann hier:
        // request.apiKey = apiKey;
      }
    }
  }
}

server.get('/sub/:id/:language', { preHandler: verifyAuthHeader }, async (request, reply) => {
  const { id, language } = request.params
  
  const teletaskId = parseInt(id, 10)
  
  if (isNaN(teletaskId) || teletaskId <= 0 || teletaskId.toString() !== id) {
    return reply.code(400).send({
      error: 'Bad Request',
      message: 'ID must be a positive integer'
    })
  }
  
  try {
    const vttFile = await db.getVttFile(teletaskId, language)
    
    if (!vttFile) {
      if (!language) {
        try {
          await fetch('http://transcriber:8000/prioritize/' + teletaskId, { method: 'POST' })
        } catch (err) {
          console.error('Failed to notify checker:', err)
        }
      }
      return reply.code(404).send({
        error: 'Not Found',
        message: `No VTT files found for teletask ID ${teletaskId}${language ? ` with language ${language}` : ''}`
      })
    }
    
    reply.header('Content-Type', 'text/vtt; charset=utf-8')
    reply.header("Access-Control-Allow-Origin", "https://www.tele-task.de");
    return Buffer.from(vttFile.vtt_data).toString('utf-8')
    
  } catch (error) {
    console.error('Database error:', error)
    return reply.code(500).send({
      error: 'Internal Server Error',
      message: 'Failed to fetch VTT file'
    })
  }
})

server.listen({ port: 80, host: '0.0.0.0' }, (err, address) => {
  if (err) {
    console.error(err)
    process.exit(1)
  }
  console.log(`Server listening at ${address}`)
})