# auto-generated by elastipy/query/generator.py on 2020-12-31

from .query import Query, QueryInterface


class Match(Query):

    name = "match"
    _top_level_parameter = "field"
    _optional_parameters = {
        "auto_generate_synonyms_phrase_query": True,
        "fuzziness": None,
        "max_expansions": 50,
        "prefix_length": 0,
        "fuzzy_transpositions": True,
        "fuzzy_rewrite": None,
        "lenient": False,
        "operator": None,
        "minimum_should_match": None,
        "zero_terms_query": 'none',
    }

    def __init__(
            self,
            field: str,
            query: str,
            auto_generate_synonyms_phrase_query: bool=True,
            fuzziness: str=None,
            max_expansions: int=50,
            prefix_length: int=0,
            fuzzy_transpositions: bool=True,
            fuzzy_rewrite: str=None,
            lenient: bool=False,
            operator: str=None,
            minimum_should_match: str=None,
            zero_terms_query: str='none',
    ):
        """
        Returns documents that match a provided text, number, date or boolean
        value. The provided text is analyzed before matching.

        The match query is the standard query for performing a full-text search,
        including options for fuzzy matching.

        See: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-match-query.html
        :param field: str
            Field you wish to search.

        :param query: str
            Text, number, boolean value or date you wish to find in the provided
            <field>.

            The match query analyzes any provided text before performing a
            search. This means the match query can search text fields for
            analyzed tokens rather than an exact term.

        :param auto_generate_synonyms_phrase_query: bool
            If true, match phrase queries are automatically created for
            multi-term synonyms. Defaults to true.

        :param fuzziness: str
            Maximum edit distance allowed for matching. See Fuzziness for valid
            values and more information. See Fuzziness in the match query for an
            example.

        :param max_expansions: int
            Maximum number of terms to which the query will expand. Defaults to
            50. 

        :param prefix_length: int
            Number of beginning characters left unchanged for fuzzy matching.
            Defaults to 0. 

        :param fuzzy_transpositions: bool
            If true, edits for fuzzy matching include transpositions of two
            adjacent characters (ab → ba). Defaults to true.

        :param fuzzy_rewrite: str
            Method used to rewrite the query. See the rewrite parameter for
            valid values and more information.

            If the fuzziness parameter is not 0, the match query uses a
            fuzzy_rewrite method of top_terms_blended_freqs_${max_expansions} by
            default.

        :param lenient: bool
            If true, format-based errors, such as providing a text query value
            for a numeric field, are ignored. Defaults to false. 

        :param operator: str
            Boolean logic used to interpret text in the query value. Valid
            values are:
                OR (Default)
                    For example, a query value of capital of Hungary is
                    interpreted as capital OR of OR Hungary. 
                AND
                    For example, a query value of capital of Hungary is
                    interpreted as capital AND of AND Hungary. 

        :param minimum_should_match: str
            Minimum number of clauses that must match for a document to be
            returned. See the minimum_should_match parameter for valid values
            and more information.

        :param zero_terms_query: str
            Indicates whether no documents are returned if the analyzer removes
            all tokens, such as when using a stop filter. Valid values are:
                none (Default)
                    No documents are returned if the analyzer removes all
                    tokens.
                all
                    Returns all documents, similar to a match_all query. 
        """
        super().__init__(
            field=field,
            query=query,
            auto_generate_synonyms_phrase_query=auto_generate_synonyms_phrase_query,
            fuzziness=fuzziness,
            max_expansions=max_expansions,
            prefix_length=prefix_length,
            fuzzy_transpositions=fuzzy_transpositions,
            fuzzy_rewrite=fuzzy_rewrite,
            lenient=lenient,
            operator=operator,
            minimum_should_match=minimum_should_match,
            zero_terms_query=zero_terms_query,
        )


class MatchAll(Query):

    name = "match_all"
    _optional_parameters = {
        "boost": None,
    }

    def __init__(
            self,
            boost: float=None,
    ):
        """
        The most simple query, which matches all documents, giving them all a
        _score of 1.0.

        The _score can be changed with the boost parameter

        See: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-match-all-query.html
        :param boost: float
            The _score can be changed with the boost parameter
        """
        super().__init__(
            boost=boost,
        )


class MatchNone(Query):

    name = "match_none"
    _optional_parameters = {
    }

    def __init__(
            self,
    ):
        """
        This is the inverse of the match_all query, which matches no documents.

        See: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-match-all-query.html        """
        super().__init__(
        )


class Term(Query):

    name = "term"
    _top_level_parameter = "field"
    _optional_parameters = {
        "boost": None,
        "case_insensitive": None,
    }

    def __init__(
            self,
            field: str,
            value: str,
            boost: float=None,
            case_insensitive: bool=None,
    ):
        """
        Returns documents that contain an exact term in a provided field.

        You can use the term query to find documents based on a precise value
        such as a price, a product ID, or a username.

        See: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-term-query.html
        :param field: str
            Field you wish to search.

        :param value: str
            Term you wish to find in the provided <field>. To return a document,
            the term must exactly match the field value, including whitespace
            and capitalization.

        :param boost: float
            Floating point number used to decrease or increase the relevance
            scores of a query. Defaults to 1.0.

            You can use the boost parameter to adjust relevance scores for
            searches containing two or more queries.

            Boost values are relative to the default value of 1.0. A boost value
            between 0 and 1.0 decreases the relevance score. A value greater
            than 1.0 increases the relevance score.

        :param case_insensitive: bool
            allows ASCII case insensitive matching of the value with the indexed
            field values when set to true. Default is false which means the case
            sensitivity of matching depends on the underlying field’s mapping.
        """
        super().__init__(
            field=field,
            value=value,
            boost=boost,
            case_insensitive=case_insensitive,
        )


class Terms(Query):

    name = "terms"
    _top_level_parameter = "field"
    _optional_parameters = {
        "boost": None,
    }

    def __init__(
            self,
            field: str,
            value: str,
            boost: float=None,
    ):
        """
        Returns documents that contain one or more exact terms in a provided
        field.

        The terms query is the same as the term query, except you can search for
        multiple values.

        See: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-terms-query.html
        :param field: str
            Field you wish to search.

        :param value: str
            The value of this parameter is an array of terms you wish to find in
            the provided field. To return a document, one or more terms must
            exactly match a field value, including whitespace and
            capitalization.

            By default, Elasticsearch limits the terms query to a maximum of
            65,536 terms. You can change this limit using the
            index.max_terms_count setting.

        :param boost: float
            Floating point number used to decrease or increase the relevance
            scores of a query. Defaults to 1.0.

            You can use the boost parameter to adjust relevance scores for
            searches containing two or more queries.

            Boost values are relative to the default value of 1.0. A boost value
            between 0 and 1.0 decreases the relevance score. A value greater
            than 1.0 increases the relevance score.
        """
        super().__init__(
            field=field,
            value=value,
            boost=boost,
        )

