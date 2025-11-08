# File System Reorganization - Migration Notes

## What Changed?

The project has been reorganized from a flat structure to a modular, organized structure for better maintainability.

### Old Structure (Flat)

```
acs_llm_agent/
├── mvp.py
├── intent.py
├── resolver.py
├── mvp_multiagent.py
├── acs_tools.py
├── geography.py
├── agents/ (...)
├── test_*.py (scattered)
├── *.md (documentation scattered)
└── various scripts
```

### New Structure (Organized)

```
acs_llm_agent/
├── main.py                    # Entry point
├── src/                       # All source code
│   ├── single_agent/          # Single-agent mode
│   ├── agents/                # Multi-agent mode
│   ├── acs_tools.py          # Shared utilities
│   ├── geography.py          # Shared data
│   └── mvp_multiagent.py     # Multi-agent CLI
├── tests/                     # All tests
├── scripts/                   # Utility scripts
├── docs/                      # All documentation
└── cache/                     # Data cache

```

## Breaking Changes

### For Users

✅ **NO BREAKING CHANGES** - All functionality works the same:

```bash
# Still works exactly the same
python main.py
python main.py --mode multi
python main.py --compare
```

### For Developers/Imports

#### If you imported modules directly:

**OLD**:

```python
from mvp import run_query
from intent import extract_intent
from resolver import resolve_measure
```

**NEW**:

```python
import sys
sys.path.insert(0, 'src/single_agent')
from mvp import run_query
from intent import extract_intent
from resolver import resolve_measure
```

**Or use main.py** (recommended):

```bash
python main.py --mode single  # Uses single-agent
python main.py --mode multi   # Uses multi-agent
```

## Benefits of New Structure

1. **Clearer Organization**

   - Single-agent code in `src/single_agent/`
   - Multi-agent code in `src/agents/`
   - Tests in `tests/`
   - Docs in `docs/`
   - Scripts in `scripts/`

2. **Better Modularity**

   - Easier to find files
   - Logical grouping
   - Cleaner root directory

3. **Easier Maintenance**

   - All tests together
   - All documentation together
   - All utilities together

4. **Professional Structure**
   - Follows Python best practices
   - Easier for new contributors
   - Better for packaging

## File Mappings

### Core Files

| Old Location        | New Location                   |
| ------------------- | ------------------------------ |
| `mvp.py`            | `src/single_agent/mvp.py`      |
| `intent.py`         | `src/single_agent/intent.py`   |
| `resolver.py`       | `src/single_agent/resolver.py` |
| `mvp_multiagent.py` | `src/mvp_multiagent.py`        |
| `acs_tools.py`      | `src/acs_tools.py`             |
| `geography.py`      | `src/geography.py`             |
| `agents/`           | `src/agents/`                  |

### Tests

| Old Location       | New Location      |
| ------------------ | ----------------- |
| `test_*.py` (root) | `tests/test_*.py` |

### Documentation

| Old Location            | New Location                   |
| ----------------------- | ------------------------------ |
| `README.md`             | `docs/README.md` (full docs)   |
|                         | `README.md` (project overview) |
| `USAGE_GUIDE.md`        | `docs/USAGE_GUIDE.md`          |
| `MULTIAGENT_SUMMARY.md` | `docs/MULTIAGENT_SUMMARY.md`   |
| Other `*.md`            | `docs/*.md`                    |

### Scripts

| Old Location      | New Location              |
| ----------------- | ------------------------- |
| `check_ollama.py` | `scripts/check_ollama.py` |
| `debug_intent.py` | `scripts/debug_intent.py` |
| `verify_*.py`     | `scripts/verify_*.py`     |

## Testing After Migration

```bash
# Verify structure
python scripts/show_structure.py

# Test single-agent mode
python main.py
> What are the top 5 richest tracts in Orleans Parish?

# Test multi-agent mode
python main.py --mode multi
> Show me high-poverty areas in Caddo Parish

# Run tests (update paths if you have custom test runners)
cd tests
python -m pytest
```

## Rollback (if needed)

If you need to revert to the flat structure:

```powershell
# Move files back to root
Move-Item -Path "src\single_agent\*" -Destination "."
Move-Item -Path "src\*" -Destination "."
Move-Item -Path "tests\*" -Destination "."
Move-Item -Path "docs\*" -Destination "."
Move-Item -Path "scripts\*" -Destination "."

# Remove new directories
Remove-Item -Recurse src, tests, docs, scripts
```

## Questions?

See:

- `STRUCTURE.md` - Detailed structure documentation
- `docs/README.md` - Full project documentation
- `docs/USAGE_GUIDE.md` - Usage examples
