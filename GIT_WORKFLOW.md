# Git Workflow & Common Issues

## Common Issue: Push Rejected (master -> master)

This happens when the remote repository has changes you don't have locally.

### The Fix:
```bash
git pull --rebase && git push
```

### Why This Happens:
- Someone else (or you from another machine) pushed changes
- Your local branch is behind the remote
- Git prevents you from overwriting remote changes

### Alternative Approaches:

1. **Simple Pull (creates merge commit):**
   ```bash
   git pull
   git push
   ```

2. **Check Status First:**
   ```bash
   git fetch
   git status
   # Shows if you're behind
   ```

3. **Force Push (DANGEROUS - only if you're sure):**
   ```bash
   git push --force
   # WARNING: This overwrites remote changes!
   ```

## Best Practices:

1. **Always pull before starting work:**
   ```bash
   git pull
   ```

2. **Use branches for features:**
   ```bash
   git checkout -b feature/my-feature
   # Work on feature
   git push -u origin feature/my-feature
   ```

3. **Check remote before pushing:**
   ```bash
   git fetch
   git log HEAD..origin/master --oneline
   ```

## Quick Reference:
- `git pull --rebase` - Pull and replay your commits on top
- `git status` - Check if you're behind/ahead
- `git fetch` - Update remote info without merging
- `git log --oneline -5` - See recent commits