


const { S3Client, GetObjectCommand,ListObjectsV2Command,PutObjectCommand } = require('@aws-sdk/client-s3');
const { SQSClient, SendMessageCommand } = require('@aws-sdk/client-sqs');
const { getSignedUrl } = require('@aws-sdk/s3-request-presigner');

const { randomUUID } = require('crypto');


const s3list = async (event) => {
  const urls = await getRecentS3FileUrls(process.env.AWS_BUCKET, process.env.AWS_REGION, 5, 'png');
  console.log('Presigned URLs:', urls);
  return {
    statusCode: 200,
    headers: {
      'Access-Control-Allow-Origin': 'https://ai.mcneely.io',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
    body: JSON.stringify(urls)
  };
};


/**
 * Finds the 5 most recently added files in an S3 bucket,
 * generates presigned URLs for each, and returns an array of URLs.
 * @param {string} bucketName - The S3 bucket name.
 * @param {string} region - AWS region.
 * @param {number} count - Number of recent files to fetch.
 * @returns {Promise<string[]>} Array of presigned URLs.
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

    // Generate presigned URLs
    const urls = await Promise.all(
      recentFiles.map(obj =>
        getSignedUrl(s3Client, new GetObjectCommand({
          Bucket: bucketName,
          Key: obj.Key
        }), { expiresIn: 3600 })
      )
    );
    return urls;
  } catch (err) {
    console.error('Error fetching S3 files:', err);
    return [];
  }
}



const requestImage = async (event) => {
  // Handle CORS preflight
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 204,
      headers: {
        'Access-Control-Allow-Origin': 'https://ai.mcneely.io',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
      body: ''
    };
  }
  console.log('Received event:', JSON.stringify(event));
  const sqsClient = new SQSClient({ region: process.env.AWS_REGION });
  const s3Client = new S3Client({ region: process.env.AWS_REGION });
  const { height, width, steps, prompt, model } = JSON.parse(event.body || '{}');

  // Input validation
  if (
    typeof height !== 'number' || height > 1024 ||
    typeof width !== 'number' || width > 1024 ||
    typeof steps !== 'number' || steps > 100 ||
    typeof prompt !== 'string' || prompt.length > 10000 ||
    (model !== 'hidream' && model !== 'flux')
  ) {
    return {
      statusCode: 400,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Invalid input: height and width must be <= 1024, steps <= 100, prompt length < 10000, model must be hidream or flux.' }),
    };
  }

  // Generate UUID and add to message
  const id = randomUUID();
  const messageObj = { id, height, width, steps, prompt, model };
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
      headers: { 'Content-Type': 'application/json' },
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
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Failed to send message to SQS.' }),
    };
  }

  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': 'https://ai.mcneely.io',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
    body: JSON.stringify({ status: 'Message sent', data: { id, height, width, steps, prompt, model } }),
  };
};

module.exports = {
  s3list,
  requestImage
};