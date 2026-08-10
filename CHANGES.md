# Changes

## 2026-08-10 — Fix British-to-American spelling normalisation in `cleaning()`

### Summary

`util.cleaning()` is used to normalise entity names before they are embedded and
before they are compared for an exact match. Part of that normalisation is
converting British spellings to American ones, so that an ontology written
`colourOfPaper` can match one written `colorOfPaper`. That conversion never ran,
and the function it depended on was returning wrong answers. Both problems are
fixed by replacing the spellchecker with `breame`, a curated British → American
mapping, applied one word at a time.

This changes the text fed to the `syntactic` embedding, so `ontology_matching.csv`
must be regenerated before results are compared against earlier runs.

### Background

There were two separate defects, and the first was hiding the second.

**1. The conversion was applied to a whole phrase.**

`cleaning()` splits a camelCase name into words before normalising, so by the
time the conversion ran it was holding a phrase:

```python
cleaned_name = cleaned_name.lower()                          # "programme committee"
cleaned_name = change_british_to_american(cleaned_name)      # whole phrase
```

`change_british_to_american()` asks a dictionary whether the input is a British
word. Dictionaries only ever contain single words, so the answer for a phrase was
always "no" and the input was returned untouched. Every multi-word entity name —
which is most of them, after camelCase splitting — passed through unconverted.
Single-word names were converted, so the behaviour was inconsistent rather than
uniformly absent.

**2. The conversion itself guessed.**

The function returned the spellchecker's first suggestion:

```python
suggestions = us_dict.suggest(word)
return suggestions[0] if suggestions else word
```

`suggest()` is a "did you mean?" feature. It answers *"this is not a US word —
which US word is spelled most similarly?"*, ranking candidates by how few
character edits separate them. It has no concept of British versus American
English. For `programme` it returns nine candidates, and `program` is not first:

| rank | suggestion | edits from `programme` |
|---|---|---|
| 0 | `programmer` | 1 (add `r`) — **this is what the code took** |
| 1 | `programmed` | 1 |
| 2 | `program` | 2 (delete `m`, `e`) — the correct answer |

One mistake is more likely than two, so `programmer` outranks `program`. The
function was answering a different question from the one being asked. It happened
to be right for `colour → color`, where the nearest lookalike is also the correct
American spelling, but that is a coincidence and it held for only about half the
vocabulary.

Because of defect 1, defect 2 was almost never reached. Fixing the call site
alone would therefore have made matters worse, turning a silent no-op into active
corruption of entity names.

### Measured impact

Applying the old function per word across all entity names and `rdfs:label`
values in `data/` (43,141 names, 85,740 tokens) produced 157 rewrites, of which
**86 (55%) were wrong**. The most frequent:

| occurrences | rewrite | problem |
|---|---|---|
| 18× | `analyse` → `analyses` | verb turned into a plural noun |
| 16× | `axe` → `ace` | unrelated word (archaeology track) |
| 16× | `grey` → `Grey` | capitalised, after `cleaning()` had lowercased |
| 14× | `programme` → `programmer` | different concept |
| 5× | `matt` → `Matt` | matte finish turned into a proper noun |
| 5× | `programmes` → `programmers` | |
| 2× | `cheque` → `cheek` | |
| 1× | `armour` → `Armour` | capitalised, and never normalised to `armor` |
| 1× | `flyer` → `fayer` | not a word |

The capitalised results are a second-order problem: `cleaning()` lowercases
before converting, so its output was no longer guaranteed lowercase.

### The fix

`breame` is a curated table of 1,730 British → American pairs. It is a lookup,
not a ranked guess, so it cannot return a lookalike. A word it does not know is
returned unchanged rather than replaced.

```python
def change_british_to_american(word):
    return get_american_spelling(word)


def change_phrase_british_to_american(phrase):
    # breame looks up one word at a time, so a phrase has to be split first
    return " ".join(get_american_spelling(word) for word in phrase.split())
```

The per-word split is still required: `breame` is a word-level lookup and returns
a phrase unchanged.

Over the same corpus this produces **162 rewrites, all correct**, and it also
catches conversions the old code missed entirely:

```
12×  disc            -> disk           3×  archaeological -> archeological
 2×  tonne           -> ton            2×  archaeology    -> archeology
```

Verification: `cleaning()` ran over all 43,141 entity names with **zero
exceptions**. The previous code raised `ValueError: can't check spelling of empty
string` on an empty name; that path is now safe. The new code is roughly 700×
faster (3.6 s → 0.005 s per 2,100 names), because a dictionary lookup replaces a
spellchecker query per token.

### Behavioural notes

`breame` normalises some words the old code left alone: `axe → ax`,
`grey → gray`, `disc → disk`, `archaeology → archeology`. These are legitimate
American variants. For matching this is an improvement rather than a risk, since
both the source and target ontology pass through the same function — an ontology
written `archaeology` now normalises to the same string as one written
`archeology`, which previously would not have matched.

### Files changed

| file | change |
|---|---|
| `util.py` | dropped the `enchant` and `hunspell` imports and the module-level dictionary globals; replaced `change_british_to_american()`; added `change_phrase_british_to_american()`; `cleaning()` now calls the per-word helper |
| `requirements.txt` | `pyenchant==3.2.2` → `breame==0.1.2`; removed `hunspell==0.5.5` |

`breame` has no dependencies, so both spellchecker libraries could be removed.
That also removes the hardcoded dictionary paths

```python
uk_dict = hunspell.HunSpell('/usr/share/hunspell/en_GB.dic', ...)
```

which made `util.py` fail at import on any machine without those exact files —
and `util.py` is imported by every module in the pipeline.

`test_function/test_hunspell.py` still imports `hunspell` and is left as-is; it
is a standalone scratch script and will no longer run on a fresh install.

The same change was applied to the `ontology-versioning` repository, which
carries an identical copy of `util.cleaning()`.

### Migration

Regenerate `ontology_matching.csv` and re-embed before comparing any results
with earlier runs. Numbers produced before and after this change are not
comparable, because the text passed to the `syntactic` embedding has changed.

```
pip install -r requirements.txt
python run_config.py
```

### Not included

This release fixes only the spelling normalisation. The following are known and
untouched:

- The `alignment` environment variable set by the `run_series_*.py` drivers
  overrides only `alignment` in `run_config.py`, not `context`, `o1_is_code` or
  `o2_is_code`. The track block must still be uncommented by hand to match the
  driver being run, or the run silently uses another track's settings. The
  `ontology-versioning` repository already carries a fix for this.
- `run_config.py` continues to the next script after a stage fails, so a later
  stage can run against the previous alignment's database.
- Tool selection in the agents is delegated to the LLM with no constraint or
  error handling, so an unexpected tool name raises `KeyError` and aborts the run.
