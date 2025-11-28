# Catanduanes Connect

A comprehensive web platform connecting job seekers, businesses, and service providers in Catanduanes, Philippines.

## Features

- **Job Portal**: Browse and apply for local job opportunities
- **Business Directory**: Discover and support local businesses
- **Service Marketplace**: Find and offer professional services
- **User Management**: Role-based authentication (Job Seeker, Business Owner, Service Provider, Admin)
- **Real-time Chat**: AI-powered chatbot for assistance
- **Reviews & Ratings**: Community-driven feedback system
- **Interactive Maps**: Location-based search and visualization
- **Admin Dashboard**: Comprehensive platform management
- **Email Notifications**: Automated alerts and updates
- **Mobile Responsive**: Optimized for all devices

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: Neo4j (Graph Database)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Styling**: Tailwind CSS
- **Maps**: Leaflet.js
- **Caching**: SimpleCache
- **Web Server**: Nginx

## Prerequisites

- Python 3.11+
- Neo4j 5.12+
- Node.js 18+ (for development)

## Installation

### Option 1: Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/catanduanes-connect.git
   cd catanduanes-connect
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

5. **Start Neo4j**
   ```bash
   # Start your local Neo4j installation
   # Make sure Neo4j is running on port 7687
   ```

6. **Initialize database**
   ```bash
   python seed.py
   ```

7. **Run the application**
   ```bash
   flask run --debug
   ```

### Option 2: Docker Deployment

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/catanduanes-connect.git
   cd catanduanes-connect
   ```

2. **Set up environment variables**
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

3. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Seed the database**
   ```bash
   docker-compose exec app python seed.py
   ```

## Configuration

### Environment Variables

Copy `.env.template` to `.env` and configure the following:

```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password



# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# File Upload Configuration
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216  # 16MB
```

## Demo Accounts

After running the seed script, you can use these demo accounts:

- **Admin**: admin@example.com / Password123!
- **Job Seeker**: job_seeker@example.com / Password123!
- **Business Owner**: business_owner@example.com / Password123!
- **Service Provider**: service_client@example.com / Password123!

## API Documentation

API documentation is available at `/api/docs` when running the application.

### Key Endpoints

- **Auth**: `/auth/*`
- **Jobs**: `/jobs/*`
- **Businesses**: `/businesses/*`
- **Services**: `/services/*`
- **Chat**: `/chat/*`
- **Admin**: `/admin/*`

## Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-flask pytest-mock

# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app tests/
```

### E2E Tests

```bash
# Install Playwright
pip install playwright
playwright install

# Run E2E tests
pytest tests/e2e/
```

## Development

### Code Style

The project uses:
- **Black** for code formatting
- **Flake8** for linting
- **isort** for import sorting

```bash
# Format code
black .

# Sort imports
isort .

# Run linter
flake8
```

### Git Hooks

Set up pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

## Deployment

### Production Deployment

1. **Update environment variables for production**
   ```env
   FLASK_ENV=production
   SECRET_KEY=strong-random-secret-key
   SESSION_COOKIE_SECURE=true
   ```

2. **Build production image**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
   ```

3. **Deploy**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

### CI/CD

The project includes GitHub Actions workflows for:
- Code quality checks
- Automated testing
- Docker image building
- Deployment to production

## Monitoring

### Health Checks

- Application health: `/health`
- Metrics: `/metrics` (Prometheus)

### Logging

Logs are written to:
- Application logs: `logs/app.log`
- Error logs: `logs/error.log`
- Access logs: `logs/access.log`

## Security

### Security Features

- CSRF protection
- SQL injection prevention (parameterized queries)
- XSS protection
- Rate limiting
- Secure file uploads
- HTTPS enforcement in production

### Security Headers

The application includes security headers:
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Content-Security-Policy

## Performance

### Caching

- Redis for session storage
- Query result caching
- Static file caching
- API response caching

### Optimization

- Database query optimization
- Image compression
- Lazy loading
- CDN integration ready

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write tests for new features
- Update documentation
- Use meaningful commit messages

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the GitHub repository
- Check the documentation
- Contact the development team

## Roadmap

### Upcoming Features

- [ ] Mobile app (React Native)
- [ ] Advanced search with filters
- [ ] Video interviews
- [ ] Skills assessment
- [ ] Payment integration
- [ ] Multi-language support
- [ ] Advanced analytics
- [ ] API for third-party integrations

### Technical Improvements

- [ ] GraphQL API
- [ ] Advanced caching strategies
- [ ] Real-time notifications
- [ ] Machine learning recommendations

## Acknowledgments

- OpenStreetMap contributors for map data
- Tailwind CSS team for the CSS framework
- Flask community for the web framework
- Neo4j team for the graph database
- All contributors and supporters

---

**Catanduanes Connect** - Connecting communities, creating opportunities.