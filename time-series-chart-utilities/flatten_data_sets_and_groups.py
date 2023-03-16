from connectors.core.connector import get_logger, ConnectorError
from .constants import LOGGER_NAME
logger = get_logger(LOGGER_NAME)


def flatten_data_sets_and_groups(config, params):
    data_sets = params.get('dataSets')
    dataSetResults, groups, types = flatten_datasets(data_sets)
    return {'dataSets': dataSetResults, 'groups':groups, 'types': types}

# Chart datasets can be individual or nested. We need to flatten them into a single list of individual
# datasets, while maintaining record of which datasets are meant to be grouped together.
def flatten_datasets(dataSets, group=False):
    queries = []
    groups = []
    types = {}
    for dataSet in dataSets:
        title = dataSet['title']
        plotType = dataSet.get('plotType', None)
        if "query" in dataSet and len(dataSet["query"]) > 0:
            queries.append(dataSet)
            if group:
                groups.append(title)
            if plotType and plotType != 'Bar':
                if 'groupingFieldOptions' in dataSet:
                    for option in dataSet['groupingFieldOptions']:
                        types[dataSet['title'] + ' - ' + option] = plotType.lower()
                else:
                    types[dataSet['title']] = plotType.lower()
            continue
        elif "dataSets" in dataSet:
            subqueries, grouped_queries, subTypes = flatten_datasets(dataSet['dataSets'], group=True)
            queries = queries + subqueries
            groups.append(grouped_queries)
    return queries, groups, types