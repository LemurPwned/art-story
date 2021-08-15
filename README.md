# ART story 

## Description
A search engine for art.
Using elasticsearch and basic feature generation to create searchable mockups.

## Setup
### Elasticsearch 
Elasticsearch is used as a backend service for all of the search features.
Running the ES instance can be done with Docker:
```bash 
docker run -p 9200:9200 -p 9300:9300 \
           -e "discovery.type=single-node" \
           docker.elastic.co/elasticsearch/elasticsearch:7.13.4
```