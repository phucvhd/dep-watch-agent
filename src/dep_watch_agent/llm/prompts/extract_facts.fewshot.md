Worked examples. They are made up, not taken from real issues; they show how the rules apply.

Example 1: the reporter's version is "affects", nothing more.
<fix_versions>
3.7.1
</fix_versions>
<summary>
Producer hangs on close
</summary>
<description>
We run 3.6.0 and the producer never returns from close() when the broker is down.
</description>
Answer: {"evidence": [{"version": "3.6.0", "kind": "affects", "quote": "We run 3.6.0 and the producer never returns from close() when the broker is down."}]}
Seen on 3.6.0 says nothing about 3.5.2 or any other release; do not add facts for them.

Example 2: an upgrade sentence gives two facts.
<fix_versions>
3.5.2, 3.6.0
</fix_versions>
<summary>
Consumer group stuck rebalancing
</summary>
<description>
Everything worked on 3.4.1. After upgrading to 3.5.0 the group never finishes rebalancing.
</description>
Answer: {"evidence": [{"version": "3.4.1", "kind": "unaffected", "quote": "Everything worked on 3.4.1."}, {"version": "3.5.0", "kind": "introduced", "quote": "After upgrading to 3.5.0 the group never finishes rebalancing."}]}

Example 3: a regression named in a comment, and versions of other software.
<fix_versions>
2.8.2
</fix_versions>
<summary>
NPE in log cleaner
</summary>
<description>
Broker on Java 11.0.12 with ZooKeeper 3.5.9 throws NullPointerException in LogCleaner.
</description>
<comment>
This is a regression from KAFKA-99999, which first shipped in 2.8.0.
</comment>
Answer: {"evidence": [{"version": "2.8.0", "kind": "introduced", "quote": "This is a regression from KAFKA-99999, which first shipped in 2.8.0."}]}
Java 11.0.12 and ZooKeeper 3.5.9 are not Kafka releases.

Example 4: release lines are not releases; a fix release missing from <fix_versions> is a fact.
<fix_versions>
3.4.0
</fix_versions>
<summary>
Wrong metric name in Connect
</summary>
<description>
The metric is misnamed in all 3.x versions.
</description>
<comment>
Merged to trunk and cherry-picked, so the fix will also be in 3.3.3.
</comment>
Answer: {"evidence": [{"version": "3.3.3", "kind": "fix", "quote": "Merged to trunk and cherry-picked, so the fix will also be in 3.3.3."}]}

Example 5: a bug that started on a release line, and a feature that is not a bug's start.
<fix_versions>
2.9.1
</fix_versions>
<summary>
Rebalance loops when a member restarts
</summary>
<description>
Since 2.7 a restarted member triggers a second rebalance. The new heartbeat API was introduced in 2.5, but that is unrelated.
</description>
Answer: {"evidence": [{"version": "2.7", "kind": "introduced", "quote": "Since 2.7 a restarted member triggers a second rebalance."}]}

Example 6: a downgrade sentence.
<fix_versions>
3.2.1
</fix_versions>
<summary>
Stream thread dies on restore
</summary>
<description>
Stream threads die during state restoration on 3.2.0. After downgrading to 3.1.1 the problem went away.
</description>
Answer: {"evidence": [{"version": "3.2.0", "kind": "affects", "quote": "Stream threads die during state restoration on 3.2.0."}, {"version": "3.1.1", "kind": "unaffected", "quote": "After downgrading to 3.1.1 the problem went away."}]}

Example 7: no version facts.
<fix_versions>
4.0.0
</fix_versions>
<summary>
Typo in the javadoc of KafkaConsumer
</summary>
<description>
"recieve" should be "receive".
</description>
Answer: {"evidence": []}

Now read the issue below. Answer with only the JSON object, no other text.
