import fastify from 'fastify'
import { createRequire } from 'module'

const require = createRequire(import.meta.url)
const db = require('./database.js')

const server = fastify()

server.get('/ping', async (request, reply) => {
  return 'pong\n'
})

server.get('/', async (request, reply) => {
  return reply.redirect('https://github.com/C0NZZ/better-teletask');
})

server.get('/sub/:id/:language', async (request, reply) => {
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
    
    // Return the VTT content directly as text
    reply.header('Content-Type', 'text/vtt; charset=utf-8')
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