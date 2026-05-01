# AgentGuard QA Checklist

## Smoke

- [ ] Homepage loads without console errors.
- [ ] Header links work: Demo, Simulator, Alerts, Logs, GitHub.
- [ ] `/demo` loads.
- [ ] `/simulator` loads.
- [ ] `/approvals` loads.
- [ ] `/logs` loads.
- [ ] `/alerts` loads.

## Configuration

- [ ] Create an agent from `/agents`.
- [ ] Create an action from `/actions`.
- [ ] Create an action policy from `/action-policies`.
- [ ] Create an alert webhook from `/alerts`.
- [ ] Create a secret from `/secrets`; value is never displayed.

## Demo Flow

- [ ] Open `/demo`.
- [ ] Enter a customer email and context.
- [ ] Generate email.
- [ ] Simulation shows decision, risk, and reason.
- [ ] Send to AgentGuard creates a pending approval for external recipients.
- [ ] Edit the approval payload.
- [ ] Approve the action.
- [ ] Mock Gmail draft result appears.
- [ ] Logs show original input, edited input, status, and result.
- [ ] Configured webhook receives alert events.

## Policy Simulator

- [ ] External email simulation returns `approval_required`.
- [ ] Internal email simulation returns `allow` when default allow policy exists.
- [ ] Block policy simulation returns `block`.
- [ ] Simulation does not create approvals.
- [ ] Simulation does not create audit logs.

## Approvals

- [ ] Pending approvals are listed.
- [ ] Reviewer/admin can edit approval input.
- [ ] Approve executes edited input, not original input.
- [ ] Reject changes status to rejected.
- [ ] Viewer role cannot edit, approve, or reject when Clerk auth is enabled.

## Logs

- [ ] Logs are workspace scoped.
- [ ] Sensitive values are redacted.
- [ ] `policy_match`, `risk_level`, and execution result display correctly.

## Browser Console

- [ ] No hydration mismatch errors.
- [ ] No uncaught runtime exceptions.
- [ ] No failed backend requests during the happy path.
