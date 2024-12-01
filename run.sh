#!/bin/bash

# Get the current timestamp
TIMESTAMP=$(date +%s)

# Print the timestamp
echo "Running Docker Compose with TIMESTAMP=$TIMESTAMP"

# Run Docker Compose with the TIMESTAMP environment variable
TIMESTAMP=$TIMESTAMP docker-composer down -v && docker rmi -f $(docker images -aq) && docker-compose up -d