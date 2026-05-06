from sqlalchemy import text
def get_latest_order(engine_track):
    sql = """
    SELECT TOP 1
        CURRENT_STATUSCODE,
        EXPECTED_DELIVERYDATE,
        L_NAMELINE1,
        U_NAMELINE1,
        L_ADDRESSLINE1,
        U_ADDRESSLINE1,
        L_ZIPCODE,
        U_ZIPCODE,
        L_CITY,
        U_CITY,
        L_COUNTRY_FULL,
        U_COUNTRY_FULL
    FROM [BRING].[v_dossiers]
    WHERE PRIMARYREFERENCE IS NOT NULL
    ORDER BY INTERNALNUMBER DESC
    """

    with engine_track.connect() as conn:
        result = conn.execute(text(sql))
        row = result.fetchone()
        columns = result.keys()

    if not row:
        return "No result found"

    data = dict(zip(columns, row))

    return f"""Status: {data.get('CURRENT_STATUSCODE')}
Expected deliveryday: {data.get('EXPECTED_DELIVERYDATE')}

Loading Address:
Name: {data.get('L_NAMELINE1')}
Addressline1: {data.get('L_ADDRESSLINE1')}
Zipcode: {data.get('L_ZIPCODE')}
City: {data.get('L_CITY')}
Country: {data.get('L_COUNTRY_FULL')}

Unloading Address:
Name: {data.get('U_NAMELINE1')}
Addressline1: {data.get('U_ADDRESSLINE1')}
Zipcode: {data.get('U_ZIPCODE')}
City: {data.get('U_CITY')}
Country: {data.get('U_COUNTRY_FULL')}"""