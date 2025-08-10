#!/bin/bash
set -e

# Wait for Grafana to be ready
echo "Waiting for Grafana to start..."
until curl -f http://grafana:3000/api/health > /dev/null 2>&1; do
    sleep 2
done

echo "Grafana is ready. Creating service account for MCP..."

# Create service account for MCP
SERVICE_ACCOUNT_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "name": "mcp-server",
    "role": "Editor",
    "isDisabled": false
  }' \
  "http://admin:admin@grafana:3000/api/serviceaccounts")

SERVICE_ACCOUNT_ID=$(echo $SERVICE_ACCOUNT_RESPONSE | grep -o '"id":[0-9]*' | cut -d':' -f2)

if [ "$SERVICE_ACCOUNT_ID" != "null" ]; then
  echo "Service account created with ID: $SERVICE_ACCOUNT_ID"
  
  # Create API key for the service account
  API_KEY_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{
      "name": "mcp-token",
      "role": "Editor"
    }' \
    "http://admin:admin@grafana:3000/api/serviceaccounts/$SERVICE_ACCOUNT_ID/tokens")
  
  API_KEY=$(echo $API_KEY_RESPONSE | grep -o '"key":"[^"]*"' | cut -d':' -f2 | tr -d '"')
  
  if [ "$API_KEY" != "null" ]; then
    echo "MCP API Key created successfully"
    echo "GRAFANA_API_KEY=$API_KEY" > /var/lib/grafana/mcp-credentials.env
    echo "GRAFANA_API_KEY=$API_KEY" > /var/lib/grafana/mcp-env.sh
    chmod +x /var/lib/grafana/mcp-env.sh
    echo "Use this API key in your MCP configuration: $API_KEY"
    echo "API key saved to /var/lib/grafana/mcp-credentials.env and /var/lib/grafana/mcp-env.sh"
  else
    echo "Failed to create API key"
  fi
else
  echo "Failed to create service account"
fi
