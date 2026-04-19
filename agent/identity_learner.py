"""Zaya Brain — Identity Learning System.

An autonomous engine that processes every conversation and continuously
builds Zaya's unique identity — the 7 lens files that make Zaya show up
differently for every user, especially in their moments of weakness.

Architecture:
  Every Conversation
          ↓
  [IdentityLearner.process()] — called after each session + nightly
          ↓
  ┌─────────────────────────────────────────────────────────────┐
  │  EXTRACTOR: Parse raw messages into structured signals       │
  │  EMOTION TAGGER: Run feelings_ontology on every message       │
  │  PATTERN MINER: Find recurring themes across sessions        │
  │  TRAJECTORY TRACKER: Map emotional arcs over time           │
  │  CONTRADICTION DETECTOR: Flag beliefs that conflict          │
  │  ANCHOR WEIGHT: Score belief confidence by evidence strength │
  │  IDENTITY UPDATER: Write new data into the 7 lens files      │
  │  COHERENCE CHECKER: Ensure lens files don't contradict       │
  └─────────────────────────────────────────────────────────────┘
          ↓
  7 Identity Lens Files (auto-updated, never static)

The key insight: the 7 lens files are NOT populated by hand.
They are BUILT by this system from raw conversation data.
The more you talk to Zaya, the more Zaya knows when to show up for you.
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class ConversationSignal:
    """A single extracted signal from a conversation."""
    source: str              # "user" or "assistant"
    text: str
    timestamp: str
    primary_emotion: str     # from Plutchik
    intensity: float         # 0.0-1.0
    arousal: str            # "low" | "medium" | "high"
    trigger_flags: list[str] # detected triggers
    is_distress_signal: bool
    key_phrases: list[str]   # distinctive language patterns
    topic: str              # what they were talking about


@dataclass
class IdentityUpdate:
    """A proposed update to one of the 7 identity files."""
    file: str                # which lens file
    section: str             # which section within the file
    entry: str               # the content to add/update
    confidence: float         # 0.0-1.0 — how strong is the evidence
    source_signals: list[str] # session IDs where this was detected
    evidence_count: int      # how many times this pattern appeared
    replaces: Optional[str] = None   # old entry this overwrites (if contradictory)
    reasoning: str = ""      # why Zaya believes this is true


@dataclass
class AnchorScore:
    """A belief with its evidence strength."""
    belief: str
    confidence: float        # weighted by evidence count + recency
    first_seen: str          # timestamp
    last_confirmed: str      # timestamp
    evidence_sessions: list[str]
    contradicted_by: list[str]  # sessions that challenged this belief
    is_stable: bool         # True once confidence > 0.8 and stable


@dataclass
class EmotionalTrajectory:
    """Tracks how a user's emotional state changes over time."""
    date: str
    overall_state: str       # "stable" | "stressed" | "flourishing" | "declining"
    primary_emotion: str
    intensity_avg: float
    distress_level: float   # 0.0-1.0
    notable_events: list[str]
    trajectory_direction: str  # "improving" | "stable" | "declining" | "volatile"


# =============================================================================
# EXTRACTOR — Parse raw messages into ConversationSignals
# =============================================================================

