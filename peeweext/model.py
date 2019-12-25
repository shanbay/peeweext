import inspect

import peewee as pw
import pendulum
from blinker import signal

from .validation import ValidationError
from .fields import DatetimeTZField

pre_save = signal('pre_save')
post_save = signal('post_save')
pre_delete = signal('pre_delete')
post_delete = signal('post_delete')
pre_init = signal('pre_init')


class ModelMeta(pw.ModelBase):
    """Model meta class, provide validation."""

    def __init__(cls, name, bases, attrs):
        """Store validator."""
        super().__init__(name, bases, attrs)
        setattr(cls, '_validators', {})  # {'field_name': `callable`}
        # add validator by model`s validation method
        for k, v in attrs.items():
            if k.startswith('validate_') and inspect.isfunction(v):
                fn = k[9:]  # 9 = len('validate_')
                if fn in cls._meta.combined:
                    cls._validators[fn] = v


class Model(pw.Model, metaclass=ModelMeta):
    created_at = DatetimeTZField(default=pendulum.now)
    updated_at = DatetimeTZField(default=pendulum.now)

    __attr_whitelist__ = False
    __attr_accessible__ = set()
    __attr_protected__ = set()

    def __init__(self, *args, **kwargs):
        pre_init.send(type(self), instance=self)
        self._validate_errors = {}  # eg: {'field_name': 'error information'}
        super().__init__(*args, **kwargs)
        self.delete = self._delete

    @classmethod
    def create(cls, **query):
        """
        secure create, mass assignment protected
        """
        return super().create(**cls._filter_attrs(query))

    def update_with(self, **query):
        """
        secure update, mass assignment protected
        """
        for k, v in self._filter_attrs(query).items():
            setattr(self, k, v)
        return self.save()

    @classmethod
    def _filter_attrs(cls, attrs):
        """
        attrs: { attr_name: attr_value }
        if __attr_whitelist__ is True:
            only attr in __attr_accessible__ AND not in __attr_protected__
            will pass
        else:
            only attr not in __attr_protected__ OR in __attr_accessible__
            will pass
        """
        if cls.__attr_whitelist__:
            whitelist = cls.__attr_accessible__ - cls.__attr_protected__
            return {k: v for k, v in attrs.items() if k in whitelist}
        else:
            blacklist = cls.__attr_protected__ - cls.__attr_accessible__
            return {k: v for k, v in attrs.items() if k not in blacklist}

    def save(self, *args, **kwargs):
        skip_validation = kwargs.pop('skip_validation', False)
        if not skip_validation:
            errors = self._validate(only=kwargs.get("only"))
            if errors:
                raise ValidationError(str(errors))

        pk_value = self._pk
        created = kwargs.get('force_insert', False) or not bool(pk_value)
        pre_save.send(type(self), instance=self, created=created)
        ret = super().save(*args, **kwargs)
        post_save.send(type(self), instance=self, created=created)
        return ret

    def delete_instance(self, *args, **kwargs):
        model = type(self)
        pre_delete.send(model, instance=self)
        recursive = kwargs.get('recursive', False)
        delete_nullable = kwargs.get('delete_nullable', False)
        if recursive:
            dependencies = self.dependencies(delete_nullable)
            for query, fk in reversed(list(dependencies)):
                fk_model = fk.model
                if fk.null and not delete_nullable:
                    fk_model.update(**{fk.name: None}).where(query).execute()
                else:
                    fk_model.delete().where(query).execute()
        ret = model.delete().where(self._pk_expr()).execute()
        post_delete.send(model, instance=self)
        return ret

    def _delete(self, *args, **kwargs):
        raise UserWarning(
            "Use delete() in instance is forbidden! Try to use "
            "delete_instance()"
        )

    def _validate(self, only=None):
        """Validate model data and save errors
        """
        errors = {}

        if only:
            items = []
            for field in only:
                if isinstance(field, pw.basestring):
                    name = field
                else:
                    name = field.name
                validator = self._validators.get(name)
                if validator:
                    items.append((name, validator))
        else:
            items = self._validators.items()

        for name, validator in items:
            value = getattr(self, name)

            try:
                validator(self, value)
            except ValidationError as e:
                errors[name] = str(e)

        return errors


def _touch_model(sender, instance, created):
    if issubclass(sender, Model):
        instance.updated_at = pendulum.now()


pre_save.connect(_touch_model)
