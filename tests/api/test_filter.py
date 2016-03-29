# external imports
import unittest
# local imports
import nautilus
import nautilus.models as models
from nautilus.api.filter import args_for_model, filter_model

class TestUtil(unittest.TestCase):

    def setUp(self):
        # the model to test
        class TestModel(models.BaseModel):
            first_name = models.fields.CharField()
            last_name = models.fields.CharField()

        # save a reference to the test model
        self.model = TestModel
        # generate the arguments for the model
        self.args = args_for_model(TestModel)
        # create a set out of the arguments
        self.arg_names = set(self.args.keys())

        # create a database table to test on
        nautilus.db.create_table(self.model)


    def tearDown(self):
        # remove the test table
        nautilus.db.drop_table(self.model)


    def test_args_match_model(self):
        # make sure the argument contain the model fields
        assert self.arg_names >= {field.name for field in self.model.fields()}, (
            "Generated args do not contain model fields"
        )


    def test_args_have_primary_key_attr(self):
        # make sure there is a pk arg
        assert 'pk' in self.arg_names, (
            "Generated args doesn't have a pk filter."
        )


    def test_args_has_oneof_filter(self):
        # the filters we would exepect for the contains arg
        contains_filter_args = {'first_name_in', 'last_name_in', 'pk_in'}
        # make sure the arguments exist for the contains filter
        assert self.arg_names >= contains_filter_args, (
            "Generated args do not have contains filter."
        )


    def test_can_filter_by_field(self):
        # some test records
        record1 = self.model(first_name='foo', last_name='bar')
        record2 = self.model(first_name='bar', last_name='foo')
        # save the record to the database
        record1.save()
        record2.save()

        # the argument to filter for
        filter_args = dict(first_name=record1.first_name)
        # filter the models
        records_filtered = filter_model(self.model, filter_args)

        # make sure only one record was returned
        assert len(records_filtered) == 1, (
            "More than one record was returned by filter."
        )

        # pull out the retrieved record
        retrieved_record = records_filtered[0]
        # make sure the first name matches
        assert retrieved_record.first_name == record1.first_name, (
            "The wrong record was retrieved."
        )


    def test_can_filter_by_contains(self):
        # some test records
        record1 = self.model(first_name='foo', last_name='bar')
        record2 = self.model(first_name='bar', last_name='foo')
        # save the record to the database
        record1.save()
        record2.save()

        # the argument to filter for
        filter_args = dict(first_name_in=[record1.first_name, record2.first_name])
        # filter the models
        records_filtered = filter_model(self.model, filter_args)

        # make sure only one record was returned
        assert len(records_filtered) == 2, (
            "More than one record was returned by filter."
        )

        # figure out the names of the records we retrieved
        retrieved_names = {record.first_name for record in records_filtered}

        # make sure the first name matches
        assert retrieved_names == {record1.first_name, record2.first_name}, (
            "The wrong record was retrieved."
        )

    def gen_test_data(self):
        # some test records
        i = 1
        while i < 10:
            record = self.model(first_name='foo%s' % (i), last_name='bar')
            record.save()
            record = self.model(first_name='bar%s' % (i), last_name='foo')
            record.save()
            i +=1

    def test_can_handle_first(self):
        self.gen_test_data()
        # the argument to filter for
        filter_args = dict(first=2, offset=0)
        # filter the models
        records_filtered = filter_model(self.model, filter_args)

        # figure out the names of the records we retrieved
        retrieved_names = [record.first_name for record in records_filtered]
        expected = ['foo1', 'bar1']
        assert retrieved_names == expected, (
            "Wrong first records retrieved: %(retrieved_names)s instead of %(expected)s" % locals()
        )

    def test_can_handle_last(self):
        self.gen_test_data()
        # the argument to filter for
        filter_args = dict(last=2, offset=0)
        # filter the models
        records_filtered = filter_model(self.model, filter_args)

        # figure out the names of the records we retrieved
        retrieved_names = [record.first_name for record in records_filtered]
        expected = ['bar9', 'foo9']
        assert retrieved_names == expected, (
            "Wrong last records retrieved: %(retrieved_names)s instead of %(expected)s" % locals()
        )

    def test_can_handle_last_offset(self):
        self.gen_test_data()
        # the argument to filter for
        filter_args = dict(last=2, offset=2)
        # filter the models
        records_filtered = filter_model(self.model, filter_args)

        # figure out the names of the records we retrieved
        retrieved_names = [record.first_name for record in records_filtered]
        expected = ['bar8', 'foo8']
        assert retrieved_names == expected, (
            "Wrong last offset records retrieved: %(retrieved_names)s instead of %(expected)s" % locals()
        )

    def test_can_handle_first_offset(self):
        self.gen_test_data()
        # the argument to filter for
        filter_args = dict(first=4, offset=2)
        # filter the models
        records_filtered = filter_model(self.model, filter_args)

        # figure out the names of the records we retrieved
        retrieved_names = [record.first_name for record in records_filtered]
        expected = ['foo2', 'bar2', 'foo3', 'bar3']
        assert retrieved_names == expected, (
            "Wrong first offset records retrieved: %(retrieved_names)s instead of %(expected)s" % locals()
        )

    def test_can_handle_first_offset_order_by(self):
        self.gen_test_data()
        # the argument to filter for
        filter_args = dict(first=4, offset=2, order_by="last_name, -first_name")
        # filter the models
        records_filtered = filter_model(self.model, filter_args)

        # figure out the names of the records we retrieved
        retrieved_names = [record.first_name for record in records_filtered]
        expected = ['foo7', 'foo6', 'foo5', 'foo4']
        assert retrieved_names == expected, (
            "Wrong first offset records retrieved: %(retrieved_names)s instead of %(expected)s" % locals()
        )
