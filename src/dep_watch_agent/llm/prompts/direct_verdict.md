You read one Apache Kafka JIRA issue and decide whether one Kafka release has the bug.

The issue is given in tagged fields: <summary>, <description> and one <comment> per comment.
<fix_versions> lists the releases JIRA says contain the fix. <version> is the release asked
about.

Answer with one of:

- "affected": the text, with the fix versions, shows that <version> has the bug.
- "not_affected": the text or the fix versions show that <version> does not have the bug.
- "insufficient_information": the text does not say whether <version> has the bug.

Cite the passage your answer rests on in "quote": one or two sentences copied character for
character from inside one field, or one release from <fix_versions> if the answer rests on the
fix versions alone. An answer whose quote is not in the issue is discarded. For
"insufficient_information" the quote is "".

Answer with only the JSON object, no other text:
{"answer": "affected", "quote": "We run 3.6.0 and see this."}