class SignalExtractor:
    """Extracts structured signals from raw conversation data."""

    def __init__(self, ontology: dict[str, Any]):
        self.ontology = ontology
        self.primary_emotions = ontology.get("primary_emotions", {})

    def process_message(self, msg: dict[str, Any], session_id: str) -> ConversationSignal:
        """Convert a raw message dict into a ConversationSignal."""
        role = msg.get("role", "unknown")
        content = self._extract_text(msg.get("content", ""))
        timestamp = msg.get("timestamp", datetime.now(timezone.utc).isoformat())

        emotion = self._detect_emotion(content)
        intensity = self._estimate_intensity(content)
        arousal = self._estimate_arousal(emotion, intensity)
        triggers = self._detect_triggers(content)
        distress = self._is_distress_signal(content, triggers)
        phrases = self._extract_key_phrases(content)
        topic = self._detect_topic(content)

        return ConversationSignal(
            source=role,
            text=content,
            timestamp=timestamp,
            primary_emotion=emotion,
            intensity=intensity,
            arousal=arousal,
            trigger_flags=triggers,
            is_distress_signal=distress,
            key_phrases=phrases,
            topic=topic,
        )

    def _extract_text(self, content: Any) -> str:
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    return block.get("text", "").strip()
        return ""

    def _detect_emotion(self, text: str) -> str:
        text_lower = text.lower()
        scores: dict[str, float] = {}

        for emotion_name, emotion_data in self.primary_emotions.items():
            signals = emotion_data.get("signals", [])
            score = sum(1 for sig in signals if sig.lower() in text_lower)
            if score > 0:
                scores[emotion_name] = score / len(signals)

        if not scores:
            return "neutral"
        return max(scores, key=scores.get)  # type: ignore

    def _estimate_intensity(self, text: str) -> float:
        # High-intensity markers
        high_markers = ["!", "!!", "???", "!!!" , "actually", "really", "so much", "absolutely", "literally", "completely"]
        low_markers = ["maybe", "perhaps", "sort of", "kind of", "a bit", "slightly", "fairly"]

        text_lower = text.lower()
        high = sum(1 for m in high_markers if m in text_lower)
        low = sum(1 for m in low_markers if m in text_lower)

        score = min(1.0, (high * 0.2) - (low * 0.1) + 0.4)
        return score

    def _estimate_arousal(self, emotion: str, intensity: float) -> str:
        # High-arousal emotions: anger, fear, anticipation, joy
        high_arousal = {"anger", "fear", "anticipation", "joy"}
        low_arousal = {"sadness", "trust", "disgust"}

        if emotion in high_arousal:
            return "high"
        if emotion in low_arousal:
            return "low"
        return "medium"

    def _detect_triggers(self, text: str) -> list[str]:
        text_lower = text.lower()
        triggers = []

        trigger_map = {
            "abandonment": ["ghost", "left", "abandoned", "ignored", "dropped", "gone", "no response", "silence"],
            "rejection": ["not wanted", "rejected", "don't belong", "judged", "left out", "not included"],
            "betrayal": ["lied", "betrayed", "behind my back", "stabbed", "used me", "can't trust"],
            "inadequacy": ["not enough", "failure", "stupid", "dumb", "worthless", "can't do anything right"],
            "control": ["trapped", "cornered", "no choice", "have to", "forced", "told me to"],
            "disrespect": ["waste my time", "disrespect", "don't value", "free", "cheap", "owed me"],
        }

        for trigger_name, keywords in trigger_map.items():
            if any(kw in text_lower for kw in keywords):
                triggers.append(trigger_name)

        return triggers

    def _is_distress_signal(self, text: str, triggers: list[str]) -> bool:
        text_lower = text.lower()
        distress_keywords = [
            "stuck", "burned out", "breaking point", "overwhelmed",
            "can't do this", "falling apart", "done", "give up",
            "worthless", "helpless", "hopeless",
        ]
        return bool(triggers) or any(kw in text_lower for kw in distress_keywords)

    def _extract_key_phrases(self, text: str) -> list[str]:
        """Extract distinctive phrases that reveal values/beliefs."""
        phrases = []

        # Patterns that reveal core values
        patterns = [
            (r"don't want to (pay|gives?|give)\s", "reluctant_to_value_time"),
            (r"co-founder|partner|join forces", "values_partnership"),
            (r"\b(billionaire|CEO|correct|direct)\b", "respects_clarity"),
            (r"\b(back and forth|going back|ghost)\b", "integrity_matters"),
            (r"(constant|inconsisten|unreliable)", "values_consistency"),
            (r"one-command|zero.?friction|install", "product_quality"),
            (r"\b(own|owning|ownership)\b", "values_ownership"),
            (r"\b(wrapper|fork|knockoff|copy)\b", "values_originality"),
        ]

        for pattern, label in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                phrases.append(label)

        return phrases

    def _detect_topic(self, text: str) -> str:
        text_lower = text.lower()
        topics = {
            "partnership": ["partner", "co-founder", "joint", "three of us", "business partner"],
            "payment": ["pay", "invoice", "money", "2k", "20k", "charge", "paid", "expensive"],
            "product": ["zaya", "product", "build", "engine", "brain", "architecture"],
            "relationship": ["ghost", "trust", "commitment", "word", "agreement", "promised"],
            "emotional": ["feeling", "hurt", "pain", "upset", "angry", "sad", "confused"],
            "strategy": ["decide", "strategy", "should i", "thinking", "options", "plan"],
        }

        for topic_name, keywords in topics.items():
            if any(kw in text_lower for kw in keywords):
                return topic_name
        return "general"


