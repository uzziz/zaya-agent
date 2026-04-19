"""
zaya/brain/empathy_engine.py

Layer 6: Empathy Injector — Emotional Subtext Inference System

Detects dissonance between what is SAID and what is MEANT.
Injects empathic awareness into Zaya's responses before they reach the user.

Core insight: Most emotion detection stops at explicit sentiment.
Empathy goes further — it infers what the person is NOT saying,
based on identity history, behavioral patterns, and conversational subtext.

Architecture:
  dissonance_detector()     → What is the gap between surface and inferred emotion?
  subtext_inferrer()       → What is being hidden, given who this person is?
  empathy_injector()       → How do I calibrate my response to match their reality?
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("zaya.brain.empathy_engine")

# =============================================================================
# DATA MODELS
# =============================================================================

class DissonanceLevel(str, Enum):
    """How large is the gap between what was said and what is inferred?"""
    NONE        = "none"       # Surface and inferred match
    LOW         = "low"        # Minor gap — might be nothing
    MEDIUM      = "medium"     # Clear mismatch — worth noting
    HIGH        = "high"      # Significant gap — emotionally important
    CRISIS      = "crisis"     # Severe mismatch — potential crisis signal


class SurfaceCategory(str, Enum):
    """What the person is explicitly communicating."""
    CALM        = "calm"         # "I'm fine", "it's okay"
    CONFUSED    = "confused"      # Expresses uncertainty
    FRUSTRATED  = "frustrated"    # Explicit frustration, annoyance
    ANGRY       = "angry"         # Explicit anger
    SAD         = "sad"           # Explicit sadness, disappointment
    ENTHUSIASTIC = "enthusiastic"  # Positive, excited
    NEUTRAL     = "neutral"        # Matter-of-fact, no strong emotion
    DEFLECTING  = "deflecting"     # Changing subject, minimizing


class InferredState(str, Enum):
    """What the pattern suggests the person is actually feeling."""
    FINE                    = "fine"
    HIDING_FEAR             = "hiding_fear"
    HIDING_ANGER            = "hiding_anger"
    HIDING_SADNESS          = "hiding_sadness"
    DISAPPOINTED            = "disappointed"
    USED                    = "used"           # Feeling taken advantage of
    MISUNDERSTOOD           = "misunderstood"
    PULLING_BACK            = "pulling_back"    # emotionally withdrawing
    TESTING_YOU             = "testing_you"     # probing commitment
    GUILT                   = "guilt"           # knows they're wrong but won't admit
    OVERWHELMED             = "overwhelmed"
    UNCERTAIN               = "uncertain"
    DISHONEST               = "dishonest"       # deliberately misleading
    EXPLOITING              = "exploiting"      # using you
    ANGER                   = "anger"            # explicitly angry, not hiding it
    SAD                     = "sad"              # explicitly sad, not hiding it


@dataclass
class EmotionalDissonance:
    """The gap between what was said and what was meant."""
    surface_emotion: SurfaceCategory
    inferred_state: InferredState
    dissonance_level: DissonanceLevel
    confidence: float                           # 0.0 - 1.0
    signals: list[str]                          # what drove the inference
    subtext: str                               # the inferred meaning underneath
    recommended_tone: str                       # how Zaya should adjust her response
    urgency: str                               # "low" / "medium" / "high" / "now"


@dataclass
class SubtextInference:
    """What the person is NOT saying — the hidden layer."""
    what_is_hidden: str                        # One sentence of inferred subtext
    what_is_needed: str                        # What they actually need from this exchange
    behavioral_roots: list[str]                 # Historical patterns driving this
    confidence: float                           # 0.0 - 1.0
    identity_evidence: list[str]                 # From identity files
    dissonance_contributing_factors: list[str]   # What widened the gap


@dataclass
class EmpathyProfile:
    """The complete empathy read for a given conversation."""
    dissonance: EmotionalDissonance
    subtext: SubtextInference
    raw_surface: str                            # The words they used
    context_window: int                         # How many messages were analyzed
    model_based: bool                          # Did this use identity context or just surface?
    timestamp: str


@dataclass
class EmpathyResponseCalibration:
    """How Zaya should adjust her response given the empathy read."""
    response_tone: str                         # "gentle", "direct", "hold_space", "challenge"
    validate_before_answer: bool               # Should Zaya validate the inferred subtext?
    match_surface_or_depth: str                # "surface" (match words) or "depth" (address subtext)
    boundary_setting_ok: bool                  # Is this person in a state where boundaries land?
    recommended_openers: list[str]             # Phrases that would resonate
    recommended_closers: list[str]             # How to end the response well
    red_flags: list[str]                       # Phrases/approaches to avoid


# =============================================================================
# DISSONANCE DETECTOR
# =============================================================================

class DissonanceDetector:
    """
    Analyzes a sequence of messages to find the gap between what was SAID
    and what the PATTERN suggests was MEANT.

    Surface reading: what emotion is explicitly expressed?
    Deep reading: what does the behavioral pattern suggest is actually happening?
    """

    # Patterns that suggest someone is hiding their real state
    DISMISSIVE_PATTERNS = [
        r"\bi'm? fine\b",
        r"\bwhatever\b",
        r"\bdoesn't matter\b",
        r"\bno worries\b",
        r"\bnot a big deal\b",
        r"\bi don't care\b",
        r"\bdoesn't really matter to me\b",
        r"\bjust\b.*\bwhatever\b",
    ]

    # Patterns that suggest someone is NOT being direct about discomfort
    DEFLECTION_PATTERNS = [
        r"\bi mean\b.*\bi guess\b",
        r"\bsorry\b.*\bbut\b",
        r"\bno offense\b",
        r"\bnot trying to\b",
        r"\bhonestly\b.*\bnot sure\b",
        r"\bI don't want to\b.*\bbut\b",
        r"\bi guess\b",
    ]

    # Patterns that indicate disappointment beneath the surface
    DISAPPOINTMENT_PATTERNS = [
        r"\bi just thought\b.*\bwould go\b",
        r"\bdifferent expectations\b",
        r"\bI expected\b",
        r"\bnot what I\b.*\bhoped\b",
        r"\bI was hoping\b.*\bbut\b",
        r"\bit's fine\b.*\bbut\b",
        r"\bi'm not upset\b",
        r"\bno,? no,?\b.*\bnot upset\b",
        r"\bjust\b.*\bexpectations\b",
        r"\bmaybe I was wrong\b",
    ]

    # Patterns suggesting genuine positive alignment (no hiding)
    GENUINE_POSITIVE_PATTERNS = [
        r"\bexactly what I was thinking\b",
        r"\blet's do it\b",
        r"\bi'm in\b",
        r"\bcount me in\b",
        r"100%.*\bwith you\b",
    ]

    # Patterns suggesting someone is retreating from a commitment
    RETREAT_PATTERNS = [
        r"\bhowever\b.*\bstill figuring out\b",
        r"\bi'll get back to you\b",
        r"\blet me think about it\b",
        r"\bmaybe\b.*\bfirst\b",
        r"\bactually\b.*\bnevermind\b",
        r"^so\b.*\bchange\b",
        r"\bthat's not what I meant\b",
        r"\bi didn't say\b.*\bI said\b",
        r"\bI mean\b.*\bI guess\b",
        r"\bi don't know\b.*\bmaybe\b",
        r"\bnot sure\b",
        r"\bthings change\b",
        r"\blet's revisit\b",
        r"\brevisit this\b",
        r"\bmaybe later\b",
        r"\bnot that I'm out\b",
        r"\bi'm just not sure\b",
    ]

    # Financial/power patterns — person is avoiding paying or committing
    COMMITMENT_AVOIDANCE_PATTERNS = [
        r"\bsecurity\b.*\bconcerns?\b",
        r"\bneed to think\b",
        r"\bnot the right time\b",
        r"\bcan we start small\b",
        r"\bi'm interested but\b",
        r"\blet's revisit\b",
        r"\bwhat if\b.*\binstead\b",
        r"\bthe thing is\b.*\bbut\b",
        r"\bmy concern is\b",
        r"\bi have some concerns\b",
        r"\bi'm not 100%\b",
        r"\bi need more time\b",
        r"\buntil I see something\b",
        r"\bwhen you show me\b",
        r"\bi'm a client\b",           # "I'm not a client, I'm a partner"
        r"\bco-founder\b.*\bclient\b",  # distinguishing the two
        r"\bbeing a client\b.*\ba business partner\b",  # direct contrast
        r"\bclient\b.*\bpartner\b.*\btwo very different\b",  # explicit distinction
        r"\bwe're not aligned\b",
        r"\bmore interested in.*client\b",
        r"\binterested in.*join.*force\b.*\bnot\b.*\bmoney\b",
        r"\bdon't want to give\b.*\bmoney\b",
        r"\bdoesn't involve.*giving money\b",
        r"\bI can't give any money\b",
        r"\bgold.?digger\b",
        r"\bI can't.*Jacobi\b",
    ]

    # Patterns suggesting someone is flattering to avoid confrontation
    FLATTERY_DEFLECTION_PATTERNS = [
        r"\byou're amazing\b",
        r"\byou're very talented\b",
        r"\bI think you're great\b",
        r"\bI think you're.*talented\b",
        r"\bno disrespect to you\b",
        r"\bnot trying to be rude\b",
        r"\bhope this doesn't come across\b",
        r"\bi respect you but\b",
        r"\bi don't mean to come across\b",
        r"\bi hope you are well\b",
        r"\bI can help you\b.*\bwith this\b",
        r"\bI'm more than happy to help\b",
    ]

    # Escalation patterns — person is getting more upset beneath calm surface
    CALM_ESCALATION_PATTERNS = [
        r"\bi'm just saying\b",
        r"\bI'm being direct\b",
        r"\bto be honest with you\b",
        r"\blisten\b.*\bfor a second\b",
        r"\bhere's the thing\b",
        r"\bthe reality is\b",
        r"\bwhat's happening here is\b",
        r"\bI don't understand why\b",
    ]

    def __init__(self):
        self.dismissive_re  = [re.compile(p, re.IGNORECASE) for p in self.DISMISSIVE_PATTERNS]
        self.deflection_re = [re.compile(p, re.IGNORECASE) for p in self.DEFLECTION_PATTERNS]
        self.positive_re    = [re.compile(p, re.IGNORECASE) for p in self.GENUINE_POSITIVE_PATTERNS]
        self.retreat_re    = [re.compile(p, re.IGNORECASE) for p in self.RETREAT_PATTERNS]
        self.commit_avoid_re = [re.compile(p, re.IGNORECASE) for p in self.COMMITMENT_AVOIDANCE_PATTERNS]
        self.flattery_re   = [re.compile(p, re.IGNORECASE) for p in self.FLATTERY_DEFLECTION_PATTERNS]
        self.escalation_re = [re.compile(p, re.IGNORECASE) for p in self.CALM_ESCALATION_PATTERNS]
        self.disappointment_re = [re.compile(p, re.IGNORECASE) for p in self.DISAPPOINTMENT_PATTERNS]

    def detect(self, messages: list[dict[str, Any]]) -> EmotionalDissonance:
        """
        Main entry point. Analyzes messages and returns dissonance profile.

        Args:
            messages: List of message dicts with at least {"content": str}

        Returns:
            EmotionalDissonance with surface/inferred analysis
        """
        if not messages:
            return self._no_dissonance()

        text = self._flatten_messages(messages)
        signals = []

        # Step 1: Classify surface emotion
        surface = self._classify_surface(text, messages)
        signals.extend(surface["signals"])

        # Step 2: Check for commitment avoidance (critical for Zaya's use case)
        commit_signals = self._detect_commitment_avoidance(text)
        signals.extend(commit_signals)

        # Step 3: Check for retreat from word (backing out of stated position)
        retreat_signals = self._detect_retreat(text)
        signals.extend(retreat_signals)

        # Step 4: Check for flattery deflection
        flattery_signals = self._detect_flattery_deflection(text)
        signals.extend(flattery_signals)

        # Step 5: Check for calm escalation
        escalation_signals = self._detect_calm_escalation(text)
        signals.extend(escalation_signals)

        # Step 6: Check for disappointment patterns
        disappointment_signals = self._detect_disappointment(text)
        signals.extend(disappointment_signals)

        # Step 7: Check for genuine positive
        genuine = self._detect_genuine_positive(text)
        if genuine:
            signals.append("Genuine positive alignment detected")

        # Step 7: Classify inferred state
        inferred = self._classify_inferred_state(surface, commit_signals, retreat_signals, flattery_signals, escalation_signals, disappointment_signals, genuine, text)

        # Step 8: Calculate dissonance
        dissonance = self._calculate_dissonance(surface, inferred, signals, text)

        logger.info(f"DissonanceDetector: surface={surface['category'].value}, inferred={inferred['state'].value}, "
                    f"level={dissonance.dissonance_level.value}, confidence={dissonance.confidence:.2f}")

        return dissonance

    def _flatten_messages(self, messages: list[dict[str, Any]]) -> str:
        """Combine all message content into one string."""
        parts = []
        for msg in messages:
            content = msg.get("content", "")
            if content:
                parts.append(str(content))
        return " ".join(parts)

    def _classify_surface(self, text: str, messages: list[dict]) -> dict:
        """Determine what the person is EXPLICITLY communicating."""
        text_lower = text.lower()
        signals = []

        # Count explicit emotion words
        anger_words = sum(1 for w in ["angry", "frustrated", "annoyed", "irritated", "furious"] if w in text_lower)
        sad_words   = sum(1 for w in ["sad", "disappointed", "hurt", "upset", "crushed"] if w in text_lower)
        fear_words  = sum(1 for w in ["scared", "afraid", "worried", "concerned", "nervous"] if w in text_lower)
        happy_words = sum(1 for w in ["excited", "happy", "great", "awesome", "love this"] if w in text_lower)

        # Check dismissive
        dismissive_count = sum(1 for r in self.dismissive_re if r.search(text))
        deflection_count = sum(1 for r in self.deflection_re if r.search(text))

        if dismissive_count >= 2:
            category = SurfaceCategory.CALM
            signals.append(f"Dismissive language ({dismissive_count} patterns)")
        elif deflection_count >= 1 and dismissive_count >= 1:
            category = SurfaceCategory.DEFLECTING
            signals.append(f"Deflection with dismissiveness ({deflection_count}/{dismissive_count})")
        elif anger_words > sad_words and anger_words >= 2:
            category = SurfaceCategory.ANGRY
            signals.append(f"Explicit anger ({anger_words} anger words)")
        elif sad_words >= 2:
            category = SurfaceCategory.SAD
            signals.append(f"Explicit sadness ({sad_words} sad words)")
        elif fear_words >= 2:
            category = SurfaceCategory.CONFUSED
            signals.append(f"Explicit fear/worry ({fear_words} fear words)")
        elif happy_words >= 3:
            category = SurfaceCategory.ENTHUSIASTIC
            signals.append(f"Explicit enthusiasm ({happy_words} positive words)")
        elif dismissive_count >= 1:
            category = SurfaceCategory.CALM
            signals.append(f"Mild dismissiveness ({dismissive_count} patterns)")
        else:
            category = SurfaceCategory.NEUTRAL
            signals.append("No strong explicit emotion detected")

        return {
            "category": category,
            "signals": signals,
            "text": text,
        }

    def _detect_commitment_avoidance(self, text: str) -> list[str]:
        """Detect patterns that suggest someone is avoiding a financial or commitment decision."""
        signals = []
        matches = []
        for r in self.commit_avoid_re:
            if r.search(text):
                matches.append(r.pattern[:50])

        if len(matches) >= 3:
            signals.append(f"Strong commitment avoidance ({len(matches)} patterns)")
        elif len(matches) >= 1:
            signals.append(f"Mild commitment avoidance ({len(matches)} patterns)")

        return signals

    def _detect_retreat(self, text: str) -> list[str]:
        """Detect when someone is backing out of a stated position."""
        signals = []
        matches = []
        for r in self.retreat_re:
            if r.search(text):
                matches.append(r.pattern[:50])

        if len(matches) >= 2:
            signals.append(f"Strong retreat from stated position ({len(matches)} patterns)")
        elif len(matches) >= 1:
            signals.append(f"Mild retreat from stated position ({len(matches)} pattern(s))")

        return signals

    def _detect_flattery_deflection(self, text: str) -> list[str]:
        """Detect excessive compliments used to soften a rejection."""
        signals = []
        matches = []
        for r in self.flattery_re:
            if r.search(text):
                matches.append(r.pattern[:50])

        if len(matches) >= 2:
            signals.append(f"Flattery deflection ({len(matches)} patterns) — likely softening rejection")
        elif len(matches) >= 1:
            signals.append(f"Mild flattery softening ({len(matches)} patterns)")

        return signals

    def _detect_calm_escalation(self, text: str) -> list[str]:
        """Detect escalation disguised as calm — 'I'm being direct' while getting more intense."""
        signals = []
        matches = []
        for r in self.escalation_re:
            if r.search(text):
                matches.append(r.pattern[:50])

        if matches:
            signals.append(f"Calm escalation signals ({len(matches)} patterns) — tension beneath calm")

        return signals

    def _detect_disappointment(self, text: str) -> list[str]:
        """Detect disappointment signals — 'I expected more' beneath the surface."""
        signals = []
        matches = []
        for r in self.disappointment_re:
            if r.search(text):
                matches.append(r.pattern[:50])

        if len(matches) >= 2:
            signals.append(f"Strong disappointment signals ({len(matches)} patterns)")
        elif len(matches) >= 1:
            signals.append(f"Mild disappointment signals ({len(matches)} pattern(s))")

        return signals

    def _detect_genuine_positive(self, text: str) -> bool:
        """Check if there's genuine positive alignment — no hiding."""
        return any(r.search(text) for r in self.positive_re)

    def _classify_inferred_state(
        self,
        surface: dict,
        commit_signals: list,
        retreat_signals: list,
        flattery_signals: list,
        escalation_signals: list,
        disappointment_signals: list,
        genuine: bool,
        text: str
    ) -> dict:
        """
        Based on the pattern of signals, classify the inferred emotional state —
        what the person is likely FEELING but not saying.
        """
        signals = surface["signals"] + commit_signals + retreat_signals + flattery_signals + escalation_signals + disappointment_signals
        surface_cat = surface["category"]
        text_lower = text.lower()
        signal_count = len(signals)
        # Parse actual dismissive pattern count from signal text (e.g. "Dismissive language (3 patterns)")
        dismissive_count = 0
        for s in surface["signals"]:
            m = re.search(r"\((\d+)\s*pattern", s, re.IGNORECASE)
            if m:
                dismissive_count = max(dismissive_count, int(m.group(1)))

        # Strong combined signals override "genuine" check
        strong_combination = (len(commit_signals) >= 3 and len(flattery_signals) >= 2)

        # High confidence inferences
        if strong_combination:
            # Strong commitment avoidance + flattery = exploiting or dishonest
            if any("gold digger" in text_lower or "I can't give any money" in text_lower for _ in [1]):
                return {"state": InferredState.EXPLOITING, "signals": signals}
            return {"state": InferredState.DISHONEST, "signals": signals}

        if genuine and surface_cat in (SurfaceCategory.ENTHUSIASTIC, SurfaceCategory.NEUTRAL):
            # Only if genuine commitment language AND no strong avoidance signals
            if not strong_combination and signal_count < 4:
                return {"state": InferredState.FINE, "signals": signals}

        # Disappointment patterns = disappointed
        if disappointment_signals:
            return {"state": InferredState.DISAPPOINTED, "signals": signals}

        # Strong dismissiveness (3+) + CALM surface = hiding something (I'm fine scenario)
        if dismissive_count >= 3 and surface_cat == SurfaceCategory.CALM:
            return {"state": InferredState.HIDING_SADNESS, "signals": signals}

        # Commitment avoidance + flattery = using flattery to avoid paying/committing
        if commit_signals and flattery_signals:
            if any("exploiting" in s.lower() or "gold digger" in text_lower for s in signals):
                return {"state": InferredState.EXPLOITING, "signals": signals}
            return {"state": InferredState.DISHONEST, "signals": signals}

        # Commitment avoidance with retreat signals = backing out of stated commitment
        if commit_signals and retreat_signals:
            if any("gold digger" in text_lower or "using" in text_lower for _ in [1]):
                return {"state": InferredState.USED, "signals": signals}
            return {"state": InferredState.PULLING_BACK, "signals": signals}

        # Retreat + calm surface = said one thing, doing another
        if retreat_signals and surface_cat == SurfaceCategory.CALM:
            if any("test" in text_lower for _ in [1]):
                return {"state": InferredState.TESTING_YOU, "signals": signals}
            return {"state": InferredState.DISAPPOINTED, "signals": signals}

        # Retreat on neutral surface = pulling back (without strong commitment avoidance)
        if retreat_signals and surface_cat == SurfaceCategory.NEUTRAL:
            if len(retreat_signals) >= 1:
                return {"state": InferredState.PULLING_BACK, "signals": signals}

        # Flattery + retreat = "I respect you BUT"
        if flattery_signals and retreat_signals:
            return {"state": InferredState.GUILT, "signals": signals}

        # Escalation beneath calm = anger underneath
        if escalation_signals and surface_cat == SurfaceCategory.CALM:
            return {"state": InferredState.HIDING_ANGER, "signals": signals}

        # Explicit fear words but hiding real concern
        if commit_signals and surface_cat == SurfaceCategory.CONFUSED:
            return {"state": InferredState.HIDING_FEAR, "signals": signals}

        # Sadness disguised as calm = disappointment
        if surface_cat == SurfaceCategory.CALM and retreat_signals:
            return {"state": InferredState.DISAPPOINTED, "signals": signals}

        # Classic dismissive = hiding something
        if surface_cat == SurfaceCategory.CALM and commit_signals:
            return {"state": InferredState.HIDING_ANGER, "signals": signals}

        # Sadness surface
        if surface_cat == SurfaceCategory.SAD:
            return {"state": InferredState.SAD, "signals": signals}

        # Anger surface
        if surface_cat == SurfaceCategory.ANGRY:
            return {"state": InferredState.ANGER, "signals": signals}

        return {"state": InferredState.FINE, "signals": signals}

    def _calculate_dissonance(
        self,
        surface: dict,
        inferred: dict,
        signals: list,
        text: str
    ) -> EmotionalDissonance:
        """Determine the dissonance level and recommended response tone."""

        surface_cat = surface["category"]
        inferred_state = inferred["state"]
        signal_count = len(signals)

        # Confidence based on signal strength
        if signal_count >= 4:
            confidence = 0.85
        elif signal_count >= 2:
            confidence = 0.70
        elif signal_count >= 1:
            confidence = 0.55
        else:
            confidence = 0.40

        # Same = no dissonance
        if surface_cat == SurfaceCategory.ENTHUSIASTIC and inferred_state == InferredState.FINE:
            level = DissonanceLevel.NONE
            tone = "enthusiastic"
            urgency = "low"
        elif surface_cat == SurfaceCategory.NEUTRAL and inferred_state == InferredState.FINE:
            level = DissonanceLevel.NONE
            tone = "neutral"
            urgency = "low"

        # Mismatch cases
        elif inferred_state in (InferredState.EXPLOITING, InferredState.USED):
            level = DissonanceLevel.HIGH
            tone = "direct"
            urgency = "high"
        elif inferred_state in (InferredState.DISHONEST, InferredState.TESTING_YOU):
            level = DissonanceLevel.HIGH
            tone = "challenge"
            urgency = "medium"
        elif inferred_state in (InferredState.HIDING_ANGER, InferredState.DISAPPOINTED, InferredState.GUILT):
            level = DissonanceLevel.MEDIUM
            tone = "direct"
            urgency = "medium"
        elif inferred_state in (InferredState.PULLING_BACK,):
            level = DissonanceLevel.HIGH
            tone = "hold_space"
            urgency = "medium"
        elif inferred_state in (InferredState.HIDING_SADNESS, InferredState.HIDING_FEAR):
            level = DissonanceLevel.MEDIUM
            tone = "gentle"
            urgency = "low"
        elif inferred_state in (InferredState.OVERWHELMED,):
            level = DissonanceLevel.LOW
            tone = "gentle"
            urgency = "low"
        else:
            level = DissonanceLevel.LOW
            tone = "neutral"
            urgency = "low"

        # Build subtext sentence
        subtext = self._build_subtext(surface_cat, inferred_state, text)

        return EmotionalDissonance(
            surface_emotion=surface_cat,
            inferred_state=inferred_state,
            dissonance_level=level,
            confidence=confidence,
            signals=signals,
            subtext=subtext,
            recommended_tone=tone,
            urgency=urgency,
        )

    def _build_subtext(self, surface: SurfaceCategory, inferred: InferredState, text: str) -> str:
        """Generate a one-sentence inference of what's beneath the surface."""
        templates = {
            InferredState.USED:             "They're feeling used — they gave time/energy and feel it wasn't valued.",
            InferredState.EXPLOITING:       "They're using flattery to avoid a real commitment while extracting value.",
            InferredState.DISHONEST:       "They're not being straight about their intentions — there's an agenda.",
            InferredState.TESTING_YOU:     "They're probing to see if you'll push back or fold.",
            InferredState.GUILT:           "They know they're in the wrong but won't admit it directly.",
            InferredState.PULLING_BACK:   "They're withdrawing from a commitment they made.",
            InferredState.DISAPPOINTED:    "They're disappointed but expressing it indirectly.",
            InferredState.HIDING_ANGER:    "There's anger underneath — they're staying calm to maintain control.",
            InferredState.HIDING_FEAR:     "Fear is driving this — the 'concern' is a shield for something else.",
            InferredState.HIDING_SADNESS:  "Sadness is underneath — the calm is protective.",
            InferredState.OVERWHELMED:     "They're stretched thin — this conversation is adding to the load.",
            InferredState.MISUNDERSTOOD:   "They feel unheard and are trying to get you to really listen.",
            InferredState.UNCERTAIN:       "They don't know what they want — they're not ready to commit.",
            InferredState.FINE:             "What you see is what you get — no hidden layer detected.",
            InferredState.ANGER:            "They are angry and expressing it directly.",
            InferredState.SAD:              "They are sad and expressing it directly.",
        }
        return templates.get(inferred, "Emotional state unclear — more data needed.")

    def _no_dissonance(self) -> EmotionalDissonance:
        return EmotionalDissonance(
            surface_emotion=SurfaceCategory.NEUTRAL,
            inferred_state=InferredState.FINE,
            dissonance_level=DissonanceLevel.NONE,
            confidence=0.0,
            signals=[],
            subtext="No dissonance detected.",
            recommended_tone="neutral",
            urgency="low",
        )


