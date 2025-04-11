# pysdk - Universal SDK for Async API Connections

pysdk is a powerful Python package that provides a universal software development kit (SDK) for connecting to various APIs in an asynchronous manner. It aims to simplify the process of interacting with APIs by offering a consistent interface and handling common tasks such as authentication, rate limiting, and error handling.

## Current features

- **Async Support**: pysdk is built using async/await syntax, allowing you to write efficient and non-blocking code when working with APIs.
- **Universal Interface**: The package provides a unified interface for connecting to different APIs, reducing the learning curve when switching between services.
- **Standardized syntax**: Standard syntax for GET, POST, PUT and DELETE requests
- **Pydantic support**: use BaseModels from pydantic to define and validates inputs of the api
- **Basic error handling**: Automatically retries for timeouts

## Future/ optional features

- **Improved typing and IDE hinting**: Addition of defining pydantic BaseModel for responses.
- **Api-libary**: Storge generated code in an API library, ready to be used in your projects
- **Authentication Handling**: pysdk supports multiple authentication mechanisms, including API keys, OAuth, and JWT tokens, making it easy to connect to secure APIs.
- **Rate Limiting**: The SDK includes rate limiting capabilities, helping you stay within the API's rate limits and avoid potential disruptions.
- **Advanced Error Handling**: pysdk provides robust error handling mechanisms, allowing you to handle and log API errors gracefully.
- **Telemetry**: When an universal SDK is used for api communication, telemetry becomes very powerful to log data streams
- **MCP server generation**: The generated code is perfectly suited for MCP endpoints, making it easy to build your own MCP for a given API.

## Installation

You can install pysdk using pip:

`pip install git+https://github.com/jeroenvermunt/async-api`

## Usage
Checkout the examples to see pysdk in action
