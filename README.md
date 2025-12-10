# Cartesia German TTS Test (LiveKit)

This repository contains a test script for verifying the Cartesia TTS plugin with German voice configuration and Deepgram fallback using LiveKit agents.

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

Install LiveKit agents and TTS plugins:

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install livekit-agents livekit-plugins-cartesia livekit-plugins-deepgram
```

### Required API Keys

Set the following environment variables:

```bash
export CARTESIA_API_KEY="your_cartesia_api_key"
export DEEPGRAM_API_KEY="your_deepgram_api_key"
```

Alternatively, copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
# Edit .env with your API keys
```

## Usage

### Run the Test

```bash
python test_cartesia_german_tts.py
```

Or make it executable and run directly:

```bash
chmod +x test_cartesia_german_tts.py
./test_cartesia_german_tts.py
```

### Expected Output

The script will:
1. Initialize both Cartesia and Deepgram TTS services
2. Test synthesis of German text: "Es freut mich, Sie kennenzulernen, Ich hoffe, Sie haben einen schönen Tag"
3. Log detailed information about the process
4. Report the number of audio frames generated and total bytes
5. Print a summary of test results

### Example Output

```
============================================================
Starting Cartesia German TTS Test (LiveKit)
============================================================
2025-12-10 10:00:00 - __main__ - INFO - Initializing Cartesia TTS with German voice configuration...
2025-12-10 10:00:00 - __main__ - INFO - Cartesia TTS initialized successfully
2025-12-10 10:00:00 - __main__ - INFO - Configuration:
2025-12-10 10:00:00 - __main__ - INFO -   - Model: sonic-3-2025-10-27
2025-12-10 10:00:00 - __main__ - INFO -   - Voice: viktoria-german (b9de4a89-2257-424b-94c2-db18ba68c81a)
2025-12-10 10:00:00 - __main__ - INFO -   - Language: de (German)
2025-12-10 10:00:00 - __main__ - INFO -   - Speed: 0.2
2025-12-10 10:00:00 - __main__ - INFO -   - Emotions: positivity:highest, curiosity:highest

============================================================
Testing Cartesia (primary) TTS synthesis
Text: Es freut mich, Sie kennenzulernen, Ich hoffe, Sie haben einen schönen Tag
============================================================

2025-12-10 10:00:00 - __main__ - INFO - Starting synthesis...
2025-12-10 10:00:01 - __main__ - DEBUG - Synthesis started
2025-12-10 10:00:01 - __main__ - DEBUG - Audio frame 1: 4096 bytes
2025-12-10 10:00:01 - __main__ - DEBUG - Audio frame 2: 4096 bytes
...
2025-12-10 10:00:02 - __main__ - DEBUG - Synthesis finished
2025-12-10 10:00:02 - __main__ - INFO - 
✓ SUCCESS: Generated 42 audio frames (172032 bytes total)

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
   ```bash
   echo $CARTESIA_API_KEY
   echo $DEEPGRAM_API_KEY
   ```

2. **Network Connection**: Verify you can reach the API endpoints
   ```bash
   curl -I https://api.cartesia.ai
   curl -I https://api.deepgram.com
   ```

3. **Voice ID**: Confirm the voice ID `b9de4a89-2257-424b-94c2-db18ba68c81a` is correct for the Cartesia model

4. **Text Input**: Ensure the German text is properly formatted and encoded

5. **Logs**: Check the detailed logs (DEBUG level) for specific error messages

### Common Issues

- **ImportError**: 
  ```
  ERROR: Required LiveKit modules not found.
  ```
  **Solution**: Install the required packages:
  ```bash
  pip install livekit-agents livekit-plugins-cartesia livekit-plugins-deepgram
  ```

- **API Key Not Set**: 
  ```
  ERROR: CARTESIA_API_KEY environment variable not set
  ```
  **Solution**: Set environment variables or use a `.env` file

- **Rate Limiting**: If testing repeatedly, you may hit rate limits
  **Solution**: Wait a few minutes between test runs

- **Model Not Found**: If the model name has changed, update the model parameter in the script

### Getting API Keys

- **Cartesia**: Sign up at [https://cartesia.ai](https://cartesia.ai) and get your API key from the dashboard
- **Deepgram**: Sign up at [https://console.deepgram.com](https://console.deepgram.com) and create an API key

## Purpose

This test script helps debug the "no audio frames were pushed" error by:

1. Providing detailed logging at each step of the synthesis process
2. Counting and reporting audio frames and bytes generated
3. Testing both primary (Cartesia) and fallback (Deepgram) TTS services
4. Handling errors gracefully with informative messages
5. Verifying the complete TTS pipeline works end-to-end with LiveKit

## Architecture

The script uses LiveKit's agents framework with:
- **Primary TTS**: Cartesia plugin with German voice configuration
- **Fallback TTS**: Deepgram plugin for reliability
- **Async Streams**: Uses async iterators to process synthesis events
- **Event Types**: Tracks STARTED, AUDIO, FINISHED, and ERROR events

## Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed
- `130`: Test interrupted by user (Ctrl+C)

## Development

To modify the test:

1. Edit configuration in `initialize_cartesia_tts()` or `initialize_deepgram_fallback()`
2. Change test text in the `german_text` variable
3. Adjust logging level in `logging.basicConfig()` (DEBUG, INFO, WARNING, ERROR)
4. Add additional test cases in `run_tests()` method

## License

This test script is provided as-is for testing and debugging purposes.
