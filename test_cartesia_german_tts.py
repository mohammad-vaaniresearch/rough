#!/usr/bin/env python3
"""
Test script for Cartesia TTS with German voice (viktoria-german) and Deepgram fallback using LiveKit.

This script tests the Cartesia TTS with the following configuration:
- Model: sonic-3-2025-10-27
- Voice: viktoria-german (b9de4a89-2257-424b-94c2-db18ba68c81a)
- Speed: 0.2
- Language: de (German)
- Emotions: positivity:highest, curiosity:highest
- Fallback: Deepgram TTS (aura-2-arcas-en)
"""

import asyncio
import logging
import os
import sys
from typing import Optional

try:
    from livekit import agents
    from livekit.agents import tts
    from livekit.plugins import cartesia, deepgram
except ImportError as e:
    print("ERROR: Required LiveKit modules not found.")
    print("Please install LiveKit agents and plugins:")
    print("  pip install livekit-agents livekit-plugins-cartesia livekit-plugins-deepgram")
    print(f"Import error: {e}")
    sys.exit(1)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TTSTester:
    """Test harness for TTS services with primary and fallback configuration."""
    
    def __init__(self):
        self.primary_tts: Optional[cartesia.TTS] = None
        self.fallback_tts: Optional[deepgram.TTS] = None
        self.audio_frames_count = 0
        
    def initialize_cartesia_tts(self) -> bool:
        """Initialize Cartesia TTS with German voice configuration."""
        try:
            api_key = os.getenv('CARTESIA_API_KEY')
            if not api_key:
                logger.error("CARTESIA_API_KEY environment variable not set")
                return False
            
            logger.info("Initializing Cartesia TTS with German voice configuration...")
            
            self.primary_tts = cartesia.TTS(
                api_key=api_key,
                model="sonic-3-2025-10-27",
                voice="b9de4a89-2257-424b-94c2-db18ba68c81a",
                language="de",
                speed=0.2,
                emotion=["positivity:highest", "curiosity:highest"]
            )
            
            logger.info("Cartesia TTS initialized successfully")
            logger.info("Configuration:")
            logger.info("  - Model: sonic-3-2025-10-27")
            logger.info("  - Voice: viktoria-german (b9de4a89-2257-424b-94c2-db18ba68c81a)")
            logger.info("  - Language: de (German)")
            logger.info("  - Speed: 0.2")
            logger.info("  - Emotions: positivity:highest, curiosity:highest")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Cartesia TTS: {e}", exc_info=True)
            return False
    
    def initialize_deepgram_fallback(self) -> bool:
        """Initialize Deepgram TTS as fallback."""
        try:
            api_key = os.getenv('DEEPGRAM_API_KEY')
            if not api_key:
                logger.error("DEEPGRAM_API_KEY environment variable not set")
                return False
            
            logger.info("Initializing Deepgram TTS fallback...")
            
            self.fallback_tts = deepgram.TTS(
                api_key=api_key,
                model="aura-2-arcas-en"
            )
            
            logger.info("Deepgram TTS fallback initialized successfully")
            logger.info("Configuration:")
            logger.info("  - Model: aura-2-arcas-en")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Deepgram TTS: {e}", exc_info=True)
            return False
    
    async def test_synthesis(self, text: str, use_fallback: bool = False) -> bool:
        """
        Test TTS synthesis with the given text.
        
        Args:
            text: The text to synthesize
            use_fallback: If True, use fallback TTS instead of primary
            
        Returns:
            True if synthesis succeeded, False otherwise
        """
        tts_service = self.fallback_tts if use_fallback else self.primary_tts
        service_name = "Deepgram (fallback)" if use_fallback else "Cartesia (primary)"
        
        if not tts_service:
            logger.error(f"{service_name} TTS not initialized")
            return False
        
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing {service_name} TTS synthesis")
            logger.info(f"Text: {text}")
            logger.info(f"{'='*60}\n")
            
            self.audio_frames_count = 0
            total_audio_bytes = 0
            
            logger.info("Starting synthesis...")
            
            stream = tts_service.synthesize(text)
            
            async for event in stream:
                if event.type == tts.SynthesisEventType.STARTED:
                    logger.debug("Synthesis started")
                elif event.type == tts.SynthesisEventType.AUDIO:
                    self.audio_frames_count += 1
                    audio_data = event.audio
                    if audio_data and audio_data.data:
                        audio_bytes = len(audio_data.data)
                        total_audio_bytes += audio_bytes
                        logger.debug(f"Audio frame {self.audio_frames_count}: {audio_bytes} bytes")
                elif event.type == tts.SynthesisEventType.FINISHED:
                    logger.debug("Synthesis finished")
                elif event.type == tts.SynthesisEventType.ERROR:
                    logger.error(f"Synthesis error: {event.error}")
                    return False
            
            if self.audio_frames_count > 0:
                logger.info(f"\n✓ SUCCESS: Generated {self.audio_frames_count} audio frames ({total_audio_bytes} bytes total)")
                return True
            else:
                logger.warning("\n✗ WARNING: No audio frames were generated")
                return False
                
        except Exception as e:
            logger.error(f"\n✗ ERROR during synthesis: {e}", exc_info=True)
            return False
    
    async def run_tests(self):
        """Run all TTS tests."""
        logger.info("="*60)
        logger.info("Starting Cartesia German TTS Test (LiveKit)")
        logger.info("="*60)
        
        german_text = "Es freut mich, Sie kennenzulernen, Ich hoffe, Sie haben einen schönen Tag"
        
        cartesia_ok = self.initialize_cartesia_tts()
        deepgram_ok = self.initialize_deepgram_fallback()
        
        results = {
            'cartesia_init': cartesia_ok,
            'deepgram_init': deepgram_ok,
            'cartesia_synthesis': False,
            'deepgram_synthesis': False
        }
        
        if cartesia_ok:
            results['cartesia_synthesis'] = await self.test_synthesis(german_text, use_fallback=False)
        else:
            logger.error("Skipping Cartesia synthesis test - initialization failed")
        
        if deepgram_ok:
            results['deepgram_synthesis'] = await self.test_synthesis(german_text, use_fallback=True)
        else:
            logger.warning("Skipping Deepgram fallback test - initialization failed")
        
        self.print_summary(results)
        
        return results
    
    def print_summary(self, results: dict):
        """Print test results summary."""
        logger.info("\n" + "="*60)
        logger.info("TEST SUMMARY")
        logger.info("="*60)
        
        def status(success: bool) -> str:
            return "✓ PASS" if success else "✗ FAIL"
        
        logger.info(f"Cartesia Initialization:     {status(results['cartesia_init'])}")
        logger.info(f"Cartesia Synthesis:          {status(results['cartesia_synthesis'])}")
        logger.info(f"Deepgram Initialization:     {status(results['deepgram_init'])}")
        logger.info(f"Deepgram Synthesis:          {status(results['deepgram_synthesis'])}")
        
        all_passed = all(results.values())
        logger.info("="*60)
        if all_passed:
            logger.info("✓ ALL TESTS PASSED")
        else:
            logger.warning("✗ SOME TESTS FAILED")
        logger.info("="*60)
        
        return 0 if all_passed else 1


async def main():
    """Main entry point."""
    tester = TTSTester()
    results = await tester.run_tests()
    
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
