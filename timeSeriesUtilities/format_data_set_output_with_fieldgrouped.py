from connectors.core.connector import get_logger, ConnectorError
from .constants import LOGGER_NAME
logger = get_logger(LOGGER_NAME)


def format_data_set_output_with_fieldgrouped(config, params):
    result_dict = {}
    query_results = params.get('queryOutput')
    time_buckets = params.get('timeBucketsQueried')
    data_set = params.get('dataSetConfiguration')

    category_key = data_set['groupingField']
    for option_value in data_set['groupingFieldOptions']:
        result_dict[option_value] = [data_set['title'] + ' - ' + option_value]

    for i in range(0, len(time_buckets)):
        # Check query result corresponding to time bucket i
        tw_result = query_results[i]['data']
        # If there are no results for that bucket, move on to next bucket
        if len(tw_result['hydra:member']) == 0:
            for option_list in result_dict.values():
                option_list.append(0)
            continue
        for sub_result in tw_result['hydra:member']:
            # If resulting dictionary doesnt have a list for this value of the category key (eg. High if the grouping field is severity)
            # then a new element needs to be added to the result dictionary
            if sub_result[category_key] not in result_dict:
                result_dict[sub_result[category_key]] = [data_set['title'] + " - " + sub_result[category_key]]
            # Whenever a grouped field value should have 0 results, that value is omitted from the query results
            # Thus the next time that value occurs, it needs to "catch up" to the rest of the lists by populating its list
            # with zeros. We use i+1 as the comparator here because the result list will have an extra element for the list "title".
            while len(result_dict[sub_result[category_key]]) < i+1:
                result_dict[sub_result[category_key]].append(0)
            # After "catching up" if needed, we add the actual value for this time bucket to the result dictionary
            result_dict[sub_result[category_key]].append(sub_result['total'])
    # Finally, need to add trailing zeros to any list which does not contain the correct number of values
    for k, v in result_dict.items():
        while len(v) < len(time_buckets)+1:
            v.append(0)
    return list(result_dict.values())