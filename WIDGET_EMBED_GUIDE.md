# Embeddable Query Widgets Guide

Add live, interactive query widgets to your blog or website with customizable themes and secure API key management.

## 🎯 Features

- ✅ **iframe Embed Code** - Simple copy-paste embed code
- ✅ **Customizable Themes** - Light, dark, minimal, and custom CSS
- ✅ **API Key Management** - Secure widget-specific API keys
- ✅ **Natural Language Queries** - Users can ask questions in plain English
- ✅ **Responsive Design** - Works on all screen sizes
- ✅ **No Backend Required** - Everything runs client-side

## 🚀 Quick Start

### Step 1: Create a Widget

Create a widget using the API:

```bash
curl -X POST http://localhost:5000/widget/api/create \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_AGENT_API_KEY" \
  -d '{
    "agent_id": "your-agent-id",
    "name": "My Blog Widget",
    "theme": "light",
    "height": "600px",
    "width": "100%"
  }'
```

**Response:**
```json
{
  "success": true,
  "widget_id": "widget_abc123",
  "widget_api_key": "secure-key-here",
  "embed_code": "<iframe src=\"...\"></iframe>",
  "embed_url": "http://localhost:5000/widget/embed/widget_abc123"
}
```

### Step 2: Copy Embed Code

Copy the `embed_code` from the response and paste it into your HTML:

```html
<iframe 
    src="http://localhost:5000/widget/embed/widget_abc123?theme=light"
    width="100%"
    height="600px"
    frameborder="0"
    allow="clipboard-read; clipboard-write"
    style="border: none; border-radius: 8px;">
</iframe>
```

### Step 3: Done!

Your widget is now live! Users can query your data using natural language.

## 🎨 Themes

### Available Themes

1. **Light** (default) - Clean white background
2. **Dark** - Dark mode with dark background
3. **Minimal** - Minimalist design

### Using Themes

Add `?theme=dark` to the embed URL:

```html
<iframe src="http://localhost:5000/widget/embed/widget_abc123?theme=dark"></iframe>
```

### Custom CSS

For advanced customization, use custom CSS when creating the widget:

```bash
curl -X POST http://localhost:5000/widget/api/create \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_AGENT_API_KEY" \
  -d '{
    "agent_id": "your-agent-id",
    "name": "Custom Widget",
    "theme": "light",
    "custom_css": "
      :root {
        --widget-primary-color: #ff6b6b;
        --widget-bg-color: #f8f9fa;
      }
    "
  }'
```

### CSS Variables

Customize the widget using CSS variables:

- `--widget-bg-color` - Background color
- `--widget-text-color` - Text color
- `--widget-primary-color` - Primary button color
- `--widget-card-bg` - Card background
- `--widget-border-color` - Border color
- `--widget-input-bg` - Input background
- `--widget-button-text` - Button text color
- `--widget-hover-bg` - Hover background
- `--widget-error-bg` - Error background
- `--widget-error-text` - Error text color

## 🔐 API Key Management

### Widget API Keys

Each widget has its own API key for security:

- **Agent API Key** - Used to create/manage widgets
- **Widget API Key** - Used by the widget to execute queries

### Regenerating Keys

If a widget key is compromised, regenerate it:

```bash
curl -X POST http://localhost:5000/widget/api/widget_abc123/regenerate-key \
  -H "X-API-Key: YOUR_AGENT_API_KEY"
```

### Domain Restrictions (Optional)

Restrict widget usage to specific domains:

```bash
curl -X PUT http://localhost:5000/widget/api/widget_abc123 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_AGENT_API_KEY" \
  -d '{
    "allowed_domains": ["example.com", "blog.example.com"]
  }'
```

## 📚 API Reference

### Create Widget

```http
POST /widget/api/create
Content-Type: application/json
X-API-Key: YOUR_AGENT_API_KEY

{
  "agent_id": "string (required)",
  "name": "string (required)",
  "theme": "light|dark|minimal (optional)",
  "height": "string (optional, default: 600px)",
  "width": "string (optional, default: 100%)",
  "custom_css": "string (optional)",
  "custom_js": "string (optional)",
  "allowed_domains": ["array of strings (optional)"]
}
```

### List Widgets

```http
GET /widget/api/list
X-API-Key: YOUR_AGENT_API_KEY
```

