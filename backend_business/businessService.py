import os
import requests
import jwt
from flask import jsonify, request, Blueprint, Response
from datetime import datetime
from dbdef import db, Flight, Bookings, Transfers, Reviews
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

businessService = Blueprint('businessService', __name__)
SECRET_KEY = os.environ.get('SECRET_KEY')

c_booking_search = Counter('counter_for_search', 'This is my counter for /bookings/searchTransfer')
c_booking = Counter('counter_for_register', 'This is my counter for /bookings/bookTransfer')
c_booking_data = Counter('counter_for_login', 'This is my counter for /bookings')
c_booking_delete = Counter('counter_for_check', 'This is my counter for /bookings/deleteBooking')
c_booking_update = Counter('counter_for_delete', 'This is my counter for /bookings/modifyBooking')

@businessService.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

def getTransferCode(queryLocation):
    url = "https://tripadvisor16.p.rapidapi.com/api/v1/flights/searchAirport"

    querystring = {"query":queryLocation}

    headers = {
        "X-RapidAPI-Key": "6c692327f4msh8b44c0051255fa6p11e031jsn6c9f4a6d658d",
        "X-RapidAPI-Host": "tripadvisor16.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    
    if response.status_code == 200:
        flight = response.json()
        if 'data' in flight and flight['data']:
            airport_code = flight['data'][0]['airportCode']
            print(airport_code) 
            return airport_code
        else:
            return ""
    else:
        return ""

@businessService.route('/bookings/searchTransfer', methods=['GET'])
def searchTransfer():
    c_booking_search.inc()
    global flight_info
    sourceAirport = getTransferCode(request.json['source'])
    destinationAirport = getTransferCode(request.json['destination'])

    if not sourceAirport or not destinationAirport:
        return {"error": "Error fetching airport code"}, 404

    url = "https://tripadvisor16.p.rapidapi.com/api/v1/flights/searchFlights"

    querystring = {
        "sourceAirportCode": sourceAirport,
        "destinationAirportCode": destinationAirport,
        "date": request.json['date'],
        "itineraryType": request.json['type'],
        "sortOrder": request.json['order'],
        "numAdults": request.json['adultNumber'],
        "numSeniors": request.json['seniorNumber'],
        "classOfService": request.json['classOfService']
    }

    if request.json['type'] == 'ROUND_TRIP':
        querystring['returnDate'] = request.json['returnDate']

    headers = {
        "X-RapidAPI-Key": "6c692327f4msh8b44c0051255fa6p11e031jsn6c9f4a6d658d",
        "X-RapidAPI-Host": "tripadvisor16.p.rapidapi.com", 
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        data = response.json().get('data', {})
        if data.get('complete') and data.get('flights'):
            flights = data['flights']
            flight_info = []

            for flight in flights:
                segments = flight.get('segments', [])

                if request.json['type'] == "ONE_WAY":
                    for segment in segments:
                        legs = segment.get('legs', [])
                        if legs:
                            leg = legs[0]

                            departure_datetime_str = leg.get('departureDateTime')
                            arrival_datetime_str = leg.get('arrivalDateTime')

                            departure_datetime = datetime.fromisoformat(departure_datetime_str)
                            formatted_departure_datetime = departure_datetime.strftime('%Y-%m-%d %H:%M:%S')

                            arrival_datetime = datetime.fromisoformat(arrival_datetime_str)
                            formatted_arrival_datetime = arrival_datetime.strftime('%Y-%m-%d %H:%M:%S')

                            flight_info.append({
                                'departureDateTime': formatted_departure_datetime,
                                'arrivalDateTime': formatted_arrival_datetime,
                                'flightNumber': leg.get('flightNumber'),
                                'operatingCarrier': leg.get('operatingCarrier', {}).get('displayName')
                            })

                elif request.json['type'] == "ROUND_TRIP":
                    for segment in segments:
                        legs = segment.get('legs', [])

                        if legs:
                            leg = legs[0]

                            departure_datetime_str = leg.get('departureDateTime')
                            arrival_datetime_str = leg.get('arrivalDateTime')

                            departure_datetime = datetime.fromisoformat(departure_datetime_str)
                            formatted_departure_datetime = departure_datetime.strftime('%Y-%m-%d %H:%M:%S')

                            arrival_datetime = datetime.fromisoformat(arrival_datetime_str)
                            formatted_arrival_datetime = arrival_datetime.strftime('%Y-%m-%d %H:%M:%S')

                            way = "INBOUND" if segments.index(segment) == 0 else "OUTBOUND"

                            flight_info.append({
                                'way': way,
                                'departureDateTime': formatted_departure_datetime,
                                'arrivalDateTime': formatted_arrival_datetime,
                                'flightNumber': leg.get('flightNumber'),
                                'operatingCarrier': leg.get('operatingCarrier', {}).get('displayName')
                            })

            return {"flights": flight_info}, 200
        else:
            return {"error": "No flight data available"}, 404
    else:
        return {"error": "Failed to retrieve flight data"}, response.status_code

@businessService.route('/bookings/bookTransfer', methods=['POST'])
def bookTransfer():
    c_booking.inc()
    transfer_data = request.json

    try:
        decoded_token = jwt.decode(transfer_data.get('token'), SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_token.get('user_id')

    except jwt.DecodeError:
        return {"error": "No user with this token :P"}, 404

    if request.json['type'] == "ONE_WAY":
        departure_datetime = transfer_data.get('departureDateTime')
        arrival_datetime = transfer_data.get('arrivalDateTime')
        flight_number = transfer_data.get('flightNumber')
        operating_carrier = transfer_data.get('operatingCarrier')

        source_location = transfer_data.get('source')
        destination_location = transfer_data.get('destination')
        class_of_service = transfer_data.get('classOfService')

        flight = Flight(
            number=flight_number,
            departure_time=departure_datetime,
            arrival_time=arrival_datetime,
            company_name=operating_carrier
        )
        db.session.add(flight)
        db.session.commit()

        transfer = Transfers(
            type=class_of_service,
            source=source_location,
            destination=destination_location,
            flight_id=flight.flight_id
        )
        db.session.add(transfer)
        db.session.commit()

        booking = Bookings(
            flight_id=flight.flight_id,
            user_id=user_id,
            booking_date=datetime.utcnow(),
            payment_status="Done"
        )
        db.session.add(booking)
        db.session.commit()

    elif request.json['type'] == "ROUND_TRIP":
        departure_datetime_inbound = transfer_data.get('departureDateTimeInbound')
        arrival_datetime_inbound = transfer_data.get('arrivalDateTimeInbound')
        flight_number_inbound = transfer_data.get('flightNumberInbound')
        operating_carrier_inbound = transfer_data.get('operatingCarrierInbound')

        source_location_inbound = transfer_data.get('sourceInbound')
        destination_location_inbound = transfer_data.get('destinationInbound')
        class_of_service_inbound = transfer_data.get('classOfServiceInbound')

        flight_inbound = Flight(
            number=flight_number_inbound,
            departure_time=departure_datetime_inbound,
            arrival_time=arrival_datetime_inbound,
            company_name=operating_carrier_inbound
        )
        db.session.add(flight_inbound)
        db.session.commit()

        transfer_inbound = Transfers(
            type=class_of_service_inbound,
            source=source_location_inbound,
            destination=destination_location_inbound,
            flight_id=flight_inbound.flight_id
        )
        db.session.add(transfer_inbound)
        db.session.commit()

        booking_inbound = Bookings(
            flight_id=flight_inbound.flight_id,
            user_id=user_id,
            booking_date=datetime.utcnow(),
            payment_status="Done"
        )
        db.session.add(booking_inbound)
        db.session.commit()

        departure_datetime_outbound = transfer_data.get('departureDateTimeOutbound')
        arrival_datetime_outbound = transfer_data.get('arrivalDateTimeOutbound')
        flight_number_outbound = transfer_data.get('flightNumberOutbound')
        operating_carrier_outbound = transfer_data.get('operatingCarrierOutbound')

        source_location_outbound = transfer_data.get('sourceOutbound')
        destination_location_outbound = transfer_data.get('destinationOutbound')
        class_of_service_outbound = transfer_data.get('classOfServiceOutbound')

        flight_outbound = Flight(
            number=flight_number_outbound,
            departure_time=departure_datetime_outbound,
            arrival_time=arrival_datetime_outbound,
            company_name=operating_carrier_outbound
        )
        db.session.add(flight_outbound)
        db.session.commit()

        transfer_outbound = Transfers(
            type=class_of_service_outbound,
            source=source_location_outbound,
            destination=destination_location_outbound,
            flight_id=flight_outbound.flight_id
        )
        db.session.add(transfer_outbound)
        db.session.commit()

        booking_outbound = Bookings(
            flight_id=flight_outbound.flight_id,
            user_id=user_id,
            booking_date=datetime.utcnow(),
            payment_status="Done"
        )
        db.session.add(booking_outbound)
        db.session.commit()


    return jsonify({"message": "Booking successful"}), 200

@businessService.route('/bookings/deleteBooking', methods=['DELETE'])
def delete_booking():
    c_booking_delete.inc()

    transfer_data = request.json

    try:
        decoded_token = jwt.decode(transfer_data.get('token'), SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_token.get('user_id')

    except jwt.DecodeError:
        return {"error": "No user with this token :P"}, 404
        
    booking_id = transfer_data.get('booking_id')
    booking = Bookings.query.get(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    if booking.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        db.session.delete(booking)

        transfer = Transfers.query.filter_by(flight_id=booking.flight_id).first()
        if transfer:
            db.session.delete(transfer)

        flight = Flight.query.get(booking.flight_id)
        if flight:
            db.session.delete(flight)

        db.session.commit()
        return jsonify({"message": "Booking deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@businessService.route('/bookings', methods=['GET'])
def get_bookings():
    c_booking_data.inc()

    transfer_data = request.json

    try:
        decoded_token = jwt.decode(transfer_data.get('token'), SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_token.get('user_id')

    except jwt.DecodeError:
        return {"error": "No user with this token :P"}, 404

    bookings = Bookings.query.filter_by(user_id=user_id).all()

    bookings_data = []
    for booking in bookings:
        booking_data = {
            "booking_id": booking.booking_id,
            "flight_id": booking.flight_id,
            "user_id": booking.user_id,
            "booking_date": booking.booking_date.isoformat(),
            "payment_status": booking.payment_status
        }
        bookings_data.append(booking_data)

    return jsonify({"bookings": bookings_data}), 200

@businessService.route('/bookings/modifyBooking', methods=['PUT'])
def modify_booking():
    c_booking_update.inc()

    booking_data = request.json
    booking_id = booking_data.get('booking_id')
    try:
        decoded_token = jwt.decode(booking_data.get('token'), SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_token.get('user_id')

    except jwt.DecodeError:
        return {"error": "No user with this token"}, 404

    booking = Bookings.query.filter_by(booking_id=booking_id, user_id=user_id).first()
    if not booking:
        return {"error": "Booking not found or unauthorized"}, 404

    booking.booking_date = datetime.utcnow()
    booking.payment_status = booking_data.get('payment_status')

    try:
        db.session.commit()

        transfer = Transfers.query.filter_by(flight_id=booking.flight_id).first()
        if transfer:
            transfer.type = booking_data.get('transfer_type')

        db.session.commit()

        return jsonify({"message": "Booking modified successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@businessService.route('/bookings/reviews/create', methods=['POST'])
def create_review():
    data = request.json

    try:
        decoded_token = jwt.decode(data.get('token'), SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_token.get('user_id')

    except jwt.DecodeError:
        return {"error": "No user with this token"}, 404
    
    new_review = Reviews(
        flight_id=data['flight_id'],
        user_id=user_id,
        rating=data['rating'],
        comment=data['comment']
    )

    db.session.add(new_review)
    db.session.commit()
    return jsonify({'message': 'Review created successfully'}), 201

@businessService.route('/bookings/reviews', methods=['GET'])
def get_review():
    data = request.json
    try:
        decoded_token = jwt.decode(data.get('token'), SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_token.get('user_id')

    except jwt.DecodeError:
        return {"error": "No user with this token"}, 404

    review_id = request.json.get('review_id')
    review = Reviews.query.get(review_id)
    if not review:
        return jsonify({'error': 'Review not found'}), 404
    review_data = {
        'review_id': review.review_id,
        'flight_id': review.flight_id,
        'user_id': review.user_id,
        'rating': review.rating,
        'comment': review.comment
    }
    return jsonify(review_data)

@businessService.route('/bookings/reviews/modify', methods=['PUT'])
def modify_review():
    data = request.json
    try:
        decoded_token = jwt.decode(data.get('token'), SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_token.get('user_id')

    except jwt.DecodeError:
        return {"error": "No user with this token"}, 404
    
    review_id = request.json.get('review_id')
    review = Reviews.query.get(review_id)
    if not review:
        return jsonify({'error': 'Review not found'}), 404
    data = request.json
    review.flight_id = data.get('flight_id', review.flight_id)
    review.rating = data.get('rating', review.rating)
    review.comment = data.get('comment', review.comment)
    db.session.commit()
    return jsonify({'message': 'Review modified successfully'})

@businessService.route('/bookings/reviews/delete', methods=['DELETE'])
def delete_review():
    data = request.json
    try:
        decoded_token = jwt.decode(data.get('token'), SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_token.get('user_id')

    except jwt.DecodeError:
        return {"error": "No user with this token"}, 404
    
    review_id = request.json.get('review_id')
    review = Reviews.query.get(review_id)
    if not review:
        return jsonify({'error': 'Review not found'}), 404
    db.session.delete(review)
    db.session.commit()
    return jsonify({'message': 'Review deleted successfully'})