


const { S3Client, GetObjectCommand,ListObjectsV2Command,PutObjectCommand } = require('@aws-sdk/client-s3');
const { SQSClient, SendMessageCommand, GetQueueAttributesCommand } = require('@aws-sdk/client-sqs');
const { getSignedUrl } = require('@aws-sdk/s3-request-presigner');

const { randomUUID } = require('crypto');

// CORS configuration
const allowedOrigins = process.env.ALLOWED_ORIGINS 
  ? JSON.parse(process.env.ALLOWED_ORIGINS)
  : [];

const getCorsHeaders = (origin, isStaticFile = false) => {
  // For static files, be more permissive
  if (isStaticFile) {
    return {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Access-Control-Max-Age': '86400'
    };
  }
  
  const isOriginAllowed = !origin || allowedOrigins.includes(origin);
  return {
    'Access-Control-Allow-Origin': isOriginAllowed ? (origin || '*') : 'null',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Credentials': 'true',
    'Access-Control-Max-Age': '86400' // 24 hours
  };
};


const s3list = async (event) => {
  const origin = event.headers?.origin || event.headers?.Origin;
  const corsHeaders = getCorsHeaders(origin);
  
  const results = await getRecentS3FileUrls(process.env.AWS_BUCKET, process.env.AWS_REGION, 5, 'png');
  console.log('S3 file results:', results);
  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/json',
      ...corsHeaders
    },
    body: JSON.stringify(results)
  };
};


/**
 * Finds the 5 most recently added files in an S3 bucket,
 * generates presigned URLs for each, and returns an array of URLs.
 * @param {string} bucketName - The S3 bucket name.
 * @param {string} region - AWS region.
 * @param {number} count - Number of recent files to fetch.
 * @returns {Promise<Object[]>} Array of objects with filename and signed URL.
 */

async function getRecentS3FileUrls(bucketName, region = process.env.AWS_REGION, count = 5, suffix = undefined) {
  const s3Client = new S3Client({ region });
  try {
    const response = await s3Client.send(new ListObjectsV2Command({ Bucket: bucketName }));
    if (!response.Contents) return [];

    // Print all S3 files found
    console.log('S3 files found:', response.Contents.map(obj => obj.Key));

    // Optionally filter by file suffix
    let files = response.Contents;
    if (suffix) {
      files = files.filter(obj => obj.Key.endsWith(suffix));
    }

    // Sort by LastModified descending
    const sortedFiles = files.sort(
      (a, b) => new Date(b.LastModified) - new Date(a.LastModified)
    );
    const recentFiles = sortedFiles.slice(0, count);

//    const url = await getSignedUrl(s3Client, new GetObjectCommand({ Bucket, Key }), { expiresIn: 3600 });

    // Generate presigned URLs with filename info and prompt
    const results = await Promise.all(
      recentFiles.map(async obj => {
        const url = await getSignedUrl(s3Client, new GetObjectCommand({
          Bucket: bucketName,
          Key: obj.Key
        }), { expiresIn: 3600 });
        
        // Get base filename without extension and read corresponding JSON
        const baseFilename = obj.Key.replace(/\.[^/.]+$/, "");
        const jsonKey = `${baseFilename}_final.json`;
        let prompt = null;
        let height = null;
        let width = null;
        let steps = null;
        let seed = null;
        let cfg = null;
        let negativePrompt = null;
        let model = null;
        let elapsed = null;
        
        try {
          const jsonResponse = await s3Client.send(new GetObjectCommand({
            Bucket: bucketName,
            Key: jsonKey
          }));
          const jsonContent = await jsonResponse.Body.transformToString();
          const jsonData = JSON.parse(jsonContent);
          prompt = jsonData.prompt || null;
          height = jsonData.height || null;
          width = jsonData.width || null;
          steps = jsonData.steps || null;
          seed = jsonData.seed || null;
          cfg = jsonData.cfg || null;
          negativePrompt = jsonData.negativePrompt || null;
          model = jsonData.model || null;
          elapsed = jsonData.elapsed || null;
        } catch (err) {
          console.log(`No JSON file found for ${jsonKey} or error reading it:`, err.message);
        }
        
        return {
          filename: obj.Key,
          url: url,
          prompt: prompt,
          height: height,
          width: width,
          steps: steps,
          seed: seed,
          cfg: cfg,
          negativePrompt: negativePrompt,
          model: model,
          elapsed: elapsed,
          timestamp: obj.LastModified,
          uuid: baseFilename
        };
      })
    );
    return results;
  } catch (err) {
    console.error('Error fetching S3 files:', err);
    return [];
  }
}



