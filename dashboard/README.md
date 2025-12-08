# RoadSense Dashboard

React.js dashboard for RoadSense road defect detection system.

## Features

- 📊 Real-time statistics and analytics
- 🗺️ Interactive map with defect markers
- 📤 Image upload for defect detection
- 📈 Charts and trends visualization
- 🎯 Priority-based maintenance list
- 💾 Export data in multiple formats

## Tech Stack

- React 18 + Vite
- TailwindCSS for styling
- Leaflet for maps
- Chart.js for data visualization
- Axios for API calls

## Running in Docker

The dashboard is automatically built and deployed with docker-compose:

```bash
docker-compose up -d dashboard
```

Access at: http://localhost:3000

## API Integration

The dashboard connects to:
- Detection Service: http://localhost:8001
- Severity Service: http://localhost:8002

## Pages

1. **Home** - Overview with statistics
2. **Map** - Geographic view of defects
3. **Upload** - Upload images for detection
4. **Analytics** - Charts and trends
5. **Priority** - Maintenance priority list
6. **Export** - Download data
7. **Settings** - Configuration
