# Using Ollama with Doctown

Doctown supports using Ollama for local, private AI processing with **zero rate limits**.

## Quick Start (Local Development)

### 1. Install Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Or visit https://ollama.com/download
```

### 2. Pull a Model

```bash
# Recommended: Fast and capable
ollama pull llama3.1:8b

# Alternative: Smaller, faster
ollama pull llama3.2:3b

# Alternative: Larger, more capable
ollama pull llama3.1:70b
```

### 3. Configure Environment

Create or update `.env` in the project root:

```bash
# Use Ollama instead of OpenAI
USE_OLLAMA=true

# Model to use (default: llama3.1:8b)
OLLAMA_MODEL=llama3.1:8b

# Ollama server URL (default works for local)
OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
```

### 4. Run Doctown

```bash
# Process a docpack with Ollama
./cli/target/release/localdoc run my-project.docpack
```

That's it! No API keys, no rate limits, completely private.

## Production Deployment (RunPod)

For cloud deployment with GPU acceleration:

### 1. Deploy Ollama on RunPod

```bash
# Use the official Ollama template
# Or custom Dockerfile:
```

**Dockerfile for RunPod:**
```dockerfile
FROM ollama/ollama:latest

# Expose Ollama API
EXPOSE 11434

# Pull models on container start
RUN ollama pull llama3.1:8b

CMD ["ollama", "serve"]
```

### 2. Configure Doctown to Use RunPod

```bash
# In your .env
USE_OLLAMA=true
OLLAMA_BASE_URL=https://your-runpod-instance.com/v1
OLLAMA_MODEL=llama3.1:8b
```

## Model Recommendations

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| `llama3.2:3b` | 3GB | ⚡⚡⚡ | ⭐⭐ | Simple docs, fast iteration |
| `llama3.1:8b` | 8GB | ⚡⚡ | ⭐⭐⭐ | **Recommended default** |
| `llama3.1:70b` | 70GB | ⚡ | ⭐⭐⭐⭐⭐ | Complex analysis, best quality |
| `codellama:13b` | 13GB | ⚡⚡ | ⭐⭐⭐⭐ | Code-focused documentation |

## Performance Tips

### 1. GPU Acceleration (Optional but Recommended)

Ollama automatically uses GPU if available:
- **NVIDIA**: CUDA support built-in
- **Apple Silicon**: Metal acceleration built-in
- **CPU only**: Still works, just slower

### 2. Adjust Context Window

For large codebases, increase context:

```bash
# In Ollama modelfile
PARAMETER num_ctx 8192  # Default: 2048
```

### 3. Concurrent Processing

Ollama handles multiple requests efficiently. For batch processing:

```bash
# Process multiple docpacks in parallel
for pack in *.docpack; do
  localdoc run "$pack" &
done
wait
```

## Cost Comparison

### OpenAI GPT-4o
- $15 per 1M input tokens
- Rate limits: 30k TPM
- **Cost for 100 docpacks**: ~$30-50

### Ollama (Self-Hosted)
- One-time GPU cost or RunPod rental
- No rate limits
- **Cost for 100 docpacks**: $0 (after infrastructure)

### RunPod Pricing
- **RTX 4090**: ~$0.69/hour (~$500/month 24/7)
- **A40**: ~$0.79/hour (~$570/month)
- **Break-even**: ~50 docpacks/month vs OpenAI

## Troubleshooting

### "Cannot connect to Ollama"

1. Check Ollama is running:
```bash
ollama list  # Should show your models
```

2. Test API directly:
```bash
curl http://localhost:11434/api/tags
```

3. For Docker, ensure `host.docker.internal` resolves:
```bash
# Add to docker-compose.yml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

### "Model not found"

Pull the model first:
```bash
ollama pull llama3.1:8b
```

### Slow Performance

1. Check if GPU is being used:
```bash
nvidia-smi  # For NVIDIA
```

2. Use a smaller model:
```bash
OLLAMA_MODEL=llama3.2:3b
```

3. Reduce concurrent requests

## Switching Between OpenAI and Ollama

You can easily switch by changing one environment variable:

```bash
# Use OpenAI
USE_OLLAMA=false
OPENAI_API_KEY=sk-...

# Use Ollama
USE_OLLAMA=true
```

This makes it easy to:
- Develop locally with Ollama
- Use OpenAI for production if needed
- Let users choose their preference