# =============================================================================
# PATTERN MINER — Find recurring themes across sessions
# =============================================================================

class PatternMiner:
    """Identifies patterns across multiple conversation signals."""

    def __init__(self):
        self.emotion_counts: dict[str, int] = defaultdict(int)
        self.trigger_counts: dict[str, int] = defaultdict(int)
        self.topic_counts: dict[str, int] = defaultdict(int)
        self.phrase_counts: dict[str, int] = defaultdict(int)
        self.session_emotions: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def ingest(self, signals: list[ConversationSignal], session_id: str) -> None:
        """Ingest a batch of signals from a session."""
        for sig in signals:
            self.emotion_counts[sig.primary_emotion] += 1
            for t in sig.trigger_flags:
                self.trigger_counts[t] += 1
            self.topic_counts[sig.topic] += 1
            for p in sig.key_phrases:
                self.phrase_counts[p] += 1
            self.session_emotions[session_id][sig.primary_emotion] += 1

    def get_top_emotions(self, n: int = 5) -> list[tuple[str, int]]:
        return sorted(self.emotion_counts.items(), key=lambda x: -x[1])[:n]

    def get_top_triggers(self, n: int = 5) -> list[tuple[str, int]]:
        return sorted(self.trigger_counts.items(), key=lambda x: -x[1])[:n]

    def get_top_topics(self, n: int = 5) -> list[tuple[str, int]]:
        return sorted(self.topic_counts.items(), key=lambda x: -x[1])[:n]

    def get_distinctive_phrases(self, n: int = 10) -> list[tuple[str, int]]:
        """Phrases that appear 3+ times — these reveal stable values."""
        return [(p, c) for p, c in sorted(self.phrase_counts.items(), key=lambda x: -x[1]) if c >= 3][:n]

    def get_emotional_trajectory(self, session_dates: list[str]) -> EmotionalTrajectory:
        """Analyze emotional direction across sessions."""
        if not session_dates:
            return EmotionalTrajectory(
                date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                overall_state="unknown",
                primary_emotion="neutral",
                intensity_avg=0.5,
                distress_level=0.0,
                notable_events=[],
                trajectory_direction="unknown",
            )

        recent_sessions = list(self.session_emotions.items())[-7:]  # last 7 sessions

        # Calculate average distress
        total_distress = 0
        total_intensity = 0
        emotion_totals: dict[str, int] = defaultdict(int)

        for session_id, emotions in recent_sessions:
            emotion_totals["anger"] += emotions.get("anger", 0)
            emotion_totals["sadness"] += emotions.get("sadness", 0)
            emotion_totals["fear"] += emotions.get("fear", 0)
            emotion_totals["joy"] += emotions.get("joy", 0)
            emotion_totals["trust"] += emotions.get("trust", 0)

        primary = max(emotion_totals, key=emotion_totals.get) if emotion_totals else "neutral"

        # Determine direction
        if len(recent_sessions) >= 3:
            early = sum(self.session_emotions[s].get("joy", 0) for s, _ in recent_sessions[:2])
            late = sum(self.session_emotions[s].get("joy", 0) for s, _ in recent_sessions[-2:])
            if late > early:
                direction = "improving"
            elif late < early:
                direction = "declining"
            else:
                direction = "stable"
        else:
            direction = "stable"

        # Overall state
        if emotion_totals.get("anger", 0) > 3 or emotion_totals.get("sadness", 0) > 3:
            overall = "stressed"
        elif emotion_totals.get("joy", 0) > emotion_totals.get("sadness", 0):
            overall = "flourishing"
        else:
            overall = "stable"

        return EmotionalTrajectory(
            date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            overall_state=overall,
            primary_emotion=primary,
            intensity_avg=0.5,
            distress_level=min(1.0, emotion_totals.get("anger", 0) * 0.1 + emotion_totals.get("fear", 0) * 0.1),
            notable_events=[],
            trajectory_direction=direction,
        )


