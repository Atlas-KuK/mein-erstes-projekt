#!/bin/bash

# PRE-COMMIT SECURITY HOOK
# ========================
# Blockiert Commits mit:
# - Secrets (Passwords, API Keys, Tokens)
# - Große Binär-Dateien
# - Debug-Statements
#
# Installiere: cp .git-hooks-pre-commit.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

set -e

echo "🔍 Running pre-commit security checks..."

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counter for errors
ERRORS=0

# ============================================
# 1. SECRETS SCANNING
# ============================================
echo -e "\n${YELLOW}→${NC} Checking for secrets..."

SECRETS_FOUND=$(git diff --cached 2>/dev/null | grep -iE \
  "(password|api[_-]?key|secret[_-]?key|access[_-]?token|refresh[_-]?token|auth[_-]?token|private[_-]?key|aws[_-]?secret|db[_-]?password|sqlpassword|authorization.*Bearer)" \
  || true)

if [ ! -z "$SECRETS_FOUND" ]; then
    echo -e "${RED}  ✗ FAIL: Secrets found in staged changes!${NC}"
    echo "    Pattern matches:"
    echo "$SECRETS_FOUND" | head -5
    echo ""
    echo "    Don't commit:"
    echo "    - Passwords (use environment variables)"
    echo "    - API Keys (use .env or Secret Manager)"
    echo "    - Tokens (use .env.local, in .gitignore)"
    echo "    - Private Keys (use .env or secure storage)"
    echo ""
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}  ✓ No secrets found${NC}"
fi

# ============================================
# 2. .ENV FILE CHECK
# ============================================
echo -e "\n${YELLOW}→${NC} Checking for .env files..."

ENV_FILES=$(git diff --cached --name-only 2>/dev/null | grep -E "^\\.env" || true)

if [ ! -z "$ENV_FILES" ]; then
    echo -e "${RED}  ✗ FAIL: .env files staged for commit!${NC}"
    echo "    Files: $ENV_FILES"
    echo ""
    echo "    Add to .gitignore:"
    echo "    .env"
    echo "    .env.local"
    echo "    .env.*.local"
    echo ""
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}  ✓ No .env files staged${NC}"
fi

# ============================================
# 3. LARGE FILES
# ============================================
echo -e "\n${YELLOW}→${NC} Checking file sizes..."

LARGE_FILES=$(git diff --cached --name-only --diff-filter=A -z 2>/dev/null | \
  xargs -0 ls -lh 2>/dev/null | awk '$5 ~ /[0-9][0-9][0-9]M|[0-9]G/ {print $9, $5}' || true)

if [ ! -z "$LARGE_FILES" ]; then
    echo -e "${YELLOW}  ⚠ WARNING: Large files detected (>100MB)${NC}"
    echo "    Files:"
    echo "$LARGE_FILES" | sed 's/^/      /'
    echo ""
    echo "    Consider using git-lfs for binary files:"
    echo "    git lfs install"
    echo "    git lfs track '*.zip'"
fi

# ============================================
# 4. DEBUG STATEMENTS
# ============================================
echo -e "\n${YELLOW}→${NC} Checking for debug statements..."

DEBUG_FOUND=$(git diff --cached 2>/dev/null | grep -E \
  "^\+.*console\\.log|^\+.*console\\.debug|^\+.*debugger|^\+.*pdb\\.set_trace|^\+.*import pdb|^\+.*breakpoint()" \
  || true)

if [ ! -z "$DEBUG_FOUND" ]; then
    echo -e "${YELLOW}  ⚠ WARNING: Debug statements found${NC}"
    echo "    Matches:"
    echo "$DEBUG_FOUND" | head -3
    echo ""
    echo "    Remove before committing:"
    echo "    - console.log() / console.debug()"
    echo "    - debugger"
    echo "    - pdb.set_trace() / breakpoint()"
fi

# ============================================
# 5. COMMENT CHECK (optional)
# ============================================
echo -e "\n${YELLOW}→${NC} Checking for security comments..."

SEC_COMMENTS=$(git diff --cached 2>/dev/null | grep -iE \
  "TODO.*password|TODO.*secret|FIXME.*auth|TODO.*validate|FIXME.*sql" \
  || true)

if [ ! -z "$SEC_COMMENTS" ]; then
    echo -e "${YELLOW}  ⚠ WARNING: Security TODOs found${NC}"
    echo "    Fix these before commit:"
    echo "$SEC_COMMENTS" | head -3
fi

# ============================================
# FINAL RESULT
# ============================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}✗ Pre-commit check FAILED ($ERRORS error(s))${NC}"
    echo ""
    echo "Fix the issues above and try again:"
    echo "  git add [fixed-files]"
    echo "  git commit -m '...'"
    echo ""
    echo "Or force commit (NOT RECOMMENDED):"
    echo "  git commit --no-verify"
    exit 1
else
    echo -e "${GREEN}✓ Pre-commit check PASSED${NC}"
    echo "Safe to commit!"
fi

exit 0
