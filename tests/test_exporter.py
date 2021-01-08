import datetime
from copy import copy
import unittest

from elastipy import Search, query, Exporter


# some basic fields, and no id
# a document transform adds the current time
#   (actually for test stability, it uses a fixed increase)
class TestExporter(Exporter):
    INDEX_NAME = "elastipy---unittest-exporter-no-id"
    MAPPINGS = {
        "properties": {
            "id": {"type": "long"},
            "string": {"type": "text"},
            "number": {"type": "float"},
            "tag": {"type": "keyword"},
            "timestamp": {"type": "date"},
        }
    }

    timestamp = datetime.datetime.now()

    def transform_document(self, data):
        data = copy(data)
        data["timestamp"] = self.timestamp
        self.timestamp += datetime.timedelta(seconds=1)
        return data


# this has a fixed elasticsearch id, depending on the source document
class TestExporterWithId(TestExporter):
    INDEX_NAME = "elastipy---unittest-exporter-id"

    def get_document_id(self, es_data):
        return es_data["id"]


# this exporter actually exports two documents for each input document
class TestExporterMulti(TestExporter):
    INDEX_NAME = "elastipy---unittest-exporter-multi"

    def transform_document(self, data):
        data = super().transform_document(data)
        data["number"] = 1
        yield data
        data["number"] = 2
        yield data


# here each replicated document get's it's own id
class TestExporterMultiWithId(TestExporterMulti):
    INDEX_NAME = "elastipy---unittest-exporter-multi-id"

    def get_document_id(self, es_data):
        return "%(id)s-%(number)s" % es_data


class TestTheExporter(unittest.TestCase):

    def assertDocuments(self, documents, response):
        self.assertEqual(len(documents), len(response.documents))
        for expected_doc, doc in zip(documents, response.documents):
            doc = copy(doc)
            doc.pop("timestamp")
            self.assertEqual(expected_doc, doc)

    def test_create_update_no_id(self):
        exporter = TestExporter()
        exporter.update_index()
        try:
            exporter.export_list([{"id": 0}, {"id": 1}], refresh=True)
            self.assertDocuments(
                [{"id": 0}, {"id": 1}],
                exporter.search().execute(),
            )

            exporter.export_list([{"id": 2}], refresh=True)
            self.assertDocuments(
                [{"id": 0}, {"id": 1}, {"id": 2}],
                exporter.search().sort("timestamp").execute(),
            )

            exporter.export_list([{"id": 0, "string": "hello"}, {"id": 1, "tag": "python"}], refresh=True)
            self.assertDocuments(
                [{"id": 0}, {"id": 1}, {"id": 2}, {"id": 0, "string": "hello"}, {"id": 1, "tag": "python"}],
                exporter.search().sort("timestamp").execute(),
            )

            exporter.export_list([{"id": 0}, {"id": 1}], refresh=True)
            self.assertDocuments(
                [{"id": 0}, {"id": 1}, {"id": 2}, {"id": 0, "string": "hello"}, {"id": 1, "tag": "python"}, {"id": 0}, {"id": 1}],
                exporter.search().sort("timestamp").execute(),
            )

        finally:
            exporter.delete_index()

    def test_create_update_id(self):
        exporter = TestExporterWithId()
        exporter.update_index()
        try:
            exporter.export_list([{"id": 0}, {"id": 1}], refresh=True)
            self.assertDocuments(
                [{"id": 0}, {"id": 1}],
                exporter.search().sort("timestamp").execute(),
            )

            exporter.export_list([{"id": 2}], refresh=True)
            self.assertDocuments(
                [{"id": 0}, {"id": 1}, {"id": 2}],
                exporter.search().sort("timestamp").execute(),
            )

            exporter.export_list([{"id": 0, "string": "hello"}, {"id": 1, "tag": "python"}], refresh=True)
            self.assertDocuments(
                [{"id": 2}, {"id": 0, "string": "hello"}, {"id": 1, "tag": "python"}],
                exporter.search().sort("timestamp").execute(),
            )

            exporter.export_list([{"id": 0}, {"id": 1}], refresh=True)
            self.assertDocuments(
                [{"id": 2}, {"id": 0}, {"id": 1}],
                exporter.search().sort("timestamp").execute(),
            )

        finally:
            exporter.delete_index()

    def test_create_update_multi(self):
        exporter = TestExporterMulti()
        exporter.update_index()
        try:
            exporter.export_list([{"id": 0}, {"id": 1}], refresh=True)
            self.assertDocuments(
                [{"id": 0, "number": 1}, {"id": 0, "number": 2},
                 {"id": 1, "number": 1}, {"id": 1, "number": 2}],
                exporter.search().sort("timestamp").execute(),
            )

            exporter.export_list([{"id": 0}], refresh=True)
            self.assertDocuments(
                [{"id": 0, "number": 1}, {"id": 0, "number": 2},
                 {"id": 1, "number": 1}, {"id": 1, "number": 2},
                 {"id": 0, "number": 1}, {"id": 0, "number": 2}],
                exporter.search().sort("timestamp").execute(),
            )

        finally:
            exporter.delete_index()

    def test_create_update_multi_id(self):
        exporter = TestExporterMultiWithId()
        exporter.update_index()
        try:
            exporter.export_list([{"id": 0}, {"id": 1}], refresh=True)
            self.assertDocuments(
                [{"id": 0, "number": 1}, {"id": 0, "number": 2},
                 {"id": 1, "number": 1}, {"id": 1, "number": 2}],
                exporter.search().sort("timestamp").execute(),
            )

            exporter.export_list([{"id": 0}], refresh=True)
            self.assertDocuments(
                [{"id": 1, "number": 1}, {"id": 1, "number": 2},
                 {"id": 0, "number": 1}, {"id": 0, "number": 2}],
                exporter.search().sort("timestamp").execute(),
            )

        finally:
            exporter.delete_index()


if __name__ == "__main__":
    unittest.main()
