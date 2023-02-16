from connectors.core.connector import get_logger, ConnectorError
from .constants import LOGGER_NAME
import arrow
logger = get_logger(LOGGER_NAME)

def assemble_query_time_windows(config, params):
    relative_date = params.get('relativeDate')
    period = params.get('period')
    date_format = params.get('dateFormat', 'YYYY-MM-DDTHH:mm:ss.SSS[Z]')
    existing_times = params.get('times', [])
    query_modified = params.get('queryModified', False)

    start_time, end_time = handleRelativeDate(relative_date, period)

    if existing_times and not query_modified:
        # Find the index of the first time in the exiting time stamps which is >= to the calculated start time
        first_bucket_index = 0
        column_heading_present = False
        try:
            arrow.get(existing_times[first_bucket_index])
        except arrow.parser.ParserError:
            first_bucket_index = 1
            column_heading_present = True
        try:
            while arrow.get(existing_times[first_bucket_index]) < start_time:
                first_bucket_index += 1
        except arrow.parser.ParserError as e:
            logger.error("Arrow library could not parse the object {}".format(existing_times[first_bucket_index]))
            raise ConnectorError("Arrow library could not parse the object {}".format(existing_times[first_bucket_index]))
        
        # Strip out all times less than the calculated start time
        existing_times = existing_times[first_bucket_index:]
        first_record_to_keep_index = first_bucket_index if column_heading_present else first_bucket_index + 1

        # We will always re-query the last time window from the existing chart
        # because it likely represents an incomplete time window. After that, keep applying the 
        # time period shift until a timestamp is found which is after the "end time" of the chart
        last_timebucket = existing_times[-1]
        time_buckets_to_query = [{'start': last_timebucket}]
        last_timebucket = arrow.get(last_timebucket)
        if last_timebucket < end_time:
            time_buckets_to_query[0]['end'] = shift_time(last_timebucket,  period).format(date_format)
        while arrow.get(time_buckets_to_query[-1]['end']) < end_time:
            new_bucket = {'start': time_buckets_to_query[-1]['end']}
            new_endtime = shift_time(arrow.get(time_buckets_to_query[-1]['end']), period)
            new_bucket['end'] = new_endtime.format(date_format) if new_endtime < end_time else end_time.format(date_format)
            time_buckets_to_query.append(new_bucket)
        return {"query_buckets": time_buckets_to_query, "mode": "update_buckets", "first_index_to_keep": first_record_to_keep_index}
    else:
        # When no existing data is present, we just take the start time and apply
        # the time period shift until a timestamp is reached which is past the 
        # chart's end time
        time_buckets = []
        time_slider = start_time
        while time_slider < end_time:
            new_bucket = {'start': time_slider.format(date_format)}
            time_slider = shift_time(time_slider, period)
            new_bucket['end'] = time_slider.format(date_format) if time_slider < end_time else end_time.format(date_format)
            time_buckets.append(new_bucket)
        return {'query_buckets': time_buckets, 'mode': 'new_chart', 'first_index_to_keep': None}
  
def shift_time(t, period):
    new_t = t
    if period=="Hourly":
        new_t = t.shift(hours=1)
    elif period=="Daily":
        new_t = t.shift(days=1)
    elif period == "Weekly":
        new_t = t.shift(weeks=1)
    elif period == "Montly":
        new_t = t.shift(months=1)
    elif period == "Quarterly":
        new_t = t.shift(months=3)
    elif period == "Yearly":
        new_t = t.shift(years=1)
    return new_t

def handleRelativeDate(relDate, period):
    pbStartTime = arrow.get().replace(second=0, microsecond=0)
    if "differenceType" in relDate:
        differenceValue = relDate['differenceValue']
        differenceType = relDate['differenceType']
        startDate = pbStartTime
        endDate = pbStartTime
        if differenceType == 'mins':
            differenceType = 'minutes'
        if differenceValue < 0:
            # start date is going to be shifted back by differenceValue units, end date is now
            startDate = endDate.shift(**{differenceType: differenceValue})
        elif differenceValue == 0:
            # "this" date. start date will be the start of this unit, end date is now
            if differenceType == 'minutes':
                startDate = endDate.replace(second=0,microsecond=0)
            if differenceType == 'hours':
                startDate = endDate.replace(minute=0, second=0,microsecond=0)
            elif differenceType == "days":
                startDate = endDate.replace(hour=0,minute=0,second=0,microsecond=0)
            elif differenceType == "months":
                startDate = endDate.replace(day=1, hour=0,minute=0,second=0,microsecond=0)
            elif differenceType == 'years':
                startDate = endDate.replace(month=1, day=1, hour=0,minute=0,second=0,microsecond=0)
        elif differenceValue > 0:
            #future date. Start date is now, end date is shifted forward by differenceValue uniits
            endDate = startDate.shift(**{differenceType: differenceValue})
        return startDate, endDate