# Cartesia German TTS Test

This repository contains a test script for verifying the Cartesia TTS plugin with German voice configuration and Deepgram fallback.

## Overview

The test script (`test_cartesia_german_tts.py`) initializes and tests:

1. **Primary TTS (Cartesia)** with configuration:
   - Model: `sonic-3-2025-10-27`
   - Voice: `viktoria-german` (ID: `b9de4a89-2257-424b-94c2-db18ba68c81a`)
   - Language: `de` (German)
   - Speed: `0.2`
   - Emotions: `positivity:highest`, `curiosity:highest`

2. **Fallback TTS (Deepgram)** with configuration:
   - Model: `aura-2-arcas-en`

## Prerequisites

### Required Python Packages

```bash
pip install pipecat-ai
```

### Required API Keys

Set the following environment variables:

```bash
export CARTESIA_API_KEY="your_cartesia_api_key"
export DEEPGRAM_API_KEY="your_deepgram_api_key"
```

## Usage

### Run the Test

```bash
python test_cartesia_german_tts.py
```

### Expected Output

The script will:
1. Initialize both Cartesia and Deepgram TTS services
2. Test synthesis of German text: "Es freut mich, Sie kennenzulernen, Ich hoffe, Sie haben einen schönen Tag"
3. Log detailed information about the process
4. Report the number of audio frames generated
5. Print a summary of test results

### Example Output

```
============================================================
Starting Cartesia German TTS Test
============================================================
2025-12-10 10:00:00 - INFO - Initializing Cartesia TTS with German voice configuration...
2025-12-10 10:00:00 - INFO - Cartesia TTS initialized successfully
2025-12-10 10:00:00 - INFO - Configuration:
2025-12-10 10:00:00 - INFO -   - Model: sonic-3-2025-10-27
2025-12-10 10:00:00 - INFO -   - Voice: viktoria-german (b9de4a89-2257-424b-94c2-db18ba68c81a)
2025-12-10 10:00:00 - INFO -   - Language: de (German)
2025-12-10 10:00:00 - INFO -   - Speed: 0.2
2025-12-10 10:00:00 - INFO -   - Emotions: positivity:highest, curiosity:highest

============================================================
Testing Cartesia (primary) TTS synthesis
Text: Es freut mich, Sie kennenzulernen, Ich hoffe, Sie haben einen schönen Tag
============================================================

2025-12-10 10:00:00 - INFO - Starting synthesis...
2025-12-10 10:00:01 - INFO - ✓ SUCCESS: Generated 42 audio frames

============================================================
TEST SUMMARY
============================================================
Cartesia Initialization:     ✓ PASS
Cartesia Synthesis:          ✓ PASS
Deepgram Initialization:     ✓ PASS
Deepgram Synthesis:          ✓ PASS
============================================================
✓ ALL TESTS PASSED
============================================================
```

## Troubleshooting

### No Audio Frames Generated

If you see "No audio frames were generated", check:

1. **API Keys**: Ensure your API keys are valid and properly set
2. **Network Connection**: Verify you can reach the API endpoints
3. **Voice ID**: Confirm the voice ID is correct for the Cartesia model
4. **Text Input**: Ensure the text is properly formatted
5. **Logs**: Check the detailed logs for specific error messages

### Common Issues

- **ImportError**: Install pipecat-ai: `pip install pipecat-ai`
- **API Key Not Set**: Set environment variables as shown above
- **Rate Limiting**: If testing repeatedly, you may hit rate limits

## Purpose

This test script helps debug the "no audio frames were pushed" error by:

1. Providing detailed logging at each step
2. Counting and reporting audio frames generated
3. Testing both primary and fallback TTS services
4. Handling errors gracefully with informative messages
5. Verifying the complete TTS pipeline works end-to-end

## Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed
- `130`: Test interrupted by user (Ctrl+C)
