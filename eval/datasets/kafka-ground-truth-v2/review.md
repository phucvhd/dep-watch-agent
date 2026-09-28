# kafka-ground-truth-v2: labeling review

The fix versions are GIVEN (the system sees them). For each case, decide whether
the text below plus the given fix versions say enough to conclude the metadata
answer for that config version: for `affected`, that the bug exists at or before
the config and isn't fixed by it; for `not_affected` (`before_affected`), that the
bug did not exist yet at the config ("introduced in", "works on"). "Seen on
3.6.0" alone says nothing about 3.5.2.

Record `yes` or `no` in the `answerable_from_text` column of labels.csv, with a short
note when it's borderline.

## KAFKA-723: Scala's default case class toString() is very inefficient

https://issues.apache.org/jira/browse/KAFKA-723

Given fix versions: 0.8.1
JIRA affects (masked from the system): 0.8.0

- `KAFKA-723@0.8.0`: config 0.8.0, metadata answer **affected** (listed_affected)
- `KAFKA-723@0.7.2`: config 0.7.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
Request logging is in the critical path of processing requests and we use Scala's default toString() API to log the requests. We should override the toString() in these case classes and log only what is useful.
~~~~

### Comments (2)

1.

~~~~
[~nehanarkhede] I think we did this, no?
~~~~

2.

~~~~
As [~jkreps] pointed out, this is already fixed.
~~~~

---

## KAFKA-1562: kafka-topics.sh alter add partitions resets cleanup.policy

https://issues.apache.org/jira/browse/KAFKA-1562

Given fix versions: 0.8.2.0
JIRA affects (masked from the system): 0.8.1.1

- `KAFKA-1562@0.8.1.1`: config 0.8.1.1, metadata answer **affected** (listed_affected)
- `KAFKA-1562@0.8.1`: config 0.8.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
When partitions are added to an already existing topic the cleanup.policy=compact is not retained.

{code}
./kafka-topics.sh --zookeeper localhost --create --partitions 1 --replication-factor 1 --topic KTEST --config cleanup.policy=compact

./kafka-topics.sh --zookeeper localhost --describe --topic KTEST
Topic:KTEST	PartitionCount:1	ReplicationFactor:1	Configs:cleanup.policy=compact
	Topic: KTEST	Partition: 0	Leader: 0	Replicas: 0	Isr: 0

./kafka-topics.sh --zookeeper localhost --alter --partitions 3 --topic KTEST --config cleanup.policy=compact

 ./kafka-topics.sh --zookeeper localhost --describe --topic KTEST
Topic:KTEST	PartitionCount:3	ReplicationFactor:1	Configs:
	Topic: KTEST	Partition: 0	Leader: 0	Replicas: 0	Isr: 0
	Topic: KTEST	Partition: 1	Leader: 0	Replicas: 0	Isr: 0
	Topic: KTEST	Partition: 2	Leader: 0	Replicas: 0	Isr: 0
{code}
~~~~

### Comments (6)

1.

~~~~
If it's alright, I was planning on working on this a bit. I think I know where the issue is, and I'm in the process of fixing it at the moment.
~~~~

2.

~~~~
Created reviewboard https://reviews.apache.org/r/24113/diff/
 against branch origin/trunk
~~~~

3.

~~~~
Updated reviewboard https://reviews.apache.org/r/24113/diff/
 against branch origin/trunk
~~~~

4.

~~~~
Updated reviewboard https://reviews.apache.org/r/24113/diff/
 against branch origin/trunk
~~~~

5.

~~~~
Updated reviewboard https://reviews.apache.org/r/24113/diff/
 against branch origin/trunk
~~~~

6.

~~~~
Thanks for the patch. +1 and committed to trunk.
~~~~

---

## KAFKA-2024: Cleaner can generate unindexable log segments

https://issues.apache.org/jira/browse/KAFKA-2024

Given fix versions: 0.9.0.0
JIRA affects (masked from the system): 0.8.2.0

- `KAFKA-2024@0.8.2.0`: config 0.8.2.0, metadata answer **affected** (listed_affected)
- `KAFKA-2024@0.8.1.1`: config 0.8.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
It's possible for log cleaning to generate segments that have a gap of more than Int.MaxValue between their base offset and their last offset. It's not possible to index those segments since there's only 4 bytes available to store that difference. The broker will end up writing overflowed ints into the index, and doesn't detect that there is a problem until restarted, at which point you get one of these:

2015-03-16 20:35:49,632 FATAL [main] kafka.server.KafkaServerStartable - Fatal error during KafkaServerStartable startup. Prepare to shutdown
java.lang.IllegalArgumentException: requirement failed: Corrupt index found, index file (/mnt/persistent/kafka-logs/topic/00000000000000000000.index) has non-zero size but the last offset is -1634293959 and the base offset is 0
        at scala.Predef$.require(Predef.scala:233)
        at kafka.log.OffsetIndex.sanityCheck(OffsetIndex.scala:352)
        at kafka.log.Log$$anonfun$loadSegments$5.apply(Log.scala:204)
        at kafka.log.Log$$anonfun$loadSegments$5.apply(Log.scala:203)
        at scala.collection.Iterator$class.foreach(Iterator.scala:727)
        at scala.collection.AbstractIterator.foreach(Iterator.scala:1157)
        at scala.collection.IterableLike$class.foreach(IterableLike.scala:72)
        at scala.collection.AbstractIterable.foreach(Iterable.scala:54)
        at kafka.log.Log.loadSegments(Log.scala:203)
        at kafka.log.Log.<init>(Log.scala:67)
        at kafka.log.LogManager$$anonfun$loadLogs$2$$anonfun$3$$anonfun$apply$7$$anonfun$apply$1.apply$mcV$sp(LogManager.scala:142)
        at kafka.utils.Utils$$anon$1.run(Utils.scala:54)
        at java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:471)
        at java.util.concurrent.FutureTask.run(FutureTask.java:262)
        at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1145)
        at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:615)
        at java.lang.Thread.run(Thread.java:745)
~~~~

### Comments (5)

1.

~~~~
Created reviewboard https://reviews.apache.org/r/32300/diff/
 against branch origin/trunk
~~~~

2.

~~~~
The attached patch stops grouping of segments in LogCleaner if the difference between the first offset in the group and last offset in the next segment is greater than Int.MaxValue. Unit test for border cases included in the patch. 
Also ran a manual test to recreate the reported failure in Kafka restart after a large range of offsets were grouped together. Reran the test with the fix to check that it fixes the issue
~~~~

3.

~~~~
Nice catch and nice patch. Applied.
~~~~

4.

~~~~
Shouldn't the offsetIndex.scala should have a map of 
long -> Int ?

The append() should do
 this.mmap.putInt((offset - baseOffset).toLong)
 this.mmap.putInt(position)

instead of :
 this.mmap.putInt((offset - baseOffset).toInt)
 this.mmap.putInt(position)
       
~~~~

5.

~~~~
[~mgharat] 32-bit relative offsets are stored as explained in the javadoc for OffsetIndex.scala:

{quote}

The file format is a series of entries. The physical format is a 4 byte "relative" offset and a 4 byte file location for the 
message with that offset. The offset stored is relative to the base offset of the index file. So, for example,
if the base offset was 50, then the offset 55 would be stored as 5. Using relative offsets in this way let's us use
only 4 bytes for the offset.

{quote}


~~~~

---

## KAFKA-3500: KafkaOffsetBackingStore set method needs to handle null 

https://issues.apache.org/jira/browse/KAFKA-3500

Given fix versions: 0.10.0.1, 0.10.1.0
JIRA affects (masked from the system): 0.10.0.0

- `KAFKA-3500@0.10.0.0`: config 0.10.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-3500@0.9.0.1`: config 0.9.0.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
In some cases, the key or value for the offset map can be null. However, it seems that we didn't handle null properly in this case and didn't perform null check when converting the byte buffer back to byte array. 
~~~~

### Comments (2)

1.

~~~~
[~liquanpei] Going to grab this since we wanted to get it fixed and I think you've got other stuff on your plate. If you've got something in progress already, let me know.
~~~~

2.

~~~~
Issue resolved by pull request 1662
[https://github.com/apache/kafka/pull/1662]
~~~~

---

## KAFKA-3784: TimeWindows#windowsFor misidentifies some windows if TimeWindows#advanceBy is used

https://issues.apache.org/jira/browse/KAFKA-3784

Given fix versions: 0.10.0.1
JIRA affects (masked from the system): 0.10.0.0

- `KAFKA-3784@0.10.0.0`: config 0.10.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-3784@0.9.0.1`: config 0.9.0.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
Using a time window of size 6 minutes with a 5 minute advanceBy results in some of the timestamped data being inserted into the previous overlapping window even though the event's timestamp > that window's end time. 

The fault lies in TimeWindows#windowsFor which does not check that all the windows it's adding have an endTime > event's timestamp. 

~~~~

### Comments (2)

1.

~~~~
I made a pull request with the fix, plus a unit test that can be used to verify that the problem used to exist. 

https://github.com/apache/kafka/pull/1462
~~~~

2.

~~~~
Issue resolved by pull request 1462
[https://github.com/apache/kafka/pull/1462]
~~~~

---

## KAFKA-3959: KIP-115: __consumer_offsets wrong number of replicas at startup

https://issues.apache.org/jira/browse/KAFKA-3959

Given fix versions: 0.11.0.0
JIRA affects (masked from the system): 0.10.0.0, 0.10.0.1, 0.10.0.2, 0.10.1.0, 0.10.1.1, 0.10.1.2, 0.9.0.1

- `KAFKA-3959@0.10.1.1`: config 0.10.1.1, metadata answer **affected** (listed_affected)
- `KAFKA-3959@0.9.0.0`: config 0.9.0.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 0.10.2.0, 0.11.0.0

### Description

~~~~
When creating a stack of 3 kafka brokers, the consumer is starting faster than kafka nodes and when trying to read a topic, only one kafka node is available.
So the __consumer_offsets is created with a replication factor set to 1 (instead of configured 3) :

offsets.topic.replication.factor=3
default.replication.factor=3
min.insync.replicas=2

Then, other kafka nodes go up and we have exceptions because the replicas # for __consumer_offsets is 1 and min insync is 2. So exceptions are thrown.

What I missed is : Why the __consumer_offsets is created with replication to 1 (when 1 broker is running) whereas in server.properties it is set to 3 ?

To reproduce : 
- Prepare 3 kafka nodes with the 3 lines above added to servers.properties.
- Run one kafka,
- Run one consumer (the __consumer_offsets is created with replicas =1)
- Run 2 more kafka nodes
~~~~

### Comments (23)

1.

~~~~
looks like this is done on purpose.  While creating  __consumer_offsets topic, it takes minimum of (available brokers, offsets.topic.replication) as replication factor.  Since this important internal topic, we may be creating with available replications.

https://github.com/apache/kafka/blob/trunk/core/src/main/scala/kafka/server/KafkaApis.scala#L655

but __consumer_offsets append still will fail complaining  available replicas less than min.insync.replicas.

cc [~ijuma] [~hachikuji] 
~~~~

2.

~~~~
The current behaviour "minimum of (available brokers, offsets.topic.replication) as replication factor" doesn't seem like a great idea. [~hachikuji], do you have the context?
~~~~

3.

~~~~
Perfect timing! [~toddpalino] and I hit this behavior again on Wednesday after reset one of our test clusters. The current behavior came from KAFKA-1864.

The current behavior is pretty surprising when you have clients or tooling running as the cluster is getting setup. Even if your cluster ends up being huge, you'll find out much later that __consumer_offsets was setup with no replication.

I think the right behavior should be for __consumer_offsets topic creation to fail with {{GROUP_COORDINATOR_NOT_AVAILABLE}} until there are at least {{KafkaConfig.offsetsTopicReplicationFactor}} brokers up in the cluster.
~~~~

4.

~~~~
You mentioned
bq. but __consumer_offsets append still will fail complaining  replicas less than min.insync.replicas.

We've had clusters with single replica __consumer_offsets but we have definitely been able to save offsets to them, even though they were less than min.isr.

Is min.isr set on the __consumer_offsets topic? I've never checked. 
~~~~

5.

~~~~
[~onurkaraman], I would agree. [~guozhang] proposed something similar in https://issues.apache.org/jira/browse/KAFKA-1864?focusedCommentId=14335345&page=com.atlassian.jira.plugin.system.issuetabpanels:comment-tabpanel#comment-14335345. Thoughts [~junrao]?
~~~~

6.

~~~~
Another options is to offload the responsibility of __consumer_offsets topic creation to the controller. We can do the check in KafkaController.onBrokerStartup.
~~~~

7.

~~~~
Yes,  min.insync.replicas  applicable to internal topics also. We can override with topic level configs
~~~~

8.

~~~~
Agree with Onur 100% here. We've been running into this a lot lately, and we never know about it until we do a rolling restart of the cluster and consumers break when the topic goes offline.
~~~~

9.

~~~~
btw I can pick this one up once we agree on the fix.
~~~~

10.

~~~~
I would like to present an alternative option. This problem exists with any topic created using default.replication.factor > 1 as well. That prevents using 2 or 3 as the configuration default because we want to support single nodes clusters without changing the defaults. 

Instead of preventing topics from being created with a low replication factor (unless min.isr is set). Instead it would be really nice if we tracked a "target replication factor" in the topic metadata. This is an improvement over assuming the target replication factor based on the actual replicas as is done today and can actually result in a more accurate under replicated count. 

This change would also help support any ability to automatically maintain the desired replication factor as nodes are started, stopped, etc. Some related KIPs for that are:
* [KIP-73 Replication Quotas|https://cwiki.apache.org/confluence/display/KAFKA/KIP-73+Replication+Quotas]
* [KIP-46: Self Healing Kafka|https://cwiki.apache.org/confluence/display/KAFKA/KIP-46%3A+Self+Healing+Kafka]

Would that be a viable option?
~~~~

11.

~~~~
[~granthenke] maybe in the long term. But honestly I would prefer the simple, quick fix for this edge case behavior without complicating the conversation with KIP-73 and KIP-46. To me, the cluster not meeting replication factor requirements on an internal topic is another way of saying the cluster isn't fully setup yet.
~~~~

12.

~~~~
[~onurkaraman] I understand the need for a quick fix and that automatically maintaining a given replication factor will take some time to implement. I wasn't proposing all of that KIP work for this fix. I was thinking just changing the tracked metadata to contain the "target replication factor" and leveraging it to report under replicated partitions would provide an admin enough to diagnose and fix the problem quickly. I referenced the KIPs to show that the change also supports an ultimate fix down the road.

I am worried about __consumer_offsets topic creation failing with GROUP_COORDINATOR_NOT_AVAILABLE until there is at least KafkaConfig.offsetsTopicReplicationFactor brokers because the default for KafkaConfig.offsetsTopicReplicationFactor is 3. That change means any cluster with < 3 brokers will need to change defaults before starting. Including all of the embedded clusters in our tests and likely many users and frameworks development clusters and tests as well. 
~~~~

13.

~~~~
If that's the case, then the default should be set to 1. As least having that as the default, and returning an error if the RF cannot be satisfied, is a reasonable and expected outcome. But having it set up to not enforce the configured RF leads to unintended behavior, even if it's documented here.
~~~~

14.

~~~~
[~granthenke] [~onurkaraman] [~toddpalino] Any more thoughts on this? I think the main use case for handling < 3 brokers by default is when we start up a "cluster" locally for test purposes. Any real use case that wanted a lower replication factor could set it explicitly. This is pretty important and we don't really want to have users jump through hoops to do so; that said, a dramatic warning wouldn't be the end of the world. Maybe even some combination of a low setting plus a setting that gives unsafe warnings but allows unsafely low replication factors for this topic?
~~~~

15.

~~~~
As noted, I just want the config enforced. If RF=3 is configured, that's what we should get. If you need RF=1 for testing, or for specific use cases, set it. Even make the default 1 if that's really what we want. But if I explicitly set RF=3, that's what I should get. And if it causes errors, and I've explicitly set it, that's on me as the user.
~~~~

16.

~~~~
[~toddpalino] That's fair, I think the tension is between trivial quickstart mode working and production settings. Then again, there are other things (even really simple things like the log.dirs) which presumably will differ between the two. Maybe the fix here is to both enforce it and update all quickstarts to use a config/quickstart-server.properties that has offsets.topic.replication.factor=1 and default.replication.factor=1.
~~~~

17.

~~~~
Could we leave the default at RF=3, but override it to RF=1 in config/server.properties (with some comments for why you shouldn't use that setting in practice). People should already expect to override some settings anyway (unless they want their data stored in /tmp) and this would ensure that anyone who is already maintaining their own config will continue to see the same behavior.
~~~~

18.

~~~~
+1. I was thinking about this approach too (assuming [~hachikuji] is also supporting the enforcement of "offsets.topic.replication.factor").

As [~hachikuji] said, the /tmp log.dirs does give the impression that config/server.properties was for quickstart anyway, so I think this is fine.
~~~~

19.

~~~~
+1 as well. I think keeping the config/server.properties file as a quickstart that gets you going with a standalone broker is a good plan.
~~~~

20.

~~~~
Awesome. I think we're in agreement? I can implement it if nobody's done it yet.
~~~~

21.

~~~~
[~onurkaraman] Marked for 0.10.2.0 as this seems like an important fix, but given the new behavior could be considered a breaking change, we might need to defer until 0.11.0.0. Thoughts?
~~~~

22.

~~~~
Either way, it's too late for 0.10.2.0. I'll move it to 0.10.3.0 for now as it is indeed an important fix.
~~~~

23.

~~~~
Issue resolved by pull request 2177
[https://github.com/apache/kafka/pull/2177]
~~~~

---

## KAFKA-5003: StreamThread should catch InvalidTopicException

https://issues.apache.org/jira/browse/KAFKA-5003

Given fix versions: 0.10.2.1, 0.11.0.0
JIRA affects (masked from the system): 0.10.2.0

- `KAFKA-5003@0.10.2.0`: config 0.10.2.0, metadata answer **affected** (listed_affected)
- `KAFKA-5003@0.10.1.1`: config 0.10.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 0.10.2.1, 0.10.2

### Description

~~~~
There is already a PR here: https://github.com/apache/kafka/pull/2747. Tracking with JIRA for 0.10.2.1
~~~~

### Comments (2)

1.

~~~~
The PR from about is for {{trunk}} -- there is a second PR for {{0.10.2}} branch: https://github.com/apache/kafka/pull/2774
~~~~

2.

~~~~
The trunk PR has been merged, 0.10.2 still to be done as it needs to be updated.
~~~~

---

## KAFKA-5090: Kafka Streams SessionStore.findSessions javadoc broken

https://issues.apache.org/jira/browse/KAFKA-5090

Given fix versions: 0.11.0.0
JIRA affects (masked from the system): 0.10.2.0, 0.10.2.1

- `KAFKA-5090@0.10.2.1`: config 0.10.2.1, metadata answer **affected** (listed_affected)
- `KAFKA-5090@0.10.1.1`: config 0.10.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
{code}
    /**
     * Fetch any sessions with the matching key and the sessions end is &le earliestEndTime and the sessions
     * start is &ge latestStartTime
     */
    KeyValueIterator<Windowed<K>, AGG> findSessions(final K key, long earliestSessionEndTime, final long latestSessionStartTime);
{code}

The conditions in the javadoc comment are inverted (le should be ge and ge shoudl be le), since this is what the code does. They were correct in the original KIP:
https://cwiki.apache.org/confluence/display/KAFKA/KIP-94+Session+Windows
{code}

    /**
     * Find any aggregated session values with the matching key and where the
     * session’s end time is >= earliestSessionEndTime, i.e, the oldest session to
     * merge with, and the session’s start time is <= latestSessionStartTime, i.e,
     * the newest session to merge with.
     */
   KeyValueIterator<Windowed<K>, AGG> findSessionsToMerge(final K key, final long earliestSessionEndTime, final long latestSessionStartTime);
{code}

Also, the escaped html character references are missing the trailing semicolon making them render as-is.

Happy to have this assigned to me to fix as it seems trivial.
~~~~

### Comments (1)

1.

~~~~
Issue resolved by pull request 2874
[https://github.com/apache/kafka/pull/2874]
~~~~

---

## KAFKA-5117: Kafka Connect REST endpoints reveal Password typed values

https://issues.apache.org/jira/browse/KAFKA-5117

Given fix versions: 2.0.2, 2.1.1, 2.2.0
JIRA affects (masked from the system): 0.10.2.0

- `KAFKA-5117@0.10.2.0`: config 0.10.2.0, metadata answer **affected** (listed_affected)
- `KAFKA-5117@0.10.1.1`: config 0.10.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
A Kafka Connect connector can specify ConfigDef keys as type of Password. This type was added to prevent logging the values (instead "[hidden]" is logged).

This change does not apply to the values returned by executing a GET on {{connectors/\{connector-name\}}} and {{connectors/\{connector-name\}/config}}. This creates an easily accessible way for an attacker who has infiltrated your network to gain access to potential secrets that should not be available.

I have started on a code change that addresses this issue by parsing the config values through the ConfigDef for the connector and returning their output instead (which leads to the masking of Password typed configs as [hidden]).
~~~~

### Comments (9)

1.

~~~~
[~tholmes] are you still working on this?
~~~~

2.

~~~~
I had some code that seems to work but I'm not very happy with it. I'll try to clean it up a bit and get a PR made so the approach/impact can be discussed.

One main thing I was concerned about was whether or not the connectors use these endpoints to share task configuration. I was seeing some instability when running my code change so I am unsure if it was related or not.  I didn't get a chance to fully diagnose the situation, though.
~~~~

3.

~~~~
This issue is requesting a change in a public API for several Connect REST methods, and therefore we're going to need a KIP for this change to make sure that all considerations are taken into account.
~~~~

4.

~~~~
BTW, the KIP doesn't have to be that complex, since this is a straighforward change. Just follow the process outlined [here|https://cwiki.apache.org/confluence/display/KAFKA/Kafka+Improvement+Proposals]. The "Migration Plan and Compatibility" section of the KIP should highlight the fact that the public response of several methods will change to mask the password configuration values.
~~~~

5.

~~~~
So I'm a bit concerned that simply masking the passwords will not be that advantageous. Sure, it might work if you're just managing your configuration files locally and then using the REST API with curl and thus never really needing to get configurations back out. But this change would likely break every management tool that is using the API to read, modify, and post configurations. Also, to maintain backward compatibility, we'd need to introduce a config file that defaults to _not masking_ -- doesn't that kind of defeat the purpose?

[KIP-208|https://cwiki.apache.org/confluence/display/KAFKA/KIP-208%3A+Add+SSL+support+to+Kafka+Connect+REST+interface] is already trying to add SSL/TLS support to the Connect REST API, and then adding (with a different KIP) ACLs support would mean you can control who can and cannot use different endpoints. That is definitely one approach to preventing exposure of passwords.

Another approach is to avoid putting passwords in the configuration file in the first place. KAFKA-6142 proposes adding support for variables in configuration files, and variables could be used in place of passwords to have the passwords resolved only upon deployment via some "configuration transformer" plugin.
~~~~

6.

~~~~
I would like to add couple of more points related to this KIP

Currently i noticed even accessing end point

connectors/\{connector-name}/status is also hitting the configuration. I think this endpoint need not gather config information.

 

 

 
~~~~

7.

~~~~
Going to close this since [https://cwiki.apache.org/confluence/display/KAFKA/KIP-297%3A+Externalizing+Secrets+for+Connect+Configurations] addresses this problem. Feel free to reopen if that doesn't sufficiently address the issue.
~~~~

8.

~~~~
I'm reopening this because there appears to be a bug in the worker that incorrectly returns the externalized secrets when getting the connector config from the REST API. Instead, the REST API should return the config with the raw configuration values, including those of the form `${provider:path:key}`.

[KIP-297|https://cwiki.apache.org/confluence/display/KAFKA/KIP-297%3A+Externalizing+Secrets+for+Connect+Configurations] is actually not really clear on whether the REST API will be affected, and so IMO its behavior should not have been changed by the implementation of KIP-297 and should return the connector configuration submitted via PUT and stored by the worker as before KIP-297. Only this behavior really works with tooling that edits connector configurations via GET and PUT operations. IMO, *any other behavioral changes should be determined through a new KIP.*

Here are the details. Consider a standalone worker config defines a config provider (using the example `{{FileConfigProvider}}` added by KIP-297):
{code}
...
# Define a config provider that reads from any file
config.providers=file
config.providers.file.class=org.apache.kafka.common.config.provider.FileConfigProvider
{code}

Then, create a connector with at least one property with an externalized placeholder for its value:

{code}
name=my-connector
...
connection.user=foobar
connection.password=${file:/path/to/secret.properties:db.password}
...
{code}

where the `{{/path/to/secrets.properties}}` file contains:

{code}
...
db.password=my-secret
...
{code}

then Connect will use the FileConfigProvider to replace the placeholder on the `{{connection.password}}` value with the `{{db.password}}` property in the  `{{/path/to/secrets.properties}}` file *before* these properties are given to the connector upon startup.

In fact this works just fine. The problem is that when we perform a `{{GET}} connectors/my-connector/` we get the following:

{code}
{
  "name": "my-connector",
  "config": {
    "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
    "mode": "incrementing",
    "incrementing.column.name": "id",
    "topic.prefix": "jdbc-",
    "connection.password": "my-secret",
    "connection.user": "foobar",
...
{code}

Note how the `{{connection.password}}` property is `{{my-secret}}` but should instead be `{{${file:/path/to/secret.properties:db.password}}}`:

{code}
{
  "name": "my-connector",
  "config": {
    "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
    "mode": "incrementing",
    "incrementing.column.name": "id",
    "topic.prefix": "jdbc-",
    "connection.password": "${file:/path/to/secret.properties:db.password}",
    "connection.user": "foobar",
...
{code}




~~~~

9.

~~~~
Resolved with https://github.com/apache/kafka/pull/6129
~~~~

---

## KAFKA-5644: Transient test failure: ResetConsumerGroupOffsetTest.testResetOffsetsToZonedDateTime

https://issues.apache.org/jira/browse/KAFKA-5644

Given fix versions: 0.11.0.1, 1.0.0
JIRA affects (masked from the system): 0.11.0.0

- `KAFKA-5644@0.11.0.0`: config 0.11.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-5644@0.10.2.2`: config 0.10.2.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
{quote}
unit.kafka.admin.ResetConsumerGroupOffsetTest > testResetOffsetsToZonedDateTime FAILED
    java.lang.AssertionError: Expected the consumer group to reset to when offset was 50.
        at kafka.utils.TestUtils$.fail(TestUtils.scala:339)
        at kafka.utils.TestUtils$.waitUntilTrue(TestUtils.scala:853)
        at unit.kafka.admin.ResetConsumerGroupOffsetTest.testResetOffsetsToZonedDateTime(ResetConsumerGroupOffsetTest.scala:188)
{quote}
~~~~

### Comments (1)

1.

~~~~
Issue resolved by pull request 3626
[https://github.com/apache/kafka/pull/3626]
~~~~

---

## KAFKA-6418: AdminClient should handle empty or null topic names better

https://issues.apache.org/jira/browse/KAFKA-6418

Given fix versions: 1.1.0
JIRA affects (masked from the system): 1.0.0

- `KAFKA-6418@1.0.0`: config 1.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-6418@0.11.0.3`: config 0.11.0.3, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
if you try to `createTopics(Collections.singleton(new NewTopic()));` you will get something like the following:
{noformat}
[2018-01-02 11:20:46,481] ERROR [kafka-admin-client-thread | adminclient-3] Uncaught exception in thread 'kafka-admin-client-thread | adminclient-3': (org.apache.kafka.common.utils.KafkaThread)
org.apache.kafka.common.protocol.types.SchemaException: Error computing size for field 'create_topic_requests': Error computing size for field 'topic': Missing value for field 'topic' which has no default value.
	at org.apache.kafka.common.protocol.types.Schema.sizeOf(Schema.java:94)
	at org.apache.kafka.common.protocol.types.Struct.sizeOf(Struct.java:341)
	at org.apache.kafka.common.requests.AbstractRequestResponse.serialize(AbstractRequestResponse.java:28)
	at org.apache.kafka.common.requests.AbstractRequest.serialize(AbstractRequest.java:98)
	at org.apache.kafka.common.requests.AbstractRequest.toSend(AbstractRequest.java:91)
	at org.apache.kafka.clients.NetworkClient.doSend(NetworkClient.java:423)
	at org.apache.kafka.clients.NetworkClient.doSend(NetworkClient.java:397)
	at org.apache.kafka.clients.NetworkClient.send(NetworkClient.java:358)
	at org.apache.kafka.clients.admin.KafkaAdminClient$AdminClientRunnable.sendEligibleCalls(KafkaAdminClient.java:810)
	at org.apache.kafka.clients.admin.KafkaAdminClient$AdminClientRunnable.run(KafkaAdminClient.java:1002)
	at java.lang.Thread.run(Thread.java:745)
[2018-01-02 11:20:46,481] ERROR [kafka-admin-client-thread | adminclient-3] Uncaught exception in thread 'kafka-admin-client-thread | adminclient-3': (org.apache.kafka.common.utils.KafkaThread)
org.apache.kafka.common.protocol.types.SchemaException: Error computing size for field 'create_topic_requests': Error computing size for field 'topic': Missing value for field 'topic' which has no default value.
	at org.apache.kafka.common.protocol.types.Schema.sizeOf(Schema.java:94)
	at org.apache.kafka.common.protocol.types.Struct.sizeOf(Struct.java:341)
	at org.apache.kafka.common.requests.AbstractRequestResponse.serialize(AbstractRequestResponse.java:28)
	at org.apache.kafka.common.requests.AbstractRequest.serialize(AbstractRequest.java:98)
	at org.apache.kafka.common.requests.AbstractRequest.toSend(AbstractRequest.java:91)
	at org.apache.kafka.clients.NetworkClient.doSend(NetworkClient.java:423)
	at org.apache.kafka.clients.NetworkClient.doSend(NetworkClient.java:397)
	at org.apache.kafka.clients.NetworkClient.send(NetworkClient.java:358)
	at org.apache.kafka.clients.admin.KafkaAdminClient$AdminClientRunnable.sendEligibleCalls(KafkaAdminClient.java:810)
	at org.apache.kafka.clients.admin.KafkaAdminClient$AdminClientRunnable.run(KafkaAdminClient.java:1002)
	at java.lang.Thread.run(Thread.java:745)
[2018-01-02 11:21:01,383] ERROR [qtp1875757262-59] Unhandled exception resulting in internal server error response (io.confluent.rest.exceptions.GenericExceptionMapper)
java.util.concurrent.TimeoutException
	at org.apache.kafka.common.internals.KafkaFutureImpl$SingleWaiter.await(KafkaFutureImpl.java:108)
	at org.apache.kafka.common.internals.KafkaFutureImpl.get(KafkaFutureImpl.java:225)
	at io.confluent.controlcenter.data.KafkaDao.createTopics(KafkaDao.java:85)
	at io.confluent.controlcenter.rest.KafkaResource.createTopic(KafkaResource.java:87)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:57)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:606)
{noformat}

the actual error prints immediately, but the adminclient still waits for a timeout and then exposes a TimeoutException to the user

Note that no other elements of the batch request are performed.
~~~~

### Comments (3)

1.

~~~~
If I understand correctly, the problem is that there is an invalid empty topic name here.  So we need to validate that at an earlier stage...
~~~~

2.

~~~~
validation before serialization would help. but i *think* that catching the exception in the client and failing the future with that exception would be more user friendly
~~~~

3.

~~~~
The serialization exception would prevent any other part of the request from being performed, though.  So we just have to check for empty or null topic names and issue an appropriate error.
~~~~

---

## KAFKA-6582: Partitions get underreplicated, with a single ISR, and doesn't recover. Other brokers do not take over and we need to manually restart the broker.

https://issues.apache.org/jira/browse/KAFKA-6582

Given fix versions: 2.1.1
JIRA affects (masked from the system): 1.0.0

- `KAFKA-6582@1.0.0`: config 1.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-6582@0.11.0.3`: config 0.11.0.3, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 1.0, 0.10.2.1, 0.8.2.1, 1.0.0, 0.10.0.0, 2.1, 4.4.0, 1.0.1, 0.10.1.0, 0.10.1, 2.1.0, 2.1.1, 2.0.1, 2.0, 0.10.2.0, 2.0.0, 2.3.0

### Description

~~~~
Partitions get underreplicated, with a single ISR, and doesn't recover. Other brokers do not take over and we need to manually restart the 'single ISR' broker (if you describe the partitions of replicated topic it is clear that some partitions are only in sync on this broker).

This bug resembles KAFKA-4477 a lot, but since that issue is marked as resolved this is probably something else but similar.

We have the same issue (or at least it looks pretty similar) on Kafka 1.0. 

Since upgrading to Kafka 1.0 in November 2017 we've had these issues (we've upgraded from Kafka 0.10.2.1).

This happens almost every 24-48 hours on a random broker. This is why we currently have a cronjob which restarts every broker every 24 hours. 

During this issue the ISR shows the following server log: 
{code:java}
[2018-02-20 12:02:08,342] WARN Attempting to send response via channel for which there is no open connection, connection id 10.132.0.32:9092-10.14.148.20:56352-96708 (kafka.network.Processor)
[2018-02-20 12:02:08,364] WARN Attempting to send response via channel for which there is no open connection, connection id 10.132.0.32:9092-10.14.150.25:54412-96715 (kafka.network.Processor)
[2018-02-20 12:02:08,349] WARN Attempting to send response via channel for which there is no open connection, connection id 10.132.0.32:9092-10.14.149.18:35182-96705 (kafka.network.Processor)
[2018-02-20 12:02:08,379] WARN Attempting to send response via channel for which there is no open connection, connection id 10.132.0.32:9092-10.14.150.25:54456-96717 (kafka.network.Processor)
[2018-02-20 12:02:08,448] WARN Attempting to send response via channel for which there is no open connection, connection id 10.132.0.32:9092-10.14.159.20:36388-96720 (kafka.network.Processor)
[2018-02-20 12:02:08,683] WARN Attempting to send response via channel for which there is no open connection, connection id 10.132.0.32:9092-10.14.157.110:41922-96740 (kafka.network.Processor)
{code}
Also on the ISR broker, the controller log shows this:
{code:java}
[2018-02-20 12:02:14,927] INFO [Controller-3-to-broker-3-send-thread]: Controller 3 connected to 10.132.0.32:9092 (id: 3 rack: null) for sending state change requests (kafka.controller.RequestSendThread)
[2018-02-20 12:02:14,927] INFO [Controller-3-to-broker-0-send-thread]: Controller 3 connected to 10.132.0.10:9092 (id: 0 rack: null) for sending state change requests (kafka.controller.RequestSendThread)
[2018-02-20 12:02:14,928] INFO [Controller-3-to-broker-1-send-thread]: Controller 3 connected to 10.132.0.12:9092 (id: 1 rack: null) for sending state change requests (kafka.controller.RequestSendThread){code}
And the non-ISR brokers show these kind of errors:

 
{code:java}
2018-02-20 12:02:29,204] WARN [ReplicaFetcher replicaId=1, leaderId=3, fetcherId=0] Error in fetch to broker 3, request (type=FetchRequest, replicaId=1, maxWait=500, minBytes=1, maxBytes=10485760, fetchData={......................}, isolationLevel=READ_UNCOMMITTED) (kafka.server.ReplicaFetcherThread)
java.io.IOException: Connection to 3 was disconnected before the response was read
 at org.apache.kafka.clients.NetworkClientUtils.sendAndReceive(NetworkClientUtils.java:95)
 at kafka.server.ReplicaFetcherBlockingSend.sendRequest(ReplicaFetcherBlockingSend.scala:96)
 at kafka.server.ReplicaFetcherThread.fetch(ReplicaFetcherThread.scala:205)
 at kafka.server.ReplicaFetcherThread.fetch(ReplicaFetcherThread.scala:41)
 at kafka.server.AbstractFetcherThread.processFetchRequest(AbstractFetcherThread.scala:149)
 at kafka.server.AbstractFetcherThread.doWork(AbstractFetcherThread.scala:113)
 at kafka.utils.ShutdownableThread.run(ShutdownableThread.scala:64)
{code}
 
~~~~

### Comments (21)

1.

~~~~
I am facing the same issue while upgrading our cluster from 0.8.2.1 to 1.0 . 
After starting broker it starts giving this exception 

java.io.IOException: Connection to 1 was disconnected before the response was read
        at org.apache.kafka.clients.NetworkClientUtils.sendAndReceive(NetworkClientUtils.java:95)
        at kafka.server.ReplicaFetcherBlockingSend.sendRequest(ReplicaFetcherBlockingSend.scala:96)
        at kafka.server.ReplicaFetcherThread.fetch(ReplicaFetcherThread.scala:205)
        at kafka.server.ReplicaFetcherThread.fetch(ReplicaFetcherThread.scala:41)
        at kafka.server.AbstractFetcherThread.processFetchRequest(AbstractFetcherThread.scala:149)
        at kafka.server.AbstractFetcherThread.doWork(AbstractFetcherThread.scala:113)
        at kafka.utils.ShutdownableThread.run(ShutdownableThread.scala:64)


~~~~

2.

~~~~
Hi, I am not doing any upgradations  still facing this exception 

java.io.IOException: Connection to 3 was disconnected before the response was read]

frequently in qa and Prod env.

in qa we r using 1.0.0 verison and in prod we are using 0.10.0.0 version of kafka 
~~~~

3.

~~~~
[~chetan027] what ended up resolving the issues for you. I just upgraded from 0.8.2.1 and I am facing the same issue. Any ideas on how you recovered? 
~~~~

4.

~~~~
Almost the same issue with a fresh install of version 2.1.

Environment: Ubuntu 16.04  Linux 4.4.0-141-generic
~~~~

5.

~~~~
Had the same issue after upgrading from 1.0.1 to 2.1. Rolling back to 1.0.1 helped. We are running cluster of 5 brokers with 26 topics, 16 partitions each + {{__consumer_offsets}} topic with 50 partitions. Each topic has replication factor of 2.

The only thing I have noticed is that after we had upgraded from 1.0.1 to 2.1, {{kafka_server_fetcherlagmetrics_consumerlag}} metric started to grow and behaved weirdly for all the partitions. I tried increasing {{replica.fetch.max.bytes}} and {{num.replica.fetchers}}, but it did not help.

Here is an example for one of the topics. The flat line in the middle happened during the event when one of the brokers got stuck.

!Screenshot 2019-01-18 at 13.08.17.png!

And this is how fetcher lag looks before and after rollback:

!Screenshot 2019-01-18 at 13.16.59.png!  

I also tried to check lag with `kafka-replica-verification.sh` but it did not show any issues there:
{code:java}
# ./kafka-replica-verification.sh --broker-list kafka-0.kafka:9092,kafka-1.kafka:9092,kafka-2.kafka:9092,kafka-3.kafka:9092,kafka-4.kafka:9092
2019-01-18 00:21:58,854: verification process is started.
2019-01-18 00:22:28,800: max lag is 2 for partition presence-2 at offset 11587 among 451 partitions
2019-01-18 00:22:58,803: max lag is 2 for partition mqtt-presence-13 at offset 10418 among 451 partitions
2019-01-18 00:23:28,806: max lag is 1 for partition users-11 at offset 3529 among 451 partitions
2019-01-18 00:23:58,810: max lag is 51 for partition notifications-14 at offset 193179 among 451 partitions
2019-01-18 00:24:28,811: max lag is 3 for partition api-responses-0 at offset 56367 among 451 partitions
2019-01-18 00:24:58,813: max lag is 1 for partition follows-6 at offset 1059 among 451 partitions{code}
~~~~

6.

~~~~
We encounter the same problem...

Last week I did a rolling upgrade from 0.10.1.0 in our Dev-Environment to prepare the upgrade of all Kafka-Environments to 2.1. And starting on Friday we have that error...

It started after we did the third step and changed to log.message.format.version from 0.10.1 to 2.1. The two previous steps didn't cause the problem... Or there was not enough time between them for the problem to occur as I did the upgrade of Kafka and then the inter.broker.protocol.version to 2.1 within like 24 hours.

We are using three node cluster on Docker Containers in Azure.

On Friday first the node1, then node2 failed within 3 hours of each other during morning. The node3 then failed with the mentioned error during afternoon the same day. As all three had been restarted on Friday it ran fine until Sunday evening at 8:09 PM. When node2 failed with that error and I had to restart it this Morning to get everything back online.

As this is our Dev-Environment it's not too much pain it it fails or needs to be restarted. So we can use this for debugging etc.
So just tell me which Logs I should get or what else you need or what I should try to solve this issue.
~~~~

7.

~~~~
Is the issue happening with 2.1.0 or 2.1.1?
~~~~

8.

~~~~
We are using 2.1.0

Will update to 2.1.1 today to see if it's related to the mentioned deadlock
~~~~

9.

~~~~
So far after 24 hours no issue yet... But I think it's a bit too early to tell if it's fixed with latest version.

 

However we found that balancing the leaders was not very good with default settings and we had to run the balancing manually to really change something. Still investigating on that one...
~~~~

10.

~~~~
2.1.1 fixed the problem for us and we'll now go ahead with upgrading up to Prod...
~~~~

11.

~~~~
Does anyone know if this issue affects 2.0.1. Because we have it in production and had a similar problem.
~~~~

12.

~~~~
I'm sorry, we skipped 2.0 and went directly to 2.1 from 0.10.2.0... So I have no idea if it's affected
~~~~

13.

~~~~
Hello [~pogo] we are facing the same issue in version *2.0.0*
~~~~

14.

~~~~
The Jira status is still Open. Is the issue indeed resolved in 2.1.1, or is it actually considered to be open? Thanks.
~~~~

15.

~~~~
Hello,

We are also having the same issue in version 2.0.1 in the past several months since the last upgrade.

Is this issue resolved in version 2.1.1?

Thanks.
~~~~

16.

~~~~
Hello，

I encountered the same problem in version 1.0.0.

How to fix it in 2.1.1?

Thanks.
~~~~

17.

~~~~
We are running 2.1.1 in production (and four other environments) since March without this issue showing again.
~~~~

18.

~~~~
Someone encountered similar issue in version 2.1.1(KAFKA-7870), is the issue indeed resolved in 2.1.1?
~~~~

19.

~~~~
We were running 2.1.1 in all environments without encountering this issue again before updating and now running 2.3.0 everywhere...
~~~~

20.

~~~~
Based on the comments, it looks like this has been fixed since 2.1.1. We can reopen if we see evidence to the contrary.
~~~~

21.

~~~~
我们遇到了相同问题 在 kafka_2.11-0.10.2.0 版本中
~~~~

---

## KAFKA-6737: Is Kafka imapcted by critical vulnerqbilty CVE-2018-7489

https://issues.apache.org/jira/browse/KAFKA-6737

Given fix versions: 2.0.0
JIRA affects (masked from the system): 0.10.1.0, 1.0.1, 1.1.0

- `KAFKA-6737@1.0.1`: config 1.0.1, metadata answer **affected** (listed_affected)
- `KAFKA-6737@0.10.0.1`: config 0.10.0.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.00, 1.1.1, 1.0.2

### Description

~~~~
Kafka is using FasterXML jackson-databind before 2.8.11.1 and 2.9.x before 2.9.5 , which allows unauthenticated remote code execution because of an incomplete fix for the CVE-2017-7525 deserialization flaw. This is exploitable by sending maliciously crafted JSON input to the readValue method of the ObjectMapper, bypassing a blacklist that is ineffective if the c3p0 libraries are available in the classpath.

 

I have checked that all released versions of Kafka are using jackson-databind before 2.8.11.1 and 2.9.x before 2.9.5.

There are three open questions:

Question1: Is Kafka imapcted by critical vulnerqbilty CVE-2018-7489?

[http://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2018-7489]

Question2: If answer of first question is Yes. Is there any workaround to fix it on released version. 

Question3: If answer of first question is Yes. Should we fix it in future versions?

 

 
~~~~

### Comments (3)

1.

~~~~
As the description states, c3p0 has to be in the classpath and Kafka doesn't depend on that library. We have upgraded Jackson to 2.9.5 in trunk in any case though:

https://github.com/apache/kafka/commit/9baa9bddba0dc1b3bda167ea509bd90226615e1f
~~~~

2.

~~~~
Dear Ismael,

Thanks a lot, for confirmation that Kafka does not use c3p0 in the classpath. 

Regarding Jackson upgrade to 2.9.5, what is expected release date and version. I am new to this site, so asking for help.

 

With Best Regards,

Akansh

 
~~~~

3.

~~~~
This will be fixed part of upcoming 2.00, 1.1.1, 1.0.2 releases.
~~~~

---

## KAFKA-6747: kafka-streams Invalid transition attempted from state READY to state ABORTING_TRANSACTION

https://issues.apache.org/jira/browse/KAFKA-6747

Given fix versions: 0.11.0.3, 1.0.2, 1.1.1, 2.0.0
JIRA affects (masked from the system): 1.1.0

- `KAFKA-6747@1.1.0`: config 1.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-6747@1.0.1`: config 1.0.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 1.1, 1.0

### Description

~~~~
[~frederica] running tests against kafka-streams 1.1 and get the following stack trace (everything was working alright using kafka-streams 1.0):
{code}
ERROR org.apache.kafka.streams.processor.internals.AssignedStreamsTasks - stream-thread [feedBuilder-XXX-StreamThread-4] Failed to close stream task, 0_2
org.apache.kafka.common.KafkaException: TransactionalId feedBuilder-0_2: Invalid transition attempted from state READY to state ABORTING_TRANSACTION
        at org.apache.kafka.clients.producer.internals.TransactionManager.transitionTo(TransactionManager.java:757)
        at org.apache.kafka.clients.producer.internals.TransactionManager.transitionTo(TransactionManager.java:751)
        at org.apache.kafka.clients.producer.internals.TransactionManager.beginAbort(TransactionManager.java:230)
        at org.apache.kafka.clients.producer.KafkaProducer.abortTransaction(KafkaProducer.java:660)
        at org.apache.kafka.streams.processor.internals.StreamTask.closeSuspended(StreamTask.java:486)
        at org.apache.kafka.streams.processor.internals.StreamTask.close(StreamTask.java:546)
        at org.apache.kafka.streams.processor.internals.AssignedTasks.closeNonRunningTasks(AssignedTasks.java:166)
        at org.apache.kafka.streams.processor.internals.AssignedTasks.suspend(AssignedTasks.java:151)
        at org.apache.kafka.streams.processor.internals.TaskManager.suspendTasksAndState(TaskManager.java:242)
        at org.apache.kafka.streams.processor.internals.StreamThread$RebalanceListener.onPartitionsRevoked(StreamThread.java:291)
        at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.onJoinPrepare(ConsumerCoordinator.java:414)
        at org.apache.kafka.clients.consumer.internals.AbstractCoordinator.joinGroupIfNeeded(AbstractCoordinator.java:359)
        at org.apache.kafka.clients.consumer.internals.AbstractCoordinator.ensureActiveGroup(AbstractCoordinator.java:316)
        at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.poll(ConsumerCoordinator.java:290)
        at org.apache.kafka.clients.consumer.KafkaConsumer.pollOnce(KafkaConsumer.java:1149)
        at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:1115)
        at org.apache.kafka.streams.processor.internals.StreamThread.pollRequests(StreamThread.java:827)
        at org.apache.kafka.streams.processor.internals.StreamThread.runOnce(StreamThread.java:784)
        at org.apache.kafka.streams.processor.internals.StreamThread.runLoop(StreamThread.java:750)
        at org.apache.kafka.streams.processor.internals.StreamThread.run(StreamThread.java:720)
{code}

This happens when starting the same stream-processing application on 3 JVMs all running on the same linux box, JVMs are named JVM-[2-4]. All 3 instances use separate stream state.dir. No record is ever processed because the input kafka topics are empty at this stage.

JVM-2 starts first, joined shortly after by JVM-4 and JVM-3, find the state transition logs below. The above stacktrace is from JVM-4
{code}
[JVM-2] stream-client [feedBuilder-XXX] State transition from RUNNING to REBALANCING
[JVM-2] stream-client [feedBuilder-XXX] State transition from REBALANCING to RUNNING
[JVM-4] stream-client [feedBuilder-XXX] State transition from RUNNING to REBALANCING
[JVM-2] stream-client [feedBuilder-XXX] State transition from RUNNING to REBALANCING
[JVM-2] stream-client [feedBuilder-XXX] State transition from REBALANCING to RUNNING
[JVM-3] stream-client [feedBuilder-XXX] State transition from RUNNING to REBALANCING
[JVM-2] stream-client [feedBuilder-XXX] State transition from RUNNING to REBALANCING
JVM-4 crashes here with above stacktrace
[JVM-2] stream-client [feedBuilder-XXX] State transition from REBALANCING to RUNNING
[JVM-4] stream-client [feedBuilder-XXX] State transition from REBALANCING to ERROR
[JVM-4] stream-client [feedBuilder-XXX] State transition from ERROR to PENDING_SHUTDOWN
[JVM-4] stream-client [feedBuilder-XXX] State transition from PENDING_SHUTDOWN to NOT_RUNNING
[JVM-4] stream-client [feedBuilder-XXX] State transition from RUNNING to REBALANCING
[JVM-3] stream-client [feedBuilder-XXX] State transition from REBALANCING to RUNNING
[JVM-2] stream-client [feedBuilder-XXX] State transition from RUNNING to REBALANCING
[JVM-3] stream-client [feedBuilder-XXX] State transition from RUNNING to REBALANCING
[JVM-2] stream-client [feedBuilder-XXX] State transition from REBALANCING to RUNNING
[JVM-3] stream-client [feedBuilder-XXX] State transition from REBALANCING to RUNNING
[JVM-4] stream-client [feedBuilder-XXX] State transition from REBALANCING to RUNNING
[JVM-2] stream-client [feedBuilder-XXX] State transition from RUNNING to PENDING_SHUTDOWN
[JVM-3] stream-client [feedBuilder-XXX] State transition from RUNNING to REBALANCING
[JVM-4] stream-client [feedBuilder-XXX] State transition from RUNNING to REBALANCING
[JVM-2] stream-client [feedBuilder-XXX] State transition from PENDING_SHUTDOWN to NOT_RUNNING
[JVM-4] stream-client [feedBuilder-XXX] State transition from REBALANCING to RUNNING
[JVM-3] stream-client [feedBuilder-XXX] State transition from REBALANCING to RUNNING
[JVM-3] stream-client [feedBuilder-XXX] State transition from RUNNING to PENDING_SHUTDOWN
[JVM-4] stream-client [feedBuilder-XXX] State transition from RUNNING to PENDING_SHUTDOWN
[JVM-3] stream-client [feedBuilder-XXX] State transition from PENDING_SHUTDOWN to NOT_RUNNING
[JVM-4] stream-client [feedBuilder-XXX] State transition from PENDING_SHUTDOWN to NOT_RUNNING
{code}
~~~~

### Comments (4)

1.

~~~~
https://github.com/apache/kafka/pull/4826
~~~~

2.

~~~~
Thanks for the quick catch [~tedyu]!
~~~~

3.

~~~~
What is the valid transition? I got Invalid transition attempted from state COMMITTING_TRANSACTION to state ABORTING_TRANSACTION, when the brokers are down. The code flow is to abort when commit throws exception.
~~~~

4.

~~~~
What exception did you get on commit? Some exceptions are fatal and you should not call anything on the producer any longer but just `close()` it.
~~~~

---

## KAFKA-7379: send.buffer.bytes should be allowed to set -1 in KafkaStreams

https://issues.apache.org/jira/browse/KAFKA-7379

Given fix versions: 2.1.0
JIRA affects (masked from the system): 0.10.2.2, 0.11.0.3, 1.0.2, 1.1.1, 2.0.0

- `KAFKA-7379@2.0.0`: config 2.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-7379@0.10.2.1`: config 0.10.2.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
send.buffer.bytes and receive.buffer.bytes are declared with atLeast(0) constraint in StreamsConfig, whereas -1 should be also allowed to set. This is like KAFKA-6891.


~~~~

### Comments (2)

1.

~~~~
Hello! I will work on this issue.
~~~~

2.

~~~~
Thanks for picking this up [~Aleksei_Izmalkin]. I added you to the list of contributors and assigned the ticket to you. You can now also self-assign tickets.
~~~~

---

## KAFKA-7386: Streams Scala wrapper should not cache serdes

https://issues.apache.org/jira/browse/KAFKA-7386

Given fix versions: 2.0.1, 2.1.0
JIRA affects (masked from the system): 2.0.0

- `KAFKA-7386@2.0.0`: config 2.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-7386@1.1.1`: config 1.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
for example, [https://github.com/apache/kafka/blob/trunk/streams/streams-scala/src/main/scala/org/apache/kafka/streams/scala/Serdes.scala#L28] invokes Serdes.String() once and caches the result.

However, the implementation of the String serde has a non-empty configure method that is variant in whether it's used as a key or value serde. So we won't get correct execution if we create one serde and use it for both keys and values.

The fix is simple: change all the `val` declarations in scala.Serdes to `def`. Thanks to the referential transparency for parameterless methods in scala, no user-facing code will break.
~~~~

---

## KAFKA-7557: optimize LogManager.truncateFullyAndStartAt()

https://issues.apache.org/jira/browse/KAFKA-7557

Given fix versions: 2.2.0
JIRA affects (masked from the system): 2.0.0, 2.1.0

- `KAFKA-7557@2.1.0`: config 2.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-7557@1.1.1`: config 1.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
When a ReplicaFetcherThread calls LogManager.truncateFullyAndStartAt() for a partition, we call LogManager.checkpointLogRecoveryOffsetsInDir() and then Log.deleteSnapshotsAfterRecoveryPointCheckpoint() on all the logs in that directory. This requires listing all the files in each log dir to figure out the snapshot files. If some logs have many log segment files. This could take some time. The can potentially block a replica fetcher thread, which indirectly causes the request handler threads to be blocked.

 
~~~~

### Comments (2)

1.

~~~~
To improve this, instead of calling Log.deleteSnapshotsAfterRecoveryPointCheckpoint() on all logs, we could probably call only the one that's being truncated.
~~~~

2.

~~~~
merged to trunk
~~~~

---

## KAFKA-7579: System Test Failure - security_test.SecurityTest.test_client_ssl_endpoint_validation_failure

https://issues.apache.org/jira/browse/KAFKA-7579

Given fix versions: 2.0.2, 2.1.0
JIRA affects (masked from the system): 2.0.1

- `KAFKA-7579@2.0.1`: config 2.0.1, metadata answer **affected** (listed_affected)
- `KAFKA-7579@2.0.0`: config 2.0.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 0.7.1, 2.0.1

### Description

~~~~
The security_test.SecurityTest.test_client_ssl_endpoint_validation_failure test with security_protocol=SSL fails to pass
{code:java}
SESSION REPORT (ALL TESTS) ducktape version: 0.7.1 session_id: 2018-10-31--002 run time: 2 minutes 12.452 seconds tests run: 2 passed: 1 failed: 1 ignored: 0 test_id: kafkatest.tests.core.security_test.SecurityTest.test_client_ssl_endpoint_validation_failure.interbroker_security_protocol=PLAINTEXT.security_protocol=SSL status: FAIL run time: 1 minute 2.149 seconds Node ducker@ducker05: did not stop within the specified timeout of 15 seconds Traceback (most recent call last): File "/usr/local/lib/python2.7/dist-packages/ducktape/tests/runner_client.py", line 132, in run data = self.run_test() File "/usr/local/lib/python2.7/dist-packages/ducktape/tests/runner_client.py", line 185, in run_test return self.test_context.function(self.test) File "/usr/local/lib/python2.7/dist-packages/ducktape/mark/_mark.py", line 324, in wrapper return functools.partial(f, *args, **kwargs)(*w_args, **w_kwargs) File "/opt/kafka-dev/tests/kafkatest/tests/core/security_test.py", line 114, in test_client_ssl_endpoint_validation_failure self.consumer.stop() File "/usr/local/lib/python2.7/dist-packages/ducktape/services/background_thread.py", line 80, in stop super(BackgroundThreadService, self).stop() File "/usr/local/lib/python2.7/dist-packages/ducktape/services/service.py", line 278, in stop self.stop_node(node) File "/opt/kafka-dev/tests/kafkatest/services/console_consumer.py", line 254, in stop_node (str(node.account), str(self.stop_timeout_sec)) AssertionError: Node ducker@ducker05: did not stop within the specified timeout of 15 seconds test_id: kafkatest.tests.core.security_test.SecurityTest.test_client_ssl_endpoint_validation_failure.interbroker_security_protocol=SSL.security_protocol=PLAINTEXT status: PASS run time: 1 minute 10.144 seconds ducker-ak test failed
{code}
~~~~

### Comments (4)

1.

~~~~
This issue is related to KAFKA-7561
~~~~

2.

~~~~
tests are passing locally after increasing console consume timeout. looks like the issue started after [https://github.com/apache/kafka/pull/5735]
I am going to lower the priority to unblock 2.0.1 release. Let me know if any concerns.
~~~~

3.

~~~~
Is this still a blocker?
~~~~

4.

~~~~
This is fixed via  KAFKA-7561.
~~~~

---

## KAFKA-7697: Possible deadlock in kafka.cluster.Partition

https://issues.apache.org/jira/browse/KAFKA-7697

Given fix versions: 2.1.1, 2.2.0
JIRA affects (masked from the system): 2.1.0

- `KAFKA-7697@2.1.0`: config 2.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-7697@2.0.1`: config 2.0.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 0.10.2.0, 2.1.0, 2.1.1, v2.0.0, v2.1.0, 2.0.0, 2.0.1, 2.2.0

### Description

~~~~
After upgrading a fairly busy broker from 0.10.2.0 to 2.1.0, it locked up within a few minutes (by "locked up" I mean that all request handler threads were busy, and other brokers reported that they couldn't communicate with it). I restarted it a few times and it did the same thing each time. After downgrading to 0.10.2.0, the broker was stable. I attached a threaddump.txt from the last attempt on 2.1.0 that shows lots of kafka-request-handler- threads trying to acquire the leaderIsrUpdateLock lock in kafka.cluster.Partition.

It jumps out that there are two threads that already have some read lock (can't tell which one) and are trying to acquire a second one (on two different read locks: 0x0000000708184b88 and 0x000000070821f188): kafka-request-handler-1 and kafka-request-handler-4. Both are handling a produce request, and in the process of doing so, are calling Partition.fetchOffsetSnapshot while trying to complete a DelayedFetch. At the same time, both of those locks have writers from other threads waiting on them (kafka-request-handler-2 and kafka-scheduler-6). Neither of those locks appear to have writers that hold them (if only because no threads in the dump are deep enough in inWriteLock to indicate that).

ReentrantReadWriteLock in nonfair mode prioritizes waiting writers over readers. Is it possible that kafka-request-handler-1 and kafka-request-handler-4 are each trying to read-lock the partition that is currently locked by the other one, and they're both parked waiting for kafka-request-handler-2 and kafka-scheduler-6 to get write locks, which they never will, because the former two threads own read locks and aren't giving them up?
~~~~

### Comments (29)

1.

~~~~
Marking as blocker until we understand the details.
~~~~

2.

~~~~
Changes made under KAFKA-7395 now protect fetch using the Partition's {{leaderIsrUpdateLock}}. This results in the read lock being acquired while completing a delayed fetch. This is unsafe since delayed operations can be completed while holding onto another Partition lock. For example the thread dump for request-handler-4 shows:

{quote}
        at sun.misc.Unsafe.park(Native Method)
        - parking to wait for  <0x000000070821f188> (a java.util.concurrent.locks.ReentrantReadWriteLock$NonfairSync)
        at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
        at java.util.concurrent.locks.AbstractQueuedSynchronizer.parkAndCheckInterrupt(AbstractQueuedSynchronizer.java:836)
        at java.util.concurrent.locks.AbstractQueuedSynchronizer.doAcquireShared(AbstractQueuedSynchronizer.java:967)
        at java.util.concurrent.locks.AbstractQueuedSynchronizer.acquireShared(AbstractQueuedSynchronizer.java:1283)
        at java.util.concurrent.locks.ReentrantReadWriteLock$ReadLock.lock(ReentrantReadWriteLock.java:727)
        at kafka.utils.CoreUtils$.inLock(CoreUtils.scala:249)
        at kafka.utils.CoreUtils$.inReadLock(CoreUtils.scala:257)
        at kafka.cluster.Partition.fetchOffsetSnapshot(Partition.scala:832)
        at kafka.server.DelayedFetch.$anonfun$tryComplete$1(DelayedFetch.scala:87)
        at kafka.server.DelayedFetch.$anonfun$tryComplete$1$adapted(DelayedFetch.scala:79)
        at kafka.server.DelayedFetch$$Lambda$912/582152661.apply(Unknown Source)
        at scala.collection.mutable.ResizableArray.foreach(ResizableArray.scala:58)
        at scala.collection.mutable.ResizableArray.foreach$(ResizableArray.scala:51)
        at scala.collection.mutable.ArrayBuffer.foreach(ArrayBuffer.scala:47)
        at kafka.server.DelayedFetch.tryComplete(DelayedFetch.scala:79)
        at kafka.server.DelayedOperation.maybeTryComplete(DelayedOperation.scala:121)
        at kafka.server.DelayedOperationPurgatory$Watchers.tryCompleteWatched(DelayedOperation.scala:371)
        at kafka.server.DelayedOperationPurgatory.checkAndComplete(DelayedOperation.scala:277)
        at kafka.server.ReplicaManager.tryCompleteDelayedFetch(ReplicaManager.scala:307)
        at kafka.cluster.Partition.$anonfun$appendRecordsToLeader$1(Partition.scala:743)
        at kafka.cluster.Partition$$Lambda$917/80048373.apply(Unknown Source)
        at kafka.utils.CoreUtils$.inLock(CoreUtils.scala:251)
        at kafka.utils.CoreUtils$.inReadLock(CoreUtils.scala:257)
        at kafka.cluster.Partition.appendRecordsToLeader(Partition.scala:729)
        at kafka.server.ReplicaManager.$anonfun$appendToLocalLog$2(ReplicaManager.scala:735)
        at kafka.server.ReplicaManager$$Lambda$915/220982367.apply(Unknown Source)
        at scala.collection.TraversableLike.$anonfun$map$1(TraversableLike.scala:233)
        at scala.collection.TraversableLike$$Lambda$12/1209669119.apply(Unknown Source)
        at scala.collection.mutable.HashMap.$anonfun$foreach$1(HashMap.scala:145)
        at scala.collection.mutable.HashMap$$Lambda$24/477289012.apply(Unknown Source)
        at scala.collection.mutable.HashTable.foreachEntry(HashTable.scala:235)
        at scala.collection.mutable.HashTable.foreachEntry$(HashTable.scala:228)
        at scala.collection.mutable.HashMap.foreachEntry(HashMap.scala:40)
        at scala.collection.mutable.HashMap.foreach(HashMap.scala:145)
        at scala.collection.TraversableLike.map(TraversableLike.scala:233)
        at scala.collection.TraversableLike.map$(TraversableLike.scala:226)
        at scala.collection.AbstractTraversable.map(Traversable.scala:104)
        at kafka.server.ReplicaManager.appendToLocalLog(ReplicaManager.scala:723)
        at kafka.server.ReplicaManager.appendRecords(ReplicaManager.scala:470)
        at kafka.server.KafkaApis.handleProduceRequest(KafkaApis.scala:482)
        at kafka.server.KafkaApis.handle(KafkaApis.scala:106)
        at kafka.server.KafkaRequestHandler.run(KafkaRequestHandler.scala:69)
        at java.lang.Thread.run(Thread.java:748)
{quote}

A whole bunch of threads including all request handler threads seem to be deadlocked as a result of {{leaderIsrUpdateLock}} of two partitions that are blocked while completing delayed fetch as a result of waiting writers.

For purgatory operations that acquire a lock, we use that lock as the delayed operation lock, but that is not an option here since fetch could contain multiple partitions. So we need some other way to avoid blocking for a Partition lock while holding onto another Partition lock.
~~~~

3.

~~~~
when 2.1.1 is expected to be released?
~~~~

4.

~~~~
Hi all!   We just had this bug hit a second cluster - deadlocked node with fast growing FD consumption.    Any chance we can get a release quickly that contains this fix?   
~~~~

5.

~~~~
Same here. After upgrading from v2.0.0 to v2.1.0 we also hit this bug.
~~~~

6.

~~~~
Apache Kafka 2.1.1 containing the fix is currently going through the release process and RC1 is available for testing and voting - see http://mail-archives.apache.org/mod_mbox/kafka-users/201901.mbox/%3C67fc2ed5-0cc3-4fc6-8e14-ba562f6e4c56@www.fastmail.com%3E
~~~~

7.

~~~~
Also hit this bug after upgrading from 2.0.0 to 2.1.0.
~~~~

8.

~~~~
Is there anything that can be done as a workaround for this issue in the mean time? Any configuration that can be changed?

WIll a restart of all Kafka brokers help?
~~~~

9.

~~~~
[~shaharmor] Apache Kafka 2.1.1 containing the fix has been released. So an upgrade is recommended. With 2.1.0, you will need to restart affected brokers whenever they run into the issue.
~~~~

10.

~~~~
2.1.1 has other issues.   I'd recommend proceeding with caution.   Had to downgrade all of our clusters back to 2.0.1 to get stable.
~~~~

11.

~~~~
What issues [~jnadler]?
~~~~

12.

~~~~
We also hit the same issue. Had to restart the broker after almost every 6 hours!

[~jnadler] what is the issue with 2.1.1 ? We are planning to move to this version.. 

[~rsivaram] Shall we move to 2.0.1 since 2.1.1 is just released and we might hit other issues? 2.0.1 seems pretty stable!
~~~~

13.

~~~~
we also hit the same issue with 2.1.1 !

Get the metric "kafka.network:type=RequestChannel,name=RequestQueueSize" value is always 1000, and we config queued.max.requests=1000

 

kafka-network-thread-5-ListenerName(PLAINTEXT)-PLAINTEXT-4" #97 prio=5 os_prio=0 tid=0x00007fb7ce0ba800 nid=0x2d5 waiting on condition [0x00007fad6e5f8000]
 java.lang.Thread.State: WAITING (parking)
 at sun.misc.Unsafe.park(Native Method)
 - parking to wait for <0x00000004530783a0> (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject)
 at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
 at java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject.await(AbstractQueuedSynchronizer.java:2039)
 at java.util.concurrent.ArrayBlockingQueue.put(ArrayBlockingQueue.java:353)
 at kafka.network.RequestChannel.sendRequest(RequestChannel.scala:310)
 at kafka.network.Processor.$anonfun$processCompletedReceives$1(SocketServer.scala:709)
 at kafka.network.Processor.$anonfun$processCompletedReceives$1$adapted(SocketServer.scala:699)
 at kafka.network.Processor$$Lambda$877/855310793.apply(Unknown Source)
 at scala.collection.Iterator.foreach(Iterator.scala:937)
 at scala.collection.Iterator.foreach$(Iterator.scala:937)
 at scala.collection.AbstractIterator.foreach(Iterator.scala:1425)
 at scala.collection.IterableLike.foreach(IterableLike.scala:70)
 at scala.collection.IterableLike.foreach$(IterableLike.scala:69)
 at scala.collection.AbstractIterable.foreach(Iterable.scala:54)
 at kafka.network.Processor.processCompletedReceives(SocketServer.scala:699)
 at kafka.network.Processor.run(SocketServer.scala:595)
 at java.lang.Thread.run(Thread.java:748)

Locked ownable synchronizers:
 - None

 

"kafka-request-handler-15" #87 daemon prio=5 os_prio=0 tid=0x00007fb7ceee6800 nid=0x2cb waiting on condition [0x00007fad71af4000]
 java.lang.Thread.State: WAITING (parking)
 at sun.misc.Unsafe.park(Native Method)
 - parking to wait for <0x00000004540423f0> (a java.util.concurrent.locks.ReentrantReadWriteLock$NonfairSync)
 at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
 at java.util.concurrent.locks.AbstractQueuedSynchronizer.parkAndCheckInterrupt(AbstractQueuedSynchronizer.java:836)
 at java.util.concurrent.locks.AbstractQueuedSynchronizer.doAcquireShared(AbstractQueuedSynchronizer.java:967)
 at java.util.concurrent.locks.AbstractQueuedSynchronizer.acquireShared(AbstractQueuedSynchronizer.java:1283)
 at java.util.concurrent.locks.ReentrantReadWriteLock$ReadLock.lock(ReentrantReadWriteLock.java:727)
 at kafka.utils.CoreUtils$.inLock(CoreUtils.scala:249)
 at kafka.utils.CoreUtils$.inReadLock(CoreUtils.scala:257)
 at kafka.cluster.Partition.appendRecordsToLeader(Partition.scala:729)
 at kafka.server.ReplicaManager.$anonfun$appendToLocalLog$2(ReplicaManager.scala:735)
 at kafka.server.ReplicaManager$$Lambda$1567/915411568.apply(Unknown Source)
 at scala.collection.TraversableLike.$anonfun$map$1(TraversableLike.scala:233)
 at scala.collection.TraversableLike$$Lambda$12/811760110.apply(Unknown Source)
 at scala.collection.immutable.Map$Map1.foreach(Map.scala:125)
 at scala.collection.TraversableLike.map(TraversableLike.scala:233)
 at scala.collection.TraversableLike.map$(TraversableLike.scala:226)
 at scala.collection.AbstractTraversable.map(Traversable.scala:104)
 at kafka.server.ReplicaManager.appendToLocalLog(ReplicaManager.scala:723)
 at kafka.server.ReplicaManager.appendRecords(ReplicaManager.scala:470)
 at kafka.coordinator.group.GroupMetadataManager.appendForGroup(GroupMetadataManager.scala:280)
 at kafka.coordinator.group.GroupMetadataManager.storeOffsets(GroupMetadataManager.scala:423)
 at kafka.coordinator.group.GroupCoordinator.$anonfun$doCommitOffsets$1(GroupCoordinator.scala:518)
 at kafka.coordinator.group.GroupCoordinator$$Lambda$1816/513285617.apply$mcV$sp(Unknown Source)
 at scala.runtime.java8.JFunction0$mcV$sp.apply(JFunction0$mcV$sp.java:12)
 at kafka.utils.CoreUtils$.inLock(CoreUtils.scala:251)
 at kafka.coordinator.group.GroupMetadata.inLock(GroupMetadata.scala:197)
 at kafka.coordinator.group.GroupCoordinator.doCommitOffsets(GroupCoordinator.scala:503)
 at kafka.coordinator.group.GroupCoordinator.handleCommitOffsets(GroupCoordinator.scala:482)
 at kafka.server.KafkaApis.handleOffsetCommitRequest(KafkaApis.scala:365)
 at kafka.server.KafkaApis.handle(KafkaApis.scala:114)
 at kafka.server.KafkaRequestHandler.run(KafkaRequestHandler.scala:69)
 at java.lang.Thread.run(Thread.java:748)

Locked ownable synchronizers:
 - <0x0000000794ea4248> (a java.util.concurrent.locks.ReentrantLock$NonfairSync)    
 - 
 - 

 

The thread dumps of a broker: [^kafka_jstack.txt]

 
~~~~

14.

~~~~
[~little brother ma]  wo also hit the same issue with 2.1.1 .I checked the source code for version 2.1.1 and found that partition. Scala did not incorporate the changes
~~~~

15.

~~~~
[~rsivaram] We also encountered the same problem，and controller-event-thread looks like deadlock.
Newly created topic which isr and leader is none，the topicChangeListener can not work
~~~~

16.

~~~~
[~little brother ma] [~boge] [~yanrui] Can you provide full thread dumps of a broker that encountered this issue with 2.1.1? Thank you!
~~~~

17.

~~~~
Currently experiencing this on Kafka 2.1.0, happen to have a thread dump handy if it's useful! We're noticing it occur seemingly randomly, however partition reassignment and heavy produce bursts seem to exacerbate this issue. kill -9 has been the only solution for us thus far, tons of open file descriptors start to accumulate.

[^kafka.log]
~~~~

18.

~~~~
[~rsivaram]  We also encountered the same issue with 2.1.0 in our production stack.

Below is the sample stack trace. If we want to up grade/down grade Kafka in our setup, which version we can go.

kafka-request-handler-3 tid=53 [WAITING] [DAEMON]
java.util.concurrent.locks.ReentrantReadWriteLock$ReadLock.lock() ReentrantReadWriteLock.java:727
kafka.utils.CoreUtils$.inLock(Lock, Function0) CoreUtils.scala:249
kafka.utils.CoreUtils$.inReadLock(ReadWriteLock, Function0) CoreUtils.scala:257
kafka.cluster.Partition.fetchOffsetSnapshot(Optional, boolean) Partition.scala:832
kafka.server.DelayedFetch.$anonfun$tryComplete$1(DelayedFetch, IntRef, Object, Tuple2) DelayedFetch.scala:87
kafka.server.DelayedFetch.$anonfun$tryComplete$1$adapted(DelayedFetch, IntRef, Object, Tuple2) DelayedFetch.scala:79
kafka.server.DelayedFetch$$Lambda$969.apply(Object)
scala.collection.mutable.ResizableArray.foreach(Function1) ResizableArray.scala:58
scala.collection.mutable.ResizableArray.foreach$(ResizableArray, Function1) ResizableArray.scala:51
scala.collection.mutable.ArrayBuffer.foreach(Function1) ArrayBuffer.scala:47
kafka.server.DelayedFetch.tryComplete() DelayedFetch.scala:79
kafka.server.DelayedOperation.maybeTryComplete() DelayedOperation.scala:121
kafka.server.DelayedOperationPurgatory$Watchers.tryCompleteWatched() DelayedOperation.scala:371
kafka.server.DelayedOperationPurgatory.checkAndComplete(Object) DelayedOperation.scala:277
kafka.server.ReplicaManager.tryCompleteDelayedFetch(DelayedOperationKey) ReplicaManager.scala:307
kafka.cluster.Partition.$anonfun$appendRecordsToLeader$1(Partition, MemoryRecords, boolean, int) Partition.scala:743
kafka.cluster.Partition$$Lambda$856.apply()
kafka.utils.CoreUtils$.inLock(Lock, Function0) CoreUtils.scala:251
kafka.utils.CoreUtils$.inReadLock(ReadWriteLock, Function0) CoreUtils.scala:257
kafka.cluster.Partition.appendRecordsToLeader(MemoryRecords, boolean, int) Partition.scala:729
kafka.server.ReplicaManager.$anonfun$appendToLocalLog$2(ReplicaManager, boolean, boolean, short, Tuple2) ReplicaManager.scala:735
kafka.server.ReplicaManager$$Lambda$844.apply(Object)
scala.collection.TraversableLike.$anonfun$map$1(Function1, Builder, Object) TraversableLike.scala:233
scala.collection.TraversableLike$$Lambda$10.apply(Object)
scala.collection.mutable.HashMap.$anonfun$foreach$1(Function1, DefaultEntry) HashMap.scala:145
scala.collection.mutable.HashMap$$Lambda$22.apply(Object)
scala.collection.mutable.HashTable.foreachEntry(Function1) HashTable.scala:235
scala.collection.mutable.HashTable.foreachEntry$(HashTable, Function1) HashTable.scala:228
scala.collection.mutable.HashMap.foreachEntry(Function1) HashMap.scala:40
scala.collection.mutable.HashMap.foreach(Function1) HashMap.scala:145
scala.collection.TraversableLike.map(Function1, CanBuildFrom) TraversableLike.scala:233
scala.collection.TraversableLike.map$(TraversableLike, Function1, CanBuildFrom) TraversableLike.scala:226
scala.collection.AbstractTraversable.map(Function1, CanBuildFrom) Traversable.scala:104
kafka.server.ReplicaManager.appendToLocalLog(boolean, boolean, Map, short) ReplicaManager.scala:723
kafka.server.ReplicaManager.appendRecords(long, short, boolean, boolean, Map, Function1, Option, Function1) ReplicaManager.scala:470
kafka.server.KafkaApis.handleProduceRequest(RequestChannel$Request) KafkaApis.scala:482
kafka.server.KafkaApis.handle(RequestChannel$Request) KafkaApis.scala:106
kafka.server.KafkaRequestHandler.run() KafkaRequestHandler.scala:69
java.lang.Thread.run() Thread.java:748

-Murthy
~~~~

19.

~~~~
[~jwesteen] [~nsnmurthy] Thank you! The deadlock was fixed in 2.2.0 and 2.1.1. We are keen to see if there are other similar issues still remaining in these two releases, so that we can fix them before the next release. If experiencing this issue in 2.1.0, please upgrade to 2.1.1.
~~~~

20.

~~~~
[~rsivaram]
I have put file called kafka_jstack.txt  which contain full thread dumps of a broker that encountered this issue with 2.1.1 in the attachment
~~~~

21.

~~~~
[~rsivaram]This problem usually occurs with kafka and zk broken chains，it seems to be this situation triggers a lot of write lock operations and the write lock is not released at the end.
~~~~

22.

~~~~
 use 2.1.1 kafka which deadlock happen  a moment ago，I have put file  called 322.tdump  in the attachment
~~~~

23.

~~~~
[~yanrui] Thanks for the thread dumps. It looks like kafka_jstack.txt was using an older release (not 2.1.1, perhaps 2.1.0 or earlier) since it doesn't seem to have the fix for this Jira. Can you confirm that?

322.dump shows the issue described in KAFKA-8151 for 2.1.1 due to ZK session expiry.  As a workaround, you can increase ZK session timeouts for the broker until KAFKA-8151 is fixed if you are regularly running into this issue. It will be good to know if you see the issue with 2.2.0 if you are able to recreate. Thanks.
~~~~

24.

~~~~
[~rsivaram]Thank you very much, let me increase this parameters and try it for a few days
~~~~

25.

~~~~
[~rsivaram] The problem was fixed after the upgrade 2.1.1, but there was a new problem.I'm not sure if the two questions are related, but the logs they print when the problem occurs are similar.
A similar broker hangs was encountered in 2.1.1 . the problem cause broker crash in 2.1.0, but will automatically recovered in a few minutes in 2.1.1, and the cluster was unavailable during this time. 
I uploaded a log whose file name is 2.1.1-hangs.log  [^2.1.1-hangs.log] . When we find and log in to the server, the cluster was restored. All the stack information has not yet been obtained, but we can see that there is a problem from the logs of the broker and consumer. Could you give me some help,Thank you !
~~~~

26.

~~~~
[~muchl] This Jira addressed the deadlock which is fixed in 2.1.1. There is a separate Jira  to reduce lock contention (https://issues.apache.org/jira/browse/KAFKA-7538) which could be the issue you ran into in 2.1.1.
~~~~

27.

~~~~
[~rsivaram] Thank you very much.
[KAFKA-7538 | https://issues.apache.org/jira/browse/KAFKA-7538] This seems to be the problem I encountered.I will focus on the KAFKA-7538.

~~~~

28.

~~~~
Is it possible to overcome this issue by simply increasing the number of threads?

Maybe using num.io.threads or num.network.threads?
~~~~

29.

~~~~
Does increasing num.network.threads help improve the performance when kafka has high load in terms of more no. of producer/consumer requests?
~~~~

---

## KAFKA-7755: Kubernetes - Kafka clients are resolving DNS entries only one time

https://issues.apache.org/jira/browse/KAFKA-7755

Given fix versions: 2.1.1, 2.2.0
JIRA affects (masked from the system): 2.1.0

- `KAFKA-7755@2.1.0`: config 2.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-7755@2.0.1`: config 2.0.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.1.0, 2.1

### Description

~~~~
*Introduction*
 Since 2.1.0 Kafka clients are supporting multiple DNS resolved IP addresses if the first one fails. This change has been introduced by https://issues.apache.org/jira/browse/KAFKA-6863. However this DNS resolution is now performed only one time by the clients. This is not a problem if all brokers have fixed IP addresses, however this is definitely an issue when Kafka brokers are run on top of Kubernetes. Indeed, new Kubernetes pods will receive another IP address, so as soon as all brokers will have been restarted clients won't be able to reconnect to any broker.

*Impact*
 Everyone running Kafka 2.1 or later on top of Kubernetes is impacted when a rolling restart is performed.

*Root cause*
 Since https://issues.apache.org/jira/browse/KAFKA-6863 Kafka clients are resolving DNS entries only once.

*Proposed solution*
 In [https://github.com/apache/kafka/blob/trunk/clients/src/main/java/org/apache/kafka/clients/ClusterConnectionStates.java#L368] Kafka clients should perform the DNS resolution again when all IP addresses have been "used" (when _index_ is back to 0)
~~~~

### Comments (2)

1.

~~~~
(U) Is there anything about this issue and its fix that makes it specific to only Kubernetes? Or would this issue, and this fix, be applicable in any environment where the IP addresses backing the DNS hostname for brokers changes over time? Would this be expected to apply equally to an AWS environment where a DNS hostname such as broker1 in Route 53 is updated to point to a newly-launched EC2 instance when the previous EC2 instance died due to hardware failure?
~~~~

2.

~~~~
@Tim: This is not only specific to Kubernetes, but, as you suggested, this is affecting all environments where IP addresses of Kafka broker are changed at some time
~~~~

---

## KAFKA-7958: Transactions are broken with kubernetes hosted brokers

https://issues.apache.org/jira/browse/KAFKA-7958

Given fix versions: 2.1.1
JIRA affects (masked from the system): 2.1.0

- `KAFKA-7958@2.1.0`: config 2.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-7958@2.0.1`: config 2.0.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.1.1, 2.2.1

### Description

~~~~
After a rolling re-start in a kubernetes-like environment, brokers may change IP address.  From our logs it seems that the transaction manager in the brokers never re-resolves the DNS name of other brokers, keeping stale pod IPs.  Thus transactions stop working.  

??[2019-02-20 02:20:20,085] WARN [TransactionCoordinator id=1001] Connection to node 0 (khaki-joey-kafka-0.khaki-joey-kafka-headless.hyperspace-dev/[10.233.124.181:9092|http://10.233.124.181:9092/]) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)??

??[2019-02-20 02:20:57,205] WARN [TransactionCoordinator id=1001] Connection to node 1 (khaki-joey-kafka-1.khaki-joey-kafka-headless.hyperspace-dev/[10.233.122.67:9092|http://10.233.122.67:9092/]) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)??

This is from the log from broker 1001 which was restarted first, followed by 1 and then 0.  The log entries are from the day after the rolling restart.

I note a similar issue was fixed for clients 2.1.1  https://issues.apache.org/jira/browse/KAFKA-7755.  We are using streams lib 2.1.1

*Update* We are now testing with Kafka 2.1.1 (docker cp-kafka 5.1.2-1) and it looks like this may be resolved.  Would be good to get confirmation though.
~~~~

### Comments (2)

1.

~~~~
Yes, there were a couple of issues related to DNS refresh that were fixed in 2.1.1.
~~~~

2.

~~~~
_"Would be good to get confirmation though.":_ confirm the fix for https://issues.apache.org/jira/browse/KAFKA-7755 fixes the problem in the transaction manager. Tested on 2.2.1.
~~~~

---

## KAFKA-8069: Committed offsets get cleaned up right after the coordinator loading them back from __consumer_offsets in broker with old inter-broker protocol version (< 2.2)

https://issues.apache.org/jira/browse/KAFKA-8069

Given fix versions: 2.0.2, 2.1.2, 2.2.0
JIRA affects (masked from the system): 2.1.0, 2.1.1, 2.1.2, 2.2.0, 2.2.1

- `KAFKA-8069@2.1.0`: config 2.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-8069@2.0.1`: config 2.0.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.2, 2.1, 0.11, 2.2.0, 2.0

### Description

~~~~
After the 2.1 release, if the broker hasn't been upgrade to the latest inter-broker protocol version, 
the committed offsets stored in the __consumer_offset topic will get cleaned up way earlier than it should be when the offsets are loaded back from the __consumer_offset topic in GroupCoordinator, which will happen during leadership transition or after broker bounce.

TL;DR
For V1 on-disk format for __consumer_offsets, we have the *expireTimestamp* field and if the inter-broker protocol (IBP) version is prior to 2.1 (prior to [KIP-211|https://cwiki.apache.org/confluence/display/KAFKA/KIP-211%3A+Revise+Expiration+Semantics+of+Consumer+Group+Offsets]) for a kafka 2.1 broker, the logic of getting the expired offsets looks like:
{code:java}
def getExpiredOffsets(baseTimestamp: CommitRecordMetadataAndOffset => Long): Map[TopicPartition, OffsetAndMetadata] = {
 offsets.filter {
 case (topicPartition, commitRecordMetadataAndOffset) =>
 ... && {
 commitRecordMetadataAndOffset.offsetAndMetadata.expireTimestamp match {
 case None =>
 // current version with no per partition retention
 currentTimestamp - baseTimestamp(commitRecordMetadataAndOffset) >= offsetRetentionMs
 case Some(expireTimestamp) =>
 // older versions with explicit expire_timestamp field => old expiration semantics is used
 currentTimestamp >= expireTimestamp
 }
 }
 }....
 }
{code}
The expireTimestamp in the on-disk offset record can only be set when storing the committed offset in the __consumer_offset topic. But the GroupCoordinator also has keep a in-memory representation for the expireTimestamp (see the codes above), which can be set in the following two cases:
 # Upon the GroupCoordinator receiving OffsetCommitRequest, the expireTimestamp is set using the following logic:
{code:java}
expireTimestamp = offsetCommitRequest.retentionTime match {
 case OffsetCommitRequest.DEFAULT_RETENTION_TIME => None
 case retentionTime => Some(currentTimestamp + retentionTime)
}
{code}
In all the latest client versions, the consumer will set out OffsetCommitRequest with DEFAULT_RETENTION_TIME so the expireTimestamp will always be None in this case. *This means any committed offset set in this case will always hit the "case None" in the "getExpiredOffsets(...)" when coordinator is doing the cleanup, which is correct.*

 # Upon the GroupCoordinatorReceiving loading the committed offset stored in the __consumer_offsets topic from disk, the expireTimestamp is set using the following logic if IBP<2.1:
{code:java}
val expireTimestamp = value.get(OFFSET_VALUE_EXPIRE_TIMESTAMP_FIELD_V1).asInstanceOf[Long]
{code}
and the logic to persist the expireTimestamp is:
{code:java}
// OffsetCommitRequest.DEFAULT_TIMESTAMP = -1
value.set(OFFSET_VALUE_EXPIRE_TIMESTAMP_FIELD_V1, offsetAndMetadata.expireTimestamp.getOrElse(OffsetCommitRequest.DEFAULT_TIMESTAMP))
{code}
Since the in-memory expireTimestamp will always be None in our case as mentioned in 1), we will always store -1 on-disk. Therefore, when the offset is loaded from the __consumer_offsets topic, the in-memory expireTimestamp will always be set to -1. *This means any committed offset set in this case will always hit "case Some(expireTimestamp)" in the "getExpiredOffsets(...)" when coordinator is doing the cleanup, which basically indicates we will always expire the committed offset on the first expiration check (which is shortly after they are loaded from __consumer_offsets topic)*.

I am able to reproduce this bug on my local box with one broker using 2.*,1.* and 0.11.* consumer. The consumer will see null committed offset after the broker is bounced.

This bug is introduced by [PR-5690|https://github.com/apache/kafka/pull/5690] in the kafka 2.1 release and the fix is very straight-forward, which is basically set the expireTimestamp to None if it is -1 in the on-disk format.
~~~~

### Comments (5)

1.

~~~~
[~hzxa21] are you planning to submit a PR?
~~~~

2.

~~~~
[~mjsax] I think this is a blocker for 2.2.0. What do you think?
~~~~

3.

~~~~
Great find and thanks for the detailed summary. I was able to confirm this on trunk. The only requirement is a 2.1+ broker with IBP set to an old version. I did the following:
 # Start up the broker with IBP set to 2.0
 # Start up a console consumer (on trunk) and verify it commits offsets
 # Stop the consumer
 # Restart the broker

We see the following in the logs:
{code:java}
[2019-03-07 22:49:25,774] DEBUG [GroupMetadataManager brokerId=0] Loaded group metadata GroupMetadata(groupId=blah, generation=4, protocolType=Some(consumer), currentState=Empty, members=Map()) with offsets Map(foo-0 -> CommitRecordMetadataAndOffset(Some(12),OffsetAndMetadata(offset=1, leaderEpoch=Optional.empty, metadata=, commitTimestamp=1552027741320, expireTimestamp=Some(-1)))) and pending offsets Map() (kafka.coordinator.group.GroupMetadataManager)                                            {code}
The key is `*expireTimestamp=Some(-1)*`. Shortly after I see the coordinator expiring the offset.
~~~~

4.

~~~~
[~mjsax] [~hachikuji], is this critical enough that we will spin a new RC for 2.2.0?
~~~~

5.

~~~~
Yes. I just marked it as a blocker. Will do a new RC.
~~~~

---

## KAFKA-8104: Consumer cannot rejoin to the group after rebalancing

https://issues.apache.org/jira/browse/KAFKA-8104

Given fix versions: 2.4.0
JIRA affects (masked from the system): 2.0.0, 2.1.0, 2.2.0, 2.3.0

- `KAFKA-8104@2.3.0`: config 2.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-8104@1.1.1`: config 1.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.3, 1.1.1, 2.2.0, 1.1.0

### Description

~~~~
TL;DR; {{KafkaConsumer}} cannot rejoin to the group due to inconsistent {{AbstractCoordinator.generation}} (which is {{NO_GENERATION}} and {{AbstractCoordinator.joinFuture}} (which is succeeded {{RequestFuture}}). See explanation below.

There are 16 consumers in single process (threads from pool-4-thread-1 to pool-4-thread-16). All of them belong to single consumer group {{hercules.sink.elastic.legacy_logs_elk_c2}}. Rebalancing has been acquired and consumers have got {{CommitFailedException}} as expected:

{noformat}
2019-03-10T03:16:37.023Z [pool-4-thread-10] WARN  r.k.vostok.hercules.sink.SimpleSink - Commit failed due to rebalancing
org.apache.kafka.clients.consumer.CommitFailedException: Commit cannot be completed since the group has already rebalanced and assigned the partitions to another member. This means that the time between subsequent calls to poll() was longer than the configured max.poll.interval.ms, which typically implies that the poll loop is spending too much time message processing. You can address this either by increasing the session timeout or by reducing the maximum size of batches returned in poll() with max.poll.records.
	at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.sendOffsetCommitRequest(ConsumerCoordinator.java:798)
	at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.commitOffsetsSync(ConsumerCoordinator.java:681)
	at org.apache.kafka.clients.consumer.KafkaConsumer.commitSync(KafkaConsumer.java:1334)
	at org.apache.kafka.clients.consumer.KafkaConsumer.commitSync(KafkaConsumer.java:1298)
	at ru.kontur.vostok.hercules.sink.Sink.commit(Sink.java:156)
	at ru.kontur.vostok.hercules.sink.SimpleSink.run(SimpleSink.java:104)
	at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
	at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
	at java.lang.Thread.run(Thread.java:748)
{noformat}

After that, most of them successfully rejoined to the group with generation 10699:
{noformat}
2019-03-10T03:16:39.208Z [pool-4-thread-13] INFO  o.a.k.c.c.i.AbstractCoordinator - [Consumer clientId=consumer-13, groupId=hercules.sink.elastic.legacy_logs_elk_c2] Successfully joined group with generation 10699
2019-03-10T03:16:39.209Z [pool-4-thread-13] INFO  o.a.k.c.c.i.ConsumerCoordinator - [Consumer clientId=consumer-13, groupId=hercules.sink.elastic.legacy_logs_elk_c2] Setting newly assigned partitions [legacy_logs_elk_c2-18]
...
2019-03-10T03:16:39.216Z [pool-4-thread-11] INFO  o.a.k.c.c.i.AbstractCoordinator - [Consumer clientId=consumer-11, groupId=hercules.sink.elastic.legacy_logs_elk_c2] Successfully joined group with generation 10699
2019-03-10T03:16:39.217Z [pool-4-thread-11] INFO  o.a.k.c.c.i.ConsumerCoordinator - [Consumer clientId=consumer-11, groupId=hercules.sink.elastic.legacy_logs_elk_c2] Setting newly assigned partitions [legacy_logs_elk_c2-10, legacy_logs_elk_c2-11]
...
2019-03-10T03:16:39.218Z [pool-4-thread-15] INFO  o.a.k.c.c.i.ConsumerCoordinator - [Consumer clientId=consumer-15, groupId=hercules.sink.elastic.legacy_logs_elk_c2] Setting newly assigned partitions [legacy_logs_elk_c2-24]
2019-03-10T03:16:42.320Z [kafka-coordinator-heartbeat-thread | hercules.sink.elastic.legacy_logs_elk_c2] INFO  o.a.k.c.c.i.AbstractCoordinator - [Consumer clientId=consumer-6, groupId=hercules.sink.elastic.legacy_logs_elk_c2] Attempt to heartbeat failed since group is rebalancing
2019-03-10T03:16:42.320Z [kafka-coordinator-heartbeat-thread | hercules.sink.elastic.legacy_logs_elk_c2] INFO  o.a.k.c.c.i.AbstractCoordinator - [Consumer clientId=consumer-5, groupId=hercules.sink.elastic.legacy_logs_elk_c2] Attempt to heartbeat failed since group is rebalancing
2019-03-10T03:16:42.323Z [kafka-coordinator-heartbeat-thread | hercules.sink.elastic.legacy_logs_elk_c2] INFO  o.a.k.c.c.i.AbstractCoordinator - [Consumer clientId=consumer-7, groupId=hercules.sink.elastic.legacy_logs_elk_c2] Attempt to heartbeat failed since group is rebalancing
2019-03-10T03:17:13.235Z [pool-4-thread-4] INFO  o.a.k.c.c.i.AbstractCoordinator - [Consumer clientId=consumer-4, groupId=hercules.sink.elastic.legacy_logs_elk_c2] Successfully joined group with generation -1

{noformat}


But one consumer (pool-4-thread-4) got strange generation -1 (see last log record from above).
Further log records in attached log file.

Finally, 15 consumers successfully rejoined. But consumer with thread {{pool-4-thread-4}} didn't rejoin:

{noformat}
2019-03-10T03:17:13.355Z [pool-4-thread-4] ERROR r.k.vostok.hercules.sink.SimpleSink - Unspecified exception has been acquired
java.lang.IllegalStateException: Coordinator selected invalid assignment protocol: null
	at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.onJoinComplete(ConsumerCoordinator.java:241)
	at org.apache.kafka.clients.consumer.internals.AbstractCoordinator.joinGroupIfNeeded(AbstractCoordinator.java:422)
	at org.apache.kafka.clients.consumer.internals.AbstractCoordinator.ensureActiveGroup(AbstractCoordinator.java:352)
	at org.apache.kafka.clients.consumer.internals.AbstractCoordinator.ensureActiveGroup(AbstractCoordinator.java:337)
	at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.poll(ConsumerCoordinator.java:333)
	at org.apache.kafka.clients.consumer.KafkaConsumer.updateAssignmentMetadataIfNeeded(KafkaConsumer.java:1218)
	at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:1175)
	at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:1154)
	at ru.kontur.vostok.hercules.sink.Sink.poll(Sink.java:152)
	at ru.kontur.vostok.hercules.sink.SimpleSink.run(SimpleSink.java:70)
	at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
	at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
	at java.lang.Thread.run(Thread.java:748)
2019-03-10T03:17:13.360Z [pool-4-thread-4] ERROR r.k.vostok.hercules.sink.SimpleSink - Unspecified exception has been acquired
java.lang.IllegalStateException: Coordinator selected invalid assignment protocol: null
	at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.onJoinComplete(ConsumerCoordinator.java:241)
	at org.apache.kafka.clients.consumer.internals.AbstractCoordinator.joinGroupIfNeeded(AbstractCoordinator.java:422)
	at org.apache.kafka.clients.consumer.internals.AbstractCoordinator.ensureActiveGroup(AbstractCoordinator.java:352)
	at org.apache.kafka.clients.consumer.internals.AbstractCoordinator.ensureActiveGroup(AbstractCoordinator.java:337)
	at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.poll(ConsumerCoordinator.java:333)
	at org.apache.kafka.clients.consumer.KafkaConsumer.updateAssignmentMetadataIfNeeded(KafkaConsumer.java:1218)
	at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:1175)
	at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:1154)
	at ru.kontur.vostok.hercules.sink.Sink.poll(Sink.java:152)
	at ru.kontur.vostok.hercules.sink.SimpleSink.run(SimpleSink.java:70)
	at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
	at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
	at java.lang.Thread.run(Thread.java:748)}}
{noformat}

It is important to note, that {{KafkaConsumer.coordinator.joinFuture}} is not null and succeeded, but {{ConsumerCoordinator}} cannot perform {{resetJoinGroupFuture()}} due to exception was thrown from {{onJoinComplete()}}:
{code:java}
            if (future.succeeded()) {
                // Duplicate the buffer in case `onJoinComplete` does not complete and needs to be retried.
                ByteBuffer memberAssignment = future.value().duplicate();
                onJoinComplete(generation.generationId, generation.memberId, generation.protocol, memberAssignment);

                // We reset the join group future only after the completion callback returns. This ensures
                // that if the callback is woken up, we will retry it on the next joinGroupIfNeeded.
                resetJoinGroupFuture();
                needsJoinPrepare = true;
            }
{code}

If I understood correctly, the generation was changed to {{NO_GENERATION}} in another thread by one of CoordinatorResponseHandlers.
 
 [^consumer-rejoin-fail.log] 
~~~~

### Comments (10)

1.

~~~~
It also happens with version 2.3 of the client
~~~~

2.

~~~~
[~mbarbon] [~kgn] do you have any broker-side logs around the time this happens that can be shared on this ticket as well?
~~~~

3.

~~~~
[~guozhang], I found server.log (there are 3 brokers, but only one of them has relevant log entries in log):

{code}
[2019-03-10 02:46:43,627] INFO [GroupCoordinator 2]: Stabilized group hercules.sink.elastic.legacy_logs_elk_c2 generation 10693 (__consumer_offsets-25) (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:43,630] INFO [GroupCoordinator 2]: Assignment received from leader for group hercules.sink.elastic.legacy_logs_elk_c2 for generation 10693 (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:45,397] INFO [GroupCoordinator 2]: Preparing to rebalance group hercules.sink.elastic.legacy_logs_elk_c2 with old generation 10693 (__consumer_offsets-25) (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,628] INFO [GroupCoordinator 2]: Member consumer-7-cc600ccb-72b6-4582-b288-3ea966f33c7c in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,628] INFO [GroupCoordinator 2]: Member consumer-1-f284c5c8-22fc-40d5-aa30-46c2875463bd in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,628] INFO [GroupCoordinator 2]: Member consumer-5-e608adfc-e9ad-427e-99b5-99ff1538611d in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,628] INFO [GroupCoordinator 2]: Member consumer-6-daa568cc-a5ee-49a9-aa7c-bd34fbb1da52 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,628] INFO [GroupCoordinator 2]: Member consumer-2-da70d65b-53e6-4467-b06d-63f02ff89eec in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,628] INFO [GroupCoordinator 2]: Member consumer-12-a0cb16ff-46eb-4945-a87a-244a20261af9 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,628] INFO [GroupCoordinator 2]: Member consumer-10-c10cb15d-edc3-4c6a-b21a-68e2b8298284 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,628] INFO [GroupCoordinator 2]: Member consumer-16-d80c8a16-be83-48f3-ac9d-08431b87c198 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,628] INFO [GroupCoordinator 2]: Member consumer-5-75899722-91a9-439a-a0c5-f23eb7c6c93f in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,628] INFO [GroupCoordinator 2]: Member consumer-11-14fe64e9-1553-49e1-abf9-5ea623847c84 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,628] INFO [GroupCoordinator 2]: Member consumer-3-9b62bde0-ff71-46f7-b6a4-7be14e6055b5 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-14-42336dad-be7c-49da-a76b-72d13a856943 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-6-1d57e91e-a6cd-4917-9560-19fa6579d02e in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-13-a310873e-5c66-402c-a031-0b2fce8eb4cc in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-1-7c591ed8-01d8-4f2c-b756-a5c3d3f63eea in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-7-70c381bc-5d32-4e2c-923b-2c15c0f15aa2 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-15-5de2a785-0cd8-43f8-b3e2-6b1da2983910 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-10-92f6d7a8-cc6c-4091-9eb4-1a8be9a08541 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-5-bd971902-bea5-49ef-83f6-3788e7363924 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-11-18b7fff3-f477-44c8-bece-4bde079bb578 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-2-bb9ff074-6738-4092-a2c0-f3d49e5e7e2a in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-9-ef6b36b3-376f-4a04-a0cb-709c8a28712b in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-13-57c73f24-4e8d-407e-874b-ab95409f7b1c in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-10-265e41ea-c8c3-47f2-96d2-33309f975f29 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-15-f3ea2d41-09df-454a-a13b-c2007e0bff32 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-11-dcbc5baf-b7e4-433f-9580-b5e846418748 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-14-3cfd686d-e590-4055-9c8c-70f673a0a624 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-8-43d4c7af-a8f5-4616-8346-33bed246a253 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-11-bf244902-001f-460c-8cf5-e9ac5e7cb4a6 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-10-74f336ca-6a0f-4603-b93a-fcee81953f9f in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-1-65fe1595-6bff-4506-8a9b-6f35f3663f48 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-16-470b7eb9-942d-48fa-b8c1-d128ae21900d in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,629] INFO [GroupCoordinator 2]: Member consumer-2-d587e29f-4d7e-4234-a774-21813af82415 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-7-a1fbd1a5-a4a8-42a8-bf7e-d6742edb8003 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-16-47eaa6a5-1fe9-4216-8afa-aaa5a7684755 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-10-1cba9737-26c2-4879-82c7-d3ef6399a2b3 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-13-b4031cae-43c3-45a4-b258-b9cfe2645eb6 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-3-e23f1744-7781-4e09-b394-6e3a09a5ed6d in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-4-59459730-4118-4379-a208-83bfba9a751e in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-9-4291927f-119f-4610-bd00-f9503847ff05 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-6-b8d722e7-58d3-4e2f-af03-92ab01e23f8d in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-14-b2504ede-535c-4884-aea5-03734661bb4d in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-6-afb90678-4548-4a23-bbbb-3ce2ffb6b59c in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-15-ecd3673c-c585-4fab-98ae-b14f5583e59d in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-7-d534cf40-ecf6-4cac-a823-c5bb7d515ffe in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-15-6c51bd3b-88c0-407a-a606-f21f8a16b22e in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-16-47e4622c-aea3-4a7f-b3c4-c4e88c553c63 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-13-6aef6aef-2fa7-4499-a138-8132f10662fd in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-1-d5563ddf-63dc-4308-b456-881b0f3bd64f in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-3-323295d3-d5b5-49f4-a364-18c681fcc534 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-3-494d66e9-5225-4673-8400-ebf1f96d5e5e in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-1-5035e670-86ff-4365-9be1-daf28bb85894 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-7-2bccc8ef-31f0-4974-8042-4721d60d0be4 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-13-e5e10c2d-28a2-4def-a5ec-2e33e3162c6c in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-4-b18fc59c-d2e0-474b-9eb7-76150001406a in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-1-c99e56c9-bd3b-4230-a3fa-c01ae0208333 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-13-c7331006-f001-4cee-b7f7-feb4be3db7e5 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-5-fcf52494-4825-43da-8b8f-622b69f19707 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-4-7f88af3b-bcc8-475c-84e0-e254871998b3 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-16-b5952574-6146-4f4f-9fb9-e5a1a0165296 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-3-0b751ea6-b228-489b-9679-381173ac7bb8 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-6-5f5ed961-0ac6-4463-8e2d-87a0d40de556 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-9-180c4643-92f2-4989-b807-b6a4f8ab4ac9 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-15-24048d2d-7442-4392-af17-b4a959e58bf7 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-5-6fc6f5b5-cd67-4cb6-a8fb-b4b4dd8fc2ea in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-8-9fca323f-e32d-4e4a-99eb-356557892607 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-3-3b403a81-75d5-44df-b9d5-c0accc173e67 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-15-dbd7b016-fb76-4ce0-be8e-753995fa701e in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-12-39204442-c071-46d5-8f5d-45a89dbe9426 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-11-dd4283b7-9226-496c-834e-4abfba06396c in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-2-f5f81416-0d70-4d44-86b4-cf834add0c5c in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,630] INFO [GroupCoordinator 2]: Member consumer-12-a889fd7d-edc8-4323-9aea-4e7c98f24e64 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,631] INFO [GroupCoordinator 2]: Member consumer-6-cbe5c48d-24ac-4aab-87a8-227c1292bffa in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,631] INFO [GroupCoordinator 2]: Member consumer-2-5e1893ac-76ee-495c-9624-ee06b8004565 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,631] INFO [GroupCoordinator 2]: Member consumer-5-3f0832ba-0b9e-4ff1-8e10-1ba9c61a7b67 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,631] INFO [GroupCoordinator 2]: Member consumer-8-ab32a5e0-4781-487c-8e8f-2a163d1437dd in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:46:53,631] INFO [GroupCoordinator 2]: Member consumer-7-4457a612-a996-43ed-95ee-9a0e1c9e5371 in group hercules.sink.elastic.legacy_logs_elk_c2 has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:47:00,306] INFO [GroupMetadataManager brokerId=2] Removed 0 expired offsets in 0 milliseconds. (kafka.coordinator.group.GroupMetadataManager)
[2019-03-10 02:47:09,911] WARN Attempting to send response via channel for which there is no open connection, connection id 10.0.3.151:9092-10.0.3.60:41792-1811027 (kafka.network.Processor)
[2019-03-10 02:47:15,431] INFO [GroupCoordinator 2]: Stabilized group hercules.sink.elastic.legacy_logs_elk_c2 generation 10694 (__consumer_offsets-25) (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:47:15,433] INFO [GroupCoordinator 2]: Preparing to rebalance group hercules.sink.elastic.legacy_logs_elk_c2 with old generation 10694 (__consumer_offsets-25) (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:47:15,436] INFO [GroupCoordinator 2]: Stabilized group hercules.sink.elastic.legacy_logs_elk_c2 generation 10695 (__consumer_offsets-25) (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:47:15,437] INFO [GroupCoordinator 2]: Assignment received from leader for group hercules.sink.elastic.legacy_logs_elk_c2 for generation 10695 (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:47:22,774] INFO [GroupCoordinator 2]: Preparing to rebalance group hercules.sink.elastic.legacy_logs_elk_c2 with old generation 10695 (__consumer_offsets-25) (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:47:42,111] INFO [GroupCoordinator 2]: Stabilized group hercules.sink.elastic.legacy_logs_elk_c2 generation 10696 (__consumer_offsets-25) (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:47:42,113] INFO [GroupCoordinator 2]: Assignment received from leader for group hercules.sink.elastic.legacy_logs_elk_c2 for generation 10696 (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:48:04,754] WARN Attempting to send response via channel for which there is no open connection, connection id 10.0.3.151:9092-10.0.3.60:43668-1811310 (kafka.network.Processor)
[2019-03-10 02:48:10,975] WARN Attempting to send response via channel for which there is no open connection, connection id 10.0.3.151:9092-10.0.3.153:56162-1811343 (kafka.network.Processor)
[2019-03-10 02:48:32,082] WARN Attempting to send response via channel for which there is no open connection, connection id 10.0.3.151:9092-10.0.3.60:44598-1811455 (kafka.network.Processor)
[2019-03-10 02:50:09,387] WARN Attempting to send response via channel for which there is no open connection, connection id 10.0.3.151:9092-10.0.3.60:48904-1811956 (kafka.network.Processor)
[2019-03-10 02:50:16,787] INFO [GroupCoordinator 2]: Preparing to rebalance group hercules.sink.elastic.legacy_logs_elk_c2 with old generation 10696 (__consumer_offsets-25) (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:50:22,630] INFO [GroupCoordinator 2]: Stabilized group hercules.sink.elastic.legacy_logs_elk_c2 generation 10697 (__consumer_offsets-25) (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:50:22,633] INFO [GroupCoordinator 2]: Assignment received from leader for group hercules.sink.elastic.legacy_logs_elk_c2 for generation 10697 (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:51:13,251] INFO [GroupCoordinator 2]: Preparing to rebalance group hercules.sink.elastic.legacy_logs_elk_c2 with old generation 10697 (__consumer_offsets-25) (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:51:13,967] INFO [GroupCoordinator 2]: Stabilized group hercules.sink.elastic.legacy_logs_elk_c2 generation 10698 (__consumer_offsets-25) (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:51:13,969] INFO [GroupCoordinator 2]: Assignment received from leader for group hercules.sink.elastic.legacy_logs_elk_c2 for generation 10698 (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 02:57:00,306] INFO [GroupMetadataManager brokerId=2] Removed 0 expired offsets in 0 milliseconds. (kafka.coordinator.group.GroupMetadataManager)
[2019-03-10 03:13:44,854] WARN Attempting to send response via channel for which there is no open connection, connection id 10.0.3.151:9092-10.0.3.153:42480-1819319 (kafka.network.Processor)
[2019-03-10 03:16:11,256] INFO [GroupCoordinator 2]: Preparing to rebalance group hercules.sink.elastic.legacy_logs_elk_c2 with old generation 10698 (__consumer_offsets-25) (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 03:16:39,196] INFO [GroupCoordinator 2]: Stabilized group hercules.sink.elastic.legacy_logs_elk_c2 generation 10699 (__consumer_offsets-25) (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 03:16:39,204] INFO [GroupCoordinator 2]: Assignment received from leader for group hercules.sink.elastic.legacy_logs_elk_c2 for generation 10699 (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 03:16:39,221] INFO [GroupCoordinator 2]: Preparing to rebalance group hercules.sink.elastic.legacy_logs_elk_c2 with old generation 10699 (__consumer_offsets-25) (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 03:17:00,306] INFO [GroupMetadataManager brokerId=2] Removed 0 expired offsets in 0 milliseconds. (kafka.coordinator.group.GroupMetadataManager)
[2019-03-10 03:17:31,693] INFO [GroupCoordinator 2]: Stabilized group hercules.sink.elastic.legacy_logs_elk_c2 generation 10700 (__consumer_offsets-25) (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 03:17:31,695] INFO [GroupCoordinator 2]: Assignment received from leader for group hercules.sink.elastic.legacy_logs_elk_c2 for generation 10700 (kafka.coordinator.group.GroupCoordinator)
[2019-03-10 03:20:05,312] WARN Attempting to send response via channel for which there is no open connection, connection id 10.0.3.151:9092-10.0.3.60:60490-1821319 (kafka.network.Processor)
[2019-03-10 03:22:56,928] WARN Attempting to send response via channel for which there is no open connection, connection id 10.0.3.151:9092-10.0.3.60:38542-1822186 (kafka.network.Processor)
[2019-03-10 03:24:43,989] WARN Attempting to send response via channel for which there is no open connection, connection id 10.0.3.151:9092-10.0.3.60:42936-1822733 (kafka.network.Processor)
[2019-03-10 03:27:00,306] INFO [GroupMetadataManager brokerId=2] Removed 0 expired offsets in 0 milliseconds. (kafka.coordinator.group.GroupMetadataManager)
[2019-03-10 03:37:00,306] INFO [GroupMetadataManager brokerId=2] Removed 0 expired offsets in 0 milliseconds. (kafka.coordinator.group.GroupMetadataManager)
{code}

I've skipped logs about segment deletion and so on.
~~~~

4.

~~~~
FWIW, I'm seeing the same
{code:java}
java.lang.IllegalStateException: Coordinator selected invalid assignment protocol: null
{code}
while using kafka-clients:1.1.1
~~~~

5.

~~~~
same issue.   kafka-client 2.2.0

it happens in large topology. like each topic has > 16 partitions. so that for each topic, client needs > 16 consumer threads.

 

 

 
~~~~

6.

~~~~
same issue.   kafka-client 1.1.1-cp1

100 partitions. 5 consumers with the same consumer group with 20 threads each
~~~~

7.

~~~~
[~kgn] , [~nizhikov]

*Version 1.1.0 is also affect*, thanks.

 

[2019-10-01 17:40:33,995] INFO [GroupCoordinator 1001]: Member <client>-2af431fd-60e4-4dd7-a4fd-8dd85d4a5620 in group main has failed, removing it from the group (kafka.coordinator.group.GroupCoordinator)
[2019-10-01 17:40:33,995] INFO [GroupCoordinator 1001]: Preparing to rebalance group main with old generation 15 (__consumer_offsets-1) (kafka.coordinator.group.GroupCoordinator)
[2019-10-01 17:40:33,995] INFO [GroupCoordinator 1001]: Group main with generation 16 is now empty (__consumer_offsets-1) (kafka.coordinator.group.GroupCoordinator)
~~~~

8.

~~~~
Hello.

I wrote a reproducer [1] for this issue.
It generates the output [2] exact to the issue description.
It requires to emulate specific consumer threads execution path.
It emulated via CyclicBarrier.

Seems, we have a synchronization issue.

[~guozhang] can you take a look?
Is reproducer correct?
Can you, please, assist me on how it should be fixed?

[1] https://github.com/nizhikov/kafka/pull/1/files#diff-d5e6de9941a0199b89a70d312962d546
[2] https://gist.github.com/nizhikov/8c4d5e0c78fd634a97557fdc0ece0097#file-kafka-8104-reproducer-output-L1578
~~~~

9.

~~~~
Reproducer simplified and updated.

[1] https://github.com/nizhikov/kafka/pull/1
~~~~

10.

~~~~
[~nizhikov] Thanks for picking this up, I think this issue is the same as reported in https://issues.apache.org/jira/browse/KAFKA-8891 and https://issues.apache.org/jira/browse/KAFKA-7263 as well, which is a long-lurking bug. So I'm linking them together now.

I will take a look into your PR as well.
~~~~

---

## KAFKA-8204: Streams may flush state stores in the incorrect order

https://issues.apache.org/jira/browse/KAFKA-8204

Given fix versions: 2.2.1, 2.3.0
JIRA affects (masked from the system): 1.1.0, 1.1.1, 2.0.0, 2.0.1, 2.1.0, 2.1.1, 2.2.0

- `KAFKA-8204@2.0.1`: config 2.0.1, metadata answer **affected** (listed_affected)
- `KAFKA-8204@1.0.2`: config 1.0.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 0.10.2, 1.0, 1.1, 2.2, 2.3, 2.1, 2.2.1

### Description

~~~~
Cached state stores may forward records during a flush call, so Streams should flush the stores in topological order. Otherwise, Streams may flush a downstream store before an upstream one, resulting in sink results being committed without the corresponding state changelog updates being committed.

This behavior is partly responsible for the bug reported in KAFKA-7895 .

The fix is simply to flush the stores in topological order, then when the upstream store forwards records to a downstream stateful processor, the corresponding state changes will be correctly flushed as well.

An alternative would be to repeatedly call flush on all state stores until they report there is nothing left to flush, but this requires a public API change to enable state stores to report whether they need a flush or not.
~~~~

### Comments (8)

1.

~~~~
How far back should we backport the fix for this?

The bug seems to affect cached state stores in every version of Streams since 0.10.2, and it's quite a subtle effect. You have to have multiple cached state stores in a row in the same subtopology, and Streams has to flush them in the wrong order (which is not guaranteed). In this case, Streams will mark a record as consumed even though it's still buffered in memory in the downstream store. If you stop (or crash) the app at this point, the record won't be added to the downstream store's changelog or emitted, constituting data loss.

With the introduction of Suppress, the scenario is basically the same, but the effect is that we *do* emit the output record, but we *do not* mark the record as emitted in the suppression buffer changelog. When we restore, we forget that we previously emitted the record, leading to a duplicate result (or possibly disordered earlier result being emitted).
~~~~

2.

~~~~
I would recommend to back port as far as `1.0`.
~~~~

3.

~~~~
Thanks [~mjsax]. Actually, in the code review, [~guozhang] asked some awkward questions that made me re-evaluate the nature of the bug. Upon review, I think it was introduced in [https://github.com/apache/kafka/pull/4215|https://github.com/apache/kafka/pull/4215/files] and therefore was introduced in 1.1 .

 

The details are here: [https://github.com/apache/kafka/pull/6555#discussion_r274997288] 
~~~~

4.

~~~~
Nice find! Thanks for the details!
~~~~

5.

~~~~
The latest PR has been merged to 2.2 / trunk, we will add more to fixed versions as we cherry-pick it to older branches via different PRs.
~~~~

6.

~~~~
Ok! this is merged to trunk (2.3), 2.2, and 2.1 . I'm waiting on KAFKA-8254 before requesting patch releases.
~~~~

7.

~~~~
2.2.1 has been proposed: https://cwiki.apache.org/confluence/display/KAFKA/Release+Plan+2.2.1
~~~~

8.

~~~~
FYI, 2.2.1 RC0 vote is in progress. (https://lists.apache.org/thread.html/3486798e63ae666fc336ce9009f07c7fdf66a96badc1fed63bcbd2ed@%3Cdev.kafka.apache.org%3E)

Please feel free to test it out, and reply on the vote thread if you have some trouble with it.
~~~~

---

## KAFKA-8366: partitions of topics being deleted show up in the offline partitions metric

https://issues.apache.org/jira/browse/KAFKA-8366

Given fix versions: 4.0.0
JIRA affects (masked from the system): 3.0.0, 3.0.1, 3.0.2, 3.1.0, 3.1.1, 3.2.0, 3.2.1, 3.3.0

- `KAFKA-8366@3.1.1`: config 3.1.1, metadata answer **affected** (listed_affected)
- `KAFKA-8366@2.8.2`: config 2.8.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.9, 4.0

### Description

~~~~
i believe this is a bug
offline partitions is a metric that indicates an error condition - lack of kafka availability.
as an artifact of how deletion is implemented the partitions for a topic undergoing deletion will show up as offline, which just creates false-positive alerts.

if needed, maybe there should exist a separate "partitions to be deleted" sensor.
~~~~

### Comments (3)

1.

~~~~
I also ran into this issue. I managed to replicate this bug with an integration test

[https://github.com/soarez/kafka/blob/replicate-bug-offline-partition-metrics-from-deleted-topics/core/src/test/scala/integration/kafka/api/OfflinePartitionsFromDeletedTopicTest.scala]

The problem is that the controller caches the offline partitions count, and when it is re-elected it fails to clear it if the topic is now being deleted.

 
~~~~

2.

~~~~
I'm sorry, but I don't think we should do this in 3.9.

The offline partitions metric is at least a decade old, and has always worked this way in ZK mode. Changing the behavior at this point would require a KIP. And probably even then, we'd want to create a new metric rather than changing the behavior of the old one. Topics in "deleting" state really do represent a lack of availability in some sense, since their names cannot be used until the deleting state is cleared (probably manually, by starting stopped brokers.) So some administrators may be relying on the current behavior of this metric to detect that and realize they need to do something about it.

Deleting state doesn't exist in 4.0 / KRaft, so if you agree, we can just close this JIRA with fix version 4.0.
~~~~

3.

~~~~
This is addressed by KRaft and sa KRaft is the only option starting from 4.0, we can close it.
~~~~

---

## KAFKA-8448: Too many kafka.log.Log instances (Memory Leak)

https://issues.apache.org/jira/browse/KAFKA-8448

Given fix versions: 2.4.0
JIRA affects (masked from the system): 2.2.0

- `KAFKA-8448@2.2.0`: config 2.2.0, metadata answer **affected** (listed_affected)
- `KAFKA-8448@2.1.1`: config 2.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
We have a custom Kafka health check which creates a topic, add some ACLs (read/write topic and group), produce & consume a single message and then quickly remove it and all the related ACLs created. We close the consumer involved, but no the producer.

We have observed that # of instances of {{kafka.log.Log}} keep growing, while there's no evidence of topics being leaked, neither running {{/opt/kafka/bin/kafka-topics.sh --zookeeper localhost:2181 --describe}} , nor looking at the disk directory where topics are stored.

After looking at the heapdump we've observed the following
 - None of the {{kafka.log.Log}} references ({{currentLogs}}, {{logsToBeDeleted }} and {{logsToBeDeleted}}) in {{kafka.log.LogManager}} is holding the big amount of {{kafka.log.Log}} instances.
 - The only reference preventing {{kafka.log.Log}} to be Garbage collected seems to be {{java.util.concurrent.ScheduledThreadPoolExecutor$DelayedWorkQueue}} which contains schedule tasks created with the name {{PeriodicProducerExpirationCheck}}.

I can see in the code that for every {{kafka.log.Log}} a task with this name is scheduled.
{code:java}
  scheduler.schedule(name = "PeriodicProducerExpirationCheck", fun = () => {
    lock synchronized {
      producerStateManager.removeExpiredProducers(time.milliseconds)
    }
  }, period = producerIdExpirationCheckIntervalMs, delay = producerIdExpirationCheckIntervalMs, unit = TimeUnit.MILLISECONDS)
{code}

However it seems those tasks are never unscheduled/cancelled
~~~~

### Comments (1)

1.

~~~~
Nice find, thanks for the report.
~~~~

---

## KAFKA-8586: Source task producers silently fail to send records

https://issues.apache.org/jira/browse/KAFKA-8586

Given fix versions: 1.0.3, 1.1.2, 2.0.2, 2.1.2, 2.2.2, 2.3.1, 2.4.0
JIRA affects (masked from the system): 2.3.0

- `KAFKA-8586@2.3.0`: config 2.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-8586@2.2.1`: config 2.2.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.3.0

### Description

~~~~
The Connect framework marks source records as successfully sent when they are dispatched to the producer, instead of when they are actually sent to Kafka. [This is assumed to be good enough|https://github.com/apache/kafka/blob/3e9d1c1411c5268de382f9dfcc95bdf66d0063a0/connect/runtime/src/main/java/org/apache/kafka/connect/runtime/WorkerSourceTask.java#L324-L331] since the Connect framework sets up its producer to use infinite retries on retriable errors, but in the case of an authorization or authentication failure with a secured Kafka broker, the errors aren't retriable and cause the producer to invoke its send callback with an exception and then give up on sending the message. This is a problem since the callback currently used by the WorkerSourceTask class when it invokes Producer.send(...) logs the exception and does nothing else. This leads to data loss since the source offsets for those failed records are committed, and the status of the task is never affected so users may not even know that something is wrong unless they check the worker log files or notice that data isn't flowing into Kafka. Until and unless someone does notice that something's wrong, the task will continue processing records and committing offsets, even though nothing is making it into Kafka.
~~~~

### Comments (1)

1.

~~~~
`recordSent` call could probably be moved into the `else` block that validates there wasn't an exception. This goes way back to Connect v1 – the first AuthenticationException that arguably violates the semantics of Retriable vs non-Retriable exceptions appeared after that code was written, but same release iirc.

However, let's not overestimate the impact here, but also account for changes in 2.3.0. Until 2.3.0, Connect was basically using a single producer config for all connectors (via `producer.` overrides). For this issue in particular, it *could* be using different principals for offset commits and task producers (since iirc only the task producers take the overrides), or the topics could have different ACLs. It's likely the most common case is not differentiating, and thus lack of any reports of this. (I'd have to review what e2e coverage we have – we have tests to generally discover loss like this, but in the context specifically of different principals or ACLs, I wouldn't be terribly surprised if we didn't have coverage today).

Now, thinking about impact moving forward, 2.3.0 will have [https://cwiki.apache.org/confluence/display/KAFKA/KIP-458%3A+Connector+Client+Config+Override+Policy]. This is more interesting because combined with [https://cwiki.apache.org/confluence/display/KAFKA/KIP-297%3A+Externalizing+Secrets+for+Connect+Configurations], Connect is in a much more reasonable position for users to truly go multi-tenant, have their own secrets, use a bunch of different principals, and make much more extensive use of ACLs. I'm not sure it makes it *that* much more likely to hit this issue (folks that weren't satisfied with state of security for multi-tenant use would have used multiple clusters but still potentially used different principals between internal and source task output topics), but it might make the pattern more common.

We should also talk about fallout and workarounds. There are 2 major failure modes that I can see. The first is probably the most common: when you are trying to configure a connector for the first time, trying to iterate to a good config, and hit auth failures. In this case, the follow up would be to clear out all offset data since nothing useful would have been produced anyway. The second case is if somebody mucks with ACLs after a connector is successfully configured. In this case, you'd need an offset *reset*, rather than deletion. I suspect case 1 is far more common and a bigger issue than case 2, and while source offset tooling isn't good/existent, at least it is de facto and in the future default standardized [https://cwiki.apache.org/confluence/display/KAFKA/KIP-174+-+Deprecate+and+remove+internal+converter+configs+in+WorkerConfig] in a way that makes it possible to work through this problem (at least for case 1).

In terms of solutions, we can move `recordSent` such that the offset commit, but we'd also still need to do something like aggressively propagate the exception to turn it into a task failure if we want to respect those failure modes. Users would then just have to iterate on restarting all the tasks.

Interestingly, we do config validation, but I don't think it validates any ability to connect or do anything against the brokers. It would be interesting to pre-flight check some of this, but don't think its a full solution because, e.g., a source connector might just start producing to a new topic it doesn't have permissions to. Additionally, permissions might change on the fly, so even a pre-flight against known topics might not fully cover us.
~~~~

---

## KAFKA-8802: ConcurrentSkipListMap shows performance regression in cache and in-memory store

https://issues.apache.org/jira/browse/KAFKA-8802

Given fix versions: 2.3.1, 2.4.0
JIRA affects (masked from the system): 2.3.0

- `KAFKA-8802@2.3.0`: config 2.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-8802@2.2.2`: config 2.2.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.3.0

### Description

~~~~
The use of ConcurrentSkipListMap in the cache and in-memory stores caused a performance regression in 2.3.0. We should revert back to using TreeMap 
~~~~

### Comments (3)

1.

~~~~
[~ableegoldman] Just curious if you could share what exactly was the performance hit and performance improvement by this PR. 
~~~~

2.

~~~~
Hi [~f2005870@gmail.com], I can't really give an exact number since it depends on so many factors.
~~~~

3.

~~~~
Sorry to have to re-open this, but unfortunately copying the keyset view when creating the InMemoryKeyValueIterator doesn't stop the ConcurrentModificationException, but rather shifts when it happens to be while performing the copy during the creation of the InMemoryKeyValueIterator, instead of during the iteration. This might have made it slightly less likely to be triggered, but I just encountered it personally in the wild. Until this is fixed I will need to avoid using an InMemoryKeyValueStore in any place where it's accessed via {{KakfaStreams.store().}}

The performance hit for ConcurrentSkipListMap vs TreeMap from other sources I can find reports it at around half as fast. On the other hand, the existing version also makes an entire copy of the iterated data into a new TreeSet which takes time and especially unnecessary space. Another way you might look at this is that the InMemoryKeyValueStore would merely operate as fast as the fastest available (open-source) map implementation in Java that's both sorted and concurrent. If someone really, really needed that extra performance out of it they could license [AirConcurrentMap|[https://github.com/boilerbay/airconcurrentmap]] and reimplement InMemoryKeyValueStore using that. Heck, we could make the ConcurrentNavigableMap implementation configurable in Kafka Streams if it was important enough. Another potential option is to provide the option of creating a higher-performance in memory store using the TreeMap as long as it's guaranteed to only be used from a single thread.

The new issue is at KAFKA-14260
~~~~

---

## KAFKA-8862: Misleading exception message for non-existant partition

https://issues.apache.org/jira/browse/KAFKA-8862

Given fix versions: 3.9.1, 4.0.0
JIRA affects (masked from the system): 2.3.0

- `KAFKA-8862@2.3.0`: config 2.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-8862@2.2.2`: config 2.2.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
https://issues.apache.org/jira/browse/KAFKA-6833 changed the logic of the {{KafkaProducer.waitOnMetadata}} so that if a partition did not exist it would wait for it to exist.
It means that if called with an incorrect partition the method will eventually throw a {{TimeoutException}}, which covers both topic and partition non-existence cases.

However, the exception message was not changed for the case where {{metadata.awaitUpdate(version, remainingWaitMs)}} throws a {{TimeoutException}}.

This results in a confusing exception message. For example, if a producer tries to send to a non-existent partition of an existing topic the message is 
"Topic %s not present in metadata after %d ms.", when timeout via the other code path would come with message
"Partition %d of topic %s with partition count %d is not present in metadata after %d ms."


~~~~

### Comments (1)

1.

~~~~
[~hachikuji] any chance you could review this? Thanks.
~~~~

---

## KAFKA-9073: Kafka Streams State stuck in rebalancing after one of the StreamThread encounters java.lang.IllegalStateException: No current assignment for partition

https://issues.apache.org/jira/browse/KAFKA-9073

Given fix versions: 2.3.2, 2.4.0
JIRA affects (masked from the system): 2.3.0

- `KAFKA-9073@2.3.0`: config 2.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-9073@2.2.2`: config 2.2.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.2.0, 2.3.0, 2.4, 2.3, 2.4.0

### Description

~~~~
I have a Kafka stream application that stores the incoming messages into a state store, and later during the punctuation period, we store them into a big data persistent store after processing the messages.

The application consumes from 120 partitions distributed across 40 instances. The application has been running fine without any problem for months, but all of a sudden some of the instances failed because of a stream thread exception saying  

```java.lang.IllegalStateException: No current assignment for partition <app_name>-<store_name>-changelog-98```

 

And other instances are stuck in the REBALANCING state, and never comes out of it. Here is the full stack trace, I just masked the application-specific app name and store name in the stack trace due to NDA.

 

```

2019-10-21 13:27:13,481 ERROR [application.id-a2c06c51-bfc7-449a-a094-d8b770caee92-StreamThread-3] [org.apache.kafka.streams.processor.internals.StreamThread] [] stream-thread [application.id-a2c06c51-bfc7-449a-a094-d8b770caee92-StreamThread-3] Encountered the following error during processing:
java.lang.IllegalStateException: No current assignment for partition application.id-store_name-changelog-98
 at org.apache.kafka.clients.consumer.internals.SubscriptionState.assignedState(SubscriptionState.java:319)
 at org.apache.kafka.clients.consumer.internals.SubscriptionState.requestFailed(SubscriptionState.java:618)
 at org.apache.kafka.clients.consumer.internals.Fetcher$2.onFailure(Fetcher.java:709)
 at org.apache.kafka.clients.consumer.internals.RequestFuture.fireFailure(RequestFuture.java:177)
 at org.apache.kafka.clients.consumer.internals.RequestFuture.raise(RequestFuture.java:147)
 at org.apache.kafka.clients.consumer.internals.RequestFutureAdapter.onFailure(RequestFutureAdapter.java:30)
 at org.apache.kafka.clients.consumer.internals.RequestFuture$1.onFailure(RequestFuture.java:209)
 at org.apache.kafka.clients.consumer.internals.RequestFuture.fireFailure(RequestFuture.java:177)
 at org.apache.kafka.clients.consumer.internals.RequestFuture.raise(RequestFuture.java:147)
 at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient$RequestFutureCompletionHandler.fireCompletion(ConsumerNetworkClient.java:574)
 at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.firePendingCompletedRequests(ConsumerNetworkClient.java:388)
 at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:294)
 at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:233)
 at org.apache.kafka.clients.consumer.KafkaConsumer.pollForFetches(KafkaConsumer.java:1281)
 at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:1225)
 at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:1201)
 at org.apache.kafka.streams.processor.internals.StreamThread.maybeUpdateStandbyTasks(StreamThread.java:1126)
 at org.apache.kafka.streams.processor.internals.StreamThread.runOnce(StreamThread.java:923)
 at org.apache.kafka.streams.processor.internals.StreamThread.runLoop(StreamThread.java:805)
 at org.apache.kafka.streams.processor.internals.StreamThread.run(StreamThread.java:774)

```

 

Now I checked the state sore disk usage; it is less than 40% of the total disk space available. Restarting the application solves the problem for a short amount of time, but the error popping up randomly on some other instances quickly. I tried to change the retry and retry.backoff.ms configuration but not helpful at all

```

retries = 2147483647

retry.backoff.ms

```

After googling for some time I found there was a similar bug reported to the Kafka team in the past, and also notice my stack trace is exactly matching with the stack trace of the reported bug.

Here is the link for the bug reported on a comparable basis a year ago.

https://issues.apache.org/jira/browse/KAFKA-7181

 

Now I am wondering is there a workaround for this bug though configuration changes, or is there something wrong the way I set up the application, the following are the configuration I have for my stream application.

 

```

consumer.session.timeout.ms=30000
 metric.reporters=org.apache.kafka.common.metrics.JmxReporter
 replication.factor=3
 metadata.max.age.ms=30000
 max.partition.fetch.bytes=2000000
 producer.retries=2147483647
 bootstrap.servers= <bootstrap server list goes here>
 metrics.recording.level=DEBUG
 producer.retry.backoff.ms=60000
 consumer.auto.offset.reset=latest
 application.server=0.0.0.0:6063
 num.standby.replicas=1
 max.poll.records=2
 group.initial.rebalance.delay.ms=30000
 state.dir= <state dir path goes here>
 heartbeat.interval.ms=10000
 max.poll.interval.ms=300000
 num.stream.threads=10
 application.id= <application id goes here>

```

Note: The original bug reported a year back got a conclusion that it is related to https://issues.apache.org/jira/browse/KAFKA-7657 and reported solved in version 2.2.0, but I am using the latest 2.3.0 version.

I appreciate your help concerning this bug.
~~~~

### Comments (7)

1.

~~~~
Okay, Today morning I got the same error in my staging environment, luckily I got INFO level logging this time,

I just attached the log for you guys to review, please let me know if you find any potential root cause.

Thanks.
~~~~

2.

~~~~
It looks like this was actually found and fixed as part of this (much larger) PR: [https://github.com/apache/kafka/pull/6884/files#r310328559]

Maybe we should split this bugfix into its own PR to backport to other branches, since it seems like people are actually hitting it? [~guozhang]

[~simplyamuthan] The fix did make it into 2.4, just fyi
~~~~

3.

~~~~
Thanks for the find-out, I can prepare a PR for 2.3 and try to cherry-pick to older branches :)
~~~~

4.

~~~~
[~simplyamuthan] [~ableegoldman] [~guozhang] -- should we close this ticket as fixed?
~~~~

5.

~~~~
We can resolve this as fixed in 2.4.0 only for now, once I have other PR merged in I will update the ticket.
~~~~

6.

~~~~
I am more interested in understanding the root cause, [~guozhang] could you please explain the scenario. Also, is this bug fix going to be a minor release under 2.3 ?
~~~~

7.

~~~~
[~simplyamuthan] You can find the explanation in the above PR, it is actually a pretty straight-forward bug.
~~~~

---

## KAFKA-9074: Connect's Values class does not parse time or timestamp values from string literals

https://issues.apache.org/jira/browse/KAFKA-9074

Given fix versions: 2.3.2, 2.4.1, 2.5.0, 2.6.0
JIRA affects (masked from the system): 1.1.0, 2.0.0, 2.1.0, 2.2.0, 2.3.0

- `KAFKA-9074@2.3.0`: config 2.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-9074@1.0.2`: config 1.0.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 1.1.0, 2.5, 2.4, 2.3

### Description

~~~~
The `Values.parseString(String)` method that returns a `SchemaAndValue` is not able to parse a string that contains a time or timestamp literal into a logical time or timestamp value. This is likely because the `:` is a delimiter for the internal parser, and so literal values such as `2019-08-23T14:34:54.346Z` and `14:34:54.346Z` are separated into multiple tokens before matching the pattern.

The colon can be escaped to prevent the unexpected tokenization, but then the literal string contains the backslash character before each colon, and again the pattern matching for the time and timestamp literal strings fails to match.

This should be backported as far back as possible: the `Values` class was introduced in AK 1.1.0.
~~~~

### Comments (1)

1.

~~~~
Merged to the `trunk`, `2.5`, `2.4`, and `2.3` branches. 
~~~~

---

## KAFKA-9077: System Test Failure: StreamsSimpleBenchmarkTest

https://issues.apache.org/jira/browse/KAFKA-9077

Given fix versions: 2.5.0
JIRA affects (masked from the system): 2.4.0

- `KAFKA-9077@2.4.0`: config 2.4.0, metadata answer **affected** (listed_affected)
- `KAFKA-9077@2.3.1`: config 2.3.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.4, 2.4.0

### Description

~~~~
StreamsSimpleBenchmarkTest tests are failing on 2.4 and trunk.
http://confluent-kafka-2-4-system-test-results.s3-us-west-2.amazonaws.com/2019-10-21--001.1571716233--confluentinc--2.4--cb4944f/report.html
~~~~

### Comments (4)

1.

~~~~
[~mjsax] [~guozhang] Can we check if these failures are blockers for 2.4.0 release?
~~~~

2.

~~~~
[~guozhang] – had a quick look into the logs. I found the following:

From jmx_tool.err.log:
{code:java}
Could not find all object names, retrying
Could not find all requested object names after 10000 ms. Missing kafka.streams:type=stream-metrics,client-id=simple-benchmark-StreamThread-1
Exiting.
{code}
From python debug log:
{code:java}
[DEBUG - 2019-10-21 11:34:33,238 - remoteaccount - _log - lineno:160]: ubuntu@worker4: Running ssh command: test -s /mnt/streams/jmx_tool.log
...
kafkatest.benchmarks.streams.streams_simple_benchmark_test.StreamsSimpleBenchmarkTest.test_simple_benchmark.test=streamcount.scale=1: FAIL: ubuntu@worker4: Jmx tool took too long to start
...
File "/home/jenkins/workspace/system-test-kafka_2.4/kafka/venv/local/lib/python2.7/site-packages/ducktape-0.7.6-py2.7.egg/ducktape/utils/util.py", line 41, in wait_until raise TimeoutError(err_msg() if callable(err_msg) else err_msg) TimeoutError: ubuntu@worker4: Jmx tool took too long to start
{code}
Does this ring a bell?
~~~~

3.

~~~~
I looked into the {{StreamsSimpleBenchmarkTest}} failure. The error message comes from {{kafka.tools.JmxTool}}. {{kafka.tools.JmxTool}} fetches metrics from a given endpoint. You can specify the endpoint when you start a java application with {{-Dcom.sun.management.jmxremote.port=9192}} (turn off authentication and ssl with {{-Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false}}). So, I started locally a Kafka Streams application using the 2.4 library and with a JMX endpoint. Then I started {{kafka.tools.JmxTool}} with the endpoint specified in the Kafka Streams application. {{kafka.tools.JmxTool}} could read the metrics that it could not read in the {{StreamsSimpleBenchmarkTest}}. I do not know why it does not work in {{StreamsSimpleBenchmarkTest}} but at least until now it seems to be an issue in {{StreamsSimpleBenchmarkTest}} or the test environment.
~~~~

4.

~~~~
Ran the tests on 2.4 branch to confirm the failures. All the tests are passed. 

[http://testing.confluent.io/confluent-kafka-2-4-system-test-results/?prefix=2019-10-23--001.1571831015--omkreddy--2.4--ac85cfb/]
~~~~

---

## KAFKA-9176: Flaky test failure:  OptimizedKTableIntegrationTest.shouldApplyUpdatesToStandbyStore

https://issues.apache.org/jira/browse/KAFKA-9176

Given fix versions: 2.6.0
JIRA affects (masked from the system): 2.4.0

- `KAFKA-9176@2.4.0`: config 2.4.0, metadata answer **affected** (listed_affected)
- `KAFKA-9176@2.3.1`: config 2.3.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.4

### Description

~~~~
h4. [https://builds.apache.org/blue/organizations/jenkins/kafka-2.4-jdk8/detail/kafka-2.4-jdk8/65/tests]
h4. Error
org.apache.kafka.streams.errors.InvalidStateStoreException: Cannot get state store source-table because the stream thread is PARTITIONS_ASSIGNED, not RUNNING
h4. Stacktrace
org.apache.kafka.streams.errors.InvalidStateStoreException: Cannot get state store source-table because the stream thread is PARTITIONS_ASSIGNED, not RUNNING
 at org.apache.kafka.streams.state.internals.StreamThreadStateStoreProvider.stores(StreamThreadStateStoreProvider.java:51)
 at org.apache.kafka.streams.state.internals.QueryableStoreProvider.getStore(QueryableStoreProvider.java:59)
 at org.apache.kafka.streams.KafkaStreams.store(KafkaStreams.java:1129)
 at org.apache.kafka.streams.integration.OptimizedKTableIntegrationTest.shouldApplyUpdatesToStandbyStore(OptimizedKTableIntegrationTest.java:157)
 at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
 at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
 at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
 at java.lang.reflect.Method.invoke(Method.java:498)
 at org.junit.runners.model.FrameworkMethod$1.runReflectiveCall(FrameworkMethod.java:59)
 at org.junit.internal.runners.model.ReflectiveCallable.run(ReflectiveCallable.java:12)
 at org.junit.runners.model.FrameworkMethod.invokeExplosively(FrameworkMethod.java:56)
 at org.junit.internal.runners.statements.InvokeMethod.evaluate(InvokeMethod.java:17)
 at org.junit.internal.runners.statements.RunBefores.evaluate(RunBefores.java:26)
 at org.junit.internal.runners.statements.RunAfters.evaluate(RunAfters.java:27)
 at org.junit.rules.ExternalResource$1.evaluate(ExternalResource.java:54)
 at org.junit.runners.ParentRunner$3.evaluate(ParentRunner.java:305)
 at org.junit.runners.BlockJUnit4ClassRunner$1.evaluate(BlockJUnit4ClassRunner.java:100)
 at org.junit.runners.ParentRunner.runLeaf(ParentRunner.java:365)
 at org.junit.runners.BlockJUnit4ClassRunner.runChild(BlockJUnit4ClassRunner.java:103)
 at org.junit.runners.BlockJUnit4ClassRunner.runChild(BlockJUnit4ClassRunner.java:63)
 at org.junit.runners.ParentRunner$4.run(ParentRunner.java:330)
 at org.junit.runners.ParentRunner$1.schedule(ParentRunner.java:78)
 at org.junit.runners.ParentRunner.runChildren(ParentRunner.java:328)
 at org.junit.runners.ParentRunner.access$100(ParentRunner.java:65)
 at org.junit.runners.ParentRunner$2.evaluate(ParentRunner.java:292)
 at org.junit.runners.ParentRunner$3.evaluate(ParentRunner.java:305)
 at org.junit.runners.ParentRunner.run(ParentRunner.java:412)
 at org.gradle.api.internal.tasks.testing.junit.JUnitTestClassExecutor.runTestClass(JUnitTestClassExecutor.java:110)
 at org.gradle.api.internal.tasks.testing.junit.JUnitTestClassExecutor.execute(JUnitTestClassExecutor.java:58)
 at org.gradle.api.internal.tasks.testing.junit.JUnitTestClassExecutor.execute(JUnitTestClassExecutor.java:38)
 at org.gradle.api.internal.tasks.testing.junit.AbstractJUnitTestClassProcessor.processTestClass(AbstractJUnitTestClassProcessor.java:62)
 at org.gradle.api.internal.tasks.testing.SuiteTestClassProcessor.processTestClass(SuiteTestClassProcessor.java:51)
 at sun.reflect.GeneratedMethodAccessor24.invoke(Unknown Source)
 at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
 at java.lang.reflect.Method.invoke(Method.java:498)
 at org.gradle.internal.dispatch.ReflectionDispatch.dispatch(ReflectionDispatch.java:36)
 at org.gradle.internal.dispatch.ReflectionDispatch.dispatch(ReflectionDispatch.java:24)
 at org.gradle.internal.dispatch.ContextClassLoaderDispatch.dispatch(ContextClassLoaderDispatch.java:33)
 at org.gradle.internal.dispatch.ProxyDispatchAdapter$DispatchingInvocationHandler.invoke(ProxyDispatchAdapter.java:94)
 at com.sun.proxy.$Proxy2.processTestClass(Unknown Source)
 at org.gradle.api.internal.tasks.testing.worker.TestWorker.processTestClass(TestWorker.java:118)
 at sun.reflect.GeneratedMethodAccessor23.invoke(Unknown Source)
 at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
 at java.lang.reflect.Method.invoke(Method.java:498)
 at org.gradle.internal.dispatch.ReflectionDispatch.dispatch(ReflectionDispatch.java:36)
 at org.gradle.internal.dispatch.ReflectionDispatch.dispatch(ReflectionDispatch.java:24)
 at org.gradle.internal.remote.internal.hub.MessageHubBackedObjectConnection$DispatchWrapper.dispatch(MessageHubBackedObjectConnection.java:182)
 at org.gradle.internal.remote.internal.hub.MessageHubBackedObjectConnection$DispatchWrapper.dispatch(MessageHubBackedObjectConnection.java:164)
 at org.gradle.internal.remote.internal.hub.MessageHub$Handler.run(MessageHub.java:412)
 at org.gradle.internal.concurrent.ExecutorPolicy$CatchAndRecordFailures.onExecute(ExecutorPolicy.java:64)
 at org.gradle.internal.concurrent.ManagedExecutorImpl$1.run(ManagedExecutorImpl.java:48)
 at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
 at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
 at org.gradle.internal.concurrent.ThreadFactoryImpl$ManagedThreadRunnable.run(ThreadFactoryImpl.java:56)
 at java.lang.Thread.run(Thread.java:748)
~~~~

### Comments (5)

1.

~~~~
[https://builds.apache.org/job/kafka-pr-jdk8-scala2.11/27147/testReport/junit/org.apache.kafka.streams.integration/OptimizedKTableIntegrationTest/shouldApplyUpdatesToStandbyStore/]
~~~~

2.

~~~~
[https://builds.apache.org/job/kafka-pr-jdk8-scala2.12/143/testReport/junit/org.apache.kafka.streams.integration/OptimizedKTableIntegrationTest/shouldApplyUpdatesToStandbyStore/]
~~~~

3.

~~~~
[https://builds.apache.org/job/kafka-pr-jdk8-scala2.12/970/testReport/junit/org.apache.kafka.streams.integration/OptimizedKTableIntegrationTest/shouldApplyUpdatesToStandbyStore/]

Different error:
{quote}java.lang.IllegalStateException: KafkaStreams is not running. State is ERROR. at org.apache.kafka.streams.KafkaStreams.validateIsRunningOrRebalancing(KafkaStreams.java:314) at org.apache.kafka.streams.KafkaStreams.store(KafkaStreams.java:1182) at org.apache.kafka.streams.integration.OptimizedKTableIntegrationTest.shouldApplyUpdatesToStandbyStore(OptimizedKTableIntegrationTest.java:122){quote}
~~~~

4.

~~~~
The recent failure on trunk is an actual bug, filing this PR to fix: https://github.com/apache/kafka/pull/8235
~~~~

5.

~~~~
Saw this fail again on a PR with
h3. Stacktrace

org.apache.kafka.streams.errors.InvalidStateStoreException: The state store, source-table, may have migrated to another instance. at org.apache.kafka.streams.state.internals.QueryableStoreProvider.getStore(QueryableStoreProvider.java:64) at org.apache.kafka.streams.KafkaStreams.store(KafkaStreams.java:1183) at org.apache.kafka.streams.integration.OptimizedKTableIntegrationTest.shouldApplyUpdatesToStandbyStore(OptimizedKTableIntegrationTest.java:126)
~~~~

---

## KAFKA-9279: Silent data loss in Kafka producer

https://issues.apache.org/jira/browse/KAFKA-9279

Given fix versions: 3.2.0
JIRA affects (masked from the system): 2.3.0

- `KAFKA-9279@2.3.0`: config 2.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-9279@2.2.2`: config 2.2.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.3.0

### Description

~~~~
It appears that it is possible for a producer.commitTransaction() call to succeed even if an individual producer.send() call has failed. The following code demonstrates the issue:
{code:java}
package org.example.dataloss;

import java.nio.charset.StandardCharsets;
import java.util.Properties;
import java.util.Random;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.common.serialization.ByteArraySerializer;

public class Main {

    public static void main(final String[] args) {
        final Properties producerProps = new Properties();

        if (args.length != 2) {
            System.err.println("Invalid command-line arguments");
            System.exit(1);
        }
        final String bootstrapServer = args[0];
        final String topic = args[1];

        producerProps.setProperty(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServer);
        producerProps.setProperty(ProducerConfig.BATCH_SIZE_CONFIG, "500000");
        producerProps.setProperty(ProducerConfig.LINGER_MS_CONFIG, "1000");
        producerProps.setProperty(ProducerConfig.MAX_REQUEST_SIZE_CONFIG, "1000000");
        producerProps.setProperty(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, "true");
        producerProps.setProperty(ProducerConfig.CLIENT_ID_CONFIG, "dataloss_01");
        producerProps.setProperty(ProducerConfig.TRANSACTIONAL_ID_CONFIG, "dataloss_01");

        try (final KafkaProducer<byte[], byte[]> producer = new KafkaProducer<>(producerProps, new ByteArraySerializer(), new ByteArraySerializer())) {
            producer.initTransactions();
            producer.beginTransaction();

            final Random random = new Random();
            final byte[] largePayload = new byte[2000000];
            random.nextBytes(largePayload);
            producer.send(
                new ProducerRecord<>(
                    topic,
                    "large".getBytes(StandardCharsets.UTF_8),
                    largePayload
                ),
                (metadata, e) -> {
                    if (e == null) {
                        System.out.println("INFO: Large payload succeeded");
                    } else {
                        System.err.printf("ERROR: Large payload failed: %s\n", e.getMessage());
                    }
                }
            );

            producer.commitTransaction();
            System.out.println("Commit succeeded");

        } catch (final Exception e) {
            System.err.printf("FATAL ERROR: %s", e.getMessage());
        }
    }
}
{code}
The code prints the following output:
{code:java}
ERROR: Large payload failed: The message is 2000093 bytes when serialized which is larger than the maximum request size you have configured with the max.request.size configuration.
Commit succeeded{code}
 
~~~~

### Comments (4)

1.

~~~~
This is affecting out team as well, with client version 2.3.0.
~~~~

2.

~~~~
Hey there, what's the expected behavior in this case? You want to fail the entire transaction if there is any send failure?
~~~~

3.

~~~~
The transaction is supposed to fail if any of the individual sends fails, which is clearly stated in the [Kafka Producer documentation|https://kafka.apache.org/23/javadoc/org/apache/kafka/clients/producer/KafkaProducer.html]:
{quote}
When used as part of a transaction, it is not necessary to define a callback or check the result of the future in order to detect errors from {{send}}. If any of the send calls failed with an irrecoverable error, the final [{{commitTransaction()}}|https://kafka.apache.org/23/javadoc/org/apache/kafka/clients/producer/KafkaProducer.html#commitTransaction--] call will fail and throw the exception from the last failed send. When this happens, your application should call [{{abortTransaction()}}|https://kafka.apache.org/23/javadoc/org/apache/kafka/clients/producer/KafkaProducer.html#abortTransaction--] to reset the state and continue to send data.
{quote}
The examples on that page also do not check the result of the individual producer send calls that form part of a transaction, which further reinforces the idea that failing the transaction on any send failure is the expected behaviour.
 
~~~~

4.

~~~~
I agree that this behaviour is unexpected and clearly breaks the transactional contract. See `commitTransaction` javadoc for example:
{code:java}
* Commits the ongoing transaction. This method will flush any unsent records before actually committing the transaction.
*
* Further, if any of the {@link #send(ProducerRecord)} calls which were part of the transaction hit irrecoverable
* errors, this method will throw the last received exception immediately and the transaction will not be committed.
* So all {@link #send(ProducerRecord)} calls in a transaction must succeed in order for this method to succeed.
...
public void commitTransaction() throws ProducerFencedException {{code}
~~~~

---

## KAFKA-9366: Upgrade log4j to log4j2

https://issues.apache.org/jira/browse/KAFKA-9366

Given fix versions: 4.0.0
JIRA affects (masked from the system): 2.1.1, 2.2.0, 2.3.0, 2.4.0

- `KAFKA-9366@2.4.0`: config 2.4.0, metadata answer **affected** (listed_affected)
- `KAFKA-9366@2.1.0`: config 2.1.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.0, 3.1, 2.7.0, 2.8.0, 3.0.0, 2.0.0, 2.0, 2.1.0, 3.2.0, 3.3.0, v3.2.0, 3.1.1, 4.0.0, 4.0

### Description

~~~~
h2. CVE-2019-17571 Detail

Included in Log4j 1.2 is a SocketServer class that is vulnerable to deserialization of untrusted data which can be exploited to remotely execute arbitrary code when combined with a deserialization gadget when listening to untrusted network traffic for log data. This affects Log4j versions up to 1.2 up to 1.2.17.

 

[https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2019-17571]

 
~~~~

### Comments (32)

1.

~~~~
This feature was not approved on time for 3.0. Pushing the target version to 3.1
[|https://issues.apache.org/jira/secure/AddComment!default.jspa?id=13198668]
~~~~

2.

~~~~
[~kkonstantine] Got it.
~~~~

3.

~~~~
May I kindly ask about the plan to upgrade log4j to version 2.x? I see that mentioned PR is still open. Any plans for releasing it in 3.1? 
Thanks!
~~~~

4.

~~~~
Hi Guys

Is there any plan to fix this issue soon?

Thanks

Ashish
~~~~

5.

~~~~
ALL // Sorry for being late. This KIP was originally passed for AK 3.0 but dropped from the release for the lack of review. I think it will be included in 3.1.

If you need this feature urgently, please have a look at a custom build of 2.7.0 [here|http://home.apache.org/~dongjin/post/apache-kafka-log4j2-support/]. I could not complete it for 2.8.0 and 3.0 for my medical concerns but will resume the work now.

If you are using log4j-appender, please have a look at [KIP-719|https://cwiki.apache.org/confluence/display/KAFKA/KIP-719%3A+Add+Log4J2+Appender]. This KIP proposes a log4j2 equivalent for log4j-appender. I am also working on a custom release of it.

Thank you again for your interest in my workings.
~~~~

6.

~~~~
Thanks, [~dongjin]
~~~~

7.

~~~~
Moved the target release to the next one as the PR was not approved in time for the feature freeze.
~~~~

8.

~~~~
Please upgrade to Log4j to 2.15.0 or newer for CVE-2021-44228. Thanks.
~~~~

9.

~~~~
[~showuon] Sure. The PR is now updated to handle log4j2 2.16.0.
~~~~

10.

~~~~
What is the ETA for this issue resolution!
~~~~

11.

~~~~
[~tarungoswami] I can't give you any guarantee but, [here|http://home.apache.org/~dongjin/post/apache-kafka-log4j2-support/] is a preview based on Apache Kafka 3.0.0.
~~~~

12.

~~~~
Hi Dongjin Lee,

Could you please let us know if any tentative dates for official release for latest log4j build.
~~~~

13.

~~~~
[~Ashoking] No, I can't certain it. Please have a look on the preview based on 3.0.0.
~~~~

14.

~~~~
I'm also looking for an official release date with the latest log4j.  Also, what version will you be upgrading to?  Thank you for your help in this matter.
~~~~

15.

~~~~
https://kafka.apache.org/cve-list claims to list all security
vulnerabilities that are fixed in released versions of Apache Kafka.
I understand this as "all other vulnerabilities are potentially
exploitable unless explicitly told otherwise".  Here is the list as of
2022-02-02 Wednesday:

- CVE-2017-12610 Authenticated Kafka clients may impersonate other
  users

- CVE-2018-1288 Authenticated Kafka clients may interfere with data
  replication

- CVE-2018-17196 Authenticated clients with Write permission may
  bypass transaction/idempotent ACL validation

- CVE-2019-12399 Apache Kafka Connect REST API may expose plaintext
  secrets in tasks endpoint

- CVE-2021-4104 Flaw in Apache Log4j logging library in versions 1.x

- CVE-2021-38153 Timing Attack Vulnerability for Apache Kafka Connect
  and Clients

- CVE-2021-44228 Flaw in Apache Log4j logging library in versions from
  2.0.0 and before 2.15.0

- CVE-2021-45046 Flaw in Apache Log4j logging library in versions from
  2.0-beta9 through 2.12.1 and from 2.13.0 through 2.15.0

- CVE-2022-23307 Deserialization of Untrusted Data Flaw in Apache
  Log4j logging library in versions 1.x

https://logging.apache.org/log4j/1.2/ lists several vulnerabilities
that affect log4j 1.x.  As of 2022-02-02 Wednesday:

- CVE-2019-17571 is a high severity issue targeting the
  SocketServer. Log4j includes a SocketServer that accepts serialized
  log events and deserializes them without verifying whether the
  objects are allowed or not. This can provide an attack vector that
  can be expoited.
  => NOT FIXED IN KAFKA?

- CVE-2020-9488 is a moderate severity issue with the
  SMTPAppender. Improper validation of certificate with host mismatch
  in Apache Log4j SMTP appender. This could allow an SMTPS connection
  to be intercepted by a man-in-the-middle attack which could leak any
  log messages sent through that appender.
  => NOT FIXED IN KAFKA?

- CVE-2021-4104 is a high severity deserialization vulnerability in
  JMSAppender. JMSAppender uses JNDI in an unprotected manner allowing
  any application using the JMSAppender to be vulnerable if it is
  configured to reference an untrusted site or if the site referenced
  can be accesseed by the attacker. For example, the attacker can
  cause remote code execution by manipulating the data in the LDAP
  store.
  => mitigated: one can remove JMSAppender from the log4j-1.2.17.jar
  artifact.

- CVE-2022-23302 is a high severity deserialization vulnerability in
  JMSSink. JMSSink uses JNDI in an unprotected manner allowing any
  application using the JMSSink to be vulnerable if it is configured
  to reference an untrusted site or if the site referenced can be
  accesseed by the attacker. For example, the attacker can cause
  remote code execution by manipulating the data in the LDAP store.
  => NOT FIXED IN KAFKA?

- CVE-2022-23305 is a high serverity SQL injection flaw in
  JDBCAppender that allows the data being logged to modify the
  behavior of the component. By design, the JDBCAppender in Log4j
  1.2.x accepts an SQL statement as a configuration parameter where
  the values to be inserted are converters from PatternLayout. The
  message converter, %m, is likely to always be included. This allows
  attackers to manipulate the SQL by entering crafted strings into
  input fields or headers of an application that are logged allowing
  unintended SQL queries to be executed.
  => NOT FIXED IN KAFKA?

- CVE-2022-23307 is a critical severity against the chainsaw component
  in Log4j 1.x. This is the same issue corrected in CVE-2020-9493
  fixed in Chainsaw 2.1.0 but Chainsaw was included as part of Log4j
  1.2.x.
  => mitigated: one can remove Chainsaw from the log4j-1.2.17.jar
  artifact.

From all that, it looks like there is a number of still-open
vulnerabilities in kafka induced by the use of log4j?  Can somebody
confirm?

May I suggest any interested reader to consider voting for this issue?
~~~~

16.

~~~~
Hi [~noonbs], this issue will be resolved with KAFKA-12399. I expect it will be done in 3.2.0.
~~~~

17.

~~~~
Hi [~dongjin] 

Could you please help me any approximate dates for official release for latest log4j build......? 
~~~~

18.

~~~~
Voting has been done by multiple users, and more are the requests for upgrading log4j.

 

Can we set or request ETA for log4j upgrade to log4j2. Any other challenge in doing so.

 

[https://logging.apache.org/log4j/1.2/download.html]

Log4j 1.x was End-Of-Llife on August 5, 2015. Kafka and Log4j, both are connected to Apache. As a strong community we need to think :: Does Apache-Kafka require more than 6 years of time to upgrade a log4j library, which was declared End-of-Life by Apache-log4j in 2015.

 

 

 

 
~~~~

19.

~~~~
 If this issue will be fixed in 3.2.0 ., what the ETA for 3.2.0
~~~~

20.

~~~~
Seems scheduled for April. 

[https://cwiki.apache.org/confluence/display/KAFKA/Release+Plan+3.2.0]

 

Even though Kafka is not on 2.x, a lot of Corporate IT departments are looking un-kindly on applications using old Log4j. I would strongly suggest back porting the log4j fixes and doing a hotfix ASAP.
~~~~

21.

~~~~
Thanks :)
~~~~

22.

~~~~
Hi, [~dongjin] please can you confirm that the latest available log4j2 will be used in the upgrade? Corporate needs us to eliminate anything before log4j2 2.17.2 as of this writing.
~~~~

23.

~~~~
[~roncraig] Sorry for being late. the PR is now updated with log4j2 2.17.2.
~~~~

24.

~~~~
Perfect!  Thanks, [~dongjin] .
~~~~

25.

~~~~
[~cadonna] did I really just see that you kicked this out of the 3.3.0 release?! We've all been waiting months for you all to patch the Log4J CVEs, how are you going to just boot it to some undetermined time in the future?! I think the world need this for at least 2 months ago!

 

CC [~dongjin] 
~~~~

26.

~~~~
[~brandonk]  and all, we are aware of the log4j CVE issue is impacting many users. Currently, we are discussing compatibility issue for the log4j2 upgrade, and is considering to temporarily replace log4j with reload4j in v3.2.0. The discussion thread is here: https://lists.apache.org/thread/qo1y3249xldt4cpg6r8zkcq5m1q32bf1 

 

Welcome to provide your comments and thoughts. Thanks.

 
~~~~

27.

~~~~
[~brandonk] Actually, I removed it from the 3.2.0 release and postponed it to the 3.3.0 release. You are welcome to comment in the discussion thread [~showuon] posted above. You could lay out your arguments and propose to block the 3.2.0 release on this ticket. You could also comment on the compatibility issues that were brought up in the thread from user perspective. All of these would help us to take a good decision about how to proceed.    
~~~~

28.

~~~~
[~showuon] I appreciate your dedication and efforts to resolve log4j 1.x EOL version from Kafka.

Log4j 1.x is declared End-of-Life by Apache-log4j in 2015. Apache-Kafka is still using.

As well as security scanners are reporting EOL version of log4j as vulnerability in Kafka, and there is little scope to explain it to whole world. 

[~showuon]  please discuss and review to find a solution with user, who has blocked chance of log4j upgrade (log4j 1.x to log4j 2.x) in Kafka in 3.2.0 release.

 

Or is there any plan to remove log4 1.x in 3.2.0 release? Please advise.
~~~~

29.

~~~~
[~akansh] As stated in the mailing list thread [~showuon] posted above, we will not upgrade to log4j2 in 3.2.0 due to risks of breaking backward compatibility. However, we will replace log4j12 with reload4j in 3.2.0 and 3.1.1 to account for the CVE. I merged the corresponding PR yesterday (see https://issues.apache.org/jira/browse/KAFKA-13660). We plan to move to log4j2 in the next major release 4.0.0.
~~~~

30.

~~~~
[~dongjin] I see you are active again. We now have a much clearer view of the timeline towards Kafka 4.0. Are you able to complete this task?
~~~~

31.

~~~~
Hi everyone,

If [~dongjin] doesn't have enough bandwidth, I'd be willing to take it over.
~~~~

32.

~~~~
Thanks [~frankvicky], assigned to you.
~~~~

---

## KAFKA-9492: ProducerResponse with record-level errors throw NPE with older client version

https://issues.apache.org/jira/browse/KAFKA-9492

Given fix versions: 2.4.1, 2.5.0
JIRA affects (masked from the system): 2.4.0

- `KAFKA-9492@2.4.0`: config 2.4.0, metadata answer **affected** (listed_affected)
- `KAFKA-9492@2.3.1`: config 2.3.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
ProduceResponse.toStruct(version) throws NullPointerException if the response contains record errors and version < 8 (before record errors were aded to ProduceResponse). The response can't be serialized to send to older clients as a result.
~~~~

---

## KAFKA-9724: Consumer wrongly ignores fetched records "since it no longer has valid position"

https://issues.apache.org/jira/browse/KAFKA-9724

Given fix versions: 2.5.1, 2.6.0
JIRA affects (masked from the system): 2.4.0

- `KAFKA-9724@2.4.0`: config 2.4.0, metadata answer **affected** (listed_affected)
- `KAFKA-9724@2.3.1`: config 2.3.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.4.0, 2.2.0, 2.3, 0.8, 2.4, 2.2

### Description

~~~~
After upgrading kafka-client to 2.4.0 (while brokers are still at 2.2.0) consumers in a consumer group intermittently stop progressing on assigned partitions, even when there are messages to consume. This is not a permanent condition, as they progress from time to time, but become slower with time, and catch up after restart.

Here is a sample of 3 consecutive ignored fetches:

{noformat}
2020-03-15 12:08:58,440 DEBUG [Thread-6] o.a.k.c.c.i.ConsumerCoordinator - Committed offset 538065584 for partition mrt-rrc10-6
2020-03-15 12:08:58,541 DEBUG [Thread-6] o.a.k.c.consumer.internals.Fetcher - Skipping validation of fetch offsets for partitions [mrt-rrc10-1, mrt-rrc10-6, mrt-rrc22-7] since the broker does not support the required protocol version (introduced in Kafka 2.3)
2020-03-15 12:08:58,549 DEBUG [Thread-6] org.apache.kafka.clients.Metadata - Updating last seen epoch from null to 62 for partition mrt-rrc10-6
2020-03-15 12:08:58,557 DEBUG [Thread-6] o.a.k.c.c.i.ConsumerCoordinator - Committed offset 538065584 for partition mrt-rrc10-6
2020-03-15 12:08:58,652 DEBUG [Thread-6] o.a.k.c.consumer.internals.Fetcher - Skipping validation of fetch offsets for partitions [mrt-rrc10-1, mrt-rrc10-6, mrt-rrc22-7] since the broker does not support the required protocol version (introduced in Kafka 2.3)
2020-03-15 12:08:58,659 DEBUG [Thread-6] org.apache.kafka.clients.Metadata - Updating last seen epoch from null to 62 for partition mrt-rrc10-6
2020-03-15 12:08:58,659 DEBUG [Thread-6] o.a.k.c.consumer.internals.Fetcher - Fetch READ_UNCOMMITTED at offset 538065584 for partition mrt-rrc10-6 returned fetch data (error=NONE, highWaterMark=538065631, lastStableOffset = 538065631, logStartOffset = 485284547, preferredReadReplica = absent, abortedTransactions = null, recordsSizeInBytes=16380)
2020-03-15 12:08:58,659 DEBUG [Thread-6] o.a.k.c.consumer.internals.Fetcher - Ignoring fetched records for partition mrt-rrc10-6 since it no longer has valid position
2020-03-15 12:08:58,665 DEBUG [Thread-6] o.a.k.c.c.i.ConsumerCoordinator - Committed offset 538065584 for partition mrt-rrc10-6
2020-03-15 12:08:58,761 DEBUG [Thread-6] o.a.k.c.consumer.internals.Fetcher - Skipping validation of fetch offsets for partitions [mrt-rrc10-1, mrt-rrc10-6, mrt-rrc22-7] since the broker does not support the required protocol version (introduced in Kafka 2.3)
2020-03-15 12:08:58,761 DEBUG [Thread-6] o.a.k.c.consumer.internals.Fetcher - Added READ_UNCOMMITTED fetch request for partition mrt-rrc10-6 at position FetchPosition{offset=538065584, offsetEpoch=Optional[62], currentLeader=LeaderAndEpoch{leader=node03.kafka:9092 (id: 3 rack: null), epoch=-1}} to node node03.kafka:9092 (id: 3 rack: null)
2020-03-15 12:08:58,761 DEBUG [Thread-6] o.a.k.c.consumer.internals.Fetcher - Sending READ_UNCOMMITTED IncrementalFetchRequest(toSend=(), toForget=(), implied=(mrt-rrc10-6, mrt-rrc22-7, mrt-rrc10-1)) to broker node03.kafka:9092 (id: 3 rack: null)
2020-03-15 12:08:58,770 DEBUG [Thread-6] org.apache.kafka.clients.Metadata - Updating last seen epoch from null to 62 for partition mrt-rrc10-6
2020-03-15 12:08:58,770 DEBUG [Thread-6] o.a.k.c.consumer.internals.Fetcher - Fetch READ_UNCOMMITTED at offset 538065584 for partition mrt-rrc10-6 returned fetch data (error=NONE, highWaterMark=538065727, lastStableOffset = 538065727, logStartOffset = 485284547, preferredReadReplica = absent, abortedTransactions = null, recordsSizeInBytes=51864)
2020-03-15 12:08:58,770 DEBUG [Thread-6] o.a.k.c.consumer.internals.Fetcher - Ignoring fetched records for partition mrt-rrc10-6 since it no longer has valid position
2020-03-15 12:08:58,808 DEBUG [Thread-6] o.a.k.c.c.i.ConsumerCoordinator - Committed offset 538065584 for partition mrt-rrc10-6
{noformat}

After which consumer makes progress:

{noformat}
2020-03-15 12:08:58,871 DEBUG [Thread-6] o.a.k.c.consumer.internals.Fetcher - Skipping validation of fetch offsets for partitions [mrt-rrc10-1, mrt-rrc10-6, mrt-rrc22-7] since the broker does not support the required protocol version (introduced in Kafka 2.3)
2020-03-15 12:08:58,871 DEBUG [Thread-6] o.a.k.c.consumer.internals.Fetcher - Added READ_UNCOMMITTED fetch request for partition mrt-rrc10-6 at position FetchPosition{offset=538065584, offsetEpoch=Optional[62], currentLeader=LeaderAndEpoch{leader=node03.kafka:9092 (id: 3 rack: null), epoch=-1}} to node node03.kafka:9092 (id: 3 rack: null)
2020-03-15 12:08:58,871 DEBUG [Thread-6] o.a.k.c.consumer.internals.Fetcher - Sending READ_UNCOMMITTED IncrementalFetchRequest(toSend=(), toForget=(), implied=(mrt-rrc10-6, mrt-rrc22-7, mrt-rrc10-1)) to broker node03.kafka:9092 (id: 3 rack: null)
2020-03-15 12:08:58,872 DEBUG [Thread-6] o.a.k.c.consumer.internals.Fetcher - Fetch READ_UNCOMMITTED at offset 538065584 for partition mrt-rrc10-6 returned fetch data (error=NONE, highWaterMark=538065744, lastStableOffset = 538065744, logStartOffset = 485284547, preferredReadReplica = absent, abortedTransactions = null, recordsSizeInBytes=58293)
2020-03-15 12:08:58,872 DEBUG [Thread-6] o.a.k.c.consumer.internals.Fetcher - Added READ_UNCOMMITTED fetch request for partition mrt-rrc10-6 at position FetchPosition{offset=538065744, offsetEpoch=Optional[62], currentLeader=LeaderAndEpoch{leader=node03.kafka:9092 (id: 3 rack: null), epoch=-1}} to node node03.kafka:9092 (id: 3 rack: null)
2020-03-15 12:08:58,872 DEBUG [Thread-6] o.a.k.c.consumer.internals.Fetcher - Sending READ_UNCOMMITTED IncrementalFetchRequest(toSend=(mrt-rrc10-6), toForget=(), implied=(mrt-rrc22-7, mrt-rrc10-1)) to broker node03.kafka:9092 (id: 3 rack: null)
2020-03-15 12:08:58,880 DEBUG [Thread-6] org.apache.kafka.clients.Metadata - Updating last seen epoch from null to 62 for partition mrt-rrc10-6
2020-03-15 12:08:58,885 DEBUG [Thread-6] o.a.k.c.c.i.ConsumerCoordinator - Committed offset 538065744 for partition mrt-rrc10-6
{noformat}

But it could be stuck for quite a long time.

~~~~

### Comments (12)

1.

~~~~
cc [~hachikuji] [~bchen225242]
~~~~

2.

~~~~
[~o.muravskiy] Thanks for the report. Could you include your consumer configuration?
~~~~

3.

~~~~
Sure [~hachikuji]: 

{noformat}
        allow.auto.create.topics = true
        auto.commit.interval.ms = 5000
        auto.offset.reset = earliest
        check.crcs = true
        client.dns.lookup = default
        client.id = ris-updates-to-hbase-ristest
        client.rack = 
        connections.max.idle.ms = 540000
        default.api.timeout.ms = 60000
        enable.auto.commit = false
        exclude.internal.topics = true
        fetch.max.bytes = 5000000
        fetch.max.wait.ms = 8000
        fetch.min.bytes = 1
        group.id = ris-updates-to-hbase-ristest
        group.instance.id = null
        heartbeat.interval.ms = 3000
        interceptor.classes = []
        internal.leave.group.on.close = true
        isolation.level = read_uncommitted
        max.partition.fetch.bytes = 4000000
        max.poll.interval.ms = 300000
        max.poll.records = 500000
        metadata.max.age.ms = 300000
        metric.reporters = []
        metrics.num.samples = 2
        metrics.recording.level = INFO
        metrics.sample.window.ms = 30000
        partition.assignment.strategy = [org.apache.kafka.clients.consumer.StickyAssignor]
        receive.buffer.bytes = 65536
        reconnect.backoff.max.ms = 1000
        reconnect.backoff.ms = 50
        request.timeout.ms = 30000
        retry.backoff.ms = 100
        sasl.client.callback.handler.class = null
        sasl.jaas.config = null
        sasl.kerberos.kinit.cmd = /usr/bin/kinit
        sasl.kerberos.min.time.before.relogin = 60000
        sasl.kerberos.service.name = null
        sasl.kerberos.ticket.renew.jitter = 0.05
        sasl.kerberos.ticket.renew.window.factor = 0.8
        sasl.login.callback.handler.class = null
        sasl.login.class = null
        sasl.login.refresh.buffer.seconds = 300
        sasl.login.refresh.min.period.seconds = 60
        sasl.login.refresh.window.factor = 0.8
        sasl.login.refresh.window.jitter = 0.05
        sasl.mechanism = GSSAPI
        security.protocol = PLAINTEXT
        security.providers = null
        send.buffer.bytes = 65536
        session.timeout.ms = 300000
        ssl.cipher.suites = null
        ssl.enabled.protocols = [TLSv1.2, TLSv1.1, TLSv1]
        ssl.endpoint.identification.algorithm = https
        ssl.key.password = null
        ssl.keymanager.algorithm = SunX509
        ssl.keystore.location = null
        ssl.keystore.password = null
        ssl.keystore.type = JKS
        ssl.protocol = TLS
        ssl.provider = null
        ssl.secure.random.implementation = null
        ssl.trustmanager.algorithm = PKIX
        ssl.truststore.location = null
        ssl.truststore.password = null
        ssl.truststore.type = JKS
{noformat}

~~~~

4.

~~~~
[~o.muravskiy] could you attach a larger log snippet? I'm having trouble reproducing this with 2.4 client and 2.2 broker. I see you have {{enable.auto.commit}} turned off. Can you describe the application a little?
~~~~

5.

~~~~
The interesting thing in the log snippet is the frequency of offset commits. Is that expected? I was speculating that we might be entering a loop like the following:

1. user commits offset with `commitSync` (or similar) which updates Metadata.lastSeenLeaderEpochs
2. in prepareFetch, Metadata.currentLeader then would return no leader and the last seen epoch
3. we trigger a metadata update because we have no leader
4. we get the metadata update without epoch information and reset Metadata.lastSeenLeaderEpochs
5. now we can fetch, but if we get another offset commit first, we would go back to 1

I tried to reproduce this issue locally, but can't say I fully succeeded. I did notice some pauses, but they were very brief. I definitely did notice the unnecessary metadata updates from step 3) though, so I think this is worth fixing even if it does not turn out to be the root cause of this issue. A potential fix is to skip updating `lastSeenLeaderEpochs` in step 1 if we have a current leader, but the epoch is not known.
~~~~

6.

~~~~
Here's the bigger fragment of a log:
 [^consumer.log.xz]  
~~~~

7.

~~~~
The algorithm of a consumer is fairly simple:
- subscribe to a number of topics with pattern subscription
- poll
- process the batch (insert to HBase)
- produce a record to another topic (status info)
- async commit consumed offsets
- loop to poll

But looking at [~hachikuji]'s reply, I want to add that I'm using an OffsetCommitCallback which in essence is 

{code:java}
    public synchronized void onComplete(Map<TopicPartition, OffsetAndMetadata> offsets, Exception exception) {
        if (exception instanceof RetriableCommitFailedException) {
            if (++failureCount < ignoranceLevel) {
                log.warn("Non-fatally failed to commit offsets, will keep going on. ", exception);
            } else {
                try {
                    Thread.sleep((long) (Math.random() * TimeUnit.SECONDS.toMillis(10)));
                    consumer.commitSync(offsets);
                    failureCount = 0;
                } catch (Exception e) {
                    onComplete(offsets, e);
                }
            }
        } else if (exception != null) {
            log.error("Can't commit offsets, starting shutdown: ", exception);
            System.exit(-1);
        }
    }
{code}

~~~~

8.

~~~~
[~o.muravskiy], I have a patch available here https://github.com/apache/kafka/pull/8376. Would you be willing to try it out and see if you continue to see hanging in the consumer? 
~~~~

9.

~~~~
[~o.muravskiy] any chance you can test the patch above?
~~~~

10.

~~~~
[~ijuma] Sorry – I deployed it, wanted to run for a longer time and kind of forgot.

I could confirm the issue have disappeared.
~~~~

11.

~~~~
That's great to hear!
~~~~

12.

~~~~
When merge this to Kafka 2.4.x?  Have any plan?
~~~~

---

## KAFKA-9788: Sensor name collision for group and transaction coordinator load metrics

https://issues.apache.org/jira/browse/KAFKA-9788

Given fix versions: 2.6.0
JIRA affects (masked from the system): 2.4.1, 2.5.0

- `KAFKA-9788@2.4.1`: config 2.4.1, metadata answer **affected** (listed_affected)
- `KAFKA-9788@2.4.0`: config 2.4.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
Both the group coordinator and the transaction coordinator create a Sensor object on startup to track the time it takes to load partitions, and both name the Sensor "PartitionLoadTime":

[https://github.com/apache/kafka/blob/trunk/core/src/main/scala/kafka/coordinator/transaction/TransactionStateManager.scala#L98]

[https://github.com/apache/kafka/blob/trunk/core/src/main/scala/kafka/coordinator/group/GroupMetadataManager.scala#L92]

However, Sensor names are meant to be unique. This name collision means that there is actually only one underlying "PartitionLoadTime" Sensor per broker, which is marked for each partition loaded by either coordinator, resulting in the metrics for group and transaction partition loading to be identical, and based the combination of each data set. These should be renamed to allow distinguishing between the two coordinator types.
~~~~

---

## KAFKA-9841: Connector and Task duplicated when a worker join with old generation assignment

https://issues.apache.org/jira/browse/KAFKA-9841

Given fix versions: 2.3.2, 2.4.2, 2.5.1, 2.6.0
JIRA affects (masked from the system): 2.3.1, 2.4.0, 2.4.1

- `KAFKA-9841@2.4.1`: config 2.4.1, metadata answer **affected** (listed_affected)
- `KAFKA-9841@2.3.0`: config 2.3.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.5.1

### Description

~~~~
When using IncrementalCooperativeAssignor.class to assign connectors and tasks.

Suppose there is a worker 'W' got some connection issue with the coordinator.

During the connection issue, the connectors/tasks on 'W' are assigned to the others worker

When the connection issue disappear, 'W' will join the group with an old generation assignment. Then the group leader will get duplicated connectors/tasks in the metadata sent by the workers. But the duplicated connectors/tasks will not be revoked.

 

Generation 3:

Worker1:

[2020-03-17 04:31:23,481] INFO [Worker clientId=connect-1, groupId=xxxxxx_mm2_fb__connect__group] Joined group at generation 3 with protocol version 2 and got assignment: Assignment\{error=0, leader='connect-1-ae2a2c31-fe73-4134-a376-4c4af8f466d0', leaderUrl='http://xxxxxx-2:8083/', offset=514, connectorIds=[], taskIds=[misc-0], revokedConnectorIds=[], revokedTaskIds=[], delay=0} with rebalance delay: 0 (org.apache.kafka.connect.runtime.distributed.DistributedHerder)

Worker2:

[2020-03-17 04:31:23,481] INFO [Worker clientId=connect-1, groupId=xxxxxx_mm2_fb__connect__group] Joined group at generation 3 with protocol version 2 and got assignment: Assignment\{error=0, leader='connect-1-ae2a2c31-fe73-4134-a376-4c4af8f466d0', leaderUrl='http://xxxxxx-2:8083/', offset=514, connectorIds=[], taskIds=[misc-4], revokedConnectorIds=[], revokedTaskIds=[], delay=0} with rebalance delay: 0 (org.apache.kafka.connect.runtime.distributed.DistributedHerder)

Worker3:

[2020-03-17 04:31:23,481] INFO [Worker clientId=connect-1, groupId=xxxxxx_mm2_fb__connect__group] Joined group at generation 3 with protocol version 2 and got assignment: Assignment\{error=0, leader='connect-1-ae2a2c31-fe73-4134-a376-4c4af8f466d0', leaderUrl='http://xxxxxx-2:8083/', offset=514, connectorIds=[], taskIds=[misc-3], revokedConnectorIds=[], revokedTaskIds=[], delay=0} with rebalance delay: 0 (org.apache.kafka.connect.runtime.dist 1480 ributed.DistributedHerder)

Worker4:

[2020-03-17 04:31:23,481] INFO [Worker clientId=connect-1, groupId=xxxxxx_mm2_fb__connect__group] Joined group at generation 3 with protocol version 2 and got assignment: Assignment\{error=0, leader='connect-1-ae2a2c31-fe73-4134-a376-4c4af8f466d0', leaderUrl='http://xxxxxx-2:8083/', offset=514, connectorIds=[misc], taskIds=[misc-1], revokedConnectorIds=[], revokedTaskIds=[], delay=0} with rebalance delay: 0 (org.apache.kafka.connect.runtime.distributed.DistributedHerder)

Worker5:

[2020-03-17 04:31:23,482] INFO [Worker clientId=connect-1, groupId=xxxxxx_mm2_fb__connect__group] Joined group at generation 3 with protocol version 2 and got assignment: Assignment\{error=0, leader='connect-1-ae2a2c31-fe73-4134-a376-4c4af8f466d0', leaderUrl='http://xxxxxx-2:8083/', offset=514, connectorIds=[], taskIds=[misc-5, misc-2], revokedConnectorIds=[], revokedTaskIds=[], delay=0} with rebalance delay: 0 (org.apache.kafka.connect.runtime.distributed.DistributedHerder)

 

Generation 4:

Worker1:

[2020-03-17 04:32:37,165] INFO [Worker clientId=connect-1, groupId=xxxxxx_mm2_fb__connect__group] Joined group at generation 4 with protocol version 2 and got assignment: Assignment\{error=0, leader='connect-1-2a332d4a-ef64-4b45-89c4-55f48d58f28c', leaderUrl='http://xxxxxx-4:8083/', offset=515, connectorIds=[], taskIds=[misc-0], revokedConnectorIds=[], revokedTaskIds=[], delay=0} with rebalance delay: 0 (org.apache.kafka.connect.runtime.distributed.DistributedHerder)

Worker2:

[2020-03-17 04:32:37,165] INFO [Worker clientId=connect-1, groupId=xxxxxx_mm2_fb__connect__group] Joined group at generation 4 with protocol version 2 and got assignment: Assignment\{error=0, leader='connect-1-2a332d4a-ef64-4b45-89c4-55f48d58f28c', leaderUrl='http://xxxxxx-4:8083/', offset=515, connectorIds=[], taskIds=[misc-4], revokedConnectorIds=[], revokedTaskIds=[], delay=0} with rebalance delay: 0 (org.apache.kafka.connect.runtime.distributed.DistributedHerder)

Worker3:

[2020-03-17 04:32:35,489] INFO [Worker clientId=connect-1, groupId=xxxxxx_mm2_fb__connect__group] Group coordinator xxxxxx:9092 (id: 2147483631 rack: null) is unavailable or invalid, will attempt rediscovery (org.apache.kafka.clients.consumer.internals.AbstractCoordinator)
[2020-03-17 04:32:35,590] INFO [Worker clientId=connect-1, groupId=xxxxxx_mm2_fb__connect__group] Discovered group coordinator xxxxxx:9092 (id: 2147483631 rack: null) (org.apache.kafka.clients.consumer.internals.AbstractCoordinator)
[2020-03-17 04:32:36,910] INFO WorkerSourceTask\{id=misc-3} Committing offsets (org.apache.kafka.connect.runtime.WorkerSourceTask)
[2020-03-17 04:32:36,910] INFO WorkerSourceTask\{id=misc-3} flushing 86 outstanding messages for offset commit (org.apache.kafka.connect.runtime.WorkerSourceTask)
[2020-03-17 04:32:37,164] INFO [Worker clientId=connect-1, groupId=xxxxxx_mm2_fb__connect__group] Attempt to heartbeat failed since group is rebalancing (org.apache.kafka.clients.consumer.internals.AbstractCoordinator)
[2020-03-17 04:32:37,164] INFO [Worker clientId=connect-1, groupId=xxxxxx_mm2_fb__connect__group] Rebalance started (org.apache.kafka.connect.runtime.distributed.WorkerCoordinator)
[2020-03-17 04:32:37,164] INFO [Worker clientId=connect-1, groupId=xxxxxx_mm2_fb__connect__group] (Re-)joining group (org.apache.kafka.clients.consumer.internals.AbstractCoordinator)

Worker4:

[2020-03-17 04:32:37,165] INFO [Worker clientId=connect-1, groupId=xxxxxx_mm2_fb__connect__group] Joined group at generation 4 with protocol version 2 and got assignment: Assignment\{error=0, leader='connect-1-2a332d4a-ef64-4b45-89c4-55f48d58f28c', leaderUrl='http://xxxxxx-4:8083/', offset=515, connectorIds=[misc], taskIds=[misc-3, misc-1], revokedConnectorIds=[], revokedTaskIds=[], delay=0} with rebalance delay: 0 (org.apache.kafka.connect.runtime.distributed.DistributedHerder)

Worker5:

[2020-03-17 04:32:37,165] INFO [Worker clientId=connect-1, groupId=xxxxxx_mm2_fb__connect__group] Joined group at generation 4 with protocol version 2 and got assignment: Assignment\{error=0, leader='connect-1-2a332d4a-ef64-4b45-89c4-55f48d58f28c', leaderUrl='http://xxxxxx-4:8083/', offset=515, connectorIds=[], taskIds=[misc-5, misc-2], revokedConnectorIds=[], revokedTaskIds=[], delay=0} with rebalance delay: 0 (org.apache.kafka.connect.runtime.distributed.DistributedHerder)

 

Generation 5:

Worker1:

[2020-03-17 04:32:42,757] INFO [Worker clientId=connect-1, groupId=xxxxxx_mm2_fb__connect__group] Joined group at generation 5 with protocol version 2 and got assignment: Assignment\{error=0, leader='connect-1-2a332d4a-ef64-4b45-89c4-55f48d58f28c', leaderUrl='http://xxxxxx-4:8083/', offset=515, connectorIds=[], taskIds=[misc-0], revokedConnectorIds=[], revokedTaskIds=[], delay=0} with rebalance delay: 0 (org.apache.kafka.connect.runtime.distributed.DistributedHerder)

Worker2:

[2020-03-17 04:32:42,756] INFO [Worker clientId=connect-1, groupId=xxxxxx_mm2_fb__connect__group] Joined group at generation 5 with protocol version 2 and got assignment: Assignment\{error=0, leader='connect-1-2a332d4a-ef64-4b45-89c4-55f48d58f28c', leaderUrl='http://xxxxxx-4:8083/', offset=515, connectorIds=[], taskIds=[misc-4], revokedConnectorIds=[], revokedTaskIds=[], delay=0} with rebalance delay: 0 (org.apache.kafka.connect.runtime.distributed.DistributedHerder)

Worker3:

[2020-03-17 04:32:42,757] INFO [Worker clientId=connect-1, groupId=xxxxxx_mm2_fb__connect__group] Joined group at generation 5 with protocol version 2 and got assignment: Assignment\{error=0, leader='connect-1-2a332d4a-ef64-4b45-89c4-55f48d58f28c', leaderUrl='http://xxxxxx-4:8083/', offset=515, connectorIds=[], taskIds=[misc-3], revokedConnectorIds=[], revokedTaskIds=[], delay=0} with rebalance delay: 0 (org.apache.kafka.connect.runtime.distributed.DistributedHerder)

Worker4:

[2020-03-17 04:32:42,756] INFO [Worker clientId=connect-1, groupId=xxxxxx_mm2_fb__connect__group] Joined group at generation 5 with protocol version 2 and got assignment: Assignment\{error=0, leader='connect-1-2a332d4a-ef64-4b45-89c4-55f48d58f28c', leaderUrl='http://xxxxxx-4:8083/', offset=515, connectorIds=[misc], taskIds=[misc-3, misc-1], revokedConnectorIds=[], revokedTaskIds=[], delay=0} with rebalance delay: 0 (org.apache.kafka.connect.runtime.distributed.DistributedHerder)

Worker5:

[2020-03-17 04:32:42,757] INFO [Worker clientId=connect-1, groupId=xxxxxx_mm2_fb__connect__group] Joined group at generation 5 with protocol version 2 and got assignment: Assignment\{error=0, leader='connect-1-2a332d4a-ef64-4b45-89c4-55f48d58f28c', leaderUrl='http://xxxxxx-4:8083/', offset=515, connectorIds=[], taskIds=[misc-5, misc-2], revokedConnectorIds=[], revokedTaskIds=[], delay=0} with rebalance delay: 0 (org.apache.kafka.connect.runtime.distributed.DistributedHerder)

 

 
~~~~

### Comments (9)

1.

~~~~
Thanks for reporting the issue and submitting a pull-request [~LucentWong] !

Deduplicating once a zombie worker returns to the group might be a bit late since redundant tasks might have been running for some time, but it's definitely worth adding this check as a guard and last line of defense against zombie tasks. 
~~~~

2.

~~~~
I assigned to me to review your PR but feel free to add your Jira Id to the project with a request to the dev mailing list and you can assign this ticket back to yourself. 
~~~~

3.

~~~~
Thank you, [~kkonstantine].
~~~~

4.

~~~~
Hello [~LucentWong] and [~kkonstantine] ,

I'm just getting started on the 2.5.1 release. What's the status of this ticket?

Thanks,

-John
~~~~

5.

~~~~
Thanks for checking [~vvcephei]. I'd like to get this in asap along with a couple of other related bugfixes. 

How much time do we have available for {{2.5.1}} ?
~~~~

6.

~~~~
This fix is now merged. Seems it can make {{2.5.1}} 
Thanks for checking [~vvcephei] and thanks for the contribution [~LucentWong]
~~~~

7.

~~~~
Thank you for checking [~vvcephei]  and thank you for your help [~kkonstantine].
~~~~

8.

~~~~
Hi guys, will fix be back-ported to older versions of kafka?
~~~~

9.

~~~~
Hi [~vutkin]. 
This fix has been backported to all the applicable release branches. 

These branches are listed under the {{Fix Versions:}} field in this Jira ticket 
~~~~

---

## KAFKA-9846: Race condition can lead to severe lag underestimate for active tasks

https://issues.apache.org/jira/browse/KAFKA-9846

Given fix versions: 2.6.0
JIRA affects (masked from the system): 2.5.0

- `KAFKA-9846@2.5.0`: config 2.5.0, metadata answer **affected** (listed_affected)
- `KAFKA-9846@2.4.1`: config 2.4.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.5, 2.6, 2.5.1, 2.6.0, 2.7.0, 2.5.0

### Description

~~~~
In KIP-535 we added the ability to query still-restoring and standby tasks. To give users control over how out of date the data they fetch can be, we added an API to KafkaStreams that fetches the end offsets for all changelog partitions and computes the lag for each local state store.

During this lag computation, we check whether an active task is in RESTORING and calculate the actual lag if so. If not, we assume it's in RUNNING and return a lag of zero. However, tasks may be in other states besides running and restoring; notably they first pass through the CREATED state before getting to RESTORING. A CREATED task may happen to be caught-up to the end offset, but in many cases it is likely to be lagging or even completely uninitialized.

This introduces a race condition where users may be led to believe that a task has zero lag and is "safe" to query even with the strictest correctness guarantees, while the task is actually lagging by some unknown amount.  During transfer of ownership of the task between different threads on the same machine, tasks can actually spend a while in CREATED while the new owner waits to acquire the task directory lock. So, this race condition may not be particularly rare in multi-threaded Streams applications
~~~~

### Comments (15)

1.

~~~~
Thanks for the report [~ableegoldman] . I'd offer one clarifying comment. The only strict correctness guarantee available is to disable querying stale stores in StoryQueryParameters, which would be unaffected by this race condition, and in fact, such use cases wouldn't even check lags, only the ownership of the active replica.

Additionally, I'd like to add that there's no way to reason strictly about the relationship between the reported lag and the actual lag at the time of a subsequent query. Even if the reported lag is correctly zero, the store may become arbitrarily laggy by the time of a subsequent query.

That said, this bug is clearly a violation of the method's contract, which may overestimate lagginess, but never underestimate it. The fact that we might underestimate by saying that it's fully caught up when it's not even initialized makes it seem that much more egregious.

I've looked into the code base, and I believe that this bug was incidentally fixed by refactoring in trunk, so it would only affect the 2.5 branch.
~~~~

2.

~~~~
First of all, thanks for flagging this issue [~ableegoldman]! 

 

IMO this need not block the release. It is bad in that sense, that a public API misbehaves under a race condition. However, this is a new feature and the architecture around building lag aware IQ routing around this has looser guarantees,  at least for the application I work on. That said, if any one deems that this evaluation is different from how AK community classifies blockers, please discard my opinion..  

 

I am looking more closely at the issue.. Will respond again in a bit. 
~~~~

3.

~~~~
>>During transfer of ownership of the task between different threads on the same machine, tasks can actually spend a while in CREATED

Looking at this more closely, there is some consolation since if the caller decides to actually call kafkaStreams.store() based on underestimated lag (0), then we would error out here for CREATED tasks.. But the race does exist for STARTING, PARTITION_ASSIGNED states. but softens the blow quite a bit (IIUC what happens in each transition)

[https://github.com/apache/kafka/blob/2.5/streams/src/main/java/org/apache/kafka/streams/state/internals/StreamThreadStateStoreProvider.java#L58]

[https://github.com/apache/kafka/blob/2.5/streams/src/main/java/org/apache/kafka/streams/processor/internals/StreamThread.java#L151] 

 

 
~~~~

4.

~~~~
Hey [~vinoth], just to clarify, the CREATED state this ticket refers to is a task-level state. This is independent from the thread-level states (as in PARTITIONS_ASSIGNED, STARTING)
~~~~

5.

~~~~
hi [~ableegoldman], if you were talking about Task.State, then you are in the future. 
https://github.com/apache/kafka/blame/b02bdd3227f08eef78080ef471c0950a4f77e5fb/streams/src/main/java/org/apache/kafka/streams/processor/internals/Task.java

I don't think we had that in 2.5 branch and was one of the harder things to reason about then. IIUC pre 2.5, there is state in only KafkaStreams level and thread level.. Thread level is what we checked to open stores. Let me see how to do a localized fix in 2.5, for this. 
~~~~

6.

~~~~
True, the literal Task.State was introduced for 2.6, but there was always a concept of task state. It was just relatively poorly managed and much more difficult to keep track of – hence the refactoring that introduced Task.State. The TaskManager delegated to the now-removed AssignedStreamTasks class, which kept track of task state by adding/removing tasks from the "created", "restoring", "running", and "suspended" maps. Suspended probably also causes problems for IQ, as a task in suspended is basically already revoked
~~~~

7.

~~~~
Understood, I was always wary of grabbing those maps at will to build this out.. 

Anyways, here's what I found.. 

The original test did not fail for this reason. the test did not wait for the instance to transition into RUNNING, instead just waiting till the lags went down to zero. This only guarantees onRestoreStart() would definitely have been called (otherwise restoration cannot start and lag would not have been zero.). It might happen that the actual lag went to 0 and thread was on its way to RUNNING state by finishing up onRestoreEnd() call. But the test could check for restoreEnd lags before that. and cause the NPE..

 
{code:java}
java.lang.NullPointerException
	at org.apache.kafka.streams.integration.LagFetchIntegrationTest.shouldFetchLagsDuringRestoration(LagFetchIntegrationTest.java:306)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43) {code}
 

On the issue reported in this ticket itself, we need to have a scenario where the streamThread.allStreamsTasks() returns a task in `created` and `suspended` lists for e.g.. I wrote a thread to constantly poll for the streamThread.allStreamsTasks() as an active was starting up and restoring and transitioning into RUNNING.  I saw that the first time, I got some tasks back using allStreamsTasks() was only after PARTITIONS_ASSIGNED and it was already a restoring task. 

Do you have suggestions on reproducing this in a test?  [~ableegoldman] you mentioned sometimes the tasks can be in CREATED for a long time? Anyways, I have posted a patch here [https://github.com/apache/kafka/pull/8462/files] 

This issue does not happen on master. So if we are targetting this really for 2.6. We can close this 

 
~~~~

8.

~~~~
Just realized I never replied [~vinoth]. To answer your question about how to get a task stuck in CREATED during a test, one way would be to start up an instance with two threads and have one of them hang indefinitely. It will drop out of the group and its task will be assigned to the other thread, but since the first thread hasn't released the task state directory lock, this task will be stuck in CREATED.

Anyways, just bringing this up since [~vvcephei] is setting up the 2.5.1 release. It seems like we understand the problem and the fix is quite straightforward, can we get this patched for 2.5.1?
~~~~

9.

~~~~
Probably don't have time this week.. But if y'all can take a quick pass at the patch above, I can work on this next week.. does that work
~~~~

10.

~~~~
Ok no worries. I don't think it's critical, just wanted to bring it up in case you wanted to get it fixed. Since 2.6 is almost out, we can always point people who want to use this feature to use the latest version
~~~~

11.

~~~~
Sounds good. Close this as "Wont fix" then?
~~~~

12.

~~~~
I think we can just leave it open and maybe someone from the community will pick it up
~~~~

13.

~~~~
Since this is not a blocker issue, as part of the 2.6.0 release process I'm changing the fix version to `2.7.0`. If this is incorrect, please respond and discuss on the "[DISCUSS] Apache Kafka 2.6.0 release" discussion mailing list thread.
~~~~

14.

~~~~
This is definitely a limitation of the current Affects Version/Fix Version system – this actually is fixed in 2.6.0, but has not been fixed in 2.5.0 (hence the ticket is unresolved).

That said, to avoid interfering with the release process I think we can leave it as is for now and then put 2.6.0 back on the fix version once it's released so that users know this doesn't affect 2.6+
~~~~

15.

~~~~
Resolving since this is fixed in 2.6
~~~~

---

## KAFKA-9988: Connect incorrectly logs that task has failed when one takes too long to shutdown

https://issues.apache.org/jira/browse/KAFKA-9988

Given fix versions: 3.0.0
JIRA affects (masked from the system): 2.2.3, 2.3.0, 2.3.1, 2.3.2, 2.4.0, 2.4.1, 2.4.2, 2.5.0, 2.5.1

- `KAFKA-9988@2.4.0`: config 2.4.0, metadata answer **affected** (listed_affected)
- `KAFKA-9988@2.2.2`: config 2.2.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
If the OffsetStorageReader is closed while the task is trying to shutdown, and the task is trying to access the offsets from the OffsetStorageReader, then we see the following in the logs.

{code:java}
[2020-05-05 05:28:58,937] ERROR WorkerSourceTask{id=connector-18} Task threw an uncaught and unrecoverable exception (org.apache.kafka.connect.runtime.WorkerTask)
org.apache.kafka.connect.errors.ConnectException: Failed to fetch offsets.
        at org.apache.kafka.connect.storage.OffsetStorageReaderImpl.offsets(OffsetStorageReaderImpl.java:114)
        at org.apache.kafka.connect.storage.OffsetStorageReaderImpl.offset(OffsetStorageReaderImpl.java:63)
        at org.apache.kafka.connect.runtime.WorkerSourceTask.execute(WorkerSourceTask.java:205)
        at org.apache.kafka.connect.runtime.WorkerTask.doRun(WorkerTask.java:175)
        at org.apache.kafka.connect.runtime.WorkerTask.run(WorkerTask.java:219)
        at java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:511)
        at java.util.concurrent.FutureTask.run(FutureTask.java:266)
        at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1142)
        at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:617)
        at java.lang.Thread.run(Thread.java:745)
Caused by: org.apache.kafka.connect.errors.ConnectException: Offset reader closed while attempting to read offsets. This is likely because the task was been scheduled to stop but has taken longer than the graceful shutdown period to do so.
        at org.apache.kafka.connect.storage.OffsetStorageReaderImpl.offsets(OffsetStorageReaderImpl.java:103)
        ... 14 more
[2020-05-05 05:28:58,937] ERROR WorkerSourceTask{id=connector-18} Task is being killed and will not recover until manually restarted (org.apache.kafka.connect.runtime.WorkerTask)
{code}

This is a bit misleading, because the task is already on its way of being shutdown, and doesn't actually need manual intervention to be restarted. We can see that as later on in the logs we see that it throws another unrecoverable exception.

{code:java}
[2020-05-05 05:40:39,361] ERROR WorkerSourceTask{id=connector-18} Task threw an uncaught and unrecoverable exception (org.apache.kafka.connect.runtime.WorkerTask)
{code}

If we know a task is on its way of shutting down, we should not throw a ConnectException and instead log a warning so that we don't log false negatives.

~~~~

---

## KAFKA-10029: Selector.completedReceives should not be modified when channel is closed

https://issues.apache.org/jira/browse/KAFKA-10029

Given fix versions: 2.5.1, 2.6.0
JIRA affects (masked from the system): 2.5.0

- `KAFKA-10029@2.5.0`: config 2.5.0, metadata answer **affected** (listed_affected)
- `KAFKA-10029@2.4.1`: config 2.4.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.5.0

### Description

~~~~
Selector.completedReceives are processed using `forEach` by SocketServer and NetworkClient when processing receives from a poll. Since we may close channels while processing receives, changes to the map while closing channels can result in ConcurrentModificationException. We clear the entire map after each poll anyway, so we don't need to remove channel from the map while closing channels.
~~~~

### Comments (2)

1.

~~~~
Good catch. Is this a recent regression?
~~~~

2.

~~~~
[~ijuma] It was a regression in 2.5.0 introduced by KAFKA-7639.
~~~~

---

## KAFKA-10134: High CPU issue during rebalance in Kafka consumer after upgrading to 2.5

https://issues.apache.org/jira/browse/KAFKA-10134

Given fix versions: 2.6.1, 2.7.0
JIRA affects (masked from the system): 2.5.0

- `KAFKA-10134@2.5.0`: config 2.5.0, metadata answer **affected** (listed_affected)
- `KAFKA-10134@2.4.1`: config 2.4.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.5, 2.4.1, 2.5.0, 2.4, 0.8, 2.5.1, 2.6.0, 2.6.1, 2.7.0, 2.6, v2.6.0

### Description

~~~~
We want to utilize the new rebalance protocol to mitigate the stop-the-world effect during the rebalance as our tasks are long running task.

But after the upgrade when we try to kill an instance to let rebalance happen when there is some load(some are long running tasks >30S) there, the CPU will go sky-high. It reads ~700% in our metrics so there should be several threads are in a tight loop. We have several consumer threads consuming from different partitions during the rebalance. This is reproducible in both the new CooperativeStickyAssignor and old eager rebalance rebalance protocol. The difference is that with old eager rebalance rebalance protocol used the high CPU usage will dropped after the rebalance done. But when using cooperative one, it seems the consumers threads are stuck on something and couldn't finish the rebalance so the high CPU usage won't drop until we stopped our load. Also a small load without long running task also won't cause continuous high CPU usage as the rebalance can finish in that case.

 

"executor.kafka-consumer-executor-4" #124 daemon prio=5 os_prio=0 cpu=76853.07ms elapsed=841.16s tid=0x00007fe11f044000 nid=0x1f4 runnable  [0x00007fe119aab000]"executor.kafka-consumer-executor-4" #124 daemon prio=5 os_prio=0 cpu=76853.07ms elapsed=841.16s tid=0x00007fe11f044000 nid=0x1f4 runnable  [0x00007fe119aab000]   java.lang.Thread.State: RUNNABLE at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.poll(ConsumerCoordinator.java:467) at org.apache.kafka.clients.consumer.KafkaConsumer.updateAssignmentMetadataIfNeeded(KafkaConsumer.java:1275) at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:1241) at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:1216) at

 

By debugging into the code we found it looks like the clients are  in a loop on finding the coordinator.

I also tried the old rebalance protocol for the new version the issue still exists but the CPU will be back to normal when the rebalance is done.

Also tried the same on the 2.4.1 which seems don't have this issue. So it seems related something changed between 2.4.1 and 2.5.0.

 
~~~~

### Comments (59)

1.

~~~~
[~ableegoldman] [~guozhang] Any idea?
~~~~

2.

~~~~
This is a bit weird to me -- discover of coordinator logic did not change from 2.4 -> 2.5 AFAIK.

[~seanguo] could you list the configs of consumer when you used cooperative rebalance, v.s. eager rebalance?
~~~~

3.

~~~~
[~guozhang] 
Cooperative:
{noformat}
ConsumerConfig values: 
	allow.auto.create.topics = true
	auto.commit.interval.ms = 5000
	auto.offset.reset = latest
	bootstrap.servers = [xxx,xxx,xxx,xxx,xxx,xxx]
	check.crcs = true
	client.dns.lookup = default
	client.id = 
	client.rack = 
	connections.max.idle.ms = 540000
	default.api.timeout.ms = 60000
	enable.auto.commit = false
	exclude.internal.topics = true
	fetch.max.bytes = 52428800
	fetch.max.wait.ms = 500
	fetch.min.bytes = 1
	group.id = xxx-consumer-group
	group.instance.id = null
	heartbeat.interval.ms = 3000
	interceptor.classes = []
	internal.leave.group.on.close = true
	isolation.level = read_uncommitted
	key.deserializer = class com.cisco.wx2.kafka.serialization.SimpleKafkaDeserializer
	max.partition.fetch.bytes = 1048576
	max.poll.interval.ms = 1800000
	max.poll.records = 10
	metadata.max.age.ms = 300000
	metric.reporters = []
	metrics.num.samples = 2
	metrics.recording.level = INFO
	metrics.sample.window.ms = 30000
	partition.assignment.strategy = [org.apache.kafka.clients.consumer.CooperativeStickyAssignor]
	receive.buffer.bytes = 65536
	reconnect.backoff.max.ms = 1000
	reconnect.backoff.ms = 50
	request.timeout.ms = 30000
	retry.backoff.ms = 100
	sasl.client.callback.handler.class = null
	sasl.jaas.config = null
	sasl.kerberos.kinit.cmd = /usr/bin/kinit
	sasl.kerberos.min.time.before.relogin = 60000
	sasl.kerberos.service.name = null
	sasl.kerberos.ticket.renew.jitter = 0.05
	sasl.kerberos.ticket.renew.window.factor = 0.8
	sasl.login.callback.handler.class = null
	sasl.login.class = null
	sasl.login.refresh.buffer.seconds = 300
	sasl.login.refresh.min.period.seconds = 60
	sasl.login.refresh.window.factor = 0.8
	sasl.login.refresh.window.jitter = 0.05
	sasl.mechanism = GSSAPI
	security.protocol = SSL
	security.providers = null
	send.buffer.bytes = 131072
	session.timeout.ms = 30000
	ssl.cipher.suites = null
	ssl.enabled.protocols = [TLSv1.2, TLSv1.1, TLSv1]
	ssl.endpoint.identification.algorithm = https
	ssl.key.password = null
	ssl.keymanager.algorithm = SunX509
	ssl.keystore.location = null
	ssl.keystore.password = null
	ssl.keystore.type = JKS
	ssl.protocol = TLS
	ssl.provider = null
	ssl.secure.random.implementation = null
	ssl.trustmanager.algorithm = PKIX
	ssl.truststore.location = null
	ssl.truststore.password = null
	ssl.truststore.type = JKS
	value.deserializer = class com.cisco.wx2.kafka.serialization.SimpleKafkaDeserializer
{noformat}

Eager:
{noformat}
ConsumerConfig values: 
	allow.auto.create.topics = true
	auto.commit.interval.ms = 5000
	auto.offset.reset = latest
	bootstrap.servers = [xxx,xxx,xxx,xxx,xxx,xxx]
	check.crcs = true
	client.dns.lookup = default
	client.id = 
	client.rack = 
	connections.max.idle.ms = 540000
	default.api.timeout.ms = 60000
	enable.auto.commit = false
	exclude.internal.topics = true
	fetch.max.bytes = 52428800
	fetch.max.wait.ms = 500
	fetch.min.bytes = 1
	group.id = xxx-consumer-group
	group.instance.id = null
	heartbeat.interval.ms = 3000
	interceptor.classes = []
	internal.leave.group.on.close = true
	isolation.level = read_uncommitted
	key.deserializer = class com.cisco.wx2.kafka.serialization.SimpleKafkaDeserializer
	max.partition.fetch.bytes = 1048576
	max.poll.interval.ms = 1800000
	max.poll.records = 10
	metadata.max.age.ms = 300000
	metric.reporters = []
	metrics.num.samples = 2
	metrics.recording.level = INFO
	metrics.sample.window.ms = 30000
	partition.assignment.strategy = [class org.apache.kafka.clients.consumer.RangeAssignor]
	receive.buffer.bytes = 65536
	reconnect.backoff.max.ms = 1000
	reconnect.backoff.ms = 50
	request.timeout.ms = 30000
	retry.backoff.ms = 100
	sasl.client.callback.handler.class = null
	sasl.jaas.config = null
	sasl.kerberos.kinit.cmd = /usr/bin/kinit
	sasl.kerberos.min.time.before.relogin = 60000
	sasl.kerberos.service.name = null
	sasl.kerberos.ticket.renew.jitter = 0.05
	sasl.kerberos.ticket.renew.window.factor = 0.8
	sasl.login.callback.handler.class = null
	sasl.login.class = null
	sasl.login.refresh.buffer.seconds = 300
	sasl.login.refresh.min.period.seconds = 60
	sasl.login.refresh.window.factor = 0.8
	sasl.login.refresh.window.jitter = 0.05
	sasl.mechanism = GSSAPI
	security.protocol = SSL
	security.providers = null
	send.buffer.bytes = 131072
	session.timeout.ms = 30000
	ssl.cipher.suites = null
	ssl.enabled.protocols = [TLSv1.2, TLSv1.1, TLSv1]
	ssl.endpoint.identification.algorithm = https
	ssl.key.password = null
	ssl.keymanager.algorithm = SunX509
	ssl.keystore.location = null
	ssl.keystore.password = null
	ssl.keystore.type = JKS
	ssl.protocol = TLS
	ssl.provider = null
	ssl.secure.random.implementation = null
	ssl.trustmanager.algorithm = PKIX
	ssl.truststore.location = null
	ssl.truststore.password = null
	ssl.truststore.type = JKS
	value.deserializer = class com.cisco.wx2.kafka.serialization.SimpleKafkaDeserializer
{noformat}

With 2.5.1 we can reproduce the high CPU issue with both eager and cooperative rebalancing protocol but not in 2.4.1. The difference between eager and cooperative with 2.5.1 is that for eager rebalance the CPU can go back to normal after the rebalance is done but for cooperative it seems it stuck on rebalancing and never ends.
~~~~

4.

~~~~
Any additional thoughts [~guozhang]? [~seanguo] would you be able to share a profile of the consumer while the high CPU usage is going on?
~~~~

5.

~~~~
[~guozhang], [~ijuma], [~seanguo]: what's the status of this? Do we want to continue treating this as a blocker for the 2.6.0 release? If so, what's the timeframe for fixing this?

If this should not block the release, should we downgrade the priority and/or change the fix versions to 2.6.1 and/or 2.7.0?
~~~~

6.

~~~~
we have experienced same issue,

one easy way to reproduce is: 1. start both kafka server and java consumer thread 2. stop kafka

then you should observe consumer thread keeps busy cpu loop and cause very high cpu

the reason is due to java consumer 2.5.0 code change
{code:java}
// code placeholder
org.apache.kafka.clients.consumer.KafkaConsumer  line: 1235
if (includeMetadataInTimeout) {
    // try to update assignment metadata BUT do not need to block on the timer,
    // since even if we are 1) in the middle of a rebalance or 2) have partitions
    // with unknown starting positions we may still want to return some data
    // as long as there are some partitions fetchable; NOTE we always use a timer with 0ms
    // to never block on completing the rebalance procedure if there's any
    updateAssignmentMetadataIfNeeded(time.timer(0L));
}
{code}
if it fails to fetch metadata, this line never blocks, and it run thru and keep cpu busy loop, due to 
{code:java}
// code placeholder
while (timer.notExpired());
{code}
please help on this issue, this is blocker for us to upgrade to java client 2.5.0

it's particular bad if we deploy both kafka/java consumer in same VM/(k8s node)
 if something wrong make kafka hiccup, all java consumers cause cpu high, and make kafka even slower to recover (like restart by k8s), and eventually make entire node/VM not be able to going forward. 

(java consumers keep busy loop to wait kafka ready, kafka has too little cpu to move on)

 
~~~~

7.

~~~~
 
{code:java}
do {
    client.maybeTriggerWakeup();

    if (includeMetadataInTimeout) {
        // try to update assignment metadata BUT do not need to block on the timer,
        // since even if we are 1) in the middle of a rebalance or 2) have partitions
        // with unknown starting positions we may still want to return some data
        // as long as there are some partitions fetchable; NOTE we always use a timer with 0ms
        // to never block on completing the rebalance procedure if there's any
        updateAssignmentMetadataIfNeeded(time.timer(0L));
    } else {
        while (!updateAssignmentMetadataIfNeeded(time.timer(Long.MAX_VALUE))) {
            log.warn("Still waiting for metadata");
        }
    }

    final Map<TopicPartition, List<ConsumerRecord<K, V>>> records = pollForFetches(timer);
    if (!records.isEmpty()) {
        // before returning the fetched records, we can send off the next round of fetches
        // and avoid block waiting for their responses to enable pipelining while the user
        // is handling the fetched records.
        //
        // NOTE: since the consumed position has already been updated, we must not allow
        // wakeups or any other errors to be triggered prior to returning the fetched records.
        if (fetcher.sendFetches() > 0 || client.hasPendingRequests()) {
            client.transmitSends();
        }

        return this.interceptors.onConsume(new ConsumerRecords<>(records));
    }
} while (timer.notExpired());
{code}
from the current design, i guess one possible fix is to add exponentially retry if metadata is not available and nothing returned by pollForFetches(timer), until timer expired.


then let outside application code to call consumer.poll(timeout) again

 
~~~~

8.

~~~~
[~seanguo] I think [~neowu0]'s brought up issue is a valid one to tackle, but I'm not sure if it is the same root cause you've seen: basically the consumer maybe tied in the metadata refresh loop if it cannot find the coordinator, but that is only the case if the coordinator broker is indeed not available during that time.

In your observation though, there should be no broker unavailability since you're just bouncing the consumer instance and the coordinator should be quick to discover.
~~~~

9.

~~~~
I've provided a PR for trunk, but it should apply cleanly to 2.5 as well (I will cherry-pick this when merging). [~neowu0] [~seanguo] please let me know if you could apply the patch and verify if it helps resolving the issue.
~~~~

10.

~~~~
Hi, [~guozhang]

Thanks for quick update! 

I reviewed and tested your patch, and still found some issue
{code:java}
if (subscriptions.fetchablePartitions(tp -> true).isEmpty()) {
    updateAssignmentMetadataIfNeeded(timer);
} else {
    final Timer updateMetadataTimer = time.timer(0L);
    updateAssignmentMetadataIfNeeded(updateMetadataTimer);
    timer.update(updateMetadataTimer.currentTimeMs());
}
{code}
there are 2 scenarios
1) start java consumer with kafka stopped, the code work as expected, it flows to first branch, and wait with timer, 
and will be able to connect to kafka when kafka is up (with low cpu usage due to timer)

however in 2nd secnarios

 

2) start both java consumer and kafka, and let java consumer successfully subscribe some topics, then force stop kafka
then subscriptions.fetchablePartitions(tp -> true) will return non empty result, then it will go into second branch without blocking
and it will trigger busy cpu wait

Thanks,
~~~~

11.

~~~~
maybe besides fetchablePartitions, it also should check records = pollForFetches(timer)?
~~~~

12.

~~~~
something like this fix my issues, but i am not sure whether this is right thing to do to fit bigger picture
{code:java}
// poll for new data until the timeout expires
Map<TopicPartition, List<ConsumerRecord<K, V>>> records = null;
do {
    client.maybeTriggerWakeup();
    if (includeMetadataInTimeout) {
        // try to update assignment metadata BUT do not need to block on the timer if we still have
        // some assigned partitions, since even if we are 1) in the middle of a rebalance
        // or 2) have partitions with unknown starting positions we may still want to return some data
        // as long as there are some partitions fetchable; NOTE we always use a timer with 0ms
        // to never block on completing the rebalance procedure if there's any
        if (subscriptions.fetchablePartitions(tp -> true).isEmpty() || records == null || records.isEmpty()) {
            updateAssignmentMetadataIfNeeded(timer);
        } else {
            final Timer updateMetadataTimer = time.timer(0L);
            updateAssignmentMetadataIfNeeded(updateMetadataTimer);
            timer.update(updateMetadataTimer.currentTimeMs());
        }
    } else {
        while (!updateAssignmentMetadataIfNeeded(time.timer(Long.MAX_VALUE))) {
            log.warn("Still waiting for metadata");
        }
    }

    records = pollForFetches(timer);
    if (!records.isEmpty()) {
        // before returning the fetched records, we can send off the next round of fetches
        // and avoid block waiting for their responses to enable pipelining while the user
        // is handling the fetched records.
        //
        // NOTE: since the consumed position has already been updated, we must not allow
        // wakeups or any other errors to be triggered prior to returning the fetched records.
        if (fetcher.sendFetches() > 0 || client.hasPendingRequests()) {
            client.transmitSends();
        }

        return this.interceptors.onConsume(new ConsumerRecords<>(records));
    }
} while (timer.notExpired());
{code}
~~~~

13.

~~~~
We can try the patch next week to see whether this also addresses the issue we met as we had also seen a lots of operations on finding the coordinator when this issue happens.
~~~~

14.

~~~~
[~neowu0] What's still puzzling me is that, even in the second branch, since we always keep calling `timer.update` then we should still eventually exit the while loop with `timer.expired`. So why would we observe that it blocks inside the while-loop forever is not clear to me.
~~~~

15.

~~~~
Here's my reasoning: if there are still some owned partitions that are fetchable even during a rebalance, then within the while-loop even if we exit the updateAssignmentMetadataIfNeeded we can still try to fetch from then and then break out of the while loop. However, if we do not have fetchable partitions then we may be blocked in the while-loop for a long time until the poll timeout expires. During this period of time we would then see high CPU usage indeed. I think [~neowu0]'s idea is better: we should also use long poll if there are fetchable partitions but not data fetched.

What's puzzling me however, is that even in that case we should still be able to exit the busy while-loop eventually since the `timer.update` should still be called in pollForFetches within that while loop and hence advance the timer, why with cooperative rebalance we would block inside the while loop forever is not clear to me.
~~~~

16.

~~~~
Hi, [~guozhang]

for "What's still puzzling me is that, even in the second branch, since we always keep calling `timer.update` then we should still eventually exit the while loop with `timer.expired`. So why would we observe that it blocks inside the while-loop forever is not clear to me."

yes, it will exit while loop eventually, but usually the app code is like following (at least in my case)
{code:java}
while (!shutdown) {
    try {
        ConsumerRecords<byte[], byte[]> records = consumer.poll(Duration.ofSeconds(30));
        if (records.isEmpty()) continue;
        processRecords(records);
    } catch (Throwable e) {
        if (shutdown) break;
        logger.error("failed to pull message, retry in 10 seconds", e);
        Threads.sleepRoughly(Duration.ofSeconds(10));
    }
}
{code}
so during 30s, if kafak is down in the middle, since fetchablePartitions return non-empty, the consumer.poll keeps busy loop,

and as soon as it exists, the application usually will try to poll immediately.

in application level, sure i can put delay if poll return empty, but still it will trigger high cpu time to time, and timeout passed into consumer.poll can't be high, say if i use 5 secs,

in the second case, the thread acts like, high cpu 5sec, -> sleep 5s -> 100%cpu 5s, (which is still not considered as healthy behavior)

 
~~~~

17.

~~~~
Hey [~neowu0] thanks a lot for your comments. Much appreciated!

Just to clarify, what I was puzzling is the original observation that [~seanguo] made, that is with eager rebalance we would eventually escape the while-loop / high CPU, whereas with the new cooperative rebalance protocol we are stuck in this loop. Do you observe the same pattern? If yes what's your take on it?
~~~~

18.

~~~~
What I observed is not exactly same as Sean, I only tested client 2.5.0 on test env, where all kafka/app pod are in one k8s node.

and during k8s deployment, new pod joins and old pod fades out (this is similar as Sean's case),

during the deployment, since the new pod (consumer) are not fully joined the kafka consumer group yet, it causes high cpu, and made kafka even slower to assign group, and eventually it goes to negative loop, make both new pod and kafka stuck.

i suppose Sean's case is more or less similar, and the current fix should be able to resolve it. 
~~~~

19.

~~~~
[~neowu0] Thanks for your comments. I will incorporate them in my PR and ping you and [~seanguo] to test out before merging.
~~~~

20.

~~~~
I've updated the PR.
~~~~

21.

~~~~
[~guozhang] Looks like this also resolves our issue. After applied this patch the high CPU issue is not reproduced in our local environment. Thank you for the quick fix. [~neowu0] Thank you for pointing out the cause of this issue.
One thing to note is the latest code in the PR has a small issue "random.nextInt(2 << retries)" when retries is larger than 30 , this method will throw exception, we have modified to use timer.remainingMs() instead in that situation.
~~~~

22.

~~~~
[~seanguo] thanks for confirming! As the root cause is known now I've thought about an alternative solution to fix it: I think ideally we would split {{updateAssignmentMetadataIfNeeded}} into three different logic: 1) discover coordinator if necessary, 2) join-group if necessary, 3) refresh metadata and fetch position if necessary. Then we can just make 2) to be best-effort if there are still some fetchable partitions.


But that’s a rather big change to make as a last minute blocker fix for 2.6, so I made a smaller change to make updateAssignmentMetadataIfNeeded has an optional boolean flag to indicate if 2) above should wait until either expired or complete, otherwise do not wait on the join-group future and just try once with the timer which would return if there’s anything written on the socket. I’ve updated the PR for this, if people agree this would be a reasonable fix for 2.6 I can add the test coverage and merge it. LMK.
~~~~

23.

~~~~
[~guozhang] do you have an updated ETA to complete this issue?
~~~~

24.

~~~~
I've merged the PR and would like [~seanguo] [~neowu0] to verify if it has fixed their observed issue.
~~~~

25.

~~~~
Hi, [~guozhang]

Your latest change fixed all my issues, Thanks!
~~~~

26.

~~~~
Thanks for the confirmation! I'm resolving this ticket then.
~~~~

27.

~~~~
cc 2.5.1 release manager [~vvcephei] I'm merging it to 2.5 branch too.
~~~~

28.

~~~~
[~guozhang] Looks like the latest change bring back the high CPU issue based on our local tests.
~~~~

29.

~~~~
Hmm, interesting. What setup are you using with the local tests? I tried to setup a single consumer and a single broker, and then shutdown the broker; under this scenario the issue does not show up anymore.
~~~~

30.

~~~~
[~guozhang] Should we reopen this issue given [~seanguo]'s comment?
~~~~

31.

~~~~
[~guozhang], I have three brokers and 10 consumers. When I restart one of consumers, some of other consumers will be with high CPU issue. 


{code:java}
// from KafkaConsumer.java (a fine fix)
// private ConsumerRecords<K, V> poll(final Timer timer, final boolean includeMetadataInTimeout);
                if (includeMetadataInTimeout) {
                    // try to update assignment metadata BUT do not need to block on the timer if we still have
                    // some assigned partitions, since even if we are 1) in the middle of a rebalance
                    // or 2) have partitions with unknown starting positions we may still want to return some data
                    // as long as there are some partitions fetchable; NOTE we always use a timer with 0ms
                    // to never block on completing the rebalance procedure if there's any
                    if (subscriptions.fetchablePartitions(tp -> true).isEmpty()) {
                        updateAssignmentMetadataIfNeeded(timer);
                    } else {
                        final Timer updateMetadataTimer = time.timer(0L);
                        updateAssignmentMetadataIfNeeded(updateMetadataTimer);
                        timer.update(updateMetadataTimer.currentTimeMs());
                    }
                } else {
                    while (!updateAssignmentMetadataIfNeeded(time.timer(Long.MAX_VALUE))) {
                        log.warn("Still waiting for metadata");
                    }
                }
{code}


{code:java}
// from KafkaConsumer.java (last commit)
// private ConsumerRecords<K, V> poll(final Timer timer, final boolean includeMetadataInTimeout);

               if (includeMetadataInTimeout) {
                    // try to update assignment metadata BUT do not need to block on the timer for join group
                    updateAssignmentMetadataIfNeeded(timer, false);
                } else {
                    while (!updateAssignmentMetadataIfNeeded(time.timer(Long.MAX_VALUE), true)) {
                        log.warn("Still waiting for metadata");
                    }
                }
{code}

Per the above two commits I have one question about `updateAssignmentMetadataIfNeeded(timer, false);` why the second parameter is false? Per my understanding when it's false, actually it's same as before `updateAssignmentMetadataIfNeeded(time.timer(0L));` 
I've tested w/ true, it looks fine for us and I'm thinking when it's w/ true, the behavior is similar to [the commit|https://github.com/apache/kafka/pull/8934/commits/333a967ec22ea22babf32b18349b76b6552a2fac].
~~~~

32.

~~~~
[~zhowei] Just to clarify are you working with [~seanguo] on the same issue?

The rationale for the final fix is that we only need `timer.timer(0L)` for join-group, but not for others, for example even if the flag is set to false we would still use the original timer trying to discover the coordinator etc, because our setting was based on the observation that when the coordinator is not available, we are spending busy loops looking for it.

From your description, your case actually is not the same as my setup or [~neowu0]'s, i.e. the coordinator is fine, but all the partitions are revoked and hence you have none to fetch from while looping for the join-group request to complete. I've prepared a new PR that adds the fetchable logic back in a more efficient way, LMK if it works for you: https://github.com/apache/kafka/pull/9011
~~~~

33.

~~~~
[~guozhang], yes, [~seanguo] and I are working on the same issue.
I've verified PR:https://github.com/apache/kafka/pull/9011. looks like the CPU issue has gone away, but the new consumer spends much more long time joining group than before, it's about 2mins.
~~~~

34.

~~~~
[~zhowei] [~seanguo] I tried to reproduce your high CPU with {{three brokers and 10 consumers, and restart one of consumers}} but I failed to do that locally.

I've prepared a patch just improving on some log4j entries as we suspect your issue maybe related to heartbeats: https://github.com/apache/kafka/pull/9038 Could you try it out while reproducing the issue, and share your logs (you'd have to enable it to at least ERROR level) here so we can further understand the root cause?
~~~~

35.

~~~~
[~guozhang] refer to the attached file (consumer5.log.2020-07-22.log), the last re-join happened at " 10:52:41.247 [pool-1-thread-1] INFO  o.a.k.c.consumer.internals.AbstractCoordinator - [Consumer clientId=consumer5, groupId=consumerGroupId] (Re-)joining group" because there is one consumer trying to join. interesting, this time looks better than before, but still spend more than one min.
~~~~

36.

~~~~
Can somebody please clarify if this defect affects consumers if we don't use the new cooperative protocol? We're considering whether to upgrade to 2.4.1 or 2.5.0 and it looks like this particular defect makes staying on 2.4.1 a better idea. Thanks!
~~~~

37.

~~~~
[~zhowei] Did your run include both the log4j improvement and the other PR depending on fetchable partitions to do long polling?
~~~~

38.

~~~~
BTW I found that the main latency during rebalance is on discovering the coordinator while we keep getting "Join group failed with org.apache.kafka.common.errors.DisconnectException" and it kept retrying for about a minute. But I think you did not shutdown the broker in your experiment, is there anything else happening that cause that broker node to be not reachable?
~~~~

39.

~~~~
[~guozhang] I'm using logback and PR: https://github.com/apache/kafka/pull/9011 included as well.  yeah, just to restart consumer w/o broker change, both brokers &consumers were running on my local laptop, not found any other issue.
~~~~

40.

~~~~
[~zhowei] So you're saying you see the issue when restarting the consumers, not when restarting the brokers?
~~~~

41.

~~~~
[~ijuma] correct, just while restarting consumer, not broker restart.
~~~~

42.

~~~~
What I did not see from my local run is the following:

{code}
Join group failed with org.apache.kafka.common.errors.DisconnectException
{code}

Which indicates that the socket connecting to the brokers cannot be established, and the consumer has to retry discovering (the same) broker, and then re-connect to it, and somehow after one minute or two the issue goes away itself. If you did not restart the broker during that time, then I can only think of transient network issues..

Actually, could you try only patching the logback PR but not the 9011 PR (i.e. let it to falls into busy loop) and upload the logs so I can also check what's causing the busy loops as well?
~~~~

43.

~~~~
The long time joining group is related to *max.poll.records*, looks like rejoin is trigged in *poll()*, it means only when processing complete and *poll()* be called. And *DisconnectException* should not be a real socket error, before leader consumer issues a rejoin request, looks like rejoin request from other consumers will be failed w/ *DisconnectException*.
~~~~

44.

~~~~
Kafka clients v2.6.0 is already released, but high cpu issue doesn't go away for our scenario and find there is a significant difference between v2.6.0 and PR #9011:

[Kafka branch2.6|https://github.com/apache/kafka/blob/fe0279026bd3d854a7291f5bf99503469e900038/clients/src/main/java/org/apache/kafka/clients/consumer/KafkaConsumer.java#L1230]
{code:java}
if (includeMetadataInTimeout) {
    // try to update assignment metadata BUT do not need to block on the timer for join group
    updateAssignmentMetadataIfNeeded(timer, false);
} else {
    ...
}
{code}

[PR #9011|https://github.com/apache/kafka/pull/9011]
{code:java}
if (includeMetadataInTimeout) {
    // try to update assignment metadata;
    // do not need to block on the timer for join group if we have any fetchable partitions
    updateAssignmentMetadataIfNeeded(timer, !subscriptions.hasAnyFetchablePartitions());
} 
{code}

~~~~

45.

~~~~
What's in PR #9011 was meant to help debug the remaining issue, we know it was not merged. I reopened the Jira to avoid confusion. [~guozhang], thoughts on the remaining issue?
~~~~

46.

~~~~
I think I'd need more information to further investigate this issue. [~zhowei] could you apply https://github.com/apache/kafka/pull/9038 only (this is for improved log4j entries) on top of 2.6 to reproduce this issue and then upload the enhanced log file?
~~~~

47.

~~~~
[~guozhang] sure, I'll porting PR #9038 on 2.6.0 and share log with u. thx.
please refer to the attached file: consumer3.log.2020-08-20.log
~~~~

48.

~~~~
[~zhowei] Thanks for the new log files, it has been very helpful for me to nail down the root causes and I will refine an existing WIP PR https://github.com/apache/kafka/pull/8834 as a final fix for this. Please stay tuned.
~~~~

49.

~~~~
[~zhowei] could you try out https://github.com/apache/kafka/pull/8834 and lmk if it works fixing the issue now.
~~~~

50.

~~~~
[~guozhang] cool, I'll try it later, thanks
~~~~

51.

~~~~
[~guozhang] I've tested against PR #8834, it works fine for our scenario. appreciate.
~~~~

52.

~~~~
[~guozhang] one more question about PR #8834, whether or not *GroupCoordinator* changes is mandatory. I mean Kafka server changes should be more expensive that clients.
~~~~

53.

~~~~
Hello [~zhowei] that broker-side change is not mandatory, I just included that part to make the whole PR complete, but it is not a necessary change for your situation.
~~~~

54.

~~~~
[~guozhang] thanks, I've tested clients changes in PR #8834 against legacy Kafka server, it works fine as well. thanks for your response. 
~~~~

55.

~~~~
I'd like to see the title of this bug clarified: It is worse than just "High CPU usage".  I have a couple of Kafka Streams apps with a high number of tasks/threads and this issue is causing infinite rebalance loops where the entire *cluster stops processing and cannot successfully rebalance*.  This causes hard downtime.  I've had to roll back to 2.4.1.

Edit: clarification: tested with 2.6.0.  Have not tested 2.5.

I'm currently working on building the patch, will test.

 

Late to the party since you've already got the fix in progress, but in case it helps, I'd like to share what I'm seeing:

The rebalance failures seems to be associated the TimeoutExceptions, DisconnectionExceptions and other side effects as noted in earlier comments.  When many StreamThreads are all spinning, then each time a rebalance is attempted, when there are a large number of threads it is likely that _some_ thread will fail, and the rebalance never succeeds.  The downward spiral begins as ConsumerThreads become "fenced" and it triggers a full (not incremental) rebalance, and eventually all data flow gets blocked.  I've tried different combinations of session.timeout.ms, rebalance.timeout.ms, max.poll.time.ms, default.api.timeout.ms (as recommended in the text of the timeout exceptions) to no avail.

Of my applications, the ones that are affected include
 * one stateless app with num.stream.threads=24.  With more than 1 instance (2-4x=48-96 threads), it will often never rebalance correctly, or only after multiple attempts (30+ minutes).  
 * one stateful app with 36 partitions of large-ish (500MB-1GB each) state stores which can take a while to restore.  This app successfully starts if I shut down all instances, delete state stores, set initial rebalance delay, and start all up simultaneously – but if any instance restarts or I attempt to scale up later, then rebalance will never succeed.  Additionally, when state stores are reassigned, there are "LockExceptions" (DEBUG level logs) in a tight loop, and the state stores fail to be closed cleanly, which forces the restore process to begin all over again.  The only way I can successfully do a rolling restart is if I use static membership and increase the session timeout.  If there is only a single instance of the app, then it works with no problems (but this is not a solution as I need multiple instances for scale).

Other side effects: the tight loop logs several DEBUG logs, which filled up log storage and caused pod evictions, which caused state stores to become invalid and restore (workaround: disable this logging).

Additionally, have seen the following exceptions sporadically, not sure if these are separate bugs:

{{2020-08-31T00:40:47.786Z ERROR Uncaught stream processing error! KafkaStreamsConfiguration java.lang.IllegalStateException: There are insufficient bytes available to read assignment from the sync-group response (actual byte size 0) , this is not expected; it is possible that the leader's assign function is buggy and did not return any assignment for this member, or *because static member is configured and the protocol is buggy* hence did not get the assignment for this member}}
 {{    at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.onJoinComplete(ConsumerCoordinator.java:367)}}
 {{    at org.apache.kafka.clients.consumer.internals.AbstractCoordinator.joinGroupIfNeeded(AbstractCoordinator.java:440)}}
 {{    at org.apache.kafka.clients.consumer.internals.AbstractCoordinator.ensureActiveGroup(AbstractCoordinator.java:359)}}
 {{    at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.poll(ConsumerCoordinator.java:513)}}
 {{    at org.apache.kafka.clients.consumer.KafkaConsumer.updateAssignmentMetadataIfNeeded(KafkaConsumer.java:1268)}}
 {{    at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:1230)}}
 {{    at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:1210)}}
 {{    at org.apache.kafka.streams.processor.internals.StreamThread.pollRequests(StreamThread.java:766)}}
 {{    at org.apache.kafka.streams.processor.internals.StreamThread.runOnce(StreamThread.java:624)}}
 {{    at org.apache.kafka.streams.processor.internals.StreamThread.runLoop(StreamThread.java:551)}}
 {{    at org.apache.kafka.streams.processor.internals.StreamThread.run(StreamThread.java:510)}}

{{2020-09-03T15:53:17.524Z ERROR Uncaught stream processing error! KafkaStreamsConfiguration java.lang.IllegalStateException: Active task 3_0 should have been suspended}}
 {{    at org.apache.kafka.streams.processor.internals.TaskManager.handleAssignment(TaskManager.java:281)}}
 {{    ... 13 common frames omitted}}
 {{Wrapped by: java.lang.RuntimeException: Unexpected failure to close 1 task(s) [[3_0]]. First unexpected exception (for task 3_0) follows.}}
 {{    at org.apache.kafka.streams.processor.internals.TaskManager.handleAssignment(TaskManager.java:349)}}
 {{    at org.apache.kafka.streams.processor.internals.StreamsPartitionAssignor.onAssignment(StreamsPartitionAssignor.java:1428)}}
 {{    at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.invokeOnAssignment(ConsumerCoordinator.java:279)}}
 {{    at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.onJoinComplete(ConsumerCoordinator.java:421)}}
 {{    ... 10 common frames omitted}}
 {{Wrapped by: org.apache.kafka.common.KafkaException: User rebalance callback throws an error}}
 {{    at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.onJoinComplete(ConsumerCoordinator.java:436)}}
 {{    at org.apache.kafka.clients.consumer.internals.AbstractCoordinator.joinGroupIfNeeded(AbstractCoordinator.java:440)}}
 {{    at org.apache.kafka.clients.consumer.internals.AbstractCoordinator.ensureActiveGroup(AbstractCoordinator.java:359)}}
 {{    at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.poll(ConsumerCoordinator.java:513)}}
 {{    at org.apache.kafka.clients.consumer.KafkaConsumer.updateAssignmentMetadataIfNeeded(KafkaConsumer.java:1268)}}
 {{    at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:1230)}}
 {{    at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:1210)}}
 {{    at org.apache.kafka.streams.processor.internals.StreamThread.pollRequests(StreamThread.java:766)}}
 {{    at org.apache.kafka.streams.processor.internals.StreamThread.runOnce(StreamThread.java:628)}}
 {{    at org.apache.kafka.streams.processor.internals.StreamThread.runLoop(StreamThread.java:551)}}
 {{    at org.apache.kafka.streams.processor.internals.StreamThread.run(StreamThread.java:510)}}
~~~~

56.

~~~~
Hey [~davispw],

It looks like you might have run into a few distinct issues: the rebalancing problems, the "insufficient bytes available" IllegalStateException, and the "Active task 3_0 should have been suspended" IllegalStateException.

The rebalancing seems to point to this issue, as the full fix did not make it into 2.6.0 in time. It would be great if you could test out the patch and see if that helps (building from [pull/8834|https://github.com/apache/kafka/pull/8834] specifically, which is not yet merged). The patch I linked also includes a fix for KAFKA-10122, another cause of unnecessary rebalances.

For the two IllegalStateException issues, could you open separate tickets? They seem unrelated to this, and to each other, but definitely merit a closer look. Any logs you have from the time of the exceptions would help a lot. 

Thanks!
~~~~

57.

~~~~
The PR has been merged to trunk and 2.6
~~~~

58.

~~~~
[~guozhang] looks the fix version is 2.7.0 &2.6.1, do u know when to release them? thanks.
~~~~

59.

~~~~
I don't think there's a concrete plan for 2.6.1 yet, for 2.7.0 it is planned for Nov.
~~~~

---

## KAFKA-10179: State Store Passes Wrong Changelog Topic to Serde for Optimized Source Tables

https://issues.apache.org/jira/browse/KAFKA-10179

Given fix versions: 2.7.0
JIRA affects (masked from the system): 2.5.0

- `KAFKA-10179@2.5.0`: config 2.5.0, metadata answer **affected** (listed_affected)
- `KAFKA-10179@2.4.1`: config 2.4.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
{{MeteredKeyValueStore}} passes the name of the changelog topic of the state store to the state store serdes. Currently, it always passes {{<application ID>-<store name>-changelog}} as the changelog topic name. However, for optimized source tables the changelog topic is the source topic. 
Most serdes do not use the topic name passed to them. However, if the serdes actually use the topic name for (de)serialization, e.g., when Kafka Streams is used with Confluent's Schema Registry, a {{org.apache.kafka.common.errors.SerializationException}} is thrown.
~~~~

### Comments (9)

1.

~~~~
I'm not sure it's correct to use the same "topic" name for materializing optimized source tables, as it's logically different data. In the normal flow (not recovery), we're taking the topic data, validating/transforming it by deserializing it (which might apply some transforms like projecting just fields of interest), and then serializing it, and then writing it into the store. So the "topic" we pass to the serializer should be different since it represents different data from the source topic.

This has consequences in practice when used with a schema registry using the confluent serializers. If we use the same topic, `serialize` might register a different schema with the source subject, which we probably don't want.

I think the technically correct thing to do (though this is of course more expensive) would be (when the source table is optimized) to deserialize and serialize each record when restoring.

Another issue that I think exists (need to try to reproduce) that deserializing/serializing would solve is skipped validation. The source topic deserializer functions as a sort of validator for records from the source topic. When the streams app is configured to skip on deserialization errors, bad source records are just skipped. However if we restore by just writing those records to the state store, we now hit the deserialization error when reading the state store, which is a query-killing error.

 
~~~~

2.

~~~~
{quote}I'm not sure it's correct to use the same "topic" name for materializing optimized source tables, as it's logically different data. In the normal flow (not recovery), we're taking the topic data, validating/transforming it by deserializing it (which might apply some transforms like projecting just fields of interest), and then serializing it, and then writing it into the store. So the "topic" we pass to the serializer should be different since it represents different data from the source topic.

For this case, the soure-topic-changelog optimization does no apply, and the store would always have its own changelog topic. And thus, the input-topic schema registered in the SR should not be "touched", and the write to the changelog topic should register a new scheme using the changelog topic name. Thus, no naming issue in SR should happen.
{quote}
The source-topic-changelog optimization really only applies, if the data in the input topic is exactly the same as in the changelog topic and thus, we avoid creating the changelog topic. To ensure this, we don't allow any processing to happen in between. The data would be deserialized and re-serialized using the same Serde (this is inefficiency we pay, as we also need to send the de-serialized data downstream for further processing).
{quote}Another issue that I think exists (need to try to reproduce) that deserializing/serializing would solve is skipped validation. The source topic deserializer functions as a sort of validator for records from the source topic. When the streams app is configured to skip on deserialization errors, bad source records are just skipped. However if we restore by just writing those records to the state store, we now hit the deserialization error when reading the state store, which is a query-killing error.
{quote}
This is a known issue and tracked via: https://issues.apache.org/jira/browse/KAFKA-8037
~~~~

3.

~~~~
Deserialization may itself be a transformation. For example, suppose I have source data with 10 fields, but only care about 3 of them for my stream processing app. It seems that it would be reasonable to provide a deserializer that just extracts those 3 fields. I suppose you could express this as a projection after creating the table, but that does preclude optimizations that use selective deserialization. And it may be much more expensive to do the materialization (since you're potentially materializing lots of data unnecessarily). I think there should be some way to achieve each of the following: 

 
 * optimized and the data in the store is exactly the same as the topic data . In this case (what's implemented today) the data can be restored by writing the source records into the store
 * optimized and the deserializer transforms the data somehow. In this case the data can be restored by deserializing/serializing each row from the source topic before writing it into the store. I don't think this is possible today.
 * not optimized (w/ which you could have a transforming deserializer and faster recovery, at the cost of extra data in kafka). I don't think this is possible today without turning all optimizations off.

 

> This is a known issue and tracked via: https://issues.apache.org/jira/browse/KAFKA-8037
  ack - thanks!
~~~~

4.

~~~~
Also, it's not really clear from the documentation that `serialize(deserialize())` is assumed to be the identity function  for `ktable(..)`.
~~~~

5.

~~~~
What you say is fair I guess. Given the current code, if you want to do any of those, you need to disable the optimization.

However, for the actual bug this ticket is about, the problem seems to be, that if the optimization is turned on, at some point in the code we pass the changelog topic name into the serde instead of the source topic name. And thus the schema cannot be found and the serde crashes. Thus, this ticket should focus on this bug.

Not sure if KAFKA-8037 covers all cases you describe. Maybe you want to follow up on this ticket (so we can extent its scope) or create a new ticket that describes the shortcomings of the current implementation.
~~~~

6.

~~~~
[~desai.p.rohan] While I find the idea of optimizing the materialization in the deserializer intriguing, I think the performance penalty that we would pay by deserializing and serializing each record during restoration is not worthwhile. Additionally -- if optimization is turned on -- we would need to read the original data from the source topic instead of the projected data from the changelog topic during each restoration which would again hit performance. Of course, we would need experiments to better understand the implications. 

An alternative idea would be to allow to plugin a byte-based transformation that does not need to deserialize and serialize each record. However, that would not solve the issue of having to read the unprojected data during each restoration.
 
If you are concerned with the amount of data to materialize a solution could be to optimize on topology-level by introducing a {{map()}} that makes the projection followed by a {{toTable()}} to materialize the data. That data read from the input topic would be the unprojected data but the one materialized is the projected one and also during restoration we would just read the projected data. An additional advantage of this method is that you can leave the source table optimization turned on, because it would not apply to this case.

In summary, the source table optimization was not introduced for the case you describe. IMO, it is not even an optimization in that case. 
~~~~

7.

~~~~
[~desai.p.rohan] I'm not sure I understand why it's a problem for the deserializer to modify the value slightly, by dropping fields to take your example. We would end up restoring the full bytes into the store, sure, but the plain bytes are never actually used right? We would always go through the deserializer when reading the value from the store and using it in an operation. So the "extra" fields would still get dropped.

Maybe if your values are bloated with a lot of useful information that you didn't want to store, this could blow up the disk usage. But I think there's a difference between a simple operation on data to extract only the relevant bits – eg dropping a field you don't care about – and fundamentally transforming the data to get it into a different form. The former seems reasonable to do during a deserialization, but the latter should be its own operation in the topology.

Of course, this just applies to modifying the values. If your deserializer modifies the key in any way, this would be a problem since lookups by key would fail after a restoration copies over the plain bytes. But I would argue that it's illegal to modify the key during de/serialization at all, not because of the restoration issue but because it can cause incorrect partitioning.

Anyways, I'm probably overlooking something obvious, but I'm struggling to see exactly where and how this breaks. That said I do agree we should clarify that `serialize(deserialize())` must be the identity for keys
~~~~

8.

~~~~
[~ableegoldman] I confirmed locally that nothing "breaks" if we use a deserializer that projects a subset of the fields in the record, as you suspected, but consider the following points:
 # Some of the most popular serdes are asymmetric (e.g. avro builds in the concept of reader/writer schema into their APIs)
 # It may be impossible to determine, for a given serde, whether it is symmetric
 # State after recovery should be identical to before recovery for predictable operations (especially in cloud environments)
 # Some of the most popular serdes have side effects (e.g. Confluent schema registry serdes will create subjects on your behalf)

In practice, the first three points in conjunction with what [~mjsax] said (the source-topic-changelog optimization really only applies, if the data in the input topic is exactly the same as in the changelog topic and thus, we avoid creating the changelog topic), means that we can't safely turn on the source-topic-changelog optimization unless the user indicates either (a) they are using a symmetrical serde or (b) they are willing to waive 3 in order to speed up recovery ([~cadonna] if we consider 3 a matter of correctness, we can't sacrifice correctness for performance without the user's consent).

Even if the user indicates (a) or (b) above, I still don't think we can implement the fix described here because of the fourth point. It may be possible that the user is using a symmetric serde but their schema is not identical to the one that wrote to the kafka topic (e.g. ksql, for example, generates a new schema where all the fields are the same but the schema has a different name, I can also easily imagine a schema with _more_ fields that would write the same value as it read from an event with fewer fields).

I'm not sure I understand this comment: "The data would be deserialized and re-serialized using the same Serde (this is inefficiency we pay, as we also need to send the de-serialized data downstream for further processing)." Why can't we just always pass-through the data into the state store if the optimization is enabled?

 
~~~~

9.

~~~~
I agree with Almog and Rohan’s arguments here. What I’m thinking is how we could define a principle for users to indicate that:

1) the bytes in the source topic are exactly the same as bytes in the state store (i.e. the serdes are symmetric).
2) there’s no side-effects that serde incurs; only 1) and 2) together means it is safe to skip serde during restoration.
3) and also, there’s no corrupted or ill-formatted data from source topics that should be skipped when loading into state stores. This is https://issues.apache.org/jira/browse/KAFKA-8037

During restoration time, compared with during normal processing time.
~~~~

---

## KAFKA-10224: The license term about jersey is not correct

https://issues.apache.org/jira/browse/KAFKA-10224

Given fix versions: 2.3.2, 2.4.2, 2.5.2, 2.6.0, 2.7.0
JIRA affects (masked from the system): 2.3.0

- `KAFKA-10224@2.3.0`: config 2.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-10224@2.2.2`: config 2.2.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.3.0, 2.5.0, 2.5, 1.0, 1.1, 2.0, 3.0, v1.0

### Description

~~~~
Kafka 2.3.0 and later bundle jersey 2.28. Since 2.28, jersey changed the license type from CDDL/GPLv2+CPE to EPLv2. But in Kafka 2.5.0's LICENSE file [https://github.com/apache/kafka/blob/2.5/LICENSE], it still said

"This distribution has a binary dependency on jersey, which is available under the CDDL".

This should be corrected ASAP.
~~~~

### Comments (1)

1.

~~~~
Kafka upgraded to Jersey 2.28 starting in 2.3.0 via [https://github.com/apache/kafka/pull/6665]. 

Also, just to clarify, per [https://www.apache.org/legal/resolved.html#weak-copyleft-licenses] it is still valid for Apache Kafka to include Jersey in binary form:

{quote}
Software under the following licenses may be included in binary form within an Apache product if the inclusion is appropriately labeled (see above):

 Common Development and Distribution Licenses: CDDL 1.0 and CDDL 1.1
 Common Public License: CPL 1.0
 Eclipse Public License: EPL 1.0
 IBM Public License: IPL 1.0
 Mozilla Public Licenses: MPL 1.0, MPL 1.1, and MPL 2.0
 Sun Public License: SPL 1.0
 Open Software License 3.0
 Erlang Public License
 UnRAR License (only for unarchiving)
 SIL Open Font License
 Ubuntu Font License Version 1.0
 IPA Font License Agreement v1.0
 Ruby License (including the older version when GPLv2 was a listed alternative Ruby 1.9.2 license)
 Eclipse Public License 2.0: EPL 2.0
{quote}
~~~~

---

## KAFKA-10268: dynamic config like "--delete-config log.retention.ms" doesn't work

https://issues.apache.org/jira/browse/KAFKA-10268

Given fix versions: 2.6.0, 2.7.0
JIRA affects (masked from the system): 2.1.1

- `KAFKA-10268@2.1.1`: config 2.1.1, metadata answer **affected** (listed_affected)
- `KAFKA-10268@2.1.0`: config 2.1.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.6, 2.6.0

### Description

~~~~
After I set "log.retention.ms=301000" to clean the data,i use the cmd

"bin/kafka-configs.sh --bootstrap-server 10.129.104.15:9092 --entity-type brokers --entity-default --alter --delete-config log.retention.ms" to reset to default.

Static broker configuration like log.retention.hours is 168h and no topic level configuration like retention.ms.

it did not take effect actually although server.log print the broker configuration like that.

log.retention.check.interval.ms = 300000
 log.retention.hours = 168
 log.retention.minutes = null
 {color:#ff0000}log.retention.ms = null{color}
 log.roll.hours = 168
 log.roll.jitter.hours = 0
 log.roll.jitter.ms = null
 log.roll.ms = null
 log.segment.bytes = 1073741824
 log.segment.delete.delay.ms = 60000

 

Then we can see that retention time is still 301000ms from the server.log and segments have been deleted.

[2020-07-13 14:30:00,958] INFO [Log partition=test_retention-2, dir=/data/kafka_logs-test] Found deletable segments with base offsets [5005329,6040360] due to retention time 301000ms breach (kafka.log.Log)
 [2020-07-13 14:30:00,959] INFO [Log partition=test_retention-2, dir=/data/kafka_logs-test] Scheduling log segment [baseOffset 5005329, size 1073741222] for deletion. (kafka.log.Log)
 [2020-07-13 14:30:00,959] INFO [Log partition=test_retention-2, dir=/data/kafka_logs-test] Scheduling log segment [baseOffset 6040360, size 1073728116] for deletion. (kafka.log.Log)
 [2020-07-13 14:30:00,959] INFO [Log partition=test_retention-2, dir=/data/kafka_logs-test] Incrementing log start offset to 7075648 (kafka.log.Log)
 [2020-07-13 14:30:00,960] INFO [Log partition=test_retention-0, dir=/data/kafka_logs-test] Found deletable segments with base offsets [5005330,6040410] {color:#FF0000}due to retention time 301000ms{color} breach (kafka.log.Log)
 [2020-07-13 14:30:00,960] INFO [Log partition=test_retention-0, dir=/data/kafka_logs-test] Scheduling log segment [baseOffset 5005330, size 1073732368] for deletion. (kafka.log.Log)
 [2020-07-13 14:30:00,961] INFO [Log partition=test_retention-0, dir=/data/kafka_logs-test] Scheduling log segment [baseOffset 6040410, size 1073735366] for deletion. (kafka.log.Log)
 [2020-07-13 14:30:00,961] INFO [Log partition=test_retention-0, dir=/data/kafka_logs-test] Incrementing log start offset to 7075685 (kafka.log.Log)
 [2020-07-13 14:31:00,959] INFO [Log partition=test_retention-2, dir=/data/kafka_logs-test] Deleting segment 5005329 (kafka.log.Log)
 [2020-07-13 14:31:00,959] INFO [Log partition=test_retention-2, dir=/data/kafka_logs-test] Deleting segment 6040360 (kafka.log.Log)
 [2020-07-13 14:31:00,961] INFO [Log partition=test_retention-0, dir=/data/kafka_logs-test] Deleting segment 5005330 (kafka.log.Log)
 [2020-07-13 14:31:00,961] INFO [Log partition=test_retention-0, dir=/data/kafka_logs-test] Deleting segment 6040410 (kafka.log.Log)
 [2020-07-13 14:31:01,144] INFO Deleted log /data/kafka_logs-test/test_retention-2/00000000000006040360.log.deleted. (kafka.log.LogSegment)
 [2020-07-13 14:31:01,144] INFO Deleted offset index /data/kafka_logs-test/test_retention-2/00000000000006040360.index.deleted. (kafka.log.LogSegment)
 [2020-07-13 14:31:01,144] INFO Deleted time index /data/kafka_logs-test/test_retention-2/00000000000006040360.timeindex.deleted. (kafka.log.LogSegment)

 

Here are a few steps to reproduce it.

1、set log.retention.ms=301000:

bin/kafka-configs.sh --bootstrap-server 10.129.104.15:9092 --entity-type brokers --entity-default --alter --add-config log.retention.ms=301000

2、produce messages to the topic:

bin/kafka-producer-perf-test.sh --topic test_retention --num-records 10000000 --throughput -1 --producer-props bootstrap.servers=10.129.104.15:9092 --record-size 1024

3、reset log.retention.ms to the default:

bin/kafka-configs.sh --bootstrap-server 10.129.104.15:9092 --entity-type brokers --entity-default --alter --delete-config log.retention.ms

 

I have attched server.log. You can see the log from row 238 to row 731. 
~~~~

### Comments (1)

1.

~~~~
This was also cherry-picked to {{2.6}}, but that branch has been frozen while we try to release AK 2.6.0. However, given that this is low-risk, I'll leave it on {{2.6}}, and updated the "Fix Versions" field above to include `2.6.0`.
~~~~

---

## KAFKA-10413: rebalancing leads to unevenly balanced connectors

https://issues.apache.org/jira/browse/KAFKA-10413

Given fix versions: 2.4.2, 2.5.2, 2.6.2, 2.7.1, 2.8.0
JIRA affects (masked from the system): 2.5.1

- `KAFKA-10413@2.5.1`: config 2.5.1, metadata answer **affected** (listed_affected)
- `KAFKA-10413@2.5.0`: config 2.5.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.4, 2.3.0, 2.7.1, 2.8.0

### Description

~~~~
GHi,

With CP 5.5, running kafka connect s3 sink on EC2 whith autoscaling enabled, if a connect instance disappear, or a new one appear, we're seeing unbalanced consumption, much like mentionned in this post:

[https://stackoverflow.com/questions/58644622/incremental-cooperative-rebalancing-leads-to-unevenly-balanced-connectors]


This usually leads to one kafka connect instance taking most of the load and consumption not being able to keep on.
Currently, we're "fixing" this by deleting the connector and re-creating it, but this is far from ideal.

Any suggestion on what we could do to mitigate this ?
~~~~

### Comments (20)

1.

~~~~
I have this issue too when EC2 scale in (S3 sink connector).
 It seems that using the old connect.protocol=eager result in a well balanced tasks across the workers.

[https://stackoverflow.com/questions/63348308/how-to-get-kafka-connect-to-balance-tasks-connectors-evenly]

 

Here is a screenshot of tasks monitoring distibution by EC2 with scale in at 19h30.

We can see that the new workers are poorly distributed compared to other one.

!connect_worker_balanced.png!
~~~~

2.

~~~~
This is an issue starting with Kafka version 2.4.x onwards. The only work around I could find is to switch back to eager protocol which defeats the purpose of incremental cooperative rebalancing all together. 
~~~~

3.

~~~~
Hi, 

We are also affected by this issue, seem's for us that is started with 2.3.0, when the incremental cooperative rebalancing was introduced.

We mainly notice this issue with HDFS connectors on our side. 

BR
~~~~

4.

~~~~
We have PR opened on  this [https://github.com/apache/kafka/pull/9319] 
~~~~

5.

~~~~
Hello, we're very excited the PR has been accepted and merged for this bug. Is there a fix-version? 
~~~~

6.

~~~~
[~chrisLee] we are looking to get this out fix in the next minor version release 2.7.1 

 
~~~~

7.

~~~~
I'm actually still in the process of cherry-picking into the previous release branches. Running the tests takes some time too. 
I'll update the fixed versions and close the ticket once I'm done very soon. 

Thanks again for the fix [~ramkrish1489]. Added you to the contributors list and assigned you the ticket
~~~~

8.

~~~~
Thanks for this fix ! 
~~~~

9.

~~~~
Hi,

I'm reopening this because I'm still seeing this issue with CP 6.2.0 which ships with 2.8.0 which is marked as a fixed version.
We basically see the same behavior as mentioned in the issue description.
~~~~

10.

~~~~
Hello, 
I confirm that we also see the same issue, any news on this ?
Thanks
~~~~

11.

~~~~
I am experiencing this issue as well, and it's particularly nasty because we're running in kubernetes so we have to WAY over limit our CPU because we end up with very uneven distribution of tasks resulting in CPU throttling on the workers that get work over-allocated to them. I've tried the mitigation of using connect.protocl=eager, but it seems my connector always gets back into an uneven state through pause/deploy/resume cycles.
~~~~

12.

~~~~
Hi, any news on this issue ?
I'm suspecting it is linked with https://issues.apache.org/jira/browse/KAFKA-12495 (I tried the attached PR and did not see the unbalance occur).
The current way we found to mitigate this is to destroy / re-create the connectors.
~~~~

13.

~~~~
Hello,

One year later with CP 7.5, I still have the issue

Regards
~~~~

14.

~~~~
KAFKA-12495 has been fixed.
~~~~

15.

~~~~
Hi [~sagarrao] , it did not fix it, I still have the issue with CP 7.6
~~~~

16.

~~~~
Hi [~yazgoo] Could you provide some more details that would help in debugging this, and open a new ticket? We currently don't have any leads for what could be causing the imbalance, and you could help with that.
~~~~

17.

~~~~
[~yazgoo] , yeah as Greg mentioned can you provide more info. Also, looks like you are talking about Confluent platform while this ticket is for AK. 
~~~~

18.

~~~~
Hello, I launch the attached script :

[^rebalance.sh]

And in my test after waiting for a few minutes, I get:

one connect well balanced
{code:java}
 ❯ curl -s http://localhost:8081/connectors/s3-connector2/status | jq .tasks |grep worker_id | sort | uniq -c
     15     "worker_id": "k2:8082"
     15     "worker_id": "k3:8083"
     15     "worker_id": "k4:8084"
     15     "worker_id": "k5:8085"
     15     "worker_id": "k6:8086"
     15     "worker_id": "k7:8087"
     15     "worker_id": "k8:8088"
     15     "worker_id": "k9:8089"
{code}
 

And the other one unbalanced

 
{code:java}
❯ curl -s http://localhost:8081/connectors/s3-connector1/status | jq .tasks |grep worker_id | sort | uniq -c
     27     "worker_id": "k1:8081"
     11     "worker_id": "k2:8082"
     12     "worker_id": "k3:8083"
     11     "worker_id": "k4:8084"
     12     "worker_id": "k5:8085"
     12     "worker_id": "k6:8086"
     11     "worker_id": "k7:8087"
     12     "worker_id": "k8:8088"
     12     "worker_id": "k9:8089"
{code}
 

Regards
~~~~

19.

~~~~
Here is yet another simpler version of the script, with less workers and which does not try and restart any worker:

 
{code:java}
#!/bin/bash
set -xe
dkill() {
  docker stop "$1" || true
  docker rm -v -f "$1" || true
}
write_topic() {
  # write 200 messages to the topic
  json='{"name": "test"}'
  docker exec -i kafka bash -c "(for i in {1..200}; do echo '$json'; done) | /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server 0.0.0.0:9092 --topic test_topic$1"
}

launch_minio() {
  # Launch Minio (Fake S3)
  docker run --network host -d --name minio \
    -e MINIO_ROOT_USER=minioadmin \
    -e MINIO_ROOT_PASSWORD=minioadmin \
    minio/minio server --console-address :9001 /data
      docker exec -it minio mkdir /data/my-minio-bucket
}
launch_kafka_connect() {
  # Start Kafka Connect with S3 Connector
  docker run --network host -d --name "kafka-connect$1" \
    -e  AWS_ACCESS_KEY_ID=minioadmin \
    -e  AWS_SECRET_ACCESS_KEY=minioadmin \
    -e  CONNECT_REST_ADVERTISED_HOST_NAME="k$1" \
    -e  CONNECT_LISTENERS="http://localhost:808$1" \
    -e  CONNECT_BOOTSTRAP_SERVERS=0.0.0.0:9092 \
    -e  CONNECT_REST_PORT="808$1" \
    -e  CONNECT_GROUP_ID="connect-cluster" \
    -e  CONNECT_CONFIG_STORAGE_TOPIC="connect-configs" \
    -e  CONNECT_OFFSET_STORAGE_TOPIC="connect-offsets" \
    -e  CONNECT_STATUS_STORAGE_TOPIC="connect-status" \
    -e  CONNECT_KEY_CONVERTER="org.apache.kafka.connect.json.JsonConverter" \
    -e  CONNECT_VALUE_CONVERTER="org.apache.kafka.connect.json.JsonConverter" \
    -e  CONNECT_VALUE_CONVERTER_SCHEMAS_ENABLE=false \
    -e  CONNECT_INTERNAL_KEY_CONVERTER="org.apache.kafka.connect.json.JsonConverter" \
    -e  CONNECT_INTERNAL_VALUE_CONVERTER="org.apache.kafka.connect.json.JsonConverter" \
    -e  CONNECT_INTERNAL_VALUE_CONVERTER_SCHEMAS_ENABLE=false \
    -e  CONNECT_PLUGIN_PATH="/usr/share/java,/usr/share/confluent-hub-components" \
    --entrypoint bash \
    confluentinc/cp-kafka-connect:7.6.1 \
    -c "confluent-hub install --no-prompt confluentinc/kafka-connect-s3:latest && /etc/confluent/docker/run"
}
cleanup_docker_env() {
  docker volume prune -f
  for container in $(for i in {1..9}; do echo "kafka-connect$i";done) kafka minio
  do
    dkill "$container"
  done
}
launch_kafka() {
  docker run --network host --hostname localhost --ulimit nofile=65536:65536 -d --name kafka -p 9092:9092 apache/kafka
  for i in {1..2}
  do
    # Create a Kafka topic
    docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --create --bootstrap-server 0.0.0.0:9092 --replication-factor 1 --partitions 120 --topic "test_topic$i"
    write_topic "$i"
  done
  for topic in connect-configs connect-offsets connect-status
  do
    # with cleanup.policy=compact, we can't have more than 1 partition
    docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --create --bootstrap-server 0.0.0.0:9092 --replication-factor 1 --partitions 1 --topic $topic --config cleanup.policy=compact
  done
}
cleanup_docker_env
launch_kafka
launch_minio
launch_kafka_connect 1
while true
do
  sleep 5
  # Check if Kafka Connect is up
  curl http://localhost:8081/ || continue
  break
done
sleep 10
for i in {1..2}
do
# Set up a connector
curl -X POST -H "Content-Type: application/json" --data '{
  "name": "s3-connector'"$i"'",
  "config": {
    "connector.class": "io.confluent.connect.s3.S3SinkConnector",
    "tasks.max": "120",
    "topics": "test_topic'"$i"'",
    "s3.region": "us-east-1",
    "store.url": "http://0.0.0.0:9000",
    "s3.bucket.name": "my-minio-bucket",
    "s3.part.size": "5242880",
    "flush.size": "3",
    "storage.class": "io.confluent.connect.s3.storage.S3Storage",
    "format.class": "io.confluent.connect.s3.format.json.JsonFormat",
    "schema.generator.class": "io.confluent.connect.storage.hive.schema.DefaultSchemaGenerator",
    "schema.compatibility": "NONE"
  }
}' http://localhost:8081/connectors
done
launch_kafka_connect 2
launch_kafka_connect 3
{code}
 

 

When the script ends, I have one worker with connector #1 tasks, the other one with connector #2 tasks.
{code:java}
❯ curl -s http://localhost:8081/connectors/s3-connector1/status | jq .tasks |grep worker_id | sort | uniq -c
    120     "worker_id": "k1:8081"{code}
{code:java}
❯ curl -s http://localhost:8081/connectors/s3-connector2/status | jq .tasks |grep worker_id | sort | uniq -c
    120     "worker_id": "k1:8081"
{code}
 

Then I wait 3 minutes

And I get the final state:
{code:java}
❯ curl -s http://localhost:8081/connectors/s3-connector2/status | jq .tasks |grep worker_id | sort | uniq -c
     60     "worker_id": "k2:8082"
     60     "worker_id": "k3:8083"{code}
 
{code:java}
❯ curl -s http://localhost:8081/connectors/s3-connector1/status | jq .tasks |grep worker_id | sort | uniq -c
     80     "worker_id": "k1:8081"
     20     "worker_id": "k2:8082"
     20     "worker_id": "k3:8083"
{code}
 

In the end, we indeed get 80 tasks on each workers, but for distribution reasons , I think it should be (40, 40, 40) for each connector, because all task don't do the same amount of work, which will lead to a processing/network imbalance overall.



In my test I always get the same outcome.

This is consistent with what we see in production.
~~~~

20.

~~~~
I created https://issues.apache.org/jira/browse/KAFKA-17049
~~~~

---

## KAFKA-10710: MirrorMaker 2 creates all combinations of herders

https://issues.apache.org/jira/browse/KAFKA-10710

Given fix versions: 2.8.0
JIRA affects (masked from the system): 2.5.1

- `KAFKA-10710@2.5.1`: config 2.5.1, metadata answer **affected** (listed_affected)
- `KAFKA-10710@2.5.0`: config 2.5.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 1.0

### Description

~~~~
We are using MM2 distributed to synchronize topics from a "Central" broker down to multiple "Local" brokers. 
{quote}replica_CENTRAL->replica_OLS.enabled = true
 replica_CENTRAL->replica_OLS.topics = _schemas
 replica_CENTRAL->replica_OLS.replication.factor = 3

replica_CENTRAL->replica_HBG.enabled = true
 replica_CENTRAL->replica_HBG.topics = _schemas
 replica_CENTRAL->replica_HBG.replication.factor = 3

...

many more

...

replica_CENTRAL->replica_VIT.enabled = true
 replica_CENTRAL->replica_VIT.topics = _schemas
 replica_CENTRAL->replica_VIT.replication.factor = 3

replica_CENTRAL->replica_UGO.enabled = true
 replica_CENTRAL->replica_UGO.topics = _schemas
 replica_CENTRAL->replica_UGO.replication.factor = 3
{quote}
 

When looking into the Mirror Maker logs, we discover that a herder is created for each combination even if we specifically don't describe a link between 2 clusters

 

Exemples:
{quote}[2020-11-12 08:43:30,351] INFO creating herder for replica_VIT->replica_UGO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:43:33,697] INFO creating herder for replica_CNO->replica_UGO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:43:36,020] INFO creating herder for replica_CENTRAL->replica_OLS (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:43:38,508] INFO creating herder for replica_UMO->replica_UGO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:43:40,438] INFO creating herder for replica_CNO->replica_VIT (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:43:42,898] INFO creating herder for replica_ARA->replica_OLS (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:43:45,457] INFO creating herder for replica_TST->replica_OLS (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:43:47,860] INFO creating herder for replica_UMO->replica_VIT (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:43:50,248] INFO creating herder for replica_OLS->replica_ARA (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:43:52,817] INFO creating herder for replica_UGO->replica_VLD (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:43:54,903] INFO creating herder for replica_HBG->replica_CNO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:43:57,081] INFO creating herder for replica_OLS->replica_TST (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:43:59,215] INFO creating herder for replica_TST->replica_HBG (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:01,481] INFO creating herder for replica_OLS->replica_UMO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:03,320] INFO creating herder for replica_CNO->replica_HBG (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:05,337] INFO creating herder for replica_VIT->replica_HBG (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:07,494] INFO creating herder for replica_CENTRAL->replica_HBG (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:09,595] INFO creating herder for replica_ARA->replica_VIT (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:12,201] INFO creating herder for replica_VLD->replica_CNO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:14,360] INFO creating herder for replica_HBG->replica_VLD (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:16,490] INFO creating herder for replica_OLS->replica_CNO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:18,680] INFO creating herder for replica_ARA->replica_HBG (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:20,779] INFO creating herder for replica_VLD->replica_UGO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:22,596] INFO creating herder for replica_CENTRAL->replica_UGO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:24,579] INFO creating herder for replica_VIT->replica_CENTRAL (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:26,076] INFO creating herder for replica_TST->replica_UMO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:27,868] INFO creating herder for replica_OLS->replica_HBG (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:30,047] INFO creating herder for replica_TST->replica_CNO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:32,295] INFO creating herder for replica_OLS->replica_CENTRAL (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:33,777] INFO creating herder for replica_CNO->replica_OLS (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:36,083] INFO creating herder for replica_CENTRAL->replica_VIT (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:38,857] INFO creating herder for replica_ARA->replica_UGO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:40,629] INFO creating herder for replica_CNO->replica_ARA (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:43,170] INFO creating herder for replica_UGO->replica_HBG (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:45,154] INFO creating herder for replica_HBG->replica_UMO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:46,981] INFO creating herder for replica_UMO->replica_VLD (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:49,042] INFO creating herder for replica_UGO->replica_VIT (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:51,881] INFO creating herder for replica_HBG->replica_ARA (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:54,406] INFO creating herder for replica_HBG->replica_TST (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:56,378] INFO creating herder for replica_TST->replica_ARA (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:44:58,825] INFO creating herder for replica_ARA->replica_CENTRAL (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:00,394] INFO creating herder for replica_CNO->replica_CENTRAL (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:02,060] INFO creating herder for replica_UGO->replica_OLS (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:04,513] INFO creating herder for replica_TST->replica_CENTRAL (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:06,071] INFO creating herder for replica_VLD->replica_OLS (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:08,700] INFO creating herder for replica_CNO->replica_UMO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:10,533] INFO creating herder for replica_VIT->replica_TST (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:12,539] INFO creating herder for replica_CNO->replica_TST (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:14,749] INFO creating herder for replica_HBG->replica_CENTRAL (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:16,222] INFO creating herder for replica_UMO->replica_CNO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:18,308] INFO creating herder for replica_VIT->replica_UMO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:20,212] INFO creating herder for replica_HBG->replica_VIT (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:22,618] INFO creating herder for replica_VLD->replica_HBG (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:24,663] INFO creating herder for replica_UGO->replica_CENTRAL (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:26,333] INFO creating herder for replica_ARA->replica_CNO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:28,408] INFO creating herder for replica_CNO->replica_VLD (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:30,480] INFO creating herder for replica_HBG->replica_OLS (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:32,810] INFO creating herder for replica_VIT->replica_VLD (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:34,904] INFO creating herder for replica_OLS->replica_UGO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:36,893] INFO creating herder for replica_UMO->replica_CENTRAL (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:38,364] INFO creating herder for replica_UMO->replica_ARA (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:40,781] INFO creating herder for replica_OLS->replica_VIT (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:43,168] INFO creating herder for replica_VIT->replica_CNO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:45,215] INFO creating herder for replica_CENTRAL->replica_VLD (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:47,305] INFO creating herder for replica_UMO->replica_TST (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 08:45:49,331] INFO creating herder for replica_VLD->replica_VIT (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:00:16,537] INFO creating herder for replica_VIT->replica_UGO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:00:20,193] INFO creating herder for replica_CNO->replica_UGO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:00:22,410] INFO creating herder for replica_CENTRAL->replica_OLS (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:00:25,009] INFO creating herder for replica_UMO->replica_UGO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:00:26,949] INFO creating herder for replica_CNO->replica_VIT (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:00:29,604] INFO creating herder for replica_ARA->replica_OLS (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:00:32,121] INFO creating herder for replica_TST->replica_OLS (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:00:34,883] INFO creating herder for replica_UMO->replica_VIT (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:00:37,323] INFO creating herder for replica_OLS->replica_ARA (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:00:39,755] INFO creating herder for replica_UGO->replica_VLD (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:00:42,106] INFO creating herder for replica_HBG->replica_CNO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:00:44,425] INFO creating herder for replica_OLS->replica_TST (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:00:46,484] INFO creating herder for replica_TST->replica_HBG (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:00:49,388] INFO creating herder for replica_OLS->replica_UMO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:00:51,300] INFO creating herder for replica_CNO->replica_HBG (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:00:54,560] INFO creating herder for replica_VIT->replica_HBG (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:00:57,861] INFO creating herder for replica_CENTRAL->replica_HBG (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:00,673] INFO creating herder for replica_ARA->replica_VIT (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:03,222] INFO creating herder for replica_VLD->replica_CNO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:05,627] INFO creating herder for replica_HBG->replica_VLD (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:07,752] INFO creating herder for replica_OLS->replica_CNO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:09,947] INFO creating herder for replica_ARA->replica_HBG (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:12,492] INFO creating herder for replica_VLD->replica_UGO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:14,265] INFO creating herder for replica_CENTRAL->replica_UGO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:16,102] INFO creating herder for replica_VIT->replica_CENTRAL (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:17,661] INFO creating herder for replica_TST->replica_UMO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:19,440] INFO creating herder for replica_OLS->replica_HBG (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:22,479] INFO creating herder for replica_TST->replica_CNO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:24,830] INFO creating herder for replica_OLS->replica_CENTRAL (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:26,478] INFO creating herder for replica_CNO->replica_OLS (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:29,179] INFO creating herder for replica_CENTRAL->replica_VIT (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:31,616] INFO creating herder for replica_ARA->replica_UGO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:33,467] INFO creating herder for replica_CNO->replica_ARA (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:35,816] INFO creating herder for replica_UGO->replica_HBG (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:37,937] INFO creating herder for replica_HBG->replica_UMO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:40,195] INFO creating herder for replica_UMO->replica_VLD (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:42,318] INFO creating herder for replica_UGO->replica_VIT (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:44,688] INFO creating herder for replica_HBG->replica_ARA (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:47,083] INFO creating herder for replica_HBG->replica_TST (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:49,199] INFO creating herder for replica_TST->replica_ARA (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:51,516] INFO creating herder for replica_ARA->replica_CENTRAL (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:53,042] INFO creating herder for replica_CNO->replica_CENTRAL (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:54,575] INFO creating herder for replica_UGO->replica_OLS (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:57,081] INFO creating herder for replica_TST->replica_CENTRAL (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:01:58,540] INFO creating herder for replica_VLD->replica_OLS (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:01,584] INFO creating herder for replica_CNO->replica_UMO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:03,401] INFO creating herder for replica_VIT->replica_TST (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:05,714] INFO creating herder for replica_CNO->replica_TST (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:07,664] INFO creating herder for replica_HBG->replica_CENTRAL (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:09,246] INFO creating herder for replica_UMO->replica_CNO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:11,565] INFO creating herder for replica_VIT->replica_UMO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:13,451] INFO creating herder for replica_HBG->replica_VIT (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:15,872] INFO creating herder for replica_VLD->replica_HBG (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:18,094] INFO creating herder for replica_UGO->replica_CENTRAL (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:19,597] INFO creating herder for replica_ARA->replica_CNO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:21,576] INFO creating herder for replica_CNO->replica_VLD (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:23,834] INFO creating herder for replica_HBG->replica_OLS (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:26,410] INFO creating herder for replica_VIT->replica_VLD (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:28,516] INFO creating herder for replica_OLS->replica_UGO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:30,344] INFO creating herder for replica_UMO->replica_CENTRAL (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:31,850] INFO creating herder for replica_UMO->replica_ARA (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:34,094] INFO creating herder for replica_OLS->replica_VIT (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:36,743] INFO creating herder for replica_VIT->replica_CNO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:38,778] INFO creating herder for replica_CENTRAL->replica_VLD (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:40,785] INFO creating herder for replica_UMO->replica_TST (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:42,816] INFO creating herder for replica_VLD->replica_VIT (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:45,225] INFO creating herder for replica_VLD->replica_CENTRAL (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:46,659] INFO creating herder for replica_ARA->replica_VLD (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:48,729] INFO creating herder for replica_TST->replica_VLD (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:50,722] INFO creating herder for replica_TST->replica_UGO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:52,387] INFO creating herder for replica_UGO->replica_UMO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:54,326] INFO creating herder for replica_CENTRAL->replica_UMO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:56,085] INFO creating herder for replica_ARA->replica_UMO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:57,914] INFO creating herder for replica_VLD->replica_UMO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:02:59,665] INFO creating herder for replica_ARA->replica_TST (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:03:01,717] INFO creating herder for replica_OLS->replica_VLD (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:03:03,832] INFO creating herder for replica_UGO->replica_ARA (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:03:06,278] INFO creating herder for replica_VLD->replica_TST (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:03:08,417] INFO creating herder for replica_CENTRAL->replica_CNO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:03:10,731] INFO creating herder for replica_UGO->replica_TST (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:03:12,712] INFO creating herder for replica_TST->replica_VIT (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:03:15,082] INFO creating herder for replica_VIT->replica_OLS (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:03:17,439] INFO creating herder for replica_VLD->replica_ARA (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:03:19,800] INFO creating herder for replica_HBG->replica_UGO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:03:21,554] INFO creating herder for replica_UMO->replica_HBG (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:03:23,536] INFO creating herder for replica_VIT->replica_ARA (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:03:26,041] INFO creating herder for replica_CENTRAL->replica_TST (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:03:28,090] INFO creating herder for replica_UGO->replica_CNO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:03:30,353] INFO creating herder for replica_CENTRAL->replica_ARA (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-12 09:03:32,826] INFO creating herder for replica_UMO->replica_OLS (org.apache.kafka.connect.mirror.MirrorMaker)
{quote}
So much that we reached the limit of our user property LimitNOFILE recently when trying to add a new "Local" cluster.

I believe this behavior leads to unecessary connections and resource usage that could be easily avoided by just limiting the herder creation only to elements specifically described in the mirrormaker.properties file

[https://github.com/apache/kafka/blob/trunk/connect/mirror/src/main/java/org/apache/kafka/connect/mirror/MirrorMaker.java#L130-L136]

 
~~~~

### Comments (1)

1.

~~~~
Results with fix provided in PR:
{code:java}
[2020-11-13 15:53:53,935] INFO creating herder for replica_CENTRAL->replica_ZAR (org.apache.kafka.connect.mirror.MirrorMaker) 
[2020-11-13 15:53:58,597] INFO creating herder for replica_CENTRAL->replica_UGO (org.apache.kafka.connect.mirror.MirrorMaker) 
[2020-11-13 15:54:01,180] INFO creating herder for replica_CENTRAL->replica_HBG (org.apache.kafka.connect.mirror.MirrorMaker) 
[2020-11-13 15:54:03,656] INFO creating herder for replica_CENTRAL->replica_OLS (org.apache.kafka.connect.mirror.MirrorMaker) 
[2020-11-13 15:54:06,097] INFO creating herder for replica_CENTRAL->replica_UMO (org.apache.kafka.connect.mirror.MirrorMaker) 
[2020-11-13 15:54:08,186] INFO creating herder for replica_OLS->replica_CENTRAL (org.apache.kafka.connect.mirror.MirrorMaker) 
[2020-11-13 15:54:09,774] INFO creating herder for replica_CENTRAL->replica_CNO (org.apache.kafka.connect.mirror.MirrorMaker)
[2020-11-13 15:54:12,253] INFO creating herder for replica_CENTRAL->replica_TST (org.apache.kafka.connect.mirror.MirrorMaker) 
[2020-11-13 15:54:14,407] INFO creating herder for replica_CENTRAL->replica_VLD (org.apache.kafka.connect.mirror.MirrorMaker) 
[2020-11-13 15:54:16,599] INFO creating herder for replica_CENTRAL->replica_ARA (org.apache.kafka.connect.mirror.MirrorMaker) 
[2020-11-13 15:54:19,005] INFO creating herder for replica_CENTRAL->replica_VIT (org.apache.kafka.connect.mirror.MirrorMaker) 
[2020-11-13 15:54:21,789] INFO Kafka MirrorMaker starting with 11 herders. (org.apache.kafka.connect.mirror.MirrorMaker){code}

 Before fix
 Main PID: 880 (java) Tasks: 2204 Memory: 2.9G
  
 Afterfix :
 Main PID: 48881 (java) Tasks: 224 Memory: 1.0G
~~~~

---

## KAFKA-12165: org.apache.kafka.common.quota classes omitted from Javadoc

https://issues.apache.org/jira/browse/KAFKA-12165

Given fix versions: 2.8.0
JIRA affects (masked from the system): 2.7.0

- `KAFKA-12165@2.7.0`: config 2.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-12165@2.6.3`: config 2.6.3, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
The public API classes in `org.apache.kafka.common.quota` should be included in the javadoc, but are currently omitted. E.g. see https://kafka.apache.org/27/javadoc/org/apache/kafka/clients/admin/Admin.html#alterClientQuotas-java.util.Collection-
~~~~

---

## KAFKA-12303: Flatten SMT drops some fields when null values are present

https://issues.apache.org/jira/browse/KAFKA-12303

Given fix versions: 3.0.0
JIRA affects (masked from the system): 2.0.1, 2.1.1, 2.2.2, 2.3.1, 2.4.1, 2.5.1, 2.6.1, 2.7.0, 2.8.0

- `KAFKA-12303@2.3.1`: config 2.3.1, metadata answer **affected** (listed_affected)
- `KAFKA-12303@2.0.0`: config 2.0.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
[This line|https://github.com/apache/kafka/blob/0bc394cc1d19f1e41dd6646e9ac0e09b91fb1398/connect/transforms/src/main/java/org/apache/kafka/connect/transforms/Flatten.java#L109] should be {{continue}} instead of {{return}}; otherwise, the rest of the entries in the currently-being-iterated map are skipped unnecessarily.
~~~~

---

## KAFKA-12308: ConfigDef.parseType deadlock

https://issues.apache.org/jira/browse/KAFKA-12308

Given fix versions: 3.0.0
JIRA affects (masked from the system): 2.5.0

- `KAFKA-12308@2.5.0`: config 2.5.0, metadata answer **affected** (listed_affected)
- `KAFKA-12308@2.4.1`: config 2.4.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
hi,
 the problem was found, when I restarted *ConnectDistributed*

I restart ConnectDistributed in the single node for the test, with not delete connectors.
 sometimes the process stopped when creating connectors.

I add some logger and found it had a deadlock in `ConfigDef.parseType`.My connectors always have the same transforms. I guess when connector startup (in startAndStopExecutor which default 8 threads) and load the same class file it has something wrong.

I attached the jstack log file.

thanks for any help.
~~~~

### Comments (4)

1.

~~~~
I think this is caused by the fact the {{DelegatingClassLoader}} is not registered as parallel capable, but should be. It should be because, according to https://docs.oracle.com/javase/7/docs/technotes/guides/lang/cl-mt.html, to qualify for the acyclic delegation model "If the class is not found, the class loader asks its parent to locate the class. If the parent cannot find the class, the class loader attempts to locate the class itself.", but {{DelegatingClassLoader}} may actually ask the {{PluginClassLoader}} to load a class before it's tried {{super}}.

From the stack dump provided
{noformat}
"StartAndStopExecutor-connect-1-5":
	at java.lang.ClassLoader.loadClass(ClassLoader.java:398)                                              // wait for DCL getClassLoadingLock
	- waiting to lock <0x00000006c222db00> (a org.apache.kafka.connect.runtime.isolation.DelegatingClassLoader)
	at org.apache.kafka.connect.runtime.isolation.DelegatingClassLoader.loadClass(DelegatingClassLoader.java:397) // deletate to super
	at java.lang.ClassLoader.loadClass(ClassLoader.java:405)                                              // super delegates to parent (DCL)
	- locked <0x000000077b9bf3c0> (a java.lang.Object)                                                    // lock PCLY+name (super's getClassLoadingLock)
	at org.apache.kafka.connect.runtime.isolation.PluginClassLoader.loadClass(PluginClassLoader.java:104)
	- locked <0x000000077b9bf3c0> (a java.lang.Object)                                                    // lock PCLY+name (getClassLoadingLock)
	- locked <0x00000006c25b4e38> (a org.apache.kafka.connect.runtime.isolation.PluginClassLoader)        // lock PCLY (synchronized)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:351)
	at java.lang.Class.forName0(Native Method)
	at java.lang.Class.forName(Class.java:348)
{noformat}

and 

{noformat}
"StartAndStopExecutor-connect-1-6":
	at org.apache.kafka.connect.runtime.isolation.PluginClassLoader.loadClass(PluginClassLoader.java:91) // lock PCLX (synchronized)
	- waiting to lock <0x00000006c25b4e38> (a org.apache.kafka.connect.runtime.isolation.PluginClassLoader)
	at org.apache.kafka.connect.runtime.isolation.DelegatingClassLoader.loadClass(DelegatingClassLoader.java:394) // delegated to PCL
	at java.lang.ClassLoader.loadClass(ClassLoader.java:351)                                             // ClassLoader.loadClass(String name) calling PCL.loadClass(String,
	at java.lang.Class.forName0(Native Method)
	at java.lang.Class.forName(Class.java:348)
{noformat}

It also says 

{noformat}
"StartAndStopExecutor-connect-1-5":
  waiting to lock monitor 0x00000203a553b6f8 (object 0x00000006c222db00, a org.apache.kafka.connect.runtime.isolation.DelegatingClassLoader),
  which is held by "StartAndStopExecutor-connect-1-6"
{noformat}

the {{0x00000006c222db00}} doesn't appear in the stacktrace, I think that's because it's [held by the JVM itself|https://github.com/openjdk/jdk/blob/06170b7cbf6129274747b4406562184802d4ff07/src/hotspot/share/classfile/systemDictionary.cpp#L695]. 

If DelegatingClassloader is registered as parallel capable this won't happen

{noformat}
	at java.lang.ClassLoader.loadClass(ClassLoader.java:398)                                              // wait for DCL getClassLoadingLock
	- waiting to lock <0x00000006c222db00> (a org.apache.kafka.connect.runtime.isolation.DelegatingClassLoader)
{noformat}

Because {{DCL.getClassLoadingLock}} will return an object specific to the class being loaded, rather than the DCL instance itself, which is locked by the JVM.

Does this seem plausible to you [~kkonstantine] [~ChrisEgerton]?
~~~~

2.

~~~~
[~tombentley] I actually think that the initial suggestion in https://issues.apache.org/jira/browse/KAFKA-7421 regarding the removal of the method lock is correct. 

The `DelegatingClassLoader` doesn't seem to need to be parallel because it delegates loading to either `PluginClassLoader` instances that are parallel capable or the parent which normally is the system classloader and should also be parallel. 

Note, that the loading sequence that you mention above, is inverted on purpose to actually implement classloading isolation. First we attempt loading the class from the "child" `PluginClassLoader` of the designated plugin and if not found then the parent classloader of the `DelegatingClassLoader` is consulted. 

I have updated the PR that had added a test for this type of deadlock originally submitted by [~gharris1727] in: 
 [https://github.com/apache/kafka/pull/8259]

cc [~rhauch]
~~~~

3.

~~~~
[~kkonstantine] I'm not an expert in classloaders but I'm still not sure that DCL shouldn't be considered parallel. The referred class loader guide explicitly says that an acyclic CL should delegate to {{super}} _first_. I understand that delegating to PCL first is intentional, but it doesn't fit with the definition given AFAICS. The fact that the CLs it delegates to are both parallel doesn't seem to be relevant. Also, the parent of the PCL is the DCL, which looks like a cycle to me (but, as I said, I'm no expert, so happy to be corrected). 

Assuming the {{synchronized}} was removed from PCL {{loadClass}}, then 
{noformat}
"StartAndStopExecutor-connect-1-6":
	at org.apache.kafka.connect.runtime.isolation.PluginClassLoader.loadClass(PluginClassLoader.java:91) // lock PCLX (synchronized)
{noformat}
wouldn't get blocked, but there would still be two threads contenting two locks when racing to load the same class, those locks would be the {{getClassLoadingLock()}} on the PCL and the monitor of the DCL instance itself, so I think perhaps a deadlock would still be possible, just on different monitors. 
~~~~

4.

~~~~
Adding the comment that I added in the PR here as well: 



The idea that the {{DelegatingClassLoader}} did not have to be parallel capable originated to the fact that it doesn't load classes directly. It delegates loading either to the appropriate PluginClassLoader directly via composition, or to the parent by calling {{super.loadClass}}.

The latter is the key point of why we need to make the {{DelegatingClassLoader}} also parallel capable even though it doesn't load a class. Because inheritance is used (via a call to {{super.loadClass}}) and not composition (via a hypothetical call to {{parent.loadClass}}, which is not possible because {{parent}} is a private member of the base abstract class {{ClassLoader}}) when {{getClassLoadingLock}} is called in {{super.loadClass}} it checks that actually the derived class (here an instance of {{DelegatingClassLoader}}) is not parallel capable and therefore ends up not applying fine-grain locking during classloading even though the parent clasloader is used actually load the classes.

Based on the above, the {{DelegatingClassLoader}} needs to be parallel capable too in order for the parent loader to load classes in parallel. 

I've tested both classloader types being parallel capable in a variety of scenarios with multiple connectors, SMTs and converters and a deadlock did not reproduce. Of course reproducing the issue is difficult without the specifics of the jar layout to begin with. The possibility of a deadlock is still not zero, but also probably not exacerbated compared to the current code. The plugin that depends on other plugins to be loaded while it's loading its classes is the connector type plugin only and there are no inter-connector dependencies (a connector requiring another connector's classes to be loaded while loading its own). With that in mind, a deadlock should be even less possible now. In the future we could consider introducing deadlock recovery methods to get out of this type of situation if necessary.
~~~~

---

## KAFKA-13106: Offsets deletion error

https://issues.apache.org/jira/browse/KAFKA-13106

Given fix versions: 2.7.0
JIRA affects (masked from the system): 2.3.1, 2.7.0

- `KAFKA-13106@2.3.1`: config 2.3.1, metadata answer **affected** (listed_affected)
- `KAFKA-13106@2.3.0`: config 2.3.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.3.1

### Description

~~~~
When I use:

kafka-consumer-groups.sh --bootstrap-server broker:9092 --delete-offsets --group myGroup --topic myTopic

 

I have a error:

 

SLF4J: Class path contains multiple SLF4J bindings.

SLF4J: Found binding in [jar:file:/kafka/libs/slf4j-log4j12-1.7.26.jar!/org/slf4j/impl/StaticLoggerBinder.class]

SLF4J: Found binding in [jar:file:/kafka/libs/slf4j-log4j12-1.7.30.jar!/org/slf4j/impl/StaticLoggerBinder.class]

SLF4J: See [http://www.slf4j.org/codes.html#multiple_bindings] for an explanation.

SLF4J: Actual binding is of type [org.slf4j.impl.Log4jLoggerFactory]

Exception in thread "main" joptsimple.UnrecognizedOptionException: delete-offsets is not a recognized option

        at joptsimple.OptionException.unrecognizedOption(OptionException.java:108)

        at joptsimple.OptionParser.handleLongOptionToken(OptionParser.java:510)

        at joptsimple.OptionParserState$2.handleArgument(OptionParserState.java:56)

        at joptsimple.OptionParser.parse(OptionParser.java:396)

        at kafka.admin.ConsumerGroupCommand$ConsumerGroupCommandOptions.<init>(ConsumerGroupCommand.scala:917)

        at kafka.admin.ConsumerGroupCommand$.main(ConsumerGroupCommand.scala:46)

        at kafka.admin.ConsumerGroupCommand.main(ConsumerGroupCommand.scala)

 


 When I use kafka protocol base on:
 [https://kafka.apache.org/protocol#The_Messages_OffsetDelete]
 
 I have kafka log:
 
 [2021-07-20 07:23:37,832] ERROR Closing socket for 10.1.1.20:9092-192.168.65.3:56050-0 because of error (kafka.network.Processor)

org.apache.kafka.common.errors.InvalidRequestException: Unknown API key 47

[2021-07-20 07:23:37,835] ERROR Exception while processing request from 10.1.1.20:9092-192.168.65.3:56050-0 (kafka.network.Processor)

org.apache.kafka.common.errors.InvalidRequestException: Unknown API key 47
 
 
 Base on:
 [https://cwiki.apache.org/confluence/display/KAFKA/KIP-496%3A+Administrative+API+to+delete+consumer+offsets]
 
 Those things should be working.
~~~~

### Comments (1)

1.

~~~~
version 2.3.1 does not suport it
~~~~

---

## KAFKA-13197: KStream-GlobalKTable join semantics don't match documentation

https://issues.apache.org/jira/browse/KAFKA-13197

Given fix versions: 3.5.2, 3.6.0
JIRA affects (masked from the system): 2.7.0

- `KAFKA-13197@2.7.0`: config 2.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-13197@2.6.3`: config 2.6.3, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.7

### Description

~~~~
As part of KAFKA-10277, the behavior of KStream-GlobalKTable joins was changed. It appears the change was intended to merely relax a requirement but it actually broke backwards compatibility. Although it does allow {{null}} keys and values in the KStream to be joined, it now excludes {{null}} results of the {{KeyValueMapper}}. We have an application which can return {{null}} from the {{KeyValueMapper}} for non-null keys in the KStream, and relies on these nulls being passed to the {{ValueJoiner}}. Indeed the javadoc still explicitly says this is done:
{quote}If a KStream input record key or value is null the record will not be included in the join operation and thus no output record will be added to the resulting KStream.
 If keyValueMapper returns null implying no match exists, a null value will be provided to ValueJoiner.
{quote}
Both these statements are incorrect.

I think the new behavior is worse than the previous/documented behavior. It feels more reasonable to have a non-null stream record map to a null join key (our use-case is event-enhancement where the incoming record doesn't have the join field), than the reverse.
~~~~

### Comments (3)

1.

~~~~
Thanks for filing this [~twbecker]. The current doc says "If {@code keyValueMapper} returns {@code null} implying no match exists, no output record will be added to the resulting {@code KStream}." But I read the tickets and I think you are right: this property is not very reasonable since users may want to know if a single stream record does not find any matching results as well.

I think the reasonable behavior (and the java doc should be updated accordingly) in KAFKA-10277 should be

{code}
If the keyValueMapper returns null implying no matching key found, the ValueJoiner would still be triggered with (null, v, null).
{code}

Does that sound right to you?
~~~~

2.

~~~~
Hey [~guozhang] thanks for the response. To be clear, I'm looking at {{KStream.leftJoin(GlobalKTable, KeyValueMapper, ValueJoiner)}} as shown [here|https://github.com/apache/kafka/blob/trunk/streams/src/main/java/org/apache/kafka/streams/kstream/KStream.java#L2964] and similar signatures, which still have the (incorrect) verbiage I quoted.

It seems from the churn in this area that there is a need to allow both null stream key/value records as well as non-null stream side records that map to null join keys,, though my use-case and this issue are specifically about the latter, which used to work prior to 2.7.
~~~~

3.

~~~~
[~twbecker], thanks for raising this. The documentation has been fixed.
KIP-962 will allow for the old behavior again: 'no longer drop records when KeyValueMapper returns 'null' and call ValueJoiner with 'null' for right value'.
~~~~

---

## KAFKA-13214: Consumer should not reset group state after disconnect

https://issues.apache.org/jira/browse/KAFKA-13214

Given fix versions: 2.7.2, 2.8.1, 3.0.0
JIRA affects (masked from the system): 2.7.0, 2.8.0

- `KAFKA-13214@2.8.0`: config 2.8.0, metadata answer **affected** (listed_affected)
- `KAFKA-13214@2.6.3`: config 2.6.3, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
When the consumer disconnects from the coordinator while a rebalance is in progress, we currently reset the memberId and generation. The coordinator then must await the session timeout in order to expire the old memberId. This was apparently a regression from https://github.com/apache/kafka/commit/7e7bb184d2abe34280a7f0eb0f0d9fc0e32389f2#diff-15efe9b844f78b686393b6c2e2ad61306c3473225742caed05c7edab9a138832R478. It would be better to keep the memberId/generation.
~~~~

---

## KAFKA-13488: Producer fails to recover if topic gets deleted (and gets auto-created)

https://issues.apache.org/jira/browse/KAFKA-13488

Given fix versions: 2.8.2, 3.0.1, 3.1.0
JIRA affects (masked from the system): 2.2.2, 2.3.1, 2.4.1, 2.5.1, 2.6.3, 2.7.2, 2.8.1

- `KAFKA-13488@2.2.2`: config 2.2.2, metadata answer **affected** (listed_affected)
- `KAFKA-13488@2.2.1`: config 2.2.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
Producer currently fails to produce messages to a topic if the topic is deleted and gets auto-created OR is created manually during the lifetime of the producer (and certain other conditions are met - leaderEpochs of deleted topic > 0).

 

To reproduce, these are the steps which can be carried out:

0) A cluster with 2 brokers 0 and 1 with auto.topic.create=true.

1) Create a topic T with 2 partitions P0-> (0,1), P1-> (0,1)

2) Reassign the partitions such that P0-> (1,0), P1-> (1,0).

2) Create a producer P and send few messages which land on all the TPs of topic T.

3) Delete the topic T

4) Immediately, send a new message from producer P, this message will be failed to send and eventually timed out.

A test-case which fails with the above steps is added at the end as well as a patch file.

 

This happens after leaderEpoch (KIP-320) was introduced in the MetadataResponse KAFKA-7738. There is a solution attempted to fix this issue in KAFKA-12257, but the solution has a bug due to which the above use-case still fails.

 

*Issue in the solution of KAFKA-12257:*
{code:java}
// org.apache.kafka.clients.Metadata.handleMetadataResponse():
       ...
        Map<String, Uuid> topicIds = new HashMap<>();
        Map<String, Uuid> oldTopicIds = cache.topicIds();
        for (MetadataResponse.TopicMetadata metadata : metadataResponse.topicMetadata()) {
            String topicName = metadata.topic();
            Uuid topicId = metadata.topicId();
            topics.add(topicName);
            // We can only reason about topic ID changes when both IDs are valid, so keep oldId null unless the new metadata contains a topic ID
            Uuid oldTopicId = null;
            if (!Uuid.ZERO_UUID.equals(topicId)) {
                topicIds.put(topicName, topicId);
                oldTopicId = oldTopicIds.get(topicName);
            } else {
                 topicId = null;
            }
    ...
} {code}
With every new call to {{{}handleMetadataResponse{}}}(), {{cache.topicIds()}} gets created afresh. When a topic is deleted and created immediately soon afterwards (because of auto.create being true), producer's call to {{MetadataRequest}} for the deleted topic T will result in a {{UNKNOWN_TOPIC_OR_PARTITION}} or {{LEADER_NOT_AVAILABLE}} error {{MetadataResponse}} depending on which point of topic recreation metadata is being asked at. In the case of errors, TopicId returned back in the response is {{{}Uuid.ZERO_UUID{}}}. As seen in the above logic, if the topicId received is ZERO, the method removes the earlier topicId entry from the cache.

Now, when a non-Error Metadata Response does come back for the newly created topic T, it will have a non-ZERO topicId now but the leaderEpoch for the partitions will mostly be ZERO. This situation will lead to rejection of the new MetadataResponse if the older LeaderEpoch was >0 (for more details, refer to KAFKA-12257). Because of the rejection of the metadata, producer will never get to know the new Leader of the TPs of the newly created topic.

 

{{*}} 1. Solution / Fix (Preferred){*}:
Client's metadata should keep on remembering the old topicId till:
1) response for the TP has ERRORs
2) topicId entry was already present in the cache earlier
3) retain time is not expired
{code:java}
--- a/clients/src/main/java/org/apache/kafka/clients/Metadata.java
+++ b/clients/src/main/java/org/apache/kafka/clients/Metadata.java
@@ -336,6 +336,10 @@ public class Metadata implements Closeable {
                 topicIds.put(topicName, topicId);
                 oldTopicId = oldTopicIds.get(topicName);
             } else {
+                // Retain the old topicId for comparison with newer TopicId created later. This is only needed till retainMs
+                if (metadata.error() != Errors.NONE && oldTopicIds.get(topicName) != null && retainTopic(topicName, false, nowMs))
+                    topicIds.put(topicName, oldTopicIds.get(topicName));
+                else
                     topicId = null;
             }

{code}
{{*}} 2. Alternative Solution / Fix {{*}}:
To allow updates to LeaderEpoch when originalTopicId was {{{}null{}}}. This is less desirable as when cluster moves from no topic IDs to using topic IDs, we will count this topic as new and update LeaderEpoch irrespective of whether newEpoch was greater than current or not.
{code:java}
@@ -394,7 +398,7 @@ public class Metadata implements Closeable {
         if (hasReliableLeaderEpoch && partitionMetadata.leaderEpoch.isPresent()) {
             int newEpoch = partitionMetadata.leaderEpoch.get();
             Integer currentEpoch = lastSeenLeaderEpochs.get(tp);
-            if (topicId != null && oldTopicId != null && !topicId.equals(oldTopicId)) {
+            if (topicId != null && !topicId.equals(oldTopicId)) {
                 // If both topic IDs were valid and the topic ID changed, update the metadata
                 log.info("Resetting the last seen epoch of partition {} to {} since the associated topicId changed from {} to {}",
                          tp, newEpoch, oldTopicId, topicId);
{code}
From the above discussion, i think Solution 1 would be a better solution.

–
Testcase to repro the issue:
{code:java}
  @Test
  def testSendWithTopicDeletionMidWay(): Unit = {
    val numRecords = 10

    // create topic with leader as 0 for the 2 partitions.
    createTopic(topic, Map(0 -> Seq(0, 1), 1 -> Seq(0, 1)))

    val reassignment = Map(
      new TopicPartition(topic, 0) -> Seq(1, 0),
      new TopicPartition(topic, 1) -> Seq(1, 0)
    )

    // Change leader to 1 for both the partitions to increase leader Epoch from 0 -> 1
    zkClient.createPartitionReassignment(reassignment)
    TestUtils.waitUntilTrue(() => !zkClient.reassignPartitionsInProgress,
      "failed to remove reassign partitions path after completion")

    val producer = createProducer(brokerList, maxBlockMs = 5 * 1000L, deliveryTimeoutMs = 20 * 1000)

    (1 to numRecords).map { i =>
      val resp = producer.send(new ProducerRecord(topic, null, ("value" + i).getBytes(StandardCharsets.UTF_8))).get
      assertEquals(topic, resp.topic())
    }

    // start topic deletion
    adminZkClient.deleteTopic(topic)

    // Verify that the topic is deleted when no metadata request comes in
    TestUtils.verifyTopicDeletion(zkClient, topic, 2, servers)
    
    // Producer would timeout and not self-recover after topic deletion.
    val e = assertThrows(classOf[ExecutionException], () => producer.send(new ProducerRecord(topic, null, ("value").getBytes(StandardCharsets.UTF_8))).get)
    assertEquals(classOf[TimeoutException], e.getCause.getClass)
  }
{code}
Attaching the solution proposal and test repro as a patch file.
~~~~

### Comments (8)

1.

~~~~
[~jolshan] [~hachikuji] Let me know your thoughts on the solution proposal (as you've worked on the prior [PR|https://github.com/apache/kafka/pull/10952] to this). I will create the PR with more test cases with the fix.
~~~~

2.

~~~~
To clarify, did KAFKA-12257 make this issue worse, or just didn't fix it all the way? 
~~~~

3.

~~~~
[~jolshan] KAFKA-12257 doesn't fix it all the way.
~~~~

4.

~~~~
[~prat0318] Thanks for the investigation and the patch. Would you mind opening a pull request to https://github.com/apache/kafka? In general, I think we probably need to be looser in the epoch check to allow for these kinds of cases. The consequence of taking stale metadata is much less severe than the potential for the client to get stuck. It is tempting to go as far as saying that we _only_ rely on the leader epoch check when the topicId matches.
~~~~

5.

~~~~
For sake of simplicity, i would go with Solution 2 i.e. accept the new epochs in case of old topicId is null.
~~~~

6.

~~~~
[~hachikuji] I have raised [https://github.com/apache/kafka/pull/11552] to fix this.
~~~~

7.

~~~~
Hi [~hachikuji] [~jolshan] I have incorporated the review suggestions to the PR: [https://github.com/apache/kafka/pull/11552]. PTAL.
~~~~

8.

~~~~
Fixed in https://github.com/apache/kafka/pull/11552
~~~~

---

## KAFKA-13558: NioEchoServer fails to close resources

https://issues.apache.org/jira/browse/KAFKA-13558

Given fix versions: 3.2.0
JIRA affects (masked from the system): 3.0.0

- `KAFKA-13558@3.0.0`: config 3.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-13558@2.8.2`: config 2.8.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
{{NioEchoServer}} does not close the selectors that it opens. The result of this can be manifested in flaky tests because the JVM/OS can run out of available file descriptors if the {{NioEchoServer}} is used in a lot of tests. Each test then leaks a handful of descriptors, and eventually the 'too many open files' error is thrown.

This was compounded because the {{NioEchoServer}} intentionally doesn't output stack traces, so the underlying issue was hidden and was manifest in odd (flaky) ways in tests.
~~~~

---

## KAFKA-13600: Rebalances while streams is in degraded state can cause stores to be reassigned and restore from scratch

https://issues.apache.org/jira/browse/KAFKA-13600

Given fix versions: 3.2.0
JIRA affects (masked from the system): 2.8.1, 3.0.0, 3.1.0

- `KAFKA-13600@2.8.1`: config 2.8.1, metadata answer **affected** (listed_affected)
- `KAFKA-13600@2.8.0`: config 2.8.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
Consider this scenario:
 # A node is lost from the cluster.
 # A rebalance is kicked off with a new "target assignment"'s(ie the rebalance is attempting to move a lot of tasks - see https://issues.apache.org/jira/browse/KAFKA-10121).
 # The kafka cluster is now a bit more sluggish from the increased load.
 # A Rolling Deploy happens triggering rebalances, during the rebalance processing continues but offsets can't be committed(Or nodes are restarted but fail to commit offsets)
 # The most caught up nodes now aren't within `acceptableRecoveryLag` and so the task is started in it's "target assignment" location, restoring all state from scratch and delaying further processing instead of using the "almost caught up" node.

We've hit this a few times and having lots of state (~25TB worth) and being heavy users of IQ this is not ideal for us.

While we can increase `acceptableRecoveryLag` to larger values to try get around this that causes other issues (ie a warmup becoming active when its still quite far behind)



The solution seems to be to balance "balanced assignment" with "most caught up nodes".

We've got a fork where we do just this and it's made a huge difference to the reliability of our cluster.

Our change is to simply use the most caught up node if the "target node" is more than `acceptableRecoveryLag` behind.
This gives up some of the load balancing type behaviour of the existing code but in practise doesn't seem to matter too much.

I guess maybe an algorithm that identified candidate nodes as those being within `acceptableRecoveryLag` of the most caught up node might allow the best of both worlds.

 

Our fork is

[https://github.com/apache/kafka/compare/trunk...tim-patterson:fix_balance_uncaughtup?expand=1]
(We also moved the capacity constraint code to happen after all the stateful assignment to prioritise standby tasks over warmup tasks)

Ideally we don't want to maintain a fork of kafka streams going forward so are hoping to get a bit of discussion / agreement on the best way to handle this.
More than happy to contribute code/test different algo's in production system or anything else to help with this issue
~~~~

### Comments (11)

1.

~~~~
[~tim.patterson] Thanks for filing this ticket.

I'd like to clarify a few things to help my own understanding here: in step 5, "The most caught up nodes now aren't within `acceptableRecoveryLag` and so the task is started in it's "target assignment" location" could you explain a bit more about this? For a specific task, let's say it has an ongoing active host say A a.k.a. the most caught up node, and then a target host B which is not yet caught up. Let's say due to commit failure the active host A fails out of the `acceptableRecoveryLag`, A's lag should still be smaller than B so that the task would stay with A until B's within the `acceptableRecoveryLag`. Am I reading it wrong?
~~~~

2.

~~~~
[~guozhang] Thats the desired result and the change I've made.
The current Implementation in Master only considers placing the task on nodes returned by this method

[https://github.com/apache/kafka/blob/trunk/streams/src/main/java/org/apache/kafka/streams/processor/internals/assignment/HighAvailabilityTaskAssignor.java#L235]

So as soon as active hosts A falls out of the `acceptableRecoveryLag` in your example it will jump to target host B, even if the lag on target host B is far far behind(ie just starting to restore)
~~~~

3.

~~~~
Thinking about it, the same problem can be hit when we lose a node and some of the standby tasks for the lost actives have fallen a bit behind for whatever reason, In this case it wont promote the standbys to actives but instead start restoring those tasks from scratch on some other node
~~~~

4.

~~~~
[~tim.patterson] I checked the assignor code and I agree with you that we only distinguish between caught-up and not caught-up. IIRC, we decided to go that way since considering task load and the rank of non caught-up clients turned out to be more complicated that we wanted to make the assignment algorithm, at that time.
If you have found a good trade-off between those dimensions, the best thing is to write up your proposal in a KIP. Although this change would not affect the public API, we usually discuss changes to the assignment algorithms in KIPs because they imply important behavioral changes. [KIP-441|https://cwiki.apache.org/confluence/x/0i4lBg] and [KIP-708|https://cwiki.apache.org/confluence/x/UQ5RCg] are examples for such KIPs.
~~~~

5.

~~~~
Thanks [~cadonna] 
I'm not sure I have the perfect solution either, more just raising this to point out a bit of a hole in the existing implementation.
I do wonder if simply changing the definition of "caught up" in `tasksToCaughtUpClients` from "within acceptableRecoveryLag of the head of the changelog topic" to "within acceptableRecoveryLag of the most caught up client" might solve 80% of the issues with 20% of the effort/risk...

I'll have a bit of a read through the KIP process and have a bit more of a think.
~~~~

6.

~~~~
[~tim.patterson] To come up with a perfect solution is not easy with such an optimization problem. If you think your solution is a good trade-off and you have good arguments then I think it is worth discussing on a KIP.

I am not sure that changing the definition of caught-up as you proposed is so straight forward. For example, in the case where all clients have no or little state all clients would be considered caught-up and the balance might suffer. What I want to say is that it is probably not just a change of a definition.

If you are interested, in the past I looked at the [linear balanced assignment problem|https://en.wikipedia.org/wiki/Assignment_problem#Balanced_assignment]. I considered the [Hungarian algorithm|https://en.wikipedia.org/wiki/Hungarian_algorithm] for a solution, more specifically I looked at [one of the most popular variants|https://link.springer.com/article/10.1007%2FBF02278710]. But I did not have time to go deep enough.
~~~~

7.

~~~~
Hi [~tim.patterson] , thanks for the report and the patch!

 

It sounds like you're reporting two things here:
 # a bug around the acceptable recovery lag.
 # an improvement on assignment balance

If we can discuss those things independently, then we can definitely merge the bugfix immediately. Depending on the impact of the improvement, it might also fall into the category of a simple ticket, or it might be more appropriate to have a KIP as [~cadonna] suggested.

Regarding the bug, I find it completely plausible that we have a bug, but I have to confess that I'm not 100% sure I understand the report. Is the situation that there's an active that's happens to be processing quite a bit ahead of the replicas, such that when the active goes offline, there's no "caught-up" node, and instead of failing the task over to the least-lagging node, we just assign it to a fresh node? If that's it, then it is certainly not the desired behavior.

The notion of acceptableRecoveryLag was introduced because follower replicas will always lag the active task, by definition. We want task ownership to be able to swap over from the active to a warm-up when it's caught up, but it will never be 100% caught up (because it is a follower until it takes over). acceptableRecoveryLag is a way to define a small amount of lag that "acceptable" so that when a warm-up is only lagging by that amount, we can consider it to be effectively caught up and move the active to the warm-up node.

As you can see, this has nothing at all to do with which nodes are eligible to take over when an active exits the cluster. In that case, it was always the intent that the most-caught-up node should take over active processing, regardless of its lag.

I've been squinting at our existing code, and also your patch ([https://github.com/apache/kafka/commit/a4b622685423fbfd68b1291dad85cc1f44b086f1)] . It looks to me like the flaw in the existing implementation is essentially just here:

[https://github.com/apache/kafka/commit/a4b622685423fbfd68b1291dad85cc1f44b086f1#diff-83a301514ee18b410df40a91595f6f1afd51f6152ff813b5789516cf5c3605baL92-L96]
{code:java}
// if the desired client is not caught up, and there is another client that _is_ caught up, then
// we schedule a movement, so we can move the active task to the caught-up client. We'll try to
// assign a warm-up to the desired client so that we can move it later on.{code}
which should indeed be just like what you described:
{code:java}
// if the desired client is not caught up, and there is another client that _is_ more caught up,
// then we schedule a movement [to] move the active task to the [most] caught-up client. 
// We'll try to assign a warm-up to the desired client so that we can move it later on.{code}
On the other hand, we should not lose this important predicate to determine whether a task is considered "caught up:

[https://github.com/apache/kafka/commit/a4b622685423fbfd68b1291dad85cc1f44b086f1#diff-e50a755ba2a4d2f7306d1016d079018cba22f9f32993ef5dd64408d1a94d79acL245]
{code:java}
activeRunning(taskLag) || unbounded(acceptableRecoveryLag) || acceptable(acceptableRecoveryLag, taskLag) {code}
This captures a couple of subtleties in addition to the obvious "a task is caught up if it's under the acceptable recovery lag":
 # A running, active task doesn't have a real lag at all, but instead its "lag" is the sentinel value `-2`
 # You can disable the "warm up" phase completely by setting acceptableRecoveryLag to `Long.MAX_VALUE`, in which case, we ignore lags completely and consider all nodes to be caught up, even if they didn't report a lag at all.

 

One extra thing I like about your patch is this:

[https://github.com/apache/kafka/commit/a4b622685423fbfd68b1291dad85cc1f44b086f1#diff-83a301514ee18b410df40a91595f6f1afd51f6152ff813b5789516cf5c3605baR54-R56]
{code:java}
// Even if there is a more caught up client, as long as we're within allowable lag then
// its best just to stick with what we've got {code}
I agree that, if two nodes are within the acceptableRecoveryLag of each other, we should consider their lags to be effectively the same. That's something I wanted to do when we wrote this code, but couldn't figure out a good way to do it.

 

One thing I'd need more time on is the TaskMovementTest. At first glance, it looks like those changes are just about the slightly different method signature, but I'd want to be very sure that we're still testing the same invariants that we wanted to test.

Would you be willing to submit this bugfix as a PR so that we can formally review and merge it?
~~~~

8.

~~~~
Thanks  [~cadonna]
yeah I had a bit of a think and I think you're right, it also gets a bit weird when dealing with replicas..
Like you almost have to decide what's "caught up", assign the actives, remove those node/partitions from the candidates and then recalc for the replicas to handle the case where theres a large gab between the most caught up and second most caught up.

[~vvcephei] 
> Is the situation that there's an active that's happens to be processing quite a bit ahead of the replicas, such that when the active goes offline, there's no "caught-up" node, and instead of failing the task over to the least-lagging node, we just assign it to a fresh node
Yeah that's it!.
Although what we also hit a couple of times is a variation on clusters with no replicas where the active is restarted but its failed to locally checkpoint in a couple of minutes, when it comes back up its seen as not being caught up and so the task is assigned to a fresh(ish) node
(of course this only occurs when the cluster is already wanting to move that task to a new home due to a node being added/removed recently)



One thing I haven't really taken into consideration/thought about is clusters with more than one replica, I'm not entirely convinced it works there although the unit tests do pass.
 

Did you mean submit as is,  or to create a minimal PR where I only try to address that flaw you've identified here
[https://github.com/apache/kafka/commit/a4b622685423fbfd68b1291dad85cc1f44b086f1#diff-83a301514ee18b410df40a91595f6f1afd51f6152ff813b5789516cf5c3605baL92-L96]

I can certainly have a go at that (it was a few months ago that I patched this so it might take me a bit to wrap my head around it again lol).

Thanks
Tim
~~~~

9.

~~~~
Thanks guys for the great discussion here.

I think just changing (and of course still maintaining the subtlety of those edge cases) the behavior of "if we cannot find any caught-up node, assign to a fresh node" to "if we cannot find any caught-up node, pick one that is closest to head" as a general principal should be okay for just the scope of this ticket. We can leave further improvements of the assignment algorithm (I know Bruno/John already have some ideas) to a larger scoped KIP. WDYT?
~~~~

10.

~~~~
I am fine with discussing the improvement on the PR and not in a KIP. I actually realized that the other improvements to the assignment algorithm included changes to the public API and therefore a KIP was needed. For me it is just important that we look really careful at the improvements because the assignment algorithm is a quite critical part of the system. 

Additionally, I did not want to discuss about a totally new assignment algorithm. I just linked the information for general interest.

Looking forward to the PR.
~~~~

11.

~~~~
Hey sorry about the delay, I've finally been able to get a few hours in a row to be able to concentrate on this.
Trying to just fix "if we cannot find any caught-up node, pick one that is closest to head" with minimal other changes.
 
While it doesn't change much algorithmically, unfortunately its more than the 5-10 line change I was hoping for.
https://github.com/apache/kafka/pull/11760/files
~~~~

---

## KAFKA-13613: Kafka Connect has a hard dependency on KeyGenerator.HmacSHA256

https://issues.apache.org/jira/browse/KAFKA-13613

Given fix versions: 3.3.0
JIRA affects (masked from the system): 3.0.0

- `KAFKA-13613@3.0.0`: config 3.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-13613@2.8.2`: config 2.8.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
If a server is running Java 8 that has been configured for FIPS mode according to [openjdk-8-configuring_openjdk_8_on_rhel_with_fips-en-us.pdf|https://access.redhat.com/documentation/en-us/openjdk/8/pdf/configuring_openjdk_8_on_rhel_with_fips/openjdk-8-configuring_openjdk_8_on_rhel_with_fips-en-us.pdf] then the SunJCE provider is not available. As such the KeyGenerator HmacSHA256 is not available. The KeyGenerators I see available are

 * DES
 * ARCFOUR
 * AES
 * DESede

Out of these I think AES would be most appropriate, but that's not the point of this issue, just including for completeness.

When Kafka Connect is started in distributed mode on one of these servers I see the following stack trace

{noformat}
[2022-01-20 20:36:30,027] ERROR Stopping due to error (org.apache.kafka.connect.cli.ConnectDistributed)
java.lang.ExceptionInInitializerError
        at org.apache.kafka.connect.cli.ConnectDistributed.startConnect(ConnectDistributed.java:94)
        at org.apache.kafka.connect.cli.ConnectDistributed.main(ConnectDistributed.java:79)
Caused by: org.apache.kafka.common.config.ConfigException: Invalid value HmacSHA256 for configuration inter.worker.key.generation.algorithm: HmacSHA256 KeyGenerator not available
        at org.apache.kafka.connect.runtime.distributed.DistributedConfig.validateKeyAlgorithm(DistributedConfig.java:504)
        at org.apache.kafka.connect.runtime.distributed.DistributedConfig.lambda$configDef$2(DistributedConfig.java:375)
        at org.apache.kafka.common.config.ConfigDef$LambdaValidator.ensureValid(ConfigDef.java:1043)
        at org.apache.kafka.common.config.ConfigDef$ConfigKey.<init>(ConfigDef.java:1164)
        at org.apache.kafka.common.config.ConfigDef.define(ConfigDef.java:152)
        at org.apache.kafka.common.config.ConfigDef.define(ConfigDef.java:172)
        at org.apache.kafka.common.config.ConfigDef.define(ConfigDef.java:211)
        at org.apache.kafka.common.config.ConfigDef.define(ConfigDef.java:373)
        at org.apache.kafka.connect.runtime.distributed.DistributedConfig.configDef(DistributedConfig.java:371)
        at org.apache.kafka.connect.runtime.distributed.DistributedConfig.<clinit>(DistributedConfig.java:196)
        ... 2 more
{noformat}

It appears the {{org.apache.kafka.connect.runtime.distributed.DistributedConfig}} is triggering a validation of the hard-coded default {{inter.worker.key.generation.algorithm}} property, which is {{HmacSHA256}}.

Ideally a fix would use the value from the configuration file before attempting to validate a default value.

Updates [2022/01/27]: I just tested on a FIPS-enabled version of OpenJDK 11 using the instructions at [configuring_openjdk_11_on_rhel_with_fips|https://access.redhat.com/documentation/en-us/openjdk/11/html-single/configuring_openjdk_11_on_rhel_with_fips/index], which resulted in the same issues. One workaround is to disable FIPS for Kafka Connect by passing in the JVM parameter {{-Dcom.redhat.fips=false}}, however, that means Kafka Connect and all the workers are out of compliance for anyone required to use FIPS-enabled systems.
~~~~

### Comments (3)

1.

~~~~
I think OpenJDK17 should work, as support for this type of key was added with SHA3 support for the SunPKCS11 provider in JDK16[1,2].

References:
[1][java-17-openjdk / rhel-8.5: Mac keys generated by KeyGenerator do not work with corresponding Mac in FIPS mode|https://bugzilla.redhat.com/show_bug.cgi?id=2007331]
[2][Add SHA3 support to SunPKCS11 provider|https://bugs.openjdk.java.net/browse/JDK-8256082]
~~~~

2.

~~~~
Thanks for reporting this, [~that_guy]. I'm working on a fix and would like to confirm something with you–is the primary use case here _running_ Kafka Connect on a FIPS-compliant JVM (or really, any JVM that doesn't come with the {{HmacSHA256}} key generator algorithm), or is it also necessary to be able to _build_ Kafka Connect from source on that kind of JVM, including running all unit and integration tests?
~~~~

3.

~~~~
[~ChrisEgerton] The issue is only observed for running. We tend to utilize pre-compiled binaries whenever possible. Thanks!
~~~~

---

## KAFKA-13699: ProcessorContext does not expose Stream Time

https://issues.apache.org/jira/browse/KAFKA-13699

Given fix versions: 3.2.0
JIRA affects (masked from the system): 3.0.0

- `KAFKA-13699@3.0.0`: config 3.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-13699@2.8.2`: config 2.8.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.0, 3.1, 3.2, 2.7.0, 3.2.0, 3.0.1, 3.1.1, 3.0.0

### Description

~~~~
As a KS developer, I would like to leverage [KIP-622|https://cwiki.apache.org/confluence/display/KAFKA/KIP-622%3A+Add+currentSystemTimeMs+and+currentStreamTimeMs+to+ProcessorContext] and access stream time in Processor Context.

_(Updated)_

However, the methods currentStreamTimeMs or currentSystemTimeMs is missing from for KStreams 3.0+.

Checked with [~mjsax] , the methods are absent from the Processor API , i.e.
 * org.apache.kafka.streams.processor.api.ProcessorContext
~~~~

### Comments (6)

1.

~~~~
Hi [~lqxshay] thanks for filing the ticket. Just to clarify I think the function did exist in the deprecated old API:

```
org.apache.kafka.streams.processor.ProcessorContext
```

They are not in the new API:

```
org.apache.kafka.streams.processor.api.ProcessorContext
```

Is that right?
~~~~

2.

~~~~
That's my understanding, too. Seems we missed to add both to the new `.api.ProcessorContext` API, as both KIPs kinda overlapped.

Not sure if we could fix this in 3.0 and 3.1 as KIP-622 originally landed in 3.0, or if we can only fix forward in 3.2?
~~~~

3.

~~~~
Hi team [~guozhang] [~mjsax] yes, as Matthias mentioned, the methods are missing in `.api.ProcessorContext` API.

(Matthias and I connected offline and discussed it wouldn't be possible to patch backwards in 2.7.0. )
~~~~

4.

~~~~
Seems the only question is, if we need to update the KIP? And if we can only fix forward in 3.2.0 (or if we can back-port to `3.0.1` and `3.1.1` ?

\cc [~mimaison] [~guozhang] WDYT? `3.0.1` is already on it's way...
~~~~

5.

~~~~
Even if it was voted and partly landed in 3.0.0, I think we should only the missing APIs in 3.2.0.  
~~~~

6.

~~~~
I agree with [~mimaison], that we would only be able to fix forward in 3.2.0+.
~~~~

---

## KAFKA-13880: DefaultStreamPartitioner may get "stuck" to one partition for unkeyed messages

https://issues.apache.org/jira/browse/KAFKA-13880

Given fix versions: 3.3.0
JIRA affects (masked from the system): 2.4.0

- `KAFKA-13880@2.4.0`: config 2.4.0, metadata answer **affected** (listed_affected)
- `KAFKA-13880@2.3.1`: config 2.3.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
While working on KIP-794, I noticed that DefaultStreamPartitioner does not call .onNewBatch.  The "sticky" DefaultStreamPartitioner introduced as a result of https://issues.apache.org/jira/browse/KAFKA-8601 requires .onNewBatch call in order to switch to a new partitions for unkeyed messages, just calling .partition would return the same "sticky" partition chosen during the first call to .partition.  The partition doesn't change even if the partition leader is unavailable.

Ideally, for unkeyed messages the DefaultStreamPartitioner should take advantage of the new built-in partitioning logic introduced in [https://github.com/apache/kafka/pull/12049.]  Perhaps, it could return null partition for unkeyed message, so that KafkaProducer could run built-in partitioning logic.
~~~~

---

## KAFKA-14062: OAuth client token refresh fails with SASL extensions

https://issues.apache.org/jira/browse/KAFKA-14062

Given fix versions: 3.1.2, 3.2.1, 3.3.0
JIRA affects (masked from the system): 3.1.0, 3.1.1, 3.2.0, 3.3.0

- `KAFKA-14062@3.1.0`: config 3.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-14062@3.0.2`: config 3.0.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
While testing OAuth for Connect an issue surfaced where authentication that was successful initially fails during token refresh. This appears to be due to missing SASL extensions on refresh, though those extensions were present on initial authentication.

During token refresh, the Kafka client adds and removes any SASL extensions. If a refresh is attempted during the window when the extensions are not present in the subject, the refresh fails with the following error:
{code:java}
[2022-04-11 20:33:43,250] INFO [AdminClient clientId=adminclient-8] Failed authentication with <host>/<IP> (Authentication failed: 1 extensions are invalid! They are: xxx: Authentication failed) (org.apache.kafka.common.network.Selector){code}
~~~~

---

## KAFKA-14196: Duplicated consumption during rebalance, causing OffsetValidationTest to act flaky

https://issues.apache.org/jira/browse/KAFKA-14196

Given fix versions: 3.2.3, 3.3.0
JIRA affects (masked from the system): 3.2.1

- `KAFKA-14196@3.2.1`: config 3.2.1, metadata answer **affected** (listed_affected)
- `KAFKA-14196@3.2.0`: config 3.2.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.2, 3.2.1, 3.2.0

### Description

~~~~
Several flaky tests under OffsetValidationTest are indicating potential consumer duplication issue, when autocommit is enabled.  I believe this is affecting *3.2* and onward.  Below shows the failure message:

 
{code:java}
Total consumed records 3366 did not match consumed position 3331 {code}
 

After investigating the log, I discovered that the data consumed between the start of a rebalance event and the async commit was lost for those failing tests.  In the example below, the rebalance event kicks in at around 1662054846995 (first record), and the async commit of the offset 3739 is completed at around 1662054847015 (right before partitions_revoked).

 
{code:java}
{"timestamp":1662054846995,"name":"records_consumed","count":3,"partitions":[{"topic":"test_topic","partition":0,"count":3,"minOffset":3739,"maxOffset":3741}]}
{"timestamp":1662054846998,"name":"records_consumed","count":2,"partitions":[{"topic":"test_topic","partition":0,"count":2,"minOffset":3742,"maxOffset":3743}]}
{"timestamp":1662054847008,"name":"records_consumed","count":2,"partitions":[{"topic":"test_topic","partition":0,"count":2,"minOffset":3744,"maxOffset":3745}]}
{"timestamp":1662054847016,"name":"partitions_revoked","partitions":[{"topic":"test_topic","partition":0}]}
{"timestamp":1662054847031,"name":"partitions_assigned","partitions":[{"topic":"test_topic","partition":0}]}
{"timestamp":1662054847038,"name":"records_consumed","count":23,"partitions":[{"topic":"test_topic","partition":0,"count":23,"minOffset":3739,"maxOffset":3761}]} {code}
A few things to note here:
 # Manually calling commitSync in the onPartitionsRevoke cb seems to alleviate the issue
 # Setting includeMetadataInTimeout to false also seems to alleviate the issue.

The above tries seems to suggest that contract between poll() and asyncCommit() is broken.  AFAIK, we implicitly uses poll() to ack the previously fetched data, and the consumer would (try to) commit these offsets in the current poll() loop.  However, it seems like as the poll continues to loop, the "acked" data isn't being committed.

 

I believe this could be introduced in  KAFKA-14024, which originated from KAFKA-13310.

More specifically, (see the comments below), the ConsumerCoordinator will alway return before async commit, due to the previous incomplete commit.  However, this is a bit contradictory here because:
 # I think we want to commit asynchronously while the poll continues, and if we do that, we are back to KAFKA-14024, that the consumer will get rebalance timeout and get kicked out of the group.
 # But we also need to commit all the "acked" offsets before revoking the partition, and this has to be blocked.

*Steps to Reproduce the Issue:*
 # Check out AK 3.2
 # Run this several times: (Recommend to only run runs with autocommit enabled in consumer_test.py to save time)
{code:java}
_DUCKTAPE_OPTIONS="--debug" TC_PATHS="tests/kafkatest/tests/client/consumer_test.py::OffsetValidationTest.test_consumer_failure" bash tests/docker/run_tests.sh {code}
 

*Steps to Diagnose the Issue:*
 # Open the test results in *results/*
 # Go to the consumer log.  It might look like this

 
{code:java}
results/2022-09-03--005/OffsetValidationTest/test_consumer_failure/clean_shutdown=True.enable_autocommit=True.metadata_quorum=ZK/2/VerifiableConsumer-0-xxxxxxxxxx/dockerYY {code}
3. Find the docker instance that has partition getting revoked and rejoined.  Observed the offset before and after.

*Propose Fixes:*

 TBD

 

https://github.com/apache/kafka/pull/12603
~~~~

### Comments (13)

1.

~~~~
If I understand this correctly: Seems like this is introduced in https://issues.apache.org/jira/browse/KAFKA-14024, which originated from https://issues.apache.org/jira/browse/KAFKA-13310.  I think the cause of the flakiness/duplication is, the consumer is busy waiting for the prior async commit to complete (in order to complete the rebalance process), while fetching new data.  After the async complete finished, the partition gets revoked, and the fetch progress will be lost, and eventually causes duplicated consumption.

A few comments:
 # Do we want to continue to fetch, while waiting for the async commit to complete? I believe this is the expectation of the new poll API.
 # If we don't want to block consumer from fetching, then we will need to continue to commit asynchronously.  I see this could be problematic, as the consumer could stuck in the poll loop while busy catching up with committing the fetched data, and never complete the rebalance process.
~~~~

2.

~~~~
Kind of originated from this commit: https://github.com/apache/kafka/pull/12349/files
~~~~

3.

~~~~
[~pnee] , thanks for the analysis. Yes, we forgot about during the following poll, the offset might advance while we're waiting for the old async offset commit completion.

Actually, while checking the code, even if we don't do the change for KAFKA-14024,and KAFKA-13310, (that is, changing sync commit to async commit) the issue will still happen, just not that easily. The issue is, in the consumer#poll process, we do onJoinPrepare (i.e. commit the offset), and then fetch new records. I'm thinking we should have a way to terminate poll process to avoid it keep fetching new records and return.

 

Maybe in `KafkaConsumer#updateAssignmentMetadataIfNeeded`, we passed in a parameter to allow the `onJoinPrepare` method to change the flag to notify if we need to terminate the poll and not to fetch records. WDYT?

cc [~guozhang] [~dajac]  [~aiquestion]
~~~~

4.

~~~~
Thanks Luke, per your suggestion, could you elaborate more about the reason to terminate the poll?

I've got a few questions to clarify here:
 # I don't think we need to pause the fetch if the previous async commit (autocommit) hasn't yet go through, for the normal situation (not rebalancing)? Because as long as we are sending out the commit, I think we could tentatively assume the acked data has been committed. Am I right?
 # I think we only need to pause the fetch, if there's a rebalance process taking place, because it only waits for the current in-flight commit, then revoke the partition.  Once the partition is revoked, I don't think we can do anything about the uncommitted data.

And because this regression was caused by the "rebalancing internal state" (pardon me if the words use is confusing), do you think it might be worth exposing the rebalance internal states? and perhaps adding a state to represent the current rebalancing progress, to prevent more fetching from happening during onJoinPrepare?
~~~~

5.

~~~~
[~pnee] Thanks for reporting this. While reviewing KAFKA-13310 I have realized this, but as Luke said this is not a new regression (we would potentially have duplicates even before this, since as we commit sync, and if the commit fails, we still log a warning and move forward with the revocation, in which case we would also have duplicates), I suggested we add a TODO there indicating it's sub-optimal but is allowed under at least once semantics.

I think in the long run, as we move the rebalancing related procedure all to the background thread, this would no longer be an issue since between the time background thread received an response telling it to start rebalancing (of which, the first step is to potentially revoking partitions in `onJoinPrepare`), and the time after the auto commit has been completed, the background thread could simply mark those revoking partitions as "not retrievable" so that calling thread's `poll` calls would not return any more data for those partitions. Right?

If that's the case, then we only need to consider before that comes, what we should do with this. Like I said, the behaviors before are 1) we commit sync, and even if it fails we still move forward, which would cause duplicates, or 2) we commit async so that `poll` timeout could be respected, but we would still potentially return data for those revoking partitions. I'm thinking what about just taking the middle ground: we still commit async, while at the same time mark those revoking partitions as "not retrievable" to not return any more data, note this would still not forbid duplicates completely, but would basically take us to where we were in the likelihood of the duplicates. And then we rely on the threading remodeling (there's a WIP page that Philip would be sending out soon) to completely resolve this issue.
~~~~

6.

~~~~
[~pnee] 
 # I don't think we need to pause the fetch if the previous async commit (autocommit) hasn't yet go through, for the normal situation (not rebalancing)? Because as long as we are sending out the commit, I think we could tentatively assume the acked data has been committed. Am I right?

 --> correct. for normal situation (not rebalancing), we don't pause anything
 # I think we only need to pause the fetch, if there's a rebalance process taking place, because it only waits for the current in-flight commit, then revoke the partition.  Once the partition is revoked, I don't think we can do anything about the uncommitted data.

--> correct.

 

[~guozhang] , thanks for the suggestion.

> I suggested we add a TODO there indicating it's sub-optimal but is allowed under at least once semantics.

Agree!

> we still commit async, while at the same time mark those revoking partitions as "not retrievable" to not return any more data

Sounds good to me!

 

From Philip:

> And because this regression was caused by the "rebalancing internal state" (pardon me if the words use is confusing), do you think it might be worth exposing the rebalance internal states? and perhaps adding a state to represent the current rebalancing progress, to prevent more fetching from happening during onJoinPrepare?

I think we can just `pause` the SubscriptionState of the partitions that we're going to revoked. From the javadoc:
{code:java}
/**
 * Suspend fetching from the requested partitions. Future calls to {@link #poll(Duration)} will not return
 * any records from these partitions until they have been resumed using {@link #resume(Collection)}.
 * Note that this method does not affect partition subscription. In particular, it does not cause a group
 * rebalance when automatic assignment is used.
 *
 * Note: Rebalance will not preserve the pause/resume state.
 * @param partitions The partitions which should be paused
 * @throws IllegalStateException if any of the provided partitions are not currently assigned to this consumer
 */
@Override
public void pause(Collection<TopicPartition> partitions) {{code}
 

I think that's what we want, right?
~~~~

7.

~~~~
Thanks Luke and GW, it looks like we could just pause it, but I'll test it out to see if that does what we want... I'll get back to you guys soon. :)
~~~~

8.

~~~~
[~showuon] and [~guozhang] - I think pausing should probably work, and it's also kind of convenient because the partition revocation will unpausing these partition automatically.  Let me know if you think the draft is ok, I'll add tests later on: [https://github.com/apache/kafka/pull/12603]

 

Though a few questions here:
 # Should we consider the difference between cooperative and eager protocol.  Because, cooperative doesn't revoke all partitions.  However, I worry that the subscription might change during the onJoinPrepare, so I meant there could be edge cases we need to handle here.
 # I believe this only applies to autocommit enabled.  I think for non-autocommit case, user should handle the offset during the revocation, so we are good there?
~~~~

9.

~~~~
# Should we consider the difference between cooperative and eager protocol.  Because, cooperative doesn't revoke all partitions.  However, I worry that the subscription might change during the onJoinPrepare, so I meant there could be edge cases we need to handle here.

--> I think we should consider the difference between cooperative and eager protocol, because one of the purpose for cooperative rebalance is to allow "non-revoking" partitions can keep processing during rebalance. About the edge case, I think that's fine because in the your PR, we'll check and pause the partitions each time we enter onJoinPrepare, right? So, even if there's subscription change while we're waiting commitAsync, we can pause the updated subscription partitions in onJoinPrepare each time. Besides, that's really rare. WDYT?
 # I believe this only applies to autocommit enabled.  I think for non-autocommit case, user should handle the offset during the revocation, so we are good there?

--> Yes, we only need to worry about autocmmit enabled case
~~~~

10.

~~~~
Thanks Philip, and regarding your two questions above I agree with [~showuon]'s thoughts as well. Especially for 1), I think even if subscriptions changed in between consecutive onJoinPrepare, as long as they will not change the assigned partitions (i.e. as long as `assignFromSubscribed()` has not called) I think we are fine, since the returned records depend on that assigned partitions.
~~~~

11.

~~~~
To clarify, this was introduced in 3.2.1 (not 3.2.0), correct?

Also, this is currently marked as a blocker. Is there a crisp description of the regression?
~~~~

12.

~~~~
[~ijuma] - I think that's right, according to the [release notes|https://downloads.apache.org/kafka/3.2.1/RELEASE_NOTES.html] (I see 10424 there).  I can add the description but I don't really know where, do you mean by updating the description/title of this ticket?
~~~~

13.

~~~~
>  Also, this is currently marked as a blocker. Is there a crisp description of the regression?

Prior to revocation, eager rebalance strategies will attempt to auto-commit offsets before revoking partitions and joining the rebalance. Originally this logic was synchronous, which meant there was no opportunity for additional data to be returned before the revocation completed. This changed when we introduced asynchronous offset commit logic. Any progress made between the time the asynchronous offset commit was sent and the revocation completed would be lost. This results in duplicate consumption.
~~~~

---

## KAFKA-14260: InMemoryKeyValueStore iterator still throws ConcurrentModificationException

https://issues.apache.org/jira/browse/KAFKA-14260

Given fix versions: 3.4.0
JIRA affects (masked from the system): 2.3.1, 3.2.3

- `KAFKA-14260@2.3.1`: config 2.3.1, metadata answer **affected** (listed_affected)
- `KAFKA-14260@2.3.0`: config 2.3.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
This is the same bug as KAFKA-7912 which was then re-introduced by KAFKA-8802.

Any iterator returned from {{InMemoryKeyValueStore}} may end up throwing a ConcurrentModificationException because the backing map is not concurrent safe. I expect that this only happens when the store is retrieved from {{KafkaStreams.store()}} from outside of the topology since any usage of the store from inside of the topology should be naturally single-threaded.

To start off, a reminder that this behaviour explicitly violates the interface contract for {{ReadOnlyKeyValueStore}} which states
{quote}The returned iterator must be safe from java.util.ConcurrentModificationExceptions
{quote}
It is often complicated to make code to demonstrate concurrency bugs, but thankfully it is trivial to reason through the source code in {{InMemoryKeyValueStore.java}} to show why this happens:
 * All of the InMemoryKeyValueStore methods that return iterators do so by passing a keySet based on the backing TreeMap to the InMemoryKeyValueIterator constructor.
 * These keySets are all VIEWS of the backing map, not copies.
 * The InMemoryKeyValueIterator then makes a private copy of the keySet by passing the original keySet into the constructor for TreeSet. This copying was implemented in KAFKA-8802, incorrectly intending it to fix the concurrency problem.
 * TreeSet then iterates over the keySet to make a copy. If the original backing TreeMap in InMemoryKeyValueStore is changed while this copy is being created it will fail-fast a ConcurrentModificationException.

This bug should be able to be trivially fixed by replacing the backing TreeMap with a ConcurrentSkipListMap but here's the rub:

This bug has already been found in KAFKA-7912 and the TreeMap was replaced with a ConcurrentSkipListMap. It was then reverted back to a TreeMap in KAFKA-8802 because of the performance regression. I can [see from one of the PRs|https://github.com/apache/kafka/pull/7212/commits/384c12e40f3a59591f897d916f92253e126820ed] that it was believed the concurrency problem with the TreeMap implementation was fixed by copying the keyset when the iterator is created but the problem remains, plus the fix creates an extra copy of the iterated portion of the set in memory.

For what it's worth, the performance difference between TreeMap and ConcurrentSkipListMap do not extend into complexity. TreeMap enjoys a similar ~2x speed through all operations with any size of data, but at the cost of what turned out to be an easy-to-encounter bug.

This is all unfortunate since the only time the state stores ever get accessed concurrently is through the `KafkaStreams.store()` mechanism, but I would imagine that "correct and slightly slower) is better than "incorrect and faster".

Too bad BoilerBay's AirConcurrentMap is closed-source and patented.
~~~~

### Comments (7)

1.

~~~~
Hello [~aviperksy] just checking is https://github.com/apache/kafka/pull/11367 related?
~~~~

2.

~~~~
[~guozhang] as far as I can see, your PR with the "copyOnRange" flag set does not manage to avoid the concurrency problem. InMemoryKeyValueStore.java line 125 still creates the iterator using the original map, and if that original map is a TreeMap then the iteration over the TreeMap when you're copying it/(or parts of it) will eventually result in a ConcurrentModificationException if the map is modified during the iteration. When the flag is not set, your PR uses a ConcurrentSkipListMap which is immune to ConcurrentModificationExceptions.
~~~~

3.

~~~~
Hello [~aviperksy] sorry for the late reply! I looked at the code again and I think I agree with you --- we are probably looking at different versions of the source code since in latest trunk, line 125 seems irrelevant (https://github.com/apache/kafka/blob/trunk/streams/src/main/java/org/apache/kafka/streams/state/internals/InMemoryKeyValueStore.java#L125) --- but the thing is that at the time when this line was called:

{code}
if (forward) {
                this.iter = new TreeSet<>(keySet).iterator();
            } else {
                this.iter = new TreeSet<>(keySet).descendingIterator();
            }
{code}

in which the constructor of {{TreeSet}} loops over the {{keySet}}, if that {{keySet}}'s underlying map is modified then we will still have an issue. As for the fix, I think in the near term we'd have to bite the bullet of performance can turn back to ConcurrentSkipListMap (we may tune some initial params e.g. using concurrencyLevel of 1). In the long term, I think we could leverage on similar ideas we are pursuing for transactional state stores, where we keep two in-memory maps, and the first map is read-only for IQ, and second is used to maintain deltas within a commit interval and during processing, we'd need to read both maps, and upon committing we lock the first one to apply the deltas.

cc [~ableegoldman] what do you think?
~~~~

4.

~~~~
Seems like we should just make sure to synchronize when making an iterator/copying the key set, right? Actually it looks like most of the methods already are but I notice that the new #prefixScan for example is not. [~aviperksy]  were you using that API when you saw this ConcurrentModificationException?

It would really be a bummer if we had to go back to the ConcurrentSkipList, it just could not keep up with the basic TreeSet especially for larger stores :/ Of course if we have to then we have to, but we should make sure to exhaust the alternatives before we settle on that
~~~~

5.

~~~~
Getting to work adding the missing `sychronized`. 
~~~~

6.

~~~~
Ok I did merge a patch to fix where we forgot to synchronize, which is certainly a bug leading to potential CME, but I realize that's not what this ticket was about so I want to explain why I resolved it: ie that synchronization is sufficient for avoiding CMEs. I do think you pointed out something of note here, though, which is worth following up on though perhaps tracking separately.

In the IMKVIterator constructor from [~guozhang]'s snippet above, it's true we get an iterator based on the original map, but it's still just a copy of that map: so this iterator doesn't pin any part of the original map and just happily returns the set of keys that were in the original map when the range API was invoked. There's no way to modify the contents of this copy as it's internal to the (also internal) iterator, and even if you delete a record with a given key in that store, the actual key object itself still exists (and can/will still be returned by that iterator)

So I really don't see how a CME is possible if we properly synchronize the APIs to enforce single-threaded access while that copy is being made. Which we do (now, since merging [~Cerchie] 's PR)

That said, it still feels a bit awkward because the keyset-copy iterator can return keys that no longer exist in the actual store. In this case when we issue a get on that key it'll return null, and the range read will have an entry with a null value. Technically Streams makes no guarantees about whether a range scan will reflect only the original state store contents or only the latest contents or anything in between, and I'm not sure there's even a "right" answer there.

Still, returning a KeyValue("key1", null) is still pretty awkward and likely unexpected by most users, so I _can_ this resulting in an NPE. Fortunately that's a much easier fix, as we can just toss out that result and return whatever is next. I think it's worth filing a separate ticket for that one, though

[~aviperksy] thoughts? Did I miss something obvious here? Also note that the code has changed a lot over the years, so it's possible what you described does affect some older branch(es)
~~~~

7.

~~~~
Well, actually, it turns out we are breaking a public contract here because I just happened to notice that we do in fact assert that null values shouldn't be returned. So I filed https://issues.apache.org/jira/browse/KAFKA-14460
~~~~

---

## KAFKA-14324: [CVE-2018-25032] introduced by rocksdbjni:6.29.4.1

https://issues.apache.org/jira/browse/KAFKA-14324

Given fix versions: 3.0.3, 3.1.3, 3.2.4, 3.3.2, 3.4.0
JIRA affects (masked from the system): 3.1.2, 3.2.3, 3.3.1

- `KAFKA-14324@3.3.1`: config 3.3.1, metadata answer **affected** (listed_affected)
- `KAFKA-14324@3.1.1`: config 3.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: v3.0

### Description

~~~~
Hi, Team
There is an old CVE introduced by rocksdbjni-6.29.4.1, which has already been fixed by [https://github.com/facebook/rocksdb/commit/5dbdb197f19644d3f53f75781a3ef56e4387134b]

[https://nvd.nist.gov/vuln/detail/cve-2018-25032]

*Current Description:* 

zlib before 1.2.12 allows memory corruption when deflating (i.e., when compressing) if the input has many distant matches.

CVE-2018-25032 - CVSS Score:{*}7.5{*} (v3.0) (zlib-1.2.11)

Please help to upgrade the rocksdb.
Thanks
~~~~

### Comments (1)

1.

~~~~
Hello [~vinsonZhang]! I prepared a pull request for this and I would be grateful if you could review it :)
~~~~

---

## KAFKA-14337: topic name with "." cannot be created after deletion

https://issues.apache.org/jira/browse/KAFKA-14337

Given fix versions: 3.3.2, 3.4.0
JIRA affects (masked from the system): 3.3.1

- `KAFKA-14337@3.3.1`: config 3.3.1, metadata answer **affected** (listed_affected)
- `KAFKA-14337@3.3.0`: config 3.3.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.3.1, v3.3.2, v3.4.0

### Description

~~~~
Hi admin,

My issue is after i create topic like topic.AAA or Topic.AAA.01 then delete 1 of the other 2 topics.

Then i can't create 1 of the 2 topics.

But i create topic test123 then delete and recreate fine.

This is log i tried to create topic.AAA

WARN [Controller 1] createTopics: failed with unknown server exception NoSuchElementException at epoch 14 in 193 us.  Renouncing leadership and reverting to the last committed offset 28. (org.apache.kafka.controller.QuorumController)
java.util.NoSuchElementException
        at org.apache.kafka.timeline.SnapshottableHashTable$CurrentIterator.next(SnapshottableHashTable.java:167)
        at org.apache.kafka.timeline.SnapshottableHashTable$CurrentIterator.next(SnapshottableHashTable.java:139)
        at org.apache.kafka.timeline.TimelineHashSet$ValueIterator.next(TimelineHashSet.java:120)
        at org.apache.kafka.controller.ReplicationControlManager.validateNewTopicNames(ReplicationControlManager.java:799)
        at org.apache.kafka.controller.ReplicationControlManager.createTopics(ReplicationControlManager.java:567)
        at org.apache.kafka.controller.QuorumController.lambda$createTopics$7(QuorumController.java:1832)
        at org.apache.kafka.controller.QuorumController$ControllerWriteEvent.run(QuorumController.java:767)
        at org.apache.kafka.queue.KafkaEventQueue$EventContext.run(KafkaEventQueue.java:121)
        at org.apache.kafka.queue.KafkaEventQueue$EventHandler.handleEvents(KafkaEventQueue.java:200)
        at org.apache.kafka.queue.KafkaEventQueue$EventHandler.run(KafkaEventQueue.java:173)
        at java.base/java.lang.Thread.run(Thread.java:829)

ERROR [Controller 1] processBrokerHeartbeat: unable to start processing because of NotControllerException. (org.apache.kafka.controller.QuorumController)

 

I'm run kafka mode Kraft !!!

Tks admin.
~~~~

### Comments (4)

1.

~~~~
Nice find! Investigating!

 
~~~~

2.

~~~~
Hi admin,

Tks you for fixed , after i change code to this link [GitHub Pull Request #12790|https://github.com/apache/kafka/pull/12790] , it's worked on kafka Source download: [kafka-3.3.1-src.tgz.|https://downloads.apache.org/kafka/3.3.1/kafka-3.3.1-src.tgz]

But can I fix on Binary downloads: Scala 2.13  - [kafka_2.13-3.3.1.tgz|https://downloads.apache.org/kafka/3.3.1/kafka_2.13-3.3.1.tgz] ([asc|https://downloads.apache.org/kafka/3.3.1/kafka_2.13-3.3.1.tgz.asc], [sha512|https://downloads.apache.org/kafka/3.3.1/kafka_2.13-3.3.1.tgz.sha512]) on my kafka.

I deploy to 3 broker kafka running kraft mode .

Best regards !!!
~~~~

3.

~~~~
[~thanhnd96] , this bug fix will be in Kafka v3.3.2 and v3.4.0 and later. The release date is not confirmed, yet, but it should be happen by the end of the year, or the beginning of 2023. FYI

 
~~~~

4.

~~~~
thank you [~showuon] !!!
~~~~

---

## KAFKA-14545: MirrorCheckpointTask throws NullPointerException when group hasn't consumed from some partitions

https://issues.apache.org/jira/browse/KAFKA-14545

Given fix versions: 3.3.3, 3.4.1, 3.5.0
JIRA affects (masked from the system): 3.3.0, 3.4.0

- `KAFKA-14545@3.4.0`: config 3.4.0, metadata answer **affected** (listed_affected)
- `KAFKA-14545@3.2.3`: config 3.2.3, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
MirrorTaskConnector looks like it's throwing a NullPointerException when a consumer group hasn't consumed from all topics from a partition. This blocks the syncing of consumer group offsets to the target cluster. The stacktrace and error message is as follows:
{code:java}
WARN Failure polling consumer state for checkpoints. (org.apache.kafka.connect.mirror.MirrorCheckpointTask)
at java.base/java.lang.Thread.run(Thread.java:829)Dec 20
at java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:628)
at java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1128)
at java.base/java.util.concurrent.FutureTask.run(FutureTask.java:264)
at java.base/java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:515)
at org.apache.kafka.connect.runtime.AbstractWorkerSourceTask.run(AbstractWorkerSourceTask.java:72)
at org.apache.kafka.connect.runtime.WorkerTask.run(WorkerTask.java:244)
at org.apache.kafka.connect.runtime.WorkerTask.doRun(WorkerTask.java:189)
at org.apache.kafka.connect.runtime.AbstractWorkerSourceTask.execute(AbstractWorkerSourceTask.java:346)
at org.apache.kafka.connect.runtime.AbstractWorkerSourceTask.poll(AbstractWorkerSourceTask.java:452)
at org.apache.kafka.connect.mirror.MirrorCheckpointTask.poll(MirrorCheckpointTask.java:142)
at org.apache.kafka.connect.mirror.MirrorCheckpointTask.sourceRecordsForGroup(MirrorCheckpointTask.java:160)
at org.apache.kafka.connect.mirror.MirrorCheckpointTask.checkpointsForGroup(MirrorCheckpointTask.java:177)
at java.base/java.util.stream.ReferencePipeline.collect(ReferencePipeline.java:578)
at java.base/java.util.stream.AbstractPipeline.evaluate(AbstractPipeline.java:234)
at java.base/java.util.stream.ReduceOps$ReduceOp.evaluateSequential(ReduceOps.java:913)
at java.base/java.util.stream.AbstractPipeline.wrapAndCopyInto(AbstractPipeline.java:474)
at java.base/java.util.stream.AbstractPipeline.copyInto(AbstractPipeline.java:484)
at java.base/java.util.HashMap$EntrySpliterator.forEachRemaining(HashMap.java:1764)
at java.base/java.util.stream.ReferencePipeline$2$1.accept(ReferencePipeline.java:177)
at java.base/java.util.stream.ReferencePipeline$3$1.accept(ReferencePipeline.java:195)
at org.apache.kafka.connect.mirror.MirrorCheckpointTask.lambda$checkpointsForGroup$2(MirrorCheckpointTask.java:174)
at org.apache.kafka.connect.mirror.MirrorCheckpointTask.checkpoint(MirrorCheckpointTask.java:191)
java.lang.NullPointerException
 {code}
This seems to happen if the OffsetFetch call returns a OffsetFetchPartitionResponsePartition with a negative commitedOffset. Mirrormaker should handle this case more gracefully and still be sync over consumer offsets for non negative partitions.
{code:java}
TRACE [AdminClient clientId=adminclient-55] Call(callName=offsetFetch(api=OFFSET_FETCH), deadlineMs=1671657869539, tries=0, nextAllowedTryMs=0) got response OffsetFetchResponseData(throttleTimeMs=0, topics=[OffsetFetchResponseTopic(name='XXX', partitions=[OffsetFetchResponsePartition(partitionIndex=1, committedOffset=866, committedLeaderEpoch=-1, metadata='', errorCode=0), OffsetFetchResponsePartition(partitionIndex=0, committedOffset=865, committedLeaderEpoch=-1, metadata='', errorCode=0), OffsetFetchResponsePartition(partitionIndex=9, committedOffset=868, committedLeaderEpoch=-1, metadata='', errorCode=0), OffsetFetchResponsePartition(partitionIndex=14, committedOffset=870, committedLeaderEpoch=-1, metadata='', errorCode=0), OffsetFetchResponsePartition(partitionIndex=5, committedOffset=803, committedLeaderEpoch=-1, metadata='', errorCode=0), OffsetFetchResponsePartition(partitionIndex=8, committedOffset=881, committedLeaderEpoch=-1, metadata='', errorCode=0), OffsetFetchResponsePartition(partitionIndex=11, committedOffset=-1, committedLeaderEpoch=-1, metadata='', errorCode=0), OffsetFetchResponsePartition(partitionIndex=4, committedOffset=872, committedLeaderEpoch=-1, metadata='', errorCode=0), OffsetFetchResponsePartition(partitionIndex=7, committedOffset=863, committedLeaderEpoch=-1, metadata='', errorCode=0), OffsetFetchResponsePartition(partitionIndex=10, committedOffset=835, committedLeaderEpoch=-1, metadata='', errorCode=0), OffsetFetchResponsePartition(partitionIndex=13, committedOffset=860, committedLeaderEpoch=-1, metadata='', errorCode=0), OffsetFetchResponsePartition(partitionIndex=12, committedOffset=885, committedLeaderEpoch=-1, metadata='', errorCode=0), OffsetFetchResponsePartition(partitionIndex=3, committedOffset=771, committedLeaderEpoch=-1, metadata='', errorCode=0), OffsetFetchResponsePartition(partitionIndex=6, committedOffset=859, committedLeaderEpoch=-1, metadata='', errorCode=0), OffsetFetchResponsePartition(partitionIndex=2, committedOffset=820, committedLeaderEpoch=-1, metadata='', errorCode=0), OffsetFetchResponsePartition(partitionIndex=15, committedOffset=826, committedLeaderEpoch=-1, metadata='', errorCode=0)])], errorCode=0, groups=[]) (org.apache.kafka.clients.admin.KafkaAdminClient) {code}
~~~~

### Comments (2)

1.

~~~~
Adding a check for null values in [MirrorCheckpointTask.checkpointsForGroups |https://github.com/apache/kafka/blob/trunk/connect/mirror/src/main/java/org/apache/kafka/connect/mirror/MirrorCheckpointTask.java#L172]seems like the simplest fix for this issue.
~~~~

2.

~~~~
ended up making the change in checkpoint instead of checkpointsForGroups since it was easier to test there.
~~~~

---

## KAFKA-14816: Connect loading SSL configs when contacting non-HTTPS URLs

https://issues.apache.org/jira/browse/KAFKA-14816

Given fix versions: 3.4.1, 3.5.0
JIRA affects (masked from the system): 3.4.0

- `KAFKA-14816@3.4.0`: config 3.4.0, metadata answer **affected** (listed_affected)
- `KAFKA-14816@3.3.2`: config 3.3.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
Due to changes made here: [https://github.com/apache/kafka/pull/12828]
Connect now unconditionally loads SSL configs from the worker into rest clients it uses for cross-worker communication and uses them even when issuing requests to HTTP (i.e., non-HTTPS) URLs. Previously, it would only attempt to load (and validate) SSL properties when issuing requests to HTTPS URLs. This can cause issues when a Connect cluster has stopped securing its REST API with SSL but its worker configs still contain the old (and now-invalid) SSL properties. When this happens, REST requests that hit a follower worker but need to be forwarded to the leader will fail, and connectors that perform dynamic reconfigurations via [ConnectorContext::requestTaskReconfiguration|https://kafka.apache.org/34/javadoc/org/apache/kafka/connect/connector/ConnectorContext.html#requestTaskReconfiguration()] will fail to trigger that reconfiguration if they are not running on the leader.

In our testing environments - older versions without the linked changes pass with the following configuration, and newer versions with the changes fail:

{{ssl.keystore.location = /mnt/security/test.keystore.jks}}
{{ssl.keystore.password = [hidden]}}
{{ssl.keystore.type = JKS}}
{{ssl.protocol = TLSv1.2}}

It's important to note that the file {{/mnt/security/test.keystore.jks}} isn't generated for our non-SSL tests, however these configs are still included in our worker config file.

This leads to a 500 response when hitting the create connector REST endpoint with the following error:

bq. { "error_code":500,   "message":"Failed to start RestClient:   /mnt/security/test.keystore.jks is not a valid keystore" }
~~~~

### Comments (1)

1.

~~~~
Thanks [~imcdo] for filing this. I believe the root cause is slightly different than what you initially described on the ticket, so I've updated the description with something more plausible given the changes in the PR where this was originally discussed.

This is definitely worth addressing as it is a regression in behavior and can cause clusters to fail after upgrades. Hopefully people aren't leaving invalid SSL properties in their worker configs when using HTTP for their REST API, but there's no reason that their cluster should break if they are.

I'll file a PR to fix this sometime today.

CC [~gharris1727] 
~~~~

---

## KAFKA-14843: Connector plugins config endpoint does not include Common configs

https://issues.apache.org/jira/browse/KAFKA-14843

Given fix versions: 3.2.4, 3.3.3, 3.4.1, 3.5.0
JIRA affects (masked from the system): 3.2.0, 3.2.1, 3.2.2, 3.2.3, 3.3.0, 3.3.1, 3.3.2, 3.4.0

- `KAFKA-14843@3.2.3`: config 3.2.3, metadata answer **affected** (listed_affected)
- `KAFKA-14843@3.1.2`: config 3.1.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
Connector plugins GET config endpoint introduced in [https://cwiki.apache.org/confluence/display/KAFKA/KIP-769%3A+Connect+APIs+to+list+all+connector+plugins+and+retrieve+their+configuration+definitions]  allows to get plugin configuration from the rest endpoint.

This configuration only includes the plugin configuration, but not the base configuration of the Sink/Source Connector.

For instance, when validating the configuration of a plugin, _all_ configs are returned:

```

curl -s $CONNECT_URL/connector-plugins/io.aiven.kafka.connect.http.HttpSinkConnector/config | jq -r '.[].name' | sort -u | wc -l     
21

curl -s $CONNECT_URL/connector-plugins/io.aiven.kafka.connect.http.HttpSinkConnector/config/validate -XPUT -H 'Content-type: application/json' --data "\{\"connector.class\": \"io.aiven.kafka.connect.http.HttpSinkConnector\", \"topics\": \"example-topic-name\"}" | jq -r '.configs[].definition.name' | sort -u | wc -l
39

```

and the missing configs are all from base config:

```

diff validate.txt config.txt                                                                                                    
6,14d5
< config.action.reload
< connector.class
< errors.deadletterqueue.context.headers.enable
< errors.deadletterqueue.topic.name
< errors.deadletterqueue.topic.replication.factor
< errors.log.enable
< errors.log.include.messages
< errors.retry.delay.max.ms
< errors.retry.timeout
16d6
< header.converter
24d13
< key.converter
26d14
< name
33d20
< predicates
35,39d21
< tasks.max
< topics
< topics.regex
< transforms
< value.converter

```

Would be great to get the base configs from the same endpoint as well, so we could rely on it instead of using the validate endpoint to get all configs.
~~~~

---

## KAFKA-14963: Incorrect partition count metrics for kraft controllers

https://issues.apache.org/jira/browse/KAFKA-14963

Given fix versions: 3.4.1
JIRA affects (masked from the system): 3.4.0

- `KAFKA-14963@3.4.0`: config 3.4.0, metadata answer **affected** (listed_affected)
- `KAFKA-14963@3.3.2`: config 3.3.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.4.0

### Description

~~~~
It is possible for the KRaft controller to report more partitions than are available in the cluster. This is because the following test fail against 3.4.0:
{code:java}
       @Test
      public void testPartitionCountDecreased() {
          ControllerMetrics metrics = new MockControllerMetrics();
          ControllerMetricsManager manager = new ControllerMetricsManager(metrics);          Uuid createTopicId = Uuid.randomUuid();
          Uuid createPartitionTopicId = new Uuid(
              createTopicId.getMostSignificantBits(),
              createTopicId.getLeastSignificantBits()
          );
          Uuid removeTopicId = new Uuid(createTopicId.getMostSignificantBits(), createTopicId.getLeastSignificantBits());
          manager.replay(topicRecord("test", createTopicId));
          manager.replay(partitionRecord(createPartitionTopicId, 0, 0, Arrays.asList(0, 1, 2)));
          manager.replay(partitionRecord(createPartitionTopicId, 1, 0, Arrays.asList(0, 1, 2)));
          manager.replay(removeTopicRecord(removeTopicId));
          assertEquals(0, metrics.globalPartitionCount());
      }
{code}
~~~~

---

## KAFKA-15096: CVE 2023-34455 - Vulnerability identified with Apache kafka

https://issues.apache.org/jira/browse/KAFKA-15096

Given fix versions: 3.3.3, 3.4.2, 3.5.1, 3.6.0
JIRA affects (masked from the system): 3.3.0, 3.3.1, 3.3.2, 3.4.0, 3.4.1, 3.5.0

- `KAFKA-15096@3.4.1`: config 3.4.1, metadata answer **affected** (listed_affected)
- `KAFKA-15096@3.2.3`: config 3.2.3, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.3, 3.4, 3.5

### Description

~~~~
A new vulnerability CVE-2023-34455 is identified with apache kafka dependency. The vulnerability is coming from snappy-java:1.1.8.4

Version 1.1.10.1 contains a patch for this issue. Please upgrade the snappy-java version to fix this issue

 
snappy-java is a fast compressor/decompressor for Java. Due to use of an unchecked chunk length, an unrecoverable fatal error can occur in versions prior to 1.1.10.1.
The code in the function hasNextChunk in the fileSnappyInputStream.java checks if a given stream has more chunks to read. It does that by attempting to read 4 bytes. If it wasn’t possible to read the 4 bytes, the function returns false. Otherwise, if 4 bytes were available, the code treats them as the length of the next chunk.
In the case that the `compressed` variable is null, a byte array is allocated with the size given by the input data. Since the code doesn’t test the legality of the `chunkSize` variable, it is possible to pass a negative number (such as 0xFFFFFFFF which is -1), which will cause the code to raise a `java.lang.NegativeArraySizeException` exception. A worse case would happen when passing a huge positive value (such as 0x7FFFFFFF), which would raise the fatal `java.lang.OutOfMemoryError` error.
~~~~

### Comments (2)

1.

~~~~
Thank you for reporting the issue [~Sasikumarms] an PR has been opened in 
[https://github.com/apache/kafka/pull/13865]
to bump the version. 
Once merged, I'll let the release managers determine how far the fix can be backported. 
~~~~

2.

~~~~
I cherry-picked this to 3.3, 3.4 and 3.5
~~~~

---

## KAFKA-15243: User creation mismatch

https://issues.apache.org/jira/browse/KAFKA-15243

Given fix versions: 3.4.2, 3.5.2, 3.6.0
JIRA affects (masked from the system): 3.3.2

- `KAFKA-15243@3.3.2`: config 3.3.2, metadata answer **affected** (listed_affected)
- `KAFKA-15243@3.3.1`: config 3.3.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
We found the Kafka users were not created properly, so let's suppose we create the user [myuser@myuser.com|mailto:myuser@myuser.com]

 

COMMAND:
{code:java}
/etc/new_kafka/bin/kafka-configs.sh  --bootstrap-server localhost:9092 --alter --add-config 'SCRAM-SHA-256=[iterations=4096,password=blabla],SCRAM-SHA-256=[password=blabla]' --entity-type users --entity-name myuser@myuser.com{code}
RESPONSE:
{code:java}
Completed updating config for user myuser@myuser.com{code}
When listing the users I see the user was created as an encoded string

COMMAND
{code:java}
kafka-configs.sh --bootstrap-server localhost:9092 --describe --entity-type users|grep myuser {code}
RESPONSE
{code:java}
SCRAM credential configs for user-principal 'myuser%40myuser.com' are SCRAM-SHA-256=iterations=8192, SCRAM-SHA-512=iterations=4096 {code}
 

So basically the user is being "sanitized" and giving a false OK to the user requester. The user requested does not exist as it should, it creates the encoded one instead.

 

I dug deep in the code until I found this is happening in the ZkAdminManager.scala in this line 

 
{code:java}
adminZkClient.changeConfigs(ConfigType.User, Sanitizer.sanitize(user), configsByPotentiallyValidUser(user)) {code}
So removing the Sanitizer fix the problem, but I have a couple of doubts

I checked we Sanitize because of some JMX metrics, but in this case I don't know if this is really needed, supossing this is needed I think we should forbid to create users with characters that will be encoded.

Even worse after creating an user in general we create ACLs and they are created properly without encoding the characters, this creates a mismatch between the user and the ACLs.

 

 

So I can work on fixing this, but I think we need to decide :

 

A) We forbid to create users with characters that will be encoded, so we fail in the user creation step.

 

B) We allow the user creation with special characters and remove the Sanitizer.sanitize(user) from the 2 places where it shows up in the file ZkAdminManager.scala

 

 

And of course if we go for B we need to create the tests.

Please let me know what you think and i can work on it
~~~~

### Comments (9)

1.

~~~~
Does this happen with KRaft?
~~~~

2.

~~~~
[~pprovenzano] we don't use KRaft yet, so this is happening right before this the new user is registered in ZK. (ZKclient)

So I know ZK will be fully deprecated in Version 4 but I still consider this can be easily fixed

 

 
~~~~

3.

~~~~
I just want to make sure that it works the same in both Zk and KRaft after the fix. 
~~~~

4.

~~~~
[~sergio_troiano@hotmail.com]  We sanitize the names because some characters are not allowed in Zookeeper paths. We sanitize the names using `Sanitizer.sanitize(user)` before storing in ZK and use `Sanitizer.desanitize` after reading from ZK.
In this case, it looks like a bug when calling describe all user scram configs (`--entity-type users`). We are returning sanitized names in the response  here [https://github.com/apache/kafka/blob/trunk/core/src/main/scala/kafka/server/ZkAdminManager.scala#L851] . We should rerun desanitized names
~~~~

5.

~~~~
[~omkreddy] ,

 

Thanks for the quick reply,One more comment, long time ago when we were running old Kafka version I saw the users were able to create the users with "@" and they re still present in ZK, it seems at some point we added the Sanitizer and this broke compatibility. but this is just a detail.

 

For us the current bug is a problem as we have an API to allow the clients to manage their users, the problem is we rely on listing them to check if they exist, so for example if you create user@user and then you want to change the password we first check if it exists and then we have the problem.

 

I will send the PR. Should I create a KIP for this? or can I send the PR here as it is a quick change ? cheers

 
~~~~

6.

~~~~
[~sergio_troiano@hotmail.com] This doesn't require KIP. This is broker side bug. we can just return desanitized names
~~~~

7.

~~~~
[~omkreddy] ,

 

OK, I will open a PR, is that ok?
~~~~

8.

~~~~
[~sergio_troiano@hotmail.com] Yes, Please open a PR. 
~~~~

9.

~~~~
[~omkreddy] , thanks, PR open

https://github.com/apache/kafka/pull/14094
~~~~

---

## KAFKA-15338: The metric group documentation for metrics added in KAFKA-13945 is incorrect

https://issues.apache.org/jira/browse/KAFKA-15338

Given fix versions: 3.3.3, 3.4.2, 3.5.2, 3.6.0
JIRA affects (masked from the system): 3.3.0

- `KAFKA-15338@3.3.0`: config 3.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-15338@3.2.3`: config 3.2.3, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
ops.html (docs/streams/ops.html) incorrectly states that the metrics type is "stream-processor-node-metrics", but in looking at the metrics and inspecting the code in TopicMetrics, these metrics have a type of "stream-topic-metrics".

4 metrics are in error "bytes-consumed-total", "bytes-produced-total", "records-consumed-total", and "records-produced-total".

Looks like the type was changed from the KIP, and the documentation still reflects the KIP.
~~~~

### Comments (2)

1.

~~~~
can i pick this up?

~~~~

2.

~~~~
Sure. Thank a lot!
~~~~

---

## KAFKA-15465: MM2 not working when its internal topics are pre-created on a cluster that disallows topic creation

https://issues.apache.org/jira/browse/KAFKA-15465

Given fix versions: 3.7.0
JIRA affects (masked from the system): 3.4.1

- `KAFKA-15465@3.4.1`: config 3.4.1, metadata answer **affected** (listed_affected)
- `KAFKA-15465@3.4.0`: config 3.4.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.7.0, 3.6.0

### Description

~~~~
h1. Replication steps
 * Setup a source kafka cluster (alias SOURCE) which doesn't allow topic creation to MM2 (therefore it doesn't allow the creation of internal topics)
 * Create MM2 internal topics in the source kafka cluster
 * Setup a target kafka cluster (alias TARGET)
 * Enable one way replication SOURCE->TARGET

MM2 will attempt to create or find its internal topics on the source cluster but it will fail with the following stack trace
{code:java}
{"log_timestamp": "2023-09-13T09:39:25.612+0000", "log_level": "ERROR", "process_id": 1, "process_name": "mirror-maker", "thread_id": 1, "thread_name": "Scheduler for MirrorSourceConnector-creating upstream offset-syncs topic", "action_name": "org.apache.kafka.connect.mirror.Scheduler", "log_message": "Scheduler for MirrorSourceConnector caught exception in scheduled task: creating upstream offset-syncs topic"}
org.apache.kafka.connect.errors.ConnectException: Error while attempting to create/find topic 'mm2-offset-syncs.TARGET.internal'
	at org.apache.kafka.connect.mirror.MirrorUtils.createCompactedTopic(MirrorUtils.java:155)
	at org.apache.kafka.connect.mirror.MirrorUtils.createSinglePartitionCompactedTopic(MirrorUtils.java:161)
	at org.apache.kafka.connect.mirror.MirrorSourceConnector.createOffsetSyncsTopic(MirrorSourceConnector.java:328)
	at org.apache.kafka.connect.mirror.Scheduler.run(Scheduler.java:93)
	at org.apache.kafka.connect.mirror.Scheduler.executeThread(Scheduler.java:112)
	at org.apache.kafka.connect.mirror.Scheduler.lambda$execute$2(Scheduler.java:63)
[...]
Caused by: java.util.concurrent.ExecutionException: org.apache.kafka.common.errors.TopicAuthorizationException: Authorization failed.
	at java.base/java.util.concurrent.CompletableFuture.reportGet(CompletableFuture.java:395)
	at java.base/java.util.concurrent.CompletableFuture.get(CompletableFuture.java:1999)
	at org.apache.kafka.common.internals.KafkaFutureImpl.get(KafkaFutureImpl.java:165)
	at org.apache.kafka.connect.mirror.MirrorUtils.createCompactedTopic(MirrorUtils.java:124)
	... 11 more
Caused by: org.apache.kafka.common.errors.TopicAuthorizationException: Authorization failed. {code}
 
h1. Root cause analysis

The changes introduced by KAFKA-13401 in [{{{}MirrorUtils{}}}|https://github.com/apache/kafka/pull/12577/files#diff-fa8f595307a4ade20cc22253a7721828e3b55c96f778e9c4842c978801e0a1a4] are supposed to follow the same logic as [{{{}TopicAdmin{}}}|https://github.com/apache/kafka/blob/a7e865c0a756504cc7ae6f4eb0772cadd3333c53/connect/runtime/src/main/java/org/apache/kafka/connect/util/TopicAdmin.java#L423] according to the contributor's [comment|https://github.com/apache/kafka/pull/12577#discussion_r991566108]

{{TopicAdmin.createOrFindTopics(...)}} and {{MirrorUtils.createCompactedTopic(...)}} aren't aligned in terms of allowed exceptions
||Exception||TopicAdmin||MirrorUtils||
|TopicExistsException|OK|OK|
|UnsupportedVersionException|OK|_KO_|
|ClusterAuthorizationException|OK|_KO_|
|TopicAuthorizationException|OK|_KO_|

 
~~~~

### Comments (3)

1.

~~~~
[~omnia_h_ibrahim], Can you please take a look and confirm my findings. Also, I will be happy to provide the fix but I can't assign myself to the bug.
~~~~

2.

~~~~
Hi [~ahibot] ,

I re-checked the code of TopicAdmin.createOrFindTopics and we missed a few returns. I'm raising a pr for this shortly. Thanks for reporting this.
~~~~

3.

~~~~
Moving it to 3.7.0 as 3.6.0 code freeze is over.
~~~~

---

## KAFKA-15510: Follower's lastFetchedEpoch wrongly set when fetch response has no record

https://issues.apache.org/jira/browse/KAFKA-15510

Given fix versions: 3.7.0
JIRA affects (masked from the system): 3.5.1, 3.6.0

- `KAFKA-15510@3.5.1`: config 3.5.1, metadata answer **affected** (listed_affected)
- `KAFKA-15510@3.5.0`: config 3.5.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
A regression is introduced by [https://github.com/apache/kafka/pull/13843/files#diff-508e9dc4d52744119dda36d69ce63a1901abfd3080ca72fc4554250b7e9f5242.|https://github.com/apache/kafka/pull/13843/files#diff-508e9dc4d52744119dda36d69ce63a1901abfd3080ca72fc4554250b7e9f5242] When the fetch response has no record for a partition, validBytes is 0. In this case, we shouldn't set the last fetch epoch to logAppendInfo.lastLeaderEpoch.asScala since there is no record and it is Optional.empty. We should use currentFetchState.lastFetchedEpoch instead.

An effect of this is truncation of fetch might not work correctly.

 
~~~~

### Comments (1)

1.

~~~~
This does not currently impact truncation in followers, but it seems useful to fix the regression to avoid breaking in future, if the timing scenario for truncation changes.
~~~~

---

## KAFKA-15653: NPE in ChunkedByteStream

https://issues.apache.org/jira/browse/KAFKA-15653

Given fix versions: 3.6.1, 3.7.0
JIRA affects (masked from the system): 3.6.0

- `KAFKA-15653@3.6.0`: config 3.6.0, metadata answer **affected** (listed_affected)
- `KAFKA-15653@3.5.2`: config 3.5.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.6, 3.5

### Description

~~~~
When looping franz-go integration tests, I received an UNKNOWN_SERVER_ERROR from producing. The broker logs for the failing request:

 
{noformat}
[2023-10-19 22:29:58,160] ERROR [ReplicaManager broker=2] Error processing append operation on partition 2fa8995d8002fbfe68a96d783f26aa2c5efc15368bf44ed8f2ab7e24b41b9879-24 (kafka.server.ReplicaManager)
java.lang.NullPointerException
	at org.apache.kafka.common.utils.ChunkedBytesStream.<init>(ChunkedBytesStream.java:89)
	at org.apache.kafka.common.record.CompressionType$3.wrapForInput(CompressionType.java:105)
	at org.apache.kafka.common.record.DefaultRecordBatch.recordInputStream(DefaultRecordBatch.java:273)
	at org.apache.kafka.common.record.DefaultRecordBatch.compressedIterator(DefaultRecordBatch.java:277)
	at org.apache.kafka.common.record.DefaultRecordBatch.skipKeyValueIterator(DefaultRecordBatch.java:352)
	at org.apache.kafka.storage.internals.log.LogValidator.validateMessagesAndAssignOffsetsCompressed(LogValidator.java:358)
	at org.apache.kafka.storage.internals.log.LogValidator.validateMessagesAndAssignOffsets(LogValidator.java:165)
	at kafka.log.UnifiedLog.append(UnifiedLog.scala:805)
	at kafka.log.UnifiedLog.appendAsLeader(UnifiedLog.scala:719)
	at kafka.cluster.Partition.$anonfun$appendRecordsToLeader$1(Partition.scala:1313)
	at kafka.cluster.Partition.appendRecordsToLeader(Partition.scala:1301)
	at kafka.server.ReplicaManager.$anonfun$appendToLocalLog$6(ReplicaManager.scala:1210)
	at scala.collection.StrictOptimizedMapOps.map(StrictOptimizedMapOps.scala:28)
	at scala.collection.StrictOptimizedMapOps.map$(StrictOptimizedMapOps.scala:27)
	at scala.collection.mutable.HashMap.map(HashMap.scala:35)
	at kafka.server.ReplicaManager.appendToLocalLog(ReplicaManager.scala:1198)
	at kafka.server.ReplicaManager.appendEntries$1(ReplicaManager.scala:754)
	at kafka.server.ReplicaManager.$anonfun$appendRecords$18(ReplicaManager.scala:874)
	at kafka.server.ReplicaManager.$anonfun$appendRecords$18$adapted(ReplicaManager.scala:874)
	at kafka.server.KafkaRequestHandler$.$anonfun$wrap$3(KafkaRequestHandler.scala:73)
	at kafka.server.KafkaRequestHandler.run(KafkaRequestHandler.scala:130)
	at java.base/java.lang.Thread.run(Unknown Source)

{noformat}
~~~~

### Comments (18)

1.

~~~~
{noformat}
[2023-10-20 02:31:00,204] ERROR [ReplicaManager broker=1] Error processing append operation on partition 2c69b88eab8670ef1fd0e55b81b9e000995386afd8756ea342494d36911e6f01-29 (kafka.server.ReplicaManager)
java.lang.NullPointerException: Cannot invoke "java.nio.ByteBuffer.hasArray()" because "this.intermediateBufRef" is null 
        at org.apache.kafka.common.utils.ChunkedBytesStream.<init>(ChunkedBytesStream.java:89)
        at org.apache.kafka.common.record.CompressionType$3.wrapForInput(CompressionType.java:105)
        at org.apache.kafka.common.record.DefaultRecordBatch.recordInputStream(DefaultRecordBatch.java:273)
        at org.apache.kafka.common.record.DefaultRecordBatch.compressedIterator(DefaultRecordBatch.java:277)
        at org.apache.kafka.common.record.DefaultRecordBatch.skipKeyValueIterator(DefaultRecordBatch.java:352)
        at org.apache.kafka.storage.internals.log.LogValidator.validateMessagesAndAssignOffsetsCompressed(LogValidator.java:358)
        at org.apache.kafka.storage.internals.log.LogValidator.validateMessagesAndAssignOffsets(LogValidator.java:165)
        at kafka.log.UnifiedLog.$anonfun$append$2(UnifiedLog.scala:805)
        at kafka.log.UnifiedLog.append(UnifiedLog.scala:1845)
        at kafka.log.UnifiedLog.appendAsLeader(UnifiedLog.scala:719)
        at kafka.cluster.Partition.$anonfun$appendRecordsToLeader$1(Partition.scala:1313)
        at kafka.cluster.Partition.appendRecordsToLeader(Partition.scala:1301)
        at kafka.server.ReplicaManager.$anonfun$appendToLocalLog$6(ReplicaManager.scala:1210)
        at scala.collection.TraversableLike.$anonfun$map$1(TraversableLike.scala:286)
        at scala.collection.immutable.HashMap$HashMap1.foreach(HashMap.scala:400)
        at scala.collection.immutable.HashMap$HashTrieMap.foreach(HashMap.scala:728)
        at scala.collection.immutable.HashMap$HashTrieMap.foreach(HashMap.scala:728)
        at scala.collection.TraversableLike.map(TraversableLike.scala:286)
        at scala.collection.TraversableLike.map$(TraversableLike.scala:279)
        at scala.collection.AbstractTraversable.map(Traversable.scala:108)
        at kafka.server.ReplicaManager.appendToLocalLog(ReplicaManager.scala:1198)
        at kafka.server.ReplicaManager.appendRecords(ReplicaManager.scala:754)
        at kafka.server.KafkaApis.handleProduceRequest(KafkaApis.scala:686)
        at kafka.server.KafkaApis.handle(KafkaApis.scala:180)
        at kafka.server.KafkaRequestHandler.run(KafkaRequestHandler.scala:149)
        at java.base/java.lang.Thread.run(Thread.java:833)
{noformat}
~~~~

2.

~~~~
cc [~divijvaidya] 
~~~~

3.

~~~~
I will look into this tomorrow. Assigning this to myself.
~~~~

4.

~~~~
In 3.6, we started using Buffer pool local to each request handler thread to perform decompression. The above stack trace indicates a null when we ask for a buffer from the buffer pool, returned by bufferQueue.pollfirst() at [https://github.com/apache/kafka/blob/c81a7252195261f649faba166ee723552bed4d81/clients/src/main/java/org/apache/kafka/common/utils/BufferSupplier.java#L76] 

Ideally that should not be possible bufferQueue.pollfirst() returns null only when bufferQueue is empty. And we already check fr bufferQueue being empty in the line above. Also this function is not thread safe. It doesn't need to be thread safe because a particular instance of buffer pool (DefaultSupplier) is associated with single thread (the request handler thread) and only one thread should be accessing it at one time. 

Either we are incorrectly accessing DefaultBufferSupplier.get() from two threads and causing race condition OR somehow in the same thread reference is being set to null/or garbage collected?!



I will try to eyeball to code here to see if I can find something. But practically [~twmb] it would be greatly useful if you can share your integration/unit test with us so that we can find a deterministic way to reproduce it.
~~~~

5.

~~~~
I think the potential bug could be in how we are closing the ChunkedBytesStream and returning the buffer for re-use later.
{code:java}
@Override
public void close() throws IOException {
    byte[] mybuf = intermediateBuf;
    intermediateBuf = null;

    InputStream input = in;
    in = null;

    if (mybuf != null)
        bufferSupplier.release(intermediateBufRef);
    if (input != null)
        input.close();
} {code}
I -am suspecting this because, we are setting underlying buffer behind the ByteBuffer to be null, which will allow it to be garbage collected. But we don't want it to be GC'ed because we simply want to return it to the pool so that it can be used later again.-

-I will verify this tomorrow with a test and have a fix out soon.-
Nevermind, it will not be GC'ed because we have a reference to it via mybuf. I verified it using a test.


{code:java}
@Test
public void testValidReturnToBufferSupplierOnClose() throws IOException, InterruptedException {
    final BufferSupplier threadSpecificSupplier = BufferSupplier.create();
    final boolean delegateSkipToSourceStream = false;

    final ByteBuffer inputBuffer = ByteBuffer.allocate(SIZE_LITTLE_LARGE_THAN_INTERMEDIATE_BUFFER_SIZE);
    final ByteBuffer originalIntermediateBufferRef;

    try (ChunkedBytesStream is = new ChunkedBytesStream(new ByteBufferInputStream(inputBuffer.duplicate()), threadSpecificSupplier, DEFAULT_INTERMEDIATE_BUFFER_SIZE, delegateSkipToSourceStream)) {
        assertNotNull(is.intermediateBufRef);
        // read everything to verify sanity
        Utils.readFully(is, ByteBuffer.allocate(inputBuffer.capacity()));
        // store reference of intermediate buffer provided by buffer supplier
        originalIntermediateBufferRef = is.intermediateBufRef;
    }

    // The intermediate buffer should have been returned to buffer supplier.
    // Force GC to rule out any lingering references. Notably this is just a hint and may not cause actual GC.
    System.gc();
    // Wait to GC to do it's magic.
    Thread.sleep(2000);

    try (ChunkedBytesStream is = new ChunkedBytesStream(new ByteBufferInputStream(inputBuffer.duplicate()), threadSpecificSupplier, DEFAULT_INTERMEDIATE_BUFFER_SIZE, delegateSkipToSourceStream)) {
        assertNotNull(is.intermediateBufRef);
        assertEquals(originalIntermediateBufferRef, is.intermediateBufRef);
    }
} {code}
~~~~

6.

~~~~
Maybe related?
{noformat}
org.apache.kafka.common.errors.InvalidRequestException: Error getting request for apiKey: PRODUCE, apiVersion: 9, connectionId: 127.0.0.1:9092-127.0.0.1:46394-145, listenerName: ListenerName(PLAINTEXT), principal: User:ANONYMOUS
Caused by: java.nio.BufferUnderflowException
        at java.base/java.nio.Buffer.nextGetIndex(Buffer.java:699)
        at java.base/java.nio.HeapByteBuffer.get(HeapByteBuffer.java:165)
        at org.apache.kafka.common.utils.ByteUtils.readUnsignedVarint(ByteUtils.java:160)
        at org.apache.kafka.common.protocol.ByteBufferAccessor.readUnsignedVarint(ByteBufferAccessor.java:70)
        at org.apache.kafka.common.message.ProduceRequestData.read(ProduceRequestData.java:195)
        at org.apache.kafka.common.message.ProduceRequestData.<init>(ProduceRequestData.java:114)
        at org.apache.kafka.common.requests.ProduceRequest.parse(ProduceRequest.java:256)
        at org.apache.kafka.common.requests.AbstractRequest.doParseRequest(AbstractRequest.java:178)
        at org.apache.kafka.common.requests.AbstractRequest.parseRequest(AbstractRequest.java:172)
        at org.apache.kafka.common.requests.RequestContext.parseRequest(RequestContext.java:95)
        at kafka.network.RequestChannel$Request.<init>(RequestChannel.scala:108)
        at kafka.network.Processor.$anonfun$processCompletedReceives$1(SocketServer.scala:1148)
        at java.base/java.util.LinkedHashMap$LinkedValues.forEach(LinkedHashMap.java:647)
        at kafka.network.Processor.processCompletedReceives(SocketServer.scala:1126)
        at kafka.network.Processor.run(SocketServer.scala:1012)
        at java.base/java.lang.Thread.run(Thread.java:833)
{noformat}

Next comment I'll attach a small script that can be used to repro; I'm testing it a few times to iron out bash kinks
~~~~

7.

~~~~
Sorry, one more note: I'm also occasionally getting InvalidRecordException frequently without NPE. The attached repro script ignores InvalidRecordException because it's easier to get a failure that contains NPE when ignoring that error, when not ignoring that error, frequently the test fails with InvalidRecordException without an NPE (so, different sort of problem -- but perhaps related).

Attached is a script that will clone the franz-go repo, optionally install Go, and loop docker compose up/down with integration tests. Once the script stops, container logs are in CONTAINER_LOGS, and franz-go debug logs are in FRANZ_FAIL. In FRANZ_FAIL, you can search for `--- FAIL` to see the error that caused the test to stop (usually UNKNOWN_SERVER_ERROR) and then search for the first instance of that error -- it will be returned from producing. In CONTAINER_LOGS, you can look for NullPointerException or InvalidRecordException.

 [^repro.sh] 
~~~~

8.

~~~~
Thank you for the nice script [~twmb] . I am able to reproduce it locally on my setup. Notably, I don't have to restart Kafka server to reproduce this. 

I haven't found the root cause yet. Will keep this Jira updated if I find anything. 
~~~~

9.

~~~~
I think I found a quite fundamental problem here.

By design, BufferPool is not thread safe in Kafka [1]. And that is acceptable because the buffer pool instance is local to a request handler thread [2]. Hence we assume that a particular buffer pool will always be accessed only by it's owner thread.

However, unfortunately, seems like that this assumption is not true!

I have same BufferPool being accessed by two different request handler threads. The first access is legitimate while trying to process an API request at [3]. The second access comes from a change introduced in [https://github.com/apache/kafka/commit/56dcb837a2f1c1d8c016cfccf8268a910bb77a36] where we are passing the stateful variable of a request (including the buffer supplier) to a callback which could be executed by a different request handler thread [4] . Hence, we will end up in a situation where stateful members such as requestLocal of one thread is being accessed by another different thread. This is a bug.

*Impact of the bug*

This bug has been present since 3.5 but the impact is visible in 3.6 because in 3.6 we expanded the use of request local buffer pool to perform decompression. Earlier the buffer pool was only being used in read path and by log cleaner. The callback mentioned above calls appendToLocalLog and prior to 3.6 this code path wasn't using requestLocal.

All 3.6 operations which call the following line in ReplicaManager are impacted which is basically use case of transactions and also specifically to AddPartitionsToTxnManager API calls.

```
addPartitionsToTxnManager.foreach({_}.addTxnData(node, notYetVerifiedTransaction, KafkaRequestHandler.wrap(appendEntries(entriesPerPartition)({_}))))
```

*Possible solutions*
[~jolshan] can you please take a look and see if we can avoid leaking the requestLocal (bufferpool) belonging to one thread to the other thread?

One way we can fix this is to store the bufferpool reference in ThreadLocal and instead of passing the reference around, whenever we want to use bufferpool, we will directly ask the executing thread for it. This will ensure that a thread is always using it's own instance of the buffer pool. [~ijuma] since you wrote the original requestLocal buffer pool, what do you think about this solution?

Another option is to extract out function `appendEntries` outside of `appendRecords` since it is `appendEntries` is invoked as a callback and shouldn't rely on local variable/state of `appendRecords`.



[1] [https://github.com/apache/kafka/blob/9c77c17c4eae19af743e551e8e7d8b49b07c4e99/clients/src/main/java/org/apache/kafka/common/utils/BufferSupplier.java#L27] 

[2] [https://github.com/apache/kafka/blob/9c77c17c4eae19af743e551e8e7d8b49b07c4e99/core/src/main/scala/kafka/server/KafkaRequestHandler.scala#L96] 

[3] [https://github.com/apache/kafka/blob/9c77c17c4eae19af743e551e8e7d8b49b07c4e99/core/src/main/scala/kafka/server/KafkaRequestHandler.scala#L154] 

[4] [https://github.com/apache/kafka/blob/526d0f63b5d82f8fb50c97aea9c61f8f85467e92/core/src/main/scala/kafka/server/ReplicaManager.scala#L874] 

[5] [https://docs.oracle.com/javase/8/docs/api/java/lang/ThreadLocal.html] 
~~~~

10.

~~~~
Good catch. I think we should review the design of this change in closer detail to understand the full implications - is the buffer supplier the only issue or are there others? The assumption is that anything that is executed in a different thread would have to ensure thread-safety, etc.
~~~~

11.

~~~~
Thanks [~divijvaidya] and [~ijuma] for looking at this. I am also investigating now.

For folks who are affected by this issue, disabling verification either by static config + rolling or dynamically should stop the issue.

{{transaction.partition.verification.enable=false

}}

Just for clarification, the AddPartitionsToTxn code was not added until 3.6 since the 3.5 version was reverted ([https://github.com/apache/kafka/commit/928070e3206867fa81bafbb138373bcb0e2ba962)]

However, there was some other way to access the bug in 3.5? I will work in the background to resolve this, but was a little bit confused about that part. 
~~~~

12.

~~~~
> However, there was some other way to access the bug in 3.5? I will work in the background to resolve this, but was a little bit confused about that part. 

My assumption that the bug is present in 3.5 was based on the 3.5 tag associated with the original commit. I missed the part that it has been reverted. Given that, I don't think 3.5 is impacted and neither does the reproducer suggest so.

I will not get to work on the fix at least this week. So I will move this Jira to unassigned. [~jolshan] please feel free to pick up if you are working on this. 

[~twmb], would you like to verify the workaround that Justine mentioned above and see if that unblocks you? Once we are sure about the workaround, we can find a way to communicate it to the broader community until a fix is in place.


 
~~~~

13.

~~~~
I've loop tested this a few times at this point, and so far the configuration option `transaction.partition.verification.enable=false` prevents test failures. I'm going to go ahead and close KAFKA-15657 and KAFKA-15656 which both seem like different manifestations of this issue.
~~~~

14.

~~~~
I will definitely work on this [~divijvaidya].
I plan on moving the method appendEntries out and supplying the correct requestLocal in the callback.

I am also filing a new Jira to address the requestLocal's future, since this mistake was easy to make. 
https://issues.apache.org/jira/browse/KAFKA-15674
~~~~

15.

~~~~
Thanks [~jolshan] . I will add my thoughts on how to prevent this in future the new Jira you started. As a summary, I think we might want to start working towards a "debug" mode in the broker which will enable assertions for different invariants in Kafka. Invariants could be derived from formal verification that Jack and others have shared with the community earlier OR from tribal knowledge in the community such as network threads should not perform any storage IO. The release qualification will run the broker in "debug" mode and will validate these assertions while running different series of tests. 

EDIT - I started a thread in dev mailing list to solicit ideas on detecting & preventing hard bugs [https://lists.apache.org/thread/zjcyp4h9kkl3gjfblgcwodf2y8oyy0hj] 
~~~~

16.

~~~~
Our existing tests in Apache Kafka missed catching this bug. Creating a ticket at https://issues.apache.org/jira/browse/KAFKA-15764 to bolster our test suite and fill the missing gap.
~~~~

17.

~~~~
Is this Jira resolved?  I saw all the three linked PRs are merged in already.
~~~~

18.

~~~~
Yes. [~hcai@pinterest.com] this is resolved. KAFKA-15784 which was discovered while working on this is still open, but I'm working on it.
~~~~

---

## KAFKA-15693: Disabling scheduled rebalance delay in Connect can lead to indefinitely unassigned connectors and tasks

https://issues.apache.org/jira/browse/KAFKA-15693

Given fix versions: 3.5.2, 3.6.1, 3.7.0
JIRA affects (masked from the system): 2.3.0, 2.3.1, 2.4.0, 2.4.1, 2.5.0, 2.5.1, 2.6.0, 2.6.1, 2.6.2, 2.6.3, 2.7.0, 2.7.1, 2.7.2, 2.8.0, 2.8.1, 2.8.2, 3.0.0, 3.0.1, 3.0.2, 3.1.0, 3.1.1, 3.1.2, 3.2.0, 3.2.1, 3.2.2, 3.2.3, 3.3.0, 3.3.1, 3.3.2, 3.4.0, 3.4.1, 3.5.0, 3.5.1, 3.6.0, 3.7.0

- `KAFKA-15693@2.8.1`: config 2.8.1, metadata answer **affected** (listed_affected)
- `KAFKA-15693@2.2.2`: config 2.2.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
Kafka Connect supports deferred resolution of imbalances when using the incremental rebalancing algorithm introduced in [KIP-415|https://cwiki.apache.org/confluence/display/KAFKA/KIP-415%3A+Incremental+Cooperative+Rebalancing+in+Kafka+Connect]. When enabled, this feature introduces a configurable delay period between when "lost" assignments (i.e., connectors and tasks that were assigned to a worker in the previous round of rebalance but are not assigned to a worker during the current round of rebalance) are detected and when they are reassigned to a worker. The delay can be configured with the {{scheduled.rebalance.max.delay.ms}} property.

If this property is set to 0, then there should be no delay between when lost assignments are detected and when they are reassigned. Instead, however, this configuration can cause lost assignments to be withheld during a rebalance, remaining unassigned until the next rebalance, which, because scheduled delays are disabled, will not happen on its own and will only take place when unrelated conditions warrant it (such as the creation or deletion of a connector, a worker joining or leaving the cluster, new task configs being generated for a connector, etc.).
~~~~

### Comments (1)

1.

~~~~
For all affected versions, the most graceful workaround is to instead set the {{scheduled.rebalance.max.delay.ms}} property to an extremely low value (such as 1) instead of 0.
~~~~

---

## KAFKA-15834: Subscribing to non-existent topic blocks StreamThread from stopping

https://issues.apache.org/jira/browse/KAFKA-15834

Given fix versions: 3.8.0
JIRA affects (masked from the system): 3.6.0

- `KAFKA-15834@3.6.0`: config 3.6.0, metadata answer **affected** (listed_affected)
- `KAFKA-15834@3.5.2`: config 3.5.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
In NamedTopologyIntegrationTest#shouldContinueProcessingOtherTopologiesWhenNewTopologyHasMissingInputTopics a topology is created which references an input topic which does not exist. The test as-written passes, but the KafkaStreams#close(Duration) at the end times out, and leaves StreamsThreads running.

From some cursory investigation it appears that this is happening:
1. The consumer calls the StreamsPartitionAssignor, which calls TaskManager#handleRebalanceStart as a side-effect
2. handleRebalanceStart sets the rebalanceInProgress flag
3. This flag is checked by StreamThread.runLoop, and causes the loop to remain running.
4. The consumer never calls StreamsRebalanceListener#onPartitionsAssigned, because the topic does not exist
5. Because no partitions are ever assigned, the TaskManager#handleRebalanceComplete never clears the rebalanceInProgress flag
 
This log message is printed in a tight loop while the close is ongoing and the consumer is being polled with zero duration:
{noformat}
[2023-11-15 11:42:43,661] WARN [Consumer clientId=NamedTopologyIntegrationTestshouldContinueProcessingOtherTopologiesWhenNewTopologyHasMissingInputTopics-942756f8-5213-4c44-bb6b-5f805884e026-StreamThread-1-consumer, groupId=NamedTopologyIntegrationTestshouldContinueProcessingOtherTopologiesWhenNewTopologyHasMissingInputTopics] Received unknown topic or partition error in fetch for partition unique_topic_prefix-topology-1-store-repartition-0 (org.apache.kafka.clients.consumer.internals.FetchCollector:321)
{noformat}
Practically, this means that this test leaks two StreamsThreads and the associated clients and sockets, and delays the completion of the test until the KafkaStreams#close(Duration) call times out.

Either we should change the rebalanceInProgress flag to avoid getting stuck in this rebalance state, or figure out a way to shut down a StreamsThread that is in an extended rebalance state during shutdown.
~~~~

### Comments (4)

1.

~~~~
Thank for reporting and such a detailed analysis, [~gharris1727]! 
~~~~

2.

~~~~
Yeah great analysis, thanks [~gharris1727] 

I'm a bit confused by point #4, however – is this a change in behavior (possibly related to KIP-848)? It's my understanding that the #onPartitionsAssigned callback is guaranteed to always be invoked regardless of whether the set of partitions being newly assigned is non-empty or not. This is in contrast with the #onPartitionsRevoked and #onPartitionsLost callbacks, which are only invoked when the set of partitions to act upon is non-empty.

I think one could argue that this inconsistency is not ideal, but the behavior of always invoking #onPartitionsAssigned is a stated guarantee in the public contract of ConsumerRebalanceListener. See [this paragraph|https://github.com/apache/kafka/blob/254335d24ab6b6d13142dcdb53fec3856c16de9e/clients/src/main/java/org/apache/kafka/clients/consumer/ConsumerRebalanceListener.java#L67] of the javadocs. In other words, I don't think we can change this without a KIP, and if this behavior was modified recently then we need to revert that change until a KIP is accepted.
~~~~

3.

~~~~
I just checked the current code and it looks like we do still respect the guarantee of invoking #onPartitionsAssigned in all cases. So I don't think step #4 is correct. Did you happen to see anything in the logs that would suggest the StreamThread was continuing in its regular loop and never stopping due to the rebalanceInProgress flag? Or is it possible that it's hanging somewhere in the shutdown process (or even in the rebalance itself)?

I'm just wondering if it might be related to the Producer, not the Consumer. I know we had some issues with the Producer#close hanging in the past, and that it was related to users deleting topics from under the app, which would be a similar situation to what you found here. I'm not sure if we ever fixed that, maybe [~mjsax] will remember the ticket for the Producer issue?
~~~~

4.

~~~~
Found the ticket: https://issues.apache.org/jira/browse/KAFKA-9398

And yes, it's still unresolved. 

Given all the above, I think we can honestly just disable/remove the test, as the named topologies feature was never made into a real public API. I do know of a few people who are using it anyway but they're aware it was only an experimental feature and not fully supported by Streams. So imo we don't need to go out of our way to fix any flaky tests: provided we can demonstrate that the issue is specific to named topologies and not potentially an issue with Streams itself. Of course in this case it's actually the latter, but we've recognized the root cause as a known issue, so I don't think there's anything more this test can do for us besides be flaky and annoy everyone.

Thanks for digging into this! 
~~~~

---

## KAFKA-16017: Checkpointed offset is incorrect when task is revived and restoring 

https://issues.apache.org/jira/browse/KAFKA-16017

Given fix versions: 3.6.2, 3.7.0
JIRA affects (masked from the system): 3.3.1

- `KAFKA-16017@3.3.1`: config 3.3.1, metadata answer **affected** (listed_affected)
- `KAFKA-16017@3.3.0`: config 3.3.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
Streams checkpoints the wrong offset when a task is revived after a {{TaskCorruptedException}} and the task is then migrated to another stream thread during restoration.

This might happen in a situation like the following if the Streams application runs under EOS:

1. Streams encounters a Network error which triggers a {{TaskCorruptedException}}
2. The task that encountered the exception is closed dirty and revived. The state store directory is wiped out and a rebalance is triggered.
3. Until the sync of the rebalance is received the revived task is restoring.
4. When the sync is received the revived task is revoked and a new rebalance is triggered. During the revocation the task is closed cleanly and a checkpoint file is written.
5. With the next rebalance the task moves back to stream thread from which it was revoked, read the checkpoint and starts restoring. (I might be enough if the task moves to a stream thread on the same Streams client that shares the same state directory).
6. The state of the task misses some records

To mitigate the issue one can restart the the stream thread and delete of the state on disk. After that the state restores completely from the changelog topic and the state does not miss any records anymore.

The root cause is that the checkpoint that is written in step 4 contains the offset that the record collector stored when it sent the records to the changelog topic. However, since in step 2 the state directory is wiped out, the state does not contain those records anymore. It only contains the records that it restored in step 3 which might be less. The root cause of this is that the offsets in the record collector are not cleaned up when the record collector is closed. 

I created a repro under https://github.com/cadonna/kafka/tree/KAFKA-16017.

The repro can be started with

{code}
./gradlew streams:test -x checkstyleMain -x checkstyleTest -x spotbugsMain -x spotbugsTest --tests RestoreIntegrationTest.test --info > test.log
{code}

The repro writes records into a state store and tries to retrieve them again (https://github.com/cadonna/kafka/blob/355bdfe33df403e73deaac0918aae7d2c736342c/streams/src/test/java/org/apache/kafka/streams/integration/RestoreIntegrationTest.java#L582). It will throw an {{IllegalStateException}} if it cannot find a record in the state (https://github.com/cadonna/kafka/blob/355bdfe33df403e73deaac0918aae7d2c736342c/streams/src/test/java/org/apache/kafka/streams/integration/RestoreIntegrationTest.java#L594). Once the offsets in the record collector are cleared on close (https://github.com/cadonna/kafka/blob/355bdfe33df403e73deaac0918aae7d2c736342c/streams/src/main/java/org/apache/kafka/streams/processor/internals/RecordCollectorImpl.java#L332 and https://github.com/cadonna/kafka/blob/355bdfe33df403e73deaac0918aae7d2c736342c/streams/src/main/java/org/apache/kafka/streams/processor/internals/RecordCollectorImpl.java#L349), the {{IllegalStateException}} does not occur anymore.

In the logs you can check for 
- {{Restore batch end offset is}} which are the restored offsets in the state.
- {{task [0_1] Writing checkpoint:}} which are the written checkpoints.
- {{task [0_1] Checkpointable offsets}} which show the offsets coming from the sending records to the changelog topic {{RestoreIntegrationTesttest-stateStore-changelog-1}}
Always the last instances of these before the {{IllegalStateException}} is thrown.

You will see that the restored offsets are less than the offsets that are written to the checkpoint. The offsets written to the checkpoint come from the offsets stored when sending the records to the changelog topic.  


~~~~

---

## KAFKA-16226: Java client: Performance regression in Trogdor benchmark with high partition counts

https://issues.apache.org/jira/browse/KAFKA-16226

Given fix versions: 3.6.2, 3.7.1, 3.8.0
JIRA affects (masked from the system): 3.6.1, 3.7.0

- `KAFKA-16226@3.6.1`: config 3.6.1, metadata answer **affected** (listed_affected)
- `KAFKA-16226@3.6.0`: config 3.6.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
h1. Background

https://issues.apache.org/jira/browse/KAFKA-15415 implemented optimisation in java-client to skip backoff period if client knows of a newer leader, for produce-batch being retried.
h1. What changed

The implementation introduced a regression noticed on a trogdor-benchmark running with high partition counts(36000!).
With regression, following metrics changed on the produce side.
 # record-queue-time-avg: increased from 20ms to 30ms.
 # request-latency-avg: increased from 50ms to 100ms.

h1. Why it happened

As can be seen from the original [PR|https://github.com/apache/kafka/pull/14384] RecordAccmulator.partitionReady() & drainBatchesForOneNode() started using synchronised method Metadata.currentLeader(). This has led to increased synchronization between KafkaProducer's application-thread that call send(), and background-thread that actively send producer-batches to leaders.

Lock profiles clearly show increased synchronisation in KAFKA-15415 PR(highlighted in {color:#de350b}Red{color}) Vs baseline ( see below ). Note the synchronisation is much worse for paritionReady() in this benchmark as its called for each partition, and it has 36k partitions!
h3. Lock Profile: Kafka-15415

!kafka_15415_lock_profile.png!
h3. Lock Profile: Baseline

!baseline_lock_profile.png!
h1. Fix

Synchronization has to be reduced between 2 threads in order to address this. [https://github.com/apache/kafka/pull/15323] is a fix for it, as it avoids using Metadata.currentLeader() instead rely on Cluster.leaderFor().

With the fix, lock-profile & metrics are similar to baseline.

 
~~~~

---

## KAFKA-16243: Idle kafka-console-consumer with new consumer group protocol preemptively leaves group

https://issues.apache.org/jira/browse/KAFKA-16243

Given fix versions: 3.8.0
JIRA affects (masked from the system): 3.7.0

- `KAFKA-16243@3.7.0`: config 3.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-16243@3.6.2`: config 3.6.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
Using the new consumer group protocol with kafka-console-consumer.sh, I find that if I leave the consumer with no records to process for 5 minutes (max.poll.interval.ms = 300000ms), the tool logs the following warning message and leaves the group.

"consumer poll timeout has expired. This means the time between subsequent calls to poll() was longer than the configured max.poll.interval.ms, which typically implies that the poll loop is spending too much time processing messages. You can address this either by increasing max.poll.interval.ms or by reducing the maximum size of batches returned in poll() with max.poll.records."

With the older consumer, this did not occur.

The reason is that the consumer keeps a poll timer which is used to ensure liveness of the application thread. The poll timer automatically updates while the `Consumer.poll(Duration)` method is blocked, while the newer consumer only updates the poll timer when a new call to `Consumer.poll(Duration)` is issued. This means that the kafka-console-consumer.sh tools, which uses a very long timeout by default, works differently with the new consumer.
~~~~

---

## KAFKA-16254: Allow MM2 to fully disable offset sync feature

https://issues.apache.org/jira/browse/KAFKA-16254

Given fix versions: 3.9.0
JIRA affects (masked from the system): 3.5.0, 3.6.0, 3.7.0

- `KAFKA-16254@3.7.0`: config 3.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-16254@3.4.1`: config 3.4.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.5, 3.9

### Description

~~~~
*Background:* 
At the moment syncing offsets feature in MM2 is broken to 2 parts
 # One is in `MirrorSourceTask` where we store the new recored's offset on target cluster to {{offset_syncs}} internal topic after mirroring the record. 
Before KAFKA-14610 in 3.5 MM2 used to just queue the offsets and publish them later but since 3.5 this behaviour changed we now publish any offset syncs that we've queued up, but have not yet been able to publish when `MirrorSourceTask.commit` get invoked. This introduced an over head to commit process.
 # The second part is in checkpoints source task where we use the new record offsets from {{offset_syncs}} and update {{checkpoints}} and {{__consumer_offsets}} topics.

*Problem:*
For customers who only use MM2 for mirroring data and not interested in syncing offsets feature they now can disable the second part of this feature which is by disabling {{emit.checkpoints.enabled}} and/or {{sync.group.offsets.enabled}} to disable emitting {{__consumer_offsets}} topic but nothing disabling 1st part of the feature. 

The problem get worse if they disabled MM2 from creating offset syncs internal topic as 
1. this will increase throughput as MM2 will try to force trying to update the offset with every mirrored batch which impacting the performance of our MM2.
2. Get too many error logs because they don't create the sync offset topic as they don't use the feature.

*Possible solution:*
Allow customers to fully disable the feature if they don't really need it similar to how we fully can disable other MM2 features like heartbeat feature by adding a new config.
~~~~

### Comments (1)

1.

~~~~
Changing target fix version to 3.9 since this is not a blocker and we are past code freeze
~~~~

---

## KAFKA-16541: Potential leader epoch checkpoint file corruption on OS crash

https://issues.apache.org/jira/browse/KAFKA-16541

Given fix versions: 3.8.0
JIRA affects (masked from the system): 3.7.0

- `KAFKA-16541@3.7.0`: config 3.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-16541@3.6.2`: config 3.6.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.8.0, 3.7.1, 3.6.0

### Description

~~~~
Pointed out by [~junrao] on [GitHub|https://github.com/apache/kafka/pull/14242#discussion_r1556161125]

[A patch for KAFKA-15046|https://github.com/apache/kafka/pull/14242] got rid of fsync of leader-epoch ckeckpoint file in some path for performance reason.

However, since now checkpoint file is flushed to the device asynchronously by OS, content would corrupt if OS suddenly crashes (e.g. by power failure, kernel panic) in the middle of flush.

Corrupted checkpoint file could prevent Kafka broker to start-up
~~~~

### Comments (5)

1.

~~~~
Thanks for filing the jira, [~ocadaruma] !  Since this is a regression, it would be useful to have this fixed in 3.8.0 and 3.7.1.

One way to fix it is to (1) change LeaderEpochFileCache.truncateFromEnd and LeaderEpochFileCache.truncateFromStart to only write to memory without writing to the checkpoint file, (2) change the implementation of [renamDir|https://github.com/apache/kafka/blob/3.6.0/core/src/main/scala/kafka/log/UnifiedLog.scala#L681] so that it doesn't reinitialize from the file and just change the Path of the backing CheckpointFile.
~~~~

2.

~~~~
[~ocadaruma] : Will you be able to work on this soon? The 3.8.0 code freeze is getting close. Thanks.
~~~~

3.

~~~~
[~junrao] Yes.
My concern now is only changing renameDir may not be enough, so I'm trying to figure out if we can fix in another way without checking all call paths
~~~~

4.

~~~~
[~junrao] Hi, i've just submitted a patch. PTAL
~~~~

5.

~~~~
Merged the PR to trunk.
~~~~

---

## KAFKA-16566: Update consumer static membership fencing system test to support new protocol

https://issues.apache.org/jira/browse/KAFKA-16566

Given fix versions: 3.8.0
JIRA affects (masked from the system): 3.7.0

- `KAFKA-16566@3.7.0`: config 3.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-16566@3.6.2`: config 3.6.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
consumer_test.py contains OffsetValidationTest.test_fencing_static_consumer that verifies the sequence in which static members join a group when using conflicting instance id. This behaviour is different in the classic and consumer protocol, so the tests should be updated to set the right expectations when running with the new consumer protocol. Note that what the tests covers (params, setup), apply to both protocols. It is the expected results that are not the same. 

When conflicts between static members joining a group:

Classic protocol: all members join the group with the same group instance id, and then the first one will eventually receive a HB error with FencedInstanceIdException

Consumer protocol: new member with an instance Id already in use is not able to join, receiving an UnreleasedInstanceIdException in the response to the HB to join the group.  
~~~~

### Comments (2)

1.

~~~~
I'm a bit confused – I thought we haven't migrated Streams over to the new consumer rebalancing protocol. Or is this referring to something else? What is the "classic" vs "consumer" protocol? And when/why did we migrate our system tests to using it? Does it have to do with static membership specifically?

 

Sorry for being out of the loop here
~~~~

2.

~~~~
Hey [~ableegoldman], this is specific to the static membership, and related to the consumer system tests only, that were parametrized to run with the legacy and new protocol/consumer. You're on the right page regarding the rest: Streams tests haven't been migrated yet because it's not integrated with the new protocol. 

Classic protocol refers to the existing group protocol, and Consumer protocol refers to the new one introduced with KIP-848 (just using the names proposed to be used in the configs to switch between both)
~~~~

---

## KAFKA-16883: Zookeeper-Kraft failing migration - RPC got timed out before it could be sent

https://issues.apache.org/jira/browse/KAFKA-16883

Given fix versions: 3.7.1
JIRA affects (masked from the system): 3.6.1, 3.6.2, 3.7.0

- `KAFKA-16883@3.6.1`: config 3.6.1, metadata answer **affected** (listed_affected)
- `KAFKA-16883@3.6.0`: config 3.6.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.6.1, 3.6.2, 3.7.0, 3.7, 3.6, v3.7.1, 3.7.1

### Description

~~~~
Despite several attempts to migrate from Zookeeper cluster to Kraft, it failed to properly migrate.

We spawn a need cluster fully healthy with 3 Kafka nodes connected to 3 Zookeeper nodes. 3 new Kafka nodes are there for the new controllers.
It was tested with Kafka 3.6.1, 3.6.2 and 3.7.0.

it might be linked to KAFKA-15330.

The controllers are started without issue. When the brokers are then configured for the migration, the migration is not starting. Once the last broker is restarted, we got the following logs.
{code:java}
[2024-06-03 15:11:48,192] INFO [ReplicaFetcherThread-0-11]: Stopped (kafka.server.ReplicaFetcherThread)
[2024-06-03 15:11:48,193] INFO [ReplicaFetcherThread-0-11]: Shutdown completed (kafka.server.ReplicaFetcherThread)
{code}
Then we only get the following every 30s
{code:java}
[2024-06-03 15:12:04,163] INFO [BrokerLifecycleManager id=12 isZkBroker=true] Unable to register the broker because the RPC got timed out before it could be sent. (kafka.server.BrokerLifecycleManager)
[2024-06-03 15:12:34,297] INFO [BrokerLifecycleManager id=12 isZkBroker=true] Unable to register the broker because the RPC got timed out before it could be sent. (kafka.server.BrokerLifecycleManager)
[2024-06-03 15:13:04,536] INFO [BrokerLifecycleManager id=12 isZkBroker=true] Unable to register the broker because the RPC got timed out before it could be sent. (kafka.server.BrokerLifecycleManager){code}

The config on the controller node is the following
{code:java}
kafka0202e1 ~]$  sudo grep -v '^\s*$\|^\s*\#' /etc/kafka/server.properties  | grep -v password | sort
advertised.host.name=kafka0202e1.ahub.sb.eu.ginfra.net
broker.rack=e1
controller.listener.names=CONTROLLER
controller.quorum.voters=20@kafka0202e1.ahub.sb.eu.ginfra.net:9093,21@kafka0202e2.ahub.sb.eu.ginfra.net:9093,22@kafka0202e3.ahub.sb.eu.ginfra.net:9093
default.replication.factor=3
delete.topic.enable=false
group.initial.rebalance.delay.ms=3000
inter.broker.protocol.version=3.7
listeners=CONTROLLER://kafka0202e1.ahub.sb.eu.ginfra.net:9093
listener.security.protocol.map=CONTROLLER:SSL,PLAINTEXT:PLAINTEXT,SSL:SSL,SASL_PLAINTEXT:SASL_PLAINTEXT,SASL_SSL:SASL_SSL
log.dirs=/data/kafka
log.message.format.version=3.6
log.retention.check.interval.ms=300000
log.retention.hours=240
log.segment.bytes=1073741824
min.insync.replicas=2
node.id=20
num.io.threads=8
num.network.threads=3
num.partitions=1
num.recovery.threads.per.data.dir=1
offsets.topic.replication.factor=3
process.roles=controller
security.inter.broker.protocol=SSL
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600
socket.send.buffer.bytes=102400
ssl.cipher.suites=TLS_AES_256_GCM_SHA384
ssl.client.auth=required
ssl.enabled.protocols=TLSv1.3
ssl.endpoint.identification.algorithm=HTTPS
ssl.keystore.location=/etc/kafka/ssl/keystore.ts
ssl.keystore.type=JKS
ssl.secure.random.implementation=SHA1PRNG
ssl.truststore.location=/etc/kafka/ssl/truststore.ts
transaction.state.log.min.isr=3
transaction.state.log.replication.factor=3
unclean.leader.election.enable=false
zookeeper.connect=10.135.65.199:2181,10.133.65.199:2181,10.137.64.56:2181,
zookeeper.metadata.migration.enable=true
 {code}

The config on the broker node is the following
{code}
$ sudo grep -v '^\s*$\|^\s*\#' /etc/kafka/server.properties  | grep -v password | sort
advertised.host.name=kafka0201e3.ahub.sb.eu.ginfra.net
advertised.listeners=SSL://kafka0201e3.ahub.sb.eu.ginfra.net:9092
broker.id=12
broker.rack=e3
controller.listener.names=CONTROLLER # added once all controllers were started
controller.quorum.voters=20@kafka0202e1.ahub.sb.eu.ginfra.net:9093,21@kafka0202e2.ahub.sb.eu.ginfra.net:9093,22@kafka0202e3.ahub.sb.eu.ginfra.net:9093 # added once all controllers were started
default.replication.factor=3
delete.topic.enable=false
group.initial.rebalance.delay.ms=3000
inter.broker.protocol.version=3.7
listener.security.protocol.map=CONTROLLER:SSL,PLAINTEXT:PLAINTEXT,SSL:SSL,SASL_PLAINTEXT:SASL_PLAINTEXT,SASL_SSL:SASL_SSL
listeners=SSL://kafka0201e3.ahub.sb.eu.ginfra.net:9092
log.dirs=/data/kafka
log.retention.check.interval.ms=300000
log.retention.hours=240
log.segment.bytes=1073741824
min.insync.replicas=2
num.io.threads=8
num.network.threads=3
num.partitions=1
num.recovery.threads.per.data.dir=1
offsets.topic.replication.factor=3
security.inter.broker.protocol=SSL
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600
socket.send.buffer.bytes=102400
ssl.cipher.suites=TLS_AES_256_GCM_SHA384
ssl.client.auth=required
ssl.enabled.protocols=TLSv1.3
ssl.endpoint.identification.algorithm=HTTPS
ssl.keystore.location=/etc/kafka/ssl/keystore.ts
ssl.keystore.type=JKS
ssl.secure.random.implementation=SHA1PRNG
ssl.truststore.location=/etc/kafka/ssl/truststore.ts
transaction.state.log.min.isr=3
transaction.state.log.replication.factor=3
unclean.leader.election.enable=false
zookeeper.connect=10.133.65.199:2181,10.135.65.199:2181,10.137.64.56:2181,
zookeeper.connection.timeout.ms=6000
zookeeper.metadata.migration.enable=true # added once all controllers were started
{code}

When trying to move to the next step (`Migrating brokers to KRaft`), it fails to get controller quorum and crashes.
{code}
[2024-06-03 15:33:21,553] INFO [BrokerLifecycleManager id=12] Unable to register the broker because the RPC got timed out before it could be sent. (kafka.server.BrokerLifecycleManager)
[2024-06-03 15:33:32,549] ERROR [BrokerLifecycleManager id=12] Shutting down because we were unable to register with the controller quorum. (kafka.server.BrokerLifecycleManager)
[2024-06-03 15:33:32,550] INFO [BrokerLifecycleManager id=12] Transitioning from STARTING to SHUTTING_DOWN. (kafka.server.BrokerLifecycleManager)
[2024-06-03 15:33:32,551] INFO [broker-12-to-controller-heartbeat-channel-manager]: Shutting down (kafka.server.NodeToControllerRequestThread)
[2024-06-03 15:33:32,551] INFO [broker-12-to-controller-heartbeat-channel-manager]: Shutdown completed (kafka.server.NodeToControllerRequestThread)
[2024-06-03 15:33:32,551] ERROR [BrokerServer id=12] Received a fatal error while waiting for the controller to acknowledge that we are caught up (kafka.server.BrokerServer)
java.util.concurrent.CancellationException
{code}
~~~~

### Comments (2)

1.

~~~~
I re-executed the migration on v3.7.1 and now it works!
~~~~

2.

~~~~
Thanks for confirming your success [~nicolas.henneaux].

 

Looking at the log between 3.7.0 and 3.7.1, there were a handful of fixes related to metadata/controller and one fix specific to migrations (KAFKA-16563)

 
~~~~

---

## KAFKA-17112: StreamThread shutdown calls completeShutdown only in CREATED state

https://issues.apache.org/jira/browse/KAFKA-17112

Given fix versions: 4.0.0
JIRA affects (masked from the system): 3.9.0

- `KAFKA-17112@3.9.0`: config 3.9.0, metadata answer **affected** (listed_affected)
- `KAFKA-17112@3.8.1`: config 3.8.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
While running tests in `StreamThreadTest.java` in kafka/streams, I noticed the test left many lingering threads. Though the class runs `shutdown` after each test, the shutdown only executes `completeShutdown` if the StreamThread is in CREATED state. See [https://github.com/apache/kafka/blob/0b11971f2c94f7aadc3fab2c51d94642065a72e5/streams/src/test/java/org/apache/kafka/streams/processor/internals/StreamThreadTest.java#L231] and [https://github.com/apache/kafka/blob/0b11971f2c94f7aadc3fab2c51d94642065a72e5/streams/src/main/java/org/apache/kafka/streams/processor/internals/StreamThread.java#L1435]
 
For example, you may run test org.apache.kafka.streams.processor.internals.StreamThreadTest#shouldNotCloseTaskProducerWhenSuspending with commit 0b11971f2c94f7aadc3fab2c51d94642065a72e5. When the test calls `thread.shutdown()`, the thread is in `PARTITIONS_REVOKED` state. Thus, `completeShutdown` is not called. The test creates three lingering threads: 2 `StateUpdater` and 1 `TaskExecutor`
 
This means that calls to `thread.shutdown` has no effect in `StreamThreadTest.java`. 
~~~~

### Comments (8)

1.

~~~~
[~aoli-al] I think you are right. We are leaking the state updater and processing threads in that test. The issue is that when we create the stream thread we create and start the state updater thread and the processing threads. 

Would you be interested to fix this issue?
~~~~

2.

~~~~
Yes, I'm happy to submit a patch. I'm thinking of two potential fixes: 

1. extend the `shutdown()` method to `shutdown(boolean forceCleanup)`. 

{code}
    public void shutdown(boolean forceCleanup) {
        log.info("Informed to shut down");
        final State oldState = setState(State.PENDING_SHUTDOWN);
        if (oldState == State.CREATED || forceCleanup) {
            // The thread may not have been started. Take responsibility for shutting down
            completeShutdown(true);
        }
    }
{code}

2. make `completeShutdown` public and directly call it from the test. 

Which one do you think is better?
~~~~

3.

~~~~
[~aoli-al] I think it would be better to change where the state updater and the processing threads are started. I am not sure why we start the threads before we start the stream thread. If we start those threads in the same location where we start the stream thread, we should not need to change anything in our shutdown logic to not leak threads in tests.
~~~~

4.

~~~~
[~cadonna] Aren't stateUpdater and processingThread expected to be started in some tests since the parameterized tests control them.

{code}
    @Parameter(0)
    public boolean stateUpdaterEnabled = true;

    @Parameter(1)
    public boolean processingThreadsEnabled = true;

    @Parameters
    public static Collection<Object[]> data() {
        return Arrays.asList(new Object[][] {
            {false, false}, {true, false}, {true, true}
        });
    }
{code}

and here 

{code}
    private static StateUpdater maybeCreateAndStartStateUpdater(final boolean stateUpdaterEnabled,
                                                                final StreamsMetricsImpl streamsMetrics,
                                                                final StreamsConfig streamsConfig,
                                                                final Consumer<byte[], byte[]> restoreConsumer,
                                                                final ChangelogReader changelogReader,
                                                                final TopologyMetadata topologyMetadata,
                                                                final Time time,
                                                                final String clientId,
                                                                final int threadIdx) {
        if (stateUpdaterEnabled) {
            final String name = clientId + "-StateUpdater-" + threadIdx;
            final StateUpdater stateUpdater = new DefaultStateUpdater(
                name,
                streamsMetrics.metricsRegistry(),
                streamsConfig,
                restoreConsumer,
                changelogReader,
                topologyMetadata,
                time
            );
            stateUpdater.start();
            return stateUpdater;
        } else {
            return null;
        }
    }
{code}
~~~~

5.

~~~~
[~aoli-al] Yes, but I guess they are only expected to be started in tests that also start the stream thread. So ideally, the processing thread and the state updater thread should be started when the stream thread is started. I haven't double checked my assumption.
~~~~

6.

~~~~
[~cadonna]Thanks for your reply! I've tried moving `stateUpdater.start();` to `StreamThread::start`. This does not work for many tests because the `StreamTread::start` is never called. 

{code}
    @Test
    public void shouldLogAndRecordSkippedRecordsForInvalidTimestamps() {
        internalTopologyBuilder.addSource(null, "source1", null, null, null, topic1);

        final Properties properties = configProps(false);
        properties.setProperty(
            StreamsConfig.DEFAULT_TIMESTAMP_EXTRACTOR_CLASS_CONFIG,
            LogAndSkipOnInvalidTimestamp.class.getName()
        );
        final StreamsConfig config = new StreamsConfig(properties);
        thread = createStreamThread(CLIENT_ID, config);

        thread.setState(StreamThread.State.STARTING);
        thread.setState(StreamThread.State.PARTITIONS_REVOKED);

        final TaskId task1 = new TaskId(0, t1p1.partition());
        final Set<TopicPartition> assignedPartitions = Collections.singleton(t1p1);
        thread.taskManager().handleAssignment(
            Collections.singletonMap(
                task1,
                assignedPartitions),
            emptyMap());

        final MockConsumer<byte[], byte[]> mockConsumer = (MockConsumer<byte[], byte[]>) thread.mainConsumer();
        mockConsumer.assign(Collections.singleton(t1p1));
        mockConsumer.updateBeginningOffsets(Collections.singletonMap(t1p1, 0L));
        thread.rebalanceListener().onPartitionsAssigned(assignedPartitions);
        runOnce();
{code}

If we move `stateUpdater.start();` to `StreamThread::start`, they will hang because they may wait for stateUpdater. I also tried to replace all `thread.setState(StreamThread.State.STARTING);` with `thread.start();` to see if it is an easy fix, but it also breaks many tests. 

Also, the processingThread (TaskExecutor) is created in `StreamThread::create` and then passed to `TaskManager`, and StreamThread will lose its access after the StreamThread::creat call. This could be fixed easily by implementing a start method in TaskManager.
~~~~

7.

~~~~
[~aoli-al] I think a quick fix to get rid of the leaked threads is to shutdown them in the tests by calling {{thread.taskmanager().shutdown()}}.
For the rest, it seems we need to how we start the threads and revisit {{StreamThreadTest}}.
~~~~

8.

~~~~
Hi [~cadonna], I've submitted a patch. Could you please take a look at it when you have time?
~~~~

---

## KAFKA-17148: Kafka storage tool prints MetaPropertiesEnsemble

https://issues.apache.org/jira/browse/KAFKA-17148

Given fix versions: 3.7.2, 3.8.0, 3.9.0
JIRA affects (masked from the system): 3.7.0, 3.7.1, 3.8.0

- `KAFKA-17148@3.7.0`: config 3.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-17148@3.6.2`: config 3.6.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.6, 3.7, 3.8

### Description

~~~~
Using this following command on the 3.6 branch yields this result:
{noformat}
$ bin/kafka-storage.sh format --config config/kraft/server.properties --cluster-id "$(bin/kafka-storage.sh random-uuid)"
Formatting /tmp/kraft-combined-logs with metadata.version 3.6-IV2.{noformat}
While on 3.7 it has this behavior:
{noformat}
$ bin/kafka-storage.sh format --config config/kraft/server.properties --cluster-id "$(bin/kafka-storage.sh random-uuid)"
SLF4J: Class path contains multiple SLF4J bindings.
...
SLF4J: Actual binding is of type [org.slf4j.impl.Reload4jLoggerFactory]
metaPropertiesEnsemble=MetaPropertiesEnsemble(metadataLogDir=Optional.empty, dirs={/tmp/kraft-combined-logs: EMPTY})
Formatting /tmp/kraft-combined-logs with metadata.version 3.7-IV4.
{noformat}
and on 3.8:
{noformat}
$ bin/kafka-storage.sh format --config config/kraft/server.properties --cluster-id "$(bin/kafka-storage.sh random-uuid)"
metaPropertiesEnsemble=MetaPropertiesEnsemble(metadataLogDir=Optional.empty, dirs={/tmp/kraft-combined-logs: EMPTY})
Formatting /tmp/kraft-combined-logs with metadata.version 3.8-IV0.{noformat}
This doesn't appear to be a useful log message for users, so could/should be eliminated.
~~~~

### Comments (1)

1.

~~~~
I verified that this is introduced by [https://github.com/apache/kafka/pull/14628] .
~~~~

---

## KAFKA-17190: AssignmentsManager gets stuck retrying on deleted topics

https://issues.apache.org/jira/browse/KAFKA-17190

Given fix versions: 3.7.2, 3.8.2, 3.9.0
JIRA affects (masked from the system): 3.7.1, 3.8.1

- `KAFKA-17190@3.8.1`: config 3.8.1, metadata answer **affected** (listed_affected)
- `KAFKA-17190@3.7.0`: config 3.7.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.7, 3.8

### Description

~~~~
In MetadataVersion 3.7-IV2 and above, on the broker, AssignmentsManager sends an RPC to the controller informing it about which directory we have chosen to place a replica on. Unfortunately, the code does not check to see if the topic still exists in the MetadataImage before sending the RPC. It will also retry infinitely. Therefore, when a topic is created and deleted in rapid succession, we can get stuck retrying the AssignReplicasToDirsRequest forever.

In order to prevent this problem, the AssignmentsManager should check if a topic still exists (and is still present on the broker in question) before sending the RPC. In order to prevent log spam, we should not log any error messages until several minutes have gone past without success. Finally, rather than creating a new EventQueue event for each assignment request, we should simply modify a shared data structure and schedule a deferred event to send the accumulated RPCs. This will improve efficiency.
~~~~

### Comments (1)

1.

~~~~
This has been backported to 3.7 and 3.8 [https://github.com/apache/kafka/commit/431c00d80241506ea34ea8a00f1b67034956b53d] 

[https://github.com/apache/kafka/commit/0afab4b39317732d4d30db59f1edc560a99fde08] 

Updating the fix versions.
~~~~

---

## KAFKA-17233: MirrorCheckpointConnector should use batched listConsumerGroupOffsets

https://issues.apache.org/jira/browse/KAFKA-17233

Given fix versions: 4.0.0
JIRA affects (masked from the system): 3.5.0

- `KAFKA-17233@3.5.0`: config 3.5.0, metadata answer **affected** (listed_affected)
- `KAFKA-17233@3.4.1`: config 3.4.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.6

### Description

~~~~
The AdminClient provides us a single-group listConsumerGroupOffsets, and a batched listConsumerGroupOffsets. Because we are potentially requesting the offsets for hundreds or thousands of groups, serially requesting all of the offsets may be very slow.
~~~~

### Comments (7)

1.

~~~~
Hello [~gharris1727] 

May I have this issue?

Many thanks 😺
~~~~

2.

~~~~
Hi, [~gharris1727]! I've noticed that [~frankvicky] has done some work on KAFKA-17232. But this issue here remains unassigned. Could I pick it, guys? I've already done some exploration and thought about a solution.
~~~~

3.

~~~~
Based on [Contributing Code Changes|https://cwiki.apache.org/confluence/display/KAFKA/Contributing+Code+Changes], I've checked there is no PR for this issue. Also there no update since July 31, so I assign it to me. Please let me know about if it's a problem, guys
~~~~

4.

~~~~
I am having some trouble to test. When I run the tests on my machine even based on trunk HEAD, some tests fails. How could I distinguish that the problem is not caused by my modifications? [~gharris1727] 

Also CI have appointed a failed test that in fact passed on my local run:

[https://ci-builds.apache.org/job/Kafka/job/kafka-pr/job/PR-17038/1/testReport/junit/org.apache.kafka.connect.integration/OffsetsApiIntegrationTest/Build___JDK_21_and_Scala_2_13___testGetSinkConnectorOffsets__/]

!image-2024-08-31-15-47-14-066.png!

 

Many thanks!
~~~~

5.

~~~~
Another example:

 

I run gradle clean unitTest --console plain > /tmp/unitTestX.txt where X is the number of the run. I have obtained three different results:

 

$ grep ' FAILED' /tmp/unitTest.txt 
Gradle Test Run :clients:unitTest > Gradle Test Executor 624 > AbstractCoordinatorTest > testWakeupAfterSyncGroupReceivedExternalCompletion() FAILED
Gradle Test Run :metadata:unitTest > Gradle Test Executor 697 > QuorumControllerTest > testBootstrapZkMigrationRecord() FAILED
Gradle Test Run :metadata:unitTest > Gradle Test Executor 697 > QuorumControllerTest > testBalancePartitionLeaders() FAILED
Gradle Test Run :metadata:unitTest > Gradle Test Executor 697 > QuorumControllerTest > testBrokerHeartbeatDuringMigration(MetadataVersion) > "testBrokerHeartbeatDuringMigration(MetadataVersion).metadataVersion=3.6-IV1" FAILED
Gradle Test Run :clients:unitTest > Gradle Test Executor 703 > CooperativeConsumerCoordinatorTest > testOutdatedCoordinatorAssignment() FAILED
> Task :metadata:unitTest FAILED
> Task :clients:unitTest FAILED

$ grep ' FAILED' /tmp/unitTest2.txt 
Gradle Test Run :clients:unitTest > Gradle Test Executor 1193 > AbstractCoordinatorTest > testWakeupAfterSyncGroupReceivedExternalCompletion() FAILED
Gradle Test Run :metadata:unitTest > Gradle Test Executor 1160 > QuorumControllerTest > testNoOpRecordWriteAfterTimeout() FAILED
> Task :metadata:unitTest FAILED
> Task :clients:unitTest FAILED

$ grep ' FAILED' /tmp/unitTest3.txt 
Gradle Test Run :metadata:unitTest > Gradle Test Executor 1511 > QuorumControllerTest > testInsertBootstrapRecordsToEmptyLog() FAILED
> Task :metadata:unitTest FAILED
Gradle Test Run :clients:unitTest > Gradle Test Executor 1582 > Tls13SelectorTest > testCloseOldestConnection() FAILED
Gradle Test Run :clients:unitTest > Gradle Test Executor 1611 > KafkaConsumerTest > testMissingOffsetNoResetPolicy(GroupProtocol) > "testMissingOffsetNoResetPolicy(GroupProtocol).groupProtocol=CONSUMER" FAILED
> Task :clients:unitTest FAILED
~~~~

6.

~~~~
https://github.com/apache/kafka/pull/17038
~~~~

7.

~~~~
Hi, [~gharris1727]! I have pushed a fix since your last review, could you check it? Thanks :)
~~~~

---

## KAFKA-17448: New consumer seek should update positions in background thread

https://issues.apache.org/jira/browse/KAFKA-17448

Given fix versions: 4.0.0
JIRA affects (masked from the system): 3.7.0, 3.7.1, 3.8.0

- `KAFKA-17448@3.7.0`: config 3.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-17448@3.6.2`: config 3.6.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
In the new AsyncKafkaConsumer, a call to seek will update the positions in subscription state for the assigned partitions in the app thread ([https://github.com/apache/kafka/blob/c23b6b0365af5c58b76d8ad3fb628f766f95348f/clients/src/main/java/org/apache/kafka/clients/consumer/internals/AsyncKafkaConsumer.java#L796])

This could lead to race conditions like we've seen when subscription state changes in the app thread (over a set of assigned partitions), that could have been modified in the background thread, leading to errors on "No current assignment for partition " [https://github.com/apache/kafka/blob/c23b6b0365af5c58b76d8ad3fb628f766f95348f/clients/src/main/java/org/apache/kafka/clients/consumer/internals/SubscriptionState.java#L378] 

Also, positions update is moved the background with KAFKA-17066 for the same reason, so even if the assignment does not change, we could have a race between the background setting positions to the committed offsets for instance, and the app thread setting them manually via seek. 

To avoid all of the above, we should have seek generate an event, send it to the background, and then update the subscription state when processing that event (similar to other api calls, ex, assign with KAFKA-17064)
~~~~

### Comments (5)

1.

~~~~
Hey [~payang] , this issue is very similar to KAFKA-17064 you just fixed. If you have bandwidth this would probably be very familiar to you already :).
~~~~

2.

~~~~
Hi [~lianetm], thank you. I can handle it. 👍
~~~~

3.

~~~~
Thanks! Let me know if you have questions or when you need help with reviews. 
~~~~

4.

~~~~
[~yangpoan]—sorry for the nag, but can you mark this as Patch Available since the PR is out for review? Thanks!
~~~~

5.

~~~~
Updated the Jira status. Thanks for the reminder.
~~~~

---

## KAFKA-17478: Wrong configuration of metric.reporters lead to NPE in KafkaProducer constructor

https://issues.apache.org/jira/browse/KAFKA-17478

Given fix versions: 4.0.0
JIRA affects (masked from the system): 3.7.0, 3.7.1, 3.8.0

- `KAFKA-17478@3.7.1`: config 3.7.1, metadata answer **affected** (listed_affected)
- `KAFKA-17478@3.6.2`: config 3.6.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
if the metric.reporters property contains some invalid class, the KafkaProducer constructor fails with non explicit NPE:
{code:java}
Exception in thread "main" java.lang.NullPointerException: Cannot invoke "java.util.Optional.ifPresent(java.util.function.Consumer)" because "this.clientTelemetryReporter" is null
    at org.apache.kafka.clients.producer.KafkaProducer.close(KafkaProducer.java:1424)
    at org.apache.kafka.clients.producer.KafkaProducer.<init>(KafkaProducer.java:472)
    at org.apache.kafka.clients.producer.KafkaProducer.<init>(KafkaProducer.java:295)
    at org.apache.kafka.clients.producer.KafkaProducer.<init>(KafkaProducer.java:322)
    at org.apache.kafka.clients.producer.KafkaProducer.<init>(KafkaProducer.java:307)
    at org.frouleau.kafka.clients.Produce.sendAvroSpecific(Produce.java:89)
    at org.frouleau.kafka.clients.Produce.main(Produce.java:63){code}
This behavior was introduced by KAFKA-15901 implementing KIP-714.
~~~~

### Comments (1)

1.

~~~~
The exception is raised by 
List<MetricsReporter> reporters = CommonClientConfigs.metricsReporters(clientId, config);
before the Optional field clientTelemetryReporter is instantiated. The exception handler is calling close() which expect to have clientTelemetryReporter being instantiated.
 
Swapping 2 lines just allow the field not to be null and then to have the proper exception being raised.
~~~~

---

## KAFKA-19054: StreamThread exception handling with SHUTDOWN_APPLICATION may trigger a tight loop with MANY logs

https://issues.apache.org/jira/browse/KAFKA-19054

Given fix versions: 4.0.1, 4.1.0
JIRA affects (masked from the system): 2.8.0

- `KAFKA-19054@2.8.0`: config 2.8.0, metadata answer **affected** (listed_affected)
- `KAFKA-19054@2.7.2`: config 2.7.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
When configured with SHUTDOWN_APPLICATION for uncaught exception handler:

{code:java}
kafkaStreams.setUncaughtExceptionHandler(e -> StreamsUncaughtExceptionHandler.StreamThreadExceptionResponse.SHUTDOWN_APPLICATION);
{code}

The kafka streams application may fall in a tight loop where inside StreamThread#runLoop()

{code:java}
        while (isRunning() || taskManager.rebalanceInProgress()) { //continue to loop because rebalanceInProgress even though the thread is already PENDING_SHUTDOWN
            try {
                checkForTopologyUpdates();
                // If we received the shutdown signal while waiting for a topology to be added, we can
                // stop polling regardless of the rebalance status since we know there are no tasks left
                if (!isRunning() && topologyMetadata.isEmpty()) {
                    log.info("Shutting down thread with empty topology.");
                    break;
                }

                maybeSendShutdown();
                // omitted code, returns very quickly because consumer#poll will return immediately due to it receiving shutdown request
        }
{code}

Inside maybeSendShutdown(), logs are printed to flood the log. We received more than 13k logs in a short period of 50ms. 

Please add logic to avoid the tight loop. Thank you.

~~~~

### Comments (2)

1.

~~~~
Hi [~boquan], If you're not currently working on it, may I take it? Thanks.
~~~~

2.

~~~~
[~apalan60] Hey, please feel free to work on it, thanks!
~~~~

---

## KAFKA-19171: Kafka Streams crashes with UnsupportedOperationException

https://issues.apache.org/jira/browse/KAFKA-19171

Given fix versions: 4.0.1, 4.1.0
JIRA affects (masked from the system): 4.0.0

- `KAFKA-19171@4.0.0`: config 4.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-19171@3.9.2`: config 3.9.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
We observed the following stack trace in our soak cluster
{code:java}
Caused by: java.lang.UnsupportedOperationException
at java.base/java.util.AbstractCollection.add(AbstractCollection.java:251)
at org.apache.kafka.streams.processor.internals.TaskManager.closeTaskClean(TaskManager.java:959)
at org.apache.kafka.streams.processor.internals.TaskManager.handleTasksPendingInitialization(TaskManager.java:517) {code}
Looks like an regression bug: we are passing in an immutable Set.
~~~~

---

## KAFKA-19208: KStream-GlobalKTable join should not drop left-null-key record

https://issues.apache.org/jira/browse/KAFKA-19208

Given fix versions: 4.0.1, 4.1.0
JIRA affects (masked from the system): 3.7.0

- `KAFKA-19208@3.7.0`: config 3.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-19208@3.6.2`: config 3.6.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
We relaxed join null-handling with KIP-962: [https://cwiki.apache.org/confluence/display/KAFKA/KIP-962%3A+Relax+non-null+key+requirement+in+Kafka+Streams]

However, stream-globalTable left-join incorrectly still drop left input record with null-key.
~~~~

---

## KAFKA-19359: [8.8] [CVE-2025-48734] [commons-beanutils] [1.9.4]

https://issues.apache.org/jira/browse/KAFKA-19359

Given fix versions: 3.9.2, 4.0.1, 4.1.0
JIRA affects (masked from the system): 4.0.0

- `KAFKA-19359@4.0.0`: config 4.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-19359@3.9.1`: config 3.9.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.0.0, 2.5, v4.0.0

### Description

~~~~
This security defect has been flagged by *aqua container scan.* Description of security defect is given below :-



*Aqua Description :* Improper Access Control vulnerability in Apache Commons.

A special BeanIntrospector class was added in version 1.9.2. This can be used to stop attackers from using the declared class property of Java enum objects to get access to the classloader. However this protection was not enabled by default. PropertyUtilsBean (and consequently BeanUtilsBean) now disallows declared class level property access by default.

Releases 1.11.0 and 2.0.0-M2 address a potential security issue when accessing enum properties in an uncontrolled way. If an application using Commons BeanUtils passes property paths from an external source directly to the getProperty() method of PropertyUtilsBean, an attacker can access the enum's class loader via the "declaredClass" property available on all Java "enum" objects. Accessing the enum's "declaredClass" allows remote attackers to access the ClassLoader and execute arbitrary code. The same issue exists with PropertyUtilsBean.getNestedProperty().
Starting in versions 1.11.0 and 2.0.0-M2 a special BeanIntrospector suppresses the "declaredClass" property. Note that this new BeanIntrospector is enabled by default, but you can disable it to regain the old behavior; see section 2.5 of the user's guide and the unit tests.

This issue affects Apache Commons BeanUtils 1.x before 1.11.0, and 2.x before 2.0.0-M2.Users of the artifact commons-beanutils:commons-beanutils

1.x are recommended to upgrade to version 1.11.0, which fixes the issue.

Users of the artifact org.apache.commons:commons-beanutils2

2.x are recommended to upgrade to version 2.0.0-M2, which fixes the issue.

*My Review*

I checked this defect is due to commons-validator version 1.9.0 used in kafka v4.0.0.
~~~~

### Comments (4)

1.

~~~~
This defect is flagged due to commons-validator v1.9.0 used in kafka_2.13 v4.0.0 which uses commons-beanutils v1.9.4
~~~~

2.

~~~~
I've requested for a release in `commons-validator` project: [https://github.com/apache/commons-validator/commit/e6c1c3e875a4913577245751c4814177cea758b3] .
~~~~

3.

~~~~
To me, it looks like Kafka is not vulnerable to CVE-2025-48734. In core we depend on commons-validator:1.7 that brings in the vulnerable commons-beanutils:1.9.4. From commons-validator, we only use InetAddressValidator in CoreUtils, which does not use PropertyUtilsBean and BeanUtils classes.
~~~~

4.

~~~~
This PR: [https://github.com/apache/kafka/pull/19939] is to bump the `commons-beanutils` dependency version to 1.11.0 to resolve the CVE. After `commons-validator` has new release, we should remove this `commons-beanutils` version bump workaround in this PR. Closing this ticket.
~~~~

---

## KAFKA-19668: processValues() must be declared as value-changing operation

https://issues.apache.org/jira/browse/KAFKA-19668

Given fix versions: 4.0.1, 4.1.1, 4.2.0
JIRA affects (masked from the system): 3.3.0

- `KAFKA-19668@3.3.0`: config 3.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-19668@3.2.3`: config 3.2.3, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 4.0.0, 4.0.1, 4.1.1, 4.2.0

### Description

~~~~
When adding `KStreams#processValues()` we missed to declare the operation as "value changing". This can lead to an "incorrectly" built topology.

The main problem is, that `processValues()` is the replacement of `transformValues()` which we removed with AK 4.0.0 release. Thus, if users rewrite existing programs from `transformValues()` to the new `processValues()` (what will be required when upgrading to 4.x release), they might observe this change as a regression.

The impact of the changed topology is, that local state is effectively lost, and must be restored from the changelog topic, resulting in downtime after an upgrade.

Note: the bug does only surface, if topology optimization is used, in particular the "merge repartition topics" rewrite.
~~~~

### Comments (2)

1.

~~~~
Do not break backward compatibility, we decided to not enable this fix by default in AK 4.0.1 and 4.1.1 releases, and will do some follow up work for AK 4.2.0 for allow us to enable the fix by default there.
~~~~

2.

~~~~
While we mark this ticket as resolved for AK 4.2.0 release, we also need a follow up for a cleaner fix. Filed https://issues.apache.org/jira/browse/KAFKA-19688 for AK 4.2.0 follow up work.
~~~~

---

## KAFKA-19882: JMX tags applied to all client metrics, not just client state for KIP-1091

https://issues.apache.org/jira/browse/KAFKA-19882

Given fix versions: 4.0.2, 4.1.2, 4.2.0
JIRA affects (masked from the system): 4.0.0

- `KAFKA-19882@4.0.0`: config 4.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-19882@3.9.2`: config 3.9.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
When working on [KIP-1091|https://cwiki.apache.org/confluence/display/KAFKA/KIP-1091%3A+Improved+Kafka+Streams+operator+metrics], we mistakenly applied the `process-id` tag to all client-level metrics, rather than just the `client-state`, `thread-state`, and `recording-level` metrics as specified in the KIP.  This issue came to light while working on KIP-1221, which aimed to add the `application-id` as a tag to the `client-state` metric introduced by KIP-1091.


~~~~

---

## KAFKA-20449: OffsetFetcherUtils.updateSubscriptionState logs at WARN for benign race condition during rebalance

https://issues.apache.org/jira/browse/KAFKA-20449

Given fix versions: 4.3.2, 4.4.0
JIRA affects (masked from the system): 4.1.2, 4.2.1, 4.3.0

- `KAFKA-20449@4.3.0`: config 4.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-20449@4.1.1`: config 4.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
KAFKA-20131 introduced a log.warn() in OffsetFetcherUtils.updateSubscriptionState() for the case where a LIST_OFFSETS response arrives after the partition has already been revoked:

{code:java}
log.warn("Not updating high watermark for partition {} as it is no longer assigned", partition);
{code}

This is a benign race condition that naturally occurs during consumer group rebalances — a LIST_OFFSETS request is issued, the partition gets revoked before the response returns, and the response is simply
discarded. No data loss or correctness issue arises.

However, the WARN level is problematic in practice. Many organizations use warning log rates as a signal for canary release health. Since rebalances are frequent during rolling deployments, canary instances
generate a high volume of these warnings, which triggers automated rollback of otherwise healthy releases.

The log should be downgraded to DEBUG (or at most INFO), since it describes expected, harmless behavior that requires no operator action.

Affected code:

clients/src/main/java/org/apache/kafka/clients/consumer/internals/OffsetFetcherUtils.java, lines 281-285 (introduced in commit abcbef6a4c, PR #21457).

Both log statements are affected:
- "Not updating high watermark for partition {} as it is no longer assigned" (READ_UNCOMMITTED)
- "Not updating last stable offset for partition {} as it is no longer assigned" (READ_COMMITTED)
~~~~

---

## KAFKA-20700: AllowedPaths should resolve symlinks before validating paths against allowed.paths

https://issues.apache.org/jira/browse/KAFKA-20700

Given fix versions: 4.3.2, 4.4.0
JIRA affects (masked from the system): 4.3.0

- `KAFKA-20700@4.3.0`: config 4.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-20700@4.2.1`: config 4.2.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
h2. Problem

`AllowedPaths.parseUntrustedPath()` validates user-supplied paths using lexical `Path.normalize()` only. It does not resolve symbolic links before checking whether a path is under a configured `allowed.paths` base directory.

As a result, if a symlink exists inside an allowed directory (e.g. `/opt/kafka/secrets/link -> /some/other/path`), validation passes because the lexical path appears under the allowed base, but `FileConfigProvider` and `DirectoryConfigProvider` later read the symlink target when accessing the filesystem.

h2. Affected components

* `org.apache.kafka.common.config.internals.AllowedPaths`
* `org.apache.kafka.common.config.provider.FileConfigProvider`
* `org.apache.kafka.common.config.provider.DirectoryConfigProvider`

h2. Example

* `allowed.paths` configured as `/opt/kafka/secrets`
* Symlink present: `/opt/kafka/secrets/test -> /etc/sensitive`
* Config reference: `${file:/opt/kafka/secrets/test:key}`
* Validation allows `/opt/kafka/secrets/test`
* File read follows symlink and accesses `/etc/sensitive`

h2. Current behavior

{code:java}
Path normalisedPath = parsedPath.normalize();
long allowed = allowedPaths.stream().filter(normalisedPath::startsWith).count();
{code}

`normalize()` collapses `.` and `..` but does not resolve symlinks.

h2. Expected behavior

Path validation should use the resolved filesystem path (e.g. `toRealPath()`) so that a symlink inside an allowed directory pointing outside that directory is rejected.

h2. Proposed fix

{code:java}
try {
    Path realPath = parsedPath.toRealPath();
    long allowed = allowedPaths.stream().filter(realPath::startsWith).count();
    if (allowed == 0) {
        return null;
    }
    return realPath;
} catch (IOException e) {
    return null;
}
{code}

Consider also resolving allowed base paths with `toRealPath()` at configuration time for consistent `startsWith` comparisons.

h2. Test coverage

`AllowedPathsTest` covers `..` traversal but has no test for symlink resolution. Add tests for:
* Symlink inside allowed dir pointing outside → rejected
* Symlink inside allowed dir pointing inside → allowed
* Direct path (no symlink) → unchanged behavior

h2. Context

This was reported to the security team. They noted that exploiting this requires write access to the Connect worker filesystem to create symlinks, and therefore do not classify it as a security issue. They agreed the behavior is not intuitive and welcomed a community PR to improve it.

h2. References

* `clients/src/main/java/org/apache/kafka/common/config/internals/AllowedPaths.java`
* `clients/src/test/java/org/apache/kafka/common/config/provider/AllowedPathsTest.java`
* Related hardening: CVE-2024-31141 (`allowed.paths`)
~~~~

---

## KAFKA-20845: Consumer group downgrades can leave group in invalid state when classic group metadata is very large

https://issues.apache.org/jira/browse/KAFKA-20845

Given fix versions: 4.0.3, 4.1.3, 4.2.2, 4.3.2, 4.4.0
JIRA affects (masked from the system): 4.0.2, 4.1.1, 4.2.0, 4.3.0, 4.4.0

- `KAFKA-20845@4.0.2`: config 4.0.2, metadata answer **affected** (listed_affected)
- `KAFKA-20845@4.0.1`: config 4.0.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 4.4.0, 4.5.0

### Description

~~~~
Introduced by KAFKA-19760 while attempting to fix writes for large compressible records.

When downgrading a consumer group, we apply changes to the group coordinator state directly and do not replay the produced records. However, when appending a large but compressible batch, we can allocate an empty batch, then flush, then allocate another empty batch. Flushing an empty batch silently fails the empty batch and rolls back coordinator state. We then write the records for the downgrade, which leaves the in-memory state inconsistent with the state on disk.

After further writes, the state on disk becomes unloadable because the next consumer group records cannot be applied to the classic group.
 # We should not flush an empty batch when appending large batches.
 # We could consider succeeding empty batches instead.

NB: Both succeeding and failing empty batches leads to divergence between in-memory state and disk state when there are write operations that update the state directly without replay.

When succeeding empty batches, a write operation that updates state directly and then fails to serialize its records could leave an empty batch. When the batch is committed, we end up with in-memory changes without corresponding records on disk.

When failing empty batches, a lingering empty batch followed by a write operation that updates state directly and then flushes immediately will have its in-memory changes revert whilst records are written to disk.
~~~~

### Comments (4)

1.

~~~~
We past the code freeze for 4.4.0 now so If you don't think this would make it to 4.4.0 as "bug fix" then we should move this to 4.5.0 
~~~~

2.

~~~~
Moving this to 4.5.0 since we are past the code freeze
~~~~

3.

~~~~
Let's try to ship it in 4.4.0 as this is a nasty bug. [~omnia_h_ibrahim] Could we merge it if we can make it by next week?
~~~~

4.

~~~~
[~dajac] sure I agree this is blocker and should be merged 
~~~~

---

## KAFKA-20893: KafkaStreams incorrectly reports task-offsets (ie state) for non-existing (previously owned) in-memory stores to the task assignor

https://issues.apache.org/jira/browse/KAFKA-20893

Given fix versions: 4.3.2, 4.4.0
JIRA affects (masked from the system): 4.3.0

- `KAFKA-20893@4.3.0`: config 4.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-20893@4.2.1`: config 4.2.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 4.4

### Description

~~~~
KIP-1035 replaced the local state directory .checkpoint files with persistent state store internal offset tracking, plus an in-memory offsets cache inside StateDirectory. However, the cache is incorrectly populated with in-memory store offsets, while it should only contain persistent store offsets (cf [https://github.com/apache/kafka/commit/5740a26525a27df9eacd847a6d4ed6eb23fda0dc] which replaces `ProcessorStateManger#checkpoint()` which contains a check `storeMetadata.stateStore.persistent()` with new code lacking such a check).

After a task (with an in-memory) store is closed (and the in-memory state is gone), these offset are still in the in-memory cache, and might get reported to the task-assignor during a rebalance, which the task assignor would interpret as "existing local state", even if there is none. This may leads to incorrect task placement decisions.

The bug can only hit if a task has both an in-memory store and persistent store, so by itself it should hit not too frequently, as most apps either have all in-memory or all persistent stores (even if `suppress()` which is only available in-memory elevate the problem).

However, with the recent changes via KIP-1071 (not release yet), this bug will be elevated and thus it should be fixed before AK 4.4 gets released, by ensuring that in-memory offsets are never added to the cache in the first place.
~~~~

---
