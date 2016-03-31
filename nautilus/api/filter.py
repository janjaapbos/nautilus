# external imports
from graphene import List
from graphene.core.types.scalars import Int, String

# local imports
from nautilus.contrib.graphene_peewee import convert_peewee_field

def args_for_model(Model):
    # the attribute arguments (no filters)
    args = { field.name.lower() : convert_peewee_field(field) \
                                        for field in Model.fields() }

    # add the primary key filter

    # the primary keys for the Model
    primary_key = Model.primary_key()
    # add the primary key filter to the arg dictionary
    args['pk'] = convert_peewee_field(primary_key)

    # create a copy of the argument dict we can mutate
    fullArgs = args.copy()

    # todo: add type-specific filters
    # go over the arguments
    for arg, field_type in args.items():
        # add the list member filter
        fullArgs[arg + '_in'] = List(field_type)

    for k in ['first', 'last', 'offset']:
        fullArgs[k] = Int()
    for k in ['order_by']:
        fullArgs[k] = String()

    # return the complete dictionary of arguments
    return fullArgs

def parse_order_by(Model, order_by):
    out = []
    order_by = order_by.split(",")
    for key in order_by:
       key = key.strip()
       if key.startswith("+"):
           out.append(getattr(Model, key[1:]))
       elif key.startswith("-"):
           out.append(getattr(Model, key[1:]).desc())
       else:
           out.append(getattr(Model, key))
    return out

def filter_model(Model, args):

    first = last = offset = order_by = None

    # convert any args referencing pk to the actual field
    keys = [key.replace('pk', Model.primary_key().name) for key in args.keys()]

    # start off with the full list of Models
    models = Model.select()
    # for each argument
    for arg, value in zip(keys, args.values()):
        if arg == "first":
            first = value
        elif arg == "last":
            last = value
        elif arg == "offset":
            offset = value
        elif arg == "order_by":
            order_by = value
        # if the filter is for a group of values
        elif isinstance(value, list):
            model_attribute = getattr(Model, arg[:-3])
            # filter the query
            models = models.where(model_attribute.in_(value))
        else:
            # filter the argument
            models = models.where(getattr(Model, arg) == value)

    if first:
        if order_by is None:
            order_by = "+" + Model.primary_key().name
        order_by = parse_order_by(Model, order_by)
        models = models.order_by(*order_by)
        if offset:
            models = models.offset(offset)
        models = models.limit(first)
    elif last:
        if order_by is None:
            order_by = "-" + Model.primary_key().name
        order_by = parse_order_by(Model, order_by)
        models = models.order_by(*order_by)
        if offset:
            models = models.offset(offset)
        models = models.limit(last)
    elif order_by:
        order_by = parse_order_by(Model, order_by)
        models = models.order_by(*order_by)

    # return the filtered list
    return list(models)