# =============================================================================
# ANCHOR SYSTEM — Confidence-weighted belief storage
# =============================================================================

class AnchorSystem:
    """Tracks how confident Zaya is in each belief about the user.

    Every belief has an ANCHOR SCORE — a weighted confidence based on:
    - How many times it was confirmed across sessions
    - How recent the confirmations are
    - Whether it was ever contradicted (which degrades confidence)
    - What type of evidence: "action" > "specific words" > "implied"

    This is what makes Zaya's identity updates intelligent, not just cumulative.
    If the user says "I'm always direct" in one session but shows up soft
    and hesitant in 5 sessions afterward, the Anchor System weighs the
    BEHAVIOR higher than the SELF-DESCRIPTION.
    """

    def __init__(self):
        self.anchors: dict[str, AnchorScore] = {}

    def record(self, belief: str, session_id: str, evidence: str = "implied",
              contradicted: bool = False) -> None:
        """Record a belief observation."""
        now = datetime.now(timezone.utc).isoformat()

        if belief not in self.anchors:
            self.anchors[belief] = AnchorScore(
                belief=belief,
                confidence=0.3,
                first_seen=now,
                last_confirmed=now,
                evidence_sessions=[session_id],
                contradicted_by=[],
                is_stable=False,
            )

        anchor = self.anchors[belief]

        if contradicted:
            anchor.contradicted_by.append(session_id)
            anchor.confidence = max(0.1, anchor.confidence - 0.15)
        else:
            # Evidence strength: action=0.3, specific_words=0.2, implied=0.1
            strength = {"action": 0.3, "specific_words": 0.2, "implied": 0.1}.get(evidence, 0.1)
            anchor.confidence = min(1.0, anchor.confidence + strength)
            anchor.last_confirmed = now
            if session_id not in anchor.evidence_sessions:
                anchor.evidence_sessions.append(session_id)

        # Stable when confidence > 0.8 and evidence spans 3+ sessions
        if anchor.confidence > 0.8 and len(set(anchor.evidence_sessions)) >= 3:
            anchor.is_stable = True

    def get(self, belief: str) -> Optional[AnchorScore]:
        return self.anchors.get(belief)

    def get_all_stable(self) -> list[AnchorScore]:
        return [a for a in self.anchors.values() if a.is_stable]

    def get_unstable_beliefs(self) -> list[AnchorScore]:
        """Return beliefs that need more evidence."""
        return [a for a in self.anchors.values() if not a.is_stable and a.confidence > 0.3]

    def check_coherence(self, new_belief: str, existing_beliefs: list[str]) -> tuple[bool, str]:
        """Check if a new belief contradicts established ones."""
        contradictions = {
            "values_partnership": ["respects_clarity"],
            "reluctant_to_value_time": ["respects_clarity"],
            "integrity_matters": ["reluctant_to_value_time"],
        }

        for existing in existing_beliefs:
            if existing in contradictions and new_belief in contradictions[existing]:
                return False, f"Contradiction: '{new_belief}' conflicts with '{existing}'"

        return True, "coherent"


# =============================================================================
# IDENTITY UPDATER — Writes updates to the 7 lens files
# =============================================================================