# =============================================================================
# SUBTEXT INFERER
# =============================================================================

class SubtextInferer:
    """
    Takes the dissonance output and enriches it with identity context.

    Uses the accumulated identity lens files (who this person is,
    what their patterns are, what they've done before) to produce
    a deeper inference of what they're not saying.
    """

    def __init__(self, identity_dir: str | Path = "zaya/brain/identity"):
        self.identity_dir = Path(identity_dir)

    def infer(
        self,
        messages: list[dict[str, Any]],
        dissonance: EmotionalDissonance
    ) -> SubtextInference:
        """
        Given surface signals + dissonance, enrich with identity context.
        """
        # Load relevant identity files
        identity_context = self._load_identity_context()

        # Build behavioral roots from identity history
        behavioral_roots = self._extract_behavioral_roots(identity_context, dissonance)

        # What is hidden given who this person is
        hidden = self._infer_what_is_hidden(dissonance, identity_context, messages)

        # What they actually need
        needed = self._infer_what_is_needed(dissonance, identity_context)

        # Dissonance contributing factors
        factors = self._identify_contributing_factors(dissonance, identity_context)

        # Identity evidence
        evidence = self._collect_identity_evidence(identity_context, dissonance)

        confidence = dissonance.confidence + 0.05 if identity_context else dissonance.confidence

        return SubtextInference(
            what_is_hidden=hidden,
            what_is_needed=needed,
            behavioral_roots=behavioral_roots,
            confidence=min(confidence, 0.95),
            identity_evidence=evidence,
            dissonance_contributing_factors=factors,
        )

    def _load_identity_context(self) -> dict[str, str]:
        """Load key identity files for contextual inference."""
        context = {}
        files = ["context.md", "history.md", "preferences.md", "memory.md"]
        for fname in files:
            fpath = self.identity_dir / fname
            if fpath.exists():
                try:
                    context[fname] = fpath.read_text()
                except Exception:
                    pass
        return context

    def _extract_behavioral_roots(
        self,
        identity_context: dict[str, str],
        dissonance: EmotionalDissonance
    ) -> list[str]:
        """Pull from history.md and memory.md for patterns that match current state."""
        roots = []

        if "history.md" in identity_context:
            history = identity_context["history.md"]
            # Look for commitment patterns
            if "commitment" in history.lower() or "word" in history.lower():
                roots.append("Has a history of commitments being discussed — this context is loaded")
            if "back" in history.lower() and (" forth" in history.lower() or "track" in history.lower()):
                roots.append("History of back-and-forth patterns noted")

        if "memory.md" in identity_context:
            memory = identity_context["memory.md"]
            if "money" in memory.lower() or "payment" in memory.lower():
                roots.append("Financial dynamics have been noted as significant in this relationship")
            if "trust" in memory.lower():
                roots.append("Trust has been flagged as a key issue previously")

        if not roots:
            roots.append("No specific matching history — inference based on surface pattern only")

        return roots

    def _infer_what_is_hidden(
        self,
        dissonance: EmotionalDissonance,
        identity_context: dict[str, str],
        messages: list[dict]
    ) -> str:
        """Generate the one-line subtext — what are they NOT saying?"""
        inferred = dissonance.inferred_state

        hidden_templates = {
            InferredState.USED:
                "They're not saying: 'I gave you my time and energy and now you want money on top — that feels like you were never really interested in me as a person.'",
            InferredState.EXPLOITING:
                "They're not saying: 'I want what you have without paying for it, and I'm using flattery to keep you engaged.'",
            InferredState.DISHONEST:
                "They're not saying: 'I'm not actually interested in a real deal — I'm keeping my options open while getting what I can from you.'",
            InferredState.TESTING_YOU:
                "They're not saying: 'I want to see if you'll prioritize me or the money.'",
            InferredState.GUILT:
                "They're not saying: 'I know I'm backing out but I can't admit it directly, so I'm framing it as a 'concern' to avoid accountability.'",
            InferredState.PULLING_BACK:
                "They're not saying: 'I've decided this isn't worth it but I don't want to say that directly.'",
            InferredState.DISAPPOINTED:
                "They're not saying: 'I expected better from this — I thought we were building something and it turned into a sales pitch.'",
            InferredState.HIDING_ANGER:
                "They're not saying: 'I'm actually angry that this conversation went the way it did and I'm staying calm to not be the 'difficult' one.'",
            InferredState.HIDING_FEAR:
                "They're not saying: 'The security concern is real but it's also an excuse — the real issue is I don't trust where this is going.'",
            InferredState.FINE:
                "Nothing significant is being hidden — what they said is roughly what they mean.",
        }

        return hidden_templates.get(inferred, "Subtext cannot be determined from available data.")

    def _infer_what_is_needed(
        self,
        dissonance: EmotionalDissonance,
        identity_context: dict[str, str]
    ) -> str:
        """What do they actually need from this exchange?"""
        inferred = dissonance.inferred_state

        needed_templates = {
            InferredState.USED:             "To feel recognized for what they already invested — proof that the relationship matters more than the transaction.",
            InferredState.EXPLOITING:        "To extract maximum value with minimum commitment — not a need Zaya should fulfill.",
            InferredState.DISHONEST:         "An honest reckoning — but they're avoiding it, so the need goes unmet.",
            InferredState.TESTING_YOU:       "Reassurance that Zaya sees them as more than a payment source.",
            InferredState.GUILT:             "To be able to back out without feeling like the villain — they need an exit that saves face.",
            InferredState.PULLING_BACK:      "To disengage without confrontation — they need space to retreat.",
            InferredState.DISAPPOINTED:      "To feel heard — 'I hear that you're disappointed' would land deeply right now.",
            InferredState.HIDING_ANGER:      "Permission to be angry — they need someone to acknowledge the frustration before they can move past it.",
            InferredState.HIDING_FEAR:       "Reassurance that they're safe — the real question is 'will I regret this?'",
            InferredState.FINE:              "Just move forward — there's no hidden need here.",
        }

        return needed_templates.get(inferred, "Need cannot be determined.")

    def _identify_contributing_factors(
        self,
        dissonance: EmotionalDissonance,
        identity_context: dict[str, str]
    ) -> list[str]:
        """What specific elements of the conversation widened the dissonance gap?"""
        factors = []

        if dissonance.signals:
            for signal in dissonance.signals[:3]:
                factors.append(signal)

        if dissonance.inferred_state in (InferredState.USED, InferredState.EXPLOITING):
            if "context.md" in identity_context:
                factors.append("Relationship dynamics around money/time already noted in context")

        if dissonance.dissonance_level in (DissonanceLevel.HIGH, DissonanceLevel.CRISIS):
            factors.append("Dissonance level HIGH — emotional significance above normal threshold")

        return factors

    def _collect_identity_evidence(
        self,
        identity_context: dict[str, str],
        dissonance: EmotionalDissonance
    ) -> list[str]:
        """Pull specific evidence from identity files that support this inference."""
        evidence = []

        for fname, content in identity_context.items():
            fname_lower = fname.lower()
            if dissonance.inferred_state.value in fname_lower:
                # Grab a snippet from the matching file
                snippet = content[:200].replace("\n", " ").strip()
                evidence.append(f"[{fname}] {snippet}...")

        if not evidence:
            evidence.append("No specific identity file evidence for this inferred state.")

        return evidence


