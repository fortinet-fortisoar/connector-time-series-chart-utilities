from connectors.core.connector import get_logger, ConnectorError
from .constants import LOGGER_NAME
logger = get_logger(LOGGER_NAME)


def combine_query_results_into_data_columns(config, params):
    # This function takes in any existing chart data (input_columns), the
    #  first index numerically to keep in the data (based on the time window
    #  of the chart), the new time buckets to add to the chart, and the results
    #  of the chart queries for those new time buckets, and puts it all together
    #  so that the output is the data columns for all data sets, including
    #  both data that was already in the chart (but is recent enough to not
    #  be left off) and the newly queried data
    dataCols = []
    playbook_mode = params.get('playbookMode')
    first_index = params.get('firstIndexToKeep')
    time_buckets = params.get('queriedTimeBuckets')
    query_results = params.get('queryResults', [])
    input_columns = params.get('existingDataColumns')

    # First remove any "too old" elements from the timestamp column, and then
    # add on the new time buckets which were just queried
    if input_columns and playbook_mode != "new_chart":
        x_col = ['x'] + input_columns[0][first_index:-1] + [tb['start'] for tb in time_buckets]
    else:
        x_col = ['x'] + [tb['start'] for tb in time_buckets]

    # Then remove all the too-old elements from the data lists
    if input_columns and playbook_mode != "new_chart":
        for column in input_columns[1:]:
            newCol = [column[0]]
            newCol += column[first_index:-1]
            dataCols.append(newCol)

    # Run through the results of the new queries
    for qr in query_results:
        try:
            #  if quantities[0] is a string, it means it is a non-field-grouped dataset
            if isinstance(qr['quantities'][0], str):
                handle_query_result_list(qr['quantities'], dataCols, len(x_col))
            # Otherwise quantities[0] will be a list, for field-grouped dataSets
            else:
                for sub_qr in qr['quantities']:
                    handle_query_result_list(sub_qr, dataCols, len(x_col))
        except KeyError as e:
            raise ConnectorError("Expected key 'quantities' not found in query result")
        except IndexError as e:
            raise ConnectorError("'Quantities'  attribute of query result is an empty list.")
    # Finally, run through all the data columns and add trailing zeros to any that need them
    for col in dataCols:
        if len(col) < len(x_col):
            col += [0] * (len(x_col) - len(col))
    return [x_col] + dataCols


def handle_query_result_list(qr_list, dataCols, x_len):
    col_header = qr_list[0]
    matching_column = [col for col in dataCols if col[0]==col_header]
    if matching_column:
        matching_column[0] += qr_list[1:]
    else:
        matching_column = [col_header]
        matching_column += [0] * (x_len - len(qr_list))
        matching_column += qr_list[1:]
        dataCols.append(matching_column)