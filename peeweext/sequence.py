import peewee as pw

from . import Model


class SequenceModel(Model):
    class Meta:
        seq_scope_field_name = None

    id = pw.AutoField()
    # currently we only support a fixed column_name
    sequence = pw.DoubleField(column_name='sequence', null=True)

    def save(self, force_insert=False, only=None):
        if force_insert or not bool(self._pk):
            klass = self.__class__
            max_id_obj = klass.select(klass.id).order_by(-klass.id).first()
            self.sequence = max_id_obj.id + 1 if max_id_obj else 1.0
        return super(SequenceModel, self).save(force_insert, only)

    def _sequence_query(self):
        """
        query all sequence rows
        """
        klass = self.__class__
        query = klass.select().where(klass.sequence.is_null(False))
        seq_scope_field_name = self._meta.seq_scope_field_name or ''
        seq_scope_field = getattr(klass, seq_scope_field_name, None)
        if seq_scope_field:
            seq_scope_field_value = getattr(self, seq_scope_field_name)
            return query.where(seq_scope_field == seq_scope_field_value)
        return query

    def _loosen(self):
        collection = self._sequence_query().order_by(+self.__class__.sequence)
        for index, instance in enumerate(collection):
            instance.sequence = float(index + 1)
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

        with self._meta.database.connection_context():
            with self._meta.database.atomic('IMMEDIATE'):
                klass = self.__class__
                current_sequence = self._sequence_query().where(
                    klass.sequence <= self.sequence).count()
                if current_sequence == new_sequence:
                    return
                if new_sequence > 1:
                    instances = self._sequence_query() \
                        .order_by(+klass.sequence)
                    # frontwards
                    if current_sequence > new_sequence:
                        start = new_sequence - 2
                        end = new_sequence
                    # backwards
                    else:
                        start = new_sequence - 1
                        end = new_sequence + 1
                    instances = instances[start:end]
                    if not len(instances):
                        raise ValueError("Sequence is not proper")

                    if len(instances) == 1:
                        prev_seq = instances[0].sequence
                        next_seq = prev_seq + 1
                    else:
                        prev_ins, next_ins = instances
                        prev_seq = prev_ins.sequence
                        next_seq = next_ins.sequence
                else:
                    prev_seq = 0
                    next_seq = self._sequence_query() \
                        .order_by(+klass.sequence).first().sequence

                self.sequence = (prev_seq + next_seq) / 2
                self.save()

                # Sequence auto loosen
                # regenerate all sequence when precision lost
                if abs(prev_seq - next_seq) < 0.000001:
                    self._loosen()
