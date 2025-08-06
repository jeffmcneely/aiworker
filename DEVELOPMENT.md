# Development Environment Setup

This document explains how to set up and use the development environment for the aiworker project.

## Quick Start

1. **Initial Setup** (run once):
   ```bash
   ./setup.sh
   ```

2. **Daily Development** (run each time you start working):
   ```bash
   source ./activate.sh
   ```

3. **Start Development Server**:
   ```bash
   devweb  # or: cd website && npm run dev
   ```

## Environment Files

### `.envrc` (direnv)
- Automatically loads when you enter the project directory (if direnv is installed)
- Sets up Python virtual environment and environment variables

### `activate.sh`
- Manual activation script for the project environment
- Sets up aliases and environment variables
- Can be sourced from any shell

### `.env.local` (Next.js)
- Environment variables specifically for the Next.js website
- Contains `NEXT_PUBLIC_METRICS_URL` for the metrics widget

## Environment Variables

### Required
- `NEXT_PUBLIC_METRICS_URL`: S3 Express One Zone URL for metrics JSON
  ```
  https://bucket-name--usw2-az1--x-s3.s3express-usw2-az1.us-west-2.amazonaws.com/metrics.json
  ```

### Optional
- `AWS_PROFILE`: AWS profile to use for CLI operations
- `AWS_REGION`: AWS region for S3 operations
- `NODE_ENV`: Node.js environment (development/production)

## Available Aliases (after activation)

### Navigation
- `cdproject` - Go to project root
- `cdwebsite` - Go to website directory
- `cdlambda` - Go to lambda directory
- `cdscripts` - Go to scripts directory

### Development
- `devweb` - Start Next.js development server
- `buildweb` - Build Next.js website
- `lintfix` - Run ESLint with auto-fix

### AWS/S3
- `runmetrics` - Run S3 CORS configuration script
- `testcors` - Test S3 CORS configuration

## Shell Functions (optional)

Add to your `~/.zshrc`:
```bash
source /Users/jeffmc/aiworker/.zshrc_aiworker
```

This provides these global functions:
- `aiworker` - Navigate to project and activate
- `aiworker-dev` - Start development server
- `aiworker-build` - Build website
- `aiworker-cors` - Configure S3 CORS
- `aiworker-test-cors` - Test S3 CORS

## direnv Setup (Recommended)

Install direnv for automatic environment loading:

```bash
# macOS
brew install direnv

# Add to ~/.zshrc
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
source ~/.zshrc

# Enable for this project
cd /Users/jeffmc/aiworker
direnv allow
```

## Project Structure

```
aiworker/
├── .envrc                 # direnv configuration
├── activate.sh           # Manual activation script
├── setup.sh              # Initial setup script
├── .zshrc_aiworker       # Shell functions
├── .venv/                # Python virtual environment
├── scripts/              # Python scripts
│   ├── configure_s3_cors.py
│   ├── test_s3_cors.py
│   └── requirements.txt
├── website/              # Next.js website
│   ├── .env.local        # Next.js environment variables
│   ├── components/
│   │   └── MetricsWidget.tsx
│   └── pages/
└── lambda/               # AWS Lambda functions
```

## Troubleshooting

### Virtual Environment Issues
```bash
# Recreate virtual environment
rm -rf .venv
python3 -m venv .venv
source ./activate.sh
```

### Environment Variables Not Loading
```bash
# Check environment variables
echo $NEXT_PUBLIC_METRICS_URL
echo $PROJECT_ROOT

# Reload environment
source ./activate.sh
```

### Node.js Dependencies
```bash
cd website
rm -rf node_modules package-lock.json
npm install
```

### AWS Credentials
```bash
# Check AWS configuration
aws configure list

# Set AWS profile (if needed)
export AWS_PROFILE=your-profile-name
```

## Development Workflow

1. **Start of day**:
   ```bash
   cd /Users/jeffmc/aiworker
   source ./activate.sh
   ```

2. **Work on website**:
   ```bash
   cdwebsite
   npm run dev
   ```

3. **Work on Python scripts**:
   ```bash
   cdscripts
   python configure_s3_cors.py
   ```

4. **Deploy changes**:
   ```bash
   buildweb  # Test build
   # Commit and push to trigger Amplify deployment
   ```
