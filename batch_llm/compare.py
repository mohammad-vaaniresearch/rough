"""
Batch LLM API Comparison: OpenAI vs Gemini
Both using their async batch APIs with proper implementation

This script compares the performance and cost of batch processing
using OpenAI Batch API and Google Gemini Batch API.

Requirements:
    - OPENAI_API_KEY environment variable
    - GOOGLE_AI_API_KEY environment variable

Example usage:
    python -m batch_llm.compare
"""

import os
import time
import json
import asyncio
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

# Test data for entity extraction
TEST_CALLS = [
    ("call-1", "Agent: Hello! Customer: My name is John Doe, email john@example.com, phone 555-1234"),
    ("call-2", "Agent: Hi there! Customer: I'm Jane Smith, jane@test.com, 555-5678"),
    ("call-3", "Agent: Good morning! Customer: This is Bob Wilson, bob@company.com, 555-9012"),
    ("call-4", "Agent: Welcome! Customer: Alice Brown here, alice@email.com, 555-3456"),
    ("call-5", "Agent: How can I help? Customer: I'm Charlie Davis, charlie@mail.com, 555-7890"),
]


@dataclass
class BatchResult:
    """Result of a batch API test"""
    elapsed_time: float
    success: bool
    results: list
    cost_per_1k: float


class OpenAIBatchProcessor:
    """OpenAI Batch API processor"""
    
    BASE_COST_PER_1M = 0.075  # $0.075 per 1M tokens for gpt-4o-mini batch
    BATCH_DISCOUNT = 0.5  # 50% discount for batch
    
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"
    
    def create_prompt(self, transcript: str) -> str:
        """Create extraction prompt for a transcript"""
        return (
            "Extract the following from this call transcript:\n"
            "- Customer name\n"
            "- Email address\n"
            "- Phone number\n\n"
            f"Transcript: {transcript}\n\n"
            "Return as JSON with keys: customer_name, email, phone"
        )
    
    def create_batch_requests(self) -> list[dict]:
        """Create batch request payload"""
        requests = []
        for call_id, transcript in TEST_CALLS:
            requests.append({
                "custom_id": call_id,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": self.model,
                    "messages": [{
                        "role": "user",
                        "content": self.create_prompt(transcript)
                    }],
                    "temperature": 0.1,
                    "max_tokens": 500,
                    "response_format": {"type": "json_object"}
                }
            })
        return requests
    
    async def upload_batch_file(self, requests: list[dict]) -> str:
        """Upload batch requests file to OpenAI"""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for req in requests:
                f.write(json.dumps(req) + '\n')
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                batch_file = self.client.files.create(
                    file=f,
                    purpose="batch"
                )
            return batch_file.id
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
    
    def create_batch_job(self, file_id: str) -> dict:
        """Create batch job from uploaded file"""
        batch = self.client.batches.create(
            input_file_id=file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )
        return batch
    
    async def wait_for_completion(self, batch_id: str, poll_interval: int = 10) -> dict:
        """Poll for batch completion"""
        while True:
            batch = self.client.batches.retrieve(batch_id)
            
            if batch.status == "completed":
                return batch
            elif batch.status in ["failed", "expired", "cancelled"]:
                raise RuntimeError(f"Batch failed with status: {batch.status}")
            
            await asyncio.sleep(poll_interval)
    
    async def get_results(self, output_file_id: str) -> list[dict]:
        """Retrieve and parse batch results"""
        result_file = self.client.files.content(output_file_id)
        results = []
        
        for line in result_file.text.split('\n'):
            if line.strip():
                parsed = json.loads(line)
                custom_id = parsed['custom_id']
                content = json.loads(
                    parsed['response']['body']['choices'][0]['message']['content']
                )
                results.append({
                    "call_id": custom_id,
                    "data": content
                })
        
        return results
    
    async def run(self) -> BatchResult:
        """Execute full batch process and return results"""
        start_time = time.time()
        results = []
        
        try:
            print("  📤 Uploading batch requests...")
            requests = self.create_batch_requests()
            file_id = await self.upload_batch_file(requests)
            
            print("  📋 Creating batch job...")
            batch = self.create_batch_job(file_id)
            print(f"  🆔 Batch ID: {batch.id}")
            
            print("  ⏳ Waiting for completion...")
            completed_batch = await self.wait_for_completion(batch.id)
            
            print("  📥 Retrieving results...")
            results = await self.get_results(completed_batch.output_file_id)
            
            elapsed = time.time() - start_time
            print(f"  ✅ Completed in {elapsed:.2f}s")
            
            return BatchResult(
                elapsed_time=elapsed,
                success=True,
                results=results,
                cost_per_1m=self.BASE_COST_PER_1M * self.BATCH_DISCOUNT
            )
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ❌ Failed: {e}")
            return BatchResult(
                elapsed_time=elapsed,
                success=False,
                results=results,
                cost_per_1m=self.BASE_COST_PER_1M * self.BATCH_DISCOUNT
            )