const requestImage = async (event) => {
  const origin = event.headers?.origin || event.headers?.Origin;
  const corsHeaders = getCorsHeaders(origin);
  
  // Handle CORS preflight
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 204,
      headers: corsHeaders,
      body: ''
    };
  }
  
  console.log('Received event:', JSON.stringify(event));
  const sqsClient = new SQSClient({ region: process.env.AWS_REGION });
  const s3Client = new S3Client({ region: process.env.AWS_REGION });
  const { height, width, steps, seed, cfg, prompt, negativePrompt, model } = JSON.parse(event.body || '{}');

  // Input validation with specific error messages
  const errors = [];

  // Height validation
  if (typeof height !== 'number') {
    errors.push('Height must be a number');
  } else if (height <= 0) {
    errors.push('Height must be greater than 0');
  } else if (height > 1024) {
    errors.push('Height must not exceed 1024 pixels');
  }

  // Width validation
  if (typeof width !== 'number') {
    errors.push('Width must be a number');
  } else if (width <= 0) {
    errors.push('Width must be greater than 0');
  } else if (width > 1024) {
    errors.push('Width must not exceed 1024 pixels');
  }

  // Steps validation
  if (typeof steps !== 'number') {
    errors.push('Steps must be a number');
  } else if (steps <= 0) {
    errors.push('Steps must be greater than 0');
  } else if (steps > 100) {
    errors.push('Steps must not exceed 100');
  }

  // Seed validation
  if (typeof seed !== 'number') {
    errors.push('Seed must be a number');
  } else if (seed < 0) {
    errors.push('Seed must be 0 or greater (use 0 for random)');
  }

  // CFG validation
  if (typeof cfg !== 'number') {
    errors.push('CFG must be a number');
  } else if (cfg < 0) {
    errors.push('CFG must be 0 or greater');
  } else if (cfg > 10) {
    errors.push('CFG must not exceed 10');
  }

  // Prompt validation
  if (typeof prompt !== 'string') {
    errors.push('Prompt must be a string');
  } else if (prompt.trim().length === 0) {
    errors.push('Prompt cannot be empty');
  } else if (prompt.length > 10000) {
    errors.push('Prompt must not exceed 10,000 characters');
  }

  // Negative prompt validation
  if (negativePrompt !== null && negativePrompt !== undefined) {
    if (typeof negativePrompt !== 'string') {
      errors.push('Negative prompt must be a string');
    } else if (negativePrompt.length > 10000) {
      errors.push('Negative prompt must not exceed 10,000 characters');
    }
  }

  // Model validation
  const validModels = ['hidream', 'flux', 'omnigen', 'sd3.5'];
  if (typeof model !== 'string') {
    errors.push('Model must be a string');
  } else if (!validModels.includes(model)) {
    errors.push(`Model must be one of: ${validModels.join(', ')}`);
  }

  // Return validation errors if any
  if (errors.length > 0) {
    return {
      statusCode: 400,
      headers: { 
        'Content-Type': 'application/json',
        ...corsHeaders
      },
      body: JSON.stringify({ 
        error: 'Validation failed',
        details: errors
      }),
    };
  }

  // Generate UUID and handle seed
  const id = randomUUID();
  const finalSeed = seed === 0 ? Math.floor(Math.random() * (2**53 - 1)) : seed;
  const messageObj = { id, height, width, steps, prompt, negativePrompt: negativePrompt || '', model, seed: finalSeed, cfg };
  const message = JSON.stringify(messageObj);

  // Upload message to S3 as a JSON file
  const bucket = process.env.AWS_BUCKET;
  const key = `${id}.json`;
  try {
    await s3Client.send(new PutObjectCommand({
      Bucket: bucket,
      Key: key,
      Body: message,
      ContentType: 'application/json',
    }));
  } catch (err) {
    console.error('Failed to upload message to S3:', err);
    return {
      statusCode: 500,
      headers: { 
        'Content-Type': 'application/json',
        ...corsHeaders
      },
      body: JSON.stringify({ error: 'Failed to upload message to S3.' }),
    };
  }

  // Send message to SQS
  try {
    await sqsClient.send(new SendMessageCommand({
      QueueUrl: process.env.AWS_SQS_URL,
      MessageBody: message,
      MessageGroupId: 1, // Use the generated UUID as the group ID for FIFO ordering
    }));
  } catch (err) {
    console.error('Failed to send message to SQS:', err);
    return {
      statusCode: 500,
      headers: { 
        'Content-Type': 'application/json',
        ...corsHeaders
      },
      body: JSON.stringify({ error: 'Failed to send message to SQS.' }),
    };
  }

  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/json',
      ...corsHeaders
    },
    body: JSON.stringify({ status: 'Message sent', data: { id, height, width, steps, prompt, negativePrompt: negativePrompt || '', model, seed: finalSeed, cfg } }),
  };
};

const sqsMonitor = async (event) => {
  const origin = event.headers?.origin || event.headers?.Origin;
  const corsHeaders = getCorsHeaders(origin);
  
  const sqsClient = new SQSClient({ region: process.env.AWS_REGION });
  
  try {
    const fastQueueUrl = process.env.FAST_QUEUE;
    const slowQueueUrl = process.env.SLOW_QUEUE;
    
    if (!fastQueueUrl || !slowQueueUrl) {
      return {
        statusCode: 500,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        },
        body: JSON.stringify({ error: 'Queue URLs not configured' })
      };
    }
    
    // Get attributes for both queues
    const [fastQueueResponse, slowQueueResponse] = await Promise.all([
      sqsClient.send(new GetQueueAttributesCommand({
        QueueUrl: fastQueueUrl,
        AttributeNames: ['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
      })),
      sqsClient.send(new GetQueueAttributesCommand({
        QueueUrl: slowQueueUrl,
        AttributeNames: ['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
      }))
    ]);
    
    const result = [
      {
        queueName: 'fast',
        messagesAvailable: parseInt(fastQueueResponse.Attributes?.ApproximateNumberOfMessages || '0'),
        messagesInFlight: parseInt(fastQueueResponse.Attributes?.ApproximateNumberOfMessagesNotVisible || '0')
      },
      {
        queueName: 'slow', 
        messagesAvailable: parseInt(slowQueueResponse.Attributes?.ApproximateNumberOfMessages || '0'),
        messagesInFlight: parseInt(slowQueueResponse.Attributes?.ApproximateNumberOfMessagesNotVisible || '0')
      }
    ];
    
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      },
      body: JSON.stringify(result)
    };
    
  } catch (err) {
    console.error('Error monitoring SQS queues:', err);
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      },
      body: JSON.stringify({ error: 'Failed to monitor queues' })
    };
  }
};

module.exports = {
  s3list,
  requestImage,
  sqsMonitor
};