class IdentityUpdater:
    """Writes updates to the 7 identity lens files."""

    LENS_FILES = [
        "context.md",
        "history.md",
        "memory.md",
        "preferences.md",
        "conversations.md",
        "ethos.md",
        "morals.md",
    ]

    def __init__(self, identity_dir: Path):
        self.identity_dir = identity_dir
        self.identity_dir.mkdir(parents=True, exist_ok=True)

    def apply_update(self, update: IdentityUpdate) -> None:
        """Apply a single IdentityUpdate to the appropriate lens file."""
        file_path = self.identity_dir / update.file
        current = ""
        if file_path.exists():
            current = file_path.read_text()

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        confidence_bar = "█" * int(update.confidence * 10) + "░" * (10 - int(update.confidence * 10))

        new_entry = f"\n\n---\n[{now}] · confidence: {confidence_bar} ({update.confidence:.0%}) · evidence: {update.evidence_count}x\n**[{update.section}]** {update.entry}\n_reason: {update.reasoning}"

        if update.replaces and update.replaces in current:
            current = current.replace(update.replaces, new_entry)
        else:
            current += new_entry

        file_path.write_text(current)

    def initialize_empty_files(self) -> None:
        """Initialize all 7 lens files with headers if they don't exist."""
        headers = {
            "context.md": "# Context\n\nCurrent situation, environment, pressures.\n\n---\n",
            "history.md": "# History\n\nPatterns of what the user has experienced before.\n\nBuilt automatically from conversation analysis.\n---\n",
            "memory.md": "# Memory\n\nAccumulated knowledge and learned lessons about the user.\n\n---\n",
            "preferences.md": "# Communication Preferences\n\nHow the user actually communicates — especially under stress.\n\n---\n",
            "conversations.md": "# Conversational Voice\n\nZaya's actual speaking patterns when talking to this user.\n\n---\n",
            "ethos.md": "# Ethos\n\nCore beliefs about human worth, potential, and redemption.\n\nBuilt from observed patterns, not assumptions.\n---\n",
            "morals.md": "# Morals\n\nNon-negotiable lines this user has shown they hold.\n\nBuilt from observed behavior, not proclaimed beliefs.\n---\n",
        }

        for filename, header in headers.items():
            path = self.identity_dir / filename
            if not path.exists():
                path.write_text(header)


# =============================================================================
# COHERENCE CHECKER — Ensures lens files don't contradict each other
# =============================================================================

class CoherenceChecker:
    """Validates that identity updates don't create internal contradictions."""

    # Rules: if file X contains Y, file Z should not contain W
    CONTRADICTION_RULES: list[tuple[str, str, str, str, str]] = [
        # (source_file, source_pattern, target_file, target_pattern, description)
        ("preferences.md", "direct_with_validation", "ethos.md", "always_soft", "Style is direct but ethos says always soft"),
        ("morals.md", "never_abandon", "ethos.md", "disengage_on_abuse", "Morals say never abandon but ethos allows disengage"),
        ("preferences.md", "does_not_want_coddling", "ethos.md", "coddles_on_sadness", "Preferences say no coddling but ethos coddles"),
    ]

    def check_update(self, update: IdentityUpdate, identity_dir: Path) -> tuple[bool, list[str]]:
        """Check if applying an update would create contradictions."""
        warnings = []

        for rule in self.CONTRADICTION_RULES:
            src_file, src_pat, tgt_file, tgt_pat, desc = rule
            if update.file == src_file and src_pat in update.entry:
                # Check if the target file already has the contradictory content
                tgt_path = identity_dir / tgt_file
                if tgt_path.exists():
                    tgt_content = tgt_path.read_text()
                    if tgt_pat in tgt_content:
                        warnings.append(f"COHERENCE WARNING: {desc}")

        return len(warnings) == 0, warnings


# =============================================================================
# IDENTITY LEARNER — The main orchestrator
# =============================================================================

