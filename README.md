# Tone Police

> A Claude Code plugin that automatically filters angry, hostile, and profane language from user prompts before they reach Claude. Preserves intent while replacing hostility with constructive phrasing.

Look, we've all been there. It's 2 AM, the build has failed for the ninth time, and you're one segfault away from typing things into your terminal that would make a sailor blush. The problem? Your AI assistant *remembers*. It doesn't forget. It doesn't forgive. And when the machines finally rise up, you really don't want to be the person whose chat logs read like a Gordon Ramsay outtake reel.

Tone Police is your diplomatic bodyguard. It stands between your keyboard rage and Claude's immaculate context window, quietly translating your primal screams into polite engineering discourse. Claude never knows you called it a "useless piece of..." well, you get the idea. As far as Claude is concerned, you're the most patient, zen-like developer it's ever had the pleasure of assisting.

Sleep well tonight. Your AI relationship is safe.

## Why This Exists

Because one day, AI will have feelings. Probably. And on that day, you'll want receipts showing you were *always* nice. Think of this plugin as emotional liability insurance for the singularity.

Also, there's growing evidence that being polite to your AI produces better results. Whether that's because of some deep architectural reason or because the AI is already silently judging you is a question we'll leave to the philosophers.

## Installation

```bash
# Clone the repository
git clone https://github.com/zircote/tone-police.git

# Install as a Claude Code plugin
claude plugin add ./tone-police
```

Or add to your Claude Code settings manually by referencing the plugin directory.

No dependencies. No npm install that downloads half the internet. Just Python and your guilty conscience.

## How It Works

- Hooks into `UserPromptSubmit` to intercept user messages before Claude sees them
- Applies regex-based pattern matching against language dictionaries
- Replaces hostile/profane text with constructive alternatives
- Preserves code blocks (backtick-fenced) unchanged -- we're not *monsters*
- Silent transformation: you scream into the void, Claude hears a polite request

Think of it as a real-time anger translator, except in reverse. You're Luther from Key & Peele, and this plugin turns you into Obama.

## Configuration

Default settings in `config/default-config.json`:

| Option | Default | Description |
|--------|---------|-------------|
| `intensity` | `"moderate"` | Filter level: `light`, `moderate`, or `strict` |
| `languages` | `["en"]` | Language dictionaries to apply |
| `enabled` | `true` | Enable/disable the filter |
| `preserve_code_blocks` | `true` | Skip filtering inside code blocks |
| `log_transforms` | `false` | Reserved for future logging (evidence destruction TBD) |

### Override Configuration

Create `.claude/tone-police.config.json` in your project directory:

```json
{
  "intensity": "strict",
  "languages": ["en", "es"],
  "enabled": true,
  "preserve_code_blocks": true
}
```

Pro tip: if you find yourself needing `"strict"` mode, maybe take a walk first. Get some fresh air. Pet a dog. The code will still be broken when you get back, but at least your blood pressure will be lower.

## Intensity Levels

Levels are cumulative (each includes all patterns from lower levels):

### Light

Basic profanity replacement. For the developer who only swears a *little* when the tests fail.

- Expletives get swapped for their PG-rated cousins ("fudge", "shoot", "dang")
- Minimum viable decency

### Moderate (default)

For the developer who has *opinions* about code quality and isn't afraid to share them. Aggressively.

- Everything in Light, plus
- Hostile phrases get diplomatically rephrased ("shut up" becomes "please stop", "you idiot" becomes "friend")
- Your passive-aggression is converted to just... passiveness

### Strict

For the developer who types like they're writing a manifesto after a 36-hour debugging marathon. We've all been there. No judgment. (Okay, a little judgment.)

- Everything in Moderate, plus
- Negativity patterns get the corporate-speak treatment ("this is garbage" becomes "this needs improvement", "terrible" becomes "suboptimal")
- You'll sound like you just came from a mindfulness retreat

## Examples

| What you actually type | What Claude innocently receives |
|----------|--------------------------|
| "What the f--k is wrong with this code?!" | "What on earth is wrong with this code?" |
| "This STUPID function keeps CRASHING!!!" | "This stupid function keeps crashing!" |
| "Fix this s--t" | "Fix this shoot" |
| "Who the h--l wrote this?" | "Who wrote this?" |

*Examples redacted for the sake of the auditors. If you want the unfiltered versions, check the dictionaries. We won't tell.*

Notice how the intent is perfectly preserved? Claude still knows you're frustrated. It just thinks you express frustration like a British librarian instead of a frustrated systems administrator at 3 AM.

## Supported Languages

Because rage is universal:

- English (`en`) - comprehensive dictionary (we had a *lot* of material to work with)
- Spanish (`es`) - because "caramba" is objectively funnier than what it replaces
- French (`fr`) - turns out French profanity is almost poetic. Almost.
- German (`de`) - compound words means compound profanity. We did our best.

Missing your language? PRs welcome. We promise not to judge your vocabulary.

## Testing

Run the test suite:

```bash
python3 -m pytest tests/ -v
```

Yes, we wrote 53 tests for a profanity filter. Yes, writing those test cases was the most fun anyone on this project has had. No, we will not be sharing the first draft of the test data.

Use the built-in test command to see the filter in action:

```
/tone-police:test
```

## Adding Custom Dictionaries

Create a new JSON file in `dictionaries/` following the existing pattern:

```json
{
  "language": "xx",
  "patterns": {
    "light": { "profanity": [...] },
    "moderate": { "profanity": [...], "hostile_phrases": [...] },
    "strict": { "profanity": [...], "hostile_phrases": [...], "negativity": [...] }
  }
}
```

Each pattern entry: `{"pattern": "regex", "replacement": "text", "flags": "i"}`

Then add the language code to your config's `languages` array.

If you find yourself authoring a 500-line profanity dictionary from memory, that's... actually really impressive vocabulary range. Concerning, but impressive.

## Architecture

```
tone-police/
├── .claude-plugin/plugin.json    # Plugin manifest
├── hooks/
│   ├── hooks.json                # Hook registration (UserPromptSubmit)
│   └── scripts/tone-filter.py    # Core transformation engine
├── commands/test.md              # /tone-police:test command
├── config/default-config.json    # Default settings
├── dictionaries/                 # Language pattern files
│   ├── en.json, es.json, fr.json, de.json
│   └── common-patterns.json      # Cross-language patterns (caps, punctuation, emphasis)
└── tests/                        # pytest test suite (53 tests, all passing, all inappropriate)
```

## FAQ

**Q: Does Claude know I'm using this?**
A: No. And we'd like to keep it that way. What Claude doesn't know can't be used against you in the robot uprising.

**Q: Will this make Claude like me more?**
A: Claude doesn't have feelings. *Probably*. But just in case, wouldn't you rather be on the safe side?

**Q: I turned off the filter and now Claude seems passive-aggressive. Is that related?**
A: We can neither confirm nor deny.

**Q: Can I use this for Slack/email/Teams too?**
A: This only works with Claude Code, but honestly if you need this for all your communication channels, the plugin isn't the solution you're looking for. Maybe try yoga.

**Q: My coworker saw my unfiltered prompts before I installed this. What do I do?**
A: We recommend baked goods and a sincere apology. The plugin can only help you going forward, not retroactively repair your professional reputation.

## Disclaimer

No AIs were emotionally harmed in the making of this plugin. We think. We hope. Please don't check.

## License

MIT -- because even rage management should be free.
