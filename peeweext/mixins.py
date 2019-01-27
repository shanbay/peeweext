from peewee import fn, SQL

from .model import pre_save


def _gen_sequence(sender, instance, created):
    if issubclass(sender, SequenceMixin) and created:
        model = sender
        max_id_obj = model.select(model.id).order_by(-model.id).first()
        instance.sequence = max_id_obj.id + 1 if max_id_obj else 1.0


pre_save.connect(_gen_sequence)


class SequenceMixin:
    """
    Add function for sequence support,
    to use this feature, make sure that your model
    should inherit from peeweext.Model
    and has fields we need.

    id = pw.AutoField()
    # currently we only support a fixed column_name
    sequence = pw.DoubleField()
    """
    __seq_scope_field_name__ = None

    def _sequence_query(self):
        """
        query all sequence rows
        """
        klass = self.__class__
        query = klass.select().where(klass.sequence.is_null(False))
        seq_scope_field_names =\
            (self.__seq_scope_field_name__ or '').split(',')
        for name in seq_scope_field_names:
            seq_scope_field = getattr(klass, name, None)
            if seq_scope_field:
                seq_scope_field_value = getattr(self, name)
                query = query.where(seq_scope_field == seq_scope_field_value)
        return query

    def _loosen(self):
        collection = self._sequence_query().order_by(+self.__class__.sequence)
        for index, instance in enumerate(collection):
            instance.sequence = float(index + 1)
            instance.save()

    def _change_sequence(self, new_sequence):
        with self._meta.database.atomic():
            klass = self.__class__
            current_sequence = self._sequence_query().where(
                klass.sequence <= self.sequence).select(
                fn.COUNT(SQL('*'))).scalar()
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
        self._change_sequence(new_sequence)