class GeminiBatchProcessor:
    """Google Gemini Batch API processor"""
    
    # Gemini 2.0 Flash batch pricing (50% off)
    BASE_COST_PER_1M = 0.0375
    
    def __init__(self):
        import google.generativeai as genai
        self.genai = genai
        self.model = "gemini-2.0-flash-exp"
    
    def create_prompt(self, transcript: str) -> str:
        """Create extraction prompt for a transcript"""
        return (
            "Extract the following from this call transcript:\n"
            "- Customer name\n"
            "- Email address\n"
            "- Phone number\n\n"
            f"Transcript: {transcript}\n\n"
            "Return as JSON with keys: customer_name, email, phone"
        )
    
    def create_inline_requests(self) -> list[dict]:
        """Create inline batch requests for Gemini"""
        requests = []
        for call_id, transcript in TEST_CALLS:
            requests.append({
                "model": self.model,
                "contents": [{
                    "parts": [{"text": self.create_prompt(transcript)}],
                    "role": "user"
                }],
                "config": {
                    "temperature": 0.1,
                    "response_mime_type": "application/json"
                }
            })
        return requests
    
    async def run(self) -> BatchResult:
        """Execute full batch process and return results"""
        from google import genai
        
        start_time = time.time()
        results = []
        
        try:
            api_key = os.getenv("GOOGLE_AI_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_AI_API_KEY not set")
            
            self.genai.configure(api_key=api_key)
            client = genai.Client(api_key=api_key)
            
            # Create batch job
            print("  📋 Creating batch job...")
            inline_requests = self.create_inline_requests()
            
            batch_job = client.batches.create(
                model=self.model,
                src=inline_requests,
                config={
                    "display_name": f"entity-extraction-{int(time.time())}",
                }
            )
            
            batch_name = batch_job.name if hasattr(batch_job, 'name') else batch_job
            print(f"  🆔 Batch name: {batch_name}")
            
            print("  ⏳ Waiting for completion...")
            completed_job = await self._wait_for_completion(client, batch_name)
            
            print("  📥 Retrieving results...")
            results = self._parse_results(completed_job)
            
            elapsed = time.time() - start_time
            print(f"  ✅ Completed in {elapsed:.2f}s")
            
            return BatchResult(
                elapsed_time=elapsed,
                success=True,
                results=results,
                cost_per_1m=self.BASE_COST_PER_1M
            )
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ❌ Failed: {e}")
            import traceback
            traceback.print_exc()
            return BatchResult(
                elapsed_time=elapsed,
                success=False,
                results=results,
                cost_per_1m=self.BASE_COST_PER_1M
            )
    
    async def _wait_for_completion(self, client, batch_name: str, poll_interval: int = 10) -> dict:
        """Poll for batch completion"""
        from google.api_core.exceptions import NotFound
        
        completed_states = {
            'JOB_STATE_SUCCEEDED',
            'JOB_STATE_FAILED', 
            'JOB_STATE_CANCELLED',
            'JOB_STATE_EXPIRED',
        }
        
        while True:
            try:
                batch_job = client.batches.get(name=batch_name)
                state = batch_job.state if hasattr(batch_job, 'state') else str(batch_job)
                
                if state in completed_states:
                    return batch_job
                
                await asyncio.sleep(poll_interval)
                
            except NotFound:
                raise RuntimeError(f"Batch job not found: {batch_name}")
    
    def _parse_results(self, batch_job) -> list[dict]:
        """Parse results from completed batch job"""
        results = []
        
        # Check for inline responses
        if hasattr(batch_job, 'inline_responses') and batch_job.inline_responses:
            for idx, response in enumerate(batch_job.inline_responses):
                if hasattr(response, 'response') and response.response:
                    try:
                        text = ""
                        for part in response.response.candidates[0].content.parts:
                            if hasattr(part, 'text'):
                                text += part.text
                        
                        data = json.loads(text.strip())
                        results.append({
                            "call_id": TEST_CALLS[idx][0],
                            "data": data
                        })
                    except Exception as e:
                        print(f"    ⚠️  Error parsing response {idx}: {e}")
        
        return results


