# Metrics Widget

The Metrics Widget is an embeddable component that displays real-time system metrics from a JSON API endpoint.

## Features

- 📊 **Real-time monitoring**: Updates every 1 second
- 🎨 **Visual indicators**: Green/yellow/red color coding based on usage levels
- 📱 **Responsive design**: Works on desktop and mobile
- 🌙 **Theme support**: Automatic dark/light theme detection
- 🔧 **Configurable**: Easy to customize and extend

## Metrics Displayed

- **CPU Usage**: Percentage (0-100%)
- **Memory Usage**: Virtual memory percentage (0-100%)
- **Swap Usage**: Swap memory percentage (0-100%)
- **GPU Memory**: GPU memory percentage (0-100%)
- **GPU Temperature**: Temperature in Celsius (20-70°C range)

## Color Coding

- 🟢 **Green**: 0-50% (Healthy)
- 🟡 **Yellow**: 51-80% (Warning)
- 🔴 **Red**: 81-100% (Critical)

## Setup

### 1. Environment Variable

Set the metrics API endpoint in your environment:

```bash
NEXT_PUBLIC_METRICS_URL=https://your-api-endpoint.com/metrics.json
```

### 2. JSON Format

The API should return JSON in this format:

```json
{
  "timestamp": "2025-08-03T17:40:15.952216+00:00Z",
  "hostname": "server-name",
  "cpu": {
    "usage_percent": 25.5
  },
  "memory": {
    "virtual": {
      "percent": 45.2
    },
    "swap": {
      "percent": 10.8
    }
  },
  "gpu": [
    {
      "memory": {
        "percent": 15.3
      },
      "temperature": 42
    }
  ]
}
```

### 3. Usage

Import and use the component:

```tsx
import MetricsWidget from '../components/MetricsWidget'

function MyPage() {
  return (
    <div>
      <MetricsWidget />
    </div>
  )
}
```

## Integration

The widget is automatically included on:
- **Index page**: In the sidebar below the "image generation" link
- **Request page**: At the top of the page

## Error Handling

The widget gracefully handles:
- ❌ Network errors
- ❌ Invalid JSON responses
- ❌ Missing environment variables
- ❌ API timeouts

## Customization

### Styling

Edit `components/MetricsWidget.module.css` to customize:
- Colors and themes
- Layout and spacing
- Responsive breakpoints
- Animation timing

### Thresholds

Modify the `getColor` function in `MetricsWidget.tsx` to change warning thresholds:

```tsx
const getColor = (percentage: number) => {
  if (percentage <= 50) return '#4ade80' // green
  if (percentage <= 80) return '#fbbf24' // yellow
  return '#ef4444' // red
}
```

### Update Frequency

Change the refresh interval (default: 1000ms):

```tsx
const interval = setInterval(fetchMetrics, 5000) // 5 seconds
```

## Deployment

The widget works with:
- ✅ Next.js static export
- ✅ AWS Amplify
- ✅ Vercel
- ✅ Netlify
- ✅ Any static hosting

## Troubleshooting

### Widget shows "Error"
- Check `NEXT_PUBLIC_METRICS_URL` environment variable
- Verify the API endpoint is accessible
- Check browser console for detailed error messages

### Widget shows "Loading..."
- Verify API returns valid JSON
- Check network connectivity
- Ensure CORS is properly configured on the API

### No GPU metrics
- GPU metrics are optional
- Widget will only show GPU data if present in the JSON response
