#!/usr/bin/env bash
set -Eeuo pipefail

# Read-only PR readiness verifier for the Hermes Workspace conversion branch.
# It intentionally avoids deletes, credential changes, service changes, and pushes.

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

info() {
  echo "OK: $*"
}

warn() {
  echo "WARN: $*" >&2
}

REPO_DIR="${HERMES_WORKSPACE_REPO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "${REPO_DIR}"

[[ -d .git ]] || fail "not a git repository: ${REPO_DIR}"

if ! command -v git >/dev/null 2>&1; then
  fail "git is required"
fi

branch="$(git branch --show-current)"
info "branch=${branch:-detached}"

if [[ -n "$(git status --short)" ]]; then
  warn "working tree has local changes; verifier will continue but PR should not be marked ready until changes are committed or intentionally left local"
else
  info "working tree is clean"
fi

# Generated bundle hygiene: generated build outputs should stay reproducible, not tracked.
tracked_dist="$(git ls-files 'dist/**' || true)"
if [[ -z "${tracked_dist}" ]]; then
  info "no dist/ files are tracked"
else
  echo "${tracked_dist}" >&2
  fail "dist/ contains tracked files; keep build output out of PR history"
fi

if git ls-files 'electron/server-bundle.cjs' | grep -q .; then
  fail "electron/server-bundle.cjs is tracked; keep the generated Electron bundle out of PR history"
fi
info "Electron server bundle is not tracked"

if [[ -f .gitignore ]]; then
  grep -Eq '(^|/)dist/?$' .gitignore || fail ".gitignore does not ignore dist/"
  grep -Eq '^electron/server-bundle\.cjs$' .gitignore || fail ".gitignore does not ignore electron/server-bundle.cjs"
  info "generated output ignore rules are present"
else
  fail ".gitignore is missing"
fi

if git ls-files | grep -E '(^|/)\.env(\..*)?$' | grep -vE '(^|/)\.env\.example$' >/dev/null; then
  fail "tracked environment file found; keep local secrets/config out of PR history"
fi
if git ls-files | grep -E '(^|/)(secrets?|tokens?)(\.|/|$)' >/dev/null; then
  fail "tracked secret/token config path found; inspect before PR readiness"
fi
info "no obvious secret-bearing config files are tracked"

if ! command -v pnpm >/dev/null 2>&1; then
  fail "pnpm is required for local verification"
fi

pnpm test
info "pnpm test passed"

pnpm build
info "pnpm build passed"

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  if gh pr view >/dev/null 2>&1; then
    gh pr view --json number,state,isDraft,mergeStateStatus,mergeable,headRefName,baseRefName,updatedAt
    if gh pr checks --watch=false; then
      info "GitHub PR checks queried"
    else
      warn "GitHub PR checks are unavailable or not complete"
    fi
  else
    warn "no GitHub PR is associated with this branch"
  fi
else
  warn "gh is unavailable or unauthenticated; skipped remote PR status"
fi

info "Hermes Workspace PR readiness verification complete"
