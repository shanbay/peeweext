# upgrade from pre 0.7.0 to 0.7.x

1. db_url 不再支持 `smart` 家族，替换为 `pool`
2. `peeweext.Peeweext` 位置更新。
    2.1 sea 项目 -> `peeweext.sea.Peeweext`
    2.2 flask 项目 -> `peeweext.flask.Peeweext`
3. 所有 Field 移到 `peeweext.fields`
4. 增加 validation
5. 对于 Sea 项目，请在 `MIDDLEWARES` 列表中增加 `'peeweext.sea.PeeweextMiddleware'`
