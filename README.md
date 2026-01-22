# Batch LLM Comparison

A Python project to compare batch processing performance between OpenAI and Google Gemini APIs.

## Features

- **OpenAI Batch API** integration using official Python client
- **Google Gemini Batch API** integration with inline requests
- **Concurrent race mode** to run both providers simultaneously
- **Cost comparison** showing pricing differences (50% batch discount)
- **Result parsing** with JSON extraction

## Requirements

- Python 3.10+
- OpenAI API key
- Google AI API key

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/batch-llm-comparison.git
cd batch-llm-comparison

# Install dependencies
pip install -e .

# Or with uv
uv pip install -e .
```

## Configuration

Set your API keys as environment variables:

```bash
# For bash/zsh
export OPENAI_API_KEY="sk-..."
export GOOGLE_AI_API_KEY="AIza..."

# Or create a .env file
cp .env.example .env
# Edit .env with your keys
```

## Usage

### Simple Comparison (Synchronous)

```bash
python examples/simple_compare.py
```

### Advanced Comparison (Async)

```bash
python -m batch_llm.compare
```

## API Pricing

Both providers offer 50% discount for batch processing:

| Provider | Model | Batch Price | Regular Price |
|----------|-------|-------------|---------------|
| OpenAI | gpt-4o-mini | $0.075/M tokens | $0.15/M tokens |
| Gemini | gemini-1.5-flash | $0.0375/M tokens | $0.075/M tokens |

**Gemini is 2x cheaper for batch processing!**

## Output Example

```
======================================
🏁 BATCH API RACE: OpenAI vs Gemini
======================================
Processing 5 calls
Both using async Batch APIs with 50% discount

🔵 OpenAI Batch API: Starting...
🔵 OpenAI: Uploading batch file...
🔵 OpenAI: Creating batch job...
🔵 OpenAI: Batch ID: batch_abc123
🔵 OpenAI: Polling for completion...
🔵 OpenAI: ✅ COMPLETED in 45.2s

🟢 Gemini Batch API: Starting...
🟢 Gemini: Creating batch job...
🟢 Gemini: Batch job created: projects/*/locations/*/batchPredictionJobs/xyz789
🟢 Gemini: ✅ COMPLETED in 38.7s

======================================
🏁 RACE RESULTS
======================================

⏱️  Processing Time:
  🔵 OpenAI:   45.2s
  🟢 Gemini:   38.7s

🏆 Winner: Gemini
⏱️  Time difference: 6.5s
⚡ Gemini is 1.2x faster

💰 Cost Comparison (per 1M tokens):
   Gemini Batch: $0.0375 (50% off)
   OpenAI Batch: $0.075 (50% off)
   → Gemini is 2x cheaper for batch!

⏱️  Total race time: 45.2s
======================================
```

## How It Works

### OpenAI Batch API

1. Create JSONL file with batch requests
2. Upload file to OpenAI
3. Create batch job with uploaded file
4. Poll for completion
5. Download and parse results

### Gemini Batch API

1. Create inline batch requests
2. Create batch prediction job
3. Poll for completion
4. Retrieve inline results
5. Parse JSON responses

## Project Structure

```
batch-llm-comparison/
├── batch_llm/
│   ├── __init__.py
│   └── compare.py          # Advanced async comparison
├── examples/
│   └── simple_compare.py   # Simple sync comparison
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

## License

MIT