### Get Widget

```http
GET /widget/api/{widget_id}
X-API-Key: YOUR_AGENT_API_KEY
```

### Update Widget

```http
PUT /widget/api/{widget_id}
Content-Type: application/json
X-API-Key: YOUR_AGENT_API_KEY

{
  "name": "string (optional)",
  "theme": "string (optional)",
  "height": "string (optional)",
  "width": "string (optional)",
  "custom_css": "string (optional)",
  "custom_js": "string (optional)"
}
```

### Delete Widget

```http
DELETE /widget/api/{widget_id}
X-API-Key: YOUR_AGENT_API_KEY
```

### Get Embed Code

```http
GET /widget/api/{widget_id}/embed-code?theme=light&height=600px&width=100%
X-API-Key: YOUR_AGENT_API_KEY
```

### Regenerate Widget Key

```http
POST /widget/api/{widget_id}/regenerate-key
X-API-Key: YOUR_AGENT_API_KEY
```

## 💡 Examples

### Example 1: Basic Widget

```html
<!DOCTYPE html>
<html>
<head>
    <title>My Blog</title>
</head>
<body>
    <h1>Query My Data</h1>
    <iframe 
        src="http://localhost:5000/widget/embed/widget_abc123"
        width="100%"
        height="600px"
        frameborder="0"
        style="border: none;">
    </iframe>
</body>
</html>
```

### Example 2: Dark Theme Widget

```html
<iframe 
    src="http://localhost:5000/widget/embed/widget_abc123?theme=dark"
    width="100%"
    height="600px"
    frameborder="0"
    style="border: none; border-radius: 8px;">
</iframe>
```

### Example 3: Custom Styled Widget

```html
<div style="max-width: 800px; margin: 0 auto; padding: 20px;">
    <h2>Ask Questions About Our Data</h2>
    <iframe 
        src="http://localhost:5000/widget/embed/widget_abc123?theme=minimal"
        width="100%"
        height="700px"
        frameborder="0"
        style="border: 2px solid #e0e0e0; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    </iframe>
</div>
```

## 🔧 Advanced Customization

### Custom JavaScript

Add custom JavaScript for advanced interactions:

```bash
curl -X POST http://localhost:5000/widget/api/create \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_AGENT_API_KEY" \
  -d '{
    "agent_id": "your-agent-id",
    "name": "Advanced Widget",
    "custom_js": "
      // Add custom event listeners
      document.addEventListener(\"queryComplete\", (e) => {
        console.log(\"Query completed:\", e.detail);
      });
    "
  }'
```

### Responsive Sizing

Use CSS for responsive sizing:

```html
<style>
.widget-container {
    position: relative;
    width: 100%;
    padding-bottom: 75%; /* 4:3 aspect ratio */
    height: 0;
    overflow: hidden;
}

.widget-container iframe {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
}
</style>

<div class="widget-container">
    <iframe src="http://localhost:5000/widget/embed/widget_abc123"></iframe>
</div>
```

## 🛡️ Security Best Practices

1. **Use Widget API Keys** - Never expose agent API keys in widgets
2. **Regenerate Keys** - If compromised, regenerate immediately
3. **Domain Restrictions** - Use `allowed_domains` for production
4. **HTTPS** - Always use HTTPS in production
5. **Rate Limiting** - Widget queries respect agent rate limits

## 📊 Widget Analytics

Track widget usage:

```bash
curl http://localhost:5000/widget/api/widget_abc123 \
  -H "X-API-Key: YOUR_AGENT_API_KEY"
```

Response includes:
- `usage_count` - Total queries executed
- `last_used` - Last query timestamp

## 🐛 Troubleshooting

### Widget Not Loading

- Check if widget exists: `GET /widget/api/{widget_id}`
- Verify agent API key is correct
- Check browser console for errors

### Queries Failing

- Verify widget API key is valid
- Check agent permissions
- Review agent logs

### Styling Issues

- Clear browser cache
- Check custom CSS syntax
- Verify theme parameter

## 📝 Next Steps

- [API Documentation](../README.md#api-endpoints)
- [Agent Management](../README.md#api-endpoints)
- [Security Guide](../SECURITY.md)

---

**Questions?** Check the [troubleshooting](#-troubleshooting) section or review the [main README](../README.md).

