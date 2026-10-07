# ==============================================================================
# FIRST-PRINCIPLES VERCEL ZERO-REMOTE-BUILD POLICY v2
# Target: https://github.com/koreaelonmusk/*
# ==============================================================================

[OBJECTIVE]
Minimize Vercel build spend by deleting unnecessary remote-build paths without weakening correctness.
Never claim "$0" or "fully enforced" unless the repository and Vercel project settings have been verified.

[ENGINEERING ALGORITHM]
1. Question every requirement.
2. Delete unnecessary parts/processes.
3. Simplify and optimize.
4. Accelerate cycle time.
5. Automate only after the first four steps.

### LAW 1. DISABLE GIT-TRIGGERED VERCEL BUILDS
- Root `vercel.json` MUST set:
  {
    "$schema": "https://openapi.vercel.sh/vercel.json",
    "git": { "deploymentEnabled": false }
  }
- Preserve all existing routes, rewrites, functions, headers, crons, framework and security settings when adding this key.
- If project settings expose an Ignored Build Step, use `exit 0` so every accidental Git deployment is skipped.
- Do NOT use a condition that returns non-zero for production; Vercel interprets non-zero as "continue the build".

### LAW 2. NO UNVERIFIED REMOTE-BUILD CLI PATH
- Repository-owned deployment scripts/CI MUST NOT call bare `vercel`, `vercel deploy`, or `vercel --prod` when those commands would trigger a remote build.
- Preferred compatible flow:
  `vercel pull --yes --environment=production && <required local checks> && vercel build --prod && vercel deploy --prebuilt --prod`
- `--prebuilt` is allowed ONLY after checking compatibility. Vercel System Environment Variables are not automatically available at prebuilt build time, and features such as Skew Protection can require additional configuration.
- If a project depends on unavailable build-time Vercel system variables and no safe explicit binding exists, HOLD deployment rather than silently shipping a broken artifact.
- If the repository has no machine-owned deployment entrypoint, treat the CLI ban as an agent/human policy, not as a claim that the repository technically prevents manual CLI use.

### LAW 3. NEVER BUY COST SAVINGS WITH BROKEN BUILDS
- Do NOT globally set `typescript.ignoreBuildErrors=true` or `eslint.ignoreDuringBuilds=true` merely to shorten builds.
- Type checking, linting, tests and security checks MUST run locally or in required CI before a production artifact is accepted.
- Suppression inside a framework build is permitted only when equivalent independent required checks exist and the exact deployment commit has passed them.
- Do not generate huge static page loops when on-demand, dynamic rendering, ISR, or affected-only builds are correct alternatives.

### LAW 4. PROJECT RESOURCE FLOOR
- When Vercel project settings are writable, prefer:
  - buildMachineType: basic
  - buildMachineSelection: fixed
  - previewDeploymentsDisabled: true when previews are not required
  - Ignored Build Step: `exit 0`
- Do not pause a production project merely to imitate Spend Management.
- Do not mutate budget/concurrency controls unless the exact supported API/setting and account permissions are verified.

### LAW 5. VERIFICATION BEFORE CLAIMS
For CI/CD or deployment changes:
1. inspect the repository's actual deploy entrypoints;
2. verify `vercel.json` preserves existing configuration and disables Git deployments;
3. verify local/CI correctness gates still fail closed;
4. inspect Vercel project settings when accessible;
5. report unsupported or permission-blocked controls explicitly.
