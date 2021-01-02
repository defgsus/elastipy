import datetime
import json
import time
import unittest

import elasticsearch

from elastipy import get_elastic_client, Search, query

from . import data


class TestOrdersAggregations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = int(1e5)
        cls.client = get_elastic_client()
        data.export_data(data.orders.orders1, data.orders.OrderExporter, cls.client)
        time.sleep(1.1)  # give time to update index

    @classmethod
    def tearDownClass(cls):
        data.orders.OrderExporter(client=cls.client).delete_index()

    def search(self):
        return Search(index=data.orders.OrderExporter.INDEX_NAME, client=self.client)

    def test_orders_terms_sku(self):
        q = self.search()
        agg_sku_count = q.agg_terms(field="sku")
        agg_sku_qty = agg_sku_count.metric_sum(field="quantity")

        #q.dump_body()
        q.execute()#.dump()

        self.assertEqual(
            {
                "sku-1": 4,
                "sku-2": 2,
                "sku-3": 1,
            },
            agg_sku_count.to_dict()
        )
        self.assertEqual(
            {
                "sku-1": 7,
                "sku-2": 3,
                "sku-3": 5,
            },
            agg_sku_qty.to_dict()
        )

    def test_orders_terms_sku_terms_channel(self):
        q = self.search()
        agg_sku = q.agg_terms(field="sku")
        agg_channel = agg_sku.agg_terms(field="channel")
        agg_qty = agg_channel.metric_sum(field="quantity")

        q.execute()# .dump()

        self.assertEqual(
            {
                ("sku-1", "the-shop"): 2,
                ("sku-1", "the-sale"): 1,
                ("sku-1", "the-end"): 1,
                ("sku-2", "the-shop"): 1,
                ("sku-2", "the-sale"): 1,
                ("sku-3", "the-end"): 1,
            },
            agg_channel.to_dict()
        )

        self.assertEqual(
            {
                ("sku-1", "the-shop"): 3,
                ("sku-1", "the-sale"): 3,
                ("sku-1", "the-end"): 1,
                ("sku-2", "the-shop"): 2,
                ("sku-2", "the-sale"): 1,
                ("sku-3", "the-end"): 5,
            },
            agg_qty.to_dict()
        )

    def test_orders_terms_sku_terms_channel_terms_country(self):
        q = self.search()
        agg_sku = q.agg_terms(field="sku")
        agg_channel = agg_sku.aggregation("terms", field="channel")
        agg_country = agg_channel.aggregation("terms", field="country")
        agg_qty = agg_country.metric("sum", field="quantity")

        q.execute()#.dump()

        self.assertEqual(
            {
                ("sku-1", "the-shop", "DE"): 1,
                ("sku-1", "the-shop", "GB"): 2,
                ("sku-1", "the-sale", "DE"): 3,
                ("sku-1", "the-end",  "GB"): 1,
                ("sku-2", "the-shop", "DE"): 2,
                ("sku-2", "the-sale", "DE"): 1,
                ("sku-3", "the-end",  "GB"): 5,
            },
            agg_qty.to_dict()
        )
        #agg_qty.dump_table()

    def test_orders_filter(self):
        aggs = [
            self.search().agg_filter(filter={"term": {"sku": "sku-1"}}).metric_sum("qty", field="quantity"),
            self.search().agg_filter(filter=query.Term(field="sku", value="sku-1")).metric_sum("qty", field="quantity"),
        ]
        for agg in aggs:
            #q.dump_body()
            agg.execute()#.dump()

            #agg.dump_table()
            self.assertEqual(
                [
                    ["a0", "a0.doc_count", "qty"],
                    ["a0", 4, 7]
                ],
                list(agg.rows())
            )

    def test_orders_filters(self):
        q = self.search()
        agg_sku = q.agg_filters("group", filters={
            "group1": {"term": {"sku": "sku-1"}},
            "group2": {"term": {"sku": "sku-2"}},
        })
        agg_qty = agg_sku.metric_sum("qty", field="quantity")
        #q.dump_body()
        q.execute()# .dump()

        self.assertEqual(
            [
                ["group", "group.doc_count", "qty"],
                ["group1", 4, 7],
                ["group2", 2, 3],
            ],
            list(agg_qty.rows())
        )

    def test_orders_filters_with_query(self):
        q = self.search()
        agg_sku = q.agg_filters("group", filters={
            "group1": query.Term("sku", "sku-1"),
            "group2": query.Bool(must=[query.Term("sku", "sku-2")]),
        })
        agg_qty = agg_sku.metric_sum("qty", field="quantity")
        #q.dump_body()
        q.execute()# .dump()

        self.assertEqual(
            [
                ["group", "group.doc_count", "qty"],
                ["group1", 4, 7],
                ["group2", 2, 3],
            ],
            list(agg_qty.rows())
        )

    def test_orders_date_histogram(self):
        q = self.search()
        items_per_day = q.agg_date_histogram(field="timestamp", calendar_interval="1d")
        orders_per_day = items_per_day.metric_cardinality(field="order_id")
        #q.dump_body()
        q.execute()#.dump()

        self.assertEqual(
            {
                "2000-01-01T00:00:00.000Z": 2,
                "2000-01-02T00:00:00.000Z": 1,
                "2000-01-03T00:00:00.000Z": 4,
            },
            items_per_day.to_dict()
        )

        self.assertEqual(
            {
                "2000-01-01T00:00:00.000Z": 2,
                "2000-01-02T00:00:00.000Z": 1,
                "2000-01-03T00:00:00.000Z": 2,
            },
            orders_per_day.to_dict()
        )


if __name__ == "__main__":
    unittest.main()
