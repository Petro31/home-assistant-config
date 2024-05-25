
entities = data.get('weather')
ret = []
if entities:
    service_data = {"type": "hourly", "entity_id": entities}
    response = hass.services.call(
        "weather", "get_forecasts", service_data, blocking=True, return_response=True
    )

    combined = {}
    t = dt_util.now().replace(minute=0, second=0, microsecond=0) + datetime.timedelta(days=1, hours=1)

    for entity_id, items in response.items():
        for item in items.get('forecast', []):
            dt = dt_util.as_local(dt_util.parse_datetime(item['datetime']))
            if dt <= t:
                ts = dt.isoformat()
                if ts not in combined:
                    combined[ts] = {}

                for k, v in item.items():
                    if k not in combined[ts]:
                        combined[ts][k] = {}
                    combined[ts][k][entity_id] = v

    for dt in sorted(combined.keys()):
        combined[dt].update(datetime=dt)
        ret.append(combined[dt])

output['forecast'] = ret
