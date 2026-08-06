import time
import numpy as np
import sys
import os

# add parent directory to path so app. can be resolved
sys.path.insert(0, os.path.dirname(__file__))

from app.services.asr_service import asr_service
from app.core.config import config

def run_benchmark():
    print(f"Loading model... device: {config.asr_device}")
    start_load = time.time()
    success = asr_service.load_model()
    if not success:
        print("Model failed to load. Aborting benchmark.")
        return
    
    print(f"Model loaded in {time.time() - start_load:.2f}s. Engine: {asr_service.engine_name}")
    
    # 2 seconds of random audio noise to simulate speech
    sample_rate = 16000
    audio_data = np.random.randn(sample_rate * 2).astype(np.float32)
    
    print("Warming up model...")
    asr_service.transcribe(audio_data, sample_rate)
    
    print("Running benchmark (5 iterations)...")
    latencies = []
    for i in range(5):
        audio_data = np.random.randn(sample_rate * 2).astype(np.float32)
        start_time = time.time()
        res = asr_service.transcribe(audio_data, sample_rate)
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        latencies.append(latency_ms)
        print(f"Iter {i+1}: {latency_ms:.2f} ms | Text: {res.get('text', '')}")
    
    avg_latency = np.mean(latencies)
    print(f"Average Latency: {avg_latency:.2f} ms per 2s window")

if __name__ == '__main__':
    run_benchmark()