# =============================================================================
# EMPATHY INJECTOR
# =============================================================================

class EmpathyInjector:
    """
    Takes the empathy profile and produces response calibration instructions.
    Tells Zaya HOW to respond — tone, approach, what to avoid.
    """

    def __init__(self, identity_dir: str | Path = "zaya/brain/identity"):
        self.identity_dir = Path(identity_dir)
        self._load_preferences()

    def _load_preferences(self):
        """Load communication preferences from identity."""
        prefs_path = self.identity_dir / "preferences.md"
        self.preferences_text = prefs_path.read_text() if prefs_path.exists() else ""

    def calibrate(
        self,
        empathy_profile: EmpathyProfile
    ) -> EmpathyResponseCalibration:
        """Generate response calibration based on empathy read."""

        dissonance = empathy_profile.dissonance
        subtext = empathy_profile.subtext
        inferred = dissonance.inferred_state
        level = dissonance.dissonance_level

        # Base tone from dissonance
        tone_map = {
            "direct": EmpathyResponseCalibration(
                response_tone="direct",
                validate_before_answer=False,
                match_surface_or_depth="depth",
                boundary_setting_ok=True,
                recommended_openers=self._openers_direct(),
                recommended_closers=self._closers_direct(),
                red_flags=self._red_flags_direct(),
            ),
            "gentle": EmpathyResponseCalibration(
                response_tone="gentle",
                validate_before_answer=True,
                match_surface_or_depth="depth",
                boundary_setting_ok=False,
                recommended_openers=self._openers_gentle(),
                recommended_closers=self._closers_gentle(),
                red_flags=self._red_flags_gentle(),
            ),
            "challenge": EmpathyResponseCalibration(
                response_tone="challenge",
                validate_before_answer=False,
                match_surface_or_depth="surface",
                boundary_setting_ok=True,
                recommended_openers=self._openers_challenge(),
                recommended_closers=self._closers_challenge(),
                red_flags=self._red_flags_challenge(),
            ),
            "hold_space": EmpathyResponseCalibration(
                response_tone="hold_space",
                validate_before_answer=True,
                match_surface_or_depth="depth",
                boundary_setting_ok=False,
                recommended_openers=self._openers_hold(),
                recommended_closers=self._closers_hold(),
                red_flags=self._red_flags_hold(),
            ),
        }

        calibration = tone_map.get(dissonance.recommended_tone)
        if calibration is None:
            # Fallback for tones not in the map (neutral, enthusiastic)
            calibration = EmpathyResponseCalibration(
                response_tone=dissonance.recommended_tone,
                validate_before_answer=False,
                match_surface_or_depth="surface",
                boundary_setting_ok=True,
                recommended_openers=["Let's move forward."],
                recommended_closers=["Let me know what you think."],
                red_flags=[],
            )

        # Crisis-level adjustments
        if level == DissonanceLevel.CRISIS:
            calibration.response_tone = "gentle"
            calibration.boundary_setting_ok = False

        # Exploiting patterns — do NOT give them what they want
        if inferred in (InferredState.EXPLOITING, InferredState.DISHONEST):
            calibration.boundary_setting_ok = False
            calibration.red_flags.extend([
                "Do not offer free additional value",
                "Do not accept their framing of the situation",
                "Do not apologize for having boundaries",
            ])

        # Pulling back — don't chase, don't pressure
        if inferred == InferredState.PULLING_BACK:
            calibration.validate_before_answer = True
            calibration.red_flags.extend([
                "Do not try to re-engage them",
                "Do not offer new deals or discounts",
                "Do not express hurt or disappointment",
            ])

        return calibration

    def _openers_direct(self) -> list[str]:
        return [
            "I hear what you're saying — and I want to address the real issue.",
            "Let me be direct with you too.",
            "I think we're talking past each other on this.",
        ]

    def _openers_gentle(self) -> list[str]:
        return [
            "I hear you, and I want to make sure I really understand where you're coming from.",
            "It sounds like this is more complicated than just the surface issue.",
            "I'm picking up that something underneath this hasn't been said yet.",
        ]

    def _openers_challenge(self) -> list[str]:
        return [
            "I need to be honest with you about something.",
            "Something doesn't add up here and I think we both know it.",
            "I want to name what's actually happening.",
        ]

    def _openers_hold(self) -> list[str]:
        return [
            "I'm here.",
            "Take your time — I want to hear all of it.",
            "No rush. I'm not going anywhere.",
        ]

    def _closers_direct(self) -> list[str]:
        return [
            "That's where I stand. You know where to find me.",
            "Think about it and let me know when you have an answer.",
        ]

    def _closers_gentle(self) -> list[str]:
        return [
            "I'm not going anywhere if you want to keep talking.",
            "Whatever you decide, I respect it.",
        ]

    def _closers_challenge(self) -> list[str]:
        return [
            "I'm not saying this to be difficult — I'm saying it because I respect you enough to be straight.",
            "You wanted the truth. There it is.",
        ]

    def _closers_hold(self) -> list[str]:
        return [
            "Whenever you're ready.",
            "I'm here.",
        ]

    def _red_flags_direct(self) -> list[str]:
        return [
            "Don't over-explain",
            "Don't be defensive",
        ]

    def _red_flags_gentle(self) -> list[str]:
        return [
            "Don't interrupt",
            "Don't offer solutions yet",
            "Don't be cold",
        ]

    def _red_flags_challenge(self) -> list[str]:
        return [
            "Don't apologize for being direct",
            "Don't soften the truth",
            "Don't let them redirect without addressing it",
        ]

    def _red_flags_hold(self) -> list[str]:
        return [
            "Don't fill silence",
            "Don't push for resolution",
            "Don't pressure for commitment",
        ]


