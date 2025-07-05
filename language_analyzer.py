"""
Advanced Language Analysis Module
Provides comprehensive analysis of speech including emotion, sentiment, prosodic features, and linguistic complexity.
"""

import librosa
import numpy as np
import json
from typing import Dict, Any, Optional, Tuple
import logging
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

# NLP and ML imports
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    from textblob import TextBlob
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    from nltk.tag import pos_tag
    import scipy.stats as stats
except ImportError as e:
    logging.warning(f"Some language analysis dependencies not available: {e}")

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('vader_lexicon', quiet=True)
except:
    pass

logger = logging.getLogger(__name__)

class LanguageAnalyzer:
    """Comprehensive language analysis including emotion, sentiment, and prosodic features."""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._emotion_pipeline = None
        self._sentiment_analyzer = SentimentIntensityAnalyzer()
        self._setup_models()
    
    def _setup_models(self):
        """Initialize ML models for analysis."""
        try:
            # Initialize emotion recognition pipeline
            self._emotion_pipeline = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                device=-1  # Use CPU
            )
        except Exception as e:
            logger.warning(f"Could not initialize emotion pipeline: {e}")
            self._emotion_pipeline = None
    
    async def analyze_audio_features(self, audio_path: str) -> Dict[str, Any]:
        """Extract prosodic and acoustic features from audio."""
        def _extract_features():
            try:
                # Load audio file
                y, sr = librosa.load(audio_path, sr=None)
                
                # Extract prosodic features
                features = {}
                
                # Pitch analysis
                pitches, magnitudes = librosa.piptrack(y=y, sr=sr, threshold=0.1)
                pitch_values = []
                for t in range(pitches.shape[1]):
                    index = magnitudes[:, t].argmax()
                    pitch = pitches[index, t]
                    if pitch > 0:
                        pitch_values.append(pitch)
                
                if pitch_values:
                    features['average_pitch'] = float(np.mean(pitch_values))
                    features['pitch_variance'] = float(np.var(pitch_values))
                else:
                    features['average_pitch'] = 0.0
                    features['pitch_variance'] = 0.0
                
                # Speaking rate (approximate)
                onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
                duration = len(y) / sr
                features['onset_rate'] = len(onset_frames) / duration if duration > 0 else 0
                
                # Energy/Volume analysis
                rms = librosa.feature.rms(y=y)[0]
                features['volume_variance'] = float(np.var(rms))
                features['average_energy'] = float(np.mean(rms))
                
                # Spectral features
                spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
                features['spectral_centroid_mean'] = float(np.mean(spectral_centroids))
                
                # Zero crossing rate (indicator of speech clarity)
                zcr = librosa.feature.zero_crossing_rate(y)[0]
                features['zero_crossing_rate'] = float(np.mean(zcr))
                
                # Pause analysis (silence detection)
                intervals = librosa.effects.split(y, top_db=20)
                if len(intervals) > 1:
                    pause_durations = []
                    for i in range(1, len(intervals)):
                        pause_start = intervals[i-1][1]
                        pause_end = intervals[i][0]
                        pause_duration = (pause_end - pause_start) / sr
                        pause_durations.append(pause_duration)
                    
                    features['pause_frequency'] = len(pause_durations) / duration if duration > 0 else 0
                    features['average_pause_duration'] = float(np.mean(pause_durations)) if pause_durations else 0
                else:
                    features['pause_frequency'] = 0.0
                    features['average_pause_duration'] = 0.0
                
                return features
                
            except Exception as e:
                logger.error(f"Error extracting audio features: {e}")
                return {}
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _extract_features)
    
    async def analyze_emotion(self, text: str) -> Dict[str, Any]:
        """Analyze emotion from text using transformer model."""
        def _analyze():
            try:
                if not self._emotion_pipeline or not text.strip():
                    return {
                        'dominant_emotion': 'neutral',
                        'emotion_confidence': 0.0,
                        'emotion_scores': {}
                    }
                
                results = self._emotion_pipeline(text)
                
                # Convert to our format
                emotion_scores = {}
                dominant_emotion = results[0]['label'].lower()
                emotion_confidence = results[0]['score']
                
                for result in results[:5]:  # Top 5 emotions
                    emotion_scores[result['label'].lower()] = result['score']
                
                return {
                    'dominant_emotion': dominant_emotion,
                    'emotion_confidence': float(emotion_confidence),
                    'emotion_scores': emotion_scores
                }
                
            except Exception as e:
                logger.error(f"Error in emotion analysis: {e}")
                return {
                    'dominant_emotion': 'neutral',
                    'emotion_confidence': 0.0,
                    'emotion_scores': {}
                }
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _analyze)
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using VADER and TextBlob."""
        try:
            # VADER sentiment analysis
            vader_scores = self._sentiment_analyzer.polarity_scores(text)
            
            # TextBlob sentiment analysis
            blob = TextBlob(text)
            textblob_polarity = blob.sentiment.polarity
            textblob_subjectivity = blob.sentiment.subjectivity
            
            # Combine scores
            compound_score = (vader_scores['compound'] + textblob_polarity) / 2
            
            # Determine label
            if compound_score >= 0.05:
                sentiment_label = 'positive'
            elif compound_score <= -0.05:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
            
            return {
                'sentiment_score': float(compound_score),
                'sentiment_label': sentiment_label,
                'sentiment_confidence': float(abs(compound_score)),
                'vader_scores': vader_scores,
                'textblob_polarity': float(textblob_polarity),
                'textblob_subjectivity': float(textblob_subjectivity)
            }
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'sentiment_confidence': 0.0
            }
    
    def analyze_linguistic_features(self, text: str) -> Dict[str, Any]:
        """Analyze linguistic complexity and features."""
        try:
            if not text.strip():
                return {
                    'vocabulary_complexity': 0.0,
                    'sentence_complexity': 0.0,
                    'coherence_score': 0.0,
                    'fluency_score': 0.0,
                    'word_count': 0,
                    'sentence_count': 0,
                    'avg_sentence_length': 0.0,
                    'lexical_diversity': 0.0
                }
            
            # Tokenization
            sentences = sent_tokenize(text)
            words = word_tokenize(text.lower())
            
            # Basic statistics
            word_count = len(words)
            sentence_count = len(sentences)
            avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
            
            # Lexical diversity (Type-Token Ratio)
            unique_words = set(words)
            lexical_diversity = len(unique_words) / word_count if word_count > 0 else 0
            
            # POS tagging for complexity analysis
            pos_tags = pos_tag(words)
            
            # Count different POS types
            pos_counts = {}
            for word, pos in pos_tags:
                pos_counts[pos] = pos_counts.get(pos, 0) + 1
            
            # Vocabulary complexity (based on POS diversity and rare words)
            pos_diversity = len(pos_counts) / len(set(pos for _, pos in pos_tags)) if pos_tags else 0
            
            # Sentence complexity (based on average sentence length and structure)
            sentence_lengths = [len(word_tokenize(sent)) for sent in sentences]
            sentence_complexity = np.std(sentence_lengths) if len(sentence_lengths) > 1 else 0
            
            # Coherence score (simplified - based on repetition and flow)
            coherence_score = self._calculate_coherence(text, sentences)
            
            # Fluency score (based on sentence flow and complexity)
            fluency_score = self._calculate_fluency(sentences, words)
            
            return {
                'vocabulary_complexity': float(pos_diversity * lexical_diversity),
                'sentence_complexity': float(sentence_complexity / 10),  # Normalize
                'coherence_score': float(coherence_score),
                'fluency_score': float(fluency_score),
                'word_count': word_count,
                'sentence_count': sentence_count,
                'avg_sentence_length': float(avg_sentence_length),
                'lexical_diversity': float(lexical_diversity),
                'pos_distribution': pos_counts
            }
            
        except Exception as e:
            logger.error(f"Error in linguistic analysis: {e}")
            return {
                'vocabulary_complexity': 0.0,
                'sentence_complexity': 0.0,
                'coherence_score': 0.0,
                'fluency_score': 0.0
            }
    
    def _calculate_coherence(self, text: str, sentences: list) -> float:
        """Calculate a simple coherence score based on word repetition and flow."""
        try:
            if len(sentences) < 2:
                return 1.0
            
            # Calculate word overlap between consecutive sentences
            overlaps = []
            for i in range(len(sentences) - 1):
                words1 = set(word_tokenize(sentences[i].lower()))
                words2 = set(word_tokenize(sentences[i + 1].lower()))
                
                # Remove stopwords
                try:
                    stop_words = set(stopwords.words('english'))
                    words1 = words1 - stop_words
                    words2 = words2 - stop_words
                except:
                    pass
                
                if len(words1) > 0 and len(words2) > 0:
                    overlap = len(words1.intersection(words2)) / len(words1.union(words2))
                    overlaps.append(overlap)
            
            return np.mean(overlaps) if overlaps else 0.5
            
        except Exception:
            return 0.5
    
    def _calculate_fluency(self, sentences: list, words: list) -> float:
        """Calculate a fluency score based on sentence structure and flow."""
        try:
            if not sentences or not words:
                return 0.0
            
            # Factors for fluency
            factors = []
            
            # Sentence length variation (good fluency has varied sentence lengths)
            sentence_lengths = [len(word_tokenize(sent)) for sent in sentences]
            if len(sentence_lengths) > 1:
                length_variation = 1 - (np.std(sentence_lengths) / np.mean(sentence_lengths))
                factors.append(max(0, min(1, length_variation)))
            
            # Average sentence length (not too short, not too long)
            avg_length = np.mean(sentence_lengths)
            optimal_length = 15  # Optimal sentence length
            length_score = 1 - abs(avg_length - optimal_length) / optimal_length
            factors.append(max(0, min(1, length_score)))
            
            # Word repetition (some repetition is natural, too much reduces fluency)
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            repetition_score = 1 - (sum(1 for freq in word_freq.values() if freq > 3) / len(word_freq))
            factors.append(max(0, min(1, repetition_score)))
            
            return np.mean(factors) if factors else 0.5
            
        except Exception:
            return 0.5
    
    def calculate_speaking_rate(self, text: str, audio_duration: float) -> float:
        """Calculate speaking rate in words per minute."""
        try:
            if audio_duration <= 0:
                return 0.0
            
            words = word_tokenize(text)
            word_count = len(words)
            
            # Convert to words per minute
            speaking_rate = (word_count / audio_duration) * 60
            return float(speaking_rate)
            
        except Exception:
            return 0.0
    
    async def comprehensive_analysis(
        self, 
        text: str, 
        audio_path: Optional[str] = None,
        audio_duration: Optional[float] = None
    ) -> Dict[str, Any]:
        """Perform comprehensive language analysis."""
        try:
            results = {}
            
            # Text-based analyses
            emotion_results = await self.analyze_emotion(text)
            sentiment_results = self.analyze_sentiment(text)
            linguistic_results = self.analyze_linguistic_features(text)
            
            results.update(emotion_results)
            results.update(sentiment_results)
            results.update(linguistic_results)
            
            # Audio-based analyses
            if audio_path and Path(audio_path).exists():
                audio_features = await self.analyze_audio_features(audio_path)
                results.update(audio_features)
                
                # Calculate speaking rate if duration is available
                if audio_duration:
                    speaking_rate = self.calculate_speaking_rate(text, audio_duration)
                    results['speaking_rate'] = speaking_rate
            
            # Overall quality scores
            results['overall_quality'] = self._calculate_overall_quality(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {}
    
    def _calculate_overall_quality(self, analysis_results: Dict[str, Any]) -> float:
        """Calculate an overall quality score from all analysis results."""
        try:
            scores = []
            
            # Fluency score
            if 'fluency_score' in analysis_results:
                scores.append(analysis_results['fluency_score'])
            
            # Coherence score
            if 'coherence_score' in analysis_results:
                scores.append(analysis_results['coherence_score'])
            
            # Vocabulary complexity (normalized)
            if 'vocabulary_complexity' in analysis_results:
                vocab_score = min(1.0, analysis_results['vocabulary_complexity'] * 2)
                scores.append(vocab_score)
            
            # Sentiment confidence (neutral to positive bias)
            if 'sentiment_confidence' in analysis_results:
                sentiment_score = analysis_results['sentiment_confidence']
                if analysis_results.get('sentiment_label') == 'positive':
                    sentiment_score *= 1.2  # Boost positive sentiment
                scores.append(min(1.0, sentiment_score))
            
            # Speaking rate score (optimal range: 140-180 WPM)
            if 'speaking_rate' in analysis_results:
                rate = analysis_results['speaking_rate']
                if 140 <= rate <= 180:
                    rate_score = 1.0
                elif 120 <= rate < 140 or 180 < rate <= 200:
                    rate_score = 0.8
                elif 100 <= rate < 120 or 200 < rate <= 220:
                    rate_score = 0.6
                else:
                    rate_score = 0.4
                scores.append(rate_score)
            
            return float(np.mean(scores)) if scores else 0.5
            
        except Exception:
            return 0.5

# Global analyzer instance
language_analyzer = LanguageAnalyzer()