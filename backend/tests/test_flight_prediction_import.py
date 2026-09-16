from datetime import date

from scripts.import_flight_predictions_csv import transform_prediction_row


def test_transform_prediction_row_maps_city_and_airline_names():
    row = {
        "ID": "42",
        "airline": "Air_India",
        "flight": "AI-887",
        "source_city": "Delhi",
        "departure_time": "Morning",
        "stops": "zero",
        "arrival_time": "Afternoon",
        "destination_city": "Mumbai",
        "class": "Economy",
        "duration": "2.25",
        "days_left": "7",
        "price": "5955",
    }

    transformed = transform_prediction_row(row, reference_date=date(2026, 9, 16))

    assert transformed["route_code"] == "DEL-BOM"
    assert transformed["airline_code"] == "AI"
    assert transformed["travel_date"] == date(2026, 9, 23)
    assert transformed["advance_days"] == 7
    assert transformed["total_fare"] == 5955
    assert transformed["flight_number"] == "AI-887"
