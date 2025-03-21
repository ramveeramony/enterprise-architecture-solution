# Getting Started

This guide will help you set up the Enterprise Architecture Solution project for development.

## Prerequisites

- Node.js 18+
- Python 3.9+
- Git
- Supabase CLI
- Docker and Docker Compose (for local Supabase development)
- Access to OpenAI API
- Microsoft developer account (for Entra ID integration)

## Environment Setup

1. Clone the repository:

```bash
git clone https://github.com/ramveeramony/enterprise-architecture-solution.git
cd enterprise-architecture-solution
```

2. Create environment files:

```bash
cp .env.example .env
```

Update the `.env` file with your API keys and configuration settings.

## Backend Setup

1. Set up the Supabase project:

```bash
cd backend
supabase init
supabase start
```

2. Apply the database migrations:

```bash
supabase db push
```

3. Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Frontend Setup

1. Install Node.js dependencies:

```bash
cd frontend
npm install
```

2. Start the development server:

```bash
npm run dev
```

## Integration Configuration

See the [Integration Setup Guide](./integrations/SETUP.md) for detailed instructions on configuring the system integrations.

## Running Tests

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

## Deployment

See the [Deployment Guide](./DEPLOYMENT.md) for information on deploying the application to production environments.