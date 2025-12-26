import { Pool, PoolClient, QueryResult, QueryResultRow } from 'pg';
import dotenv from 'dotenv';

dotenv.config({ path: '.env' });

const pool = new Pool({
  user: process.env.DB_USER || process.env.POSTGRES_USER,
  host: process.env.DB_HOST || 'localhost',
  database: process.env.DB_NAME || process.env.POSTGRES_DB,
  password: String(process.env.DB_PASS ?? process.env.POSTGRES_PASSWORD ?? ''),
  port: Number(process.env.DB_PORT || process.env.POSTGRES_PORT || 5432),
});

pool.on('connect', () => {
  console.log('Connected to PostgreSQL database');
});

pool.on('error', (err: Error) => {
  console.error('Unexpected error on idle client', err);
  process.exit(-1);
});

async function query<T extends QueryResultRow = QueryResultRow>(text: string, params?: unknown[]): Promise<QueryResult<T>> {
  const start = Date.now();
  try {
    const res = await pool.query<T>(text, params as any[] | undefined);
    const duration = Date.now() - start;
    console.log('Executed query', { text, duration, rows: res.rowCount });
    return res;
  } catch (error) {
    console.error('Database query error:', error);
    throw error;
  }
}

async function getClient(): Promise<PoolClient> {
  const client = await pool.connect();
  const queryRef = client.query.bind(client);
  const releaseRef = client.release.bind(client);

  const timeout = setTimeout(() => {
    console.error('A client has been checked out for more than 5 seconds!');
  }, 5000);

  client.query = ((...args: Parameters<PoolClient['query']>) => {
    (client as PoolClient & { lastQuery?: Parameters<PoolClient['query']> }).lastQuery = args;
    return queryRef(...args as Parameters<PoolClient['query']>);
  }) as PoolClient['query'];

  client.release = () => {
    clearTimeout(timeout);
    client.query = queryRef as unknown as PoolClient['query'];
    client.release = releaseRef;
    return releaseRef();
  };

  return client;
}

export type VttFileRow = {
  id: number;
  teletask_id: number;
  language: string;
  vtt_data: Buffer;
  is_original_lang?: boolean;
};

export type ApiKeyRow = {
  api_key: string;
  expiration_date: Date | string;
  status: string;
};

async function getVttFile(teletaskId: number, language?: string): Promise<VttFileRow | undefined> {
  let result: QueryResult<VttFileRow>;
  if (!language) {
    result = await query<VttFileRow>(
      'SELECT id, teletask_id, language, is_original_lang, vtt_data FROM vtt_files WHERE teletask_id = $1 AND is_original_lang = True ORDER BY language LIMIT 1',
      [teletaskId]
    );
  } else {
    result = await query<VttFileRow>(
      'SELECT id, teletask_id, language, vtt_data FROM vtt_files WHERE teletask_id = $1 AND language = $2',
      [teletaskId, language]
    );
  }
  return result.rows[0];
}

async function getApiKey(key: string): Promise<ApiKeyRow | undefined> {
  const result = await query<ApiKeyRow>(
    'SELECT api_key, expiration_date, status FROM api_keys WHERE api_key = $1 LIMIT 1',
    [key]
  );
  return result.rows[0];
}

process.on('SIGINT', async () => {
  console.log('Closing database pool...');
  await pool.end();
  process.exit(0);
});

export {
  query,
  getClient,
  pool,
  getVttFile,
  getApiKey,
};
