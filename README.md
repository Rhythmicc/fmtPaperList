# fmtPaperList

一个爬论文信息的玩意，理论上有论文信息的 URL 就行了，比如 IEEE 或者 ACM 的。

你可以按照格式编辑`dist/1.md`，脚本主要利用 URL 爬取，其余作为辅助信息使用。

## 安装依赖项

```sh
pip3 install Qpro selenium requests -U
```

## 使用

`qrun --help` 获取帮助

## 注意

可以修改`check-all`命令来使本工具更契合你的需求。

## 样例

使用[`dist/1.md`](./dist/1.md)，可生成[`dist/to.md`](./dist/to.md)
