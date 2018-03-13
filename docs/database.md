# database


## SmartDatabase

peeweext 提供 `Smart` 类的 database。会自动处理 connection，包括

- `SmartMySQLDatabase`
- `SmartPostgresqlDatabase`
- `SmartPostgresqlExtDatabase`
- `SmartSqliteDatabase`
- `SmartSqliteExtDatabase`
- `SmartCSqliteExtDatabase`

*对应的 Database URL*

`mysql+smart`: `SmartMySQLDatabase`
`postgres+smart`: `SmartPostgresqlDatabase`
`postgresql+smart`: `SmartPostgresqlDatabase`
`postgresext+smart`: `SmartPostgresqlExtDatabase`
`postgresqlext+smart`: `SmartPostgresqlExtDatabase`
`sqlite+smart`: `SmartSqliteDatabase`
`sqliteext+smart`: `SmartSqliteExtDatabase`
`csqliteext+smart`: `SmartCSqliteExtDatabase`

## 注意点

如果需要使用 `transaction`，需要放在 `Database.connection_context` block 中

```python
pwdb = peeweext.Peeweext()

db = pwdb.database

with db.connection_context():
        with db.atomic() as transaction:
            pass
```
