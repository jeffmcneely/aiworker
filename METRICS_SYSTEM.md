# Multi-Host Metrics System

## Overview

The metrics system has been updated to support multiple hosts through a list-based approach. Instead of fetching metrics from a single URL, the system now:

1. Fetches `list.json` every 30 seconds to get available metric sources
2. Loads individual metric files for each host listed
3. Provides a host selector in the UI when multiple hosts are available

## File Structure

### list.json
Contains a mapping of hostnames to their last update timestamps:
```json
{
  "stryker": "2025-08-06T03:03:16.999106+00:00Z",
  "server2": "2025-08-06T03:02:45.123456+00:00Z"
}
```

### Individual Metric Files
Each host has its own JSON file named `{hostname}.json`:
- `stryker.json`
- `server2.json`
- etc.

## Environment Variables

### Development (.env.local)
```bash
NEXT_PUBLIC_METRICS_BUCKET_BASE=https://your-bucket.s3express-region.amazonaws.com
```

### Project Environment (.envrc or activate.sh)
```bash
export AWS_S3_BUCKET="your-bucket--region-az--x-s3"
export AWS_REGION="us-west-2"
export METRICS_OBJECT_KEY="metrics.json"
export METRICS_BUCKET_BASE="https://your-bucket.s3express-region.amazonaws.com"
```

## Updated Components

### MetricsWidget
- Fetches list.json every 30 seconds
- Fetches individual metrics every 1 second
- Shows host selector when multiple hosts available
- Displays online/total host count

### Scripts
- `configure_s3_cors.py` - Accepts bucket name as argument or uses env var
- `test_s3_cors.py` - Accepts bucket name as argument or uses env var
- `s3_helper.py` - Updated to show base URL and list URL

## Usage

### Command Line Arguments
```bash
python scripts/configure_s3_cors.py my-bucket--usw2-az1--x-s3
python scripts/test_s3_cors.py my-bucket--usw2-az1--x-s3
python scripts/s3_helper.py show-config my-bucket--usw2-az1--x-s3
```

### Environment Variables (fallback)
```bash
export AWS_S3_BUCKET="my-bucket--usw2-az1--x-s3"
python scripts/configure_s3_cors.py
python scripts/test_s3_cors.py
python scripts/s3_helper.py show-config
```

## Testing

1. Create sample files:
   - `list.json` with host entries
   - `{hostname}.json` files for each host

2. Upload to S3 Express One Zone bucket

3. Start development server:
   ```bash
   cd website && npm run dev
   ```

4. Visit http://localhost:3000 to see the multi-host metrics widget