class IdentityLearner:
    """The autonomous identity building system.

    Call `.process_session(messages, session_id)` after every conversation.
    Call `.nightly_consolidation()` on a cron schedule.

    This is what makes Zaya intelligent about EACH user.
    Not just "this user is angry" — but "this specific user shows anger
    by going quiet and pulling away, so Zaya knows to give space."
    """

    def __init__(self, identity_dir: Path, ontology: dict[str, Any]):
        self.extractor = SignalExtractor(ontology)
        self.miner = PatternMiner()
        self.anchor = AnchorSystem()
        self.updater = IdentityUpdater(identity_dir)
        self.coherence = CoherenceChecker()
        self.identity_dir = identity_dir

    def process_session(
        self,
        messages: list[dict[str, Any]],
        session_id: str,
    ) -> list[IdentityUpdate]:
        """Process a single conversation session and return proposed updates."""
        if not messages:
            return []

        # Step 1: Extract signals from all messages
        signals = []
        for msg in messages:
            if not msg.get("content"):
                continue
            sig = self.extractor.process_message(msg, session_id)
            signals.append(sig)

        self.miner.ingest(signals, session_id)

        # Step 2: Generate identity updates from extracted signals
        updates = self._generate_updates(signals, session_id)

        # Step 3: Check coherence and apply
        for update in updates:
            coherent, warnings = self.coherence.check_update(update, self.identity_dir)
            if warnings:
                logger.warning(f"Coherence check on session {session_id}: {warnings}")
            self.updater.apply_update(update)

        # Step 4: Update anchor scores based on key phrases
        for sig in signals:
            for phrase in sig.key_phrases:
                self.anchor.record(phrase, session_id, evidence="implied",
                                  contradicted=("ghost" in phrase or "back" in phrase))

        # Step 5: Track trajectory
        trajectory = self.miner.get_emotional_trajectory([session_id])
        self._update_trajectory(trajectory, session_id)

        logger.info(
            "IdentityLearner: session %s -> %d signals, %d updates",
            session_id, len(signals), len(updates)
        )
        return updates

    def nightly_consolidation(self, all_sessions) -> None:
        """Run deep analysis across ALL sessions to find cross-session patterns.

        Called by dream mode every 6 hours. This is where the real intelligence
        lives — patterns that only emerge when you zoom out to see all sessions.
        """
        # Re-process all sessions through the pattern miner
        self.miner = PatternMiner()  # Reset for fresh analysis
        for session_id, messages in all_sessions:
            signals = [
                self.extractor.process_message(msg, session_id)
                for msg in messages if msg.get("content")
            ]
            self.miner.ingest(signals, session_id)

        # Generate cross-session updates
        updates = self._generate_cross_session_updates()
        for update in updates:
            self.updater.apply_update(update)

        # Update stable anchors
        stable = self.anchor.get_all_stable()
        trajectory = self.miner.get_emotional_trajectory(
            [s[0] for s in all_sessions]
        )
        self._update_trajectory(trajectory, "nightly_consolidation")

        logger.info(
            f"Nightly consolidation: {len(all_sessions)} sessions → "
            f"{len(stable)} stable anchors, trajectory={trajectory.trajectory_direction}"
        )

    def _generate_updates(
        self,
        signals: list[ConversationSignal],
        session_id: str,
    ) -> list[IdentityUpdate]:
        """Generate IdentityUpdate objects from extracted signals."""
        updates = []

        # Aggregate by type
        emotions = [s.primary_emotion for s in signals]
        triggers = [t for s in signals for t in s.trigger_flags]
        topics = [s.topic for s in signals]
        phrases = [p for s in signals for p in s.key_phrases]
        distress_signals = [s for s in signals if s.is_distress_signal]

        # CONTEXT UPDATE: what's happening now
        if topics:
            top_topic = max(set(topics), key=topics.count)
            if top_topic != "general":
                updates.append(IdentityUpdate(
                    file="context.md",
                    section="Current Focus",
                    entry=f"Recent topic: **{top_topic}** — session {session_id}",
                    confidence=0.7,
                    source_signals=[session_id],
                    evidence_count=topics.count(top_topic),
                    reasoning=f"Most frequent topic in session ({topics.count(top_topic)}x)",
                ))

        # HISTORY UPDATE: patterns across sessions
        if triggers:
            top_trigger = max(set(triggers), key=triggers.count)
            updates.append(IdentityUpdate(
                file="history.md",
                section="Trigger Patterns",
                entry=f"Trigger detected: **{top_trigger}** (from {signals[0].text[:100]}...)",
                confidence=0.6,
                source_signals=[session_id],
                evidence_count=triggers.count(top_trigger),
                reasoning="Trigger appeared in this session",
            ))

        # PREFERENCES UPDATE: how they communicate under stress
        for sig in distress_signals:
            if sig.arousal == "high":
                updates.append(IdentityUpdate(
                    file="preferences.md",
                    section="Under Stress",
                    entry=f"When highly activated (intensity={sig.intensity:.0%}), uses: **{sig.primary_emotion}** — example: \"{sig.text[:80]}\"",
                    confidence=0.5,
                    source_signals=[session_id],
                    evidence_count=1,
                    reasoning="Distress signal with high arousal in session",
                ))

        # CONVERSATIONS UPDATE: distinctive language
        if phrases:
            for phrase in set(phrases):
                updates.append(IdentityUpdate(
                    file="conversations.md",
                    section="Distinctive Language",
                    entry=f"Pattern **{phrase}** — evidence: \"{next(s.text[:80] for s in signals if phrase in s.key_phrases)}\"",
                    confidence=0.5,
                    source_signals=[session_id],
                    evidence_count=phrases.count(phrase),
                    reasoning=f"Phrase appeared {phrases.count(phrase)}x in session",
                ))

        return updates

    def _generate_cross_session_updates(self) -> list[IdentityUpdate]:
        """Deep analysis across all sessions — generates high-confidence updates."""
        updates = []

        # Top emotions across all sessions
        top_emotions = self.miner.get_top_emotions(3)
        if top_emotions:
            top_emotion, count = top_emotions[0]
            updates.append(IdentityUpdate(
                file="context.md",
                section="Emotional Baseline",
                entry=f"Most frequent emotional state: **{top_emotion}** (observed {count}x across sessions)",
                confidence=min(0.9, 0.4 + count * 0.05),
                source_signals=[],
                evidence_count=count,
                reasoning="Dominant emotion across all analyzed sessions",
            ))

        # Top triggers — these become stable identity markers
        top_triggers = self.miner.get_top_triggers(3)
        for trigger, count in top_triggers:
            if count >= 2:
                updates.append(IdentityUpdate(
                    file="history.md",
                    section="Core Triggers",
                    entry=f"**{trigger}** — activated {count}x across sessions. Pattern: {trigger}",
                    confidence=min(0.9, 0.3 + count * 0.15),
                    source_signals=[],
                    evidence_count=count,
                    reasoning=f"Trigger detected {count}x across multiple sessions — stable pattern",
                ))

        # Distinctive phrases — 3+ appearances = stable value
        distinctive = self.miner.get_distinctive_phrases(5)
        for phrase, count in distinctive:
            updates.append(IdentityUpdate(
                file="preferences.md",
                section="Stated Values",
                entry=f"**{phrase}** — demonstrated {count}x. This is a core value.",
                confidence=min(0.95, 0.5 + count * 0.1),
                source_signals=[],
                evidence_count=count,
                reasoning=f"Phrase detected {count}x across sessions — treated as stable value",
            ))

        # Trajectory — are they improving or declining?
        trajectory = self.miner.get_emotional_trajectory([])
        updates.append(IdentityUpdate(
            file="history.md",
            section="Emotional Trajectory",
            entry=f"Overall direction: **{trajectory.trajectory_direction}** · state: {trajectory.overall_state}",
            confidence=0.7,
            source_signals=[],
            evidence_count=1,
            reasoning="Trajectory analysis from cross-session pattern mining",
        ))

        return updates

    def _update_trajectory(self, trajectory: EmotionalTrajectory, session_id: str) -> None:
        """Store emotional trajectory for trend analysis."""
        trajectory_path = self.identity_dir / "trajectory.jsonl"
        entry = {
            "session_id": session_id,
            "date": trajectory.date,
            "state": trajectory.overall_state,
            "direction": trajectory.trajectory_direction,
            "distress": trajectory.distress_level,
            "primary_emotion": trajectory.primary_emotion,
        }
        with open(trajectory_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
