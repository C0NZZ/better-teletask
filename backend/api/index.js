import fastify from 'fastify'
import { createRequire } from 'module'

const require = createRequire(import.meta.url)
const db = require('./database.js')

const server = fastify()

server.get('/ping', async (request, reply) => {
  return 'pong\n'
})

// Dynamic route for integer IDs - returns VTT file directly
server.get('/:id', async (request, reply) => {
  const { id } = request.params
  
  // Validate that id is an integer
  const teletaskId = parseInt(id, 10)
  
  if (isNaN(teletaskId) || teletaskId <= 0 || teletaskId.toString() !== id) {
    return reply.code(400).send({
      error: 'Bad Request',
      message: 'ID must be a positive integer'
    })
  }
  
  try {
    // Query database for VTT files with this teletask ID
    const result = await db.query(
      'SELECT id, teletaskid, language, isOriginalLanguage, vtt_data FROM vtt_files WHERE teletaskid = $1 AND isOriginalLanguage = True ORDER BY language LIMIT 1',
      [teletaskId]
    )
    
    if (result.rows.length === 0) {
      // notify local checker service that a missing VTT was requested
      // (best-effort, non-blocking; ignore errors)
      try {
        await fetch('http://localhost:8000/prioritize/' + teletaskId, { method: 'POST' })
      } catch (err) {
        console.error('Failed to notify checker:', err)
      }
      return reply.code(404).send({
        error: 'Not Found',
        message: `No VTT files found for teletask ID: ${teletaskId}`
      })
    }
    
    const vttFile = result.rows[0]
    const vttContent = Buffer.from(vttFile.vtt_data).toString('utf-8')
    
    // Set headers for VTT file
    reply.header('Content-Type', 'text/vtt; charset=utf-8')
    
    return vttContent
    
  } catch (error) {
    console.error('Database error:', error)
    return reply.code(500).send({
      error: 'Internal Server Error',
      message: 'Failed to fetch VTT file'
    })
  }
})

// Optional: Route to get specific language for a teletask ID
server.get('/:id/:language', async (request, reply) => {
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
      return reply.code(404).send({
        error: 'Not Found',
        message: `No VTT file found for teletask ID ${teletaskId} with language '${language}'`
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

server.listen({ port: 8080, host: '0.0.0.0' }, (err, address) => {
  if (err) {
    console.error(err)
    process.exit(1)
  }
  console.log(`Server listening at ${address}`)
})