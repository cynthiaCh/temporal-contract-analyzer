前台准备客户端面对 `false`（pending）时，应继续检查同一活动的包；只有收到 `true`（ready）后，才将该包标为已完成并对外发布。pending 可以重复出现，传输层不会自行重试。前台资源的公开操作包括 start、close、reopen、snapshot；最终 owner disposal 释放资源。

