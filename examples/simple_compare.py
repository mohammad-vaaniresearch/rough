#!/usr/bin/env python3
"""
Batch LLM API Comparison: OpenAI vs Gemini
A simpler synchronous version that's easier to run and debug.

Requirements:
    - OPENAI_API_KEY environment variable
    - GOOGLE_AI_API_KEY environment variable

Usage:
    python examples/simple_compare.py
"""

import os
import time
import json
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

# Test data - 5 calls
TEST_CALLS = [
    ("call-1", "Agent: Hello! Customer: My name is John Doe, email john@example.com, phone 555-1234"),
    ("call-2", "Agent: Hi there! Customer: I'm Jane Smith, jane@test.com, 555-5678"),
    ("call-3", "Agent: Good morning! Customer: This is Bob Wilson, bob@company.com, 555-9012"),
    ("call-4", "Agent: Welcome! Customer: Alice Brown here, alice@email.com, 555-3456"),
    ("call-5", "Agent: How can I help? Customer: I'm Charlie Davis, charlie@mail.com, 555-7890"),
]


def create_openai_prompt(transcript: str) -> str:
    """Create extraction prompt for OpenAI"""
    return (
        "Extract the following from this call transcript:\n"
        "- Customer name\n"
        "- Email address\n"
        "- Phone number\n\n"
        f"Transcript: {transcript}\n\n"
        "Return as JSON with keys: customer_name, email, phone"
    )


def create_gemini_prompt(transcript: str) -> str:
    """Create extraction prompt for Gemini"""
    return create_openai_prompt(transcript)  # Same prompt for both


# ============================================================================
# OpenAI Batch API
# ============================================================================

