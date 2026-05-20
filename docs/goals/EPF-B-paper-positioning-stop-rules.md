# EPF-B paper-positioning stop rules

Stop and report EPF_PAPER_POSITIONING_BLOCKED if:

* paper wording would imply paper evidence
* paper wording would imply measurement_validation
* paper wording would imply calibrated_proxy_supported or vinfo_proxy_supported
* paper wording would imply teacher-forced NLL support
* paper wording would imply metric bridge support
* Route 5 or Route 8 would need to be unlocked
* WS5 measurement validation would require human/external gold labels not present
* code or experimental artifacts would need to be changed
* generated WS6 nested claim_ledger.json files would need to be staged
* unrelated leftovers would need to be staged
* tests require out-of-scope edits
* secrets or raw API responses would be introduced

Do not weaken claim boundaries or convert candidate operational evidence into paper evidence to avoid a blocked state.
