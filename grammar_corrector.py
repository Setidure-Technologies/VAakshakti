from string import Template
from llm_engine import call_ollama

def get_corrected_grammar(transcript, question=None, model="mistral:latest"):
    if not transcript:
        return "⚠️ No transcript found to correct."

    with open("prompts/correction_prompt.txt") as f:
        prompt_template = Template(f.read())

    prompt = prompt_template.substitute(
        transcript=transcript,
        question=question or "No specific question provided."
    )

    return call_ollama(prompt, model=model)

def get_speech_feedback(flagged_words, transcript=None, question=None, model="mistral:latest"):
    if not flagged_words:
        return "✅ Your speech was clear!"

    flagged = "\n".join([
        f'- "{w.strip()}" ({round(p * 100)}%) — Pronunciation below clarity threshold'
        for w, p in flagged_words
    ])

    with open("prompts/feedback_prompt.txt") as f:
        prompt_template = Template(f.read())

    prompt = prompt_template.substitute(
        flagged_words=flagged,
        transcript=transcript or "Transcript not available.",
        question=question or "No question provided."
    )

    return call_ollama(prompt, model=model)

def compare_answers(user_answer, ideal_answer, question, model="mistral:latest"):
    prompt = f"""
You are an English communication evaluator.

The user was asked the following question:
"{question}"

Compare the student's answer to the ideal answer.

User's Spoken Answer:
{user_answer}

Ideal Answer:
{ideal_answer}

Evaluate based on:
- Relevance to the question
- Structure and fluency
- Grammar and vocabulary

Then provide:
1. A short comparison
2. 2 suggestions to improve
"""
    return call_ollama(prompt, model=model)

def generate_question_and_answer(topic, difficulty, model="mistral:latest"):
    with open("prompts/question_prompt.txt") as f:
        prompt_template = Template(f.read())
    
    prompt = prompt_template.substitute(
        topic=topic,
        difficulty=difficulty
    )
    
    response = call_ollama(prompt, model=model)
    
    # The response is expected to be a JSON string with "question" and "ideal_answer" keys.
    # We'll parse it here.
    try:
        import json
        data = json.loads(response)
        return data.get("question", "Error: Could not parse question."), data.get("ideal_answer", "Error: Could not parse ideal answer.")
    except json.JSONDecodeError:
        # Fallback if the model doesn't return valid JSON
        return "Error: Invalid response format from model.", "Could not generate an ideal answer."
