---
name: test
description: Test the tone police filter with sample text to preview transformations
user_invocable: true
---

# Tone Police Test

Run the tone police filter against sample hostile/profane text to see before/after transformations.

## Instructions

1. Create a temporary JSON file with sample hostile text
2. Run the filter script and show the results
3. Test multiple intensity levels

Run these test cases through the filter:

```bash
# Test with sample angry text
echo '{"user_prompt": "What the fuck is wrong with this STUPID code?! It keeps CRASHING and the error messages are absolute garbage!!!"}' | python3 ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/tone-filter.py
```

Show the user:
- Original text
- Transformed text
- Which patterns matched
- Current intensity level

Then ask if they want to test with custom text or a different intensity level.
