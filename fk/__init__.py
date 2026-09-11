"""fk: a deliberate, credit-aware client and data layer for the Form King Modellers API.

Design rules, in priority order:
1. Every API call is recorded in the credit ledger before its response is used.
2. Nothing about the API (paths, parameter names, credit costs, auth header) is
   hardcoded. It is read from the OpenAPI spec at load time, and anything the
   spec does not say must be supplied explicitly in credits.yaml.
3. A response field we have not confirmed against the spec is never guessed
   silently: fk.fields raises FieldUnmapped naming the keys that were present.
"""
