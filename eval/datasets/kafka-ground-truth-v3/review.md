# kafka-ground-truth-v3: labeling review

The fix versions are GIVEN (the system sees them). For each case, decide whether
the text below plus the given fix versions say enough to conclude the metadata
answer for that config version: for `affected`, that the bug exists at or before
the config and isn't fixed by it; for `not_affected` (`before_affected`), that the
bug did not exist yet at the config ("introduced in", "works on"). "Seen on
3.6.0" alone says nothing about 3.5.2.

Record `yes` or `no` in the `answerable_from_text` column of labels.csv, with a short
note when it's borderline.

## KAFKA-1531: zookeeper.connection.timeout.ms is set to 10000000 in configuration file in Kafka tarball

https://issues.apache.org/jira/browse/KAFKA-1531

Given fix versions: 0.8.2.0
JIRA affects (masked from the system): 0.8.0, 0.8.1.1

- `KAFKA-1531@0.8.1.1`: config 0.8.1.1, metadata answer **affected** (listed_affected)
- `KAFKA-1531@0.7.2`: config 0.7.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
I've noticed that Kafka tarball comes with zookeeper.connection.timeout.ms=1000000 in server.properties while https://kafka.apache.org/08/documentation.html says the default is 6000. This setting was introduced in configuration file in 46b6144a, so quite a long time ago (3 years), which makes it look intentional, but as per Jun Rao's comment on IRC, 6000 sounds more reasonable, so that entry should probably be changed or removed from config at all.
~~~~

### Comments (12)

1.

~~~~
Can I submit a patch by setting all the occurrences of zookeeper.connection.timeout.ms to 6000?
~~~~

2.

~~~~
Yes, I think so. Thanks,
~~~~

3.

~~~~
Created reviewboard https://reviews.apache.org/r/23396/diff/
 against branch origin/trunk
~~~~

4.

~~~~
[~junrao] [~omkreddy] If it's a default value, should we set it in config at all? My idea would be rather to remove that line completely.
~~~~

5.

~~~~
Agreed, I think we should only specify required configs and other configs that we do need to override the default in those config property files.
~~~~

6.

~~~~
I feel some of the important tunable parameters can be part of config files with default values. 

The following tunable properties are currently available in server.properties config file. 

num.network.threads=2 
num.io.threads=8

socket.send.buffer.bytes=1048576
socket.receive.buffer.bytes=1048576
socket.request.max.bytes=104857600
num.partitions=2

log.retention.hours=168
log.segment.bytes=536870912
log.retention.check.interval.ms=60000
log.cleaner.enable=false

All the above properties have some defined default value. 
Some of the above property values are different from the default values
given in documentation.

Can we clean some of the above properties also?

~~~~

7.

~~~~
Yes, it would be good to clean those up too. We can just set all those values with the defaults.
~~~~

8.

~~~~
Created reviewboard https://reviews.apache.org/r/23417/diff/
 against branch origin/trunk
~~~~

9.

~~~~
The following properties  updated in server.properties.  

zookeeper.connection.timeout.ms=6000
num.network.threads=3
num.partitions=1
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=65536
log.segment.bytes=1073741824
log.retention.check.interval.ms=300000

~~~~

10.

~~~~
Thanks for the patch. Do you want to include the changes you made in the previous RB?
~~~~

11.

~~~~
Previous patch I tried to update all the conf files across all the folders config, various test_suite etc..

Latest patch contains changes related to config/server.properties and config/consumer.properties only. 
I think latest changes are sufficient for preparing kafka tar release.
~~~~

12.

~~~~
Thanks for the patch. Committed the 2nd RB to trunk.
~~~~

---

## KAFKA-2146: adding partition did not find the correct startIndex 

https://issues.apache.org/jira/browse/KAFKA-2146

Given fix versions: 0.10.0.0
JIRA affects (masked from the system): 0.8.2.0

- `KAFKA-2146@0.8.2.0`: config 0.8.2.0, metadata answer **affected** (listed_affected)
- `KAFKA-2146@0.8.1.1`: config 0.8.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
TopicCommand provide a tool to add partitions for existing topics. It try to find the startIndex from existing partitions. There's a minor flaw in this process, it try to use the first partition fetched from zookeeper as the start partition, and use the first replica id in this partition as the startIndex.

One thing, the first partition fetched from zookeeper is not necessary to be the start partition. As partition id begin from zero, we should use partition with id zero as the start partition.

The other, broker id does not necessary begin from 0, so the startIndex is not necessary to be the first replica id in the start partition. 

  
~~~~

### Comments (8)

1.

~~~~
I'd like to provide a patch soon.
~~~~

2.

~~~~
use partition 0 as head partition;
find the index of first replica of head partition in sortedBrokerList and use it as startIndex

~~~~

3.

~~~~
[~chenshangan521@163.com] Thanks for the patch, and sorry for the late review.

I agree with you on #1, but for #2 there is a case when some brokers are temporarily not available, while the existing replica list is set statically. So 

<code>
brokerList.indexOf(existingReplicaList.head)
<code>

may return -1 in this case, causing a random pick of the starting index. In this case, we should probably pick the next available broker as the starting broker, i.e. if now the available broker list is (1,2,5) and the replica list of partition 0 is 3, we should pick broker-5 as starting broker.

Also for #1, I think for better replica distribution we should pick the starting index as the first replica of the LAST partition's list plus one. That is, if we already have three partitions with replica list:

1, 2, 3
2, 3, 4
3, 4, 5

Then if we add another partition, its starting broker should be 4 given if all (1,2,3,4,5) brokers are available; or should be 5 if only (1,2,3,5) are available

Another minor comment: not introduced in this patch, but the name of "existingReplicaList" was originally misleading, we could rename it to "existingReplicaListForLastPartition" or "existingReplicaListForPartitionZero" with your current patch.

2. 
~~~~

4.

~~~~
[~guozhang] It's ok.

For #2 I totally agree, it's better to pick the next available broker than pick a random one.

But for #1, I think we do not need to process as function #assignReplicasToBrokers will help us to deal with it as following

{code}
val firstReplicaIndex = (currentPartitionId + startIndex) % brokerList.size
{code}

And starting index has its own definition in function #assignReplicasToBrokers, if you use the LAST partition, you need to change the logic of this function, and this modification will gain nothing.

If we get agreed, I will update the patch.

I have another task KAFKA-2106, I think it's a big headache for users of kafka. My current solution is a workaround, but not well distributed , hope for some comment on that.  




~~~~

5.

~~~~
Yeah I agree, could you update the patch?
~~~~

6.

~~~~
updated patch.
~~~~

7.

~~~~
[~chenshangan521@163.com] your updated patch seems not apply cleanly on trunk, could you rebase?
~~~~

8.

~~~~
Issue resolved by pull request 329
[https://github.com/apache/kafka/pull/329]
~~~~

---

## KAFKA-2189: Snappy compression of message batches less efficient in 0.8.2.1

https://issues.apache.org/jira/browse/KAFKA-2189

Given fix versions: 0.8.2.2, 0.9.0.0
JIRA affects (masked from the system): 0.8.2.1

- `KAFKA-2189@0.8.2.1`: config 0.8.2.1, metadata answer **affected** (listed_affected)
- `KAFKA-2189@0.8.2.0`: config 0.8.2.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 0.8.2.1, 0.8.1.1, 0.8.2.2, 0.8.2, 0.8.2.0

### Description

~~~~
We are using snappy compression and noticed a fairly substantial increase (about 2.25x) in log filesystem space consumption after upgrading a Kafka cluster from 0.8.1.1 to 0.8.2.1. We found that this is caused by messages being seemingly recompressed individually (or possibly with a much smaller buffer or dictionary?) instead of as a batch as sent by producers. We eventually tracked down the change in compression ratio/scope to this [1] commit that updated the snappy version from 1.0.5 to 1.1.1.3. The Kafka client version does not appear to be relevant as we can reproduce this with both the 0.8.1.1 and 0.8.2.1 Producer.

Here are the log files from our troubleshooting that contain the same set of 1000 messages, for batch sizes of 1, 10, 100, and 1000. f9d9b was the last commit with 0.8.1.1-like behavior prior to f5ab8 introducing the issue.

{noformat}
-rw-rw-r-- 1 kafka kafka 404967 May 12 11:45 /var/kafka2/f9d9b-batch-1-0/00000000000000000000.log
-rw-rw-r-- 1 kafka kafka 119951 May 12 11:45 /var/kafka2/f9d9b-batch-10-0/00000000000000000000.log
-rw-rw-r-- 1 kafka kafka  89645 May 12 11:45 /var/kafka2/f9d9b-batch-100-0/00000000000000000000.log
-rw-rw-r-- 1 kafka kafka  88279 May 12 11:45 /var/kafka2/f9d9b-batch-1000-0/00000000000000000000.log

-rw-rw-r-- 1 kafka kafka 402837 May 12 11:41 /var/kafka2/f5ab8-batch-1-0/00000000000000000000.log
-rw-rw-r-- 1 kafka kafka 382437 May 12 11:41 /var/kafka2/f5ab8-batch-10-0/00000000000000000000.log
-rw-rw-r-- 1 kafka kafka 364791 May 12 11:41 /var/kafka2/f5ab8-batch-100-0/00000000000000000000.log
-rw-rw-r-- 1 kafka kafka 380693 May 12 11:41 /var/kafka2/f5ab8-batch-1000-0/00000000000000000000.log
{noformat}

[1] https://github.com/apache/kafka/commit/f5ab8e1780cf80f267906e3259ad4f9278c32d28 
~~~~

### Comments (11)

1.

~~~~
I have verified that the issue [1] was introduced in snappy-java 1.1.1.2 and has already been fixed [2], in snappy-java 1.1.1.7.

[1] https://github.com/xerial/snappy-java/issues/100
[2] https://github.com/xerial/snappy-java/commit/dc2dd27f85e5167961883f71ac2681b73b33e5df
~~~~

2.

~~~~
Created reviewboard https://reviews.apache.org/r/34144/diff/
 against branch upstream/trunk
~~~~

3.

~~~~
Everything looks good so far in our development environment, the log file sizes were returned back to the 0.8.1.1 baseline when we replaced 1.1.1.6 with 1.1.1.7 in the broker libs. Producer/broker performance was the same or in some cases better.

Should be moving this change into production within the next couple of days to free up some disk space, will update again once we have been running 1.1.1.7 in prod for a few days.
~~~~

4.

~~~~
We've been running with snappy-java 1.1.1.7 in production for four days now with no issues.
~~~~

5.

~~~~
Given the positive feedback, it seems like it would be good to get this merged so that more people can test it before the final release?
~~~~

6.

~~~~
Thanks for the patch. +1 and committed to trunk.
~~~~

7.

~~~~
Hi all,

The Wikimedia Foundation had a serious production issue when we upgraded to 0.8.2.1 because of this bug.  Snappy compression doesn't work at scale in 0.8.2.1.  I know 0.8.3 is slated for release soon, maybe you should consider doing a 0.8.2.2 release just to get this out there in a stable tag, so that others don't run into this issue.

~~~~

8.

~~~~
Hi all,
I was wondering if this affects only 0.8.2.1 or also 0.8.2? We are on 0.8.2 and just did a complete rebalance across our brokers and some brokers are at 70% disk utilization and some are at 30%. Thanks.
~~~~

9.

~~~~
0.8.2.0 has the same problem since it depends on snappy-java 1.1.1.6.
~~~~

10.

~~~~
quick question, I assume there should be no issues with upgrading brokers and/or producers/consumers independently with this change?  E.g. can snappy 1.1.1.6 and 1.1.1.7 interoperate without any compatibility issues?
~~~~

11.

~~~~
[~jbrosenberg@gmail.com] Yes your assumption is correct, this was only an efficiency/chunking issue and not any protocol incompatibility.
~~~~

---

## KAFKA-2551: Unclean leader election docs outdated

https://issues.apache.org/jira/browse/KAFKA-2551

Given fix versions: 0.10.0.0
JIRA affects (masked from the system): 0.8.2.2

- `KAFKA-2551@0.8.2.2`: config 0.8.2.2, metadata answer **affected** (listed_affected)
- `KAFKA-2551@0.8.2.1`: config 0.8.2.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 0.8.2.0

### Description

~~~~
Current unclean leader election docs state:
{quote}
In the future, we would like to make this configurable to better support use cases where downtime is preferable to inconsistency.
{quote}

Since 0.8.2.0, unclean leader election strategy (whether to allow it or not) is already configurable via {{unclean.leader.election.enable}} broker config property.

That sentence is in both https://svn.apache.org/repos/asf/kafka/site/083/design.html and https://svn.apache.org/repos/asf/kafka/site/082/design.html near the end of "Unclean leader election: What if they all die?" section. Next section, "Availability and Durability Guarantees", mentions ability to disable unclean leader election, so likely just this one reference needs to be updated.
~~~~

### Comments (2)

1.

~~~~
yes I agree with you;
currently we can configure via unclean.leader.election.enable;

for this parameter, I did an experiment:
I have 2 brokers(broker0 and broker1) and 1 topic named "p1r2" with 1 partition and 2 replicas;
firstly, I use default unclean.leader.election.enable=true; at this moment log size=1000;
then I shutdown broker1, and use console producer to send messages into kafka queue, tail log size=1009;
then I shutdown broker0, and restart broker1, found log size=1000, but the leader changed to be broker1;
but when I want to send messages to kafka(at this moment, only broker1 alive), I got exception as below:


[2015-09-21 17:06:06,654] ERROR fetching topic metadata for topics [Set(p1r2)] from broker [ArrayBuffer(id:0,host:soho-pipe-kafka-test1-test,port:9092, id:1,host:soho-pipe-kafka-test2-test:9092,port:9092)] failed (kafka.utils.Utils$)
kafka.common.KafkaException: fetching topic metadata for topics [Set(p1r2)] from broker [ArrayBuffer(id:0,host:soho-pipe-kafka-test1-test,port:9092, id:1,host:soho-pipe-kafka-test2-test:9092,port:9092)] failed
	at kafka.client.ClientUtils$.fetchTopicMetadata(ClientUtils.scala:72)
	at kafka.producer.BrokerPartitionInfo.updateInfo(BrokerPartitionInfo.scala:82)
	at kafka.producer.async.DefaultEventHandler$$anonfun$handle$2.apply$mcV$sp(DefaultEventHandler.scala:78)
	at kafka.utils.Utils$.swallow(Utils.scala:172)
	at kafka.utils.Logging$class.swallowError(Logging.scala:106)
	at kafka.utils.Utils$.swallowError(Utils.scala:45)
	at kafka.producer.async.DefaultEventHandler.handle(DefaultEventHandler.scala:78)
	at kafka.producer.async.ProducerSendThread.tryToHandle(ProducerSendThread.scala:105)
	at kafka.producer.async.ProducerSendThread$$anonfun$processEvents$3.apply(ProducerSendThread.scala:88)
	at kafka.producer.async.ProducerSendThread$$anonfun$processEvents$3.apply(ProducerSendThread.scala:68)
	at scala.collection.immutable.Stream.foreach(Stream.scala:547)
	at kafka.producer.async.ProducerSendThread.processEvents(ProducerSendThread.scala:67)
	at kafka.producer.async.ProducerSendThread.run(ProducerSendThread.scala:45)
Caused by: java.nio.channels.ClosedChannelException
	at kafka.network.BlockingChannel.send(BlockingChannel.scala:100)
	at kafka.producer.SyncProducer.liftedTree1$1(SyncProducer.scala:73)
	at kafka.producer.SyncProducer.kafka$producer$SyncProducer$$doSend(SyncProducer.scala:72)
	at kafka.producer.SyncProducer.send(SyncProducer.scala:113)
	at kafka.client.ClientUtils$.fetchTopicMetadata(ClientUtils.scala:58)
	... 12 more
[2015-09-21 17:06:06,655] ERROR Failed to send requests for topics p1r2 with correlation ids in [17,24] (kafka.producer.async.DefaultEventHandler)
[2015-09-21 17:06:06,655] ERROR Error in handling batch of 1 events (kafka.producer.async.ProducerSendThread)
kafka.common.FailedToSendMessageException: Failed to send messages after 3 tries.
	at kafka.producer.async.DefaultEventHandler.handle(DefaultEventHandler.scala:90)
	at kafka.producer.async.ProducerSendThread.tryToHandle(ProducerSendThread.scala:105)
	at kafka.producer.async.ProducerSendThread$$anonfun$processEvents$3.apply(ProducerSendThread.scala:88)
	at kafka.producer.async.ProducerSendThread$$anonfun$processEvents$3.apply(ProducerSendThread.scala:68)
	at scala.collection.immutable.Stream.foreach(Stream.scala:547)
	at kafka.producer.async.ProducerSendThread.processEvents(ProducerSendThread.scala:67)
	at kafka.producer.async.ProducerSendThread.run(ProducerSendThread.scala:45)
with unclean.leader.election.enable, I was expecting that I can still send messages to broker1, even though I lost messages on broker0;
Am I wrong?
~~~~

2.

~~~~
GitHub user omkreddy opened a pull request:

    https://github.com/apache/kafka/pull/1054
~~~~

---

## KAFKA-3590: KafkaConsumer fails with "Messages are rejected since there are fewer in-sync replicas than required." when polling

https://issues.apache.org/jira/browse/KAFKA-3590

Given fix versions: 0.10.1.0, 0.10.2.0
JIRA affects (masked from the system): 0.9.0.1

- `KAFKA-3590@0.9.0.1`: config 0.9.0.1, metadata answer **affected** (listed_affected)
- `KAFKA-3590@0.9.0.0`: config 0.9.0.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 0.9.0.1

### Description

~~~~
KafkaConsumer.poll() fails with "Messages are rejected since there are fewer in-sync replicas than required.". Isn't this message about minimum number of ISR's when *sending* messages?

Stacktrace:
org.apache.kafka.common.KafkaException: Unexpected error from SyncGroup: Messages are rejected since there are fewer in-sync replicas than required.
        at org.apache.kafka.clients.consumer.internals.AbstractCoordinator$SyncGroupRequestHandler.handle(AbstractCoordinator.java:444) ~[kafka-clients-0.9.0.1.jar:na]
        at org.apache.kafka.clients.consumer.internals.AbstractCoordinator$SyncGroupRequestHandler.handle(AbstractCoordinator.java:411) ~[kafka-clients-0.9.0.1.jar:na]
        at org.apache.kafka.clients.consumer.internals.AbstractCoordinator$CoordinatorResponseHandler.onSuccess(AbstractCoordinator.java:665) ~[kafka-clients-0.9.0.1.jar:na]
        at org.apache.kafka.clients.consumer.internals.AbstractCoordinator$CoordinatorResponseHandler.onSuccess(AbstractCoordinator.java:644) ~[kafka-clients-0.9.0.1.jar:na]
        at org.apache.kafka.clients.consumer.internals.RequestFuture$1.onSuccess(RequestFuture.java:167) ~[kafka-clients-0.9.0.1.jar:na]
        at org.apache.kafka.clients.consumer.internals.RequestFuture.fireSuccess(RequestFuture.java:133) ~[kafka-clients-0.9.0.1.jar:na]
        at org.apache.kafka.clients.consumer.internals.RequestFuture.complete(RequestFuture.java:107) ~[kafka-clients-0.9.0.1.jar:na]
        at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient$RequestFutureCompletionHandler.onComplete(ConsumerNetworkClient.java:380) ~[kafka-clients-0.9.0.1.jar:na]
        at org.apache.kafka.clients.NetworkClient.poll(NetworkClient.java:274) ~[kafka-clients-0.9.0.1.jar:na]
        at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.clientPoll(ConsumerNetworkClient.java:320) ~[kafka-clients-0.9.0.1.jar:na]
        at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:213) ~[kafka-clients-0.9.0.1.jar:na]
        at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:193) ~[kafka-clients-0.9.0.1.jar:na]
        at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:163) ~[kafka-clients-0.9.0.1.jar:na]
        at org.apache.kafka.clients.consumer.internals.AbstractCoordinator.ensureActiveGroup(AbstractCoordinator.java:222) ~[kafka-clients-0.9.0.1.jar:na]
        at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.ensurePartitionAssignment(ConsumerCoordinator.java:311) ~[kafka-clients-0.9.0.1.jar:na]
        at org.apache.kafka.clients.consumer.KafkaConsumer.pollOnce(KafkaConsumer.java:890) ~[kafka-clients-0.9.0.1.jar:na]
        at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:853) ~[kafka-clients-0.9.0.1.jar:na]
~~~~

### Comments (5)

1.

~~~~
[~salaev] it looks like this is occurring in a SyncGroup call so it's probably due to the fact that the new consumer needs to write to the __consumer_offsets topic and can't because __consumer_offsets isn't meeting the min ISR requirements for the cluster.  The error message isn't very clear, so maybe we can start by improving that.  I can take a shot at the pull request in the next couple of days.
~~~~

2.

~~~~
This looks similar to KAFKA-3766, Jason suggests a different solution there.
~~~~

3.

~~~~
Thanks [~ijuma], I didn't see that one.  Updated the PR to move toward Jason's recommendation.
~~~~

4.

~~~~
[~hachikuji] is going to take this one over for now.
~~~~

5.

~~~~
Issue resolved by pull request 1859
[https://github.com/apache/kafka/pull/1859]
~~~~

---

## KAFKA-3919: Broker faills to start after ungraceful shutdown due to non-monotonically incrementing offsets in logs

https://issues.apache.org/jira/browse/KAFKA-3919

Given fix versions: 0.11.0.0
JIRA affects (masked from the system): 0.9.0.1

- `KAFKA-3919@0.9.0.1`: config 0.9.0.1, metadata answer **affected** (listed_affected)
- `KAFKA-3919@0.9.0.0`: config 0.9.0.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 0.11

### Description

~~~~
Hi All,

I encountered an issue with Kafka following a power outage that saw a proportion of our cluster disappear. When the power came back on several brokers halted on start up with the error:

{noformat}
	Fatal error during KafkaServerStartable startup. Prepare to shutdown”
	kafka.common.InvalidOffsetException: Attempt to append an offset (1239742691) to position 35728 no larger than the last offset appended (1239742822) to /data3/kafka/mt_xp_its_music_main_itsevent-20/00000000001239444214.index.
	at kafka.log.OffsetIndex$$anonfun$append$1.apply$mcV$sp(OffsetIndex.scala:207)
	at kafka.log.OffsetIndex$$anonfun$append$1.apply(OffsetIndex.scala:197)
	at kafka.log.OffsetIndex$$anonfun$append$1.apply(OffsetIndex.scala:197)
	at kafka.utils.CoreUtils$.inLock(CoreUtils.scala:262)
	at kafka.log.OffsetIndex.append(OffsetIndex.scala:197)
	at kafka.log.LogSegment.recover(LogSegment.scala:188)
	at kafka.log.Log$$anonfun$loadSegments$4.apply(Log.scala:188)
	at kafka.log.Log$$anonfun$loadSegments$4.apply(Log.scala:160)
	at scala.collection.TraversableLike$WithFilter$$anonfun$foreach$1.apply(TraversableLike.scala:772)
	at scala.collection.IndexedSeqOptimized$class.foreach(IndexedSeqOptimized.scala:33)
	at scala.collection.mutable.ArrayOps$ofRef.foreach(ArrayOps.scala:108)
	at scala.collection.TraversableLike$WithFilter.foreach(TraversableLike.scala:771)
	at kafka.log.Log.loadSegments(Log.scala:160)
	at kafka.log.Log.<init>(Log.scala:90)
	at kafka.log.LogManager$$anonfun$loadLogs$2$$anonfun$3$$anonfun$apply$10$$anonfun$apply$1.apply$mcV$sp(LogManager.scala:150)
	at kafka.utils.CoreUtils$$anon$1.run(CoreUtils.scala:60)
	at java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:511)
	at java.util.concurrent.FutureTask.run(FutureTask.java:266)
	at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1142)
	at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:617)
	at java.lang.Thread.run(Thread.java:745)
{noformat}

The only way to recover the brokers was to delete the log files that contained non monotonically incrementing offsets.

We've spent some time digging through the logs and I feel I may have worked out the sequence of events leading to this issue, (though this is based on some assumptions I've made about the way Kafka is working, which may be wrong).

First off, we have unclean leadership elections disable. (We did later enable them to help get around some other issues we were having, but this was several hours after this issue manifested), and we're producing to the topic with gzip compression and acks=1

We looked through the data logs that were causing the brokers to not start. What we found the initial part of the log has monotonically increasing offset, where each compressed batch normally contained one or two records. Then the is a batch that contains many records, whose first records have an offset below the previous batch and whose last record has an offset above the previous batch. Following on from this there continues a period of large batches, with monotonically increasing offsets, and then the log returns to batches with one or two records.

Our working assumption here is that the period before the offset dip, with the small batches, is pre-outage normal operation. The period of larger batches is from just after the outage, where producers have a back log to processes when the partition becomes available, and then things return to normal batch sizes again once the back log clears.

We did also look through the Kafka's application logs to try and piece together the series of events leading up to this. Here’s what we know happened, with regards to one partition that has issues, from the logs:

Prior to outage:
* Replicas for the partition are brokers 2011, 2012,  2024, with 2024 being the preferred leader.
* Producers using acks=1, compression=gzip
* Brokers configured with unclean.elections=false, zk.session-timeout=36s

Post outage:
* 2011 comes up first, (also as the Controller), recovers unflushed log segment 1239444214, completes load with offset 1239740602, and becomes leader of the partition.
* 2012 comes up next, recovers its log,  recovers unflushed log segment 1239444214, truncates to offset 1239742830, (thats 2,228 records ahead of the recovered offset of the current leader), and starts following.
* 2024 comes up quickly after 2012.  recovers unflushed log segment 1239444214, truncates to offset  1239742250, (thats 1,648 records ahead of the recovered offset of the current leader), and starts following.
* The Controller adds 2024 to the replica set just before 2024 halts due to another partition having an offset greater than the leader.
* The Controller adds 2012 to the replica set just before 2012 halts due to another partition having an offset greater than the leader.
* When 2012 is next restarted, it fails to fully start as its complaining of invalid offsets in the log.

You’ll notice that the offset the brokers truncate to are different for each of the three brokers. 

We're assuming that when the 2012 starts up and follows the leader it request records from its truncated offsets, but that the logs have diverged on these two brokers to the point that the requested offset corresponds within the leader's log to the middle of a compressed record set, not at a record set boundary.  The leader then returns the whole compressed set, which the follower appends to its log - unknowingly introducing a dip in its otherwise monotonically incrementing offsets.

Several of our brokers were unlucky enough to have this dip at the 4K boundary used by the offset indexer, causing a protracted outage.  We’ve written a little utility that shows several more brokers have a dip outside of the 4K boundary.

There are some assumptions in there, which I’ve not got around to confirming / denying. (A quick attempt to recreate this failed and I've not found the time to invest more).

Of course I'd really appreciate the community / experts stepping in and commenting on whether our assumptions are right or wrong, or if there is another explanation to the problem. 

Obviously, the fact the broker got into this state and then won’t start is obviously a bug, and one I’d like to fix.  A Kafka broker should not corrupt its own log during normal operation to the point that it can’t restart! :D

A secondary issue is if we think the divergent logs are acceptable? This may be deemed acceptable given the producers have chosen availability over consistency when they produced with acks = 1?  Though personally, the system having diverging replicas of an immutable commit log just doesn't sit right.

I see us having a few options here:
* Have the replicas detect the divergence of their logs e.g. a follower compares the checksum of its last record with the same offset on the leader. The follower can then workout that its log has diverged from the leader.  At which point it could either halt, stop replicating that partition or search backwards to find the point of divergence, truncate and recover. (possibly saving the truncated part somewhere). This would be a protocol change for Kafka.  This solution trades availability, (you’ve got less ISRs during the extended re-sync process), for consistency.
* Leave the logs as they are and have the indexing of offsets in the log on start up handle such a situation gracefully.  This leaves logs in a divergent state between replicas, (meaning replays would yield different messages if the leader was up to down), but gives better availability, (no time spent not being an ISR while it repairs any divergence).
* Support multiple options and allow it be tuned, ideally by topic.
* Something else...


I’m happy/keen to contribute here. But I’d like to first discuss which option should be investigated.

Andy
~~~~

### Comments (18)

1.

~~~~
Thanks for the report. Did you mean to file both this and KAFKA-3918 (which looks very similar)?
~~~~

2.

~~~~
[~BigAndy], thanks for reporting and investigating this. It seems that somehow messages with out of order offsets leaked into the broker log, which prevented the broker to restart. First, a few things about how replication works.

1. At the high level, we try to make replicas byte-wise identical. Each replica always checkpoints the last committed offsets to a local file. On restarting, the replica will truncate its local log to the last committed offset before fetching from the leader. So, in this case, the leader can be a few messages ahead of the follower. But those messages won't be committed and will be truncated if the leader becomes the follower.

2. Compressed messages are always appended to the log atomically in both the leader and the follower. So, during replication, in theory, it shouldn't be possible for a follower to request an offset that's in the middle of a compressed message set.

3. The only case that we allow the replicas to diverge a bit is when unclean leader election is enabled. Suppose that a non-in-sync replica becomes the leader and has messages from offset 0 to 100. It then committed new messages from 101 to 200. Now, another previous in-sync replica may come back with a last committed offset at 150 (which is larger than the last offset when the leader is started). This replica will only get messages from 151 to 200 from the new leader. It thinks it already has messages from 101 to 150, but those are actually different from the new leader's data. The divergence won't be forever though.

So, I am not sure if your hypothesis can indeed happen. It would be useful to dig deeper on this. Do you still have the log segment files? If so, could you use our DumpLogSegments tool to see the layout of the offsets? Also, did you have unclean.leader.election disabled? When the new leader becomes the follower, it will log the offset that it truncates to during startup. Could you dig that out too?
~~~~

3.

~~~~
[~ijuma] - duplicate submission not intentional, (Jira timed out on first submission). Closed as duplicate
[~junrao] - Yep, I did check app-logs for truncation points and data-logs to see what the offsets were doing. I'll get back to you shortly with details.
~~~~

4.

~~~~
Hi [~junrao], thanks for taking the time to look at this.

First off, we have unclean leadership elections disable. (We did later enable them to help get around some other issues we were having, but this was several hours after this issue manifested).

We did look through data logs that were causing the brokers to not start. What we found before the incident was a monotonically increasing offset, where each compressed batch normally contained one or two records. Then the is a batch that contains many records, whose first records has an offset below the previous batch and whose last record has an offset above the previous batch. Following on from this there continues a period of large batches, with monotonically increasing offsets, and then the log returns to batches with one or two records.

Our working assumption here is that the period before the offset dip is pre-outage normal operation. The period of larger batches is from just after the outage, where producers have a back log to processes when the partition becomes available, and then things return to normal batch sizes again once the back log clears.

We did also look through the Kafka's application logs to try and piece together the series of events leading up to this:

Here’s what I know happened, with regards to one partition that has issues, from the logs:

Prior to outage:
Replicas for the partition are brokers 2011, 2012,  2024, with 2024 being the preferred leader.
Producers using acks=1, compression=gzip
Brokers configured with unclean.elections=false, zk.session-timeout=36s

Post outage:
2011 comes up first, (also as the Controller), recovers unflushed log segment 1239444214, completes load with offset 1239740602, and becomes leader of the partition.
2012 comes up next, recovers its log,  recovers unflushed log segment 1239444214, truncates to offset 1239742830, (thats 2,228 records ahead of the recovered offset of the current leader), and starts following.
2024 comes up quickly after 2012.  recovers unflushed log segment 1239444214, truncates to offset  1239742250, (thats 1,648 records ahead of the recovered offset of the current leader), and starts following.
The Controller adds 2024 to the replica set just before 2024 halts due to another partition having an offset greater than the leader.
The Controller adds 2012 to the replica set just before 2012 halts due to another partition having an offset greater than the leader.
When 2012 is next restarted, it fails to fully start as its complaining of invalid offsets in the log.

You’ll notice that the offset the brokers truncate to are different for each of the three brokers. 

Given that I can write to the partition with only one broker available, and that I can then take this broker down and bring up a different one from the replica set and write to that one, how does Kafka currently look to reconcile these different histories when the first node is brought back online?  I know that if the first node has a greater offset it will halt when it tries to follow the second, but what happens if the first node has a lower offset?

Maybe the above scenario is correctly handled and I’m off down a tangent! (I’d appreciate any info to improve my understanding of Kafka and help me figure out what is happening here.). I’m just trying to reconcile the data I’m seeing in the logs and your response to my post.

I’m going to extract the pertinent entries from our app logs, obfuscate and add them in here.

(I’ll also add some of that I’ve written here to the description above for the benefit of anyone new to the ticket)

Thanks,

Andy
~~~~

5.

~~~~
[~BigAndy], thanks for the investigation and the additional information.

Let me first explain how log reconciliation normal works. Each broker maintains the last committed offset for each partition and stores that information in a checkpoint file replication-offset-checkpoint. A message is only considered committed if it's received by all in-sync replicas. The leader advances the last committed offset and propagates it to the followers. So, the follower's last committed offset is always <= the leader's. When a replica becomes a leader, it won't do any truncation to its log and will instead try to commit all messages in its local log. When a replica becomes a follower, it will first truncate its log to the last committed offset stored in its local checkpoint file and then start replicating from that offset. If unclean leader election is disabled, after truncation, the follower's last offset should always be <= the leader's last offset.

Another thing we do is that if a broker is shut down forcefully, on startup, we will do log recovery to remove any corrupted messages. In your case, it seems what happens is that when the new leader (2011) comes up, its log is actually corrupted and therefore it has to truncate some messages. This potentially will remove messages that have been previously committed. Then, when broker 2012 comes up and becomes the follower. It's possible that after the follower truncates its log to its local last committed offset, that offset is actually larger than the last recovered offset in the leader. If no new messages have been appended to the new leader, the follower will realize that its offset is out of range and will truncate its log again to the leader's last offset. However, in this case, it seems some new messages have been published to the new leader and the follower's offset is actually in range. It's just that the follower's offset may now point to a completely new set of messages. In this case if the follower's offset points to the middle of a compressed message set, the follower will get the whole compressed message set and append it to its local log. Currently, in the follower, will only ensure that the last offset in a compressed message set be larger than the last offset in the log, but not the first offset. This seems to be the situation that you are in.

There is still one thing not very clear to me. When building indexes during log recovery, we actually only add index entries at the boundary of compressed message set. So as long as the last offset of each compressed set keeps increasing, we won't hit the InvalidOffsetException in the description. Could you check whether 1239742691 is the last offset of a compressed set and if so whether there is a case that the last offset of a compressed set is out of order in the log?
~~~~

6.

~~~~
[~junrao] My understanding was that the offset index looks at the offset of the first record in the compressed set, not the last.  Having checked the code this does seem to be the case. (Code below from LogSegment.scala, recover()):

{code}
val startOffset =
            entry.message.compressionCodec match {
              case NoCompressionCodec =>
                entry.offset
              case _ =>
                ByteBufferMessageSet.deepIterator(entry.message).next().offset
          }
{code}
~~~~

7.

~~~~
[~BigAndy], yes, you are right. We actually do index based on the first offset in a compressed messageSet during recovery. So, the hypothesis can indeed happen. It seems that you lost multiple brokers in a hard way at the same time, was that due to a power outage?

To fix this properly, we probably want to fix KAFKA-1211. This is a bit involved since we need to keep track of the leader generations in the log. However, if we can do that, if the same situation occurs when a follower wants to fetch from an offset that has been overwritten with new messages in the leader, the follower would know those messages are from a newer generation of the leader and will truncate its local log to a correct offset.

Another thing that's a bit weird right now is that in the leader, we index based on the first offset in a compressed message set. But in the follower, we index based on the last offset in a compressed message set. This is mostly to avoid decompression on the follower side since we only store the last offset in the wrapper message. Indexing either first offset or last offset is semantically correct, but it would be good to make this consistent. Next time when we evolve the message format, we probably want to consider adding the first offset in the wrapper message.
~~~~

8.

~~~~
[~junrao] Yes, we lost a good number of brokers in a power outage.

The solution you're proposing in KAFKA-1211 looks fairly involved, i.e. a protocol change, is this something you think I can pick up, (having never committed to Kafka, but no newbie to distributed programming), or something I'd be best of leaving to the committers? (I'm conscious that its been sat as a known issue for a long time, and internally this is viewed as a blocker...)


~~~~

9.

~~~~
[~BigAndy], yes, the fix could be involved and we haven't nailed down a detailed design yet. Zookeeper has to deal with a similar issue. Let me discuss this with [~fpj] a bit. Once we are comfortable with a design, we can see if you want to pick it up or not.
~~~~

10.

~~~~
[~junrao]  Good stuff. Look forward to hearing from you and getting involved more =)
~~~~

11.

~~~~
We experienced a similar incident again recently. This time the cluster was destabilised when there was intermittent connectivity issues with ZK for a few minutes. This resulted in a quick succession of Controller elections and changes, and ISR shrinks and grows.  During the ISR shrinks and grows some brokers seem to have got themselves into the same inconsistent state as above and halted. To recover the brokers we needed to manually delete the corrupted log segments.

So it looks like the above issue is not related, or not just related, to ungraceful shutdown. This inconsistent state appears to be possible during ISR changes where producers are producing with acks=1. Though obviously the ZK connectivity issues will likely have played a role.

~~~~

12.

~~~~
Thanks [~BigAndy]. It's worth noting that the discussion moved to KAFKA-1211 after Jun's last comment above. I'll leave it to Jun to comment on whether the KAFKA-1211 fix being discussed is also relevant for the most recent incident that did not involve an ungraceful shutdown.
~~~~

13.

~~~~
Thanks [~ijuma]. Given that the problems I'm experiencing are purely related to messages produced with acks=1 and KAFKA-2111 speaks explicitly about acks>1, I'd be interested if [~junrao] thinks that 2111 does indeed fix this issue too, given this new information on the problem.

Thanks all!
~~~~

14.

~~~~
[~BigAndy], the error trace in the description of the jira only happens when the broker does log recovery due to ungraceful shutdown. So, it seems some ungraceful shutdown had occurred. Now, assuming there was no data loss during ungraceful shutdown, I am not sure frequent leader election or ISR changes themselves can lead to the reported issue.

If there was data loss due to ungraceful shutdown, this issue can happen regardless of whether the producer uses ack = 1 or all. KAFKA-1211 in general fixes a data loss issue when the leader changes too frequently, but also addresses this particular issue. We have made a more concrete proposal in KAFKA-1211 for a fix. Perhaps you can see if it makes sense to you and/or whether you'd be able to help out on the fix.
~~~~

15.

~~~~
This is fixed by KAFKA-1211. Closing the jira.
~~~~

16.

~~~~
I made an analysis of this problem specifically:
https://objcoding.com/2020/03/14/kafka-invalid-offset-exception/
~~~~

17.

~~~~
[~zhangchenghui]: Appreciate the detailed analysis. I noticed that the magic in the message format is 1, which is quite old. The latest message format with magic 2 has been introduced since 0.11 and is probably what most people are using now. So, I'd recommend that you try the new message format. If you still see an issue, let us know (So far, we haven't seen a similar issue reported on the new message format).
~~~~

18.

~~~~
Hi, [~junrao]
When the Kafka partition is unavailable and the leader copy is damaged, I try to minimize data loss by doing the following:
1. Partition reallocation of unavailable partitions;
2. Modify zk node: / brokers / topics / test-topic / partitions / 0 / state
3.Restart the broker
When a partition is unavailable, can I provide an option for users to manually set any copy in the partition as the leader?
Because once the cluster has set unclean.leader.election.enable = false, it is not possible to elect a copy other than ISR as the leader. In extreme cases, only the leader copy is still in the ISR. At this time, the broker where the leader is located is down. What if the broker data is corrupted? In this case, is it possible for the user to choose the leader replica himself? Although this will also result in data loss, the situation will be much better than data loss for the entire partition.
This is my summary：
https://mp.weixin.qq.com/s/b1etPGC97xNjmgdQbycnSg
~~~~

---

## KAFKA-3996: ByteBufferMessageSet.writeTo() should be non-blocking

https://issues.apache.org/jira/browse/KAFKA-3996

Given fix versions: 0.10.0.1
JIRA affects (masked from the system): 0.10.0.0

- `KAFKA-3996@0.10.0.0`: config 0.10.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-3996@0.9.0.1`: config 0.9.0.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 0.8, 0.10.0

### Description

~~~~
Currently, in ByteBufferMessageSet.writeTo(), we try to finish writing all bytes in the buffer in a single call. The code has been like that since 0.8. This hasn't been a problem historically since the broker uses zero-copy to send fetch responses and only use ByteBufferMessageSet to send produce responses, which are small. However, in 0.10.0, if a consumer is before 0.10.0, the broker has to down convert the message and use ByteBufferMessageSet to send a fetch response to the consumer. If the client is slow and there are lots of bytes in the ByteBufferMessageSet, we may not be able to completely send all the bytes in the buffer for a long period of time. When this happens, the Processor will be blocked and can't handle other connections, which is bad.
~~~~

### Comments (2)

1.

~~~~
To address this issue, we will need to get rid of the while loop and return the bytes returned from channel.write(buffer) similar to what's in ByteBufferSend.
~~~~

2.

~~~~
Issue resolved by pull request 1669
[https://github.com/apache/kafka/pull/1669]
~~~~

---

## KAFKA-4374: Improve Response Errors Logging

https://issues.apache.org/jira/browse/KAFKA-4374

Given fix versions: 3.9.0
JIRA affects (masked from the system): 0.10.0.1

- `KAFKA-4374@0.10.0.1`: config 0.10.0.1, metadata answer **affected** (listed_affected)
- `KAFKA-4374@0.10.0.0`: config 0.10.0.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
When NetworkClient.java gets a response error, it runs:
{code}
            if (response.errors().size() > 0) {
                log.warn("Error while fetching metadata with correlation id {} : {}", header.correlationId(), response.errors());
            }
{code}

Logging that at warn level and saying there is an error, is confusing to new people. They don't see it was a warn and not error level. They just see that it says "Error while...".

Maybe it should be something like "The metadata response from the cluster reported a recoverable issue..."
~~~~

---

## KAFKA-4698: `-target:jvm-1.7` in scalaCompileOptions seems to cause java.lang.VerifyError when loading kafka/client/ClientUtils 

https://issues.apache.org/jira/browse/KAFKA-4698

Given fix versions: 0.10.2.0
JIRA affects (masked from the system): 0.10.1.1

- `KAFKA-4698@0.10.1.1`: config 0.10.1.1, metadata answer **affected** (listed_affected)
- `KAFKA-4698@0.10.1.0`: config 0.10.1.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 0.10.1.1, 0.8.2.2, 0.10.1.2, 0.10.1, 0.10.2.0

### Description

~~~~
When we updated to kafka 2.11-0.10.1.1 from 2.11-0.8.2.2 we started getting the following error 

{noformat}
java.lang.VerifyError: Stack map does not match the one at exception handler 190
Exception Details:
  Location:
    kafka/client/ClientUtils$.fetchTopicMetadata(Lscala/collection/Set;Lscala/collection/Seq;Lkafka/producer/ProducerConfig;I)Lkafka/api/TopicMetadataResponse; @190: astore
  Reason:
    Type top (current frame, locals[12]) is not assignable to 'kafka/producer/SyncProducer' (stack map, locals[12])
  Current Frame:
    bci: @63
    flags: { }
    locals: { 'kafka/client/ClientUtils$', 'scala/collection/Set', 'scala/collection/Seq', 'kafka/producer/ProducerConfig', integer, integer, 'scala/runtime/IntRef', 'kafka/api/TopicMetadataRequest', 'kafka/api/TopicMetadataResponse', 'java/lang/Throwable', 'scala/collection/Seq', 'kafka/producer/SyncProducer' }
    stack: { 'java/lang/Throwable' }
  Stackmap Frame:
    bci: @190
    flags: { }
    locals: { 'kafka/client/ClientUtils$', 'scala/collection/Set', 'scala/collection/Seq', 'kafka/producer/ProducerConfig', integer, integer, 'scala/runtime/IntRef', 'kafka/api/TopicMetadataRequest', 'kafka/api/TopicMetadataResponse', 'java/lang/Throwable', 'scala/collection/Seq', top, 'kafka/producer/SyncProducer' }
    stack: { 'java/lang/Throwable' }
  Bytecode:
    0x0000000: 0336 0503 b800 aa3a 06bb 00ac 59b2 00b1
    0x0000010: b600 b515 042d b600 ba2b b900 c001 00b7
    0x0000020: 00c3 3a07 013a 0801 3a09 b200 c82c b200
    0x0000030: cdb6 00d1 b600 d5c0 00d7 3a0a a700 353a
    0x0000040: 0b2a bb00 0b59 2b15 0419 0619 0ab7 00de
    0x0000050: bb00 0d59 190b b700 e1b6 00e3 190b 3a09
    0x0000060: 1906 1906 b400 e704 60b5 00e7 190c b600
    0x0000070: ea19 06b4 00e7 190a b900 ee01 00a2 0057
    0x0000080: 1505 9a00 52b2 00f3 2d19 0a19 06b4 00e7
    0x0000090: b900 f702 00c0 00f9 b600 fd3a 0c2a bb00
    0x00000a0: 0f59 2b15 0419 0619 0ab7 00fe b601 0019
    0x00000b0: 0c19 07b6 0104 3a08 0436 05a7 ffa5 3a0d
    0x00000c0: 1906 1906 b400 e704 60b5 00e7 190c b600
    0x00000d0: ea19 0dbf 1505 9900 122a bb00 1159 2bb7
    0x00000e0: 0107 b601 0919 08b0 bb01 0b59 bb01 0d59
    0x00000f0: b201 1213 0114 b601 18b7 011a b201 1205
    0x0000100: bd00 0459 032b 5359 0419 0a53 b601 1eb6
    0x0000110: 0122 1909 b701 25bf                    
  Exception Handler Table:
    bci [175, 190] => handler: 63
    bci [175, 190] => handler: 190
    bci [63, 96] => handler: 190
  Stackmap Table:
    full_frame(@63,{Object[#2],Object[#188],Object[#215],Object[#183],Integer,Integer,Object[#166],Object[#172],Object[#217],Object[#72],Object[#215],Object[#219]},{Object[#72]})
    full_frame(@96,{Object[#2],Object[#188],Object[#215],Object[#183],Integer,Integer,Object[#166],Object[#172],Object[#217],Object[#72],Object[#215],Top,Object[#219]},{})
    chop_frame(@113,2)
    full_frame(@190,{Object[#2],Object[#188],Object[#215],Object[#183],Integer,Integer,Object[#166],Object[#172],Object[#217],Object[#72],Object[#215],Top,Object[#219]},{Object[#72]})
    chop_frame(@212,2)
    same_frame(@232)
 
	at kafka.consumer.ConsumerFetcherManager$LeaderFinderThread.doWork(ConsumerFetcherManager.scala:65)
	at kafka.utils.ShutdownableThread.run(ShutdownableThread.scala:63)
{noformat}

Which looks like it's coming from the change in https://issues.apache.org/jira/browse/KAFKA-3375.  The suggested fix was to rebuild the 0.10.1.1 jar without

{code}
"-target:jvm-${sourceCompatibility}".toString(),
{code}

in the `scalaCompileOptions.additionalParameters`.

Once we made this change and rebuilt the jar the VerifyError stopped happening.

The complete diff of the change we used is

{noformat}
diff --git a/build.gradle b/build.gradle
index fded48e05..857144d62 100644
--- a/build.gradle
+++ b/build.gradle
@@ -250,7 +250,6 @@ subprojects {
       "-deprecation",
       "-unchecked",
       "-encoding", "utf8",
-      "-target:jvm-${sourceCompatibility}".toString(),
       "-Xlog-reflective-calls",
       "-feature",
       "-language:postfixOps",
{noformat}

cc: [~ijuma] [~sriharsha]
~~~~

### Comments (4)

1.

~~~~
Issue resolved by pull request 2434
[https://github.com/apache/kafka/pull/2434]
~~~~

2.

~~~~
[~ijuma] [~hachikuji] - any chance we can get this into 0.10.1.2 (if that's going to be a release) as a bugfix / hotfix?
~~~~

3.

~~~~
[~nickt], we can cherry-pick this into the 0.10.1 branch, but 0.10.2.0 will be out before 0.10.1.2. The former should be out in February while there is currently no date for 0.10.1.2.
~~~~

4.

~~~~
On second thought, I am not sure if we can backport this to 0.10.1.2. We'd have to make sure that it doesn't cause binary compatibility issues.
~~~~

---

## KAFKA-5037: Infinite loop if all input topics are unknown at startup

https://issues.apache.org/jira/browse/KAFKA-5037

Given fix versions: 2.1.0
JIRA affects (masked from the system): 0.10.2.0

- `KAFKA-5037@0.10.2.0`: config 0.10.2.0, metadata answer **affected** (listed_affected)
- `KAFKA-5037@0.10.1.1`: config 0.10.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 0.11, 1.0.0, 1.1, 2.0

### Description

~~~~
See discusion: https://github.com/apache/kafka/pull/2815

We will need some rewrite on {{StreamPartitionsAssignor}} and to add much more test for all kind of corner cases, including pattern subscriptions.
~~~~

### Comments (14)

1.

~~~~
A similar issue got reported here: http://search-hadoop.com/m/Kafka/uyzND14MkzKYvKSh2?subj=Kafka+Streams+Application+does+not+start+after+10+1+to+10+2+update+if+topics+need+to+be+auto+created
~~~~

2.

~~~~
[~mjsax] is this still for 0.11?
~~~~

3.

~~~~
Ping [~mjsax]: do we target this for 1.0.0?
~~~~

4.

~~~~
Ping – any update on this?
~~~~

5.

~~~~
Hey Michael, we have not yet started working on this. Did you see more and more people complaining about it?
~~~~

6.

~~~~
I'm now grouping these three tickets: 5037, 6587 and 6437 into a single general issue, and here is my summary of it:

1. If there is a repartition topic whose num.partitions is dependent on the corresponding sub-topology's input topic, and that input topic does not exist in {{metadata}}, then it will be assigned as {{NOT_AVAILABLE}} and the corresponding topic will not be created, and any tasks that needs it as input topics will be silently dropped (see {{DefaultPartitionGrouper#maxNumPartitions}}). This is reported as in KAFKA-6437.

1.1. If we happen to pass the while loop because of the {{NOT_AVAILABLE}} tag, we may still hit the issue in {{CopartitionedTopicsValidator#validate}} that will cause runtime exception being thrown.

2. If there is a repartition topic whose num.partitions is dependent on the corresponding sub-topology's input topic, and that input topic is also a repartition topic with num.partition as {{NOT_AVAILABLE}}, then there is a bug that will cause the while loop to never finish. This is reported as in KAFKA-5037 and the PR 2815 contains the fix of it already.

3. Before 1.1, we have another while loop inside {{prepareTopic}}. If the metadata cannot be fetched then we will also fall into a blocking scenario. This is more related to KAFKA-6587 and should have been fixed automatically now.

{code}
            // wait until each one of the topic metadata has been propagated to at least one broker
            while (!allTopicsCreated(topicNamesToMakeReady, topicsToMakeReady)) {
                try {
                    Thread.sleep(50L);
                } catch (InterruptedException e) {
                    // ignore
                }
            }
{code}
~~~~

7.

~~~~
If we want to only fix-forward this issue beyond 2.0. I'd propose the following to refactor the {{StreamsPartitionAssignor#assign()}} function as follows. The principle is that, unlike consumer who would assign partial available topics to members hoping that when the metadata gets refreshed again another rebalance is triggered to complete the full subscription, in Streams we would not start at all if not all the requested source topics are available. This is a simpler rule and easier for users to reason: in the past the most complaints are that "I need to be notified when this happens, but I still see application in RUNNING, and was not aware we are actually only executing partial topology".

1. At the beginning of {{assign}}, we first check that all the non-repartition source topics are included in the {{metadata}}. If not, we log an error at the leader and set an error in the Assignment userData bytes, indicating that leader cannot complete assignment and the error code would indicate the root cause of it.

2. Upon receiving the assignment, if the error is not NONE the streams will shutdown itself with a log entry re-stating the root cause interpreted from the error code.

3. With 1) / 2) above, the non repartition source topics should always been available, and hence we should never encounter the `NOT_AVAILABLE` case for num.partitions of those repartition topics, we will remove `NOT_AVAILABLE` from the possible values, and remove the corresponding logic in DefaultPartitionGrouper for `NOT_AVAILABLE`.

Note that 1) above requires us to bump up the version for assignment userData again, which should be fine with version probing added in 2.0. There is an alternative walkaround, to use negative version numbers as the error codes, and as long as clients knows how to interpret them that is fine. Personally I felt it is a bit hacky and would suggest we just bump up the version.

WDYT?
~~~~

8.

~~~~
I'm adding the tag `newbie++` for anyone wanting to pick it up. Note the proposed solution is targeted to fix all three JIRAs: 5037, 6587, 6437.
~~~~

9.

~~~~
Originally I threw exception in the if block for the following line in {{assign}}:
{code}
                                        if (numPartitionsCandidate == null) {
{code}
In patch v2, I construct assignment map. See if this is close to what you propose.
~~~~

10.

~~~~
Currently both SubscriptionInfo.LATEST_SUPPORTED_VERSION and AssignmentInfo.LATEST_SUPPORTED_VERSION are 3.
There may be some intricacy w.r.t. {{minReceivedMetadataVersion}} which is initialized to SubscriptionInfo.LATEST_SUPPORTED_VERSION.
With my patch, I see:
{code}
org.apache.kafka.streams.processor.internals.StreamsPartitionAssignorTest > shouldReturnUnchangedAssignmentForOldInstancesAndEmptyAssignmentForFutureInstances FAILED
    java.lang.AssertionError:
    Expected: <[version=4, supported version=4, active tasks=[0_0, 0_1], standby tasks={0_2=[topic1-2]}, global assignment={}]>
         but: was <[version=3, supported version=4, active tasks=[0_0, 0_1], standby tasks={0_2=[topic1-2]}, global assignment={}]>
        at org.hamcrest.MatcherAssert.assertThat(MatcherAssert.java:20)
        at org.junit.Assert.assertThat(Assert.java:956)
        at org.junit.Assert.assertThat(Assert.java:923)
        at org.apache.kafka.streams.processor.internals.StreamsPartitionAssignorTest.                                                                                           shouldReturnUnchangedAssignmentForOldInstancesAndEmptyAssignmentForFutureInstances(StreamsPartitionAssignorTest.java:1280)
{code}
~~~~

11.

~~~~
Patch v4 rewrites assertions in shouldReturnUnchangedAssignmentForOldInstancesAndEmptyAssignmentForFutureInstances so that the test passes.
~~~~

12.

~~~~
In KafkaStreams, I am adding the following method in order to detect state transition of StreamThread:
{code}
    /**
     * An app can set a single {@link StreamThread.StateListener} so that the app is notified when state changes.
     *
     * @param listener a new StreamThread state listener
     * @throws IllegalStateException if this {@code KafkaStreams} instance is not in state {@link State#CREATED CREATED}.
     */
    public void setStreamThreadStateListener(StreamThread.StateListener listener) {
{code}
Let me know whether a KIP is needed.
~~~~

13.

~~~~
Since {{StreamThread}} is an internal class, adding any public functions on that class should not require a KIP.
~~~~

14.

~~~~
Issue resolved by pull request 5322
[https://github.com/apache/kafka/pull/5322]
~~~~

---

## KAFKA-5061: client.id should be set for Connect producers/consumers

https://issues.apache.org/jira/browse/KAFKA-5061

Given fix versions: 2.3.0
JIRA affects (masked from the system): 0.10.2.1

- `KAFKA-5061@0.10.2.1`: config 0.10.2.1, metadata answer **affected** (listed_affected)
- `KAFKA-5061@0.10.2.0`: config 0.10.2.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
In order to properly monitor individual tasks using the producer and consumer metrics, we need to have the framework disambiguate them. Currently when we create producers (https://github.com/apache/kafka/blob/trunk/connect/runtime/src/main/java/org/apache/kafka/connect/runtime/Worker.java#L362) and create consumers (https://github.com/apache/kafka/blob/trunk/connect/runtime/src/main/java/org/apache/kafka/connect/runtime/WorkerSinkTask.java#L371-L394) the client ID is not being set. You can override it for the entire worker via worker-level producer/consumer overrides, but you can't get per-task metrics.

There are a couple of things we might want to consider doing here:
1. Provide default client IDs based on the worker group ID + task ID (providing uniqueness for multiple connect clusters up to the scope of the Kafka cluster they are operating on). This seems ideal since it's a good default; however it is a public-facing change and may need a KIP. Normally I would be less worried about this, but some folks may be relying on picking up metrics without this being set, in which case such a change would break their monitoring.
2. Allow overriding client.id on a per-connector basis. I'm not sure if this will really be useful or not -- it lets you differentiate between metrics for different connectors' tasks, but within a connector, all metrics would go to a single client.id. On the other hand, this makes the tasks act as a single group from the perspective of broker handling of client IDs.
~~~~

### Comments (13)

1.

~~~~
[~ewencp] So you are suggesting to add client.id per task level in this, if user has not supplied any cient.id?
And also provide option to user ti define client.id per connector basis
~~~~

2.

~~~~
[~ewencp] , I would like to work on this issue.
Will keep you posted with progress/updates.
~~~~

3.

~~~~
I'd be happy with the default you mentioned Ewen. Would really help monitoring
~~~~

4.

~~~~
Hmm, not sure I did suggest a default? There are at least two options there and unfortunately there is a tradeoff in:

a) uniquely identifying the clients in metrics
b) enforcing quotas

For (a), connect is relatively unusual in that many applications using Kafka won't need more than one producer/consumer per process and metrics name conflicts aren't an issue for global per-process registries like JMX; Connect, however, has common cases where using just the task name for the client ID could cause conflicts since it will be common to have 2 tasks from the same connector running in the same worker process. (Note that KIP-196 is adding per-task metrics, some of which might replace the need for the lower-level producer/consumer metrics, so some of these arguments may not be as critical; however, that info is still useful for debugging, so not ideal if just lost).

For (b), the tradeoff depends a lot on whether you are working with a secured cluster (i.e. whether your quotas can include your auth principal or if you're working only with client.id), and of course, whether you even care about quotas in your environment. If you're only working with client.id, then using the full task ID isn't great since you probably want to apply quoatas to the logical group of all tasks for a given connector (i.e. in that case you really want to define client.id == connector ID). And of course, I can also imagine just wanting to apply quotas across the entire Connect cluster, in which case you want your client IDs == Connect cluster ID.

Finally, I think there is also an issue wrt allowing some sort of prefix/custom formatting on top of the basic task ID -- if you're running multiple connect clusters, you may need to be able to differentiate their tasks. This probably relates to KAFKA-4028 and might mean just having a sane default template but letting the user override it would be the option that provides the most flexibility (assuming we think that flexibility is really needed). And of course, such a config would need a KIP as it would be new user-facing API.

So I'm not sure what the right answer here is exactly -- I can see a number of use cases with different requirements, but I'm not sure which ones people will be trying to use in practice and would prefer to keep things less complicated if possible.
~~~~

5.

~~~~
This bug became an urgent issue at Salesforce as we needed full task-level monitoring in production for Mirus (our open source Kafka Source Connector).  As a work-around we created a patch, to meet our specific needs, which has been running successfully in production since March. I would really like to see this bug resolved, so I have submitted a Pull Request ([https://github.com/apache/kafka/pull/5775]) with our battle-tested patch.

The change is similar to the one Satyajit submitted, but instead of using a default based on group id, it appends the task id to the client id when a “unique.client.id” property is set to true (false by default). This allows us to control the client id independent of the group id, so we can use a custom prefix on our producer client ids.  This is useful for monitoring. 

[~ewencp] this may not address all your concerns, but it certainly solved an urgent issue for us in a real-world use case.  Let me know where the gaps are and I will try to help to find a general solution. If the new Worker property in the PR requires a KIP then let me know and I can help create one.  There are no unit tests at present, but I am happy to add those if the change looks otherwise OK.
~~~~

6.

~~~~
I updated PR [https://github.com/apache/kafka/pull/5775] to resolve some conflicts that appeared after recent changes in trunk.  How should I go about getting this change reviewed (and hopefully merged)? [~ewencp] - is this something you can help with?
~~~~

7.

~~~~
[~pdavidson] I had a quick look at the PR and it appears that we are introducing a new configuration to handle this. We would probably require a small KIP since its a public facing change. 
~~~~

8.

~~~~
Thanks for the response [~mageshn] - I will create a KIP.
~~~~

9.

~~~~
I have created [KIP-411: Add option to make Kafka Connect task client ID values unique|https://cwiki.apache.org/confluence/display/KAFKA/KIP-411%3A+Add+option+to+make+Kafka+Connect+task+client+ID+values+unique] 

FYI [~mageshn]

 

 
 
~~~~

10.

~~~~
I have created a alternative PR after comments from [~ewencp] and [~kkonstantine] on KIP-411. This PR simply changes the default client id and avoids creating any new configuration options.  See https://github.com/apache/kafka/pull/6097
~~~~

11.

~~~~
[~pdavidson]: as seen in the previous comment from the bot, I've closed your first PR that introduced a new config option. You've already submitted the second PR and changed KIP-411 to reflect it, so I'm assuming you're okay with this.
~~~~

12.

~~~~
https://github.com/apache/kafka/pull/3952 was an earlier attempt (prior to creation of KIP-411) at solving this problem, and it too introduced a new configuration. Closed that PR without merging, in favor of https://github.com/apache/kafka/pull/6097
~~~~

13.

~~~~
Voting is now underway on [KIP-411|https://cwiki.apache.org/confluence/display/KAFKA/KIP-411%3A+Make+default+Kafka+Connect+worker+task+client+IDs+distinct].  Please vote if you would like this bug resolved! 
~~~~

---

## KAFKA-5413: Log cleaner fails due to large offset in segment file

https://issues.apache.org/jira/browse/KAFKA-5413

Given fix versions: 0.10.2.2, 0.11.0.0
JIRA affects (masked from the system): 0.10.2.0, 0.10.2.1

- `KAFKA-5413@0.10.2.1`: config 0.10.2.1, metadata answer **affected** (listed_affected)
- `KAFKA-5413@0.10.1.1`: config 0.10.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 0.11.0, 0.10.2, 0.9, 0.9.0, 0.10.2.2, 0.11.0.2, 0.10, 0.11

### Description

~~~~
The log cleaner thread in our brokers is failing with the trace below

{noformat}
[2017-06-08 15:49:54,822] INFO {kafka-log-cleaner-thread-0} Cleaner 0: Cleaning segment 0 in log __consumer_offsets-12 (largest timestamp Thu Jun 08 15:48:59 PDT 2017) into 0, retaining deletes. (kafka.log.LogCleaner)
[2017-06-08 15:49:54,822] INFO {kafka-log-cleaner-thread-0} Cleaner 0: Cleaning segment 2147343575 in log __consumer_offsets-12 (largest timestamp Thu Jun 08 15:49:06 PDT 2017) into 0, retaining deletes. (kafka.log.LogCleaner)
[2017-06-08 15:49:54,834] ERROR {kafka-log-cleaner-thread-0} [kafka-log-cleaner-thread-0], Error due to  (kafka.log.LogCleaner)
java.lang.IllegalArgumentException: requirement failed: largest offset in message set can not be safely converted to relative offset.
        at scala.Predef$.require(Predef.scala:224)
        at kafka.log.LogSegment.append(LogSegment.scala:109)
        at kafka.log.Cleaner.cleanInto(LogCleaner.scala:478)
        at kafka.log.Cleaner$$anonfun$cleanSegments$1.apply(LogCleaner.scala:405)
        at kafka.log.Cleaner$$anonfun$cleanSegments$1.apply(LogCleaner.scala:401)
        at scala.collection.immutable.List.foreach(List.scala:381)
        at kafka.log.Cleaner.cleanSegments(LogCleaner.scala:401)
        at kafka.log.Cleaner$$anonfun$clean$4.apply(LogCleaner.scala:363)
        at kafka.log.Cleaner$$anonfun$clean$4.apply(LogCleaner.scala:362)
        at scala.collection.immutable.List.foreach(List.scala:381)
        at kafka.log.Cleaner.clean(LogCleaner.scala:362)
        at kafka.log.LogCleaner$CleanerThread.cleanOrSleep(LogCleaner.scala:241)
        at kafka.log.LogCleaner$CleanerThread.doWork(LogCleaner.scala:220)
        at kafka.utils.ShutdownableThread.run(ShutdownableThread.scala:63)
[2017-06-08 15:49:54,835] INFO {kafka-log-cleaner-thread-0} [kafka-log-cleaner-thread-0], Stopped  (kafka.log.LogCleaner)
{noformat}

This seems to point at the specific line [here| https://github.com/apache/kafka/blob/0.11.0/core/src/main/scala/kafka/log/LogSegment.scala#L92] in the kafka src where the difference is actually larger than MAXINT as both baseOffset and offset are of type long. It was introduced in this [pr| https://github.com/apache/kafka/pull/2210/files/56d1f8196b77a47b176b7bbd1e4220a3be827631]

These were the outputs of dumping the first two log segments

{noformat}
:~$ /usr/bin/kafka-run-class kafka.tools.DumpLogSegments --deep-iteration --files /kafka-logs/__consumer_offsets-12/000
00000000000000000.log
Dumping /kafka-logs/__consumer_offsets-12/00000000000000000000.log
Starting offset: 0
offset: 1810054758 position: 0 NoTimestampType: -1 isvalid: true payloadsize: -1 magic: 0 compresscodec: NONE crc: 3127861909 keysize: 34

:~$ /usr/bin/kafka-run-class kafka.tools.DumpLogSegments --deep-iteration --files /kafka-logs/__consumer_offsets-12/000
00000002147343575.log
Dumping /kafka-logs/__consumer_offsets-12/00000000002147343575.log
Starting offset: 2147343575
offset: 2147539884 position: 0 NoTimestampType: -1 isvalid: true paylo
adsize: -1 magic: 0 compresscodec: NONE crc: 2282192097 keysize: 34
{noformat}

My guess is that since 2147539884 is larger than MAXINT, we are hitting this exception. Was there a specific reason, this check was added in 0.10.2?

E.g. if the first offset is a key = "key 0" and then we have MAXINT + 1 of "key 1" following, wouldn't we run into this situation whenever the log cleaner runs?
~~~~

### Comments (28)

1.

~~~~
More details (I'm investigating the same issue in the same company): the problem seems to be exactly what is described in [this comment on the PR|https://github.com/apache/kafka/pull/2210/files/56d1f8196b77a47b176b7bbd1e4220a3be827631#r91192806].

Debugger output:
{code}
kafka-log-cleaner-thread-0[7] where
  [7] kafka.log.Cleaner.cleanSegments (LogCleaner.scala:401)
  [8] kafka.log.Cleaner$$anonfun$clean$4.apply (LogCleaner.scala:363)
  [9] kafka.log.Cleaner$$anonfun$clean$4.apply (LogCleaner.scala:362)
  [10] scala.collection.immutable.List.foreach (List.scala:381)
  [11] kafka.log.Cleaner.clean (LogCleaner.scala:362)
  [12] kafka.log.LogCleaner$CleanerThread.cleanOrSleep (LogCleaner.scala:241)
  [13] kafka.log.LogCleaner$CleanerThread.doWork (LogCleaner.scala:220)
  [14] kafka.utils.ShutdownableThread.run (ShutdownableThread.scala:63)
kafka-log-cleaner-thread-0[7] print segments
 segments = "List(LogSegment(baseOffset=0, size=18527), LogSegment(baseOffset=2147343575, size=60))"
{code}
~~~~

2.

~~~~
cc [~junrao]
~~~~

3.

~~~~
[~ny2ko], [~Federico Giraud], thanks for the reporting this issue. In LogCleaner.groupSegmentsBySize(), we try to groups segments with the following check.
   segs.head.index.lastOffset - group.last.index.baseOffset <= Int.MaxValue

The intention is that if 2 segments's offset differ by more than Int.MaxValue, they will be put into different groups and therefore won't be writing to the same output segment. So, I am not sure why the grouping didn't happen.

Do you think you could get the value of index.lastOffset and index.baseOffset of these 2 segments in the debugger? Alternatively, if you could upload the 2 log segments (with both the log and the index files) with base offset 0 and 2147343575 to the jira, we can take a look of that locally.
~~~~

4.

~~~~
Could you attach the .index file of the 2 segments too?
~~~~

5.

~~~~
I've uploaded all files pertaining to the two segments. In both cases the .index files are zero bytes and couldn't be uploaded
~~~~

6.

~~~~
Please let us know if you need any additional information that could help debugging the issue. We had to rollback the cluster to 0.9 but we would like to move to the new version.
~~~~

7.

~~~~
I've just had this issue myself. The problem is that when the index file size is 0 the actual last offset in the .log file is not reported. It uses the baseoffset.  This causes the group segments to incorrectly group the segments.
The log compaction uses the actual offsets from the log file which are often too large a range to fit into a single segment hitting the require statement.
The fix is to ensure that the correct last offset is always reported.

This is more apparent with heavily compacted topics where the last offset can be much larger than the base offset.

~~~~

8.

~~~~
This happened again today on another cluster we had upgraded ~3 weeks ago. [~junrao] could you please suggest a workaround if it exists to tackle this issue? It is a high priority for us since log cleaner threads and in turn compaction have stopped.
~~~~

9.

~~~~
[~Kelvinrutt], yes, that seems to be the issue. segs.head.index.lastOffset doesn't give the precise last offset in the segment, especially in the case where the index is empty. The issue seems to be there even in 0.9.0.

About the fix. LogSegment.nextOffset() gives the offset that we want, but can be expensive. Perhaps we could use the next segment's base offset instead. [~Kelvinrutt], do you think you could patch it?

Until this is fixed, not sure if there is an easy way to get around the issue.
~~~~

10.

~~~~
This is the patch I did.  It's basic but does the job.
~~~~

11.

~~~~
[~Kelvinrutt], thanks for the patch. We normally contribute code through git pull requests (see details http://kafka.apache.org/contributing) to make the review and testing easy. Do you think you could submit a git PR instead? Thanks,
~~~~

12.

~~~~
[~junrao], no problem. It might be a couple of days before I can do this. It seems my patch makes the symptoms less likely but doesn't fix the problem.  We need to ensure the last index is always written to the .index file because log.index.interval.bytes is preventing this. 
I still see the issue even when the .index file is not zero length.
~~~~

13.

~~~~
[~Kelvinrutt], yes, getting the last offset from the index won't be reliable since the last offset is not guaranteed to be in the index. We can probably just use (the base offset of the next segment - 1) as the last Offset for the current segment. The next segment should always exist since the last segment will never be cleaned.
~~~~

14.

~~~~
Issue resolved by pull request 3357
[https://github.com/apache/kafka/pull/3357]
~~~~

15.

~~~~
Merged https://github.com/apache/kafka/pull/3397 to 0.10.2.
~~~~

16.

~~~~
Thanks [~Kelvinrutt] for getting this solved very quickly! [~junrao] is there a timeline/plans for the 0.10.2.2 release?
~~~~

17.

~~~~
Also hit this issue, when could 0.10.2.2 expected to be released?
~~~~

18.

~~~~
We are encountering this bug - Is 0.10.2.2 released? I don't see a link in the releases page.
~~~~

19.

~~~~
0.10.2.2 hasn't been released and there are no immediate plans to release it. Can you upgrade to 0.11.0.2 instead?
~~~~

20.

~~~~
We're hitting the same problem and would like to upgrade to a 0.10.x version to reduce the workload and, more importantly, risks. According to https://issues.apache.org/jira/projects/KAFKA/versions/12340570 there are 19 bugs total, 2 of which are marked critical and 14 major.

As far as I can tell, there is no workaround for this problem. Is this enough reason to go through a release cycle? I'd like to provide some help, but obviously I can't do that for releasing. What are things that users like us can do to make a 0.10.2.2 release happen?
~~~~

21.

~~~~
We ran into this for a partition of the __consumer_offsets topic. The issue was discovered when we noticed that the open file count for a Kafka broker had been steadily growing for a couple months, and was about 2x higher than any other broker in the cluster. When we restarted this broker it seemed able to recover, deleting a large number of old log segments, with the open file count returning to a more normal value.
~~~~

22.

~~~~
Yes, that's what happens when the log cleaner dies for any reason (the compacted logs are no longer compacted and will grow unbounded). The original issue has no workaround, meaning that the log cleaner will die again after restarting the broker...

FWIW, we ended up upgrading to 0.11.x since there was clearly no intention on releasing 0.10.2.2.
~~~~

23.

~~~~
Thanks for the insight, we'll keep a watchful eye on it.
~~~~

24.

~~~~
Is this the same issue as was reported here? https://issues.apache.org/jira/browse/KAFKA-6056  (note the workaround we used, also)
~~~~

25.

~~~~
{quote}Is this the same issue as was reported here?{quote}

It sounds like a related issue, that may be more rare than what the correction for this one addressed, or a variant that eluded the bug fix here. The stack trace looks the same.
~~~~

26.

~~~~
Hi, I have the same problem and I'm running 0.11.0.2.

That is what appears in log-cleaner.log:

 

[2018-04-18 10:00:32,918] INFO Cleaner 3: Cleaning log __consumer_offsets-13 (cleaning prior to Tue Mar 06 12:04:48 CET 2018, discarding tombstones prior to Tue Dec 19 19:33:28 CET 2017)... (kafka.log.LogCleaner)
[2018-04-18 10:00:32,919] INFO Cleaner 3: Cleaning segment 0 in log __consumer_offsets-13 (largest timestamp Tue Dec 12 09:06:39 CET 2017) into 0, retaining deletes. (kafka.log.LogCleaner)
[2018-04-18 10:00:32,954] ERROR [kafka-log-cleaner-thread-3]: Error due to (kafka.log.LogCleaner)
java.lang.IllegalArgumentException: requirement failed: largest offset in message set can not be safely converted to relative offset.
        at scala.Predef$.require(Predef.scala:224)
        at kafka.log.LogSegment.append(LogSegment.scala:121)
        at kafka.log.Cleaner.cleanInto(LogCleaner.scala:547)
        at kafka.log.Cleaner.cleanSegments(LogCleaner.scala:443)
        at kafka.log.Cleaner$$anonfun$doClean$4.apply(LogCleaner.scala:385)
        at kafka.log.Cleaner$$anonfun$doClean$4.apply(LogCleaner.scala:384)
        at scala.collection.immutable.List.foreach(List.scala:392)
        at kafka.log.Cleaner.doClean(LogCleaner.scala:384)
        at kafka.log.Cleaner.clean(LogCleaner.scala:361)
        at kafka.log.LogCleaner$CleanerThread.cleanOrSleep(LogCleaner.scala:256)
        at kafka.log.LogCleaner$CleanerThread.doWork(LogCleaner.scala:236)
        at kafka.utils.ShutdownableThread.run(ShutdownableThread.scala:64)
[2018-04-18 10:00:32,954] INFO [kafka-log-cleaner-thread-3]: Stopped (kafka.log.LogCleaner)

Any suggestion?

 

Thanks!!
~~~~

27.

~~~~
Hi [~davidpsv17]

Did you just upgraded to 0.11.x when you hit this issue? If yes, it maybe related to KAFKA-6264. 

Thanks

Badai
~~~~

28.

~~~~
Can we manually delete .index and .log files for that partition if we don't care about data loss as our consumer group is disbaled now, which was catered by the consumer offsets partition which is having this issue.
~~~~

---

## KAFKA-5891: Cast transformation fails if record schema contains timestamp field

https://issues.apache.org/jira/browse/KAFKA-5891

Given fix versions: 1.0.3, 1.1.2, 2.0.1
JIRA affects (masked from the system): 0.11.0.0

- `KAFKA-5891@0.11.0.0`: config 0.11.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-5891@0.10.2.2`: config 0.10.2.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
I have the following simple type cast transformation:
{code}
name=postgresql-source-simple
connector.class=io.confluent.connect.jdbc.JdbcSourceConnector
tasks.max=1

connection.url=jdbc:postgresql://localhost:5432/testdb?user=postgres&password=mysecretpassword
query=SELECT 1::INT as a, '2017-09-14 10:23:54'::TIMESTAMP as b

transforms=Cast
transforms.Cast.type=org.apache.kafka.connect.transforms.Cast$Value
transforms.Cast.spec=a:boolean

mode=bulk
topic.prefix=clients
{code}
Which fails with the following exception in runtime:
{code}
[2017-09-14 16:51:01,885] ERROR Task postgresql-source-simple-0 threw an uncaught and unrecoverable exception (org.apache.kafka.connect.runtime.WorkerTask:148)
org.apache.kafka.connect.errors.DataException: Invalid Java object for schema type INT64: class java.sql.Timestamp for field: "null"
	at org.apache.kafka.connect.data.ConnectSchema.validateValue(ConnectSchema.java:239)
	at org.apache.kafka.connect.data.ConnectSchema.validateValue(ConnectSchema.java:209)
	at org.apache.kafka.connect.data.Struct.put(Struct.java:214)
	at org.apache.kafka.connect.transforms.Cast.applyWithSchema(Cast.java:152)
	at org.apache.kafka.connect.transforms.Cast.apply(Cast.java:108)
	at org.apache.kafka.connect.runtime.TransformationChain.apply(TransformationChain.java:38)
	at org.apache.kafka.connect.runtime.WorkerSourceTask.sendRecords(WorkerSourceTask.java:190)
	at org.apache.kafka.connect.runtime.WorkerSourceTask.execute(WorkerSourceTask.java:168)
	at org.apache.kafka.connect.runtime.WorkerTask.doRun(WorkerTask.java:146)
	at org.apache.kafka.connect.runtime.WorkerTask.run(WorkerTask.java:190)
	at java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:511)
	at java.util.concurrent.FutureTask.run(FutureTask.java:266)
	at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1142)
  at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:617)
	at java.lang.Thread.run(Thread.java:745)
{code}
If I remove the  transforms.* part of the connector it will work correctly. Actually, it doesn't really matter which types I use in the transformation for field 'a', just the existence of a timestamp field brings the exception.
~~~~

### Comments (4)

1.

~~~~
Seems like Kafka Connect's Cast transformation loses schema information (basically, schema name) while doing type casting. I was able to reproduce this problem with the following test in org.apache.kafka.connect.transforms.CastTest for current trunk repository branch:
{code}
@SuppressWarnings("unchecked")
@Test
public void castWholeRecordValueWithSchemaBooleanAndTimestampField() {
    final Cast<SourceRecord> xform = new Cast.Value<>();
    xform.configure(Collections.singletonMap(Cast.SPEC_CONFIG, "int64:boolean"));

    SchemaBuilder builder = SchemaBuilder.struct();
    builder.field("int64", Schema.INT64_SCHEMA);
    builder.field("timestamp", Timestamp.SCHEMA);
    Schema supportedTypesSchema = builder.build();

    Struct recordValue = new Struct(supportedTypesSchema);
    recordValue.put("int64", (long) 64);
    recordValue.put("timestamp", new java.sql.Timestamp(0L));

    SourceRecord transformed = xform.apply(new SourceRecord(null, null, "topic", 0,
            supportedTypesSchema, recordValue));

    assertEquals(true, ((Struct) transformed.value()).get("int64"));
    assertEquals(new java.sql.Timestamp(0L), ((Struct) transformed.value()).get("timestamp"));
}
{code}
The problem is that Timestamp.SCHEMA has schema.type = 'INT64' and schema.name = "org.apache.kafka.connect.data.Timestamp", but org.apache.kafka.connect.transforms.Cast#getOrBuildSchema method copies schema.type only:
{code}
SchemaBuilder fieldBuilder =
    convertFieldType(casts.containsKey(field.name()) ? casts.get(field.name()) : field.schema().type());
{code}

~~~~

2.

~~~~
I am facing same issue when consuming from KAFKA to HDFS with CAST TRANSFORMS. Any pointer please.

My Connector :
*********************
{code:java}
{
 "name": "hdfs-sink-avro-cast-test-stndln",
 "config": {
  "key.converter": "io.confluent.connect.avro.AvroConverter",
  "key.converter.schema.registry.url": "http://localhost:8081",
  "value.converter": "io.confluent.connect.avro.AvroConverter",
  "value.converter.schema.registry.url": "http://localhost:8081",
  "key.converter.schemas.enable": "true",
  "value.converter.schemas.enable": "true",
  "internal.key.converter": "org.apache.kafka.connect.json.JsonConverter",
  "internal.value.converter": "org.apache.kafka.connect.json.JsonConverter",
  "internal.key.converter.schemas.enable": "false",
  "internal.value.converter.schemas.enable": "false",
  "offset.storage.file.filename": "/tmp/connect.offsets.avroHdfsConsumer.casttest.stndln",
  "offset.flush.interval.ms": "500",
  "parse.key": "true",
  "connector.class": "io.confluent.connect.hdfs.HdfsSinkConnector",
  "hadoop.home": "/usr/lib/hadoop",
  "hdfs.url": "hdfs://ip-127-34-56-789.us-east-1.compute.interna:8020",
  "topics": "avro_raw_KFK_SRP_USER_TEST_V,avro_raw_KFK_SRP_PG_HITS_TEST_V",
  "tasks.max": "1",
  "topics.dir": "/home/hadoop/kafka/data/streams/in/raw/casttest1",
  "logs.dir": "/home/hadoop/kafka/wal/streams/in/raw/casttest1",
  "hive.integration": "true",
  "hive.metastore.uris": "thrift://ip-127-34-56-789.us-east-1.compute.internal:9083",
  "schema.compatibility": "BACKWARD",
  "flush.size": "10000",
  "rotate.interval.ms": "1000",
  "mode": "timestamp",
  "transforms": "Cast",
  "transforms.Cast.type": "org.apache.kafka.connect.transforms.Cast$Value",
  "transforms.Cast.spec": "residuals:float64,comp:float64"
 }
}
{code}


{code:java}
[2017-11-16 01:14:39,719] ERROR Task hdfs-sink-avro-cast-test-stndln-0 threw an uncaught and unrecoverable exception (org.apache.kafka.connect.runtime.WorkerTask:148)
org.apache.kafka.connect.errors.DataException: Invalid Java object for schema type INT64: class java.util.Date for field: "null"
        at org.apache.kafka.connect.data.ConnectSchema.validateValue(ConnectSchema.java:239)
        at org.apache.kafka.connect.data.ConnectSchema.validateValue(ConnectSchema.java:209)
        at org.apache.kafka.connect.data.Struct.put(Struct.java:214)
        at org.apache.kafka.connect.transforms.Cast.applyWithSchema(Cast.java:152)
        at org.apache.kafka.connect.transforms.Cast.apply(Cast.java:108)
        at org.apache.kafka.connect.runtime.TransformationChain.apply(TransformationChain.java:38)
        at org.apache.kafka.connect.runtime.WorkerSinkTask.convertMessages(WorkerSinkTask.java:414)
        at org.apache.kafka.connect.runtime.WorkerSinkTask.poll(WorkerSinkTask.java:250)
        at org.apache.kafka.connect.runtime.WorkerSinkTask.iteration(WorkerSinkTask.java:180)
        at org.apache.kafka.connect.runtime.WorkerSinkTask.execute(WorkerSinkTask.java:148)
        at org.apache.kafka.connect.runtime.WorkerTask.doRun(WorkerTask.java:146)
        at org.apache.kafka.connect.runtime.WorkerTask.run(WorkerTask.java:190)
        at java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:511)
        at java.util.concurrent.FutureTask.run(FutureTask.java:266)
        at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
        at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
        at java.lang.Thread.run(Thread.java:748)
[2017-11-16 01:14:39,719] ERROR Task is being killed and will not recover until manually restarted (org.apache.kafka.connect.runtime.WorkerTask:149)
[2017-11-16 01:14:39,719] INFO Shutting down Hive executor service. (io.confluent.connect.hdfs.DataWriter:309)
{code}
~~~~

3.

~~~~
[~broartem]
Could you test my patch ?
~~~~

4.

~~~~
KAFKA-6290 is another issue related to the CAST transformation, but deals with actually being able to CAST fields that use logical types.

This issue, OTOH, is simply that the record's Struct can only contain fields that have a castable (i.e., currently primitive) type.
~~~~

---

## KAFKA-6088: Kafka Consumer slows down when reading from highly compacted topics

https://issues.apache.org/jira/browse/KAFKA-6088

Given fix versions: 0.11.0.0
JIRA affects (masked from the system): 0.10.2.1

- `KAFKA-6088@0.10.2.1`: config 0.10.2.1, metadata answer **affected** (listed_affected)
- `KAFKA-6088@0.10.2.0`: config 0.10.2.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 0.10.2.1, 0.11.0.0, 0.11, 0.11.0.1, 0.10.0.0

### Description

~~~~
Summary of the issue
-----
We found a performance issue with the Kafka Consumer where it gets less efficient if you have frequent gaps in offsets (which happens when there is lots of compaction on the topic).

The issue is present in 0.10.2.1 and possibly prior.

It is fixed in 0.11.0.0.

Summary of cause
-----
The fetcher code assumes that there will be no gaps in message offsets. If there are, it does an additional round trip to the broker. For topics with large gaps in offsets, it is possible that most calls to {{poll()}} will generate a roundtrip to the broker.

Background and details 
-----
We have a topic with roughly 8 million records. The topic is log compacted. It turns out that most of the initial records in the topic were never overwritten, whereas in the 2nd half of the topic we had lots of overwritten records. That means that for the first part of the topic, there are no gaps in offsets. But in the 2nd part of the topic, there are frequent gaps in the offsets (due to records being compacted away).

We have a consumer that starts up and reads the entire topic from beginning to end. We noticed that the consumer would read through the first part of the topic very quickly. When it got to the part of the topic with frequent gaps in offsets, consumption rate slowed down dramatically. This slowdown was consistent across multiple runs.

What is happening is this:
1) A call to {{poll()}} happens. The consumer goes to the broker and returns 1MB of data (the default of {{max.partition.fetch.bytes}}). It then returns to the caller just 500 records (the default of {{max.poll.records}}), and keeps the rest of the data in memory to use in future calls to {{poll()}}. 
2) Before returning the 500 records, the consumer library records the *next* offset it should return. It does so by taking the offset of the last record, and adds 1 to it. (The offset of the 500th message from the set, plus 1). It calls this the {{nextOffset}}
3) The application finishes processing the 500 messages, and makes another call to {{poll()}} happens. During this call, the consumer library does a sanity check. It checks that the first message of the set *it is about to return* has an offset that matches the value of {{nextOffset}}. That is it checks if the 501th record has an offset that is 1 greater than the 500th record.
	a. If it matches, then it returns an additional 500 records, and increments the {{nextOffset}} to (offset of the 1000th record, plus 1)
	b. If it doesn't match, then it throws away the remainder of the 1MB of data that it stored in memory in step 1, and it goes back to the broker to fetch an additional 1MB of data, starting at the offset {{nextOffset}}.

In topics have no gaps (a non-compacted topic), then the code will always hit the 3a code path.
If the topic has gaps in offsets and the call to {{poll()}} happens to fall onto a gap, then the code will hit code path 3b.

If the gaps are frequent, then it will frequently hit code path 3b.

The worst case scenario that can happen is if you have a large number of gaps, and you run with {{max.poll.records=1}}. Every gap will result in a new fetch to the broker. You may possibly end up only processing one message per fetch. Or, said another way, you will end up doing a single fetch for every single message in the partition.


Repro
-----

We created a repro. It appears that the bug is in 0.10.2.1, but was fixed in 0.11. I've attached the tarball with all the code and instructions. 

The repro is:
1) Create a single partition topic with log compaction turned on 
2) Write messages with the following keys: 1 1 2 2 3 3 4 4 5 5 ... (each message key written twice in a row) 
3) Let compaction happen. This would mean that that offsets 0 2 4 6 8 10 ... would be compacted away 
4) Consume from this topic with {{max.poll.records=1}}

More concretely,

Here is the producer code:
{code}
Producer<String, String> producer = new KafkaProducer<String, String>(props); 
for (int i = 0; i < 1000000; i++) { 
    producer.send(new ProducerRecord<String, String>("compacted", Integer.toString(i), Integer.toString(i))); 
    producer.send(new ProducerRecord<String, String>("compacted", Integer.toString(i), Integer.toString(i))); 
} 
producer.flush(); 
producer.close();
{code}


When consuming with a 0.10.2.1 consumer, you can see this pattern (with Fetcher logs at DEBUG, see file consumer_0.10.2/debug.log):

{code}
offset = 1, key = 0, value = 0 
22:58:51.262 [main] DEBUG o.a.k.c.consumer.internals.Fetcher - Ignoring fetched records for compacted-0 at offset 3 since the current position is 2 
22:58:51.263 [main] DEBUG o.a.k.c.consumer.internals.Fetcher - Sending fetch for partitions [compacted-0] to broker 192.168.0.105:9092 (id: 0 rack: null) 
offset = 3, key = 1, value = 1 
22:58:51.299 [main] DEBUG o.a.k.c.consumer.internals.Fetcher - Ignoring fetched records for compacted-0 at offset 5 since the current position is 4 
22:58:51.299 [main] DEBUG o.a.k.c.consumer.internals.Fetcher - Sending fetch for partitions [compacted-0] to broker 192.168.0.105:9092 (id: 0 rack: null) 
offset = 5, key = 2, value = 2 
22:58:51.337 [main] DEBUG o.a.k.c.consumer.internals.Fetcher - Ignoring fetched records for compacted-0 at offset 7 since the current position is 6 
22:58:51.337 [main] DEBUG o.a.k.c.consumer.internals.Fetcher - Sending fetch for partitions [compacted-0] to broker 192.168.0.105:9092 (id: 0 rack: null) 
offset = 7, key = 3, value = 3 
22:58:51.361 [main] DEBUG o.a.k.c.consumer.internals.Fetcher - Ignoring fetched records for compacted-0 at offset 9 since the current position is 8 
22:58:51.361 [main] DEBUG o.a.k.c.consumer.internals.Fetcher - Sending fetch for partitions [compacted-0] to broker 192.168.0.105:9092 (id: 0 rack: null) 
offset = 9, key = 4, value = 4 
22:58:51.382 [main] DEBUG o.a.k.c.consumer.internals.Fetcher - Ignoring fetched records for compacted-0 at offset 11 since the current position is 10 
22:58:51.382 [main] DEBUG o.a.k.c.consumer.internals.Fetcher - Sending fetch for partitions [compacted-0] to broker 192.168.0.105:9092 (id: 0 rack: null) 
offset = 11, key = 5, value = 5 
22:58:51.404 [main] DEBUG o.a.k.c.consumer.internals.Fetcher - Ignoring fetched records for compacted-0 at offset 13 since the current position is 12 
22:58:51.404 [main] DEBUG o.a.k.c.consumer.internals.Fetcher - Sending fetch for partitions [compacted-0] to broker 192.168.0.105:9092 (id: 0 rack: null) 
offset = 13, key = 6, value = 6 
22:58:51.424 [main] DEBUG o.a.k.c.consumer.internals.Fetcher - Ignoring fetched records for compacted-0 at offset 15 since the current position is 14 
22:58:51.424 [main] DEBUG o.a.k.c.consumer.internals.Fetcher - Sending fetch for partitions [compacted-0] to broker 192.168.0.105:9092 (id: 0 rack: null)
{code}


When consuming with a 0.11.0.1 consumer ,you can see the following pattern: (see file consumer_0.11/debug.log): 
{code}
offset = 1, key = 0, value = 0 
offset = 3, key = 1, value = 1 
offset = 5, key = 2, value = 2 
offset = 7, key = 3, value = 3 
offset = 9, key = 4, value = 4 
offset = 11, key = 5, value = 5 
offset = 13, key = 6, value = 6 
offset = 15, key = 7, value = 7 
offset = 17, key = 8, value = 8 
offset = 19, key = 9, value = 9 
offset = 21, key = 10, value = 10 
{code}

From looking at the github history, it appears it was fixed in https://github.com/apache/kafka/commit/a0b8e435c9419a9402d08408260bea0c1d95cff0

Specifically, this line 
https://github.com/apache/kafka/commit/a0b8e435c9419a9402d08408260bea0c1d95cff0#diff-b45245913eaae46aa847d2615d62cde0L930

Was replaced by this line: 
https://github.com/apache/kafka/commit/a0b8e435c9419a9402d08408260bea0c1d95cff0#diff-b45245913eaae46aa847d2615d62cde0R933

Mitigation
-----
This problem is fixed in 0.11.0.0. If you can upgrade to 0.11.0.0, then you will not be affected by the problem.

If you cannot upgrade to 0.11.0.0, then you can reduce the impact of this by increasing the value of {{max.poll.records}}. This works because check happens on each call to {{poll()}}, and increasing the value of {{max.poll.records}} will reduce the number of calls to {{poll()}}.

~~~~

### Comments (3)

1.

~~~~
I spoke with Confluent engineers about this, and they agree with the analysis above. However, since it is fixed in 0.11.0.0, and since 0.11.0.0 can be used on brokers as far back as 0.10.0.0, there is no need to release a bugfix for the older releases. So, marking this as WONT FIX.

Note that if you are using 0.10.0.0 brokers and are using Kafka Streams, that you will not be able to use Kafka Streams 0.11.0.0. That means you may still be affected by this bug. Until you are able to move to newer brokers, you will have to use the mitigation steps described above.

[~apurva], is there anything else I missed on this?
~~~~

2.

~~~~
It is fixed in kafka client 0.11.0.0, and 0.11.0.0 clients can be used against brokers as far back as 0.10.0.0. So if anyone is affected, they can update their kafka clients in order to get the fix. So, we won't issue a patch fix to older releases.
~~~~

3.

~~~~
Since it was fixed in 0.11.0.0, marking it as fixed.
~~~~

---

## KAFKA-6490: JSON SerializationException Stops Connect

https://issues.apache.org/jira/browse/KAFKA-6490

Given fix versions: 2.0.0
JIRA affects (masked from the system): 1.0.0

- `KAFKA-6490@1.0.0`: config 1.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-6490@0.11.0.3`: config 0.11.0.3, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 1.1, 2.0

### Description

~~~~
If you configure KafkaConnect to parse JSON messages, and you send it a non-JSON message, the SerializationException message will bubble up to the top, and stop KafkaConnect. While I understand sending non-JSON to a JSON serializer is a bad idea, I think that a single malformed message stopping all of KafkaConnect is even worse.

The data exception is thrown here: [https://github.com/apache/kafka/blob/trunk/connect/json/src/main/java/org/apache/kafka/connect/json/JsonConverter.java#L305]
 
From the call here: [https://github.com/apache/kafka/blob/trunk/connect/runtime/src/main/java/org/apache/kafka/connect/runtime/WorkerSinkTask.java#L476]

This bubbles all the way up to the top, and KafkaConnect simply stops with the message: {{ERROR WorkerSinkTask\{id=elasticsearch-sink-0} Task threw an uncaught and unrecoverable exception (org.apache.kafka.connect.runtime.WorkerTask:172)}}

Thoughts on adding a {{try/catch}} around the {{for}} loop in WorkerSinkTask's {{convertMessages}} so messages that don't properly parse are logged, but simply ignored? This way KafkaConnect can keep working even when it encounters a message it cannot decode?
~~~~

### Comments (10)

1.

~~~~
Yes I also faces this issue. I feel that the connector should throw a warning and should move on to the next message. But still I would like other contributors to comment on this.
~~~~

2.

~~~~
Seems like a simple fix. I wrapped the inside of the {{for}} loop with a {{try/catch}} for a {{DataException}} and reported the exception as a warning. This will allow other messages to be processed. Only hitch is that if you have an entire topic full of non-JSON messages, then you'll fill up your logs with a bunch of these messages. One way to remedy this would be to put a counter such that after say 100 of these warnings, it stops reporting... however, that might be too clever. Thoughts?
~~~~

3.

~~~~
[~mjsax] Can you please help [~wspeirs] with this ticket ?

 
 
~~~~

4.

~~~~
I am not too familiar with the details of Connect. However, it sound like this change might require a KIP. There was a similar issue for Streams and we added a config so people can choose to resume of fail for this case: [https://cwiki.apache.org/confluence/display/KAFKA/KIP-161%3A+streams+deserialization+exception+handlers]

\cc  [~wicknicks] [~rhauch] [~kkonstantine]
~~~~

5.

~~~~
Thanks for you response [~mjsax]. I think we need a similar feature in connector because now if we get a malformed JSON message the connector will fail and will not process any additional message that are coming after this one. Can you also please add me to the contributors list ?
~~~~

6.

~~~~
A change in behavior like that would definitely require a KIP – existing users would not expect this at all.

Connect started with the current behavior because for many users losing data is worse than suffering some downtime. However, it's clear some alternatives are warranted; this question comes up from time to time on mailing lists. Generally there are only a few options that seem to make sense:
 * Stop processing (current behavior) and log
 * Log and retry (really only makes sense for unusual edge cases where data got corrupted in flight between Kafka and Connect)
 * Discard and log (I care about uptime more than a bit of lost data)
 * Dead letter queue (or some other fallback handler)

The retry case is probably the least important here as it will rarely make a difference, so the other 3 are the ones I think we'd want to implement. A KIP for this should be straightforward, though the implementation will require care to make sure we handle all places errors can occur (in the producer/consumer, during deserialization, during transformations, etc).
~~~~

7.

~~~~
[~ewencp]: Thanks for feedback. What you are mentioning makes sense we should users option to chose from because each use case is different. I feel that Discard and log option can be provided to the user and skeptical about the dead letter queue.  

Also which version should this bug be worked upon ? 

 

Can I get please get access to the confluent ([https://cwiki.apache.org/confluence/display/KAFKA/Kafka+Improvement+Proposals)] as well ? 
~~~~

8.

~~~~
[~prasanna1433] I've given you wiki permissions, you should be able to create a page now.

The dead letter queue is something I've specifically heard from a number of users, so it's definitely in demand. The list I gave is based on a ton of real user feedback, so I feel pretty confident that it is both a) covering important use cases and b) comprehensive enough to address the vast majority of use cases. But I'm of course open to discussion of the options. I suspect *more* options would be the result rather than removing some. If you want to take on this improvement, we can of course discuss further in the KIP thread :)

 

With respect to the version, new features should almost universally be worked on in trunk – older release branches are reserved for bug fixes. In this case, since we just cut 1.1 branches, this would be a candidate for 1.2 / 2.0 and can simply be developed against trunk.
~~~~

9.

~~~~
[~ewencp]: Thanks for giving me permissions. 

I am interested in working on this improvement and yes we need to discuss more on the dead letter queue.

After creating the page I will start the discussion thread in the mailing list.
~~~~

10.

~~~~
Closing as this is effectively fixed by [https://cwiki.apache.org/confluence/display/KAFKA/KIP-298%3A+Error+Handling+in+Connect] which allows you to configure how errors are handled, and should apply to errors in Converters, Transformations, and Connectors.
~~~~

---

## KAFKA-6710: Streams integration tests hang during shutdown

https://issues.apache.org/jira/browse/KAFKA-6710

Given fix versions: 2.0.0
JIRA affects (masked from the system): 1.1.0

- `KAFKA-6710@1.1.0`: config 1.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-6710@1.0.2`: config 1.0.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
Builds have been timing out a lot recently and many of the logs show streams integration tests being run, but not completed. While running tests locally, I saw a failure during shutdown of {{TableTableJoinIntegrationTest}}. The test was stuck waiting for a broker to shutdown when a {{KafkaScheduler}} was attemping to delete logs. KAFKA-6624 (Commit #1ea07b993d75ed68f4c04282eb177bf84156e0b2) added a _Thread.sleep_ to wait for the time to delete each log segment inside the scheduled delete task. The failing streams test had 62 logs to delete and since MockTime doesn't get updated during the test, it would have waited for 62 minutes to complete. This blocks shutdown of the broker for 62 minutes. This is an issue if a streams integration test takes more than 30 seconds when the first delayed delete task is scheduled to be run.

Changing _Thread.sleep_ to _time.sleep_ fixes this test issue. But it will be good to know why we have a _sleep_ on a _Scheduler_ at all. With the default _log.segment.delete.delay.ms_ of one minute, this potentially blocks a scheduler thread for upto a minute when there are logs to be deleted. Couldn't we just break out of the loop if it is not yet time to delete the first log segment in the list? The log would then get deleted when the broker checks next time. [~junrao] [~lindong] ?

 

*Stack trace from failing test*:

{{"kafka-scheduler-8" daemon prio=5 tid=0x00007fe58dc16800 nid=0x9603 waiting on condition [0x0000700003f25000]}}
{{   java.lang.Thread.State: TIMED_WAITING (sleeping)}}
{{        at java.lang.Thread.sleep(Native Method)}}
{{        at kafka.log.LogManager.kafka$log$LogManager$$deleteLogs(LogManager.scala:717)}}
{{        at kafka.log.LogManager$$anonfun$3.apply$mcV$sp(LogManager.scala:406)}}
{{        at kafka.utils.KafkaScheduler$$anonfun$1.apply$mcV$sp(KafkaScheduler.scala:110)}}
{{        at kafka.utils.CoreUtils$$anon$1.run(CoreUtils.scala:62)}}
{{        at java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:471)}}
{{        at java.util.concurrent.FutureTask.run(FutureTask.java:262)}}
{{        at java.util.concurrent.ScheduledThreadPoolExecutor$ScheduledFutureTask.access$201(ScheduledThreadPoolExecutor.java:178)}}
{{        at java.util.concurrent.ScheduledThreadPoolExecutor$ScheduledFutureTask.run(ScheduledThreadPoolExecutor.java:292)}}
{{        at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1145)}}
{{        at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:615)}}
{{        at java.lang.Thread.run(Thread.java:745)}}{{}}

{{}}{{"Test worker" prio=5 tid=0x00007fe58db72000 nid=0x5203 waiting on condition [0x0000700001cbd000]}}
{{   java.lang.Thread.State: TIMED_WAITING (parking)}}
{{        at sun.misc.Unsafe.park(Native Method)}}
{{        - parking to wait for  <0x0000000780fb8918> (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject)}}
{{        at java.util.concurrent.locks.LockSupport.parkNanos(LockSupport.java:226)}}
{{        at java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject.awaitNanos(AbstractQueuedSynchronizer.java:2082)}}
{{        at java.util.concurrent.ThreadPoolExecutor.awaitTermination(ThreadPoolExecutor.java:1468)}}
{{        at kafka.utils.KafkaScheduler.shutdown(KafkaScheduler.scala:98)}}
{{        at kafka.server.KafkaServer$$anonfun$shutdown$5.apply$mcV$sp(KafkaServer.scala:569)}}
{{        at kafka.utils.CoreUtils$.swallow(CoreUtils.scala:85)}}
{{        at kafka.server.KafkaServer.shutdown(KafkaServer.scala:569)}}
{{        at org.apache.kafka.streams.integration.utils.KafkaEmbedded.stop(KafkaEmbedded.java:129)}}
{{        at org.apache.kafka.streams.integration.utils.EmbeddedKafkaCluster.stop(EmbeddedKafkaCluster.java:126)}}
{{        at org.apache.kafka.streams.integration.utils.EmbeddedKafkaCluster.after(EmbeddedKafkaCluster.java:158)}}
{{        at org.junit.rules.ExternalResource$1.evaluate(ExternalResource.java:50)}}
{{        at org.junit.rules.RunRules.evaluate(RunRules.java:20)}}
~~~~

---

## KAFKA-6853: ResponseMetadata calculates latency incorrectly (and therefore ZooKeeperRequestLatencyMs is incorrect)

https://issues.apache.org/jira/browse/KAFKA-6853

Given fix versions: 1.1.1, 2.0.0
JIRA affects (masked from the system): 1.1.0

- `KAFKA-6853@1.1.0`: config 1.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-6853@1.0.2`: config 1.0.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
responseTimeMs always negative.

Currently:
{code}
case class ResponseMetadata(sendTimeMs: Long, receivedTimeMs: Long) {
  def responseTimeMs: Long = sendTimeMs - receivedTimeMs
}
{code}

Should be:
{code}
case class ResponseMetadata(sendTimeMs: Long, receivedTimeMs: Long) {
  def responseTimeMs: Long = receivedTimeMs - sendTimeMs
}
{code}
~~~~

---

## KAFKA-7012: Performance issue upgrading to kafka 1.0.1 or 1.1

https://issues.apache.org/jira/browse/KAFKA-7012

Given fix versions: 1.0.2, 1.1.1, 2.0.0
JIRA affects (masked from the system): 1.0.1, 1.1.0

- `KAFKA-7012@1.1.0`: config 1.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-7012@1.0.0`: config 1.0.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 1.0.1, 1.1, 0.11.0.1, 2.0.0, 1.0, 1.1.1, 1.1.2, 1.0.2

### Description

~~~~
We are trying to upgrade kafka cluster from Kafka 0.11.0.1 to Kafka 1.0.1. After upgrading 1 node on the cluster, we notice that network threads use most of the cpu. It is a 3 node cluster with 15k messages/sec on each node. With Kafka 0.11.0.1 typical usage of the servers is around 50 to 60% vcpu(using less than 1 vcpu). After upgrade we are noticing that cpu usage is high depending on the number of network threads used. If networks threads is set to 8, then the cpu usage is around 850%(9 vcpus) and if it is set to 4 then the cpu usage is around 450%(5 vcpus). Using the same kafka server.properties for both.

Did further analysis with git bisect, couple of build and deploys, traced the issue to commit 47ee8e954df62b9a79099e944ec4be29afe046f6. CPU usage is fine for commit f15cdbc91b240e656d9a2aeb6877e94624b21f8d. But with commit 47ee8e954df62b9a79099e944ec4be29afe046f6 cpu usage has increased. Have attached screenshots of profiling done with both the commits. Screenshot Commit-f15cdbc91b-profile shows less cpu usage by network threads and Screenshots Commit-47ee8e954-profile and Commit-47ee8e954-profile2 show higher cpu usage(almost entire cpu usage) by network threads. Also noticed that kafka.network.Processor.poll() method is invoked 10 times more with commit 47ee8e954df62b9a79099e944ec4be29afe046f6.

We need the issue to be resolved to upgrade the cluster. Please let me know if you need any additional information.
~~~~

### Comments (29)

1.

~~~~
Hi [~patl], I'm working with [~rajadayalanvdms] , and noticed you  have assigned this ticket to yourself. I just wanted to inquire about your expectations of when you'll have time to look into this ticket, etc. This will help us plan work on our side. Thank you!
~~~~

2.

~~~~
[~radai], any thoughts on this?
~~~~

3.

~~~~
the attached profile screenshot shows only 210ms (out of >650k ms) of self time in pool.tryAllocate().
a possible time drain with the patch is determineHandlingOrder() - it may shuffle the sockets in order to guarantee fairness under low memory conditions - but it doesnt appear in the screenshot.
there's also no equivalent screenshot of a detailed profile breakdown for the results without the patch, so no base to compare to.
was the profiler using cpu time or wall clock time for measurements?
were the ssl settings (cipher used etc) the same across measurements?
~~~~

4.

~~~~
Thanks, my comments added inline

the attached profile screenshot shows only 210ms (out of >650k ms) of self time in pool.tryAllocate().
 a possible time drain with the patch is determineHandlingOrder() - it may shuffle the sockets in order to guarantee fairness under low memory conditions - but it doesnt appear in the screenshot.
bq. did not notice issue with memory, i can do profiling with memory and include it.
 there's also no equivalent screenshot of a detailed profile breakdown for the results without the patch, so no base to compare to.
bq. attaching screenshot Commit-f15cdbc91b-profile2 for comparing.
 was the profiler using cpu time or wall clock time for measurements?
bq. In the attached screenshot Total time is the wall clock time and Total time(CPU) is the cpu time.
 were the ssl settings (cipher used etc) the same across measurements?
bq. ssl settings and cipher used are same across measurements.
~~~~

5.

~~~~
You can precede quoted comment with 'bq.' (note the trailing dot).
~~~~

6.

~~~~
attached the screenshots(Commit-47ee8e954-0607-profile, Commit-47ee8e954-0607-memory)  done with one more profiling.
~~~~

7.

~~~~
my only current hypothesis is that `keysWithBufferedRead` is non-empty, causing lots of very short poll() calls for those.
could you try comment out that poll() and re-run the experiment ?
~~~~

8.

~~~~
do you mean to comment the poll method in org.apache.kafka.common.network.Selector as below
{quote}@@ -324,6 +324,7 @@ public class Selector implements Selectable, AutoCloseable {
 */
 @Override
 public void poll(long timeout) throws IOException {
 + /*
 if (timeout < 0)
 throw new IllegalArgumentException("timeout should be >= 0");

@@ -345,8 +346,10 @@ public class Selector implements Selectable, AutoCloseable {
 }
 outOfMemory = false;
 }
 -
 + */
 /* check ready keys */
 +
 + /*
 long startSelect = time.nanoseconds();
 int numReadyKeys = select(timeout);
 long endSelect = time.nanoseconds();
 @@ -379,6 +382,7 @@ public class Selector implements Selectable, AutoCloseable
Unknown macro: \{ // Add to completedReceives after closing expired connections to avoid removing // channels with completed receives until all staged receives are completed. addToCompletedReceives();+ */ }
 
{quote}
~~~~

9.

~~~~
no, not all of poll(), just this part:
{code}
            // Poll from channels that have buffered data (but nothing more from the underlying socket)
            if (dataInBuffers) {
                keysWithBufferedRead.removeAll(readyKeys); //so no channel gets polled twice
                Set<SelectionKey> toPoll = keysWithBufferedRead;
                keysWithBufferedRead = new HashSet<>(); //poll() calls will repopulate if needed
                pollSelectionKeys(toPoll, false, endSelect);  <---- COMMENT THIS OUT
            }
{code}

just comment out the call to pollSelectionKeys() at the end of the condition
~~~~

10.

~~~~
yes, your hypothesis is right. cpu usage is fine with the pollSelectionKeys() line commented, screenshot attached. Tried it on 1.0.1 version also and cpu usage is fine.
~~~~

11.

~~~~
that line is meant to handle a (hypothetical) scenario where socket data is available in the SSL cyphertext buffer but no data will ever be read from the socket itself again.
i guess we'll need to add some code to only run this path every-so-often as the SSL code is apparently likely to leave things behind.
did commenting this out affect function/correctness? missing msgs? higher 99th percentile latencies?
~~~~

12.

~~~~
Need to check regarding the correctness/missing msgs. Will check and update.
~~~~

13.

~~~~
Tried out in a different cluster 20 nodes(million msgs/sec), upgraded 5 nodes to 1.0.1 with the patched jar. can confirm that it is not affecting function/Missing msgs and latency also looks fine.
~~~~

14.

~~~~
in light of that i think the safe change to make would be to only record keys with bytes still buffered if memory pressure prevented anything from being read out this round (as opposed to always, as is current behaviour).
~~~~

15.

~~~~
Thanks, are you planning a PR to change the behaviour of polling buffered keys? 
~~~~

16.

~~~~
i dont have the time to pick this up right now.

IIRC the original PR (https://github.com/apache/kafka/pull/2330) had a more complicated condition for when a key (channel) gets picked into `keysWithBufferedRead`. the codition is currently
{code}
                if (channel.hasBytesBuffered()) {
                    //this channel has bytes enqueued in intermediary buffers that we could not read
                    //(possibly because no memory). it may be the case that the underlying socket will
                    //not come up in the next poll() and so we need to remember this channel for the
                    //next poll call otherwise data may be stuck in said buffers forever.
                    keysWithBufferedRead.add(key);
                }
{code}
which results in lots of "false positives" - keys that have something left over in ssl buffers (likely, since request sizes are rarely a multiple of ssl cipher block sizes) that cause the next poll() cycle to be inefficient.

the conditions needs to check if a channel has something left *that could not be read out due to memory pressure*.

alternatively - the doomsday scenario this is meant to handle is pretty rare: if a channel has a request fully inside the ssl buffers that cannot be read due to memory pressure, *and* the underlying channel will never have any more incoming bytes (so will never come back from select) the request will sit there and rot resulting in a client timeout.

the alternative to making the condition more complicated is not treating this case at all and suffering the (rare?) timeout?
~~~~

17.

~~~~
bq. not treating this case at all and suffering the (rare?) timeout?

Should be acceptable before better solution (with no performance penalty) is found.
~~~~

18.

~~~~
[~rsivaram] [~junrao], what are your thoughts on this one? It's a performance regression so it would be good to address.
~~~~

19.

~~~~
[~patl] Are you actively working on this JIRA? If not, can I pick it up and provide a simple solution to include in 2.0.0 - we are very close to cutting the first RC and it will be good to include at least a simple fix for this issue (we can improve on that in a follow on PR if required after the release). Let me know if you have any objections. Thank you!
~~~~

20.

~~~~
Thanks for resolving the issue. Will this patch be applied to 1.0.1/1.1 versions also? We are planning to upgrade to 1.0.1/1.1 version, patch for that version will be helpful.
~~~~

21.

~~~~
[~rajadayalanvdms] [~lindong] [~mjsax] I have cherry-picked this to 1.0 and 1.1 branches, so it should be available in the next bug-fix release.
~~~~

22.

~~~~
[~rsivaram] [~lindong] Was this cherry-picked to 1.1 before or after the RC0 was cut? Might not be in 1.1.1 release, but go into 1.1.2 if cherry-picked afterwards. We should double check and maybe update the "fix version" of this ticket. For 1.0.2, is will go in – I am blocked on some system test atm to cut the first RC.
~~~~

23.

~~~~
Yes, I think this may have missed the 1.1.1 cut.
~~~~

24.

~~~~
[~mjsax] It is not included in RC0 for 1.1.1. I just updated the "fix version" to include 1.1.2.

For cases like this, do we expect to include the patch in RC1 for 1.1.1?
~~~~

25.

~~~~
Unless it's deemed a blocker, it would wait until 1.1.2.
~~~~

26.

~~~~
Dong has published 1.1.1 RC1 due to another issue which means that this will be in 1.1.1.
~~~~

27.

~~~~
On behalf of [~rajadayalanvdms] and myself, thank you all!
~~~~

28.

~~~~
Tried 1.1.2 version in our kafka cluster, performance looks good. 
 
Thank you all again!!!
~~~~

29.

~~~~
Great to know that the fix works!

 
~~~~

---

## KAFKA-7097: VerifiableProducer does not work properly with --message-create-time argument

https://issues.apache.org/jira/browse/KAFKA-7097

Given fix versions: 2.1.0
JIRA affects (masked from the system): 1.0.0

- `KAFKA-7097@1.0.0`: config 1.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-7097@0.11.0.3`: config 0.11.0.3, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
If you run:

 

./bin/kafka-verifiable-producer.sh --broker-list <broker-list:9092> --topic test_topic_increasing_p2 --message-create-time <epoch argument> --acks -1 --max-messages 100

the "<epoch argument>" for --message-create-time doesn't take a 13 digit long like 1529656934000. 

The error message:

verifiable-producer: error: argument --message-create-time: could not convert '1529656934000' to Integer (For input string: "1529656934000")

 

When you provide a 10 digit (1529656934) epoch for the argument it does work but this leads to your topic being cleaned up in a few minutes since the retention time is expired.

 

The error seems to be obvious since VerifiableProducer.java has:

        Long createTime = (long) res.getInt("createTime");

when parsing the argument. This should be taken as a Long instead.
~~~~

---

## KAFKA-7168: Broker shutdown during SSL handshake may be handled as handshake failure

https://issues.apache.org/jira/browse/KAFKA-7168

Given fix versions: 2.0.0
JIRA affects (masked from the system): 1.0.2, 1.1.1, 2.0.0

- `KAFKA-7168@1.1.1`: config 1.1.1, metadata answer **affected** (listed_affected)
- `KAFKA-7168@1.0.1`: config 1.0.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
If broker is shutdown while SSL handshake of a client connection is in progress, the client may process the resulting SSLException as a non-retriable handshake failure rather than a retriable I/O exception. This can cause streams applications to fail during rolling restarts.

Exception stack trace:

{quote}
org.apache.kafka.common.errors.SslAuthenticationException: SSL handshake failed
Caused by: javax.net.ssl.SSLException: Received close_notify during handshake
        at sun.security.ssl.Alerts.getSSLException(Alerts.java:208)
        at sun.security.ssl.SSLEngineImpl.fatal(SSLEngineImpl.java:1639)
        at sun.security.ssl.SSLEngineImpl.fatal(SSLEngineImpl.java:1607)
        at sun.security.ssl.SSLEngineImpl.recvAlert(SSLEngineImpl.java:1752)
        at sun.security.ssl.SSLEngineImpl.readRecord(SSLEngineImpl.java:1068)
        at sun.security.ssl.SSLEngineImpl.readNetRecord(SSLEngineImpl.java:890)
        at sun.security.ssl.SSLEngineImpl.unwrap(SSLEngineImpl.java:764)
        at javax.net.ssl.SSLEngine.unwrap(SSLEngine.java:624)
        at org.apache.kafka.common.network.SslTransportLayer.handshakeUnwrap(SslTransportLayer.java:465)
        at org.apache.kafka.common.network.SslTransportLayer.handshake(SslTransportLayer.java:266)
        at org.apache.kafka.common.network.KafkaChannel.prepare(KafkaChannel.java:88)
        at org.apache.kafka.common.network.Selector.pollSelectionKeys(Selector.java:474)
        at org.apache.kafka.common.network.Selector.poll(Selector.java:412)
        at org.apache.kafka.clients.NetworkClient.poll(NetworkClient.java:460)
        at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:258)
        at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:230)
        at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:206)
        at org.apache.kafka.clients.consumer.internals.AbstractCoordinator.ensureCoordinatorReady(AbstractCoordinator.java:219)
        at org.apache.kafka.clients.consumer.internals.AbstractCoordinator.ensureCoordinatorReady(AbstractCoordinator.java:205)
        at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.poll(ConsumerCoordinator.java:284)
        at org.apache.kafka.clients.consumer.KafkaConsumer.pollOnce(KafkaConsumer.java:1146)
        at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:1111)
        at org.apache.kafka.streams.processor.internals.StreamThread.pollRequests(StreamThread.java:848)
        at org.apache.kafka.streams.processor.internals.StreamThread.runOnce(StreamThread.java:805)
        at org.apache.kafka.streams.processor.internals.StreamThread.runLoop(StreamThread.java:771)
        at org.apache.kafka.streams.processor.internals.StreamThread.run(StreamThread.java:741)
{quote}
 
~~~~

---

## KAFKA-7225: Kafka Connect ConfigProvider not invoked before validation

https://issues.apache.org/jira/browse/KAFKA-7225

Given fix versions: 2.0.1, 2.1.0
JIRA affects (masked from the system): 2.0.0

- `KAFKA-7225@2.0.0`: config 2.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-7225@1.1.1`: config 1.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
When trying to register a JDBC connector with externalised secrets (e.g. connection.password) the validation fails and the endpoint returns a 500. I think that the problem is that the config transformer is not being invoked before the validation so trying to exercise the credentials against the database fails. I have checked that publishing the connector configuration directly to the connect-config topic to skip the validation and restarting the server is enough to get the connector working so that confirms that we are just missing to call config transformer before validating the connector. Please let me know if you need further information.

I'm happy to open a PR to address this issue given that I think that this is easy enough to fix for a new contributor to the project. So please feel free to assign the resolution of the bug to me.
~~~~

### Comments (6)

1.

~~~~
[~rayokota] I'm quite disappointed with your behaviour. I explicitly asked for this issue to be assigned to me. I think that this kind of behaviour is not only inelegant but also damages the open source collaboration model. 
~~~~

2.

~~~~
Hi [~nachomdo], thanks for finding and logging this issue.

Oh, I'm very sorry.  When you said feel free to assign to you, I misread it as you would be happy to look into it if no one else would.  Again, I apologize I that I misunderstood you.
~~~~

3.

~~~~
If you want, I can still close my PR so you can look into it.  Would that be ok with you?
~~~~

4.

~~~~
No worries. Thanks for fixing it so quickly! 
~~~~

5.

~~~~
Thank you! no need to close your PR, there are plenty of bugs to fix :) I hope to have more luck next time 
~~~~

6.

~~~~
Thanks [~nachomdo]!  Again, I really appreciate your feedback. :)
~~~~

---

## KAFKA-7231: NetworkClient.newClientRequest() ignores custom request timeout in favor of the default

https://issues.apache.org/jira/browse/KAFKA-7231

Given fix versions: 2.0.1, 2.1.0
JIRA affects (masked from the system): 2.0.0

- `KAFKA-7231@2.0.0`: config 2.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-7231@1.1.1`: config 1.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
The below code in {{org.apache.kafka.clients.KafkaClient}} is not passing in the provided {{requestTimeoutMs}} -- it is ignoring it in favor of the {{defaultRequestTimeoutMs}} value.
{code:java}
@Override
public ClientRequest newClientRequest(String nodeId,
                                      AbstractRequest.Builder<?> requestBuilder,
                                      long createdTimeMs,
                                      boolean expectResponse,
                                      int requestTimeoutMs,
                                      RequestCompletionHandler callback) {
     return new ClientRequest(nodeId, requestBuilder, correlation++, clientId, createdTimeMs, expectResponse,
            defaultRequestTimeoutMs, callback);
}
{code}

This is an easy fix, but the impact of fixing it is difficult to quantify.  Clients that set a custom timeout are getting the default timeout -- fixing this will suddenly cause the custom timeout to take effect.

~~~~

### Comments (1)

1.

~~~~
Ouch. I think the only place we use this is in the consumer when we override the join group timeout. Using the default in this case could cause problems when a consumer is first joining the group. In general retrying the JoinGroup is safe, but it causes problems when a member first joins the group since retries cause new members to be added.
~~~~

---

## KAFKA-7250: Kafka-Streams-Scala DSL transform shares transformer instance

https://issues.apache.org/jira/browse/KAFKA-7250

Given fix versions: 2.0.1, 2.1.0
JIRA affects (masked from the system): 2.0.0

- `KAFKA-7250@2.0.0`: config 2.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-7250@1.1.1`: config 1.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
The new Kafka Streams Scala DSL provides transform function with following signature

{{def transform[K1, V1](transformer: Transformer[K, V, (K1, V1)], stateStoreNames: String*): KStream[K1, V1]}}

the provided 'transformer' (will refer to it as scala-transformer)  instance is than used to derive java Transformer instance and in turn a TransformerSupplier that is passed to the underlying java DSL. However that causes all the tasks to share the same instance of the scala-transformer. This introduce all sort of issues. The simplest way to reproduce is to implement simplest transformer of the following shape:

{{.transform(new Transformer[String, String, (String, String)] {}}

    var context: ProcessorContext = _

{{  def init(pc: ProcessorContext) = \{ context = pc}}}

{{  def transform(k: String, v: String): (String, String) = {}}

        context.timestamp() 

        ...

{{  }}}{{})}}

the call to timestmap will die with exception "This should not happen as timestamp() should only be called while a record is processed" due to record context not being set - while the update of record context was actually performed, but due to shared nature of the scala-transformer the local reference to the processor context is pointing to the one of the last initialized task rather than the current task. 

The solution is to accept a function in following manner: 

def transform[K1, V1](getTransformer: () => Transformer[K, V, (K1, V1)], stateStoreNames: String*): KStream[K1, V1]

 or TransformerSupplier - like the transformValues DSL function does.
~~~~

### Comments (7)

1.

~~~~
I looked at the code and can confirm it is the issue:

{code}
def transform[K1, V1](transformer: Transformer[K, V, (K1, V1)],
    stateStoreNames: String*): KStream[K1, V1] = {
    val transformerSupplierJ: TransformerSupplier[K, V, KeyValue[K1, V1]] = new TransformerSupplier[K, V, KeyValue[K1, V1]] {
      override def get(): Transformer[K, V, KeyValue[K1, V1]] = {
        new Transformer[K, V, KeyValue[K1, V1]] {
          override def transform(key: K, value: V): KeyValue[K1, V1] = {
            transformer.transform(key, value) match {
              case (k1, v1) => KeyValue.pair(k1, v1)
              case _ => null
            }
          }

          override def init(context: ProcessorContext): Unit = transformer.init(context)

          override def close(): Unit = transformer.close()
        }
      }
    }
    inner.transform(transformerSupplierJ, stateStoreNames: _*)
  }
{code}

The API itself is actually buggy: we should not take a Transform object, but a TransformSupplier as we did in transformValues call.
~~~~

2.

~~~~
[~michald] Do you want to submit a PR to fix this issue?
~~~~

3.

~~~~
Absolutely, no problem



~~~~

4.

~~~~
Great! I've assigned you to the ticket, please feel free to follow the PR guidelines: https://cwiki.apache.org/confluence/display/KAFKA/Contributing+Code+Changes#ContributingCodeChanges-PullRequest
~~~~

5.

~~~~
{{[~guozhang] it seems like the API is really inconsistent:}}
{code:java}
def transform[K1, V1](transformer: Transformer[K, V, (K1, V1)], stateStoreNames: String*): KStream[K1, V1]{code}
versus:
{code:java}
def transformValues[VR](valueTransformerSupplier: ValueTransformerSupplier[V, VR],stateStoreNames: String*): KStream[K, VR]
def transformValues[VR](valueTransformerSupplier: ValueTransformerWithKeySupplier[K, V, VR], stateStoreNames: String*): KStream[K, VR]{code}
versus
{code:java}
def process(processorSupplier: () => Processor[K, V], stateStoreNames: String*): Unit{code}

Personally, I think the `process`  is the best option (and it matches all other operations like map, join, aggregate etc.)

I tried a quick implementation but there are some issues with transformValues due to type erasure so I just did PR for the transform as it is currently not very usable, while  I will go over the API and try to make it a bit more consistent later... 

 
~~~~

6.

~~~~
Ack, thanks!
~~~~

7.

~~~~
I've created [https://github.com/apache/kafka/pull/5481] to make transform expect a TransformerSupplier instead of a Function[Transformer]. This is a super minor change, but it does move us toward having one pattern for these methods instead of two.

( I started the PR because I thought there was a way to fix the bug without breaking the API, but instead my dreams were broken. Nevertheless, I think just moving toward Supplier is still beneficial. )
~~~~

---

## KAFKA-7296: Producer should handle COORDINATOR_LOADING error in TxnOffsetCommit

https://issues.apache.org/jira/browse/KAFKA-7296

Given fix versions: 2.0.1
JIRA affects (masked from the system): 2.0.0

- `KAFKA-7296@2.0.0`: config 2.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-7296@1.1.1`: config 1.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
The producer should check for the COORDINATOR_LOADING error when handling the TxnOffsetCommit response. We fixed the logic in GroupCoordinator to correctly check for offset loading in https://github.com/apache/kafka/pull/4788. Prior to this fix, it was not possible to see this error, so we were able to get away with not having the check.
~~~~

---

## KAFKA-7304: memory leakage in org.apache.kafka.common.network.Selector

https://issues.apache.org/jira/browse/KAFKA-7304

Given fix versions: 2.0.1
JIRA affects (masked from the system): 1.1.0, 1.1.1

- `KAFKA-7304@1.1.0`: config 1.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-7304@1.0.2`: config 1.0.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 1.1.1, 1.1, 1.1.0, 2.0, 2.2

### Description

~~~~
We are testing secured writing to kafka through ssl. Testing at small scale, ssl writing to kafka was fine. However, when we enabled ssl writing at a larger scale (>40k clients write concurrently), the kafka brokers soon hit OutOfMemory issue with 4G memory setting. We have tried with increasing the heap size to 10Gb, but encountered the same issue. 

We took a few heap dumps , and found that most of the heap memory is referenced through org.apache.kafka.common.network.Selector objects.  There are two Channel maps field in Selector. It seems that somehow the objects is not deleted from the map in a timely manner. 

One observation is that the memory leak seems relate to kafka partition leader changes. If there is broker restart etc. in the cluster that caused partition leadership change, the brokers may hit the OOM issue faster. 

{code}
    private final Map<String, KafkaChannel> channels;
    private final Map<String, KafkaChannel> closingChannels;
{code}

Please see the  attached images and the following link for sample gc analysis. 

http://gceasy.io/my-gc-report.jsp?p=c2hhcmVkLzIwMTgvMDgvMTcvLS1nYy5sb2cuMC5jdXJyZW50Lmd6LS0yLTM5LTM0


the command line for running kafka: 
{code}
java -Xms10g -Xmx10g -XX:NewSize=512m -XX:MaxNewSize=512m -Xbootclasspath/p:/usr/local/libs/bcp -XX:MetaspaceSize=128m -XX:+UseG1GC -XX:MaxGCPauseMillis=25 -XX:InitiatingHeapOccupancyPercent=35 -XX:G1HeapRegionSize=16M -XX:MinMetaspaceFreeRatio=25 -XX:MaxMetaspaceFreeRatio=75 -XX:+PrintGCDetails -XX:+PrintGCDateStamps -XX:+PrintTenuringDistribution -Xloggc:/var/log/kafka/gc.log -XX:+UseGCLogFileRotation -XX:NumberOfGCLogFiles=40 -XX:GCLogFileSize=50M -Djava.awt.headless=true -Dlog4j.configuration=file:/etc/kafka/log4j.properties -Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote.port=9999 -Dcom.sun.management.jmxremote.rmi.port=9999 -cp /usr/local/libs/*  kafka.Kafka /etc/kafka/server.properties
{code}

We use java 1.8.0_102, and has applied a TLS patch on reducing X509Factory.certCache map size from 750 to 20. 

{code}
java -version
java version "1.8.0_102"
Java(TM) SE Runtime Environment (build 1.8.0_102-b14)
Java HotSpot(TM) 64-Bit Server VM (build 25.102-b14, mixed mode)
{code}
~~~~

### Comments (38)

1.

~~~~
Was there any exception in broker log ?

thanks
~~~~

2.

~~~~
[~yuzhihong@gmail.com]  There was no exception in server.log before the broker hit frequent full gc. There was various errors in the log after the broker ran into full gc. But i think that those exceptions are not relevant to the root cause. 
~~~~

3.

~~~~
Looking at the close() method, I don't see where the channels in closingChannels are closed (if the given id is found in channels Map).
{code}
diff --git a/clients/src/main/java/org/apache/kafka/common/network/Selector.java b/clients/src/main/java/org/apache/kafka/common/network/Selector.java
index 7e32509..2164a40 100644
--- a/clients/src/main/java/org/apache/kafka/common/network/Selector.java
+++ b/clients/src/main/java/org/apache/kafka/common/network/Selector.java
@@ -320,6 +320,10 @@ public class Selector implements Selectable, AutoCloseable {
         }
         sensors.close();
         channelBuilder.close();
+        for (Map.Entry<String, KafkaChannel> entry : this.closingChannels.entrySet()) {
+            doClose(entry.getValue(), false);
+        }
+        this.closingChannels.clear();
     }

     /**
{code}
I wonder if the above change would fix the leakage.
~~~~

4.

~~~~
[~yuzhihong@gmail.com] The channel was closed in `doClose`.
~~~~

5.

~~~~
You're seeing this with Kafka 1.1.1? There was a memory leak in the Selector, but it should have been fixed by 1.1.1.
~~~~

6.

~~~~
[~ijuma] We have an internal build that cherry-picks 1.1.1 changes.  I might miss some fixes. 

https://github.com/apache/kafka/commits/1.1/clients/src/main/java/org/apache/kafka/common/network/Selector.java shows that there were only two Selector.java related changes after 1.1.0 release date that was March 23rd. 

 Do you mean the fix for https://issues.apache.org/jira/browse/KAFKA-6529 ? kafka 1.1.0 has included that change. 
~~~~

7.

~~~~
[~rsivaram], [~hachikuji]  could you share any insights on this? thanks! 
~~~~

8.

~~~~
By running test suite with additional logging, I saw the following:
{code}
org.apache.kafka.common.network.SslSelectorTest > testMuteOnOOM STANDARD_OUT
    There are 1 entries in closingChannels
{code}
This shows the log I added:

https://pastebin.com/CSGUXM45
~~~~

9.

~~~~
Yes, I was thinking of KAFKA-6529.
~~~~

10.

~~~~
I raised the priority of this issue until we know what's going on. [~yuzhihong@gmail.com], that's interesting. The thing we need to figure out is why we have a connection in both `channels` and `closingChannels`. It should be in one or the other and we do the right thing if that is the case. [~yuyang08], do you see any errors in the broker logs?
~~~~

11.

~~~~
Through a bit more additional logging, here is what happens to testMuteOnOOM.
There are two channels added to closingChannels:
{code}
    adding org.apache.kafka.common.network.KafkaChannel@334b860c for clientX
    adding org.apache.kafka.common.network.KafkaChannel@334b860d for clientY
{code}
Later, when Selector.close() is called by tearDown, the channel for clientY is still in closingChannels :
{code}
    There are 1 entries in closingChannels
    org.apache.kafka.common.network.KafkaChannel@334b860d
{code}
This is because Selector#clear() is not called for the second Channel added to {{closingChannels}}
My change above would close the channels left in closingChannels, preventing memory leak.
~~~~

12.

~~~~
Patch v4 adds an assertion for the count of Channels in closingChannels in SslSelectorTest#tearDown .
~~~~

13.

~~~~
Without the fix, the test would fail with:
{code}
org.apache.kafka.common.network.SslSelectorTest > testMuteOnOOM FAILED
    java.lang.AssertionError: expected:<0> but was:<1>
        at org.junit.Assert.fail(Assert.java:88)
        at org.junit.Assert.failNotEquals(Assert.java:834)
        at org.junit.Assert.assertEquals(Assert.java:645)
        at org.junit.Assert.assertEquals(Assert.java:631)
        at org.apache.kafka.common.network.SslSelectorTest.tearDown(SslSelectorTest.java:79)
{code}
~~~~

14.

~~~~
Selector has {{lowMemThreshold}} which used to determine iteration order.

I wonder if we can make use of the threshold in determining when out of memory error is going to happen and take corresponding actions.
~~~~

15.

~~~~
In patch v7, I added some assertion to SslTransportLayerTest#teardown

The test passes.

Digging some more ...
~~~~

16.

~~~~
Thanks for looking into this, [~yuzhihong@gmail.com]!  We also did more experiments on our side with various settings. Based on the initial experiment, it seems to me that your patch earlier has fixed the resource leakage in the closing channel.  Meanwhile with >40k concurrent ssl connections, sometimes the brokers may still run into OOM issue as the connections are not closed on time. Currently I am experimenting with increased heap size. Will report back to the thread if we have any findings. 
~~~~

17.

~~~~
Thanks for the feedback, Yu.

There are a few {{log.error()}} calls in the patch.
If you happen to see any of those logs from broker, please let us know.
~~~~

18.

~~~~
I am looking at SaslSslAdminClientIntegrationTest .

It seems some getter methods need to be added in SocketServer, KafkaServer, Processor before assertion can be made on Selector in the test.
~~~~

19.

~~~~
After more experiments, we currently think that the issue is caused by too many idle ssl connections that are not closed on time. 

I set up a test cluster of 24 brokers using d2.8xlarge instances, allocated 32gb for kafka process heap space, and have ~40k clients writes to a test topic on this cluster. The following graph shows the jvm heap usage and gc activity in the past 24 hours or so. The cluster ran fine with low heap usage and low cpu usage.  However, the heap usage and the cpu usage of brokers increased sharply when we added or terminated brokers in this cluster (for broker termination, there was no topic partitions allocated on those terminated nodes).  

http://gceasy.io/my-gc-report.jsp?p=c2hhcmVkLzIwMTgvMDgvMjgvLS1nYy5sb2cuMC5jdXJyZW50Lmd6LS01LTQzLTU=

http://gceasy.io/my-gc-report.jsp?p=c2hhcmVkLzIwMTgvMDgvMjgvLS1nYy5sb2cuMC5jdXJyZW50Lmd6LS03LTYtMzU=

Sometimes the cluster can be recovered by turning off the ssl writing traffic to the cluster, letting the broker to garbage collect the objects in the old gen, and resuming the ssl writing traffic.  Sometimes the cluster still  could not recover fully due to dramatic increase of heap size and high cpu usage when we turned on the ssl writing traffic again. 
~~~~

20.

~~~~
One potential cause for the delayed closing of idle connections is that ConsumerNetworkClient#poll does the following before calling {{client.poll}} (leading to selector.poll where selector.closingChannels is checked):
{code}
            long pollDelayMs = trySend(timer.currentTimeMs());
{code}
It seems when selector.closingChannels grows to certain size, we should proactively release the KafkaChannel's inside selector.closingChannels
~~~~

21.

~~~~
[~yuyang08]:
Please confirm that the gap between the following two metrics kept getting bigger:
{code}
            this.connectionClosed = sensor("connections-closed:" + tagsSuffix);

            this.connectionCreated = sensor("connections-created:" + tagsSuffix);
{code}
~~~~

22.

~~~~
[~yuzhihong@gmail.com] I applied https://issues.apache.org/jira/secure/attachment/12937151/7304.v7.txt  to our test cluster and did more experiments yesterday. We did not observed channel closing/removal related log messages that are added to the patch.  I took another memory dump on a test host. This time the memory analyzer reports memory suspects leakage in `sun.security.ssl.SSLSessionImpl`. 


~~~~

23.

~~~~
1.8.0_102 was old .

Is the TLS patch integrated in newer JDK ?

I wonder upgrading JDK would help with reducing leak of SSLSessionImpl
~~~~

24.

~~~~
We experimented with 1.8.0_171, and did not see obvious improvements on reducing ssl related memory usage etc.  We also experimented with jdk 10.0.2. Currently we are see two issues with ssl writing to kafka: 1) there is some potential resource leakage in kafka.  the leakage might have already been fixed with  [~yuzhihong@gmail.com]'s patch.  2)  kafka may get high cpu usage when a large number of clients writes to kafka through ssl channels.  see https://issues.apache.org/jira/browse/KAFKA-7364 for details. This seems to be related to inefficiency in jdk ssl related implementation.  Switching to use https://github.com/netty/netty-tcnative to handle ssl handshake might be helpful. 
~~~~

25.

~~~~
[~yuyang08] Thanks for reporting this issue. Do you see an actual difference with the patch from [~yuzhihong@gmail.com]? I don't see how the patch helps since the changes are only in {{Selector.close()}}. When a broker goes down, with a very large number of clients, I imagine the connections made for metadata requests could create a load spike on other brokers. What is your {{connections.max.idle.ms}} for brokers? Just to confirm - all the brokers are up for longer than this after a broker restart/leader change, but don't see any drop in memory usage? Also, the metrics attached show a large number of failed authentications, is that expected? I wasn't sure if the metrics correspond to the heap objects in any of the attached screenshots (because the number of active connections in the metrics is quite low).
~~~~

26.

~~~~
[~rsivaram]  Thanks for looking into the issue!   We are still evaluating whether Ted's patch makes a difference. I am testing ssl writing at a smaller scale now. gceasy reports that some brokers run with jdk 10.0.2 + kafka 2.0 with Ted's patch has memory leakage: http://gceasy.io/my-gc-report.jsp?p=c2hhcmVkLzIwMTgvMDkvMy8tLWdjLmxvZy5nei0tMTktMS01.  Meanwhile  brokers running with jdk 1.8u172 seems fine.  http://gceasy.io/my-gc-report.jsp?p=c2hhcmVkLzIwMTgvMDkvMy8tLWdjLmxvZy4xLmN1cnJlbnQuZ3otLTE5LTktMjc= . 

We used the default value (10 minutes) for `connections.max.idle.ms`.  I also tried to set `connections.max.idle.ms` to 1 minute and 30 seconds. Setting a shorter connections.max.idle.ms did not help. 

When we did experiments with broker restart, all brokers that were not restarted were up for longer than `connections.max.idle.ms`.  The heap memory usages for those brokers was not drop. 

The failed authentications should not be expected. It is not clear to me how that happened. 
 
~~~~

27.

~~~~
[~yuyang08] Thank you. Would it be possible to share the heap dump from an OOM (either the original one reported or a test scenario that resulted in OOM)? I am hoping it would compress well, but not sure if it will be possible to upload on the JIRA. The difference in memory usage between jdk 10.0.2 and 1.8 may be GC timing, since the peak usage is much lower than the allocated heap. But it will be good if you can generate a heap dump with live objects and check if the number of KafkaChannels referenced from Selector is much higher than expected.

[~ijuma] You mentioned in a comment: "The thing we need to figure out is why we have a connection in both `channels` and `closingChannels`. It should be in one or the other and we do the right thing if that is the case." Where did you see the same channel in both?

~~~~

28.

~~~~
[~yuyang08] We came across a similar issue with large number of clients for which we had a heap dump. There was no leak in `Selector#closingChannels` which were mostly empty, but there were a large number of channels in `Selector#channels`, mainly due to client reconnections. I have submitted two PRs to reduce memory pressure in this type of scenario:
 * [https://github.com/apache/kafka/pull/5713]
 * [https://github.com/apache/kafka/pull/5712]

It will be good to know if these help with your scenario. We are also considering limiting the number of new connections processed in each iteration by the broker to improve fairness between processing of new and existing connections, but we need to do more testing for that before submitting a PR.
~~~~

29.

~~~~
Thanks [~rsivaram]!  We will try these fixes and let you know the result. 
~~~~

30.

~~~~
[~rsivaram] Tested with latest kafka 2.0 branch code, using d2.2x instances, 16g max heap size for kafka process, and ~20k producers. Using 16gb heap size, we did not see frequent gc. But at the same time, we still hit the high cpu usage issue that is documented in KAFKA-7364. Did you see high cpu usage related issue in your case?

The following is our ssl related kafka setting:
{code:java}
listeners=PLAINTEXT://:9092,SSL://:9093
security.inter.broker.protocol=PLAINTEXT
ssl.client.auth=required
ssl.enabled.protocols=TLSv1.2,TLSv1.1,TLSv1
ssl.endpoint.identification.algorithm=HTTPS
ssl.key.password=key_password
ssl.keystore.location=keystore_location
ssl.keystore.password=keystore_password
ssl.keystore.type=JKS
ssl.secure.random.implementation=SHA1PRNG
ssl.truststore.location=truststore_path
ssl.truststore.password=truststore_password
ssl.truststore.type=JKS
 {code}

The following is the gc chart on a broker using kafka 2.0 binary with commits up to [https://github.com/apache/kafka/commit/74c8b831472ed07e10ceda660e0e504a6a6821c4]

[http://gceasy.io/my-gc-report.jsp?p=c2hhcmVkLzIwMTgvMDkvMzAvLS1nYy5sb2cuMC5jdXJyZW50Lmd6LS01LTM3LTQ3]

!Screen Shot 2018-09-29 at 10.38.12 PM.png|width=500!

The following is the cpu usage chart of our cluster. The cpu usage jumped to almost 100% after enabling TLS-based writing to the cluster. 

!Screen Shot 2018-09-29 at 10.38.38 PM.png|width=500!

There is another issue that we saw with the following setting. See KAFKA-7450 for details. 
{code}
listeners=PLAINTEXT://:9092,SSL://:9093
security.inter.broker.protocol=SSL
{code}
~~~~

31.

~~~~
[~yuyang08] We saw the OOM during a load test, so CPU usage would have been high anyway. With a large number of clients producing a large amount of traffic, we would expect high CPU usage with SSL. We haven't done any comparisons with other SSL implementations like OpenSSL though to see if we can improve on this.
~~~~

32.

~~~~
[~rsivaram] This is marked as "Critical" for 2.2 release but it seems there was no progress on the PR since September. What is the current status?
~~~~

33.

~~~~
[~mjsax] We have fixed all the known memory leak issues. [~yuyang08] Can we reduce the priority of this JIRA since the only remaining issue is high CPU with SSL?
~~~~

34.

~~~~
[~rsivaram] sure.  I have reduced te priority of this ticket to "major". 
~~~~

35.

~~~~
Thanks [~rsivaram] and [~yuyang08]!
~~~~

36.

~~~~
Hi,Yu Yang..Is there any solution to this memory leak problem in kafka1.x.
~~~~

37.

~~~~
Given that this Jira is for reporting memory issues and those were fixed, does it make sense to either close this or explicitly rename/redo the description to mention it's tracking high CPU with SSL?

cc [~rsivaram] [~yuyang08]
~~~~

38.

~~~~
Marking as fixed since the leaks were fixed.
~~~~

---

## KAFKA-7482: LeaderAndIsrRequest should be sent to the shutting down broker

https://issues.apache.org/jira/browse/KAFKA-7482

Given fix versions: 2.1.0
JIRA affects (masked from the system): 1.1.0, 2.0.0

- `KAFKA-7482@1.1.0`: config 1.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-7482@1.0.2`: config 1.0.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 1.1, 2.1

### Description

~~~~
We introduced a regression in KAFKA-5642 in 1.1. Before 1.1, during a controlled shutdown, the LeaderAndIsrRequest is sent to the shutting down broker to inform it that it's no longer the leader for partitions whose leader have been moved. After 1.1, such LeaderAndIsrRequest is no longer sent to the shutting down broker. This can delay the time for the client to find out the new leader.
~~~~

### Comments (1)

1.

~~~~
merged to 2.1 and trunk
~~~~

---

## KAFKA-7607: NetworkClientUtils.sendAndReceive can take a long time to return during shutdown

https://issues.apache.org/jira/browse/KAFKA-7607

Given fix versions: 1.1.2, 2.0.2, 2.1.1
JIRA affects (masked from the system): 2.0.0

- `KAFKA-7607@2.0.0`: config 2.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-7607@1.1.1`: config 1.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
If a RequestSendThread is shut down while waiting on the underlying Selector to return from a select() call, the Selector will swallow the interrupt, wake up and return immediately. NetworkClientUtils.sendAndReceive will then potentially re-poll the client, forcing the thread shutdown to wait for the request to complete. We should check the thread interrupt status before re-polling the client to prevent this delay.
~~~~

### Comments (3)

1.

~~~~
Is this related to KAFKA-7576? cc [~rsivaram]
~~~~

2.

~~~~
[~ijuma] Yes, it is a very similar pattern of code to the one used by replica fetcher. With the changes in KAFKA-7576, we should be able to fix this one as well by invoking networkClient.initiateClose() when shutdown is initiated for RequestSendThread. I will update that PR.
~~~~

3.

~~~~
Fixed under KAFKA-7576.
~~~~

---

## KAFKA-7873: KafkaBasedLog's consumer should always seek to beginning when starting

https://issues.apache.org/jira/browse/KAFKA-7873

Given fix versions: 2.0.2, 2.1.1, 2.2.0
JIRA affects (masked from the system): 2.1.0

- `KAFKA-7873@2.1.0`: config 2.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-7873@2.0.1`: config 2.0.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
KafkaBasedLog expects that callers set the `group.id` for the consumer configuration, and does not itself set the `group.id` if the caller does not explicitly do so. However, [KIP-289|https://cwiki.apache.org/confluence/display/KAFKA/KIP-289%3A+Improve+the+default+group+id+behavior+in+KafkaConsumer] changed the default for the `group.id` from a blank string to be null, which changes how KafkaBasedLog behaves when no `group.id` is set, and it actually deprecates and issues a warning when no `group.id` is specified.

When KafkaBasedLog starts up, it should always start from the beginning of the topic and consume to the end. The consumer's logic for where to start is always:
# explicit seek
# committed offset (skipped if group.id is null)
# auto reset behavior

and currently Connect does not explicitly seek to the beginning and instead relies upon `auto.offset.reset=earliest`. However, if a `group.id` is specified *ant* there are committed offsets, then the consumer will start from the committed offsets rather than from the beginning. If a 'group.id' is not specified, then the auto reset behavior should work.

However, to avoid the warning and possible exception when no `group.id` is specified, KafkaBasedLog should always call {{consumer.seekToBeginning()}} during startup. 
~~~~

---

## KAFKA-8198: KStreams testing docs use non-existent method "pipe"

https://issues.apache.org/jira/browse/KAFKA-8198

Given fix versions: 1.1.0, 2.0.0, 2.1.0, 2.2.0, 2.3.0, 2.4.0
JIRA affects (masked from the system): 1.1.1, 2.0.1, 2.1.1, 2.2.0

- `KAFKA-8198@2.0.1`: config 2.0.1, metadata answer **affected** (listed_affected)
- `KAFKA-8198@1.0.2`: config 1.0.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 1.1, 2.3, 2.2, 2.1, 2.0

### Description

~~~~
In [the testing docs for KStreams|https://kafka.apache.org/20/documentation/streams/developer-guide/testing.html], we use the following code snippet:
{code:java}
ConsumerRecordFactory<String, Integer> factory = new ConsumerRecordFactory<>("input-topic", new StringSerializer(), new IntegerSerializer());
testDriver.pipe(factory.create("key", 42L));
{code}
We should correct the docs to use the pipeInput method.
~~~~

### Comments (2)

1.

~~~~
I can confirm that ever since 1.1 when we add the KIP, the API was `pipeInput` already, so this doc fix should go all the way back to 1.1 branch.
~~~~

2.

~~~~
cherry-picked to 2.3, 2.2, 2.1, 2.0 and 1.1
~~~~

---

## KAFKA-8670: kafka-topics.sh shows IllegalArgumentException when describing all topics if no topics exist on the cluster

https://issues.apache.org/jira/browse/KAFKA-8670

Given fix versions: 2.3.1, 2.4.0
JIRA affects (masked from the system): 2.2.0, 2.2.1, 2.3.0

- `KAFKA-8670@2.2.1`: config 2.2.1, metadata answer **affected** (listed_affected)
- `KAFKA-8670@2.1.1`: config 2.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
When trying to describe all  the kafka-topics.sh utility, a user would run kafka-topics.sh --describe without passing a --topic option. If there are no topics on the cluster, Kafka returns an error with IllegalArgumentException.
{code:java}
./kafka-topics.sh --zookeeper 172.16.7.230:2181,172.16.17.27:2181,172.16.10.89:2181 --describe
Error while executing topic command : Topics in [] does not exist
[2019-07-07 03:33:15,288] ERROR java.lang.IllegalArgumentException: Topics in [] does not exist
at kafka.admin.TopicCommand$.kafka$admin$TopicCommand$$ensureTopicExists(TopicCommand.scala:416)
at kafka.admin.TopicCommand$ZookeeperTopicService.describeTopic(TopicCommand.scala:332)
at kafka.admin.TopicCommand$.main(TopicCommand.scala:66)
at kafka.admin.TopicCommand.main(TopicCommand.scala)
(kafka.admin.TopicCommand$)
{code}
 
 If no --topic option is passed to the command, and there are no topics on the cluster, the command should not fail, rather have empty output.
~~~~

### Comments (2)

1.

~~~~
This issue is distinct from https://issues.apache.org/jira/browse/KAFKA-8053 which is about Kafka's error message being confusing when --describe is called with a --topic argument, but there are no topics on the cluster.

The distinction here is that this ticket addresses the case where no --topic is passed, while the other focuses on a better error message when --topic is indeed passed, but there are no topics on the cluster.
~~~~

2.

~~~~
This bug was introduced as part of this commit

[https://github.com/apache/kafka/commit/55334453a561646b303e7de961e5990345effc15]

 

I have written a fix for this issue. Will be publishing it soon.
~~~~

---

## KAFKA-8678: LeaveGroup request getErrorResponse is incorrect on throttle time and error setting

https://issues.apache.org/jira/browse/KAFKA-8678

Given fix versions: 2.2.2, 2.3.1
JIRA affects (masked from the system): 2.2.0, 2.3.0

- `KAFKA-8678@2.2.0`: config 2.2.0, metadata answer **affected** (listed_affected)
- `KAFKA-8678@2.1.1`: config 2.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
[https://github.com/apache/kafka/pull/6188] accidentally changed the version of setting throttle time from v1 to v2, and neglected the passed in exception. We should fix this change.
~~~~

---

## KAFKA-8764: LogCleanerManager endless loop while compacting/cleaning segments

https://issues.apache.org/jira/browse/KAFKA-8764

Given fix versions: 2.2.3, 2.3.2, 2.4.1, 2.5.0
JIRA affects (masked from the system): 2.2.1, 2.3.0, 2.4.0

- `KAFKA-8764@2.3.0`: config 2.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-8764@2.2.0`: config 2.2.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.2.1, 1.0, 3.8, 2.4.0

### Description

~~~~
{{LogCleanerManager stuck in endless loop while clearing segments for one partition resulting with many log outputs and heavy disk read/writes/IOPS.}}

 

Issue appeared on follower brokers, and it happens on every (new) broker if partition assignment is changed.

 

Original issue setup:
 * kafka_2.12-2.2.1 deployed as statefulset on kubernetes, 5 brokers
 * log directory is (AWS) EBS mounted PV, gp2 (ssd) kind of 750GiB
 * 5 zookeepers
 * topic created with config:
 ** name = "backup_br_domain_squad"
partitions = 36
replication_factor = 3

config = {
 "cleanup.policy" = "compact"
 "min.compaction.lag.ms" = "86400000"
 "min.cleanable.dirty.ratio" = "0.3"
}

 

 

Log excerpt:

{{[2019-08-07 12:10:53,895] INFO [Log partition=backup_br_domain_squad-14, dir=/var/lib/kafka/data/topics] Deleting segment 0 (kafka.log.Log)}}
{{[2019-08-07 12:10:53,895] INFO Deleted log /var/lib/kafka/data/topics/backup_br_domain_squad-14/00000000000000000000.log.deleted. (kafka.log.LogSegment)}}
{{[2019-08-07 12:10:53,896] INFO Deleted offset index /var/lib/kafka/data/topics/backup_br_domain_squad-14/00000000000000000000.index.deleted. (kafka.log.LogSegment)}}
{{[2019-08-07 12:10:53,896] INFO Deleted time index /var/lib/kafka/data/topics/backup_br_domain_squad-14/00000000000000000000.timeindex.deleted. (kafka.log.LogSegment)}}
{{[2019-08-07 12:10:53,964] INFO [Log partition=backup_br_domain_squad-14, dir=/var/lib/kafka/data/topics] Deleting segment 0 (kafka.log.Log)}}
{{[2019-08-07 12:10:53,964] INFO Deleted log /var/lib/kafka/data/topics/backup_br_domain_squad-14/00000000000000000000.log.deleted. (kafka.log.LogSegment)}}
{{[2019-08-07 12:10:53,964] INFO Deleted offset index /var/lib/kafka/data/topics/backup_br_domain_squad-14/00000000000000000000.index.deleted. (kafka.log.LogSegment)}}
{{[2019-08-07 12:10:53,964] INFO Deleted time index /var/lib/kafka/data/topics/backup_br_domain_squad-14/00000000000000000000.timeindex.deleted. (kafka.log.LogSegment)}}
{{[2019-08-07 12:10:54,031] INFO [Log partition=backup_br_domain_squad-14, dir=/var/lib/kafka/data/topics] Deleting segment 0 (kafka.log.Log)}}
{{[2019-08-07 12:10:54,032] INFO Deleted log /var/lib/kafka/data/topics/backup_br_domain_squad-14/00000000000000000000.log.deleted. (kafka.log.LogSegment)}}
{{[2019-08-07 12:10:54,032] INFO Deleted offset index /var/lib/kafka/data/topics/backup_br_domain_squad-14/00000000000000000000.index.deleted. (kafka.log.LogSegment)}}
{{[2019-08-07 12:10:54,032] INFO Deleted time index /var/lib/kafka/data/topics/backup_br_domain_squad-14/00000000000000000000.timeindex.deleted. (kafka.log.LogSegment)}}
{{[2019-08-07 12:10:54,101] INFO [Log partition=backup_br_domain_squad-14, dir=/var/lib/kafka/data/topics] Deleting segment 0 (kafka.log.Log)}}
{{[2019-08-07 12:10:54,101] INFO Deleted log /var/lib/kafka/data/topics/backup_br_domain_squad-14/00000000000000000000.log.deleted. (kafka.log.LogSegment)}}
{{[2019-08-07 12:10:54,101] INFO Deleted offset index /var/lib/kafka/data/topics/backup_br_domain_squad-14/00000000000000000000.index.deleted. (kafka.log.LogSegment)}}
{{[2019-08-07 12:10:54,101] INFO Deleted time index /var/lib/kafka/data/topics/backup_br_domain_squad-14/00000000000000000000.timeindex.deleted. (kafka.log.LogSegment)}}
{{[2019-08-07 12:10:54,173] INFO [Log partition=backup_br_domain_squad-14, dir=/var/lib/kafka/data/topics] Deleting segment 0 (kafka.log.Log)}}
{{[2019-08-07 12:10:54,173] INFO Deleted log /var/lib/kafka/data/topics/backup_br_domain_squad-14/00000000000000000000.log.deleted. (kafka.log.LogSegment)}}
{{[2019-08-07 12:10:54,173] INFO Deleted offset index /var/lib/kafka/data/topics/backup_br_domain_squad-14/00000000000000000000.index.deleted. (kafka.log.LogSegment)}}
{{[2019-08-07 12:10:54,173] INFO Deleted time index /var/lib/kafka/data/topics/backup_br_domain_squad-14/00000000000000000000.timeindex.deleted. (kafka.log.LogSegment)}}

 

And such log keeps repeating forever.

 

 

I've been able to extract segment files from (running) leader broker, and replicated same behaviour locally.
h1.  
h1. *Reproduction setup:*
 * start single broker kafka_2.12-2.2.1
 * create topic
 ** {{./bin/kafka-topics.sh --bootstrap-server *__BOOTSTRAP_SERVER__*:9092 --create --topic backup_br_domain_squad --partitions 1 --replication-factor 1 --config cleanup.policy=compact --config min.compaction.lag.ms=86400000 --config min.cleanable.dirty.ratio=0.3}}
 * stop broker
 * copy segment files (attachment content, under segments) to backup_br_domain_squad-0 log folder
 * rerun broker again

 

After rerun, fun starts with endless repeating logging outputs:

{{[2019-08-07 13:05:37,610] DEBUG Checking if log segment may be cleaned: log='backup_br_domain_squad-0' segment.baseOffset=0 segment.largestTimestamp=1563203503987; now - compactionLag=1565096737609; is uncleanable=false (kafka.log.LogCleanerManager$)}}
{{[2019-08-07 13:05:37,610] DEBUG Finding range of cleanable offsets for log=backup_br_domain_squad-0 topicPartition=backup_br_domain_squad-0. Last clean offset=Some(0) now=1565183137609 => firstDirtyOffset=0 firstUncleanableOffset=233 activeSegment.baseOffset=233 (kafka.log.LogCleanerManager$)}}
{{[2019-08-07 13:05:37,613] INFO Cleaner 0: Beginning cleaning of log backup_br_domain_squad-0. (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,613] INFO Cleaner 0: Building offset map for backup_br_domain_squad-0... (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,628] INFO Cleaner 0: Building offset map for log backup_br_domain_squad-0 for 1 segments in offset range [0, 233). (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,643] INFO Cleaner 0: Offset map for log backup_br_domain_squad-0 complete. (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,644] INFO Cleaner 0: Cleaning log backup_br_domain_squad-0 (cleaning prior to Wed Aug 07 13:05:22 GMT 2019, discarding tombstones prior to Thu Jan 01 00:00:00 GMT 1970)... (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,645] DEBUG Loaded index file /runtime/logs/kafka_1/backup_br_domain_squad-0/00000000000000000000.index.cleaned with maxEntries = 1310720, maxIndexSize = 10485760, entries = 0, lastOffset = 0, file position = 0 (kafka.log.OffsetIndex)}}
{{[2019-08-07 13:05:37,646] DEBUG Loaded index file /runtime/logs/kafka_1/backup_br_domain_squad-0/00000000000000000000.timeindex.cleaned with maxEntries = 873813, maxIndexSize = 10485760, entries = 0, lastOffset = TimestampOffset(-1,0), file position = 0 (kafka.log.TimeIndex)}}
{{[2019-08-07 13:05:37,647] INFO Cleaner 0: Cleaning segment 0 in log backup_br_domain_squad-0 (largest timestamp Mon Jul 15 15:11:43 GMT 2019) into 0, retaining deletes. (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,656] DEBUG Resized /runtime/logs/kafka_1/backup_br_domain_squad-0/00000000000000000000.index.cleaned to 32, position is 32 and limit is 32 (kafka.log.OffsetIndex)}}
{{[2019-08-07 13:05:37,657] DEBUG Resized /runtime/logs/kafka_1/backup_br_domain_squad-0/00000000000000000000.timeindex.cleaned to 36, position is 36 and limit is 36 (kafka.log.TimeIndex)}}
{{[2019-08-07 13:05:37,669] INFO Cleaner 0: Swapping in cleaned segment LogSegment(baseOffset=0, size=1044021) for segment(s) List(LogSegment(baseOffset=0, size=1044021)) in log Log(/runtime/logs/kafka_1/backup_br_domain_squad-0) (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,672] INFO [kafka-log-cleaner-thread-0]:}}
{{ Log cleaner thread 0 cleaned log backup_br_domain_squad-0 (dirty section = [0, 0])}}
{{ 1.0 MB of log processed in 0.1 seconds (17.2 MB/sec).}}
{{ Indexed 1.0 MB in 0.0 seconds (33.2 Mb/sec, 51.7% of total time)}}
{{ Buffer utilization: 0.0%}}
{{ Cleaned 1.0 MB in 0.0 seconds (35.6 Mb/sec, 48.3% of total time)}}
{{ Start size: 1.0 MB (231 messages)}}
{{ End size: 1.0 MB (231 messages)}}
{{ 0.0% size reduction (0.0% fewer messages)}}
{{ (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,676] DEBUG Checking if log segment may be cleaned: log='backup_br_domain_squad-0' segment.baseOffset=0 segment.largestTimestamp=1563203503987; now - compactionLag=1565096737676; is uncleanable=false (kafka.log.LogCleanerManager$)}}
{{[2019-08-07 13:05:37,677] DEBUG Finding range of cleanable offsets for log=backup_br_domain_squad-0 topicPartition=backup_br_domain_squad-0. Last clean offset=Some(232) now=1565183137676 => firstDirtyOffset=232 firstUncleanableOffset=233 activeSegment.baseOffset=233 (kafka.log.LogCleanerManager$)}}
{{[2019-08-07 13:05:37,677] INFO Cleaner 0: Beginning cleaning of log backup_br_domain_squad-0. (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,678] INFO Cleaner 0: Building offset map for backup_br_domain_squad-0... (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,680] INFO [SocketServer brokerId=1001] Created data-plane acceptor and processors for endpoint : EndPoint(null,9082,ListenerName(INSIDE_DOCKER),PLAINTEXT) (kafka.network.SocketServer)}}
{{[2019-08-07 13:05:37,680] INFO [SocketServer brokerId=1001] Created data-plane acceptor and processors for endpoint : EndPoint(null,9082,ListenerName(INSIDE_DOCKER),PLAINTEXT) (kafka.network.SocketServer)}}
{{[2019-08-07 13:05:37,681] INFO Awaiting socket connections on s0.0.0.0:9092. (kafka.network.Acceptor)}}
{{[2019-08-07 13:05:37,681] INFO Awaiting socket connections on s0.0.0.0:9092. (kafka.network.Acceptor)}}
{{[2019-08-07 13:05:37,700] INFO [SocketServer brokerId=1001] Created data-plane acceptor and processors for endpoint : EndPoint(null,9092,ListenerName(OUTSIDE_DOCKER),PLAINTEXT) (kafka.network.SocketServer)}}
{{[2019-08-07 13:05:37,700] INFO [SocketServer brokerId=1001] Created data-plane acceptor and processors for endpoint : EndPoint(null,9092,ListenerName(OUTSIDE_DOCKER),PLAINTEXT) (kafka.network.SocketServer)}}
{{[2019-08-07 13:05:37,701] INFO Awaiting socket connections on s0.0.0.0:19092. (kafka.network.Acceptor)}}
{{[2019-08-07 13:05:37,701] INFO Cleaner 0: Building offset map for log backup_br_domain_squad-0 for 1 segments in offset range [232, 233). (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,701] INFO Awaiting socket connections on s0.0.0.0:19092. (kafka.network.Acceptor)}}
{{[2019-08-07 13:05:37,702] INFO Cleaner 0: Offset map for log backup_br_domain_squad-0 complete. (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,702] INFO Cleaner 0: Cleaning log backup_br_domain_squad-0 (cleaning prior to Wed Aug 07 13:05:22 GMT 2019, discarding tombstones prior to Tue Aug 06 13:05:22 GMT 2019)... (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,703] INFO [kafka-log-cleaner-thread-0]:}}
{{ Log cleaner thread 0 cleaned log backup_br_domain_squad-0 (dirty section = [232, 232])}}
{{ 0.0 MB of log processed in 0.0 seconds (0.0 MB/sec).}}
{{ Indexed 0.0 MB in 0.0 seconds (0.3 Mb/sec, 96.2% of total time)}}
{{ Buffer utilization: 0.0%}}
{{ Cleaned 0.0 MB in 0.0 seconds (0.0 Mb/sec, 3.8% of total time)}}
{{ Start size: 0.0 MB (0 messages)}}
{{ End size: 0.0 MB (0 messages)}}
{{ NaN% size reduction (NaN% fewer messages)}}
{{ (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,707] DEBUG Checking if log segment may be cleaned: log='backup_br_domain_squad-0' segment.baseOffset=0 segment.largestTimestamp=1563203503987; now - compactionLag=1565096737707; is uncleanable=false (kafka.log.LogCleanerManager$)}}
{{[2019-08-07 13:05:37,708] DEBUG Finding range of cleanable offsets for log=backup_br_domain_squad-0 topicPartition=backup_br_domain_squad-0. Last clean offset=Some(0) now=1565183137707 => firstDirtyOffset=0 firstUncleanableOffset=233 activeSegment.baseOffset=233 (kafka.log.LogCleanerManager$)}}
{{[2019-08-07 13:05:37,708] INFO Cleaner 0: Beginning cleaning of log backup_br_domain_squad-0. (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,708] INFO Cleaner 0: Building offset map for backup_br_domain_squad-0... (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,719] INFO [SocketServer brokerId=1001] Created data-plane acceptor and processors for endpoint : EndPoint(null,19092,ListenerName(MAC_OS_DOCKER),PLAINTEXT) (kafka.network.SocketServer)}}
{{[2019-08-07 13:05:37,719] INFO [SocketServer brokerId=1001] Created data-plane acceptor and processors for endpoint : EndPoint(null,19092,ListenerName(MAC_OS_DOCKER),PLAINTEXT) (kafka.network.SocketServer)}}
{{[2019-08-07 13:05:37,721] INFO Cleaner 0: Building offset map for log backup_br_domain_squad-0 for 1 segments in offset range [0, 233). (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,722] INFO [SocketServer brokerId=1001] Started 3 acceptor threads for data-plane (kafka.network.SocketServer)}}
{{[2019-08-07 13:05:37,722] INFO [SocketServer brokerId=1001] Started 3 acceptor threads for data-plane (kafka.network.SocketServer)}}
{{[2019-08-07 13:05:37,730] INFO Cleaner 0: Offset map for log backup_br_domain_squad-0 complete. (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,730] INFO Cleaner 0: Cleaning log backup_br_domain_squad-0 (cleaning prior to Wed Aug 07 13:05:22 GMT 2019, discarding tombstones prior to Thu Jan 01 00:00:00 GMT 1970)... (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,732] DEBUG Loaded index file /runtime/logs/kafka_1/backup_br_domain_squad-0/00000000000000000000.index.cleaned with maxEntries = 1310720, maxIndexSize = 10485760, entries = 0, lastOffset = 0, file position = 0 (kafka.log.OffsetIndex)}}
{{[2019-08-07 13:05:37,733] DEBUG Loaded index file /runtime/logs/kafka_1/backup_br_domain_squad-0/00000000000000000000.timeindex.cleaned with maxEntries = 873813, maxIndexSize = 10485760, entries = 0, lastOffset = TimestampOffset(-1,0), file position = 0 (kafka.log.TimeIndex)}}
{{[2019-08-07 13:05:37,733] INFO Cleaner 0: Cleaning segment 0 in log backup_br_domain_squad-0 (largest timestamp Mon Jul 15 15:11:43 GMT 2019) into 0, retaining deletes. (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,739] DEBUG Resized /runtime/logs/kafka_1/backup_br_domain_squad-0/00000000000000000000.index.cleaned to 32, position is 32 and limit is 32 (kafka.log.OffsetIndex)}}
{{[2019-08-07 13:05:37,739] DEBUG Resized /runtime/logs/kafka_1/backup_br_domain_squad-0/00000000000000000000.timeindex.cleaned to 36, position is 36 and limit is 36 (kafka.log.TimeIndex)}}
{{[2019-08-07 13:05:37,764] INFO Cleaner 0: Swapping in cleaned segment LogSegment(baseOffset=0, size=1044021) for segment(s) List(LogSegment(baseOffset=0, size=1044021)) in log Log(/runtime/logs/kafka_1/backup_br_domain_squad-0) (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,767] INFO [kafka-log-cleaner-thread-0]:}}
{{ Log cleaner thread 0 cleaned log backup_br_domain_squad-0 (dirty section = [0, 0])}}
{{ 1.0 MB of log processed in 0.1 seconds (17.2 MB/sec).}}
{{ Indexed 1.0 MB in 0.0 seconds (45.3 Mb/sec, 37.9% of total time)}}
{{ Buffer utilization: 0.0%}}
{{ Cleaned 1.0 MB in 0.0 seconds (27.7 Mb/sec, 62.1% of total time)}}
{{ Start size: 1.0 MB (231 messages)}}
{{ End size: 1.0 MB (231 messages)}}
{{ 0.0% size reduction (0.0% fewer messages)}}
{{ (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,772] DEBUG Checking if log segment may be cleaned: log='backup_br_domain_squad-0' segment.baseOffset=0 segment.largestTimestamp=1563203503987; now - compactionLag=1565096737771; is uncleanable=false (kafka.log.LogCleanerManager$)}}
{{[2019-08-07 13:05:37,772] DEBUG Finding range of cleanable offsets for log=backup_br_domain_squad-0 topicPartition=backup_br_domain_squad-0. Last clean offset=Some(232) now=1565183137771 => firstDirtyOffset=232 firstUncleanableOffset=233 activeSegment.baseOffset=233 (kafka.log.LogCleanerManager$)}}
{{[2019-08-07 13:05:37,773] INFO Cleaner 0: Beginning cleaning of log backup_br_domain_squad-0. (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,774] INFO Cleaner 0: Building offset map for backup_br_domain_squad-0... (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,795] INFO [ExpirationReaper-1001-Produce]: Starting (kafka.server.DelayedOperationPurgatory$ExpiredOperationReaper)}}
{{[2019-08-07 13:05:37,795] INFO [ExpirationReaper-1001-Produce]: Starting (kafka.server.DelayedOperationPurgatory$ExpiredOperationReaper)}}
{{[2019-08-07 13:05:37,800] INFO [ExpirationReaper-1001-Fetch]: Starting (kafka.server.DelayedOperationPurgatory$ExpiredOperationReaper)}}
{{[2019-08-07 13:05:37,800] INFO [ExpirationReaper-1001-Fetch]: Starting (kafka.server.DelayedOperationPurgatory$ExpiredOperationReaper)}}
{{[2019-08-07 13:05:37,803] INFO [ExpirationReaper-1001-DeleteRecords]: Starting (kafka.server.DelayedOperationPurgatory$ExpiredOperationReaper)}}
{{[2019-08-07 13:05:37,803] INFO [ExpirationReaper-1001-DeleteRecords]: Starting (kafka.server.DelayedOperationPurgatory$ExpiredOperationReaper)}}
{{[2019-08-07 13:05:37,805] INFO [ExpirationReaper-1001-ElectPreferredLeader]: Starting (kafka.server.DelayedOperationPurgatory$ExpiredOperationReaper)}}
{{[2019-08-07 13:05:37,805] INFO [ExpirationReaper-1001-ElectPreferredLeader]: Starting (kafka.server.DelayedOperationPurgatory$ExpiredOperationReaper)}}
{{[2019-08-07 13:05:37,806] INFO Cleaner 0: Building offset map for log backup_br_domain_squad-0 for 1 segments in offset range [232, 233). (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,807] INFO Cleaner 0: Offset map for log backup_br_domain_squad-0 complete. (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,808] INFO Cleaner 0: Cleaning log backup_br_domain_squad-0 (cleaning prior to Wed Aug 07 13:05:22 GMT 2019, discarding tombstones prior to Tue Aug 06 13:05:22 GMT 2019)... (kafka.log.LogCleaner)}}
{{[2019-08-07 13:05:37,809] INFO [kafka-log-cleaner-thread-0]:}}
{{ Log cleaner thread 0 cleaned log backup_br_domain_squad-0 (dirty section = [232, 232])}}
{{ 0.0 MB of log processed in 0.0 seconds (0.0 MB/sec).}}
{{ Indexed 0.0 MB in 0.0 seconds (0.2 Mb/sec, 97.1% of total time)}}
{{ Buffer utilization: 0.0%}}
{{ Cleaned 0.0 MB in 0.0 seconds (0.0 Mb/sec, 2.9% of total time)}}
{{ Start size: 0.0 MB (0 messages)}}
{{ End size: 0.0 MB (0 messages)}}
{{ NaN% size reduction (NaN% fewer messages)}}
{{ (kafka.log.LogCleaner)}}

 

 
~~~~

### Comments (14)

1.

~~~~
h1. Clue:

 

By further investigation, it looks like:
 * segment 00000000000000000000 has end (existing) offset at 231
 * record with offset 232 is missing?! 
 * while (active) segment 00000000000000000233 has first offset 233

 

When LogCleaner starts, it first looks for [0,233) to cleanup, but while building buildOffsetMap, it ends up with offset 231 (that's last written offset in 00000000000000000000 segment), and new endOffset = 231 + 1 = 232, and this is written in cleaner-offset-checkpoint file.

Next time, LogCleaner starts with [232,233) to cleanup, but while building buildOffsetMap, it ends up with offset -1, since 232 is non-existing in 00000000000000000000 segment, and new endOffset= -1 + 1 = 0, and this is written in cleaner-offset-checkpoint.

 

 
h1. Elaboration:

 

By looking at *kafka_2.12_2.2.1* source code,
 * all this happens inside LogCleaner.doClean (lines: 492-520), where buildOffsetMap(line: 501) in second clean run (probably also in first run, since 232 is non-existing offset) builds wrong offsetMap since reading 
 * segment.log.readInto(readBuffer, position) (line: 899) and val records = MemoryRecords.readableRecords(readBuffer) (line: 905) 
 * yields with offset 231 record, and 
 * for (batch <- records.batches.asScala) (line: 909-934) is skipped, while 
 * map: OffsetMap remains unfilled with default lastOffset = -1 which is later used to determine endOffset for next cleaning (thus endOffset = -1 + 1 = 0, later written in cleaner-offset-checkpoint)

 

 
h1. Summary:

Since last record offset in segment 00000000000000000000 is 231 (232 is missing) and next rolled segment is 00000000000000000233, LogCleaner never progress past segment 00000000000000000000 ending in endless loop cleaning segment 00000000000000000000 with *cleaner-offset-checkpoint* 0->232->0->232....causing high disk read/write/iops operations.

 
~~~~

2.

~~~~
Well it happened again on totally separated environment (production this time), same version of kafka (2.2.1). Issue started after I've removed one broker from cluster, wipe out data, and return it to cluster.

 

When checked log segment (kafka.tools.DumpLogSegments) 00000000000000000000 of troublesome partition, last offset was 179959, while next (active) segment was rolled with 180015 offset. So log cleaner again was jumping:
 * Building offset map for log X for 1 segments in offset range [0, 180015)
 * Building offset map for log X for 1 segments in offset range [179960, 180015)
 * Building offset map for log X for 1 segments in offset range [0, 180015)
 * ...etc

 

Since I'm not familiar with LOG structure, I don't know if empty offsets (from [179960, 180015)) in 0 segment are allowed, and if it's problem in LogCleaner, LOG structure or discrepancy between them.
~~~~

3.

~~~~
Btw. *solution* for this issue, while I'm waiting for someone smart to find/fix the bug, is to manually update *cleaner-offset-checkpoint.*

 
h2. Steps:
 # Stop broker(s) with described issue
 # find partition(s) that bugged LogCleaner
 ** good place for search them is log-cleaner.log output, something like endless lines of this:
 ** [2019-08-21 09:33:32,060] INFO Cleaner 0: Building offset map for log br_domain_match-22 for 1 segments in offset range [0, 180015). (kafka.log.LogCleaner)
 ** [2019-08-21 09:33:32,167] INFO Cleaner 0: Building offset map for log br_domain_match-22 for 1 segments in offset range [179960, 180015). (kafka.log.LogCleaner)
 ** [2019-08-21 09:33:32,195] INFO Cleaner 0: Building offset map for log br_domain_match-22 for 1 segments in offset range [0, 180015). (kafka.log.LogCleaner)
 ** [2019-08-21 09:33:32,440] INFO Cleaner 0: Building offset map for log br_domain_match-22 for 1 segments in offset range [179960, 180015). (kafka.log.LogCleaner)
 ** ...
 ** in this case, partition br_domain_match-22 is troubled one, and LogCleaner flip-flops between [0, 180015), [179960, 180015), [0, 180015), ....
 # remember/writeup last offset for partition in ranges (in my case [179960, 180015), so it's *NEXT_CLEANING_OFFSET=180015*)
 # open cleaner-offset-checkpoint file (placed at root of log.dirs folder), and find line with topic-partition
 ** in my case, it's topic *br_domain_match*, partition *22*, so line contains *br_domain_match 22 XXXXX*
 ** replace *XXXXX* with *NEXT_CLEANING_OFFSET* (from point 3.)
 ** save file
 # and repeat that for each partition with issue
 # start broker and watch cleaner log file, with little luck, everything should be ok
~~~~

4.

~~~~
I wanted to throw my .02 in here:   We are seeing the same issue, also with compact topics.   The compact topics in question are quite low traffic.

LogCleaner is running flat-out, with only a few ms between attempts to clean a single topic-partition.

The log cleaner thread is consuming almost an entire core:
{code:java}
14857 kafka     20   0 8894844 2.187g  12396 R 87.5 56.8  47:04.92 kafka-log-clean 
{code}
We're running 2.4.0, openjdk11, happy to provide any add'l info to help with this issue.   

 
~~~~

5.

~~~~
Hi,

We have the exact same issue with __consumer_offset compacted topic which kills our consumer groups. Thanks, [~trajakovic], for the solution on manually update *cleaner-offset-checkpoint file.*

BR
~~~~

6.

~~~~
[~jnadler] and [~seva.f] so it seems that they still didn't fix this issue, or it happens in rare condition(s). I know that in time when I was solving this issue, I've tested it with multiple versions (of 2.x.x) and all had same problem. Although I'm not so much fluent in Scala, I could probably compile latest version and give some hints about patching this issue out (got some clues back then when issue occurred).

 

Btw. voting for this issue might get faster help/attention ;).
~~~~

7.

~~~~
Kafka (2.4.0) LogCleaner patch for issue
~~~~

8.

~~~~
I just attached a graph of CPU usage in a small, 3-node cluster that shows this issue.   You can see that for all 3 nodes a massive increase in CPU usage when the log cleaner is going nuts - the high CPU periods correspond to tons of log entries in 'log-cleaner.log', and high CPU usage of the 'kafka-log-clean' thread.
~~~~

9.

~~~~
[~trajakovic]: Thanks for the investigation. Normally, the offset map is built from the dirty portion of the log that shouldn't contain holes in offsets. If segment [0,233) misses offset 232, it means that this segment has been cleaned and the dirty offset should have moved to 233 after the first round of cleaning. Was the dirty offset ever reset manually? In any case, I agree that it would be better to make the code more defensive. Could you submit the patch as a PR (details can be found in [https://cwiki.apache.org/confluence/display/KAFKA/Contributing+Code+Changes])?
~~~~

10.

~~~~
Hy [~junrao]. This issue happened on relatively busy kafka cluster, but I've never tinkered with kafka files, or  did any manual actions. And what's more indicative, this issue first time happened on follower brokers/replicas (ISRs), while master broker for topic-partition didn't "feel" same effect. Maybe origin of the problem was "first" ever cleanup on master broker, leaving holes, but that's just my guess.

 

And yes, I'm gonna make PR, just need to see "first good PR" and Contribution guideline.

 

 
~~~~

11.

~~~~
[~trajakovic]: Thanks for providing the additional info. That makes sense now. Currently, the log cleaner runs independently on each replica. If a follower has been down for some time, it is possible that the leader has already cleaned the data and left holes in some log segments. When those segments get replicated to the follower, the follower will clean the same data again and potentially hit the above issue.
~~~~

12.

~~~~
[~jnadler] for now, try to "help" LogCleaner by following solution steps from above. Idea is to move it's state file (cleaner-offset-checkpoint inside topic-partition folder) on all brokers that experiencing issue. Once when next LogSegment becomes available for cleaning, LogCleaner would fix himself and continue to work as expected (unless you'll have new record "holes", but that is, as [~junrao] stated, is rare event happening in edge cases).

 

Advanced solution is to checkout kafka 2.4.0 from github, apply patch attached to this issue, rebuild kafka and run patched version of kafka with your data, and issue, hopefully, should be gone. 
~~~~

13.

~~~~
[~junrao], in the comment https://issues.apache.org/jira/browse/KAFKA-8764?focusedCommentId=17013081&page=com.atlassian.jira.plugin.system.issuetabpanels:comment-tabpanel#comment-17013081 above, you said
{quote}Currently, the log cleaner runs independently on each replica. If a follower has been down for some time, it is possible that the leader has already cleaned the data and left holes in some log segments. When those segments get replicated to the follower, the follower will clean the same data again and potentially hit the above issue.
{quote}
 

Would this also happen if you added a new follower? For example, if I have a compacted topic on Brokers 1 2 3 where compaction has already happened, and then I use kafka-reassign-partitions to move the brokers 4 5 6, it sounds like compaction will happen independently on brokers 4 5 6, and will run into this issue.
~~~~

14.

~~~~
[~wushujames]: Yes, reassigned replica can have the same issue.
~~~~

---

## KAFKA-9046: Connect worker configs require undocumented 'admin.' prefix to configure DLQ for connectors

https://issues.apache.org/jira/browse/KAFKA-9046

Given fix versions: 2.3.2, 2.4.0
JIRA affects (masked from the system): 2.3.0, 2.3.1, 2.4.0

- `KAFKA-9046@2.3.1`: config 2.3.1, metadata answer **affected** (listed_affected)
- `KAFKA-9046@2.2.2`: config 2.2.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
The changes for KAFKA-8265 involved [adding a prefix of "admin." to Connect worker configs|https://github.com/apache/kafka/pull/6624/files#diff-316d2c222b623ee65e8065863bf4b9ceR606] that would be used to configure the admin client that's used for connector DLQs. However, this was never documented in the [corresponding KIP|https://cwiki.apache.org/confluence/display/KAFKA/KIP-458%3A+Connector+Client+Config+Override+Policy] and has broken backwards compatibility with prior Connect releases since workers without the necessary {{"admin."}}-prefixed properties in their configuration files will now fail in some circumstances (e.g., when interacting with a secured Kafka cluster that requires authentication from all admin clients that interact with it).
~~~~

### Comments (3)

1.

~~~~
Although backwards compatibility was broken by these changes and the initial approach for a bug fix may be to simply revert them, it's likely that these changes have been picked up by Connect users and that removing support for the {{"admin."}} prefix in worker config files will likely break things _again_ for those users and cause confusion. Additionally, with the support for per-connect admin client config overrides added by KIP-458, it would be best to keep support for worker-level default admin client configs to match the current behavior for connector producers and consumers.

As a result, it'd be good if a bug fix for this issue removed the _requirement_ for the {{"admin."}} prefix in worker files but still respected those configurations if they're present.

One possible approach is to alter the behavior of the Connect worker to calculate connector admin client configurations by drawing from the following properties, in ascending order of priority:
 # Begin with all top-level worker properties (in order to retain backwards compatibility with Connect releases unaffected by this issue)
 # Then, apply all properties prefixed with {{"admin."}} in the worker file after removing the prefix (in order to retain the undocumented changes brought in by the PR for KIP-458)
 # Finally, apply all properties prefixed with {{"admin.override."}} in the connector configuration after removing the prefix (in the fashion dictated by KIP-458)
~~~~

2.

~~~~
If the PR is accepted, we should add a note to KIP-458 explaining how that functionality was modified and what the impact is on Connect (both before and after any fixes that are implemented as part of this issue).
~~~~

3.

~~~~
Issue resolved by pull request 7525
[https://github.com/apache/kafka/pull/7525]
~~~~

---

## KAFKA-9169: Standby Tasks point ask for incorrect offsets on resuming post suspension

https://issues.apache.org/jira/browse/KAFKA-9169

Given fix versions: 2.5.0
JIRA affects (masked from the system): 1.1.0

- `KAFKA-9169@1.1.0`: config 1.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-9169@1.0.2`: config 1.0.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.0, 2.3, 2.5.0, 2.3.0, 1.1, 1.1.0

### Description

~~~~
In versions(check 2.0) where standby tasks are suspended on each rebalance the checkpoint file is updated post the flush and the expected behaviour is that post assignment the same standby task gets assigned back on the machine it will start reading data from changelog from the same offset from it left off. 

 

But there looks like a bug in the code, every time post rebalance it starts reading from the offset from where it read the first time the task was assigned on this machine. This has 2 repercussions:
 # After every rebalance the standby tasks start restoring huge amount of data which they have already restored earlier(Verified this via 300x increase Network IO on all streams instances post rebalance even when no change in assignment) .
 # If changelog has time retention those offsets will not be available in the changelog, which leads to offsetOutOfRange exceptions and the stores get deleted and recreated again.

 

I have gone through the code and I think I know the issue.

In TaskManager# updateNewAndRestoringTasks(), the function assignStandbyPartitions() gets called for all the running standby tasks where it populates the Map: checkpointedOffsets from the standbyTask.checkpointedOffsets() which is only updated at the time of initialization of a StandbyTask(i.e. in it's constructor). 

 

This has an easy fix.

Post resumption we are reading standbyTask.checkpointedOffsets() to know the offset from where the standby task should start running and not from stateMgr.checkpointed() which gets updated on every commit to the checkpoint file. In the former case it's always reading from the same offset, even those which it had already read earlier and in cases where changelog topic has a retention time, it gives offsetOutOfRange exception. So, standbyTask.checkpointedOffsets() is quite useless and we should use stateMgr.checkpointed() instead to return offsets to task manager.
~~~~

### Comments (7)

1.

~~~~
After testing, I've determined that the bug is pre-existing in the 2.3 branch at least.

Since it's not a regression, I'm downgrading it to critical.
~~~~

2.

~~~~
This was fixed in https://github.com/apache/kafka/pull/7681/ and merged to trunk (currently 2.5.0-SNAPSHOT)
~~~~

3.

~~~~
Update "Affects Version" to first affected version what is sufficient for tracking.
~~~~

4.

~~~~
Aha, that makes more sense... Thanks, [~mjsax]

n.b., 2.3.0 is probably not truly the first affected version, but it's the first *confirmed* affected version. For this issue, we can only determine an affected version empirically, so we would have to port the system test from the PR to each old version we want to consider.

Just wanted to make that clear in case someone wants to know later on if a specific older version < 2.3.0 is affected. The answer is, "unknown, but we can find out".
~~~~

5.

~~~~
Yeah. If we confirm for older version, we can just update the ticket.
~~~~

6.

~~~~
I can confirm that this has been there since 1.1 version.
~~~~

7.

~~~~
Thanks, Navinder. I’ve set the affected version field to 1.1.0
~~~~

---

## KAFKA-9263: The new hw is added to incorrect log when  ReplicaAlterLogDirsThread is replacing log (fix  PlaintextAdminIntegrationTest.testAlterReplicaLogDirs)

https://issues.apache.org/jira/browse/KAFKA-9263

Given fix versions: 2.8.0
JIRA affects (masked from the system): 2.4.0

- `KAFKA-9263@2.4.0`: config 2.4.0, metadata answer **affected** (listed_affected)
- `KAFKA-9263@2.3.1`: config 2.3.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
This test has failed for me on https://builds.apache.org/job/kafka-pr-jdk11-scala2.12/9691/testReport/junit/kafka.api/AdminClientIntegrationTest/testAlterReplicaLogDirs/

{noformat}
Error Message
org.scalatest.exceptions.TestFailedException: only 0 messages are produced within timeout after replica movement. Producer future Some(Failure(java.util.concurrent.TimeoutException: Timeout after waiting for 10000 ms.))
Stacktrace
org.scalatest.exceptions.TestFailedException: only 0 messages are produced within timeout after replica movement. Producer future Some(Failure(java.util.concurrent.TimeoutException: Timeout after waiting for 10000 ms.))
	at org.scalatest.Assertions.newAssertionFailedException(Assertions.scala:530)
	at org.scalatest.Assertions.newAssertionFailedException$(Assertions.scala:529)
	at org.scalatest.Assertions$.newAssertionFailedException(Assertions.scala:1389)
	at org.scalatest.Assertions.fail(Assertions.scala:1091)
	at org.scalatest.Assertions.fail$(Assertions.scala:1087)
	at org.scalatest.Assertions$.fail(Assertions.scala:1389)
	at kafka.utils.TestUtils$.waitUntilTrue(TestUtils.scala:842)
	at kafka.api.AdminClientIntegrationTest.testAlterReplicaLogDirs(AdminClientIntegrationTest.scala:459)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.base/java.lang.reflect.Method.invoke(Method.java:566)
	at org.junit.runners.model.FrameworkMethod$1.runReflectiveCall(FrameworkMethod.java:59)
	at org.junit.internal.runners.model.ReflectiveCallable.run(ReflectiveCallable.java:12)
	at org.junit.runners.model.FrameworkMethod.invokeExplosively(FrameworkMethod.java:56)
	at org.junit.internal.runners.statements.InvokeMethod.evaluate(InvokeMethod.java:17)
	at org.junit.internal.runners.statements.RunBefores.evaluate(RunBefores.java:26)
	at org.junit.internal.runners.statements.RunAfters.evaluate(RunAfters.java:27)
	at org.junit.internal.runners.statements.FailOnTimeout$CallableStatement.call(FailOnTimeout.java:288)
	at org.junit.internal.runners.statements.FailOnTimeout$CallableStatement.call(FailOnTimeout.java:282)
	at java.base/java.util.concurrent.FutureTask.run(FutureTask.java:264)
	at java.base/java.lang.Thread.run(Thread.java:834)
Standard Output
[2019-12-03 04:54:16,111] ERROR [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0] Error for partition unclean-test-topic-1-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:54:21,711] ERROR [ReplicaFetcher replicaId=0, leaderId=1, fetcherId=0] Error for partition topic-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:54:21,712] ERROR [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0] Error for partition topic-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:54:27,092] ERROR [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0] Error for partition unclean-test-topic-1-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:54:27,091] ERROR [ReplicaFetcher replicaId=0, leaderId=1, fetcherId=0] Error for partition unclean-test-topic-1-1 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:54:35,263] ERROR [ReplicaFetcher replicaId=1, leaderId=0, fetcherId=0] Error for partition elect-preferred-leaders-topic-1-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:54:35,264] ERROR [ReplicaFetcher replicaId=2, leaderId=0, fetcherId=0] Error for partition elect-preferred-leaders-topic-1-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:54:35,463] ERROR [ReplicaFetcher replicaId=1, leaderId=0, fetcherId=0] Error for partition elect-preferred-leaders-topic-2-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:54:35,463] ERROR [ReplicaFetcher replicaId=2, leaderId=0, fetcherId=0] Error for partition elect-preferred-leaders-topic-2-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:54:45,719] ERROR [ReplicaFetcher replicaId=1, leaderId=0, fetcherId=0] Error for partition list-reassignments-no-reassignments-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:54:45,719] ERROR [ReplicaFetcher replicaId=2, leaderId=0, fetcherId=0] Error for partition list-reassignments-no-reassignments-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:54:57,062] ERROR [ReplicaFetcher replicaId=2, leaderId=0, fetcherId=0] Error for partition topic-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:54:57,062] ERROR [ReplicaFetcher replicaId=1, leaderId=0, fetcherId=0] Error for partition topic-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:55:24,200] ERROR [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0] Error for partition xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:55:24,202] ERROR [ReplicaFetcher replicaId=2, leaderId=0, fetcherId=0] Error for partition xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-1 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:55:24,220] ERROR [ReplicaFetcher replicaId=0, leaderId=1, fetcherId=0] Error for partition xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:55:27,652] ERROR [ReplicaFetcher replicaId=1, leaderId=0, fetcherId=0] Error for partition mytopic2-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:55:27,652] ERROR [ReplicaFetcher replicaId=0, leaderId=1, fetcherId=0] Error for partition mytopic2-2 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:55:27,652] ERROR [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0] Error for partition mytopic2-2 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:55:27,655] ERROR [ReplicaFetcher replicaId=2, leaderId=0, fetcherId=0] Error for partition mytopic2-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:55:27,655] ERROR [ReplicaFetcher replicaId=0, leaderId=2, fetcherId=0] Error for partition mytopic2-1 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:55:27,656] ERROR [ReplicaFetcher replicaId=1, leaderId=2, fetcherId=0] Error for partition mytopic2-1 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:55:27,716] ERROR [ReplicaFetcher replicaId=0, leaderId=2, fetcherId=0] Error for partition mytopic-1 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:55:32,005] ERROR [ReplicaFetcher replicaId=1, leaderId=0, fetcherId=0] Error for partition topic-1 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:55:32,006] ERROR [ReplicaFetcher replicaId=1, leaderId=2, fetcherId=0] Error for partition topic-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:55:32,061] ERROR [ReplicaFetcher replicaId=0, leaderId=2, fetcherId=0] Error for partition topic-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:55:48,686] ERROR [ReplicaManager broker=0] Error while changing replica dir for partition topic-0 (kafka.server.ReplicaManager:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: Error while fetching partition state for topic-0
[2019-12-03 04:55:48,686] ERROR [ReplicaManager broker=1] Error while changing replica dir for partition topic-0 (kafka.server.ReplicaManager:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: Error while fetching partition state for topic-0
[2019-12-03 04:55:48,686] ERROR [ReplicaManager broker=2] Error while changing replica dir for partition topic-0 (kafka.server.ReplicaManager:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: Error while fetching partition state for topic-0
[2019-12-03 04:55:48,711] ERROR [ReplicaFetcher replicaId=0, leaderId=2, fetcherId=0] Error for partition topic-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:55:48,711] ERROR [ReplicaFetcher replicaId=1, leaderId=2, fetcherId=0] Error for partition topic-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:56:09,041] ERROR [ReplicaFetcher replicaId=1, leaderId=0, fetcherId=0] Error for partition topic-1 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:56:09,041] ERROR [ReplicaFetcher replicaId=1, leaderId=2, fetcherId=0] Error for partition topic-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:56:09,350] ERROR [ReplicaFetcher replicaId=0, leaderId=2, fetcherId=0] Error for partition topic-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:56:09,350] ERROR [ReplicaFetcher replicaId=2, leaderId=0, fetcherId=0] Error for partition topic-1 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:56:22,628] ERROR [ReplicaFetcher replicaId=2, leaderId=0, fetcherId=0] Error for partition mytopic-2 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:56:22,629] ERROR [ReplicaFetcher replicaId=0, leaderId=2, fetcherId=0] Error for partition mytopic-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:56:22,628] ERROR [ReplicaFetcher replicaId=1, leaderId=0, fetcherId=0] Error for partition mytopic-2 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:56:22,631] ERROR [ReplicaFetcher replicaId=1, leaderId=2, fetcherId=0] Error for partition mytopic-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:56:34,653] ERROR [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0] Error for partition unclean-test-topic-1-1 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:56:34,654] ERROR [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0] Error for partition unclean-test-topic-1-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:56:42,023] ERROR [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0] Error for partition unclean-test-topic-1-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:56:46,235] ERROR [ReplicaFetcher replicaId=2, leaderId=0, fetcherId=0] Error for partition create-partitions-topic-2-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:56:46,543] ERROR [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0] Error for partition create-partitions-topic-2-2 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:56:54,128] ERROR [ReplicaFetcher replicaId=1, leaderId=0, fetcherId=0] Error for partition mytopic-2 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:56:54,129] ERROR [ReplicaFetcher replicaId=2, leaderId=0, fetcherId=0] Error for partition mytopic-2 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:56:54,129] ERROR [ReplicaFetcher replicaId=0, leaderId=1, fetcherId=0] Error for partition mytopic-1 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:56:54,130] ERROR [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0] Error for partition mytopic-1 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:57:03,561] ERROR [ReplicaFetcher replicaId=0, leaderId=1, fetcherId=0] Error for partition unclean-test-topic-1-1 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:57:03,561] ERROR [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0] Error for partition unclean-test-topic-1-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:57:11,532] ERROR [ReplicaFetcher replicaId=2, leaderId=0, fetcherId=0] Error for partition topic-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:57:11,534] ERROR [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0] Error for partition topic-1 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:57:11,564] ERROR [ReplicaFetcher replicaId=0, leaderId=1, fetcherId=0] Error for partition topic-1 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:57:16,528] ERROR [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0] Error for partition unclean-test-topic-1-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:57:31,988] ERROR [ReplicaFetcher replicaId=1, leaderId=0, fetcherId=0] Error for partition topic-1 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:57:31,988] ERROR [ReplicaFetcher replicaId=1, leaderId=2, fetcherId=0] Error for partition topic-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:57:32,036] ERROR [ReplicaFetcher replicaId=0, leaderId=2, fetcherId=0] Error for partition topic-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:57:41,348] ERROR [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0] Error for partition topic-1 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:57:41,350] ERROR [ReplicaFetcher replicaId=2, leaderId=0, fetcherId=0] Error for partition topic-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:57:41,552] ERROR [ReplicaFetcher replicaId=0, leaderId=1, fetcherId=0] Error for partition topic-1 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:57:41,552] ERROR [ReplicaFetcher replicaId=1, leaderId=0, fetcherId=0] Error for partition topic-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
[2019-12-03 04:57:45,010] ERROR [Consumer instanceId=test_instance_id, clientId=test_client_id, groupId=test_group_id] Offset commit failed on partition test_topic-1 at offset 0: Specified group generation id is not valid. (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:1108)
[2019-12-03 04:57:48,148] ERROR [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0] Error for partition unclean-test-topic-1-0 at offset 0 (kafka.server.ReplicaFetcherThread:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: This server does not host this topic-partition.
{noformat}
~~~~

### Comments (3)

1.

~~~~
update the title since KAFKA-9183 had renamed AdminClientIntegrationTest to PlaintextAdminIntegrationTest
~~~~

2.

~~~~
 

Test failure [https://builds.apache.org/job/kafka-pr-jdk11-scala2.13/7843/testReport/junit/kafka.api/PlaintextAdminIntegrationTest/testAlterReplicaLogDirs/]

 
{noformat}
2020-08-14 17:34:06,420] ERROR [ReplicaManager broker=0] Error while changing replica dir for partition topic-0 (kafka.server.ReplicaManager:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: Error while fetching partition state for topic-0
[2020-08-14 17:34:06,420] ERROR [ReplicaManager broker=1] Error while changing replica dir for partition topic-0 (kafka.server.ReplicaManager:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: Error while fetching partition state for topic-0
[2020-08-14 17:34:06,420] ERROR [ReplicaManager broker=2] Error while changing replica dir for partition topic-0 (kafka.server.ReplicaManager:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: Error while fetching partition state for topic-0
[2020-08-14 17:36:24,822] ERROR [Consumer instanceId=test_instance_id_1, clientId=test_client_id, groupId=test_group_id] Offset commit failed on partition test_topic-1 at offset 0: The coordinator is not aware of this member. (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:1191)
[2020-08-14 17:36:24,823] ERROR Thread Thread[Thread-4,5,FailOnTimeoutGroup] died (org.apache.zookeeper.server.NIOServerCnxnFactory:92)
org.apache.kafka.clients.consumer.CommitFailedException: Commit cannot be completed since the group has already rebalanced and assigned the partitions to another member. This means that the time between subsequent calls to poll() was longer than the configured max.poll.interval.ms, which typically implies that the poll loop is spending too much time message processing. You can address this either by increasing max.poll.interval.ms or by reducing the maximum size of batches returned in poll() with max.poll.records.
	at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator$OffsetCommitResponseHandler.handle(ConsumerCoordinator.java:1257)
	at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator$OffsetCommitResponseHandler.handle(ConsumerCoordinator.java:1164)
	at org.apache.kafka.clients.consumer.internals.AbstractCoordinator$CoordinatorResponseHandler.onSuccess(AbstractCoordinator.java:1132)
	at org.apache.kafka.clients.consumer.internals.AbstractCoordinator$CoordinatorResponseHandler.onSuccess(AbstractCoordinator.java:1107)
	at org.apache.kafka.clients.consumer.internals.RequestFuture$1.onSuccess(RequestFuture.java:206)
	at org.apache.kafka.clients.consumer.internals.RequestFuture.fireSuccess(RequestFuture.java:169)
	at org.apache.kafka.clients.consumer.internals.RequestFuture.complete(RequestFuture.java:129)
	at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient$RequestFutureCompletionHandler.fireCompletion(ConsumerNetworkClient.java:602)
	at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.firePendingCompletedRequests(ConsumerNetworkClient.java:412)
	at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:297)
	at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:236)
	at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:215)
	at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.commitOffsetsSync(ConsumerCoordinator.java:1006)
	at org.apache.kafka.clients.consumer.KafkaConsumer.commitSync(KafkaConsumer.java:1394)
	at org.apache.kafka.clients.consumer.KafkaConsumer.commitSync(KafkaConsumer.java:1348)
	at kafka.api.PlaintextAdminIntegrationTest$$anon$1.run(PlaintextAdminIntegrationTest.scala:1071)
[2020-08-14 17:36:24,848] ERROR [Consumer instanceId=test_instance_id_2, clientId=test_client_id, groupId=test_group_id] Offset commit failed on partition test_topic1-0 at offset 0: Specified group generation id is not valid. (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:1191)
[2020-08-14 17:36:24,852] ERROR [Consumer clientId=test_client_id, groupId=test_group_id] Offset commit failed on partition test_topic2-0 at offset 0: Specified group generation id is not valid. (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:1191)
[2020-08-14 18:29:44,855] ERROR [ReplicaManager broker=1] Error while changing replica dir for partition topic-0 (kafka.server.ReplicaManager:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: Error while fetching partition state for topic-0
[2020-08-14 18:29:44,855] ERROR [ReplicaManager broker=0] Error while changing replica dir for partition topic-0 (kafka.server.ReplicaManager:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: Error while fetching partition state for topic-0
[2020-08-14 18:29:44,855] ERROR [ReplicaManager broker=2] Error while changing replica dir for partition topic-0 (kafka.server.ReplicaManager:76)
org.apache.kafka.common.errors.UnknownTopicOrPartitionException: Error while fetching partition state for topic-0{noformat}
 
~~~~

3.

~~~~
PlaintextAdminIntegrationTest.testLogStartOffsetCheckpoint does not fail recently and I looped it 200 times, all pass.

The https://github.com/apache/kafka/pull/9423 which fixes kafka.api.PlaintextAdminIntegrationTest.testAlterReplicaLogDirs is going to be merged so I will revise the title of this issue (i.e remove PlaintextAdminIntegrationTest.testLogStartOffsetCheckpoint)
~~~~

---

## KAFKA-9390: Non-key joining of KTable not compatible with confluent avro serdes

https://issues.apache.org/jira/browse/KAFKA-9390

Given fix versions: 2.4.1, 2.5.0
JIRA affects (masked from the system): 2.4.0

- `KAFKA-9390@2.4.0`: config 2.4.0, metadata answer **affected** (listed_affected)
- `KAFKA-9390@2.3.1`: config 2.3.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.4

### Description

~~~~
I was trying out the new one-to-many KTable joins against some CDC data in Avro format and kept getting serialisation errors.

 
{code:java}
org.apache.kafka.common.errors.SerializationException: Error registering Avro schema: {"type":"record","name":"Key","namespace":"dbserver1.inventory.orders","fields":[

{"name":"order_number","type":"int"}

],"connect.name":"dbserver1.inventory.orders.Key"}
 Caused by: io.confluent.kafka.schemaregistry.client.rest.exceptions.RestClientException: Schema being registered is incompatible with an earlier schema; error code: 409
  
{code}
Both tables have avro keys of different types (one is an order key, the other a customer key).

This looks like it will cause issues.

[https://github.com/apache/kafka/blob/2.4/streams/src/main/java/org/apache/kafka/streams/kstream/internals/foreignkeyjoin/CombinedKeySchema.java#L57-L60]

 They will both attempt to register schemas with the same subject to the schema registry which will fail a backward compatibility check.

I also noticed in the schema registry there were some subjects that didn't have the application id prefix. This is probably caused by this...

 [https://github.com/apache/kafka/blob/2.4/streams/src/main/java/org/apache/kafka/streams/kstream/internals/foreignkeyjoin/ForeignJoinSubscriptionSendProcessorSupplier.java#L88]

Where here {{repartitionTopicName}} doesn't have the application prefix.

 

 

 

 

 
~~~~

### Comments (3)

1.

~~~~
Here's the code snippet. I'm joining the orders table to the customers table using the customer key as the foreign key.
{code:java}
final KTable<dbserver1.inventory.customers.Key, dbserver1.inventory.customers.Value> customersTable =
    CdcHelpers.valueTable(streams.customers(), "customersTable");
final KTable<dbserver1.inventory.orders.Key, dbserver1.inventory.orders.Value> ordersTable =
    CdcHelpers.valueTable(streams.orders(), "ordersTable");
final KTable<dbserver1.inventory.orders.Key, OrderView> enrichedOrders =
    ordersTable.join(
      customersTable,
      order -> new dbserver1.inventory.customers.Key(order.getPurchaser()),
      (order, customer) ->
          OrderView.newBuilder()
            .setCustomerName(customer.getFirstName() + ' ' + customer.getLastName())
            .setOrderId(order.getOrderNumber())
            .setOrderDate(LocalDate.fromDateFields(Date.valueOf(java.time.LocalDate.ofEpochDay(order.getOrderDate()))))
            .setOrderQuantity(order.getQuantity())
            .setProductName("unknown")
            .setProductWeight(0.0d)
            .build(),
        Named.as("wtf"),
        AvroSerdes.materializedAs("ordersWithCustomerxx"));
{code}
~~~~

2.

~~~~
Also I'm using the 2.4 version of Kafka Streams with 5.3.2 version of confluent serdes (since 5.4 isn't out)
~~~~

3.

~~~~
There is a known issue I think since Confluent's SR do not allow nulls and hence we use a not-null dummy value. Not sure if there are still missing pieces out there. [~bbejeck] [~mjsax] could you take a look?
~~~~

---

## KAFKA-9675: RocksDB metrics reported always at zero

https://issues.apache.org/jira/browse/KAFKA-9675

Given fix versions: 2.4.2, 2.5.1, 2.6.0
JIRA affects (masked from the system): 2.4.0

- `KAFKA-9675@2.4.0`: config 2.4.0, metadata answer **affected** (listed_affected)
- `KAFKA-9675@2.3.1`: config 2.3.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
The rocksdb metrics listed under {{stream-state-metrics}} are reported as zero for all metrics and all rocksdb instances. The metrics are present in JMX, but are always zero.

The streams state is configured with {{MetricsRecordingLevel}} at {{debug}}. I am able to see metrics with appropriate values in the {{stream-rocksdb-window-state-metrics}}, {{stream-record-cache-metrics}}, {{stream-task-metrics}}, and {{stream-processor-node-metrics}}.

Additionally, my DEBUG logs show the appropriate messages for recording events, i.e.

{{org.apache.kafka.streams.state.internals.metrics.RocksDBMetricsRecorder [RocksDB Metrics Recorder for agg-store] Recording metrics for store agg-store}}

It happens that all of my rocksdb instances are windowed stores, not key value stores, so I haven't been able to check if this issue is unique to windowed stores.
~~~~

---

## KAFKA-9704: z/OS won't let us resize file when mmap

https://issues.apache.org/jira/browse/KAFKA-9704

Given fix versions: 2.4.2, 2.5.1, 2.6.0
JIRA affects (masked from the system): 2.4.0

- `KAFKA-9704@2.4.0`: config 2.4.0, metadata answer **affected** (listed_affected)
- `KAFKA-9704@2.3.1`: config 2.3.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
z/OS won't let us resize file when mmap, so we need to force unman like Windows.

 
It was found that if messages were ever published to the Kafka server, the Kafka server will not restart. The issue occurs repeatedly in two of our guest z/OS systems.
 
*java.io.IOException: EDC5121I Invalid argument.*                                                   
 at sun.nio.ch.FileChannelImpl.map0(Native Method)                                                
 at sun.nio.ch.FileChannelImpl.map(FileChannelImpl.java:946)                                      
 at kafka.log.AbstractIndex.$anonfun$resize$1(AbstractIndex.scala:190)                            
 at kafka.log.AbstractIndex$$Lambda$238.00000000D24C4D30.apply$mcZ$sp(Unknown Source)             
 at scala.runtime.java8.JFunction0$mcZ$sp.apply(JFunction0$mcZ$sp.java:23)                        
 at kafka.utils.CoreUtils$.inLock(CoreUtils.scala:253)                                            
 at kafka.log.AbstractIndex.resize(AbstractIndex.scala:174)                                       
 at kafka.log.LogSegment.resizeIndexes(LogSegment.scala:77)                                       
 at kafka.log.Log.loadSegments(Log.scala:728)                                                     
 at kafka.log.Log.<init>(Log.scala:298)                                                           
 at kafka.log.Log$.apply(Log.scala:2461)                                                          
 at kafka.log.LogManager.loadLog(LogManager.scala:283)                                            
 at kafka.log.LogManager.$anonfun$loadLogs$12(LogManager.scala:353)                               
 at kafka.log.LogManager$$Lambda$198.00000000C9F511B0.apply$mcV$sp(Unknown Source)                
 at kafka.utils.CoreUtils$$anon$1.run(CoreUtils.scala:65)                                         
 at java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:522)                       
 at java.util.concurrent.FutureTask.run(FutureTask.java:277)                                      
 at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1160)               
 at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:635)               
 at java.lang.Thread.run(Thread.java:812)                                                         
~~~~

---

## KAFKA-9752: Consumer rebalance can be stuck after new member timeout with old JoinGroup version

https://issues.apache.org/jira/browse/KAFKA-9752

Given fix versions: 2.2.3, 2.3.2, 2.4.2, 2.5.0
JIRA affects (masked from the system): 2.2.2, 2.3.1, 2.4.1

- `KAFKA-9752@2.2.2`: config 2.2.2, metadata answer **affected** (listed_affected)
- `KAFKA-9752@2.2.1`: config 2.2.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.3.2, 2.4.2

### Description

~~~~
For older versions of the JoinGroup protocol (v3 and below), there was no way for new consumer group members to get their memberId until the first rebalance completed. If the JoinGroup request timed out and the client disconnected, the member would nevertheless be left in the group until the rebalance completed and the session timeout expired. 

In order to prevent this situation from causing the group size to grow unboundedly, we added logic in KAFKA-7610 to limit the maximum time a new member will be left in the group before it would be kicked out (in spite of rebalance state). 

In KAFKA-9232, we addressed one issue with this solution. Basically the new member expiration logic did not properly get cancelled after the rebalance completed which means that in certain cases, a successfully joined member might get kicked out of the group unnecessarily. 

Unfortunately, this patch introduced a regression in the normal session expiration logic following completion of the initial rebalance. Basically the expiration task fails to get scheduled properly. The issue is in this function:

{code}
  def shouldKeepAlive(deadlineMs: Long): Boolean = {
    if (isNew) {
      // New members are expired after the static join timeout
      latestHeartbeat + GroupCoordinator.NewMemberJoinTimeoutMs > deadlineMs
    } else if (isAwaitingJoin || isAwaitingSync) {
      // Don't remove members as long as they have a request in purgatory
      true
    } else {
      // Otherwise check for session expiration
      latestHeartbeat + sessionTimeoutMs > deadlineMs
    }
  }
{code}

We use this logic in order to check for session expiration. On the surface, there is nothing wrong with it, but it has an odd interaction with the purgatory. When the heartbeat is first scheduled with `tryCompleteElseWatch`, the code relies on `shouldKeepAlive` returning false so that the heartbeat task is not immediately completed. This only works because we update `latestHeartbeat` just prior to calling `tryCompleteElseWatch`, which means that the first or third checks will fail, `shouldKeepAlive` will return false, and the heartbeat expiration task will not be immediately completed. 

The bug in this case has to do with the case when `isNew` is true. When we schedule the session expiration task, the `isNew` flag is still set to true, which means we will hit the first check above. Since in most cases, the session timeout is less than the new member timeout of 5 minutes, the check is very likely to return true. This seems like what we would want, but as noted above, we rely on this function returning false when the expiration task is passed to `tryCompleteElseWatch`. Since it returns true instead, the task completes immediately, which means we cannot rely on its expiration.

The impact of this bug in the worst case is that a consumer group can be left in the `PreparingRebalance` state indefinitely. This state will persist until there is a coordinator change (e.g. as a result of restarting the broker). Note that this is only possible if 1) we have a consumer using an old JoinGroup version, 2) the consumer times out and disconnects from its initial JoinGroup request. 



~~~~

### Comments (6)

1.

~~~~
Would be nice if we could remove 2.3.2 and 2.4.2 from the fixed versions section, since these Kafka versions don't seem to exist.
~~~~

2.

~~~~
[~gokul2411s] That's to signal that they would be included in such releases if they are created (i.e. they are in the appropriate branch). Otherwise, how would we create the appropriate release notes?
~~~~

3.

~~~~
[~ijuma] thanks for the explanation. makes sense.
~~~~

4.

~~~~
Hi [~ijuma] [~hachikuji], I am seeing a different issue now with this fix . Earlier the ConsumerGroup was stuck in "PendingRebalance" state , which is not happening now , but now I see members not able to join the group . I see below logs where members are being removed after session timeout.

 

[2020-08-09 09:29:00,558] INFO [GroupCoordinator 5]: *Pending member* XXX in group YYY  *has been removed after session timeout expiration*. (kafka.coordinator.group.GroupCoordinator)

[2020-08-09 09:29:55,856] INFO [GroupCoordinator 5]: *Pending member* ZZZ in group YYY  *has been removed after session timeout expiration*. (kafka.coordinator.group.GroupCoordinator)

 

As I see the GroupCoridinator code,  when new member tries to join for first time,  GroupCoridinator also schedule a addPendingMemberExpiration (in doUnknownJoinGroup call ) with SessionTimeOut…

{code:}

addPendingMemberExpiration(group, newMemberId, sessionTimeoutMs)

{code:}

 

If for some reason , if addMemberAndRebalance call takes longer, and member still in “Pending” state, the above addPendingMemberExpiration can remove the pending member and they cannot join the group. I think that is what is happening. 

When for new member , Coordinator is already setting a timeout in 

{code:}

completeAndScheduleNextExpiration(group, member, NewMemberJoinTimeoutMs) 

{code:}

 

What the requirement for one more addPendingMemberExpiration task ? 

 
~~~~

5.

~~~~
What version of the Kafka clients (consumer/producer/streams) use JoinGroup v4 that isn’t affected by this bug?

Thx
~~~~

6.

~~~~
Do you think [~hachikuji] that the problem we described [in this thread|https://lists.apache.org/thread.html/rdf907dbb78092d46e039a9669a40edc7f36bd2eaacfd1a3025db4b6e%40%3Cusers.kafka.apache.org%3E] is caused by the bug you solved in this ticket? Thanks
~~~~

---

## KAFKA-9840: Consumer should not use OffsetForLeaderEpoch without current epoch validation

https://issues.apache.org/jira/browse/KAFKA-9840

Given fix versions: 2.6.0
JIRA affects (masked from the system): 2.4.1

- `KAFKA-9840@2.4.1`: config 2.4.1, metadata answer **affected** (listed_affected)
- `KAFKA-9840@2.4.0`: config 2.4.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
We have observed a case where the consumer attempted to detect truncation with the OffsetsForLeaderEpoch API against a broker which had become a zombie. In this case, the last epoch known to the consumer was higher than the last epoch known to the zombie broker, so the broker returned -1 as both the end offset and epoch in the response. The consumer did not check for this in the response, which resulted in the following message:

{code}
Truncation detected for partition topic-1 at offset FetchPosition{offset=11859, offsetEpoch=Optional[46], currentLeader=LeaderAndEpoch{leader=broker-host (id: 3 rack: null), epoch=-1}}, resetting offset to the first offset known to diverge FetchPosition{offset=-1, offsetEpoch=Optional[-1], currentLeader=LeaderAndEpoch{broker-host (id: 3 rack: null), epoch=-1}} (org.apache.kafka.clients.consumer.internals.SubscriptionState:414)
{code}

There are a couple ways we the consumer can handle this situation better. First, the reason we did not detect the zombie broker is that we did not include the current leader epoch in the OffsetForLeaderEpoch request. This was likely because of KAFKA-9212. Following this patch, we would not initialize the current leader epoch from metadata responses because there are cases that we cannot rely on it. But if the client cannot rely on being able to detect zombies, then the epoch validation is less useful anyway. So the simple solution is to not bother with the validation unless we have a reliable current leader epoch.

Second, the consumer needs to check for the case when the returned offset and epoch are not defined. In this case, we have to treat this as a normal OffsetOutOfRange case and invoke the reset policy. 


~~~~

### Comments (4)

1.

~~~~
For the second case, when the returned offset / epoch is not defined could the consumer tries to refresh its metadata trying to find the new leader?
~~~~

2.

~~~~
[~guozhang] If we have the current epoch validation, it's a bit unclear whether this case should even be possible. There shouldn't be any situation where the epoch we're requesting is larger than the current leader epoch, so the leader should always be able to provide an end offset in the response. I guess we could even treat this as an unexpected error in the client. What do you think?
~~~~

3.

~~~~
What I'm thinking is that, if we treat it as an unexpected error, either defaulting to reset policy or even throwing are not ideal -- since we are talking to a zombie broker, the consumer should not pay the price as either re-consuming or losing data or even crashing; on the other hand, suppose we do not remove the current validation from broker (since new client can always talk to old brokers), does returning -1 always means that the broker we are talking to is a zombie? If yes, instead of resetting or throwing the consumer can just try to find the current leader and retry.
~~~~

4.

~~~~
Other than the zombie case, the only way I could see this happening is some kind of disaster scenario where the cluster had to revert to an older epoch. The current epoch validation in that case would also fail, which would cause the consumer to retry. So perhaps retrying on -1 without the current epoch validation is reasonable as well.
~~~~

---

## KAFKA-10101: recovery point is advanced without flushing the data after recovery

https://issues.apache.org/jira/browse/KAFKA-10101

Given fix versions: 2.8.0
JIRA affects (masked from the system): 2.5.0

- `KAFKA-10101@2.5.0`: config 2.5.0, metadata answer **affected** (listed_affected)
- `KAFKA-10101@2.4.1`: config 2.4.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 1.0.0

### Description

~~~~
Currently, in Log.recoverLog(), we set recoveryPoint to logEndOffset after recovering the log segment. However, we don't flush the log segments after recovery. The potential issue is that if the broker has another hard failure, segments may be corrupted on disk but won't be going through recovery on another restart.

This logic was introduced in KAFKA-5829 since 1.0.0.
~~~~

### Comments (4)

1.

~~~~
[~ijuma] : Could you double check if this is an issue? Thanks.
~~~~

2.

~~~~
If this is an issue, one way to fix that is to simply not advance recoveryPoint after recovery.
~~~~

3.

~~~~
[~junrao] That's a good point. I agree with you that it's probably simplest to remove the code that changes the recover point. The previous code had:

 
{code:java}
if(hasCleanShutdownFile) {
  this.recoveryPoint = activeSegment.nextOffset()
  return
}{code}
It has since been consolidated into the same path. We can probably keep that. I'll submit a PR.
~~~~

4.

~~~~
Discussed with Jun a bit offline. This is a bit unlikely in practice as the hard failure has to happen after we write the recovery point (which happens in a scheduled thread) and before we roll/flush the truncated segment. Still, good to fix it. Also, it's easier to reason about if we only update the recovery point after we roll segments. While looking at the code, we noticed a few more edge cases. Will try to fix them at the same time.
~~~~

---

## KAFKA-10173: BufferUnderflowException during Kafka Streams Upgrade

https://issues.apache.org/jira/browse/KAFKA-10173

Given fix versions: 2.4.2, 2.5.1, 2.6.0
JIRA affects (masked from the system): 2.5.0

- `KAFKA-10173@2.5.0`: config 2.5.0, metadata answer **affected** (listed_affected)
- `KAFKA-10173@2.4.1`: config 2.4.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.3.1, 2.5.0, 2.3, 2.5.1, 2.6, 2.4.0, 2.3.0, 2.6.0, 2.4, 2.4.1, v2.5.0

### Description

~~~~
I migrated a Kafka Streams application from version 2.3.1 to 2.5.0. I followed the steps described in the upgrade guide and set the property {{migrate.from=2.3}}. On my dev system with just one running instance I got the following exception:

{noformat}
stream-thread [0-StreamThread-2] Encountered the following error during processing:
java.nio.BufferUnderflowException: null
	at java.base/java.nio.HeapByteBuffer.get(Unknown Source)
	at java.base/java.nio.ByteBuffer.get(Unknown Source)
	at org.apache.kafka.streams.state.internals.BufferValue.extractValue(BufferValue.java:94)
	at org.apache.kafka.streams.state.internals.BufferValue.deserialize(BufferValue.java:83)
	at org.apache.kafka.streams.state.internals.InMemoryTimeOrderedKeyValueBuffer.restoreBatch(InMemoryTimeOrderedKeyValueBuffer.java:368)
	at org.apache.kafka.streams.processor.internals.CompositeRestoreListener.restoreBatch(CompositeRestoreListener.java:89)
	at org.apache.kafka.streams.processor.internals.StateRestorer.restore(StateRestorer.java:92)
	at org.apache.kafka.streams.processor.internals.StoreChangelogReader.processNext(StoreChangelogReader.java:350)
	at org.apache.kafka.streams.processor.internals.StoreChangelogReader.restore(StoreChangelogReader.java:94)
	at org.apache.kafka.streams.processor.internals.TaskManager.updateNewAndRestoringTasks(TaskManager.java:401)
	at org.apache.kafka.streams.processor.internals.StreamThread.runOnce(StreamThread.java:779)
	at org.apache.kafka.streams.processor.internals.StreamThread.runLoop(StreamThread.java:697)
	at org.apache.kafka.streams.processor.internals.StreamThread.run(StreamThread.java:670)
{noformat}

I figured out, that this problem only occurs for stores, where I use the suppress feature. If I rename the changelog topics during the migration, the problem will not occur. 
~~~~

### Comments (20)

1.

~~~~
Thanks for the report [~karsten.schnitter] . I'm sorry for the trouble.

I've marked it as a blocker for the ongoing 2.5.1 release. I'll investigate the root cause ASAP.
~~~~

2.

~~~~
Would be great to know if this might be a blocker for 2.6, too. \cc [~rhauch] (just as a potential heads-up).
~~~~

3.

~~~~
[~mjsax], [~vvcephei]: I guess whether we should include this in 2.6 depends on the timing and the risk. We'll start cutting RCs pretty soon.
~~~~

4.

~~~~
Hi [~karsten.schnitter] ,

I've had a chance now to look into this. It's actually quite strange, although I'm probably missing something.

That stacktrace means that Streams is actually having trouble deserializing data written with changelog schema version 2, which IIRC was introduced in version 2.4.0. If you only ran the application with version 2.3.1, stopped it, then started it with version 2.5.0, it shouldn't be possible to hit this branch, as it means reading data that 2.3.1 couldn't possibly have written.

The only thing I can imagine is if you had previously run Streams with a version _less than_ 2.3.0 AND if some of your data happened to contain a header with the name "v", then it could lead to this kind of corruption. But, in that case, you should have gotten an exception while running with version 2.3.1 already. So, this doesn't sound like it fits.

The only thing that seems to fit your report is that the serialization/deserialization logic is actually wrong. But it's quite heavily tested, and has been exercised in production for quite a while also. There is always the possibility of a rare edge case, though. I've just given the logic another pass, and I'm not seeing what could be the problem. Is there any chance you could find the changelog record that caused this exception and just send me the bytes for it?

Short of that, I'm not sure how to proceed.

-John

P.s., while reviewing the code, I did find one flaw, which I've submitted [https://github.com/apache/kafka/pull/8905] for. I doubt that was your problem, but we might as well fix it anyway.
~~~~

5.

~~~~
[~rhauch] and [~mjsax] , you can consider my last comment for yourselves, but it doesn't seem like this would need to block 2.6.0. The code in question doesn't seem to have changed since 2.4.0.
~~~~

6.

~~~~
Hi [~vvcephei],

The application has been running in different version for quite some time. Since it consumes the Kafka dependencies via Spring, I am very confident, that it never ran in any 2.4.x version. It started with earlier versions though. I try to get the offending message, but this is not an easy endeavour so far. I am not sure what topic to look at: Do I need to investigate the suppress topics or the original store changelog? Or can this stem from even other topics? How can I identify the message within the topic? And lastly once identified, how can I get the bytes? Soo far I am using the Kafka-console-consumer.sh for these kinds of investigations. But as far as I know this is not well suited to extract the bytes, right?
~~~~

7.

~~~~
Hi [~vvcephei],

after trying for the whole weekend, I finally found a solution to provide the messages. My approach is to change {{org.apache.kafka.streams.state.internals.BufferValue}} in a way to log during deserialisation:

{code:java}
public final class BufferValue {
        // omitted

	private static final Logger LOG = LoggerFactory.getLogger(BufferValue.class);

	static BufferValue deserialize(final ByteBuffer buffer) {
		final ProcessorRecordContext context = ProcessorRecordContext.deserialize(buffer);

		LOG.debug("Deserialize with context <{}>", context);

		try {
			final byte[] priorValue = extractValue(buffer);

			final byte[] oldValue;
			final int oldValueLength = buffer.getInt();
			if (oldValueLength == NULL_VALUE_SENTINEL) {
				oldValue = null;
			} else if (oldValueLength == OLD_PREV_DUPLICATE_VALUE_SENTINEL) {
				oldValue = priorValue;
			} else {
				oldValue = new byte[oldValueLength];
				buffer.get(oldValue);
			}

			final byte[] newValue = extractValue(buffer);

			return new BufferValue(priorValue, oldValue, newValue, context);
		} catch (BufferUnderflowException underflow) {
			LOG.error("Error deserializing buffer <{}>", bytesToHex(buffer.array()));
			throw underflow;
		}
	}

	private static final char[] HEX_ARRAY = "0123456789ABCDEF".toCharArray();

	private static String bytesToHex(byte[] bytes) {
		char[] hexChars = new char[bytes.length * 2];
		for (int j = 0; j < bytes.length; j++) {
			int v = bytes[j] & 0xFF;
			hexChars[j * 2] = HEX_ARRAY[v >>> 4];
			hexChars[j * 2 + 1] = HEX_ARRAY[v & 0x0F];
		}
		return new String(hexChars);
	}

        // omitted
}
{code}

The result of this is somewhat confusing to me:

{noformat}
DEBUG.   Deserialize with context <ProcessorRecordContext{topic='logs-ingress', partition=57, offset=0, timestamp=1592648746703, headers=RecordHeaders(headers = [], isReadOnly = false)}>
ERROR.   Error deserializing buffer <00000172D14346CF00000000000000000000000C6C6F67732D696E6772657373000000390000000000000059FFFFFFFF00000051080110AC051A2436346139616437662D313838352D346234342D613163302D633134346565633162636665222436346139616437662D313838352D346234342D613163302D633134346565633162636665FFFFFFFF00000172D14346CF>
{noformat}

# The DEBUG log of the context tells me, that a message from my main topic was read. I would have expected a message from a store changelog. I guess the context is misleading here?
# The ERROR log has a rather short message, that fits much better to a store changelog. As a background: This is most likely a protobuf message containing two uuids encoded as strings together with some integer or long numbers.

The system I used was freshly created on Saturday, June 20th. It is running a Kafka Cluster on version 2.4.1 and the Kafka Streams application in version 2.3.1. The error was recorded with the same Kafka Streams application ugraded to v2.5.0 with the modification from above. Since there are two stream threads, I can provide another buffer that fails:

{noformat}
ERROR.   Error deserializing buffer <00000172D1434655000000000000006F0000000C6C6F67732D696E6772657373000000180000000000000059FFFFFFFF00000051080110AC051A2436346139616437662D313838352D346234342D613163302D633134346565633162636665222436346139616437662D313838352D346234342D613163302D633134346565633162636665FFFFFFFF00000172D1434655>
{noformat}

Best Regards,
Karsten
~~~~

8.

~~~~
Wow, thanks for that great information, [~karsten.schnitter] !

I was able to reproduce your exception with this code:
{code:java}
public final class BufferValue {
...

public static void main(String[] args) {
    final String str="00000172D14346CF00000000000000000000000C6C6F67732D696E6772657373000000390000000000000059FFFFFFFF00000051080110AC051A2436346139616437662D313838352D346234342D613163302D633134346565633162636665222436346139616437662D313838352D346234342D613163302D633134346565633162636665FFFFFFFF00000172D14346CF";
    final byte[] arr = hexStringToByteArray(str);

    final BufferValue deserialize = deserialize(ByteBuffer.wrap(arr));
    System.out.println(deserialize);
}

public static byte[] hexStringToByteArray(String s) {
    int len = s.length();
    byte[] data = new byte[len / 2];
    for (int i = 0; i < len; i += 2) {
        data[i / 2] = (byte) ((Character.digit(s.charAt(i), 16) << 4)
            + Character.digit(s.charAt(i+1), 16));
    }
    return data;
}

...
}
{code}
I also see the context deserialized as:
{code:java}
ProcessorRecordContext{topic='logs-ingress', partition=57, offset=0, timestamp=1592648746703, headers=RecordHeaders(headers = [], isReadOnly = false)}{code}
Note, this is not the record context of the suppression changelog, it's the context of the input record that got suppressed.

Incidentally, the context I get for that second record is:
{code:java}
ProcessorRecordContext{topic='logs-ingress', partition=24, offset=111, timestamp=1592648746581, headers=RecordHeaders(headers = [], isReadOnly = false)}{code}
One hypothesis I was hoping to verify was that we are in fact correctly attempting to deserialize a "version 2" record, not another record we're erroneously interpreting as "version 2". It looks like this is the case, otherwise it seems like we'd be unlikely to get a valid-looking ProcessorRecordContext. Still, maybe you can confirm that your topic "logs-ingress" really has a partition 57, and that the record at offset 0 has timestamp 1592648746703? And also, I guess, that it doesn't have any headers?

At least, that looks like a plausible timestamp:
{code:java}
jshell> new Date(1592648746703L)
$1 ==> Sat Jun 20 05:25:46 CDT 2020

{code}
Just looking at what is getting unpacked from this buffer (which ultimately results in that exception):
 # the context above
 # a "prior value" for this key (a byte array of length 89) of (hex): "FFFFFFFF00000051080110AC051A2436346139616437662D313838352D346234342D613163302D633134346565633162636665222436346139616437662D313838352D346234342D613163302D633134346565633162636665"
 ** Surprisingly, the "prior value" for the other record you gave me is exactly the same! It comes from a different partition of logs-ingress, though, so I don't think it could be the same record.
 # a null "old value"
 # When we come to extract the "new value" part, we read the length of the new value as 370, but at this point, we're at position 141 in the buffer, which is only 145 bytes long, so we get the underflow because we try to read 370 bytes, but there are only 4 bytes remaining.

Unfortunately, I still don't have any good answers at this point.

I think it's suspicious that we are reading a record that is apparently from offset zero of its topic partition, yet it has a "prior value".

[~karsten.schnitter], I'm sorry to put this back on you, but can you try to:
 # Verify that the context we got above looks legitimate? If not, it'll help narrow down where my serializer went wrong.
 # If you're able, perhaps you can take a look at the input records from the partition and offset that we see encoded here to see if it has the same key as the record we're trying to restore from the suppression changelog?
 # In addition to the information you've captured so far, can you also try to dump out the whole record we're restoring in `restoreBatch`? That one will let me look at the metadata for the changelog entry itself, not just the record we suppressed.
 # I'm really sorry to do this to you, but perhaps you can add some more debugging to the ByteBuffer#serialize path as well, so that we can see what actually went in when we wrote these records?

I'm still a little mystified about how we even wind up in this position... We're deserializing a version 2 changelog record, which must have been written by the _upgraded_ application, since version 2 was introduced in 2.4.0. But if all you're doing to repro this is run the app with 2.3.1 and then restarting with version 2.5.0, it shouldn't even be possible to get a version 2 record in the restore path.

I'll keep trying to figure it out, but any further assistance you can provide is greatly appreciated. Thanks (and sorry).

-John
~~~~

9.

~~~~
Hi [~vvcephei],

the original message is lost due to retention. I will implement the additional logging and start from a clean slate once again. Today, the system was unavailable to me, but I hope to get to more testing tomorrow or the day after. If you have any further suggestions, were I can add logging statements to extract information, please let me know. So far I can verify, that the context looks legitimate. There are actually 60 partitions, so 57 is fine. Can the equal priors be explained by very similar data in both partitions? It is not unlikely, that both partitions may have been aggregated to very similar data.

Best Regards,
Karsten
~~~~

10.

~~~~
Hi [~karsten.schnitter] ,

Thanks for your efforts. I'm also adding some additional system tests specifically for suppression in combination with an upgrade from 2.3.1 to 2.5.0.

Thanks for the confirmation about the context. I think logging both the serialization and deserialization path should provide a lot of clarity for now. The stacktrace above implies the record was written by the 2.5.0 application, so it will be interesting to see if it really prints out your serialization log messages.

I'll also add some "trace" level log messages to suppression in AK to help in future debugging efforts.

If you're able, I guess this should be sufficient for now:
 * Log the who record during restore
 * Log the data in InMemoryTimeOrderedKeyValueBuffer#logValue, both the Key and BufferValue before serialization and the byte array that we return from BufferValue#serialize

In response to your last question, certainly! You'd know best what data this application is producing. If the value for two different records could be exactly the same, then the identical priorValue may be expected.

What doesn't seem expected to me is that there would be a priorValue at all for the record that was at offset zero of the input. It makes me wonder if the application state is corrupted somehow, but I can't wrap my head around _how_.

I'll let you know how my testing efforts progress today.

-John
~~~~

11.

~~~~
Hi [~karsten.schnitter] ,

I have "good" news! I managed to reproduce this exception in a system test:
{code:java}
java.nio.BufferUnderflowException
	at java.nio.HeapByteBuffer.get(HeapByteBuffer.java:151)
	at java.nio.ByteBuffer.get(ByteBuffer.java:715)
	at org.apache.kafka.streams.state.internals.BufferValue.extractValue(BufferValue.java:94)
	at org.apache.kafka.streams.state.internals.BufferValue.deserialize(BufferValue.java:83)
	at org.apache.kafka.streams.state.internals.InMemoryTimeOrderedKeyValueBuffer.restoreBatch(InMemoryTimeOrderedKeyValueBuffer.java:368)
	at org.apache.kafka.streams.processor.internals.CompositeRestoreListener.restoreBatch(CompositeRestoreListener.java:89)
	at org.apache.kafka.streams.processor.internals.StateRestorer.restore(StateRestorer.java:92)
	at org.apache.kafka.streams.processor.internals.StoreChangelogReader.processNext(StoreChangelogReader.java:350)
	at org.apache.kafka.streams.processor.internals.StoreChangelogReader.restore(StoreChangelogReader.java:94)
	at org.apache.kafka.streams.processor.internals.TaskManager.updateNewAndRestoringTasks(TaskManager.java:401)
	at org.apache.kafka.streams.processor.internals.StreamThread.runOnce(StreamThread.java:779)
	at org.apache.kafka.streams.processor.internals.StreamThread.runLoop(StreamThread.java:697)
	at org.apache.kafka.streams.processor.internals.StreamThread.run(StreamThread.java:670){code}
I know it's a pain for you to debug on your end. Please feel free to continue if you like to, but I should be able to make progress by iterating on the test for now. I'll let you know what I learn.

Thanks so much for your help,

-John
~~~~

12.

~~~~
Hi [~vvcephei],

That is great news. Actually, I had some problems with my setup and could not do further testing today.

Best Regards,
Karsten
~~~~

13.

~~~~
Ok, I'm horrified and embarrassed to report that I know what the problem is, as well as the solution. I'll update my PR tomorrow, and I'll re-escalate this ticket to a blocker for 2.5.1 and 2.6.0.

In a nutshell, although we have a version number on these changelog records so that we can deserialize old formats, I subtly changed the serialization format in 2.4.0 without updating the version number, so although the serialization format is incompatible between 2.3.1 and 2.5.0, they both claim to be at "version 2" (I was mistaken about this before).

This mistake happens to also render the serialization compatibility test I had written to be ineffectual.

And I've also just discovered that our system test that covers application upgrades had suffered an oversight that made it skip these versions.

Needless to say, in addition to fixing this bug, I'm fixing the serialization test to avoid using the same code paths as the application, and I'm also revamping the upgrade system test to be sure we'll have a much more robust test going forward.

Although this bug was introduced in 2.4.0, I'd still classify it as a blocker, since it's so severe (you simply can't upgrade the application until we fix it).

Thanks for the excellently detailed report, and, again, my sincere apologies,

-John
~~~~

14.

~~~~
cc [~rhauch]
~~~~

15.

~~~~
Hi [~vvcephei],

I am really glad to hear, that you found the problem and the solution. No need to feel embarrassed though. I really appreciate all the hard work, that goes into this project. Keep it up.

One more background information: I consume the Kafka Streams dependency transitively through Spring Boot. Spring skipped the 2.4.x releases and went directly from 2.3.1 to 2.5.0. So I would expect, that more people will have this kind of migration.

Best Regards,
Karsten

~~~~

16.

~~~~
Thanks for that information, [~karsten.schnitter] . It really reinforces the importance of blocking the 2.5.1 bugfix release in particular.
~~~~

17.

~~~~
Ok, I've just merged the fix ([https://github.com/apache/kafka/pull/8905] ), and I'm backporting it now.

To control the scope of the change, I've separated the upgrade system tests out for a second PR, which I'll submit next week. I did run them locally, and they pass after #8905, so I have confidence the bug is really fixed.
~~~~

18.

~~~~
Ok, the fix is now backported all the way back to 2.4. I'll leave this ticket open until I get the system test PR in.
~~~~

19.

~~~~
Here's the system test PR: https://github.com/apache/kafka/pull/8938
~~~~

20.

~~~~
Hey all, I'm resolving this ticket to unblock the 2.6.0 release. I'm still working on backporting the system test fixes.
~~~~

---

## KAFKA-10284: Group membership update due to static member rejoin should be persisted

https://issues.apache.org/jira/browse/KAFKA-10284

Given fix versions: 2.5.2, 2.6.1, 2.7.0
JIRA affects (masked from the system): 2.3.0, 2.4.0, 2.5.0, 2.6.0

- `KAFKA-10284@2.3.0`: config 2.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-10284@2.2.2`: config 2.2.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
For known static members rejoin, we would update its corresponding member.id without triggering a new rebalance. This serves the purpose for avoiding unnecessary rebalance for static membership, as well as fencing purpose if some still uses the old member.id. 

The bug is that we don't actually persist the membership update, so if no upcoming rebalance gets triggered, this new member.id information will get lost during group coordinator immigration, thus bringing up the zombie member identity.

The bug find credit goes to [~hachikuji] 
~~~~

### Comments (17)

1.

~~~~
[https://github.com/apache/kafka/blob/trunk/core/src/main/scala/kafka/coordinator/group/GroupCoordinator.scala#L1042]
~~~~

2.

~~~~
[~bchen225242] Thanks for the find. Just trying to clarify that "bring up the zombie member ID" would break correctness, since if the zombie member still exists, it may be able to commit offsets which would rewind the position. Is that right?
~~~~

3.

~~~~
If we have a combined scenario like below:
 # A static member X joins the group and updates member.id to M1, then gets stuck
 # Another static member Y with the same instance.id joins and updates member.id to M2, while starts working and commit offsets
 # The group coordinator migrates, and the member.id for the same static member rewinds to M1
 # The static member X goes back online, and validated. It would try to fetch from Y's committed offset

In this flow, I don't think we are violating the offset committing policy here. 

The only downside I could think of is that there is only one member Y who will get fenced by itself after the immigration as stated in the description. [~guozhang]
~~~~

4.

~~~~
Fair enough. So it seems not a correctness breaking issue at the moment.
~~~~

5.

~~~~
Hi [~bchen225242]/[~guozhang],

I've raised the bug related to the same issue 6 days ago. Please look at it once.

https://issues.apache.org/jira/browse/KAFKA-10285

 

Analysis,

`when i've not restarted the broker and restarted consumer, I could see below logs` 
 ```
 [2020-07-16 13:56:17,189] INFO [GroupCoordinator 1001]: Preparing to rebalance group 0 in state PreparingRebalance with old generation 0 (__consumer_offsets-48) (reason: Adding new member 1-1594907777144 with group instanceid Some(1)) (kafka.coordinator.group.GroupCoordinator)
 [2020-07-16 13:56:17,236] INFO [GroupCoordinator 1001]: Stabilized group 0 generation 1 (__consumer_offsets-48) (kafka.coordinator.group.GroupCoordinator)
 [2020-07-16 13:56:17,282] INFO [GroupCoordinator 1001]: Assignment received from leader for group 0 for generation 1 (kafka.coordinator.group.GroupCoordinator)

********
 [2020-07-16 13:59:33,613] INFO [GroupCoordinator 1001]: Static member Some(1) with unknown member id rejoins, assigning new member id 1-1594907777335, while old member 1-1594907777144 will be removed. (kafka.coordinator.group.GroupCoordinator)
 [2020-07-16 13:59:33,635] INFO [GroupCoordinator 1001]: Static member joins during Stable stage will not trigger rebalance. (kafka.coordinator.group.GroupCoordinator)
 ```
 when restarted the broker, I could see broker is expecting some other member.id(old member.id of consumer)
 ```
 2020-07-16 14:04:04,953] ERROR given member.id 1-1594907777335 is identified as a known static member 1,but not matching the expected member.id 1-1594907777144 (kafka.coordinator.group.GroupMetadata)
 ```

 

 
~~~~

6.

~~~~
You know, I think we actually hit this too, but weren't able to recognize the problem at the time. A few weeks ago one of our StreamThreads/Consumers seemed to "take off" from the group at some point, as evidenced by the steadily increasing last-rebalance-seconds-ago metric (whereas the other members had rebalanced multiple times since then). Right before this occurred we saw that same error message in the logs:

 
{code:java}
ERROR given member.id X is identified as a known static member 1,but not matching the expected member.id Y (kafka.coordinator.group.GroupMetadata)
{code}
Unfortunately we killed the client trying to remotely debug it so we couldn't get any more useful information. Would you say that this was mysterious encounter was likely due to the bug reported here? [~guozhang] [~bchen225242]

 
~~~~

7.

~~~~
[~akshaysh] I didn't see any trace that the group coordinator gets migrated in the pasted ticket, so it might be a separate issue.

[~ableegoldman] Well, the symptom matches, but I don't know for sure if this is the same cause :)
~~~~

8.

~~~~
What [~ableegoldman] described seems aligned to this, BUT I thought that fenced instance Y should still try to rejoin the group, but in [~ableegoldman] that thread did not try to rejoin at all?
~~~~

9.

~~~~
At initial, Group Coordinator will assign member id to the new joined consumer i.e X with generation id 1, when the consumer take off at the same point and try to rejoin there be no re-balance(i.e generation id will be 1), but group coordinator will assign new member id to the consumer i.e Y. Now, when broker restart due to some reason, groupmetadatamanager will reload the metadata and expects that member.id to be present, he is now expecting X member.id. and that's why consumer is fenced.

1) Is this a expected behaviour?

2) when consumer member id changes, groupmetadatamanager not updates new member.id information?

3) consumer is fenced with new instance, even single consumer is running. Why?

[~bchen225242] [~guozhang]

 

 
~~~~

10.

~~~~
Nope, it just spun in a loop where it would poll and then call Consumer#position to try and initialize some metadata. Poll just returned empty I guess and Consumer#position continued to throw TimeoutException. 

The TimeoutException part seems pretty weird, so maybe it was an unrelated bug (or some other issue like a hung socket being the primary/only guess we had). I just thought of it because it definitely happened immediately after a "id does not match expected member.id" error.

I actually still have some of the broker and client side logs from around this incident, if that might help. But again, I'm not really sure if it could be related to this or not
~~~~

11.

~~~~
[~bchen225242] Hmm.. Not totally sure I buy this:

> A static member X joins the group and updates member.id to M1, then gets stuck
> Another static member Y with the same instance.id joins and updates member.id to M2, while starts working and commit offsets
> The group coordinator migrates, and the member.id for the same static member rewinds to M1
> The static member X goes back online, and validated. It would try to fetch from Y's committed offset

Why would member X fetch Y's committed offset? If it doesn't know it had been fenced temporarily, it might just commit its latest offsets. This does seem like a correctness problem to me.
~~~~

12.

~~~~
That's a good observation, I forgot that for static members they don't actually do another Fetch offset immediately after they rejoin the group. You should be right about this, and I haven't thought about the scenario where EOS and static membership are both turned on.
~~~~

13.

~~~~
Resign from this ticket for now, others feel free to pick up.
~~~~

14.

~~~~
[~bchen225242] [~hachikuji] Is this a correctness problem for all applications or only EOS?
~~~~

15.

~~~~
I would say for all. Let me check if [~feyman] is interested in picking this up.
~~~~

16.

~~~~
Checked with [~bchen225242] offline, and I just reproduced the issue with the procedure as in the attachment, happy to know if there are more failure scenarios related.[^How to reproduce the issue in KAFKA-10284.md]
~~~~

17.

~~~~
Just FYI, created a PR: https://github.com/apache/kafka/pull/9270
~~~~

---

## KAFKA-10340: Source connectors should report error when trying to produce records to non-existent topics instead of hanging forever

https://issues.apache.org/jira/browse/KAFKA-10340

Given fix versions: 2.6.2, 2.7.1, 2.8.1, 3.0.0
JIRA affects (masked from the system): 2.5.1, 2.6.1, 2.7.0, 2.8.0

- `KAFKA-10340@2.8.0`: config 2.8.0, metadata answer **affected** (listed_affected)
- `KAFKA-10340@2.5.0`: config 2.5.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.0, 2.7, 2.7.1, 2.6, 2.6.2, 2.8, 2.8.0, 2.8.1

### Description

~~~~
Currently, a source connector will blindly attempt to write a record to a Kafka topic. When the topic does not exist, its creation is controlled by the {{auto.create.topics.enable}} config on the brokers. When auto.create is disabled, the producer.send() call on the Connect worker will hang indefinitely (due to the "infinite retries" configuration for said producer). In setups where this config is usually disabled, the source connector simply appears to hang and not produce any output.

It is desirable to either log an info or an error message (or inform the user somehow) that the connector is simply stuck waiting for the destination topic to be created. When the worker has permissions to inspect the broker settings, it can use the {{listTopics}} and {{describeConfigs}} API in AdminClient to check if the topic exists, the broker can {{auto.create.topics.enable}} topics, and if these cases do not exist, either throw an error.

With the recently merged [KIP-158|https://cwiki.apache.org/confluence/display/KAFKA/KIP-158%3A+Kafka+Connect+should+allow+source+connectors+to+set+topic-specific+settings+for+new+topics], this becomes even more specific a corner case: when topic creation settings are enabled, the worker should handle the corner case where topic creation is disabled, {{auto.create.topics.enable}} is set to false and topic does not exist.
~~~~

### Comments (10)

1.

~~~~
After investigation, if the {{auto.create.topics.enable}} is disabled, the producer.send will get only {{TimeoutException}} and no other valuable clue for users. So, I will improve the logging in this area.

Proposed to add 2 logs:

1. When the topic creation is disabled or topic is existed:

log.debug({color:#008000}"The topic creation setting is disabled or the topic name {} is already created. " {color}+
 {color:#008000}"If the topic doesn't exist, we'll rely on the auto.create.topics.enable setting in broker side " {color}+
 {color:#008000}"to see if the topic can be auto created or not"{color}, topic);

2. Before the producer send the record:

log.trace({color:#008000}"{} is going to send record to {}"{color}, WorkerSourceTask.{color:#000080}this{color}, topic);

 

So, for the request to let user know it's stuck waiting for the destination topic to be created is now basically cannot know from client side because the producer.send will block on waitOnMetadata method, which will keep trying until timeout. There are many possible reasons for this timeout. It's hard to tell.

 

And the dynamically {{describeConfigs}} to get the broker setting is also not easy because the broker name (we need broker name to describeConfig) is not kept in the config, and also there's no other places in Kafka to check the broker setting before doing something. I'd prefer to keep it as is because this behavior(auto create topic or not while producer.send) applied for all kafka, not only for connectors.

 

Thanks.
~~~~

2.

~~~~
The logging changes are certainly an improvement, but don't address the underlying issue: source tasks and their producers hang and remain active (i.e., are not closed) indefinitely, even after the task is scheduled for shutdown. If several task instances are scheduled for shutdown and then recreated (which may happen as a result of rebalance or connector reconfiguration), any of those instances in this bad state will keep sending metadata requests to the broker from their producers, and any resources allocated by the {{SourceTask}} instances will not be freed.

This creates a resource leak and the impact is substantial enough that I believe the ticket should be reopened until it has been addressed with a functional fix.
~~~~

3.

~~~~
Hi, guys!

According to [KAFKA-5295](https://issues.apache.org/jira/browse/KAFKA-5295) I supposed that now topics are always created by AdminClient if  "topic.creation.enable = true".

But now I see that topics are created by AdminClient, only when "topic.creation.enable = true" and "topic.creation" parameters are used.
But I wonder why?
Why do not create topics always by AdminClient if  "topic.creation.enable = true"?
 
It will partially solve the current problem (described in this ticket) and only the case with "topic.creation.enable = false" is the problem.
 
 
And also current approach can be a problem for us - we wanted to set "auto.create.topics.enable = false" on Kafka cluster by default. But we cannot do that, because our connectors can be created with 
"topic.creation" parameters or without them, we cannot guarantee that. And in case connectors have not this property, we get errors.

 

Any comments and your opinion is appreciated! 
~~~~

4.

~~~~
And also I cannot understand, why we even have the property "topic.creation.enable" and do not create all topics by AdminClient? Isn't it a better approach to create topics always explicitly using AdminClient than to rely on auto creation?

And also I cannot see how can it has a bad impact on users. Why someone may want to set "topic.creation.enable = false"?

According to KIP-158 we have an option to set replication.factor and partitions to -1 to use the broker's default value. So why we cannot always create topics by AdminClient and use these broker's default values in case connector does not have any "topic.creation" properties?

 

As far as I understand this will completely solve the problem described in this ticket. And also people will be able to set "auto.create.topics.enable = false" on Kafka cluster without any impact.

 

Please, correct me if I am wrong.
~~~~

5.

~~~~
[~xakassi] wrote:

{quote}
And also I cannot understand, why we even have the property "topic.creation.enable" and do not create all topics by AdminClient? Isn't it a better approach to create topics always explicitly using AdminClient than to rely on auto creation?
{quote}

When we introduced KIP-158 to allow Connect to source connectors to specify the rules for creating topics, it was important that we maintained backward compatibility. Many people upgrade Kafka and Connect simply to get fixes, and do not want new features they don't know about nor wish to use enabled by default. This is an essential aspect of all KIPs and AK features, even when by default most users *probably* would want to use the feature.  

{quote}
According to KIP-158 we have an option to set replication.factor and partitions to -1 to use the broker's default value. So why we cannot always create topics by AdminClient and use these broker's default values in case connector does not have any "topic.creation" properties?

As far as I understand this will completely solve the problem described in this ticket.
{quote}
It actually would not solve the problem. If Connect were to have the behavior you suggest, then we'd still run into the issue when the broker has autocreation of topics disabled *and* the particular source connector did not specify the topic creation rules.

The bottom line is that many things would be made easier *for some people* if we could easily change defaults, but upgrading would become painfully difficult for those that don't wish to use those new features or behaviors. By maintaining backward compatibility, we dramatically reduce the overhead and risk of upgrades to get fixes, which is an important characteristic that the AK community cherishes.

We will have the option in 3.0 to *change* defaults and behaviors -- it is a major release that may not be entirely backward compatible. Obviously, we'll want to not break things unnecessarily, but changing the default `topic.creation.enable = true` will be one such change we are very much looking forward to making.
~~~~

6.

~~~~
Merged to `trunk` and backported to:
* `2.7` for inclusion in the upcoming 2.7.1
* `2.6` for inclusion in the upcoming 2.6.2

The `2.8` branch is currently blocked for the 2.8.0 release, so I've created https://github.com/apache/kafka/pull/10238 for the 2.8 backport -- either if this is approved as a 2.8.0 blocker or after 2.8.0 has been released.

Leaving this issue open until 2.8 is addressed.
~~~~

7.

~~~~
Temporarily removed 2.6.2 from the Fix Version so I can proceed with the 2.6.2 release, since it's already been cherrypicked to 2.6 This should be added back once the ticket is resolved
~~~~

8.

~~~~
[~vvcephei] Are we picking this change in 2.8? 

I wonder if this we should actually resolve this JIRA as the fix has been made to trunk, 2.6 and 2.7. If John decides to pull it in 2.8, then we can just add 2.8.0 to Fix Versions. That would enable us to run the 2.6.2 and 2.7.1 releases without having to tweak Fix Versions
~~~~

9.

~~~~
{quote}

I wonder if this we should actually resolve this JIRA as the fix has been made to trunk, 2.6 and 2.7. If John decides to pull it in 2.8, then we can just add 2.8.0 to Fix Versions. That would enable us to run the 2.6.2 and 2.7.1 releases without having to tweak Fix Versions.

{quote}

That sounds fine with me. I'll will add the 2.6.2 fix, mark this as resolved. We can then add the 2.8 version (either `2.8.0` or `2.8.1`) if/when [https://github.com/apache/kafka/pull/10238] is merged to 2.8.
~~~~

10.

~~~~
I cherry-picked the original PR (https://github.com/apache/kafka/pull/10016) to the `2.8` branch (now that it's not frozen) and updated the fixed versions.

This completes all of the planned work for this issue.
~~~~

---

## KAFKA-10557: Missing docs when describing topic configs including documentation

https://issues.apache.org/jira/browse/KAFKA-10557

Given fix versions: 2.6.1, 2.7.0
JIRA affects (masked from the system): 2.6.0

- `KAFKA-10557@2.6.0`: config 2.6.0, metadata answer **affected** (listed_affected)
- `KAFKA-10557@2.5.1`: config 2.5.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
When describing topic or broker configs with the AdminClient, we can request the documentation of configuration settings to be included.

This does not work with topic configs. The issue lies in this line:
https://github.com/apache/kafka/blob/trunk/core/src/main/scala/kafka/server/AdminManager.scala#L767

This uses a KafkaConfig object to look up topic configs. Hence for configurations that have different names between KafkaConfig and LogConfig, no documentation is found!
~~~~

---

## KAFKA-10582: Mirror Maker 2 not replicating new topics until restart

https://issues.apache.org/jira/browse/KAFKA-10582

Given fix versions: 3.5.0
JIRA affects (masked from the system): 2.5.1

- `KAFKA-10582@2.5.1`: config 2.5.1, metadata answer **affected** (listed_affected)
- `KAFKA-10582@2.5.0`: config 2.5.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.5.1, 2.6.1, 2.7.0, 3.0.0, 3.3.1

### Description

~~~~
We are using Mirror Maker 2 from the 2.5.1 release for replication on some clusters.  Replication is working as expected for existing topics.  When we create a new topic, however, Mirror Maker 2 creates the replicated topic as expected but never starts replicating it.  If we restart Mirror Maker 2 within 2-3 minutes the topic starts replicating as expected.  From documentation we haveve seen it appears this should start replicating without a restart based on the settings we have.

*Example:*
Create topic "mytesttopic" on source cluster
MirrorMaker 2 creates "source.mytesttopioc" on target cluster with no issue
MirrorMaker 2 does not replicate "mytesttopic" -> "source.mytesttopic"
Restart MirrorMaker 2 and now replication works for "mytesttopic" -> "source.mytesttopic"

*Example config:*
name = source->target
group.id = source-to-target

clusters = source, target
source.bootstrap.servers = sourcehosts:9092
target.bootstrap.servers = targethosts:9092
source->target.enabled = true
source->target.topics = .*
target->source = false
target->source.topics = .*
replication.factor=3
checkpoints.topic.replication.factor=3
heartbeats.topic.replication.factor=3
offset-syncs.topic.replication.factor=3
offset.storage.replication.factor=3
status.storage.replication.factor=3
config.storage.replication.factor=3
tasks.max = 16
refresh.topics.enabled = true
sync.topic.configs.enabled = true
refresh.topics.interval.seconds = 300
refresh.groups.interval.seconds = 300
readahead.queue.capacity = 100
emit.checkpoints.enabled = true
emit.checkpoints.interval.seconds = 5
~~~~

### Comments (12)

1.

~~~~
Hello! 
How do you run MM2?   How many instances of MM2 do you have? 
~~~~

2.

~~~~
We are running MM2 as a standalone cluster with one instance in each data center doing one way replication.
Instance in DC1 replicates from DC2->DC1.  
Instance in DC2 replicates from DC1->DC2.

~~~~

3.

~~~~
Which cluster do you specify to run MM2? Is it different for the instances? 
Does it work,when you run only one instance of MM2? 
~~~~

4.

~~~~
So we have one instance replicating one direction.  Then another instance replicating the other direction.  In effect both clusters are replicating.

The new topics replicate after a restart but not before in any setup we've tried, even using only once instance.
~~~~

5.

~~~~
I have the same problem, but in my case just restarting the mirror maker does not help.

Here is what I have to do: stop the mirror maker, then delete the *mm2-offset-syncs.<target cluster>.internal* topic on the source cluster, and then start the mirror maker again.

I am using the mirror maker that comes with Confluent 6.1.0, and I run 3 instances on the same hosts as the target cluster.
~~~~

6.

~~~~
Actually, it does work without cleaning up that internal topic, but it takes much longer time to start replicating.

I guess, I was not patient enough.

Is it some timeout that can be configured?
~~~~

7.

~~~~
Hi,

I'm facing same problem. I'm using kafka 2.6.1. In my case, kafka restart on one instance works if restart done within few minutes of new topic creation. However, if it takes long time to restart then restarting on one instance doesn't help and both instances needs to be restarted in parallel (stop both instance and start both instance).

Please let me know if there is any workaround to overcome this problem.

Best Regards,

Ravi
~~~~

8.

~~~~
This still happens in version 2.7.0. I really don't understand why. In my enviroment, creating a new topic is regularly and must restart mm2 continuously it is very uncomfortable :(
~~~~

9.

~~~~
I got the same issue and don't understand why this happens. I am using Kafka 3.0.0 with 3 passive standby instances where the topics are mirrored to, but it works for new topics only after the restart like described in other comments :( 
~~~~

10.

~~~~
I'm having similar issue with latest version of kafka 3.3.1. Is there any workaround or a setting for this specific issue? 
~~~~

11.

~~~~
Is this somehow related to (or better yet fixed by) https://issues.apache.org/jira/browse/KAFKA-15372?
~~~~

12.

~~~~
Hi [~frankgrimes97] Thanks for finding this ticket.

I think this one is actually caused by https://issues.apache.org/jira/browse/KAFKA-10586 because it involves the topic being created after MM2 is running, rather than an existing topic being added to the dedicated config.
So upgrading to a version with KAFKA-15732 patched but without _dedicated.mode.enable.internal.rest=true_ would still exhibit this problem.
~~~~

---

## KAFKA-10658: ErrantRecordReporter.report always return completed future even though the record is not sent to DLQ topic yet 

https://issues.apache.org/jira/browse/KAFKA-10658

Given fix versions: 2.6.2, 2.7.1, 2.8.0
JIRA affects (masked from the system): 2.6.0

- `KAFKA-10658@2.6.0`: config 2.6.0, metadata answer **affected** (listed_affected)
- `KAFKA-10658@2.5.1`: config 2.5.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
This issue happens when both DLQ and error log are enabled. There is a incorrect filter in handling multiple reports and it results in the uncompleted future is filtered out. Hence, users always receive a completed future even though the record is still in producer buffer.
~~~~

---

## KAFKA-10793: Race condition in FindCoordinatorFuture permanently severs connection to group coordinator

https://issues.apache.org/jira/browse/KAFKA-10793

Given fix versions: 2.6.2, 2.7.1, 2.8.0
JIRA affects (masked from the system): 2.5.0

- `KAFKA-10793@2.5.0`: config 2.5.0, metadata answer **affected** (listed_affected)
- `KAFKA-10793@2.4.1`: config 2.4.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
Pretty much as soon as we started actively monitoring the _last-rebalance-seconds-ago_ metric in our Kafka Streams test environment, we started seeing something weird. Every so often one of the StreamThreads (ie a single Consumer instance) would appear to permanently fall out of the group, as evidenced by a monotonically increasing _last-rebalance-seconds-ago._ We inject artificial network failures every few hours at most, so the group rebalances quite often. But the one consumer never rejoins, with no other symptoms (besides a slight drop in throughput since the remaining threads had to take over this member's work). We're confident that the problem exists in the client layer, since the logs confirmed that the unhealthy consumer was still calling poll. It was also calling Consumer#committed in its main poll loop, which was consistently failing with a TimeoutException.

When I attached a remote debugger to an instance experiencing this issue, the network client's connection to the group coordinator (the one that uses MAX_VALUE - node.id as the coordinator id) was in the DISCONNECTED state. But for some reason it never tried to re-establish this connection, although it did successfully connect to that same broker through the "normal" connection (ie the one that juts uses node.id).

The tl;dr is that the AbstractCoordinator's FindCoordinatorRequest has failed (presumably due to a disconnect), but the _findCoordinatorFuture_ is non-null so a new request is never sent. This shouldn't be possible since the FindCoordinatorResponseHandler is supposed to clear the _findCoordinatorFuture_ when the future is completed. But somehow that didn't happen, so the consumer continues to assume there's still a FindCoordinator request in flight and never even notices that it's dropped out of the group.

These are the only confirmed findings so far, however we have some guesses which I'll leave in the comments. Note that we only noticed this due to the newly added _last-rebalance-seconds-ago_ __metric, and there's no reason to believe this bug hasn't been flying under the radar since the Consumer's inception
~~~~

### Comments (4)

1.

~~~~
At this point we can only guess, but all signs point to a race condition between the main consumer thread and the heartbeat thread. One possibility is that when the future failed it just didn't trigger the `onFailure` callback, but [~guozhang] & I have both looked through the source code and don't see any way for this to occur. Another possibility is that the `onFailure` callback was triggered, but it was invoked too soon. If the future was completed before we ever assigned it to the _findCoordinatorFuture_ field, then we would never actually clear the latest future (we would just set an already-null field to null again).

Is this possible? Here's how the AbstractCoordinator builds the request and assigns the future:
{code:java}
protected synchronized RequestFuture<Void> lookupCoordinator() {
    ...
    findCoordinatorFuture = sendFindCoordinatorRequest(node);
}
{code}
{code:java}
private RequestFuture<Void> sendFindCoordinatorRequest(Node node) {
    ...
    return client.send(node, requestBuilder)
       .compose(new FindCoordinatorResponseHandler());{code}
{code:java}
}{code}
Inside #compose we call #addListener, which contains this snippet:
{code:java}
if (failed()) 
    fireFailure(); 
{code}
If the request has already failed by the time we reach this, then we'll trigger the `onFailure` callback before #compose ever returns – ie before we've assigned the future to _findCoordinatorFuture_.

The obvious question now is whether it's possible for the request to be failed in another thread while one thread is in the middle of the synchronized lookupCoordinator(). The request can be failed by the ConsumerNetworkClient when polled, during checkDisconnects(). The heartbeat thread actually synchronizes the entire run loop, so it doesn't seem possible for the hb thread to fail this request in the background of the main thread during a lookupCoordinator().

But the inverse is not true: it's possible for the main consumer thread to fail the request while the hb thread is inside of lookupCoordinator(). The AbstractCoordinator will poll the network client inside of joinGroupIfNeeded(), which in not itself synchronized and may be invoked without any locking through a Consumer#poll. 
~~~~

2.

~~~~
[~ableegoldman] I want to check whether the heartbeat Thread will check the status , thanks. 
~~~~

3.

~~~~
So that's our best guess. We should discuss the solution on the PR, but I'll lay out the two possibilities I see here in case anyone has any better ideas.

1) synchronize joinGroupIfNeeded()
2) clear the _findCoordinatorFuture_ when handling the result, rather than in the listener callbacks. For example in the main loop of ensureCoordinatorReady()

Personally I think option 2 is better, since it makes a lot more sense to me to begin with. By clearing the future in the listener callbacks, we might clear it before we ever even get to check on the result, eg the exception if failed. We actually seem to already anticipate this particular problem and recently implemented a workaround by adding an extra listener which saves the exception to a class _findCoordinatorException_ field. If we just wait to clear the future then presumably we could remove this workaround as well, and just save the exception when we check "if (future.failed())" inside of lookupCoordinator().

All that said, I'm not intimately familiar with the technical details of the ConsumerNetworkClient and how it handles its RequestFutures, so it's possible I'm missing something important.
~~~~

4.

~~~~
cc [~hachikuji] [~ijuma] Hopefully we nailed it this time! :)
~~~~

---

## KAFKA-12257:  Consumer mishandles topics deleted and recreated with the same name

https://issues.apache.org/jira/browse/KAFKA-12257

Given fix versions: 2.8.2, 3.0.0, 3.1.0
JIRA affects (masked from the system): 2.2.2, 2.3.1, 2.4.1, 2.5.1, 2.6.1, 2.7.1, 2.8.1

- `KAFKA-12257@2.2.2`: config 2.2.2, metadata answer **affected** (listed_affected)
- `KAFKA-12257@2.2.1`: config 2.2.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.2, 2.4, 3.1

### Description

~~~~
In KAFKA-7738, caching of leader epochs (KIP-320) was added to o.a.k.c.Metadata to ignore metadata responses with epochs smaller than the last seen epoch.

The current implementation can cause problems in cases where a consumer is subscribed to a topic that has been deleted and then recreated with the same name. This is something seen more often in consumers that subscribe to a multitude of topics using a wildcard.

Currently, when a topic is deleted and the Fetcher receives UNKNOWN_TOPIC_OR_PARTITION, the leader epoch is not cleared. If at a later time while the consumer is still running a topic is created with the same name, the leader epochs are set to 0 for the new topics partitions, and are likely smaller than those for the previous topic. For example, if a broker had restarted during the lifespan of the previous topic, the leader epoch would be at least 1 or 2. In this case the metadata will be ignored since it is incorrectly considered stale. Of course, the user will sometimes get lucky, and if a topic was only recently created so that the epoch is still 0, no problem will occur on recreation. The issue is also not seen when consumers happen to have been restarted in between deletion and recreation.

The most common side effect of the new metadata being disregarded is that the new partitions end up assigned but the Fetcher is unable to fetch data because it does not know the leaders. When recreating a topic with the same name it is likely that the partition leaders are not the same as for the previous topic, and the number of partitions may even be different. Besides not being able to retrieve data for the new topic, there is a more sinister side effect of the Fetcher triggering a metadata update after the fetch fails. The subsequent update will again ignore the topic's metadata if the leader epoch is still smaller than the cached value. This metadata refresh loop can continue indefinitely and with a sufficient number of consumers may even put a strain on a cluster since the requests are occurring in a tight loop. This can also be hard for clients to identify since there is nothing logged by default that would indicate what's happening. Both the Metadata class's logging of "_Not replacing existing epoch_", and the Fetcher's logging of "_Leader for partition <T-P> is unknown_" are at DEBUG level.

A second possible side effect was observed where if the consumer is acting as leader of the group and happens to not have any current data for the previous topic, e.g. it was cleared due to a metadata error from a broker failure, then the new topic's partitions may simply end up unassigned within the group. This is because while the subscription list contains the recreated topic the metadata for it was previously ignored due to the leader epochs. In this case the user would see logs such as:
{noformat}
WARN o.a.k.c.c.i.ConsumerCoordinator [Consumer clientId=myClientId, groupId=myGroup] The following subscribed topics are not assigned to any members: [myTopic]{noformat}
Interestingly, I believe the Producer is less affected by this problem since o.a.k.c.p.i.ProducerMetadata explicitly clears knowledge of its topics in retainTopics() after each metadata expiration. ConsumerMetadata does no such thing.

To reproduce this issue:
 # Turn on DEBUG logging, e.g. for org.apache.kafka.clients.consumer and org.apache.kafka.clients.Metadata
 # Begin a consumer for a topic (or multiple topics)
 # Restart a broker that happens to be a leader for one of the topic's partitions
 # Delete the topic
 # Create another topic with the same name
 # Publish data for the new topic
 # The consumer will not receive data for the new topic, and there will be a high rate of metadata requests.
 # The issue can be corrected by restarting the consumer or restarting brokers until leader epochs are large enough

I believe KIP-516 (unique topic ids) will likely fix this problem, since after those changes the leader epoch map should be keyed off of the topic id, rather than the name.

One possible workaround with the current version of Kafka is to add code to onPartitionsRevoked() to manually clear leader epochs before each rebalance, e.g.
{code:java}
Map<TopicPartition, Integer> emptyLeaderEpochs = new HashMap<>();
ConsumerMetadata metadata = (ConsumerMetadata)FieldUtils.readField(consumer, "metadata", 
true);
FieldUtils.writeField(metadata, "lastSeenLeaderEpochs", emptyLeaderEpochs, true);{code}
This is not really recommended of course, since besides modifying private consumer state, it defeats the purpose of epochs! It does in a sense revert the consumer to pre-2.2 behavior before leader epochs existed.
~~~~

### Comments (3)

1.

~~~~
With the changes from [KIP-516|https://cwiki.apache.org/confluence/display/KAFKA/KIP-516%3A+Topic+Identifiers] there some options to fix this bug. This ticket mentions using the topic ID as a key for the leader epoch map, but another option that might be a bit simpler to implement is checking for a new topic ID in the request.

There is already work ongoing to update the Fetch path to use topic IDs ([https://github.com/apache/kafka/pull/9944]) and this will include storing the topic ID in the consumer's metadata cache.  Upon receiving a new metadata response, we can check if the topic ID matches the ID already stored in the cache and set a flag if it has changed. Then, in `updateLatestMetadata`, we have code that checks the epoch:
{code:java}
if (currentEpoch == null || newEpoch >= currentEpoch) {
    log.debug("Updating last seen epoch for partition {} from {} to epoch {} from new metadata", tp, currentEpoch, newEpoch);
    lastSeenLeaderEpochs.put(tp, newEpoch);
    return Optional.of(partitionMetadata);
{code}
 

If we include an or ( || ) for the changed topic ID, I believe this will achieve the behavior this ticket is looking for. The lastSeenEpoch will be reset to the epoch of the new topic and we will use the new partitionMetadata.
~~~~

2.

~~~~
We were able to reproduce this issue in Kafka 2.4.
~~~~

3.

~~~~
We should merge the change for 3.1. [~hachikuji] I can take another look at the PR and update it.
~~~~

---

## KAFKA-12350: document  about refresh.topics.interval.seconds default value is not right 

https://issues.apache.org/jira/browse/KAFKA-12350

Given fix versions: 3.0.0
JIRA affects (masked from the system): 2.7.0

- `KAFKA-12350@2.7.0`: config 2.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-12350@2.6.3`: config 2.6.3, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
The config, refresh.topics.interval.seconds, described in document  give the defalut value 6000, ten minutes. 600 seconds or 100 minutes?
~~~~

### Comments (1)

1.

~~~~
The default values are set to 10 * 60 seconds, which is 10 minutes. I'll update the document. Thanks for reporting [~superheizai]
~~~~

---

## KAFKA-12525: Inaccurate task status due to status record interleaving in fast rebalances in Connect

https://issues.apache.org/jira/browse/KAFKA-12525

Given fix versions: 3.6.0
JIRA affects (masked from the system): 2.3.1, 2.4.1, 2.5.1, 2.6.1, 2.7.0

- `KAFKA-12525@2.7.0`: config 2.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-12525@2.3.0`: config 2.3.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
When a task is stopped in Connect it produces an {{UNASSIGNED}} status record. 
Equivalently, when a task is started or restarted in Connect it produces an {{RUNNING}} status record in the Connect status topic.

At the same time rebalances are decoupled from task start and stop. These operations happen in separate executor outside of the main worker thread that performs the rebalance.

Normally, any delayed and stale {{UNASSIGNED}} status records are fenced by the worker that is sending them. This worker is using the {{StatusBackingStore#putSafe}} method that will reject any stale status messages (called only for {{UNASSIGNED}} or {{FAILED}}) as long as the worker is aware of the newer status record that declares a task as {{RUNNING}}.

In cases of fast consecutive rebalances where a task is revoked from one worker and assigned to another one, it has been observed that there is a small time window and thus a race condition during which a {{RUNNING}} status record in the new generation is produced and is immediately followed by a delayed {{UNASSIGNED}} status record belonging to the same or a previous generation before the worker that sends this message reads the {{RUNNING}} status record that corresponds to the latest generation.

A couple of options are available to remediate this race condition. 
For example a worker that is has started a task can re-write the {{RUNNING}} status message in the topic if it reads a stale {{UNASSIGNED}} message from a previous generation (that should have been fenced). 
Another option is to ignore stale {{UNASSIGNED}} message (messages from an earlier generation than the one in which the task had {{RUNNING}} status).

Worth noting that when this race condition takes place, besides the inaccurate status representation, the actual execution of the tasks remains unaffected (e.g. the tasks are running correctly even though they appear as {{UNASSIGNED}}). 
~~~~

---

## KAFKA-12558: MM2 may not sync partition offsets correctly

https://issues.apache.org/jira/browse/KAFKA-12558

Given fix versions: 3.3.3, 3.4.1, 3.5.0
JIRA affects (masked from the system): 2.6.1, 2.7.0

- `KAFKA-12558@2.7.0`: config 2.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-12558@2.6.0`: config 2.6.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
There is a race condition in {{MirrorSourceTask}} where certain partition offsets may never be sent. The bug occurs when the [outstandingOffsetSync semaphore is full|https://github.com/apache/kafka/blob/trunk/connect/mirror/src/main/java/org/apache/kafka/connect/mirror/MirrorSourceTask.java#L207]. In this case, the sendOffsetSync [will silently fail|https://github.com/apache/kafka/blob/trunk/connect/mirror/src/main/java/org/apache/kafka/connect/mirror/MirrorSourceTask.java#L207].

This failure is normally acceptable since offset sync will retry frequently. However, {{maybeSyncOffsets}} has a bug where it will [mutate the partition state|https://github.com/apache/kafka/blob/trunk/connect/mirror/src/main/java/org/apache/kafka/connect/mirror/MirrorSourceTask.java#L199] prior to confirming the result of {{sendOffsetSync}}. The end result is that the partition state is mutated prematurely, and prevent future offset syncs to recover.

Since {{MAX_OUTSTANDING_OFFSET_SYNCS}} is 10, this bug happens when you assign more than 10 partitions to each task.

In my test cases where I had over 100 partitions per task, the majority of the offsets were wrong. Here's an example of such a failure. https://issues.apache.org/jira/browse/KAFKA-12468?focusedCommentId=17308308&page=com.atlassian.jira.plugin.system.issuetabpanels%3Acomment-tabpanel#comment-17308308

During my troubleshooting, I customized the {{MirrorSourceTask}} to confirm that all partitions that have the wrong offset were failing to acquire the initial semaphore. The condition [can be trapped here|https://github.com/apache/kafka/blob/trunk/connect/mirror/src/main/java/org/apache/kafka/connect/mirror/MirrorSourceTask.java#L208].

*Possible Fix:*

A possible fix is to create a {{shouldUpdate}} method in {{PartitionState}}. This method should be read-only and return true if {{sendOffsetSync}} is needed. Once {{sendOffsetSync}} is successful, only then {{update}} should be called.

Here's some pseudocode
{code:java}
private void maybeSyncOffsets(TopicPartition topicPartition, long upstreamOffset,
        long downstreamOffset) {
    PartitionState partitionState =
        partitionStates.computeIfAbsent(topicPartition, x -> new PartitionState(maxOffsetLag));
    if (partitionState.shouldUpdate(upstreamOffset, downstreamOffset)) {
        if(sendOffsetSync(topicPartition, upstreamOffset, downstreamOffset)) {
            partitionState.update(upstreamOffset, downstreamOffset)
        }
    }
}
{code}
 

*Workaround:*

For those who are experiencing this issue, the workaround is to make sure you have less than or equal to 10 partitions per task. Set your `tasks.max` value accordingly.
~~~~

### Comments (2)

1.

~~~~
This sounds right. Updating the partition store without sending an offset sync means additional offset syncs are unlikely to arrive for a long time, if ever.

I'm happy to fix but will leave this unassigned for a bit in case someone else wants to take this on.
~~~~

2.

~~~~
Just one clarification:
 The number of *LEADER* partitions / The number of tasks <= 10
Correct?
[~askldjd]
~~~~

---

## KAFKA-12762: Use connection timeout when polling the network for new connections

https://issues.apache.org/jira/browse/KAFKA-12762

Given fix versions: 3.0.1, 3.1.0
JIRA affects (masked from the system): 2.7.0, 2.8.0

- `KAFKA-12762@2.7.0`: config 2.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-12762@2.6.3`: config 2.6.3, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.7

### Description

~~~~
In some cases, when connecting to brokers, we end up calling selector.select() with the wrong timeout. Since 2.7, we should use a timeout computed from socket.connection.setup.timeout.ms to ensure we detect bad hosts quickly.

This is especially relevant now that client.dns.lookup defaults to use_all_dns_ips. In case, one of the IPs returned in currently unavailable, we want the client to quickly discover it and avoid timing out user calls.
h4.  
~~~~

---

## KAFKA-12999: NPE when accessing RecordHeader.key() concurrently

https://issues.apache.org/jira/browse/KAFKA-12999

Given fix versions: 4.2.0
JIRA affects (masked from the system): 2.8.0

- `KAFKA-12999@2.8.0`: config 2.8.0, metadata answer **affected** (listed_affected)
- `KAFKA-12999@2.7.2`: config 2.7.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.8.0

### Description

~~~~
h2. Summary

After upgrading clients to {{2.8.0}}, reading {{ConsumerRecord}}'s header keys started resulting in occasional {{java.lang.NullPointerException}} in case of concurrent access from multiple(2) threads.
h2. Where

NPE happens here [RecordHeader.java:45|https://github.com/apache/kafka/blob/2.8.0/clients/src/main/java/org/apache/kafka/common/header/internals/RecordHeader.java#L45]:
{code:java}
public String key() {
    if (key == null) {
        key = Utils.utf8(keyBuffer, keyBuffer.remaining()); // NPE here 
        keyBuffer = null;
    }
    return key;
}
{code}
h2. When/why

Cause of issue is introduced by changes of KAFKA-10438 to avoid unnecessary creation of key's *{color:#0747a6}{{String}}{color}* when it might never be used.
 It is good optimization but this *lazy* initialization of field {{RecordHeader.key}} creates a problem if being accessed/initialized by 2 threads concurrently since it's now no longer read-only operation and there is race between initializing {color:#0747a6}*{{key}}*{color} and nullifying {color:#0747a6}*{{keyBuffer}}*{color}
h2. Simple workaround

Upon consuming record(s) and before passing {color:#0747a6}*{{ConsumerRecord}}*{color} to multiple processing threads, eagerly initialize all header keys by iterating through headers and invoking {color:#0747a6}*{{key()}}*{color} or even {color:#0747a6}*{{ConsumerRecord.headers().hashCode()}}*{color} which will initialize all keys (and header values too)
h2. Consequences

Current implementation renders RecordHeader not thread-safe for read-only access.
h2. Reproducibility

With enough iterations it's always possible to reproduce (at least on my local)
 Here is minimal snippet to reproduce:
{code:java}
@Test
public void testConcurrentKeyInit() throws ExecutionException, InterruptedException {
    ByteBuffer keyBuffer = ByteBuffer.wrap("key".getBytes(StandardCharsets.UTF_8));
    ByteBuffer valueBuffer = ByteBuffer.wrap("value".getBytes(StandardCharsets.UTF_8));

    ExecutorService executorService = Executors.newSingleThreadExecutor();
    try {
        for (int i = 0; i < 1_000_000; i++) {
            RecordHeader header = new RecordHeader(keyBuffer, valueBuffer);
            Future<String> future = executorService.submit(header::key);
            assertEquals("key", header.key());
            assertEquals("key", future.get());
        }
    } finally {
        executorService.shutdown();
    }
}
{code}
h2. Possible solution #1

Leave implementation as-is but somehow document this to users.
h2. Possible solution #2

Add some concurrency primitives to current implementation
*   simply adding {color:#0747a6}*{{synchronized}}*{color} on method *{color:#0747a6}{{key()}}{color}* (and on *{color:#0747a6}{{value()}}{color}* too) gives correct behaviour avoiding race-conditions. 
* JMH benchmark comparing *{color:#0747a6}{{key()}}{color}* with and without {color:#0747a6}*{{synchronized}}*{color} showed no significant performance penalty
{code}
Benchmark                              Mode  Cnt   Score   Error  Units
RecordHeaderBenchmark.key              avgt    15  31.308 ± 7.862  ns/op
RecordHeaderBenchmark.synchronizedKey  avgt    15  31.853 ± 7.096  ns/op
{code}

 

 
~~~~

### Comments (6)

1.

~~~~
Thanks for the ticket. This class was never meant to be thread safe, the value was initialized lazily previously and it just so happened the key was not. Since the consumer is single threaded, this was deemed ok.

For now, the easiest path is for you to copy the data you care about to your own thread safe class. We could consider making ConsumerRecord thread safe, but it would require a KIP and it would probably only be done in a feature release.
~~~~

2.

~~~~
cc [~chia7712]
~~~~

3.

~~~~
{quote}but it would require a KIP and it would probably only be done in a feature release.{quote}
[~ijuma] What do you suggest for me to do? Should I then write a KIP? Cancel my [PR|https://github.com/apache/kafka/pull/10933]?

{quote}For now, the easiest path is for you to copy the data you care about to your own thread safe class{quote}
Yes, this is obvious once you hit NPE and only then realise class is not thread-safe
~~~~

4.

~~~~
A KIP seems reasonable. The class could be made thread safe at low cost by using a volatile field and synchronization during initialization only.
~~~~

5.

~~~~
Thanks for this ticket. As juma explained, the class is not designed for thread-safe.

As modern Java make optimization for single thread in sync block, adding sync to make it thread-safe seems to be fine to me. Of course, it needs KIP :)

~~~~

6.

~~~~
Note that biased locking has been deprecated and will be removed in JDK 18 or soon after. So, synchronized blocks have a cost. We should do what I suggested and have the synchronized _only_ during initialization.
~~~~

---

## KAFKA-13255: Mirrormaker config property config.properties.exclude is not working as expected 

https://issues.apache.org/jira/browse/KAFKA-13255

Given fix versions: 3.1.1, 3.2.0
JIRA affects (masked from the system): 2.8.0

- `KAFKA-13255@2.8.0`: config 2.8.0, metadata answer **affected** (listed_affected)
- `KAFKA-13255@2.7.2`: config 2.7.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.8.0, 2.8, v3.1.0, 3.0, 3.1.0, 3.1

### Description

~~~~
Objective - Use MM2 (kafka connect in distributed cluster) for data migration between cluster hosted in private data center and aws msk cluster.

Steps performed -
 # Started kafka-connect service.
 # Created 3 MM2 connectors (i.e. source connector, checkpoint connector and heartbeat connector). Curl commands used to create connectors are in the attached file.  To exclude certain config properties while topic replication, we are using the 'config.properties.exclude' property in the MM2 source connector.

Expected -

Source topic 'dev.portlandDc.anamika.helloMsk' should be successfully created in destination cluster.

Actual -

Creation of the source topic 'dev.portlandDc.anamika.helloMsk' in destination cluster fails with an error. Error is
{code:java}
[2021-08-06 06:13:40,944] WARN [mm2-msc|worker] Could not create topic dev.portlandDc.anamika.helloMsk. (org.apache.kafka.connect.mirror.MirrorSourceConnector:371)
org.apache.kafka.common.errors.InvalidConfigurationException: Unknown topic config name: confluent.value.schema.validation{code}
~~~~

### Comments (14)

1.

~~~~
I keep getting HTTP error 403 when trying to attach file with curl commands to this jira. As a work around I am pasting the file contents below.
{code:java}
curl -X POST http://10.xx.xx.xx:8083/connectors -H "Content-Type: application/json" -d '{
   "name":"mm2-msc",
   "config":{
      "connector.class":"org.apache.kafka.connect.mirror.MirrorSourceConnector",
      "clusters":"mysource,mydestination",
      "source.cluster.alias":"mysource",
      "target.cluster.alias":"mydestination",
      "replication.policy.class":"com.amazonaws.kafka.samples.CustomMM2ReplicationPolicy",
      "target.cluster.bootstrap.servers":"b-2.mydestination.amazonaws.com:9096,b-3.mydestination.amazonaws.com:9096,b-1.mydestination.amazonaws.com:9096",
      "source.cluster.bootstrap.servers":"10.xx.xx.xx:9093,10.xx.xx.xx:9093,10.xx.xx.xx:9093,10.xx.xx.xx:9093,10.xx.xx.xx:9093",
      "topics":"dev.portlandDc.anamika.helloMsk",
      "config.properties.exclude":"^confluent\\..*$",
      "tasks.max":"1",
      "key.converter":" org.apache.kafka.connect.converters.ByteArrayConverter",
      "value.converter":"org.apache.kafka.connect.converters.ByteArrayConverter",
      "replication.factor":"3",
      "offset-syncs.topic.replication.factor":"3",
      "sync.topic.acls.interval.seconds":"20",
      "sync.topic.configs.interval.seconds":"20",
      "refresh.topics.interval.seconds":"20",
      "refresh.groups.interval.seconds":"20",
      "consumer.group.id":"mm2-msc-cons",
      "producer.enable.idempotence":"true",
      "source.cluster.security.protocol":"SASL_SSL",
      "source.cluster.sasl.mechanism":"PLAIN",
      "source.cluster.ssl.truststore.location":"/home/ec2-user/dc/kafka.client.truststore.jks",
      "source.cluster.ssl.truststore.password":"xxxxx",
      "source.cluster.ssl.endpoint.identification.algorithm":"",
      "source.cluster.sasl.jaas.config":"org.apache.kafka.common.security.plain.PlainLoginModule required username=\"xxxxx\" password=\"xxxxx\";",
      "target.cluster.security.protocol":"SASL_SSL",
      "target.cluster.sasl.mechanism":"SCRAM-SHA-512",
      "target.cluster.ssl.truststore.location":"/home/ec2-user/kafka_2.13-2.8.0/config/msk/kafka.client.truststore.jks",
      "target.cluster.sasl.jaas.config":"org.apache.kafka.common.security.scram.ScramLoginModule required username=\"xxxxx\" password=\"xxxxx\";"
   }
}' | jq .
curl -X POST http://10.xx.xx.xx:8083/connectors -H "Content-Type: application/json" -d '{
   "name":"mm2-cpc",
   "config":{
      "connector.class":"org.apache.kafka.connect.mirror.MirrorCheckpointConnector",
      "clusters":"mysource,mydestination",
      "source.cluster.alias":"mysource",
      "target.cluster.alias":"mydestination",
      "config.properties.exclude":"confluent.value.schema.validation",
      "config.properties.blacklist":"confluent.value.schema.validation",
      "target.cluster.bootstrap.servers":"b-2.mydestination.amazonaws.com:9096,b-3.mydestination.amazonaws.com:9096,b-1.mydestination.amazonaws.com:9096",
      "source.cluster.bootstrap.servers":"10.xx.xx.xx:9093,10.xx.xx.xx:9093,10.xx.xx.xx:9093,10.xx.xx.xx:9093,10.xx.xx.xx:9093",
      "tasks.max":"1",
      "key.converter":" org.apache.kafka.connect.converters.ByteArrayConverter",
      "value.converter":"org.apache.kafka.connect.converters.ByteArrayConverter",
      "replication.policy.class":"com.amazonaws.kafka.samples.CustomMM2ReplicationPolicy",
      "replication.factor":"3",
      "sync.topic.configs.enabled":"false",
      "checkpoints.topic.replication.factor":"3",
      "emit.checkpoints.interval.seconds":"20",
      "source.cluster.security.protocol":"SASL_SSL",
      "source.cluster.sasl.mechanism":"PLAIN",
      "source.cluster.ssl.truststore.location":"/home/ec2-user/dc/kafka.client.truststore.jks",
      "source.cluster.ssl.truststore.password":"xxxxx",
      "source.cluster.ssl.endpoint.identification.algorithm":"",
      "source.cluster.sasl.jaas.config":"org.apache.kafka.common.security.plain.PlainLoginModule required username=\"xxxxx\" password=\"xxxxx\";",
      "target.cluster.security.protocol":"SASL_SSL",
      "target.cluster.sasl.mechanism":"SCRAM-SHA-512",
      "target.cluster.ssl.truststore.location":"/home/ec2-user/kafka_2.13-2.8.0/config/msk/kafka.client.truststore.jks",
      "target.cluster.sasl.jaas.config":"org.apache.kafka.common.security.scram.ScramLoginModule required username=\"xxxxx\" password=\"xxxxx\";"
   }
}' | jq .
curl -X POST http://10.xx.xx.xx:8083/connectors -H "Content-Type: application/json" -d '{
   "name":"mm2-hbc",
   "config":{
      "connector.class":"org.apache.kafka.connect.mirror.MirrorHeartbeatConnector",
      "clusters":"mysource,mydestination",
      "source.cluster.alias":"mysource",
      "target.cluster.alias":"mydestination",
      "target.cluster.bootstrap.servers":"b-2.mydestination.amazonaws.com:9096,b-3.mydestination.amazonaws.com:9096,b-1.mydestination.amazonaws.com:9096",
      "source.cluster.bootstrap.servers":"10.xx.xx.xx:9093,10.xx.xx.xx:9093,10.xx.xx.xx:9093,10.xx.xx.xx:9093,10.xx.xx.xx:9093",
      "tasks.max":"1",
      "key.converter":" org.apache.kafka.connect.converters.ByteArrayConverter",
      "value.converter":"org.apache.kafka.connect.converters.ByteArrayConverter",
      "replication.factor":"3",
      "heartbeats.topic.replication.factor":"3",
      "emit.heartbeats.interval.seconds":"20",
      "source.cluster.security.protocol":"SASL_SSL",
      "source.cluster.ssl.truststore.location":"/home/ec2-user/dc/kafka.client.truststore.jks",
      "source.cluster.ssl.truststore.password":"xxxxx",
      "source.cluster.sasl.jaas.config":"org.apache.kafka.common.security.plain.PlainLoginModule required username=\"xxxxx\" password=\"xxxxx\";",
      "source.cluster.sasl.mechanism":"PLAIN",
      "target.cluster.security.protocol":"SASL_SSL",
      "target.cluster.ssl.truststore.location":"/home/ec2-user/kafka_2.13-2.8.0/config/msk/kafka.client.truststore.jks",
      "target.cluster.sasl.mechanism":"SCRAM-SHA-512",
      "target.cluster.sasl.jaas.config":"org.apache.kafka.common.security.scram.ScramLoginModule required username=\"xxxxx\" password=\"xxxxx\";"
   }
}
' | jq .
{code}
~~~~

2.

~~~~
To replicate source topic in destination cluster with no prefix (<sourcealias>), I am using custom replication policy while creating source connector. You can generate custom replication policy jar from below link. I am getting 'HTTP - 403 Forbidden' , when I am trying to attach the jar.

https://github.com/aws-samples/mirrormaker2-msk-migration/tree/master/CustomMM2ReplicationPolicy

 
~~~~

3.

~~~~
I have fixed this issue and would like to contribute my changes to apache kafka code. I am trying to attach a file but I am not able to do it.

Please suggest, how to upload a file?
~~~~

4.

~~~~
hey [~anadkarni], you'll need to create a pull request on github (https://github.com/apache/kafka) so that we can review and merge the changes. Let me know if you need help.
~~~~

5.

~~~~
[~ryannedolan] Submitted PR. Thank you !!
~~~~

6.

~~~~
[~ryannedolan] How much time usually it takes to get PR approved on kafka?

https://github.com/apache/kafka/pull/11328
~~~~

7.

~~~~
[~ryannedolan], I recommend to fix this bug report:

Subject: Mirrormaker doesn't honor exclude filters for new topics

The bug was indeed introduced in 2.8, when MM started creating topics WITH configs. Prior to this, MM would create new topic on target without any config from source, and then `syncTopicConfigs` would replicate config while honoring the exclude filter defined in `DefaultConfigPropertyFilter` or explicitly specified in MM property `config.properties.exclude`.

After the update in 2.8, MM started creating new topics along with their configs from source cluster, but the configs aren't being filtered against exclude param.

I've submitted PR with a little update to use the same method as used for `syncTopicConfigs` to apply the filter.

 

https://github.com/apache/kafka/pull/11401
~~~~

8.

~~~~
[~mimaison] [~bdesert] , do you know if there's any workaround for this issue? If no, do you think we should get this fix cherry-picked back to v3.1.0, since it blocked users using MM2?

Thank you.
~~~~

9.

~~~~
It's not a regression from 3.0 so it's probably too late for 3.1.0. David Jacot is the release manager and has the final say. You can ask him if you think this should be included.
I'm not sure if there's a workaround apart from not mirroring topics with custom configurations

~~~~

10.

~~~~
the workaround would be to pre-create topics on a target cluster. Also, this bug is critical (show stopper) only if MM2 configured to replicate topics cross-flavors cluster, as reported in the original case above (Confluent to MSK, or to vanilla Apache Kafka). Once topic is created on target, this bug won't affect data mirroring process.
~~~~

11.

~~~~
Thanks for your response. In that case, I agree we don't need to include this fix in v3.1.0. Thank you.
~~~~

12.

~~~~
Would have been really nice to have this fix in 3.1 
~~~~

13.

~~~~
OK [~ecomar] I've cherry-picked it to 3.1
~~~~

14.

~~~~
Thanks Tom !!! [~tombentley]
~~~~

---

## KAFKA-13419: sync group failed with rebalanceInProgress error might cause out-of-date ownedPartition in Cooperative protocol

https://issues.apache.org/jira/browse/KAFKA-13419

Given fix versions: 3.1.0
JIRA affects (masked from the system): 3.0.0

- `KAFKA-13419@3.0.0`: config 3.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-13419@2.8.2`: config 2.8.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
In KAFKA-13406, we found there's user got stuck when in rebalancing with cooperative sticky assignor. The reason is the "ownedPartition" is out-of-date, and it failed the cooperative assignment validation.

Investigate deeper, I found the root cause is we didn't reset generation and state after sync group fail. In KAFKA-12983, we fixed the issue that the onJoinPrepare is not called in resetStateAndRejoin method. And it causes the ownedPartition not get cleared. But there's another case that the ownedPartition will be out-of-date. Here's the example:
 # consumer A joined and synced group successfully with generation 1
 # New rebalance started with generation 2, consumer A joined successfully, but somehow, consumer A doesn't send out sync group immediately
 # other consumer completed sync group successfully in generation 2, except consumer A.
 # After consumer A send out sync group, the new rebalance start, with generation 3. So consumer A got REBALANCE_IN_PROGRESS error with sync group response
 # When receiving REBALANCE_IN_PROGRESS, we re-join the group, with generation 3, with the assignment (ownedPartition) in generation 1.
 # So, now, we have out-of-date ownedPartition sent, with unexpected results happened

 

We might want to do *resetStateAndRejoin* when *RebalanceInProgressException* errors happend in *sync group*. Because when we got sync group error, it means, join group passed, and other consumers (and the leader) might already completed this round of rebalance. The assignment distribution this consumer have is already out-of-date.

 
~~~~

### Comments (9)

1.

~~~~
[~showuon] - this Jira is marked as in progress, yet I see that the corresponding PR has been merged already. Is this still in progress? If not, please update the fixed version and mark as fixed.

Thanks!
~~~~

2.

~~~~
[~kirktrue] , thanks for the reminder. Updated.
~~~~

3.

~~~~
Hi [~showuon] 

After i applied this fix and my previous change to make this fix work[https://github.com/apache/kafka/pull/12140, |https://github.com/apache/kafka/pull/12140]what we are seeing is that: sometimes consumer will revoker almost all partitions with cooperative enabled.

detail:
 * we have more than 1000 consumers, coopeartive rebalance. 
 * Just the same as the example in this JIRA:  in cooperative rebalance some consumer will do a very quick re-join after get SyncGroupResponse. if there are some consumer that didn't send SyncGroupRequest yet, it will do a revoke-all and re-join operation.
 * after applied this change, it will solve the rebalance many rounds problem https://issues.apache.org/jira/browse/KAFKA-13891
 * but it will result in many partitions revoked if there is a very fast re-join consumer, and make cooperative almost the same as eager rebalance.

So instead of "{*}resetStateAndRejoin{*} when *RebalanceInProgressException* errors happend in {*}sync group{*}", can we just treat the ownedPartition in previous generation legal if there are no same partition claimed by other member? 

 

What do you think?

Thanks a lot!
~~~~

4.

~~~~
{quote}  can we just treat the ownedPartition in previous generation legal if there are no same partition claimed by other member? 
{quote}
Huh, I thought that's already what the cooperative assignor does? Maybe we intentionally left/took it out of the constrained case algorithm for some reason? Or possibly we had just discussed doing this and never did, either way I definitely remember this specific handling logic coming up during the recent(ish) optimizations that I worked on with [~showuon] 

I'll check out the code I guess
~~~~

5.

~~~~
[~ableegoldman] , you are right. We have the logic to handle multiple consumers owned the same partitions case.

 
~~~~

6.

~~~~
Cool, thanks for confirming this is already handled in the assignor. Ok then, that said – or actually, _because_ of this, I do agree that we should revert https://issues.apache.org/jira/browse/KAFKA-13891. 

 

Maybe we can look into the logs to better understand the original problem you were experiencing [~aiquestion] – or were you not personally hitting the issue "fixed" by https://issues.apache.org/jira/browse/KAFKA-13891, just vigilant about submitting a patch when you noticed we had mentioned making this change in [https://github.com/apache/kafka/pull/11451] but then apparently left it out?
~~~~

7.

~~~~
[~ableegoldman] [~showuon] Looking at the code in AbstractStickyPartitioner, it seems that we discard all previous generations when we see a more recent one. So we have the code to handle multiple generations but we don't try to reuse previous generations. So if a partition is claimed by a member at an older generation and no one else, it seems to me that we won't reuse it. I may be reading it wrong as well. This is the first time I read this code.
~~~~

8.

~~~~
[~dajac] , you're right. We don't use owned partitions in old generation. We treat is as stale owned partitions and ignore them. But you're right, if there are no other members claiming owning the partitions, we can keep letting the member own them.

 
~~~~

9.

~~~~
[~showuon] Thanks for confirming.
~~~~

---

## KAFKA-13518: Update gson dependency

https://issues.apache.org/jira/browse/KAFKA-13518

Given fix versions: 3.4.0
JIRA affects (masked from the system): 3.0.0

- `KAFKA-13518@3.0.0`: config 3.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-13518@2.8.2`: config 2.8.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.0.0, 3.1.0, 3.0.1, 4.2.2, 4.5.0

### Description

~~~~
*Describe the bug*
I checked kafka_2.13-3.0.0.tgz distribution with WhiteSource and find out that some libraries have vulnerabilities.
Here they are:
* gson-2.8.6.jar has WS-2021-0419 vulnerability. The way to fix it is to upgrade to com.google.code.gson:gson:2.8.9
* netty-codec-4.1.65.Final.jar has CVE-2021-37136 and CVE-2021-37137 vulnerabilities. The way to fix it is to upgrade to io.netty:netty-codec:4.1.68.Final

*To Reproduce*
Download kafka_2.13-3.0.0.tgz and find jars, listed above.
Check that these jars with corresponding versions are mentioned in corresponding vulnerability description.

*Expected behavior*

* gson upgraded to 2.8.9 or higher
* netty-codec upgraded to 4.1.68.Final or higher

*Actual behaviour*

* gson is 2.8.6
* netty-codec is 4.1.65.Final
~~~~

### Comments (1)

1.

~~~~
The security problems on netty-codec were already fixed with KAFKA-13294. It will be shipped with AK 3.1.0 and 3.0.1.

In the case of gson, this problem is introduced by spotbugs 4.2.2. [spotbugs 4.5.0|https://mvnrepository.com/artifact/com.github.spotbugs/spotbugs/4.5.0] uses [gson 2.8.9|https://github.com/google/gson/releases/tag/gson-parent-2.8.9], which [resolves|https://github.com/google/gson/pull/1991] WS-2021-0419 vulnerability.
~~~~

---

## KAFKA-13539: Improve propagation and processing of SSL handshake failures

https://issues.apache.org/jira/browse/KAFKA-13539

Given fix versions: 3.2.0
JIRA affects (masked from the system): 3.1.0

- `KAFKA-13539@3.1.0`: config 3.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-13539@3.0.2`: config 3.0.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
{color:#172b4d}When server fails SSL handshake and closes its connection, we attempt to report this to clients on a best-effort basis. However, our tests assume that peer always detects the failure. This may not be the case when there are delays. It will be good to improve reliability of handshake failure reporting. {color}
~~~~

---

## KAFKA-13562: Mirror Maker 2 Negative Offsets

https://issues.apache.org/jira/browse/KAFKA-13562

Given fix versions: 3.3.3, 3.4.1, 3.5.0
JIRA affects (masked from the system): 2.8.1

- `KAFKA-13562@2.8.1`: config 2.8.1, metadata answer **affected** (listed_affected)
- `KAFKA-13562@2.8.0`: config 2.8.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.4.1, 2.8.1

### Description

~~~~
We recently started a migration from a traditional self-managed Apache Kafka cluster to Strimzi. We enabled group offset sync and something I'm struggling to fully understand is why the mirrored group has a current-offset matching (or close to matching) the source offset, but then the log-end-offset essentially starts over resulting in a negative lag. Is this just aesthetic? The lag is slowly moving closer to 0 but some of our negative lags are very "large". Several hundred million. I verified all the data has moved over, but I'm struggling on this lag issue.

Any help clearing this up is much appreciated!

Source cluster is 2.4.1 destination is 2.8.1. Detailed info in the Github URL.
~~~~

---

## KAFKA-13661: KRaft uses the wrong permission for adding topic partitions

https://issues.apache.org/jira/browse/KAFKA-13661

Given fix versions: 3.1.1, 3.2.0
JIRA affects (masked from the system): 3.0.0, 3.1.0

- `KAFKA-13661@3.1.0`: config 3.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-13661@2.8.2`: config 2.8.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.0, 3.1

### Description

~~~~
[~cmccabe] caught this as part of KAFKA-13646. KRaft currently checks CREATE on the topic resource. It should be ALTER. This will be fixed in trunk as part of KAFKA-13646, but it would be good to fix for 3.0 and 3.1 as well.

Note this does not affect zookeeper-based clusters.
~~~~

### Comments (1)

1.

~~~~
Another minor difference in behavior is that KRaft allows CREATE on the Cluster resource. This is not allowed in zk clusters and was not documented by KIP-195: https://cwiki.apache.org/confluence/display/KAFKA/KIP-195%3A+AdminClient.createPartitions. Probably not a big deal to allow this, but I'm inclined nevertheless to drop it for consistency.
~~~~

---

## KAFKA-13719: connector restart cause duplicate tasks

https://issues.apache.org/jira/browse/KAFKA-13719

Given fix versions: 3.1.1, 3.2.0, 3.3.0
JIRA affects (masked from the system): 3.0.0

- `KAFKA-13719@3.0.0`: config 3.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-13719@2.8.2`: config 2.8.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
Restart connector with parameter includeTasks=true&onlyFailed=false cause duplicate tasks and duplicate message。
~~~~

---

## KAFKA-13741: Cluster IDs should not have leading dash

https://issues.apache.org/jira/browse/KAFKA-13741

Given fix versions: 3.2.0
JIRA affects (masked from the system): 3.0.0, 3.1.0

- `KAFKA-13741@3.0.0`: config 3.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-13741@2.8.2`: config 2.8.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
Since we use URL-safe base64 encoded Uuid's for cluster ID, it is possible for dash ("-") characters to be present in the ID string. When a cluster ID has a leading dash, we can run into problems when running the Kafka bash scripts.

For example, if the ID "-Xflm1nKSfOK8QGt_AXhxw" is generated with "random-uuid" sub-command of kafka-storage.sh, we would then normally format the log directories like:

{code}
./bin/kafka-storage.sh format --config ./config/kraft/controller.properties \
    --cluster-id -Xflm1nKSfOK8QGt_AXhxw
{code}

This will not parse correctly as the argument parsing library will treat the cluster ID as an argument. It leads to the following error:

{code}
usage: kafka-storage format [-h] --config CONFIG --cluster-id CLUSTER_ID [--ignore-formatted]
kafka-storage: error: argument --cluster-id/-t: expected one argument
{code}

This can be worked around by putting the ID in quotes, or by using an "=" between the "--cluster-id" and the Uuid.

We can solve this going forward by not generating random Uuid's that contain a leading dash.


~~~~

---

## KAFKA-13998: JoinGroupRequestData 'reason' can be too large

https://issues.apache.org/jira/browse/KAFKA-13998

Given fix versions: 3.2.1, 3.3.0
JIRA affects (masked from the system): 3.2.0

- `KAFKA-13998@3.2.0`: config 3.2.0, metadata answer **affected** (listed_affected)
- `KAFKA-13998@3.1.2`: config 3.1.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.2.0

### Description

~~~~
We saw an exception like this: 

```org.apache.kafka.streams.errors.StreamsException: java.lang.RuntimeException: 'reason' field is too long to be serialized 3 at org.apache.kafka.streams.processor.internals.StreamThread.runLoop(StreamThread.java:627) 4 at org.apache.kafka.streams.processor.internals.StreamThread.run(StreamThread.java:551) 5Caused by: java.lang.RuntimeException: 'reason' field is too long to be serialized 6 at org.apache.kafka.common.message.JoinGroupRequestData.addSize(JoinGroupRequestData.java:465) 7 at org.apache.kafka.common.protocol.SendBuilder.buildSend(SendBuilder.java:218) 8 at org.apache.kafka.common.protocol.SendBuilder.buildRequestSend(SendBuilder.java:187) 9 at org.apache.kafka.common.requests.AbstractRequest.toSend(AbstractRequest.java:101) 10 at org.apache.kafka.clients.NetworkClient.doSend(NetworkClient.java:524) 11 at org.apache.kafka.clients.NetworkClient.doSend(NetworkClient.java:500) 12 at org.apache.kafka.clients.NetworkClient.send(NetworkClient.java:460) 13 at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.trySend(ConsumerNetworkClient.java:499) 14 at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:255) 15 at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:236) 16 at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:215) 17 at org.apache.kafka.clients.consumer.internals.AbstractCoordinator.joinGroupIfNeeded(AbstractCoordinator.java:437) 18 at org.apache.kafka.clients.consumer.internals.AbstractCoordinator.ensureActiveGroup(AbstractCoordinator.java:371) 19 at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.poll(ConsumerCoordinator.java:542) 20 at org.apache.kafka.clients.consumer.KafkaConsumer.updateAssignmentMetadataIfNeeded(KafkaConsumer.java:1271) 21 at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:1235) 22 at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:1215) 23 at org.apache.kafka.streams.processor.internals.StreamThread.pollRequests(StreamThread.java:969) 24 at org.apache.kafka.streams.processor.internals.StreamThread.pollPhase(StreamThread.java:917) 25 at org.apache.kafka.streams.processor.internals.StreamThread.runOnce(StreamThread.java:736) 26 at org.apache.kafka.streams.processor.internals.StreamThread.runLoop(StreamThread.java:589) 27 ... 1 more```

This appears to be caused by the code passing an entire stack trace in the `rejoinReason`.  See https://github.com/apache/kafka/blob/3.2.0/clients/src/main/java/org/apache/kafka/clients/consumer/internals/AbstractCoordinator.java#L481
~~~~

---

## KAFKA-14089: Flaky ExactlyOnceSourceIntegrationTest.testSeparateOffsetsTopic

https://issues.apache.org/jira/browse/KAFKA-14089

Given fix versions: 3.8.0
JIRA affects (masked from the system): 3.3.0

- `KAFKA-14089@3.3.0`: config 3.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-14089@3.2.3`: config 3.2.3, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
It looks like the sequence got broken around "65535, 65537, 65536, 65539, 65538, 65541, 65540, 65543"
~~~~

### Comments (7)

1.

~~~~
cc [~ChrisEgerton]
~~~~

2.

~~~~
Thanks [~mimaison]. We don't assert on order of records, just that the expected seqnos were present in any order, so the wonkiness around 65535 isn't actually an issue (and it's even present in the stringified representation of both the expected _and_ the actual seqno sets).

After doing some Bash scrubbing on the file attached to the ticket, it looks like seqnos start to be missing (i.e., they're in the expected set but not the actual) between 114463 and 114754. Not every seqno in that range is missing, but there's 105 missing in total. After that, starting at 114755, there's 105 extra (i.e., in the actual set but not the expected) seqnos.

Given that the issues crop up at the very end of the seqno set, it seems like this could be caused by non-graceful shutdown of the worker after exactly-once support is disabled, or even possibly the recently-discovered KAFKA-14079. -It's a little worrisome, though, since the results here indicate possible data loss.- Actually, on second thought, this is probably not data loss, since we're reading the records that have been produced to Kafka, but not necessarily the records whose offsets have been committed.

If this was on Jenkins, do you have a link to the CI run that caused it? Or if it was encountered elsewhere, do you have any logs available? I'll try to kick off some local runs but I'm in the middle of stress-testing my laptop with the latest KIP-618 system tests and may not be able to reproduce locally.

I suspect a fix for this would involve reading the last-committed offset for each task, then only checking seqnos for that task up to the seqno in that offset. But I'd like to have a better idea of what exactly is causing the failure before pulling the trigger on that, especially if it's unclean task/worker shutdown and we can find a way to fix that instead of adjusting our tests to handle sloppy shutdowns.
~~~~

3.

~~~~
I've hit this issue locally and I can reproduce it fairly consistently. See attached logs

[^org.apache.kafka.connect.integration.ExactlyOnceSourceIntegrationTest.testSeparateOffsetsTopic.test.stdout] 
~~~~

4.

~~~~
Thanks Mickael. I put together a draft fix [here|https://github.com/apache/kafka/pull/12429], although I still haven't been able to replicate the failure locally. If you have time, would you mind giving it a try and see if it has positive effects in your environment? I can also kick off several Jenkins builds by re-triggering CI runs, although that will be more time-consuming as it will run the build for the whole project instead of just Connect.
~~~~

5.

~~~~
Failure occurred on PR build: https://ci-builds.apache.org/blue/organizations/jenkins/Kafka%2Fkafka-pr/detail/PR-14699/24/tests/

 
{code:java}
org.apache.kafka.connect.runtime.rest.errors.ConnectRestException: Could not execute PUT request. Error response: {"error_code":500,"message":"Request timed out"}Stacktraceorg.apache.kafka.connect.runtime.rest.errors.ConnectRestException: Could not execute PUT request. Error response: {"error_code":500,"message":"Request timed out"}	at org.apache.kafka.connect.util.clusters.EmbeddedConnect.putConnectorConfig(EmbeddedConnect.java:272)	at org.apache.kafka.connect.util.clusters.EmbeddedConnect.configureConnector(EmbeddedConnect.java:196)	at org.apache.kafka.connect.util.clusters.EmbeddedConnectCluster.configureConnector(EmbeddedConnectCluster.java:48)	at org.apache.kafka.connect.integration.ExactlyOnceSourceIntegrationTest.testSeparateOffsetsTopic(ExactlyOnceSourceIntegrationTest.java:776)	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)	at java.lang.reflect.Method.invoke(Method.java:498)	at org.junit.runners.model.FrameworkMethod$1.runReflectiveCall(FrameworkMethod.java:59)	at org.junit.internal.runners.model.ReflectiveCallable.run(ReflectiveCallable.java:12)	at org.junit.runners.model.FrameworkMethod.invokeExplosively(FrameworkMethod.java:56)	at org.junit.internal.runners.statements.InvokeMethod.evaluate(InvokeMethod.java:17)	at org.junit.internal.runners.statements.RunBefores.evaluate(RunBefores.java:26)	at org.junit.internal.runners.statements.RunAfters.evaluate(RunAfters.java:27)	at org.junit.runners.ParentRunner$3.evaluate(ParentRunner.java:306)	at org.junit.runners.BlockJUnit4ClassRunner$1.evaluate(BlockJUnit4ClassRunner.java:100)	at org.junit.runners.ParentRunner.runLeaf(ParentRunner.java:366)	at org.junit.runners.BlockJUnit4ClassRunner.runChild(BlockJUnit4ClassRunner.java:103)	at org.junit.runners.BlockJUnit4ClassRunner.runChild(BlockJUnit4ClassRunner.java:63)	at org.junit.runners.ParentRunner$4.run(ParentRunner.java:331)	at org.junit.runners.ParentRunner$1.schedule(ParentRunner.java:79)	at org.junit.runners.ParentRunner.runChildren(ParentRunner.java:329)	at org.junit.runners.ParentRunner.access$100(ParentRunner.java:66)	at org.junit.runners.ParentRunner$2.evaluate(ParentRunner.java:293)	at org.junit.runners.ParentRunner$3.evaluate(ParentRunner.java:306) {code}
~~~~

6.

~~~~
I've seen this again as well. https://ge.apache.org/scans/tests?search.names=Git%20branch&search.relativeStartTime=P28D&search.rootProjectNames=kafka&search.timeZoneId=America%2FLos_Angeles&search.values=trunk&tests.container=org.apache.kafka.connect.integration.ExactlyOnceSourceIntegrationTest&tests.test=testSeparateOffsetsTopic
~~~~

7.

~~~~
Should be fixed by [https://github.com/apache/kafka/pull/16306|https://github.com/apache/kafka/pull/16306.]
~~~~

---

## KAFKA-14275: KRaft Controllers should crash after failing to apply any metadata record 

https://issues.apache.org/jira/browse/KAFKA-14275

Given fix versions: 3.4.1, 3.5.2, 3.6.2, 3.7.0
JIRA affects (masked from the system): 3.3.1

- `KAFKA-14275@3.3.1`: config 3.3.1, metadata answer **affected** (listed_affected)
- `KAFKA-14275@3.3.0`: config 3.3.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
When replaying records on a standby controller, any error encountered will halt further processing of that batch. Currently we log an error and allow the controller to continue normal operation. In contrast a similar error on the active controller causes it to halt and exit the jvm. This is inconsistent behavior as nothing prevents a standby from eventually becoming the active controller (even when it had skipped over a record batch). We should halt the process in the case of a standby controller as well.
~~~~

### Comments (1)

1.

~~~~
PR – https://github.com/apache/kafka/pull/12709
~~~~

---

## KAFKA-14388: NPE When Retrieving StateStore with new Processor API

https://issues.apache.org/jira/browse/KAFKA-14388

Given fix versions: 3.3.2, 3.4.0
JIRA affects (masked from the system): 3.3.0, 3.3.1

- `KAFKA-14388@3.3.1`: config 3.3.1, metadata answer **affected** (listed_affected)
- `KAFKA-14388@3.2.3`: config 3.2.3, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.3

### Description

~~~~
Using the new Processor API introduced with KIP-820 when adding a state store to the Processor when executing `context().getStore("store-name")` always returns `null` as the store is not in the `stores` `HashMap` in the `ProcessorStateManager`.  This occurs even when using the `ConnectedStoreProvider.stores()` method

I've confirmed the store is associated with the processor by viewing the `Topology` description.   

From some initial triage, it looks like the store is never registered.
~~~~

### Comments (3)

1.

~~~~
PR with details of the bug https://github.com/apache/kafka/pull/12861
~~~~

2.

~~~~
Merged PR to trunk
~~~~

3.

~~~~
Cherry-picked to 3.3
~~~~

---

## KAFKA-14693: KRaft Controller and ProcessExitingFaultHandler can deadlock shutdown

https://issues.apache.org/jira/browse/KAFKA-14693

Given fix versions: 3.4.1, 3.5.0
JIRA affects (masked from the system): 3.4.0

- `KAFKA-14693@3.4.0`: config 3.4.0, metadata answer **affected** (listed_affected)
- `KAFKA-14693@3.3.2`: config 3.3.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
h1. Problem

When the kraft controller encounters an error that it cannot handle it calls {{ProcessExitingFaultHandler}} which calls {{Exit.exit}} which calls {{{}Runtime.exit{}}}.

Based on the Runtime.exit documentation:
{quote}All registered [shutdown hooks|https://docs.oracle.com/javase/8/docs/api/java/lang/Runtime.html#addShutdownHook-java.lang.Thread-], if any, are started in some unspecified order and allowed to run concurrently until they finish. Once this is done the virtual machine [halts|https://docs.oracle.com/javase/8/docs/api/java/lang/Runtime.html#halt-int-].
{quote}
One of the shutdown hooks registered by Kafka is {{{}Server.shutdown(){}}}. This shutdown hook eventually calls {{{}KafkaEventQueue.close{}}}. This last close method joins on the controller thread. Unfortunately, the controller thread also joined waiting for the shutdown hook thread to finish.

Here are an sample thread stacks:
{code:java}
   "QuorumControllerEventHandler" #45 prio=5 os_prio=0 cpu=429352.87ms elapsed=620807.49s allocated=38544M defined_classes=353 tid=0x00007f5aeb31f800 nid=0x80c in Object.wait()  [0x00007f5a658fb000]
     java.lang.Thread.State: WAITING (on object monitor)                                                                                                                                                                                                            at java.lang.Object.wait(java.base@17.0.5/Native Method)
          - waiting on <no object reference available>
          at java.lang.Thread.join(java.base@17.0.5/Thread.java:1304)
          - locked <0x00000000a29241f8> (a org.apache.kafka.common.utils.KafkaThread)
          at java.lang.Thread.join(java.base@17.0.5/Thread.java:1372)
          at java.lang.ApplicationShutdownHooks.runHooks(java.base@17.0.5/ApplicationShutdownHooks.java:107)
          at java.lang.ApplicationShutdownHooks$1.run(java.base@17.0.5/ApplicationShutdownHooks.java:46)
          at java.lang.Shutdown.runHooks(java.base@17.0.5/Shutdown.java:130)
          at java.lang.Shutdown.exit(java.base@17.0.5/Shutdown.java:173)
          - locked <0x00000000ffe020b8> (a java.lang.Class for java.lang.Shutdown)
          at java.lang.Runtime.exit(java.base@17.0.5/Runtime.java:115)
          at java.lang.System.exit(java.base@17.0.5/System.java:1860)
          at org.apache.kafka.common.utils.Exit$2.execute(Exit.java:43)
          at org.apache.kafka.common.utils.Exit.exit(Exit.java:66)
          at org.apache.kafka.common.utils.Exit.exit(Exit.java:62)
          at org.apache.kafka.server.fault.ProcessExitingFaultHandler.handleFault(ProcessExitingFaultHandler.java:54)
          at org.apache.kafka.controller.QuorumController$ControllerWriteEvent$1.apply(QuorumController.java:891)
          at org.apache.kafka.controller.QuorumController$ControllerWriteEvent$1.apply(QuorumController.java:874)
          at org.apache.kafka.controller.QuorumController.appendRecords(QuorumController.java:969){code}
and
{code:java}
  "kafka-shutdown-hook" #35 prio=5 os_prio=0 cpu=43.42ms elapsed=378593.04s allocated=4732K defined_classes=74 tid=0x00007f5a7c09d800 nid=0x4f37 in Object.wait()  [0x00007f5a47afd000]
     java.lang.Thread.State: WAITING (on object monitor)
          at java.lang.Object.wait(java.base@17.0.5/Native Method)
          - waiting on <no object reference available>
          at java.lang.Thread.join(java.base@17.0.5/Thread.java:1304)
          - locked <0x00000000a272bcb0> (a org.apache.kafka.common.utils.KafkaThread)
          at java.lang.Thread.join(java.base@17.0.5/Thread.java:1372)
          at org.apache.kafka.queue.KafkaEventQueue.close(KafkaEventQueue.java:509)
          at org.apache.kafka.controller.QuorumController.close(QuorumController.java:2553)
          at kafka.server.ControllerServer.shutdown(ControllerServer.scala:521)
          at kafka.server.KafkaRaftServer.shutdown(KafkaRaftServer.scala:184)
          at kafka.Kafka$.$anonfun$main$3(Kafka.scala:99)
          at kafka.Kafka$$$Lambda$406/0x0000000800fb9730.apply$mcV$sp(Unknown Source)
          at kafka.utils.Exit$.$anonfun$addShutdownHook$1(Exit.scala:38)
          at kafka.Kafka$$$Lambda$407/0x0000000800fb9a10.run(Unknown Source)
          at java.lang.Thread.run(java.base@17.0.5/Thread.java:833)
          at org.apache.kafka.common.utils.KafkaThread.run(KafkaThread.java:64) {code}
h1. Possible Solution

A possible solution is to have the controller's unhandled fault handler call {{Runtime.halt}} instead of {{{}Runtime.exit{}}}.
~~~~

---

## KAFKA-14831: Illegal state errors should be fatal in transactional producer

https://issues.apache.org/jira/browse/KAFKA-14831

Given fix versions: 3.6.0
JIRA affects (masked from the system): 3.2.3

- `KAFKA-14831@3.2.3`: config 3.2.3, metadata answer **affected** (listed_affected)
- `KAFKA-14831@3.2.2`: config 3.2.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.5, 3.6, 3.6.0

### Description

~~~~
In KAFKA-14830, the producer hit an illegal state error. The error was propagated to the {{Sender}} thread and logged, but the producer otherwise continued on. It would be better to make illegal state errors fatal since continuing to write to transactions when the internal state is inconsistent may cause incorrect and unpredictable behavior.
~~~~

### Comments (5)

1.

~~~~
Is this near completion? If not I'll move this out of 3.5 as we're now past code freeze.
~~~~

2.

~~~~
[~jolshan] has been providing most of the feedback on the PR. [~jolshan] - what do you think? Is it "near" to be doing done or no? I'd prefer to wait if there's any question about correctness/stability.
~~~~

3.

~~~~
I guess I had assumed we missed the code freeze and haven't been treating this as a blocker. It might be good to wait until 3.6.
~~~~

4.

~~~~
Sounds good, [~jolshan]. I updated the fix version to 3.6.0. Thanks!
~~~~

5.

~~~~
Thanks!
~~~~

---

## KAFKA-15102: Mirror Maker 2 - KIP690 backward compatibility

https://issues.apache.org/jira/browse/KAFKA-15102

Given fix versions: 3.1.3, 3.2.4, 3.3.3, 3.4.2, 3.5.2, 3.6.0
JIRA affects (masked from the system): 3.1.0

- `KAFKA-15102@3.1.0`: config 3.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-15102@3.0.2`: config 3.0.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.1.0, 4.0

### Description

~~~~
According to KIP690, "When users upgrade an existing MM2 cluster they don’t need to change any of their current configuration as this proposal maintains the default behaviour for MM2."

Now, the separator is subject to customization.

As a consequence, when an MM2 upgrade is performed, if the separator was customized with replication.policy.separator, the name of this internal topic changes. It then generates issues like:
Caused by: java.util.concurrent.ExecutionException: org.apache.kafka.common.errors.InvalidTopicException: Topic 'mm2-offset-syncs_bkts28_internal' collides with existing topics: mm2-offset-syncs.bkts28.internal

It has been observed that the replication can then be broken sometimes several days after the upgrade (reason not identified). By deleting the old topic name, it recovers.
~~~~

### Comments (11)

1.

~~~~
[~ddufour1a] Thanks for raising this. I believe if we wanted to preserve backward compatibility perfectly, we would have had to ignore the custom separator when creating topics affected by KIP-690, and possibly introduced separate opt-in configuration logic to disable that behavior (i.e., resume taking custom separators into account, even for topics that were not affected prior to KIP-690).

However, since 3.1.0 came out a year and a half ago, things are less cut-and-dry: there may be more negative fallout for users who are accustomed to the current behavior than what's currently being experienced by those who are used to the previous behavior.

One possibility could be to revert to older behavior for the remainder of our 3.x.y releases with a single configuration property such as {{replication.policy.internal.topic.separator.enabled}} that defaults to {{false}} for now and, come 4.0, defaults to {{{}true{}}}.

[~omnia_h_ibrahim] [~mimaison] do either of you have thoughts on how to approach this accidental break in compatibility? It's probably worth bringing this up in a discussion thread on the user/dev mailing lists, but I'd rather get some feedback on a potential fix before bringing this before a larger audience.
~~~~

2.

~~~~
Thanks, [~ddufour1a] for raising this. The backward compatibility mentioned in the KIP accounted only for using the default separator configuration and didn't address the usage custom separator (my mistake here). [~ChrisEgerton] I think having `{{{}replication.policy.internal.topic.separator.enabled` is a good option.{}}}

{{{}We can also update the backward compatibility section in KIP-690 to ask users to provide a custom implementation that the override `ReplicationPolicy.{}}}offsetSyncsTopic`and `ReplicationPolicy.checkpointsTopic` methods to use old topics if they still want to use the old internal topics or delete them so they are aware of this issue.
~~~~

3.

~~~~
[~omnia_h_ibrahim] Good call 👍 we should definitely update the compatibility section in the KIP to mention this. We may also want list the affected versions and link to this issue for further context.
~~~~

4.

~~~~
[~ChrisEgerton] I updated the compatibility section in the KIP with the impacted versions and linked to this JIRA. I can open a small KIP to have `{{{}replication.policy.internal.topic.separator.enabled` if you don't have time to do it. {}}}
~~~~

5.

~~~~
Thanks [~omnia_h_ibrahim], I'd love it if you could take on that KIP!
~~~~

6.

~~~~
[~ChrisEgerton] I'll prepare the KIP this week.
~~~~

7.

~~~~
💯 [~omnia_h_ibrahim] I've assigned you this ticket so nobody else picks it up by mistake; feel free to unassign if you no longer want to work on this.
~~~~

8.

~~~~
I opened this small KIP to fix this [https://cwiki.apache.org/confluence/display/KAFKA/KIP-949%3A+Add+flag+to+enable+the+usage+of+topic+separator+in+MM2+DefaultReplicationPolicy]
~~~~

9.

~~~~
The KIP got accepted and the PR is ready
~~~~

10.

~~~~
Thanks for this
~~~~

11.

~~~~
Closed
~~~~

---

## KAFKA-15114: StorageTool help specifies user as parameter not name

https://issues.apache.org/jira/browse/KAFKA-15114

Given fix versions: 3.5.1, 3.6.0
JIRA affects (masked from the system): 3.5.0

- `KAFKA-15114@3.5.0`: config 3.5.0, metadata answer **affected** (listed_affected)
- `KAFKA-15114@3.4.1`: config 3.4.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
StorageTool help message current specifies setting a {{user}} parameter when creating a SCRAM record for bootstrap.

The StorageTool parses and only accepts the parameter as {{name}} and so the help message is wrong.

The choice of using {{name}} vs. {{user}} as a parameter is because internally the record uses name, all tests using the StorageTool use name as a parameter, KafkaPrincipals are created with {{name}} and because creating SCRAM credentials is done with {{--entity-name}}

I will change the help to specify {{name}} instead of {{user}}.


 
~~~~

---

## KAFKA-15490: Invalid path provided to the log failure channel upon I/O error when writing broker metadata checkpoint

https://issues.apache.org/jira/browse/KAFKA-15490

Given fix versions: 3.6.2
JIRA affects (masked from the system): 3.4.0, 3.4.1, 3.5.1, 3.6.1

- `KAFKA-15490@3.5.1`: config 3.5.1, metadata answer **affected** (listed_affected)
- `KAFKA-15490@3.3.2`: config 3.3.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.4

### Description

~~~~
There is a small bug/typo in the handling of I/O error when writing broker metadata checkpoint in {{{}KafkaServer{}}}. The path provided to the log dir failure channel is the full path of the checkpoint file whereas only the log directory is expected ([source|https://github.com/apache/kafka/blob/3.4/core/src/main/scala/kafka/server/KafkaServer.scala#L958C8-L961C8]).
{code:java}
case e: IOException =>
   val dirPath = checkpoint.file.getAbsolutePath
   logDirFailureChannel.maybeAddOfflineLogDir(dirPath, s"Error while writing meta.properties to $dirPath", e){code}
As a result, after an {{IOException}} is captured and enqueued in the log dir failure channel ({{{}<logDir>{}}} is to be replaced with the actual path of the log directory):
{code:java}
[2023-09-22 17:07:32,052] ERROR Error while writing meta.properties to <logDir>/meta.properties (kafka.server.LogDirFailureChannel) java.io.IOException{code}
The log dir failure handler cannot lookup the log directory:
{code:java}
[2023-09-22 17:07:32,053] ERROR [LogDirFailureHandler]: Error due to (kafka.server.ReplicaManager$LogDirFailureHandler) org.apache.kafka.common.errors.LogDirNotFoundException: Log dir <logDir>/meta.properties is not found in the config.{code}
An immediate fix for this is to use the {{logDir}} provided from to the checkpointing method instead of the path of the metadata file.

For brokers with only one log directory, this bug will result in preventing the broker from shutting down as expected.

The L{{{}ogDirNotFoundException{}}} then kills the log dir failure handler thread, and subsequent {{IOException}} are not handled, and the broker never stops.
{code:java}
[2024-02-27 02:13:13,564] INFO [LogDirFailureHandler]: Stopped (kafka.server.ReplicaManager$LogDirFailureHandler){code}
Another consideration here is whether the {{LogDirNotFoundException}} should terminate the log dir failure handler thread.
~~~~

---

## KAFKA-15602: Breaking change in 3.4.0 ByteBufferSerializer

https://issues.apache.org/jira/browse/KAFKA-15602

Given fix versions: 3.4.2, 3.5.2, 3.6.1, 3.7.0
JIRA affects (masked from the system): 3.4.0, 3.4.1, 3.5.0, 3.5.1, 3.6.0

- `KAFKA-15602@3.5.1`: config 3.5.1, metadata answer **affected** (listed_affected)
- `KAFKA-15602@3.3.2`: config 3.3.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.4.0, 3.3.2, 3.4, 0.10, 3.5.2, 3.4.2, 3.6

### Description

~~~~
[This PR|https://github.com/apache/kafka/pull/12683/files] claims to have solved the situation described by KAFKA-4852, namely, to have ByteBufferSerializer respect ByteBuffers wrapping byte arrays with non-0 offsets (or, put another way, to honor the buffer's position() as the start point to consume bytes from). Unfortunately, it failed to actually do this, and instead changed the expectations for how an input ByteBuffer's limit and position should be set before being provided to send() on a producer configured with ByteBufferSerializer. Code that worked with pre-3.4.0 releases now produce 0-length messages instead of the intended messages, effectively introducing a breaking change for existing users of the serializer in the wild.

Here are a few different inputs and serialized outputs under pre-3.4.0 and 3.4.0+ to summarize the breaking change:
||buffer argument||3.3.2 serialized output||3.4.0+ serialized output||
|ByteBuffer.wrap("test".getBytes(UTF_8))|len=4 
val=test|len=4 val=test|
|ByteBuffer.allocate(8).put("test".getBytes(UTF_8)).flip()|len=4 
val=test|len=0 val=|
|ByteBuffer.allocate(8).put("test".getBytes(UTF_8))|len=8 val=test<0><0><0><0>|len=4 val=test|
|ByteBuffer buff = ByteBuffer.allocate(8).put("test".getBytes(UTF_8));
buff.limit(buff.position());|len=4 
val=test|len=4 val=test|
|ByteBuffer.wrap("test".getBytes(UTF_8), 1, 3)|len=4 val=test|len=1 val=t|

Notably, plain-wrappers of byte arrays continue to work under both versions due to the special case in the serializer for them. I suspect that this is the dominant use-case, which is why this has apparently gone un-reported to this point. The wrapped-with-offset case fails for both cases for different reasons (the expected value would be "est"). As demonstrated here, you can ensure that a manually assembled ByteBuffer will work under both versions by ensuring that your buffers start have position == limit == message-length (and an actual desired start position of 0). Clearly, though, behavior has changed dramatically for the second and third case there, with the 3.3.2 behavior, in my experience, aligning better with naive expectations.

[Previously|https://github.com/apache/kafka/blob/35a0de32ee3823dfb548a1cd5d5faf4f7c99e4e0/clients/src/main/java/org/apache/kafka/common/serialization/ByteBufferSerializer.java], the serializer would just rewind() the buffer and respect the limit as the indicator as to how much data was in the buffer. So, essentially, the prevailing contract was that the data from position 0 (always!) up to the limit on the buffer would be serialized; so it was really just the limit that was honored. So if, per the original issue, you have a byte[] array wrapped with, say, ByteBuffer.wrap(bytes, 3, 5) then that will yield a ByteBuffer() with position = 3 indicating the desired start point to read from, but effectively ignored by the serializer due to the rewind().

So while the serializer didn't work when presenting a ByteBuffer view onto a sub-view of a backing array, it did however follow expected behavior when employing standard patterns to populate ByteBuffers backed by larger-than-necessary arrays and using limit() to identify the end of actual data, consistent with conventional usage of flip() to switch from writing to a buffer to setting it up to be read from (e.g., to be passed into a producer.send() call). E.g.,
{code:java}
ByteBuffer bb = ByteBuffer.allocate(TOO_MUCH);
... // some sequence of 
bb.put(...); // populate buffer with some number of bytes less than TOO_MUCH ... 
bb.flip(); /* logically, this says "I am done writing, let's set this up for reading"; pragmatically, it sets the limit to the current position so that whoever reads the buffer knows when to stop reading, and sets the position to zero so it knows where to start reading from */ 
producer.send(bb); {code}
Technically, you wouldn't even need to use flip() there, since position is ignored; it would sufficient to just call {{{}bb.limit(bb.position()){}}}. Notably, a buffer constructed using any variant of ByteBuffer.wrap() is essentially immediately in read-mode with position indicating the start and limit the end.

With the change introduced in 3.4.0, however, the contract changes dramatically, and the code just presented produces a 0-byte message. As indicated above, it also continues to fail if you just passed in an offset-specified ByteBuffer.wrap()ped message, too, i.e., the case described by KAFKA-4852:
{code:java}
@Test
public void testByteBufferSerializerOnOffsetWrappedBytes() {
    final byte[] bytes = "Hello".getBytes(UTF_8);
    try (final ByteBufferSerializer serializer = new ByteBufferSerializer()) {
        assertArrayEquals("ello".getBytes(UTF_8), 
                // FAILS: this will yield "H", not "ello"
                serializer.serialize(topic, ByteBuffer.wrap(bytes, 1, bytes.length - 1)));
    }
}
 {code}
What happened here?

The resulting PR, it seems, focussed on a flawed proposed test case in the first comment of KAFKA-4852 that failed against pre-3.4.0 Kafka. I reproduce that here with commented annotations from me: 
{code:java}
@Test // flawed proposed test case
public void testByteBufferSerializer() {
    final byte[] bytes = "Hello".getBytes(UTF_8);
    final ByteBuffer buffer = ByteBuffer.allocate(7);
    buffer.put(bytes);
    // buffer.flip();   <-- would make the test work

    try (final ByteBufferSerializer serializer = new ByteBufferSerializer()) {
        assertArrayEquals(bytes, serializer.serialize(topic, buffer));
    }
}  {code}
In pre-3.4.0, this would yield a 7-byte serialization of "Hello" followed by 2 0-value bytes. I contend that this was actually expected and correct behavior, as the ByteBuffer had never had its limit set, so the implicit and mildly expected contract was never actually abided by. If there was a buffer.flip() after the .put(bytes) call, as the calling code _should_ have applied, however, then the test would have succeeded. In short, by trying to make this test case succeed, I think this PR represented nothing more than a misunderstanding for how one should prepare ByteBuffers for reading, but has managed to result in a breaking change. The breaking nature of this was actually briefly noted in PR comments but kind of shrugged off with some test changes and explanatory comments on the class.

Obviously a correction to restore 3.3.2 behavior would represent another breaking change for users that are running on 3.4+, unless they were also somewhat surprisingly configuring buffers for position() == limit() before passing them to send. Arguably, it would also be a breaking change (though possibly not one of great consequence) if either version was changed to correctly handle the wrapped-with-offset case as represented in the original ticket.

I do not have much experience contending with a situation like this, but at the risk of jumping to a solution here, I wonder if the only way to really move forward safely and unambiguously here is to remove ByteBufferSerializer as it stands and replace it with a differently named substitute that handles both the plain-wrapped special case and just serializes content from position() to limit(), forcing an evaluation by users when upgrading as to whether the provided byte buffer is correctly configured or not. Of course, a change like that would have be released at an appropriate version level, too, so I don't know exactly what the desired interim behavior would be (deprecation?). I believe I would be eager to contribute to a fix, but obviously I would need guidance from maintainers regarding the correct path forward semantically.
~~~~

### Comments (24)

1.

~~~~
Hi [~luke.kirby] ,

Thanks for reporting this.  I briefly went over the code a bit and I can now understand your concern.

The original documentation mentioned the user "{_}Do not need to flip{_}", I assume that means the serializer will automatically rewind the position to zero for the user as flip explicitly stated ".{_}..limit is set to the current position and then the position is set to zero{_}".  However, the serializer API didn't make any assumptions to the current position of the buffer, so it is hard to say if the original design intended to handle a user-given offset... From reading the unit test, it doesn't seem so.

I can see the problem comes from the serializer doesn't know if the position is an offset or just the next byte to be written.  These are two different definitions of the position so it doesn't really make sense to handle both cases in a single API call.

I wonder if the sensible thing to do for now is to is to make the contract and expectations more explicit on the Javadoc, i.e., the serialize method doesn't support user-provided offset, and the serializer will rewind the current offset to zero for the user.

[~guozhang] - Would you kindly provide some input on this issue? As you reviewed the KAFKA-4852. 

Thanks!

P
~~~~

2.

~~~~
{quote}The original documentation mentioned the user "{_}Do not need to flip{_}", I assume that means the serializer will automatically rewind the position to zero for the user as flip explicitly stated ".{_}..limit is set to the current position and then the position is set to zero{_}".  However, the serializer API didn't make any assumptions to the current position of the buffer, so it is hard to say if the original design intended to handle a user-given offset... From reading the unit test, it doesn't seem so.
{quote}
Ah, no there was no documentation on the serializer before; the "Do not need to flip" comment was introduced with the breaking change in 3.4, though it's pretty plain to see that previous users of the serializer likely _were_ flipping, or, at least, writing buffers (with content starting at position 0), flipping them, and sending them _worked_ but now doesn't.

Looking at the history for the file, it does look like prior to the 3.4 change it always did a rewind() so yeah, position() on the buffer has never really been respected. Now, it kind of _does_ respect position; but not in the expected way, as it essentially identifies the end of the buffer rather than the start.

I don't know why the original version used a rewind() rather than expecting the buffer to already have a position() reflecting the start point to read from, since in my experience this is clearly the convention for passing ByteBuffer inputs for reading in any library I'm familiar with, and I expect the expectation of most users; perhaps I'm ignorant of some other pattern! I don't know if there's some valid contextual reason for it using explicit rewinds() before, but it seems unusual. My suggestion would be to replace the currently named ByteBufferSerializer with a new one that respects the standard interface unambiguously – i.e., it serializes data from buffer.pos() to buffer.limit(), continuing to use appropriate shortcuts for the simple wrap(byte[]) cases.
{quote}I wonder if the sensible thing to do for now is to is to make the contract and expectations more explicit on the Javadoc, i.e., the serialize method doesn't support user-provided offset, and the serializer will rewind the current offset to zero for the user.
{quote}
Explicit documentation would surely be improvement, and is probably at the core of how this situation was arrived at, but it doesn't do anything about folk being surprised by the completely different behavior and broken output that worked from 0.10 - 3.3.2 when upgrading to 3.4.0... though hopefully they notice it. 

 

 
~~~~

3.

~~~~
The original intent of the PR was to make the serializer compatible with user offsets; I don't see any test that covers this, am I missing anything?

 

replace the currently named ByteBufferSerializer with a new one that respects the standard interface unambiguously

- We are talking about creating a separated serializer that handles the user offset aren't we? It seems to be the only way to handle this case.
~~~~

4.

~~~~
{quote}The original intent of the PR was to make the serializer compatible with user offsets; I don't see any test that covers this, am I missing anything?
{quote}
Yep, no test that covers it. I wrote up the kind of test you'd use to assess it above and it fails. I think the actual intent of the PR writer was to handle the case that they noticed (incorrectly, I contend) and the offsets question just kind of got accidentally ignored. That said, I'm more concerned about the breaking behavior change more than the specifics of handling offsets, which neither version has ever done properly.

 
{quote}We are talking about creating a separated serializer that handles the user offset aren't we? It seems to be the only way to handle this case.
{quote}
 
Yeah, I think so. Again, though, I think something has to be done to advertise to users that the contract here has changed and that upgrades to 3.4 will more likely than not result in previously functional producers emitting 0-length messages if anything other than a ByteBuffer.wrap(byte[]) message is provided to send(), and that removing the existing class may be the only way to really achieve that safely – i.e., break loudly. Totally not my call though!
~~~~

5.

~~~~
Hi [~luke.kirby] , i think we need to do two things here. One is probably revert the change and patch it with better documentation and tests.  Second is optional, if you want to introduce a separated serializer to handle offset, I think we might need to write a KIP.  This is a long term solution.  Are you interested in helping out to resolve this issue?  I can help reviewing the code and KIP.
~~~~

6.

~~~~
Hi Philip! Are we at all concerned about how reverting that change might break other folks' code if they'd started a project in 3.4+ or had already changed their buffer configurations without complaining about it? Not my decision to make here, obviously, I just want to confirm that that's not a big concern.

And yeah, we'd like to be involved in both of these things and am in the process of doing some paperwork to make that accomplishable; might take a little time though.
~~~~

7.

~~~~
Hi [~luke.kirby] 

I think since the PR didn't actually solve the problem, but introduced a subtle behavior change to the previous implementation (flip the position), whether it was the correct way of setting the position or not, so it seems logical to me to revert that PR and actually try to solve KAFKA-4852.

I wonder what do folks on the other ticket think - [~LSK] [~guozhang] [~wdaehn]

P
~~~~

8.

~~~~
I think that's a pretty reasonable take, [~pnee]! Will give the others involved some time to chime in. Should we be doing anything about changing the state of KAFKA-4852 given that it doesn't seem like it's really resolved at all?
~~~~

9.

~~~~
Hey, [~pnee] pointed me to this ticket. I am not a ByterBuffer expert, but it seems to me, that a reasonable API contract would be, that the user is responsible to prepare the buffer for reading, and the returned byte[] array is from the buffer's position to limit. Any other behavior seems odd to me. Thoughts? (Not sure if the position should be modified by the serializer or not thought? I tend to think yes?)

Overall, it seems like a case to fix forward? If the above propose contract makes sense, it's rather a bug fix and we should just push it out? (In the end KAFKA-4852 was done without a KIP, too – kinda boarder line to begin with...) 

For example (1), it seems it would be a breaking change though? Given that this is indeed the "prime" use-case, doing a KIP might indeed be better? (For this case, reverting KAFKA-4852 might indeed be a good call, as it breaks more than it fixes as it seems.)

For example (2), pre-3.4 seems to be correct, while 3.4+ is broken.

For example (3), pre-3.4 seems to be correct, while 3.4+ seems to be incorrect – the user did not limit to 4 bytes, so all 8 bytes should be returned IMHO?

For example (4), pre-3.4 seems to be incorrect, while 3.4+ seems to be incorrect, too? In the end, the position was not set back to zero, hence a zero-length array should be returned?

And last example (5), as already discussed, is also broken in all versions, but should result "est".
{quote}I can see the problem comes from the serializer doesn't know if the position is an offset or just the next byte to be written.  These are two different definitions of the position so it doesn't really make sense to handle both cases in a single API call.
{quote}
Not sure if I can follow here? What do you mean bey "is an offset or just the next byte to be written"? Why would position have two different definitions?

\cc [~showuon] as RM for 3.5.2 release – might be worth to get this fix in, too?
~~~~

10.

~~~~
Hi [~mjsax] - Thanks for the response!

I think your proposal can be a breaking change because, in both versions, the user is expecting the serializer to rewind the position, whether through flip or rewind...

To make the serializer also compatible with user-provided offset, I think your proposal would work, but it would require a KIP, to document the expectation, right? Because now we are asking the user to rewind the position to the starting position.
~~~~

11.

~~~~
Sounds fair. – Let me revert K4852 in all applicable branches and re-open it for a proper KIP. – Guess we can close this ticket afterwards?

 
~~~~

12.

~~~~
Great I think so. [~luke.kirby] - Do you agree? Also, do you agree with Matthias's proposal? Are you interested in writing a KIP?
~~~~

13.

~~~~
Btw: also left a comment on K4852: https://issues.apache.org/jira/browse/KAFKA-4852?focusedCommentId=17778727&page=com.atlassian.jira.plugin.system.issuetabpanels%3Acomment-tabpanel#comment-17778727 
~~~~

14.

~~~~
Hi [~pnee] , [~mjsax] – I largely agree with what's been said and am fully on board with the plan to revert the change from K4852. Thanks for taking care of that, Matthias!

That said, I'm not entirely sure I understand Matthias's point regarding example 1, which has the right behavior under both examples, and we would expect to work similarly under any revised serializers. I agree that I think example 4 highlights the weirdness of just not respecting position() at all, and we would expect different behavior under the serializer to emerge from the KIP.

I will leave it up to you to decide whether this change, that _might_ break users previously on 3.4+, has to be communicated strongly in some fashion to those upgrading. In the interest of avoiding _other_ interesting ways of breaking things, I agree with Philip that in the interest of minimizing surprising behavior under upgrades, creating a properly functioning serializer that respects starting position should be covered by a KIP and a new class with fresh, clean and good behavior, with the existing serializer maintaining its curious always-rewind behavior. I would still be interested in taking charge with a KIP there just because it seems like a nice lightweight KIP to get our feet wet with, anticipating that we might be interested in some others down the line.
~~~~

15.

~~~~
Thanks, [~luke.kirby] - Can you create a Jira to document what you intend to do in the KIP? I think we can close this issue after reverting the PR.  Let us know if you have any questions regarding the KIP process, we are here to help!
~~~~

16.

~~~~
{quote}I'm not entirely sure I understand Matthias's point regarding example 1,
{quote}
Well, in example one, the position is at 4, and if we say we want to respect position the result would be empty – the user would need to rewind to zero before calling the serializer to make it work. Does this make sense?

We can discuss details on a KIP, but instead of introducing a new class, I was thinking if we should use a config `enable.auto.rewind=true` (by default), that users can set to `false` to get the new behavior. For this case, we don't break compatibility, and it gives user the ability to add explicit rewind call before calling serialize before they change the config to `false`.
{quote}Can you create a Jira to document
{quote}
I think we can re-open K4852 for this purpse?
~~~~

17.

~~~~
>Well, in example one, the position is at 4, and if we say we want to respect position the result would be empty – the user would need to rewind to zero before calling the serializer to make it work. Does this make sense?

Ah, nah, ByteBuffer.wrap("test".getBytes()) yields a ByteBuffer with position=0 limit=4; i.e., it's already ready to be read.

I would hope to be able to get some time to start on the KIP sometime this week; happy for you two to tell me where I should do it!

 
~~~~

18.

~~~~
Hi [~luke.kirby] - Here's the guide to create a KIP: [https://cwiki.apache.org/confluence/display/kafka/kafka+improvement+proposals]

 
~~~~

19.

~~~~
> Ah, nah, ByteBuffer.wrap("test".getBytes()) yields a ByteBuffer with position=0 limit=4; i.e., it's already ready to be read.

Ah, great. For this case, there is not even a backward compatibility concern. – Should make it pretty easy to get the KIP approved for this case.
~~~~

20.

~~~~
[~luke.kirby] Thanks for reporting the issue, I read through the description / examples that you and [~mjsax] [~pnee] discussed, and I agree I totally misread the original issue while reviewing it. To make it quick into the hotfix version, I'm onboard with reverting the changes first.
~~~~

21.

~~~~
As discussed, reverted this in all applicable branches.
~~~~

22.

~~~~
Thanks so much team! Maybe not the right place to ask this, but is there a plan for a 3.4.2 release? I can see that there's a 3.5.2 just waiting on some things.

On the KIP front, I am still interested in pursuing that, but it's not as pressing a concern. Reading through the guidance there (thanks Philip!) it looks like I have to request committer status first? I'll probably get some CCLA stuff rolling on my end to make that happen.
~~~~

23.

~~~~
Hi [~luke.kirby] - You don't need to become a committer to write a KIP, apache committer means something different :)

 

You just need to send an email to the mailing list to request the permission per...
{code:java}
If this is your first time contributing:Sign up for the Developer mailing list dev@kafka.apache.org . The instructions to sign up are here: http://kafka.apache.org/contactCreate a wiki ID (https://cwiki.apache.org/confluence/signup.action)Create a Jira ID (It's a different system than the wiki) using the ASF Self-serve Portal (https://selfserve.apache.org/jira-account.html)Send an email to the dev mailing list (dev@kafka.apache.org) containing your wiki ID and Jira ID requesting permissions to contribute to Apache Kafka. {code}
Looking forward to seeing the KIP!
~~~~

24.

~~~~
[~luke.kirby] – it seems unlikely that there will be a 3.4.2 bug-fix release – I am actually surprised that we do a 3.5.2... Historically, we focus on bug-fix releases for the current release minor/major version (ie, currently 3.6) only.
~~~~

---

## KAFKA-15802: Trying to access uncopied segments metadata on listOffsets

https://issues.apache.org/jira/browse/KAFKA-15802

Given fix versions: 3.6.1, 3.7.0
JIRA affects (masked from the system): 3.6.0

- `KAFKA-15802@3.6.0`: config 3.6.0, metadata answer **affected** (listed_affected)
- `KAFKA-15802@3.5.2`: config 3.5.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.6.1, 3.7, 2.8, 3.6

### Description

~~~~
We have a tiered storage cluster running with Aiven s3 plugin. 

On our cluster, we have a process doing regular listOffsets requests. 

This triggers the following exception:
{code:java}
org.apache.kafka.common.KafkaException: org.apache.kafka.server.log.remote.storage.RemoteResourceNotFoundException: Requested remote resource was not found
at org.apache.kafka.storage.internals.log.RemoteIndexCache.lambda$createCacheEntry$6(RemoteIndexCache.java:355)
at org.apache.kafka.storage.internals.log.RemoteIndexCache.loadIndexFile(RemoteIndexCache.java:318)
Nov 09, 2023 1:42:01 PM com.github.benmanes.caffeine.cache.LocalAsyncCache lambda$handleCompletion$7
WARNING: Exception thrown during asynchronous load
java.util.concurrent.CompletionException: io.aiven.kafka.tieredstorage.storage.KeyNotFoundException: Key cluster/topic-0A_3phS5QWu9eU28KG0Lxg/24/00000000000000149691-Rdf4cUR_S4OYAGImco6Lbg.rsm-manifest does not exists in storage S3Storage{bucketName='bucket', partSize=16777216}
at com.github.benmanes.caffeine.cache.CacheLoader.lambda$asyncLoad$0(CacheLoader.java:107)
at java.base/java.util.concurrent.CompletableFuture$AsyncSupply.run(CompletableFuture.java:1768)
at java.base/java.util.concurrent.CompletableFuture$AsyncSupply.exec(CompletableFuture.java:1760)
at java.base/java.util.concurrent.ForkJoinTask.doExec(ForkJoinTask.java:373)
at java.base/java.util.concurrent.ForkJoinPool$WorkQueue.topLevelExec(ForkJoinPool.java:1182)
at java.base/java.util.concurrent.ForkJoinPool.scan(ForkJoinPool.java:1655)
at java.base/java.util.concurrent.ForkJoinPool.runWorker(ForkJoinPool.java:1622)
at java.base/java.util.concurrent.ForkJoinWorkerThread.run(ForkJoinWorkerThread.java:165)
Caused by: io.aiven.kafka.tieredstorage.storage.KeyNotFoundException: Key cluster/topic-0A_3phS5QWu9eU28KG0Lxg/24/00000000000000149691-Rdf4cUR_S4OYAGImco6Lbg.rsm-manifest does not exists in storage S3Storage{bucketName='bucket', partSize=16777216}
at io.aiven.kafka.tieredstorage.storage.s3.S3Storage.fetch(S3Storage.java:80)
at io.aiven.kafka.tieredstorage.manifest.SegmentManifestProvider.lambda$new$1(SegmentManifestProvider.java:59)
at com.github.benmanes.caffeine.cache.CacheLoader.lambda$asyncLoad$0(CacheLoader.java:103)
... 7 more
Caused by: software.amazon.awssdk.services.s3.model.NoSuchKeyException: The specified key does not exist. (Service: S3, Status Code: 404, Request ID: CFMP27PVC9V2NNEM, Extended Request ID: F5qqlV06qQJ5qCuWl91oueBaha0QLMBURJudnOnFDQk+YbgFcAg70JBATcARDxN44DGo+PpfZHAsum+ioYMoOw==)
at software.amazon.awssdk.core.internal.http.CombinedResponseHandler.handleErrorResponse(CombinedResponseHandler.java:125)
at software.amazon.awssdk.core.internal.http.CombinedResponseHandler.handleResponse(CombinedResponseHandler.java:82)
at software.amazon.awssdk.core.internal.http.CombinedResponseHandler.handle(CombinedResponseHandler.java:60)
at software.amazon.awssdk.core.internal.http.CombinedResponseHandler.handle(CombinedResponseHandler.java:41)
at software.amazon.awssdk.core.internal.http.pipeline.stages.HandleResponseStage.execute(HandleResponseStage.java:40)
at software.amazon.awssdk.core.internal.http.pipeline.stages.HandleResponseStage.execute(HandleResponseStage.java:30)
at software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage.execute(RequestPipelineBuilder.java:206)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptTimeoutTrackingStage.execute(ApiCallAttemptTimeoutTrackingStage.java:72)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptTimeoutTrackingStage.execute(ApiCallAttemptTimeoutTrackingStage.java:42)
at software.amazon.awssdk.core.internal.http.pipeline.stages.TimeoutExceptionHandlingStage.execute(TimeoutExceptionHandlingStage.java:78)
at software.amazon.awssdk.core.internal.http.pipeline.stages.TimeoutExceptionHandlingStage.execute(TimeoutExceptionHandlingStage.java:40)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptMetricCollectionStage.execute(ApiCallAttemptMetricCollectionStage.java:52)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptMetricCollectionStage.execute(ApiCallAttemptMetricCollectionStage.java:37)
at software.amazon.awssdk.core.internal.http.pipeline.stages.RetryableStage.execute(RetryableStage.java:81)
at software.amazon.awssdk.core.internal.http.pipeline.stages.RetryableStage.execute(RetryableStage.java:36)
at org.apache.kafka.storage.internals.log.RemoteIndexCache.createCacheEntry(RemoteIndexCache.java:351)
at org.apache.kafka.storage.internals.log.RemoteIndexCache.lambda$getIndexEntry$5(RemoteIndexCache.java:341)
at com.github.benmanes.caffeine.cache.BoundedLocalCache.lambda$doComputeIfAbsent$14(BoundedLocalCache.java:2406)
at java.base/java.util.concurrent.ConcurrentHashMap.compute(ConcurrentHashMap.java:1916)
at com.github.benmanes.caffeine.cache.BoundedLocalCache.doComputeIfAbsent(BoundedLocalCache.java:2404)
at com.github.benmanes.caffeine.cache.BoundedLocalCache.computeIfAbsent(BoundedLocalCache.java:2387)
at com.github.benmanes.caffeine.cache.LocalCache.computeIfAbsent(LocalCache.java:108)
at com.github.benmanes.caffeine.cache.LocalManualCache.get(LocalManualCache.java:62)
at org.apache.kafka.storage.internals.log.RemoteIndexCache.getIndexEntry(RemoteIndexCache.java:340)
at org.apache.kafka.storage.internals.log.RemoteIndexCache.lookupTimestamp(RemoteIndexCache.java:421)
at kafka.log.remote.RemoteLogManager.lookupTimestamp(RemoteLogManager.java:447)
at kafka.log.remote.RemoteLogManager.findOffsetByTimestamp(RemoteLogManager.java:522)
at kafka.log.UnifiedLog.$anonfun$fetchOffsetByTimestamp$2(UnifiedLog.scala:1338)
at kafka.log.UnifiedLog.fetchOffsetByTimestamp(UnifiedLog.scala:1845)
at kafka.cluster.Partition.$anonfun$fetchOffsetForTimestamp$4(Partition.scala:1536)
at scala.Option.flatMap(Option.scala:283)
at kafka.cluster.Partition.getOffsetByTimestamp$1(Partition.scala:1536)
at software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage.execute(RequestPipelineBuilder.java:206)
at kafka.cluster.Partition.$anonfun$fetchOffsetForTimestamp$1(Partition.scala:1548)
at software.amazon.awssdk.core.internal.http.StreamManagingStage.execute(StreamManagingStage.java:56)
at kafka.cluster.Partition.fetchOffsetForTimestamp(Partition.scala:1510)
at software.amazon.awssdk.core.internal.http.StreamManagingStage.execute(StreamManagingStage.java:36)
at kafka.server.ReplicaManager.fetchOffsetForTimestamp(ReplicaManager.scala:1253)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage.executeWithTimer(ApiCallTimeoutTrackingStage.java:80)
at kafka.server.KafkaApis.$anonfun$handleListOffsetRequestV1AndAbove$5(KafkaApis.scala:1128)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage.execute(ApiCallTimeoutTrackingStage.java:60)
at scala.collection.StrictOptimizedIterableOps.map(StrictOptimizedIterableOps.scala:100)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage.execute(ApiCallTimeoutTrackingStage.java:42)
at scala.collection.StrictOptimizedIterableOps.map$(StrictOptimizedIterableOps.scala:87)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallMetricCollectionStage.execute(ApiCallMetricCollectionStage.java:50)
at scala.collection.convert.JavaCollectionWrappers$JListWrapper.map(JavaCollectionWrappers.scala:115)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallMetricCollectionStage.execute(ApiCallMetricCollectionStage.java:32)
at kafka.server.KafkaApis.$anonfun$handleListOffsetRequestV1AndAbove$4(KafkaApis.scala:1109)
at software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage.execute(RequestPipelineBuilder.java:206)
at scala.collection.immutable.List.map(List.scala:246)
at software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage.execute(RequestPipelineBuilder.java:206)
at scala.collection.immutable.List.map(List.scala:79)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ExecutionFailureExceptionReportingStage.execute(ExecutionFailureExceptionReportingStage.java:37)
at kafka.server.KafkaApis.handleListOffsetRequestV1AndAbove(KafkaApis.scala:1108)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ExecutionFailureExceptionReportingStage.execute(ExecutionFailureExceptionReportingStage.java:26)
at kafka.server.KafkaApis.handleListOffsetRequest(KafkaApis.scala:1022)
at software.amazon.awssdk.core.internal.http.AmazonSyncHttpClient$RequestExecutionBuilderImpl.execute(AmazonSyncHttpClient.java:196)
at kafka.server.KafkaApis.handle(KafkaApis.scala:182)
at software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler.invoke(BaseSyncClientHandler.java:103)
at kafka.server.KafkaRequestHandler.run(KafkaRequestHandler.scala:149)
at java.base/java.lang.Thread.run(Thread.java:840)
Caused by: org.apache.kafka.server.log.remote.storage.RemoteResourceNotFoundException: Requested remote resource was not found
at software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler.doExecute(BaseSyncClientHandler.java:171)
at io.aiven.kafka.tieredstorage.RemoteStorageManager.fetchIndex(RemoteStorageManager.java:493)
at software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler.lambda$execute$0(BaseSyncClientHandler.java:68)
at org.apache.kafka.server.log.remote.storage.ClassLoaderAwareRemoteStorageManager.lambda$fetchIndex$5(ClassLoaderAwareRemoteStorageManager.java:89)
at software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler.measureApiCallSuccess(BaseSyncClientHandler.java:179)
at org.apache.kafka.server.log.remote.storage.ClassLoaderAwareRemoteStorageManager.withClassLoader(ClassLoaderAwareRemoteStorageManager.java:66)
at software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler.execute(BaseSyncClientHandler.java:62)
at software.amazon.awssdk.core.client.handler.SdkSyncClientHandler.execute(SdkSyncClientHandler.java:52)
at software.amazon.awssdk.awscore.client.handler.AwsSyncClientHandler.execute(AwsSyncClientHandler.java:63)
at org.apache.kafka.server.log.remote.storage.ClassLoaderAwareRemoteStorageManager.fetchIndex(ClassLoaderAwareRemoteStorageManager.java:89)
at org.apache.kafka.storage.internals.log.RemoteIndexCache.lambda$createCacheEntry$6(RemoteIndexCache.java:353)
... 33 more
Caused by: io.aiven.kafka.tieredstorage.storage.KeyNotFoundException: Key cluster/topic-0A_3phS5QWu9eU28KG0Lxg/24/00000000000000149691-Rdf4cUR_S4OYAGImco6Lbg.rsm-manifest does not exists in storage S3Storage{bucketName='bucket', partSize=16777216}
at io.aiven.kafka.tieredstorage.storage.s3.S3Storage.fetch(S3Storage.java:80)
at io.aiven.kafka.tieredstorage.manifest.SegmentManifestProvider.lambda$new$1(SegmentManifestProvider.java:59)
at com.github.benmanes.caffeine.cache.CacheLoader.lambda$asyncLoad$0(CacheLoader.java:103)
at java.base/java.util.concurrent.CompletableFuture$AsyncSupply.run(CompletableFuture.java:1768)
at java.base/java.util.concurrent.CompletableFuture$AsyncSupply.exec(CompletableFuture.java:1760)
at java.base/java.util.concurrent.ForkJoinTask.doExec(ForkJoinTask.java:373)
at java.base/java.util.concurrent.ForkJoinPool$WorkQueue.topLevelExec(ForkJoinPool.java:1182)
at java.base/java.util.concurrent.ForkJoinPool.scan(ForkJoinPool.java:1655)
at java.base/java.util.concurrent.ForkJoinPool.runWorker(ForkJoinPool.java:1622)
at java.base/java.util.concurrent.ForkJoinWorkerThread.run(ForkJoinWorkerThread.java:165)
Caused by: software.amazon.awssdk.services.s3.model.NoSuchKeyException: The specified key does not exist. (Service: S3, Status Code: 404, Request ID: CFMP27PVC9V2NNEM, Extended Request ID: F5qqlV06qQJ5qCuWl91oueBaha0QLMBURJudnOnFDQk+YbgFcAg70JBATcARDxN44DGo+PpfZHAsum+ioYMoOw==)
at software.amazon.awssdk.core.internal.http.CombinedResponseHandler.handleErrorResponse(CombinedResponseHandler.java:125)
at software.amazon.awssdk.services.s3.DefaultS3Client.getObject(DefaultS3Client.java:4483)
at software.amazon.awssdk.services.s3.S3Client.getObject(S3Client.java:7916)
at io.aiven.kafka.tieredstorage.storage.s3.S3Storage.fetch(S3Storage.java:77)
... 9 moreat software.amazon.awssdk.core.internal.http.CombinedResponseHandler.handleResponse(CombinedResponseHandler.java:82)
at software.amazon.awssdk.core.internal.http.CombinedResponseHandler.handle(CombinedResponseHandler.java:60)
at software.amazon.awssdk.core.internal.http.CombinedResponseHandler.handle(CombinedResponseHandler.java:41)
at software.amazon.awssdk.core.internal.http.pipeline.stages.HandleResponseStage.execute(HandleResponseStage.java:40)
at software.amazon.awssdk.core.internal.http.pipeline.stages.HandleResponseStage.execute(HandleResponseStage.java:30)
at software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage.execute(RequestPipelineBuilder.java:206)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptTimeoutTrackingStage.execute(ApiCallAttemptTimeoutTrackingStage.java:72)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptTimeoutTrackingStage.execute(ApiCallAttemptTimeoutTrackingStage.java:42)
at software.amazon.awssdk.core.internal.http.pipeline.stages.TimeoutExceptionHandlingStage.execute(TimeoutExceptionHandlingStage.java:78)
at software.amazon.awssdk.core.internal.http.pipeline.stages.TimeoutExceptionHandlingStage.execute(TimeoutExceptionHandlingStage.java:40)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptMetricCollectionStage.execute(ApiCallAttemptMetricCollectionStage.java:52)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallAttemptMetricCollectionStage.execute(ApiCallAttemptMetricCollectionStage.java:37)
at software.amazon.awssdk.core.internal.http.pipeline.stages.RetryableStage.execute(RetryableStage.java:81)
at software.amazon.awssdk.core.internal.http.pipeline.stages.RetryableStage.execute(RetryableStage.java:36)
at software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage.execute(RequestPipelineBuilder.java:206)
at software.amazon.awssdk.core.internal.http.StreamManagingStage.execute(StreamManagingStage.java:56)
at software.amazon.awssdk.core.internal.http.StreamManagingStage.execute(StreamManagingStage.java:36)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage.executeWithTimer(ApiCallTimeoutTrackingStage.java:80)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage.execute(ApiCallTimeoutTrackingStage.java:60)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallTimeoutTrackingStage.execute(ApiCallTimeoutTrackingStage.java:42)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallMetricCollectionStage.execute(ApiCallMetricCollectionStage.java:50)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ApiCallMetricCollectionStage.execute(ApiCallMetricCollectionStage.java:32)
at software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage.execute(RequestPipelineBuilder.java:206)
at software.amazon.awssdk.core.internal.http.pipeline.RequestPipelineBuilder$ComposingRequestPipelineStage.execute(RequestPipelineBuilder.java:206)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ExecutionFailureExceptionReportingStage.execute(ExecutionFailureExceptionReportingStage.java:37)
at software.amazon.awssdk.core.internal.http.pipeline.stages.ExecutionFailureExceptionReportingStage.execute(ExecutionFailureExceptionReportingStage.java:26)
at software.amazon.awssdk.core.internal.http.AmazonSyncHttpClient$RequestExecutionBuilderImpl.execute(AmazonSyncHttpClient.java:196)
at software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler.invoke(BaseSyncClientHandler.java:103)
at software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler.doExecute(BaseSyncClientHandler.java:171)
at software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler.lambda$execute$0(BaseSyncClientHandler.java:68)
at software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler.measureApiCallSuccess(BaseSyncClientHandler.java:179)
at software.amazon.awssdk.core.internal.handler.BaseSyncClientHandler.execute(BaseSyncClientHandler.java:62)
at software.amazon.awssdk.core.client.handler.SdkSyncClientHandler.execute(SdkSyncClientHandler.java:52)
at software.amazon.awssdk.awscore.client.handler.AwsSyncClientHandler.execute(AwsSyncClientHandler.java:63)
at software.amazon.awssdk.services.s3.DefaultS3Client.getObject(DefaultS3Client.java:4483)
at software.amazon.awssdk.services.s3.S3Client.getObject(S3Client.java:7916)
at io.aiven.kafka.tieredstorage.storage.s3.S3Storage.fetch(S3Storage.java:77)
... 9 more{code}
 

When looking at the remote storage (here, s3) for this file, I can see the file but it has been created a few seconds after the log line above.

When setting the logging to trace in the plugin, I can clearly see that we are trying to access a segment in the COPY_SEGMENT_STARTED state, which is presumably the reason why it doesn't exist yet on S3.
{code:java}
Fetching index OFFSET for RemoteLogSegmentMetadata{remoteLogSegmentId=RemoteLogSegmentId{topicIdPartition=0A_3phS5QWu9eU28KG0Lxg:topic-24, id=Rdf4cUR_S4OYAGImco6Lbg}, startOffset=149691, endOffset=159829, brokerId=10005, maxTimestampMs=1699537315336, eventTimestampMs=1699537319870, segmentLeaderEpochs={4=149691}, segmentSizeInBytes=536566004, customMetadata=Optional.empty, state=COPY_SEGMENT_STARTED} {code}
I believe there are 2 issues, possibly related: 
1. We should not try to access elements in COPY_SEGMENT_STARTED state
2. it should rather be retrieved from the local disk as I believe it's still on local disk at this stage.
~~~~

### Comments (7)

1.

~~~~
In your stack trace, we are accessing RLM.findOffsetByTimestamp(fetchOffset) -> RLM.lookupTimestamp(rlsMetadata) where rlsMetadata contains pointer to a segment which hasn't been uploaded yet. The rlsMetadata is obtained by RLMM.listRemoteLogSegments(). It seems like the RLMM plugin is not filtering out segments which are still in COPY_STARTED lifecycle stage. In this place we are only interested in copy_finished segments. 

We have two options, 1\ add the filtering in RLM.findOffsetByTimestamp() 2\ modify the RLMM.listRemoteLogSegments() to accept a filter for states which should be returned.I think we should do the latter so that RLMM can optimize conditional search but this API change will require a KIP.

We can also choose to try finding the first segment larger than given timestamp in local first at [https://github.com/apache/kafka/blob/81cceedf7e7985160397459ca0f7a6fbbfd3b019/core/src/main/scala/kafka/log/UnifiedLog.scala#L1327-L1341] but that will be incorrect because the first segment greater than targetTimestamp may actually reside in remote (instead of the first segment in local).

Meanwhile, [~f.visconte] would you please write a test case that fails for this situation?

 

cc: [~satishd] [~lukec] 
~~~~

2.

~~~~
Hi [~divijvaidya] , see [https://github.com/apache/kafka/pull/14727] for a test case and a quick implementation of the option 1.

We may consider option 1 fix for 3.6.1 and work on a KIP to extend RLMM API for 3.7, what do you think?
~~~~

3.

~~~~
[~jeqo] [~divijvaidya] +1 to go with filtering the targeted segments that indicate the segment is available for now. This is the existing  approach in 2.8.x internal tiered storage implementation branches.  
We can discuss later whether a general filtering API is required for some of the methods or a very specific API is needed. 

~~~~

4.

~~~~
+1 to go with option 1 first. 
~~~~

5.

~~~~
Hey folks - I am on vacation and might not look at this actively. Going with approach 1 sounds good to me. I have left a comment in the PR for another place where this bug will manifest.

[~showuon] if/when you merge this, can you please consider this for backporting to 3.6? I have added the backport-candidate tag as a reminder. Please don't wait for my approval on this PR since I may not be available to review in next few weeks.
~~~~

6.

~~~~
[~satish.duggana] You merged both PRs, can we now resolve this item?
~~~~

7.

~~~~
[~mimaison] Sorry for updating the JIRA. This can be resolved as fixed, I closed it now.
~~~~

---

## KAFKA-16009: Fix PlaintextConsumerTest.testMaxPollIntervalMsDelayInRevocation

https://issues.apache.org/jira/browse/KAFKA-16009

Given fix versions: 3.8.0
JIRA affects (masked from the system): 3.7.0

- `KAFKA-16009@3.7.0`: config 3.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-16009@3.6.2`: config 3.6.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
The integration test {{PlaintextConsumerTest.testMaxPollIntervalMsDelayInRevocation}} is failing when using the {{AsyncKafkaConsumer}}.

The error is:

{code}
org.opentest4j.AssertionFailedError: Timed out before expected rebalance completed
	at org.junit.jupiter.api.AssertionUtils.fail(AssertionUtils.java:38)
	at org.junit.jupiter.api.Assertions.fail(Assertions.java:134)
	at kafka.api.AbstractConsumerTest.awaitRebalance(AbstractConsumerTest.scala:317)
	at kafka.api.PlaintextConsumerTest.testMaxPollIntervalMsDelayInRevocation(PlaintextConsumerTest.scala:235)
{code}

The logs include this line:
 
{code}
[2023-12-13 15:20:27,824] WARN [Consumer clientId=ConsumerTestConsumer, groupId=my-test] consumer poll timeout has expired. This means the time between subsequent calls to poll() was longer than the configured max.poll.interval.ms, which typically implies that the poll loop is spending too much time processing messages. You can address this either by increasing max.poll.interval.ms or by reducing the maximum size of batches returned in poll() with max.poll.records. (org.apache.kafka.clients.consumer.internals.HeartbeatRequestManager:188)
{code} 

I don't know if that's related or not.

 

 
~~~~

---

## KAFKA-16221: IllegalStateException from Producer

https://issues.apache.org/jira/browse/KAFKA-16221

Given fix versions: 3.7.0
JIRA affects (masked from the system): 3.6.0

- `KAFKA-16221@3.6.0`: config 3.6.0, metadata answer **affected** (listed_affected)
- `KAFKA-16221@3.5.2`: config 3.5.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.7, 3.7.0

### Description

~~~~
https://issues.apache.org/jira/browse/KAFKA-14831 fixed a producer bug about internal TX state transition and the producer is now throwing an IllegalStateException in situations it did swallow an internal error before.

This change surfaces a bug in Kafka Streams: Kafka Streams calls `abortTransaction()` blindly when a task is closed dirty, even if the Producer is already in an internal fatal state. However, if the Producer is in a fatal state, Kafka Streams should skip `abortTransaction` and only `close()` the Producer when closing a task dirty.

The bug is surfaced after `commitTransaction()` did timeout or after an `InvalidProducerEpochException` from a `send()` call, leading to the call to `abortTransaction()` – Kafka Streams does not track right now if a commit-TX is in progress.
{code:java}
java.lang.IllegalStateException: Cannot attempt operation `abortTransaction` because the previous call to `commitTransaction` timed out and must be retried
    at org.apache.kafka.clients.producer.internals.TransactionManager.handleCachedTransactionRequestResult(TransactionManager.java:1203)
    at org.apache.kafka.clients.producer.internals.TransactionManager.beginAbort(TransactionManager.java:326)
    at org.apache.kafka.clients.producer.internals.Sender.run(Sender.java:274) {code}
and
{code:java}
[2024-01-16 04:19:32,584] ERROR [kafka-producer-network-thread | i-01aea6907970b1bf6-StreamThread-1-producer] stream-thread [i-01aea6907970b1bf6-StreamThread-1] stream-task [1_2] Error encountered sending r       ecord to topic joined-counts for task 1_2 due to:
org.apache.kafka.common.errors.InvalidProducerEpochException: Producer attempted to produce with an old epoch.
Written offsets would not be recorded and no more records would be sent since the producer is fenced, indicating the task may be migrated out (org.apache.kafka.streams.processor.internals.RecordCollectorImp       l)
org.apache.kafka.common.errors.InvalidProducerEpochException: Producer attempted to produce with an old epoch.

// followed by

[2024-01-16 04:19:32,587] ERROR [kafka-producer-network-thread | i-01aea6907970b1bf6-StreamThread-1-producer] [Producer clientId=i-01aea6907970b1bf6-StreamThread-1-producer, transactionalId=stream-soak-test       -bbb995dc-1ba2-41ed-8791-0512ab4b904d-1] Aborting producer batches due to fatal error (org.apache.kafka.clients.producer.internals.Sender)
java.lang.IllegalStateException: TransactionalId stream-soak-test-bbb995dc-1ba2-41ed-8791-0512ab4b904d-1: Invalid transition attempted from state FATAL_ERROR to state ABORTABLE_ERROR
        at org.apache.kafka.clients.producer.internals.TransactionManager.transitionTo(TransactionManager.java:996)
        at org.apache.kafka.clients.producer.internals.TransactionManager.transitionToAbortableError(TransactionManager.java:451)
        at org.apache.kafka.clients.producer.internals.TransactionManager.maybeTransitionToErrorState(TransactionManager.java:664)
        at org.apache.kafka.clients.producer.internals.TransactionManager.handleFailedBatch(TransactionManager.java:669)
        at org.apache.kafka.clients.producer.internals.Sender.failBatch(Sender.java:835)
        at org.apache.kafka.clients.producer.internals.Sender.failBatch(Sender.java:819)
        at org.apache.kafka.clients.producer.internals.Sender.failBatch(Sender.java:771)
        at org.apache.kafka.clients.producer.internals.Sender.completeBatch(Sender.java:702)
        at org.apache.kafka.clients.producer.internals.Sender.lambda$null$1(Sender.java:627)
        at java.util.ArrayList.forEach(ArrayList.java:1259)
        at org.apache.kafka.clients.producer.internals.Sender.lambda$handleProduceResponse$2(Sender.java:612)
        at java.lang.Iterable.forEach(Iterable.java:75)
        at org.apache.kafka.clients.producer.internals.Sender.handleProduceResponse(Sender.java:612)
        at org.apache.kafka.clients.producer.internals.Sender.lambda$sendProduceRequest$8(Sender.java:917)
        at org.apache.kafka.clients.ClientResponse.onComplete(ClientResponse.java:154)
        at org.apache.kafka.clients.NetworkClient.completeResponses(NetworkClient.java:608)
        at org.apache.kafka.clients.NetworkClient.poll(NetworkClient.java:600)
        at org.apache.kafka.clients.producer.internals.Sender.maybeSendAndPollTransactionalRequest(Sender.java:460)
        at org.apache.kafka.clients.producer.internals.Sender.runOnce(Sender.java:337)
        at org.apache.kafka.clients.producer.internals.Sender.run(Sender.java:252)
        at java.lang.Thread.run(Thread.java:750) {code}
If the Producer throws an IllegalStateException on `abortTransaction()` Kafka Streams treats this exception ("correctly") as fatal, and StreamsThread dies. However, Kafka Streams is actually in a state in which it can recover from, and thus should not let StreamThread die by carry forward (by not calling `abortTransaction()` and moving forward with the dirty close of the task).

 

It is unclear right now, how https://issues.apache.org/jira/browse/KAFKA-14567 is related – it has a similar stack trace, but it was reported before https://issues.apache.org/jira/browse/KAFKA-14831 was merged.
~~~~

### Comments (4)

1.

~~~~
Marking this as resolved to 3.7 for now – we might want to re-open this ticket after 3.7.0 was release for a proper fix.
~~~~

2.

~~~~
Im still facing this issue in version 3.7. Do you guys have any update on this issue?

org.apache.kafka.streams.processor.internals.StreamThread.runLoop(StreamThread.java:686)\n\tat org.apache.kafka.streams.processor.internals.StreamThread.run(StreamThread.java:645)\nCaused by: java.lang.IllegalStateException: Cannot attempt operation `send` because the previous call to `commitTransaction` timed out and must be retried\n\tat 
~~~~

3.

~~~~
I'm working in this area of invalid transaction states. [~mjsax]—can I reopen and assign to myself?
~~~~

4.

~~~~
If it's helpful to re-open, sure.

Given that we have multiple ticket which seem to be related, we need to pick one in the end for the target PR, so not sure if re-opening this one is the right move or not?
~~~~

---

## KAFKA-16407: ForeignKey INNER join ignores FK change when its previous value is null

https://issues.apache.org/jira/browse/KAFKA-16407

Given fix versions: 3.9.1, 4.0.1, 4.1.0
JIRA affects (masked from the system): 2.8.2, 3.0.2, 3.1.2, 3.2.3, 3.3.2, 3.4.1, 3.5.2, 3.6.1, 3.7.0

- `KAFKA-16407@3.2.3`: config 3.2.3, metadata answer **affected** (listed_affected)
- `KAFKA-16407@2.8.1`: config 2.8.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.8

### Description

~~~~
We have two topics : _left-topic[String, LeftRecord]_ and _right-topic[String, String]_

where _LeftRecord_ :
{code:scala}
 case class LeftRecord(foreignKey: String, name: String){code}
we do a simple *INNER* foreign key join on left-topic's foreignKey field. The resulting join value is the value in right-topic.

 

*Scenario: Primary key pk1 gets mapped to a new FK after having a null FK*
{code:scala}
rightTopic.pipeInput("fk", "1")

leftTopic.pipeInput("pk1", LeftRecord(null, "pk1"))
leftTopic.pipeInput("pk1", LeftRecord("fk", "pk1")) {code}
 

*+Expected result+*
{code:scala}
KeyValue(pk1, 1){code}
 

*+Actual result+*
{code:scala}
# No output !

# Logs:

20:14:29,723 WARN  org.apache.kafka.streams.kstream.internals.foreignkeyjoin.ForeignJoinSubscriptionSendProcessorSupplier  - Skipping record due to null foreign key. value=[LeftRecord(null,pk1)] topic=[left-topic] partition=[0] offset=[0]

20:14:29,728 WARN  org.apache.kafka.streams.kstream.internals.foreignkeyjoin.ForeignJoinSubscriptionSendProcessorSupplier  - Skipping record due to null foreign key. value=[LeftRecord(null,pk1)] topic=[left-topic] partition=[0] offset=[1]
{code}
 

After looking into the code, I believe this is the line behind the issue : https://github.com/apache/kafka/blob/trunk/streams/src/main/java/org/apache/kafka/streams/kstream/internals/foreignkeyjoin/SubscriptionSendProcessorSupplier.java#L147
~~~~

### Comments (2)

1.

~~~~
Did [https://cwiki.apache.org/confluence/display/KAFKA/KIP-962%3A+Relax+non-null+key+requirement+in+Kafka+Streams] not fix this?
~~~~

2.

~~~~
Actually this behavior is not concerned by this KIP, it's a condition that existed since 2.8 which wrongly assumes if old foreign key is null then we should skip the current record. From what I saw, the implementation of the KIP didn't change that code.
~~~~

---

## KAFKA-16465: New consumer does not invoke rebalance callbacks as expected in consumer_test.py system test

https://issues.apache.org/jira/browse/KAFKA-16465

Given fix versions: 3.8.0
JIRA affects (masked from the system): 3.7.0

- `KAFKA-16465@3.7.0`: config 3.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-16465@3.6.2`: config 3.6.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
The {{consumer_test.py}} system test fails with the following error:

{noformat}
test_id:    kafkatest.tests.client.consumer_test.OffsetValidationTest.test_static_consumer_bounce.clean_shutdown=True.static_membership=False.bounce_mode=all.num_bounces=5.metadata_quorum=ISOLATED_KRAFT.use_new_coordinator=True.group_protocol=consumer
status:     FAIL
run time:   1 minute 29.511 seconds


    AssertionError('Total revoked count 0 does not match the expectation of having 0 revokes as 0')
Traceback (most recent call last):
  File "/home/jenkins/workspace/system-test-kafka-branch-builder/kafka/venv/lib/python3.7/site-packages/ducktape/tests/runner_client.py", line 184, in _do_run
    data = self.run_test()
  File "/home/jenkins/workspace/system-test-kafka-branch-builder/kafka/venv/lib/python3.7/site-packages/ducktape/tests/runner_client.py", line 262, in run_test
    return self.test_context.function(self.test)
  File "/home/jenkins/workspace/system-test-kafka-branch-builder/kafka/venv/lib/python3.7/site-packages/ducktape/mark/_mark.py", line 433, in wrapper
    return functools.partial(f, *args, **kwargs)(*w_args, **w_kwargs)
  File "/home/jenkins/workspace/system-test-kafka-branch-builder/kafka/tests/kafkatest/tests/client/consumer_test.py", line 254, in test_static_consumer_bounce
    (num_revokes_after_bounce, check_condition)
AssertionError: Total revoked count 0 does not match the expectation of having 0 revokes as 0
{noformat}
~~~~

---

## KAFKA-16563: migration to KRaft hanging after MigrationClientException

https://issues.apache.org/jira/browse/KAFKA-16563

Given fix versions: 3.7.1, 3.8.0
JIRA affects (masked from the system): 3.7.0

- `KAFKA-16563@3.7.0`: config 3.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-16563@3.6.2`: config 3.6.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
When running ZK migrating to KRaft process, we encountered an issue that the migrating is hanging and the `ZkMigrationState` cannot move to `MIGRATION` state. After investigation, the root cause is because the pollEvent didn't retry with the retriable `MigrationClientException` (i.e. ZK client retriable errors) while it should. And because of this, the poll event will not poll anymore, which causes the KRaftMigrationDriver cannot work as expected.

 
{code:java}
2024-04-11 21:27:55,393 INFO [KRaftMigrationDriver id=5] Encountered ZooKeeper error during event PollEvent. Will retry. (org.apache.kafka.metadata.migration.KRaftMigrationDriver) [controller-5-migration-driver-event-handler]org.apache.zookeeper.KeeperException$NodeExistsException: KeeperErrorCode = NodeExists for /migration    at org.apache.zookeeper.KeeperException.create(KeeperException.java:126)    at org.apache.zookeeper.KeeperException.create(KeeperException.java:54)    at kafka.zookeeper.AsyncResponse.maybeThrow(ZooKeeperClient.scala:570)    at kafka.zk.KafkaZkClient.createInitialMigrationState(KafkaZkClient.scala:1701)    at kafka.zk.KafkaZkClient.getOrCreateMigrationState(KafkaZkClient.scala:1689)    at kafka.zk.ZkMigrationClient.$anonfun$getOrCreateMigrationRecoveryState$1(ZkMigrationClient.scala:109)    at kafka.zk.ZkMigrationClient.getOrCreateMigrationRecoveryState(ZkMigrationClient.scala:69)    at org.apache.kafka.metadata.migration.KRaftMigrationDriver.applyMigrationOperation(KRaftMigrationDriver.java:248)    at org.apache.kafka.metadata.migration.KRaftMigrationDriver.recoverMigrationStateFromZK(KRaftMigrationDriver.java:169)    at org.apache.kafka.metadata.migration.KRaftMigrationDriver.access$1900(KRaftMigrationDriver.java:62)    at org.apache.kafka.metadata.migration.KRaftMigrationDriver$PollEvent.run(KRaftMigrationDriver.java:794)    at org.apache.kafka.queue.KafkaEventQueue$EventContext.run(KafkaEventQueue.java:127)    at org.apache.kafka.queue.KafkaEventQueue$EventHandler.handleEvents(KafkaEventQueue.java:210)    at org.apache.kafka.queue.KafkaEventQueue$EventHandler.run(KafkaEventQueue.java:181)    at java.base/java.lang.Thread.run(Thread.java:840){code}
~~~~

### Comments (1)

1.

~~~~
[~davidarthur] [~akhileshchg] , could you take a look at this issue. Thanks.
~~~~

---

## KAFKA-16576: New consumer fails with assert in consumer_test.py’s test_consumer_failure system test

https://issues.apache.org/jira/browse/KAFKA-16576

Given fix versions: 4.0.0
JIRA affects (masked from the system): 3.7.0

- `KAFKA-16576@3.7.0`: config 3.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-16576@3.6.2`: config 3.6.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
The {{consumer_test.py}} system test intermittently fails with the following error:

{code}
test_id:    kafkatest.tests.client.consumer_test.OffsetValidationTest.test_consumer_failure.clean_shutdown=True.enable_autocommit=True.metadata_quorum=ISOLATED_KRAFT.use_new_coordinator=True.group_protocol=consumer
status:     FAIL
run time:   42.582 seconds


    AssertionError()
Traceback (most recent call last):
  File "/home/jenkins/workspace/system-test-kafka-branch-builder/kafka/venv/lib/python3.7/site-packages/ducktape/tests/runner_client.py", line 184, in _do_run
    data = self.run_test()
  File "/home/jenkins/workspace/system-test-kafka-branch-builder/kafka/venv/lib/python3.7/site-packages/ducktape/tests/runner_client.py", line 262, in run_test
    return self.test_context.function(self.test)
  File "/home/jenkins/workspace/system-test-kafka-branch-builder/kafka/venv/lib/python3.7/site-packages/ducktape/mark/_mark.py", line 433, in wrapper
    return functools.partial(f, *args, **kwargs)(*w_args, **w_kwargs)
  File "/home/jenkins/workspace/system-test-kafka-branch-builder/kafka/tests/kafkatest/tests/client/consumer_test.py", line 399, in test_consumer_failure
    assert partition_owner is not None
AssertionError
Notify
{code}

Affected tests:
 * {{test_consumer_failure}}
~~~~

### Comments (1)

1.

~~~~
Fixed by https://github.com/apache/kafka/pull/16845.
~~~~

---

## KAFKA-17064: New consumer assign should update assignment in background thread

https://issues.apache.org/jira/browse/KAFKA-17064

Given fix versions: 4.0.0
JIRA affects (masked from the system): 3.8.0

- `KAFKA-17064@3.8.0`: config 3.8.0, metadata answer **affected** (listed_affected)
- `KAFKA-17064@3.7.2`: config 3.7.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 4.0

### Description

~~~~
With the new async consumer, the subscriptionState object is shared between the app thread and the background thread, but in principle all updates to the assignment should happen in the background thread, to avoid race conditions. Note that it's in the background where most updates to the assignment happen, as result of app event processing like unsubscribe, reconciliations, etc.). 

We've faced such races in places like unsubscribe and close, fixed by ensuring that all assignment updates happen in the background, and this also needs to be reviewed for the consumer.assign. The current implementation triggers an AssignmentChange event that is processed in the background, but that event is not really changing the assignment. It only commits offsets, and the assignment is updated in the app thread by calling subscriptionState.assignFromUser 

We should consider moving the assignment update to the background thread, as part of the AssignmentChangeEvent.  
~~~~

### Comments (5)

1.

~~~~
Hi [~lianetm], in KAFKA-17017, we call `subscriptions#unsubscribe` if `groupMetadata` is not present in `AsyncKafkaConsumer`. Do you think we should also use event to trigger background thread to handle it? Thank you. cc [~chia7712].
~~~~

2.

~~~~
Hey [~yangpoan] , definitely, based on events that in the end will execute in the background thread. I see 2 cases:

1. If the assign has empty partitions I would say we're covered: it relies on a call to unsubscribe, and that performs all assignment updates in the background already. We just need KAFKA-17017 to get it all right when the member is not in a group, sure thing. 
2. if the assign has non-empty partitions, it will end up updating the assignment in the app thread, and we should fix that (this issue). We should rely on a event indeed and we already have it actually, it's the 
AssignmentChangeEvent. The issue is that this event currently does only part of the job (it only triggers a commit https://github.com/apache/kafka/blob/c97d4ce026fdb75f80760bcce00b239db951a481/clients/src/main/java/org/apache/kafka/clients/consumer/internals/events/ApplicationEventProcessor.java#L181). Misleading name indeed. 
We should consider having that event handle the full assignment change (commit and update the subscription state with assignFromUser), all in the background.  
~~~~

3.

~~~~
Hi [~lianetm], thanks for your explanation. If you're not working on this, may I assign the issue to myself? I can handle it after [https://github.com/apache/kafka/pull/16449] is merged. Thank you.
~~~~

4.

~~~~
Sure, you can take it, thanks for helping out! Let me know if you have any other questions, and ping me when there is a PR, happy to help with the review. 
~~~~

5.

~~~~
Changing target fix version to 4.0 since this is not a blocker and we are past code freeze.
~~~~

---

## KAFKA-17154: New consumer subscribe may join group without a call to consumer.poll

https://issues.apache.org/jira/browse/KAFKA-17154

Given fix versions: 4.0.0
JIRA affects (masked from the system): 3.8.0

- `KAFKA-17154@3.8.0`: config 3.8.0, metadata answer **affected** (listed_affected)
- `KAFKA-17154@3.7.2`: config 3.7.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 4.0

### Description

~~~~
With the new consumer, a call to consumer.subscribe will update the client subscription state via a SubscriptionChangedEvent. This will be picked up by the background thread, and will send a Heartbeat RPC on the next poll of the background thread (without requiring a consumer.poll). This is a change in behaviour with the legacy consumer, that breaks the consumer#subscribe contract for "rebalances will only occur during an active call to \{@link #poll(Duration)}", so it should be fixed.  

In the legacy its a similar principle but different behaviour: subscribe changes the subscription state, and the coordinator picks it up to send the JoinRequest on the next poll of the coordinator (but this happens only as part of a consumer.poll)

We should make the new consumer join (send HB to join) only on consumer.poll after a call to subscribed. We could consider having the SubscriptionChangedEvent only signal to the background that the subscription changed without doing the transition to JOINING that triggers the HB (membershipMgr#onSubscriptionUpdated could simply flip a flag, no transition), and then do the actual transition to JOINING when processing a PollEvent if the flag is on (flipping it back). (Just first simple approach that comes to mind, we should think about it a bit more and consider other interactions that could happen in between, like unsubscribe, close, etc).

We should add test coverage to ensure the common behaviour with the legacy.
~~~~

### Comments (4)

1.

~~~~
Hi [~lianetm], I'm interested in this jira. If you're not working on it, may I assign to myself? Thank you.
~~~~

2.

~~~~
Sure, assigned to you [~yangpoan], thanks a lot! The description has the first approach that comes to mind but we should review the details in case I'm missing some interaction. Let me know if you have any questions. 
~~~~

3.

~~~~
Hey [~yangpoan] , just bumping this one up to make sure we have it in our radar. Are you still planning to work on it before 4.0? Let me know if you need any help. Thanks a lot! 
~~~~

4.

~~~~
Yes, I'll work on it this week. Thank you.
~~~~

---

## KAFKA-17182: Consumer fetch sessions are evicted too quickly with AsyncKafkaConsumer

https://issues.apache.org/jira/browse/KAFKA-17182

Given fix versions: 4.0.0, 4.1.0
JIRA affects (masked from the system): 3.8.0

- `KAFKA-17182@3.8.0`: config 3.8.0, metadata answer **affected** (listed_affected)
- `KAFKA-17182@3.7.2`: config 3.7.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 4.0.0, 4.0

### Description

~~~~
h1. Background

{{Consumer}} implementations fetch data from the cluster and temporarily buffer it in memory until the user next calls {{{}Consumer.poll(){}}}. When a fetch request is being generated, partitions that already have buffered data are not included in the fetch request.

The {{ClassicKafkaConsumer}} performs much of its fetch logic and network I/O in the application thread. On {{{}poll(){}}}, if there is any locally-buffered data, the {{ClassicKafkaConsumer}} does not fetch _any_ new data and simply returns the buffered data to the user from {{{}poll(){}}}.

On the other hand, the {{AsyncKafkaConsumer}} consumer splits its logic and network I/O between two threads, which results in a potential race condition during fetch. The {{AsyncKafkaConsumer}} also checks for buffered data on its application thread. If it finds there is none, it signals the background thread to create a fetch request. However, it's possible for the background thread to receive data from a previous fetch and buffer it before the fetch request logic starts. When that occurs, as the background thread creates a new fetch request, it skips any buffered data, which has the unintended result that those partitions get added to the fetch request's "to remove" set. This signals to the broker to remove those partitions from its internal cache.

This issue is technically possible in the {{ClassicKafkaConsumer}} too, since the heartbeat thread performs network I/O in addition to the application thread. However, because of the frequency at which the {{{}AsyncKafkaConsumer{}}}'s background thread runs, it is ~100x more likely to happen.
h1. Options

The core decision is: what should the background thread do if it is asked to create a fetch request and it discovers there's buffered data. There were multiple proposals to address this issue in the {{{}AsyncKafkaConsumer{}}}. Among them are:
 # The background thread should omit buffered partitions from the fetch request as before (this is the existing behavior)
 # The background thread should skip the fetch request generation entirely if there are _any_ buffered partitions
 # The background thread should include buffered partitions in the fetch request, but use a small “max bytes” value
 # The background thread should skip fetching from the nodes that have buffered partitions

Option 3 won out. The change in {{AsyncKafkaConsumer}} is to include in the fetch request any partition with buffered data. By using a "max bytes" size of 1, this should cause the fetch response to return as little data as possible. In that way, the consumer doesn't buffer too much data on the client before it can be returned from {{{}poll(){}}}.
h1. Testing
h2. Eviction rate testing

Here are the results of our internal stress testing:
 * {{{}ClassicKafkaConsumer{}}}—after the initial spike during test start up, the average rate settles down to ~0.14 evictions/second  !1.png|width=833,height=300!
 * {{{}AsyncKafkaConsumer{}}}, (w/o fix)—after startup, the evictions still settle down, but they are ~100x higher than the {{ClassicKafkaConsumer}} at ~1.48 evictions/second   !2.png|width=830,height=300!
 * {{AsyncKafkaConsumer}} (w/ fix)—the eviction rate is now closer to the {{ClassicKafkaConsumer}} at ~0.22 evictions/second  !3.png|width=833,height=300!

h2. {{EndToEndLatency}} testing

The bundled {{EndToEndLatency}} test runner was executed on a single machine using Docker. The {{apache/kafka:latest}} Docker image was used and either the {{cluster/combined/plaintext/docker-compose.yml}} or {{single-node/plaintext/docker-compose.yml}} Docker Compose configuration files, depending on the test. The Docker containers were recreated from scratch before each test.

A single topic was created with 30 partitions and with a replication factor of either 1 or 3, depending on a single- or multi-node setup.

For each of the test runs these argument values were used:
 * Message count: 100000
 * {{{}acks{}}}: 1
 * Message size: 128 bytes

A configuration file which contained a single configuration value of {{group.protocol=<$group_protocol>}} was also provided to the test, where {{$group_protocol}} was either {{CLASSIC}} or {{{}CONSUMER{}}}.
h3. Test results
h4. Test 1—{{{}CLASSIC{}}} group protocol, cluster size: 3 nodes, replication factor: 3
||Metric||{{trunk}}||PR||
|Average latency|1.4901|1.4871|
|50th percentile|1|1|
|99th percentile|3|3|
|99.9th percentile|6|6|
h4. Test 2—{{{}CONSUMER{}}} group protocol, cluster size: 3 nodes, replication factor: 3
||Metric||{{trunk}}||PR||
|Average latency|1.4704|1.4807|
|50th percentile|1|1|
|99th percentile|3|3|
|99.9th percentile|6|7|
h4. Test 3—{{{}CLASSIC{}}} group protocol, cluster size: 1 node, replication factor: 1
||Metric||{{trunk}}||PR||
|Average latency|1.0777|1.0193|
|50th percentile|1|1|
|99th percentile|2|2|
|99.9th percentile|5|4|
h4. Test 4—{{{}CONSUMER{}}} group protocol, cluster size: 1 node, replication factor: 1
||Metric||{{trunk}}||PR||
|Average latency|1.0937|1.0503|
|50th percentile|1|1|
|99th percentile|2|2|
|99.9th percentile|4|4|
h3. Conclusion

These tests did not reveal any significant differences between the current fetcher logic on {{trunk}} and the one proposed in this PR. Addition test runs using larger message counts and/or larger message sizes did not affect the result.
~~~~

### Comments (6)

1.

~~~~
PR has been merged into trunk, and working to back-port it to 4.0.0.
~~~~

2.

~~~~
Cherry-picked to 4.0 [https://github.com/apache/kafka/commit/9c02072c4fd8159087b7960872d6ee8271a308ab] 
~~~~

3.

~~~~
Reopening to investigated reported issues. Reverted in trunk and 4.0 in the meantime
~~~~

4.

~~~~
Thanks!

For details about the introduced regression, cf https://issues.apache.org/jira/browse/KAFKA-18686 
~~~~

5.

~~~~
Merged to trunk with the updated PR after the regression, and cherry-picked to 4.0 [https://github.com/apache/kafka/commit/b60d05ca1bccc69937fdd5336cf45aa55f706395] 
~~~~

6.

~~~~
[~kirktrue] [~lianetm]  I see we added wakeup call in handleFetchSuccess but not in handleFetchFailure. Will it not stalled when failure happening during the fetch ?
~~~~

---

## KAFKA-17584: Fix incorrect synonym handling for dynamic log configurations

https://issues.apache.org/jira/browse/KAFKA-17584

Given fix versions: 3.7.2, 3.8.1, 3.9.0
JIRA affects (masked from the system): 3.0.0

- `KAFKA-17584@3.0.0`: config 3.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-17584@2.8.2`: config 2.8.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.9.0, 3.8.1, 3.8.0, 3.7.2, 3.0, 3.7, 3.8

### Description

~~~~
Updating certain dynamic configurations (for example `message.max.bytes`) causes retention based on time to reset to the default value (source code) for log.retention.ms. This poses a durability issue if users have set their retention by using log.retention.hours or log.retention.minutes. In other words, if a user has set log.retention.hours=-1 (infinite retention) and they dynamically change `message.max.bytes` their retention will immediately change back to the default of 604800000 ms (7 days) and data before this will be scheduled for deletion immediately.

Steps to reproduce:

 1. Add log.retention.minutes=1,log.retention.check.interval.ms=1000 to server.properties
 2. Start a single ZK or KRaft instance + a single Kafka instance
 3. Create a topic using

{code:java}
bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic A --replication-factor 1 --partitions 1 --config min.insync.replicas=1 --config segment.bytes=512{code}
 4. Create a few segments with the console producer
 5. Observe that they are deleted after 1 minute
 6. Use the following command

{code:java}
bin/kafka-configs.sh --bootstrap-server loclahost:9092 --entity-type brokers --entity-default --alter --add-config message.max.bytes=1048609{code}
(the value of `message.max.bytes` is irrelevant)
 7. Create a few more segments with the console producer
 8. Observe that segments are no longer deleted after 1 minute
~~~~

### Comments (7)

1.

~~~~
I can confirm the issue as described. I reproduced with trunk, 3.9.0-rc0, and currently supported releases.
~~~~

2.

~~~~
[~christo_lolov] – why is "affects version" set to 3.9.0 while fix version includes 3.8.1? "affects version" should be the earliest version which has this bug.

It seem we should at least update it to 3.8.0, but I am wondering if we want to cherry-pick this for 3.7.2 release that we plan to do?
~~~~

3.

~~~~
[~mjsax]: Going from memory, this particular bug goes all the way back to the earliest 3.0 releases. I didn't bother cherry-picking to 3.7 since I didn't think anyone would make another 3.7 release. There's no reason why it couldn't be ported back to that release, though.
~~~~

4.

~~~~
[~mjsax] Apologies for the delay, I was taking some time off from computers :). At the time of discovering the bug 3.9.0 was undergoing its release candidates, hence I put 3.9.0 as affected version. As Colin correctly mentioned, this is present in all Kafka versions at least since 3.0.
~~~~

5.

~~~~
Thanks. I tried to cherry-pick to 3.7 branch, but it does not cherry-pick cleanly. Should we include it in 3.7.2? If yes, would be great to get some help from people who know this code better. I am also fine with just leave it as is, and not include in 3.7.2. Thoughts?
~~~~

6.

~~~~
Heya [~mjsax], I have a preference for this to make it in 3.7.2. I have made an attempt to port the changes https://github.com/apache/kafka/pull/17696, but I would like reviews from [~cmccabe] (author of the original fix) and [~showuon] (ported the fix to 3.8)
~~~~

7.

~~~~
Thanks! I'll monitor the PR and wait until it's merged before creating the first RC for 3.7.2. Appreciate the help to backport the PR!
~~~~

---

## KAFKA-17749: Throttle metrics have changed name

https://issues.apache.org/jira/browse/KAFKA-17749

Given fix versions: 3.8.1, 3.9.0, 4.0.0
JIRA affects (masked from the system): 3.8.0, 3.9.0

- `KAFKA-17749@3.8.0`: config 3.8.0, metadata answer **affected** (listed_affected)
- `KAFKA-17749@3.7.2`: config 3.7.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.8

### Description

~~~~
In https://github.com/apache/kafka/commit/e4e1116156d44d5e7a52ad8fb51a57d5e5755710, we moved the Throttler class to the storage module but this made the metrics emitted from this class change name.

Since 3.8 the metrics are named org.apache.kafka.storage.internals.utils.Throttler. Previously they were called kafka.utils.Thottler
~~~~

---

## KAFKA-18073: Data loss when exception is raised from Kafka Connect record conversion call

https://issues.apache.org/jira/browse/KAFKA-18073

Given fix versions: 4.0.0
JIRA affects (masked from the system): 3.0.0, 3.0.1, 3.0.2, 3.1.0, 3.1.1, 3.1.2, 3.2.0, 3.2.1, 3.2.2, 3.2.3, 3.3.0, 3.3.1, 3.3.2, 3.4.0, 3.4.1, 3.5.0, 3.5.1, 3.5.2, 3.6.0, 3.6.1, 3.6.2, 3.7.0, 3.7.1, 3.8.0, 3.8.1, 3.9.0

- `KAFKA-18073@3.1.1`: config 3.1.1, metadata answer **affected** (listed_affected)
- `KAFKA-18073@2.8.2`: config 2.8.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.8.1, 3.6.1, 2.0.0, 2.0, 3.9, 3.8, 3.7, 4.0.0

### Description

~~~~
We are experiencing data loss when Kafka Connect source connector fails to send data to Kafka topic after receiving a retriable exception from a schema registry (when converting the record).

Kafka cluster & connect details:
 # Kafka Connect version: 3.8.1
 # Kafka Version 3.6.1
 # Cluster size: 16 brokers
 # Number of partitions in Kafka data topic: 32
 # Number of partitions in offsets topic: 
 # Replication Factor: 4
 # Min In Sync Replicas: 2
 # Unclean leader election disabled
 # Uses Apicurio schema registry to convert to Avro
 # Uses default error tolerance i.e., None

Producer configs
 * acks = -1
 * max.in.flight.requests.per.connection = 1
 * batch.size = 524288

Our connector uses the offsets committed by Kafka Connect (does not have any internal checkpointing/state storage).

Data loss is noticed on occasion when a timeout is received during the [convertTransformedRecod|https://github.com/apache/kafka/blob/3.8.1/connect/runtime/src/main/java/org/apache/kafka/connect/runtime/AbstractWorkerSourceTask.java#L398] call. The timeout is from connecting to the schema registry for the schema. Full stack trace [here|https://gist.github.com/twthorn/5764b9dae2664ca72e71c1e6ebd4c792]

Logs (dropped record is from task 79):
{code:java}
2024-10-22T01:37:41.059Z - INFO - WorkerSourceTask{id=keyspace1-connector-79} Committing offsets for 3 acknowledged messages
2024-10-22T01:37:41.066Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-232} Committing offsets for 1 acknowledged messages
2024-10-22T01:37:41.540Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-259} Committing offsets for 3 acknowledged messages
2024-10-22T01:37:41.928Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-273} Committing offsets for 2 acknowledged messages
2024-10-22T01:37:44Z - info - Handshake message sent
2024-10-22T01:37:51Z - info - Handshake timed out
2024-10-22T01:37:52Z - info - Handshake message sent
2024-10-22T01:37:58Z - info - Handshake timed out
2024-10-22T01:38:04Z - info - Handshake message sent
2024-10-22T01:38:10Z - info - Handshake timed out
2024-10-22T01:38:11.664Z - INFO - [Producer clientId=connector-producer-keyspace1-table1-connector-268] Node 1078 disconnected.
2024-10-22T01:38:15.798Z - INFO - [Producer clientId=connector-producer-keyspace1-table1-connector-219] Node 1089 disconnected.
2024-10-22T01:38:20Z - info - Handshake message sent
2024-10-22T01:38:23.225Z - INFO - [Producer clientId=connector-producer-keyspace1-connector-107] Node 1085 disconnected.
2024-10-22T01:38:23.224Z - INFO - [Producer clientId=connector-producer-keyspace1-connector-107] Node 1088 disconnected.
2024-10-22T01:38:24.536Z - INFO - [Producer clientId=connector-producer-keyspace1-table1-connector-13] Node 1076 disconnected.
2024-10-22T01:38:27Z - info - Handshake timed out
2024-10-22T01:38:27.491Z - INFO - [Producer clientId=connector-producer-keyspace1-table1-connector-237] Node 1082 disconnected.
2024-10-22T01:38:27.492Z - INFO - [Producer clientId=connector-producer-keyspace1-table1-connector-237] Node 1089 disconnected.
2024-10-22T01:38:27.493Z - INFO - [Producer clientId=connector-producer-keyspace1-table1-connector-237] Node 1085 disconnected.
2024-10-22T01:38:27.832Z - INFO - [Producer clientId=connector-producer-keyspace1-table1-connector-237] Node 1088 disconnected.
2024-10-22T01:38:28.470Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-12} Committing offsets for 2 acknowledged messages
2024-10-22T01:38:28.549Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-64} Committing offsets for 14 acknowledged messages
2024-10-22T01:38:36.930Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-53} Committing offsets for 38 acknowledged messages
2024-10-22T01:38:37.701Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-13} Committing offsets for 2 acknowledged messages
2024-10-22T01:38:37.838Z - INFO - [AdminClient clientId=dbzium-prod-keyspace1-shared-admin] Node 1089 disconnected.
2024-10-22T01:38:38.369Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-25} Committing offsets for 6 acknowledged messages
2024-10-22T01:38:39.212Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-56} Committing offsets for 21 acknowledged messages
2024-10-22T01:38:39.597Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-51} Committing offsets for 11 acknowledged messages
2024-10-22T01:38:39.642Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-219} Committing offsets for 4 acknowledged messages
2024-10-22T01:38:39.647Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-237} Committing offsets for 1 acknowledged messages
2024-10-22T01:38:39.681Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-268} Committing offsets for 8 acknowledged messages
2024-10-22T01:38:41.059Z - INFO - WorkerSourceTask{id=keyspace1-connector-107} Committing offsets for 3 acknowledged messages
2024-10-22T01:38:41.540Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-232} Committing offsets for 3 acknowledged messages
2024-10-22T01:38:41.928Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-259} Committing offsets for 2 acknowledged messages
2024-10-22T01:38:42.252Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-273} Committing offsets for 1 acknowledged messages
2024-10-22T01:38:44.913Z - ERROR - Failed to send HTTP request to endpoint: http://schema-registry.service.prod-us-east-1-dw1.consul:8080/apis/ccompat/v6/subjects/prod.keyspace1.table1-key/versions?normalize=false
2024-10-22T01:38:52Z - info - Handshake message sent
2024-10-22T01:39:06.790Z - INFO - [Worker clientId=connect-dbzium-prod-keyspace1-b7cfc9bcc-8z59m.node.prod-us-east-1-vitess1.consul:8083, groupId=dbzium-prod-keyspace1] Rebalance started
2024-10-22T01:39:07.134Z - INFO - [Worker clientId=connect-dbzium-prod-keyspace1-b7cfc9bcc-8z59m.node.prod-us-east-1-vitess1.consul:8083, groupId=dbzium-prod-keyspace1] Successfully joined group with generation Generation{generationId=2477, memberId='connect-dbzium-prod-keyspace1-b7cfc9bcc-8z59m.node.prod-us-east-1-vitess1.consul:8083-a174acf5-1b8f-419a-a25a-4c58dab02a8d', protocol='sessioned'}
2024-10-22T01:39:07.171Z - INFO - [Worker clientId=connect-dbzium-prod-keyspace1-b7cfc9bcc-8z59m.node.prod-us-east-1-vitess1.consul:8083, groupId=dbzium-prod-keyspace1] Successfully synced group in generation Generation{generationId=2477, memberId='connect-dbzium-prod-keyspace1-b7cfc9bcc-8z59m.node.prod-us-east-1-vitess1.consul:8083-a174acf5-1b8f-419a-a25a-4c58dab02a8d', protocol='sessioned'}
2024-10-22T01:39:07.171Z - INFO - [Worker clientId=connect-dbzium-prod-keyspace1-b7cfc9bcc-8z59m.node.prod-us-east-1-vitess1.consul:8083, groupId=dbzium-prod-keyspace1] Joined group at generation 2477 with protocol version 2 and got assignment: Assignment{error=0, leader='connect-dbzium-prod-keyspace1-b7cfc9bcc-h8gxb.node.prod-us-east-1-vitess1.consul:8083-dbbc75cb-1de9-4907-bf4c-f3f6cca6eb9a', leaderUrl='http://dbzium-prod-keyspace1-b7cfc9bcc-h8gxb.node.prod-us-east-1-vitess1.consul:8083/', offset=236838, connectorIds=[], taskIds=[keyspace1-table1-connector-12, keyspace1-table1-connector-13, keyspace1-table1-connector-25, keyspace1-table1-connector-51, keyspace1-table1-connector-53, keyspace1-table1-connector-56, keyspace1-table1-connector-64, keyspace1-table1-connector-219, keyspace1-table1-connector-232, keyspace1-table1-connector-237, keyspace1-table1-connector-259, keyspace1-table1-connector-268, keyspace1-table1-connector-273, keyspace1-connector-79, keyspace1-connector-107, keyspace1-connector-285], revokedConnectorIds=[], revokedTaskIds=[], delay=180000} with rebalance delay: 180000
2024-10-22T01:39:07.172Z - INFO - [Worker clientId=connect-dbzium-prod-keyspace1-b7cfc9bcc-8z59m.node.prod-us-east-1-vitess1.consul:8083, groupId=dbzium-prod-keyspace1] Finished starting connectors and tasks
2024-10-22T01:39:07.172Z - INFO - [Worker clientId=connect-dbzium-prod-keyspace1-b7cfc9bcc-8z59m.node.prod-us-east-1-vitess1.consul:8083, groupId=dbzium-prod-keyspace1] Starting connectors and tasks using config offset 236838
2024-10-22T01:39:12Z - info - Handshake message received
2024-10-22T01:39:12Z - info - Handshake message sent
2024-10-22T01:39:27.534Z - INFO - [Producer clientId=connector-producer-keyspace1-connector-107] Node 1074 disconnected.
2024-10-22T01:39:27.535Z - INFO - [Producer clientId=connector-producer-keyspace1-connector-107] Node 1077 disconnected.
2024-10-22T01:39:28.550Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-12} Committing offsets for 4 acknowledged messages
2024-10-22T01:39:28.622Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-64} Committing offsets for 48 acknowledged messages
2024-10-22T01:39:37.102Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-53} Committing offsets for 30 acknowledged messages
2024-10-22T01:39:38.194Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-13} Committing offsets for 3 acknowledged messages
2024-10-22T01:39:38.556Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-25} Committing offsets for 14 acknowledged messages
2024-10-22T01:39:39.598Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-56} Committing offsets for 15 acknowledged messages
2024-10-22T01:39:40.043Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-51} Committing offsets for 8 acknowledged messages
2024-10-22T01:39:40.086Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-219} Committing offsets for 6 acknowledged messages
2024-10-22T01:39:40.096Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-237} Committing offsets for 1 acknowledged messages
2024-10-22T01:39:40.100Z - INFO - WorkerSourceTask{id=keyspace1-table1-connector-268} Committing offsets for 8 acknowledged messages
2024-10-22T01:39:41.392Z - INFO - WorkerSourceTask{id=keyspace1-connector-79} Committing offsets for 12 acknowledged messages{code}
Does Kafka Connect commit offsets for a batch even if some of the records failed? Or must the whole batch be successful to commit offsets?

It is odd there is no restart, just a logged error that should have been retried.
~~~~

### Comments (7)

1.

~~~~
Perhaps [~cegerton] any ideas on this? I saw your name in the Git history for the files that handle this logic
~~~~

2.

~~~~
The issue appears to be from errors.tolerance. We do not specify a config so it defaults to "none"

 
{code:java}
SourceConnectorConfig values: config.action.reload = restart connector.class = io.debezium.connector.vitess.VitessConnector errors.log.enable = false errors.log.include.messages = false errors.retry.delay.max.ms = 60000 errors.retry.timeout = 0 errors.tolerance = none exactly.once.support = requested header.converter = null key.converter = null name = vifl-4-users_prefs-connector offsets.storage.topic = null predicates = [] tasks.max = 300 tasks.max.enforce = true topic.creation.groups = [] transaction.boundary = poll transaction.boundary.interval.ms = null transforms = [filterTransactionTopicRecords, removeField, useLocalVgtid] value.converter = null {code}
However the connector is still skipping messages, as we see the Grafana metric 
kafka_connect_task_error_metrics_total_records_skipped will start reporting skipped records when we observe data loss. This value jumps from no value to 1.
 
~~~~

3.

~~~~
https://github.com/apache/kafka/pull/18146
~~~~

4.

~~~~
Hmm, yeah this is a regression introduced by KAFKA-6738, added to 2.0.0. The PR and KIP say that it's backwards-compatible, but <2.0 RetriableExceptions caused tasks to fail, and >= 2.0 RetriableExceptions cause the record to be dropped.

I think you can work-around this with a config: [https://kafka.apache.org/documentation/#sourceconnectorconfigs_errors.retry.timeout] which causes the RetriableExceptions to be retried. If you set it to infinite retries, the record will never be dropped, but also the task will never make progress.

As for changing this; I think it is reasonable to make it so that errors.tolerance=none never causes a record to be dropped, as I don't think someone would want RetriableExceptions to be dropped, but non-retriable exceptions to throw an error.
~~~~

5.

~~~~
[~gharris1727] Can we also backport to the other supported releases of 3.9, 3.8, and 3.7? I am happy to put out the PR to each respectively named branch.
~~~~

6.

~~~~
We very likely will not do another release of 3.7, and i'm a little gun-shy of backporting this to 3.8/3.9 after some of my MM2 fixes.

[~mimaison] [~cegerton] do you think this should be backported? It was a breaking change in 2.0.0 that we have now effectively reverted in 4.0.0, and it causes rather severe data loss in 2.x-3.9.x.
~~~~

7.

~~~~
[~gharris1727] If you're unsure, it's safer to not backport this. Hopefully 4.0.0 will release in the coming weeks.
~~~~

---

## KAFKA-18615: StreamThread *-ratio metrics suffer from sampling bias

https://issues.apache.org/jira/browse/KAFKA-18615

Given fix versions: 4.3.0
JIRA affects (masked from the system): 3.8.1

- `KAFKA-18615@3.8.1`: config 3.8.1, metadata answer **affected** (listed_affected)
- `KAFKA-18615@3.8.0`: config 3.8.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
h2. Background

{{StreamThread}} defines {{{}commit-ratio{}}}, {{{}poll-ratio{}}}, {{{}process-ratio{}}}, {{punctuate-ratio}} metrics here: [https://github.com/apache/kafka/blob/trunk/streams/src/main/java/org/apache/kafka/streams/processor/internals/metrics/ThreadMetrics.java#L230-L288] These metrics indicate "The fraction of time the thread spent on \{action}". Unlike DefaultStateUpdater's ratio metrics, these metrics are "value" sensors. Meaning that the observable value of the metric is simply the last value registered before the act of observing the metric. This seems to avoid the ratio averaging issues I described in KAFKA-18369, but...
h2. Issue

Let's analyse an example scenario.

For simplicity I will ignore existence of {{poll-ratio}} and {{{}punctuate-ratio{}}}, and just consider {{{}commit-ratio{}}}, and {{{}process-ratio{}}}.

Let's say an external observer, be it a human reading JMX metrics, or an automated metric scraping solution, reads the metrics at a random point in time, uncorrelated with the inner workings of the kafka-streams application.

The application itself works under a steady workload and the stream thread does 1000 iterations every 10 seconds, of which:
 * 999 iterations execute only {{process}} taking {{{}1ms{}}}, resulting in {{commit-ratio=0}}
 * 1 iteration executes {{process}} taking {{1ms}} and {{commit}} taking {{{}9000ms{}}}, resulting in {{commit-ratio=0.9998889012}}

In no specific order. But we will assume that two committing iterations never happen one after another (the issue still exists without this assumption, the math just gets harder. Also the assumption is realistic given how kafka streams works).

The ratio metrics are always updated at the end of an iteration. Therefore metric values corresponding to iteration number I, are visible for the duration of iteration number I+1. In that 10s period, there's only 1ms during which the {{commit-ratio=0.9998889012}} can be observed, as 1ms later one of the short iterations completes and overwrites the metric values. During the remaining 9999ms a {{commit-ratio=0}} would be observed. Therefore our random observer has 99.99% probability of observing a {{{}commit-ratio=0{}}}, even though the {{{}StreamThread{}}}, spends 90% of its time on {{commit}}
h2. Solution

This ticket is a sibling of KAFKA-18369 I wanted to report it as a separate ticket as these are different metrics, with currently different implementation, affected by a different problem that needs a separate explanation. But in my opinion the ratio metrics of {{StreamThread}} and {{DefaultStateUpdate}} should work, and be implemented the same way, so when it comes to a solution I will just refer to the ongoing discussion in KAFKA-18369.
~~~~

---

## KAFKA-18843: MirrorMaker2 workerId is not unique, but use the same for all the workers

https://issues.apache.org/jira/browse/KAFKA-18843

Given fix versions: 4.1.0
JIRA affects (masked from the system): 3.7.0, 3.8.0, 3.9.0, 4.0.0

- `KAFKA-18843@3.9.0`: config 3.9.0, metadata answer **affected** (listed_affected)
- `KAFKA-18843@3.6.2`: config 3.6.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
MirrorMaker2 is using the `sourceAndTarget.toString()` as a workerId, that makes all the worker's IDs the same across the distributed herder.

[https://github.com/apache/kafka/blob/d31cbf59dee6a77c1c673db06900ecc238894ed7/connect/mirror/src/main/java/org/apache/kafka/connect/mirror/MirrorMaker.java#L243]

 

This not cause any functional issues based on our experience, but renders the workerId in the status topic messages and in the rest responses useless or misleading.
~~~~

---

## KAFKA-19147: ConsumerGroupHeartbeat API leaks topic id and partition count of unauthorized topics

https://issues.apache.org/jira/browse/KAFKA-19147

Given fix versions: 4.0.1, 4.1.0
JIRA affects (masked from the system): 4.0.0

- `KAFKA-19147@4.0.0`: config 4.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-19147@3.9.2`: config 3.9.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
KAFKA-18813 added Topic:Describe authorization of topics matching regex patterns to the group coordinator since it was difficult to authorize these in the broker when processing the new consumer heartbeat. But group coordinator is started in BrokerServer before the authorizer is created. And hence group coordinator doesn't have an authorizer and never performs authorization. As a result, topics that are not authorized for Describe may be assigned to consumers. This potentially leaks information about topic existence, topic id and partition count to users who are not authorized to describe a topic.

 

We are missing an integration test for this case.
~~~~

---

## KAFKA-19233: Members cannot rejoin with epoch=0 for KIP-848

https://issues.apache.org/jira/browse/KAFKA-19233

Given fix versions: 4.2.0
JIRA affects (masked from the system): 4.0.0, 4.1.0

- `KAFKA-19233@4.1.0`: config 4.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-19233@3.9.2`: config 3.9.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 4.1, 4.2

### Description

~~~~
If a group is on generation > 1 and a member is fenced, the member cannot rejoin until the broker expires the member from the group.

KIP-848 says "Upon receiving the UNKNOWN_MEMBER_ID or FENCED_MEMBER_EPOCH error, the consumer abandon all its partitions and rejoins with the same member id and the epoch 0.".

However, the current implementation on the broker throws FENCED_MEMBER_EPOCH if the client provided epoch, when not equal to the current epoch, is anything other than the current epoch - 1.

Specifically this line: [https://github.com/apache/kafka/blob/e68781414e9bcbc1d7cd5c247433a13f8d0e2e6e/group-coordinator/src/main/java/org/apache/kafka/coordinator/group/GroupMetadataManager.java#L1535]

If the current epoch is 13, and I reset to epoch 0, the conditional always throws FENCED_MEMBER_EPOCH.

Attached are logs of this case, here is a sample of a single log line demonstrating the problem:
{code:java}
2025-05-02 15:23:09,304 [data-plane-kafka-network-thread-3-ListenerName(PLAINTEXT)-PLAINTEXT-0] DEBUG kafka.request.logger - Completed request:{"isForwarded":false,"requestHeader":{"requestApiKey":68,"requestApiVersion":1,"correlationId":46,"clientId":"kgo","requestApiKeyName":"CONSUMER_GROUP_HEARTBEAT"},"request":{"groupId":"67660d2bfc7b197c91ff86623614522285c05c14b9f817fa99e6c105a2f54d7f","memberId":"uxNPFKnjF3OrkZIAghLN1Q==","memberEpoch":0,"instanceId":null,"rackId":null,"rebalanceTimeoutMs":60000,"subscribedTopicNames":["aed98f76851080d77b6098a03ea5ef088dabc21331462e44ed7ae5be463e2655"],"subscribedTopicRegex":null,"serverAssignor":"range","topicPartitions":[]},"response":{"throttleTimeMs":0,"errorCode":110,"errorMessage":"The consumer group member has a smaller member epoch (0) than the one known by the group coordinator (11). The member must abandon all its partitions and rejoin.","memberId":null,"memberEpoch":0,"heartbeatIntervalMs":0,"assignment":null},"connection":"127.0.0.1:9096-127.0.0.1:56686-0-292","totalTimeMs":0.801,"requestQueueTimeMs":0.159,"localTimeMs":0.106,"remoteTimeMs":0.315,"throttleTimeMs":0,"responseQueueTimeMs":0.066,"sendTimeMs":0.153,"securityProtocol":"PLAINTEXT","principal":"User:ANONYMOUS","listener":"PLAINTEXT","clientInformation":{"softwareName":"kgo","softwareVersion":"unknown"}}
{code}
The logs show the broker continuously responding errcode 110 for 50s until, I'm assuming, some condition boots the member from the group, such that the next time the broker receives the request, the member is considered new and the request is successful.

The first heartbeat is duplicated; I noticed that Kafka replies with FENCED_MEMBER_EPOCH _way too often_ if a heartbeat is duplicated, and I'm trying to see if it's possible to work around that. As an aside, between the fenced error happening {_}a lot{_}, this issue, and KAFKA-19222, I'm leaning to not opt into KIP-848 by default until the broker implementation improves.
~~~~

### Comments (16)

1.

~~~~
Hi [~twmb] ! When a member is fenced, it should be allowed to rejoin with epoch 0. This is how the flow goes:
 # member fenced: coordinator removes it from the group ([https://github.com/apache/kafka/blob/e68781414e9bcbc1d7cd5c247433a13f8d0e2e6e/group-coordinator/src/main/java/org/apache/kafka/coordinator/group/GroupMetadataManager.java#L3987] and client receives FencedMemberEpochException)
 # member rejoins with epoch 0 when it receives the FencedMemberEpochException
 # coordinator gets HB request from member that is not in the group (removed in step 1), so creates new member (epoch 0) ([https://github.com/apache/kafka/blob/e68781414e9bcbc1d7cd5c247433a13f8d0e2e6e/group-coordinator/src/main/java/org/apache/kafka/coordinator/group/GroupMetadataManager.java#L2824)]
 # validation of epoch OK on throwIfConsumerGroupMemberEpochIsInvalid ("receivedMemberEpoch" will be 0, equals to "member.memberEpoch()" 0).

From the logs you shared, doesn't look that 1 happened, so if it wasn't fenced it is expected that it cannot rejoin with epoch 0 (I see a client rejoining with epoch 0 when it's still in the group with epoch 11)
"The consumer group member has a smaller member epoch (0) than the one known by the group coordinator (11). The member must abandon all its partitions and rejoin."
So, when you say:
{noformat}
If the current epoch is 13, and I reset to epoch 0, the conditional always throws FENCED_LEADER_EPOCH.{noformat}
 

That's expected, a member that it's in a group (with epoch 13) cannot rejoin (epoch 0) without leaving the group first or being removed/fenced.

I guess you're working on a client implementation of the protocol, so maybe it helps to take a look at the java-client implementation? Specifically check out the calls to [transitionToJoining|[https://github.com/apache/kafka/blob/e68781414e9bcbc1d7cd5c247433a13f8d0e2e6e/clients/src/main/java/org/apache/kafka/clients/consumer/internals/AbstractMembershipManager.java#L533],] it can only happen:
 * after being fenced (it's not in the group at this point, removed by the coord)
 * after calling consumer.subscribe if it's not in the group
 * after pro-actively leaving the group because of time between consumer.poll too long 

Hope it helps! Best!

Lianet
~~~~

2.

~~~~
What has you thinking (1) did not happen? In the broker logs, line 2 shows the broker replying to the client with FENCED_MEMBER_EPOCH (errorCode 110).

 
 * Line 1: CONSUMER_GROUP_HEARTBEAT, member uxNP... epoch 10. The broker replies a successful response. This is a full request (all fields present).
 * Line 2, simulating the client disconnected and lost the response: CONSUMER_GROUP_HEARTBEAT for member uxNP epoch 10. The broker replies errorCode 110, FENCED_MEMBER_EPOCH. This is a full request (all fields present).
 * Line 3, repeated full request again: CONSUMER_GROUP_HEARTBEAT uxNP e10. The broker replies FENCED_MEMBER_EPOCH
 * Line 4, Client resets the epoch to 0 and sends a full request – all owned topics are lost. CONSUMER_GROUP_HEARTBEAT uxNP e0. The broker replies FENCED_MEMBER_EPOCH.

The client then repeatedly retries epoch 0 with full requests.
~~~~

3.

~~~~
Sorry, I wrote FENCED_LEADER_EPOCH above a few times when I meant to write FENCED_MEMBER_EPOCH. That's been corrected. All errors are fenced member epochs, not leader.
~~~~

4.

~~~~
I've released franz-go v1.19 opting out of enabling the next gen rebalancer by default.

I did not see any Java tests exercising what happens when heartbeat requests are repeated. My client works _fine_ when requests are repeated, but it is effectively degraded. I don't believe the broker is behaving appropriately: fences happen far too often.

Please let me know what you think for this and KAFKA-19235. I'll leave the group disabled until these are resolved.
~~~~

5.

~~~~
Hey [~twmb] , sorry busy lately but catching up here to help, some answers and questions too. On the flow you describe:

Line 1 : OK

Line 2 : OK, but why a full HB after a successful response from the broker on Line 1?

Line 3: Why is the client repeating "CONSUMER_GROUP_HEARTBEAT uxNP e10."? If it got FENCED_MEMBER_EPOCH on Line 2 from the broker, the client should release its assignment, reset the epoch to 0, and only then HB again to rejoin (so HB with 0, not 10)

Line 4: This one is unexpected. Could you double check in this case, why is the fence error set on the broker? maybe point me to the logs (member epoch is 0, I expect it doesn't exist on the broker because you have it fenced/removed) . Related to this, on the initial description you shared there was a case where I didn't see fencing hapening because of this log you shared:
> "The consumer group member has a smaller member epoch (0) than the one known by the group coordinator (11). The member must abandon all its partitions and rejoin."

If the member is "known by the group coordinator (11)" I expect it's because it is still in the group with epoch 0 (so not fenced). Are this logs mixing several clients maybe?

This test in the java client covers this area of what a fenced member should do [https://github.com/apache/kafka/blob/c28f46459ac26693b3639fca26c0961283c2ee65/clients/src/test/java/org/apache/kafka/clients/consumer/internals/ConsumerHeartbeatRequestManagerTest.java#L839] 

Please let me know the setup you are running (how many consumers?), and with that and the answers to the questions above we can probably sort this out.

Best!
~~~~

6.

~~~~
I rewired the guts of the client to deliberately trigger the case where responses are lost due to connections being cut. If needed, I can change the client to kill the connection rather than just repeated the request. Thus,

> Line 2 : OK, but why a full HB after a successful response from the broker on Line 1?

The client never "received" the response. The response is lost. The client is re-issuing a full heartbeat. My immediate question is: why is the client already fenced?

> Line 3: Why is the client repeating "CONSUMER_GROUP_HEARTBEAT uxNP e10."? If it got FENCED_MEMBER_EPOCH on Line 2 from the broker, the client should release its assignment, reset the epoch to 0, and only then HB again to rejoin (so HB with 0, not 10)

Loss simulation.

>  Could you double check in this case, why is the fence error set on the broker?

I can't. I enabled every logger on the broker with {{{}log4j.logger.kafka=DEBUG{}}}. There is no log related to decisions the broker is making with adding or removing members from the group. I'd be quite happy to have a problem in my properties file, but I saw nothing.

> Are this logs mixing several clients maybe?

The logs1 file attached in this issue are all logs for the member ID in the cluster {{{}uxNPFKnjF3OrkZIAghLN1Q=={}}}. I deleted all logs for other clients. The fourth line in that file shows the client joining with epoch 0 and receiving a fenced response:
{noformat}
2025-05-02 15:22:32,739 [data-plane-kafka-network-thread-3-ListenerName(PLAINTEXT)-PLAINTEXT-0] DEBUG kafka.request.logger - Completed request:{"isForwarded":false,"requestHeader":{"requestApiKey":68,"requestApiVersion":1,"correlationId":25,"clientId":"kgo","requestApiKeyName":"CONSUMER_GROUP_HEARTBEAT"},"request":{"groupId":"67660d2bfc7b197c91ff86623614522285c05c14b9f817fa99e6c105a2f54d7f","memberId":"uxNPFKnjF3OrkZIAghLN1Q==","memberEpoch":0,"instanceId":null,"rackId":null,"rebalanceTimeoutMs":60000,"subscribedTopicNames":["aed98f76851080d77b6098a03ea5ef088dabc21331462e44ed7ae5be463e2655"],"subscribedTopicRegex":null,"serverAssignor":"range","topicPartitions":[]},"response":{"throttleTimeMs":0,"errorCode":110,"errorMessage":"The consumer group member has a smaller member epoch (0) than the one known by the group coordinator (11). The member must abandon all its partitions and rejoin.","memberId":null,"memberEpoch":0,"heartbeatIntervalMs":0,"assignment":null},"connection":"127.0.0.1:9096-127.0.0.1:56686-0-292","totalTimeMs":0.143,"requestQueueTimeMs":0.022,"localTimeMs":0.023,"remoteTimeMs":0.056,"throttleTimeMs":0,"responseQueueTimeMs":0.013,"sendTimeMs":0.027,"securityProtocol":"PLAINTEXT","principal":"User:ANONYMOUS","listener":"PLAINTEXT","clientInformation":{"softwareName":"kgo","softwareVersion":"unknown"}} {noformat}
The prior line, you can see the client is fenced with epoch 11.

 

That test demonstrates that the client releases its subscription and rejoins with epoch 0 once it receives member fenced. There is no test that specifically simulates what happens in the case that the first heartbeat response is lost. I _suspect_ (I'm not positive) that if Confluent simulated some lost responses in an integration test, there would be a _lot_ more fenced errors encountered than expected.

 

If you're curious, this is the test I am running:

[https://github.com/twmb/franz-go/blob/master/pkg/kgo/helpers_test.go#L460-L557]

This is the code where I was ignoring the first response and reissuing the request (i.e., response lost): [https://github.com/twmb/franz-go/blob/master/pkg/kgo/consumer_group_848.go#L161-L172]

Some modifications will need to be made to trigger this issue – I have commented out the loss simulation and plan to re-run it on future releases to decide whether to opt into the next gen balancer or not.
~~~~

7.

~~~~
Hey Travis, could you double check if you're sending the assigned partitions when you're re-issuing the HB request? and if the client had no assignment yet you should be sending a empty list of partitions as a full HB (not null), please check and let me know. 

This is required so that the coordinator can let a member back in after a fencing it epoch (ex. on lost HB response). This coordinator check you were sharing:
https://github.com/apache/kafka/blob/e68781414e9bcbc1d7cd5c247433a13f8d0e2e6e/group-coordinator/src/main/java/org/apache/kafka/coordinator/group/GroupMetadataManager.java#L1535 
Also note that it checks that the member comes with the previous epoch it had (expecting that the client may loose one HB response with a bumped epoch, then rejoin with the previous epoch).

The java client deals with this situation by ensuring :
- sends only 1 HB at a time (until response from broker or timeout/error on request)
- on retriable errors (ex. timeout on no reponse) it resends a full HB (including the assigned partitions, ex. empty list if first request got no response), so the check on the coordinator allows it back it

Let me know if this helps, and I will definitely clarify on the KIP Fencing section (we were also mixing on this jira 2 fencing scenarios: fenced member vs fenced epoch). This issue is about fenced epoch, will clarify it all on the doc.  

~~~~

8.

~~~~
Yes, the client is sending the assigned partitions when re-issuing the heartbeat request. You can see in my comment just above – the broker log – that the client is sending an empty topicPartitions. `"topicPartitions":[]`. The line you sent is actually the line I included in the issue description.

 

I'm not sure what more incontrovertible proof I could attach _besides_ the broker logs that show the full request flow from the client that I attached at the start of this issue. I understand that the Java client is giving up all partitions and rejoining; I'm doing exactly the same thing. I'm pointing out two things in my series of issues:
 * There is a bug on the broker somewhere. I am rejoining with epoch 0 and a non-null empty list of partitions. The broker keeps rejecting the rejoin request.
 * If you repeat heartbeat requests, {_}simulating faulty connections{_}, the broker will fence the member way too much. This is recoverable (sometimes, minus the bug in the prior point), but it is undesirable behavior.

 
~~~~

9.

~~~~
This is still a problem on Kafka 4.1.

Again, I am joining with epoch 0, and I am receiving FENCED_MEMBER_EPOCH.
~~~~

10.

~~~~
Hi [~twmb], thanks for the bug report. I looked into it and I think that there are two issues:

1) First, as you said, we should accept the member rejoining with the same member id but with the member epoch equals to zero and the partitions equals to the empty array. With this, the member should re-sync himself.

2) There is a bug in throwIfConsumerGroupMemberEpochIsInvalid. When we check whether the member owns a subset of the currently assigned partitions, we should check both the assigned partitions and the partitions pending revocation. In the example you gave, the assigned partitions is altered by the first HB request as one partition is moved to the revocation set. Hence when the HB request is retried, the received assignment is not a subset of the assigned partitions any more. However, it is a subset of the union of both sets.

Does it sound good to you?

I will take care of fixing those issues. Sorry for the delay but I missed it.
~~~~

11.

~~~~
I think this also applies to share groups.
~~~~

12.

~~~~
Possibly. Streams is also affected. cc [~lucasbru] 
~~~~

13.

~~~~
Hum.. I take back what I said about 2) as I could not reproduce it. 

[~twmb] In the logs that you shared, the first request looks weird to me:
{noformat}
2025-05-02 15:22:32,738 [data-plane-kafka-network-thread-3-ListenerName(PLAINTEXT)-PLAINTEXT-0] DEBUG kafka.request.logger - Completed request:{"isForwarded":false,"requestHeader":{"requestApiKey":68,"requestApiVersion":1,"correlationId":22,"clientId":"kgo","requestApiKeyName":"CONSUMER_GROUP_HEARTBEAT"},"request":{"groupId":"67660d2bfc7b197c91ff86623614522285c05c14b9f817fa99e6c105a2f54d7f","memberId":"uxNPFKnjF3OrkZIAghLN1Q==","memberEpoch":10,"instanceId":null,"rackId":null,"rebalanceTimeoutMs":60000,"subscribedTopicNames":["aed98f76851080d77b6098a03ea5ef088dabc21331462e44ed7ae5be463e2655"],"subscribedTopicRegex":null,"serverAssignor":"range","topicPartitions":[{"topicId":"zHbLcuRwS5qGhVyq9KVajw","partitions":[24,25,26]}]},"response":{"throttleTimeMs":0,"errorCode":0,"errorMessage":null,"memberId":"uxNPFKnjF3OrkZIAghLN1Q==","memberEpoch":11,"heartbeatIntervalMs":5000,"assignment":{"topicPartitions":[{"topicId":"zHbLcuRwS5qGhVyq9KVajw","partitions":[24,25]}]}},"connection":"127.0.0.1:9096-127.0.0.1:56686-0-292","totalTimeMs":5.972,"requestQueueTimeMs":0.043,"localTimeMs":0.037,"remoteTimeMs":5.832,"throttleTimeMs":0,"responseQueueTimeMs":0.019,"sendTimeMs":0.039,"securityProtocol":"PLAINTEXT","principal":"User:ANONYMOUS","listener":"PLAINTEXT","clientInformation":{"softwareName":"kgo","softwareVersion":"unknown"}}{noformat}
The request has partitions 24, 25 and 26 with epoch 10. The response returns partitions 24 and 25 with epoch 11. This is not a valid transition as the member must remain in epoch 10 until partition 26 is fully revoked. I cannot explain how this happened based on the code yet. Would you have a way to reproduce it?
~~~~

14.

~~~~
We fixed the bug preventing a member to rejoin the group with epoch=0 after being fenced. Regarding the duplicate requests, we added unit and integration tests to verify that sending a new full request with the same epoch after a failure works as expected in all the possible states that the member is in. Sending a duplicate partial request is not supported by the protocol at the moment. The reason is that we need to have the owned partition when the member epoch is stale.

[~twmb] Please try again with your implementation. Feel free to raise a new bug if you still face any issues. You can tag me directly.
~~~~

15.

~~~~
[~christo_lolov] Could we include the patches of this Jira in RC1?
~~~~

16.

~~~~
Yup, I just cherry-picked these on 4.2!
~~~~

---

## KAFKA-19758: Weird behavior on Kafka Connect 4.1 class loading

https://issues.apache.org/jira/browse/KAFKA-19758

Given fix versions: 4.1.1, 4.2.0
JIRA affects (masked from the system): 4.1.0

- `KAFKA-19758@4.1.0`: config 4.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-19758@4.0.2`: config 4.0.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 4.1, 3.3.0, 4.1.0, 3.2.0, 4.0.0, 4.0, 3.4.0, 1.0, 1.1, 4.1.1

### Description

~~~~
I have the [DebeziumOpenLineageEmitter|https://github.com/debezium/debezium/blob/main/debezium-openlineage/debezium-openlineage-api/src/main/java/io/debezium/openlineage/DebeziumOpenLineageEmitter.java] class in the *debezium-openlineage-api* that internally has a static map to maintain the registered emitter, the key of this map is "connectoLogicalName-taskid"
Then there is the [OpenLineage SMT|https://github.com/debezium/debezium/blob/main/debezium-core/src/main/java/io/debezium/transforms/openlineage/OpenLineage.java], which is part of the *debezium-core.* In this SMT, I simply pass the same context to instantiate the same emitter via the connector.

Now I'm running the following image
{code:java}
FROM quay.io/debezium/connect:3.3.0.Final
ENV MAVEN_REPO="https://repo1.maven.org/maven2"
ENV GROUP_ID="io/debezium"
ENV DEBEZIUM_VERSION="3.3.0.Final"
ENV ARTIFACT_ID="debezium-openlineage-core"
ENV CLASSIFIER="-libs"
COPY log4j.properties /kafka/config/log4j.properties

Add OpenLineage
RUN mkdir -p /tmp/openlineage-libs && \
    curl "$MAVEN_REPO/$GROUP_ID/$ARTIFACT_ID/$DEBEZIUM_VERSION/$ARTIFACT_ID-${DEBEZIUM_VERSION}${CLASSIFIER}.tar.gz" -o /tmp/debezium-openlineage-core-libs.tar.gz && \
    tar -xzvf /tmp/debezium-openlineage-core-libs.tar.gz -C /tmp/openlineage-libs --strip-components=1

RUN cp -r /tmp/openlineage-libs/* /kafka/connect/debezium-connector-postgres/
RUN cp -r /tmp/openlineage-libs/* /kafka/connect/debezium-connector-mongodb/
ADD openlineage.yml /kafka/ {code}
So is practically debezium connect image with just openlineage jars copied into postgres and mongodb connector folders.

When I register the PostgreSQL connector
{code:java}
{
  "name": "inventory-connector-postgres",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "tasks.max": "1",
    "database.hostname": "postgres",
    "database.port": "5432",
    "database.user": "postgres",
    "database.password": "postgres",
    "database.server.id": "184054",
    "database.dbname": "postgres",
    "topic.prefix": "inventory",
    "snapshot.mode": "initial",
    "schema.history.internal.kafka.bootstrap.servers": "kafka:9092",
    "schema.history.internal.kafka.topic": "schema-changes.inventory",
    "slot.name": "postgres",
    "openlineage.integration.enabled": "true",
    "openlineage.integration.config.file.path": "/kafka/openlineage.yml",
    "openlineage.integration.job.description": "This connector does cdc for products",
    "openlineage.integration.tags": "env=prod,team=cdc",
    "openlineage.integration.owners": "Mario=maintainer,John Doe=Data scientist,IronMan=superero",
    "transforms": "openlineage",
    "transforms.openlineage.type": "io.debezium.transforms.openlineage.OpenLineage"
  }
} {code}
 
I get the following error
{code:java}
2025-10-03T14:22:09,761 ERROR  ||  WorkerSourceTask{id=inventory-connector-postgres-0} Task threw an uncaught and unrecoverable exception. Task is being killed and will not recover until manually restarted   [org.apache.kafka.connect.runtime.WorkerTask]
org.apache.kafka.connect.errors.ConnectException: Tolerance exceeded in error handler
    at org.apache.kafka.connect.runtime.errors.RetryWithToleranceOperator.execAndHandleError(RetryWithToleranceOperator.java:260) ~[connect-runtime-4.1.0.jar:?]
    at org.apache.kafka.connect.runtime.errors.RetryWithToleranceOperator.execute(RetryWithToleranceOperator.java:180) ~[connect-runtime-4.1.0.jar:?]
    at org.apache.kafka.connect.runtime.TransformationChain.apply(TransformationChain.java:58) ~[connect-runtime-4.1.0.jar:?]
    at org.apache.kafka.connect.runtime.AbstractWorkerSourceTask.sendRecords(AbstractWorkerSourceTask.java:415) ~[connect-runtime-4.1.0.jar:?]
    at org.apache.kafka.connect.runtime.AbstractWorkerSourceTask.execute(AbstractWorkerSourceTask.java:376) ~[connect-runtime-4.1.0.jar:?]
    at org.apache.kafka.connect.runtime.WorkerTask.doRun(WorkerTask.java:243) ~[connect-runtime-4.1.0.jar:?]
    at org.apache.kafka.connect.runtime.WorkerTask.run(WorkerTask.java:298) ~[connect-runtime-4.1.0.jar:?]
    at org.apache.kafka.connect.runtime.AbstractWorkerSourceTask.run(AbstractWorkerSourceTask.java:83) ~[connect-runtime-4.1.0.jar:?]
    at org.apache.kafka.connect.runtime.isolation.Plugins.lambda$withClassLoader$1(Plugins.java:254) ~[connect-runtime-4.1.0.jar:?]
    at java.base/java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:572) ~[?:?]
    at java.base/java.util.concurrent.FutureTask.run(FutureTask.java:317) ~[?:?]
    at java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1144) ~[?:?]
    at java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:642) ~[?:?]
    at java.base/java.lang.Thread.run(Thread.java:1583) [?:?]
Caused by: java.lang.IllegalStateException: DebeziumOpenLineageEmitter not initialized for connector ConnectorContext[connectorLogicalName=inventory, connectorName=postgresql, taskId=0, version=null, config=null]. Call init() first.
    at io.debezium.openlineage.DebeziumOpenLineageEmitter.getEmitter(DebeziumOpenLineageEmitter.java:176) ~[debezium-openlineage-api-3.3.0.Final.jar:3.3.0.Final]
    at io.debezium.openlineage.DebeziumOpenLineageEmitter.emit(DebeziumOpenLineageEmitter.java:153) ~[debezium-openlineage-api-3.3.0.Final.jar:3.3.0.Final]
    at io.debezium.transforms.openlineage.OpenLineage.apply(OpenLineage.java:74) ~[debezium-core-3.3.0.Final.jar:3.3.0.Final]
    at org.apache.kafka.connect.runtime.TransformationStage.apply(TransformationStage.java:95) ~[connect-runtime-4.1.0.jar:?]
    at org.apache.kafka.connect.runtime.TransformationChain.lambda$apply$0(TransformationChain.java:58) ~[connect-runtime-4.1.0.jar:?]
    at org.apache.kafka.connect.runtime.errors.RetryWithToleranceOperator.execAndRetry(RetryWithToleranceOperator.java:208) ~[connect-runtime-4.1.0.jar:?]
    at org.apache.kafka.connect.runtime.errors.RetryWithToleranceOperator.execAndHandleError(RetryWithToleranceOperator.java:244) ~[connect-runtime-4.1.0.jar:?]
    ... 13 more {code}
Full logs [^connect-service.log]

 

This is evidence that the emitters map is not shared between the connector and the SMT.

The situation becomes weirder if I remove all connectors from the image except PostgreSQL and MongoDB.
In that case, the PostgreSQL connector works perfectly.

The plugins are in the folder */kafka/connect* (that is, the only `plugin.path` configured folder), each under a dedicated folder with their dependencies. 

I then started to add more connectors, and it continued to work until I added the SQL Server connector.
To summarize, the problem arises when I put one or all of [sqlserver, spanner,vitess].
 
The commonality for these connectors seems to be that they support multi-task. The others don't. 

Am I correct that Kafka Connect guarantees that each connector is loaded with an isolated class loader with its dependencies so that the static emitters should be shared between the Connector and the SMT?

To add more, if I run the image from 3.2.0.Final (so Kafka 4.0.0) with all connectors, it works fine.

I did other tests, and things are more and more weird. All tests were done with *{{plugin.path=/kafka/connect}}* and *KC 4.1*

My original tests were with this directory structure

 
{code:java}
/kafka/connect
|___ debezium-connector-postgres
|___ debezium-connector-mongodb
|___ debezium-connector-sqlserver{code}
 

In this case, each connector should be isolated from each others (having a dedicated class loader). In that case, the sharing between the connector and SMT does not work for KC 4.0

Then I tried with

 
{code:java}
/kafka/connect
|___ debezium-connectors
     |___ debezium-connector-postgres
     |___ debezium-connector-mongodb
     |___ debezium-connector-sqlserver{code}
 

So all connectors are not isolated and share the same class loader. In this case, no issue. And I'll say that this is expected.

Then I tried with

 
{code:java}
/kafka/connect
|___ debezium-connectors
|    |___ debezium-connector-postgres
|    |___ debezium-connector-mongodb
|___ debezium-connector-sqlserver{code}
 

where *{{postgres}}* and *{{mongodb}}* are not isolated (same classloader) and *{{sqlserver}}* is isolated (different classloader), and in this case, it still works. I expected this to fail as with the first setup.

The SMT is in the *debezium-core* jar that and each connector has its own copy
So in each connector folder, there are:
{code:java}
debezium-api-3.3.0.Final.jar
debezium-common-3.3.0.Final.jar
debezium-connector-[connectorName]-3.3.0.Final.jar
debezium-core-3.3.0.Final.jar
debezium-openlineage-api-3.3.0.Final.jar{code}
~~~~

### Comments (22)

1.

~~~~
After some investigations, it looks like KIP-891 broke plugin isolation. For example if we have the same transformation under multiple directories, when Connect tries to execute it, it doesn't call apply with the classloader from the right connector.

The issue seems to be in DelegatingClassLoader.findPluginLoader() where it always loops through all directories to find the transformation (or predicate) and keeps the last instance. It then uses the classloader of that instance which may not be the same one as the connector.

Adding custom tracing I see:

{noformat}
ConnectorConfig.getTransformationOrPredicate connector=io.debezium.connector.postgresql.PostgresConnector connectorRange=null range=[3.4.0-SNAPSHOT,3.4.0-SNAPSHOT]
ConnectorConfig.getTransformationOrPredicate classloader=PluginClassLoader{pluginLocation=file:/tmp/plugins/debezium-connector-postgres/}
OpenLineage instantiated io.debezium.transforms.openlineage.OpenLineage@2675b74a from /tmp/plugins/debezium-connector-sqlserver/debezium-core-3.4.0-SNAPSHOT.jar
classloader null PluginClassLoader{pluginLocation=file:/tmp/plugins/debezium-connector-sqlserver/}
{noformat}

The connector is running from PluginClassLoader{pluginLocation=file:/tmp/plugins/debezium-connector-postgres/} and trying to run its transformation using PluginClassLoader{pluginLocation=file:/tmp/plugins/debezium-connector-sqlserver/}. The OpenLineage transformation exists in both directories but the DelegatingClassLoader.findPluginLoader() fails to find the appropriate one.

We should clarify the expected behavior when a plugins exists under multiple directories. Having multiple times the same connector with the same version should probably be rejected as from the connector configuration, where you have the name and version, you can't decide which one to run. On the other hands, the other connector plugins can exists in multiple copies as long as they are in different directories, thus isolated, as they are always associated with a connector so we can identify a preferred copy.

Another inconsistency found while looking at this is that we have default versions for transformations and predicates but the other plugins default to null. For example, the connector configuration submitted via the REST API does not include any version but the computed configuration injects 3.4.0-SNAPSHOT for the transformation.

{noformat}
        config.action.reload = restart
	connector.class = io.debezium.connector.postgresql.PostgresConnector
	connector.plugin.version = null
	errors.log.enable = false
	errors.log.include.messages = false
	errors.retry.delay.max.ms = 60000
	errors.retry.timeout = 0
	errors.tolerance = none
	header.converter = null
	header.converter.plugin.version = null
	key.converter = null
	key.converter.plugin.version = null
	name = inventory-connector-postgres
	predicates = []
	tasks.max = 1
	tasks.max.enforce = true
	transforms = [openlineage]
	transforms.openlineage.negate = false
	transforms.openlineage.plugin.version = 3.4.0-SNAPSHOT
	transforms.openlineage.predicate = null
	transforms.openlineage.type = class io.debezium.transforms.openlineage.OpenLineage
	value.converter = null
	value.converter.plugin.version = null
{noformat}


~~~~

2.

~~~~
[~gharris] [~snehashisp] WDYT?
~~~~

3.

~~~~
I have not had a chance to inspect the code or reproduce this for myself, but my first impressions:
 # I don't think communication via static fields is good practice, and should be avoided if possible. I personally have been on the receiving end of bugs caused by static fields within a single plugin; I also think I personally would not like to debug static fields shared across plugins.
 # In deployments which make use of the plugin.version configs, changing the pinned version will necessarily change which instance of a static variable is used. So even if the isolation is bug-free, it is trivial for a user or automated tooling to foot-gun a plugin which uses static fields by changing the plugin.version
 # The concern about the backwards-compatibility when plugin.version is unset is valid. We made some attempts to use the connector's class loader or delegating class loader like in the old implementation, so perhaps the version being explicitly injected is not just a cosmetic problem.

IMHO we should investigate the backwards-compatibility problem and try and make a minimal fix to preserve the old behavior when plugin.version is unset. And the affected plugins should eliminate their usage of static variables in order to be well behaved when the plugin.version is set.
~~~~

4.

~~~~
??I don't think communication via static fields is good practice, and should be avoided if possible. I personally have been on the receiving end of bugs caused by static fields within a single plugin; I also think I personally would not like to debug static fields shared across plugins.??

I agree that this is not the best approach, but the problem here is to understand what is possible and what is not.

AFAIK, until KC 4.0, this was possible due to plugin isolation, as the same classloader was used to load the connector and its dependencies. 

Even I think that plugin versioning is compatible also with the isolation (and this seems to be the goal of [KIP-891|https://cwiki.apache.org/confluence/display/KAFKA/KIP-891%3A+Running+multiple+versions+of+Connector+plugins]), if this is something that is not true anymore, I would have expected it to be changed in a major release and not in a minor one.

??In deployments which make use of the plugin.version configs, changing the pinned version will necessarily change which instance of a static variable is used. So even if the isolation is bug-free, it is trivial for a user or automated tooling to foot-gun a plugin which uses static fields by changing the plugin.version??

Can you better clarify this point? 

??IMHO we should investigate the backwards-compatibility problem and try and make a minimal fix to preserve the old behavior when plugin.version is unset??

Another thing to say here is that the `DelegatingClassLoader.findPluginLoader()` is not only used for transformations and predicates but also for loading the connectors themselves. So to me, this also seems to break the versioning of the connectors. 

??And the affected plugins should eliminate their usage of static variables in order to be well behaved when the plugin.version is set??

Honestly, I'm not getting the point here. I expect that even with a correct management of `plugin.version`, the isolation must be preserved. What happens in the following situation where `plugin.path=opt/plugins/`:
{noformat}
opt/
  plugins/
    blue/
      foo-connector-1.8/
        foo-connector-1.8.jar
        foo-dependencies-1.0.jar
      foo-connector-1.9/
        foo-connector-1.9.jar
        foo-dependencies-1.1.jar
{noformat}
And I register a connector `foo-connector` with version 1.8 and SMT (suppose it is in the foo-dependencies) with version 1.1? Is this possible? In the same way, this breaks the isolation. Isn't it?
~~~~

5.

~~~~
1. I agree, I don't think it's a good pattern. But I think this is only a symptom that highlights the non-deterministic, and IMHO unsafe, way plugins are loaded as I try to explain in 2. / 3.

2. / 3. When looking for a plugin that matches the requested name and version, I think we should prioritize the instance in the classloader of the current connector. If multiple copies of the same plugin exists, the current logic loads the instance from the last plugin path directory ordered alphabetically, which to me is pretty much a random one as it depends on which plugins (and their names) you have installed. If you have a class in your JAR file, you don't want that class to be loaded from another JAR file.
~~~~

6.

~~~~
We did/should continue to have a policy of choosing the co-located plugin when all else is equal, see KAFKA-8819. This has unintentionally regressed with KIP-891 and should be fixed.

However my point was that this is a very brittle setup that will only work as long as a plugin and it's connector are not isolated from one another (in the same PluginClassLoader). As soon as they are isolated, or once someone uses plugin.version to select another instance, or perhaps once a newer version is installed, I would expect this to break again.

Mario, your example plugin path is an incorrect installation, because the plugins are all in the same class loader (corresponding to the blue directory). Only one version will be discovered, and it will be arbitrary based on filesystem order. It is very likely that the different versions of the classes collide and cause more serious problems, so Connect does not consider those cases (and it's also distinct from the bug being discussed here). That directly structure is meant to be used with `plugin.path=opt/plugins/blue/`.
~~~~

7.

~~~~
> That directly structure is meant to be used with `plugin.path=opt/plugins/blue/`.

Sorry, I wrongly typed the plugin.path. I intend to write `plugin.path=opt/plugins/blue/`

> As soon as they are isolated, or once someone uses plugin.version to select another instance, or perhaps once a newer version is installed, I would expect this to break again.

I still didn't get your point here. If a connector is isolated, then all other plugins that are listed in the same directly should be loaded with the same classloader. Isn't it?
~~~~

8.

~~~~
In your example, foo-connector-1.8 and foo-connector-1.9 are isolated from one another. They are each co-located/not-isolated from their dependencies and any contained SMTs.

If you dont specify plugin.version at all, you should get the 1.9 (latest) version of the connector, the co-located version of the dependencies (non-plugins), and the 1.1 (latest) version of the SMT. This is the good path, because the latest plugins are all present in the same location.

But there are several bad paths where static variables cannot be shared:
 * If you reference an SMT that is not co-located (installed in some other directory)
 * If you specify the 1.0 version of the SMT, the 1.9 version of the connector will be loaded because it's latest
 * If you specify version 1.8 of the connector, the 1.1 version of the SMT will be loaded because it's latest
 * Another plugin is installed with a later version (1.2) of the SMT
~~~~

9.

~~~~
Now it's clear. Thanks for the detailed explanation. 

I think this needs to be reported in the documentation since it's crucial.

Well, in that case, I have to say that the new versioning feature introduced more flexibility, which is good, but at the same time, you can have the same "strict" level of isolation as before, if you configure your versions to maintain it. Previously the isolation was achieved with the directory structure on the file system. 

In my example, if I want the full isolation for both connector versions, I need to specify for 
{noformat}
1.8: connector verions = 1.8 and SMT version = 1.0
19.: connector version = 1.9 and SMT version = 1.1
{noformat}
That said. I dunno if this full flexibility will be used so often since it can lead to strange behavior, but maybe this is just my limited experience view.
~~~~

10.

~~~~
I don't think you and I are using the word "isolation" in the same way, and maybe that's the cause of some of the friction here. The boundaries of isolation are still specified at installation time in the same way as they were before, only now users can choose older versions for each plugin.

It feels strange (that 1.8+1.1 and 1.9+1.0 are broken) because static field sharing adds context that operators have to keep in mind when doing upgrades. Users are going to want to focus on data-flow/semantics when performing upgrades, not debugging static field aliasing.

FWIW, static field sharing between plugins has never been in the mental model for Connect plugins, and the threading model/initialization order/lifecycle of plugins isn't well defined enough for static fields to be safe to use. That is why I want to push back strongly on this practice, while still admitting that we broke backwards compat and need to fix it.
~~~~

11.

~~~~
> I don't think you and I are using the word "isolation" in the same way, and maybe that's the cause of some of the friction here. The boundaries of isolation are still specified at installation time in the same way as they were before, only now users can choose older versions for each plugin.

For me, isolation means loading with the same classLoader. 

> It feels strange (that 1.8+1.1 and 1.9+1.0 are broken) because static field sharing adds context that operators have to keep in mind when doing upgrades. 

This could happen not only for static field sharing but for any breaking change. For example, imagine a source connector that renames some field in a non-backward-compatible manner (in a major release) and and SMT should adapt to that change. An operator has to keep in mind this right?

> FWIW, static field sharing between plugins has never been in the mental model for Connect plugins, and the threading model/initialization order/lifecycle of plugins isn't well defined enough for static fields to be safe to use. That is why I want to push back strongly on this practice,

As said previously, also before this issue, I had a bad feeling about this static field sharing, and now I have the proof that it was a design flaw. I'm currently looking for a different way to achieve it. That said, here the problem is another. 

If my understanding is correct, please correct me if I'm wrong, in KC version until 4.0 the isolation of the connector was done just with directory separation inside the `plugin.path` folder. Level 1 directories are isolated from each other. This is similar to what happens to war files in application servers, where each war is loaded with a different class loader. 

With KC 4.1 this is no more true, since all is guided by version and your level 1 directory has no more importance for class loader isolation since you could have a connector in a level 0 folder, let's say connector a, that could then use a plugin (SMT, Converter, etc) that is in another lavel 1 folder, so loaded with a different class loader, just because it is the one thath mathes the desidered version. 

If my understanding of the past and current status for me, this is a huge behavior change that shouldn't have happened in a minor release, and so we need to be as backward compatible as possible. 
~~~~

12.

~~~~
For me, two plugins are "isolated" when they have different classloaders. This allows them to pull in other dependencies completely independently.

You're right that this generalizes to any binary compatibility between classes. If you have classes in the same class loader, they need to be binary compatible and loadable together. Because this is difficult to manage, plugin isolation was implemented to permit plugins to be distributed independently from one another.

No your understanding of isolation is not correct, as the directory structure has not changed. A plugin path (config) is made up of plugin path elements (level 0). Each plugin path element contains multiple plugin locations (level 1). Each plugin location may contain multiple jars (level 2+). PluginClassLoaders are instantiated at level 1, and different jar files at level 2+ are included together in the same loader.

What has changed in a backwards-incompatible way is that when plugin.version is not specified, the copy in the connector is preferred. Now an arbitrary copy of the latest version is preferred. This should go back to how it was before.
~~~~

13.

~~~~
I think we now all agree on the issue. It's clear there's a regression in 4.1.0. We found it via some questionable logic used in Debezium but this is clearly a change in behavior that is not correct.

I've started working on a fix, unfortunately so far I've not found a quick/small fix. I hope to have something ready to review later this week.
~~~~

14.

~~~~
> PluginClassLoaders are instantiated at level 1, and different jar files at level 2+ are included together in the same loader.

[~gharris1727] This matches my understanding. But now, apart from when `plugin.version` is not specified, this will no more true. 

If you have this situation where the `plugin.path` is `opt/ plugins/ blue/`:
{noformat}
opt/
  plugins/
    blue/
      foo-connector-1.8/
        foo-connector-1.8.jar
        foo-dependencies-1.0.jar
      foo-connector-1.9/
        foo-connector-1.9.jar
        foo-dependencies-1.1.jar{noformat}
And based on what you said, in KC 4.0, I'll have a classloader for :
 * foo-connector-1.8 that loads the foo-connector-1.8.jar and foo-dependencies-1.0.jar
 * foo-connector-1.9 that loads the foo-connector-1.9.jar foo-dependencies-1.1.jar

With KC 4.1, if I do not specify any version, the expected behavior will be to have foo-connector-1.9.jar and foo-dependencies-1.1.jar used, and by coincidence, they are in the same level 1 folder. But I can set the version in a way that I could use foo-connector-1.8.jar and foo-dependencies-1.1.jar( suppose here there are SMT or any other plugin), leading to having a plugin loaded from a different class loader. Isn't it? 
~~~~

15.

~~~~
[~mimaison] Thanks for working on it. 
~~~~

16.

~~~~
Pointing out some more details here. While classloading transformations or predicates we did make a conscious effort to ensure that, in the absence of any provided version, we try to load them using the classloader of the connector it is associated with. This happens [here|https://github.com/apache/kafka/blob/59f51fb3cac66d8096e647eb90be6c5e4ba9f485/connect/runtime/src/main/java/org/apache/kafka/connect/runtime/ConnectorConfig.java#L418] where we pass in the plugin loader for the connector class to the [newPlugin|https://github.com/apache/kafka/blob/59f51fb3cac66d8096e647eb90be6c5e4ba9f485/connect/runtime/src/main/java/org/apache/kafka/connect/runtime/isolation/Plugins.java#L376] method, which should load the transformation using the PluginClassLoader of the connector. If the connector and transformation is colocated in the same path this should have ensured the same isolation behaviour as the previous connect version. 
~~~~

17.

~~~~
Yes we have all the data in getTransformationOrPredicate() but it's not used correctly in newPlugin(). From this path, range is never null, even if it's not set in the configuration because Connect always injects a default version for transformations and predicates in EnrichablePlugin.enrich(). So newPlugin() ends up not using the classloader passed from getTransformationOrPredicate().
~~~~

18.

~~~~
[~snehashisp] It would be great if you could take a look at https://github.com/apache/kafka/pull/20675. Thanks
~~~~

19.

~~~~
Hey [~mimaison] , just touching base regarding the 4.1.1 cut. Do we have an idea of how far are we with the PR/fix? Thanks!
~~~~

20.

~~~~
[~lianetm] I put a PR out (https://github.com/apache/kafka/pull/20675) last week. Now we're waiting for reviews. 
~~~~

21.

~~~~
[~lianetm] Sorry for the delay. The fix is merged on trunk and I backported it to 4.1 too.
~~~~

22.

~~~~
Great, thanks!
~~~~

---

## KAFKA-19930: GlobalThread fails with NPE trying to use unsupported ProcessingExceptionHandler

https://issues.apache.org/jira/browse/KAFKA-19930

Given fix versions: 3.9.2, 4.0.2, 4.1.2, 4.2.0
JIRA affects (masked from the system): 3.9.0

- `KAFKA-19930@3.9.0`: config 3.9.0, metadata answer **affected** (listed_affected)
- `KAFKA-19930@3.8.1`: config 3.8.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
We introduced a new `ProcessingExceptionHandler` with [KIP-1033|https://cwiki.apache.org/confluence/display/KAFKA/KIP-1033%3A+Add+Kafka+Streams+exception+handler+for+exceptions+occurring+during+processing] which was not intended to work with global Processors.

While we might want to change this, and potentially include the GlobalThread (even if it would be more difficult for the follow up DLQ work, because the GlobalThread does not have a producer...), there is a real bug in the implementation: if a `Processor` on the global thread throws an exception, we try to use the processing exception handler, however, it was never set up, and we fail with a NPE trying to call `processingExceptionHandler.handlerError(...)` inside `ProcessorNode#process(...)`.

This ticket is really just about fixing the NPE, and check if the handler is set, and if not, just rethrow any exception bubbling up from the user code, and let the global thread die (ie, let the user exception bubble up into the uncaught exception handler).

We should also update the docs, calling out that this handler does not apply to the global thread.

If we want to make the processing-exception-handler work properly with the global thread, we should file a new ticket, as it would require proper design.
~~~~

### Comments (1)

1.

~~~~
[~mjsax]  can i pick this up ?
~~~~

---

## KAFKA-19932: AdminClient throws TimeoutException when underlying cause is OutOfMemoryError

https://issues.apache.org/jira/browse/KAFKA-19932

Given fix versions: 4.3.0
JIRA affects (masked from the system): 4.1.0

- `KAFKA-19932@4.1.0`: config 4.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-19932@4.0.2`: config 4.0.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
An issue occurred wherein the admin client was frequently returning timeout errors. On closer inspection, it was found that the instance on which the admin client was running had very little available heap space and was throwing {{OutOfMemoryError}} pretty consistently.

The fix here is to ensure that the admin client properly propagates the underlying error instead of masking it as a timeout or something else.
~~~~

### Comments (6)

1.

~~~~
[~kirktrue]  can I pick this up ?
~~~~

2.

~~~~
[~goyarpit]-Absolutely :)
~~~~

3.

~~~~
[~goyarpit]—for release planning, do you have an estimate for a fix? Thanks!
~~~~

4.

~~~~
[~kirktrue]  I have not started it , but I will raise PR for the same by 13th december. Its 2-3 dats of work probably. Will that work ?
~~~~

5.

~~~~
https://github.com/apache/kafka/pull/21117/files
~~~~

6.

~~~~
[~kirktrue]  can you review it.
~~~~

---

## KAFKA-20635: Spurious "Writing records..." failed errors in the group coordinator after partition leadership change

https://issues.apache.org/jira/browse/KAFKA-20635

Given fix versions: 4.0.3, 4.1.3, 4.2.2, 4.3.1, 4.4.0
JIRA affects (masked from the system): 4.0.0, 4.1.0, 4.2.0, 4.3.0

- `KAFKA-20635@4.1.0`: config 4.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-20635@3.9.2`: config 3.9.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
During routine __consumer_offsets partition leadership changes, the group coordinator spams ERROR-level logs for every in-flight write at the moment of transition:

{noformat}
[GroupCoordinator id=N] Writing records to __consumer_offsets-N failed due to: For requests intended only for the leader, this error indicates that the broker is not the current leader ...
[GroupCoordinator id=N] Execution of FlushBatch failed due to For requests intended only for the leader, this error indicates that the broker is not the current leader ...
{noformat}

These appear on the group coordinator that lost leadership and last for the duration of the in-flight batch queue. The behavior is correct — NotLeaderOrFollowerException propagates through failCurrentBatch to the deferred events and is mapped to NOT_COORDINATOR for clients via CoordinatorOperationExceptionHelper, so clients retry against the new coordinator. This is purely a logging-noise issue.

Same root cause as KAFKA-20634: the partition transitions to follower synchronously while the coordinator unload is async. In that window, partitionWriter.append calls replicaManager.appendRecordsToLeader which legitimately rejects writes for a partition no longer led by this broker. The exception is expected — but it gets logged at ERROR by the catch block in flushCurrentBatch and by CoordinatorInternalEvent.complete.
~~~~

---

## KAFKA-20685: EOS: checkpoint file written at restoration completion persists through RUNNING, state wipe is skipped after unclean crash

https://issues.apache.org/jira/browse/KAFKA-20685

Given fix versions: 4.1.3, 4.2.2
JIRA affects (masked from the system): 3.8.0

- `KAFKA-20685@3.8.0`: config 3.8.0, metadata answer **affected** (listed_affected)
- `KAFKA-20685@3.7.2`: config 3.7.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 4.1.2, 4.3.0, 4.3, 4.2.2, 4.1.3, 4.2, 4.1, 3.8.0, 3.8

### Description

~~~~
While crash testing our Streams app I found behavior that doesn't match the documented EOS state store model. Reproduced twice with SIGKILL tests, details below.

h3. Observed behavior (reproducible)

# After restoration completes, a {{.checkpoint}} file exists in the task directory and stays there unchanged for the whole RUNNING session. Frozen restore-time offsets, mtime never moves, verified on disk while processing around 16k rec/s.
# SIGKILL during active processing, zero grace period. On restart the instance finds that stale checkpoint, logs "State store X initialized from checkpoint with offset ...", no TaskCorruptedException, no wipe, and just replays the changelog tail (81,732 records in our test). Happened consistently across two independent kills.
# The wipe path ("State store did not find checkpoint offsets while stores are not empty...") only fired in a different test where the crash happened during restoration itself, before any checkpoint entry existed.

h3. Expected behavior

Under EOS an unclean crash during RUNNING should hit the no-checkpoint path, throw TaskCorruptedException and wipe local state, because the store may contain uncommitted writes. RocksDBStore disables the WAL and Streams doesn't flush on commit under EOS, so RocksDB background memtable flushes can persist writes from a transaction that later gets aborted. The flushes don't know anything about transaction boundaries.

h3. Code paths (verified on the 4.1.2 tag)

* {{DefaultStateUpdater.maybeCompleteRestoration}} (line 678) calls {{task.maybeCheckpoint(true)}} (line 683) on restore completion with no EOS condition. {{DefaultStateUpdater.maybeCheckpointTasks}} (line 712) also calls {{task.maybeCheckpoint(false)}} (line 724) for all updating tasks every commit interval, again with no EOS condition.
* Nothing deletes that file on the restored to RUNNING transition. {{StreamTask.completeRestoration}} writes its own checkpoint only if {{!eosEnabled}}, which suggests the intent was that no checkpoint should exist past that point under EOS. The file written by the state updater just stays.
* During RUNNING under EOS, {{StreamTask.postCommit}} only checkpoints when {{enforceCheckpoint==true}} (suspend/close/rebalance), so the stale file never gets refreshed or removed in steady state.
* The only delete sites I could find: init time ({{ProcessorStateManager.initializeStoreOffsetsFromCheckpoint}}), resume from SUSPENDED ({{deleteCheckPointFileIfEOSEnabled}}, added by KAFKA-10362), and {{DefaultStateUpdater.removeCheckpointForCorruptedTask}}.

Net effect: the restoration-completion checkpoint survives the entire RUNNING session and gets trusted at the next init, so a crash during RUNNING silently skips the EOS wipe.

h3. Why this can violate EOS

The tail replay from the stale checkpoint runs read_committed, so it skips aborted records and cannot clean up uncommitted writes that a background memtable flush already pushed to SST files. Reprocessing of the uncommitted input offsets overwrites the leftover values only when the topology is deterministic and input record driven. State written by wall clock punctuators is never regenerated. And read-before-write logic is the worst case: dedup on an ID can read the leftover uncommitted value and silently skip the redelivered record, so exactly-once becomes zero-times with no error surfaced anywhere.

KIP-892's motivation section states that under EOS, crash failures must wipe task state because data is written to the store before the changelog commit completes. The observed behavior bypasses that wipe.

h3. History

Before the state updater became the default (KAFKA-10199, enabled by default via PR #16107), no checkpoint existed during RUNNING under EOS, so a RUNNING crash reliably triggered the wipe. The restoration-time checkpoint was added deliberately in PR #12279 (motivated by KAFKA-12634) with a safety argument scoped to crashes during restoration, where over-restore is idempotent. That argument doesn't extend to the RUNNING phase.

Reproduced on 4.1.2. Not yet tested on 4.3.0 where KIP-1035 reworks the offset storage.

h3. Related

KAFKA-10199, KAFKA-12634 (introduced restoration checkpointing), KAFKA-10362 (precedent: checkpoint deleted on resume under EOS for the same class of risk), KAFKA-16017 (related but different mechanism), KIP-892 (the durable fix, not yet released).

h3. Proposed fix

On the restored to RUNNING transition under EOS, delete the checkpoint file, mirroring what KAFKA-10362 did on the resume path with {{deleteCheckPointFileIfEOSEnabled()}}. This restores the invariant that no checkpoint exists during RUNNING under EOS. The cost is full restores after unclean RUNNING crashes, which is the cost KIP-892 eventually removes properly.
~~~~

### Comments (6)

1.

~~~~
I'm happy to take this up and submit a PR if the maintainers agree with the proposed fix direction (or whatever direction is preferred). if it's okay , Could a committer add me to the contributors list so the ticket can be assigned to me? JIRA username: zoro3010200
~~~~

2.

~~~~
Thanks for reporting this [~zoro30102000] 

After doing some research the good news is that 4.3+ is not affected — not directly because we moved away from checkpoint files, but because KIP-1035 replaced the checkpoint-absence heuristic with a per-store open/closed status marker checked under EOS at store-open. A hard crash never writes the "closed" marker, so the store reopens in "open" state → TaskCorruptedException → wipe + restore.

 

Your proposed fix sounds good to me, I'd say go ahead with a PR.  If you choose to do so, please self-assign this ticket.
~~~~

3.

~~~~
{quote}Could a committer add me to the contributors list so the ticket can be assigned to me? JIRA username: zoro3010200
{quote}
Done.

Thanks for reporting. Sounds pretty bad...

Glad to hear that 4.3 is not affected, but we should fix it for 4.2.2 release (not sure if we will get a 4.1.3 one...)
~~~~

4.

~~~~
Thanks [~bbejeck]  and [~mjsax]  . Self-assigned.

I'll open the PR against the 4.2 branch. Plan is to mirror what KAFKA-10362 did, delete the checkpoint file when an EOS active task moves from restored to RUNNING, plus a test . If a 4.1.3 ever happens happy to do the cherry-pick to 4.1 too.

One question, should Affects Version/s be 3.8.0 - 4.2.x instead of just 4.1.2? The state updater is default since 3.8 so the same behavior should be there across that whole range.
~~~~

5.

~~~~
Thanks Bill and Matthias. I verified the 4.3 and trunk behavior before writing the patch: built in stores are covered by the KIP-1035 status marker as Bill described, and custom stores that do not manage their own offsets are covered since KAFKA-19712, which writes the legacy checkpoint file only under at_least_once and deletes it at init under EOS.

So there is nothing to fix on trunk or 4.3 and the PR targets the 4.2 branch:
https://github.com/apache/kafka/pull/22548. 

The fix deletes the checkpoint when an EOS task completes restoration, mirroring the KAFKA-10362 resume path. Happy to prepare the same patch for 4.1 if a 4.1.3 release is planned.
~~~~

6.

~~~~
[~zoro30102000] appologies for the delayed repsonse, it's merged into 4.2 branch.  -I'm not sure we'll do a another 4.1 release but if you want to do PR against 4.1 that's OK, just so you know about the release-

NM I cherry-picked to 4.1 thanks again for the fix!
~~~~

---

## KAFKA-20711: Streams task restore-remaining-records metric never reaches 0

https://issues.apache.org/jira/browse/KAFKA-20711

Given fix versions: 4.2.2, 4.3.2, 4.4.0
JIRA affects (masked from the system): 4.3.0

- `KAFKA-20711@4.3.0`: config 4.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-20711@4.2.1`: config 4.2.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
The Kafka Streams Task-level metric {{restore-remaining-records}} is intended to track the total number of records that still need to be restored.

This metric is inaccurate, never actually dropping to 0 for fully restored tasks, and always showing values substantially higher than reality, especially under EOS.

The root-cause is that the metric is initialized with a total number of records to restored derived as {{logEndOffset - committedOffset}}, using a READ_UNCOMMITTED consumer.

This offset range naturally includes uncommitted records and transaction markers, as well as offsets that have been compacted away, in addition to the actual records to restore.

When decrementing the metric during restore, we decrement by the actual number of (committed) records that were restored. Since this excludes uncommitted records and transaction markers, we will never decrement the metric by the total it was initialized with.

I have a fix that I will raise a PR for.
~~~~

---

## KAFKA-20721: Streams: "Task not found in the state updater. This indicates a bug." after a state updater remove times out during cold start rebalancing

https://issues.apache.org/jira/browse/KAFKA-20721

Given fix versions: 4.3.2, 4.4.0
JIRA affects (masked from the system): 4.1.2, 4.3.0

- `KAFKA-20721@4.3.0`: config 4.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-20721@4.1.1`: config 4.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 4.1.2, 4.3.0, 4.2, 4.2.1, 4.4, 4.4.0, 4.3.2, 4.3.1

### Description

~~~~
Note (2026-06-22): an earlier revision of this ticket described a pause/resume duplicate listing mechanism. That was wrong for this report; the original production occurrence had no pause/resume. The pause/resume duplicate listing is tracked separately in KAFKA-20724. This description is reverted to the original crash, which matches KAFKA-20456.

A StreamThread dies during cold start rebalancing with:

java.lang.IllegalStateException: Task X_Y was not found in the state updater. This indicates a bug.
    at TaskManager.waitForFuture(TaskManager.java:711)
    at TaskManager.addToTasksToClose(TaskManager.java:685)
    at TaskManager.handleTasksInStateUpdater(TaskManager.java:640)
    at TaskManager.handleAssignment(TaskManager.java:378)
    -> KafkaException: User rebalance callback throws an error -> SHUTDOWN_CLIENT

Environment: Kafka Streams 4.1.2, exactly_once_v2, several stateful instances, large RocksDB state, cold start with heavy rebalancing. The application does not call pause() or resume().

Mechanism (matches KAFKA-20456): during the rebalance, a remove issued from revokeTasksInStateUpdater waits in TaskManager.waitForFuture, which has a hardcoded 5 minute timeout. The state updater is stalled (restore under load), so the get() times out and waitForFuture returns null after logging "The state updater wasn't able to remove task X in time. The state updater thread may be dead." The revoked partitions are already removed from
remainingRevokedPartitions before that wait, so the task is not suspended or re tracked. The task is still visible in stateUpdater.tasks() because a pending REMOVE action is not included in the snapshot (only pending ADD is). The following onAssignment then enumerates tasks(), finds the task absent from the new assignment, and enqueues a second remove via handleTasksInStateUpdater. When the stalled state updater finally drains its action queue (FIFO), the first remove succeeds and the second finds the task in none of its collections, so DefaultStateUpdater.removeTask
completes the future with null and logs "Task X could not be removed from the state updater because the state updater does not own this task." waitForFuture in addToTasksToClose receives that null and throws the ISE.

Production evidence: four occurrences on 4.1.2, all the same order, the timeout WARN first, then 13 seconds to 2 minutes later the "does not own this task" WARN, then the ISE. No STANDBY_UPDATING, no Duplicate key, no pause or resume in any of them.

Relationship to 4.3.0: TaskManager.waitForFuture is identical in 4.1.2, 4.3.0 and trunk (same 5 minute timeout, same throw on a null completion). The KAFKA-20456 changes present in 4.3.0 are the two RocksDB ones (lighter offsets column family, avoid persisting closed state), which reduce the stalls that trigger the timeout. The timeout bound and the leaked task cleanup are not in 4.3.0 or trunk. So 4.3.0 reduces the likelihood but does not remove the timeout to duplicate remove to ISE path. No recurrence on 4.3.0 so far, but the observation window is short.

Caveat on the trigger: we did not capture a thread dump or GC log at the stall, so we can confirm the state updater stalled past 5 minutes but not that the staller was RocksDB specifically rather than, for example, a long GC pause.

Affects version: 4.1.2 (observed). The same code path exists in 4.2.x, 4.3.0 and trunk.

Suggested direction: bound the waitForFuture timeout and clean up the leaked task when the remove times out, so a slow remove does not leave a task that is later removed twice. The ISE should stay; it is correctly catching the inconsistency.
~~~~

### Comments (12)

1.

~~~~
drainRestoredActiveTasks and revokeTasksInStateUpdater are both on the StreamThread. How can there be a race between them? 

I think you have hit a real bug, but the mechanism described in this ticket doesn't seem possible, at least looking from a high-level.

The reproduction only shows that you cannot run drainRestoredActiveTasks and revokeTasksInStateUpdater from different threads, but this is expected, and doesn't show a bug. Have you reproduced the bug in a real application in all the versions (4.1.2, 4.2.1, 4.3.0 and trunk), or only your integration tests.
~~~~

2.

~~~~
Could you provide the full logs of the real occurrence of the bug (not the unit test) with DEBUG logs? 

I'm not totally against turning the `IllegalStateException` into warn+skip as you suggest, but there may be a real bug lurking here. And I think [~cadonna] introduced the ISE specifically to detect bugs like that.

Can you also adjust the "affects version" to the version where you can produce the real occurrence of the bug?
~~~~

3.

~~~~
[~lucasbru]  thanks for pushing back :) , 
Agree , the drain versus revoke mechanism in the description is wrong. 

that drainRestoredActiveTasks and revokeTasksInStateUpdater both run on the StreamThread, so they cannot interleave, and my first tests only showed that calling those two methods from different threads returns null, which is expected and not a bug. I withdraw that mechanism.

but i ran thru few things again , here is what I now believe is happening, with a reproduction.

Root cause: DefaultStateUpdater.tasks() can return the same TaskId twice. Two things combine. First, tasks() takes its snapshot under executeWithQueuesLocked, which holds tasksAndActionsLock, restoredActiveTasksLock and exceptionsAndFailedTasksLock, but not the updatingTasks or pausedTasks maps. pauseTask does pausedTasks.put(id) then updatingTasks.remove(id), and resumeTask does the reverse, so for a short window the task is in both maps and streamOfTasks() lists it twice. Second, ReadOnlyTask has no equals/hashCode, so the returned Set does not collapse the two wrappers.

Once tasks() returns a duplicate, a caller that does one remove per entry removes the same task twice. The first remove succeeds, the second reaches removeTask, finds the task in none of the four collections, and completes the future with null. waitForFuture then throws "Task X was not found in the state updater. This indicates a bug." In my runs it comes through shutdownStateUpdater -> addToTasksToClose. The same duplicate also breaks
TaskManager.allTasks(), which collects with Collectors.toMap(Task::id, ...) and throws IllegalStateException: Duplicate key, killing the StreamThread in runLoop.

On your question about a real application versus unit tests: this is a small standalone Streams application, several KafkaStreams instances in one JVM, exactly_once_v2, against a real broker, not a unit test. The trigger is cold start churn plus KafkaStreams.pause()/resume(). The duplicate window is normally sub microsecond, so to make it deterministic I widened that existing window with a Byteman rule that sleeps right after the put in pauseTask and resumeTask (no logic change, it only stretches the gap that is already there). With that, the ISE and the Duplicate key error both fire within a couple of minutes. I reproduced it this way on 4.1.2 and 4.3.0; trunk has the same code on this path. With pause/resume disabled I get no duplicates and no crash at all, even under aggressive kill all and restart all churn, which matches the window being in pauseTask/resumeTask.

I attached the DEBUG logs from one run (TaskManager, DefaultStateUpdater and StoreChangelogReader at DEBUG), the reproducer (SuBugPoc.java, pom.xml) and the Byteman rule. In the DEBUG log you can see the same task id present on the updating and the paused side at the same time, then "could not be removed from the state updater because the
state updater does not own this task", then the ISE.

On affects version: I reproduced it on 4.1.2 and 4.3.0, so I set those. 4.2.x and trunk carry the same pauseTask/resumeTask and ReadOnlyTask code, so they look affected by inspection as well.

On warn plus skip: I agree with you, I would not just downgrade the ISE. The throw is doing its job. The fix probably belongs at the source so tasks() never returns a duplicate, for example dedupe by task id before wrapping, or give ReadOnlyTask equals/hashCode based on the task id, or make the pause/resume transition atomic with respect to tasks(). I left the ISE as is.

A few related notes from the same digging, in case they help triage:

-> KAFKA-17402 is the same family (tasks() returning a duplicate, seen there as shouldGetTasksFromRestoredActiveTasks counting 3 instead of 2). Its fix made the restore completion transition atomic but did not touch pauseTask/resumeTask, which is the path here.
-> My original one off production occurrence was on 4.1.2 with no pause/resume and very large RocksDB state, which looks closer to KAFKA-20456 (the state updater stalling and waitForFuture timing out), already fixed in 4.3.0. So the production incident and this pause/resume reproduction may be two different routes to the same exception.
-> Separate crash, flagging it here since it shows up under the same pause/resume churn: resumeTask calls  changelogReader.transitToUpdateStandby() with no state guard, and that method throws if the reader is not ACTIVE_RESTORING, so under churn it can kill the StreamThread with "The changelog reader is not restoring active tasks (is STANDBY_UPDATING)...". That path was the subject of KAFKA-17946, but the fix there (PR #18253) was test stabilization and did not change resumeTask or transitToUpdateStandby, so it looks still reachable on 4.3.0 and trunk. I will add the detail on KAFKA-17946; raising it here in case you would rather track it differently.


FYI updated the ticket too on the same
~~~~

4.

~~~~
Hey, while digging into you original bug report, I also noticed the pause/resume bug, and filed https://issues.apache.org/jira/browse/KAFKA-20721

But I created a separate ticket for it. Pause/resume is a rarely used feature, triggering it at the right time to trigger this bug should be very very rare. Still worth a fix, but not the problem that you originally reported (no pause/resume was every mentioned).

I don't agree that we should just repurpose you original report for something that you didn't really do in (pausing/resuming). 

Can you try reproducing your problem with 4.3.0? This may be a recurrence of https://issues.apache.org/jira/browse/KAFKA-20456. I don't think the 5 minute timeout is correct here, as it can lead to duplication of tasks -> which in turn leads to duplication of removals later on, triggering this exception

Another bug that comes to mind is https://issues.apache.org/jira/browse/KAFKA-19853

Here, long RocksDB stalls caused the transaction timeout to be triggered. But after a cold start, it wouldn't happen.

I think if you are seeing `The state updater wasn't able to remove task` it's likely a recurrence of https://issues.apache.org/jira/browse/KAFKA-20456.

 
~~~~

5.

~~~~
[~lucasbru] Thanks Lucas, thanks for the nudge. Yyes ur right on both counts: the pause/resume rewrite did not belong on this ticket and the original crash had no pause/resume. I pulled the production logs for the original occurrence and it matches KAFKA-20456, so I have reverted the description back to that original crash.

The app is a Kafka Streams 4.1.2 service on exactly_once_v2, several instances, that crashed during cold start rebalancing. It never calls pause() or resume(). I found four occurrences and every one follows the same order:

1. A remove times out in the revoke path:
WARN TaskManager: The state updater wasn't able to remove task 1_4 in time. The state updater thread may be dead.
  at TaskManager.waitForFuture(TaskManager.java:709)
  at TaskManager.revokeTasksInStateUpdater(TaskManager.java:1220)
  at TaskManager.handleRevocation(TaskManager.java:1119)
2. About 13 seconds to 2 minutes later the state updater finally runs a now duplicate remove for the same task and finds it gone:
WARN DefaultStateUpdater: Task 1_4 could not be removed from the state updater because the state updater does not
own this task.
3. That null completion is thrown as the ISE, this time from the assignment close path:
IllegalStateException: Task 1_4 was not found in the state updater. This indicates a bug.
  at TaskManager.waitForFuture(TaskManager.java:711)
  at TaskManager.addToTasksToClose(TaskManager.java:685)
  at TaskManager.handleAssignment(TaskManager.java:378)
  -> User rebalance callback throws an error -> SHUTDOWN_CLIENT

So it is exactly what you described: the 5 minute waitForFuture times out, the task is left behind, the next rebalance handling issues a second remove for it, and that second remove completes the future with null, which becomes the ISE. The timeout WARN comes first in all four cases, so the trigger is a state updater stall longer than the 5 minute timeout, not pause/resume.

On the trigger itself: it was a cold start with large RocksDB state, and we have not seen it since moving the app to 4.3.0, which carries the two RocksDB changes from KAFKA-20456 (the lighter offsets column family and avoiding persisting closed state). I want to be precise though. I did not capture a thread dump or GC log at the moment of the stall, so I can say the state updater stalled past 5 minutes, but I cannot prove the staller was RocksDB specifically rather than, say, a long GC pause. The "thread may be dead" message only tells us the get() timed out.

One thing I checked on the fix side: TaskManager.waitForFuture is identical in 4.1.2, 4.3.0 and current trunk (same hardcoded future.get(5, TimeUnit.MINUTES), same throw on a null completion). The two KAFKA-20456 commits that shipped in 4.3.0 are the RocksDB ones; the timeout bound and the leaked task cleanup are not in 4.3.0 or trunk. So 4.3.0 makes the stall less likely but the timeout to duplicate remove to ISE path is still present. The 4.3.0 run has been clean so far, but the window is short, so I would not read much into that yet.

I set affects version to 4.1.2, where the real occurrence is. Happy to do whatever is cleanest for tracking: close this as a duplicate of KAFKA-20456, or keep it open to track that the timeout and duplicate remove protocol is still unfixed in 4.3.0 and trunk. Your call.

Separately, I have a deterministic pause/resume reproduction for the duplicate listing crash (Byteman widening the put before remove window in pauseTask and resumeTask). I will add it to KAFKA-20724, since that is the right home for it.
~~~~

6.

~~~~
Okay. I'd still think we should disable this 5 minute timeout on the future which was introduced in 

[https://github.com/apache/kafka/pull/20767]

If removing tasks from the state updater takes more than 5 minutes, we are going to have a problem either way because we are going to exceed rebalance timeout, at least if the option is default.

But we shouldn't "fix" it by just not removing a task, which can lead to duplicate tasks in the end, and other problems further down in the life cycle.

If we are going to put a timeout there, it should match the rebalance timeout and we should treat it fatally, I think.
~~~~

7.

~~~~
Agreed and I think one more piece has to go with it.

That timeout comes from KAFKA-19831 (#20767) right. It was added so shutdownStateUpdater would not hang when the state updater thread is dead and the hang it avoids is true: when the state updater thread exits, run() goes through its finally and calls clearInputQueue(), which clears tasksAndActions without completing the pending removal futures. Any remove() still queued at that point never completes, so a plain future.get() blocks forever. #20767 covered that with future.get(5, TimeUnit.MINUTES).

The problem is the recovery it chose. On TimeoutException waitForFuture logs the warning and returns null, and both callers, getNonFailedTasks and addToTasksToClose, filter the nulls out. So the task is dropped on the StreamThread side while its remove is still queued in the updater.
On the next assignment the task is still in stateUpdater.tasks(), a second remove is enqueued, that one finds the task in none of the collections and completes the future with null and waitForFuture turns that null into "was not found ... This indicates a bug". That is the
production ordering exactly: timeout warning, then "could not be removed ... does not own this task", then the ISE.

So I do not think the timeout can just be dropped on its own or we are back to the original hang on a dead updater. What I would suggest:

1. Make the state updater complete its outstanding removal futures when the thread stops. In run()'s finally, before clearing tasksAndActions, complete every pending REMOVE future exceptionally with the failure that stopped the thread. After that a dead updater no longer leaves a future hanging, which removes the reason the timeout existed.

2. Stop returning null from waitForFuture on timeout. A removal then has three outcomes: a real result, an exceptional completion that we route to a dirty close, or future.complete(null) from removeTask, which is the genuine "task is not here" case and should keep throwing the ISE so we still catch the pause/resume duplicate from KAFKA-20724.

3. If we still want a backstop for a state updater that is alive but stuck, bound it to the rebalance timeout instead of a fixed 5 minutes and treat it fatally, as you said. A removal that cannot finish within the rebalance timeout means we are out of the group anyway, so failing the thread cleanly and letting it rejoin is correct and never leaves a half removed task behind. The one wrinkle is shutdownStateUpdater, which already force closes whatever is left after its own timeout, so the fatal behavior should sit on the live revoke and assignment paths, not on shutdown.

Net effectwill be => a removal is always either completed or fails the thread cleanly, never silently skipped. I am happy to put up a PR along these lines. One question for the backstop in 3: should the rebalance timeout be read from the configured value, since TaskManager does not hold it tod
~~~~

8.

~~~~
>So the task is dropped on the StreamThread side while its remove is still queued in the updater.

we close them dirty afterwards: [https://github.com/apache/kafka/blob/trunk/streams/src/main/java/org/apache/kafka/streams/processor/internals/TaskManager.java#L1515-L1518]

 

I dug deeper, it looks like the problem may be because we update task collections without acquiring the lock here [https://github.com/apache/kafka/blob/trunk/streams/src/main/java/org/apache/kafka/streams/processor/internals/DefaultStateUpdater.java#L679-L680] and here [https://github.com/apache/kafka/blob/trunk/streams/src/main/java/org/apache/kafka/streams/processor/internals/DefaultStateUpdater.java#L694-L695.]

now it's possible to list values right in between the calls which will lead to duplicates in `tasks()`

I will try to write an integration test that reproduces it
~~~~

9.

~~~~
[~zoro30102000] I think you proposal makes sense. If we can complete all futures during shutdown, we should not block here when we close state updater.

I thought about the timeout. It is fairly difficult to cleanly deal with tasks that we cannot remove. We have to make sure that the rocksdb locks are released. I wonder if it would just introduce extra complications to have the timeout. It must be a reasonable to expect the state updater to not just live lock. If the state updater does block for more than the rebalance timeout due to rocksdb, this can be fixed by increasing the rebalance timeout or tuning the rocksdb configurations. But we'd cleanly solve it by rejoining the group. if the state updater crashes, it must take the stream thread down with it. 

[~nikita-shupletsov] these races are valid but they only affect the pausing/resuming functionality and are much less severe than the bug in this ticket. I created a separate ticket for them, see above.

Full disclosure I will be on leave starting next week and may not be able to follow up, but given the severity, I am sure [~mjsax] or [~bbejeck] would be available to review a fix PR.
~~~~

10.

~~~~
yeah, I found a separate problem. I  created another ticket for that: https://issues.apache.org/jira/browse/KAFKA-20764



for this problem I agree that we should switch from timing out to killing the stream thread when the state updater thread dies
~~~~

11.

~~~~
Hi [~zoro30102000] 
we would like to get it fixed in 4.4, and as we are approaching the code frieze, I am wondering if you would be able to get it by then?
if not, do you mind if I take it?
~~~~

12.

~~~~
[~nikita-shupletsov] sorry I never got back to you on this, I was not available for a while and missed your question. Thanks for taking it over and getting it into 4.4.0 and 4.3.2. I have tested 4.3.2 since: the "lock hold by current process" store errors we were seeing on 4.2.1 and 4.3.1 after the five minute removal timeout are gone, it now waits for the removal instead.
~~~~

---

## KAFKA-20746: NPE in MetadataCache#toCluster

https://issues.apache.org/jira/browse/KAFKA-20746

Given fix versions: 4.2.2, 4.3.2, 4.4.0
JIRA affects (masked from the system): 4.2.0, 4.3.1

- `KAFKA-20746@4.3.1`: config 4.3.1, metadata answer **affected** (listed_affected)
- `KAFKA-20746@4.1.2`: config 4.1.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 4.3.1, 4.2, 4.3

### Description

~~~~
In KAFKA-18225, we fix a bug to allow `ClientQuotaCallback#updateClusterMetadata` to be supported in KRaft mode. But the cluster object generated in MetadataCache could cause NPE. See [https://github.com/strimzi/kafka-quotas-plugin/issues/71] for more info.

 

I think the root cause is that in toCluster method, we filter out the fenced brokers to build brokerToNodes map [here|https://github.com/apache/kafka/blob/4.3.1/metadata/src/main/java/org/apache/kafka/metadata/MetadataCache.java#L151-L154]. But later, we want to get all the replicas info, which include the fenced replicas, via the filtered brokerToNodes map. So it causes the NPE. That's my assumption because from the original reported bug, we don't have other info. But it's a possible way to cause NPE. We should also think if there is other possibility to cause NPE here. 
~~~~

### Comments (3)

1.

~~~~
Actually I've filed pr to fix this issue before, see [https://github.com/apache/kafka/pull/19803.]

I'll file another pr to focus on fixing the NPE part. But looks like strimzi is using {{updateClusterMetadata?}}

{{{{Perhaps we should consider this KIP: https://cwiki.apache.org/confluence/spaces/KAFKA/pages/350783948/KIP-1162+Redesign+ClientQuotaCallback+updateClusterMetadata again}}}}
~~~~

2.

~~~~
> 
{{{{{}Perhaps we should consider this KIP: [https://cwiki.apache.org/confluence/spaces/KAFKA/pages/350783948/KIP-1162+Redesign+ClientQuotaCallback+updateClusterMetadata] again{}}}}}
[Edit|https://issues.apache.org/jira/secure/EditComment!default.jspa?id=13656000&commentId=18092250] [|https://issues.apache.org/jira/secure/DeleteComment!default.jspa?id=13656000&commentId=18092250]
I'll bring this to our team and discuss about it. Thanks [~brandboat] !
~~~~

3.

~~~~
Backport PRs:

4.2: [#22800|https://github.com/apache/kafka/pull/22800]
4.3: [#22801|https://github.com/apache/kafka/pull/22801]
~~~~

---

## KAFKA-20765: AsyncKafkaConsumer: OffsetFetch retry on STALE_MEMBER_EPOCH can spin in dedup loop and never complete the application future

https://issues.apache.org/jira/browse/KAFKA-20765

Given fix versions: 4.3.2, 4.4.0
JIRA affects (masked from the system): 4.3.0

- `KAFKA-20765@4.3.0`: config 4.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-20765@4.2.2`: config 4.2.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
AsyncKafkaConsumer: OffsetFetch retry on STALE_MEMBER_EPOCH can spin in dedup loop and never complete the application future

When an in-flight OffsetFetch fails with STALE_MEMBER_EPOCH and the member already knows a newer epoch, CommitRequestManager retries the request. If a duplicated fetch for the same partitions was chained onto the failed request, the retry can be deduplicated against the *already-completed* request: PendingRequests.addOffsetFetchRequest matches duplicates only by partitions (sameRequest) and does not check whether the matched request is still pending. A completed request may still appear in the buffers while its completion callbacks run, because buffer removal is itself a completion callback and CompletableFuture dependents run LIFO.

Chaining onto a completed future fails the retry immediately and synchronously, which triggers another retry, another dedup, and so on — a tight loop with these symptoms:
- WARN "A duplicated, inflight, request was identified, but unable to find it in the outbound buffer" repeated hundreds of times within milliseconds,
- StackOverflowError surfacing in OffsetFetchRequestState.toString(),
- no OffsetFetch with the new epoch is ever sent (the epoch is stamped at send time, which the loop never reaches),
- the application-level future is never completed.

In Kafka Streams with the streams rebalance protocol (KIP-1071) this blocks the stream thread in committed-offset initialization until default.api.timeout.ms, exceeds max.poll.interval.ms, and gets the member evicted. Observed in a system test (streams_broker_down_resilience_test, staggered startup: epoch bumped while the fetch was in flight). Plain consumer groups (group.protocol=consumer) are exposed too, given concurrent same-partition committed-offset fetches during an epoch bump.

Deterministic reproducer: two concurrent fetchOffsets() for the same partition (second gets chained), respond with STALE_MEMBER_EPOCH after updating the member epoch.

Suggested fix: exclude requests whose future is already done from the duplicate search, so the retry is enqueued and re-sent with the current epoch.

Related: the onFailure ERROR for STALE_MEMBER_EPOCH ("cannot be retried and will fail") is logged even when a retry follows; worth fixing alongside.
~~~~

---

## KAFKA-20773: [CVE-2026-54515][jackson-databind]

https://issues.apache.org/jira/browse/KAFKA-20773

Given fix versions: 4.2.2, 4.3.2, 4.4.0
JIRA affects (masked from the system): 4.1.2, 4.2.1, 4.3.0

- `KAFKA-20773@4.3.0`: config 4.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-20773@4.1.1`: config 4.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.8.0

### Description

~~~~
Description : jackson-databind contains the general-purpose data-binding functionality and tree-model for Jackson Data Processor. From 2.8.0 until 2.18.9, 2.21.5, and 3.1.4, in BeanDeserializerBase.createContextual(), per-property @JsonIgnoreProperties exclusions are applied by _handleByNameInclusion(), producing a contextual deserializer whose BeanPropertyMap has the ignored properties removed. The subsequent per-property case-insensitivity block (triggered by @JsonFormat(ACCEPT_CASE_INSENSITIVE_PROPERTIES)) rebuilds from this._beanProperties (the original, unfiltered map) instead of contextual._beanProperties, then overwrites the filtered map — restoring every property _handleByNameInclusion had just removed. The ignored property becomes writable again. This vulnerability is fixed in 2.18.9, 2.21.5, and 3.1.4.
*NVD URL :* [https://nvd.nist.gov/vuln/detail/CVE-2026-54515]

Fix Version :  2.18.9, 2.21.5, and 3.1.4.
~~~~

---

## KAFKA-20938: Previous JoinGroup/SyncGroup requests left dangling when retried

https://issues.apache.org/jira/browse/KAFKA-20938

Given fix versions: 4.5.0
JIRA affects (masked from the system): 4.0.0

- `KAFKA-20938@4.0.0`: config 4.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-20938@3.9.2`: config 3.9.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
The group coordinator can only keep track of a single JoinGroup and SyncGroup request future per member. When a member retries a blocking JoinGroup or SyncGroup request, the previous future is discarded and replaced, leaving the previous request unanswered.

This can be a problem when there are proxies in between the client and broker which wait for the response regardless of whether clients have disconnected.
~~~~

---
