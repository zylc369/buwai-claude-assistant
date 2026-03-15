# session的相关逻辑

## session id的相关逻辑

1. 前端的工作空间对session id的影响：如果当前工作空间没有任何session，这种情况会发生在工作空间刚创建的时候，这是一个新的session，前端必须创建一个使用UUIDv7生成的external_session_id字段，发送提示词给服务端的时候将前端的external_session_id也发送给服务端，但是此时前端是没有session_unique_id的。服务端处理前端请求，调用claude sdk成功后它会返回ResultMessage消息，这个消息里面有session id这个session id作为session表的session_unique_id列的值，前端传入的external_session_id作为session表的session_unique_id，向session表插入一条新的行。session表插入数据参考**session表列数据来源说明**一节。
2. 前端新建session对session id的影响：
   1. 前端使用UUIDv7生成external_session_id值，这个值只需要存储到内存中。发送提示词的时候它要一并发送给服务端，由于没有传session_unique_id给服务端，服务端就知道这是新的session了，服务端处理新session的逻辑见上面的第1点。
   2. 前端如何判断是否是新session：前端新建的session不可能有session_unique_id，这意味着就是前端新创建的session。



## session表列数据来源说明

1. id：自增
2. session_unique_id：
   1. 根源来自于claude sdk返回的session id，这是唯一合法来源
   2. 前端传参指定session_unique_id的时候，后端需要查询它是否在session表中存在，如果不存在意味着非法返回错误
3. project_unique_id：来自前端传参
4. workspace_unique_id：来自前端传参。根源来自于workspace创建的时候的workspace_unique_id，如果这个值在workspace表中不存在意味着非法返回错误。
5. directory：来自前端传参。根源来自于workspace创建的时候的directory，根据workspace_unique_id+directory查询不到数据意味着非法返回错误。
6. title：服务端自己根据提示词总结
7. external_session_id：来自前端传参，后端要查询它是否在session表中存在，如果不存在意味着这是新session
8. gmt_create是创建时间，毫秒
9. gmt_modified是修改时间，毫秒
10. test：测试用例或前端的测试模式可以传递它为true，用来做测试数据和正式数据的软隔离。



## 测试要求

1. 按照需求，服务端和前端要创建对应的测试用例，常见条件和边界条件都要测试到，尽量不要用MOCK数据。
2. 前端是不是能通过运行无头浏览器的方式，测试前端页面UI，如果是的话也需要使用这种技术进行测试。
3. 测试出现问题必须修复，修复完成后重新测试。
4. 所有测试用例都必须通过。



## Review要求

需要review，保证一定要和本文档的需求匹配。



## 其他

**工作空间和workspace是一个意思，会话和session是一个意思。**

**本次需求会变更数据库表的数据来源，本次计划执行前删除数据库然后重建。**