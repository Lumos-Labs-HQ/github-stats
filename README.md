# GitHub Stats Service

Production-grade backend service that generates dynamic GitHub statistics cards as SVG images.

## Features

- ⚡ FastAPI-based async service
- 📊 GitHub GraphQL API integration (with REST fallback)
- 🔥 Contribution streak calculation (current & longest)
- 🎨 Dynamic SVG card generation
- 💾 Redis caching (15-minute TTL)
- 🐳 Docker-ready deployment
- 🛡️ Rate limit protection via caching

## Quick Start

### Prerequisites

- Python 3.12+
- Redis
- GitHub Personal Access Token

### Installation

1. Clone and install dependencies:
```bash
uv sync
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your GITHUB_TOKEN
```

3. Start Redis:
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

4. Run the service:
```bash
uvicorn app.main:app --reload
```

### Using Docker Compose

```bash
# Set your GitHub token
export GITHUB_TOKEN=your_token_here

# Start all services
docker-compose up -d
```

## API Usage

### Get Stats Card

```
GET /stats?username={github_username}
```

This endpoint renders the full stats card:

- Total Stars Earned
- Total Commits (supports `year` filter)
- Total PRs
- Total Issues
- Contributed to
- Rank ring

If `GITHUB_TOKEN` is set, private/restricted contributions are included in commit totals and shown as `(+N private)`.

Year filter example:

```
GET /stats?username=username&year=2025
```

### Get Streak Card

```
GET /streak?username={github_username}
```

This endpoint renders streak stats (Total Contributions, Current Streak, Longest Streak) with optional `month` and `year` filters.

Theme support:

```
GET /stats?username=username&theme=default
GET /streak?username=username&theme=default
```

Available theme names:

```
GET /themes
```

Color override support (same parameter style as streak stats generators):

```
GET /stats?username=username&stroke=FF6F61&background=1E1E2E&ring=FF6F61&fire=FF6F61&currStreakNum=FF6F61&currStreakLabel=FF6F61&sideNums=FF6F61&sideLabels=FF6F61&dates=FF6F61&hide_border=true
```

**Response:** SVG image (image/svg+xml)

**Example:**
```bash
curl http://localhost:8000/stats?username=torvalds
```

### Health Check

```
GET /health
```

## Architecture

```
app/
├── main.py              # FastAPI application & endpoints
├── github.py            # GitHub API integration (GraphQL + REST)
└── services/
    ├── stats.py         # Streak calculation logic
    ├── cache.py         # Redis caching layer
    └── svg.py           # SVG card generation
```

## How It Works

1. **Request** → Check Redis cache
2. **Cache Hit** → Return cached SVG (< 200ms)
3. **Cache Miss** → Fetch from GitHub GraphQL API
4. **Process** → Calculate streaks from contribution calendar
5. **Render** → Generate styled SVG card
6. **Cache** → Store in Redis (15 min TTL)
7. **Response** → Return SVG

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | Required |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |

## Performance

- **With cache:** < 200ms response time
- **Without cache:** < 2s (GitHub API + computation)
- **Cache TTL:** 15 minutes
- **Fallback:** Returns last cached data on API failure

## Error Handling

- Invalid username → Error SVG
- Rate limit exceeded → Returns cached data or error SVG
- Network failure → Fallback to REST API, then cached data
- Missing token → Error SVG

## Production Deployment

### Docker

```bash
docker build -t github-stats .
docker run -p 8000:8000 \
  -e GITHUB_TOKEN=your_token \
  -e REDIS_URL=redis://redis:6379 \
  github-stats
```

### Scaling Considerations

- Use Redis cluster for high availability
- Add rate limiting middleware
- Configure multiple GitHub tokens for rotation
- Use CDN for SVG caching
- Monitor GitHub API quota usage

## License

MIT