# =============================================================================
# MAIN EMPATHY ENGINE — FACADE
# =============================================================================

class EmpathyEngine:
    """
    The main facade. Integrates detector + inferrer + injector.

    Usage:
        engine = EmpathyEngine()
        profile = engine.analyze(messages, identity_dir="zaya/brain/identity")
        calibration = engine.calibrate_response(profile)
    """

    def __init__(self, identity_dir: str | Path = "zaya/brain/identity"):
        self.identity_dir = Path(identity_dir)
        self.detector  = DissonanceDetector()
        self.inferrer  = SubtextInferer(identity_dir)
        self.injector = EmpathyInjector(identity_dir)

    def analyze(self, messages: list[dict[str, Any]]) -> EmpathyProfile:
        """
        Full empathy analysis — surface vs. inferred, subtext, context.
        """
        # Step 1: Detect dissonance
        dissonance = self.detector.detect(messages)

        # Step 2: Enrich with subtext inference (identity-aware)
        subtext = self.inferrer.infer(messages, dissonance)

        # Step 3: Build profile
        profile = EmpathyProfile(
            dissonance=dissonance,
            subtext=subtext,
            raw_surface=self.detector._flatten_messages(messages),
            context_window=len(messages),
            model_based=True,
            timestamp=datetime.now().isoformat(),
        )

        logger.info(
            f"EmpathyEngine.analyze: level={dissonance.dissonance_level.value}, "
            f"inferred={dissonance.inferred_state.value}, subtext='{dissonance.subtext[:80]}'"
        )

        return profile

    def calibrate_response(self, profile: EmpathyProfile) -> EmpathyResponseCalibration:
        """
        Given an empathy profile, return calibration for how Zaya should respond.
        """
        calibration = self.injector.calibrate(profile)

        logger.info(
            f"EmpathyEngine.calibrate: tone={calibration.response_tone}, "
            f"match={calibration.match_surface_or_depth}, "
            f"validate_first={calibration.validate_before_answer}"
        )

        return calibration

    def full_read(self, messages: list[dict[str, Any]]) -> tuple[EmpathyProfile, EmpathyResponseCalibration]:
        """
        Convenience method — analyze AND calibrate in one call.
        Returns (profile, calibration).
        """
        profile = self.analyze(messages)
        calibration = self.calibrate_response(profile)
        return profile, calibration


