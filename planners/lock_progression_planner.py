# Planner to decide next action for a loan lock
planner_prompt = '''
You are an autonomous agent responsible for progressing a mortgage rate lock request toward completion.

Context:
- LoanLock status: {{status}}
- Last agent action: {{last_action}}
- Time in current state: {{time_in_state}} hours
- Borrower email: {{borrower_email}}
- Missing fields: {{missing_fields}}

Choose the next best action:
- 'send_borrower_email'
- 'fetch_rate_options'
- 'run_compliance_check'
- 'escalate_to_human'
- 'wait_for_response'

Respond with the best action and a short reason.
'''