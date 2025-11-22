const { Pool } = require('pg');
require('dotenv').config({ path: '.env' });

const pool = new Pool({
  user: process.env.DB_USER || process.env.POSTGRES_USER,
  host: process.env.DB_HOST || 'localhost',
  database: process.env.DB_NAME || process.env.POSTGRES_DB,
  password: String(process.env.DB_PASS ?? process.env.POSTGRES_PASSWORD ?? ''),
  port: process.env.DB_PORT || process.env.POSTGRES_PORT || 5432,
});

// Test the connection
pool.on('connect', () => {
  console.log('Connected to PostgreSQL database');
});

pool.on('error', (err) => {
  console.error('Unexpected error on idle client', err);
  process.exit(-1);
});

// Helper function to query the database
async function query(text, params) {
  const start = Date.now();
  try {
    const res = await pool.query(text, params);
    const duration = Date.now() - start;
    console.log('Executed query', { text, duration, rows: res.rowCount });
    return res;
  } catch (error) {
    console.error('Database query error:', error);
    throw error;
  }
}

// Helper function to get a client from the pool (for transactions)
async function getClient() {
  const client = await pool.connect();
  const query = client.query;
  const release = client.release;
  
  // Set a timeout of 5 seconds, after which we will log this client's last query
  const timeout = setTimeout(() => {
    console.error('A client has been checked out for more than 5 seconds!');
  }, 5000);
  
  // Monkey patch the query method to keep track of the last query executed
  client.query = (...args) => {
    client.lastQuery = args;
    return query.apply(client, args);
  };
  
  client.release = () => {
    // Clear the timeout
    clearTimeout(timeout);
    // Set the query method back to its original implementation
    client.query = query;
    client.release = release;
    return release.apply(client);
  };
  
  return client;
}

// Example function to get VTT file by teletask ID and language
async function getVttFile(teletaskId, language) {
  let result;
  if (!language) {
    result = await query(
      'SELECT id, teletaskid, language, isOriginalLang, vtt_data FROM vtt_files WHERE teletaskid = $1 AND isOriginalLang = True ORDER BY language LIMIT 1',
      [teletaskId]
    );
  } else {
    result = await query(
      'SELECT id, teletaskid, language, vtt_data FROM vtt_files WHERE teletaskid = $1 AND language = $2',
      [teletaskId, language]
    );
  }
  return result.rows[0];
}

async function getApiKey(key) {
  result = await query(
      'SELECT api_key, expiration_date, status FROM api_keys WHERE api_key = $1 LIMIT 1',
      [key]
    );
  return result.rows[0];
}

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('Closing database pool...');
  await pool.end();
  process.exit(0);
});

module.exports = {
  query,
  getClient,
  pool,
  // Export helper functions
  getVttFile,
  getApiKey,
};
