# Enterprise Architecture Solution

A comprehensive Enterprise Architecture Solution with GenAI-powered features, built on Essential Cloud with integrations for SharePoint, Microsoft Entra ID, Halo ITSM, and Power BI.

## Overview

This solution provides a complete enterprise architecture management platform for North Metropolitan TAFE, allowing them to create, manage, and visualize architecture artifacts across all domains defined in the WA Enterprise Architecture Framework (WEAF).

### Key Features

- **Central Repository**: Store and manage all EA artifacts in a structured, searchable repository
- **Comprehensive Modeling**: Support for all architecture domains (Performance, Business, Services, Data, Technology)
- **Flexible Visualization**: Create diagrams, matrices, heatmaps, and roadmaps
- **GenAI-Powered Features**: AI assistance for modeling, documentation, impact analysis, and pattern recognition
- **System Integrations**: Connect with Halo ITSM, Microsoft Entra ID, SharePoint, and Power BI

## Technology Stack

- **Foundation**: Essential Cloud EA platform
- **Backend**: Supabase (PostgreSQL + Authentication)
- **GenAI Engine**: OpenAI API and Agents SDK
- **Frontend**: React with Tailwind CSS
- **Authentication**: Microsoft Entra ID integration

## Project Structure

```
├── backend/                 # Backend services and API
│   ├── database/            # Database schema and migrations
│   ├── integrations/        # System integrations (Halo, SharePoint, etc.)
│   └── genai/               # OpenAI integration for GenAI features
├── frontend/                # Frontend application
│   ├── public/              # Static assets
│   └── src/                 # Source code
│       ├── components/      # React components
│       ├── pages/           # Page components
│       ├── services/        # API services
│       └── utils/           # Utility functions
└── docs/                    # Documentation
    ├── architecture/        # Architecture documentation
    └── user-guides/         # User guides
```

## Getting Started

See [GETTING_STARTED.md](./docs/GETTING_STARTED.md) for detailed setup instructions.

## License

This project is proprietary software developed for North Metropolitan TAFE.