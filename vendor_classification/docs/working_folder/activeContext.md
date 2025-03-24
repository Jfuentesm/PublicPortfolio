# NAICS Vendor Classification System - Active Context

## Project Overview
We are implementing the NAICS Vendor Classification System as described in the solution design document. This system will automate the process of classifying vendors according to the NAICS (North American Industry Classification System) taxonomy using AI.

## Implementation Approach
We will implement the solution for local development using Docker Compose with the following components:

1. **Web Application Container**: FastAPI-based web service for handling file uploads, job management, and API endpoints
2. **Worker Container**: Celery workers for processing classification tasks asynchronously
3. **Redis Container**: For task queue management and caching
4. **Database Container**: PostgreSQL for storing job information, taxonomy data, and results

## Key Assumptions

1. **API Keys**: For local development, we'll use environment variables for API keys (Azure OpenAI and Tavily)
2. **NAICS Taxonomy**: We'll implement a simplified version of the NAICS taxonomy for demonstration purposes
3. **File Storage**: For local development, we'll use the local filesystem instead of S3
4. **Authentication**: Basic authentication will be implemented for the local development environment

## Development Plan

1. Set up the Docker Compose configuration
2. Implement the core application structure
3. Create data models and database schema
4. Implement the file ingestion and preprocessing component
5. Develop the classification workflow
6. Integrate with Azure OpenAI and Tavily APIs
7. Create the result generation component
8. Implement the web interface
9. Add comprehensive testing
10. Document the setup and usage instructions

## Technical Decisions

1. **FastAPI**: Chosen for its high performance, automatic OpenAPI documentation, and async support
2. **Celery**: For handling long-running classification tasks asynchronously
3. **PostgreSQL**: For robust data storage with transaction support
4. **Docker Compose**: For easy local development and testing
5. **Pydantic**: For data validation and modeling throughout the application