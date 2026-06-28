# German Learning System

A structured German learning system for adult learners who want to move from scattered vocabulary and grammar rules into confident, topic-based communication.

## Philosophy

Traditional language courses ask:

"What chapter are you on?"

This system asks:

"What situation are you trying to navigate?"

Learners build a foundation of communication functions and language patterns, then apply them across real-life situations.

The system can be used as both:

* a structured learning pathway
* a practical reference guide

The goal is practical communication, confidence, and real-world usability.

## Project Structure

- `VISION.md` defines the mission, learner promise, philosophy, and long-term direction.
- `CURRICULUM.md` outlines the learning architecture across CEFR levels and real-life topics.
- `STYLE_GUIDE.md` keeps lessons clear, practical, encouraging, and consistent.
- `design-system.html` provides the visual design system for learner-facing pages and components.
- `index.html` contains the current bundled learner-facing prototype.
- `situation-library.html` provides a clean browsable index of available situation files grouped by domain.
- `levels/` organizes learning paths from A1 through C1.
- `topics/` organizes practical communication areas such as travel, health, shopping, housing, and work.
- `templates/` provides reusable formats for lessons, vocabulary, speaking, writing, and review.
- `notes/` stores learner stories, ideas, and future product thinking.

## Design System

The project includes `design-system.html` as the visual reference for future learner-facing pages.

Use it to keep interface work consistent across:

* typography
* color
* gender-color vocabulary treatment
* CEFR level badges
* situation cards
* dialogue blocks
* writing examples
* confidence milestones
* real-world challenge callouts

## Updating The Situation Library

The situation library page is generated from the Markdown files in `situations/`.

After adding or editing a situation file, run this from the repository root:

```bash
python3 scripts/generate_situation_library.py
```

This refreshes `German-Learning-System/situation-library.html` and creates full browser-readable pages in `German-Learning-System/situation-pages/`.

## Updating The Reference Pages

The foundation and architecture pages are generated from the Markdown reference files.

After editing a reference file, run this from the repository root:

```bash
python3 scripts/generate_reference_pages.py
```

This refreshes the browser-readable versions of `FOUNDATION_REFERENCE.md`, `GRAMMAR_MAP.md`, `SENTENCE_ARCHITECTURE_MAP.md`, `COMMUNICATION_FUNCTIONS.md`, `LEARNING_MODEL.md`, and `LESSON_BLUEPRINT.md`.

## Goal

Help adult learners build usable German from the start by connecting words, grammar, situations, and confidence into one coherent learning experience.