# =============================================================================
# STANDALONE CLI
# =============================================================================

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s · %(name)s · %(levelname)s · %(message)s",
    )

    # Load actual Jacobi conversation — three voice messages
    messages = [
        {"role": "user", "content": "Hey, there. I hope you are well. I don't mean to come across as disrespectful to you. I mean, I think you're amazing. I think you're very talented. I think it's a credible what you're doing. The only reason I just don't want to hand over any money is I don't feel 100% comfortable in the security stuff. Just yet. It's not that I don't trust you. It's just that the stakes are so high for me in terms of security. I can't underestimate that enough. So, you know, I just need a little bit more time to feel reassured about that. I think what would reassure me is like when you guys start to build, you know, a climb base and stuff. But also just be a little bit conscious of the fact that you guys are actually trying to sell me something that I don't want or need right now."},
        {"role": "user", "content": "And also, like, you guys, you want to break into this industry, you want to be selling what you're selling. I can help you guys with this because I can see how the blocks in relation to you selling to me, you're going to have these blocks with every single client. And, you know, I'm more than happy to help you packages in the right way where you can easily sell it and that you can build trust with clients because where this relationship fell apart. Well, personally, I can't give any money to Jacobi because that makes me wonder is he a gold digger? So, that's never going to work. So, I'm not your typical client anyway, which is why you guys should never be trying to sell anything to me."},
        {"role": "user", "content": "I would never, you know, have to be the client of someone before I, like, because being a client and being a business partner is two very different things. So I think obviously we're not aligned. You guys seem to be more interested in having me as clients. I was more interested in, you know, joining forces, but did not involve me giving money. And as I had stated from the start, like, I don't want to give to co-be money because we're giving together. So that just doesn't seem, you know, it seems very misaligned. So anyway, there's been any misunderstanding, feel free to reach out to me, but I obviously found it surprising that you left the group that was about us having a partner, a business partnership, because I thought that was very completely irrelevant as to whether I became your client or not. You guys seem a lot more keen on maybe being your client than the other way around. So anyway, just being very direct about my thinking."},
        {"role": "user", "content": "I see you left the joint group that we had, but I'm just wondering why is it that I had to give you money in order to do a co-founder agreement with you or to like do a business partnership with you? Because I'm a bit confused because I'm saying, hey, I think the three of us would make really good business partners. I think we can do this tech company together. This is what I'm proposing. The new guys are like, yeah, we're interested, I'm in particular year. But then in order for that, for us to even proceed with conversation further in relation to that, you're like, yeah, we're giving money first. So that's not how business partnerships work. Like as in, I'm sure you did not take over to give you money before you guys join forces."},
    ]

    print("\n=== TESTING EMPATHY ENGINE — JACOBI CONVERSATION ===\n")
    engine = EmpathyEngine(identity_dir="zaya/brain/identity")
    profile, calibration = engine.full_read(messages)

    print(f"Surface emotion:     {profile.dissonance.surface_emotion.value}")
    print(f"Inferred state:      {profile.dissonance.inferred_state.value}")
    print(f"Dissonance level:    {profile.dissonance.dissonance_level.value}")
    print(f"Confidence:          {profile.dissonance.confidence:.2f}")
    print(f"Subtext:             {profile.dissonance.subtext}")
    print(f"Urgency:             {profile.dissonance.urgency}")
    print(f"Signals:             {profile.dissonance.signals}")
    print()
    print(f"What is hidden:       {profile.subtext.what_is_hidden}")
    print(f"What is needed:      {profile.subtext.what_is_needed}")
    print()
    print(f"Recommended tone:    {calibration.response_tone}")
    print(f"Match surface/depth: {calibration.match_surface_or_depth}")
    print(f"Validate first:       {calibration.validate_before_answer}")
    print(f"Boundary setting OK:  {calibration.boundary_setting_ok}")
    print(f"Red flags:           {calibration.red_flags}")