def run_openai_batch():
    """Run OpenAI Batch API test"""
    from openai import OpenAI
    
    print("\n🔵 OpenAI Batch API: Starting...")
    start_time = time.time()
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Step 1: Create batch requests
    batch_requests = []
    for call_id, transcript in TEST_CALLS:
        batch_requests.append({
            "custom_id": call_id,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4o-mini",
                "messages": [{
                    "role": "user",
                    "content": create_openai_prompt(transcript)
                }],
                "temperature": 0.1,
                "max_tokens": 500,
                "response_format": {"type": "json_object"}
            }
        })
    
    # Step 2: Upload file
    print("🔵 OpenAI: Uploading batch file...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for req in batch_requests:
            f.write(json.dumps(req) + '\n')
        batch_file_path = f.name
    
    try:
        with open(batch_file_path, 'rb') as f:
            batch_input_file = client.files.create(file=f, purpose="batch")
        
        # Step 3: Create batch job
        print("🔵 OpenAI: Creating batch job...")
        batch = client.batches.create(
            input_file_id=batch_input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )
        
        batch_id = batch.id
        print(f"🔵 OpenAI: Batch ID: {batch_id}")
        print(f"🔵 OpenAI: Status: {batch.status}")
        
        # Step 4: Poll for completion
        poll_count = 0
        while True:
            batch = client.batches.retrieve(batch_id)
            poll_count += 1
            elapsed = time.time() - start_time
            
            if batch.status == "completed":
                print(f"🔵 OpenAI: ✅ COMPLETED in {elapsed:.2f}s")
                
                # Step 5: Get results
                result_file = client.files.content(batch.output_file_id)
                results = []
                
                for line in result_file.text.split('\n'):
                    if line.strip():
                        parsed = json.loads(line)
                        custom_id = parsed['custom_id']
                        content = json.loads(
                            parsed['response']['body']['choices'][0]['message']['content']
                        )
                        results.append({"call_id": custom_id, "data": content})
                
                print(f"🔵 OpenAI: Retrieved {len(results)} results")
                
                # Show sample results
                for result in results[:2]:
                    print(f"     {result['call_id']}: {result['data']}")
                
                return elapsed, "success", results
                
            elif batch.status in ["failed", "expired", "cancelled"]:
                print(f"🔵 OpenAI: ❌ FAILED with status: {batch.status}")
                return elapsed, "failed", []
            
            # Log progress
            if poll_count % 3 == 0:
                print(f"🔵 OpenAI: Still processing... {elapsed:.0f}s elapsed (status: {batch.status})")
            
            time.sleep(10)
    
    finally:
        # Cleanup temp file
        try:
            os.unlink(batch_file_path)
        except OSError:
            pass


# ============================================================================
# Gemini Batch API
# ============================================================================

def run_gemini_batch():
    """Run Gemini Batch API test using REST API directly"""
    import requests
    import google.generativeai as genai
    
    print("\n🟢 Gemini Batch API: Starting...")
    start_time = time.time()
    
    api_key = os.getenv("GOOGLE_AI_API_KEY")
    if not api_key:
        print("❌ GOOGLE_AI_API_KEY not set")
        return -1, "failed", []
    
    genai.configure(api_key=api_key)
    
    # Get available models
    try:
        models = genai.list_models()
        model_name = "gemini-1.5-flash"  # Fallback to stable model
        for m in models:
            if "flash" in m.name.lower() and "batch" in m.supported_generation_methods:
                model_name = m.name
                break
        print(f"🟢 Gemini: Using model: {model_name}")
    except Exception as e:
        print(f"⚠️  Could not list models: {e}")
        model_name = "gemini-1.5-flash"
    
    # Prepare batch requests using REST API
    # Gemini batch API uses a different format
    base_url = "https://batchpredictiondata.googleapis.com/v1"
    
    # Create inline requests
    inline_requests = []
    for call_id, transcript in TEST_CALLS:
        inline_requests.append({
            "id": call_id,
            "request": {
                "contents": [{
                    "parts": [{"text": create_gemini_prompt(transcript)}],
                    "role": "user"
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "responseMimeType": "application/json"
                }
            }
        })
    
    try:
        # Create batch prediction job
        print("🟢 Gemini: Creating batch job...")
        
        url = f"{base_url}/projects/*/locations/*/batchPredictionJobs"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        job_config = {
            "displayName": f"entity-extraction-{int(time.time())}",
            "model": f"publishers/google/models/{model_name}",
            "inputConfig": {
                "instancesFormat": "jsonl",
                "gcsSource": None  # Using inline instances
            },
            "outputConfig": {
                "predictionsFormat": "jsonl",
                "gcsDestination": None  # Will use inline results
            },
            "instances": inline_requests
        }
        
        # Try using the official batch API
        response = requests.post(
            url,
            headers=headers,
            json=job_config,
            timeout=30
        )
        
        if response.status_code == 200:
            job_data = response.json()
            job_name = job_data.get('name')
            print(f"🟢 Gemini: Batch job created: {job_name}")
            
            # Poll for completion
            poll_count = 0
            while True:
                job_response = requests.get(
                    f"{base_url}/{job_name}",
                    headers=headers,
                    timeout=30
                )
                
                if job_response.status_code == 200:
                    job = job_response.json()
                    state = job.get('state', 'STATE_UNSPECIFIED')
                    elapsed = time.time() - start_time
                    
                    if state == 'JOB_STATE_SUCCEEDED':
                        print(f"🟢 Gemini: ✅ COMPLETED in {elapsed:.2f}s")
                        
                        # Parse results
                        results = []
                        if 'results' in job:
                            for idx, result in enumerate(job['results']):
                                try:
                                    content = json.loads(
                                        result['prediction']['contents'][0]['parts'][0]['text']
                                    )
                                    results.append({
                                        "call_id": TEST_CALLS[idx][0],
                                        "data": content
                                    })
                                except Exception as e:
                                    print(f"     ⚠️  Error parsing result {idx}: {e}")
                        
                        print(f"🟢 Gemini: Retrieved {len(results)} results")
                        
                        # Show sample results
                        for result in results[:2]:
                            print(f"     {result['call_id']}: {result['data']}")
                        
                        return elapsed, "success", results
                        
                    elif state in ['JOB_STATE_FAILED', 'JOB_STATE_CANCELLED']:
                        error = job.get('error', {}).get('message', 'Unknown error')
                        print(f"🟢 Gemini: ❌ FAILED: {error}")
                        return elapsed, "failed", []
                
                poll_count += 1
                elapsed = time.time() - start_time
                
                if poll_count % 3 == 0:
                    print(f"🟢 Gemini: Still processing... {elapsed:.0f}s elapsed")
                
                time.sleep(10)
        else:
            # If REST API fails, try official client library
            print(f"⚠️  REST API returned {response.status_code}, trying client library...")
            return run_gemini_batch_client(api_key, start_time)
            
    except Exception as e:
        print(f"🟢 Gemini: Error with REST API: {e}")
        return run_gemini_batch_client(api_key, start_time)


def run_gemini_batch_client(api_key: str, start_time: float):
    """Fallback using official Google client library"""
    from google import genai
    import google.generativeai as genai_lib
    
    print("🟢 Gemini: Using official client library...")
    
    genai_lib.configure(api_key=api_key)
    client = genai.Client(api_key=api_key)
    
    # Try to use the batch API
    try:
        inline_requests = []
        for call_id, transcript in TEST_CALLS:
            inline_requests.append({
                "contents": [{
                    "parts": [{"text": create_gemini_prompt(transcript)}],
                    "role": "user"
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "responseMimeType": "application/json"
                }
            })
        
        print("🟢 Gemini: Creating batch job...")
        batch_job = client.batches.create(
            model="models/gemini-1.5-flash",
            src=inline_requests,
            config={"display_name": f"entity-extraction-{int(time.time())}"}
        )
        
        batch_name = batch_job.name if hasattr(batch_job, 'name') else str(batch_job)
        print(f"🟢 Gemini: Batch job created: {batch_name}")
        
        # Poll for completion
        poll_count = 0
        completed_states = {'JOB_STATE_SUCCEEDED', 'JOB_STATE_FAILED', 'JOB_STATE_CANCELLED'}
        
        while True:
            try:
                batch_job = client.batches.get(name=batch_name)
                state = batch_job.state if hasattr(batch_job, 'state') else 'UNKNOWN'
                elapsed = time.time() - start_time
                
                if state in completed_states:
                    if state == 'JOB_STATE_SUCCEEDED':
                        print(f"🟢 Gemini: ✅ COMPLETED in {elapsed:.2f}s")
                        
                        results = []
                        if hasattr(batch_job, 'inline_responses') and batch_job.inline_responses:
                            for idx, response in enumerate(batch_job.inline_responses):
                                if hasattr(response, 'response') and response.response:
                                    try:
                                        text = ""
                                        for part in response.response.candidates[0].content.parts:
                                            if hasattr(part, 'text'):
                                                text += part.text
                                        data = json.loads(text.strip())
                                        results.append({"call_id": TEST_CALLS[idx][0], "data": data})
                                    except Exception as e:
                                        print(f"     ⚠️  Error parsing: {e}")
                        
                        print(f"🟢 Gemini: Retrieved {len(results)} results")
                        return elapsed, "success", results
                    else:
                        print(f"🟢 Gemini: ❌ FAILED with state: {state}")
                        return elapsed, "failed", []
                
                poll_count += 1
                if poll_count % 3 == 0:
                    print(f"🟢 Gemini: Still processing... {elapsed:.0f}s elapsed")
                
                time.sleep(10)
                
            except Exception as e:
                print(f"🟢 Gemini: Polling error: {e}")
                time.sleep(10)
                
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"🟢 Gemini: ❌ FAILED: {e}")
        return elapsed, "failed", []


# ============================================================================
# Race Test
# ============================================================================

def run_race():
    """Run both batch APIs in parallel"""
    print("\n" + "=" * 70)
    print("🏁 BATCH API RACE: OpenAI vs Gemini")
    print("=" * 70)
    print(f"📊 Processing {len(TEST_CALLS)} calls")
    print("⏱️  Both using async Batch APIs with 50% discount")
    print("💰 Gemini: $0.0375/M tokens | OpenAI: $0.075/M tokens")
    print("=" * 70)
    
    race_start = time.time()
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_openai = executor.submit(run_openai_batch)
        future_gemini = executor.submit(run_gemini_batch)
        
        openai_time, openai_status, openai_results = future_openai.result()
        gemini_time, gemini_status, gemini_results = future_gemini.result()
    
    # Results
    print("\n" + "=" * 70)
    print("🏁 RACE RESULTS")
    print("=" * 70)
    
    print(f"\n⏱️  Processing Time:")
    if openai_status == "success":
        print(f"  🔵 OpenAI:  {openai_time:>6.1f}s")
    else:
        print(f"  🔵 OpenAI:  FAILED")
    
    if gemini_status == "success":
        print(f"  🟢 Gemini:  {gemini_time:>6.1f}s")
    else:
        print(f"  🟢 Gemini:  FAILED")
    
    # Determine winner
    if openai_status == "success" and gemini_status == "success":
        if openai_time < gemini_time:
            winner = "OpenAI"
            faster_time = openai_time
            slower_time = gemini_time
        else:
            winner = "Gemini"
            faster_time = gemini_time
            slower_time = openai_time
        
        diff = abs(openai_time - gemini_time)
        speedup = slower_time / faster_time if faster_time > 0 else 1
        
        print(f"\n🏆 Winner: {winner}")
        print(f"⏱️  Time difference: {diff:.1f}s")
        print(f"⚡ {winner} is {speedup:.1f}x faster")
    
    print("\n💰 Cost Comparison (per 1M tokens):")
    print("   Gemini Batch: $0.0375 (50% off)")
    print("   OpenAI Batch: $0.075 (50% off)")
    print("   → Gemini is 2x cheaper for batch!")
    
    total_time = time.time() - race_start
    print(f"\n⏱️  Total race time: {total_time:.1f}s")
    print("=" * 70)


if __name__ == "__main__":
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not set")
        print("   Set it with: export OPENAI_API_KEY='your-key'")
        exit(1)
    
    if not os.getenv("GOOGLE_AI_API_KEY"):
        print("❌ Error: GOOGLE_AI_API_KEY not set")
        print("   Set it with: export GOOGLE_AI_API_KEY='your-key'")
        exit(1)
    
    print("\n📚 Both providers use async Batch APIs with 50% cost discount")
    print("   OpenAI: https://platform.openai.com/docs/api-reference/batch")
    print("   Gemini: https://ai.google.dev/gemini-api/docs/batch-api")
    
    run_race()
