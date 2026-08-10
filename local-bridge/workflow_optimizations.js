Workflow({
  script: [
    {
      phase: "1_Scout",
      steps: [
        {
          agent: "claude",
          task: "Create benchmark_latency_e2e.py if missing. Run benchmark_asr.py and benchmark_latency_e2e.py to establish baselines. Profile memory usage with memory_profiler and save metrics."
        }
      ]
    },
    {
      phase: "2_Optimize",
      parallel: true,
      steps: [
        {
          agent: "claude",
          task: "Optimize AudioBufferManager in local-bridge/app/services/audio_buffer.py: Replace np.interp with scipy.signal.resample, optimize windowing logic, make VAD tail check configurable."
        },
        {
          agent: "claude",
          task: "Optimize ASRService in local-bridge/app/services/asr_service.py: Tune mlx_whisper params (temperature=0.1, no_speech_threshold=0.6), expand _WHISPER_JUNK set, add thread safety checks."
        },
        {
          agent: "claude",
          task: "Optimize TranslationService in local-bridge/app/services/translation_service.py: Cache MarianMT tokenizer/model, batch translations if multiple sentences arrive within 100ms, benchmark onnxruntime vs mps."
        },
        {
          agent: "claude",
          task: "Optimize Web UI in web/index.html: Replace DOM prepend with DocumentFragment, suspend/resume AudioContext instead of recreating, add exponential backoff for WS reconnects."
        }
      ]
    },
    {
      phase: "3_Verify",
      steps: [
        {
          agent: "claude",
          task: "Rerun benchmarks, compare against baselines, verify all tests pass, and generate diff report ensuring changes are minimal and ponytail-compliant."
        }
      ]
    }
  ]
})
