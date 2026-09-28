# kafka-ground-truth-v1: labeling review

For each case, decide whether the text below (and only this text) says enough to
conclude the metadata answer for that config version. Record `yes` or `no` in the
`answerable_from_text` column of labels.csv, with a short note when it's borderline.

## KAFKA-570: Kafka should not need snappy jar at runtime

https://issues.apache.org/jira/browse/KAFKA-570

JIRA metadata: affects 0.8.0; fixed in 0.9.0.0

- `KAFKA-570@0.8.0`: config 0.8.0, metadata answer **affected** (listed_affected)
- `KAFKA-570@0.9.0.0`: config 0.9.0.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 0.9

### Description

~~~~
CompressionFactory imports snappy jar in a pattern match. The purpose of importing it this way seems to be avoiding the import unless snappy compression is actually required. However, kafka throws a ClassNotFoundException if snappy jar is removed at runtime from lib_managed. 

This exception can be easily seen by producing some data with the console producer.
~~~~

### Comments (2)

1.

~~~~
This issue will be automatically fixed when the server code moves to client's common libraries, moving to 0.9 for now.
~~~~

2.

~~~~
This is fixed in the new clients, closing.
~~~~

---

## KAFKA-824: java.lang.NullPointerException in commitOffsets 

https://issues.apache.org/jira/browse/KAFKA-824

JIRA metadata: affects 0.7.2, 0.8.2.0; fixed in 0.9.0.0

- `KAFKA-824@0.8.2.0`: config 0.8.2.0, metadata answer **affected** (listed_affected)
- `KAFKA-824@0.10.0.0`: config 0.10.0.0, metadata answer **not_affected** (later_line)

Known Kafka versions mentioned in text: 0.8.1

### Description

~~~~
Neha Narkhede

"Yes, I have. Unfortunately, I never quite around to fixing it. My guess is
that it is caused due to a race condition between the rebalance thread and
the offset commit thread when a rebalance is triggered or the client is
being shutdown. Do you mind filing a bug ?"


2013/03/25 12:08:32.020 WARN [ZookeeperConsumerConnector] [] 0_lu-ml-test10.bj-1364184411339-7c88f710 exception during commitOffsets
java.lang.NullPointerException
        at org.I0Itec.zkclient.ZkConnection.writeData(ZkConnection.java:111)
        at org.I0Itec.zkclient.ZkClient$10.call(ZkClient.java:813)
        at org.I0Itec.zkclient.ZkClient.retryUntilConnected(ZkClient.java:675)
        at org.I0Itec.zkclient.ZkClient.writeData(ZkClient.java:809)
        at org.I0Itec.zkclient.ZkClient.writeData(ZkClient.java:777)
        at kafka.utils.ZkUtils$.updatePersistentPath(ZkUtils.scala:103)
        at kafka.consumer.ZookeeperConsumerConnector$$anonfun$commitOffsets$2$$anonfun$apply$4.apply(ZookeeperConsumerConnector.scala:251)
        at kafka.consumer.ZookeeperConsumerConnector$$anonfun$commitOffsets$2$$anonfun$apply$4.apply(ZookeeperConsumerConnector.scala:248)
        at scala.collection.Iterator$class.foreach(Iterator.scala:631)
        at scala.collection.JavaConversions$JIteratorWrapper.foreach(JavaConversions.scala:549)
        at scala.collection.IterableLike$class.foreach(IterableLike.scala:79)
        at scala.collection.JavaConversions$JCollectionWrapper.foreach(JavaConversions.scala:570)
        at kafka.consumer.ZookeeperConsumerConnector$$anonfun$commitOffsets$2.apply(ZookeeperConsumerConnector.scala:248)
        at kafka.consumer.ZookeeperConsumerConnector$$anonfun$commitOffsets$2.apply(ZookeeperConsumerConnector.scala:246)
        at scala.collection.Iterator$class.foreach(Iterator.scala:631)
        at kafka.utils.Pool$$anon$1.foreach(Pool.scala:53)
        at scala.collection.IterableLike$class.foreach(IterableLike.scala:79)
        at kafka.utils.Pool.foreach(Pool.scala:24)
        at kafka.consumer.ZookeeperConsumerConnector.commitOffsets(ZookeeperConsumerConnector.scala:246)
        at kafka.consumer.ZookeeperConsumerConnector.autoCommit(ZookeeperConsumerConnector.scala:232)
        at kafka.consumer.ZookeeperConsumerConnector$$anonfun$1.apply$mcV$sp(ZookeeperConsumerConnector.scala:126)
        at kafka.utils.Utils$$anon$2.run(Utils.scala:58)
        at java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:471)
        at java.util.concurrent.FutureTask$Sync.innerRunAndReset(FutureTask.java:351)
        at java.util.concurrent.FutureTask.runAndReset(FutureTask.java:178)
        at java.util.concurrent.ScheduledThreadPoolExecutor$ScheduledFutureTask.access$301(ScheduledThreadPoolExecutor.java:178)
        at java.util.concurrent.ScheduledThreadPoolExecutor$ScheduledFutureTask.run(ScheduledThreadPoolExecutor.java:293)
        at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1110)
        at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:603)
        at java.lang.Thread.run(Thread.java:722)



~~~~

### Comments (20)

1.

~~~~
I have it as well. No special test case - but it fails periodically ~1 in 10 cases.
My configuration:
- zkclient: 0.4
- kafka: 2.9.2-0.8.1
- zookeeper: 3.4.5

~~~~

2.

~~~~
Currently we are only using zkclient 0.3. Could you check if this problem still persists in that version?

Guozhang
~~~~

3.

~~~~
It fails for both zkclient 0.3 and 0.4. Please see attached files.
~~~~

4.

~~~~
Do you see ZK session expiration around that time?
~~~~

5.

~~~~
I think it's a case then "_connection" is null for some reason: https://github.com/sgroschupf/zkclient/blob/master/src/main/java/org/I0Itec/zkclient/ZkClient.java#L308
Without going deep into hardcore I would override "ZkClient.create" with my method checking "_connection" for null:

{code:java}
public class KafkaZkClient extends ZkClient{
    public String create(final String path, Object data, final CreateMode mode) throws ZkInterruptedException, IllegalArgumentException, ZkException, RuntimeException {
        if (path == null) {
            throw new NullPointerException("path must not be null.");
        }
        final byte[] bytes = data == null ? null : serialize(data);

        return retryUntilConnected(new Callable<String>() {

            @Override
            public String call() throws Exception {
                if(_connection==null) throw new ConnectionLossException(); // FIX HERE <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                return _connection.create(path, bytes, mode);
            }
        });
    }
}
{code} 
~~~~

6.

~~~~
The root of the problem is here: https://github.com/sgroschupf/zkclient/blob/master/src/main/java/org/I0Itec/zkclient/ZkClient.java#L690
The first "return callable.call();" potentially can be called  even before "_connection"  is initialized.

So it's better to fix the root.
~~~~

7.

~~~~
Hmm, not sure if this can happen. The following is what happens in the constructor. _connection is set there and the underlying _zk in ZkConnection is also set.

    public ZkClient(IZkConnection zkConnection, int connectionTimeout, ZkSerializer zkSerializer) {
        _connection = zkConnection;
        _zkSerializer = zkSerializer;
        connect(connectionTimeout, this);
    }
~~~~

8.

~~~~
Could it be by re-using closed ZkClient? https://github.com/sgroschupf/zkclient/blob/master/src/main/java/org/I0Itec/zkclient/ZkClient.java#L941
It happens in some way.
~~~~

9.

~~~~
ZkClient is only closed when shutdown the consumer connector.
~~~~

10.

~~~~
Any progress?
Have a look: !screenshot-1.jpg!
~~~~

11.

~~~~
We are seeing a similar NPE in our application's direct usage of the ZkClient, unrelated to commitOffsets.

Here are a couple example stack traces.
{noformat}
Caused by: java.lang.NullPointerException
	at org.I0Itec.zkclient.ZkConnection.create(ZkConnection.java:87)
	at org.I0Itec.zkclient.ZkClient$1.call(ZkClient.java:308)
	at org.I0Itec.zkclient.ZkClient$1.call(ZkClient.java:304)
	at org.I0Itec.zkclient.ZkClient.retryUntilConnected(ZkClient.java:675)
	at org.I0Itec.zkclient.ZkClient.create(ZkClient.java:304)
	at org.I0Itec.zkclient.ZkClient.createPersistent(ZkClient.java:213)
{noformat}

{noformat}
Caused by: java.lang.NullPointerException
	at org.I0Itec.zkclient.ZkConnection.writeDataReturnStat(ZkConnection.java:115)
	at org.I0Itec.zkclient.ZkClient$10.call(ZkClient.java:817)
	at org.I0Itec.zkclient.ZkClient.retryUntilConnected(ZkClient.java:675)
	at org.I0Itec.zkclient.ZkClient.writeDataReturnStat(ZkClient.java:813)
	at org.I0Itec.zkclient.ZkClient.writeData(ZkClient.java:808)
	at org.I0Itec.zkclient.ZkClient.writeData(ZkClient.java:777)
{noformat}

ZkClient implements the org.apache.zookeeper.Watcher interface, so the process() callback can be invoked at any time by the background ZK event thread [1]. This callback method is not synchronized against the other ZkClient public methods, however. So if a state change event occurs that requires a reconnection [2], the internal ZkConnection is closed while reconnecting [3] which sets its org.apache.zookeeper.ZooKeeper to null [4] resulting in the NullPointerException if the process is concurrently using the ZkClient to read or write data.

[1] http://zookeeper.apache.org/doc/r3.3.4/zookeeperProgrammers.html#Java+Binding
[2] https://github.com/sgroschupf/zkclient/blob/master/src/main/java/org/I0Itec/zkclient/ZkClient.java#L457
[3] https://github.com/sgroschupf/zkclient/blob/master/src/main/java/org/I0Itec/zkclient/ZkClient.java#L953-954
[4] https://github.com/sgroschupf/zkclient/blob/master/src/main/java/org/I0Itec/zkclient/ZkConnection.java#L79
~~~~

12.

~~~~
Here's another example stack trace that we have seen.

{noformat}
java.lang.NullPointerException
	at org.I0Itec.zkclient.ZkConnection.exists(ZkConnection.java:95)
	at org.I0Itec.zkclient.ZkClient$3.call(ZkClient.java:439)
	at org.I0Itec.zkclient.ZkClient$3.call(ZkClient.java:436)
	at org.I0Itec.zkclient.ZkClient.retryUntilConnected(ZkClient.java:675)
	at org.I0Itec.zkclient.ZkClient.exists(ZkClient.java:436)
	at org.I0Itec.zkclient.ZkClient$12.call(ZkClient.java:846)
	at org.I0Itec.zkclient.ZkClient$12.call(ZkClient.java:843)
	at org.I0Itec.zkclient.ZkClient.retryUntilConnected(ZkClient.java:675)
	at org.I0Itec.zkclient.ZkClient.watchForChilds(ZkClient.java:843)
	at org.I0Itec.zkclient.ZkClient.subscribeChildChanges(ZkClient.java:114)
	at kafka.consumer.ZookeeperConsumerConnector.kafka$consumer$ZookeeperConsumerConnector$$reinitializeConsumer(ZookeeperConsumerConnector.scala:713)
	at kafka.consumer.ZookeeperConsumerConnector$WildcardStreamsHandler.(ZookeeperConsumerConnector.scala:756)
	at kafka.consumer.ZookeeperConsumerConnector.createMessageStreamsByFilter(ZookeeperConsumerConnector.scala:145)
	at kafka.javaapi.consumer.ZookeeperConsumerConnector.createMessageStreamsByFilter(ZookeeperConsumerConnector.scala:96)
{noformat}
~~~~

13.

~~~~
I have reported this issue to the zkclient project: https://github.com/sgroschupf/zkclient/issues/25
~~~~

14.

~~~~
Has any progress been made on this, or do any workarounds exist yet?  Has anyone determined what causes it in particular?

We're getting it fairly regularly and I would love to know how to mitigate the issue.
~~~~

15.

~~~~
Hi guys,

just had a look at this.
Think there are only 2 possibilities that such an exception can occur:
- 1) a null zkConnection is passed in
- 2) a retryUntilConnected action wakes up and the client was closed in meantime

I could reproduce the NPE for case 2 and changed the code to throw an clear exception instead of risking unclear follow up exception like the NPE's.
See https://github.com/sgroschupf/zkclient/commit/0630c9c6e67ab49a51e80bfd939e4a0d01a69dfe

HTH

PS: this is part of the zkclient-0.5 release which should be online in a few hours!
~~~~

16.

~~~~
Awesome, thank you for the quick follow-up :).
~~~~

17.

~~~~
Can someone confirm that upgrading to zkclient-0.5 did fix the NPE?
~~~~

18.

~~~~
[~techwhizbang] I upgraded to zkClient-0.5 so I will verify this is fixed and update the jira.
~~~~

19.

~~~~
[~junrao] Looked at the fix code and ensure that it was part of 0.5 release. The fix also had a unit test so I believe this is ok to resolve. 
~~~~

20.

~~~~
[~parth.brahmbhatt], thanks for confirming this. Resolving this jira.
~~~~

---

## KAFKA-1363: testTopicConfigChangesDuringDeleteTopic hangs

https://issues.apache.org/jira/browse/KAFKA-1363

JIRA metadata: affects 0.8.1; fixed in 0.8.1.1

- `KAFKA-1363@0.8.1`: config 0.8.1, metadata answer **affected** (listed_affected)
- `KAFKA-1363@0.8.1.1`: config 0.8.1.1, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 0.8.1

### Description

~~~~
Saw the following deadlock during shutting down the delete topic manager.

"delete-topics-thread" prio=10 tid=0x00007fd50c003800 nid=0x7d9 waiting on condition [0x00007fd53d160000]
   java.lang.Thread.State: WAITING (parking)
        at sun.misc.Unsafe.park(Native Method)
        - parking to wait for  <0x00000006b41d6318> (a java.util.concurrent.locks.ReentrantLock$NonfairSync)
        at java.util.concurrent.locks.LockSupport.park(LockSupport.java:156)
        at java.util.concurrent.locks.AbstractQueuedSynchronizer.parkAndCheckInterrupt(AbstractQueuedSynchronizer.java:811)
        at java.util.concurrent.locks.AbstractQueuedSynchronizer.acquireQueued(AbstractQueuedSynchronizer.java:842)
        at java.util.concurrent.locks.AbstractQueuedSynchronizer.acquire(AbstractQueuedSynchronizer.java:1178)
        at java.util.concurrent.locks.ReentrantLock$NonfairSync.lock(ReentrantLock.java:186)
        at java.util.concurrent.locks.ReentrantLock.lock(ReentrantLock.java:262)
        at kafka.utils.Utils$.inLock(Utils.scala:535)
        at kafka.controller.TopicDeletionManager$DeleteTopicsThread.doWork(TopicDeletionManager.scala:363)
        at kafka.utils.ShutdownableThread.run(ShutdownableThread.scala:51)

"Test worker" prio=10 tid=0x00007fd578928800 nid=0x763d waiting on condition [0x00007fd570a87000]
   java.lang.Thread.State: WAITING (parking)
        at sun.misc.Unsafe.park(Native Method)
        - parking to wait for  <0x00000006b5b6f580> (a java.util.concurrent.CountDownLatch$Sync)
        at java.util.concurrent.locks.LockSupport.park(LockSupport.java:156)
        at java.util.concurrent.locks.AbstractQueuedSynchronizer.parkAndCheckInterrupt(AbstractQueuedSynchronizer.java:811)
        at java.util.concurrent.locks.AbstractQueuedSynchronizer.doAcquireSharedInterruptibly(AbstractQueuedSynchronizer.java:969)
        at java.util.concurrent.locks.AbstractQueuedSynchronizer.acquireSharedInterruptibly(AbstractQueuedSynchronizer.java:1281)
        at java.util.concurrent.CountDownLatch.await(CountDownLatch.java:207)
        at kafka.utils.ShutdownableThread.shutdown(ShutdownableThread.scala:36)
        at kafka.controller.TopicDeletionManager.shutdown(TopicDeletionManager.scala:100)
        at kafka.controller.KafkaController$$anonfun$onControllerResignation$1.apply$mcV$sp(KafkaController.scala:345)
        at kafka.controller.KafkaController$$anonfun$onControllerResignation$1.apply(KafkaController.scala:341)
        at kafka.controller.KafkaController$$anonfun$onControllerResignation$1.apply(KafkaController.scala:341)
        at kafka.utils.Utils$.inLock(Utils.scala:537)
        at kafka.controller.KafkaController.onControllerResignation(KafkaController.scala:341)
        at kafka.controller.KafkaController$$anonfun$shutdown$1.apply$mcV$sp(KafkaController.scala:648)
        at kafka.controller.KafkaController$$anonfun$shutdown$1.apply(KafkaController.scala:646)
        at kafka.controller.KafkaController$$anonfun$shutdown$1.apply(KafkaController.scala:646)
        at kafka.utils.Utils$.inLock(Utils.scala:537)
        at kafka.controller.KafkaController.shutdown(KafkaController.scala:646)
        at kafka.server.KafkaServer$$anonfun$shutdown$9.apply$mcV$sp(KafkaServer.scala:242)
        at kafka.utils.Utils$.swallow(Utils.scala:166)
        at kafka.utils.Logging$class.swallowWarn(Logging.scala:92)
        at kafka.utils.Utils$.swallowWarn(Utils.scala:45)
        at kafka.utils.Logging$class.swallow(Logging.scala:94)
        at kafka.utils.Utils$.swallow(Utils.scala:45)
        at kafka.server.KafkaServer.shutdown(KafkaServer.scala:242)
        at kafka.admin.DeleteTopicTest$$anonfun$testTopicConfigChangesDuringDeleteTopic$1.apply(DeleteTopicTest.scala:362)
        at kafka.admin.DeleteTopicTest$$anonfun$testTopicConfigChangesDuringDeleteTopic$1.apply(DeleteTopicTest.scala:362)
        at scala.collection.LinearSeqOptimized$class.foreach(LinearSeqOptimized.scala:61)
        at scala.collection.immutable.List.foreach(List.scala:45)
        at kafka.admin.DeleteTopicTest.testTopicConfigChangesDuringDeleteTopic(DeleteTopicTest.scala:362)

~~~~

### Comments (6)

1.

~~~~
Created reviewboard https://reviews.apache.org/r/20143/
 against branch origin/trunk
~~~~

2.

~~~~
Updated reviewboard https://reviews.apache.org/r/20143/
 against branch origin/trunk
~~~~

3.

~~~~
Updated reviewboard https://reviews.apache.org/r/20143/
 against branch origin/trunk
~~~~

4.

~~~~
Created reviewboard https://reviews.apache.org/r/20187/
 against branch origin/0.8.1
~~~~

5.

~~~~
Thanks for the patch. +1 and committed to trunk.
~~~~

6.

~~~~
Checked into 0.8.1 as well
~~~~

---

## KAFKA-1947: can't explicitly set replica-assignment when add partitions

https://issues.apache.org/jira/browse/KAFKA-1947

JIRA metadata: affects 0.8.1.1; fixed in 0.9.0.0

- `KAFKA-1947@0.8.1.1`: config 0.8.1.1, metadata answer **affected** (listed_affected)
- `KAFKA-1947@0.9.0.0`: config 0.9.0.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: none

### Description

~~~~
When create topic, the replicaAssignmentOpt should not appear with partitions.
But when add partitions,  they should can appear together,  from the code below, you can see when alter topic, and has partitions in arguments, it try get "replica-assignment"
https://git1-us-west.apache.org/repos/asf?p=kafka.git;a=blob;f=core/src/main/scala/kafka/admin/TopicCommand.scala;h=285c0333ff43543d3e46444c1cd9374bb883bb59;hb=HEAD#l114 

The root cause is below code:
CommandLineUtils.checkInvalidArgs(parser, options, replicaAssignmentOpt,
 305         allTopicLevelOpts -- Set(alterOpt, createOpt) + partitionsOpt + replicationFactorOpt)

https://git1-us-west.apache.org/repos/asf?p=kafka.git;a=blob;f=core/src/main/scala/kafka/admin/TopicCommand.scala;h=285c0333ff43543d3e46444c1cd9374bb883bb59;hb=HEAD#l304

Related:  
https://issues.apache.org/jira/browse/KAFKA-1052


~~~~

### Comments (4)

1.

~~~~
Created reviewboard  against branch origin/trunk
~~~~

2.

~~~~
The fix is quite directly:
When has replicaAssignment, the command should only be createTopic or alterTopic
When the command is create topic,  and replicaAssignment appear, there should no partitions and replica number.

The command told me board is ok, but actually no.  But patch uploaded.

D:\C\Kafka_Update>kafka-patch-review_.py -b origin/trunk -j KAFKA-1947
Configuring reviewboard url to https://reviews.apache.org
Updating your remote branches to pull the latest changes
Creating diff against origin/trunk and uploading patch to JIRA KAFKA-1947
Created a new reviewboard

D:\C\Kafka_Update>
~~~~

3.

~~~~
Submit review ...

https://reviews.apache.org/r/30919/diff/

Please help check
~~~~

4.

~~~~
Thanks for the patch. Pushed to trunk
~~~~

---

## KAFKA-3894: LogCleaner thread crashes if not even one segment can fit in the offset map

https://issues.apache.org/jira/browse/KAFKA-3894

JIRA metadata: affects 0.10.0.0, 0.8.2.2, 0.9.0.1; fixed in 0.10.1.0

- `KAFKA-3894@0.10.0.0`: config 0.10.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-3894@0.10.1.0`: config 0.10.1.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 0.10.0.0, 0.9.0.1, 0.8.2.1, 0.10.0, 0.10.1.0

### Description

~~~~
The log-cleaner thread can crash if the number of keys in a topic grows to be too large to fit into the dedupe buffer. 

The result of this is a log line: 
{quote}
broker=0 pri=ERROR t=kafka-log-cleaner-thread-0 at=LogCleaner \[kafka-log-cleaner-thread-0\], Error due to  java.lang.IllegalArgumentException: requirement failed: 9750860 messages in segment MY_FAVORITE_TOPIC-2/00000000000047580165.log but offset map can fit only 5033164. You can increase log.cleaner.dedupe.buffer.size or decrease log.cleaner.threads
{quote}

As a result, the broker is left in a potentially dangerous situation where cleaning of compacted topics is not running. 

It is unclear if the broader strategy for the {{LogCleaner}} is the reason for this upper bound, or if this is a value which must be tuned for each specific use-case. 

Of more immediate concern is the fact that the thread crash is not visible via JMX or exposed as some form of service degradation. 

Some short-term remediations we have made are:
* increasing the size of the dedupe buffer
* monitoring the log-cleaner threads inside the JVM
~~~~

### Comments (26)

1.

~~~~
(disclaimer: I work with Tim)

It feels like there are a few pieces of work to do here:

1. Expose if the log cleaner state as a JMX metric (like BrokerState)
2. Somehow mark logs we've failed to clean as "busted" somewhere, and stop trying to clean them. This way instead of erroring when this occurs the broker doesn't stay completely busted, but continues on working on all other partitions
3. I'm unsure, but is it possible to fix the underlying issue by only compacting partial segments of the log when the buffer size is smaller than the desired offset map? This seems like the hardest but most valuable fix here.

We're happy picking up at least some of these, but would love feedback from the community about priorities and ease/appropriateness of these steps (and suggestions for other things to have).
~~~~

2.

~~~~
The exception looks like the one in KAFKA-3587, which was fixed in 0.10.0.0.
~~~~

3.

~~~~
Yep, we've ran into the same issue.

Would be nice if the cleaner, at the very minimum, skipped the segments with large number of records.
~~~~

4.

~~~~
[~ijuma] Not sure this is related. Our situation seems to be just a legitimate large number of records in the segment.
~~~~

5.

~~~~
About log compaction JMX metrics, there is https://issues.apache.org/jira/browse/KAFKA-3857
~~~~

6.

~~~~
A quick improvement would be to increase the severity of the log message when log cleaner stops. Right now there is just an "INFO" message that's easy to miss.
~~~~

7.

~~~~
Regarding Log cleaner JMX metrics, I just submitted a PR. Please take a look:
https://github.com/apache/kafka/pull/1593

JIRA: https://issues.apache.org/jira/browse/KAFKA-3857

~~~~

8.

~~~~
Woohoo, more metrics is so excellent!

Regarding the issue I am reporting: it is somewhat broader than the specific issues related to the log cleaner which have been resolved across the lifetime of Kafka.

* Compaction thread dies when hitting compressed and unkeyed messages (https://github.com/apache/kafka/commit/1cd6ed9e2c07a63474ed80a8224bd431d5d4243c#diff-d7330411812d23e8a34889bee42fedfe) noted in KAFKA-1755
* Logcleaner fails due to incorrect offset map computation on a replica in KAFKA-3587

Unfortunately, there is a deeper issue: if these threads die, bad things happen.

KAFKA-3587 was a great step forward, now this exception will only occur if a single segment is unable to fit within the dedupe buffer. Unfortunately, in pathological cases the thread could still die. 

Compacted topics are built to rely on the log cleaner thread and because of this, any segments which are written must be compatible with the configuration for log cleaner threads. 
As I mentioned before, we are now monitoring the log cleaner threads and as a result do not have long periods where a broker is in a dangerous and degraded state. 
One situation which comes to mind is from a talk at Kafka Summit where the thread was offline for a large period of time. Upon restart, the {{__consumer_offsets}} topic took 17 minutes to load. 
http://www.slideshare.net/jjkoshy/kafkaesque-days-at-linked-in-in-2015/49

After talking with Tom, we came up with a few solutions which could help in resolving this issue. 

1) The monitoring suggested in KAFKA-3857 is a great start and would most definitely help with determining the state of the log cleaner.
2) After the change in KAFKA-3587, it could be possible to simply leave segments which are too large and leave them as zombie segments which will never be cleaned. This is less than ideal, but means that a single large segment would not take down the whole log cleaner subsystem. 
3) Upon encountering a large segment, we considered the possibility of splitting the segment to allow the log cleaner to continue. This would potentially delay some cleanup until a later time. 
4) Currently, it seems like the write path allows for segments to be created which are unable to be processed by the log cleaner. Would it make sense to include log cleaner heuristics when determining segment size for compacted topics? This would allow the log cleaner to always process a segment, unless the buffer size was changed. 

We'd love to help in any way we can. 
~~~~

9.

~~~~
#4 is a good point. By looking at the buffer size, the broker can calculate how large a segment it can handle, and can thus make sure to only generate segments that it can handle.

The comment about having a large segment that you are unable to process made me think about the long discussion that happened in https://issues.apache.org/jira/browse/KAFKA-3810. In that JIRA, a large message in the __consumer_offsets topic would block (internal) consumers who had too small of a fetch size.

The solution that was chosen and was implemented was to loosen the fetch size for fetches from internal topics. Internal topics would always return at least one message, even if the message was larger than the fetch size.

It made me wonder if it might make sense to treat the dedupe buffer in a similar way. In a steady state, the configured dedupe buffer size would be used but if it's too small to even fit a single segment, then the dedupe buffer would be (temporarily) grown to allow cleaning of that large segment.

CC [~junrao]

~~~~

10.

~~~~
[~wushujames], this is slightly different from KAFKA-3810. In KAFKA-3810, messages are bounded by MaxMessageSize, which in turn bounds the fetch response size. For cleaning, if messages are uncompressed, the dedupBufferSize needed is bounded by segmentSize/perMessageOverhead. However, if messages are compressed, dedupBufferSize needed could be arbitrarily large. So, I am not sure if we want to auto grow the buffer size arbitrarily. 

#4 seems to be a safer approach. There are effective ways of estimating the number of unique keys (https://people.mpi-inf.mpg.de/~rgemulla/publications/beyer07distinct.pdf) incrementally. We will need to figure out where to store it in order to avoid rescanning the log on startup. 
~~~~

11.

~~~~
Jun:

#4 seems potentially very complex to me. It also doesn't work in the case that the broker is shut down and the dedupe buffer size adjusted. I much prefer #3 - it maps fine into the existing model as far as I can tell - we'd "just" split the log file we're cleaning once the offsetmap is full. That of course requires a little more IO, but it doesn't involve implementing (or using a library for) sketches that could potentially be incorrect. It also seems like the right long term solution, and more robust than automatically rolling log files some of the time. Am I missing something here? 

Upsides of #3 vs #4:
We can now clean the largest log segment, no matter the buffer size.
We don't increase complexity of the produce path, or change memory usage.
We don't have to implement or reuse a library for estimating unique keys
We don't have to figure out storing the key estimate (e.g. in the index or in a new file alongside each segment).

Downsides:
It would increase the complexity of the cleaner.
The code that swaps in and out segments will also get more complex, and the crash-safety of that code is already tricky.

Exists in both:
Larger log segments could potentially be split a lot, and not always deduplicated that well together. For example, if I write the max number of unique keys for the offset map into a topic, then the segment rolls, then I write a tombstone for every message in the previously sent messages, then neither #3 nor #4 would ever clear up any data. This is no worse than today though.

Cassandra and other LSM based systems that do log structured storage and over-time compaction use similar "splitting and combining" mechanisms to ensure everything gets cleared up over time without using too much memory. They have a very different storage architecture and goals to Kafka's compaction, for sure, but it's interesting to note that they care about similar things.
~~~~

12.

~~~~
Not adding much to the conversation, but I've just been hit by this bug.

I'm in the process of upgrading my cluster to 0.9.0.1, and in one case the log cleaner dies because of this.

{{requirement failed: 1214976153 messages in segment __consumer_offsets-15/00000000000012560043.log but offset map can fit only 40265317}}

If I'm not wrong, there's no way that much messages can fit in the buffer since it's limited to 2G anyway per thread. Right now I'm leaving it as is since the broker seems to be working, but it's not ideal.

I'm wondering if I simply delete the log file with the broker shut down, will it be fetched at startup from an other replica without problems ?
In my case, I believe this is only temporary: we never enabled the log cleaner when running 0.8.2.1 (mistake on my part) and now when migrating to 0.9.0.1 it does a giant cleanup at first startup.
~~~~

13.

~~~~
Re: "the broker seems to be working"

You may regret not taking action now.  As Tim mentioned from the talk at the Kafka Summit (http://www.slideshare.net/jjkoshy/kafkaesque-days-at-linked-in-in-2015/49), if __consumer_offsets is not compacted and has accumulated millions (or billions!) of messages, it can take many minutes for the broker to elect a new coordinator after any kind of hiccup.  *Your new consumers may be hung during this time!*

However, even shutting down brokers to change the configuration will cause coordinator elections which will cause an outage.  It seems like not having a "hot spare" for Offset Managers is a liability here…

We were bit by this bug and it caused all kinds of headaches until we managed to get __consumer_offsets cleaned up again.
~~~~

14.

~~~~
Yeah, that's why I was hoping for a workaround :)

Right now it takes a ridiculous amount of time for the broker to load some partitions, it just took like 1h+ to load a 300Gb partition. In that case it didn't impact production though.

I believe I have found a workaround in my case, since as said it's a temporary thing: I note all big partitions (more than a Gb let's say) and reassign them on brokers that are already cleaned up. The reassignment takes a long time but in the end I think it'll remove the partition from the problematic broker.
~~~~

15.

~~~~
Well that doesn't work, in fact I just realized that the log cleaner threads all died on the migrated brokers. So yep, still need to find a workaround or wait for a fix. How did you manage to cleanup the logs [~davispw] ?
~~~~

16.

~~~~
[~tcrayford-heroku], I chatted with [~jkreps] on this a bit. There are a couple things that we can do to address this issue.

a. We can potentially make the allocation of the dedup buffer more dynamic. We can start with something small like 100MB. If needed, we can grow the dedup buffer up to the configured size. This will allow us to set a larger default dedup buffer size (say 1GB). If there are not lots of keys, the broker won't be using that much memory. This will allow the default configuration to accommodate more keys.

b. To handle the edge case where a segment still has more keys than the increased dedup buffer can handle. We can do the #3 approach as you suggested. Basically, if the dedup buffer is full when only a partial segment is loaded, we remember the next offset (say L). We scan all old log segments including this one as before. The only difference is that when scanning the last segment, we force creating a new segment starting at offset L and simply copy the existing messages after L to the new segment. Then, after we swapped in the new segments, we will move the cleaner marker to offset L. This adds a bit of inefficiency since we have to scan the last swapped-in segment again. However, this will allow the cleaner to always make progress regardless of the # of keys. I am not sure that I understand the case you mentioned that won't work in both approach #3 and #4.
~~~~

17.

~~~~
I updated the title to match the issue that is still present in 0.10.0.x. Note that the log message in 0.10.0.x would be different from the one posted in the JIRA description:

{code}
require(offset > start, "Unable to build the offset map for segment %s/%s. You can increase log.cleaner.dedupe.buffer.size or decrease log.cleaner.threads".format(log.name, segment.log.file.getName))
{code}

It would be good to have a fix for 0.10.1.0 so I set the fix version. Tim and Tom, any of you interested in picking this up?


~~~~

18.

~~~~
I've bumped the bumped into this same issue (log cleaner threads dying because messages wouldn't fit the offset map).

For some of the topics the messages would almost fit, so I was able to get away just increasing the dedupe buffer load factor (https://github.com/apache/kafka/blob/trunk/core/src/main/scala/kafka/server/KafkaConfig.scala#L252) which defaults to 90% of the 2Gb max buffer size.

For other topics that had more messages and wouldn't fit in the 2Gb in any way, the workaround was to:

1) decrease the segment size config for that topic [1]
2) reassign topic partitions, in order to end up with new segments with sizes obeying the config change
3) rolling restart the nodes, to restart log cleaner threads

I'd love to know if there is another way of doing this, step 3 is particularly frustrating.

Good luck!

[1]: This can be done for a particular topic with: `kafka-topics.sh --zookeeper $ZK --topic $TOPIC --alter --config segment.bytes`, but if needed you can also set `log.segment.bytes` for topics across all cluster.
~~~~

19.

~~~~
Hi Jun,

We're probably going to start on b. for now. I think a. is incredibly valuable, but it doesn't impact this manner of the log cleaner crashing. I think there are some cases where we will fail to clean up data, but having those exist seems far more preferable than crashing the thread entirely.

We'll get started with b., hopefully will have a patch up within a few business days.
~~~~

20.

~~~~
Issue resolved by pull request 1725
[https://github.com/apache/kafka/pull/1725]
~~~~

21.

~~~~
[~tcrayford-heroku], thanks for the patch. Filed a followup jira KAFKA-4072 to improve the memory usage in log cleaner.
~~~~

22.

~~~~
I know this bug is resolved, but we just encountered this bug in our 0.9.0.1 Cluster. 

{code}
[2017-01-24 17:17:30,035] ERROR [kafka-log-cleaner-thread-0], Error due to  (kafka.log.LogCleaner)
java.lang.IllegalArgumentException: requirement failed: 13042136566 messages in segment __consumer_offsets-32/00000000000000000000.log but offset map can fit only 5033164. You can increase log.cleaner.dedupe.buffer.size or decrease log.cleaner.threads
{code}

We've tried the following attempts to fix:
- Increase the log.cleaner.dedupe.buffer.size but the # of messages is greater then MAX_INT and will be beyond the amount of memory we can allocated.
- Wipe away the partition in question from a single broker and let the data replicate back. Did not work as all the replicas for this partition also have an issue where they cannot compact the topic.

Does anyone else know of another solution to recover this partition? Do I need to just wipe away the whole partition completely?

~~~~

23.

~~~~
I had the exact same bug, didn't realize it at first. What I did was simply deleting all 000000... files manually with the broker stopped, and restarting the broker. 

I was betting that it would be fine because it's the cosumer offsets topic, and chances are the data in that file is useless anyway since my consumers commit constantly, and only fetch offsets while starting up essentially. It's a little risky, but worked. (and at that time the patch wasn't available)

Still have no idea what generated those files though.
~~~~

24.

~~~~
[~me@vrischmann.me] Thanks for the quick reply. Do you mean you deleted all logs from the partition? Or where you just targeting specific files which were throwing the error?

I was thinking of shutting down the brokers & consumers and removing the unstable partition and restarting with my `auto.offset.reset=latest` set on my consumers.
~~~~

25.

~~~~
No not all logs, just the 00000000000000000000.log one. If you notice, Kafka computes the number of messages based on the number in the filename, hence why it reports there is 13042136566 messages in your log, which is almost surely not true. At least it wasn't for me.

The file name is just wrong basically. Come to think of it, you could maybe just rename the file to some arbitrary number where you know the difference between the _next_  segment number and _this_ segment buffer is something that would fit in your dedupe buffer ? For example, here your second segment has the number _13042136566_, you could rename the 00000000000000000000.log to _13042136566 - 1000000_ then your offset map only needs to fit 1M offsets which it can do based on your log.

I'm just thinking out loud here, I didn't do this but I think it could work, and would be less risky than just deleting all data, maybe.
~~~~

26.

~~~~
[~me@vrischmann.me] I saw the exact same issue and realized the same thing that the number of messages in the file were much lower than what's reported by the log-cleaner. It is calculated based on the number in the filename as you suggested. 
I followed the approach that you suggested and renamed the 00000000000000000000.log file with something that fits inside the dedupe buffer( which is larger than the number of messages in the 00000000000000000000.log file) and it the log cleaner starts working again and cleans up the files)
~~~~

---

## KAFKA-4006: Kafka connect fails sometime with InvalidTopicException in distributed mode

https://issues.apache.org/jira/browse/KAFKA-4006

JIRA metadata: affects 0.10.0.0; fixed in 0.11.0.0

- `KAFKA-4006@0.10.0.0`: config 0.10.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-4006@1.0.0`: config 1.0.0, metadata answer **not_affected** (later_line)

Known Kafka versions mentioned in text: none

### Description

~~~~
I get trying to spin up a 3 node distributed connect cluster.

Sometimes one of the worker fails to boot with the following error when auto topic creation is enabled : 

org.apache.kafka.common.errors.InvalidTopicException: Topic 'default.config' is invalid 

default.config is the topic name for Connect config. 

Also, starting the worker again fixes the issue. 


~~~~

---

## KAFKA-4567: Connect Producer and Consumer ignore ssl parameters configured for worker

https://issues.apache.org/jira/browse/KAFKA-4567

JIRA metadata: affects 0.10.1.1; fixed in 0.11.0.0

- `KAFKA-4567@0.10.1.1`: config 0.10.1.1, metadata answer **affected** (listed_affected)
- `KAFKA-4567@0.11.0.1`: config 0.11.0.1, metadata answer **not_affected** (later_patch)

Known Kafka versions mentioned in text: none

### Description

~~~~
When using Connect with a SSL enabled Kafka cluster, the configuration options are either documented a bit misleading, or handled in an incorrect way.

The documentation states the usual available SSL options (ssl.keystore.location, ssl.truststore.location, ...) and these are picked up and used for the producers and consumers that are used to communicate with the status, offset and configs topics.
For the producers and consumers that are used for the actual data, these parameters are ignored as can be seen [here|https://github.com/apache/kafka/blob/trunk/connect/runtime/src/main/java/org/apache/kafka/connect/runtime/Worker.java#L98], which results in plaintext communication on an SSL port, leading to an OOM exception ([KAFKA-4493|https://issues.apache.org/jira/browse/KAFKA-4493]).

So in order to get Connect to communicate with a secured cluster you need to override all SSL configs with the prefixes _consumer._ and _producer._ and duplicate the values already set at a global level.

The documentation states: 

bq. The most critical site-specific options, such as the Kafka bootstrap servers, are already exposed via the standard worker configuration.

Since the address for the cluster is exposed here, I would propose that there is no reason not to also pass the SSL parameters through to the consumers and producers, as it is clearly intended that communication happens with the same cluster. 
In fringe cases, these can still be overridden manually to achieve different behavior.

I am happy to create a pull request to address this or clarify the docs, after we decide which one is the appropriate course of action.



~~~~

### Comments (3)

1.

~~~~
Given some future security features we may want to support (e.g. supporting different identities for different connectors), we probably don't want to just include the worker-level security configs into the producer & consumer. It's annoying to have to duplicate them now, but we probably want to support more flexible combinations in the future, such as having unique credentials for the workers (limiting the ability to, e.g., write to the config/offsets/status topics) than those used by producers and consumers (where we may want both unique credentials to apply ACLs and maybe support things like delegation tokens in the future).

So I think the short term solution is probably to just update the docs to clarify that you'll currently need the settings both at the worker level and prefixed by {{producer.}} and {{consumer.}} if you're trying to use the same credentials for worker, producer, and consumer.
~~~~

2.

~~~~
Alright.
I have added a small paragraph to the docs about this and created a pull request.
~~~~

3.

~~~~
Issue resolved by pull request 2511
[https://github.com/apache/kafka/pull/2511]
~~~~

---

## KAFKA-5088: some spelling error in code comment 

https://issues.apache.org/jira/browse/KAFKA-5088

JIRA metadata: affects 0.10.2.0; fixed in 0.11.0.0

- `KAFKA-5088@0.10.2.0`: config 0.10.2.0, metadata answer **affected** (listed_affected)
- `KAFKA-5088@0.11.0.1`: config 0.11.0.1, metadata answer **not_affected** (later_patch)

Known Kafka versions mentioned in text: none

### Description

~~~~
some spelling error in code comment ：
metadata==》metatdata...
metadata==》metatadata
propogated==》propagated
~~~~

### Comments (1)

1.

~~~~
Issue resolved by pull request 2871
[https://github.com/apache/kafka/pull/2871]
~~~~

---

## KAFKA-5098: KafkaProducer.send() blocks and generates TimeoutException if topic name has illegal char

https://issues.apache.org/jira/browse/KAFKA-5098

JIRA metadata: affects 0.10.2.0; fixed in 2.1.0

- `KAFKA-5098@0.10.2.0`: config 0.10.2.0, metadata answer **affected** (listed_affected)
- `KAFKA-5098@2.2.0`: config 2.2.0, metadata answer **not_affected** (later_line)

Known Kafka versions mentioned in text: 2.1.0, 2.0.0

### Description

~~~~
The server is running with auto create enabled. If we try to publish to a topic with a forward slash in the name, the call blocks and we get a TimeoutException in the Callback. I would expect it to return immediately with an InvalidTopicException.

There are other blocking issues that have been reported which may be related to some degree, but this particular cause seems unrelated.

Sample code:

{code}
import org.apache.kafka.clients.producer.*;
import java.util.*;

public class KafkaProducerUnexpectedBlockingAndTimeoutException {

  public static void main(String[] args) {
    Properties props = new Properties();
    props.put("bootstrap.servers", "kafka.example.com:9092");
    props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
    props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");
    props.put("max.block.ms", 10000); // 10 seconds should illustrate our point

    String separator = "/";
    //String separator = "_";

    try (Producer<String, String> producer = new KafkaProducer<>(props)) {

      System.out.println("Calling KafkaProducer.send() at " + new Date());
      producer.send(
          new ProducerRecord<String, String>("abc" + separator + "someStreamName",
              "Not expecting a TimeoutException here"),
          new Callback() {
            @Override
            public void onCompletion(RecordMetadata metadata, Exception e) {
              if (e != null) {
                System.out.println(e.toString());
              }
            }
          });
      System.out.println("KafkaProducer.send() completed at " + new Date());
    }


  }

}
{code}

Switching to the underscore separator in the above example works as expected.

Mea culpa: We neglected to research allowed chars in a topic name, but the TimeoutException we encountered did not help point us in the right direction.


~~~~

### Comments (6)

1.

~~~~
I will reproduce and work on this. 
~~~~

2.

~~~~
Issue resolved by pull request 3223
[https://github.com/apache/kafka/pull/3223]
~~~~

3.

~~~~
[~onurkaraman] correctly asked about the potential performance impact of doing this check for each producer record. I did some micro-benchmarking and it could be significant (particularly if the topic name is long). I reverted the change for now until we have a chance to verify its impact via `ProducerPerformance`.

I also submitted a PR that improves the performance of `Topic.validate()`:

https://github.com/apache/kafka/pull/3234
~~~~

4.

~~~~
[~huxi_2b] are you still working on this? If not, someone on our team at LinkedIn can help with picking this up.

Here is an alternate approach that avoids the performance concerns with the earlier one:
 * The producer's metadata cache could save the set of invalid topics (since the broker already indicates this in the metadata response).
 * On metadata response, update the metatadata cache's set of invalid topics if the metadata response carries errors due to invalid topics. In any subsequent send to invalid topics, the {{waitOnMetadata}} call would throw back the {{InvalidTopicException}}
 * This is pretty much similar to how we currently handle authorization exceptions.
~~~~

5.

~~~~
Moving this out to 2.1.0 since it is not ready for 2.0.0
~~~~

6.

~~~~
Since there was no response from the current Jira owner, I went ahead and created a PR for this issue.
~~~~

---

## KAFKA-5638: Inconsistency in consumer group related ACLs

https://issues.apache.org/jira/browse/KAFKA-5638

JIRA metadata: affects 0.11.0.0, 1.0.0; fixed in 2.1.0

- `KAFKA-5638@1.0.0`: config 1.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-5638@2.1.0`: config 2.1.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: none

### Description

~~~~
Users can see all groups in the cluster (using consumer group’s {{--list}} option) provided that they have {{Describe}} access to the cluster. It would make more sense to modify that experience and limit what is listed in the output to only those groups they have {{Describe}} access to. The reason is, almost everything else is accessible by a user only if the access is specifically granted (through ACL {{--add}}); and this scenario should not be an exception. The potential change would be updating the minimum required permission of {{ListGroup}} from {{Describe (Cluster)}} to {{Describe (Group)}}.

We can also look at this issue from a different angle: A user with {{Read}} access to a group can describe the group, but the same user would not see anything when listing groups (assuming there is no {{Describe}} access to the cluster). It makes more sense for this user to be able to list all groups s/he can already describe.

It would be great to know if any user is relying on the existing behavior (listing all consumer groups using a {{Describe (Cluster)}} ACL).
~~~~

### Comments (4)

1.

~~~~
[~vahid] Interesting point. Maybe we could just extend the current behavior? If the user has {{Describe(Cluster)}}, we can list all groups as we do currently. Otherwise, we can restrict the set of groups to only those that the user has {{Describe(Group)}} permission for?
~~~~

2.

~~~~
[~hachikuji] That should work too, and give us backward compatibility (is this why we would reject my suggested substitution?). I'm not sure why the required ACL was set to {{Describe(Cluster)}} in the first place. With your suggested extension I still think the inconsistency is still there, so in the long run it would make sense to get rid of the required cluster-level ACL (unless there is a sound logic behind it).

I assume extending the API would still require a KIP.
~~~~

3.

~~~~
Yes, compatibility is what I had in mind. I think my thought at the time was that {{Describe(Cluster)}} ought to imply {{Describe(Group:*)}}, but this may be the only case where we've used permission on one resource to imply permission on another (not sure about that). I guess we see this as incorrect usage? It would be nice to have some clear semantic guidelines for ACL usage since there does seem to be a few inconsistencies.

I think there's certainly an argument for treating the missing {{Describe(Group)}} check as a bug since listing the name of a group is less exposure than describing the group which is already possible with {{Describe(Group)}} permission. On the other hand, if we wanted to clean up the ACL model at the same time and drop the {{Describe(Cluster)}} permission, then a KIP would be necessary. Thoughts?
~~~~

4.

~~~~
The current usage is probably not incorrect, because the implication you mentioned makes sense. However, it is inconsistent. I also don't know of any other inferred permission like this one. That's the reason I raised the issue. Unless there is a big push back, I would like to take the KIP approach and fix this inconsistency by dropping the {{Describe(Cluster)}} check from the API and introducing a {{Describe(Group)}} permission requirement. If there is push back, we can do the latter only and implement what you suggested above. If you are okay with this approach I'll start drafting the KIP.
~~~~

---

## KAFKA-5735: Client-ids are not handled consistently by clients and broker

https://issues.apache.org/jira/browse/KAFKA-5735

JIRA metadata: affects 0.11.0.0; fixed in 1.0.0

- `KAFKA-5735@0.11.0.0`: config 0.11.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-5735@1.0.1`: config 1.0.1, metadata answer **not_affected** (later_patch)

Known Kafka versions mentioned in text: none

### Description

~~~~
At the moment, Java clients expect client-ids to use a limited set of characters so that they can be used without quoting in metrics. kafka-configs.sh allows quotas to be defined only for that limited set. But the broker does not validate client-ids. And the documentation does not mention any limitations. Existing non-Java clients do not place any restrictions on client-ids and hence introducing restrictions on the broker-side now will be a breaking change. So we should allow any characters and treat them consistently in the same way as we handle user principals.

Changes required:
1. Client-id in metrics should be sanitized using URL-encoding similar to the encoding used for user principal in quota metrics. This leaves metrics for client-ids using the current limited set of characters as-is, but will allow arbitrary characters in encoded form. To avoid sanitizing multiple times and to avoid unsanitized ids being used by mistake in some metrics, it may be better to introduce a ClientId class that stores the sanitized id and uses appropriate methods to retrieve the id for metrics etc.
2. Quota metrics and sensors as well as ZooKeeper quota configuration paths should use sanitized ids for client-ids (they already do for user principal).
3. Remove client-id validation in kafka-configs.sh and allow any characters for client-id similar to usernames, URL-encoding the names to generate ZK path.

~~~~

### Comments (1)

1.

~~~~
Issue resolved by pull request 3906
[https://github.com/apache/kafka/pull/3906]
~~~~

---

## KAFKA-5890: records.lag should use tags for topic and partition rather than using metric name.

https://issues.apache.org/jira/browse/KAFKA-5890

JIRA metadata: affects 0.10.2.0; fixed in 1.1.0

- `KAFKA-5890@0.10.2.0`: config 0.10.2.0, metadata answer **affected** (listed_affected)
- `KAFKA-5890@1.1.1`: config 1.1.1, metadata answer **not_affected** (later_patch)

Known Kafka versions mentioned in text: none

### Description

~~~~
As part of KIP-92[1] a per partition lag metric was added.

These metrics are really useful, however in the implementation  it was implemented as a prefix to the metric name: https://github.com/apache/kafka/blob/trunk/clients/src/main/java/org/apache/kafka/clients/consumer/internals/Fetcher.java#L1321-L1344

Usually these kind of metrics use tags and the name is constant for all topics, partitions.

We have a custom reporter which aggregates topics/partitions together to avoid explosion of the number of KPIs and this KPI doesn't support this as it doesn't have tags but a complex name.

[1] https://cwiki.apache.org/confluence/display/KAFKA/KIP-92+-+Add+per+partition+lag+metrics+to+KafkaConsumer
~~~~

### Comments (5)

1.

~~~~
I noticed the same thing in https://github.com/apache/kafka/pull/2993

Metric names are a public API, and so would require a KIP before changes could be made. Is that something you want to take on?
~~~~

2.

~~~~
That's what I was expecting. I'll try to get a KIP written this week.
~~~~

3.

~~~~
Hey [~wushujames] I've finally got around to open a kip about this if you want to have a look: https://cwiki.apache.org/confluence/pages/viewpage.action?pageId=74686649
~~~~

4.

~~~~
https://github.com/apache/kafka/pull/4362
~~~~

5.

~~~~
This got merged and I opened KAFKA-6445 to track the removing the old metrics.
~~~~

---

## KAFKA-6327: IllegalArgumentException in RocksDB when RocksDBException being generated

https://issues.apache.org/jira/browse/KAFKA-6327

JIRA metadata: affects 1.0.0; fixed in 2.1.0

- `KAFKA-6327@1.0.0`: config 1.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-6327@2.1.1`: config 2.1.1, metadata answer **not_affected** (later_patch)

Known Kafka versions mentioned in text: 2.1

### Description

~~~~
RocksDB had a bug where RocksDBException subCodes related to disk usage were not present and when a RocksDBException is generated for those it throws an IllegalArgumentException instead obscuring the error. This is [fixed|https://github.com/facebook/rocksdb/pull/3050] in RocksDB master but doesn't appear to have been released yet. Adding this issue so that it can be tracked for a future release.

Exception:

{noformat}
java.lang.IllegalArgumentException: Illegal value provided for SubCode.
	at org.rocksdb.Status$SubCode.getSubCode(Status.java:109)
	at org.rocksdb.Status.<init>(Status.java:30)
	at org.rocksdb.RocksDB.write0(Native Method)
	at org.rocksdb.RocksDB.write(RocksDB.java:602)
{noformat}

~~~~

### Comments (3)

1.

~~~~
Thanks for the heads up [~nyokodo]!
~~~~

2.

~~~~
This will be fixed in RocksDB release rocksdb-5.9.2 and beyond, most likely in v5.10.3.
~~~~

3.

~~~~
We have upgraded rocksDB version in trunk (upcoming 2.1 release) to 5.14.2 and hence should have fixed this issue.
~~~~

---

## KAFKA-7165: Error while creating ephemeral at /brokers/ids/BROKER_ID

https://issues.apache.org/jira/browse/KAFKA-7165

JIRA metadata: affects 1.1.0; fixed in 2.2.0

- `KAFKA-7165@1.1.0`: config 1.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-7165@2.2.0`: config 2.2.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 1.1.0, 2.0

### Description

~~~~
Kafka version: 1.1.0

Zookeeper version: 3.4.12

4 Kafka Brokers

4 Zookeeper servers

 

In one of the 4 brokers of the cluster, we detect the following error:

[2018-07-14 04:38:23,784] INFO Unable to read additional data from server sessionid 0x3000c2420cb458d, likely server has closed socket, closing socket connection and attempting reconnect (org.apache.zookeeper.ClientCnxn)
 [2018-07-14 04:38:24,509] INFO Opening socket connection to server *ZOOKEEPER_SERVER_1:PORT*. Will not attempt to authenticate using SASL (unknown error) (org.apache.zookeeper.ClientCnxn)
 [2018-07-14 04:38:24,510] INFO Socket connection established to *ZOOKEEPER_SERVER_1:PORT*, initiating session (org.apache.zookeeper.ClientCnxn)
 [2018-07-14 04:38:24,513] INFO Unable to read additional data from server sessionid 0x3000c2420cb458d, likely server has closed socket, closing socket connection and attempting reconnect (org.apache.zookeeper.ClientCnxn)
 [2018-07-14 04:38:25,287] INFO Opening socket connection to server *ZOOKEEPER_SERVER_2:PORT*. Will not attempt to authenticate using SASL (unknown error) (org.apache.zookeeper.ClientCnxn)
 [2018-07-14 04:38:25,287] INFO Socket connection established to *ZOOKEEPER_SERVER_2:PORT*, initiating session (org.apache.zookeeper.ClientCnxn)
 [2018-07-14 04:38:25,954] INFO [Partition TOPIC_NAME-PARTITION-# broker=1|#* broker=1] Shrinking ISR from 1,3,4,2 to 1,4,2 (kafka.cluster.Partition)
 [2018-07-14 04:38:26,444] WARN Unable to reconnect to ZooKeeper service, session 0x3000c2420cb458d has expired (org.apache.zookeeper.ClientCnxn)
 [2018-07-14 04:38:26,444] INFO Unable to reconnect to ZooKeeper service, session 0x3000c2420cb458d has expired, closing socket connection (org.apache.zookeeper.ClientCnxn)
 [2018-07-14 04:38:26,445] INFO EventThread shut down for session: 0x3000c2420cb458d (org.apache.zookeeper.ClientCnxn)
 [2018-07-14 04:38:26,446] INFO [ZooKeeperClient] Session expired. (kafka.zookeeper.ZooKeeperClient)
 [2018-07-14 04:38:26,459] INFO [ZooKeeperClient] Initializing a new session to *ZOOKEEPER_SERVER_1:PORT*,*ZOOKEEPER_SERVER_2:PORT*,*ZOOKEEPER_SERVER_3:PORT*,*ZOOKEEPER_SERVER_4:PORT*. (kafka.zookeeper.ZooKeeperClient)
 [2018-07-14 04:38:26,459] INFO Initiating client connection, connectString=*ZOOKEEPER_SERVER_1:PORT*,*ZOOKEEPER_SERVER_2:PORT*,*ZOOKEEPER_SERVER_3:PORT*,*ZOOKEEPER_SERVER_4:PORT* sessionTimeout=6000 watcher=kafka.zookeeper.ZooKeeperClient$ZooKeeperClientWatcher$@44821a96 (org.apache.zookeeper.ZooKeeper)
 [2018-07-14 04:38:26,465] INFO Opening socket connection to server *ZOOKEEPER_SERVER_1:PORT*. Will not attempt to authenticate using SASL (unknown error) (org.apache.zookeeper.ClientCnxn)
 [2018-07-14 04:38:26,477] INFO Socket connection established to *ZOOKEEPER_SERVER_1:PORT*, initiating session (org.apache.zookeeper.ClientCnxn)
 [2018-07-14 04:38:26,484] INFO Session establishment complete on server *ZOOKEEPER_SERVER_1:PORT*, sessionid = 0x4005b59eb6a0000, negotiated timeout = 6000 (org.apache.zookeeper.ClientCnxn)
 [2018-07-14 04:38:26,496] *INFO Creating /brokers/ids/1* (is it secure? false) (kafka.zk.KafkaZkClient)
 [2018-07-14 04:38:26,500] INFO Processing notification(s) to /config/changes (kafka.common.ZkNodeChangeNotificationListener)
 *[2018-07-14 04:38:26,547] ERROR Error while creating ephemeral at /brokers/ids/1, node already exists and owner '216186131422332301' does not match current session '288330817911521280' (kafka.zk.KafkaZkClient$CheckedEphemeral)*
 [2018-07-14 04:38:26,547] *INFO Result of znode creation at /brokers/ids/1 is: NODEEXISTS* (kafka.zk.KafkaZkClient)
 [2018-07-14 04:38:26,559] ERROR Uncaught exception in scheduled task 'isr-expiration' (kafka.utils.KafkaScheduler)

org.apache.zookeeper.KeeperException$SessionExpiredException: KeeperErrorCode = Session expired for /brokers/topics/*TOPIC_NAME*/partitions/*PARTITION-#*/state
 at org.apache.zookeeper.KeeperException.create(KeeperException.java:127)
 at org.apache.zookeeper.KeeperException.create(KeeperException.java:51)
 at kafka.zookeeper.AsyncResponse.resultException(ZooKeeperClient.scala:465)
 at kafka.zk.KafkaZkClient.conditionalUpdatePath(KafkaZkClient.scala:621)
 at kafka.utils.ReplicationUtils$.updateLeaderAndIsr(ReplicationUtils.scala:33)
 at kafka.cluster.Partition.kafka$cluster$Partition$$updateIsr(Partition.scala:669)
 at kafka.cluster.Partition$$anonfun$4.apply$mcZ$sp(Partition.scala:513)
 at kafka.cluster.Partition$$anonfun$4.apply(Partition.scala:504)
 at kafka.cluster.Partition$$anonfun$4.apply(Partition.scala:504)
 at kafka.utils.CoreUtils$.inLock(CoreUtils.scala:250)
 at kafka.utils.CoreUtils$.inWriteLock(CoreUtils.scala:258)
 at kafka.cluster.Partition.maybeShrinkIsr(Partition.scala:503)
 at kafka.server.ReplicaManager$$anonfun$kafka$server$ReplicaManager$$maybeShrinkIsr$2.apply(ReplicaManager.scala:1335)
 at kafka.server.ReplicaManager$$anonfun$kafka$server$ReplicaManager$$maybeShrinkIsr$2.apply(ReplicaManager.scala:1335)
 at scala.collection.Iterator$class.foreach(Iterator.scala:891)
 at scala.collection.AbstractIterator.foreach(Iterator.scala:1334)
 at kafka.server.ReplicaManager.kafka$server$ReplicaManager$$maybeShrinkIsr(ReplicaManager.scala:1335)
 at kafka.server.ReplicaManager$$anonfun$2.apply$mcV$sp(ReplicaManager.scala:322)
 at kafka.utils.KafkaScheduler$$anonfun$1.apply$mcV$sp(KafkaScheduler.scala:110)
 at kafka.utils.CoreUtils$$anon$1.run(CoreUtils.scala:62)
 at java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:511)
 at java.util.concurrent.FutureTask.runAndReset(FutureTask.java:308)
 at java.util.concurrent.ScheduledThreadPoolExecutor$ScheduledFutureTask.access$301(ScheduledThreadPoolExecutor.java:180)
 at java.util.concurrent.ScheduledThreadPoolExecutor$ScheduledFutureTask.run(ScheduledThreadPoolExecutor.java:294)
 at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
 at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
 at java.lang.Thread.run(Thread.java:748)

[2018-07-14 04:38:45,938] INFO [Partition TOPIC_NAME-PARTITION-# broker=1|#* broker=1] Shrinking ISR from 1,3,4,2 to 1 (kafka.cluster.Partition)
 [2018-07-14 04:38:45,952] INFO [Partition TOPIC_NAME-PARTITION-# broker=1|#* broker=1] Cached zkVersion [0] not equal to that in zookeeper, skip updating ISR (kafka.cluster.Partition)
 [2018-07-14 04:38:45,952] INFO [Partition __consumer_offsets-# broker=1|#* broker=1] Shrinking ISR from 1,2,3,4 to 1 (kafka.cluster.Partition)
 [2018-07-14 04:38:45,992] INFO [Partition __consumer_offsets-# broker=1|#* broker=1] Cached zkVersion [139] not equal to that in zookeeper, skip updating ISR (kafka.cluster.Partition)

...

...

 

The previous exception continues showing constantly without stopping. Since the cluster was still up, I have left the error showing up for about 6 hours to check if the broker recovers itself.

The only solution, to put back the broker into the cluster, was restarting.

After the restart, the replicas sync each other and the broker was able to serve again.

I imagine this is not a normal behavior.
~~~~

### Comments (17)

1.

~~~~
Looks like related to *KAFKA-6584*
~~~~

2.

~~~~
Yes, [~omkreddy] seems to be related, do you know what's the status of this? I mean, is somebody working on it? if not, I would like to collaborate, if feasible.

 

Cheers!

 
~~~~

3.

~~~~
[~pachilo]  I think we are waiting for  ZOOKEEPER-2985  fix.  If you are interested, you can work on handling the edge case on Kafka side.
~~~~

4.

~~~~
cc [~junrao] [~cmccabe]
~~~~

5.

~~~~
Ok [~omkreddy], I will get myself familiarized with the code to understand the edge case you are mentioning.
~~~~

6.

~~~~
Hello [~omkreddy]

Before doing any code, I would like to share with you all, what I have verified.

At the *kafka.zk.KafkaZkClient* class, when the broker needs to be registered:

 
{code:java}
def registerBroker(brokerInfo: BrokerInfo): Unit = {
 val path = brokerInfo.path
 checkedEphemeralCreate(path, brokerInfo.toJsonBytes)
 info(s"Registered broker ${brokerInfo.broker.id} at path $path with addresses: ${brokerInfo.broker.endPoints}")
}{code}
 

 The method:

 
{code:java}
private def checkedEphemeralCreate(path: String, data: Array[Byte]): Unit = {
 val checkedEphemeral = new CheckedEphemeral(path, data)
 info(s"Creating $path (is it secure? $isSecure)")
 val code = checkedEphemeral.create()
 info(s"Result of znode creation at $path is: $code")
 if (code != Code.OK)
 throw KeeperException.create(code)
}{code}
 

Is already checking if the node creation code was successful:
{code:java}
if (code != Code.OK){code}
 

What you all think about first checking if the code is equal to NODEEXISTS: 
{code:java}
if (code == Code.NODEEXISTS)
{code}
 

If that the case, delete that ephemeral node (_/brokers/ids/BROKER_ID_) in Zookeeper, and then trying to register the broker again.

The ephemeral node (_/brokers/ids/BROKER_ID_) is associated with the expired/previous session, that's what I do not know if that makes sense/or possible to do.

 

The method will look like:
{code:java}
private def checkedEphemeralCreate(path: String, data: Array[Byte]): Unit = {
 val checkedEphemeral = new CheckedEphemeral(path, data)
 info(s"Creating $path (is it secure? $isSecure)")
 val code = checkedEphemeral.create()
 info(s"Result of znode creation at $path is: $code")

 if (code == Code.NODEEXISTS) {
   checkedEphemeral.delete() // Not yet created method
   code = checkedEphemeral.create()
   info(s"Result of znode re-creation at $path is: $code")
 }

 if (code != Code.OK)
   throw KeeperException.create(code)
}{code}
 

How that looks like?

 
~~~~

7.

~~~~
[~pachilo]   your solution may work, but we should be careful not to remove the ephemeral nodes created by another broker. if someone starts a broker with same brokerId, then the registration should fail. 

Another option is to maintain previous zk session id and do a check [here|https://github.com/apache/kafka/blob/90e0bbec94dd85e1c5b1af0b6426df0a02e5da3f/core/src/main/scala/kafka/zk/KafkaZkClient.scala#L1512].
 If the owner matches with previous sessionID, we can delete and recreate the node.

[~cthunes]  Since you have analyzed the ZOOKEEPER-2985, any thoughts on handling this on Kafka side. also can you share the code to reproduce this this issue?
~~~~

8.

~~~~
Sure [~omkreddy] , it makes sense, some misconfiguration could lead having two or more brokers with the same id (not ideal situation).

I will wait for [~cthunes] opinion and considerations.

 

Cheers!
~~~~

9.

~~~~
One option would be to put a retry mechanism around the broker registration. When this bug is triggered, the existing (conflicting) node will be an ephemeral node associated with the old session. This session will eventually re-expire (since the client has established a new session to replace it) at which time the old broker ID node will be deleted.

This expiration should take at most a bit longer than the configured session timeout.

If two brokers have been misconfigured with the same broker ID than the first server will be registered and the second will be stuck retrying indefinitely (or until the first server stops).
~~~~

10.

~~~~
Hello [~omkreddy] and [~cthunes] , thanks a lot for the feedback.

According to the opinions, what could be the next step?

 

Cheers!
~~~~

11.

~~~~
Hi, [~omkreddy] [~ijuma], am working on a PR, who can help me and assign this Jira to me? I can not do it by myself.

 

Cheers!
~~~~

12.

~~~~
[~pachilo] Please send a mail to dev mailing list for Jira access.
~~~~

13.

~~~~
Done [~omkreddy], let's wait, thanks!
~~~~

14.

~~~~
Hello Jun Rao, I would like to continue working on this bug, hope you can have some time to elaborate a little bit more your proposal from [https://github.com/apache/kafka/pull/5575#issuecomment-416419017:]

 
{noformat}
An alternative approach is to retry the creation of the ephemeral node up to sth like twice the session timeout. It may take a bit long for the broker to be re-registered. However, it seems it's a bit safer and simpler, until ZOOKEEPER-2985 is fixed.{noformat}
 

Cheers,

–

Jonathan
~~~~

15.

~~~~
[~pachilo], your PR actually looks reasonable for addressing the issue of creating the ephemeral node. I am not sure if it addresses the org.apache.zookeeper.KeeperException$SessionExpiredException in the isr expiration thread. The failure of the creation of the ephemeral node shouldn't prevent the new ZK session being created. So, I am wondering why the SessionExpiredException continued for 6 hours. Were there extended network issue with the ZK cluster?
~~~~

16.

~~~~
Thanks for your reply [~junrao] , that was the only time we had that issue of the _org.apache.zookeeper.KeeperException$SessionExpiredException_ so far.

Now we are in version 2.0 of Kafka and from time to time suffering the *NODEEXISTS* issue.

Maybe the errors were related but difficult to ensure that, hopefully with the fix, we can get rid of the *NODEEXISTS* error.

 

Cheers!
~~~~

17.

~~~~
Merged to trunk.
~~~~

---

## KAFKA-7379: send.buffer.bytes should be allowed to set -1 in KafkaStreams

https://issues.apache.org/jira/browse/KAFKA-7379

JIRA metadata: affects 0.10.2.2, 0.11.0.3, 1.0.2, 1.1.1, 2.0.0; fixed in 2.1.0

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

JIRA metadata: affects 2.0.0; fixed in 2.0.1, 2.1.0

- `KAFKA-7386@2.0.0`: config 2.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-7386@2.2.0`: config 2.2.0, metadata answer **not_affected** (later_line)

Known Kafka versions mentioned in text: none

### Description

~~~~
for example, [https://github.com/apache/kafka/blob/trunk/streams/streams-scala/src/main/scala/org/apache/kafka/streams/scala/Serdes.scala#L28] invokes Serdes.String() once and caches the result.

However, the implementation of the String serde has a non-empty configure method that is variant in whether it's used as a key or value serde. So we won't get correct execution if we create one serde and use it for both keys and values.

The fix is simple: change all the `val` declarations in scala.Serdes to `def`. Thanks to the referential transparency for parameterless methods in scala, no user-facing code will break.
~~~~

---

## KAFKA-7633: Kafka Connect requires permission to create internal topics even if they exist

https://issues.apache.org/jira/browse/KAFKA-7633

JIRA metadata: affects 1.1.0; fixed in 2.0.2, 2.1.2, 2.2.1

- `KAFKA-7633@1.1.0`: config 1.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-7633@2.2.2`: config 2.2.2, metadata answer **not_affected** (later_patch)

Known Kafka versions mentioned in text: 2.0, 1.1

### Description

~~~~
Similar to issue https://issues.apache.org/jira/browse/KAFKA-6250 but now with a different exception.

Error is:
{code:java}
018-11-13 16:14:10,283 [DistributedHerder] ERROR o.a.k.c.r.d.DistributedHerder - Uncaught exception in herder work thread, exiting:
org.apache.kafka.connect.errors.ConnectException: Error while attempting to create/find topic(s) 'connect-offsets'
        at org.apache.kafka.connect.util.TopicAdmin.createTopics(TopicAdmin.java:255)
        at org.apache.kafka.connect.storage.KafkaOffsetBackingStore$1.run(KafkaOffsetBackingStore.java:100)
        at org.apache.kafka.connect.util.KafkaBasedLog.start(KafkaBasedLog.java:126)
        at org.apache.kafka.connect.storage.KafkaOffsetBackingStore.start(KafkaOffsetBackingStore.java:110)
        at org.apache.kafka.connect.runtime.Worker.start(Worker.java:144)
        at org.apache.kafka.connect.runtime.AbstractHerder.startServices(AbstractHerder.java:108)
        at org.apache.kafka.connect.runtime.distributed.DistributedHerder.run(DistributedHerder.java:211)
        at java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:511)
        at java.util.concurrent.FutureTask.run(FutureTask.java:266)
        at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1142)
        at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:617)
        at java.lang.Thread.run(Thread.java:745)
Caused by: java.util.concurrent.ExecutionException: org.apache.kafka.common.errors.TopicAuthorizationException: Not authorized to access topics: [Topic authorization failed.]
        at org.apache.kafka.common.internals.KafkaFutureImpl.wrapAndThrow(KafkaFutureImpl.java:45)
        at org.apache.kafka.common.internals.KafkaFutureImpl.access$000(KafkaFutureImpl.java:32)
        at org.apache.kafka.common.internals.KafkaFutureImpl$SingleWaiter.await(KafkaFutureImpl.java:89)
        at org.apache.kafka.common.internals.KafkaFutureImpl.get(KafkaFutureImpl.java:258)
        at org.apache.kafka.connect.util.TopicAdmin.createTopics(TopicAdmin.java:228)
        ... 11 common frames omitted
Caused by: org.apache.kafka.common.errors.TopicAuthorizationException: Not authorized to access topics: [Topic authorization failed.]
{code}
Kafka 2.0 uses TOPIC_AUTHORIZATION_FAILED(29) as a response code now in the [CreateTopicsResponse|https://github.com/apache/kafka/blob/trunk/clients/src/main/java/org/apache/kafka/common/requests/CreateTopicsResponse.java] class whereas it used CLUSTER_AUTHORIZATION_FAILED(31) in Kafka 1.1 [for example|https://github.com/apache/kafka/blob/1.1/clients/src/main/java/org/apache/kafka/common/requests/CreateTopicsResponse.java]
~~~~

### Comments (3)

1.

~~~~
Hey [~gavriep], do you mind taking a look at this since you created the original patch?
~~~~

2.

~~~~
[~arabelle]: Sorry, but I haven't been working with Kafka for quite a while now and no longer have the relevant setup ready.
~~~~

3.

~~~~
Which version ([https://hub.docker.com/r/confluentinc/cp-kafka-connect/tags]) of Kafka Connect docker image would have this fix ? If not, how do we get this fix pushed to docker hub as well ?
~~~~

---

## KAFKA-7776: Kafka Connect values converter parsing of ISO8601 not working properly

https://issues.apache.org/jira/browse/KAFKA-7776

JIRA metadata: affects 1.1.0, 2.0.0; fixed in 4.1.0

- `KAFKA-7776@1.1.0`: config 1.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-7776@1.0.2`: config 1.0.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
In org.apache.kafka.connect.data.Values, the Values.convertToDate/Time/Timestamp methods are intended to be able to accept Strings in ISO8601 format and convert into the Kafka Connect formats. However, the parser for strings incorrectly tokenizes the strings (having real trouble with colons) which means that the correct ISO8601 format is never actual presented as a single piece to the code that converts it into java.util.Date.

The parser needs to be enhanced to accept an ISO8601 string as a single token, probably only when it knows that the intended use is as one of the date-based logical types.
~~~~

### Comments (1)

1.

~~~~
The parsing has been fixed since this ancient issue was originally created, but the tests have not been updated. I'll use the issue to fix the tests.
~~~~

---

## KAFKA-7921: Instable KafkaStreamsTest

https://issues.apache.org/jira/browse/KAFKA-7921

JIRA metadata: affects 2.3.0; fixed in 2.4.0

- `KAFKA-7921@2.3.0`: config 2.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-7921@2.4.0`: config 2.4.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 2.3.0, 2.2

### Description

~~~~
{{KafkaStreamsTest}} failed multiple times, eg,
{quote}java.lang.AssertionError: Condition not met within timeout 15000. Streams never started.
at org.apache.kafka.test.TestUtils.waitForCondition(TestUtils.java:365)
at org.apache.kafka.test.TestUtils.waitForCondition(TestUtils.java:325)
at org.apache.kafka.streams.KafkaStreamsTest.shouldThrowOnCleanupWhileRunning(KafkaStreamsTest.java:556){quote}
or
{quote}java.lang.AssertionError: Condition not met within timeout 15000. Streams never started.
at org.apache.kafka.test.TestUtils.waitForCondition(TestUtils.java:365)
at org.apache.kafka.test.TestUtils.waitForCondition(TestUtils.java:325)
at org.apache.kafka.streams.KafkaStreamsTest.testStateThreadClose(KafkaStreamsTest.java:255){quote}
 
The preserved logs are as follows:

{quote}[2019-02-12 07:02:17,198] INFO Kafka version: 2.3.0-SNAPSHOT (org.apache.kafka.common.utils.AppInfoParser:109)
[2019-02-12 07:02:17,198] INFO Kafka commitId: 08036fa4b1e5b822 (org.apache.kafka.common.utils.AppInfoParser:110)
[2019-02-12 07:02:17,199] INFO stream-client [clientId] State transition from CREATED to REBALANCING (org.apache.kafka.streams.KafkaStreams:263)
[2019-02-12 07:02:17,200] INFO stream-thread [clientId-StreamThread-238] Starting (org.apache.kafka.streams.processor.internals.StreamThread:767)
[2019-02-12 07:02:17,200] INFO stream-client [clientId] State transition from REBALANCING to PENDING_SHUTDOWN (org.apache.kafka.streams.KafkaStreams:263)
[2019-02-12 07:02:17,200] INFO stream-thread [clientId-StreamThread-239] Starting (org.apache.kafka.streams.processor.internals.StreamThread:767)
[2019-02-12 07:02:17,200] INFO stream-thread [clientId-StreamThread-238] State transition from CREATED to STARTING (org.apache.kafka.streams.processor.internals.StreamThread:214)
[2019-02-12 07:02:17,200] INFO stream-thread [clientId-StreamThread-239] State transition from CREATED to STARTING (org.apache.kafka.streams.processor.internals.StreamThread:214)
[2019-02-12 07:02:17,200] INFO stream-thread [clientId-StreamThread-238] Informed to shut down (org.apache.kafka.streams.processor.internals.StreamThread:1192)
[2019-02-12 07:02:17,201] INFO stream-thread [clientId-StreamThread-238] State transition from STARTING to PENDING_SHUTDOWN (org.apache.kafka.streams.processor.internals.StreamThread:214)
[2019-02-12 07:02:17,201] INFO stream-thread [clientId-StreamThread-239] Informed to shut down (org.apache.kafka.streams.processor.internals.StreamThread:1192)
[2019-02-12 07:02:17,201] INFO stream-thread [clientId-StreamThread-239] State transition from STARTING to PENDING_SHUTDOWN (org.apache.kafka.streams.processor.internals.StreamThread:214)
[2019-02-12 07:02:17,205] INFO Cluster ID: J8uJhiTKQx-Y_i9LzT0iLg (org.apache.kafka.clients.Metadata:365)
[2019-02-12 07:02:17,205] INFO Cluster ID: J8uJhiTKQx-Y_i9LzT0iLg (org.apache.kafka.clients.Metadata:365)
[2019-02-12 07:02:17,205] INFO [Consumer clientId=clientId-StreamThread-238-consumer, groupId=appId] Discovered group coordinator localhost:36122 (id: 2147483647 rack: null) (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:675)
[2019-02-12 07:02:17,205] INFO [Consumer clientId=clientId-StreamThread-239-consumer, groupId=appId] Discovered group coordinator localhost:36122 (id: 2147483647 rack: null) (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:675)
[2019-02-12 07:02:17,206] INFO [Consumer clientId=clientId-StreamThread-238-consumer, groupId=appId] Revoking previously assigned partitions [] (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:458)
[2019-02-12 07:02:17,206] INFO [Consumer clientId=clientId-StreamThread-239-consumer, groupId=appId] Revoking previously assigned partitions [] (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:458)
[2019-02-12 07:02:17,206] INFO [Consumer clientId=clientId-StreamThread-238-consumer, groupId=appId] (Re-)joining group (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:491)
[2019-02-12 07:02:17,206] INFO [Consumer clientId=clientId-StreamThread-239-consumer, groupId=appId] (Re-)joining group (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:491)
[2019-02-12 07:02:17,208] INFO [Consumer clientId=clientId-StreamThread-239-consumer, groupId=appId] (Re-)joining group (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:491)
[2019-02-12 07:02:17,208] INFO [Consumer clientId=clientId-StreamThread-238-consumer, groupId=appId] (Re-)joining group (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:491)
[2019-02-12 07:02:17,278] INFO Cluster ID: J8uJhiTKQx-Y_i9LzT0iLg (org.apache.kafka.clients.Metadata:365)
[2019-02-12 07:02:17,293] INFO Cluster ID: J8uJhiTKQx-Y_i9LzT0iLg (org.apache.kafka.clients.Metadata:365)
[2019-02-12 07:02:17,301] INFO stream-thread [clientId-StreamThread-239] Shutting down (org.apache.kafka.streams.processor.internals.StreamThread:1206)
[2019-02-12 07:02:17,301] INFO [Consumer clientId=clientId-StreamThread-239-restore-consumer, groupId=null] Unsubscribed all topics or patterns and assigned partitions (org.apache.kafka.clients.consumer.KafkaConsumer:1042)
[2019-02-12 07:02:17,301] INFO stream-thread [clientId-StreamThread-238] Shutting down (org.apache.kafka.streams.processor.internals.StreamThread:1206)
[2019-02-12 07:02:17,301] INFO [Consumer clientId=clientId-StreamThread-238-restore-consumer, groupId=null] Unsubscribed all topics or patterns and assigned partitions (org.apache.kafka.clients.consumer.KafkaConsumer:1042)
[2019-02-12 07:02:17,302] INFO [Producer clientId=clientId-StreamThread-238-producer] Closing the Kafka producer with timeoutMillis = 9223372036854775807 ms. (org.apache.kafka.clients.producer.KafkaProducer:1139)
[2019-02-12 07:02:17,301] INFO [Producer clientId=clientId-StreamThread-239-producer] Closing the Kafka producer with timeoutMillis = 9223372036854775807 ms. (org.apache.kafka.clients.producer.KafkaProducer:1139)
[2019-02-12 07:02:17,863] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:18,766] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:19,769] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:20,872] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:21,775] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:22,678] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:23,882] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:24,885] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:25,888] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:26,991] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:28,095] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:28,998] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:29,901] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:31,004] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:32,108] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:33,311] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:34,515] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:35,718] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:36,921] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:37,924] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:38,927] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:40,029] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:41,232] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:42,235] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:43,337] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:44,340] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:45,442] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:46,444] WARN [AdminClient clientId=adminclient-233] Connection to node 0 (localhost/127.0.0.1:41539) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient:722)
[2019-02-12 07:02:47,305] WARN [Consumer clientId=clientId-StreamThread-239-consumer, groupId=appId] Close timed out with 1 pending requests to coordinator, terminating client connections (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:800)
[2019-02-12 07:02:47,307] INFO stream-thread [clientId-StreamThread-239] State transition from PENDING_SHUTDOWN to DEAD (org.apache.kafka.streams.processor.internals.StreamThread:214)
[2019-02-12 07:02:47,307] INFO stream-thread [clientId-StreamThread-239] Shutdown complete (org.apache.kafka.streams.processor.internals.StreamThread:1226)
[2019-02-12 07:02:47,308] WARN [Consumer clientId=clientId-StreamThread-238-consumer, groupId=appId] Close timed out with 1 pending requests to coordinator, terminating client connections (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:800)
[2019-02-12 07:02:47,313] INFO stream-thread [clientId-StreamThread-238] State transition from PENDING_SHUTDOWN to DEAD (org.apache.kafka.streams.processor.internals.StreamThread:214)
[2019-02-12 07:02:47,313] INFO stream-thread [clientId-StreamThread-238] Shutdown complete (org.apache.kafka.streams.processor.internals.StreamThread:1226)
[2019-02-12 07:02:47,315] INFO stream-client [clientId] State transition from PENDING_SHUTDOWN to NOT_RUNNING (org.apache.kafka.streams.KafkaStreams:263)
[2019-02-12 07:02:47,315] INFO stream-client [clientId] Streams client stopped completely (org.apache.kafka.streams.KafkaStreams:899)
[2019-02-12 07:02:47,316] INFO stream-client [clientId] Already in the pending shutdown state, wait to complete shutdown (org.apache.kafka.streams.KafkaStreams:849)
[2019-02-12 07:02:47,316] INFO stream-client [clientId] Streams client stopped completely (org.apache.kafka.streams.KafkaStreams:899){quote}
 
Note, that the instance goes from
{quote}[2019-02-12 07:02:17,199] INFO stream-client [clientId] State transition from CREATED to REBALANCING (org.apache.kafka.streams.KafkaStreams:263){quote}
to
{quote}[2019-02-12 07:02:17,200] INFO stream-client [clientId] State transition from REBALANCING to PENDING_SHUTDOWN (org.apache.kafka.streams.KafkaStreams:263){quote}
in the very beginning. It's unclear why this happens. Note, that the log before the copied snipped is unfortunately not complete (thank you Jenkins):
{quote}...[truncated 1593438 chars]...{quote}
Later, `AdminClient` seems to not be able to connect to the brokers (also unclear why) and the test times out. If the `AdminClient` issue is related to the first issue is unclear atm).
~~~~

### Comments (8)

1.

~~~~
Note that in a recent commit we've updated {{InternalTopicManager}} so that if topic creation / list topics return fatal errors it would be logged. So if we did not find it in the logs it means not related to admin-client creating topics.

The "informed shutdown" can only be triggered from two places: 1) KafkaStreams#close() call, which should not be the case (there's no caller at that time). or 2):

{code}
if (streamThread.assignmentErrorCode.get() == StreamsPartitionAssignor.Error.INCOMPLETE_SOURCE_TOPIC_METADATA.code()) {
                log.debug("Received error code {} - shutdown", streamThread.assignmentErrorCode.get());
                streamThread.shutdown();
                streamThread.setStateListener(null);
                return;
            }
{code}

This indicates that the source topics are not available yet:

{code}
for (final InternalTopologyBuilder.TopicsInfo topicsInfo : topicGroups.values()) {
            for (final String topic : topicsInfo.sourceTopics) {
                if (!topicsInfo.repartitionSourceTopics.keySet().contains(topic) &&
                    !metadata.topics().contains(topic)) {
                    return errorAssignment(clientsMetadata, topic, Error.INCOMPLETE_SOURCE_TOPIC_METADATA.code);
                }
            }
            for (final InternalTopicConfig topic: topicsInfo.repartitionSourceTopics.values()) {
                repartitionTopicMetadata.put(topic.name(), new InternalTopicMetadata(topic));
            }
        }
{code}

I'd suggest we upgrade DEBUG to ERROR logs on the above places when setting the error, as well as when receiving the error code to confirm. And in this case, inside {{KafkaStreamsTest}} we should add waitForCondition to wait for source topics to be successfully created. Cc [~vvcephei]
~~~~

2.

~~~~
Can we do a "two phase" approach here? First only change the log level and wait until the test fails again to see if it's really a correct root cause analysis? And afterwards put the fix into the test?
~~~~

3.

~~~~
Yup that's what I proposed as well :)
~~~~

4.

~~~~
[~vvcephei] Test failed again. Can you have a look: [https://builds.apache.org/blue/organizations/jenkins/kafka-2.2-jdk8/detail/kafka-2.2-jdk8/15/tests]

 
~~~~

5.

~~~~
One more: https://builds.apache.org/job/kafka-pr-jdk8-scala2.11/19519/
~~~~

6.

~~~~
I haven't seen a failure since we merged the PR to capture logs.

 

Checked:

[https://builds.apache.org/job/kafka-pr-jdk8-scala2.11/test_results_analyzer/]

[https://builds.apache.org/job/kafka-pr-jdk11-scala2.12/test_results_analyzer/]

 
~~~~

7.

~~~~
Let's re-open this if we see another failure.
~~~~

8.

~~~~
Should have been fixed via https://github.com/apache/kafka/pull/7382
~~~~

---

## KAFKA-7935: UNSUPPORTED_COMPRESSION_TYPE if ReplicaManager.getLogConfig returns None

https://issues.apache.org/jira/browse/KAFKA-7935

JIRA metadata: affects 2.1.0, 2.1.1; fixed in 2.1.2, 2.2.0

- `KAFKA-7935@2.1.0`: config 2.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-7935@2.2.1`: config 2.2.1, metadata answer **not_affected** (later_patch)

Known Kafka versions mentioned in text: none

### Description

~~~~
When adding zstd support, the following check was added:
{quote}if (logConfig.forall(_.compressionType == ZStdCompressionCodec.name) && versionId < 10) {
{quote}
Instead of `forall`, it should have been `exists`.
~~~~

### Comments (1)

1.

~~~~
https://github.com/apache/kafka/pull/6274
~~~~

---

## KAFKA-7990: Flaky Test KafkaStreamsTest#shouldCleanupOldStateDirs

https://issues.apache.org/jira/browse/KAFKA-7990

JIRA metadata: affects 2.2.0; fixed in 2.4.0

- `KAFKA-7990@2.2.0`: config 2.2.0, metadata answer **affected** (listed_affected)
- `KAFKA-7990@2.4.0`: config 2.4.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 2.0

### Description

~~~~
[https://builds.apache.org/blue/organizations/jenkins/kafka-2.0-jdk8/detail/kafka-2.0-jdk8/229/tests]

 
{quote}Exception in thread "appId-78a5ef7e-0f4d-47bd-af2e-54f4606fb19e-StreamThread-189" java.lang.IllegalArgumentException: Assigned partition input-0 for non-subscribed topic regex pattern; subscription pattern is topic
at org.apache.kafka.clients.consumer.internals.SubscriptionState.assignFromSubscribed(SubscriptionState.java:187)
at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.onJoinComplete(ConsumerCoordinator.java:244)
at org.apache.kafka.clients.consumer.internals.AbstractCoordinator.joinGroupIfNeeded(AbstractCoordinator.java:422)
at org.apache.kafka.clients.consumer.internals.AbstractCoordinator.ensureActiveGroup(AbstractCoordinator.java:352)
at org.apache.kafka.clients.consumer.internals.AbstractCoordinator.ensureActiveGroup(AbstractCoordinator.java:337)
at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.poll(ConsumerCoordinator.java:343)
at org.apache.kafka.clients.consumer.KafkaConsumer.updateAssignmentMetadataIfNeeded(KafkaConsumer.java:1218)
at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:1175)
at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:1154)
at org.apache.kafka.streams.processor.internals.StreamThread.pollRequests(StreamThread.java:861)
at org.apache.kafka.streams.processor.internals.StreamThread.runOnce(StreamThread.java:810)
at org.apache.kafka.streams.processor.internals.StreamThread.runLoop(StreamThread.java:767)
at org.apache.kafka.streams.processor.internals.StreamThread.run(StreamThread.java:736){quote}
~~~~

### Comments (1)

1.

~~~~
Should have been fixed via https://github.com/apache/kafka/pull/7382
~~~~

---

## KAFKA-8022: Flaky Test RequestQuotaTest#testExemptRequestTime

https://issues.apache.org/jira/browse/KAFKA-8022

JIRA metadata: affects 0.11.0.3; fixed in 2.2.0

- `KAFKA-8022@0.11.0.3`: config 0.11.0.3, metadata answer **affected** (listed_affected)
- `KAFKA-8022@2.2.0`: config 2.2.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 2.2.1, 2.2.0

### Description

~~~~
[https://builds.apache.org/blue/organizations/jenkins/kafka-trunk-jdk11/detail/kafka-trunk-jdk11/328/tests]
{quote}kafka.zookeeper.ZooKeeperClientTimeoutException: Timed out waiting for connection while in state: CONNECTING
at kafka.zookeeper.ZooKeeperClient.$anonfun$waitUntilConnected$3(ZooKeeperClient.scala:242)
at scala.runtime.java8.JFunction0$mcV$sp.apply(JFunction0$mcV$sp.java:23)
at kafka.utils.CoreUtils$.inLock(CoreUtils.scala:253)
at kafka.zookeeper.ZooKeeperClient.waitUntilConnected(ZooKeeperClient.scala:238)
at kafka.zookeeper.ZooKeeperClient.<init>(ZooKeeperClient.scala:96)
at kafka.zk.KafkaZkClient$.apply(KafkaZkClient.scala:1825)
at kafka.zk.ZooKeeperTestHarness.setUp(ZooKeeperTestHarness.scala:59)
at kafka.integration.KafkaServerTestHarness.setUp(KafkaServerTestHarness.scala:90)
at kafka.api.IntegrationTestHarness.doSetup(IntegrationTestHarness.scala:81)
at kafka.api.IntegrationTestHarness.setUp(IntegrationTestHarness.scala:73)
at kafka.server.RequestQuotaTest.setUp(RequestQuotaTest.scala:81){quote}
STDOUT:
{quote}[2019-03-01 00:40:47,090] ERROR [KafkaApi-0] Error when handling request: clientId=unauthorized-CONTROLLED_SHUTDOWN, correlationId=1, api=CONTROLLED_SHUTDOWN, body=\{broker_id=0,broker_epoch=9223372036854775807} (kafka.server.KafkaApis:76)
org.apache.kafka.common.errors.ClusterAuthorizationException: Request Request(processor=2, connectionId=127.0.0.1:37894-127.0.0.1:54838-2, session=Session(User:Unauthorized,/127.0.0.1), listenerName=ListenerName(PLAINTEXT), securityProtocol=PLAINTEXT, buffer=null) is not authorized.
[2019-03-01 00:40:47,090] ERROR [KafkaApi-0] Error when handling request: clientId=unauthorized-STOP_REPLICA, correlationId=1, api=STOP_REPLICA, body=\{controller_id=0,controller_epoch=2147483647,broker_epoch=9223372036854775807,delete_partitions=true,partitions=[{topic=topic-1,partition_ids=[0]}]} (kafka.server.KafkaApis:76)
org.apache.kafka.common.errors.ClusterAuthorizationException: Request Request(processor=0, connectionId=127.0.0.1:37894-127.0.0.1:54822-1, session=Session(User:Unauthorized,/127.0.0.1), listenerName=ListenerName(PLAINTEXT), securityProtocol=PLAINTEXT, buffer=null) is not authorized.
[2019-03-01 00:40:47,091] ERROR [KafkaApi-0] Error when handling request: clientId=unauthorized-UPDATE_METADATA, correlationId=1, api=UPDATE_METADATA, body=\{controller_id=0,controller_epoch=2147483647,broker_epoch=9223372036854775807,topic_states=[{topic=topic-1,partition_states=[{partition=0,controller_epoch=2147483647,leader=0,leader_epoch=2147483647,isr=[0],zk_version=2,replicas=[0],offline_replicas=[]}]}],live_brokers=[\{id=0,end_points=[{port=0,host=localhost,listener_name=PLAINTEXT,security_protocol_type=0}],rack=null}]} (kafka.server.KafkaApis:76)
org.apache.kafka.common.errors.ClusterAuthorizationException: Request Request(processor=1, connectionId=127.0.0.1:37894-127.0.0.1:54836-2, session=Session(User:Unauthorized,/127.0.0.1), listenerName=ListenerName(PLAINTEXT), securityProtocol=PLAINTEXT, buffer=null) is not authorized.
[2019-03-01 00:40:47,090] ERROR [KafkaApi-0] Error when handling request: clientId=unauthorized-LEADER_AND_ISR, correlationId=1, api=LEADER_AND_ISR, body=\{controller_id=0,controller_epoch=2147483647,broker_epoch=9223372036854775807,topic_states=[{topic=topic-1,partition_states=[{partition=0,controller_epoch=2147483647,leader=0,leader_epoch=2147483647,isr=[0],zk_version=2,replicas=[0],is_new=true}]}],live_leaders=[\{id=0,host=localhost,port=0}]} (kafka.server.KafkaApis:76)
org.apache.kafka.common.errors.ClusterAuthorizationException: Request Request(processor=0, connectionId=127.0.0.1:37894-127.0.0.1:54834-2, session=Session(User:Unauthorized,/127.0.0.1), listenerName=ListenerName(PLAINTEXT), securityProtocol=PLAINTEXT, buffer=null) is not authorized.
[2019-03-01 00:40:47,106] ERROR [KafkaApi-0] Error when handling request: clientId=unauthorized-WRITE_TXN_MARKERS, correlationId=1, api=WRITE_TXN_MARKERS, body=\{transaction_markers=[]} (kafka.server.KafkaApis:76)
org.apache.kafka.common.errors.ClusterAuthorizationException: Request Request(processor=0, connectionId=127.0.0.1:37894-127.0.0.1:54876-9, session=Session(User:Unauthorized,/127.0.0.1), listenerName=ListenerName(PLAINTEXT), securityProtocol=PLAINTEXT, buffer=null) is not authorized.
[2019-03-01 00:40:47,123] ERROR [KafkaApi-0] Error when handling request: clientId=unauthorized-DESCRIBE_ACLS, correlationId=1, api=DESCRIBE_ACLS, body=\{resource_type=1,resource_name=null,resource_pattern_type_filter=1,principal=null,host=null,operation=1,permission_type=1} (kafka.server.KafkaApis:76)
org.apache.kafka.common.errors.ClusterAuthorizationException: Request Request(processor=1, connectionId=127.0.0.1:37894-127.0.0.1:54908-14, session=Session(User:Unauthorized,/127.0.0.1), listenerName=ListenerName(PLAINTEXT), securityProtocol=PLAINTEXT, buffer=null) is not authorized.
[2019-03-01 00:40:47,124] ERROR [KafkaApi-0] Error when handling request: clientId=unauthorized-DELETE_ACLS, correlationId=1, api=DELETE_ACLS, body=\{filters=[{resource_type=2,resource_name=null,resource_pattern_type_filter=3,principal=User:ANONYMOUS,host=*,operation=1,permission_type=2}]} (kafka.server.KafkaApis:76)
org.apache.kafka.common.errors.ClusterAuthorizationException: Request Request(processor=2, connectionId=127.0.0.1:37894-127.0.0.1:54910-14, session=Session(User:Unauthorized,/127.0.0.1), listenerName=ListenerName(PLAINTEXT), securityProtocol=PLAINTEXT, buffer=null) is not authorized.
[2019-03-01 00:40:47,123] ERROR [KafkaApi-0] Error when handling request: clientId=unauthorized-CREATE_ACLS, correlationId=1, api=CREATE_ACLS, body=\{creations=[{resource_type=2,resource_name=mytopic,resource_pattten_type=3,principal=User:ANONYMOUS,host=*,operation=4,permission_type=2}]} (kafka.server.KafkaApis:76)
org.apache.kafka.common.errors.ClusterAuthorizationException: Request Request(processor=0, connectionId=127.0.0.1:37894-127.0.0.1:54906-14, session=Session(User:Unauthorized,/127.0.0.1), listenerName=ListenerName(PLAINTEXT), securityProtocol=PLAINTEXT, buffer=null) is not authorized.
[2019-03-01 00:40:47,168] ERROR [KafkaApi-0] Error when handling request: clientId=unauthorized-DELETE_ACLS, correlationId=2, api=DELETE_ACLS, body=\{filters=[{resource_type=2,resource_name=null,resource_pattern_type_filter=3,principal=User:ANONYMOUS,host=*,operation=1,permission_type=2}]} (kafka.server.KafkaApis:76)
org.apache.kafka.common.errors.ClusterAuthorizationException: Request Request(processor=2, connectionId=127.0.0.1:37894-127.0.0.1:54910-14, session=Session(User:Unauthorized,/127.0.0.1), listenerName=ListenerName(PLAINTEXT), securityProtocol=PLAINTEXT, buffer=null) is not authorized.
[2019-03-01 00:41:00,625] WARN Client session timed out, have not heard from server in 4001ms for sessionid 0x10299521c3d0000 (org.apache.zookeeper.ClientCnxn:1112)
[2019-03-01 00:41:00,628] WARN Unable to read additional data from client sessionid 0x10299521c3d0000, likely client has closed socket (org.apache.zookeeper.server.NIOServerCnxn:376)
[2019-03-01 00:41:02,135] WARN fsync-ing the write ahead log in SyncThread:0 took 4929ms which will adversely effect operation latency. See the ZooKeeper troubleshooting guide (org.apache.zookeeper.server.persistence.FileTxnLog:338)
[2019-03-01 00:41:08,156] WARN Client session timed out, have not heard from server in 6006ms for sessionid 0x0 (org.apache.zookeeper.ClientCnxn:1112)
[2019-03-01 00:41:13,861] WARN fsync-ing the write ahead log in SyncThread:0 took 11710ms which will adversely effect operation latency. See the ZooKeeper troubleshooting guide (org.apache.zookeeper.server.persistence.FileTxnLog:338)
[2019-03-01 00:41:13,863] WARN Unable to read additional data from client sessionid 0x102995240ed0000, likely client has closed socket (org.apache.zookeeper.server.NIOServerCnxn:376){quote}
~~~~

### Comments (3)

1.

~~~~
The fsync to ZK txn log can take 10+ secs. Filed [https://github.com/apache/kafka/pull/6354/files] to disable forceSync in ZK txn log in tests.
~~~~

2.

~~~~
The PR is merged. Closing it for now.
~~~~

3.

~~~~
Updating fixed version from 2.2.1 to 2.2.0 because we cut a new RC.
~~~~

---

## KAFKA-8072: Transient failure in SslSelectorTest.testCloseOldestConnectionWithMultipleStagedReceives

https://issues.apache.org/jira/browse/KAFKA-8072

JIRA metadata: affects 2.2.0, 2.3.0; fixed in 2.2.0

- `KAFKA-8072@2.3.0`: config 2.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-8072@2.3.1`: config 2.3.1, metadata answer **not_affected** (later_line)

Known Kafka versions mentioned in text: 2.2

### Description

~~~~
Failed in build [https://builds.apache.org/job/kafka-pr-jdk8-scala2.11/20134/]

Stacktrace
{noformat}
Error Message
java.lang.AssertionError: Channel has bytes buffered
Stacktrace
java.lang.AssertionError: Channel has bytes buffered
	at org.junit.Assert.fail(Assert.java:89)
	at org.junit.Assert.assertTrue(Assert.java:42)
	at org.junit.Assert.assertFalse(Assert.java:65)
	at org.apache.kafka.common.network.SelectorTest.createConnectionWithStagedReceives(SelectorTest.java:499)
	at org.apache.kafka.common.network.SelectorTest.verifyCloseOldestConnectionWithStagedReceives(SelectorTest.java:505)
	at org.apache.kafka.common.network.SelectorTest.testCloseOldestConnectionWithMultipleStagedReceives(SelectorTest.java:474)
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
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at org.gradle.internal.dispatch.ReflectionDispatch.dispatch(ReflectionDispatch.java:35)
	at org.gradle.internal.dispatch.ReflectionDispatch.dispatch(ReflectionDispatch.java:24)
	at org.gradle.internal.dispatch.ContextClassLoaderDispatch.dispatch(ContextClassLoaderDispatch.java:32)
	at org.gradle.internal.dispatch.ProxyDispatchAdapter$DispatchingInvocationHandler.invoke(ProxyDispatchAdapter.java:93)
	at com.sun.proxy.$Proxy2.processTestClass(Unknown Source)
	at org.gradle.api.internal.tasks.testing.worker.TestWorker.processTestClass(TestWorker.java:118)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at org.gradle.internal.dispatch.ReflectionDispatch.dispatch(ReflectionDispatch.java:35)
	at org.gradle.internal.dispatch.ReflectionDispatch.dispatch(ReflectionDispatch.java:24)
	at org.gradle.internal.remote.internal.hub.MessageHubBackedObjectConnection$DispatchWrapper.dispatch(MessageHubBackedObjectConnection.java:175)
	at org.gradle.internal.remote.internal.hub.MessageHubBackedObjectConnection$DispatchWrapper.dispatch(MessageHubBackedObjectConnection.java:157)
	at org.gradle.internal.remote.internal.hub.MessageHub$Handler.run(MessageHub.java:404)
	at org.gradle.internal.concurrent.ExecutorPolicy$CatchAndRecordFailures.onExecute(ExecutorPolicy.java:63)
	at org.gradle.internal.concurrent.ManagedExecutorImpl$1.run(ManagedExecutorImpl.java:46)
	at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
	at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
	at org.gradle.internal.concurrent.ThreadFactoryImpl$ManagedThreadRunnable.run(ThreadFactoryImpl.java:55)
	at java.lang.Thread.run(Thread.java:748)

Standard Output
[2019-03-08 10:23:06,123] ERROR Unexpected exception during send, closing connection 0 and rethrowing exception {} (org.apache.kafka.common.network.Selector:392)
java.lang.IllegalStateException: Attempt to begin a send operation with prior send operation still in progress, connection id is 0
	at org.apache.kafka.common.network.KafkaChannel.setSend(KafkaChannel.java:373)
	at org.apache.kafka.common.network.Selector.send(Selector.java:384)
	at org.apache.kafka.common.network.SelectorTest.testCantSendWithInProgress(SelectorTest.java:152)
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
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at org.gradle.internal.dispatch.ReflectionDispatch.dispatch(ReflectionDispatch.java:35)
	at org.gradle.internal.dispatch.ReflectionDispatch.dispatch(ReflectionDispatch.java:24)
	at org.gradle.internal.dispatch.ContextClassLoaderDispatch.dispatch(ContextClassLoaderDispatch.java:32)
	at org.gradle.internal.dispatch.ProxyDispatchAdapter$DispatchingInvocationHandler.invoke(ProxyDispatchAdapter.java:93)
	at com.sun.proxy.$Proxy2.processTestClass(Unknown Source)
	at org.gradle.api.internal.tasks.testing.worker.TestWorker.processTestClass(TestWorker.java:118)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at org.gradle.internal.dispatch.ReflectionDispatch.dispatch(ReflectionDispatch.java:35)
	at org.gradle.internal.dispatch.ReflectionDispatch.dispatch(ReflectionDispatch.java:24)
	at org.gradle.internal.remote.internal.hub.MessageHubBackedObjectConnection$DispatchWrapper.dispatch(MessageHubBackedObjectConnection.java:175)
	at org.gradle.internal.remote.internal.hub.MessageHubBackedObjectConnection$DispatchWrapper.dispatch(MessageHubBackedObjectConnection.java:157)
	at org.gradle.internal.remote.internal.hub.MessageHub$Handler.run(MessageHub.java:404)
	at org.gradle.internal.concurrent.ExecutorPolicy$CatchAndRecordFailures.onExecute(ExecutorPolicy.java:63)
	at org.gradle.internal.concurrent.ManagedExecutorImpl$1.run(ManagedExecutorImpl.java:46)
	at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
	at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
	at org.gradle.internal.concurrent.ThreadFactoryImpl$ManagedThreadRunnable.run(ThreadFactoryImpl.java:55)
	at java.lang.Thread.run(Thread.java:748){noformat}
~~~~

### Comments (3)

1.

~~~~
Failed again: [https://builds.apache.org/blue/organizations/jenkins/kafka-trunk-jdk8/detail/kafka-trunk-jdk8/3447/tests]
~~~~

2.

~~~~
One more: [https://jenkins.confluent.io/job/apache-kafka-test/job/2.2/60/testReport/junit/org.apache.kafka.common.network/SslSelectorTest/testCloseOldestConnectionWithMultipleStagedReceives/]
~~~~

3.

~~~~
This is fixed by the change made for KAFKA-7288.
~~~~

---

## KAFKA-8277: Fix NPE in ConnectHeaders

https://issues.apache.org/jira/browse/KAFKA-8277

JIRA metadata: affects 1.1.0; fixed in 1.1.2, 2.0.2, 2.1.2, 2.2.1, 2.3.0

- `KAFKA-8277@1.1.0`: config 1.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-8277@2.2.2`: config 2.2.2, metadata answer **not_affected** (later_patch)

Known Kafka versions mentioned in text: none

### Description

~~~~
Replace {{headers.isEmpty()}} by calls to {{isEmpty()}} as the latter does a null check on heathers (that is lazily created).
~~~~

---

## KAFKA-8363: Config provider parsing is broken

https://issues.apache.org/jira/browse/KAFKA-8363

JIRA metadata: affects 2.0.0, 2.0.1, 2.1.0, 2.1.1, 2.2.0; fixed in 2.0.2, 2.1.2, 2.2.1, 2.3.0

- `KAFKA-8363@2.1.1`: config 2.1.1, metadata answer **affected** (listed_affected)
- `KAFKA-8363@1.1.1`: config 1.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
The [regex|https://github.com/apache/kafka/blob/63e4f67d9ba9e08bdce705b35c5acf32dcd20633/clients/src/main/java/org/apache/kafka/common/config/ConfigTransformer.java#L56] used by the {{ConfigTransformer}} class to parse config provider syntax (see [KIP-279|https://cwiki.apache.org/confluence/display/KAFKA/KIP-297%3A+Externalizing+Secrets+for+Connect+Configurations]) is broken and fails when multiple path-less configs are specified. For example: {{"${provider:configOne} ${provider:configTwo}"}} would be parsed incorrectly as a reference with a path of {{"configOne} $\{provider"}}. 
~~~~

---

## KAFKA-8398: NPE when unmapping files after moving log directories using AlterReplicaLogDirs

https://issues.apache.org/jira/browse/KAFKA-8398

JIRA metadata: affects 2.2.0; fixed in 2.6.0

- `KAFKA-8398@2.2.0`: config 2.2.0, metadata answer **affected** (listed_affected)
- `KAFKA-8398@2.1.1`: config 2.1.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.7.0

### Description

~~~~
The NPE occurs after the AlterReplicaLogDirs command completes successfully and when unmapping older regions. The relevant part of log is in attached log file. Here is the stacktrace (which is repeated for both index files):

 
{code:java}
[2019-05-20 14:08:13,999] ERROR Error unmapping index /tmp/kafka-logs/test-0.567a0d8ff88b45ab95794020d0b2e66f-delete/00000000000000000000.index (kafka.log.OffsetIndex)
java.lang.NullPointerException
at org.apache.kafka.common.utils.MappedByteBuffers.unmap(MappedByteBuffers.java:73)
at kafka.log.AbstractIndex.forceUnmap(AbstractIndex.scala:318)
at kafka.log.AbstractIndex.safeForceUnmap(AbstractIndex.scala:308)
at kafka.log.AbstractIndex.$anonfun$closeHandler$1(AbstractIndex.scala:257)
at scala.runtime.java8.JFunction0$mcV$sp.apply(JFunction0$mcV$sp.java:23)
at kafka.utils.CoreUtils$.inLock(CoreUtils.scala:251)
at kafka.log.AbstractIndex.closeHandler(AbstractIndex.scala:257)
at kafka.log.AbstractIndex.deleteIfExists(AbstractIndex.scala:226)
at kafka.log.LogSegment.$anonfun$deleteIfExists$6(LogSegment.scala:597)
at kafka.log.LogSegment.delete$1(LogSegment.scala:585)
at kafka.log.LogSegment.$anonfun$deleteIfExists$5(LogSegment.scala:597)
at kafka.utils.CoreUtils$.$anonfun$tryAll$1(CoreUtils.scala:115)
at kafka.utils.CoreUtils$.$anonfun$tryAll$1$adapted(CoreUtils.scala:114)
at scala.collection.immutable.List.foreach(List.scala:392)
at kafka.utils.CoreUtils$.tryAll(CoreUtils.scala:114)
at kafka.log.LogSegment.deleteIfExists(LogSegment.scala:599)
at kafka.log.Log.$anonfun$delete$3(Log.scala:1762)
at kafka.log.Log.$anonfun$delete$3$adapted(Log.scala:1762)
at scala.collection.Iterator.foreach(Iterator.scala:941)
at scala.collection.Iterator.foreach$(Iterator.scala:941)
at scala.collection.AbstractIterator.foreach(Iterator.scala:1429)
at scala.collection.IterableLike.foreach(IterableLike.scala:74)
at scala.collection.IterableLike.foreach$(IterableLike.scala:73)
at scala.collection.AbstractIterable.foreach(Iterable.scala:56)
at kafka.log.Log.$anonfun$delete$2(Log.scala:1762)
at scala.runtime.java8.JFunction0$mcV$sp.apply(JFunction0$mcV$sp.java:23)
at kafka.log.Log.maybeHandleIOException(Log.scala:2013)
at kafka.log.Log.delete(Log.scala:1759)
at kafka.log.LogManager.deleteLogs(LogManager.scala:761)
at kafka.log.LogManager.$anonfun$deleteLogs$6(LogManager.scala:775)
at kafka.utils.KafkaScheduler.$anonfun$schedule$2(KafkaScheduler.scala:114)
at kafka.utils.CoreUtils$$anon$1.run(CoreUtils.scala:63)
at java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:511)
at java.util.concurrent.FutureTask.run(FutureTask.java:266)
at java.util.concurrent.ScheduledThreadPoolExecutor$ScheduledFutureTask.access$201(ScheduledThreadPoolExecutor.java:180)
at java.util.concurrent.ScheduledThreadPoolExecutor$ScheduledFutureTask.run(ScheduledThreadPoolExecutor.java:293)
at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
at java.lang.Thread.run(Thread.java:748)
[{code}
~~~~

### Comments (3)

1.

~~~~
seems https://github.com/apache/kafka/commit/e554dc518eaaa0747899e708160275f95c4e525f had resolved this issue.

{code:scala}
  protected def safeForceUnmap(): Unit = {
    try forceUnmap()
    catch {
      case t: Throwable => error(s"Error unmapping index $file", t)
    }
  }
{code}

Although, it would be better to avoid NPE even if NPE is swallowed.

~~~~

2.

~~~~
[~chia7712] Even before that commit, we were catching the exception. So the fix here is to avoid the noisy logs.
~~~~

3.

~~~~
Since this is not a blocker, and the PR is closed, I'm clearing the "fix version" field as part of the 2.7.0 release process.
~~~~

---

## KAFKA-8412: Still a nullpointer exception thrown on shutdown while flushing before closing producers

https://issues.apache.org/jira/browse/KAFKA-8412

JIRA metadata: affects 2.1.1; fixed in 2.1.2, 2.2.2, 2.3.1, 2.4.0

- `KAFKA-8412@2.1.1`: config 2.1.1, metadata answer **affected** (listed_affected)
- `KAFKA-8412@2.5.0`: config 2.5.0, metadata answer **not_affected** (later_line)

Known Kafka versions mentioned in text: 2.1.1

### Description

~~~~
I found a closed issue and replied there but decided to open one myself because although they're related they're slightly different. The original issue is at https://issues.apache.org/jira/browse/KAFKA-7678

The fix there has been to implement a null check around closing a producer because in some cases the producer is already null there (has been closed already)

In version 2.1.1 we are getting a very similar exception, but in the 'flush' method that is called pre-close. This is in the log:
{code:java}
message: stream-thread [webhook-poster-7034dbb0-7423-476b-98f3-d18db675d6d6-StreamThread-1] Failed while closing StreamTask 1_26 due to the following error:
logger_name: org.apache.kafka.streams.processor.internals.AssignedStreamsTasks

java.lang.NullPointerException: null
    at org.apache.kafka.streams.processor.internals.RecordCollectorImpl.flush(RecordCollectorImpl.java:245)
    at org.apache.kafka.streams.processor.internals.StreamTask.flushState(StreamTask.java:493)
    at org.apache.kafka.streams.processor.internals.StreamTask.commit(StreamTask.java:443)
    at org.apache.kafka.streams.processor.internals.StreamTask.suspend(StreamTask.java:568)
    at org.apache.kafka.streams.processor.internals.StreamTask.close(StreamTask.java:691)
    at org.apache.kafka.streams.processor.internals.AssignedTasks.close(AssignedTasks.java:397)
    at org.apache.kafka.streams.processor.internals.TaskManager.shutdown(TaskManager.java:260)
    at org.apache.kafka.streams.processor.internals.StreamThread.completeShutdown(StreamThread.java:1181)
    at org.apache.kafka.streams.processor.internals.StreamThread.run(StreamThread.java:758){code}

Followed by:
 
{code:java}
message: task [1_26] Could not close task due to the following error:
logger_name: org.apache.kafka.streams.processor.internals.StreamTask

java.lang.NullPointerException: null
    at org.apache.kafka.streams.processor.internals.RecordCollectorImpl.flush(RecordCollectorImpl.java:245)
    at org.apache.kafka.streams.processor.internals.StreamTask.flushState(StreamTask.java:493)
    at org.apache.kafka.streams.processor.internals.StreamTask.commit(StreamTask.java:443)
    at org.apache.kafka.streams.processor.internals.StreamTask.suspend(StreamTask.java:568)
    at org.apache.kafka.streams.processor.internals.StreamTask.close(StreamTask.java:691)
    at org.apache.kafka.streams.processor.internals.AssignedTasks.close(AssignedTasks.java:397)
    at org.apache.kafka.streams.processor.internals.TaskManager.shutdown(TaskManager.java:260)
    at org.apache.kafka.streams.processor.internals.StreamThread.completeShutdown(StreamThread.java:1181)
    at org.apache.kafka.streams.processor.internals.StreamThread.run(StreamThread.java:758){code}

If I look at the source code at this point, I see a nice null check in the close method, but not in the flush method that is called just before that:
{code:java}
public void flush() {
    this.log.debug("Flushing producer");
    this.producer.flush();
    this.checkForException();
}

public void close() {
    this.log.debug("Closing producer");
    if (this.producer != null) {
        this.producer.close();
        this.producer = null;
    }

    this.checkForException();
}{code}

Seems to my (ignorant) eye that the flush method should also be wrapped in a null check in the same way as has been done for close.
~~~~

### Comments (12)

1.

~~~~
Thanks for reporting this. What I don't understand is, why we would flush after we closed a task already. Hence, I am not sure if a null-guard is the correct fix, but to rather make sure we don't call flush() in the first place.

Can you maybe provide debug level logs? This might help to understand the scenario better.
~~~~

2.

~~~~
[~mjsax] I can try to reproduce it in development some more but so far we've only seen it in production.

But my theory is that it is similar to the other ticket, a comment https://issues.apache.org/jira/browse/KAFKA-7678?focusedCommentId=16715220&page=com.atlassian.jira.plugin.system.issuetabpanels:comment-tabpanel#comment-16715220 says:

_"There are one or two edge cases which can cause record collector to be closed multiple times, we have noticed them recently and are thinking about cleanup the classes along the calling hierarchy (i.e. from Task Manager -> Task -> RecordCollector) for it. One example is:_

_1) a task is *suspended*, with EOS turned on (like your case), the record collector is closed()._
 _2) then the instance got killed (SIGTERM) , which causes all threads to be closed, which will then cause all their owned tasks to be *closed*. The same record collector close() call will be triggered again"_

 

 

So this could be the same issue but now not for close but for flush. The producer is already flushed and closed but the same thing is tried again. Of course I don't know anything about the internals of the client so take this with a grain of salt.
~~~~

3.

~~~~
Do you run with EOS enabled?

Also, closing() and flushing() is a little different... I am not saying there is no issue, I just try to figure out what the correct fix is. Just adding a `null`-check could actually just mask the root cause of the bug, but not fix the bug itself.
~~~~

4.

~~~~
[~mjsax] yes we are using EOS.

And yeah you're right, I was surprised it was solved by a null check for the other ticket when it also seemed to me the situation should be avoided in the first place. But I'll leave that to the actual developers.
~~~~

5.

~~~~
[~mjsax] I looked through the code and the original JIRA (https://issues.apache.org/jira/browse/KAFKA-7285) again, and I think the above case I mentioned still exists, where the root cause is that in `suspend` we would close the record collector with EOS turned on while in `close` we may want to flush (from state commit), and close the collector again.

What I'm thinking is that, we can refactor the fix in KAFKA-7285, such that in suspend, we do the "close-and-then-recreate" completely and only leave the `initTxn` call in the `resume` function. In that case whenever we're closing we are assured there's still an open producer. With this, we no longer need the closed-check in close() function as well.
~~~~

6.

~~~~
Just cycling back to this.

I am not sure if we should do the "close-and-then-recreate" strategy. The issues seems to be, that we blindly call `task#close()` for all tasks within `AssingedTasks#close()`. However, it seems that a proper fix would be to distinguish between active and suspended tasks, and call `closeSuspended()` for suspended ones, and `close()` for all others?

With regard to KAFKA-7678: re-reading the ticket, the report says, that it should be a graceful shutdown via SIGTERM. Hence, I am wondering why the unclean shutdown path is actually executed (ie, why do we call `maybeAbortTransactionAndCloseRecordCollector()` – this should only happen for an unclean shutdown). \cc [~pachilo] who reported and work on the first NPE
~~~~

7.

~~~~
[~guozhang] also mentioned that we may need to refactor that part of the code  [in a comment on the KAFKA-7678 |https://issues.apache.org/jira/browse/KAFKA-7678?focusedCommentId=16715220&page=com.atlassian.jira.plugin.system.issuetabpanels%3Acomment-tabpanel#comment-16715220], wich is aligned with your proposal [~mjsax].
In your opinion [~mjsax], should we address that or first we could add a null check before calling the Producer#flush method? to then do the refactor of course.
 
~~~~

8.

~~~~
I would rather refactor the code directly because it seems to be cleaner. WDYT [~guozhang]?
~~~~

9.

~~~~
Matthias, Guozhang proposed I pick up this ticket to get my feet wet. I hope you don't mind, but feel free to grab it back if you are very attached to it :).
~~~~

10.

~~~~
Sure. I did not start yet to work on a PR anyway.
~~~~

11.

~~~~
I'm able to repro this and [~mjsax]'s solution should fix this.

One other observation while I was in this code is that we essentially have state spread out across classes. As a dev new to the code, I would expect to push most of the state for the task down into StreamTask and only if we need fast lookup by state keep an index of these in AssignedTask, but treat this as an index and not as the authoritative state. In other words, I would prefer to see close on StreamTask do the right thing for the state it is in instead of having AssignedTasks be responsible for different types of close. This should also make it easier to test without involving mocks, as we are in AssignedTasks.

So I see a few options:
 # Use [~mjsax]'s solution and keep state as is.
 # Push state down into StreamTask, AssignedTasks just calls close as it does today.
 # Do #1 in first patch and follow up with #2 in a second patch focused on refactoring state.

[~mjsax] [~guozhang] thoughts?
~~~~

12.

~~~~
Having played with this a bit more I think its best to go for #1 for now, which is a point fix with a pretty small scope, i.e. low risk.

I do see value in rethinking state a bit particularly around ownership and transitions, perhaps as a separate ticket. As someone new coming to the code it is difficult to work out which states and transitions are valid at a glance, especially because it is distributed across at least AssignedTasks, AbstractTask, and StreamTask.
~~~~

---

## KAFKA-8526: Broker may select a failed dir for new replica even in the presence of other live dirs

https://issues.apache.org/jira/browse/KAFKA-8526

JIRA metadata: affects 1.1.1, 2.0.1, 2.1.1, 2.2.1, 2.3.0; fixed in 2.4.0

- `KAFKA-8526@2.1.1`: config 2.1.1, metadata answer **affected** (listed_affected)
- `KAFKA-8526@2.4.0`: config 2.4.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: none

### Description

~~~~
Suppose a broker is configured with multiple log dirs. One of the log dirs fails, but there is no load on that dir, so the broker does not know about the failure yet, _i.e._, the failed dir is still in LogManager#_liveLogDirs. Suppose a new topic gets created, and the controller chooses the broker with failed log dir to host one of the replicas. The broker gets LeaderAndIsr request with isNew flag set. LogManager#getOrCreateLog() selects a log dir for the new replica from _liveLogDirs, then one two things can happen:
1) getAbsolutePath can fail, in which case getOrCreateLog will throw an IOException
2) Creating directory for new the replica log may fail (_e.g._, if directory becomes read-only, so getAbsolutePath worked). 

In both cases, the selected dir will be marked offline (which is correct). However, LeaderAndIsr will return an error and replica will be marked offline, even though the broker may have other live dirs. 

*Proposed solution*: Broker should retry selecting a dir for the new replica, if initially selected dir threw an IOException when trying to create a directory for the new replica. We should be able to do that in LogManager#getOrCreateLog() method, but keep in mind that logDirFailureChannel.maybeAddOfflineLogDir does not synchronously removes the dir from _liveLogDirs. So, it makes sense to select initial dir by calling LogManager#nextLogDir (current implementation), but if we fail to create log on that dir, one approach is to select next dir from _liveLogDirs in round-robin fashion (until we get to initial log dir – the case where all dirs failed).
~~~~

---

## KAFKA-8536: Error creating ACL Alter Topic in 2.2

https://issues.apache.org/jira/browse/KAFKA-8536

JIRA metadata: affects 2.2.1; fixed in 2.0.2, 2.1.2, 2.2.2

- `KAFKA-8536@2.2.1`: config 2.2.1, metadata answer **affected** (listed_affected)
- `KAFKA-8536@2.2.2`: config 2.2.2, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 2.2, 2.3, 2.0, 2.1

### Description

~~~~
When we try to execute the statement to create an Alter Topic ACL in version 2.2 of
Kafka through the kafka-acls.

"""

kafka-acls --authorizer-properties zookeeper.connect=fastdata-zk-discovery:2181 \ 
 --add \
 --allow-principal User:MyUser \
 --operation Alter \
 --topic topic \

"""

We get the following error: 
 
ResourceType TOPIC only supports operations

 

"""

Read,All,AlterConfigs,DescribeConfigs,Delete,Write,Create,Describe

"""

It should be possible to create an Alter Topic ACL, according to the documentation.

Thanks
~~~~

### Comments (5)

1.

~~~~
Notes:
[https://github.com/apache/kafka/pull/6263]

Looks like it was fixed in trunk and intended for 2.2 but I'm not sure if it ever made it in there

Reproduce

kafka-acls --bootstrap-server <> --add --allow-principal <> --topic <> --operation "Alter"
h2. Error

ResourceType TOPIC only supports operations Read,All,AlterConfigs,DescribeConfigs,Delete,Write,Create,Describe
h2. Code 2.2 (and other versions) showing it broken

*./core/src/main/scala/kafka/admin/AclCommand.scala*
 _private def validateOperation(opts: AclCommandOptions, resourceToAcls: Map[ResourcePatternFilter, Set[Acl]]): Unit = {_
 _for ((resource, acls) <- resourceToAcls) {_
 _val validOps = ResourceTypeToValidOperations(resource.resourceType)_
 _if ((acls.map(_.operation) -- validOps).nonEmpty)_
 _CommandLineUtils.printUsageAndDie(opts.parser, s"ResourceType ${resource.resourceType} only supports operations ${validOps.mkString(",")}")_
 _}_
 _}_

 _val ResourceTypeToValidOperations: Map[JResourceType, Set[Operation]] = Map[JResourceType, Set[Operation]](_
 _JResourceType.TOPIC -> Set(Read, Write, Create, Describe, Delete, DescribeConfigs, AlterConfigs, All),_
 _JResourceType.GROUP -> Set(Read, Describe, Delete, All),_
 _JResourceType.CLUSTER -> Set(Create, ClusterAction, DescribeConfigs, AlterConfigs, IdempotentWrite, Alter, Describe, All),_
 _JResourceType.TRANSACTIONAL_ID -> Set(Describe, Write, All),_
 _JResourceType.DELEGATION_TOKEN -> Set(Describe, All)_
 _)_
h2. Code 2.3 where it was fixed coincidentally


*./core/src/main/scala/kafka/admin/AclCommand.scala*
 _private def validateOperation(opts: AclCommandOptions, resourceToAcls: Map[ResourcePatternFilter, Set[Acl]]): Unit = {_
 _for ((resource, acls) <- resourceToAcls) {_
 _val validOps = ResourceType.fromJava(resource.resourceType).supportedOperations + All_
 _if ((acls.map(_.operation) -- validOps).nonEmpty)_
 _CommandLineUtils.printUsageAndDie(opts.parser, s"ResourceType ${resource.resourceType} only supports operations ${validOps.mkString(",")}")_
 _}_
 _}_
*./core/src/main/scala/kafka/security/auth/ResourceType.scala*
_case object Topic extends ResourceType {_
 _val name = "Topic"_
 _val error = Errors.TOPIC_AUTHORIZATION_FAILED_
 _val toJava = JResourceType.TOPIC_
 _val supportedOperations = Set(Read, Write, Create, Describe, Delete, Alter, DescribeConfigs, AlterConfigs)_
_}_
h2. Suggested Patch

*./core/src/main/scala/kafka/admin/AclCommand.scala*

 _val ResourceTypeToValidOperations: Map[JResourceType, Set[Operation]] = Map[JResourceType, Set[Operation]](_
 _JResourceType.TOPIC -> Set(Read, Write, Create, Describe, Delete, Alter, DescribeConfigs, AlterConfigs, All),_
 _JResourceType.GROUP -> Set(Read, Describe, Delete, All),_
 _JResourceType.CLUSTER -> Set(Create, ClusterAction, DescribeConfigs, AlterConfigs, IdempotentWrite, Alter, Describe, All),_
 _JResourceType.TRANSACTIONAL_ID -> Set(Describe, Write, All),_
 _JResourceType.DELEGATION_TOKEN -> Set(Describe, All)_
 _)_
~~~~

2.

~~~~
Thanks [~EeveeB]  :) 
~~~~

3.

~~~~
Talked to a few people looks like the back port was missed.

Looks like that'll happen but I'll update this when it does.
~~~~

4.

~~~~
Hi @[Evelyn Bayes|https://issues.apache.org/jira/secure/ViewProfile.jspa?name=EeveeB]

The error is minor, it affects the Kafka-acls.sh program, if we create the ACL with the Java API Kafka works correctly as indicated in the documentation.

kafka-acls.sh problem seems that it is already solved by omkreddy in the link that you sent.

Thanks :)
~~~~

5.

~~~~
Sorry, I forgot to backport the fix.  backported the  PR [https://github.com/apache/kafka/pull/6263] to 2.0, 2.1, 2.2 branches.
~~~~

---

## KAFKA-8715: Static consumer cannot join group due to ERROR in broker

https://issues.apache.org/jira/browse/KAFKA-8715

JIRA metadata: affects 2.3.0; fixed in 2.3.1

- `KAFKA-8715@2.3.0`: config 2.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-8715@2.2.2`: config 2.2.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.3.0, 2.3.1

### Description

~~~~
A streams consumer using a static group instance id is unable to join the group due to an invalid group join  -- the consumer gets the error:

{code}
ERROR stream-thread [x-stream-4a43d5d4-d38f-4cb0-8741-7a6c685abf15-StreamThread-1] Encountered the following unexpected Kafka exception during processing, this usually indicate Streams internal errors:
[[EXCEPTION: org.apache.kafka.common.KafkaException: Unexpected error in join group response: The server experienced an unexpected error when processing the request.
    at org.apache.kafka.clients.consumer.internals.AbstractCoordinator$JoinGroupResponseHandler.handle(AbstractCoordinator.java:599) ~[kafka-clients-2.3.0.jar:?]
    at org.apache.kafka.clients.consumer.internals.AbstractCoordinator$JoinGroupResponseHandler.handle(AbstractCoordinator.java:527) ~[kafka-clients-2.3.0.jar:?]
    at org.apache.kafka.clients.consumer.internals.AbstractCoordinator$CoordinatorResponseHandler.onSuccess(AbstractCoordinator.java:978) ~[kafka-clients-2.3.0.jar:?]
    at org.apache.kafka.clients.consumer.internals.AbstractCoordinator$CoordinatorResponseHandler.onSuccess(AbstractCoordinator.java:958) ~[kafka-clients-2.3.0.jar:?]
    at org.apache.kafka.clients.consumer.internals.RequestFuture$1.onSuccess(RequestFuture.java:204) ~[kafka-clients-2.3.0.jar:?]
    at org.apache.kafka.clients.consumer.internals.RequestFuture.fireSuccess(RequestFuture.java:167) ~[kafka-clients-2.3.0.jar:?]
    at org.apache.kafka.clients.consumer.internals.RequestFuture.complete(RequestFuture.java:127) ~[kafka-clients-2.3.0.jar:?]
    at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient$RequestFutureCompletionHandler.fireCompletion(ConsumerNetworkClient.java:578) ~[kafka-clients-2.3.0.jar:?]
    at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.firePendingCompletedRequests(ConsumerNetworkClient.java:388) ~[kafka-clients-2.3.0.jar:?]
    at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:294) ~[kafka-clients-2.3.0.jar:?]
    at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:233) ~[kafka-clients-2.3.0.jar:?]
    at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:224) ~[kafka-clients-2.3.0.jar:?]
    at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.awaitMetadataUpdate(ConsumerNetworkClient.java:161) ~[kafka-clients-2.3.0.jar:?]
    at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.ensureFreshMetadata(ConsumerNetworkClient.java:172) ~[kafka-clients-2.3.0.jar:?]
    at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.poll(ConsumerCoordinator.java:346) ~[kafka-clients-2.3.0.jar:?]
    at org.apache.kafka.clients.consumer.KafkaConsumer.updateAssignmentMetadataIfNeeded(KafkaConsumer.java:1251) ~[kafka-clients-2.3.0.jar:?]
    at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:1216) ~[kafka-clients-2.3.0.jar:?]
    at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:1201) ~[kafka-clients-2.3.0.jar:?]
    at org.apache.kafka.streams.processor.internals.StreamThread.pollRequests(StreamThread.java:941) ~[kafka-streams-2.3.0.jar:?]
    at org.apache.kafka.streams.processor.internals.StreamThread.runOnce(StreamThread.java:846) ~[kafka-streams-2.3.0.jar:?]
    at org.apache.kafka.streams.processor.internals.StreamThread.runLoop(StreamThread.java:805) ~[kafka-streams-2.3.0.jar:?]
    at org.apache.kafka.streams.processor.internals.StreamThread.run(StreamThread.java:774) [kafka-streams-2.3.0.jar:?]
]]
{code}

On the broker, I see this error:

{code}
[2019-07-25 08:14:11,978] ERROR [KafkaApi-1] Error when handling request: clientId=x-stream-4a43d5d4-d38f-4cb0-8741-7a6c685abf15-StreamThread-1-consumer, correlationId=6, api=JOIN_GROUP, body={group_id=x-stream,session_timeout_ms=10000,rebalance_timeout_ms=300000,member_id=,group_instance_id=lcrzf-1,protocol_type=consumer,protocols=[{name=stream,metadata=java.nio.HeapByteBuffer[pos=0 lim=64 cap=64]}]} (kafka.server.KafkaApis)
java.util.NoSuchElementException: None.get
  at scala.None$.get(Option.scala:366)
  at scala.None$.get(Option.scala:364)
  at kafka.coordinator.group.GroupMetadata.generateMemberId(GroupMetadata.scala:368)
  at kafka.coordinator.group.GroupCoordinator.$anonfun$doUnknownJoinGroup$1(GroupCoordinator.scala:178)
  at scala.runtime.java8.JFunction0$mcV$sp.apply(JFunction0$mcV$sp.java:23)
  at kafka.utils.CoreUtils$.inLock(CoreUtils.scala:253)
  at kafka.coordinator.group.GroupMetadata.inLock(GroupMetadata.scala:209)
  at kafka.coordinator.group.GroupCoordinator.doUnknownJoinGroup(GroupCoordinator.scala:169)
  at kafka.coordinator.group.GroupCoordinator.$anonfun$handleJoinGroup$2(GroupCoordinator.scala:144)
  at kafka.utils.CoreUtils$.inLock(CoreUtils.scala:253)
  at kafka.coordinator.group.GroupMetadata.inLock(GroupMetadata.scala:209)
  at kafka.coordinator.group.GroupCoordinator.handleJoinGroup(GroupCoordinator.scala:136)
  at kafka.server.KafkaApis.handleJoinGroupRequest(KafkaApis.scala:1389)
  at kafka.server.KafkaApis.handle(KafkaApis.scala:124)
  at kafka.server.KafkaRequestHandler.run(KafkaRequestHandler.scala:69)
  at java.base/java.lang.Thread.run(Thread.java:834)
{code}
~~~~

### Comments (5)

1.

~~~~
Is this happening all time? The code triggers exception is:
{code:java}
 instanceId + GroupMetadata.MemberIdDelimiter + currentStateTimestamp.get
{code}
where currentStateTimestamp is defined as:
  
{code:java}
var currentStateTimestamp: Option[Long] = Some(time.milliseconds())
{code}
 

So every time we will call timer to get current timestamp, couldn't picture how this will give none atm. Will try to reproduce the issue in the meantime.

cc [~guozhang] [~hachikuji]
~~~~

2.

~~~~
I think the root cause is that we depend on a field which is loaded in statically defined/undefined timestamp field. Will get a fix
~~~~

3.

~~~~
[~bchen225242] No it isn't happening all the time. Interestingly, I have two different instances of the same 2.3.0 client code running against the same 2.3.0 Kafka broker. The only difference between them is the configured name of the group, and the topics being consumed. One of them get this error, the other does not.

In addition, it initially used to work with both consumer groups. It stopped working for one group when I restarted the cluster in order to apply an unrelated configuration change.
~~~~

4.

~~~~
[~rocketraman] Yea, this is indeed a bug. We shouldn't rely on `currentStateTimestamp` in the first place as it could be null when we load a group from log.
~~~~

5.

~~~~
[~bchen225242]We are looking forward to use static consumer, when is 2.3.1 release planned ?
~~~~

---

## KAFKA-8788: Optimize client metadata handling with a large number of partitions

https://issues.apache.org/jira/browse/KAFKA-8788

JIRA metadata: affects 2.3.0; fixed in 2.3.1, 2.4.0

- `KAFKA-8788@2.3.0`: config 2.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-8788@2.4.0`: config 2.4.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 2.3.0, 2.2.0

### Description

~~~~
Credit to [~lbradstreet] for profiling the producer with a large number of partitions.

There was a regression in 2.3.0 that made the client metadata handling significantly less efficient when dealing with a large number of partitions. There was a less significant regression in 2.2.0.

Lucas benchmarked the producer, but the code is shared with the consumer. See the PR for more details.

 
~~~~

---

## KAFKA-9025: ZkSecurityMigrator not working with zookeeper chroot

https://issues.apache.org/jira/browse/KAFKA-9025

JIRA metadata: affects 2.3.0; fixed in 2.5.0

- `KAFKA-9025@2.3.0`: config 2.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-9025@2.6.0`: config 2.6.0, metadata answer **not_affected** (later_line)

Known Kafka versions mentioned in text: 2.3.0

### Description

~~~~
The ZkSecurityMigrator tool fails to handle installations where kafka is configured with a zookeeper chroot (as opposed to using /, the default):
 * ACLs on existing nodes are not modified (they are left world-modifiable)
 * New nodes created by the tool are created directly under the zookeeper root instead of under the chroot

The tool does not emit any message, thus the unsuspecting user can only assume everything went well, when in fact it did not and znodes are still not secure:

kafka_2.12-2.3.0 $ bin/zookeeper-security-migration.sh --zookeeper.acl=secure --zookeeper.connect=localhost:2181
kafka_2.12-2.3.0 $

For example, with kafka configured to use /kafka as chroot (zookeeper.connect=localhost:2181/kafka), the following is observed:
 * Before running the tool
 ** Zookeeper top-level nodes (all kafka nodes are under /kafka):
[zk: localhost:2181(CONNECTED) 1] ls /
[kafka, zookeeper]
 ** Example node ACL:
[zk: localhost:2181(CONNECTED) 2] getAcl /kafka/brokers
'world,'anyone
: cdrwa
 * After running the tool:
 ** Zookeeper top-level nodes (kafka nodes created by the tool appeared here):
[zk: localhost:2181(CONNECTED) 3] ls /
[admin, brokers, cluster, config, controller, controller_epoch, delegation_token, isr_change_notification, kafka, kafka-acl, kafka-acl-changes, kafka-acl-extended, kafka-acl-extended-changes, latest_producer_id_block, log_dir_event_notification, zookeeper]
 ** Example node ACL:
[zk: localhost:2181(CONNECTED) 4] getAcl /kafka/brokers
'world,'anyone
: cdrwa
 ** New node ACL:
[zk: localhost:2181(CONNECTED) 5] getAcl /brokers
'sasl,'kafka
: cdrwa
'world,'anyone
: r

 

 

 

 
~~~~

### Comments (3)

1.

~~~~
[~lmairbus] You should explicitly specify the chroot when running zookeeper-security-migration.sh if a chroot is configured, as shown below:
{code:java}
bin/zookeeper-security-migration.sh --zookeeper.acl=secure --zookeeper.connect=localhost:2181/kafka{code}
Could you retry your scenario with this command above?
~~~~

2.

~~~~
[~huxi_2b] thanks for the reminder, I had obviously specified the chroot in Kafka server.properties but forgot to set it for the migrator tool. Sorry for this!

I confirm that when the root is correctly set the migrator works fine:

 
{code:java}
bin/zookeeper-security-migration.sh --zookeeper.acl=secure --zookeeper.connect=localhost:2181/kafka{code}
 
 * Before running the tool
 ** Zookeeper top-level nodes (all kafka nodes are under /kafka):
[zk: localhost:2181(CONNECTED) 1] ls /
[kafka, zookeeper]
 ** Example node ACL:
 [zk: localhost:2181(CONNECTED) 2] getAcl /kafka/brokers
'world,'anyone
: cdrwa
 * After running the tool:
 ** Zookeeper top-level nodes (no additional node):
[zk: localhost:2181(CONNECTED) 3] ls /
[kafka, zookeeper]
 ** Example node ACL (ACLs updated as expected):
[zk: localhost:2181(CONNECTED) 4] getAcl /kafka/brokers
'sasl,'kafka
: cdrwa
'world,'anyone
: r

I would only suggest maybe adding a check when the tool starts: before actually updating ACLs, making sure that the Kafka nodes exist, if not emit a warning/asks for user confirmation to proceed. In my case, since I had forgotten to specify the chroot the check would have failed.
~~~~

3.

~~~~
Issue resolved by pull request 7618
[https://github.com/apache/kafka/pull/7618]
~~~~

---

## KAFKA-9073: Kafka Streams State stuck in rebalancing after one of the StreamThread encounters java.lang.IllegalStateException: No current assignment for partition

https://issues.apache.org/jira/browse/KAFKA-9073

JIRA metadata: affects 2.3.0; fixed in 2.3.2, 2.4.0

- `KAFKA-9073@2.3.0`: config 2.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-9073@2.4.1`: config 2.4.1, metadata answer **not_affected** (later_patch)

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

## KAFKA-9173: StreamsPartitionAssignor assigns partitions to only one worker

https://issues.apache.org/jira/browse/KAFKA-9173

JIRA metadata: affects 2.2.1, 2.3.0; fixed in 2.6.0

- `KAFKA-9173@2.2.1`: config 2.2.1, metadata answer **affected** (listed_affected)
- `KAFKA-9173@2.2.0`: config 2.2.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.4, 2.6

### Description

~~~~
I'm running a distributed KafkaStreams application on 10 worker nodes, subscribed to 21 topics with 10 partitions in each. I'm only using a Processor interface, and a persistent state store.

However, only one worker gets assigned partitions, all other workers get nothing. Restarting the application, or cleaning local state stores does not help. StreamsPartitionAssignor migrates to other nodes, and eventually picks up other node to assign partitions to, but still only one node.

It's difficult to figure out where to look for the signs of problems, I'm attaching the log messages from the StreamsPartitionAssignor. Let me know what else I could provide to help resolve this.

[^StreamsPartitionAssignor.log]
~~~~

### Comments (21)

1.

~~~~
Hi [~o.muravskiy] it seems each one of your worker is configured with 20 threads (since I saw the total capacity is 20 each) is that right? And since at the beginning there's only one instance joining the group and gets all the 10 tasks, its prev-tasks contains all of them and somehow the stickiness totally overwhelm the workload balance so later rebalances still re-assign all of them back to the instance --- I suspect that's because the capacity (20) is large enough to host all 10 tasks but still this seems to be a valid issue to fix.

cc [~vvcephei] [~bbejeck] [~ableegoldman] who's already looking into improving the StreamsPartitionAssignor. Seems to be a real bug.
~~~~

2.

~~~~
I agree we should aim to fix this, but the workaround here is pretty simple – you just need to decrease the number of threads to better match the actual workload. If your app only has 10 tasks and you want to run 10 instances, each instance only needs one thread. Even if we did "fix" the assignor so that it spread the 10 tasks evenly across the 10 instances, 19 of the 20 threads would have no tasks assigned and nothing to do.

You can change num.threads to 1 for each instance, and you will see each be assigned one of the ten tasks
~~~~

3.

~~~~
Hi [~ableegoldman],

I think I'm missing something there. I have 210 partitions to consume from, and I have configured Streams to run with 200 threads.

Why do I have only 10 tasks?

 
~~~~

4.

~~~~
What exactly do you mean by "subscribed to 21 topics"? For example are you using pattern subscription and have 21 input topics you expect to match, or are you using 21 different topics in the same topology? 
~~~~

5.

~~~~
[~o.muravskiy] Note that the num.tasks are not equal to num.partitions, as many partitions of different topics can map to one task. Although I did not see your source code, from the logs I think 21 topics are mapped together into one sub-topology (if you do not understand the concept of sub-topology you can read it in the web docs here: https://docs.confluent.io/current/streams/architecture.html), and hence you still only have 10 tasks instead of 210 tasks.
~~~~

6.

~~~~
[~ableegoldman] yes, I subscribe with a pattern that matches 21 topics, each with 10 partitions.

[~guozhang] Well, I'm citing from the link you just posted above:
{quote}Slightly simplified, the *maximum parallelism* at which your application may run is bounded by the maximum number of stream tasks, which itself is determined by maximum number of partitions of the input topic(s) the application is reading from.
{quote}
So in my case the "maximum number of partitions of the input topic(s)" is 210. Yet I only get 10 tasks. 

I do have just one sub-topology, though:

{{ Sub-topology: 0}}
{{  Source: SOURCE (topics: raw-rrc\d\d)}}
{{    --> PROCESSOR_INGEST}}
{{  Processor: PROCESSOR_INGEST (stores: [BGP-State-Store])}}
{{    --> OUTPUT_ERROR, OUTPUT_MRT}}
{{    <-- SOURCE}}
{{  Sink: OUTPUT_ERROR (topic: error)}}
{{    <-- PROCESSOR_INGEST}}
{{  Sink: OUTPUT_MRT (extractor class: net.ripe.gii.ris.exabgp.ingestion.IngestExaBgpMessages$$Lambda$29/504582810@27912e3)}}
{{    <-- PROCESSOR_INGEST}}

 
~~~~

7.

~~~~
[~o.muravskiy] Sorry that I did not make myself clearer before, I meant to say "maximum num.partitions across the input topic(s)", rather not "sum of num.partitions". So in your case since all topics have 10 partitions each, the "max" of it is still 10; if you have a topic which has, say 11 partitions, then the "max" is 11 and the num.tasks would be 11.
~~~~

8.

~~~~
I understand that this is how it is *implemented*, but it is not how it is *documented*, or at least I don't see it anywhere in the Streams documentation, apart from the description of the (default and only one) {{DefaultPartitionGrouper}}.

Is there a reason for such behaviour? Could I just implement an alternative {{PartitionGrouper}} that will assign each partition to a new task?
~~~~

9.

~~~~
That's a good point, it does need to be documented. We should consider making this more flexible, either by making this user-customizable (for example by adding a `separateNodeGroups` flag to the StreamBuilder.stream(Pattern) overload or maybe by autoscaling according to some heuristic. 

As far as workarounds for now, I wouldn't necessarily recommend implementing a custom PartitionGrouper since that's been deprecated in 2.4. You could always use normal topic subscription to source each individually and then do something like for (KStream stream : inputTopics) { _processingTopology(stream)_ } 
~~~~

10.

~~~~
[~o.muravskiy] Opened [this PR|https://github.com/apache/kafka/pull/7793] to clarify the grouping in the docs/javadocs. Let me know if you have any thoughts on how to better explain this
~~~~

11.

~~~~
Seems it's only documented it Confluent docs and we missed to update AK docs: [https://docs.confluent.io/current/streams/architecture.html#stream-partitions-and-tasks]
~~~~

12.

~~~~
[~ableegoldman] Can you help to port the CP docs to AK docs, too?
~~~~

13.

~~~~
[~mjsax] See [https://github.com/apache/kafka/pull/7808] & [https://github.com/apache/kafka-site/pull/244]
~~~~

14.

~~~~
Ack
~~~~

15.

~~~~
So should we close this as "not a problem" as the system behaves as designed?
~~~~

16.

~~~~
Sounds good to me.
~~~~

17.

~~~~
Well, we touched upon three issues here.

The very first one reported – that all 10 tasks are assigned to the same node, when 10 different nodes are present – still sounds like a bug to me.

The second issue is that when 210 partitions are available to consume from, only 10 tasks are created. It is "designed" to behave like that, but I would argue this is not very productive "design" and should be improved.

And the last issue is that this "design" is not documented very clearly.

Cheers,
Oleg
~~~~

18.

~~~~
Still an issue
~~~~

19.

~~~~
Yes you're right, we still need to figure out why the assignor is so sticky and fix it. Sorry for closing it too soon.
~~~~

20.

~~~~
{quote}The second issue is that when 210 partitions are available to consume from, only 10 tasks are created. It is "designed" to behave like that, but I would argue this is not very productive "design" and should be improved.
{quote}
Feel free to create a new ticket for this case. There might be some corner cases for which we can support this. This ticket is marked as "bug" and we should split both concerns; the new ticket should be am "improvement" ticket. Thanks.
~~~~

21.

~~~~
The issue that all 10 tasks are assigned to the same node is fixed with KIP-441 and the following PR adds unit tests that verify it:
https://github.com/apache/kafka/pull/8689

For the other issues, new tickets should be created as [~mjsax] proposed.

I will close this ticket as fixed in 2.6.
~~~~

---

## KAFKA-9212: Keep receiving FENCED_LEADER_EPOCH while sending ListOffsetRequest

https://issues.apache.org/jira/browse/KAFKA-9212

JIRA metadata: affects 2.3.0, 2.3.1; fixed in 2.3.2, 2.4.0

- `KAFKA-9212@2.3.0`: config 2.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-9212@2.4.0`: config 2.4.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 2.3, 2.2.1, 2.3.1, 2.3.0, 1.1.1, 2.4.0, 2.2

### Description

~~~~
When running Kafka connect s3 sink connector ( confluent 5.3.0), after one broker got restarted (leaderEpoch updated at this point), the connect worker crashed with the following error : 

[2019-11-19 16:20:30,097] ERROR [Worker clientId=connect-1, groupId=connect-ls] Uncaught exception in herder work thread, exiting: (org.apache.kafka.connect.runtime.distributed.DistributedHerder:253)
 org.apache.kafka.common.errors.TimeoutException: Failed to get offsets by times in 30003ms

 

After investigation, it seems it's because it got fenced when sending ListOffsetRequest in loop and then got timed out , as follows :

[2019-11-19 16:20:30,020] DEBUG [Consumer clientId=consumer-3, groupId=connect-ls] Sending ListOffsetRequest (type=ListOffsetRequest, replicaId=-1, partitionTimestamps={connect_ls_config-0={timestamp: -1, maxNumOffsets: 1, currentLeaderEpoch: Optional[1]}}, isolationLevel=READ_UNCOMMITTED) to broker kafka6.fra2.internal:9092 (id: 4 rack: null) (org.apache.kafka.clients.consumer.internals.Fetcher:905)

[2019-11-19 16:20:30,044] DEBUG [Consumer clientId=consumer-3, groupId=connect-ls] Attempt to fetch offsets for partition connect_ls_config-0 failed due to FENCED_LEADER_EPOCH, retrying. (org.apache.kafka.clients.consumer.internals.Fetcher:985)

 

The above happens multiple times until timeout.

 

According to the debugs, the consumer always get a leaderEpoch of 1 for this topic when starting up :

 
 [2019-11-19 13:27:30,802] DEBUG [Consumer clientId=consumer-3, groupId=connect-ls] Updating last seen epoch from null to 1 for partition connect_ls_config-0 (org.apache.kafka.clients.Metadata:178)
  
  
 But according to our brokers log, the leaderEpoch should be 2, as follows :
  
 [2019-11-18 14:19:28,988] INFO [Partition connect_ls_config-0 broker=4] connect_ls_config-0 starts at Leader Epoch 2 from offset 22. Previous Leader Epoch was: 1 (kafka.cluster.Partition)
  
  
 This make impossible to restart the worker as it will always get fenced and then finally timeout.
  
 It is also impossible to consume with a 2.3 kafka-console-consumer as follows :
  
 kafka-console-consumer --bootstrap-server BOOTSTRAPSERVER:9092 --topic connect_ls_config --from-beginning 
  
 the above will just hang forever ( which is not expected cause there is data) and we can see those debug messages :

[2019-11-19 22:17:59,124] DEBUG [Consumer clientId=consumer-1, groupId=console-consumer-3844] Attempt to fetch offsets for partition connect_ls_config-0 failed due to FENCED_LEADER_EPOCH, retrying. (org.apache.kafka.clients.consumer.internals.Fetcher)
  
  
 Interesting fact, if we do subscribe the same way with kafkacat (1.5.0) we can consume without problem ( must be the way kafkacat is consuming ignoring FENCED_LEADER_EPOCH):
  
 kafkacat -b BOOTSTRAPSERVER:9092 -t connect_ls_config -o beginning
  
  
~~~~

### Comments (6)

1.

~~~~
As expected, when we use a 2.2.1 API client ( kafka-console-consumer) this works fine, sureley because it's ingnoring FENCED_LEADER_EPOCH answers
~~~~

2.

~~~~
Here are leader-epoch-checkpoint on each broker ( 3 in total which are 1, 3 and 4l)

 

Broker ID 4 ( the current partition leader during issue):

cat /var/lib/kafka/logs/connect_ls_config-0/leader-epoch-checkpoint
0
2
0 0
2 22

 

Broker ID 1 :

cat /var/lib/kafka/logs/connect_ls_config-0/leader-epoch-checkpoint
0
1
0 0

 

Broker ID 3:

cat /var/lib/kafka/logs/connect_ls_config-0/leader-epoch-checkpoint
0
1
0 0

 

 

And config topic comes from kafka connect worker default creation ( compacted topic) :

Topic:connect_ls_config PartitionCount:1 ReplicationFactor:3 Configs:min.insync.replicas=2,cleanup.policy=compact,segment.bytes=1073741824,max.message.bytes=30000000

 
~~~~

3.

~~~~
[~Lambruschi] The output from the leader epoch checkpoints is curious. The contents should match for all replicas. Is replication working for this partition? I'd suggest using `bin/kafka-dump-log.sh` to dump the log contents for each `.log` file for that partition and see if they match. It would also be useful to see the broker config.
~~~~

4.

~~~~
Yeah the topic is correctly replicated according metadata output from tools like kafkacat :

 

As of today, we downgrade our clients to 2.2.1 to avoid being stuck in this fencing loop ( 2.3 client handle the FENCED_LEADER_EPOCH ).

We restarted the 3 brokers ( rolling restart) and still have discrepancies between those checkpoint files as follows :

 

Broker ID 4 :

cat /var/lib/kafka/logs/connect_ls_config-0/leader-epoch-checkpoint
0
2
0 0
6 22

 

Broker ID 1 :

cat /var/lib/kafka/logs/connect_ls_config-0/leader-epoch-checkpoint
0
2
0 0
5 22

 

Broker ID 3:

cat /var/lib/kafka/logs/connect_ls_config-0/leader-epoch-checkpoint
0
1
0 0

 

 

Regarding the dump of this topic, here they are ( there is just one .log file . for all brokers) ( cannot show the content using print-data-log as it might contain sensitive info) :

 

Broker ID 1 :

/opt/kafka/bin/kafka-run-class.sh kafka.tools.DumpLogSegments --files /var/lib/kafka/logs/connect_ls_config-0/00000000000000000000.log
Dumping /var/lib/kafka/logs/connect_ls_config-0/00000000000000000000.log
Starting offset: 0
baseOffset: 0 lastOffset: 0 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 0 CreateTime: 1573660711038 size: 962 magic: 2 compresscodec: NONE crc: 1786879997 isvalid: true
baseOffset: 1 lastOffset: 1 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 962 CreateTime: 1573660712089 size: 1009 magic: 2 compresscodec: NONE crc: 1230182444 isvalid: true
baseOffset: 2 lastOffset: 3 count: 2 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 1971 CreateTime: 1573660712091 size: 1957 magic: 2 compresscodec: NONE crc: 2419651795 isvalid: true
baseOffset: 4 lastOffset: 4 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 3928 CreateTime: 1573660712611 size: 89 magic: 2 compresscodec: NONE crc: 3321423372 isvalid: true
baseOffset: 5 lastOffset: 5 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 4017 CreateTime: 1573751698440 size: 962 magic: 2 compresscodec: NONE crc: 704355531 isvalid: true
baseOffset: 6 lastOffset: 6 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 4979 CreateTime: 1573751699462 size: 1009 magic: 2 compresscodec: NONE crc: 1489459952 isvalid: true
baseOffset: 7 lastOffset: 8 count: 2 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 5988 CreateTime: 1573751699463 size: 1957 magic: 2 compresscodec: NONE crc: 657348671 isvalid: true
baseOffset: 9 lastOffset: 9 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 7945 CreateTime: 1573751699985 size: 89 magic: 2 compresscodec: NONE crc: 1825092385 isvalid: true
baseOffset: 10 lastOffset: 11 count: 2 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 8034 CreateTime: 1573828311242 size: 104 magic: 2 compresscodec: NONE crc: 3533917687 isvalid: true
baseOffset: 12 lastOffset: 12 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 8138 CreateTime: 1573828467292 size: 953 magic: 2 compresscodec: NONE crc: 232359935 isvalid: true
baseOffset: 13 lastOffset: 13 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 9091 CreateTime: 1573828467807 size: 1000 magic: 2 compresscodec: NONE crc: 1484213287 isvalid: true
baseOffset: 14 lastOffset: 15 count: 2 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 10091 CreateTime: 1573828467808 size: 1939 magic: 2 compresscodec: NONE crc: 49865436 isvalid: true
baseOffset: 16 lastOffset: 16 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 12030 CreateTime: 1573828468331 size: 94 magic: 2 compresscodec: NONE crc: 1480833250 isvalid: true
baseOffset: 17 lastOffset: 17 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 12124 CreateTime: 1573828530715 size: 986 magic: 2 compresscodec: NONE crc: 678439265 isvalid: true
baseOffset: 18 lastOffset: 19 count: 2 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 13110 CreateTime: 1573828531239 size: 2005 magic: 2 compresscodec: NONE crc: 1542429159 isvalid: true
baseOffset: 20 lastOffset: 20 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 15115 CreateTime: 1573828531239 size: 1033 magic: 2 compresscodec: NONE crc: 865245135 isvalid: true
baseOffset: 21 lastOffset: 21 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 16148 CreateTime: 1573828531761 size: 101 magic: 2 compresscodec: NONE crc: 4023495638 isvalid: true

 

 

Broker ID 3 :

 

~$ /opt/kafka/bin/kafka-run-class.sh kafka.tools.DumpLogSegments --files /var/lib/kafka/logs/connect_ls_config-0/00000000000000000000.log
Dumping /var/lib/kafka/logs/connect_ls_config-0/00000000000000000000.log
Starting offset: 0
baseOffset: 0 lastOffset: 0 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 0 CreateTime: 1573660711038 size: 962 magic: 2 compresscodec: NONE crc: 1786879997 isvalid: true
baseOffset: 1 lastOffset: 1 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 962 CreateTime: 1573660712089 size: 1009 magic: 2 compresscodec: NONE crc: 1230182444 isvalid: true
baseOffset: 2 lastOffset: 3 count: 2 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 1971 CreateTime: 1573660712091 size: 1957 magic: 2 compresscodec: NONE crc: 2419651795 isvalid: true
baseOffset: 4 lastOffset: 4 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 3928 CreateTime: 1573660712611 size: 89 magic: 2 compresscodec: NONE crc: 3321423372 isvalid: true
baseOffset: 5 lastOffset: 5 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 4017 CreateTime: 1573751698440 size: 962 magic: 2 compresscodec: NONE crc: 704355531 isvalid: true
baseOffset: 6 lastOffset: 6 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 4979 CreateTime: 1573751699462 size: 1009 magic: 2 compresscodec: NONE crc: 1489459952 isvalid: true
baseOffset: 7 lastOffset: 8 count: 2 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 5988 CreateTime: 1573751699463 size: 1957 magic: 2 compresscodec: NONE crc: 657348671 isvalid: true
baseOffset: 9 lastOffset: 9 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 7945 CreateTime: 1573751699985 size: 89 magic: 2 compresscodec: NONE crc: 1825092385 isvalid: true
baseOffset: 10 lastOffset: 11 count: 2 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 8034 CreateTime: 1573828311242 size: 104 magic: 2 compresscodec: NONE crc: 3533917687 isvalid: true
baseOffset: 12 lastOffset: 12 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 8138 CreateTime: 1573828467292 size: 953 magic: 2 compresscodec: NONE crc: 232359935 isvalid: true
baseOffset: 13 lastOffset: 13 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 9091 CreateTime: 1573828467807 size: 1000 magic: 2 compresscodec: NONE crc: 1484213287 isvalid: true
baseOffset: 14 lastOffset: 15 count: 2 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 10091 CreateTime: 1573828467808 size: 1939 magic: 2 compresscodec: NONE crc: 49865436 isvalid: true
baseOffset: 16 lastOffset: 16 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 12030 CreateTime: 1573828468331 size: 94 magic: 2 compresscodec: NONE crc: 1480833250 isvalid: true
baseOffset: 17 lastOffset: 17 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 12124 CreateTime: 1573828530715 size: 986 magic: 2 compresscodec: NONE crc: 678439265 isvalid: true
baseOffset: 18 lastOffset: 19 count: 2 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 13110 CreateTime: 1573828531239 size: 2005 magic: 2 compresscodec: NONE crc: 1542429159 isvalid: true
baseOffset: 20 lastOffset: 20 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 15115 CreateTime: 1573828531239 size: 1033 magic: 2 compresscodec: NONE crc: 865245135 isvalid: true
baseOffset: 21 lastOffset: 21 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 16148 CreateTime: 1573828531761 size: 101 magic: 2 compresscodec: NONE crc: 4023495638 isvalid: true

 

 

Broker ID 4 : 

 

Dumping /var/lib/kafka/logs/connect_ls_config-0/00000000000000000000.log
Starting offset: 0
baseOffset: 0 lastOffset: 0 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 0 CreateTime: 1573660711038 size: 962 magic: 2 compresscodec: NONE crc: 1786879997 isvalid: true
baseOffset: 1 lastOffset: 1 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 962 CreateTime: 1573660712089 size: 1009 magic: 2 compresscodec: NONE crc: 1230182444 isvalid: true
baseOffset: 2 lastOffset: 3 count: 2 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 1971 CreateTime: 1573660712091 size: 1957 magic: 2 compresscodec: NONE crc: 2419651795 isvalid: true
baseOffset: 4 lastOffset: 4 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 3928 CreateTime: 1573660712611 size: 89 magic: 2 compresscodec: NONE crc: 3321423372 isvalid: true
baseOffset: 5 lastOffset: 5 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 4017 CreateTime: 1573751698440 size: 962 magic: 2 compresscodec: NONE crc: 704355531 isvalid: true
baseOffset: 6 lastOffset: 6 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 4979 CreateTime: 1573751699462 size: 1009 magic: 2 compresscodec: NONE crc: 1489459952 isvalid: true
baseOffset: 7 lastOffset: 8 count: 2 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 5988 CreateTime: 1573751699463 size: 1957 magic: 2 compresscodec: NONE crc: 657348671 isvalid: true
baseOffset: 9 lastOffset: 9 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 7945 CreateTime: 1573751699985 size: 89 magic: 2 compresscodec: NONE crc: 1825092385 isvalid: true
baseOffset: 10 lastOffset: 11 count: 2 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 8034 CreateTime: 1573828311242 size: 104 magic: 2 compresscodec: NONE crc: 3533917687 isvalid: true
baseOffset: 12 lastOffset: 12 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 8138 CreateTime: 1573828467292 size: 953 magic: 2 compresscodec: NONE crc: 232359935 isvalid: true
baseOffset: 13 lastOffset: 13 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 9091 CreateTime: 1573828467807 size: 1000 magic: 2 compresscodec: NONE crc: 1484213287 isvalid: true
baseOffset: 14 lastOffset: 15 count: 2 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 10091 CreateTime: 1573828467808 size: 1939 magic: 2 compresscodec: NONE crc: 49865436 isvalid: true
baseOffset: 16 lastOffset: 16 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 12030 CreateTime: 1573828468331 size: 94 magic: 2 compresscodec: NONE crc: 1480833250 isvalid: true
baseOffset: 17 lastOffset: 17 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 12124 CreateTime: 1573828530715 size: 986 magic: 2 compresscodec: NONE crc: 678439265 isvalid: true
baseOffset: 18 lastOffset: 19 count: 2 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 13110 CreateTime: 1573828531239 size: 2005 magic: 2 compresscodec: NONE crc: 1542429159 isvalid: true
baseOffset: 20 lastOffset: 20 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 15115 CreateTime: 1573828531239 size: 1033 magic: 2 compresscodec: NONE crc: 865245135 isvalid: true
baseOffset: 21 lastOffset: 21 count: 1 baseSequence: -1 lastSequence: -1 producerId: -1 producerEpoch: -1 partitionLeaderEpoch: 0 isTransactional: false isControl: false position: 16148 CreateTime: 1573828531761 size: 101 magic: 2 compresscodec: NONE crc: 4023495638 isvalid: true

 

 

 

Here is the conf used by all brokers : 

 

broker.id=XX

delete.topic.enable=true


listeners=INSIDE://0.0.0.0:9092,OUTSIDE://0.0.0.0:9492
advertised.listeners=REDACTED
listener.security.protocol.map=INSIDE:PLAINTEXT,OUTSIDE:SSL
inter.broker.listener.name=INSIDE
#SSL conf REDACTED

ssl.client.auth=required
num.network.threads=3

num.io.threads=8

socket.send.buffer.bytes=102400

socket.receive.buffer.bytes=102400

socket.request.max.bytes=104857600

inter.broker.protocol.version=2.3

 auto.create.topics.enable=true

log.dirs=/var/lib/kafka/logs

num.partitions=3

num.recovery.threads.per.data.dir=1

default.replication.factor=3

offsets.topic.replication.factor=3
transaction.state.log.replication.factor=3
transaction.state.log.min.isr=2

replica.socket.timeout.ms=30000

replica.fetch.wait.max.ms=5000

replica.lag.time.max.ms=15000

min.insync.replicas=2

acks=all

log.retention.hours=24


log.segment.bytes=1073741824

log.retention.check.interval.ms=300000

log.roll.hours=168


zookeeper.connect=REDACTED

zookeeper.connection.timeout.ms=6000

 

group.initial.rebalance.delay.ms=3000

transactional.id.expiration.ms=1814400000

offsets.retention.minutes=11580

 

 
~~~~

5.

~~~~
Chiming in here, I believe we've experienced the same error. I've been able to reproduce the behavior quite simply, as follows:
 - 3-broker cluster (running Apache Kafka 2.3.1)
 - one partition with replica assignment (0, 1, 2)
 - booted fourth broker (id 3)
 - initiated partition reassignment from (0, 1, 2) to (0, 1, 2, 3) with a very low throttle (for testing)

As soon as the assignment begins, a 2.3.0 console consumer simply hangs when started. A 1.1.1 consumer does not have any issues. I see this in leader broker's request logs:
{code:java}
[2019-12-05 16:38:36,790] DEBUG Completed request:RequestHeader(apiKey=LIST_OFFSETS, apiVersion=5, clientId=consumer-1, correlationId=1529) -- {replica_id=-1,isolation_level=0,topics=[{topic=DataPlatform.CGSynthTests,partitions=[{partition=0,current_leader_epoch=0,timestamp=-1}]}]},response:{throttle_time_ms=0,responses=[{topic=DataPlatform.CGSynthTests,partition_responses=[{partition=0,error_code=74,timestamp=-1,offset=-1,leader_epoch=-1}]}]} from connection 172.22.15.67:9092-172.22.23.98:46974-9;totalTime:0.27,requestQueueTime:0.044,localTime:0.185,remoteTime:0.0,throttleTime:0.036,responseQueueTime:0.022,sendTime:0.025,securityProtocol:PLAINTEXT,principal:User:data-pipeline-monitor,listener:PLAINTEXT (kafka.request.logger)
{code}
Note the producer fenced error code for list offsets, as in the original report.

Once the reassignment completes, the 2.3.1 console consumer starts working. I've also tried a different reassignment (0, 1, 2) -> (3, 1, 2) with the same results.

Where we stand right now is we can't initiate partition reassignments in our production cluster without paralyzing a Spark application (using 2.3.0 client libs under the hood). Downgrading the Kafka client libs there isn't possible since they are part of the Spark assembly.

Any pointers on what the issue might be here? Struggling to understand the bug because it seems like any partition reassignment breaks LIST_OFFSETS requests from 2.3 clients, but that just seems to be too severe a problem to have gone unnoticed for so long. Even ideas for a workaround would help here, since we don't see a path to do partition reassignments without causing a production incident right now.
~~~~

6.

~~~~
[~mjaschob@twilio.com] Really appreciate the extra detail. I was able to reproduce this on trunk following your instructions. What I see is the controller sending a stale epoch in the UPDATE_METADATA request which follows the initiation of the reassignment. I will work on a patch to fix the controller and I will try to make the case for the 2.4.0 release. Note that fixing this does require a broker upgrade. Until a patch is available, probably the best option is to use the 2.2 or lower clients.
~~~~

---

## KAFKA-9233: Kafka consumer throws undocumented IllegalStateException

https://issues.apache.org/jira/browse/KAFKA-9233

JIRA metadata: affects 2.3.0; fixed in 2.5.0

- `KAFKA-9233@2.3.0`: config 2.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-9233@2.5.0`: config 2.5.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 2.2.1, 2.5.0, 2.6.0

### Description

~~~~
If the provided collection of TopicPartition instances contains any duplicates, an IllegalStateException not documented in the javadoc is thrown by internal Java stream code when calling KafkaConsumer#beginningOffsets or KafkaConsumer#endOffsets.

The stack trace looks like this,

{noformat}
java.lang.IllegalStateException: Duplicate key -2
	at java.util.stream.Collectors.lambda$throwingMerger$0(Collectors.java:133)
	at java.util.HashMap.merge(HashMap.java:1254)
	at java.util.stream.Collectors.lambda$toMap$58(Collectors.java:1320)
	at java.util.stream.ReduceOps$3ReducingSink.accept(ReduceOps.java:169)
	at java.util.ArrayList$ArrayListSpliterator.forEachRemaining(ArrayList.java:1382)
	at java.util.stream.AbstractPipeline.copyInto(AbstractPipeline.java:481)
	at java.util.stream.AbstractPipeline.wrapAndCopyInto(AbstractPipeline.java:471)
	at java.util.stream.ReduceOps$ReduceOp.evaluateSequential(ReduceOps.java:708)
	at java.util.stream.AbstractPipeline.evaluate(AbstractPipeline.java:234)
	at java.util.stream.ReferencePipeline.collect(ReferencePipeline.java:499)
	at org.apache.kafka.clients.consumer.internals.Fetcher.beginningOrEndOffset(Fetcher.java:555)
	at org.apache.kafka.clients.consumer.internals.Fetcher.beginningOffsets(Fetcher.java:542)
	at org.apache.kafka.clients.consumer.KafkaConsumer.beginningOffsets(KafkaConsumer.java:2054)
	at org.apache.kafka.clients.consumer.KafkaConsumer.beginningOffsets(KafkaConsumer.java:2031)
{noformat}

{noformat}
java.lang.IllegalStateException: Duplicate key -1
	at java.util.stream.Collectors.lambda$throwingMerger$0(Collectors.java:133)
	at java.util.HashMap.merge(HashMap.java:1254)
	at java.util.stream.Collectors.lambda$toMap$58(Collectors.java:1320)
	at java.util.stream.ReduceOps$3ReducingSink.accept(ReduceOps.java:169)
	at java.util.ArrayList$ArrayListSpliterator.forEachRemaining(ArrayList.java:1382)
	at java.util.stream.AbstractPipeline.copyInto(AbstractPipeline.java:481)
	at java.util.stream.AbstractPipeline.wrapAndCopyInto(AbstractPipeline.java:471)
	at java.util.stream.ReduceOps$ReduceOp.evaluateSequential(ReduceOps.java:708)
	at java.util.stream.AbstractPipeline.evaluate(AbstractPipeline.java:234)
	at java.util.stream.ReferencePipeline.collect(ReferencePipeline.java:499)
	at org.apache.kafka.clients.consumer.internals.Fetcher.beginningOrEndOffset(Fetcher.java:559)
	at org.apache.kafka.clients.consumer.internals.Fetcher.endOffsets(Fetcher.java:550)
	at org.apache.kafka.clients.consumer.KafkaConsumer.endOffsets(KafkaConsumer.java:2109)
	at org.apache.kafka.clients.consumer.KafkaConsumer.endOffsets(KafkaConsumer.java:2081)
{noformat}

Looking at the code, it appears this may likely have been introduced by KAFKA-7831. The exception is not thrown in Kafka 2.2.1, with the duplicated TopicPartition values silently ignored. Either we should document this exception possibility (probably wrapping it with a Kafka exception class) indicating invalid client API usage, or restore the previous behavior where the duplicates were harmless.
~~~~

### Comments (6)

1.

~~~~
Set priority to minor since it is easily worked around by using a Set instead of a List or otherwise being smarter about how the collection of TopicPartition values is gathered.
~~~~

2.

~~~~
Pull request: https://github.com/apache/kafka/pull/7755
~~~~

3.

~~~~
[~hachikuji] Can you review this?
~~~~

4.

~~~~
[~junrao] or [~hachikuji] Can you review this?
~~~~

5.

~~~~
Adding 2.5.0 fix version optimistically
~~~~

6.

~~~~
Changing version from 2.6.0 to 2.5.0 (committed [here|https://github.com/apache/kafka/commit/4b2268bd296e348f5a1cbe02cfc763167ea304e2]).
~~~~

---

## KAFKA-9338: Incremental fetch sessions do not maintain or use leader epoch for fencing purposes

https://issues.apache.org/jira/browse/KAFKA-9338

JIRA metadata: affects 2.1.0, 2.2.0, 2.3.0, 2.4.0; fixed in 2.5.0

- `KAFKA-9338@2.4.0`: config 2.4.0, metadata answer **affected** (listed_affected)
- `KAFKA-9338@2.5.0`: config 2.5.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 2.1.0, 2.3.0, 2.5, 2.4

### Description

~~~~
KIP-320 adds the ability to fence replicas by detecting stale leader epochs from followers, and helping consumers handle unclean truncation.

Unfortunately the incremental fetch session handling does not maintain or use the leader epoch in the fetch session cache. As a result, it does not appear that the leader epoch is used for fencing a majority of the time. I'm not sure if this is only the case after incremental fetch sessions are established - it may be the case that the first "full" fetch session is safe.

Optional.empty is returned for the FetchRequest.PartitionData here:

[https://github.com/apache/kafka/blob/a4cbdc6a7b3140ccbcd0e2339e28c048b434974e/core/src/main/scala/kafka/server/FetchSession.scala#L111]

I believe this affects brokers from 2.1.0 when fencing was improved on the replica fetcher side, and 2.3.0 and above for consumers, which is when client side truncation detection was added on the consumer side.
~~~~

### Comments (3)

1.

~~~~
Cc [~hachikuji] [~cmccabe]
~~~~

2.

~~~~
[~lucasbradstreet] Thanks, good find.
~~~~

3.

~~~~
Marking this just as 2.5 for now. If we don't find any problems, we will backport to 2.4 at least.
~~~~

---

## KAFKA-9706: Flatten transformation fails when encountering tombstone event

https://issues.apache.org/jira/browse/KAFKA-9706

JIRA metadata: affects 2.0.1, 2.1.1, 2.2.2, 2.3.1, 2.4.1; fixed in 2.1.2, 2.2.3, 2.3.2, 2.4.2, 2.5.0

- `KAFKA-9706@2.0.1`: config 2.0.1, metadata answer **affected** (listed_affected)
- `KAFKA-9706@2.5.0`: config 2.5.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 2.5, 2.4, 2.3, 2.2, 2.1

### Description

~~~~
When applying the {{Flatten}} transformation to a tombstone event, an exception is raised:
{code:java}
org.apache.kafka.connect.errors.DataException: Only Map objects supported in absence of schema for [flattening], found: null
{code}
Instead, the transform should pass the tombstone through the transform without throwing an exception.
~~~~

### Comments (1)

1.

~~~~
Merged to {{trunk}} and release branches {{2.5, 2.4, 2.3, 2.2 and 2.1}}
~~~~

---

## KAFKA-9747: No tasks created for a connector

https://issues.apache.org/jira/browse/KAFKA-9747

JIRA metadata: affects 2.4.0; fixed in 2.8.1, 3.0.1, 3.1.0

- `KAFKA-9747@2.4.0`: config 2.4.0, metadata answer **affected** (listed_affected)
- `KAFKA-9747@2.8.2`: config 2.8.2, metadata answer **not_affected** (later_patch)

Known Kafka versions mentioned in text: none

### Description

~~~~
We are running Kafka Connect in a distributed mode on 3 nodes using Debezium (MongoDB) and Confluent S3 connectors. When adding a new connector via the REST API the connector is created in RUNNING state, but no tasks are created for the connector.

Pausing and resuming the connector does not help. When we stop all workers and then start them again, the tasks are created and everything runs as it should.

The issue does not show up if we run only a single node.

The issue is not caused by the connector plugins, because we see the same behaviour for both Debezium and S3 connectors. Also in debug logs I can see that Debezium is correctly returning a task configuration from the Connector.taskConfigs() method.

Connector configuration examples

Debezium:
{code}
{
  "name": "qa-mongodb-comp-converter-task|1",
  "config": {
    "connector.class": "io.debezium.connector.mongodb.MongoDbConnector",
    "mongodb.hosts": "mongodb-qa-001:27017,mongodb-qa-002:27017,mongodb-qa-003:27017",
    "mongodb.name": "qa-debezium-comp",
    "mongodb.ssl.enabled": true,
    "collection.whitelist": "converter[.]task",
    "tombstones.on.delete": true
  }
}
{code}
S3 Connector:
{code}
{
  "name": "qa-s3-sink-task|1",
  "config": {
    "connector.class": "io.confluent.connect.s3.S3SinkConnector",
    "topics": "qa-debezium-comp.converter.task",
    "topics.dir": "data/env/qa",
    "s3.region": "eu-west-1",
    "s3.bucket.name": "<bucket-name>",
    "flush.size": "15000",
    "rotate.interval.ms": "3600000",
    "storage.class": "io.confluent.connect.s3.storage.S3Storage",
    "format.class": "custom.kafka.connect.s3.format.plaintext.PlaintextFormat",
    "schema.generator.class": "io.confluent.connect.storage.hive.schema.DefaultSchemaGenerator",
    "partitioner.class": "io.confluent.connect.storage.partitioner.DefaultPartitioner",
    "schema.compatibility": "NONE",
    "key.converter": "org.apache.kafka.connect.json.JsonConverter",
    "value.converter": "org.apache.kafka.connect.json.JsonConverter",
    "key.converter.schemas.enable": false,
    "value.converter.schemas.enable": false,
    "transforms": "ExtractDocument",
    "transforms.ExtractDocument.type":"custom.kafka.connect.transforms.ExtractDocument$Value"
  }
}
{code}
The connectors are created using curl: {{curl -X POST -H "Content-Type: application/json" --data @<json_file> http:/<connect_host>:10083/connectors}}


~~~~

### Comments (11)

1.

~~~~
Yes, Kafka Connect team, please at least give us a WARN or ERROR as to why the task can't be created or sustained.
~~~~

2.

~~~~
I also stuck with the sample problem, task isn't created. Although I get log:
'
{code:java}
[2020-05-20 07:20:33,131] INFO [Worker clientId=connect-1, groupId=xxxxxxxxxxx] Finished starting connectors and tasks (org.apache.kafka.connect.runtime.distributed.DistributedHerder)
{code}
 
~~~~

3.

~~~~
I'm seeing similar behavior, getting random tasks that are coming back as blank when checking status through the REST API. Then a second later, these tasks are showing as running on some machine after re-requesting the status. We have 10 Connect pods running in distributed mode with a load balancer pointing to the overarching k8s service for the Connect pods.
~~~~

4.

~~~~
+1 encountered similar issue.

running a customized sink conncector in distributed mode on 2 hosts but only 1 host has both connector & task whereas the other one just has connector running.
~~~~

5.

~~~~
I have the same issue here... MongoDB (Atlas), MongoDB Connector and AWS MSK.
~~~~

6.

~~~~
Have the same problem for Debezium (Mysql connector)
  
~~~~

7.

~~~~
Same issue for Debezium (SqlServer connector)
~~~~

8.

~~~~
[https://rmoff.net/2019/11/22/common-mistakes-made-when-configuring-multiple-kafka-connect-workers/] - after making sure that workers can communiate with each other the issue is gone in my case.
~~~~

9.

~~~~
If anyone has this problem and [~pawel.wilczynski@fieldaware.com]'s suggestion to ensure that workers can communicate with each other does not work, please provide more details of your environment, including:
* the Connect version
* the Connect worker configuration
* a description of how many workers you're using
* debug-level logs showing the startup through the time where the tasks are not being started

Thanks!
~~~~

10.

~~~~
The connect name contains a character which is considered as illegal char via HttpClient::newRequest
{noformat}
java.lang.IllegalArgumentException: Illegal character in path at index ......
	at java.net.URI.create(URI.java:852)
	at org.eclipse.jetty.client.HttpClient.newRequest(HttpClient.java:453)
...
Caused by: java.net.URISyntaxException: Illegal character in path at index .......
	at java.net.URI$Parser.fail(URI.java:2848)
	at java.net.URI$Parser.checkChars(URI.java:3021)
{noformat}
~~~~

11.

~~~~
To add more details to the issue:
 * When running multiple workers
 * AND the Connector name contains a non-URL compatible character
 * AND a follower worker has the Connector in its assignment
 * Then the follower->leader request sent over Connect REST fails in RestClient (without any error logging, or the corresponding future ever completed)
~~~~

---

## KAFKA-9807: Race condition updating high watermark allows reads above LSO

https://issues.apache.org/jira/browse/KAFKA-9807

JIRA metadata: affects 0.11.0.3, 1.0.2, 1.1.1, 2.0.1, 2.1.1, 2.2.2, 2.3.1, 2.4.1; fixed in 2.4.2, 2.5.0

- `KAFKA-9807@1.1.1`: config 1.1.1, metadata answer **affected** (listed_affected)
- `KAFKA-9807@2.5.0`: config 2.5.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: none

### Description

~~~~
We had a transaction system test fail with the following error:

{code}
AssertionError: Detected 37 dups in concurrently consumed messages
{code}

After investigation, we found the duplicates were a result of the consumer reading an aborted transaction, which should not be possible with the read_committed isolation level.

We tracked down the fetch request which returned the aborted data:

{code}
[2020-03-24 07:27:58,284] INFO Completed request:RequestHeader(apiKey=FETCH, apiVersion=11, clientId=console-consumer, correlationId=283) -- {replica_id=-1,max_wait_time=500,min_bytes=1,max_bytes=52428800,isolation_level=1,session_id=2043970605,session_epoch=87,topics=[{topic=output-topic,partitions=[{partition=1,current_leader_epoch=3,fetch_offset=48393,log_start_offset=-1,partition_max_bytes=1048576}]}],forgotten_topics_data=[],rack_id=},response:{throttle_time_ms=0,error_code=0,session_id=2043970605,responses=[{topic=output-topic,partition_responses=[{partition_header={partition=1,error_code=0,high_watermark=50646,last_stable_offset=50646,log_start_offset=0,aborted_transactions=[],preferred_read_replica=-1},record_set=FileRecords(size=31582, file=/mnt/kafka/kafka-data-logs-1/output-topic-1/00000000000000045694.log, start=37613, end=69195)}]}]} 
{code}

After correlating with the contents of the log segment 00000000000000045694.log, we found that this fetch response included data which was above the returned LSO which is 50646. In fact, the high watermark matched the LSO in this case, so the data was above the high watermark as well. 

At the same time this request was received, we noted that the high watermark was updated:

{code}
[2020-03-24 07:27:58,284] DEBUG [Partition output-topic-1 broker=3] High watermark updated from (offset=50646 segment=[45694:68690]) to (offset=50683 segment=[45694:69195]) (kafka.cluster.Partition)
{code}

The position of the new high watermark matched the end position from the fetch response, so that led us to believe there was a race condition with the updating of this value. In the code, we have the following (abridged) logic for fetching the LSO:

{code}
    firstUnstableOffsetMetadata match {
      case Some(offsetMetadata) if offsetMetadata.messageOffset < highWatermark => offsetMetadata
      case _ => fetchHighWatermarkMetadata
    }
{code}

If the first unstable offset is less than the high watermark, we should use that; otherwise we use the high watermark. The problem is that the high watermark referenced here could be updated between the range check and the call to `fetchHighWatermarkMetadata`. If that happens, we would end up reading data which is above the first unstable offset.

The solution to fix this problem is to cache the high watermark value so that it is used in both places. We may consider some additional improvements here as well, such as fixing the inconsistency problem in the fetch response which included data above the returned high watermark. We may also consider having the client react more defensively by ignoring fetched data above the high watermark. This would fix this problem for newer clients talking to older brokers which might hit this problem.
~~~~

### Comments (1)

1.

~~~~
Resolving this. I will likely backport to older branches when I get a chance. I will also open separate jiras for some of the additional improvements suggested above.
~~~~

---

## KAFKA-9844: Maximum number of members within a group is not always enforced due to a race condition in join group

https://issues.apache.org/jira/browse/KAFKA-9844

JIRA metadata: affects 2.5.0; fixed in 2.6.0

- `KAFKA-9844@2.5.0`: config 2.5.0, metadata answer **affected** (listed_affected)
- `KAFKA-9844@2.6.0`: config 2.6.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: none

### Description

~~~~
While analysing https://issues.apache.org/jira/browse/KAFKA-7965, I found out that the maximum number of members constraints is not always enforced due to a race condition.

When an unknown member joins the group, the group is automatically created if it does not exist. Then, it proceeds with a unknownJoinGroup. On that path, the limit is not enforced because we assumes that the group is empty as this stage because it did not exist. As the lookup and the creation are not protected by a lock, multiple join requests could end up on that path and thus bypass the enforcement.

Here is example of the logs captured while troubleshooting KAFKA-7965. The test setups 3 consumers and use a limit of 2. The logs show that the three members were able to join the group without being evicted.
{noformat}
[2020-04-05 13:29:03,145] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Discovered group coordinator localhost:36449 (id: 2147483645 rack: null) (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:794)
[2020-04-05 13:29:03,145] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Discovered group coordinator localhost:36449 (id: 2147483645 rack: null) (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:794)
[2020-04-05 13:29:03,151] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Discovered group coordinator localhost:36449 (id: 2147483645 rack: null) (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:794)
[2020-04-05 13:29:03,153] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Attempt to heartbeat failed since member id ConsumerTestConsumer-764a71ea-f9b3-462c-9986-8e6b2530d6e3 is not valid. (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:1054)
[2020-04-05 13:29:03,155] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Giving away all assigned partitions as lost since generation has been reset,indicating that consumer is no longer part of the group (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:670)
[2020-04-05 13:29:03,155] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Lost previously assigned partitions group-max-size-test-5, group-max-size-test-4 (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:314)
[2020-04-05 13:29:03,156] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] (Re-)joining group (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:551)
[2020-04-05 13:29:03,154] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Attempt to heartbeat failed since member id ConsumerTestConsumer-2d2886ad-1244-4ef7-9e07-62282c3547fd is not valid. (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:1054)
[2020-04-05 13:29:03,156] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Attempt to heartbeat failed since member id ConsumerTestConsumer-42d0fa9d-cfbb-458f-afe9-99a75fef8e08 is not valid. (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:1054)
[2020-04-05 13:29:03,157] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Giving away all assigned partitions as lost since generation has been reset,indicating that consumer is no longer part of the group (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:670)
[2020-04-05 13:29:03,158] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Lost previously assigned partitions group-max-size-test-2, group-max-size-test-3 (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:314)
[2020-04-05 13:29:03,158] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] (Re-)joining group (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:551)
[2020-04-05 13:29:03,157] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Giving away all assigned partitions as lost since generation has been reset,indicating that consumer is no longer part of the group (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:670)
[2020-04-05 13:29:03,159] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Lost previously assigned partitions group-max-size-test-1, group-max-size-test-0 (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:314)
[2020-04-05 13:29:03,159] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] (Re-)joining group (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:551)
[2020-04-05 13:29:03,160] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] (Re-)joining group (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:551)
[2020-04-05 13:29:03,161] INFO [GroupCoordinator 2]: Preparing to rebalance group group-max-size-test in state PreparingRebalance with old generation 0 (__consumer_offsets-0) (reason: Adding new member ConsumerTestConsumer-84fd5153-c425-464d-a724-04022a0608f7 with group instanceid None) (kafka.coordinator.group.GroupCoordinator:66)
[2020-04-05 13:29:03,158] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] (Re-)joining group (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:551)
[2020-04-05 13:29:03,160] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] (Re-)joining group (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:551)
[2020-04-05 13:29:03,171] INFO [GroupCoordinator 2]: Stabilized group group-max-size-test generation 1 (__consumer_offsets-0) (kafka.coordinator.group.GroupCoordinator:66)
[2020-04-05 13:29:03,605] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Finished assignment for group at generation 1: {ConsumerTestConsumer-84fd5153-c425-464d-a724-04022a0608f7=Assignment(partitions=[group-max-size-test-0, group-max-size-test-1]), ConsumerTestConsumer-e25aedeb-73fd-4fae-b56c-fa929f11a9df=Assignment(partitions=[group-max-size-test-4, group-max-size-test-5]), ConsumerTestConsumer-8ca065a1-2ce4-44d5-881c-c6f01cb0d110=Assignment(partitions=[group-max-size-test-2, group-max-size-test-3])} (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:605)
[2020-04-05 13:29:03,606] INFO [GroupCoordinator 2]: Assignment received from leader for group group-max-size-test for generation 1 (kafka.coordinator.group.GroupCoordinator:66)
[2020-04-05 13:29:03,610] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Successfully joined group with generation 1 (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:502)
[2020-04-05 13:29:03,611] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Adding newly assigned partitions: group-max-size-test-1, group-max-size-test-0 (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:276)
[2020-04-05 13:29:03,612] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Found no committed offset for partition group-max-size-test-1 (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:1297)
[2020-04-05 13:29:03,612] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Found no committed offset for partition group-max-size-test-0 (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:1297)
[2020-04-05 13:29:03,611] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Successfully joined group with generation 1 (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:502)
[2020-04-05 13:29:03,611] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Successfully joined group with generation 1 (org.apache.kafka.clients.consumer.internals.AbstractCoordinator:502)
[2020-04-05 13:29:03,614] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Adding newly assigned partitions: group-max-size-test-2, group-max-size-test-3 (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:276)
[2020-04-05 13:29:03,614] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Adding newly assigned partitions: group-max-size-test-5, group-max-size-test-4 (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:276)
[2020-04-05 13:29:03,616] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Found no committed offset for partition group-max-size-test-2 (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:1297)
[2020-04-05 13:29:03,617] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Found no committed offset for partition group-max-size-test-3 (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:1297)
[2020-04-05 13:29:03,617] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Resetting offset for partition group-max-size-test-1 to offset 0. (org.apache.kafka.clients.consumer.internals.SubscriptionState:383)
[2020-04-05 13:29:03,617] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Found no committed offset for partition group-max-size-test-5 (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:1297)
[2020-04-05 13:29:03,618] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Found no committed offset for partition group-max-size-test-4 (org.apache.kafka.clients.consumer.internals.ConsumerCoordinator:1297)
[2020-04-05 13:29:03,619] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Resetting offset for partition group-max-size-test-3 to offset 0. (org.apache.kafka.clients.consumer.internals.SubscriptionState:383)
[2020-04-05 13:29:03,619] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Resetting offset for partition group-max-size-test-4 to offset 0. (org.apache.kafka.clients.consumer.internals.SubscriptionState:383)
[2020-04-05 13:29:03,645] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Resetting offset for partition group-max-size-test-2 to offset 0. (org.apache.kafka.clients.consumer.internals.SubscriptionState:383)
[2020-04-05 13:29:03,646] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Resetting offset for partition group-max-size-test-0 to offset 0. (org.apache.kafka.clients.consumer.internals.SubscriptionState:383)
[2020-04-05 13:29:03,651] INFO [Consumer clientId=ConsumerTestConsumer, groupId=group-max-size-test] Resetting offset for partition group-max-size-test-5 to offset 0. (org.apache.kafka.clients.consumer.internals.SubscriptionState:383){noformat}
~~~~

---

## KAFKA-9981: Running a dedicated mm2 cluster with more than one nodes,When the configuration is updated the task is not aware and will lose the update operation.

https://issues.apache.org/jira/browse/KAFKA-9981

JIRA metadata: affects 2.4.0, 2.4.1, 2.5.0; fixed in 3.5.0

- `KAFKA-9981@2.4.0`: config 2.4.0, metadata answer **affected** (listed_affected)
- `KAFKA-9981@3.5.0`: config 3.5.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 2.0

### Description

~~~~
DistributedHerder.reconfigureConnector induction config update as follows:
{code:java}
if (changed) {
    List<Map<String, String>> rawTaskProps = reverseTransform(connName, configState, taskProps);
    if (isLeader()) {
        configBackingStore.putTaskConfigs(connName, rawTaskProps);
        cb.onCompletion(null, null);
    } else {
        // We cannot forward the request on the same thread because this reconfiguration can happen as a result of connector
        // addition or removal. If we blocked waiting for the response from leader, we may be kicked out of the worker group.
        forwardRequestExecutor.submit(new Runnable() {
            @Override
            public void run() {
                try {
                    String leaderUrl = leaderUrl();
                    if (leaderUrl == null || leaderUrl.trim().isEmpty()) {
                        cb.onCompletion(new ConnectException("Request to leader to " +
                                "reconfigure connector tasks failed " +
                                "because the URL of the leader's REST interface is empty!"), null);
                        return;
                    }
                    String reconfigUrl = RestServer.urlJoin(leaderUrl, "/connectors/" + connName + "/tasks");
                    log.trace("Forwarding task configurations for connector {} to leader", connName);
                    RestClient.httpRequest(reconfigUrl, "POST", null, rawTaskProps, null, config, sessionKey, requestSignatureAlgorithm);
                    cb.onCompletion(null, null);
                } catch (ConnectException e) {
                    log.error("Request to leader to reconfigure connector tasks failed", e);
                    cb.onCompletion(e, null);
                }
            }
        });
    }
}
{code}
KafkaConfigBackingStore task checks for configuration updates,such as topic whitelist update.If KafkaConfigBackingStore task is not running on leader node,an HTTP request will be send to notify the leader of the configuration update.However,dedicated mm2 cluster does not have the HTTP server turned on,so the request will fail to be sent,causing the update operation to be lost.
~~~~

### Comments (12)

1.

~~~~
Not sure if related but I think I'm seeing issues where task configs don't seem to be getting updated consistently when new topics/partitions are found. 

 
~~~~

2.

~~~~
A new topic/partition  is created, but the data is not synchronized.
~~~~

3.

~~~~
Configuration updates only come from the REST API, afaik, which doesn't exist when running with connect-mirror-maker.sh. So I'm not sure what would be triggering the logic in the PR. In order to configuration changes to be picked up at all, the leader must be restarted. Generally you can't know which nodes are leaders of which flows, so generally it makes sense to just restart everything with a new config.

This would change if we added back the REST API to connect-mirror-maker.sh (it is purposefully turned off at present). If we had a REST API, _then_ configuration could change and workers would need to notify their leaders. But that is not the case now.
~~~~

4.

~~~~
[~ryannedolan] I think these configuration updates come from the connector requesting task reconfiguration from the framework: [https://github.com/apache/kafka/blob/62fa8fc9a95d738780d1f73d2d758d7329828feb/connect/mirror/src/main/java/org/apache/kafka/connect/mirror/MirrorSourceConnector.java#L232]

 

In distributed mode, this causes the framework to generate new task configs from the connector and then, if they've changed, try to write them to the config topic. However, only the leader is allowed to write directly to the config topic, so if the connector is hosted on a follower node, then the node has to forward those configs to the leader via the REST API: [https://github.com/apache/kafka/blob/62fa8fc9a95d738780d1f73d2d758d7329828feb/connect/runtime/src/main/java/org/apache/kafka/connect/runtime/distributed/DistributedHerder.java#L1316-L1340]

 

The endpoint for receiving these task configs was the subject of KIP-507, which sought to close a security loophole that it presented at the time. You can see the code for that internal endpoint here: [https://github.com/apache/kafka/blob/62fa8fc9a95d738780d1f73d2d758d7329828feb/connect/runtime/src/main/java/org/apache/kafka/connect/runtime/rest/resources/ConnectorsResource.java#L268-L278]

 

We might consider enabling a bare-bones REST API for MM2 that only supports this internal endpoint? As long as the {{SESSIONED}} protocol introduced in KIP-507 is used by the cluster, this wouldn't present any obvious security risks since requests would have to be signed with a session key that's distributed via the config topic and presumably only readable by workers in the cluster or trusted principals that have access to that topic.
~~~~

5.

~~~~
[~ChrisEgerton] [~ryannedolan] hi. 
In case of dedicated mm2 clusters, If the configBackingStore task is hosted on a follower node，Can the following node write directly into the config topic?
~~~~

6.

~~~~
[~qq619618919] we could but it wouldn't be simple. We'd have to take care to ensure that writes from zombie workers would be ignored, which is done right now by only allowing the leader to write to the config topic.

I think it'd be easier to bring up the task configs endpoint for MM2 than to re-architect the Connect framework, especially given the compatibility and migration concerns that would have to be addressed in order to allow non-leader workers to write to the config topic. But either approach would work.
~~~~

7.

~~~~
[~ChrisEgerton] mm2 has realized data backup. How does kafkaproduce realize automatic failover transparently?
How can the same kafkaproduce object automatically switch between two clusters?
~~~~

8.

~~~~
[~qq619618919] I'm afraid I don't know too much about MirrorMaker 2 itself; I'm more familiar with the Connect framework that it's built on top of.

[~ryannedolan] may know more?
~~~~

9.

~~~~
[~qq619618919] I also faced the same issue with our multiple node cross DC mirror maker. I've tested the changes that you've made and they are working. Can you confirm if you went ahead with these or you found another workaround ?
~~~~

10.

~~~~
[~vaibhavjaimini] That's how My prd environment works,I also do dynamic whitelist based on ZooKeeper
~~~~

11.

~~~~
This KIP aims to fix the issue by adding the REST API to MM2, and also improving the config provider reference handling in the MM2 configs: [https://cwiki.apache.org/confluence/display/KAFKA/KIP-710%3A+Full+support+for+distributed+mode+in+dedicated+MirrorMaker+2.0+clusters]
~~~~

12.

~~~~
[~durban]  [~vaibhavjaimini] any workaround available for this issue ?  i met this in production env too, and got stuck for a few days. 

thanks.
~~~~

---

## KAFKA-10046: Deprecated PartitionGrouper config is ignored

https://issues.apache.org/jira/browse/KAFKA-10046

JIRA metadata: affects 2.6.0; fixed in 3.0.0

- `KAFKA-10046@2.6.0`: config 2.6.0, metadata answer **affected** (listed_affected)
- `KAFKA-10046@3.0.0`: config 3.0.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 3.0

### Description

~~~~
It looks like at some point, we accidentally broke the chain that lets the user-provided PartitionGrouper config actually get to the Consumer-managed StreamsPartitionAssignor. The effect is that any configured value would just be ignored.

Investigation is needed to determine when this regression took place and whether we should fix it or just remove the config.

See the discussion in [https://github.com/apache/kafka/pull/8716/] . The TaskAssignorIntegrationTest in that PR can be used to verify this regression.
~~~~

### Comments (2)

1.

~~~~
We're removing this config in 3.0 so I guess we can go ahead and close this once https://issues.apache.org/jira/browse/KAFKA-7785 and/or https://issues.apache.org/jira/browse/KAFKA-12527 are merged
~~~~

2.

~~~~
[~ableegoldman] the two issues you mention above have been resolved. Thus, marking the issue here as resolved too and I assume it's completed for AK 3.0
~~~~

---

## KAFKA-10180: TLSv1.3 system tests should not run under Java 8

https://issues.apache.org/jira/browse/KAFKA-10180

JIRA metadata: affects 2.6.0; fixed in 2.7.0

- `KAFKA-10180@2.6.0`: config 2.6.0, metadata answer **affected** (listed_affected)
- `KAFKA-10180@2.8.0`: config 2.8.0, metadata answer **not_affected** (later_line)

Known Kafka versions mentioned in text: 1.0

### Description

~~~~
18 system tests relates to TLSv1.3 are running and failing under Java 8.  These system tests should not run except when Java 11 or later is in use.

http://testing.confluent.io/confluent-kafka-system-test-results/?prefix=2020-06-16--001.1592310680--confluentinc--master--d07ee594d/

(e.g. http://testing.confluent.io/confluent-kafka-system-test-results/?prefix=2020-06-16--001.1592310680--confluentinc--master--d07ee594d/Benchmark/test_end_to_end_latency/interbroker_security_protocol=PLAINTEXT.tls_version=TLSv1.3.security_protocol=SSL.compression_type=snappy/)

~~~~

### Comments (3)

1.

~~~~
[~nizhikov] Can you please look into this? It looks related to the changes to enable TLSv1.3 in system tests.
~~~~

2.

~~~~
{noformat}
====================================================================================================
SESSION REPORT (ALL TESTS)
ducktape version: 0.7.8
session_id:       2020-06-23--020
run time:         87 minutes 37.040 seconds
tests run:        62
passed:           62
failed:           0
ignored:          0
====================================================================================================
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.topic=topic-replication-factor-three.num_producers=3.acks=1
status:     PASS
run time:   1 minute 46.188 seconds
{"records_per_sec": 371040.75211400003, "mb_per_sec": 35.39}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_consumer_throughput.interbroker_security_protocol=PLAINTEXT.tls_version=TLSv1.2.security_protocol=SSL.compression_type=none
status:     PASS
run time:   3 minutes 2.029 seconds
{"records_per_sec": 0.0, "mb_per_sec": 0.0}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_consumer_throughput.interbroker_security_protocol=PLAINTEXT.tls_version=TLSv1.2.security_protocol=SSL.compression_type=snappy
status:     PASS
run time:   1 minute 19.078 seconds
{"records_per_sec": 2283105.0228, "mb_per_sec": 217.7339}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_consumer_throughput.interbroker_security_protocol=PLAINTEXT.tls_version=TLSv1.3.security_protocol=SSL.compression_type=none
status:     PASS
run time:   3 minutes 9.450 seconds
{"records_per_sec": 160402.9322, "mb_per_sec": 15.2972}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_consumer_throughput.interbroker_security_protocol=PLAINTEXT.tls_version=TLSv1.3.security_protocol=SSL.compression_type=snappy
status:     PASS
run time:   1 minute 20.393 seconds
{"records_per_sec": 2320185.6148, "mb_per_sec": 221.2701}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_consumer_throughput.security_protocol=PLAINTEXT.compression_type=none
status:     PASS
run time:   2 minutes 41.115 seconds
{"records_per_sec": 0.0, "mb_per_sec": 0.0}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_consumer_throughput.security_protocol=PLAINTEXT.compression_type=snappy
status:     PASS
run time:   1 minute 16.667 seconds
{"records_per_sec": 2328288.7078, "mb_per_sec": 222.0429}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_end_to_end_latency.security_protocol=SASL_PLAINTEXT.compression_type=none
status:     PASS
run time:   1 minute 1.228 seconds
{"latency_99th_ms": 9.0, "latency_50th_ms": 1.0, "latency_999th_ms": 21.0}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_end_to_end_latency.security_protocol=SASL_PLAINTEXT.compression_type=snappy
status:     PASS
run time:   1 minute 1.096 seconds
{"latency_99th_ms": 9.0, "latency_50th_ms": 1.0, "latency_999th_ms": 27.0}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_end_to_end_latency.security_protocol=SASL_SSL.compression_type=none
status:     PASS
run time:   1 minute 9.127 seconds
{"latency_99th_ms": 9.0, "latency_50th_ms": 1.0, "latency_999th_ms": 28.0}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_end_to_end_latency.security_protocol=SASL_SSL.compression_type=snappy
status:     PASS
run time:   1 minute 11.056 seconds
{"latency_99th_ms": 9.0, "latency_50th_ms": 1.0, "latency_999th_ms": 31.0}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_and_consumer.interbroker_security_protocol=PLAINTEXT.tls_version=TLSv1.2.security_protocol=SSL.compression_type=none
status:     PASS
run time:   2 minutes 23.215 seconds
{"consumer": {"records_per_sec": 264718.3397, "mb_per_sec": 25.2455}, "producer": {"records_per_sec": 267122.555829, "mb_per_sec": 25.47}}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_and_consumer.interbroker_security_protocol=PLAINTEXT.tls_version=TLSv1.2.security_protocol=SSL.compression_type=snappy
status:     PASS
run time:   1 minute 15.770 seconds
{"consumer": {"records_per_sec": 648592.5542, "mb_per_sec": 61.8546}, "producer": {"records_per_sec": 630437.523641, "mb_per_sec": 60.12}}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_and_consumer.interbroker_security_protocol=PLAINTEXT.tls_version=TLSv1.3.security_protocol=SSL.compression_type=none
status:     PASS
run time:   3 minutes 11.870 seconds
{"consumer": {"records_per_sec": 197180.3214, "mb_per_sec": 18.8046}, "producer": {"records_per_sec": 231229.911901, "mb_per_sec": 22.05}}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_and_consumer.interbroker_security_protocol=PLAINTEXT.tls_version=TLSv1.3.security_protocol=SSL.compression_type=snappy
status:     PASS
run time:   1 minute 16.796 seconds
{"consumer": {"records_per_sec": 683060.1093, "mb_per_sec": 65.1417}, "producer": {"records_per_sec": 650068.257167, "mb_per_sec": 62.0}}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_and_consumer.security_protocol=PLAINTEXT.compression_type=none
status:     PASS
run time:   2 minutes 27.676 seconds
{"consumer": {"records_per_sec": 317359.5684, "mb_per_sec": 30.2658}, "producer": {"records_per_sec": 310337.336685, "mb_per_sec": 29.6}}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_and_consumer.security_protocol=PLAINTEXT.compression_type=snappy
status:     PASS
run time:   1 minute 14.612 seconds
{"consumer": {"records_per_sec": 621967.9065, "mb_per_sec": 59.3155}, "producer": {"records_per_sec": 618238.021638, "mb_per_sec": 58.96}}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_end_to_end_latency.interbroker_security_protocol=PLAINTEXT.tls_version=TLSv1.2.security_protocol=SSL.compression_type=none
status:     PASS
run time:   1 minute 14.825 seconds
{"latency_99th_ms": 6.0, "latency_50th_ms": 1.0, "latency_999th_ms": 19.0}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_end_to_end_latency.interbroker_security_protocol=PLAINTEXT.tls_version=TLSv1.2.security_protocol=SSL.compression_type=snappy
status:     PASS
run time:   1 minute 13.338 seconds
{"latency_99th_ms": 7.0, "latency_50th_ms": 1.0, "latency_999th_ms": 16.0}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_end_to_end_latency.interbroker_security_protocol=PLAINTEXT.tls_version=TLSv1.3.security_protocol=SSL.compression_type=none
status:     PASS
run time:   1 minute 11.572 seconds
{"latency_99th_ms": 6.0, "latency_50th_ms": 1.0, "latency_999th_ms": 16.0}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_end_to_end_latency.interbroker_security_protocol=PLAINTEXT.tls_version=TLSv1.3.security_protocol=SSL.compression_type=snappy
status:     PASS
run time:   1 minute 12.718 seconds
{"latency_99th_ms": 7.0, "latency_50th_ms": 1.0, "latency_999th_ms": 14.0}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_end_to_end_latency.security_protocol=PLAINTEXT.compression_type=none
status:     PASS
run time:   1 minute 5.121 seconds
{"latency_99th_ms": 6.0, "latency_50th_ms": 1.0, "latency_999th_ms": 18.0}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_end_to_end_latency.security_protocol=PLAINTEXT.compression_type=snappy
status:     PASS
run time:   1 minute 6.154 seconds
{"latency_99th_ms": 6.0, "latency_50th_ms": 1.0, "latency_999th_ms": 17.0}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_long_term_producer_throughput.interbroker_security_protocol=PLAINTEXT.tls_version=TLSv1.2.security_protocol=SSL.compression_type=none
status:     PASS
run time:   2 minutes 45.360 seconds
{"0": {"records_per_sec": 241534.2254, "mb_per_sec": 23.03}}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_long_term_producer_throughput.interbroker_security_protocol=PLAINTEXT.tls_version=TLSv1.2.security_protocol=SSL.compression_type=snappy
status:     PASS
run time:   1 minute 14.977 seconds
{"0": {"records_per_sec": 837310.558486, "mb_per_sec": 79.85}}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_long_term_producer_throughput.interbroker_security_protocol=PLAINTEXT.tls_version=TLSv1.3.security_protocol=SSL.compression_type=none
status:     PASS
run time:   2 minutes 44.524 seconds
{"0": {"records_per_sec": 289922.300823, "mb_per_sec": 27.65}}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_long_term_producer_throughput.interbroker_security_protocol=PLAINTEXT.tls_version=TLSv1.3.security_protocol=SSL.compression_type=snappy
status:     PASS
run time:   1 minute 13.278 seconds
{"0": {"records_per_sec": 771426.367353, "mb_per_sec": 73.57}}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_long_term_producer_throughput.security_protocol=PLAINTEXT.compression_type=none
status:     PASS
run time:   2 minutes 16.288 seconds
{"0": {"records_per_sec": 399968.00256, "mb_per_sec": 38.14}}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_long_term_producer_throughput.security_protocol=PLAINTEXT.compression_type=snappy
status:     PASS
run time:   1 minute 7.659 seconds
{"0": {"records_per_sec": 762718.328121, "mb_per_sec": 72.74}}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.tls_version=TLSv1.2.message_size=10.topic=topic-replication-factor-three.security_protocol=SSL.acks=1.compression_type=none
status:     PASS
run time:   1 minute 29.595 seconds
{"records_per_sec": 1010067.128236, "mb_per_sec": 9.63}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.tls_version=TLSv1.2.message_size=10.topic=topic-replication-factor-three.security_protocol=SSL.acks=1.compression_type=snappy
status:     PASS
run time:   1 minute 18.901 seconds
{"records_per_sec": 984506.124844, "mb_per_sec": 9.39}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.tls_version=TLSv1.2.message_size=100.topic=topic-replication-factor-three.security_protocol=SSL.acks=1.compression_type=none
status:     PASS
run time:   1 minute 15.225 seconds
{"records_per_sec": 195225.745455, "mb_per_sec": 18.62}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.tls_version=TLSv1.2.message_size=100.topic=topic-replication-factor-three.security_protocol=SSL.acks=1.compression_type=snappy
status:     PASS
run time:   58.411 seconds
{"records_per_sec": 472098.839254, "mb_per_sec": 45.02}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.tls_version=TLSv1.2.message_size=1000.topic=topic-replication-factor-three.security_protocol=SSL.acks=1.compression_type=none
status:     PASS
run time:   1 minute 14.473 seconds
{"records_per_sec": 23085.139319, "mb_per_sec": 22.02}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.tls_version=TLSv1.2.message_size=1000.topic=topic-replication-factor-three.security_protocol=SSL.acks=1.compression_type=snappy
status:     PASS
run time:   1 minute 1.329 seconds
{"records_per_sec": 38194.934548, "mb_per_sec": 36.43}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.tls_version=TLSv1.2.message_size=10000.topic=topic-replication-factor-three.security_protocol=SSL.acks=1.compression_type=none
status:     PASS
run time:   1 minute 12.420 seconds
{"records_per_sec": 2477.113326, "mb_per_sec": 23.62}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.tls_version=TLSv1.2.message_size=10000.topic=topic-replication-factor-three.security_protocol=SSL.acks=1.compression_type=snappy
status:     PASS
run time:   1 minute 13.590 seconds
{"records_per_sec": 2360.773967, "mb_per_sec": 22.51}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.tls_version=TLSv1.2.message_size=100000.topic=topic-replication-factor-three.security_protocol=SSL.acks=1.compression_type=none
status:     PASS
run time:   1 minute 12.806 seconds
{"records_per_sec": 455.069515, "mb_per_sec": 43.4}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.tls_version=TLSv1.2.message_size=100000.topic=topic-replication-factor-three.security_protocol=SSL.acks=1.compression_type=snappy
status:     PASS
run time:   1 minute 10.757 seconds
{"records_per_sec": 448.229793, "mb_per_sec": 42.75}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.tls_version=TLSv1.3.message_size=10.topic=topic-replication-factor-three.security_protocol=SSL.acks=1.compression_type=none
status:     PASS
run time:   1 minute 26.116 seconds
{"records_per_sec": 857730.828221, "mb_per_sec": 8.18}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.tls_version=TLSv1.3.message_size=10.topic=topic-replication-factor-three.security_protocol=SSL.acks=1.compression_type=snappy
status:     PASS
run time:   1 minute 12.146 seconds
{"records_per_sec": 958424.164524, "mb_per_sec": 9.14}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.tls_version=TLSv1.3.message_size=100.topic=topic-replication-factor-three.security_protocol=SSL.acks=1.compression_type=none
status:     PASS
run time:   1 minute 16.114 seconds
{"records_per_sec": 187795.858402, "mb_per_sec": 17.91}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.tls_version=TLSv1.3.message_size=100.topic=topic-replication-factor-three.security_protocol=SSL.acks=1.compression_type=snappy
status:     PASS
run time:   1 minute 4.061 seconds
{"records_per_sec": 374073.857302, "mb_per_sec": 35.67}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.tls_version=TLSv1.3.message_size=1000.topic=topic-replication-factor-three.security_protocol=SSL.acks=1.compression_type=none
status:     PASS
run time:   1 minute 15.083 seconds
{"records_per_sec": 21895.106036, "mb_per_sec": 20.88}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.tls_version=TLSv1.3.message_size=1000.topic=topic-replication-factor-three.security_protocol=SSL.acks=1.compression_type=snappy
status:     PASS
run time:   1 minute 0.812 seconds
{"records_per_sec": 33058.374384, "mb_per_sec": 31.53}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.tls_version=TLSv1.3.message_size=10000.topic=topic-replication-factor-three.security_protocol=SSL.acks=1.compression_type=none
status:     PASS
run time:   1 minute 13.124 seconds
{"records_per_sec": 2416.021602, "mb_per_sec": 23.04}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.tls_version=TLSv1.3.message_size=10000.topic=topic-replication-factor-three.security_protocol=SSL.acks=1.compression_type=snappy
status:     PASS
run time:   1 minute 15.004 seconds
{"records_per_sec": 2333.275382, "mb_per_sec": 22.25}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.tls_version=TLSv1.3.message_size=100000.topic=topic-replication-factor-three.security_protocol=SSL.acks=1.compression_type=none
status:     PASS
run time:   1 minute 15.194 seconds
{"records_per_sec": 450.486741, "mb_per_sec": 42.96}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.tls_version=TLSv1.3.message_size=100000.topic=topic-replication-factor-three.security_protocol=SSL.acks=1.compression_type=snappy
status:     PASS
run time:   1 minute 6.961 seconds
{"records_per_sec": 447.03531, "mb_per_sec": 42.63}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.topic=topic-replication-factor-one.acks=1
status:     PASS
run time:   58.297 seconds
{"records_per_sec": 406966.949666, "mb_per_sec": 38.81}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.topic=topic-replication-factor-three.acks=-1
status:     PASS
run time:   1 minute 8.630 seconds
{"records_per_sec": 141415.762301, "mb_per_sec": 13.49}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.topic=topic-replication-factor-three.acks=1
status:     PASS
run time:   1 minute 6.691 seconds
{"records_per_sec": 244343.164027, "mb_per_sec": 23.3}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.topic=topic-replication-factor-three.security_protocol=PLAINTEXT.compression_type=none.acks=1.message_size=10
status:     PASS
run time:   1 minute 20.735 seconds
{"records_per_sec": 1028094.369973, "mb_per_sec": 9.8}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.topic=topic-replication-factor-three.security_protocol=PLAINTEXT.compression_type=none.acks=1.message_size=100
status:     PASS
run time:   1 minute 4.227 seconds
{"records_per_sec": 263326.858937, "mb_per_sec": 25.11}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.topic=topic-replication-factor-three.security_protocol=PLAINTEXT.compression_type=none.acks=1.message_size=1000
status:     PASS
run time:   1 minute 9.448 seconds
{"records_per_sec": 30229.054054, "mb_per_sec": 28.83}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.topic=topic-replication-factor-three.security_protocol=PLAINTEXT.compression_type=none.acks=1.message_size=10000
status:     PASS
run time:   1 minute 9.055 seconds
{"records_per_sec": 3347.717635, "mb_per_sec": 31.93}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.topic=topic-replication-factor-three.security_protocol=PLAINTEXT.compression_type=none.acks=1.message_size=100000
status:     PASS
run time:   1 minute 5.133 seconds
{"records_per_sec": 982.430454, "mb_per_sec": 93.69}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.topic=topic-replication-factor-three.security_protocol=PLAINTEXT.compression_type=snappy.acks=1.message_size=10
status:     PASS
run time:   1 minute 8.243 seconds
{"records_per_sec": 957398.673229, "mb_per_sec": 9.13}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.topic=topic-replication-factor-three.security_protocol=PLAINTEXT.compression_type=snappy.acks=1.message_size=100
status:     PASS
run time:   53.956 seconds
{"records_per_sec": 528416.141732, "mb_per_sec": 50.39}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.topic=topic-replication-factor-three.security_protocol=PLAINTEXT.compression_type=snappy.acks=1.message_size=1000
status:     PASS
run time:   53.178 seconds
{"records_per_sec": 59440.655447, "mb_per_sec": 56.69}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.topic=topic-replication-factor-three.security_protocol=PLAINTEXT.compression_type=snappy.acks=1.message_size=10000
status:     PASS
run time:   1 minute 8.507 seconds
{"records_per_sec": 3325.322101, "mb_per_sec": 31.71}
----------------------------------------------------------------------------------------------------
test_id:    kafkatest.benchmarks.core.benchmark_test.Benchmark.test_producer_throughput.topic=topic-replication-factor-three.security_protocol=PLAINTEXT.compression_type=snappy.acks=1.message_size=100000
status:     PASS
run time:   1 minute 3.395 seconds
{"records_per_sec": 907.369844, "mb_per_sec": 86.53}
----------------------------------------------------------------------------------------------------
{noformat}
~~~~

3.

~~~~
merged the PR to trunk
~~~~

---

## KAFKA-10254: 100% cpu usage by kafkaConsumer poll , when broker can't be connect 

https://issues.apache.org/jira/browse/KAFKA-10254

JIRA metadata: affects 2.5.0; fixed in 2.5.1

- `KAFKA-10254@2.5.0`: config 2.5.0, metadata answer **affected** (listed_affected)
- `KAFKA-10254@2.5.1`: config 2.5.1, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 2.3.1, 2.5.0

### Description

~~~~
steps

1、start kafka broker 

2、start kafka consumer and subscribe some topic with some kafkaConsumer instance and  call  kafkaConsumer.*poll(Duration.ofMillis(pollTimeout))*   and set auto.commit.enabled=false

3、iptables to disable kafka broker  ip  in client vm or shutdown kafka brokers

4、cpu go to 100%

 

*why?*

 

 

left Vserison :2.3.1

right Version:2.5.0

 

for 2.3.1 kafkaConsumer when kafka  brokers go  down,updateAssignmentMetadataIfNeeded will block x ms and return empty records ,

!image-2020-07-09-19-24-20-604.png|width=926,height=164!

 

for 2.5.0

private Map<TopicPartition, List<ConsumerRecord<K, V>>> pollForFetches(Timer timer) {
 *long pollTimeout = coordinator == null ? timer.remainingMs() :*
 *Math.min(coordinator.timeToNextPoll(timer.currentTimeMs()), timer.remainingMs());*

i check the source of kafka client ,poll timeout will be change to 0 ms ,when heartbeat timeout ，so  it will call poll without any block ,this will cause cpu go to 100%

 

 

 
~~~~

### Comments (3)

1.

~~~~
[~xiaotong.wang], see KAFKA-10134
~~~~

2.

~~~~
Hey [~xiaotong.wang] , thanks for the report! It looks like a duplicate of KAFKA-10134; is that right?
~~~~

3.

~~~~
Changing resolution to "fixed", since the linked duplicate is fixed.
~~~~

---

## KAFKA-10565: Console producer displays interactive prompt even when input is not interactive

https://issues.apache.org/jira/browse/KAFKA-10565

JIRA metadata: affects 2.6.0; fixed in 2.8.0

- `KAFKA-10565@2.6.0`: config 2.6.0, metadata answer **affected** (listed_affected)
- `KAFKA-10565@2.5.1`: config 2.5.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
The prompt introduced in KAFKA-2955 may be indeed helpful when a user enters messages manually but when the messages are read from a file, it's not helpful and may be really annoying.
h5. Steps to reproduce
 # Create a file with a decent number of messages (e.g. 80,000 in my case)
 # Start console producer and forward the file contents to its STDIN:

{noformat}
$ kafka-console-producer --broker-list b1,b2,b3 --topic test < messages.txt
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ... >>>>>>>>>>>>>>
{noformat}
For each message the producer reads from the file, there's one > displayed polluting the output.
h5. Expected behavior:
 # If the producer can detect that the input stream is a TTY, it should not display the prompt.
 # Ideally, there should be a configuration parameter to disable this explicitly.

 
~~~~

---

## KAFKA-10716: Streams processId is unstable across restarts resulting in task mass migration

https://issues.apache.org/jira/browse/KAFKA-10716

JIRA metadata: affects 2.6.0; fixed in 2.6.2, 2.7.1, 2.8.0

- `KAFKA-10716@2.6.0`: config 2.6.0, metadata answer **affected** (listed_affected)
- `KAFKA-10716@2.5.1`: config 2.5.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
The new high availability feature of KIP-441 relies on deterministic assignment to produce an eventually-stable assignment. The HighAvailabilityTaskAssignor assigns tasks based on the unique processId assigned to each client, so if the same set of Kafka Streams applications participate in a rebalance it should generate the same task assignment every time.

Unfortunately the processIds aren't stable across restarts. We generate a random UUID in the KafkaStreams constructor, so each time the process starts up it would be assigned a completely different processId. Unless this new processId happens to be in exactly the same order as the previous one, a single bounce or crash/restart can result in a large scale shuffling of tasks based on a completely different eventual assignment.

Ultimately we should fix this via KAFKA-10121, but that's a nontrivial undertaking and this bug merits some immediate relief if we don't intend to tackle the larger problem in the upcoming releases 
~~~~

### Comments (1)

1.

~~~~
There are a few possible ways forward here:

1) generate the processId from the client.id config, if specified. This requires users to set this config and ensure that it's unique to the instance
2) generate the processId from the group.instance.id, if specified. This would only work for static membership users
3) write/load the processId from the checkpoint file in task directories
4) write/load the processId from a single file in the top-level application directory

Both 1 & 2 would be simple for us to implement, but somewhat obnoxious to require of a user just for basic functionality of their app. That said, if a user already has specified either the client.id or group.instance.id, I don't see any reason _not_ to generate the processId from that. This might be a good stop-gap measure, but not a good permanent solution. However if we plan to implement KAFKA-10121 right away then maybe it's best not to mess around with options 3 or 4

Options 3 and 4 would be a bit trickier. Option 3 in particular seems to open up a lot of nasty possibilities, like the processId differing from one task directory to another, or even between threads in the same app. But Option 4 seems pretty clean: we load the processId file within the KafkaStreams constructor, and if it's not found we generate a random UUID like we do now. This would all happen before any threads are created so no need to worry about them synchronizing at all
~~~~

---

## KAFKA-12152: Idempotent Producer does not reset the sequence number of partitions without in-flight batches

https://issues.apache.org/jira/browse/KAFKA-12152

JIRA metadata: affects 2.5.0, 2.6.0, 2.7.0; fixed in 2.7.1, 2.8.0

- `KAFKA-12152@2.5.0`: config 2.5.0, metadata answer **affected** (listed_affected)
- `KAFKA-12152@2.7.2`: config 2.7.2, metadata answer **not_affected** (later_patch)

Known Kafka versions mentioned in text: none

### Description

~~~~
When a `OutOfOrderSequenceException` error is received by an idempotent producer for a partition, the producer bumps its epoch, adjusts the sequence number and the epoch of the in-flight batches of the partitions affected by the `OutOfOrderSequenceException` error. This happens in `TransactionManager#bumpIdempotentProducerEpoch`.

The remaining partitions are treated separately. When the last in-flight batch of a given partition is completed, the sequence number is reset. This happens in `TransactionManager#handleCompletedBatch`.

However, when a given partition does not have in-flight batches when the producer epoch is bumped, its sequence number is not reset. It results in having subsequent producer request to use the new producer epoch with the old sequence number and to be rejected by the broker.
~~~~

---

## KAFKA-12462: Threads in PENDING_SHUTDOWN entering a rebalance can cause an illegal state exception 

https://issues.apache.org/jira/browse/KAFKA-12462

JIRA metadata: affects 2.6.0, 2.7.0, 2.8.0; fixed in 2.7.1, 2.8.0

- `KAFKA-12462@2.7.0`: config 2.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-12462@2.5.1`: config 2.5.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.7, 2.6.2, 2.7.1, 2.6

### Description

~~~~
A thread was removed, sending it to the PENDING_SHUTDOWN state, but went through a rebalance before completing the shutdown.
{code:java}
// [2021-03-07 04:33:39,385] DEBUG [i-07430efc31ad166b7-StreamThread-6] stream-thread [i-07430efc31ad166b7-StreamThread-6] Ignoring request to transit from PENDING_SHUTDOWN to PARTITIONS_REVOKED: only DEAD state is a valid next state (org.apache.kafka.streams.processor.internals.StreamThread)
{code}
Inside StreamsRebalanceListener#onPartitionsRevoked, we have
{code:java}
// 
if (streamThread.setState(State.PARTITIONS_REVOKED) != null && !partitions.isEmpty())
    taskManager.handleRevocation(partitions);
{code}
Since PENDING_SHUTDOWN → PARTITIONS_REVOKED is a disallowed transition, we never invoke TaskManager#handleRevocation. Currently handleRevocation is responsible for preparing any active tasks for close, including committing offsets and writing the checkpoint as well as suspending the task. We can’t close the task in handleRevocation since we still support EAGER rebalancing, which invokes handleRevocation at the beginning of a rebalance on all tasks.

The tasks that are actually revoked will be closed during TaskManager#handleAssignment . The IllegalStateException is specifically because we don’t suspend the task before attempting to close it, and the direct transition from RUNNING → CLOSED is forbidden.
~~~~

### Comments (4)

1.

~~~~
Thanks Walker! This actually seems like a long-lurking bug that was just surfaced by the removeStreamThread() feature, not caused by it. Before we could remove threads this was only possible when shutting down the client, which we don’t test as frequently as we now do removeStreamThread(). It’s also hard to notice that a bug has caused thread(s) to die when the threads were supposed to shut down anyways. But now we might only be removing one thread, and thanks to the new exception handler we’ll shut down the whole application upon hitting this so the thread won’t just quietly die.

We should consider backporting the fix to 2.7, even though the bug isn't going to be as frequent or as bad in earlier versions. I wouldn't cut a new RC for 2.6.2 over this, but we might as well backport to get the fix in 2.7.1 whenever that comes out
~~~~

2.

~~~~
If we were shutting down the whole client the thread would become dead either way. In 2.7 I think the only impact it would have is that the handler would get called after the close call when it shouldn’t. But otherwise it might not have an effect. I suppose there is no harm to back-porting though.

I defiantly don't think it is worth cutting a new RC for anything that does not have removeThread in it

 
~~~~

3.

~~~~
The only real downside in 2.7 is that we won't properly clean up the task, ie we'll skip committing the offsets and writing the checkpoint. So we'd lose any work we did since the last commit – for EOS this would be a perf hit since we'd probably need to restore the state stores from scratch after starting back up, whereas for ALOS we could get some overcounting. Not the end of the world, but worth fixing if we can
~~~~

4.

~~~~
This also affects 2.6
~~~~

---

## KAFKA-12476: Worker can block for longer than scheduled rebalance delay and/or session key TTL

https://issues.apache.org/jira/browse/KAFKA-12476

JIRA metadata: affects 2.3.2, 2.4.2, 2.5.2, 2.6.2, 2.7.1, 2.8.0, 3.0.0; fixed in 3.4.0

- `KAFKA-12476@2.8.0`: config 2.8.0, metadata answer **affected** (listed_affected)
- `KAFKA-12476@2.3.1`: config 2.3.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
Near the end of a distributed worker's herder tick loop, it calculates how long it should poll for rebalance activity before beginning a new loop. See [here|https://github.com/apache/kafka/blob/8da65936d7fc53d24c665c0d01893d25a430933b/connect/runtime/src/main/java/org/apache/kafka/connect/runtime/distributed/DistributedHerder.java#L399-L409] and [here|https://github.com/apache/kafka/blob/8da65936d7fc53d24c665c0d01893d25a430933b/connect/runtime/src/main/java/org/apache/kafka/connect/runtime/distributed/DistributedHerder.java#L459].

In between then and when it begins polling for rebalancing activity, some connector and task (re-)starts take place. While this normally completes in at most a minute or two, an overloaded cluster or one in the midst of garbage collection may take longer. See [here|https://github.com/apache/kafka/blob/8da65936d7fc53d24c665c0d01893d25a430933b/connect/runtime/src/main/java/org/apache/kafka/connect/runtime/distributed/DistributedHerder.java#L411-L452].

The worker should calculate the time to poll for rebalance activity as closely as possible to when it actually begins that polling.
~~~~

---

## KAFKA-12682: Kraft MetadataPartitionsBuilder _localChanged and _localRemoved out of order 

https://issues.apache.org/jira/browse/KAFKA-12682

JIRA metadata: affects 2.8.0; fixed in 3.0.0

- `KAFKA-12682@2.8.0`: config 2.8.0, metadata answer **affected** (listed_affected)
- `KAFKA-12682@2.7.2`: config 2.7.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 2.8, 3.0

### Description

~~~~
In version 2.8, MetadataPartitionsBuilder has the field _localChanged and _localRemoved which record the change and delete partition, but we always process _localChanged partitions, and then _localRemoved in the kafka.server.RaftReplicaManager#handleMetadataRecords, not respect the original order, for example, 
1. migrate the partition p1 from b0 to b1;
2. change the leader of p1 
3.migrate p1 from b1 to b0
and the _localRemoved will delete the p1 at last.

and I think MetadataPartition should include topic uuid, and the topic name is optional
for example,
create topic t1, delete topic t1, create topic t1, change leader of p1
and then compact the records 
delete topic t1, change t1, p1

but currently, implementation will be
1. process change t1, p1
2. process delete topic t1

but the MetadataPartition doesn't include topic uuid, it only includes topic name, when to process, it can't find the origin topic uuid, and find the latest the topic id, but it's not right. and delete topic t1 should do before create t1 or change p1.

~~~~

### Comments (1)

1.

~~~~
This was fixed in 3.0 when we rewrote the ReplicaManager logic for KRaft.
~~~~

---

## KAFKA-12684: The valid partition list is incorrectly replaced by the successfully elected partition list

https://issues.apache.org/jira/browse/KAFKA-12684

JIRA metadata: affects 2.6.0, 2.7.0; fixed in 3.0.0

- `KAFKA-12684@2.6.0`: config 2.6.0, metadata answer **affected** (listed_affected)
- `KAFKA-12684@3.1.0`: config 3.1.0, metadata answer **not_affected** (later_line)

Known Kafka versions mentioned in text: none

### Description

~~~~
When using the kafka-election-tool for preferred replica election, if there are partitions in the elected list that are in the preferred replica, the list of partitions already in the preferred replica will be replaced by the successfully elected partition list.

 
~~~~

---

## KAFKA-12686: Race condition in AlterIsr response handling

https://issues.apache.org/jira/browse/KAFKA-12686

JIRA metadata: affects 2.7.0, 2.8.0; fixed in 3.0.0

- `KAFKA-12686@2.7.0`: config 2.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-12686@3.0.0`: config 3.0.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: none

### Description

~~~~
In Partition.scala, there is a race condition between the handling of an AlterIsrResponse and a LeaderAndIsrRequest. This is a pretty rare scenario and would involve the AlterIsrResponse being delayed for some time, but it is possible. This was observed in a test environment when lots of ISR and leadership changes were happening due to broker restarts.

When the leader handles the LeaderAndIsr, it calls Partition#makeLeader which overrides the {{isrState}} variable and clears the pending ISR items via {{AlterIsrManager#clearPending(TopicPartition)}}. 

The bug is that AlterIsrManager does not check its inflight state before clearing pending items. The way AlterIsrManager is designed, it retains inflight items in the pending items collection until the response is processed (to allow for retries). The result is that an inflight item is inadvertently removed from this collection.

Since the inflight item is cleared from the collection, AlterIsrManager allows for new AlterIsrItem-s to be enqueued for this partition even though it has an inflight AlterIsrItem. By allowing an update to be enqueued, Partition will transition its {{isrState}} to one of the inflight states (PendingIsrExpand, PendingIsrShrink, etc). Once the inflight partition's response is handled, it will fail to update the {{isrState}} due to detecting changes since the request was sent (which is by design). However, after the response callback is run, AlterIsrManager will clear the partitions that it saw in the response from the unsent items collection. This includes the newly added (and unsent) update.

The result is that Partition has a "inflight" isrState but AlterIsrManager does not have an unsent item for this partition. This prevents any further ISR updates on the partition until the next leader election (when {{isrState}} is reset).

If this bug is encountered, the workaround is to force a leader election which will reset the partition's state.
~~~~

---

## KAFKA-12841: NPE from the provided metadata in client callback in case of ApiException

https://issues.apache.org/jira/browse/KAFKA-12841

JIRA metadata: affects 2.6.0; fixed in 3.2.0

- `KAFKA-12841@2.6.0`: config 2.6.0, metadata answer **affected** (listed_affected)
- `KAFKA-12841@3.2.1`: config 3.2.1, metadata answer **not_affected** (later_patch)

Known Kafka versions mentioned in text: 3.2

### Description

~~~~
1.
org.apache.kafka.clients.producer.Callback interface has method onCompletion(...)
Which says as part of the documentation :

*The metadata for the record that was sent (i.e. the partition and offset). *An empty metadata with -1 value for all fields* except for topicPartition will be returned if an error occurred.


We got an NPE from doSend(...) method in org.apache.kafka.clients.producer.KafkaProducer 
Which can occur in case ApiException was thrown ...
In case of ApiException it uses the regular callback instead of InterceptorCallback which also may cover the NPE.

2. More over RecordMetadata has method partition() which return int but can also throw NPE because TopicPartition might be null.

Stack trace attached.

 
~~~~

### Comments (5)

1.

~~~~
I'd like to take a stab at this bug. Can someone kindly assign it to me? TIA.
~~~~

2.

~~~~
There are some conditions inside the {{KafkaProducer}}'s {{doSend}} method that will result in an {{ApiException}} being thrown before the {{TopicPartition}} ({{tp}}) is created. As a result, {{tp}} is null and case #2 listed in the initial bug report occurs.

Would it be OK to create a new, "dummy" {{TopicPartition}} in this case? We could use the topic from the {{ProducerRecord}}. But perhaps the partition from the {{ProducerRecord}}, if non-null, can be used? Or should we just set the partition to `-1`?
~~~~

3.

~~~~
[~kirktrue] This is what i did in this [[PR|https://github.com/apache/kafka/pull/10728]].
 Might be the right approach is to create the tp with default values
~~~~

4.

~~~~
I have submitted a [pull request|https://github.com/apache/kafka/pull/10951] for review.
~~~~

5.

~~~~
merged [https://github.com/apache/kafka/pull/11689] and a followup fix [https://github.com/apache/kafka/pull/12064] to trunk and 3.2 branch.
~~~~

---

## KAFKA-13456: Tighten KRaft config checks/constraints

https://issues.apache.org/jira/browse/KAFKA-13456

JIRA metadata: affects 2.8.0, 3.0.0; fixed in 3.1.0

- `KAFKA-13456@2.8.0`: config 2.8.0, metadata answer **affected** (listed_affected)
- `KAFKA-13456@3.1.0`: config 3.1.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: none

### Description

~~~~
We need to tighten the configuration constraints/checks related to KRaft configs because the current checks do not eliminate illegal configuration combinations.  Specifically, we need to add the following constraints:

* controller.listener.names is required to be empty for the non-KRaft (i.e. ZooKeeper) case. A ZooKeeper-based cluster that sets this config will fail to restart until this config is removed.  This generally should not be occurring -- nobody should be setting KRaft-specific configs in a ZooKeeper-based cluster -- but we currently do not prevent it from happening.
* There must be no advertised listeners when running just a KRaft controller (i.e. when process.roles=controller). This means neither listeners nor advertised.listeners (if the latter is explicitly defined) can contain a listener that does not also appear in controller.listener.names.
* When running a KRaft broker (i.e. when process.roles=broker or process.roles=broker,controller), advertised listeners must not include any listeners appearing in controller.listener.names.
* When running a KRaft controller (i.e. when process.roles=controller or process.roles=broker,controller) controller.listener.names must be non-empty and every one must appear in listeners
* When running just a KRaft broker (i.e. when process.roles=broker) controller.listener.names must be non-empty and none of them can appear in listeners. This is currently checked indirectly, but the indirect checks do not catch all cases.  We will check directly.
* When running just a KRaft broker we log a warning if more than one entry appears in controller.listener.names because only the first entry is used.

In addition to the above additional constraints, we should also map the CONTROLLER listener name to the PLAINTEXT security protocol by default when using KRaft -- this would be a very helpful convenience.

~~~~

---

## KAFKA-13457: SocketChannel in Acceptor#accept is not closed upon IOException

https://issues.apache.org/jira/browse/KAFKA-13457

JIRA metadata: affects 2.8.0; fixed in 3.2.0

- `KAFKA-13457@2.8.0`: config 2.8.0, metadata answer **affected** (listed_affected)
- `KAFKA-13457@3.2.0`: config 3.2.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: none

### Description

~~~~
When the kafka.network.Acceptor in SocketServer.scala accepts a new connection in the `accept` function, it handles the `TooManyConnectionsException` and `ConnectionThrottledException`. However, the socketChannel operations (line 720 or 721 or 722) within the try block may potentially throw an IOException as well, which is not handled.

 
{code:java}
//core/src/main/scala/kafka/network/SocketServer.scala
// Acceptor class
  private def accept(key: SelectionKey): Option[SocketChannel] = {
    val serverSocketChannel = key.channel().asInstanceOf[ServerSocketChannel]
    val socketChannel = serverSocketChannel.accept()     // line 717
    try {
      connectionQuotas.inc(endPoint.listenerName, socketChannel.socket.getInetAddress, blockedPercentMeter)
      socketChannel.configureBlocking(false)             // line 720
      socketChannel.socket().setTcpNoDelay(true)         // line 721
      socketChannel.socket().setKeepAlive(true)          // line 722
      if (sendBufferSize != Selectable.USE_DEFAULT_BUFFER_SIZE)
        socketChannel.socket().setSendBufferSize(sendBufferSize)
      Some(socketChannel)
    } catch {
      case e: TooManyConnectionsException =>       
        info(s"Rejected connection from ${e.ip}, address already has the configured maximum of ${e.count} connections.")
        close(endPoint.listenerName, socketChannel)
        None
      case e: ConnectionThrottledException => 
        val ip = socketChannel.socket.getInetAddress
        debug(s"Delaying closing of connection from $ip for ${e.throttleTimeMs} ms")
        val endThrottleTimeMs = e.startThrottleTimeMs + e.throttleTimeMs
        throttledSockets += DelayedCloseSocket(socketChannel, endThrottleTimeMs)
        None
    }
  }
{code}
This thrown IOException is caught in the caller `acceptNewConnections` in line 706, which only prints an error message. The socketChannel that throws this IOException is not closed.

 
{code:java}
//core/src/main/scala/kafka/network/SocketServer.scala
  private def acceptNewConnections(): Unit = {
    val ready = nioSelector.select(500)
    if (ready > 0) {
      val keys = nioSelector.selectedKeys()
      val iter = keys.iterator()
      while (iter.hasNext && isRunning) {
        try {
          val key = iter.next
          iter.remove()          if (key.isAcceptable) {
            accept(key).foreach { socketChannel => 
                ...
              } while (!assignNewConnection(socketChannel, processor, retriesLeft == 0))
            }
          } else
            throw new IllegalStateException("Unrecognized key state for acceptor thread.")
        } catch {
          case e: Throwable => error("Error while accepting connection", e)   // line 706
        }
      }
    }
  }
{code}
We found during testing this would cause our Kafka clients to experience errors (InvalidReplicationFactorException) for 40+ seconds when creating new topics. After 40 seconds, the clients would be able to create new topics successfully.

We check that after adding the socketChannel.close() upon IOException, the symptoms will disappear, so the clients do not need to wait for 40s to be working again.

 

 
~~~~

### Comments (3)

1.

~~~~
[~dajac] I see you merged https://github.com/apache/kafka/pull/11504 a while back. Can we now close this issue? or is there more work to do?
~~~~

2.

~~~~
[~mimaison] Done.
~~~~

3.

~~~~
Thanks!
~~~~

---

## KAFKA-13488: Producer fails to recover if topic gets deleted (and gets auto-created)

https://issues.apache.org/jira/browse/KAFKA-13488

JIRA metadata: affects 2.2.2, 2.3.1, 2.4.1, 2.5.1, 2.6.3, 2.7.2, 2.8.1; fixed in 2.8.2, 3.0.1, 3.1.0

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

## KAFKA-13692: stream thread blocked-time-ns-total metric does not include producer metadata wait time

https://issues.apache.org/jira/browse/KAFKA-13692

JIRA metadata: affects 3.1.0; fixed in 3.3.0

- `KAFKA-13692@3.1.0`: config 3.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-13692@3.3.0`: config 3.3.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: none

### Description

~~~~
The stream thread blocked-time-ns-total metric does not include producer metadata wait time (time spent in `KafkaProducer.waitOnMetadata`). This can contribute significantly to actual total blocked time in some cases. For example, if a user deletes the streams sink topic, producers will wait until the max block timeout. This time does not get included in total blocked time when it should.
~~~~

---

## KAFKA-13778: Fetch from follower should never run the preferred read replica selection

https://issues.apache.org/jira/browse/KAFKA-13778

JIRA metadata: affects 2.6.0; fixed in 3.3.0

- `KAFKA-13778@2.6.0`: config 2.6.0, metadata answer **affected** (listed_affected)
- `KAFKA-13778@3.4.0`: config 3.4.0, metadata answer **not_affected** (later_line)

Known Kafka versions mentioned in text: none

### Description

~~~~
The design purpose of the code is that only the leader broker can determine the preferred read-replica.

 
{code:java}
readFromLocalLog()
....
// If we are the leader, determine the preferred read-replica
val preferredReadReplica = clientMetadata.flatMap(
  metadata => findPreferredReadReplica(partition, metadata, replicaId, fetchInfo.fetchOffset, fetchTimeMs)) {code}
 

But in fact, since the broker does not judge whether it is the leader or not, the follower will also execute the preferred read-replica selection.
{code:java}
partition.leaderReplicaIdOpt.flatMap { leaderReplicaId =>
  // Don't look up preferred for follower fetches via normal replication and
  if (Request.isValidBrokerId(replicaId))
    None
  else { {code}
~~~~

---

## KAFKA-13791: Fix FetchResponse#`fetchData` and `forgottenTopics`: Assignment of lazy-initialized members should be the last step with double-checked locking

https://issues.apache.org/jira/browse/KAFKA-13791

JIRA metadata: affects 3.0.1; fixed in 3.3.0

- `KAFKA-13791@3.0.1`: config 3.0.1, metadata answer **affected** (listed_affected)
- `KAFKA-13791@3.3.1`: config 3.3.1, metadata answer **not_affected** (later_patch)

Known Kafka versions mentioned in text: none

### Description

~~~~
Double-checked locking can be used for lazy initialization of volatile fields, but only if field assignment is the last step in the synchronized block. Otherwise, you run the risk of threads accessing a half-initialized object.

The problem is consistent with [KAFKA-13777|https://issues.apache.org/jira/projects/KAFKA/issues/KAFKA-13777]
~~~~

---

## KAFKA-14149: Broken DynamicBrokerReconfigurationTest in 3.2 branch

https://issues.apache.org/jira/browse/KAFKA-14149

JIRA metadata: affects 3.2.2; fixed in 3.2.3

- `KAFKA-14149@3.2.2`: config 3.2.2, metadata answer **affected** (listed_affected)
- `KAFKA-14149@3.2.1`: config 3.2.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.2

### Description

~~~~
The backport of [https://github.com/apache/kafka/pull/12455] does not work in 3.2. The following tests are failing:

DynamicBrokerReconfigurationTest.testConfigDescribeUsingAdminClient(String).quorum=kraft
DynamicBrokerReconfigurationTest.testConsecutiveConfigChange(String).quorum=kraft
DynamicBrokerReconfigurationTest.testKeyStoreAlter(String).quorum=kraft
DynamicBrokerReconfigurationTest.testLogCleanerConfig(String).quorum=kraft
DynamicBrokerReconfigurationTest.testTrustStoreAlter(String).quorum=kraft
DynamicBrokerReconfigurationTest.testUpdatesUsingConfigProvider(String).quorum=kraft

Caused by :
java.util.concurrent.ExecutionException: org.apache.kafka.common.errors.InvalidRequestException: Invalid value org.apache.kafka.common.config.ConfigException: Dynamic reconfiguration of listeners is not yet supported when using a Raft-based metadata quorum for configuration Invalid dynamic configuration
~~~~

---

## KAFKA-14211: Streams log message has partition and offset transposed

https://issues.apache.org/jira/browse/KAFKA-14211

JIRA metadata: affects 3.1.1; fixed in 3.2.0

- `KAFKA-14211@3.1.1`: config 3.1.1, metadata answer **affected** (listed_affected)
- `KAFKA-14211@3.2.0`: config 3.2.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: none

### Description

~~~~
The log warning message for out-of-order KTable update has partition and offset the wrong way around.

For example:
{noformat}
[...-StreamThread-1] WARN org.apache.kafka.streams.kstream.internals.KTableSource - Detected out-of-order KTable update for KTABLE-FK-JOIN-OUTPUT-STATE-STORE-0000000274, old timestamp=[1649245600022] new timestamp=[1642429126882]. topic=[...-KTABLE-FK-JOIN-SUBSCRIPTION-RESPONSE-0000000269-topic] partition=[2813] offset=[0].{noformat}
~~~~

### Comments (2)

1.

~~~~
[~mallwoodrbi] Thank you for filing a ticket.
This is fixed via https://github.com/apache/kafka/pull/11905/files
~~~~

2.

~~~~
Resolving this since it's apparently fixed by PR (see Bruno's comment) – [~cadonna]  can you fill out the "Fix Version" for this?
~~~~

---

## KAFKA-14260: InMemoryKeyValueStore iterator still throws ConcurrentModificationException

https://issues.apache.org/jira/browse/KAFKA-14260

JIRA metadata: affects 2.3.1, 3.2.3; fixed in 3.4.0

- `KAFKA-14260@2.3.1`: config 2.3.1, metadata answer **affected** (listed_affected)
- `KAFKA-14260@3.4.1`: config 3.4.1, metadata answer **not_affected** (later_patch)

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

## KAFKA-14273: Kafka doesn't start with KRaft on Windows

https://issues.apache.org/jira/browse/KAFKA-14273

JIRA metadata: affects 3.3.1; fixed in 3.6.0

- `KAFKA-14273@3.3.1`: config 3.3.1, metadata answer **affected** (listed_affected)
- `KAFKA-14273@3.7.0`: config 3.7.0, metadata answer **not_affected** (later_line)

Known Kafka versions mentioned in text: 3.3, 3.4.0, 3.5.0, 3.6.0

### Description

~~~~
{{Basic setup doesn't work on Windows 10.}}

*{{Steps}}*
 * {{Initialize cluster with -}}

{code:sh}
    bin\windows\kafka-storage.bat random-uuid
    bin\windows\kafka-storage.bat format -t %cluster_id% -c .\config\kraft\server.properties{code}
 
 * Start Kafka with -

{code:sh}
   bin\windows\kafka-server-start.bat .\config\kraft\server.properties{code}
 

*Stacktrace*

Kafka fails to start with following exception -
{code:java}
D:\LocationGuru\Servers\Kafka-3.3>bin\windows\kafka-server-start.bat .\config\kraft\server.properties
[2022-10-03 23:14:20,089] INFO Registered kafka:type=kafka.Log4jController MBean (kafka.utils.Log4jControllerRegistration$)
[2022-10-03 23:14:20,375] INFO Setting -D jdk.tls.rejectClientInitiatedRenegotiation=true to disable client-initiated TLS renegotiation (org.apache.zookeeper.common.X509Util)
[2022-10-03 23:14:20,594] INFO [LogLoader partition=__cluster_metadata-0, dir=D:\LocationGuru\Servers\Kafka-3.3\tmp\kraft-combined-logs] Loading producer state till offset 0 with message format version 2 (kafka.log.UnifiedLog$)
[2022-10-03 23:14:20,594] INFO [LogLoader partition=__cluster_metadata-0, dir=D:\LocationGuru\Servers\Kafka-3.3\tmp\kraft-combined-logs] Reloading from producer snapshot and rebuilding producer state from offset 0 (kafka.log.UnifiedLog$)
[2022-10-03 23:14:20,594] INFO [LogLoader partition=__cluster_metadata-0, dir=D:\LocationGuru\Servers\Kafka-3.3\tmp\kraft-combined-logs] Producer state recovery took 0ms for snapshot load and 0ms for segment recovery from offset 0 (kafka.log.UnifiedLog$)
[2022-10-03 23:14:20,640] INFO Initialized snapshots with IDs SortedSet() from D:\LocationGuru\Servers\Kafka-3.3\tmp\kraft-combined-logs__cluster_metadata-0 (kafka.raft.KafkaMetadataLog$)
[2022-10-03 23:14:20,734] INFO [raft-expiration-reaper]: Starting (kafka.raft.TimingWheelExpirationService$ExpiredOperationReaper)
[2022-10-03 23:14:20,900] ERROR Exiting Kafka due to fatal exception (kafka.Kafka$)
java.io.UncheckedIOException: Error while writing the Quorum status from the file D:\LocationGuru\Servers\Kafka-3.3\tmp\kraft-combined-logs__cluster_metadata-0\quorum-state
        at org.apache.kafka.raft.FileBasedStateStore.writeElectionStateToFile(FileBasedStateStore.java:155)
        at org.apache.kafka.raft.FileBasedStateStore.writeElectionState(FileBasedStateStore.java:128)
        at org.apache.kafka.raft.QuorumState.transitionTo(QuorumState.java:477)
        at org.apache.kafka.raft.QuorumState.initialize(QuorumState.java:212)
        at org.apache.kafka.raft.KafkaRaftClient.initialize(KafkaRaftClient.java:369)
        at kafka.raft.KafkaRaftManager.buildRaftClient(RaftManager.scala:200)
        at kafka.raft.KafkaRaftManager.<init>(RaftManager.scala:127)
        at kafka.server.KafkaRaftServer.<init>(KafkaRaftServer.scala:83)
        at kafka.Kafka$.buildServer(Kafka.scala:79)
        at kafka.Kafka$.main(Kafka.scala:87)
        at kafka.Kafka.main(Kafka.scala)
Caused by: java.nio.file.FileSystemException: D:\LocationGuru\Servers\Kafka-3.3\tmp\kraft-combined-logs_cluster_metadata-0\quorum-state.tmp -> D:\LocationGuru\Servers\Kafka-3.3\tmp\kraft-combined-logs_cluster_metadata-0\quorum-state: The process cannot access the file because it is being used by another process
        at java.base/sun.nio.fs.WindowsException.translateToIOException(WindowsException.java:92)
        at java.base/sun.nio.fs.WindowsException.rethrowAsIOException(WindowsException.java:103)
        at java.base/sun.nio.fs.WindowsFileCopy.move(WindowsFileCopy.java:403)
        at java.base/sun.nio.fs.WindowsFileSystemProvider.move(WindowsFileSystemProvider.java:293)
        at java.base/java.nio.file.Files.move(Files.java:1430)
        at org.apache.kafka.common.utils.Utils.atomicMoveWithFallback(Utils.java:935)
        at org.apache.kafka.common.utils.Utils.atomicMoveWithFallback(Utils.java:918)
        at org.apache.kafka.raft.FileBasedStateStore.writeElectionStateToFile(FileBasedStateStore.java:152)
        ... 10 more
        Suppressed: java.nio.file.FileSystemException: D:\LocationGuru\Servers\Kafka-3.3\tmp\kraft-combined-logs_cluster_metadata-0\quorum-state.tmp -> D:\LocationGuru\Servers\Kafka-3.3\tmp\kraft-combined-logs_cluster_metadata-0\quorum-state: The process cannot access the file because it is being used by another process
                at java.base/sun.nio.fs.WindowsException.translateToIOException(WindowsException.java:92)
                at java.base/sun.nio.fs.WindowsException.rethrowAsIOException(WindowsException.java:103)
                at java.base/sun.nio.fs.WindowsFileCopy.move(WindowsFileCopy.java:317)
                at java.base/sun.nio.fs.WindowsFileSystemProvider.move(WindowsFileSystemProvider.java:293)
                at java.base/java.nio.file.Files.move(Files.java:1430)
                at org.apache.kafka.common.utils.Utils.atomicMoveWithFallback(Utils.java:932)
                ... 12 more{code}
 

*Environment*

Windows 10 (64 bit)
~~~~

### Comments (7)

1.

~~~~
I have the same problem. I have tried on two different machines with a clean installation and the same error always occurs when starting the server. If I use ZK it works fine.

 
{code:java}
.\bin\windows\kafka-server-start.bat .\config\kraft\server.properties
[2022-10-05 15:13:00,285] INFO Registered kafka:type=kafka.Log4jController MBean (kafka.utils.Log4jControllerRegistration$)
[2022-10-05 15:13:00,696] INFO Setting -D jdk.tls.rejectClientInitiatedRenegotiation=true to disable client-initiated TLS renegotiation (org.apache.zookeeper.common.X509Util)
[2022-10-05 15:13:00,994] INFO [LogLoader partition=__cluster_metadata-0, dir=D:\Kafka\kraft-combined-logs] Loading producer state till offset 0 with message format version 2 (kafka.log.UnifiedLog$)
[2022-10-05 15:13:00,996] INFO [LogLoader partition=__cluster_metadata-0, dir=D:\Kafka\kraft-combined-logs] Reloading from producer snapshot and rebuilding producer state from offset 0 (kafka.log.UnifiedLog$)
[2022-10-05 15:13:00,998] INFO [LogLoader partition=__cluster_metadata-0, dir=D:\Kafka\kraft-combined-logs] Producer state recovery took 2ms for snapshot load and 0ms for segment recovery from offset 0 (kafka.log.UnifiedLog$)
[2022-10-05 15:13:01,079] INFO Initialized snapshots with IDs SortedSet() from D:\Kafka\kraft-combined-logs\__cluster_metadata-0 (kafka.raft.KafkaMetadataLog$)
[2022-10-05 15:13:01,156] INFO [raft-expiration-reaper]: Starting (kafka.raft.TimingWheelExpirationService$ExpiredOperationReaper)
[2022-10-05 15:13:01,358] ERROR Exiting Kafka due to fatal exception (kafka.Kafka$)
java.io.UncheckedIOException: Error while writing the Quorum status from the file D:\Kafka\kraft-combined-logs\__cluster_metadata-0\quorum-state
        at org.apache.kafka.raft.FileBasedStateStore.writeElectionStateToFile(FileBasedStateStore.java:155)
        at org.apache.kafka.raft.FileBasedStateStore.writeElectionState(FileBasedStateStore.java:128)
        at org.apache.kafka.raft.QuorumState.transitionTo(QuorumState.java:477)
        at org.apache.kafka.raft.QuorumState.initialize(QuorumState.java:212)
        at org.apache.kafka.raft.KafkaRaftClient.initialize(KafkaRaftClient.java:369)
        at kafka.raft.KafkaRaftManager.buildRaftClient(RaftManager.scala:200)
        at kafka.raft.KafkaRaftManager.<init>(RaftManager.scala:127)
        at kafka.server.KafkaRaftServer.<init>(KafkaRaftServer.scala:83)
        at kafka.Kafka$.buildServer(Kafka.scala:79)
        at kafka.Kafka$.main(Kafka.scala:87)
        at kafka.Kafka.main(Kafka.scala)
Caused by: java.nio.file.FileSystemException: D:\Kafka\kraft-combined-logs\__cluster_metadata-0\quorum-state.tmp -> D:\Kafka\kraft-combined-logs\__cluster_metadata-0\quorum-state: The process cannot access the file because it is being used by another process.        at java.base/sun.nio.fs.WindowsException.translateToIOException(WindowsException.java:92)
        at java.base/sun.nio.fs.WindowsException.rethrowAsIOException(WindowsException.java:103)
        at java.base/sun.nio.fs.WindowsFileCopy.move(WindowsFileCopy.java:395)
        at java.base/sun.nio.fs.WindowsFileSystemProvider.move(WindowsFileSystemProvider.java:292)
        at java.base/java.nio.file.Files.move(Files.java:1422)
        at org.apache.kafka.common.utils.Utils.atomicMoveWithFallback(Utils.java:935)
        at org.apache.kafka.common.utils.Utils.atomicMoveWithFallback(Utils.java:918)
        at org.apache.kafka.raft.FileBasedStateStore.writeElectionStateToFile(FileBasedStateStore.java:152)
        ... 10 more
        Suppressed: java.nio.file.FileSystemException: D:\Kafka\kraft-combined-logs\__cluster_metadata-0\quorum-state.tmp -> D:\Kafka\kraft-combined-logs\__cluster_metadata-0\quorum-state: The process cannot access the file because it is being used by another process.                at java.base/sun.nio.fs.WindowsException.translateToIOException(WindowsException.java:92)
                at java.base/sun.nio.fs.WindowsException.rethrowAsIOException(WindowsException.java:103)
                at java.base/sun.nio.fs.WindowsFileCopy.move(WindowsFileCopy.java:309)
                at java.base/sun.nio.fs.WindowsFileSystemProvider.move(WindowsFileSystemProvider.java:292)
                at java.base/java.nio.file.Files.move(Files.java:1422)
                at org.apache.kafka.common.utils.Utils.atomicMoveWithFallback(Utils.java:932)
                ... 12 more {code}
~~~~

2.

~~~~
I wonder, why this still isn't fixed in 3.4.0 - is KRaft still in preview mode and not ready for production? This bug prevents testing KRaft under Windows, when you aren't able to setup Kafka in Docker or WSL.
~~~~

3.

~~~~
Still not fixed for 3.5.0.
~~~~

4.

~~~~
[~mumrah] [~cmccabe] [~ijuma] Is this a blocker for 3.6.0? 
~~~~

5.

~~~~
[~satish.duggana] I think it is a blocker. I sent you an email in the release thread. I'll submit a PR shortly.
~~~~

6.

~~~~
https://github.com/apache/kafka/pull/14354

~~~~

7.

~~~~
Thanks [~jsancio] for the quick fix.
~~~~

---

## KAFKA-14311: Connect Worker clean shutdown does not cleanly stop connectors/tasks

https://issues.apache.org/jira/browse/KAFKA-14311

JIRA metadata: affects 3.3.1; fixed in 3.5.0

- `KAFKA-14311@3.3.1`: config 3.3.1, metadata answer **affected** (listed_affected)
- `KAFKA-14311@3.5.1`: config 3.5.1, metadata answer **not_affected** (later_patch)

Known Kafka versions mentioned in text: none

### Description

~~~~
When the DistributedHerder::stop() method called, it triggers asynchronous shutdown of the background herder thread, and continues with synchronous shutdown of some other resources, including the stopAndStartExecutor.

This executor is responsible for cleanly stopping connectors and tasks, which it  the DistributedHerder::halt() method. There is a race condition between the halt() method asynchronously submitting these connector/task stop jobs and the stop() method terminating the executor. If the executor is terminated first, this exception appears:
{noformat}
[2022-10-17 16:29:23,396] ERROR [Worker clientId=connect-2, groupId=connect-integration-test-connect-cluster-1] Uncaught exception in herder work thread, exiting:  (org.apache.kafka.connect.runtime.distributed.DistributedHerder:366)
java.util.concurrent.RejectedExecutionException: Task java.util.concurrent.FutureTask@62878e25[Not completed, task = org.apache.kafka.connect.runtime.distributed.DistributedHerder$$Lambda$2285/0x00000008015046a8@58deade3] rejected from java.util.concurrent.ThreadPoolExecutor@10351ac3[Terminated, pool size = 0, active threads = 0, queued tasks = 0, completed tasks = 1]
    at java.base/java.util.concurrent.ThreadPoolExecutor$AbortPolicy.rejectedExecution(ThreadPoolExecutor.java:2065)
    at java.base/java.util.concurrent.ThreadPoolExecutor.reject(ThreadPoolExecutor.java:833)
    at java.base/java.util.concurrent.ThreadPoolExecutor.execute(ThreadPoolExecutor.java:1365)
    at java.base/java.util.concurrent.AbstractExecutorService.invokeAll(AbstractExecutorService.java:247)
    at org.apache.kafka.connect.runtime.distributed.DistributedHerder.startAndStop(DistributedHerder.java:1667)
    at org.apache.kafka.connect.runtime.distributed.DistributedHerder.halt(DistributedHerder.java:765)
    at org.apache.kafka.connect.runtime.distributed.DistributedHerder.run(DistributedHerder.java:361)
    at java.base/java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:539)
    at java.base/java.util.concurrent.FutureTask.run(FutureTask.java:264)
    at java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1136)
    at java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:635)
    at java.base/java.lang.Thread.run(Thread.java:833){noformat}
~~~~

---

## KAFKA-14314: MirrorSourceConnector throwing NPE during `isCycle` check

https://issues.apache.org/jira/browse/KAFKA-14314

JIRA metadata: affects 3.3.1; fixed in 3.4.0

- `KAFKA-14314@3.3.1`: config 3.3.1, metadata answer **affected** (listed_affected)
- `KAFKA-14314@3.4.0`: config 3.4.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: none

### Description

~~~~
We are using MirrorMaker to replicate topics across clusters in AWS. As the process is starting up, we are getting a NullPointerException when MirrorSourceConnector is calling `isCycle`.

Retrieving the `upstreamTopic` on [this line of code|https://github.com/apache/kafka/blob/cc582897bfb237572131369a598f7869220b43dc/connect/mirror/src/main/java/org/apache/kafka/connect/mirror/MirrorSourceConnector.java#L497] is returning null, which causes the NPE on the next line. 
~~~~

### Comments (6)

1.

~~~~
Which replication policy are you using?
~~~~

2.

~~~~
We're using a custom replication policy. Here are the contents of the mm2-msc.json file. Is this what you're asking for? I'm new to this so I'm unsure exactly what all constitutes the policy.

 
{code:java}
{
  "name": "mm2-msc",
  "connector.class": "org.apache.kafka.connect.mirror.MirrorSourceConnector",
  "replication.policy.class": "com.amazonaws.kafka.samples.CustomMM2ReplicationPolicy",
  "clusters": "prim, sec",
  "source.cluster.alias": "prim",
  "source.cluster.bootstrap.servers": "PRIMARY_BOOTSTRAP_URL",
  "source.cluster.security.protocol": "SSL",
  "source.cluster.ssl.truststore.location": "/tmp/kafka.client.truststore.jks",
  "source.cluster.ssl.truststore.password": "changeit",
  "target.cluster.alias": "sec",
  "target.cluster.bootstrap.servers": "SECONDARY_BOOTSTRAP_URL",
  "target.cluster.security.protocol": "SSL",
  "target.cluster.ssl.truststore.location": "/tmp/kafka.client.truststore.jks",
  "target.cluster.ssl.truststore.password": "changeit",
  "topics": ".*",
  "tasks.max": "4",
  "key.converter": " org.apache.kafka.connect.converters.ByteArrayConverter",
  "value.converter": "org.apache.kafka.connect.converters.ByteArrayConverter",
  "replication.factor": "3",
  "offset-syncs.topic.replication.factor": "1",
  "sync.topic.acls.interval.seconds": "10",
  "sync.topic.configs.interval.seconds": "10",
  "refresh.topics.interval.seconds": "10",
  "refresh.groups.interval.seconds": "10",
  "consumer.group.id": "mm2-msc",
  "producer.enable.idempotence": "true"
}{code}
 
~~~~

3.

~~~~
Thanks for the details.

The ReplicationPolicy [javadoc|https://kafka.apache.org/33/javadoc/org/apache/kafka/connect/mirror/ReplicationPolicy.html#upstreamTopic-java.lang.String-] states that upstreamTopic can return null to indicate a topic is not remote. So this is a bug in MirrorSourceConnector.isCycle(), null should be handled correctly.

Are you interested in submitting a pull request to fix this small issue?

 
~~~~

4.

~~~~
Thanks, Mickael. Sure I can do that. I thought it was a bug because it seems that `null` is a legitimate value here. We might have something misconfigured but even in that case it shouldn't blow up so I'll submit a PR a bit later today.
~~~~

5.

~~~~
Great, I'll assign this ticket to you then. Thanks!
~~~~

6.

~~~~
I'm not sure exactly how your project manages these tickets but I submitted [PR 12769|https://github.com/apache/kafka/pull/12769] this morning and mentioned this ticket number in the comment. It's still building.
~~~~

---

## KAFKA-14463: ConnectorClientConfigOverridePolicy is not closed at worker shutdown

https://issues.apache.org/jira/browse/KAFKA-14463

JIRA metadata: affects 2.3.0; fixed in 3.5.0

- `KAFKA-14463@2.3.0`: config 2.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-14463@3.6.0`: config 3.6.0, metadata answer **not_affected** (later_line)

Known Kafka versions mentioned in text: none

### Description

~~~~
The ConnectorClientConfigOverridePolicy is marked AutoCloseable, but is never closed by the worker on shutdown.

This is currently not a critical issue, as all known implementations of the policy have a no-op close. But a possible implementation which does instantiate background resources that must be closed in close() would leak those resources in a test environment.
~~~~

### Comments (1)

1.

~~~~
Hello, [~gharris1727] , [~ChrisEgerton]. Can, you, please, take a look at my changes?

 

https://github.com/apache/kafka/pull/13144
~~~~

---

## KAFKA-14664: Raft idle ratio is inaccurate

https://issues.apache.org/jira/browse/KAFKA-14664

JIRA metadata: affects 3.3.0, 3.3.1, 3.3.2, 3.4.0; fixed in 3.5.0

- `KAFKA-14664@3.3.0`: config 3.3.0, metadata answer **affected** (listed_affected)
- `KAFKA-14664@3.5.0`: config 3.5.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 1.0

### Description

~~~~
The `poll-idle-ratio-avg` metric is intended to track how idle the raft IO thread is. When completely idle, it should measure 1. When saturated, it should measure 0. The problem with the current measurements is that they are treated equally with respect to time. For example, say we poll twice with the following durations:

Poll 1: 2s

Poll 2: 0s

Assume that the busy time is negligible, so 2s passes overall.

In the first measurement, 2s is spent waiting, so we compute and record a ratio of 1.0. In the second measurement, no time passes, and we record 0.0. The idle ratio is then computed as the average of these two values (1.0 + 0.0 / 2 = 0.5), which suggests that the process was busy for 1s, which overestimates the true busy time.

Instead, we should sum up the time waiting over the full interval. 2s passes total here and 2s is idle, so we should compute 1.0.
~~~~

---

## KAFKA-14713: Kafka Streams global table startup takes too long

https://issues.apache.org/jira/browse/KAFKA-14713

JIRA metadata: affects 3.0.2; fixed in 3.2.0

- `KAFKA-14713@3.0.2`: config 3.0.2, metadata answer **affected** (listed_affected)
- `KAFKA-14713@3.2.1`: config 3.2.1, metadata answer **not_affected** (later_patch)

Known Kafka versions mentioned in text: 3.0.2, 3.4.0, 3.4, 3.0, 3.2.0

### Description

~~~~
*Some context first*

We have a spring based kafka streams application. This application is listening to two topics. Let's call them apartment and visitor. The apartments are stored in a global table, while the visitors are in the stream we are processing, and at one point we are joining the visitor stream together with the apartment table. In our test environment, both topics contain 10 partitions.

*Issue*

At first deployment, everything goes fine, the global table is built and all entries in the stream are processed.

After everything is finished, we shut down the application, restart it and send out a new set of visitors. The application seemingly does not respond.

After some more debugging it turned out that it simply takes 5 minutes to start up, because the global table takes 30 seconds (default value for the global request timeout) to accept that there are no messages in the apartment topics, for each and every partition. If we send out the list of apartments as new messages, the application starts up immediately.

To make matters worse, we have clients with 96 partitions, where the startup time would be 48 minutes. Not having messages in the topics between application shutdown and restart is a valid use case, so this is quite a big problem.

*Possible workarounds*

We could reduce the request timeout, but since this value is not specific for the global table initialization, but a global request timeout for a lot of things, we do not know what else it will affect, so we are not very keen on doing that. Even then, it would mean a 1.5 minute delay for this particular client (more if we will have other use cases in the future where we will need to use more global tables), which is far too much, considering that the application would be able to otherwise start in about 20 seconds.

*Potential solutions we see*
 # Introduce a specific global table initialization timeout in GlobalStateManagerImpl. Then we would be able to safely modify that value without fear of making some other part of kafka unstable.
 # Parallelize the initialization of the global table partitions in GlobalStateManagerImpl: knowing that the delay at startup is constant instead of linear with the number of partitions would be a huge help.
 # As long as we receive a response, accept the empty map in the KafkaConsumer, and continue instead of going into a busy-waiting loop.
~~~~

### Comments (7)

1.

~~~~
Sounds like a duplicate to https://issues.apache.org/jira/browse/KAFKA-14442 ? Can we close this ticket?
~~~~

2.

~~~~
Hi [~mjsax] looks similar, but not exactly. They see this issue with exactly_once_beta processing guarantee, while we have it with the default at_least_once. For us the important part is that is issue is fixed (or at least a safe workaround is provided) as soon as possible, because right now I am between a rock and a hard place because of it.
~~~~

3.

~~~~
What version are you using? – Also, can you point me to the code where it actually waits/hangs (as you did already looked into it, it would be quicker this way). – I am not sure yet, if both issues are actually the same though or not. (Maybe the "eos" config on the other ticket is a red herring.) But I guess we can dig into it a little bit.
~~~~

4.

~~~~
Entry point would be the [GlobalStateManagerImpl|https://github.com/apache/kafka/blob/trunk/streams/src/main/java/org/apache/kafka/streams/processor/internals/GlobalStateManagerImpl.java], where the [pollMsPlusRequestTimeout|https://github.com/apache/kafka/blob/trunk/streams/src/main/java/org/apache/kafka/streams/processor/internals/GlobalStateManagerImpl.java#L115] is defined as POLL_MS_CONFIG (0.1 sec, which is fine), plus [REQUEST_TIMEOUT_MS_CONFIG|https://github.com/apache/kafka/blob/trunk/streams/src/main/java/org/apache/kafka/streams/processor/internals/GlobalStateManagerImpl.java#L113] (30 sec, which is the part causing the problem). Then in [restoreState|https://github.com/apache/kafka/blob/trunk/streams/src/main/java/org/apache/kafka/streams/processor/internals/GlobalStateManagerImpl.java#L240] we start [polling the globalConsumer|https://github.com/apache/kafka/blob/trunk/streams/src/main/java/org/apache/kafka/streams/processor/internals/GlobalStateManagerImpl.java#L274] with this inflated poll timeout.

After that we jump into the [KafkaConsumer|https://github.com/apache/kafka/blob/3.0.2/clients/src/main/java/org/apache/kafka/clients/consumer/KafkaConsumer.java], and start the [polling|https://github.com/apache/kafka/blob/3.0.2/clients/src/main/java/org/apache/kafka/clients/consumer/KafkaConsumer.java#L1238] for new records, which will give us back an empty map, since there are no new entries coming in, and this loop will get stuck for 30 seconds.

Now the first set of links are pointing to the trunk, while the second set are pointing to the 3.0.2 tag, because the trunk has changed significantly since what I have, and the changes in 3.4.0 might actually solve my problem, so before continuing, let me spend some time trying to verify this (I have to admit previously I only checked the latest version of the GlobalStateManagerImpl, and there there were no significant changes yet) :)

Edit: okay, 3.4.0 does not have this issue anymore, which means that KAFKA-14442 might also be resolved with it. Anyway I'm closing this ticket. Thanks for the help :)
~~~~

5.

~~~~
Thanks for getting back. Glad it's resolved. I am not sure why though. Comparing 3.4 and 3.0 code, it seems they do the same thing.

In the end, if you have valid checkpoint on restart, you should not even hit `poll(pollMsPlusRequestTimeout)` during restore, because it should hold that `offset == highWatermark` and we should not enter the while-loop...

For K14442, we know that `offset == highWatermark - 1` (because we write the "incorrect" watermark into the checkpoint file), and thus `poll()` is executed and hangs because there is no data – the last "record" is just a commit marker.
~~~~

6.

~~~~
The difference (at least for my use case) is on the KafkaConsumer side, where the [pollForFetches|https://github.com/apache/kafka/blob/3.4.0/clients/src/main/java/org/apache/kafka/clients/consumer/KafkaConsumer.java#L1243] returns a Fetch instead of just a Map. The Fetch object is able to differentiate between "no new message" and "could not get data", so it does not wait until the request timeout passes anymore for a new record to arrive, but will return immediately.
~~~~

7.

~~~~
Ah. Thanks. That makes sense. Did not look into the consumer code, only streams. So it's fixed via https://issues.apache.org/jira/browse/KAFKA-12980 in 3.2.0 – updated the ticket accordingly. Thanks for getting back. It bugged my that I did not understand it :) 
~~~~

---

## KAFKA-14809: Connect incorrectly logs that no records were produced by source tasks

https://issues.apache.org/jira/browse/KAFKA-14809

JIRA metadata: affects 3.0.0, 3.0.1, 3.0.2, 3.1.0, 3.1.1, 3.1.2, 3.2.0, 3.2.1, 3.2.2, 3.2.3, 3.3.0, 3.3.1, 3.3.2, 3.4.0; fixed in 3.0.3, 3.1.3, 3.2.4, 3.3.3, 3.4.1, 3.5.0

- `KAFKA-14809@3.2.2`: config 3.2.2, metadata answer **affected** (listed_affected)
- `KAFKA-14809@3.6.0`: config 3.6.0, metadata answer **not_affected** (later_line)

Known Kafka versions mentioned in text: none

### Description

~~~~
There's an *{{if}}* condition when [committing offsets|https://github.com/apache/kafka/blob/trunk/connect/runtime/src/main/java/org/apache/kafka/connect/runtime/WorkerSourceTask.java#L219] that is referencing the wrong variable, so the statement always evaluates to {*}true{*}.

This causes log statements like the following to be spuriously emitted:
{quote}[2023-03-14 16:18:04,675] DEBUG WorkerSourceTask\{id=job-0} Either no records were produced by the task since the last offset commit, or every record has been filtered out by a transformation or dropped due to transformation or conversion errors. (org.apache.kafka.connect.runtime.WorkerSourceTask:220)
{quote}
~~~~

### Comments (3)

1.

~~~~
[~hgeraldino] I wanted a Jira ticket for this so that users could easily find the cause of the problem if they were confused by the incorrect log messages, so I've taken a stab at changing the title and description to describe not just the specific bug in the code, but the user-facing effects that it has. Feel free to alter anything you'd like; I just want this to be discoverable by users who may be searching for, e.g., log messages to understand what's going wrong.
~~~~

2.

~~~~
No that's perfect. Thanks [~ChrisEgerton]!
~~~~

3.

~~~~
This is arguably the root cause of KAFKA-13669, since it's likely that users would not have been so alarmed by these log messages if they were being emitted correctly.

It's probably not worth it to revert the downgrade from {{INFO}} to {{DEBUG}} level at this point, but it's at least worth noting the connection between these two issues.
~~~~

---

## KAFKA-14927: Prevent kafka-configs.sh from setting non-alphanumeric config key names

https://issues.apache.org/jira/browse/KAFKA-14927

JIRA metadata: affects 3.3.2; fixed in 3.7.0

- `KAFKA-14927@3.3.2`: config 3.3.2, metadata answer **affected** (listed_affected)
- `KAFKA-14927@3.8.0`: config 3.8.0, metadata answer **not_affected** (later_line)

Known Kafka versions mentioned in text: none

### Description

~~~~
Using {{kafka-configs}} should validate dynamic configurations before applying. It is possible to send a file with invalid configurations. 

For example a file containing the following:
{code:java}
{
  "routes": {
    "crn:///kafka=*": {
      "management": {
        "allowed": "confluent-audit-log-events_audit",
        "denied": "confluent-audit-log-events-denied"
      },
      "describe": {
        "allowed": "",
        "denied": "confluent-audit-log-events-denied"
      },
      "authentication": {
        "allowed": "confluent-audit-log-events_audit",
        "denied": "confluent-audit-log-events-denied-authn"
      },
      "authorize": {
        "allowed": "confluent-audit-log-events_audit",
        "denied": "confluent-audit-log-events-denied-authz"
      },
      "interbroker": {
        "allowed": "",
        "denied": ""
      }
    },
    "crn:///kafka=*/group=*": {
      "consume": {
        "allowed": "confluent-audit-log-events_audit",
        "denied": "confluent-audit-log-events"
      }
    },
    "crn:///kafka=*/topic=*": {
      "produce": {
        "allowed": "confluent-audit-log-events_audit",
        "denied": "confluent-audit-log-events"
      },
      "consume": {
        "allowed": "confluent-audit-log-events_audit",
        "denied": "confluent-audit-log-events"
      }
    }
  },
  "destinations": {
    "topics": {
      "confluent-audit-log-events": {
        "retention_ms": 7776000000
      },
      "confluent-audit-log-events-denied": {
        "retention_ms": 7776000000
      },
      "confluent-audit-log-events-denied-authn": {
        "retention_ms": 7776000000
      },
      "confluent-audit-log-events-denied-authz": {
        "retention_ms": 7776000000
      },
      "confluent-audit-log-events_audit": {
        "retention_ms": 7776000000
      }
    }
  },
  "default_topics": {
    "allowed": "confluent-audit-log-events_audit",
    "denied": "confluent-audit-log-events"
  },
  "excluded_principals": [
    "User:schemaregistryUser",
    "User:ANONYMOUS",
    "User:appSA",
    "User:admin",
    "User:connectAdmin",
    "User:connectorSubmitter",
    "User:connectorSA",
    "User:schemaregistryUser",
    "User:ksqlDBAdmin",
    "User:ksqlDBUser",
    "User:controlCenterAndKsqlDBServer",
    "User:controlcenterAdmin",
    "User:restAdmin",
    "User:appSA",
    "User:clientListen",
    "User:superUser"
  ]
} {code}
{code:java}
kafka-configs --bootstrap-server $KAFKA_BOOTSTRAP --entity-type brokers --entity-default --alter --add-config-file audit-log.json {code}
Yields the following dynamic configs:
{code:java}
Default configs for brokers in the cluster are:
  "destinations"=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"destinations"=null}
  "confluent-audit-log-events-denied-authn"=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"confluent-audit-log-events-denied-authn"=null}
  "routes"=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"routes"=null}
  "User=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"User=null}
  },=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:},=null}
  "excluded_principals"=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"excluded_principals"=null}
  "confluent-audit-log-events_audit"=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"confluent-audit-log-events_audit"=null}
  "authorize"=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"authorize"=null}
  "default_topics"=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"default_topics"=null}
  "topics"=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"topics"=null}
  ]=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:]=null}
  "interbroker"=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"interbroker"=null}
  "produce"=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"produce"=null}
  "denied"=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"denied"=null}
  "confluent-audit-log-events-denied"=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"confluent-audit-log-events-denied"=null}
  "confluent-audit-log-events"=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"confluent-audit-log-events"=null}
  "crn=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"crn=null}
  "management"=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"management"=null}
  "describe"=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"describe"=null}
  "allowed"=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"allowed"=null}
  "consume"=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"consume"=null}
  "confluent-audit-log-events-denied-authz"=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"confluent-audit-log-events-denied-authz"=null}
  "retention_ms"=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"retention_ms"=null}
  {=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:{=null}
  "authentication"=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:"authentication"=null}
  }=null sensitive=true synonyms={DYNAMIC_DEFAULT_BROKER_CONFIG:}=null} {code}
Attempting to remove the dynamic configs via {{kafka-configs}} will not allow removal of entries with a comma.
{code:java}
kafka-configs --bootstrap-server $KAFKA_BOOTSTRAP --entity-type brokers --alter --entity-default \
--delete-config '"User'  \
--delete-config '"destinations"'  \
--delete-config '"confluent-audit-log-events_audit"'  \
--delete-config '"authorize"'  \
--delete-config '"authentication"'  \
--delete-config '"topics"'  \
--delete-config '"interbroker"'  \
--delete-config '"produce"'  \
--delete-config '"allowed"'  \
--delete-config '"confluent-audit-log-events_audit"' \
--delete-config '"confluent-audit-log-events-denied-authn"'  \
--delete-config '"routes"'  \
--delete-config '"excluded_principals"'  \
--delete-config '"default_topics"'  \
--delete-config '"denied"'  \
--delete-config '"confluent-audit-log-events"'  \
--delete-config '"confluent-audit-log-events"'  \
--delete-config '"confluent-audit-log-events-denied"'  \
--delete-config '"management"'  \
--delete-config '"describe"'  \
--delete-config '"consume"'  \
--delete-config '"confluent-audit-log-events-denied-authz"'  \
--delete-config '"retention_ms"'  \
--delete-config '"crn'  \
--delete-config ']'  \
--delete-config '{'  \
--delete-config '}'  \
--delete-config '},' 

All sensitive broker config entries must be specified for --alter, missing entries: Set(},){code}
ConfigCommand.scala removes the comma, which blocks the config from removal:

[https://github.com/apache/kafka/blob/dd63d88ac3ea7a9a55a6dacf9c5473e939322a55/core/src/main/scala/kafka/admin/ConfigCommand.scala]

Current workaround is to reset all dynamic configurations with {{{}zookeeper-shell{}}}:
{code:java}
get /config/brokers/<default>
{"version":1,"config":{"\"destinations\"":"{","\"User":"superUser\"","\"confluent-audit-log-events_audit\"":"{","\"authorize\"":"{","\"topics\"":"{","\"interbroker\"":"{","\"produce\"":"{","\"allowed\"":"\"confluent-audit-log-events_audit\",","\"retention_ms\"":"7776000000","\"confluent-audit-log-events-denied-authn\"":"{","\"routes\"":"
{","},":"","\"excluded_principals\"":"[","\"default_topics\"":"\{","]":"","\"denied\"":"\"confluent-audit-log-events\"","\"confluent-audit-log-events\"":"{","\"confluent-audit-log-events-denied\"":"{","\"management\"":"{","\"crn":"///kafka=/topic=\": {","\"describe\"":"{","\"consume\"":"{","\"confluent-audit-log-events-denied-authz\"":"{","{":"","\"authentication\"":"{","}
":""}}
set /config/brokers/<default> {"version":1,"config":{}}
{code}
Since workaround relies on ZooKeeper the workaround would not be an option when using KRaft mode.

 
~~~~

### Comments (2)

1.

~~~~
I haven't verified this but I would expect the same behavior on KRaft since the bug here (if we want to call it that) is a mismatch between the validation in ConfigCommand and the lack of validation on the broker.

A good fix would probably be only allowing characters in '([a-z][A-Z][0-9][._-])*' to be config keys. We can always revisit if people want more options for config keys (so far I'm not aware of anyone who would want this).

This is maybe a bit of a grey area, you could argue that it needs a KIP although in some sense it's really formalizing what we've been doing all along...
~~~~

2.

~~~~
Raised the PR to add validation https://github.com/apache/kafka/pull/14514 as suggested by [~cmccabe]
~~~~

---

## KAFKA-14963: Incorrect partition count metrics for kraft controllers

https://issues.apache.org/jira/browse/KAFKA-14963

JIRA metadata: affects 3.4.0; fixed in 3.4.1

- `KAFKA-14963@3.4.0`: config 3.4.0, metadata answer **affected** (listed_affected)
- `KAFKA-14963@3.5.0`: config 3.5.0, metadata answer **not_affected** (later_line)

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

## KAFKA-15218: NPE will be thrown while deleting topic and fetch from follower concurrently

https://issues.apache.org/jira/browse/KAFKA-15218

JIRA metadata: affects 3.5.0; fixed in 3.6.0

- `KAFKA-15218@3.5.0`: config 3.5.0, metadata answer **affected** (listed_affected)
- `KAFKA-15218@3.6.1`: config 3.6.1, metadata answer **not_affected** (later_patch)

Known Kafka versions mentioned in text: 3.5.0

### Description

~~~~
When deleting topics, we'll first clear all the remoteReplicaMap when stopPartitions [here|https://github.com/apache/kafka/blob/2999168cde37142ae3a2377fe939d6b581e692b8/core/src/main/scala/kafka/server/ReplicaManager.scala#L554]. But this time, there might be fetch request coming from follower, and try to check if the replica is eligible to be added into ISR [here|https://github.com/apache/kafka/blob/2999168cde37142ae3a2377fe939d6b581e692b8/core/src/main/scala/kafka/cluster/Partition.scala#L1001]. At this moment, NPE will be thrown. Although it's fine since this topic is already deleted, it'd be better to avoid it happen.

 

 
{code:java}
java.lang.NullPointerException: Cannot invoke "kafka.cluster.Replica.stateSnapshot()" because the return value of "kafka.utils.Pool.get(Object)" is null	at kafka.cluster.Partition.isReplicaIsrEligible(Partition.scala:992) ~[kafka_2.13-3.5.0.jar:?]	at kafka.cluster.Partition.canAddReplicaToIsr(Partition.scala:974) ~[kafka_2.13-3.5.0.jar:?]	at kafka.cluster.Partition.maybeExpandIsr(Partition.scala:947) ~[kafka_2.13-3.5.0.jar:?]	at kafka.cluster.Partition.updateFollowerFetchState(Partition.scala:866) ~[kafka_2.13-3.5.0.jar:?]	at kafka.cluster.Partition.fetchRecords(Partition.scala:1361) ~[kafka_2.13-3.5.0.jar:?]	at kafka.server.ReplicaManager.read$1(ReplicaManager.scala:1164) ~[kafka_2.13-3.5.0.jar:?]	at kafka.server.ReplicaManager.$anonfun$readFromLocalLog$7(ReplicaManager.scala:1235) ~[kafka_2.13-3.5.0.jar:?]	at scala.collection.IterableOnceOps.foreach(IterableOnce.scala:575) ~[scala-library-2.13.10.jar:?]	at scala.collection.IterableOnceOps.foreach$(IterableOnce.scala:573) ~[scala-library-2.13.10.jar:?]	at scala.collection.AbstractIterable.foreach(Iterable.scala:933) ~[scala-library-2.13.10.jar:?]	at kafka.server.ReplicaManager.readFromLocalLog(ReplicaManager.scala:1234) ~[kafka_2.13-3.5.0.jar:?]	at kafka.server.ReplicaManager.fetchMessages(ReplicaManager.scala:1044) ~[kafka_2.13-3.5.0.jar:?]	at kafka.server.KafkaApis.handleFetchRequest(KafkaApis.scala:994) ~[kafka_2.13-3.5.0.jar:?]	at kafka.server.KafkaApis.handle(KafkaApis.scala:181) ~[kafka_2.13-3.5.0.jar:?]	at kafka.server.KafkaRequestHandler.run(KafkaRequestHandler.scala:76) ~[kafka_2.13-3.5.0.jar:?]	at java.lang.Thread.run(Thread.java:1623) [?:?] {code}
~~~~

---

## KAFKA-15374: ZK migration fails on configs for default broker resource

https://issues.apache.org/jira/browse/KAFKA-15374

JIRA metadata: affects 3.5.1; fixed in 3.5.2, 3.6.0

- `KAFKA-15374@3.5.1`: config 3.5.1, metadata answer **affected** (listed_affected)
- `KAFKA-15374@3.6.0`: config 3.6.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: none

### Description

~~~~
This error was seen while performing a ZK to KRaft migration on a cluster with configs for the default broker resource

 
{code:java}
java.lang.NumberFormatException: For input string: ""
	at java.base/java.lang.NumberFormatException.forInputString(NumberFormatException.java:67)
	at java.base/java.lang.Integer.parseInt(Integer.java:678)
	at java.base/java.lang.Integer.valueOf(Integer.java:999)
	at kafka.zk.ZkMigrationClient.$anonfun$migrateBrokerConfigs$2(ZkMigrationClient.scala:371)
	at kafka.zk.migration.ZkConfigMigrationClient.$anonfun$iterateBrokerConfigs$1(ZkConfigMigrationClient.scala:174)
	at kafka.zk.migration.ZkConfigMigrationClient.$anonfun$iterateBrokerConfigs$1$adapted(ZkConfigMigrationClient.scala:156)
	at scala.collection.immutable.BitmapIndexedMapNode.foreach(HashMap.scala:1076)
	at scala.collection.immutable.HashMap.foreach(HashMap.scala:1083)
	at kafka.zk.migration.ZkConfigMigrationClient.iterateBrokerConfigs(ZkConfigMigrationClient.scala:156)
	at kafka.zk.ZkMigrationClient.migrateBrokerConfigs(ZkMigrationClient.scala:370)
	at kafka.zk.ZkMigrationClient.cleanAndMigrateAllMetadata(ZkMigrationClient.scala:530)
	at org.apache.kafka.metadata.migration.KRaftMigrationDriver$MigrateMetadataEvent.run(KRaftMigrationDriver.java:618)
	at org.apache.kafka.queue.KafkaEventQueue$EventContext.run(KafkaEventQueue.java:127)
	at org.apache.kafka.queue.KafkaEventQueue$EventHandler.handleEvents(KafkaEventQueue.java:210)
	at org.apache.kafka.queue.KafkaEventQueue$EventHandler.run(KafkaEventQueue.java:181)
	at java.base/java.lang.Thread.run(Thread.java:833)
	at org.apache.kafka.common.utils.KafkaThread.run(KafkaThread.java:64) {code}
 

This is due to not considering the default resource type when we collect the broker IDs in ZkMigrationClient#migrateBrokerConfigs.

 

 
~~~~

---

## KAFKA-15537: Unsafe metadata.version downgrade is not supported

https://issues.apache.org/jira/browse/KAFKA-15537

JIRA metadata: affects 3.6.0; fixed in 3.7.0

- `KAFKA-15537@3.6.0`: config 3.6.0, metadata answer **affected** (listed_affected)
- `KAFKA-15537@3.7.1`: config 3.7.1, metadata answer **not_affected** (later_patch)

Known Kafka versions mentioned in text: 3.0, 3.1, 3.2, 3.3, 3.4

### Description

~~~~
In KIP-778 we introduced the "unsafe" (lossy) downgrade in case metadata has changes in one of the versions between target and current, as defined in MetadataVersion.

The documentation says it is possible.

bq. Note that the cluster metadata version cannot be downgraded to a pre-production 3.0.x, 3.1.x, or 3.2.x version once it has been upgraded. However, it is possible to downgrade to production versions such as 3.3-IV0, 3.3-IV1, etc.

The command line tool shows that this doesn't work.

{code}
bin/kafka-features.sh --bootstrap-server :9092 downgrade --metadata 3.4 --unsafe
Could not downgrade metadata.version to 8. Invalid metadata.version 8. Unsafe metadata downgrade is not supported in this version.
1 out of 1 operation(s) failed.
{code}

This is also a mentioned in KIP-868: "Note that lossy downgrades of the metadata log are detailed in KIP-778 and not yet fully implemented as of Kafka 3.3".

Additionally, you can't do any safe downgrade, because cluster metadata records are still evolving and every release has changes.

~~~~

### Comments (2)

1.

~~~~
[~fvaleri], thanks for raising this issue. Since you've dived into this issue, are you interested in submitting a PR for this issue?
~~~~

2.

~~~~
Sure. I already opened a PR to fix the documentation and improve the error messages.

~~~~

---

## KAFKA-15817: Avoid reconnecting to the same IP address if multiple addresses are available

https://issues.apache.org/jira/browse/KAFKA-15817

JIRA metadata: affects 3.3.2, 3.4.1, 3.5.1, 3.6.0; fixed in 3.6.2, 3.7.0

- `KAFKA-15817@3.3.2`: config 3.3.2, metadata answer **affected** (listed_affected)
- `KAFKA-15817@3.6.2`: config 3.6.2, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: none

### Description

~~~~
In https://issues.apache.org/jira/browse/KAFKA-12193, we changed the DNS resolution behavior for clients to re-resolve DNS after disconnecting from a broker, rather than wait until we iterated over all addresses from a given resolution. This is useful when the IP addresses have changed between the connection and disconnection.

However, with the behavior change, this does mean that clients could potentially reconnect immediately to the same IP they just disconnected from, if the IPs have not changed. In cases where the disconnection happened because that IP was unhealthy (such as a case where a load balancer has instances in multiple availability zones and one zone is unhealthy, or a case where an intermediate component in the network path is going through a rolling restart), this will delay the client successfully reconnecting. To address this, clients should remember the IP they just disconnected from and skip that IP when reconnecting, as long as the address resolved to multiple addresses.
~~~~

### Comments (1)

1.

~~~~
Resolving since this was merged. good job!

 
~~~~

---

## KAFKA-15945: Flaky test - testSyncTopicConfigs() – org.apache.kafka.connect.mirror.integration.MirrorConnectorsIntegrationBaseTest

https://issues.apache.org/jira/browse/KAFKA-15945

JIRA metadata: affects 3.7.0; fixed in 4.0.0

- `KAFKA-15945@3.7.0`: config 3.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-15945@4.0.0`: config 4.0.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: none

### Description

~~~~
Last seen: https://ci-builds.apache.org/blue/organizations/jenkins/Kafka%2Fkafka-pr/detail/PR-14811/7/tests

Error
org.opentest4j.AssertionFailedError: `delete.retention.ms` should be 2000, because it's explicitly defined on the target topic!  ==> expected: <2000> but was: <86400000>
Stacktrace
org.opentest4j.AssertionFailedError: `delete.retention.ms` should be 2000, because it's explicitly defined on the target topic!  ==> expected: <2000> but was: <86400000>
	at app//org.junit.jupiter.api.AssertionFailureBuilder.build(AssertionFailureBuilder.java:151)
	at app//org.junit.jupiter.api.AssertionFailureBuilder.buildAndThrow(AssertionFailureBuilder.java:132)
	at app//org.junit.jupiter.api.AssertEquals.failNotEqual(AssertEquals.java:197)
	at app//org.junit.jupiter.api.AssertEquals.assertEquals(AssertEquals.java:182)
	at app//org.junit.jupiter.api.Assertions.assertEquals(Assertions.java:1152)
	at app//org.apache.kafka.connect.mirror.integration.MirrorConnectorsIntegrationBaseTest.lambda$testSyncTopicConfigs$8(MirrorConnectorsIntegrationBaseTest.java:780)
	at app//org.apache.kafka.test.TestUtils.lambda$waitForCondition$3(TestUtils.java:331)
	at app//org.apache.kafka.test.TestUtils.retryOnExceptionWithTimeout(TestUtils.java:379)
	at app//org.apache.kafka.test.TestUtils.waitForCondition(TestUtils.java:328)
	at app//org.apache.kafka.test.TestUtils.waitForCondition(TestUtils.java:312)
	at app//org.apache.kafka.test.TestUtils.waitForCondition(TestUtils.java:302)
	at app//org.apache.kafka.connect.mirror.integration.MirrorConnectorsIntegrationBaseTest.testSyncTopicConfigs(MirrorConnectorsIntegrationBaseTest.java:774)
	at java.base@17.0.7/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at java.base@17.0.7/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:77)
	at java.base@17.0.7/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.base@17.0.7/java.lang.reflect.Method.invoke(Method.java:568)
	at app//org.junit.platform.commons.util.ReflectionUtils.invokeMethod(ReflectionUtils.java:728)
	at app//org.junit.jupiter.engine.execution.MethodInvocation.proceed(MethodInvocation.java:60)
	at app//org.junit.jupiter.engine.execution.InvocationInterceptorChain$ValidatingInvocation.proceed(InvocationInterceptorChain.java:131)
	at app//org.junit.jupiter.engine.extension.TimeoutExtension.intercept(TimeoutExtension.java:156)
	at app//org.junit.jupiter.engine.extension.TimeoutExtension.interceptTestableMethod(TimeoutExtension.java:147)
	at app//org.junit.jupiter.engine.extension.TimeoutExtension.interceptTestMethod(TimeoutExtension.java:86)
	at app//org.junit.jupiter.engine.execution.InterceptingExecutableInvoker$ReflectiveInterceptorCall.lambda$ofVoidMethod$0(InterceptingExecutableInvoker.java:103)
	at app//org.junit.jupiter.engine.execution.InterceptingExecutableInvoker.lambda$invoke$0(InterceptingExecutableInvoker.java:93)
	at app//org.junit.jupiter.engine.execution.InvocationInterceptorChain$InterceptedInvocation.proceed(InvocationInterceptorChain.java:106)
	at app//org.junit.jupiter.engine.execution.InvocationInterceptorChain.proceed(InvocationInterceptorChain.java:64)
	at app//org.junit.jupiter.engine.execution.InvocationInterceptorChain.chainAndInvoke(InvocationInterceptorChain.java:45)
	at app//org.junit.jupiter.engine.execution.InvocationInterceptorChain.invoke(InvocationInterceptorChain.java:37)
	at app//org.junit.jupiter.engine.execution.InterceptingExecutableInvoker.invoke(InterceptingExecutableInvoker.java:92)
	at app//org.junit.jupiter.engine.execution.InterceptingExecutableInvoker.invoke(InterceptingExecutableInvoker.java:86)
	at app//org.junit.jupiter.engine.descriptor.TestMethodTestDescriptor.lambda$invokeTestMethod$7(TestMethodTestDescriptor.java:218)
	at app//org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
	at app//org.junit.jupiter.engine.descriptor.TestMethodTestDescriptor.invokeTestMethod(TestMethodTestDescriptor.java:214)
	at app//org.junit.jupiter.engine.descriptor.TestMethodTestDescriptor.execute(TestMethodTestDescriptor.java:139)
	at app//org.junit.jupiter.engine.descriptor.TestMethodTestDescriptor.execute(TestMethodTestDescriptor.java:69)
	at app//org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$6(NodeTestTask.java:151)
	at app//org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
	at app//org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$8(NodeTestTask.java:141)
	at app//org.junit.platform.engine.support.hierarchical.Node.around(Node.java:137)
	at app//org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$9(NodeTestTask.java:139)
	at app//org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
	at app//org.junit.platform.engine.support.hierarchical.NodeTestTask.executeRecursively(NodeTestTask.java:138)
	at app//org.junit.platform.engine.support.hierarchical.NodeTestTask.execute(NodeTestTask.java:95)
	at java.base@17.0.7/java.util.ArrayList.forEach(ArrayList.java:1511)
	at app//org.junit.platform.engine.support.hierarchical.SameThreadHierarchicalTestExecutorService.invokeAll(SameThreadHierarchicalTestExecutorService.java:41)
	at app//org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$6(NodeTestTask.java:155)
	at app//org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
	at app//org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$8(NodeTestTask.java:141)
	at app//org.junit.platform.engine.support.hierarchical.Node.around(Node.java:137)
	at app//org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$9(NodeTestTask.java:139)
	at app//org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
	at app//org.junit.platform.engine.support.hierarchical.NodeTestTask.executeRecursively(NodeTestTask.java:138)
	at app//org.junit.platform.engine.support.hierarchical.NodeTestTask.execute(NodeTestTask.java:95)
	at java.base@17.0.7/java.util.ArrayList.forEach(ArrayList.java:1511)
	at app//org.junit.platform.engine.support.hierarchical.SameThreadHierarchicalTestExecutorService.invokeAll(SameThreadHierarchicalTestExecutorService.java:41)
	at app//org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$6(NodeTestTask.java:155)
	at app//org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
	at app//org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$8(NodeTestTask.java:141)
	at app//org.junit.platform.engine.support.hierarchical.Node.around(Node.java:137)
	at app//org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$9(NodeTestTask.java:139)
	at app//org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
	at app//org.junit.platform.engine.support.hierarchical.NodeTestTask.executeRecursively(NodeTestTask.java:138)
	at app//org.junit.platform.engine.support.hierarchical.NodeTestTask.execute(NodeTestTask.java:95)
	at app//org.junit.platform.engine.support.hierarchical.SameThreadHierarchicalTestExecutorService.submit(SameThreadHierarchicalTestExecutorService.java:35)
	at app//org.junit.platform.engine.support.hierarchical.HierarchicalTestExecutor.execute(HierarchicalTestExecutor.java:57)
	at app//org.junit.platform.engine.support.hierarchical.HierarchicalTestEngine.execute(HierarchicalTestEngine.java:54)
	at app//org.junit.platform.launcher.core.EngineExecutionOrchestrator.execute(EngineExecutionOrchestrator.java:107)
	at app//org.junit.platform.launcher.core.EngineExecutionOrchestrator.execute(EngineExecutionOrchestrator.java:88)
	at app//org.junit.platform.launcher.core.EngineExecutionOrchestrator.lambda$execute$0(EngineExecutionOrchestrator.java:54)
	at app//org.junit.platform.launcher.core.EngineExecutionOrchestrator.withInterceptedStreams(EngineExecutionOrchestrator.java:67)
	at app//org.junit.platform.launcher.core.EngineExecutionOrchestrator.execute(EngineExecutionOrchestrator.java:52)
	at app//org.junit.platform.launcher.core.DefaultLauncher.execute(DefaultLauncher.java:114)
	at app//org.junit.platform.launcher.core.DefaultLauncher.execute(DefaultLauncher.java:86)
	at app//org.junit.platform.launcher.core.DefaultLauncherSession$DelegatingLauncher.execute(DefaultLauncherSession.java:86)
	at org.gradle.api.internal.tasks.testing.junitplatform.JUnitPlatformTestClassProcessor$CollectAllTestClassesExecutor.processAllTestClasses(JUnitPlatformTestClassProcessor.java:118)
	at org.gradle.api.internal.tasks.testing.junitplatform.JUnitPlatformTestClassProcessor$CollectAllTestClassesExecutor.access$000(JUnitPlatformTestClassProcessor.java:93)
	at org.gradle.api.internal.tasks.testing.junitplatform.JUnitPlatformTestClassProcessor.stop(JUnitPlatformTestClassProcessor.java:88)
	at org.gradle.api.internal.tasks.testing.SuiteTestClassProcessor.stop(SuiteTestClassProcessor.java:62)
	at java.base@17.0.7/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at java.base@17.0.7/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:77)
	at java.base@17.0.7/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.base@17.0.7/java.lang.reflect.Method.invoke(Method.java:568)
	at org.gradle.internal.dispatch.ReflectionDispatch.dispatch(ReflectionDispatch.java:36)
	at org.gradle.internal.dispatch.ReflectionDispatch.dispatch(ReflectionDispatch.java:24)
	at org.gradle.internal.dispatch.ContextClassLoaderDispatch.dispatch(ContextClassLoaderDispatch.java:33)
	at org.gradle.internal.dispatch.ProxyDispatchAdapter$DispatchingInvocationHandler.invoke(ProxyDispatchAdapter.java:94)
	at jdk.proxy1/jdk.proxy1.$Proxy2.stop(Unknown Source)
	at org.gradle.api.internal.tasks.testing.worker.TestWorker$3.run(TestWorker.java:193)
	at org.gradle.api.internal.tasks.testing.worker.TestWorker.executeAndMaintainThreadName(TestWorker.java:129)
	at org.gradle.api.internal.tasks.testing.worker.TestWorker.execute(TestWorker.java:100)
	at org.gradle.api.internal.tasks.testing.worker.TestWorker.execute(TestWorker.java:60)
	at org.gradle.process.internal.worker.child.ActionExecutionWorker.execute(ActionExecutionWorker.java:56)
	at org.gradle.process.internal.worker.child.SystemApplicationClassLoaderWorker.call(SystemApplicationClassLoaderWorker.java:113)
	at org.gradle.process.internal.worker.child.SystemApplicationClassLoaderWorker.call(SystemApplicationClassLoaderWorker.java:65)
	at app//worker.org.gradle.process.internal.worker.GradleWorkerMain.run(GradleWorkerMain.java:69)
	at app//worker.org.gradle.process.internal.worker.GradleWorkerMain.main(GradleWorkerMain.java:74)
~~~~

### Comments (3)

1.

~~~~
Raised PR: https://github.com/apache/kafka/pull/14893
~~~~

2.

~~~~
Another instance

https://ci-builds.apache.org/blue/organizations/jenkins/Kafka%2Fkafka-pr/detail/PR-16077/4/tests/
{code:java}
org.opentest4j.AssertionFailedError: `delete.retention.ms` should be 2000, because it's explicitly defined on the target topic!  ==> expected: <2000> but was: <86400000>
    at org.junit.jupiter.api.AssertionFailureBuilder.build(AssertionFailureBuilder.java:151)
    at org.junit.jupiter.api.AssertionFailureBuilder.buildAndThrow(AssertionFailureBuilder.java:132)
    at org.junit.jupiter.api.AssertEquals.failNotEqual(AssertEquals.java:197)
    at org.junit.jupiter.api.AssertEquals.assertEquals(AssertEquals.java:182)
    at org.junit.jupiter.api.Assertions.assertEquals(Assertions.java:1156)
    at org.apache.kafka.connect.mirror.integration.MirrorConnectorsIntegrationBaseTest.lambda$testSyncTopicConfigs$8(MirrorConnectorsIntegrationBaseTest.java:788)
    at org.apache.kafka.test.TestUtils.lambda$waitForCondition$3(TestUtils.java:396)
    at org.apache.kafka.test.TestUtils.retryOnExceptionWithTimeout(TestUtils.java:444)
    at org.apache.kafka.test.TestUtils.waitForCondition(TestUtils.java:393)
    at org.apache.kafka.test.TestUtils.waitForCondition(TestUtils.java:377)
    at org.apache.kafka.test.TestUtils.waitForCondition(TestUtils.java:367)
    at org.apache.kafka.connect.mirror.integration.MirrorConnectorsIntegrationBaseTest.testSyncTopicConfigs(MirrorConnectorsIntegrationBaseTest.java:782) {code}
~~~~

3.

~~~~
This test is no longer failing on trunk and [has been green for the last week|https://ge.apache.org/scans/tests?search.rootProjectNames=kafka&search.tags=trunk&search.timeZoneId=America%2FNew_York&tests.container=org.apache.kafka.connect.mirror.integration.MirrorConnectorsIntegrationBaseTest]; closing as fixed. If we see more failures, please reopen.
~~~~

---

## KAFKA-16047: Source connector with EOS enabled have some InitProducerId requests timing out, effectively failing all the tasks & the whole connector

https://issues.apache.org/jira/browse/KAFKA-16047

JIRA metadata: affects 3.3.0, 3.3.1, 3.3.2, 3.4.0, 3.4.1, 3.5.1, 3.5.2, 3.6.0, 3.6.1; fixed in 3.7.1, 3.8.0

- `KAFKA-16047@3.6.0`: config 3.6.0, metadata answer **affected** (listed_affected)
- `KAFKA-16047@3.7.2`: config 3.7.2, metadata answer **not_affected** (later_patch)

Known Kafka versions mentioned in text: 3.6.1, 0.11

### Description

~~~~
Source Connectors with 'exactly.once.support = required' may have some of their tasks that issue InitProducerId requests from the admin client timeout. In the case of MirrorSourceConnector, which was the source connector that i found the bug, the bug was effectively making all the tasks (in the specific case of) become "FAILED". As soon as one of the tasks gets FAILED due to the 'COORDINATOR_NOT_AVAILABLE' messages (due to timeouts), no matter how many restarts i did to the connector/tasks, i couldn't get the MirrorSourceConnector in a healthy RUNNING state again.

Due to the low timeout that has been [hard-coded in the code|https://github.com/apache/kafka/blob/3.6.1/clients/src/main/java/org/apache/kafka/clients/admin/internals/FenceProducersHandler.java#L87] (1ms), there is a chance that the `InitProducerId` requests timeout in case of "slower-than-expected" Kafka brokers (that do not process & respond to the above request in <= 1ms). (feel free to read more information about the issue in the "More Context" section below)

[~ChrisEgerton] I would appreciate it if you could respond to the following questions
- How and why was the 1ms magic number for transaction timeout has to be chosen?
- Is there any specific reason that it can be guaranteed that the `InitProducerId` request can be processed in such a small time window? 
- I have tried the above in multiple different Kafka clusters that are hosted in different underlying datacenter hosts and i don't believe that those brokers are "slow" for some reason. If you feel that the brokers are slower than expected, i would appreciate any pointers on how could i find out what is the bottleneck


h3. Temporary Mitigation

I have increased the timeout to 1000ms (randomly picked this number, just wanted to give enough time to brokers to always complete those type of requests). It fix can be found in my fork https://github.com/akaltsikis/kafka/commit/8a47992e7dc63954f9d9ac54e8ed1f5a7737c97f 

h3. Final solution

The temporary mitigation is not ideal, as it still randomly picks a timeout for such an operation which may high enough but it's not ensured that it will always be high enough. Shall we introduce something client configurable ?
At the same time, i was thinking whether it makes sense to introduce some tests that simulate slower than the "blazing" fast mocked brokers that exist in Unit Tests, so as to be able to catch this type of low timeouts that potentially make some software features not usable.


h3. What is affected

The above bug exists in MirrorSourceConnector Tasks running in distributed Kafka connect cluster or MIrrorMaker 2 jobs that run with distributed mode enabled (pre-requisite for the exactly.once.support to work). I believe this should be true for other SourceConnectors as well (as the code-path that was the one to blame is Connect specific & not MirrorMaker specific).

h3. More context & logs

*Connector Logs*
{code:java}
Caused by: java.util.concurrent.CompletionException: org.apache.kafka.common.errors.TimeoutException: Timed out waiting for a node assignment. Call: fenceProducer(api=INIT_PRODUCER_ID)
{code}

*Broker Logs*
{code:java}
[2023-12-12 14:28:18,030] INFO [TransactionCoordinator id=<id>] Returning COORDINATOR_NOT_AVAILABLE error code to client for kafka-connect-uat-mm2-msc-20th-7's InitProducerId request (kafka.coordinator.transaction.TransactionCoordinator)


[2023-12-12 14:28:18,030] INFO [Transaction State Manager 1001]: TransactionalId kafka-connect-uat-mm2-msc-20th-7 append transaction log for TxnTransitMetadata(producerId=61137, lastProducerId=61137, producerEpoch=2, lastProducerEpoch=-1, txnTimeoutMs=1, txnState=Empty, topicPartitions=Set(), txnStartTimestamp=-1, txnLastUpdateTimestamp=1702391298028) transition failed due to COORDINATOR_NOT_AVAILABLE, resetting pending state from Some(Empty), aborting state transition and returning COORDINATOR_NOT_AVAILABLE in the callback (kafka.coordinator.transaction.TransactionStateManager)
{code}


h3. How to reproduce it

While the bug exists in both the Standalone MM2 deployment, it's easier to reproduce it via deploying the connector to a Kafka Connect cluster (as it is possible to update the config/delete/restart/pause/stop/resume via the Kafka Connect REST API)
Thus, Deploy a MirrorSourceConnector on a Kafka connect cluster (with `exactly.once.source.support = enabled`) and after the initial start, update it's configuration or restart the connector & tasks. 

To test whether my fork has fixed the issue once and for good i have created the following script, which constantly restarts the connector every few seconds (after it's tasks get in RUNNING state). I have been running the scripts for a few hours and the MirrorSourceConnector never got in a state that was non recoverable (as it was happening on the upstream versions)

{code:java}
#!/bin/bash

# Source vars
source /<path>/connect.sh
# Kafka Connect API endpoint
KAFKA_CONNECT_API=$KAFKA_CONNECT_URL

# Kafka Connect connector name
CONNECTOR_NAME="<connector_name>"

while true; do
    # Fetch the connector status
    connector_status=$(curl -k -u $KAFKA_CONNECT_BASIC_AUTH_USERNAME:$KAFKA_CONNECT_BASIC_AUTH_PASSWORD -s "$KAFKA_CONNECT_API/connectors/$CONNECTOR_NAME/status")

    # Check if connector is in FAILED state
    if echo "$connector_status" | grep -q '"state":"FAILED"'; then
        echo "Connector has failed. Exiting."
        exit 1
    fi

    # Fetch and check all task statuses
    task_statuses=$(echo "$connector_status" | jq '.tasks[].state')
    all_running=true
    for status in $task_statuses; do
        if [ "$status" != '"RUNNING"' ]; then
            all_running=false
            break
        fi
    done

    # If all tasks and the connector are RUNNING, restart them after 90 seconds
    if $all_running; then
        echo "All tasks are running. Restarting in 90 seconds."
        sleep 90
        date;curl -k -X POST -H "Content-Type: application/json" -u $KAFKA_CONNECT_BASIC_AUTH_USERNAME:$KAFKA_CONNECT_BASIC_AUTH_PASSWORD $KAFKA_CONNECT_API/connectors/$CONNECTOR_NAME/restart\?includeTasks=true
    else
        echo "Not all tasks are running. Checking again..."
    fi

    # Sleep for a while before checking again
    sleep 10
done
{code}






~~~~

### Comments (9)

1.

~~~~
cc. [~gregharris73]
~~~~

2.

~~~~
It appears that the transaction timeout is used as the timeout to produce records to the __transaction_state topic in TransactionStateManager#appendTransactionToLog [https://github.com/apache/kafka/blob/d582d5aff517879b150bc2739bad99df07e15e2b/core/src/main/scala/kafka/coordinator/transaction/TransactionStateManager.scala#L769-L770]
which is in turn used during init, end, and add-partitions in TransactionCoordinator: [https://github.com/apache/kafka/blob/d582d5aff517879b150bc2739bad99df07e15e2b/core/src/main/scala/kafka/coordinator/transaction/TransactionCoordinator.scala#L199] 

I see that after expiration, TransactionStateManager#writeTombstonesForExpiredTransactionalIds uses the request.timeout.ms: [https://github.com/apache/kafka/blob/d582d5aff517879b150bc2739bad99df07e15e2b/core/src/main/scala/kafka/coordinator/transaction/TransactionStateManager.scala#L283-L284] 

Should the TransactionStateManager be using the transaction timeout ms for a single-operation, or should the request timeout be used throughout? Using the transaction timeout is certainly shorter than we expect, but I wonder if that's also longer than people expect in other situations. When the producer makes these requests, it only waits for max.block.ms (default 60s) for them to complete. After that point, the producer times out the request, while the broker may be left waiting for the transaction timeout (default 60s) to expire.

* We can fix this on the broker side by changing the produce timeout to the value of "max(transaction timeout, request timeout)". Someone may have increased their max.block.ms & transaction timeout while keeping the request timeout short, and would still desire that the init call block for up to max.block.ms.
* We can fix this on the client side by changing the 1ms hardcoded value to use the same timeout as the overall fenceProducers request, which is either the default request timeout (configurable) or specified via the Options argument.
~~~~

3.

~~~~
I found this code-review comment thread about this timeout: [https://github.com/apache/kafka/pull/2849#discussion_r111528120] There was originally a comment explicitly pointing out that the transaction timeout was used, but without any substantive reasoning why. The same concern about the excessive waiting on the broker side was raised, but as the default was 60s, no action appears to have been taken.

As this code is so old (2017/0.11) and this problem only affects extremely low transaction timeouts, I think we should opt for the client-side fix to increase the transaction timeout to the request timeout, rather than hardcoding 1ms.

[~akaltsikis] Are you interested in assigning this to yourself and opening a PR to fix it? You can tag me as a reviewer.
~~~~

4.

~~~~
Yes sir. Will do so and ask for a review. Btw thanks for the extra context 👌🏽
~~~~

5.

~~~~
Hey [~gharris1727], here is the MR https://github.com/apache/kafka/pull/15078

As this is my first MR/commit in Kafka (& generally in an apache repo), please bear with me and let me know if there is something/missing on the MR.
~~~~

6.

~~~~
[~gharris1727]

I see that for a common produce request,

ReplicaManager.appendRecords uses the timeout set as  {color:#000000}ProducerConfig{color}.{color:#871094}REQUEST_TIMEOUT_MS_CONFIG{color}

i.e. {color:#000000}CommonClientConfigs.{color}{color:#871094}REQUEST_TIMEOUT_MS_CONFIG{color}

would it not make sense to always use that timeout when appending to a log ?


BTW, MirrorMaker2 is unusable in a connect cluster set up with exactly once, when the broker server.properties
are changed from the settings used in development testing and present in the config properties files.
{color:#0000ff}transaction.state.log.replication.factor{color}{color:#000000}=1{color}
{color:#0000ff}transaction.state.log.min.isr{color}{color:#000000}=1{color}
 
[~akaltsikis] I see that you could not progress your PR. Are you happy to hand over this bugfix?
~~~~

7.

~~~~
[~gharris1727] please see [https://github.com/apache/kafka/pull/16151]

This works IMHO as a hotfix that requires no KIP.

Arguably all appends to the transaction log could use this timeout, rather than the transaction timeout which has a completely different semantic, tied to the transaction not to the appending of a record and its replication. 
However I think that such a change may require a KIP and may have a much larger impact than just fixing Admin.fenceProducers and distributed Connect
~~~~

8.

~~~~
^ cc [~ChrisEgerton] [~cegerton] 
~~~~

9.

~~~~
https://github.com/apache/kafka/pull/16151
~~~~

---

## KAFKA-16055: Thread unsafe use of HashMap stored in QueryableStoreProvider#storeProviders

https://issues.apache.org/jira/browse/KAFKA-16055

JIRA metadata: affects 3.6.1; fixed in 3.8.0

- `KAFKA-16055@3.6.1`: config 3.6.1, metadata answer **affected** (listed_affected)
- `KAFKA-16055@3.8.0`: config 3.8.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 3.6.1

### Description

~~~~
This was originally raised in [a kafka-users post|https://lists.apache.org/thread/gpct1275bfqovlckptn3lvf683qpoxol].

There is a HashMap stored in QueryableStoreProvider#storeProviders ([code link|https://github.com/apache/kafka/blob/3.6.1/streams/src/main/java/org/apache/kafka/streams/state/internals/QueryableStoreProvider.java#L39]) which can be mutated by a KafkaStreams#removeStreamThread() call. This can be problematic when KafkaStreams#store is called from a separate thread.

We need to somehow make this part of code thread-safe by replacing it by ConcurrentHashMap or/and using an existing locking mechanism.
~~~~

### Comments (2)

1.

~~~~
 See this discussion on the user mailing list for additional context: [https://lists.apache.org/thread/gpct1275bfqovlckptn3lvf683qpoxol]
~~~~

2.

~~~~
Pull request: [https://github.com/apache/kafka/pull/15121]
~~~~

---

## KAFKA-16288: Values.convertToDecimal throws ClassCastExceptions on String inputs

https://issues.apache.org/jira/browse/KAFKA-16288

JIRA metadata: affects 1.1.0; fixed in 3.8.0

- `KAFKA-16288@1.1.0`: config 1.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-16288@3.9.0`: config 3.9.0, metadata answer **not_affected** (later_line)

Known Kafka versions mentioned in text: none

### Description

~~~~
The convertToDecimal function does a best-effort conversion of an arbitrary Object to a BigDecimal. Generally when a conversion cannot take place (such as when an unknown subclass is passed-in) the function throws a DataException. However, specifically for String inputs with valid number within, a ClassCastException is thrown.

This is because there is an extra "doubleValue" call in the implementation: [https://github.com/apache/kafka/blob/ead2431c37ace9255df88ffe819bb905311af088/connect/api/src/main/java/org/apache/kafka/connect/data/Values.java#L427] which immediately causes a ClassCastException in the caller: [https://github.com/apache/kafka/blob/ead2431c37ace9255df88ffe819bb905311af088/connect/api/src/main/java/org/apache/kafka/connect/data/Values.java#L305] 

This appears accidental, because the case for String is explicitly handled, it just behaves poorly. Instead of the ClassCastException, the number should be parsed correctly.
~~~~

---

## KAFKA-16310: ListOffsets doesn't report the offset with maxTimestamp anymore

https://issues.apache.org/jira/browse/KAFKA-16310

JIRA metadata: affects 3.7.0; fixed in 3.8.0

- `KAFKA-16310@3.7.0`: config 3.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-16310@3.8.0`: config 3.8.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: v3.7.0, 3.6.0, 3.7.0, 3.4, 3.6.2, 3.6, 3.7

### Description

~~~~
Updated: This is confirmed a regression issue in v3.7.0. 

The impact of this issue is that when there is a batch containing records with timestamp not in order, the offset of the timestamp will be wrong.(ex: the timestamp for t0 should be mapping to offset 10, but will get offset 12.. etc). It'll cause the time index is putting the wrong offset, so the result will be unexpected. 

===
The last offset is reported instead.
A test in librdkafka (0081/do_test_ListOffsets) is failing an it's checking that the offset with the max timestamp is the middle one and not the last one. The tests is passing with 3.6.0 and previous versions

This is the test:
[https://github.com/confluentinc/librdkafka/blob/a6d85bdbc1023b1a5477b8befe516242c3e182f6/tests/0081-admin.c#L4989]

 

there are three messages, with timestamps:
{noformat}
t0 + 100
t0 + 400
t0 + 250{noformat}
and indices 0,1,2. 

then a ListOffsets with RD_KAFKA_OFFSET_SPEC_MAX_TIMESTAMP is done.
it should return offset 1 but in 3.7.0 and trunk is returning offset 2

Even after 5 seconds from producing it's still returning 2 as the offset with max timestamp.
ProduceRequest and ListOffsets were sent to the same broker (2), the leader didn't change.


{code:java}
%7|1709134230.019|SEND|0081_admin#producer-3| [thrd:localhost:39951/bootstrap]: localhost:39951/2: Sent ProduceRequest (v7, 206 bytes @ 0, CorrId 2) %7|1709134230.020|RECV|0081_admin#producer-3| [thrd:localhost:39951/bootstrap]: localhost:39951/2: Received ProduceResponse (v7, 95 bytes, CorrId 2, rtt 1.18ms) %7|1709134230.020|MSGSET|0081_admin#producer-3| [thrd:localhost:39951/bootstrap]: localhost:39951/2: rdkafkatest_rnd22e8d8ec45b53f98_do_test_ListOffsets [0]: MessageSet with 3 message(s) (MsgId 0, BaseSeq -1) delivered {code}
{code:java}
%7|1709134235.021|SEND|0081_admin#producer-2| [thrd:localhost:39951/bootstrap]: localhost:39951/2: Sent ListOffsetsRequest (v7, 103 bytes @ 0, CorrId 7) %7|1709134235.022|RECV|0081_admin#producer-2| [thrd:localhost:39951/bootstrap]: localhost:39951/2: Received ListOffsetsResponse (v7, 88 bytes, CorrId 7, rtt 0.54ms){code}
~~~~

### Comments (36)

1.

~~~~
the bug is related to https://issues.apache.org/jira/browse/KAFKA-14477

the code of updating `offsetOfMaxTimestamp` was:

{code:scala}
    if (timestampType == TimestampType.LOG_APPEND_TIME) {
      maxTimestamp = now
      if (magic >= RecordBatch.MAGIC_VALUE_V2)
        offsetOfMaxTimestamp = offsetCounter.value - 1
      else
        offsetOfMaxTimestamp = initialOffset
    }
{code}

and now we always update `offsetOfMaxTimestamp` to `offsetCounter.value - 1` even though it is  TimestampType.LOG_APPEND_TIME (see https://github.com/apache/kafka/blob/trunk/storage/src/main/java/org/apache/kafka/storage/internals/log/LogValidator.java#L300)
{code:java}
        if (timestampType == TimestampType.LOG_APPEND_TIME) {
            maxTimestamp = now;
            offsetOfMaxTimestamp = initialOffset;
        }

        if (toMagic >= RecordBatch.MAGIC_VALUE_V2) {
            offsetOfMaxTimestamp = offsetCounter.value - 1;
        }
{code}

Furthermore, the path of compressed data has similar issue. see https://github.com/apache/kafka/blob/trunk/storage/src/main/java/org/apache/kafka/storage/internals/log/LogValidator.java#L417

[~kevinztw] [~ijuma] Please double check the root cause, thanks!

~~~~

2.

~~~~
Yes, [~jolshan] and [~hachikuji] looked into this and arrived to a similar conclusion. I think one of them was going to submit a fix soon.
~~~~

3.

~~~~
Thanks! Please let us know when the PR is open.
~~~~

4.

~~~~
[~ijuma] thanks for feedback. good to know we are on the same page :)

{quote}
I think one of them was going to submit a fix soon.
{quote}

Please feel free to assign this JIRA to us if you guys have no free cycle. It seems the fix is straightforward as we can follow the behavior of Scala code.

~~~~

5.

~~~~
By the way, the bug attribution doesn't seem completely right (or not right at all). There were more recent changes to LogValidator after the conversion to Java that touched the related area.
~~~~

6.

~~~~
More recent changes to LogValidator: [https://github.com/apache/kafka/commit/e905ef1edfb92d8771e8c2a9a668f32210ad7e07]

My understanding is that the following change caused the change to the non compressed case. It looks like the compressed case had the issue already, but we didn't go further back to see if that has always been the case or not.
~~~~

7.

~~~~
{quote}
It looks like the compressed case had the issue already, but we didn't go further back to see if that has always been the case or not.
{quote}

I think the bug is already there before. I write the tests for both cases (compression and non-compression), and both cases fails at trunk. By contrast, only compression get failure at 3.4
see: https://github.com/chia7712/kafka/blob/KAFKA-16310-3.4/core/src/test/scala/integration/kafka/api/OffsetOfMaxTimestampTest.scala#L52
~~~~

8.

~~~~
Thanks for confirming that. [https://github.com/apache/kafka/commit/e905ef1edfb92d8771e8c2a9a668f32210ad7e07] is indeed the only relevant regression then. We should take the chance to fix the regression and the previously existing issue.
~~~~

9.

~~~~
[~chia7712] Thanks for the analysis. Ironically, my original approach was to fix the compressed path to match the uncompressed path so that we passed along the actual offset of max timestamp. I ended up doing the opposite though. If either you or [~showuon] have time to submit a fix, I am happy to review. 
~~~~

10.

~~~~
{quote}
[https://github.com/apache/kafka/commit/e905ef1edfb92d8771e8c2a9a668f32210ad7e07] is indeed the only relevant regression then. We should take the chance to fix the regression and the previously existing issue.
{quote}
[~ijuma] oh, I pointed to incorrect ticket. Thanks for correcting, and sorry :-

{quote}
Thanks for the analysis. Ironically, my original approach was to fix the compressed path to match the uncompressed path so that we passed along the actual offset of max timestamp. I ended up doing the opposite though. If either you or Luke Chen have time to submit a fix, I am happy to review. 
{quote}

hi [~hachikuji] I have offline  discussion with [~showuon], so we have time to submit/backport the fix.
~~~~

11.

~~~~
Created 2 sub-tasks for compressed and un-compressed records.
~~~~

12.

~~~~
will resolve this jira after [~johnnyhsu] update KIP-734 (https://cwiki.apache.org/confluence/display/KAFKA/KIP-734:+Improve+AdminClient.listOffsets+to+return+timestamp+and+offset+for+the+record+with+the+largest+timestamp)
~~~~

13.

~~~~
The update is in below section:

 

## When the TimestampType is LOG_APPEND_TIME

When the TimestampType is LOG_APPEND_TIME, the timestamp of the records are the same. In this case, we should choose the offset of the first record. [This path|https://github.com/apache/kafka/blob/6f38fe5e0a6e2fe85fec7cb9adc379061d35ce45/storage/src/main/java/org/apache/kafka/storage/internals/log/LogValidator.java#L294] in LogValidator was added to handle this case for non-compressed type, while [this path|https://github.com/apache/kafka/blob/6f38fe5e0a6e2fe85fec7cb9adc379061d35ce45/storage/src/main/java/org/apache/kafka/storage/internals/log/LogValidator.java#L421] in LogValidator was added to handle this case for compressed type.  

I don't have the Confluence account yet, [~chia7712] would you please help update the KIP in the wiki? I will send this update to the dev thread for visibility. Thanks! 
~~~~

14.

~~~~
@johnnyhsu thanks for offers the description. I add following statement to KIP-734 according to your comments.

{quote}

This returns the offset and timestamp corresponding to the record with the highest timestamp on the partition. Noted that we should choose the offset of the earliest record if the timestamp of the records are the same.

{quote}

WDYT?
~~~~

15.

~~~~
{quote}[~chia7712] thanks for the help!

This returns the offset and timestamp corresponding to the record with the highest timestamp on the partition. Noted that we should choose the offset of the earliest record if the timestamp of the records are the same.

This sounds good to me, thanks! {quote}
~~~~

16.

~~~~
[~johnnyhsu] , [~showuon] and [~chia7712] : Sorry, but I just realized one issue with the fix. The problem is that we only fixed offsetForMaxTimestamp during leader append. The follower append still uses the lastOffset in the batch. 

 
{code:java}
UnifiedLog.analyzeAndValidateRecords()

lastOffset = batch.lastOffset

...

if (batch.maxTimestamp > maxTimestamp) {
  maxTimestamp = batch.maxTimestamp
  offsetOfMaxTimestamp = lastOffset
} {code}
We optimize the follower code to avoid decompressing a batch. So, it's kind of hard to get the exact record offset for maxTimestamp in the batch.

 

I think the easiest way to fix the listMaxTimestamp issue is probably to still maintain offsetOfMaxTimestamp at the record batch level so that it can be derived consistently at both the leader and the follower. When serving the listMaxTimestamp request, we iterate the batch containing the maxTimestamp to find the exact record offset with maxTimestamp. Since this is a rare operation, paying the decompression overhead is fine. What do you think?

 

If we want to do the above, we probably need to revert the changes in 3.6.2, which is being voted now. cc [~omkreddy] 
~~~~

17.

~~~~
[~chia7712] [~showuon] Can we revert the relavent changes from 3.6 branch as this not regression in 3.6.x releases and looks like complete fix requires few more changes. This is to unblock 3.6.2 release. 
~~~~

18.

~~~~
{quote}
Can we revert the relavent changes from 3.6 branch as this not regression in 3.6.x releases and looks like complete fix requires few more changes. This is to unblock 3.6.2 release. 
{quote}

sure, please feel free to revert KAFKA-16341 and KAFKA-16342. Sorry for that incomplete fix and it blocks the 3.6.2 :(

I will update KIP-734 to remind users that  behavior of  maxTimestamp offset could be changed in the future release.


~~~~

19.

~~~~
Thanks, I have reverted  KAFKA-16341 and KAFKA-16342. commits from 3.6 branch
~~~~

20.

~~~~
{quote}
I think the easiest way to fix the listMaxTimestamp issue is probably to still maintain offsetOfMaxTimestamp at the record batch level so that it can be derived consistently at both the leader and the follower. When serving the listMaxTimestamp request, we iterate the batch containing the maxTimestamp to find the exact record offset with maxTimestamp. Since this is a rare operation, paying the decompression overhead is fine. What do you think?
{quote}

I'm still digging in :)

BTW, it seems the recovering the segments has similar issue. 
{code}
                // The max timestamp is exposed at the batch level, so no need to iterate the records
                if (batch.maxTimestamp() > maxTimestampSoFar()) {
                    maxTimestampAndOffsetSoFar = new TimestampOffset(batch.maxTimestamp(), batch.lastOffset());
                }
{code}
~~~~

21.

~~~~
{quote}I think the easiest way to fix the listMaxTimestamp issue is probably to still maintain offsetOfMaxTimestamp at the record batch level so that it can be derived consistently at both the leader and the follower.
{quote}
Did you mean that we should change the schema to have a new field to keep `offsetOfMaxTimestamp`? or just add a new method to Batch to iterate all records to find out offsetOfMaxTimestamp?
{quote}When serving the listMaxTimestamp request, we iterate the batch containing the maxTimestamp to find the exact record offset with maxTimestamp. Since this is a rare operation, paying the decompression overhead is fine.
{quote}
I gree to this solution. Furthermore, there are other works we can do for this solution.
 # catch maxTimestamp instead of maxTimestampAndOffsetSoFar ([https://github.com/apache/kafka/blob/trunk/storage/src/main/java/org/apache/kafka/storage/internals/log/LogSegment.java#L93]) since we do iterate all records to find out the offsetOfMaxTimestamp
 # update time index by (max timestamp, last offset) even though the mapping is not accurate. It should be fine since:
 ** it does not violate spec of time index ([https://github.com/apache/kafka/blob/trunk/storage/src/main/java/org/apache/kafka/storage/internals/log/TimeIndex.java#L36]) `Any message whose timestamp is greater than TIMESTAMP must come after OFFSET`
 ** the index returned from time index is used to look up the position of batch, so it makes sense we append lastOffset to both time index and offset index

In short, we do NOT trace offsetOfMaxTimestamp for all paths. The side effect is that request to offsetOfMaxTimestamp can get slower ...
~~~~

22.

~~~~
{quote}Did you mean that we should change the schema to have a new field to keep `offsetOfMaxTimestamp`? or just add a new method to Batch to iterate all records to find out offsetOfMaxTimestamp?
{quote}
I think it's the former, otherwise, we're still iterating all records, and the overhead for follower is unnecessary.

 
{quote}When serving the listMaxTimestamp request, we iterate the batch containing the maxTimestamp to find the exact record offset with maxTimestamp. Since this is a rare operation, paying the decompression overhead is fine.
{quote}
Yes, I agree with this method. But the question is, should we revert the fix in this JIRA? I think no because the fix doesn't change anything (no additional overhead at all) if we will iterate the batch when returning listOffset for MaxTimestamp in the end.WDYT?
~~~~

23.

~~~~
> Yes, I agree with this method. But the question is, should we revert the fix in this JIRA? I think no because the fix doesn't change anything (no additional overhead at all) if we will iterate the batch when returning listOffset for MaxTimestamp in the end.WDYT?

We can do a little optimization if current fixes are kept. We do iterate batches to find the q only if we don’t cache it. i.e the path of leader can return the cached offsetOfMaxTimestanp. The other paths do not cache the offsetOfMaxTimestanpq
~~~~

24.

~~~~
[~chia7712] :
{quote}Did you mean that we should change the schema to have a new field to keep `offsetOfMaxTimestamp`? or just add a new method to Batch to iterate all records to find out offsetOfMaxTimestamp?
{quote}
Adding a new field in the batch requires record format change, which is a much bigger effort. For now, the easiest thing is to add a method in Batch to find out offsetOfMaxTimestanp by iterating all records.

Regarding the optimization on the leader side by caching offsetOfMaxTimestanp, we could do it. However, my understanding is that listMaxTimestamp is rare and I am not sure if it's worth the additional complexity.

[~showuon] : Regarding the fix, we could fix forward if we could provide the fix soon. Otherwise, we probably want to revert the fixes to avoid new code depending on the new semantic since we changed shallowOffsetOfMaxTimestanp to offsetOfMaxTimestanp.
~~~~

25.

~~~~
Team, there are serious issues that are fixed by 3.6.2. We should not delay it due to a long standing issue. As I said elsewhere, if it's not a regression or a security issue, it should be avoided. Precisely to avoid the issue that happened here. Let's revert and move on please.
~~~~

26.

~~~~
{quote}
Team, there are serious issues that are fixed by 3.6.2. We should not delay it due to a long standing issue. As I said elsewhere, if it's not a regression or a security issue, it should be avoided. Precisely to avoid the issue that happened here. Let's revert and move on please.
{quote}

 [~ijuma] Are you worry about the 3.6.2? If so, the fixes are reverted already. see https://github.com/apache/kafka/commit/da1ee97f11c1c828a93db37023122b647a5a271e and https://github.com/apache/kafka/commit/64f7a0a300c70b00c0cc357d0a936ea8b42b69fb


 
~~~~

27.

~~~~
Perfect, thanks!
~~~~

28.

~~~~
Since the follower only maintains offsetForMaxTimestamp at the batch level, the listMaxTimestamp API was never implemented correctly. So, technically, there was no regression for listMaxTimestamp. We could just fix this issue in trunk without backporting to the old branch.
~~~~

29.

~~~~
{quote}
Since the follower only maintains offsetForMaxTimestamp at the batch level, the listMaxTimestamp API was never implemented correctly. So, technically, there was no regression for listMaxTimestamp. We could just fix this issue in trunk without backporting to the old branch.
{quote}

I will revert KAFKA-16341 and KAFKA-16342 from 3.7

~~~~

30.

~~~~
see the following link to check the revert from 3.7
https://github.com/apache/kafka/commit/bd5989dd195d42c1608582316367a03b2c78cb11
https://github.com/apache/kafka/commit/fc646f920701b792eb683bacd513a1f20909f6bc
~~~~

31.

~~~~
thanks [~junrao] for pointing this out and sharing the solution, and thanks [~chia7712] [~showuon] for those discussions and revert it for 3.6. 

 
{quote}Since this is a rare operation, paying the decompression overhead is fine.

 

Adding a new field in the batch requires record format change, which is a much bigger effort. For now, the easiest thing is to add a method in Batch to find out offsetOfMaxTimestanp by iterating all records.

Regarding the optimization on the leader side by caching offsetOfMaxTimestanp, we could do it. However, my understanding is that listMaxTimestamp is rare and I am not sure if it's worth the additional complexity.
{quote}
have go through the comments and had a offline discussion with Chia-Ping, I got more context and also feel that we can transfer the workload to listMaxTimestamp when clients fetch this since it's rare. What do you think?  
~~~~

32.

~~~~
{quote}
I got more context and also feel that we can transfer the workload to listMaxTimestamp when clients fetch this since it's rare. What do you think?  
{quote}

yep, we are on the same page. I have filed a PR according to the solution. Please take a look at https://github.com/apache/kafka/pull/15621
~~~~

33.

~~~~
[~chia7712] [~omkreddy] 

>  [~ijuma] Are you worry about the 3.6.2? If so, the fixes are reverted already. see

[https://home.apache.org/~manikumar/kafka-3.6.2-rc2/RELEASE_NOTES.html]

This is my first time commenting on kafka's jira. I apologize if this is an unnecessary question.

The fix for this bug is not mentioned in the release notes of 3.6.2-rc2.

Will this bug not be fixed in 3.6.2 ?
~~~~

34.

~~~~
{quote}
Will this bug not be fixed in 3.6.2 ?
{quote}

yep. As we discussed above, all paths do NOT use same way to find the offset of max timestamp, so it is not a regression of both 3.6 and 3.7. Instead, it is a issue which is existent for a while :) 
~~~~

35.

~~~~
I will update KIP-734 later since the web site has no response ....
~~~~

36.

~~~~
have updated KIP-734
~~~~

---

## KAFKA-16319: Wrong broker destinations for DeleteRecords requests when more than one topic is involved and the topics/partitions are led by different brokers

https://issues.apache.org/jira/browse/KAFKA-16319

JIRA metadata: affects 3.6.0, 3.6.1, 3.7.0; fixed in 3.6.2, 3.7.1, 3.8.0

- `KAFKA-16319@3.6.1`: config 3.6.1, metadata answer **affected** (listed_affected)
- `KAFKA-16319@3.9.0`: config 3.9.0, metadata answer **not_affected** (later_line)

Known Kafka versions mentioned in text: 3.6.1, 3.7, 3.6.0

### Description

~~~~
h2. Context

Kafka streams applications send, time after time, {{DeleteRecords}} requests, via {{org.apache.kafka.streams.processor.internals.TaskManager#maybePurgeCommittedRecords}} method. Such requests may involve more than 1 topic (or partition), and such requests are supposed to be sent to partitions' leaders brokers.
 
h2. Observed behaviour

In case when {{DeleteRecords}} request includes more than one topic (let's say 2 - {{topic1}} and {{{}topic2{}}}), and these topics are led by different brokers (let’s say {{broker1}} and {{broker2}} respectively), the request is sent to only one broker (let’s say {{{}broker1{}}}), leading to partial not_leader_or_follower errors. As not the whole request was successful ({{{}topic1{}}} is fine, but {{topic2}} is not), it gets retried, with the _same_ arguments, to the _same_ broker ({{{}broker1{}}}), meaning the response will be partially faulty again and again. It also may (and does) happen that there is a “mirrored” half-faulty request - in this case, to {{{}broker2{}}}, where {{topic2}} operation is successful, but {{topic1}} operation fails.

Here’s an anonymised logs example from a production system (“direct” and “mirrored” requests, one after another):
{code:java}
[AdminClient clientId=worker-admin]
Sending DeleteRecordsRequestData(topics=[
  DeleteRecordsTopic(
    name='topic1',
    partitions=[DeleteRecordsPartition(partitionIndex=5, offset=88017574)]
    ),
  DeleteRecordsTopic(
    name='topic2',
    partitions=[DeleteRecordsPartition(partitionIndex=5, offset=243841)]
)], timeoutMs=60000)
to broker1:PORT (id: 2 rack: RACK1). // <-- Note the broker, it's broker1
correlationId=42003907, timeoutMs=30000

[AdminClient clientId=worker-admin]
Sending DeleteRecordsRequestData(topics=[
  DeleteRecordsTopic(
    name='topic1',
    partitions=[DeleteRecordsPartition(partitionIndex=5, offset=88017574)]
  ),
  DeleteRecordsTopic(
    name='topic2',
    partitions=[DeleteRecordsPartition(partitionIndex=5, offset=243841)]
)], timeoutMs=60000)
to broker2:9098 (id: 4 rack: RACK2). // <-- Note the broker, here it's broker2
correlationId=42003906, timeoutMs=30000 {code}
Such request results in the following response (in this case, only for the "direct" response):
{code:java}
[AdminClient clientId=worker-admin]
Call(
  callName=deleteRecords(api=DELETE_RECORDS),
  deadlineMs=...,
  tries=..., // Can be hundreds
  nextAllowedTryMs=...)
got response DeleteRecordsResponseData(
  throttleTimeMs=0,
  topics=[
    DeleteRecordsTopicResult(
      name='topic2',
      partitions=[DeleteRecordsPartitionResult(
        partitionIndex=5, lowWatermark=-1, errorCode=6)]), // <-- Note the errorCode 6, which is not_leader_or_follower
    DeleteRecordsTopicResult(
      name='topic1',
      partitions=[DeleteRecordsPartitionResult(
        partitionIndex=5, lowWatermark=..., errorCode=0)]) // <-- Note the errorCode 0, which means the operation was successful
  ]
) {code}
h2. Expected behaviour

{{DeleteRecords}} requests are sent to corresponding partitions' leaders brokers when more than 1 topic/partition is involved and they are led by different brokers.
h2. Notes
 * {_}presumably{_}, introduced in 3.6.1 via [https://github.com/apache/kafka/pull/13760] .
~~~~

### Comments (7)

1.

~~~~
With an AK 3.7 client, I see that the DeleteRecords requests for different leaders are correctly sent to their own respective brokers. So, it's not as simple as just "DeleteRecords is broken in Kafka".
~~~~

2.

~~~~
[~schofielaj] Maybe we're trying a different thing. I've just tried 3.7 client, and still experience the issue:
{code:java}
[AdminClient clientId=...-worker2-admin] Call(callName=deleteRecords(api=DELETE_RECORDS), deadlineMs=1709631680871, tries=64, nextAllowedTryMs=1709631680616) got response DeleteRecordsResponseData(throttleTimeMs=0, topics=[DeleteRecordsTopicResult(name='topic1', partitions=[DeleteRecordsPartitionResult(partitionIndex=5, lowWatermark=-1, errorCode=6)]), DeleteRecordsTopicResult(name='topic2', partitions=[DeleteRecordsPartitionResult(partitionIndex=5, lowWatermark=71227289, errorCode=0)])]) {code}
Note {{errorCode=6}} for {{topic1}} and {{errorCode=0}} for {{{}topic2{}}}.
~~~~

3.

~~~~
[~alexeyasf] How do you get it to do that? Do you have a small test program and instructions for setting up the cluster to make it happen? I'm sure I can fix it if only I can make it fail :) For one thing, I would add a test that fails without the fix and then succeeds when the code has been fixed so having a pointer would be helpful.
~~~~

4.

~~~~
I have reproduced it. Certainly fails like this on 3.6.0.
~~~~

5.

~~~~
??How do you get it to do that? Do you have a small test program and instructions for setting up the cluster to make it happen? I'm sure I can fix it if only I can make it fail :) For one thing, I would add a test that fails without the fix and then succeeds when the code has been fixed so having a pointer would be helpful.??

That's all a great idea, but, unfortunately, no, i haven't yet created a minimalistic test setup.

??I have reproduced it. Certainly fails like this on 3.6.0.??

[~schofielaj] Did you have a chance already to add a minimalistic test for this? If you did / you are on it already, i'd like to avoid duplicated work, but if you're haven't started yet - i can give it a shot 2-3 hours later.
~~~~

6.

~~~~
No worries. My initial assessment was incorrect. The code was broken in 3.6.0 and was still broken in trunk. I've submitted a fix.

Essentially, every broker was being sent every topic-partition, even ones that it didn't lead. So, the kafka-delete-records.sh tool was working because overall the KafkaAdmin.deleteRecords request was working, but the bad error codes were being masked/ignored.
~~~~

7.

~~~~
Great news, thank you very much for quick reaction! (y)
~~~~

---

## KAFKA-16558: Implement HeartbeatRequestState.toStringBase()

https://issues.apache.org/jira/browse/KAFKA-16558

JIRA metadata: affects 3.7.0; fixed in 3.9.0

- `KAFKA-16558@3.7.0`: config 3.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-16558@3.9.0`: config 3.9.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: none

### Description

~~~~
The inner class {{HeartbeatRequestState}} does not override the {{toStringBase()}} method. This affects debugging and troubleshooting consumer issues.
~~~~

### Comments (1)

1.

~~~~
[~brendendeluna] — can you update the status of this Jira to "Patch Available?" Thanks!
~~~~

---

## KAFKA-16606: JBOD support in KRaft does not seem to be gated by the metadata version

https://issues.apache.org/jira/browse/KAFKA-16606

JIRA metadata: affects 3.7.0; fixed in 3.7.1, 3.8.0

- `KAFKA-16606@3.7.0`: config 3.7.0, metadata answer **affected** (listed_affected)
- `KAFKA-16606@3.7.2`: config 3.7.2, metadata answer **not_affected** (later_patch)

Known Kafka versions mentioned in text: 3.7.0, 3.7, 3.6, 3.0, 3.7.1, 3.8.0

### Description

~~~~
JBOD support in KRaft should be supported since Kafka 3.7.0. The Kafka [source code|https://github.com/apache/kafka/blob/1b301b30207ed8fca9f0aea5cf940b0353a1abca/server-common/src/main/java/org/apache/kafka/server/common/MetadataVersion.java#L194-L195] suggests that it is supported with the metadata version {{{}3.7-IV2{}}}. However, it seems to be possible to run KRaft cluster with JBOD even with older metadata versions such as {{{}3.6{}}}. For example, I have a cluster using the {{3.6}} metadata version:
{code:java}
bin/kafka-features.sh --bootstrap-server localhost:9092 describe
Feature: metadata.version       SupportedMinVersion: 3.0-IV1    SupportedMaxVersion: 3.7-IV4    FinalizedVersionLevel: 3.6-IV2  Epoch: 1375 {code}
Yet a KRaft cluster with JBOD seems to run fine:
{code:java}
bin/kafka-log-dirs.sh --bootstrap-server localhost:9092 --describe
Querying brokers for log directories information
Received log directory information from brokers 2000,3000,1000
{"brokers":[{"broker":2000,"logDirs":[{"partitions":[{"partition":"__consumer_offsets-13","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-46","size":0,"offsetLag":0,"isFuture":false},{"partition":"kafka-test-apps-0","size":28560,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-9","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-42","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-21","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-17","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-30","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-26","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-5","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-38","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-1","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-34","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-16","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-45","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-12","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-41","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-24","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-20","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-49","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-0","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-29","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-25","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-8","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-37","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-4","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-33","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-15","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-48","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-11","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-44","size":407136,"offsetLag":0,"isFuture":false},{"partition":"kafka-test-apps-2","size":28560,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-23","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-19","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-32","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-28","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-7","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-40","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-3","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-36","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-47","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-14","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-43","size":0,"offsetLag":0,"isFuture":false},{"partition":"kafka-test-apps-1","size":114240,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-10","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-22","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-18","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-31","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-27","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-39","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-6","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-35","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-2","size":0,"offsetLag":0,"isFuture":false}],"error":null,"logDir":"/var/lib/kafka/data-0/kafka-log2000"}]},{"broker":3000,"logDirs":[{"partitions":[{"partition":"__consumer_offsets-48","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-13","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-11","size":0,"offsetLag":0,"isFuture":false},{"partition":"kafka-test-apps-2","size":28560,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-42","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-21","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-17","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-30","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-26","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-40","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-5","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-3","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-36","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-47","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-14","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-12","size":0,"offsetLag":0,"isFuture":false},{"partition":"kafka-test-apps-1","size":114240,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-41","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-10","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-20","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-18","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-0","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-27","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-39","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-37","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-4","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-2","size":0,"offsetLag":0,"isFuture":false}],"error":null,"logDir":"/var/lib/kafka/data-0/kafka-log3000"},{"partitions":[{"partition":"__consumer_offsets-15","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-46","size":0,"offsetLag":0,"isFuture":false},{"partition":"kafka-test-apps-0","size":28560,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-44","size":407136,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-9","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-23","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-19","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-32","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-28","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-7","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-38","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-1","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-34","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-16","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-45","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-43","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-24","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-22","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-49","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-31","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-29","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-25","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-8","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-6","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-35","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-33","size":0,"offsetLag":0,"isFuture":false}],"error":null,"logDir":"/var/lib/kafka/data-1/kafka-log3000"}]},{"broker":1000,"logDirs":[{"partitions":[{"partition":"__consumer_offsets-13","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-46","size":0,"offsetLag":0,"isFuture":false},{"partition":"kafka-test-apps-0","size":28560,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-9","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-42","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-21","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-17","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-30","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-26","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-5","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-38","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-1","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-34","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-16","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-45","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-12","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-41","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-24","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-20","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-49","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-0","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-29","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-25","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-8","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-37","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-4","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-33","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-15","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-48","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-11","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-44","size":407136,"offsetLag":0,"isFuture":false},{"partition":"kafka-test-apps-2","size":28560,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-23","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-19","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-32","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-28","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-7","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-40","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-3","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-36","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-47","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-14","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-43","size":0,"offsetLag":0,"isFuture":false},{"partition":"kafka-test-apps-1","size":114240,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-10","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-22","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-18","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-31","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-27","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-39","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-6","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-35","size":0,"offsetLag":0,"isFuture":false},{"partition":"__consumer_offsets-2","size":0,"offsetLag":0,"isFuture":false}],"error":null,"logDir":"/var/lib/kafka/data-0/kafka-log1000"}]}],"version":1} {code}
Is this expected? Or is it a bug? If it is a bug, can it still be fixed given there might be already users running Kafka 3.7.0 with JBOD and fixing the gating of JBOD in a later version will actually break their clusters?
~~~~

### Comments (8)

1.

~~~~
cc [~soarez] 
~~~~

2.

~~~~
Thanks for bringing this to my attention [~mimaison].

Hi [~scholzj] , thanks for pointing this out. I think there's some confusion here with a JBOD configuration being +allowed+ vs being +supported+ in KRaft.

In terms of just reading and writing data to multiple log directories, as long as those direcories are always available, there's nothing special about KRaft that would require changes compared with ZK mode. What is enabled with 3.7 is the handling of failed log directories. You'll find that partitions don't get new leaders elected – becoming indefinitely unavailable – if the log directory for the leader replica fails but the broker stays alive.

If a single directory is configured and it becomes unavailable the broker shuts down, as there is no point in continuing to run without access to storage. When it shuts down the controller becomes aware of that – via an ephemeral znode in ZK mode, or via missing hearbeats in KRaft – and it will re-elect leaders for partitions that were led by the broker. When multiple directories are configured, it is critical to have a separate mechanism to let the controller know there is a partial failure – the broker is still alive and operational on the remaining log dirs, but any partitions on the directory that failed need a leadership and ISR update.

In ZK mode that was handled by notifying the controller via a znode, so a an alternative solution was required for KRaft. You can find the details in [KIP-858|https://cwiki.apache.org/confluence/display/KAFKA/KIP-858%3A+Handle+JBOD+broker+disk+failure+in+KRaft].

Let me know if that makes sense.

 
~~~~

3.

~~~~
[~soarez] That sounds like without using the 3.7-IV2 metadata JBOD in Kraft works fine until it fails and then it might cause problems. So I wonder if it would have been better to protect the users from that situation.

But it sounds like it was an intentional decision. And as I said, changing it now might be anyway a bit tricky as it might break someone's cluster after upgrading to 3.7.1 / 3.8.0. So I guess it sounds good as it is and I will close this. Thanks for the explanation.
~~~~

4.

~~~~
That's right [~scholzj] . When KIP-858 started, the documentation was already explicit about JBOD support being one of the missing features in KRaft, but the configuration was already allowed, so it didn't seem right to change it at the time, but in hindsight maybe that would've been a better decision.
~~~~

5.

~~~~
To me that kind of looks like a bug. Previously JBOD was not supported with KRaft so it was a big deal that it did not quite work. As we're approaching JBOD being production ready, we should ease the rough edges and avoid allowing weird unsupported configurations. 

As JBOD is not production ready, would we really break anyone's cluster if we prevented using multiple log dirs with KRaft and the version set as < 3.7?  I understand some people may disagree but I wonder if it's a discussion worth having. 
~~~~

6.

~~~~
I'm inclined to agree, I think we can still do this. We are already checking that the MV is high enough before allowing migration from JBOD ZK.

Even if someone is already running KRaft in JBOD this change could still be useful: Preventing the broker from starting could be disruptive, but that's better than having an outage at a random moment in the future.

I'll re-open this and submit a PR.
~~~~

7.

~~~~
Ok, thanks [~soarez] and [~mimaison].
~~~~

8.

~~~~
[~scholzj], [~mimaison]  – this isn't super straightforward, we should consider at least the implications of:
 # Revalidating configuration once the effective {{MetadataVersion}} (MV) is discovered (we don't know of it before reading the metadata topic)
 # Shutting down the broker vs just logging at {{ERROR}} or {{WARN}} level if mulptiple dirs are configured without JBOD support in the MV

Please take a look at the [PR|https://github.com/apache/kafka/pull/15834] and let me know what you think. Thanks
~~~~

---

## KAFKA-16890: Failing to build aux state on broker failover

https://issues.apache.org/jira/browse/KAFKA-16890

JIRA metadata: affects 3.7.0, 3.7.1; fixed in 3.8.0

- `KAFKA-16890@3.7.1`: config 3.7.1, metadata answer **affected** (listed_affected)
- `KAFKA-16890@3.8.1`: config 3.8.1, metadata answer **not_affected** (later_patch)

Known Kafka versions mentioned in text: none

### Description

~~~~
We have clusters where we replace machines often falling into a state where we keep having "Error building remote log auxiliary state for loadtest_topic-22" and the partition being under-replicated until the leader is manually restarted. 

Looking into a specific case, here is what we observed in __remote_log_metadata topic:


{code:java}
 
partition: 29, offset: 183593, value: RemoteLogSegmentMetadata{remoteLogSegmentId=RemoteLogSegmentId{topicIdPartition=ClnIeN0MQsi_d4FAOFKaDA:loadtest_topic-22, id=GZeRTXLMSNe2BQjRXkg6hQ}, startOffset=10823, endOffset=11536, brokerId=10013, maxTimestampMs=1715774588597, eventTimestampMs=1715781657604, segmentLeaderEpochs={125=10823, 126=10968, 128=11047, 130=11048, 131=11324, 133=11442, 134=11443, 135=11445, 136=11521, 137=11533, 139=11535}, segmentSizeInBytes=704895, customMetadata=Optional.empty, state=COPY_SEGMENT_STARTED}
partition: 29, offset: 183594, value: RemoteLogSegmentMetadataUpdate{remoteLogSegmentId=RemoteLogSegmentId{topicIdPartition=ClnIeN0MQsi_d4FAOFKaDA:loadtest_topic-22, id=GZeRTXLMSNe2BQjRXkg6hQ}, customMetadata=Optional.empty, state=COPY_SEGMENT_FINISHED, eventTimestampMs=1715781658183, brokerId=10013}
partition: 29, offset: 183669, value: RemoteLogSegmentMetadata{remoteLogSegmentId=RemoteLogSegmentId{topicIdPartition=ClnIeN0MQsi_d4FAOFKaDA:loadtest_topic-22, id=L1TYzx0lQkagRIF86Kp0QQ}, startOffset=10823, endOffset=11544, brokerId=10008, maxTimestampMs=1715781445270, eventTimestampMs=1715782717593, segmentLeaderEpochs={125=10823, 126=10968, 128=11047, 130=11048, 131=11324, 133=11442, 134=11443, 135=11445, 136=11521, 137=11533, 139=11535, 140=11537, 142=11543}, segmentSizeInBytes=713088, customMetadata=Optional.empty, state=COPY_SEGMENT_STARTED}
partition: 29, offset: 183670, value: RemoteLogSegmentMetadataUpdate{remoteLogSegmentId=RemoteLogSegmentId{topicIdPartition=ClnIeN0MQsi_d4FAOFKaDA:loadtest_topic-22, id=L1TYzx0lQkagRIF86Kp0QQ}, customMetadata=Optional.empty, state=COPY_SEGMENT_FINISHED, eventTimestampMs=1715782718370, brokerId=10008}
partition: 29, offset: 186215, value: RemoteLogSegmentMetadataUpdate{remoteLogSegmentId=RemoteLogSegmentId{topicIdPartition=ClnIeN0MQsi_d4FAOFKaDA:loadtest_topic-22, id=L1TYzx0lQkagRIF86Kp0QQ}, customMetadata=Optional.empty, state=DELETE_SEGMENT_STARTED, eventTimestampMs=1715867874617, brokerId=10008}
partition: 29, offset: 186216, value: RemoteLogSegmentMetadataUpdate{remoteLogSegmentId=RemoteLogSegmentId{topicIdPartition=ClnIeN0MQsi_d4FAOFKaDA:loadtest_topic-22, id=L1TYzx0lQkagRIF86Kp0QQ}, customMetadata=Optional.empty, state=DELETE_SEGMENT_FINISHED, eventTimestampMs=1715867874725, brokerId=10008}
partition: 29, offset: 186217, value: RemoteLogSegmentMetadataUpdate{remoteLogSegmentId=RemoteLogSegmentId{topicIdPartition=ClnIeN0MQsi_d4FAOFKaDA:loadtest_topic-22, id=GZeRTXLMSNe2BQjRXkg6hQ}, customMetadata=Optional.empty, state=DELETE_SEGMENT_STARTED, eventTimestampMs=1715867874729, brokerId=10008}
partition: 29, offset: 186218, value: RemoteLogSegmentMetadataUpdate{remoteLogSegmentId=RemoteLogSegmentId{topicIdPartition=ClnIeN0MQsi_d4FAOFKaDA:loadtest_topic-22, id=GZeRTXLMSNe2BQjRXkg6hQ}, customMetadata=Optional.empty, state=DELETE_SEGMENT_FINISHED, eventTimestampMs=1715867874817, brokerId=10008}
{code}
 

It seems that at the time the leader is restarted (10013), a second copy of the same segment is tiered by the new leader (10008). Interestingly the segment doesn't have the same end offset, which is concerning. 

Then the follower sees the following error repeatedly until the leader is restarted: 



 
{code:java}
[2024-05-17 20:46:42,133] DEBUG [ReplicaFetcher replicaId=10013, leaderId=10008, fetcherId=0] Handling errors in processFetchRequest for partitions HashSet(loadtest_topic-22) (kafka.server.ReplicaFetcherThread)
[2024-05-17 20:46:43,174] DEBUG [ReplicaFetcher replicaId=10013, leaderId=10008, fetcherId=0] Received error OFFSET_MOVED_TO_TIERED_STORAGE, at fetch offset: 11537, topic-partition: loadtest_topic-22 (kafka.server.ReplicaFetcherThread)
[2024-05-17 20:46:43,175] ERROR [ReplicaFetcher replicaId=10013, leaderId=10008, fetcherId=0] Error building remote log auxiliary state for loadtest_topic-22 (kafka.server.ReplicaFetcherThread)
org.apache.kafka.server.log.remote.storage.RemoteStorageException: Couldn't build the state from remote store for partition: loadtest_topic-22, currentLeaderEpoch: 153, leaderLocalLogStartOffset: 11545, leaderLogStartOffset: 11537, epoch: 142as the previous remote log segment metadata was not found
{code}
The follower is trying to fetch from 11537 and gets OFFSET_MOVED_TO_TIERED_STORAGE . Then when the follower retries, it still thinks it needs to fetch from 11537 . There is no data in S3, so the correct leaderLogStartOffset should be 11545 .  I'm not sure yet if its intentional that there can be two copies of the same segment that are different uploaded to S3 or if the segments were just deleted in the wrong order, but that is what ultimately caused the leaderLogStartOffset to be set incorrectly.
~~~~

---

## KAFKA-16905: Thread block in describe topics API in Admin Client

https://issues.apache.org/jira/browse/KAFKA-16905

JIRA metadata: affects 3.8.0, 3.9.0; fixed in 3.8.0

- `KAFKA-16905@3.9.0`: config 3.9.0, metadata answer **affected** (listed_affected)
- `KAFKA-16905@3.7.2`: config 3.7.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 3.8.0, 3.8

### Description

~~~~
The threads blocks while running admin client's descirbe topics API.

 
{code:java}
"kafka-admin-client-thread | adminclient-3" #114 daemon prio=5 os_prio=31 cpu=6.57ms elapsed=417.17s tid=0x00000001364fc200 nid=0x13403 waiting on condition  [0x00000002bb419000]
   java.lang.Thread.State: WAITING (parking)
	at jdk.internal.misc.Unsafe.park(java.base@17.0.7/Native Method)
	- parking to wait for  <0x0000000773804828> (a java.util.concurrent.CompletableFuture$Signaller)
	at java.util.concurrent.locks.LockSupport.park(java.base@17.0.7/LockSupport.java:211)
	at java.util.concurrent.CompletableFuture$Signaller.block(java.base@17.0.7/CompletableFuture.java:1864)
	at java.util.concurrent.ForkJoinPool.unmanagedBlock(java.base@17.0.7/ForkJoinPool.java:3463)
	at java.util.concurrent.ForkJoinPool.managedBlock(java.base@17.0.7/ForkJoinPool.java:3434)
	at java.util.concurrent.CompletableFuture.waitingGet(java.base@17.0.7/CompletableFuture.java:1898)
	at java.util.concurrent.CompletableFuture.get(java.base@17.0.7/CompletableFuture.java:2072)
	at org.apache.kafka.common.internals.KafkaFutureImpl.get(KafkaFutureImpl.java:165)
	at org.apache.kafka.clients.admin.KafkaAdminClient.handleDescribeTopicsByNamesWithDescribeTopicPartitionsApi(KafkaAdminClient.java:2324)
	at org.apache.kafka.clients.admin.KafkaAdminClient.describeTopics(KafkaAdminClient.java:2122)
	at org.apache.kafka.clients.admin.Admin.describeTopics(Admin.java:311)
	at io.confluent.kafkarest.controllers.TopicManagerImpl.describeTopics(TopicManagerImpl.java:155)
	at io.confluent.kafkarest.controllers.TopicManagerImpl.lambda$listTopics$2(TopicManagerImpl.java:76)
	at io.confluent.kafkarest.controllers.TopicManagerImpl$$Lambda$1925/0x0000000800891448.apply(Unknown Source)
	at java.util.concurrent.CompletableFuture$UniCompose.tryFire(java.base@17.0.7/CompletableFuture.java:1150)
	at java.util.concurrent.CompletableFuture.postComplete(java.base@17.0.7/CompletableFuture.java:510)
	at java.util.concurrent.CompletableFuture.complete(java.base@17.0.7/CompletableFuture.java:2147)
	at io.confluent.kafkarest.common.KafkaFutures.lambda$toCompletableFuture$0(KafkaFutures.java:45)
	at io.confluent.kafkarest.common.KafkaFutures$$Lambda$1909/0x0000000800897528.accept(Unknown Source)
	at org.apache.kafka.common.internals.KafkaFutureImpl.lambda$whenComplete$2(KafkaFutureImpl.java:107)
	at org.apache.kafka.common.internals.KafkaFutureImpl$$Lambda$1910/0x0000000800897750.accept(Unknown Source)
	at java.util.concurrent.CompletableFuture.uniWhenComplete(java.base@17.0.7/CompletableFuture.java:863)
	at java.util.concurrent.CompletableFuture$UniWhenComplete.tryFire(java.base@17.0.7/CompletableFuture.java:841)
	at java.util.concurrent.CompletableFuture.postComplete(java.base@17.0.7/CompletableFuture.java:510)
	at java.util.concurrent.CompletableFuture.complete(java.base@17.0.7/CompletableFuture.java:2147)
	at org.apache.kafka.common.internals.KafkaCompletableFuture.kafkaComplete(KafkaCompletableFuture.java:39)
	at org.apache.kafka.common.internals.KafkaFutureImpl.complete(KafkaFutureImpl.java:122)
	at org.apache.kafka.clients.admin.KafkaAdminClient$4.handleResponse(KafkaAdminClient.java:2106)
	at org.apache.kafka.clients.admin.KafkaAdminClient$AdminClientRunnable.handleResponses(KafkaAdminClient.java:1370)
	at org.apache.kafka.clients.admin.KafkaAdminClient$AdminClientRunnable.processRequests(KafkaAdminClient.java:1523)
	at org.apache.kafka.clients.admin.KafkaAdminClient$AdminClientRunnable.run(KafkaAdminClient.java:1446)
	at java.lang.Thread.run(java.base@17.0.7/Thread.java:833) {code}
~~~~

### Comments (3)

1.

~~~~
I'm hitting this issue with 3.8.0 RC0. We should backport this fix to the 3.8 branch. Cherry-picking [https://github.com/apache/kafka/commit/c01279b92acefd9135089588319910bac79bfd4c] fixes the issue.
~~~~

2.

~~~~
Please include this follow-up fix https://github.com/apache/kafka/commit/96036aee855ba0ec1d562904636ea0ff433bce7f 


~~~~

3.

~~~~
Backport PR can be found here: https://github.com/apache/kafka/pull/16593/files
~~~~

---

## KAFKA-16986: After upgrading to Kafka 3.4.1, the producer constantly produces logs related to topicId changes

https://issues.apache.org/jira/browse/KAFKA-16986

JIRA metadata: affects 3.0.1, 3.6.1; fixed in 3.7.0

- `KAFKA-16986@3.6.1`: config 3.6.1, metadata answer **affected** (listed_affected)
- `KAFKA-16986@3.7.0`: config 3.7.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 3.4.1, 2.7.0, 3.6.1, 3.0.1, 0.8, 3.5, 3.5.0, 2.7, 2.8, 3.6, 3.7

### Description

~~~~
When updating the Kafka broker from version 2.7.0 to 3.4.1, we noticed that the applications began to log the message "{*}Resetting the last seen epoch of partition PAYMENTS-0 to 0 since the associated topicId changed from null to szRLmiAiTs8Y0nI8b3Wz1Q{*}" in a very constant, from what I understand this behavior is not expected because the topic was not deleted and recreated so it should simply use the cached data and not go through this client log line.

We have some applications with around 15 topics and 40 partitions which means around 600 log lines when metadata updates occur

The main thing for me is to know if this could indicate a problem or if I can simply change the log level of the org.apache.kafka.clients.Metadata class to warn without worries

 

There are other reports of the same behavior like this:  [https://stackoverflow.com/questions/74652231/apache-kafka-resetting-the-last-seen-epoch-of-partition-why]

 

*Some log occurrences over an interval of about 7 hours, each block refers to an instance of the application in kubernetes*

 

!image.png!

*My scenario:*

*Application:*
 - Java: 21

 - Client: 3.6.1, also tested on 3.0.1 and has the same behavior

*Broker:*
 - Cluster running on Kubernetes with the bitnami/kafka:3.4.1-debian-11-r52 image

 

*Producer Config*

 
    acks = -1
    auto.include.jmx.reporter = true
    batch.size = 16384
    bootstrap.servers = [server:9092]
    buffer.memory = 33554432
    client.dns.lookup = use_all_dns_ips
    client.id = producer-1
    compression.type = gzip
    connections.max.idle.ms = 540000
    delivery.timeout.ms = 30000
    enable.idempotence = true
    interceptor.classes = []
    key.serializer = class org.apache.kafka.common.serialization.ByteArraySerializer
    linger.ms = 0
    max.block.ms = 60000
    max.in.flight.requests.per.connection = 1
    max.request.size = 1048576
    metadata.max.age.ms = 300000
    metadata.max.idle.ms = 300000
    metric.reporters = []
    metrics.num.samples = 2
    metrics.recording.level = INFO
    metrics.sample.window.ms = 30000
    partitioner.adaptive.partitioning.enable = true
    partitioner.availability.timeout.ms = 0
    partitioner.class = null
    partitioner.ignore.keys = false
    receive.buffer.bytes = 32768
    reconnect.backoff.max.ms = 1000
    reconnect.backoff.ms = 50
    request.timeout.ms = 30000
    retries = 3
    retry.backoff.ms = 100
    sasl.client.callback.handler.class = null
    sasl.jaas.config = [hidden]
    sasl.kerberos.kinit.cmd = /usr/bin/kinit
    sasl.kerberos.min.time.before.relogin = 60000
    sasl.kerberos.service.name = null
    sasl.kerberos.ticket.renew.jitter = 0.05
    sasl.kerberos.ticket.renew.window.factor = 0.8
    sasl.login.callback.handler.class = null
    sasl.login.class = null
    sasl.login.connect.timeout.ms = null
    sasl.login.read.timeout.ms = null
    sasl.login.refresh.buffer.seconds = 300
    sasl.login.refresh.min.period.seconds = 60
    sasl.login.refresh.window.factor = 0.8
    sasl.login.refresh.window.jitter = 0.05
    sasl.login.retry.backoff.max.ms = 10000
    sasl.login.retry.backoff.ms = 100
    sasl.mechanism = PLAIN
    sasl.oauthbearer.clock.skew.seconds = 30
    sasl.oauthbearer.expected.audience = null
    sasl.oauthbearer.expected.issuer = null
    sasl.oauthbearer.jwks.endpoint.refresh.ms = 3600000
    sasl.oauthbearer.jwks.endpoint.retry.backoff.max.ms = 10000
    sasl.oauthbearer.jwks.endpoint.retry.backoff.ms = 100
    sasl.oauthbearer.jwks.endpoint.url = null
    sasl.oauthbearer.scope.claim.name = scope
    sasl.oauthbearer.sub.claim.name = sub
    sasl.oauthbearer.token.endpoint.url = null
    security.protocol = SASL_PLAINTEXT
    security.providers = null
    send.buffer.bytes = 131072
    socket.connection.setup.timeout.max.ms = 30000
    socket.connection.setup.timeout.ms = 10000
    ssl.cipher.suites = null
    ssl.enabled.protocols = [TLSv1.2, TLSv1.3]
    ssl.endpoint.identification.algorithm = https
    ssl.engine.factory.class = null
    ssl.key.password = null
    ssl.keymanager.algorithm = SunX509
    ssl.keystore.certificate.chain = null
    ssl.keystore.key = null
    ssl.keystore.location = null
    ssl.keystore.password = null
    ssl.keystore.type = JKS
    ssl.protocol = TLSv1.3
    ssl.provider = null
    ssl.secure.random.implementation = null
    ssl.trustmanager.algorithm = PKIX
    ssl.truststore.certificates = null
    ssl.truststore.location = null
    ssl.truststore.password = null
    ssl.truststore.type = JKS
    transaction.timeout.ms = 60000
    transactional.id = null
    value.serializer = class org.apache.kafka.common.serialization.ByteArraySerializer
 

If you need any more details, please let me know.
~~~~

### Comments (20)

1.

~~~~
Hey there, this has been fixed for versions > 3.5 [https://github.com/apache/kafka/commit/6d9d65e6664153f8a7557ec31b5983eb0ac26782] where it should become a debug level log

It doesn't indicate a problem. If you don't wish to upgrade, you can reduce the log level.
~~~~

2.

~~~~
[~jolshan] I have already updated my application to client version 3.6.1 and the log remains. In the commit that sent the indicated section it remains as info, will this be changed?

 

[https://github.com/apache/kafka/commit/6d9d65e6664153f8a7557ec31b5983eb0ac26782#diff-97c2911e6e1b97ed9b3c4e76531a321d8ea1fc6aa2c727c27b0a5e0ced893a2cR408]
~~~~

3.

~~~~
Hmmm. So the earlier code block should be catching the common case of client startup where we saw this log spam. (current epoch is null).

 

I guess in the upgrade case, the client is alive and you won't have current epoch as null. This should only happen on the client during the upgrade. Once the upgrade is complete you shouldn't see this error again. I don't know if it makes sense to change this case since it is a legitimate resetting of the epoch on this upgrade but I do see the argument for the log spam being annoying. 

Is it sufficient that this should not be expected after the upgrade? (And let me know if it is seen after the upgrade is fully completed.)
~~~~

4.

~~~~
[~jolshan] The only problem I currently see is the log, I took a look and actually many of our applications log this message and this pollutes the logs from time to time, I don't know exactly the process that triggers this log, but it is displayed several times during the pod life cycle not only at startup, the print I added to the issue shows this, for the same topic and the same partition there are several logs at different times in the same pod, without restarts or anything like that and I think it's important to emphasize that throughout In the life cycle of these applications we only have one producer instance that remains the same throughout the life of the pod. I even validated the code of our applications to check that there wasn't a situation where the producer kept being destroyed and created again.

 

I will leave below the occurrences in the log of the same pod that has been operating for 2 days: https://pastecode.io/s/zn1u118d

 
~~~~

5.

~~~~
To be clear, this will be a thing that pollutes the log from time to time on versions older than 3.5. 

If it is happening not just on upgrade on version 3.5 or higher, please confirm and I will look further.
~~~~

6.

~~~~
[~jolshan] The logs in the previous comments were collected from a client version 3.6.1 and the broker 3.4.1, when you refer to 3.5.0 I believe it is from the client and therefore the one I am using is in a higher version

Logs about client startup containing the version: 

 

2024-06-17 08:23:50,376 [main] INFO  o.a.k.clients.producer.KafkaProducer [] : [Producer clientId=producer-1] Instantiated an idempotent producer.
2024-06-17 08:23:50,387 [main] INFO  o.a.kafka.common.utils.AppInfoParser [] : Kafka version: 3.6.1
2024-06-17 08:23:50,387 [main] INFO  o.a.kafka.common.utils.AppInfoParser [] : Kafka commitId: 5e3c2b738d253ff5
2024-06-17 08:23:50,387 [main] INFO  o.a.kafka.common.utils.AppInfoParser [] : Kafka startTimeMs: 1718623430387

 

I added the producer settings we are using in the description, thanks for the help
~~~~

7.

~~~~
Thanks for clarifying. I will take a look. 
~~~~

8.

~~~~
I haven't forgotten about this! Just working on some blocker bugs these past few days. I will try to take a look today and if not, early next week.
~~~~

9.

~~~~
[~jolshan] No problem! Thanks for the update.
~~~~

10.

~~~~
[~viniciusxyz] just curious – this is a ZK cluster I assume since the upgrade was from an earlier version? And I'm curious if we have metadata responses for these producers (request logging) 

I am also looking at a few more avenues on my end. 

It looks like somehow the topic ID is being removed from the producer's metadata cache so it looks like the topic ID in a metadata response is the first instance of the topic ID. We included this so in the upgrade from > 2.7 -> < 2.8 we would do the epoch reset correctly. It shouldn't trigger as often as your logs show though. Checking the client code to see if there was some assumption made about retaining this ID. 
~~~~

11.

~~~~
[~jolshan] That's right, it's a cluster that currently has Kafka 3.4.1 and Zookeeper 3.8.3. To collect this metadata from the producer, just set the log as debug and send it to you or do I need to do this in some other way?
~~~~

12.

~~~~
I was thinking maybe the broker request logs could be turned on as I believe that will show the metadata response to the producer. 
That config is in kafka/config/log4j.properties 

Change to DEBUG or TRACE to enable request logging
log4j.logger.kafka.request.logger=WARN, requestAppender
 
^ change this to debug.
~~~~

13.

~~~~
[~jolshan] We managed to make this change, but in our development broker we have around 2500 partitions and countless topics and consumers, so the log was a mess and I was only able to leave it active for a few hours to avoid crashing our log collection tools during this period. Unfortunately I couldn't find any application with the behavior I reported, I'll have to start a locally isolated Kafka to evaluate this behavior and this could end up taking a while :/

 

I was able to verify that the logs are present in our approval and production environment as well, that is, Kafka installations completely isolated from each other that present the same log that I reported and in the same scenario where multiple times for the same topic and partition there is the message " associated topicId changed from null to xxxx"
~~~~

14.

~~~~
Hey, thanks for taking a look at it. It is very strange that the same producer would log this error more than once since it means somehow the producer got metadata with a topic ID, updated it (first instance of message) and then somehow loses it again and upon getting it again logs again. If a producer is writing to the same topic consistently, I'm not sure how it could lose the topic ID in the metadata unless some brokers have metadata containing the topic ID and others do not. 
~~~~

15.

~~~~
I guess you may see this as we expire metadata after metadata.max.idle.ms (= 300000). I wonder if that's what is happening.
~~~~

16.

~~~~
[~jolshan] This doesn't seem to be the case, I changed this value to 30000 and sent some 40-second messages every 40 seconds and the message doesn't appear in this case
~~~~

17.

~~~~
In the 3.6 branch, there is a bug while merging topic ids from a partial metadata update: [https://github.com/apache/kafka/blob/35f0eeb2b07cabba0287b1a83a124abfb15e6745/clients/src/main/java/org/apache/kafka/clients/MetadataSnapshot.java#L172.]  We only retain topic ids from the current partial response. Hence the next full metadata update thinks the topic id was previously null and is being updated. This has been fixed in 3.7  and trunk:[https://github.com/apache/kafka/blob/0b11971f2c94f7aadc3fab2c51d94642065a72e5/clients/src/main/java/org/apache/kafka/clients/MetadataSnapshot.java#L179|https://github.com/apache/kafka/blob/0b11971f2c94f7aadc3fab2c51d94642065a72e5/clients/src/main/java/org/apache/kafka/clients/MetadataSnapshot.java#L179_]. The fix seems to be from this commit: [https://github.com/apache/kafka/commit/a9565a799f3f87eb1d932b114dde7373748551ac] .
~~~~

18.

~~~~
[~rsivaram] Thank you for the answer!

 

Could you tell me how critical the update is, please? Is this something that could somehow affect message production performance?

 

Another point would the update only be for the correct client?
~~~~

19.

~~~~
I believe the main issue is just excessive logging.

And yes this would just be a client update. 

Thanks [~rsivaram] for finding this!
~~~~

20.

~~~~
[~jolshan] [~rsivaram] Very grateful for the team's help! I'll close the issue for now and if I find anything else strange I'll report back.
~~~~

---

## KAFKA-17455: `TaskCorruptedException` After Client Quota Throttling

https://issues.apache.org/jira/browse/KAFKA-17455

JIRA metadata: affects 3.8.0; fixed in 3.8.2, 3.9.1, 4.0.0

- `KAFKA-17455@3.8.0`: config 3.8.0, metadata answer **affected** (listed_affected)
- `KAFKA-17455@3.9.2`: config 3.9.2, metadata answer **not_affected** (later_patch)

Known Kafka versions mentioned in text: none

### Description

~~~~
When running a Kafka Streams EOS app that goes slightly above a configured user quota, we can reliably reproduce `TaskCorruptedException`s after throttling. This is the case even with an application that goes only 5-10% above the configured quota.

 

The root cause is a `TimeoutException` encountered in the `TaskExecutor.commitOffsetsOrTransaction`.

 

Stacktrace provided below:

 

```

19:45:28 ERROR [KAFKA] TaskExecutor - stream-thread [basic-tls-0-core-StreamThread-2] Committing task(s) 1_2 failed. org.apache.kafka.common.errors.TimeoutException: Timeout expired after 60000ms while awaiting AddOffsetsToTxn 19:45:28 WARN [KAFKA] StreamThread - stream-thread [basic-tls-0-core-StreamThread-2] Detected the states of tasks [1_2] are corrupted. Will close the task as dirty and re-create and bootstrap from scratch. org.apache.kafka.streams.errors.TaskCorruptedException: Tasks [1_2] are corrupted and hence need to be re-initialized at org.apache.kafka.streams.processor.internals.TaskExecutor.commitOffsetsOrTransaction(TaskExecutor.java:249) ~[server.jar:?] at org.apache.kafka.streams.processor.internals.TaskExecutor.commitTasksAndMaybeUpdateCommittableOffsets(TaskExecutor.java:154) ~[server.jar:?] at org.apache.kafka.streams.processor.internals.TaskManager.commitTasksAndMaybeUpdateCommittableOffsets(TaskManager.java:1915) ~[server.jar:?] at org.apache.kafka.streams.processor.internals.TaskManager.commit(TaskManager.java:1882) ~[server.jar:?] at org.apache.kafka.streams.processor.internals.StreamThread.maybeCommit(StreamThread.java:1384) ~[server.jar:?] at org.apache.kafka.streams.processor.internals.StreamThread.runOnceWithoutProcessingThreads(StreamThread.java:1033) ~[server.jar:?] at org.apache.kafka.streams.processor.internals.StreamThread.runLoop(StreamThread.java:711) [server.jar:?] at org.apache.kafka.streams.processor.internals.StreamThread.run(StreamThread.java:670) [server.jar:?]

```
~~~~

### Comments (7)

1.

~~~~
This is probably a problem in the Producer rather than with Streams itself.


I am confused at what causes this. The Kafka Quota documentation states:

> Byte-rate and thread utilization are measured over multiple small windows (e.g. 30 windows of 1 second each) in order to detect and correct quota violations quickly. Typically, having large measurement windows (for e.g. 10 windows of 30 seconds each) leads to large bursts of traffic followed by long delays which is not great in terms of user experience.

Our application was configured with `commit.interval.ms` of 100ms, and a producer timeout of 60 seconds (you can see that from the stacktrace).

Once the broker started throttling, the Streams Commit seemed to hang.

 

I am confused as to _why_ this would happen, given that:
 * Our app only exceeded quota by 5-10%
 * Quota enforcement is supposedly gradual according to the quota enforcement docs
 * We configured Streams to commit every 100ms, which implies that the producer send buffer also flushes every 100ms, so the quota should be experienced gradually.
 * The producer request timeout was 60 seconds. Given the `TimeoutException` it means that a 60-second timeout was exhausted. This is not likely due to normal throttling given how we were just barely over the quota.

This leads me to think there's a bug in the retries or throttling mechanism on the producer methods for committing transactions.

 

cc [~eduwerc]  and [~mjsax] 
~~~~

2.

~~~~
Hi [~coltmcnealy-lh]. Thanks for bringing this up. Could you elaborate a bit more on the quota that you use? For instance, are you talking about bandwidth quotas or request quotas? Have you tried to run the application with debug level logs? It may be interesting to see the lifecycle of that request.
~~~~

3.

~~~~
Thanks, David. It was a Producer Byte Rate quota. Let me rebuild and run with debug logs; I'll post it here tonight.
~~~~

4.

~~~~
Hi [~dajac] — here are the logs. I noticed that the app started stalling at 5:04:23, and exactly one minute later (5:05:23) we got this log:

```

05:05:23 ERROR [KAFKA] TaskExecutor - stream-thread [basic-tls-0-core-StreamThread-2] Committing task(s) 1_3, 1_9 failed.

```

Debug logs ended up being about 42 MB and I was unable to upload them to JIRA, so I sent them to you over slack.
~~~~

5.

~~~~
We were able to root cause the issue based on logs share by [~coltmcnealy-lh] privately. Posting my analysis here for the record.

In the logs, I see the following two entries:

1.
{code:java}
17:21:09 [30mTRACE[m [KAFKA] TransactionManager - [Producer clientId=my-cluster-1-core-StreamThread-1-producer, transactionalId=my-cluster-core-00000001-0000-0000-0000-000000000000-1] Request AddOffsetsToTxnRequestData(transactionalId='my-cluster-core-00000001-0000-0000-0000-000000000000-1', producerId=2, producerEpoch=32, groupId='my-cluster-core') dequeued for sending{code}

2.
{code:java}
17:22:09 [36mDEBUG[m [KAFKA] Sender - [Producer clientId=my-cluster-1-core-StreamThread-1-producer, transactionalId=my-cluster-core-00000001-0000-0000-0000-000000000000-1] Sending transactional request AddOffsetsToTxnRequestData(transactionalId='my-cluster-core-00000001-0000-0000-0000-000000000000-1', producerId=2, producerEpoch=32, groupId='my-cluster-core') to node localhost:9092 (id: 1 rack: null) with correlation ID 360{code}
Here is the code between those two log lines:
{code:java}
        TransactionManager.TxnRequestHandler nextRequestHandler = transactionManager.nextRequest(accumulator.hasIncomplete());
        if (nextRequestHandler == null)
            return false;
        AbstractRequest.Builder<?> requestBuilder = nextRequestHandler.requestBuilder();
        Node targetNode = null;
        try {
            FindCoordinatorRequest.CoordinatorType coordinatorType = nextRequestHandler.coordinatorType();
            targetNode = coordinatorType != null ?
                    transactionManager.coordinator(coordinatorType) :
                    client.leastLoadedNode(time.milliseconds()).node();
            if (targetNode != null) {
                if (!awaitNodeReady(targetNode, coordinatorType)) {
                    log.trace("Target node {} not ready within request timeout, will retry when node is ready.", targetNode);
                    maybeFindCoordinatorAndRetry(nextRequestHandler);
                    return true;
                }
            } else if (coordinatorType != null) {
                log.trace("Coordinator not known for {}, will retry {} after finding coordinator.", coordinatorType, requestBuilder.apiKey());
                maybeFindCoordinatorAndRetry(nextRequestHandler);
                return true;
            } else {
                log.trace("No nodes available to send requests, will poll and retry when until a node is ready.");
                transactionManager.retry(nextRequestHandler);
                client.poll(retryBackoffMs, time.milliseconds());
                return true;
            }
            if (nextRequestHandler.isRetry())
                time.sleep(nextRequestHandler.retryBackoffMs());
            long currentTimeMs = time.milliseconds();
            ClientRequest clientRequest = client.newClientRequest(targetNode.idString(), requestBuilder, currentTimeMs,
                true, requestTimeoutMs, nextRequestHandler);
            log.debug("Sending transactional request {} to node {} with correlation ID {}", requestBuilder, targetNode, clientRequest.correlationId());
            client.send(clientRequest, currentTimeMs);
{code}

The first log line is printed in transactionManager.nextRequest.

Hence I wonder if the sender waits in awaitNodeReady. That one calls NetworkClientUtils.awaitReady which looks like this:
{code:java}
        if (timeoutMs < 0) {
            throw new IllegalArgumentException("Timeout needs to be greater than 0");
        }
        long startTime = time.milliseconds();
        if (isReady(client, node, startTime) ||  client.ready(node, startTime))
            return true;
        long attemptStartTime = time.milliseconds();
        while (!client.isReady(node, attemptStartTime) && attemptStartTime - startTime < timeoutMs) {
            if (client.connectionFailed(node)) {
                throw new IOException("Connection to " + node + " failed.");
            }
            long pollTimeout = timeoutMs - (attemptStartTime - startTime); // initialize in this order to avoid overflow
            client.poll(pollTimeout, attemptStartTime);
            if (client.authenticationException(node) != null)
                throw client.authenticationException(node);
            attemptStartTime = time.milliseconds();
        }
        return client.isReady(node, attemptStartTime);
{code}
 

Basically, if the node is not ready, we call client.poll with the pollTimeout which is basically the timeoutMs received by the method in the beginning. Guess what? The timeout is 60000 and we have 60s between the two log lines. If it ends up there and there are no response received while it is, it waits until the timeout.

Why would the node not be ready? I saw the following log line as bit before:
{code:java}
17:21:09 [30mTRACE[m [KAFKA] NetworkClient - [Producer clientId=my-cluster-1-core-StreamThread-1-producer, transactionalId=my-cluster-core-00000001-0000-0000-0000-000000000000-1] Connection to node 1 is throttled for 13 ms until timestamp 1729038069730{code}
It means that the connection was throttled. In client.ready, we check the throttle time and consider the node not ready if the throttle time has not passed yet.

So my suspicion is that the node was not ready due to the throttle time so it ended up waiting in poll for the request timeout.
~~~~

6.

~~~~
I have a patch that appears to fix this problem. We will soak it; if it works then I'll open a PR and request help with unit tests.
~~~~

7.

~~~~
Should we update this ticket "component" field to `producer` ?
~~~~

---

## KAFKA-17995: Large value for `retention.ms` could prevent remote data cleanup in Tiered Storage

https://issues.apache.org/jira/browse/KAFKA-17995

JIRA metadata: affects 3.6.0; fixed in 3.9.1, 4.0.0

- `KAFKA-17995@3.6.0`: config 3.6.0, metadata answer **affected** (listed_affected)
- `KAFKA-17995@3.9.2`: config 3.9.2, metadata answer **not_affected** (later_patch)

Known Kafka versions mentioned in text: none

### Description

~~~~
If a user has configured value of "retention.ms" to a value > current unix timestamp epoch, then at this line of code [1] , cleanupUntilMs becomes negative. This is because cleanupUntilMs is calculated as (current unix epoch ms - retention.ms) [1]. 

This leads to cleaner failures at [https://github.com/apache/kafka/blob/5a5239770ff3565233e5cbecf11446e76339f8fe/core/src/main/java/kafka/log/remote/RemoteLogManager.java#L2218] and hence, all cleaning for that topic partition stops.

[1] [https://github.com/apache/kafka/blob/5a5239770ff3565233e5cbecf11446e76339f8fe/core/src/main/java/kafka/log/remote/RemoteLogManager.java#L1397] 
~~~~

### Comments (2)

1.

~~~~
Hi [~divijv], if you're not working on this, may I take it? Thank you.
~~~~

2.

~~~~
Hi [~yangpoan] 
Sure. Please feel free to assign it to yourself.
~~~~

---

## KAFKA-18369: State updater's *-ratio metrics are incorrect

https://issues.apache.org/jira/browse/KAFKA-18369

JIRA metadata: affects 3.8.1; fixed in 4.3.0

- `KAFKA-18369@3.8.1`: config 3.8.1, metadata answer **affected** (listed_affected)
- `KAFKA-18369@4.3.0`: config 4.3.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 0.9

### Description

~~~~
h2. Background

{{DefaultStateUpdater}} defines {{{}idle-ratio{}}}, {{{}active-restore-ratio{}}}, {{{}standby-update-ratio{}}}, {{checkpoint-ratio}} metrics here: [https://github.com/apache/kafka/blob/trunk/streams/src/main/java/org/apache/kafka/streams/processor/internals/DefaultStateUpdater.java#L1101-L1115] These metrics are averages, that are supposed to indicate "The fraction of time the thread spent on \{action}". But the metrics don't actually do that.
h2. Issue

Let me explain this with an example:

For simplicity's sake, let's consider the following example involving just {{{}standby-update-ratio{}}}, {{checkpoint-ratio}} and ignoring the existence of the other two metrics.
Let's say the thread did:
 * {{999}} iterations with {{standby-update}} taking {{1ms}} in each iteration and no {{checkpoint}} happening ({{{}0ms{}}}).
 * {{1}} iteration with {{standby-update}} taking {{1ms}} and {{checkpoint}} taking {{9000ms}}

The thread spent {{10s}} working, of which it spent {{1s}} on {{standby-updates}} and {{9s}} on checkpoint, so the fraction of time it spent on checkpoint (checkpoint-ratio) is {{{}~0.001 (0.1%){}}}. Or at least that is what the metrics will say. I would instead argue that it spent {{9s/10s == 0.9 == 90%}} on checkpoint. If you agree with my logic, then you agree that this metrics is incorrect.

The problem is that the code computes a ratio for each iteration, and then averages those ratios out, producing a number devoid of statistical meaning or practical application. It ignores the fact that the one iteration that took {{{}9s{}}}, should have a much higher weight than those quick 1ms iterations.

{{(999*(0ms/1ms) + 1*(9000ms/9001ms))/1000 ~= 0.001}}
h2. Solution

What we would like to see instead is either a ratio of average/total times, not an average of ratios. I don't think this can be easily realised within the existing metrics system. So instead, what I propose as a solution is to report {{duration-total}} and/or {{duration-rate}} (with the unit of seconds per second) metric for each of {{{}idle{}}}, {{{}active-restore{}}}, {{{}standby-restore{}}}, {{{}checkpoint{}}}. The observers of these metrics, when needed, could then derive the actual ratio of time spent on each operation for example as {{{}checkpoint-ratio = checkpoint-duration-rate / (idle-duration-rate + active-restore-duration-rate + standby-restore-duration-rate + checkpoint-duration-rate){}}}. Or by performing an analogical calculation on deltas of the {{total}} metrics.

I can submit a PR once there's an agreement on the correct way to fix this.
~~~~

### Comments (8)

1.

~~~~
Hi [~sumislawski]. I agree that something is off here. However, not sure (yet), we have to solve it by reporting different metrics. Note that metrics are part of the public interface of Kafka and thus require a KIP to be changed.

Should we report an average here in the first place? If we look at the `StreamThread`, we report similar metrics, but do not use an average stat, but report the value directly:

https://github.com/apache/kafka/blob/trunk/streams/src/main/java/org/apache/kafka/streams/processor/internals/metrics/ThreadMetrics.java#L228

If you look at the KIP that introduced these metrics, there is no mention of averaging the ratios. https://cwiki.apache.org/confluence/display/KAFKA/KIP-869%3A+Improve+Streams+State+Restoration+Visibility

In summary, I agree that this is a bug, but I'd propose to fix it by removing the averaging.
~~~~

2.

~~~~
Hi [~lucasbru] 

IMO changing it from average to value doesn't solve the problem. I was about to open a similar ticket about the `StreamThread` metrics, just didn't find the time yet. The explanation of the issue is different, but the end result is mostly the same. Let me explain this in the new ticket, and I'll link it here once it's open.
~~~~

3.

~~~~
Sure, that makes sense. Ideally, the metrics for both threads report the numbers the same way.
~~~~

4.

~~~~
Sounds like we should compute the metric using a window, what is already supported... We sum up the actually time-values inside the window, and compute the ratio base on the sums.

Given that the current metric reports garbage, I don't think we need to do a KIP to change this – of course, we might want to update the KIP and docs to point out that we report this window based (ie config  metric.sample.window.ms = 30sec [default]).
~~~~

5.

~~~~
{quote}We sum up the actually time-values inside the window, and compute the ratio base on the sums.
{quote}
Exactly.

I know that summing inside a window is supported, but do we have a way to compute a ratio of two such sums?
~~~~

6.

~~~~
Well, if we have two summed window, we can just divide both to report the metric, right?

We would need a KIP for this change though, as `org.apache.kafka.common.metrics.stats` is public API – but should not be too difficult to get done.
~~~~

7.

~~~~
[~lucasbru] 
I described the similar yet different problem affecting `StreamThead` in a separate ticket as promised: https://issues.apache.org/jira/browse/KAFKA-18615

[~mjsax] 
Yes, we need to just divide the windowed sum metrics. While not exposing the windowed sums to the outside world. Just the result of the division. 

Could you elaborate on what kind of changes in `org.apache.kafka.common.metrics.stats` you have in mind? A new Stat that would be exactly what we need: A pair of internal windowed sums divided on read?
~~~~

8.

~~~~
Did not think about it in detail... – Guess it's up to whoever picks-up this ticket to figure it out and make a proposal. :) 

But yes, something link `WindowedAvg` I guess (which would internally re-use `WindowedSum`)?
~~~~

---

## KAFKA-19371: When a broker restarts, it should not attempt to create the __remote_log_metadata topic if it already exists.

https://issues.apache.org/jira/browse/KAFKA-19371

JIRA metadata: affects 3.9.0, 4.0.0; fixed in 4.2.0

- `KAFKA-19371@4.0.0`: config 4.0.0, metadata answer **affected** (listed_affected)
- `KAFKA-19371@4.2.0`: config 4.2.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: none

### Description

~~~~
*[Precondition]*
Kafka cluster already enabled the remote storage feature based on inner topic's implementation. The core inner topic "__remote_log_metadata" already created.
 
*[Steps]*

1. Restart one broker of the Kafka cluster.

2. Check the log and the code logic for the "__remote_log_metadata"s creating when broker restarting
 
*[Expect result]*
The broker shouldn't attempt to call API to create the topic due to that it already existed.
 
*[Actual result]*
The results are different which depend on the start process' duration for broker:
*Case 1: Happy Path when restarting take a short time*
[2025-06-03 22:35:11,648] INFO Topic __remote_log_metadata {color:#00875a}exists{color}. TopicId: 4CT2TTC-R6u7fNo_njYlDA, numPartitions: 50,

*Case 2: Unhappy path 1 when restarting take some time*
[2025-06-03 23:59:40,505] INFO Topic __remote_log_metadata{color:#de350b} does not exist{color}. Error: Timed out waiting for a node assignment. Call: listNodes
[2025-06-04 00:00:36,938] INFO Topic [__remote_log_metadata] {color:#de350b}already exists{color}
*Case 3: Unhappy path 2 when restarting take a long time.*
[2025-06-03 21:57:21,151] INFO Topic __remote_log_metadata {color:#de350b}does not exist{color}. Error: {color:#de350b}Timed out waiting{color} for a node assignment. Call: {color:#de350b}listNodes {color}at
[2025-06-03 21:58:21,153] ERROR Encountered error while creating __remote_log_metadata topic. java.util.concurrent.ExecutionException: org.apache.kafka.common.errors.{color:#de350b}TimeoutException{color}: Timed out waiting for a node assignment. Call: {color:#de350b}createTopics {color}at
 
From the log and current code. we can know that {color:#de350b}case 2 and case 3 both give the prompt "the topic does not exist" and try to call topic creating API. In actually. it is useless and contradict the fact that the topic already existed. Especially. the case 2's log prompt the topic existed and not existed at the same time.{color}
 
*[Root Cause analyst]*
After reviewing the related code (TopicBasedRemoteLogMetadataManager#doesTopicExist). It is one {color:#de350b}wrong implement{color} to judge one topic existed or not.
So let me create this [PR |#19899 · apache/kafka]to fix this minor bug. Thanks
 
FYI:
Why we got the timeout exception?
It is normal case based on the fact:
When restarting broker. The connection to query/create topic in "TopicBasedRemoteLogMetadataManager#initializeResources"will fail until the broker's self  get ready.
[2025-06-03 23:21:20,752] WARN [AdminClient clientId=adminclient-1] Connection to node -1 ([10.20.1.125:9559)|https://10-20-1-125/] could not be established. Node may not be available.
[2025-06-03 23:21:21,282] INFO [BrokerServer id=2] Transition from STARTING to STARTED (kafka.server.BrokerServer)
~~~~

### Comments (2)

1.

~~~~
[When a broker restarts, it should not attempt to create the __remote_log_metadata topic if it already exists. by jiafu1115 · Pull Request #19899 · apache/kafka|https://github.com/apache/kafka/pull/19899]
~~~~

2.

~~~~
[~yangpoan] hi. can you help to take I look? thanks!
~~~~

---

## KAFKA-19425: local segment on disk never deleted forever when remote storage initial failed

https://issues.apache.org/jira/browse/KAFKA-19425

JIRA metadata: affects 3.9.0, 4.0.0; fixed in 4.2.0

- `KAFKA-19425@3.9.0`: config 3.9.0, metadata answer **affected** (listed_affected)
- `KAFKA-19425@4.3.0`: config 4.3.0, metadata answer **not_affected** (later_line)

Known Kafka versions mentioned in text: none

### Description

~~~~
remote storage initial failed is silence so that the disk keep increasing forever.
[stop the server when fail to initialize to avoid local segment never got deleted. by jiafu1115 · Pull Request #20007 · apache/kafka|https://github.com/apache/kafka/pull/20007]
~~~~

### Comments (2)

1.

~~~~
[~yangpoan] hi. can you help to take I look? thanks!  

I see you are the only person which is active on this module:)
~~~~

2.

~~~~
[~fujian1115] I will take a look today. Thanks.
~~~~

---

## KAFKA-19480: KRaft migration hangs when /migration has null value

https://issues.apache.org/jira/browse/KAFKA-19480

JIRA metadata: affects 3.4.1, 3.5.2, 3.6.2, 3.7.2, 3.8.1, 3.9.1; fixed in 3.9.2

- `KAFKA-19480@3.9.1`: config 3.9.1, metadata answer **affected** (listed_affected)
- `KAFKA-19480@3.9.2`: config 3.9.2, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 3.9

### Description

~~~~
When using the [zookeeper-security-migration|https://kafka.apache.org/39/documentation.html#zk_authz_migration] tool without the '–enable.path.check' option, the script not only updates the ACLs for the existing znodes, but also creates any non-existing ones (with the ACL options specified) using null values based on the list defined in [ZkData.SecureRootPaths.|https://github.com/apache/kafka/blob/3.9/core/src/main/scala/kafka/zk/ZkData.scala#L1089-L1102] This is especially problematic for the /migration znode as the current logic only checks for the existence of the znode and later the migration process will hang when it tries to parse the null value over and over again. 

In summary, the migration cannot be completed if the zookeeper-security-migration script was run previously, and the only workaround is to manually remove the /migration znode in such cases. I propose a simple fix to circumvent the manual step by recreating the /migration znode if it contains a null value.
~~~~

---

## KAFKA-19678: Streams open iterator tracking has high contention on metrics lock

https://issues.apache.org/jira/browse/KAFKA-19678

JIRA metadata: affects 4.1.0; fixed in 4.1.2, 4.2.0

- `KAFKA-19678@4.1.0`: config 4.1.0, metadata answer **affected** (listed_affected)
- `KAFKA-19678@4.2.0`: config 4.2.0, metadata answer **not_affected** (fix_version)

Known Kafka versions mentioned in text: 4.1.0, 4.1.1, 4.2, 4.1, 4.2.0, 4.1.2

### Description

~~~~
We run Kafka Streams 4.1.0 with custom processors that heavily use state store range iterators.

While investigating disappointing performance, we found a surprising source of lock contention.

Over the course of about a 1 minute profiler sample, the {{org.apache.kafka.common.metrics.Metrics}} lock is taken approximately 40,000 times and blocks threads for about 1 minute.

This appears to be because our state stores generally have no iterators open, except when their processor is processing a record, in which case it opens an iterator (taking the lock through {{OpenIterators.add}} into {{{}Metrics.registerMetric{}}}), does a tiny bit of work, and then closes the iterator (again taking the lock through {{OpenIterators.remove}} into {{{}Metrics.removeMetric{}}}).

So, stream processing threads takes a globally shared lock twice per record, for this subset of our data. I've attached a profiler thread state visualization with our findings - the red bar indicates the thread was blocked during the sample on this lock. As you can see, this lock seems to be severely hampering our performance.

 

!image-2025-09-05-12-13-24-910.png!
~~~~

### Comments (19)

1.

~~~~
Thanks for reporting this issue. – I am wondering what your application is doing exactly, and if it might be possible to avoid creating an iterator per record?

One hacky work-around I could think of, would be to create a "dummy iterator", so you always have at least one-open iterators, and the metric won't be removed/added over and over again?
~~~~

2.

~~~~
Thanks [~mjsax] for taking a look.

We have a product requirement to compute a streaming-min and streaming-max operation over a grouped aggregate. For example, "earliest record due date for each user" or "latest record created date for each user".

To do this, we take the input stream,
{code:java}
K1 = U1 V1
K2 = U1 V2
K3 = U2 V3
K4 = U2 V4 {code}
and reorganize the records so the group-key and value are the key prefix, like
{code:java}
U1 V1 K1 = K1
U1 V2 K2 = K2
U2 V3 K3 = K3
U2 V4 K4 = K4{code}
and put it in a state store. Then, to determine the minimum or maximum, we do a prefix range scan to take the first or last record for the group U1 or U2.

It might be possible to reduce the number of range scans by caching the minimum and maximum values by key, to know if the max or min possibly changed and skip the iterator if not, but then we need a second state store duplicating the winning record per user. We assumed the cost of opening an iterator is roughly equal to the cost of a key lookup, but maybe this is not a good assumption.

Regardless, to me, the current semantics for this metric seems wrong. If the store is open, with no iterators currently, the correct value for the metric is explicitly "0" not "null / unregister". The current setup makes it difficult to graph, since our dashboards will interpret "null" as "missing data" which is distinct from a present 0.

I would expect the metric to be unregistered only when the state store is closed or otherwise we are sure no new iterators will ever be created.
~~~~

3.

~~~~
This metric is a little bit tricky... (for context [KIP-989|https://cwiki.apache.org/confluence/display/KAFKA/KIP-989%3A+Improved+StateStore+Iterator+metrics+for+detecting+leaks]) – if we would report `0` (or `-1`), the issue is, that if you setup an alert that computes "currentTime minus metricValue" you get false-positives, as the iterator open time computation would report a high value (many years). Your alert would need to be conditional, what is a struggle as far as I know. While a dashboard can render `0` it would blow out your "y-axis" on the dashboard to a very high value, too, and it seems it would make it very hard to actually read the dashboard?

We actually reported `null` originally, but this also caused issues: https://issues.apache.org/jira/browse/KAFKA-17954 – so we decided to de-register the metric when it becomes empty.
{quote} otherwise we are sure no new iterators will ever be created.
{quote}
Not sure what you mean by this?

For your use case: how many values per group do you get? Would it be possible to do an `aggregation` per group, and compute a `List` over all values per group? This would allow you to maintain this list with a key-lookup per update, avoiding a range scan (of course, this only works if the list is small enough, to avoid too large records...)
~~~~

4.

~~~~
Thanks for the context, this does sound tricky :(

Unfortunately, some degenerate groups can have upwards of 0.5M entries (of at least 16 bytes each), so I'm concerned the list approach would quickly run into maximum-record-size problems, as well as expensive serialization and deserialization costs.

For now, we run a patched kafka client which intentionally leaks these metrics, which is far from a long term solution but at least keeps us running at the moment.
~~~~

5.

~~~~
0.5M entries... yeah, that won't work with the list approach...

Did you consider the "dummy iterator" idea? Something like, create an `all()` iterator at startup, and every X second, you first create a new all() iterator, and close the old one? This way, you have at least one open iterator all the time – you still want to close and replace it periodically, to not get an very old open iterator. Could this work?

Leaking the metrics sounds like a bad idea, as it will consume a lot a resources inside RocksDB...
~~~~

6.

~~~~
Yes, we can explore the dummy iterator approach. That said, is this not a problem also for built in processors, like the ForeignTableJoinProcessor? It also seems to use a range scan per record.
~~~~

7.

~~~~
We did not observe any regression in our test/benchmark setup with regard to throughput (but maybe our setup is just not catching it), and nobody reported anything about it yet (well, beside you :))... But yes, might be worth to look into. It's not just FK join, but also session-windows, sliding-windows, and stream-stream join that use range scans... (maybe also others – would need to double check the code).
~~~~

8.

~~~~
I believe I can observe a similar performance bottleneck where the `ForeinTableJoinProcessorSupplier$KTableKTableJoinProcessor` is less performant than it could be due to repeated registering and unregistering metrics with this lock, so while I am happy to test workaround on our custom processor, I have increased confidence that ideally there would be a fix outside of each individual processor having workarounds:



!image-2025-10-20-13-36-54-857.png!
~~~~

9.

~~~~
Ok, I think part of the reason why the monitor contention is so high, is because we have a lot of metrics registered, and the storage is a LinkedList inside a CHM. I'm not sure yet if 9.1M(!!) metrics is a leak or something we're doing wrong...

!image-2025-10-21-09-24-02-505.png!
~~~~

10.

~~~~
Ok, this might be an error on our end. I (too eagerly?) picked the fix to KAFKA-19748 before it was finished, looks like the version I have is incomplete, and thought the metrics leak was fixed. I will re-apply the final version and hope it fixes the leak properly this time.
~~~~

11.

~~~~
Re-picking the fix to KAFKA-19748 made the situation much, much better. But, I am still seeing elevated levels of contention, with the leak fixed.
~~~~

12.

~~~~
[~mjsax] , would it make sense to move the state store oldest open iterator metric from current INFO to only register when metrics is set to DEBUG level? That would resolve the issue as far as we are concerned, we are happy to accept this kind of overhead when debugging (now that the leak is fixed).
~~~~

13.

~~~~
{quote}ideally there would be a fix outside of each individual processor having workarounds
{quote}
I never disagreed about this – just wanted to get you out of the ditch, until we find a fix :) 

Glad you figures out the memory/metric leak thing, and happy to hear that the fix improves the situation... AK 4.1.1 should do out soon....

Interesting idea about making it a DEBUG level metric – could be a good solution in case we cannot figure out anything better. But would require a KIP I assume? [~bbejeck] wanted to work on this ticket. Let's hear from him. – Personally I would hope that we just find a good fix, even if I am not 100% sure what it could be – maybe something a lazy/delayed removal of the metric, that we would cancel if a new iterator comes in again?
~~~~

14.

~~~~
[~mjsax][~stevenschlansker] In taking another look at [KIP-989|https://cwiki.apache.org/confluence/display/KAFKA/KIP-989%3A+Improved+StateStore+Iterator+metrics+for+detecting+leaks] the `oldest-iterator-open-since-ms` is specified as DEBUG.  So if we decide to go down the path of only registering it when the recording level is DEBUG would work. 


~~~~

15.

~~~~
Great find [~bbejeck] --seems this makes our life much easier. If we just fix the incorrect recording level, we should have a proper fix. +1 from my side.
~~~~

16.

~~~~
That's great news - since in normal operation, iterators should not be leaked, it seems appropriate that this diagnostic is DEBUG level.
~~~~

17.

~~~~
cherry-picked https://github.com/apache/kafka/pull/21091 to 4.2 and 4.1
~~~~

18.

~~~~
Thanks all for your help!
~~~~

19.

~~~~
NP. Would you be able to build from the source, and test 4.2.0-SNAPSHOT or 4.1.2-SNAPSHOT to verify if it resolve the issue you are observing?
~~~~

---

## KAFKA-20198: StickyPartitionAssignor with group protocol classic is not acting sticky

https://issues.apache.org/jira/browse/KAFKA-20198

JIRA metadata: affects 4.1.1; fixed in 4.4.0

- `KAFKA-20198@4.1.1`: config 4.1.1, metadata answer **affected** (listed_affected)
- `KAFKA-20198@4.1.0`: config 4.1.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 4.2.0, v4.1.0

### Description

~~~~
h2. Problem

 During some tests, I noticed that many state stores were closed during group rebalancing triggered by instance scaling. I assumed that the StickyTaskAssignor was supposed to prevent exactly this. However, with each new application instance that started the stream, the rebalancing resulted in a cascade of "Handle new assignments" log entries. Scaling from one to two application instances (each with ten Kafka stream threads) generated 429 such entries, which seems excessive. The log entries showed that almost all tasks were moved to other group members throughout the entire rebalancing phase.
h2. Setup
 * Scala application based on Scala 2.13 and Kafka Streams
 * Application consumes from a single topic having 450 Partitions
 * Stream topology is implementing some stateful aggregations
 * Change logging is disabled. Only InMemory state stores are used.
 * Each app instance is configured to create 10 Stream Threads

*Following libraries are used*
 * org.apache.kafka:kafka-streams:4.2.0
 * org.apache.kafka:kafka-streams-scala_2.13:4.2.0
 * org.apache.kafka:kafka-streams-test-utils:4.2.0

The Kafka Cluster based on v4.1.0 was created with [Strimzi Operator v0.50.0|https://github.com/strimzi/strimzi-kafka-operator/releases/tag/0.50.0].

I already discussed this behavior with [~lucasbru]  and it seems to be a bug:
[Confluent Slack Channel|https://confluentcommunity.slack.com/archives/C48AHTCUQ/p1770905604912249]
h2. Further Tests

Having implemented a pretty simple Spring Boot app with an absolut minimal topology revealed the same behavior. The topology in this case didn't used state stores at all. It just consumes from a single topic (again 450 partitions) and does some logging of the key/value combinations. Also here the rebalancing led to a cascade of task re-assignments. Again i configured the app to use 10 Stream Threads.

I also did another Tests with the HATaskAssignor. Here the logic seems to 1st revoke all assigned partitions and then re-assigns the tasks in a round-robin manner, which seems to be as expected.

Another test using KIP-1071 showed that there the Sticky Task assignment works as expected.
~~~~

---

## KAFKA-20449: OffsetFetcherUtils.updateSubscriptionState logs at WARN for benign race condition during rebalance

https://issues.apache.org/jira/browse/KAFKA-20449

JIRA metadata: affects 4.1.2, 4.2.1, 4.3.0; fixed in 4.3.2, 4.4.0

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

JIRA metadata: affects 4.3.0; fixed in 4.3.2, 4.4.0

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

## KAFKA-20877: Streams task-level restore-rate and update-rate incorrect

https://issues.apache.org/jira/browse/KAFKA-20877

JIRA metadata: affects 3.5.0; fixed in 4.3.2, 4.4.0

- `KAFKA-20877@3.5.0`: config 3.5.0, metadata answer **affected** (listed_affected)
- `KAFKA-20877@3.4.1`: config 3.4.1, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
The task-level metrics restore-rate/restore-total (active tasks) and update-rate/update-total (standby tasks) are meant to report how many changelog records were restored or updated. update-rate is documented as "The average number of records updated per second".

However, the rate-metric is incorrectly captured. It counts how many times the sensor was recorded and discards the value (number of records restored), so it incorrectly reports restore/update batches per second.

Introduced via KAFKA-10199 which added these metrics.
~~~~

---

## KAFKA-21076: Oversize decompressed telemetry payload returns INVALID_RECORD and permanently disables client telemetry

https://issues.apache.org/jira/browse/KAFKA-21076

JIRA metadata: affects 4.3.1; fixed in 4.5.0

- `KAFKA-21076@4.3.1`: config 4.3.1, metadata answer **affected** (listed_affected)
- `KAFKA-21076@4.3.0`: config 4.3.0, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: 4.3.1, 4.3.0, 2.08

### Description

~~~~
Since [PR #22327|https://github.com/apache/kafka/pull/22327] (4.3.1, "MINOR: Fixed metrics decompression"), {{ClientTelemetryUtils.decompress}} throws {{TelemetryTooLargeException}} when the decompressed payload exceeds {{{}telemetry.max.bytes{}}}. The call runs inside {{ClientMetricsManager.processPushTelemetryRequest}} in the plugin export block, whose {{catch (Throwable)}} maps every failure to {{{}Errors.INVALID_RECORD{}}}:
{code:java}
catch (Throwable exception) {
    clientMetricsStats.recordPluginErrorCount(clientInstanceId);
    clientInstance.lastKnownError(Errors.INVALID_RECORD);
    log.error("Error exporting client metrics to the plugin for client instance id: {}", clientInstanceId, exception);
    return request.errorResponse(0, Errors.INVALID_RECORD);
}
{code}
KIP-714 defines INVALID_RECORD as "Broker failed to decode or validate the client's encoded metrics. Log an error and stop pushing metrics. This is viewed as a problem in the client implementation of metrics serialization that is not likely to be resolved by retrying." The Java client implements exactly that in {{{}ClientTelemetryUtils.maybeFetchErrorIntervalMs{}}}: on INVALID_RECORD it sets the push interval to {{{}Integer.MAX_VALUE{}}}, so telemetry from that client instance stops until the process restarts.

The validatePushRequest method throws the same TelemetryTooLargeException when the wire size exceeds telemetry.max.bytes, and that path returns the error through Errors.forException, which yields TELEMETRY_TOO_LARGE. So the broker returns two different codes for the same exception class depending on whether the check happens before or after decompression.

KIP-714 defines TELEMETRY_TOO_LARGE for a payload that is too large, and the client handles that code by retrying at the normal interval.

Observed effect: after a broker upgrade from 4.3.0 to 4.3.1, every Kafka Streams stream-thread consumer (payload several MB decompressed, under 1 MiB compressed) got INVALID_RECORD on its next push and disabled its telemetry. All {{org.apache.kafka.stream.*}} metrics that KIP-1076 routes through the stream-thread consumers disappeared from the metrics backend in every environment at the same time. Broker log:
{noformat}
ERROR Error exporting client metrics to the plugin for client instance id: xkdFrlXGTGig-RPx5SjuQA (org.apache.kafka.server.ClientMetricsManager)
org.apache.kafka.common.errors.TelemetryTooLargeException: Decompressed telemetry metrics exceed maximum allowed size: 1048576
{noformat}
Two further points:
 * KIP-714 documents {{telemetry.max.bytes}} as "The maximum size (after compression if compression is used) of telemetry pushed from a client to the broker." PR #22327 changed the meaning to also bound the decompressed size, with no KIP update, no release note, and no new configuration. A 4.3.0 cluster that accepted a client's pushes rejects the same pushes on 4.3.1.
 * Before PR #22327 the same code path allocated {{metrics.limit() * 2}} bytes and grew without bound, so a bound is reasonable. The bound needs its own error code and, given that decompression ratios of 10x or more are normal for OTLP metrics, its own configuration or a multiple of {{{}telemetry.max.bytes{}}}.

Measured on a Kafka Streams application (8 stream threads, subscription metrics=*, push interval 30 s) against 4.3.1 brokers. The broker's RequestMetrics RequestBytes histogram for PushTelemetry put the compressed push at a 40 KB mean, 940 KB p95, 1.34 MB p99 and 1.41 MB max in one cluster, 2.08 MB max in another; all of these passed the 1 MiB wire check before 4.3.1 or were rejected with the retryable TELEMETRY_TOO_LARGE. With telemetry.max.bytes raised to 32 MiB the brokers still logged "Decompressed telemetry metrics exceed maximum allowed size: 33554432" for several of these pushes, and 128 MiB was needed before every push was accepted. That is an expansion ratio of at least 25x between the compressed payload the client and the wire check see and the decompressed payload the new check bounds, which is the normal ratio for OTLP metrics with repeated label sets. A single telemetry.max.bytes cannot bound both sensibly: a value that admits a legitimate decompressed payload is meaningless as a wire limit. The decompressed bound should have its own configuration, or a documented multiple of telemetry.max.bytes, and it should return TELEMETRY_TOO_LARGE like the wire check does.

Suggested fix: catch {{TelemetryTooLargeException}} before the generic {{catch (Throwable)}} and return {{{}Errors.TELEMETRY_TOO_LARGE{}}}, so the client retries at its interval instead of disabling telemetry. Document the decompressed bound in {{telemetry.max.bytes}} or add a separate configuration, and mention the behavior change in the upgrade notes.

Workaround: raise {{telemetry.max.bytes}} on the brokers and restart affected clients.
~~~~

### Comments (5)

1.

~~~~
PR Raised [https://github.com/apache/kafka/pull/23444/] 
~~~~

2.

~~~~
[~stevenschlansker] Thanks for raising the issue. This all does make sense.

So we are talking about 3 concerns, correct me if I am missing something:
 # Telemetry too large exception is not propagated correctly to client when it fails to decompress. I can see [https://github.com/apache/kafka/pull/23444/] has been raised by [~rishi08rana] for same.
 # Client side handling when telemetry too large exception is encountered. I can see you have created: https://issues.apache.org/jira/browse/KAFKA-21077 for same.
 # A separate config for decompression ratio or decompression max bytes with documentation.

Is there anything else I am missing?
~~~~

3.

~~~~
[~apoorvmittal10]  [~stevenschlansker] , raised [https://github.com/apache/kafka/pull/23465] to address point 3.
~~~~

4.

~~~~
[~stevenschlansker] For this Jira, where title is specific to the issue fixed by [~rishi08rana] in the PR [https://github.com/apache/kafka/pull/23444/], I am marking the Jira as resolved.

For discussion around separate config and decompression max bytes, the idea is to maintain `telemetry.max.bytes` to right config which fits the uncompressed metrics bytes. Compression is to save on network bandwidth for metrics request. In case you think we need an improvement there then please open a follow up which can be discussed separately.
~~~~

5.

~~~~
Thank you! Yes, having max bytes apply to decompressed size is acceptable to us - we can tune appropriately.
~~~~

---

## KAFKA-21096: SharePartition instances pending cleanup even when fenced

https://issues.apache.org/jira/browse/KAFKA-21096

JIRA metadata: affects 4.2.0; fixed in 4.2.2, 4.3.2, 4.4.0

- `KAFKA-21096@4.2.0`: config 4.2.0, metadata answer **affected** (listed_affected)
- `KAFKA-21096@4.1.2`: config 4.1.2, metadata answer **not_affected** (before_affected)

Known Kafka versions mentioned in text: none

### Description

~~~~
SharePartition registers Yammer gauges whose suppliers capture the SharePartition instance (this::numInFlightRecords and cachedState::size). These gauges were never deregistered when a partition was removed from the cache, so the metrics registry kept a strong reference to every fenced SharePartition (and its cachedState) for the lifetime of the broker.
~~~~

---