class BatchComparison:
    """Main comparison runner"""
    
    def __init__(self):
        self.openai = OpenAIBatchProcessor()
        self.gemini = GeminiBatchProcessor()
    
    async def run_race(self) -> dict:
        """Run both batch APIs concurrently and compare results"""
        print("\n" + "=" * 70)
        print("🏁 BATCH API RACE: OpenAI vs Gemini")
        print("=" * 70)
        print(f"📊 Processing {len(TEST_CALLS)} calls")
        print("⏱️  Both using async Batch APIs")
        print("=" * 70)
        
        race_start = time.time()
        
        # Run concurrently
        openai_task = asyncio.create_task(self.openai.run())
        gemini_task = asyncio.create_task(self.gemini.run())
        
        openai_result, gemini_result = await asyncio.gather(
            openai_task,
            gemini_task
        )
        
        total_time = time.time() - race_start
        
        # Display results
        self._print_results(openai_result, gemini_result, total_time)
        
        return {
            "openai": openai_result,
            "gemini": gemini_result,
            "total_time": total_time
        }
    
    def _print_results(self, openai_result: BatchResult, gemini_result: BatchResult, total_time: float):
        """Print comparison results"""
        print("\n" + "=" * 70)
        print("📊 RACE RESULTS")
        print("=" * 70)
        
        # Time comparison
        print("\n⏱️  Processing Time:")
        print(f"  {'Provider':<10} {'Status':<12} {'Time':<10}")
        print(f"  {'-'*32}")
        
        if openai_result.success:
            print(f"  {'OpenAI':<10} {'✅ Success':<12} {openai_result.elapsed_time:>7.1f}s")
        else:
            print(f"  {'OpenAI':<10} {'❌ Failed':<12} {openai_result.elapsed_time:>7.1f}s")
        
        if gemini_result.success:
            print(f"  {'Gemini':<10} {'✅ Success':<12} {gemini_result.elapsed_time:>7.1f}s")
        else:
            print(f"  {'Gemini':<10} {'❌ Failed':<12} {gemini_result.elapsed_time:>7.1f}s")
        
        # Winner determination
        if openai_result.success and gemini_result.success:
            if openai_result.elapsed_time < gemini_result.elapsed_time:
                winner = "OpenAI"
                diff = gemini_result.elapsed_time - openai_result.elapsed_time
                speedup = gemini_result.elapsed_time / openai_result.elapsed_time
            else:
                winner = "Gemini"
                diff = openai_result.elapsed_time - gemini_result.elapsed_time
                speedup = openai_result.elapsed_time / gemini_result.elapsed_time
            
            print(f"\n🏆 Winner: {winner}")
            print(f"⏱️  Time difference: {diff:.1f}s")
            if speedup > 1:
                print(f"⚡ {winner} is {speedup:.1f}x faster")
        
        # Cost comparison
        print("\n" + "=" * 70)
        print("💰 Cost Comparison (per 1M tokens)")
        print("=" * 70)
        print(f"  OpenAI Batch (gpt-4o-mini): ${openai_result.cost_per_1m:.4f}")
        print(f"  Gemini Batch (gemini-2.0-flash-exp): ${gemini_result.cost_per_1m:.4f}")
        
        if openai_result.cost_per_1m > gemini_result.cost_per_1m:
            ratio = openai_result.cost_per_1m / gemini_result.cost_per_1m
            print(f"\n→ Gemini is {ratio:.1f}x cheaper!")
        else:
            ratio = gemini_result.cost_per_1m / openai_result.cost_per_1m
            print(f"\n→ OpenAI is {ratio:.1f}x cheaper!")
        
        # Sample results
        if openai_result.results:
            print("\n" + "=" * 70)
            print("📝 Sample Results (OpenAI)")
            print("=" * 70)
            for result in openai_result.results[:2]:
                print(f"  {result['call_id']}: {result['data']}")
        
        if gemini_result.results:
            print("\n" + "=" * 70)
            print("📝 Sample Results (Gemini)")
            print("=" * 70)
            for result in gemini_result.results[:2]:
                print(f"  {result['call_id']}: {result['data']}")
        
        print("\n" + "=" * 70)
        print("⏱️  Total race time: {:.1f}s".format(total_time))
        print("=" * 70)


async def main():
    """Main entry point"""
    # Check API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not set")
        print("   Set it with: export OPENAI_API_KEY='your-key'")
        return
    
    if not os.getenv("GOOGLE_AI_API_KEY"):
        print("❌ Error: GOOGLE_AI_API_KEY not set")
        print("   Set it with: export GOOGLE_AI_API_KEY='your-key'")
        return
    
    # Show pricing info
    print("\n📚 Batch API Pricing (50% off):")
    print("   OpenAI gpt-4o-mini: $0.075/M tokens")
    print("   Gemini 2.0 Flash:  $0.0375/M tokens")
    
    # Run comparison
    comparison = BatchComparison()
    await comparison.run_race()


if __name__ == "__main__":
    asyncio.run(main())
