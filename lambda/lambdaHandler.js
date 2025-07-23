


const { S3Client, ListObjectsV2Command } = require('@aws-sdk/client-s3');
const { SNSClient, PublishCommand } = require('@aws-sdk/client-sns');
const { getSignedUrl } = require('@aws-sdk/s3-request-presigner');


const s3list = async (event) => {
  const urls = await getRecentS3FileUrls(process.env.AWS_BUCKET);
  return {
    statusCode: 200,
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

async function getRecentS3FileUrls(bucketName, region = process.env.AWS_REGION, count = 5) {
  const s3Client = new S3Client({ region });
  try {
    const response = await s3Client.send(new ListObjectsV2Command({ Bucket: bucketName }));
    if (!response.Contents) return [];

    // Sort by LastModified descending
    const sortedFiles = response.Contents.sort(
      (a, b) => new Date(b.LastModified) - new Date(a.LastModified)
    );
    const recentFiles = sortedFiles.slice(0, count);

    // Generate presigned URLs
    const urls = await Promise.all(
      recentFiles.map(obj =>
        getSignedUrl(s3Client, new ListObjectsV2Command({
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
  const snsClient = new SNSClient({ region: process.env.AWS_REGION });
  const { height, width, steps, prompt } = JSON.parse(event.body || '{}');

  // Input validation
  if (
    typeof height !== 'number' || height > 1024 ||
    typeof width !== 'number' || width > 1024 ||
    typeof steps !== 'number' || steps > 100 ||
    typeof prompt !== 'string' || prompt.length > 10000
  ) {
    return {
      statusCode: 400,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Invalid input: height and width must be <= 1024, steps <= 100, prompt length < 10000.' }),
    };
  }

  const message = JSON.stringify({ height, width, steps, prompt });

  await snsClient.send(new PublishCommand({
    TopicArn: process.env.AWS_SNS_TOPIC,
    Message: message,
  }));

  return {
    statusCode: 200,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'Message sent', data: { height, width, steps, prompt } }),
  };
};

module.exports = {
  s3list,
  requestImage
};