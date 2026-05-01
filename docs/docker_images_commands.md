# Docker Images Commands Documentation

This document describes the Docker image viewing commands available in the AI Admin Server.

## Overview

The AI Admin Server provides comprehensive commands for viewing and managing Docker images, both local and remote. These commands allow you to:

- View local Docker images
- Search and view remote Docker Hub images
- Get detailed information about specific images
- Compare local and remote images
- Check for available updates

## Available Commands

### 1. docker_images - View Local Images

Lists Docker images on the local system.

**Parameters:**
- `repository` (string, optional): Show images for specific repository
- `all_images` (boolean, default: false): Show all images (including intermediate layers)
- `quiet` (boolean, default: false): Only show image IDs
- `no_trunc` (boolean, default: false): Don't truncate output
- `format_output` (string, default: "table"): Output format ("table" or "json")
- `filter_dangling` (boolean, optional): Filter dangling images

**Example:**
```json
{
  "method": "docker_images",
  "params": {
    "repository": "nginx",
    "format_output": "json",
    "all_images": false
  }
}
```

### 2. docker_hub_images - View Remote Docker Hub Images

Search and view Docker images in Docker Hub.

**Parameters:**
- `query` (string, optional): Search query for image names
- `username` (string, optional): Specific username to search in
- `repository` (string, optional): Specific repository name
- `limit` (integer, default: 20): Maximum number of results (1-100)
- `page` (integer, default: 1): Page number for pagination
- `official_only` (boolean, default: false): Show only official images
- `automated_only` (boolean, default: false): Show only automated builds
- `sort_by` (string, default: "stars"): Sort field ("stars", "pulls", "name", "updated")
- `order` (string, default: "desc"): Sort order ("asc" or "desc")
- `include_tags` (boolean, default: false): Include available tags in results

**Example:**
```json
{
  "method": "docker_hub_images",
  "params": {
    "query": "nginx",
    "limit": 10,
    "official_only": true,
    "sort_by": "stars",
    "order": "desc"
  }
}
```

### 3. docker_hub_image_info - Get Detailed Image Information

Get detailed information about a specific Docker Hub image.

**Parameters:**
- `image_name` (string, required): Full image name (e.g., 'library/nginx', 'myuser/myapp')
- `tag` (string, default: "latest"): Specific tag to get info for
- `include_layers` (boolean, default: false): Include layer information
- `include_usage` (boolean, default: false): Include usage statistics

**Example:**
```json
{
  "method": "docker_hub_image_info",
  "params": {
    "image_name": "library/nginx",
    "tag": "latest",
    "include_layers": true
  }
}
```

### 4. docker_images_compare - Compare Local and Remote Images

Compare local Docker images with remote Docker Hub images.

**Parameters:**
- `image_name` (string, optional): Specific image name to compare
- `include_all_local` (boolean, default: false): Compare all local images
- `check_updates` (boolean, default: true): Check for available updates
- `include_dangling` (boolean, default: false): Include dangling images in comparison

**Example:**
```json
{
  "method": "docker_images_compare",
  "params": {
    "image_name": "nginx",
    "check_updates": true,
    "include_dangling": false
  }
}
```

## Response Formats

### Success Response

All commands return a success response with the following structure:

```json
{
  "status": "success",
  "data": {
    // Command-specific data
  },
  "timestamp": "2024-01-01T12:00:00.000Z",
  "execution_time_ms": 150.5
}
```

### Error Response

Error responses follow this structure:

```json
{
  "status": "error",
  "message": "Error description",
  "code": "ERROR_CODE",
  "data": {
    // Additional error information
  }
}
```

## Common Error Codes

- `IMAGES_ERROR`: General error in local images command
- `HUB_IMAGES_ERROR`: Error in Docker Hub images command
- `HUB_IMAGE_INFO_ERROR`: Error in Docker Hub image info command
- `IMAGES_COMPARE_ERROR`: Error in images comparison command
- `NETWORK_ERROR`: Network-related errors
- `VALIDATION_ERROR`: Input validation errors
- `INTERNAL_ERROR`: Unexpected internal errors

## Usage Examples

### View All Local Images
```json
{
  "method": "docker_images",
  "params": {
    "format_output": "json"
  }
}
```

### Search Popular Docker Hub Images
```json
{
  "method": "docker_hub_images",
  "params": {
    "query": "python",
    "limit": 5,
    "official_only": true
  }
}
```

### Get Detailed Info About an Image
```json
{
  "method": "docker_hub_image_info",
  "params": {
    "image_name": "library/ubuntu",
    "tag": "20.04",
    "include_layers": true
  }
}
```

### Compare Local Images with Remote
```json
{
  "method": "docker_images_compare",
  "params": {
    "include_all_local": true,
    "check_updates": true
  }
}
```

## Best Practices

1. **Use pagination**: When working with large result sets, use the `limit` and `page` parameters
2. **Filter results**: Use filters like `official_only` or `automated_only` to narrow down results
3. **Include tags when needed**: Use `include_tags: true` when you need tag information
4. **Handle errors gracefully**: Always check for error responses and handle them appropriately
5. **Cache results**: Consider caching results for frequently accessed images to improve performance

## Rate Limiting

The Docker Hub API has rate limits. The commands include appropriate delays and error handling for rate limit scenarios. For production use, consider implementing additional rate limiting mechanisms.

## Security Considerations

- Commands only read information and do not modify any images
- No authentication is required for public Docker Hub images
- Private images require appropriate authentication
- Network requests are made with appropriate timeouts and error handling 