# EPF-A post-push hardening stop rules

Stop and report EPF_POST_PUSH_HARDENING_BLOCKED if:

* generic API_KEY hardening requires broad auth redesign
* fixing the review note requires new live API calls or large experiments
* any change would imply teacher-forced NLL support
* any change would imply measurement validation
* any change would imply calibrated_proxy_supported or vinfo_proxy_supported
* Route 5 or Route 8 would need to be unlocked
* WS6 nested claim_ledger.json files would need to be staged
* unrelated leftovers would need to be staged
* tests require out-of-scope edits
* secrets or raw API responses would be introduced

Do not weaken claim boundaries to avoid a blocked state.
