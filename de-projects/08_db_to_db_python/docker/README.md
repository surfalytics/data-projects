### Running docker container with PostgreSQL and imported sales data

Instructions:
1. Ensure the `sales_data.csv` file is in the `./source-data` folder
2. In the terminal, change the directory to the `docker`
3. Run the `docker build -t postgres-image .` command to build the docker image
4. Run the `docker run --name postgres-cont -e POSTGRES_PASSWORD=1 -d -p 5433:5432 postgres-image` command to run a container
