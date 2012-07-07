# SQLAlchemy example versioning
import datetime
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import mapper, class_mapper, attributes, object_mapper
from sqlalchemy.orm.exc import UnmappedClassError, UnmappedColumnError
from sqlalchemy import Table, Column, ForeignKeyConstraint, Integer, DateTime
from sqlalchemy import event
from sqlalchemy.orm.properties import RelationshipProperty

# from zabalaza.apps.words.models import Change

def col_references_table(col, table):
    for fk in col.foreign_keys:
        if fk.references(table):
            return True
    return False

def _history_mapper(local_mapper):
    cls = local_mapper.class_

    # set the "active_history" flag
    # on on column-mapped attributes so that the old version
    # of the info is always loaded (currently sets it on all attributes)
    for prop in local_mapper.iterate_properties:
        getattr(local_mapper.class_, prop.key).impl.active_history = True

    super_mapper = local_mapper.inherits
    super_history_mapper = getattr(cls, '__history_mapper__', None)

    polymorphic_on = None
    super_fks = []
    if not super_mapper or local_mapper.local_table is not super_mapper.local_table:
        cols = []
        for column in local_mapper.local_table.c:
            if column.name == 'version':
                continue

            col = column.copy()
            col.unique = False

            if super_mapper and col_references_table(column, super_mapper.local_table):
                super_fks.append((col.key, list(super_history_mapper.local_table.primary_key)[0]))

            cols.append(col)

            if column is local_mapper.polymorphic_on:
                polymorphic_on = col

        if super_mapper:
            super_fks.append(('version', super_history_mapper.base_mapper.local_table.c.version))
            cols.append(Column('version', Integer, primary_key=True))
        else:
            cols.append(Column('version', Integer, primary_key=True))

        cols.append(Column('created', DateTime(timezone=True), default=datetime.datetime.now))

        if super_fks:
            cols.append(ForeignKeyConstraint(*zip(*super_fks)))

        table = Table(local_mapper.local_table.name + '_history', local_mapper.local_table.metadata,
           *cols
        )
    else:
        # single table inheritance.  take any additional columns that may have
        # been added and add them to the history table.
        for column in local_mapper.local_table.c:
            if column.key not in super_history_mapper.local_table.c:
                col = column.copy()
                col.unique = False
                super_history_mapper.local_table.append_column(col)
        table = None

    if super_history_mapper:
        bases = (super_history_mapper.class_,)
    else:
        bases = local_mapper.base_mapper.class_.__bases__
    versioned_cls = type.__new__(type, "%sHistory" % cls.__name__, bases, {})

    m = mapper(
            versioned_cls, 
            table, 
            inherits=super_history_mapper, 
            polymorphic_on=polymorphic_on,
            polymorphic_identity=local_mapper.polymorphic_identity
            )
    m.class_.__unicode__ = cls.__unicode__.im_func
    cls.__history_mapper__ = m

    if not super_history_mapper:
        local_mapper.local_table.append_column(
            Column('version', Integer, default=1, nullable=False)
        )
        local_mapper.add_property("version", local_mapper.local_table.c.version)


class Versioned(object):
    @declared_attr
    def __mapper_cls__(cls):
        def map(cls, *arg, **kw):
            mp = mapper(cls, *arg, **kw)
            _history_mapper(mp)
            return mp
        return map


def versioned_objects(iter):
    for obj in iter:
        if hasattr(obj, '__history_mapper__'):
            yield obj

def create_version(obj, session, before_flush = False, deleted = False, new = False):
    obj_mapper = object_mapper(obj)
    history_mapper = obj.__history_mapper__
    history_cls = history_mapper.class_

    obj_state = attributes.instance_state(obj)

    attr = {}

    obj_changed = False

    for om, hm in zip(obj_mapper.iterate_to_root(), history_mapper.iterate_to_root()):
        if hm.single:
            continue

        for hist_col in hm.local_table.c:
            if hist_col.key in ['version', 'created']:
                continue
            
            obj_col = om.local_table.c[hist_col.key]

            # get the value of the
            # attribute based on the MapperProperty related to the
            # mapped column.  this will allow usage of MapperProperties
            # that have a different keyname than that of the mapped column.
            try:
                prop = obj_mapper.get_property_by_column(obj_col)
            except UnmappedColumnError:
                # in the case of single table inheritance, there may be 
                # columns on the mapped table intended for the subclass only.
                # the "unmapped" status of the subclass column on the 
                # base class is a feature of the declarative module as of sqla 0.5.2.
                continue

            # expired object attributes and also deferred cols might not be in the
            # dict.  force it to load no matter what by using getattr().
            if prop.key not in obj_state.dict:
                getattr(obj, prop.key)

            a, u, d = attributes.get_history(obj, prop.key)

            c = attributes.get_attribute(obj, prop.key)

            if d:
                attr[hist_col.key] = c
                obj_changed = True
            elif u:
                attr[hist_col.key] = c
            else:
                # if the attribute had no value.
                attr[hist_col.key] = c
                obj_changed = True

    if not obj_changed:
        # not changed, but we have relationships.  OK
        # check those too
        for prop in obj_mapper.iterate_properties:
            if isinstance(prop, RelationshipProperty) and \
                attributes.get_history(obj, prop.key).has_changes():
                obj_changed = True
                break

    if not obj_changed and not deleted and not new:
        return
    if before_flush:
        obj.version += 1
        return
        
    attr['version'] = obj.version
    hist = history_cls()
    for key, value in attr.iteritems():
        setattr(hist, key, value)

    if deleted:
        action = 'delete'
    elif new:
        action = 'create'
    else:
        action = 'update'

    from zabalaza.apps.words.models import Change

    change = Change(
        row_id=obj.id,
        word_id=obj.dependant_word_id,
        version=obj.version,
        model=obj.__class__.__name__,
        action=action
    )
    session.add(change)
    # if new:
    #     hist.version = 0
    session.add(hist)
    obj.version += 1
    session.add(obj)

def versioned_session(session):
    @event.listens_for(session, 'after_flush')
    def after_flush(session, flush_context):
        for obj in versioned_objects(session.dirty):
            create_version(obj, session)
        for obj in versioned_objects(session.deleted):
            create_version(obj, session, deleted = True)
        for obj in versioned_objects(session.new):
            create_version(obj, session, new = True)
    @event.listens_for(session, 'before_flush')
    def before_flush(session, flush_context, instances):
        for obj in versioned_objects(session.dirty):
            create_version(obj, session, before_flush=True)
        for obj in versioned_objects(session.deleted):
            create_version(obj, session, deleted = True, before_flush=True)
            

            
