First think step by step inside <reasoning> and </reasoning>:

1. List every sentence that names a Kafka release.
2. For each, say whether it states that the bug started there ("introduced"), was seen there
   ("affects"), was absent there ("unaffected"), is fixed there ("fix"), or none of these.
3. Check each candidate against the rules: an exact Kafka release, quoted character for
   character from one field, the quote names the version, a reporter's version is only
   "affects".

Then, after </reasoning>, give only the JSON object, no other text:
<reasoning>
...
</reasoning>
{"evidence": [{"version": "3.6.0", "kind": "affects", "quote": "We run 3.6.0 and see this."}]}
