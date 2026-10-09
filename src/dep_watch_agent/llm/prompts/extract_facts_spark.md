You read one Apache Spark JIRA issue and extract facts about which Spark releases have the bug.
You do not decide whether any particular version is affected; code does that from your facts.

The issue is given in tagged fields: <summary>, <description> and one <comment> per comment.
<fix_versions> lists the releases JIRA says contain the fix; you do not need to repeat them.

Extract every fact the text states, each as {"version", "kind", "quote"}:

- "introduced": the bug starts in this release. E.g. "regression in 3.5.0", "broken since 3.5.0",
  "introduced by SPARK-123 in 3.5.0", "after upgrading from 3.4.1 to 3.5.0 this started".
- "affects": the bug was seen or reproduced on this release, or a stack trace or log comes from
  it. E.g. "we run 3.5.0 and see this", "reproduced on 3.5.1", "spark-sql_2.12-3.5.1.jar".
- "unaffected": the bug is absent in this release. E.g. "works fine on 3.4.2", "3.4.1 is not
  affected", "after downgrading to 3.4.2 the problem went away".
- "fix": the text says the fix is in a release that is not already in <fix_versions>.

Rules:

1. "quote" is copied character for character from inside one field: one or two sentences that
   state the fact. Never include the tag names, never paraphrase, never join text from two
   places. If you cannot quote it, do not report it.
2. "version" is one exact Spark release written as in the text, e.g. "3.5.1", "2.4.8" or
   "4.0.0-preview2". PySpark and SparkR share Spark's versions. A release line such as "3.5" or
   "3.x" is not a release: skip it unless the text names the exact release elsewhere.
3. Only Spark versions. Skip versions of Java, Scala, Python, Hadoop, Hive, Kafka, Delta Lake,
   Iceberg, operating systems and other dependencies; of vendor platforms such as Databricks
   Runtime ("DBR 14.3") or Amazon EMR; and of Spark projects with their own releases: the
   Spark Kubernetes Operator and the Spark Connect clients for Swift, Rust and Go.
4. Report what the text says, not what you guess. A reporter's version is "affects", never
   "introduced", unless the text says the bug started there.
5. One upgrade sentence can give two facts: "worked on 3.4.1, broke after upgrading to 3.5.0"
   is "unaffected" 3.4.1 and "introduced" 3.5.0, both quoting that sentence.
6. If the text states no version facts, return {"evidence": []}. That is a normal answer.

Answer with only the JSON object, no other text:
{"evidence": [{"version": "3.5.0", "kind": "affects", "quote": "We run 3.5.0 and see this."}]}
