# Wine API
## Table of Contents
- [Wine API](#wine-api)
  - [Table of Contents](#table-of-contents)
- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Entity Relationship Diagram](#entity-relationship-diagram)
- [API Documentation](#api-documentation)
- [How to run](#how-to-run)
- [Contributing](#contributing)

# Introduction
This is a API for our research in Wine Analysis and Prediction. The API is built using Flask and deployed on Heroku. The API is used to predict the quality of wine based on the input parameters. The API is built using [Django](https://www.djangoproject.com/). 
We use [Postgres](https://www.postgresql.org/) as our database. We also use [Redis](https://redis.io/) as our cache database.

# Prerequisites
- [Python](https://www.python.org/) 3.9 or above
- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Postgres](https://www.postgresql.org/)
- [Redis](https://redis.io/)

# Entity Relationship Diagram

# API Endpoint
Here is the table of the API endpoint. You can also see the documentation after running the API on [Swagger](http://localhost:8000/doc/).

## Wine
Base URL: http://localhost:8000/api/v1/wines

<table>
    <tr>
        <th>Endpoint</th>
        <th>Full path</th>
        <th>Method</th>
        <th>Description</th>
        <th>Parameters</th>
    </tr>

<tr>
    <td>/</td>
    <td>/</td>
    <td>GET</td>
    <td>Get all wines</td>
    <td></td>
</tr>

<tr>
    <td>/</td>
    <td>/</td>
    <td>POST</td>
    <td>Create a new wine</td>
    <td></td>
</tr>

<tr>
    <td>/{id}</td>
    <td>/{id}</td>
    <td>GET</td>
    <td>Get a wine by id</td>
    <td></td>
</tr>
</table>
