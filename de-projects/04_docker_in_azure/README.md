# Docker in Azure

## Objective
Deploy a Docker container in Azure, integrate with PostgreSQL using Docker Compose, and automate deployment using GitHub CI/CD.

## Key Terms
- **Docker Container:** Lightweight, standalone package containing everything needed to run software.
- **Azure:** Microsoft's cloud computing service for application deployment and management.
- **Docker Compose:** Tool for defining and running multi-container Docker applications.
- **PostgreSQL (Postgres):** Open-source relational database management system.
- **GitHub CI/CD:** Continuous Integration and Deployment methodologies using GitHub Actions.
- **Azure Container Registry:** Azure service for storing and managing container images.

## Prerequisites
1. [Create Azure trial account](https://azure.microsoft.com/en-ca/free/search/?ef_id=_k_Cj0KCQiAj_CrBhD-ARIsAIiMxT_Ya2hhLmqz8eN_H298Of5m5zNqPnwI3d2CjsOJrj3NtY5GdvyJO6MaAo1REALw_wcB_k_&OCID=AIDcmmqz3gd78m_SEM__k_Cj0KCQiAj_CrBhD-ARIsAIiMxT_Ya2hhLmqz8eN_H298Of5m5zNqPnwI3d2CjsOJrj3NtY5GdvyJO6MaAo1REALw_wcB_k_&gad_source=1&gclid=Cj0KCQiAj_CrBhD-ARIsAIiMxT_Ya2hhLmqz8eN_H298Of5m5zNqPnwI3d2CjsOJrj3NtY5GdvyJO6MaAo1REALw_wcB)
2. [Intall Docker](https://docs.docker.com/get-docker/)

## Implementation
1. **Review Existing Container:** Examine the Docker container from the previous session.
2. **Set Up Azure Environment:** Create and configure Azure Container Registry.
3. **Docker Compose Integration:** Write `docker-compose.yml` for the application and PostgreSQL.
4. **GitHub Repository Setup:** Initialize a repository for application code and Docker configurations.
5. **Implement CI/CD with GitHub Actions:** Create workflows for testing and deployment.
6. **Deploy on Azure:** Push the Docker container to Azure Container Registry and deploy to Azure services.
7. **Testing and Validation:** Conduct end-to-end tests to validate deployment and database integration.

## Additional Materials
1. [Docker Docs](https://docs.docker.com/)
2. [Microsoft Azure Docs](https://docs.microsoft.com/en-us/azure/container-service/)
3. [GitHub Docs](https://docs.github.com/en/actions)
4. [PostgreSQL Docs](https://www.postgresql.org/docs/)
5. Online Courses: "Docker for Beginners" on Coursera or Udemy.
6. Blog Posts and Tutorials: Search for tutorials on Docker and PostgreSQL integration, and GitHub Actions CI/CD.
