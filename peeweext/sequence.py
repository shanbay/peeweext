import peewee as pw


class SequenceModel(pw.Model):
    class Meta:
        seq_scope_field_name = None

    id = pw.AutoField()
    # currently we only support a fixed column_name
    _sequence = pw.DoubleField(column_name='sequence', null=True)

    def save(self, force_insert=False, only=None):
        if force_insert or not bool(self._pk):
            klass = self.__class__
            max_id_obj = klass.select(klass.id).order_by(-klass.id).first()
            self._sequence = max_id_obj.id + 1 if max_id_obj else 1.0
        return super(SequenceModel, self).save(force_insert=force_insert, only=only)

    @property
    def sequence(self):
        return self._sequence

    def _sequence_query(self):
        """
        query all sequence rows
        """
        klass = self.__class__
        query = klass.select().where(klass._sequence.is_null(False))
        seq_scope_field_name = self._meta.seq_scope_field_name or ''
        seq_scope_field = getattr(klass, seq_scope_field_name, None)
        if seq_scope_field:
            seq_scope_field_value = getattr(self, seq_scope_field_name)
            return query.where(seq_scope_field == seq_scope_field_value)
        return query

    def _loosen(self):
        collection = self._sequence_query().order_by(+self.__class__._sequence)
        for index, instance in enumerate(collection):
            instance._sequence = float(index + 1)
            instance.save()

    def change_sequence(self, new_sequence):
        """
        :param new_sequence: 要排到第几个

        基本的排序思路是，找到要插入位置的前一个和后一个对象，把要
        拖动对象的sequence值设置成介于两个对象之间

        注意 current_sequence，new_sequence 两个变量是数组中
        的 index，与对象的 sequence 值不要混淆
        """
        if new_sequence < 1:
            raise ValueError("Sequence is not proper")  # pragma no cover

        with self._meta.database.transaction():
            klass = self.__class__
            current_sequence = self._sequence_query().where(klass._sequence <= self._sequence).count()
            if current_sequence == new_sequence:
                return

            # 拖到第一个时需要特殊处理
            if new_sequence > 1:
                instances = self._sequence_query().order_by(+klass._sequence)
                # 从后往前拖
                if current_sequence > new_sequence:
                    instances = instances[new_sequence - 2:new_sequence]
                # 从前往后拖
                else:
                    instances = instances[new_sequence - 1:new_sequence + 1]

                if not len(instances):
                    raise ValueError("Sequence is not proper")
                elif len(instances) == 1:
                    prev_seq = instances[0]._sequence
                    next_seq = prev_seq + 1
                else:
                    prev_ins, next_ins = instances
                    prev_seq, next_seq = prev_ins._sequence, next_ins._sequence
            else:
                prev_seq = 0
                next_seq = self._sequence_query().order_by(+klass._sequence).first()._sequence

            self._sequence = (prev_seq + next_seq) / 2
            self.save()

            # Sequence auto loosen
            # 不断的除以2，会导致精度丢失，当两个对象的 sequence 差过小时，全部重拍，重新生成 sequence
            if abs(prev_seq - next_seq) < 0.000001:
                self._loosen()
