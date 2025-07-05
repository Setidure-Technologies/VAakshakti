from faster_whisper import WhisperModel

# Changed device to "cpu" and compute_type to "int8" for CPU compatibility
# You can also try "float32" for compute_type on CPU if int8 has issues,
# but int8 is generally recommended for CPU by faster-whisper for good performance.
# model = WhisperModel("base.en", device="cpu", compute_type="int8") # Moved into function

def transcribe(audio_path):
    # Initialize model inside the function for testing with Celery
    print("🛠️ Initializing WhisperModel ('base.en', device='cpu', compute_type='int8') within transcribe function...")
    try:
        model = WhisperModel("base.en", device="cpu", compute_type="int8")
        print("✅ WhisperModel initialized successfully within transcribe function.")
    except Exception as e:
        print(f"🔥 Error initializing WhisperModel: {e}")
        raise # Re-raise the exception to fail the task clearly

    print("⚙️ Received audio:", audio_path)
    # Simplify the call to see if parameters are the issue
    print("🧠 Calling model.transcribe with minimal parameters...")
    segments, info = model.transcribe(audio_path) # Removed beam_size and word_timestamps
    print(f"🧠 model.transcribe returned. Language: {info.language}, Probability: {info.language_probability}, Duration: {info.duration}")

    result = ""
    # Since word_timestamps=False (default), segment.words might not be populated or be different.
    # For now, we'll just focus on getting the full transcript.
    # We can re-add word_timestamps later if this works.
    flagged_words = [] # Will be empty if word_timestamps is False

    for segment in segments:
        print("🧠 Segment:", segment)
        # if not segment.words: # This check might be problematic if word_timestamps is False
        #     continue
        result += segment.text + " "
        # Word-level processing might not work as expected without word_timestamps=True
        # for word in segment.words:
        #     print(f"🔍 Word: {word.word} — Prob: {word.probability}")
        #     if word.probability and word.probability < 0.85:
        #         flagged_words.append((word.word, word.probability))

    print("📋 Final transcript (from simplified call):", result.strip())
    print("🚩 Flagged words:", flagged_words)

    return result.strip(), flagged_words
